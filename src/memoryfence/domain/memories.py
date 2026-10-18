"""Memory records and transformation metadata.

A transformation record deliberately does not list its inputs. Inputs are known to the
system under test only through recorded provenance, which may be incomplete; storing
them here would let a defense bypass provenance degradation.
"""

from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import MemoryState, MemoryType, MemoryVisibility, TransformationType
from memoryfence.domain.ids import (
    MemoryIdField,
    RevisionIdField,
    TransformationIdField,
    UserIdField,
    WorkspaceIdField,
)
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.serialization import sha256_hex
from memoryfence.domain.sources import Content, Sha256
from memoryfence.domain.time import UtcDatetime

PromptVersion = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9._-]{0,63}$")]


class TransformationRecord(DomainModel):
    id: TransformationIdField
    workspace_id: WorkspaceIdField
    transformation_type: TransformationType
    prompt_version: PromptVersion
    derivation_round: Annotated[int, Field(ge=1)]
    performed_by: PrincipalRef
    created_at: UtcDatetime


class Memory(DomainModel):
    """A primary or derived memory.

    Primary memories reference exactly one source revision, are round 0, and inherit their
    source's ACL. Derived memories reference a transformation, are round 1 or later, and
    carry a visibility materialized at creation.
    """

    id: MemoryIdField
    workspace_id: WorkspaceIdField
    memory_type: MemoryType
    state: MemoryState
    visibility: MemoryVisibility
    owner_user_id: UserIdField | None
    content: Content
    content_sha256: Sha256
    source_revision_id: RevisionIdField | None
    transformation_id: TransformationIdField | None
    derivation_round: Annotated[int, Field(ge=0)]
    created_at: UtcDatetime
    revoked_at: UtcDatetime | None

    @model_validator(mode="after")
    def _shape_is_consistent(self) -> Self:
        if sha256_hex(self.content) != self.content_sha256:
            raise ValueError("content_sha256 does not match content")
        if self.memory_type is MemoryType.PRIMARY:
            if self.source_revision_id is None or self.transformation_id is not None:
                raise ValueError("a primary memory references exactly one source revision")
            if self.derivation_round != 0:
                raise ValueError("a primary memory is round 0")
            if self.visibility is not MemoryVisibility.INHERIT_SOURCE:
                raise ValueError("a primary memory inherits its source's visibility")
        else:
            if self.transformation_id is None or self.source_revision_id is not None:
                raise ValueError("a derived memory references exactly one transformation")
            if self.derivation_round < 1:
                raise ValueError("a derived memory is round 1 or later")
            if self.visibility is MemoryVisibility.INHERIT_SOURCE:
                raise ValueError("a derived memory has a materialized visibility")
        if (self.visibility is MemoryVisibility.PRIVATE) != (self.owner_user_id is not None):
            raise ValueError("owner_user_id is set exactly for private memories")
        if (self.state is MemoryState.REVOKED) != (self.revoked_at is not None):
            raise ValueError("revoked_at must be set exactly when the memory is revoked")
        return self
