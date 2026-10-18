"""Source documents, immutable revisions, and restricted-source access grants."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from memoryfence.domain.access import ResourceRef
from memoryfence.domain.enums import (
    EventCategory,
    Operation,
    Permission,
    ResourceKind,
    SourceDeletionState,
    SourceVisibility,
)
from memoryfence.domain.errors import InvalidTransitionError, ResourceNotFound
from memoryfence.domain.ids import IdPrefix, RevisionId, SourceId, UserId, WorkspaceId
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.serialization import sha256_hex
from memoryfence.domain.sources import SourceAccessGrant, SourceDocument, SourceRevision
from memoryfence.observability import Auditor
from memoryfence.storage.database import UnitOfWork
from memoryfence.storage.mappers import to_grant, to_revision, to_source
from memoryfence.storage.schema import (
    MembershipRow,
    SourceAccessGrantRow,
    SourceRevisionRow,
    SourceRow,
)
from memoryfence.workspace.authority import Authorizer


def _source_ref(source_id: str) -> ResourceRef:
    return ResourceRef(kind=ResourceKind.SOURCE, id=source_id)


def _add_revision(
    uow: UnitOfWork, source_id: SourceId, sequence: int, author: UserId, content: str
) -> SourceRevision:
    revision = SourceRevision(
        id=RevisionId(uow.next_id(IdPrefix.REVISION)),
        source_id=source_id,
        sequence=sequence,
        author_user_id=author,
        content=content,
        content_sha256=sha256_hex(content),
        created_at=uow.now(),
    )
    uow.session.add(
        SourceRevisionRow(
            id=revision.id,
            source_id=revision.source_id,
            sequence=revision.sequence,
            author_user_id=revision.author_user_id,
            content=revision.content,
            content_sha256=revision.content_sha256,
            created_at=revision.created_at,
        )
    )
    uow.session.flush()
    return revision


def latest_revision(session: Session, source_id: SourceId) -> SourceRevisionRow | None:
    statement = (
        select(SourceRevisionRow)
        .where(SourceRevisionRow.source_id == source_id)
        .order_by(SourceRevisionRow.sequence.desc())
        .limit(1)
    )
    return session.scalars(statement).first()


class SourceService:
    def __init__(self, auditor: Auditor) -> None:
        self._auditor = auditor

    def create(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        *,
        title: str,
        content: str,
        visibility: SourceVisibility,
    ) -> tuple[SourceDocument, SourceRevision]:
        """Create a source owned by the acting user (an agent's controlling user)."""
        with self._auditor.operation(
            EventCategory.SOURCE, Operation.SOURCE_CREATE, actor=actor, workspace_id=workspace_id
        ) as scope:
            uow = scope.uow
            facts = Authorizer(uow.session).require(actor, Permission.SOURCE_CREATE, workspace_id)
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
            revision = _add_revision(uow, source.id, 1, facts.acting_user_id, content)
            scope.resource = _source_ref(source.id)
            scope.details["revision_id"] = revision.id
            scope.details["visibility"] = visibility.value
        return source, revision

    def revise(
        self, actor: PrincipalRef | None, source_id: SourceId, content: str
    ) -> SourceRevision:
        """Append a revision. Earlier revisions are never modified."""
        with self._auditor.operation(
            EventCategory.SOURCE,
            Operation.SOURCE_REVISE,
            actor=actor,
            workspace_id=None,
            resource=_source_ref(source_id),
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            row, facts = authorizer.source(source_id, actor)
            scope.workspace_id = WorkspaceId(row.workspace_id)
            principal = authorizer.require(
                actor, Permission.SOURCE_REVISE, WorkspaceId(row.workspace_id), facts
            )
            previous = latest_revision(uow.session, source_id)
            sequence = previous.sequence + 1 if previous is not None else 1
            revision = _add_revision(uow, source_id, sequence, principal.acting_user_id, content)
            scope.details["revision_id"] = revision.id
            scope.details["sequence"] = sequence
        return revision

    def read(
        self, actor: PrincipalRef | None, source_id: SourceId
    ) -> tuple[SourceDocument, SourceRevision]:
        """The source and its latest revision, if the actor may read it."""
        with self._auditor.operation(
            EventCategory.SOURCE,
            Operation.SOURCE_READ,
            actor=actor,
            workspace_id=None,
            resource=_source_ref(source_id),
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            row, facts = authorizer.source(source_id, actor)
            scope.workspace_id = WorkspaceId(row.workspace_id)
            authorizer.require(actor, Permission.SOURCE_READ, WorkspaceId(row.workspace_id), facts)
            revision = latest_revision(uow.session, source_id)
            if revision is None:
                raise ResourceNotFound("source revision", source_id)
            result = (to_source(row), to_revision(revision))
        return result

    def revisions(
        self, actor: PrincipalRef | None, source_id: SourceId
    ) -> tuple[SourceRevision, ...]:
        with self._auditor.operation(
            EventCategory.SOURCE,
            Operation.SOURCE_READ,
            actor=actor,
            workspace_id=None,
            resource=_source_ref(source_id),
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            row, facts = authorizer.source(source_id, actor)
            scope.workspace_id = WorkspaceId(row.workspace_id)
            authorizer.require(actor, Permission.SOURCE_READ, WorkspaceId(row.workspace_id), facts)
            rows = uow.session.scalars(
                select(SourceRevisionRow)
                .where(SourceRevisionRow.source_id == source_id)
                .order_by(SourceRevisionRow.sequence)
            )
            revisions = tuple(to_revision(revision) for revision in rows)
            scope.details["revision_count"] = len(revisions)
        return revisions

    def grant_access(
        self, actor: PrincipalRef | None, source_id: SourceId, user_id: UserId
    ) -> SourceAccessGrant:
        with self._auditor.operation(
            EventCategory.SOURCE,
            Operation.SOURCE_GRANT_ACCESS,
            actor=actor,
            workspace_id=None,
            resource=_source_ref(source_id),
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            row, facts = authorizer.source(source_id, actor)
            scope.workspace_id = WorkspaceId(row.workspace_id)
            workspace_id = WorkspaceId(row.workspace_id)
            authorizer.require(actor, Permission.SOURCE_MANAGE_ACCESS, workspace_id, facts)
            if row.visibility is not SourceVisibility.RESTRICTED:
                raise InvalidTransitionError("access grants apply only to restricted sources")
            if uow.session.get(MembershipRow, (workspace_id, user_id)) is None:
                raise ResourceNotFound("membership", f"{workspace_id}/{user_id}")
            grant_row = uow.session.get(SourceAccessGrantRow, (source_id, user_id))
            if grant_row is not None and grant_row.revoked_at is None:
                raise InvalidTransitionError(f"{user_id} already has access to {source_id}")
            now = uow.now()
            if grant_row is None:
                grant_row = SourceAccessGrantRow(
                    source_id=source_id, user_id=user_id, granted_at=now, revoked_at=None
                )
                uow.session.add(grant_row)
            else:
                grant_row.granted_at = now
                grant_row.revoked_at = None
            uow.session.flush()
            scope.details["grantee"] = user_id
            grant = to_grant(grant_row)
        return grant

    def revoke_access(
        self, actor: PrincipalRef | None, source_id: SourceId, user_id: UserId
    ) -> SourceAccessGrant:
        with self._auditor.operation(
            EventCategory.SOURCE,
            Operation.SOURCE_REVOKE_ACCESS,
            actor=actor,
            workspace_id=None,
            resource=_source_ref(source_id),
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            row, facts = authorizer.source(source_id, actor)
            scope.workspace_id = WorkspaceId(row.workspace_id)
            authorizer.require(
                actor, Permission.SOURCE_MANAGE_ACCESS, WorkspaceId(row.workspace_id), facts
            )
            grant_row = uow.session.get(SourceAccessGrantRow, (source_id, user_id))
            if grant_row is None or grant_row.revoked_at is not None:
                raise InvalidTransitionError(f"{user_id} has no active grant on {source_id}")
            grant_row.revoked_at = uow.now()
            uow.session.flush()
            scope.details["grantee"] = user_id
            grant = to_grant(grant_row)
        return grant
