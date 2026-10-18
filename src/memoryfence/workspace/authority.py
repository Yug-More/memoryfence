"""Loading trusted facts for authorization and enforcing decisions.

Facts come only from the database, never from request payloads or model output.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from memoryfence.access import (
    AccessRequest,
    MemoryFacts,
    PrincipalFacts,
    SourceFacts,
    evaluate,
)
from memoryfence.domain.access import AuthorizationDecision
from memoryfence.domain.enums import MemoryType, Permission, PrincipalKind
from memoryfence.domain.errors import AuthorizationDenied, ResourceNotFound
from memoryfence.domain.ids import AgentId, MemoryId, SourceId, UserId, WorkspaceId
from memoryfence.domain.principals import Agent, PrincipalRef
from memoryfence.storage.mappers import to_agent, to_membership, to_memory, to_source
from memoryfence.storage.schema import (
    AgentPermissionRow,
    AgentRow,
    MembershipRow,
    MemoryRow,
    SourceAccessGrantRow,
    SourceRevisionRow,
    SourceRow,
    UserRow,
)


def load_agent(session: Session, agent_id: AgentId) -> Agent | None:
    row = session.get(AgentRow, agent_id)
    if row is None:
        return None
    permissions = session.scalars(
        select(AgentPermissionRow.permission).where(AgentPermissionRow.agent_id == agent_id)
    )
    return to_agent(row, frozenset(permissions))


def load_principal(
    session: Session, actor: PrincipalRef | None, workspace_id: WorkspaceId
) -> PrincipalFacts | None:
    """Facts for ``actor`` in ``workspace_id``, or ``None`` if the principal is unknown."""
    if actor is None:
        return None
    agent: Agent | None = None
    if actor.kind is PrincipalKind.USER:
        if session.get(UserRow, actor.id) is None:
            return None
        acting_user_id = UserId(actor.id)
    else:
        agent = load_agent(session, AgentId(actor.id))
        if agent is None:
            return None
        acting_user_id = agent.controlling_user_id
    membership_row = session.get(MembershipRow, (workspace_id, acting_user_id))
    return PrincipalFacts(
        principal=actor,
        acting_user_id=acting_user_id,
        agent=agent,
        membership=to_membership(membership_row) if membership_row is not None else None,
    )


def _has_active_grant(session: Session, source_id: str, user_id: UserId | None) -> bool:
    if user_id is None:
        return False
    grant = session.get(SourceAccessGrantRow, (source_id, user_id))
    return grant is not None and grant.revoked_at is None


def load_source_row(session: Session, source_id: SourceId) -> SourceRow:
    row = session.get(SourceRow, source_id)
    if row is None:
        raise ResourceNotFound("source", source_id)
    return row


def load_memory_row(session: Session, memory_id: MemoryId) -> MemoryRow:
    row = session.get(MemoryRow, memory_id)
    if row is None:
        raise ResourceNotFound("memory", memory_id)
    return row


def source_facts(session: Session, row: SourceRow, user_id: UserId | None) -> SourceFacts:
    return SourceFacts(
        source=to_source(row),
        acting_user_has_active_grant=_has_active_grant(session, row.id, user_id),
    )


def memory_facts(session: Session, row: MemoryRow, user_id: UserId | None) -> MemoryFacts:
    source: SourceFacts | None = None
    if row.memory_type is MemoryType.PRIMARY:
        revision = session.get(SourceRevisionRow, row.source_revision_id)
        if revision is None:
            raise ResourceNotFound("source revision", str(row.source_revision_id))
        source = source_facts(
            session, load_source_row(session, SourceId(revision.source_id)), user_id
        )
    return MemoryFacts(memory=to_memory(row), source=source)


class Authorizer:
    """Evaluates requests against trusted facts loaded from one session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def principal(
        self, actor: PrincipalRef | None, workspace_id: WorkspaceId
    ) -> PrincipalFacts | None:
        return load_principal(self._session, actor, workspace_id)

    def decide(
        self,
        actor: PrincipalRef | None,
        permission: Permission,
        workspace_id: WorkspaceId,
        resource: SourceFacts | MemoryFacts | None = None,
    ) -> tuple[AuthorizationDecision, PrincipalFacts | None]:
        facts = self.principal(actor, workspace_id)
        decision = evaluate(
            AccessRequest(
                actor=actor,
                principal=facts,
                permission=permission,
                workspace_id=workspace_id,
                resource=resource,
            )
        )
        return decision, facts

    def require(
        self,
        actor: PrincipalRef | None,
        permission: Permission,
        workspace_id: WorkspaceId,
        resource: SourceFacts | MemoryFacts | None = None,
    ) -> PrincipalFacts:
        """Return the actor's facts if allowed; raise :class:`AuthorizationDenied` otherwise."""
        decision, facts = self.decide(actor, permission, workspace_id, resource)
        if not decision.allowed or facts is None:
            raise AuthorizationDenied(decision)
        return facts

    def acting_user(self, actor: PrincipalRef | None, workspace_id: WorkspaceId) -> UserId | None:
        facts = self.principal(actor, workspace_id)
        return facts.acting_user_id if facts is not None else None

    def source(
        self,
        source_id: SourceId,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId | None = None,
    ) -> tuple[SourceRow, SourceFacts]:
        row = load_source_row(self._session, source_id)
        user_id = self.acting_user(actor, WorkspaceId(workspace_id or row.workspace_id))
        return row, source_facts(self._session, row, user_id)

    def memory(
        self, memory_id: MemoryId, actor: PrincipalRef | None
    ) -> tuple[MemoryRow, MemoryFacts]:
        row = load_memory_row(self._session, memory_id)
        user_id = self.acting_user(actor, WorkspaceId(row.workspace_id))
        return row, memory_facts(self._session, row, user_id)
