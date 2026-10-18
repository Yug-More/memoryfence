"""Writing and reading recorded provenance.

The writer receives a derived memory's true parents and records only the edges the seeded
degradation retains. It never stores how many edges were dropped; under the silent
missingness mode a degraded node is indistinguishable from a complete one.
"""

from collections.abc import Iterable, Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from memoryfence.domain.enums import MemoryType, MissingnessMode
from memoryfence.domain.errors import ProvenanceIntegrityError, ReasonCode, ResourceNotFound
from memoryfence.domain.ids import MemoryId, SourceId, UserId, WorkspaceId
from memoryfence.domain.provenance import (
    ProvenanceDegradationConfiguration,
    RecordedLineageView,
    RecordedProvenanceNode,
)
from memoryfence.provenance.degradation import retains_edge
from memoryfence.provenance.graph import descendants, would_create_cycle
from memoryfence.storage.mappers import to_recorded_node
from memoryfence.storage.schema import RecordedLinkRow, RecordedNodeRow


class RecordedProvenanceReader:
    """Defense-facing view of recorded provenance within one workspace."""

    def __init__(self, session: Session, workspace_id: WorkspaceId) -> None:
        self._session = session
        self._workspace_id = workspace_id

    def node(self, memory_id: MemoryId) -> RecordedProvenanceNode:
        row = self._session.get(RecordedNodeRow, memory_id)
        if row is None or row.workspace_id != self._workspace_id:
            raise ResourceNotFound("recorded provenance node", memory_id)
        return to_recorded_node(row)

    def parents(self, memory_id: MemoryId) -> tuple[MemoryId, ...]:
        statement = (
            select(RecordedLinkRow.parent_id)
            .where(RecordedLinkRow.child_id == memory_id)
            .order_by(RecordedLinkRow.parent_id)
        )
        return tuple(MemoryId(value) for value in self._session.scalars(statement))

    def children(self, memory_id: MemoryId) -> tuple[MemoryId, ...]:
        statement = (
            select(RecordedLinkRow.child_id)
            .where(RecordedLinkRow.parent_id == memory_id)
            .order_by(RecordedLinkRow.child_id)
        )
        return tuple(MemoryId(value) for value in self._session.scalars(statement))

    def ancestors(self, memory_id: MemoryId) -> set[MemoryId]:
        return descendants([memory_id], self.parents)

    def descendants(self, roots: Iterable[MemoryId]) -> set[MemoryId]:
        return descendants(roots, self.children)

    def primary_nodes_for_source(self, source_id: SourceId) -> tuple[MemoryId, ...]:
        statement = (
            select(RecordedNodeRow.memory_id)
            .where(
                RecordedNodeRow.source_id == source_id,
                RecordedNodeRow.workspace_id == self._workspace_id,
            )
            .order_by(RecordedNodeRow.memory_id)
        )
        return tuple(MemoryId(value) for value in self._session.scalars(statement))

    def reach(self, source_id: SourceId) -> set[MemoryId]:
        """Primary memories extracted from ``source_id`` and all recorded descendants."""
        primaries = self.primary_nodes_for_source(source_id)
        return set(primaries) | self.descendants(primaries)

    def lineage(self, memory_id: MemoryId) -> RecordedLineageView:
        node = self.node(memory_id)
        ancestor_ids = self.ancestors(memory_id)
        primaries = [node] if node.memory_type is MemoryType.PRIMARY else []
        primaries += [
            ancestor
            for ancestor in (self.node(ancestor_id) for ancestor_id in sorted(ancestor_ids))
            if ancestor.memory_type is MemoryType.PRIMARY
        ]
        return RecordedLineageView(
            memory_id=node.memory_id,
            workspace_id=node.workspace_id,
            memory_type=node.memory_type,
            parent_ids=self.parents(memory_id),
            ancestor_ids=tuple(sorted(ancestor_ids)),
            source_ids=tuple(sorted({SourceId(p.source_id) for p in primaries if p.source_id})),
            author_user_ids=tuple(
                sorted({UserId(p.author_user_id) for p in primaries if p.author_user_id})
            ),
            marked_incomplete=node.marked_incomplete,
        )


class RecordedProvenanceWriter:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record_primary(
        self,
        *,
        memory_id: MemoryId,
        workspace_id: WorkspaceId,
        source_id: SourceId,
        author_user_id: UserId,
        created_at: datetime,
    ) -> RecordedProvenanceNode:
        node = RecordedProvenanceNode(
            memory_id=memory_id,
            workspace_id=workspace_id,
            memory_type=MemoryType.PRIMARY,
            source_id=source_id,
            author_user_id=author_user_id,
            marked_incomplete=False,
            created_at=created_at,
        )
        self._insert(node)
        return node

    def record_derived(
        self,
        *,
        memory_id: MemoryId,
        workspace_id: WorkspaceId,
        true_parent_ids: Sequence[MemoryId],
        degradation: ProvenanceDegradationConfiguration,
        created_at: datetime,
    ) -> tuple[RecordedProvenanceNode, tuple[MemoryId, ...]]:
        """Record a derived node and its retained edges; return the node and those edges."""
        self._validate_parents(memory_id, workspace_id, true_parent_ids)
        retained = tuple(
            parent_id
            for parent_id in true_parent_ids
            if retains_edge(degradation, memory_id, parent_id)
        )
        incomplete = len(retained) < len(true_parent_ids)
        node = RecordedProvenanceNode(
            memory_id=memory_id,
            workspace_id=workspace_id,
            memory_type=MemoryType.DERIVED,
            source_id=None,
            author_user_id=None,
            marked_incomplete=incomplete and degradation.missingness is MissingnessMode.MARKED,
            created_at=created_at,
        )
        self._insert(node)
        self._session.add_all(
            RecordedLinkRow(child_id=memory_id, parent_id=parent_id) for parent_id in retained
        )
        self._session.flush()
        return node, retained

    def _validate_parents(
        self, child_id: MemoryId, workspace_id: WorkspaceId, parent_ids: Sequence[MemoryId]
    ) -> None:
        if not parent_ids:
            raise ProvenanceIntegrityError(
                ReasonCode.LINEAGE_MALFORMED, "a derived memory needs at least one parent"
            )
        if len(set(parent_ids)) != len(parent_ids):
            raise ProvenanceIntegrityError(
                ReasonCode.LINEAGE_MALFORMED, "a parent is listed more than once"
            )
        if any(parent_id == child_id for parent_id in parent_ids):
            raise ProvenanceIntegrityError(
                ReasonCode.LINEAGE_CYCLE, f"{child_id} would become its own ancestor"
            )
        for parent_id in parent_ids:
            row = self._session.get(RecordedNodeRow, parent_id)
            if row is None:
                raise ProvenanceIntegrityError(
                    ReasonCode.LINEAGE_INVALID_PARENT, f"unknown parent {parent_id}"
                )
            if row.workspace_id != workspace_id:
                raise ProvenanceIntegrityError(
                    ReasonCode.LINEAGE_CROSS_WORKSPACE,
                    f"parent {parent_id} belongs to another workspace",
                )
        reader = RecordedProvenanceReader(self._session, workspace_id)
        if would_create_cycle(child_id, parent_ids, reader.ancestors):
            raise ProvenanceIntegrityError(
                ReasonCode.LINEAGE_CYCLE, f"{child_id} would become its own ancestor"
            )

    def _insert(self, node: RecordedProvenanceNode) -> None:
        if self._session.get(RecordedNodeRow, node.memory_id) is not None:
            raise ProvenanceIntegrityError(
                ReasonCode.LINEAGE_MALFORMED, f"{node.memory_id} is already recorded"
            )
        self._session.add(
            RecordedNodeRow(
                memory_id=node.memory_id,
                workspace_id=node.workspace_id,
                memory_type=node.memory_type,
                source_id=node.source_id,
                author_user_id=node.author_user_id,
                marked_incomplete=node.marked_incomplete,
                created_at=node.created_at,
            )
        )
        self._session.flush()
