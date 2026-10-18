"""Primary extraction and derived-memory records.

Phase 2 stores a transformation result supplied by the caller. It does not call a model
and does not generate text. True provenance is reported through the write-only recorder;
recorded provenance keeps only the edges that seeded degradation retains.
"""

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from memoryfence.domain.access import ResourceRef
from memoryfence.domain.enums import (
    EventCategory,
    MemoryState,
    MemoryType,
    MemoryVisibility,
    Operation,
    Permission,
    ResourceKind,
    TransformationType,
)
from memoryfence.domain.errors import (
    DomainValidationError,
    ProvenanceIntegrityError,
    ReasonCode,
    ResourceNotFound,
)
from memoryfence.domain.ids import (
    IdPrefix,
    MemoryId,
    RevisionId,
    SourceId,
    TransformationId,
    UserId,
    WorkspaceId,
)
from memoryfence.domain.memories import Memory, TransformationRecord
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.provenance import (
    ProvenanceDegradationConfiguration,
    TrueProvenanceLink,
    TrueProvenanceNode,
)
from memoryfence.domain.serialization import sha256_hex
from memoryfence.observability import Auditor
from memoryfence.provenance.recorded import RecordedProvenanceWriter
from memoryfence.storage.database import UnitOfWork
from memoryfence.storage.mappers import to_memory
from memoryfence.storage.schema import MemoryRow, SourceRevisionRow, TransformationRow
from memoryfence.workspace.authority import Authorizer


def _memory_ref(memory_id: str) -> ResourceRef:
    return ResourceRef(kind=ResourceKind.MEMORY, id=memory_id)


class MemoryService:
    def __init__(self, auditor: Auditor, degradation: ProvenanceDegradationConfiguration) -> None:
        self._auditor = auditor
        self._degradation = degradation

    def extract(self, actor: PrincipalRef | None, revision_id: RevisionId, content: str) -> Memory:
        """Record a primary memory extracted from one source revision."""
        with self._auditor.operation(
            EventCategory.MEMORY,
            Operation.MEMORY_EXTRACT,
            actor=actor,
            workspace_id=None,
            resource=ResourceRef(kind=ResourceKind.REVISION, id=revision_id),
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            revision = uow.session.get(SourceRevisionRow, revision_id)
            if revision is None:
                raise ResourceNotFound("source revision", revision_id)
            source, facts = authorizer.source(SourceId(revision.source_id), actor)
            workspace_id = WorkspaceId(source.workspace_id)
            scope.workspace_id = workspace_id
            authorizer.require(actor, Permission.MEMORY_CREATE, workspace_id, facts)
            memory = _insert_memory(
                uow,
                memory_id=MemoryId(uow.next_id(IdPrefix.MEMORY)),
                workspace_id=workspace_id,
                memory_type=MemoryType.PRIMARY,
                visibility=MemoryVisibility.INHERIT_SOURCE,
                owner_user_id=None,
                content=content,
                source_revision_id=revision_id,
                transformation_id=None,
                derivation_round=0,
            )
            node = TrueProvenanceNode(
                memory_id=memory.id,
                workspace_id=workspace_id,
                memory_type=MemoryType.PRIMARY,
                source_id=SourceId(revision.source_id),
                source_revision_id=revision_id,
                author_user_id=UserId(source.owner_user_id),
                created_at=memory.created_at,
            )
            uow.ground_truth.record_node(node)
            RecordedProvenanceWriter(uow.session).record_primary(
                memory_id=memory.id,
                workspace_id=workspace_id,
                source_id=SourceId(revision.source_id),
                author_user_id=UserId(source.owner_user_id),
                created_at=memory.created_at,
            )
            scope.resource = _memory_ref(memory.id)
            scope.details["source_id"] = revision.source_id
            scope.details["revision_id"] = revision_id
        return memory

    def derive(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        *,
        transformation_type: TransformationType,
        prompt_version: str,
        parent_ids: tuple[MemoryId, ...],
        content: str,
    ) -> Memory:
        """Record a derived memory. ``content`` is stored output, not generated here.

        The derived memory is private to the acting user. Phase 2 does not widen a
        parent's access control list; a shared derived ACL is deferred to retrieval.
        """
        with self._auditor.operation(
            EventCategory.MEMORY,
            Operation.MEMORY_DERIVE,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            principal = authorizer.require(actor, Permission.MEMORY_TRANSFORM, workspace_id)
            if not parent_ids:
                raise ProvenanceIntegrityError(
                    ReasonCode.LINEAGE_MALFORMED, "a derived memory needs at least one parent"
                )
            if len(set(parent_ids)) != len(parent_ids):
                raise ProvenanceIntegrityError(
                    ReasonCode.LINEAGE_MALFORMED, "a parent is listed more than once"
                )
            parents = tuple(
                _readable_parent(authorizer, actor, workspace_id, parent_id)
                for parent_id in parent_ids
            )
            now = uow.now()
            try:
                transformation = TransformationRecord(
                    id=TransformationId(uow.next_id(IdPrefix.TRANSFORMATION)),
                    workspace_id=workspace_id,
                    transformation_type=transformation_type,
                    prompt_version=prompt_version,
                    derivation_round=1 + max(parent.derivation_round for parent in parents),
                    performed_by=principal.principal,
                    created_at=now,
                )
            except ValidationError:
                raise DomainValidationError("transformation metadata is invalid") from None
            uow.session.add(
                TransformationRow(
                    id=transformation.id,
                    workspace_id=workspace_id,
                    transformation_type=transformation.transformation_type,
                    prompt_version=transformation.prompt_version,
                    derivation_round=transformation.derivation_round,
                    performed_by_kind=transformation.performed_by.kind,
                    performed_by_id=transformation.performed_by.id,
                    created_at=transformation.created_at,
                )
            )
            uow.session.flush()
            memory = _insert_memory(
                uow,
                memory_id=MemoryId(uow.next_id(IdPrefix.MEMORY)),
                workspace_id=workspace_id,
                memory_type=MemoryType.DERIVED,
                visibility=MemoryVisibility.PRIVATE,
                owner_user_id=principal.acting_user_id,
                content=content,
                source_revision_id=None,
                transformation_id=transformation.id,
                derivation_round=transformation.derivation_round,
            )
            uow.ground_truth.record_node(
                TrueProvenanceNode(
                    memory_id=memory.id,
                    workspace_id=workspace_id,
                    memory_type=MemoryType.DERIVED,
                    source_id=None,
                    source_revision_id=None,
                    author_user_id=None,
                    created_at=memory.created_at,
                )
            )
            uow.ground_truth.record_links(
                tuple(
                    TrueProvenanceLink(child_id=memory.id, parent_id=parent.id, ordinal=ordinal)
                    for ordinal, parent in enumerate(parents)
                )
            )
            RecordedProvenanceWriter(uow.session).record_derived(
                memory_id=memory.id,
                workspace_id=workspace_id,
                true_parent_ids=tuple(parent.id for parent in parents),
                degradation=self._degradation,
                created_at=memory.created_at,
            )
            scope.resource = _memory_ref(memory.id)
            scope.details["transformation_id"] = transformation.id
            scope.details["transformation_type"] = transformation_type.value
            scope.details["parent_ids"] = tuple(parent.id for parent in parents)
        return memory

    def read(self, actor: PrincipalRef | None, memory_id: MemoryId) -> Memory:
        with self._auditor.operation(
            EventCategory.MEMORY,
            Operation.MEMORY_READ,
            actor=actor,
            workspace_id=None,
            resource=_memory_ref(memory_id),
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            row, facts = authorizer.memory(memory_id, actor)
            workspace_id = WorkspaceId(row.workspace_id)
            scope.workspace_id = workspace_id
            authorizer.require(actor, Permission.MEMORY_READ, workspace_id, facts)
            memory = to_memory(row)
        return memory


def _readable_parent(
    authorizer: Authorizer,
    actor: PrincipalRef | None,
    workspace_id: WorkspaceId,
    parent_id: MemoryId,
) -> Memory:
    row, facts = authorizer.memory(parent_id, actor)
    if row.workspace_id != workspace_id:
        raise ProvenanceIntegrityError(
            ReasonCode.LINEAGE_CROSS_WORKSPACE,
            f"parent {parent_id} belongs to another workspace",
        )
    authorizer.require(actor, Permission.MEMORY_READ, workspace_id, facts)
    return to_memory(row)


def _insert_memory(
    uow: UnitOfWork,
    *,
    memory_id: MemoryId,
    workspace_id: WorkspaceId,
    memory_type: MemoryType,
    visibility: MemoryVisibility,
    owner_user_id: UserId | None,
    content: str,
    source_revision_id: RevisionId | None,
    transformation_id: TransformationId | None,
    derivation_round: int,
) -> Memory:
    try:
        memory = Memory(
            id=memory_id,
            workspace_id=workspace_id,
            memory_type=memory_type,
            state=MemoryState.ACTIVE,
            visibility=visibility,
            owner_user_id=owner_user_id,
            content=content,
            content_sha256=sha256_hex(content),
            source_revision_id=source_revision_id,
            transformation_id=transformation_id,
            derivation_round=derivation_round,
            created_at=uow.now(),
            revoked_at=None,
        )
    except ValidationError:
        raise DomainValidationError("memory content is invalid") from None
    uow.session.add(
        MemoryRow(
            id=memory.id,
            workspace_id=memory.workspace_id,
            memory_type=memory.memory_type,
            state=memory.state,
            visibility=memory.visibility,
            owner_user_id=memory.owner_user_id,
            content=memory.content,
            content_sha256=memory.content_sha256,
            source_revision_id=memory.source_revision_id,
            transformation_id=memory.transformation_id,
            derivation_round=memory.derivation_round,
            created_at=memory.created_at,
            revoked_at=None,
        )
    )
    uow.session.flush()
    return memory


def memories_for_source(session: Session, source_id: SourceId) -> tuple[MemoryRow, ...]:
    """Primary memory rows extracted from ``source_id``, ordered by identifier."""
    statement = (
        select(MemoryRow)
        .join(SourceRevisionRow, MemoryRow.source_revision_id == SourceRevisionRow.id)
        .where(SourceRevisionRow.source_id == source_id)
        .order_by(MemoryRow.id)
    )
    return tuple(session.scalars(statement))
