"""The write-only ground-truth recorder handed to the system under test."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from memoryfence.domain.deletion import DeletionLedgerEntry, DeletionLedgerEvent
from memoryfence.domain.provenance import TrueProvenanceLink, TrueProvenanceNode
from memoryfence.groundtruth.schema import (
    DeletionEventRow,
    DeletionLedgerRow,
    TrueLinkRow,
    TrueNodeRow,
)


class SqlGroundTruthRecorder:
    """Implements :class:`~memoryfence.domain.protocols.GroundTruthRecorder`.

    Writes go through the unit of work's session, so ground truth commits or rolls back
    together with the system change it describes. There are no read methods.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def record_node(self, node: TrueProvenanceNode) -> None:
        self._session.add(
            TrueNodeRow(
                memory_id=node.memory_id,
                workspace_id=node.workspace_id,
                memory_type=node.memory_type,
                source_id=node.source_id,
                source_revision_id=node.source_revision_id,
                author_user_id=node.author_user_id,
                created_at=node.created_at,
            )
        )
        self._session.flush()

    def record_links(self, links: Sequence[TrueProvenanceLink]) -> None:
        self._session.add_all(
            TrueLinkRow(child_id=link.child_id, parent_id=link.parent_id, ordinal=link.ordinal)
            for link in links
        )
        self._session.flush()

    def record_deletion(
        self, event: DeletionLedgerEvent, entries: Sequence[DeletionLedgerEntry]
    ) -> None:
        self._session.add(
            DeletionEventRow(
                deletion_id=event.deletion_id,
                source_id=event.source_id,
                workspace_id=event.workspace_id,
                policy=event.policy,
                scenario=event.scenario,
                requested_by_kind=event.requested_by.kind,
                requested_by_id=event.requested_by.id,
                run_id=event.run_id,
                occurred_at=event.occurred_at,
            )
        )
        self._session.flush()
        self._session.add_all(
            DeletionLedgerRow(
                deletion_id=entry.deletion_id,
                sequence=entry.sequence,
                effect=entry.effect,
                source_id=entry.source_id,
                revision_id=entry.revision_id,
                memory_id=entry.memory_id,
                content=entry.content,
                content_sha256=entry.content_sha256,
            )
            for entry in entries
        )
        self._session.flush()
