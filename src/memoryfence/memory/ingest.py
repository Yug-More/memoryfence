"""Create a source, its first revision, and its primary memory in one transaction."""

from pydantic import ValidationError

from memoryfence.domain.access import ResourceRef
from memoryfence.domain.enums import (
    EventCategory,
    MemoryType,
    MemoryVisibility,
    Operation,
    Permission,
    ResourceKind,
    SourceDeletionState,
    SourceVisibility,
)
from memoryfence.domain.errors import DomainValidationError
from memoryfence.domain.ids import IdPrefix, MemoryId, SourceId, UserId, WorkspaceId
from memoryfence.domain.memories import Memory
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.provenance import TrueProvenanceNode
from memoryfence.domain.sources import SourceDocument, SourceRevision
from memoryfence.observability import Auditor
from memoryfence.provenance.recorded import RecordedProvenanceWriter
from memoryfence.storage.schema import SourceRow
from memoryfence.workspace.authority import Authorizer
from memoryfence.workspace.memories import _insert_memory
from memoryfence.workspace.sources import _add_revision


class IngestionService:
    def __init__(self, auditor: Auditor) -> None:
        self._auditor = auditor

    def ingest(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        *,
        title: str,
        content: str,
        visibility: SourceVisibility,
    ) -> tuple[SourceDocument, SourceRevision, Memory]:
        """Persist one source revision and the primary memory extracted from it.

        A failure in either step rolls the transaction back, so a source is never
        left without its primary memory. A second call creates a new source, not a
        second revision of the first.
        """
        with self._auditor.operation(
            EventCategory.SOURCE,
            Operation.SOURCE_INGEST,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            facts = authorizer.require(actor, Permission.SOURCE_CREATE, workspace_id)
            try:
                source = SourceDocument(
                    id=SourceId(uow.next_id(IdPrefix.SOURCE)),
                    workspace_id=workspace_id,
                    owner_user_id=facts.acting_user_id,
                    title=title,
                    visibility=visibility,
                    deletion_state=SourceDeletionState.ACTIVE,
                    deletion_policy=None,
                    created_at=uow.now(),
                    deleted_at=None,
                )
            except ValidationError:
                raise DomainValidationError("ingestion input is invalid") from None
            uow.session.add(
                SourceRow(
                    id=source.id,
                    workspace_id=source.workspace_id,
                    owner_user_id=source.owner_user_id,
                    title=source.title,
                    visibility=source.visibility,
                    deletion_state=source.deletion_state,
                    deletion_policy=None,
                    created_at=source.created_at,
                    deleted_at=None,
                )
            )
            uow.session.flush()
            _source_row, source_facts = authorizer.source(source.id, actor, workspace_id)
            authorizer.require(actor, Permission.MEMORY_CREATE, workspace_id, source_facts)
            try:
                revision = _add_revision(uow, source.id, 1, facts.acting_user_id, content)
            except ValidationError:
                raise DomainValidationError("ingestion input is invalid") from None
            memory = _insert_memory(
                uow,
                memory_id=MemoryId(uow.next_id(IdPrefix.MEMORY)),
                workspace_id=workspace_id,
                memory_type=MemoryType.PRIMARY,
                visibility=MemoryVisibility.INHERIT_SOURCE,
                owner_user_id=None,
                content=content,
                source_revision_id=revision.id,
                transformation_id=None,
                derivation_round=0,
            )
            uow.ground_truth.record_node(
                TrueProvenanceNode(
                    memory_id=memory.id,
                    workspace_id=workspace_id,
                    memory_type=MemoryType.PRIMARY,
                    source_id=source.id,
                    source_revision_id=revision.id,
                    author_user_id=UserId(source.owner_user_id),
                    created_at=memory.created_at,
                )
            )
            RecordedProvenanceWriter(uow.session).record_primary(
                memory_id=memory.id,
                workspace_id=workspace_id,
                source_id=source.id,
                author_user_id=UserId(source.owner_user_id),
                created_at=memory.created_at,
            )
            scope.resource = ResourceRef(kind=ResourceKind.SOURCE, id=source.id)
            scope.details["revision_id"] = revision.id
            scope.details["memory_id"] = memory.id
            scope.details["visibility"] = visibility.value
        return source, revision, memory
