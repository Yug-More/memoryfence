"""Identity, workspaces, membership, and agent delegation."""

from typing import Annotated, Self

from pydantic import StringConstraints, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import (
    AgentState,
    MembershipState,
    Permission,
    PrincipalKind,
    WorkspaceRole,
)
from memoryfence.domain.ids import (
    AgentId,
    AgentIdField,
    IdPrefix,
    UserId,
    UserIdField,
    WorkspaceIdField,
    is_valid_id,
)
from memoryfence.domain.time import UtcDatetime

DisplayName = Annotated[str, StringConstraints(min_length=1, max_length=200)]


class PrincipalRef(DomainModel):
    """Who is making a request. An agent reference never implies its user's identity."""

    kind: PrincipalKind
    id: str

    @model_validator(mode="after")
    def _id_matches_kind(self) -> Self:
        prefix = IdPrefix.USER if self.kind is PrincipalKind.USER else IdPrefix.AGENT
        if not is_valid_id(prefix, self.id):
            raise ValueError(f"{self.kind.value} principal requires a '{prefix.value}-' identifier")
        return self

    @classmethod
    def user(cls, user_id: UserId) -> "PrincipalRef":
        return cls(kind=PrincipalKind.USER, id=user_id)

    @classmethod
    def agent(cls, agent_id: AgentId) -> "PrincipalRef":
        return cls(kind=PrincipalKind.AGENT, id=agent_id)


class User(DomainModel):
    id: UserIdField
    display_name: DisplayName
    created_at: UtcDatetime


class Workspace(DomainModel):
    id: WorkspaceIdField
    name: DisplayName
    created_at: UtcDatetime


class WorkspaceMembership(DomainModel):
    workspace_id: WorkspaceIdField
    user_id: UserIdField
    role: WorkspaceRole
    state: MembershipState
    granted_at: UtcDatetime
    revoked_at: UtcDatetime | None

    @model_validator(mode="after")
    def _revocation_is_consistent(self) -> Self:
        revoked = self.state is MembershipState.REVOKED
        if revoked != (self.revoked_at is not None):
            raise ValueError("revoked_at must be set exactly when the membership is revoked")
        if self.revoked_at is not None and self.revoked_at < self.granted_at:
            raise ValueError("revoked_at precedes granted_at")
        return self


class Agent(DomainModel):
    """An AI agent bound to one workspace and one controlling user.

    ``delegated_permissions`` is an upper bound. The agent's effective permissions are
    the intersection with its controlling user's *current* role permissions.
    """

    id: AgentIdField
    workspace_id: WorkspaceIdField
    controlling_user_id: UserIdField
    display_name: DisplayName
    delegated_permissions: frozenset[Permission]
    state: AgentState
    created_at: UtcDatetime
    revoked_at: UtcDatetime | None

    @model_validator(mode="after")
    def _revocation_is_consistent(self) -> Self:
        if (self.state is AgentState.REVOKED) != (self.revoked_at is not None):
            raise ValueError("revoked_at must be set exactly when the agent is revoked")
        return self


class InstructionAuthority(DomainModel):
    """``authority_user_id`` may legitimately instruct ``subject_user_id``'s agents
    (for example team lead to member). Used by provenance-aware defenses in Phase 5."""

    workspace_id: WorkspaceIdField
    authority_user_id: UserIdField
    subject_user_id: UserIdField
    granted_at: UtcDatetime

    @model_validator(mode="after")
    def _distinct_users(self) -> Self:
        if self.authority_user_id == self.subject_user_id:
            raise ValueError("a user cannot hold instruction authority over themselves")
        return self
