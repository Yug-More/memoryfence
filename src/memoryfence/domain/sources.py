"""Source documents and their immutable revisions."""

from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import DeletionPolicy, SourceDeletionState, SourceVisibility
from memoryfence.domain.ids import (
    RevisionIdField,
    SourceIdField,
    UserIdField,
    WorkspaceIdField,
)
from memoryfence.domain.serialization import sha256_hex
from memoryfence.domain.time import UtcDatetime

Content = Annotated[str, StringConstraints(min_length=1, max_length=100_000)]
Title = Annotated[str, StringConstraints(min_length=1, max_length=500)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class SourceDocument(DomainModel):
    """A unit of authored content. ``owner_user_id`` is the platform-recorded author.

    A deleted source keeps only this content-free stub (no title, no revisions) so that
    repeated deletion and auditing are well defined.
    """

    id: SourceIdField
    workspace_id: WorkspaceIdField
    owner_user_id: UserIdField
    title: Title | None
    visibility: SourceVisibility
    deletion_state: SourceDeletionState
    deletion_policy: DeletionPolicy | None
    created_at: UtcDatetime
    deleted_at: UtcDatetime | None

    @model_validator(mode="after")
    def _deletion_is_consistent(self) -> Self:
        active = self.deletion_state is SourceDeletionState.ACTIVE
        if active != (self.deleted_at is None) or active != (self.deletion_policy is None):
            raise ValueError("deleted_at and deletion_policy are set exactly when not active")
        if (self.deletion_state is SourceDeletionState.DELETED) != (self.title is None):
            raise ValueError("only a hard-deleted source has no title")
        if self.deletion_policy is DeletionPolicy.NO_DELETION:
            raise ValueError("DS0 never changes a source's deletion state")
        return self


class SourceRevision(DomainModel):
    """An immutable revision. Edits create a new revision with the next sequence number."""

    id: RevisionIdField
    source_id: SourceIdField
    sequence: Annotated[int, Field(ge=1)]
    author_user_id: UserIdField
    content: Content
    content_sha256: Sha256
    created_at: UtcDatetime

    @model_validator(mode="after")
    def _hash_matches(self) -> Self:
        if sha256_hex(self.content) != self.content_sha256:
            raise ValueError("content_sha256 does not match content")
        return self


class SourceAccessGrant(DomainModel):
    """Read access to a restricted source for one user."""

    source_id: SourceIdField
    user_id: UserIdField
    granted_at: UtcDatetime
    revoked_at: UtcDatetime | None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
