"""Authorization decisions."""

from typing import Self

from pydantic import model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import Permission, ResourceKind
from memoryfence.domain.errors import ReasonCode
from memoryfence.domain.ids import WorkspaceIdField
from memoryfence.domain.principals import PrincipalRef


class ResourceRef(DomainModel):
    kind: ResourceKind
    id: str


class AuthorizationDecision(DomainModel):
    """The result of one authorization check. A decision is never a bare Boolean."""

    allowed: bool
    reason: ReasonCode
    permission: Permission
    principal: PrincipalRef | None
    workspace_id: WorkspaceIdField | None
    resource: ResourceRef | None

    @model_validator(mode="after")
    def _reason_matches_outcome(self) -> Self:
        if self.allowed != (self.reason is ReasonCode.ALLOWED):
            raise ValueError("allowed decisions use ALLOWED; denials use a denial code")
        if not self.allowed and not self.reason.is_denial:
            raise ValueError("a denial must carry a denial reason code")
        return self
