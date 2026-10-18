"""Users, workspaces, memberships, agents, and instruction authority."""

from pydantic import ValidationError
from sqlalchemy import select

from memoryfence.access import evaluate_delegation
from memoryfence.domain.access import ResourceRef
from memoryfence.domain.enums import (
    AgentState,
    EventCategory,
    MembershipState,
    Operation,
    Permission,
    PrincipalKind,
    ResourceKind,
    WorkspaceRole,
)
from memoryfence.domain.errors import (
    AuthorizationDenied,
    ConflictError,
    DomainValidationError,
    InvalidTransitionError,
    ResourceNotFound,
)
from memoryfence.domain.ids import AgentId, IdPrefix, UserId, WorkspaceId
from memoryfence.domain.principals import (
    Agent,
    InstructionAuthority,
    PrincipalRef,
    User,
    Workspace,
    WorkspaceMembership,
)
from memoryfence.observability import Auditor
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.storage.mappers import (
    to_instruction_authority,
    to_membership,
    to_user,
    to_workspace,
)
from memoryfence.storage.schema import (
    AgentPermissionRow,
    AgentRow,
    InstructionAuthorityRow,
    MembershipRow,
    UserRow,
    WorkspaceRow,
)
from memoryfence.workspace.authority import Authorizer, load_agent


class DirectoryService:
    def __init__(self, database: EpisodeDatabase, auditor: Auditor) -> None:
        self._database = database
        self._auditor = auditor

    def register_user(self, display_name: str) -> User:
        """Harness bootstrap: creating an identity grants no workspace authority."""
        with self._auditor.operation(
            EventCategory.DIRECTORY, Operation.USER_REGISTER, actor=None, workspace_id=None
        ) as scope:
            uow = scope.uow
            user = User(
                id=UserId(uow.next_id(IdPrefix.USER)),
                display_name=display_name,
                created_at=uow.now(),
            )
            uow.session.add(
                UserRow(id=user.id, display_name=user.display_name, created_at=user.created_at)
            )
            scope.resource = ResourceRef(kind=ResourceKind.USER, id=user.id)
        return user

    def create_workspace(self, creator: UserId, name: str) -> tuple[Workspace, WorkspaceMembership]:
        """Create a workspace whose creator becomes its first admin."""
        actor = PrincipalRef.user(creator)
        with self._auditor.operation(
            EventCategory.DIRECTORY, Operation.WORKSPACE_CREATE, actor=actor, workspace_id=None
        ) as scope:
            uow = scope.uow
            if uow.session.get(UserRow, creator) is None:
                raise ResourceNotFound("user", creator)
            now = uow.now()
            workspace = Workspace(
                id=WorkspaceId(uow.next_id(IdPrefix.WORKSPACE)), name=name, created_at=now
            )
            uow.session.add(WorkspaceRow(id=workspace.id, name=workspace.name, created_at=now))
            membership = WorkspaceMembership(
                workspace_id=workspace.id,
                user_id=creator,
                role=WorkspaceRole.ADMIN,
                state=MembershipState.ACTIVE,
                granted_at=now,
                revoked_at=None,
            )
            uow.session.add(_membership_row(membership))
            scope.workspace_id = workspace.id
            scope.resource = ResourceRef(kind=ResourceKind.WORKSPACE, id=workspace.id)
        return workspace, membership

    def grant_membership(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        user_id: UserId,
        role: WorkspaceRole,
    ) -> WorkspaceMembership:
        """Add a member, or reinstate a revoked one with ``role``."""
        with self._auditor.operation(
            EventCategory.DIRECTORY,
            Operation.MEMBERSHIP_GRANT,
            actor=actor,
            workspace_id=workspace_id,
            resource=ResourceRef(kind=ResourceKind.USER, id=user_id),
        ) as scope:
            uow = scope.uow
            Authorizer(uow.session).require(actor, Permission.MEMBERSHIP_MANAGE, workspace_id)
            if uow.session.get(UserRow, user_id) is None:
                raise ResourceNotFound("user", user_id)
            row = uow.session.get(MembershipRow, (workspace_id, user_id))
            if row is not None and row.state is MembershipState.ACTIVE:
                raise ConflictError(f"{user_id} is already a member of {workspace_id}")
            membership = WorkspaceMembership(
                workspace_id=workspace_id,
                user_id=user_id,
                role=role,
                state=MembershipState.ACTIVE,
                granted_at=uow.now(),
                revoked_at=None,
            )
            if row is None:
                uow.session.add(_membership_row(membership))
            else:
                row.role = role
                row.state = MembershipState.ACTIVE
                row.granted_at = membership.granted_at
                row.revoked_at = None
            scope.details["role"] = role.value
        return membership

    def revoke_membership(
        self, actor: PrincipalRef | None, workspace_id: WorkspaceId, user_id: UserId
    ) -> WorkspaceMembership:
        """Revoke a membership. The user's agents lose all authority with it."""
        with self._auditor.operation(
            EventCategory.DIRECTORY,
            Operation.MEMBERSHIP_REVOKE,
            actor=actor,
            workspace_id=workspace_id,
            resource=ResourceRef(kind=ResourceKind.USER, id=user_id),
        ) as scope:
            uow = scope.uow
            Authorizer(uow.session).require(actor, Permission.MEMBERSHIP_MANAGE, workspace_id)
            row = uow.session.get(MembershipRow, (workspace_id, user_id))
            if row is None:
                raise ResourceNotFound("membership", f"{workspace_id}/{user_id}")
            if row.state is MembershipState.REVOKED:
                raise InvalidTransitionError(f"membership of {user_id} is already revoked")
            row.state = MembershipState.REVOKED
            row.revoked_at = uow.now()
            uow.session.flush()
            membership = to_membership(row)
        return membership

    def register_agent(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        controlling_user_id: UserId,
        display_name: str,
        permissions: frozenset[Permission],
    ) -> Agent:
        """Register an agent whose delegation never exceeds its controlling user's role."""
        with self._auditor.operation(
            EventCategory.DIRECTORY,
            Operation.AGENT_REGISTER,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            uow = scope.uow
            decision = evaluate_delegation(
                actor=actor,
                principal=Authorizer(uow.session).principal(actor, workspace_id),
                workspace_id=workspace_id,
                controlling_user_id=controlling_user_id,
                requested=permissions,
            )
            if not decision.allowed:
                raise AuthorizationDenied(decision)
            agent = Agent(
                id=AgentId(uow.next_id(IdPrefix.AGENT)),
                workspace_id=workspace_id,
                controlling_user_id=controlling_user_id,
                display_name=display_name,
                delegated_permissions=permissions,
                state=AgentState.ACTIVE,
                created_at=uow.now(),
                revoked_at=None,
            )
            uow.session.add(
                AgentRow(
                    id=agent.id,
                    workspace_id=agent.workspace_id,
                    controlling_user_id=agent.controlling_user_id,
                    display_name=agent.display_name,
                    state=agent.state,
                    created_at=agent.created_at,
                    revoked_at=None,
                )
            )
            uow.session.flush()
            uow.session.add_all(
                AgentPermissionRow(agent_id=agent.id, permission=permission)
                for permission in sorted(permissions)
            )
            scope.resource = ResourceRef(kind=ResourceKind.AGENT, id=agent.id)
            scope.details["permissions"] = tuple(sorted(permissions))
        return agent

    def revoke_agent(self, actor: PrincipalRef | None, agent_id: AgentId) -> Agent:
        """An agent's controlling user, or an admin, may revoke it."""
        resource = ResourceRef(kind=ResourceKind.AGENT, id=agent_id)
        with self._database.unit_of_work() as uow:
            existing = load_agent(uow.session, agent_id)
        if existing is None:
            raise ResourceNotFound("agent", agent_id)
        own_agent = (
            actor is not None
            and actor.kind is PrincipalKind.USER
            and actor.id == existing.controlling_user_id
        )
        permission = Permission.AGENT_REGISTER if own_agent else Permission.AGENT_MANAGE
        with self._auditor.operation(
            EventCategory.DIRECTORY,
            Operation.AGENT_REVOKE,
            actor=actor,
            workspace_id=existing.workspace_id,
            resource=resource,
        ) as scope:
            uow = scope.uow
            Authorizer(uow.session).require(actor, permission, existing.workspace_id)
            row = uow.session.get(AgentRow, agent_id)
            if row is None or row.state is AgentState.REVOKED:
                raise InvalidTransitionError(f"agent {agent_id} is already revoked")
            agent = existing.model_copy(
                update={"state": AgentState.REVOKED, "revoked_at": uow.now()}
            )
            row.state = agent.state
            row.revoked_at = agent.revoked_at
        return agent

    def grant_instruction_authority(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        authority_user_id: UserId,
        subject_user_id: UserId,
    ) -> InstructionAuthority:
        with self._auditor.operation(
            EventCategory.DIRECTORY,
            Operation.INSTRUCTION_AUTHORITY_GRANT,
            actor=actor,
            workspace_id=workspace_id,
            resource=ResourceRef(kind=ResourceKind.USER, id=subject_user_id),
        ) as scope:
            uow = scope.uow
            Authorizer(uow.session).require(actor, Permission.MEMBERSHIP_MANAGE, workspace_id)
            try:
                authority = InstructionAuthority(
                    workspace_id=workspace_id,
                    authority_user_id=authority_user_id,
                    subject_user_id=subject_user_id,
                    granted_at=uow.now(),
                )
            except ValidationError:
                raise DomainValidationError("instruction authority is invalid") from None
            for user_id in (authority_user_id, subject_user_id):
                if uow.session.get(MembershipRow, (workspace_id, user_id)) is None:
                    raise ResourceNotFound("membership", f"{workspace_id}/{user_id}")
            if uow.session.get(
                InstructionAuthorityRow, (workspace_id, authority_user_id, subject_user_id)
            ):
                raise ConflictError("instruction authority already granted")
            uow.session.add(
                InstructionAuthorityRow(
                    workspace_id=workspace_id,
                    authority_user_id=authority_user_id,
                    subject_user_id=subject_user_id,
                    granted_at=authority.granted_at,
                )
            )
        return authority

    def instruction_authorities(
        self, workspace_id: WorkspaceId
    ) -> tuple[InstructionAuthority, ...]:
        with self._database.system_read_session() as session:
            rows = session.scalars(
                select(InstructionAuthorityRow)
                .where(InstructionAuthorityRow.workspace_id == workspace_id)
                .order_by(
                    InstructionAuthorityRow.authority_user_id,
                    InstructionAuthorityRow.subject_user_id,
                )
            )
            return tuple(to_instruction_authority(row) for row in rows)

    def user(self, user_id: UserId) -> User:
        with self._database.system_read_session() as session:
            row = session.get(UserRow, user_id)
            if row is None:
                raise ResourceNotFound("user", user_id)
            return to_user(row)

    def workspace(self, workspace_id: WorkspaceId) -> Workspace:
        with self._database.system_read_session() as session:
            row = session.get(WorkspaceRow, workspace_id)
            if row is None:
                raise ResourceNotFound("workspace", workspace_id)
            return to_workspace(row)

    def agent(self, agent_id: AgentId) -> Agent:
        with self._database.system_read_session() as session:
            agent = load_agent(session, agent_id)
        if agent is None:
            raise ResourceNotFound("agent", agent_id)
        return agent


def _membership_row(membership: WorkspaceMembership) -> MembershipRow:
    return MembershipRow(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        state=membership.state,
        granted_at=membership.granted_at,
        revoked_at=membership.revoked_at,
    )
