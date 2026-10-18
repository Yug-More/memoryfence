"""Authorization decisions.

Checks run in a fixed order and the only path to an allowed decision is the final
``return``; every other path denies with a stable reason code.
"""

from typing import Self

from pydantic import model_validator

from memoryfence.access.permissions import ROLE_PERMISSIONS
from memoryfence.domain.access import AuthorizationDecision, ResourceRef
from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import (
    AgentState,
    MembershipState,
    MemoryState,
    MemoryVisibility,
    Permission,
    PrincipalKind,
    ResourceKind,
    SourceDeletionState,
    SourceVisibility,
)
from memoryfence.domain.errors import DomainValidationError, ReasonCode
from memoryfence.domain.ids import UserId, UserIdField, WorkspaceId, WorkspaceIdField
from memoryfence.domain.memories import Memory
from memoryfence.domain.principals import Agent, PrincipalRef, WorkspaceMembership
from memoryfence.domain.sources import SourceDocument


class PrincipalFacts(DomainModel):
    """Trusted state about the requesting principal, loaded from the database.

    ``acting_user_id`` is the human whose authority is used: the user themself, or an
    agent's controlling user. ``membership`` is that user's membership in the requested
    workspace, if any.
    """

    principal: PrincipalRef
    acting_user_id: UserIdField
    agent: Agent | None
    membership: WorkspaceMembership | None

    @model_validator(mode="after")
    def _facts_are_coherent(self) -> Self:
        if self.principal.kind is PrincipalKind.USER:
            if self.agent is not None or self.principal.id != self.acting_user_id:
                raise ValueError("a user acts with their own authority")
        elif (
            self.agent is None
            or self.agent.id != self.principal.id
            or self.agent.controlling_user_id != self.acting_user_id
        ):
            raise ValueError("an agent acts with its controlling user's authority")
        if self.membership is not None and self.membership.user_id != self.acting_user_id:
            raise ValueError("membership must belong to the acting user")
        return self


class SourceFacts(DomainModel):
    source: SourceDocument
    acting_user_has_active_grant: bool


class MemoryFacts(DomainModel):
    """``source`` is required for primary memories, whose ACL is their source's."""

    memory: Memory
    source: SourceFacts | None

    @model_validator(mode="after")
    def _primary_has_source(self) -> Self:
        inherits = self.memory.visibility is MemoryVisibility.INHERIT_SOURCE
        if inherits != (self.source is not None):
            raise ValueError("source facts are required exactly for primary memories")
        return self


class AccessRequest(DomainModel):
    actor: PrincipalRef | None
    principal: PrincipalFacts | None
    permission: Permission
    workspace_id: WorkspaceIdField
    resource: SourceFacts | MemoryFacts | None


_SOURCE_READ_RULE = frozenset(
    {
        Permission.SOURCE_READ,
        Permission.MEMORY_CREATE,
        Permission.TOOL_PROPOSE,
        Permission.TOOL_EXECUTE,
    }
)
_SOURCE_OWNER_RULE = frozenset({Permission.SOURCE_REVISE, Permission.SOURCE_MANAGE_ACCESS})
_MEMORY_READ_RULE = frozenset({Permission.MEMORY_READ, Permission.MEMORY_TRANSFORM})
_NO_RESOURCE_RULE = frozenset(
    {
        Permission.SOURCE_CREATE,
        Permission.MEMORY_TRANSFORM,
        Permission.MEMBERSHIP_MANAGE,
        Permission.AGENT_REGISTER,
        Permission.AGENT_MANAGE,
        Permission.TOOL_PROPOSE,
        Permission.TOOL_EXECUTE,
    }
)


def effective_permissions(principal: PrincipalFacts) -> frozenset[Permission]:
    """Role permissions of the acting user, intersected with an agent's delegation."""
    membership = principal.membership
    if membership is None or membership.state is not MembershipState.ACTIVE:
        return frozenset()
    permissions = ROLE_PERMISSIONS[membership.role]
    agent = principal.agent
    if agent is not None:
        if agent.state is not AgentState.ACTIVE:
            return frozenset()
        permissions &= agent.delegated_permissions
    return permissions


def _resource_ref(resource: SourceFacts | MemoryFacts | None) -> ResourceRef | None:
    if isinstance(resource, SourceFacts):
        return ResourceRef(kind=ResourceKind.SOURCE, id=resource.source.id)
    if isinstance(resource, MemoryFacts):
        return ResourceRef(kind=ResourceKind.MEMORY, id=resource.memory.id)
    return None


def _resource_workspace(resource: SourceFacts | MemoryFacts) -> WorkspaceId:
    if isinstance(resource, SourceFacts):
        return resource.source.workspace_id
    return resource.memory.workspace_id


def _source_readable(user_id: UserId, facts: SourceFacts) -> ReasonCode | None:
    source = facts.source
    if source.deletion_state is not SourceDeletionState.ACTIVE:
        return ReasonCode.SOURCE_UNAVAILABLE
    if source.visibility is SourceVisibility.WORKSPACE or source.owner_user_id == user_id:
        return None
    if source.visibility is SourceVisibility.RESTRICTED and facts.acting_user_has_active_grant:
        return None
    return ReasonCode.SOURCE_NOT_VISIBLE


def _memory_readable(user_id: UserId, facts: MemoryFacts) -> ReasonCode | None:
    memory = facts.memory
    if memory.state is not MemoryState.ACTIVE:
        return ReasonCode.MEMORY_REVOKED
    if facts.source is not None:
        return _source_readable(user_id, facts.source)
    if memory.visibility is MemoryVisibility.PRIVATE and memory.owner_user_id != user_id:
        return ReasonCode.MEMORY_NOT_VISIBLE
    return None


def _resource_denial(
    permission: Permission,
    resource: SourceFacts | MemoryFacts | None,
    principal: PrincipalFacts,
) -> ReasonCode | None:
    user_id = principal.acting_user_id
    if resource is None:
        return None if permission in _NO_RESOURCE_RULE else ReasonCode.UNSUPPORTED_REQUEST
    if isinstance(resource, MemoryFacts):
        if permission in _MEMORY_READ_RULE:
            return _memory_readable(user_id, resource)
        return ReasonCode.UNSUPPORTED_REQUEST
    if permission in _SOURCE_READ_RULE:
        return _source_readable(user_id, resource)
    if permission in _SOURCE_OWNER_RULE:
        if resource.source.deletion_state is not SourceDeletionState.ACTIVE:
            return ReasonCode.SOURCE_UNAVAILABLE
        return None if resource.source.owner_user_id == user_id else ReasonCode.NOT_OWNER
    if permission is Permission.SOURCE_DELETE:
        if resource.source.owner_user_id == user_id:
            return None
        if Permission.SOURCE_MODERATE in effective_permissions(principal):
            return None
        return ReasonCode.NOT_OWNER
    return ReasonCode.UNSUPPORTED_REQUEST


def evaluate(request: AccessRequest) -> AuthorizationDecision:
    def decide(reason: ReasonCode) -> AuthorizationDecision:
        return AuthorizationDecision(
            allowed=reason is ReasonCode.ALLOWED,
            reason=reason,
            permission=request.permission,
            principal=request.actor,
            workspace_id=request.workspace_id,
            resource=_resource_ref(request.resource),
        )

    if request.actor is None:
        return decide(ReasonCode.MISSING_PRINCIPAL)
    principal = request.principal
    if principal is None:
        return decide(ReasonCode.UNKNOWN_PRINCIPAL)
    if principal.principal != request.actor:
        raise DomainValidationError("principal facts do not describe the requesting actor")
    membership = principal.membership
    if membership is not None and membership.workspace_id != request.workspace_id:
        raise DomainValidationError("membership facts are for a different workspace")

    agent = principal.agent
    if agent is not None and agent.workspace_id != request.workspace_id:
        return decide(ReasonCode.CROSS_WORKSPACE)
    if request.resource is not None and _resource_workspace(request.resource) != (
        request.workspace_id
    ):
        return decide(ReasonCode.CROSS_WORKSPACE)
    if agent is not None and agent.state is not AgentState.ACTIVE:
        return decide(ReasonCode.AGENT_INACTIVE)
    if membership is None:
        return decide(ReasonCode.NOT_A_MEMBER)
    if membership.state is not MembershipState.ACTIVE:
        return decide(ReasonCode.MEMBERSHIP_REVOKED)
    if request.permission not in ROLE_PERMISSIONS[membership.role]:
        return decide(ReasonCode.PERMISSION_NOT_GRANTED)
    if agent is not None and request.permission not in agent.delegated_permissions:
        return decide(ReasonCode.AGENT_NOT_DELEGATED)
    denial = _resource_denial(request.permission, request.resource, principal)
    if denial is not None:
        return decide(denial)
    return decide(ReasonCode.ALLOWED)


def evaluate_delegation(
    *,
    actor: PrincipalRef | None,
    principal: PrincipalFacts | None,
    workspace_id: WorkspaceId,
    controlling_user_id: UserId,
    requested: frozenset[Permission],
) -> AuthorizationDecision:
    """May ``actor`` register an agent for ``controlling_user_id`` with ``requested``?

    Only a user may delegate, only to their own agents, and never beyond their own
    current role permissions.
    """
    base = evaluate(
        AccessRequest(
            actor=actor,
            principal=principal,
            permission=Permission.AGENT_REGISTER,
            workspace_id=workspace_id,
            resource=None,
        )
    )
    if not base.allowed or principal is None:
        return base

    def deny(reason: ReasonCode) -> AuthorizationDecision:
        return AuthorizationDecision(
            allowed=False,
            reason=reason,
            permission=base.permission,
            principal=base.principal,
            workspace_id=base.workspace_id,
            resource=None,
        )

    if principal.agent is not None:
        return deny(ReasonCode.AGENT_CANNOT_DELEGATE)
    if principal.acting_user_id != controlling_user_id:
        return deny(ReasonCode.NOT_CONTROLLING_PRINCIPAL)
    if not requested <= effective_permissions(principal):
        return deny(ReasonCode.DELEGATION_EXCEEDS_PRINCIPAL)
    return base
