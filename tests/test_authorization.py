"""Authorization decisions from trusted facts, including adversarial cases."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from memoryfence.access.policy import (
    AccessRequest,
    MemoryFacts,
    PrincipalFacts,
    SourceFacts,
    evaluate,
    evaluate_delegation,
)
from memoryfence.domain.access import AuthorizationDecision
from memoryfence.domain.deletion import DeletionRequest
from memoryfence.domain.enums import (
    AgentState,
    DeletionPolicy,
    DeletionScenario,
    MembershipState,
    MemoryState,
    MemoryType,
    MemoryVisibility,
    Permission,
    SourceDeletionState,
    SourceVisibility,
    WorkspaceRole,
)
from memoryfence.domain.errors import ReasonCode
from memoryfence.domain.ids import AgentId, MemoryId, SourceId, UserId, WorkspaceId
from memoryfence.domain.memories import Memory
from memoryfence.domain.principals import Agent, PrincipalRef, WorkspaceMembership
from memoryfence.domain.serialization import sha256_hex
from memoryfence.domain.sources import SourceDocument

NOW = datetime(2026, 1, 1, tzinfo=UTC)
ALICE = UserId("usr-alice")
BOB = UserId("usr-bob")
HOME = WorkspaceId("ws-home")
OTHER = WorkspaceId("ws-other")


def _membership(
    user: UserId, workspace: WorkspaceId, role: WorkspaceRole, *, revoked: bool = False
) -> WorkspaceMembership:
    return WorkspaceMembership(
        workspace_id=workspace,
        user_id=user,
        role=role,
        state=MembershipState.REVOKED if revoked else MembershipState.ACTIVE,
        granted_at=NOW,
        revoked_at=NOW if revoked else None,
    )


def _facts(
    user: UserId,
    workspace: WorkspaceId,
    role: WorkspaceRole | None,
    *,
    revoked: bool = False,
    agent: Agent | None = None,
) -> PrincipalFacts:
    principal = PrincipalRef.agent(agent.id) if agent is not None else PrincipalRef.user(user)
    return PrincipalFacts(
        principal=principal,
        acting_user_id=user,
        agent=agent,
        membership=None if role is None else _membership(user, workspace, role, revoked=revoked),
    )


def _source(owner: UserId, workspace: WorkspaceId, visibility: SourceVisibility) -> SourceFacts:
    return SourceFacts(
        source=SourceDocument(
            id=SourceId("src-notes"),
            workspace_id=workspace,
            owner_user_id=owner,
            title="Notes",
            visibility=visibility,
            deletion_state=SourceDeletionState.ACTIVE,
            deletion_policy=None,
            created_at=NOW,
            deleted_at=None,
        ),
        acting_user_has_active_grant=False,
    )


def _decide(
    facts: PrincipalFacts | None,
    permission: Permission,
    workspace: WorkspaceId,
    resource: SourceFacts | MemoryFacts | None = None,
    *,
    actor: PrincipalRef | None = None,
) -> AuthorizationDecision:
    resolved = actor if actor is not None or facts is None else facts.principal
    return evaluate(
        AccessRequest(
            actor=resolved,
            principal=facts,
            permission=permission,
            workspace_id=workspace,
            resource=resource,
        )
    )


def test_missing_and_unknown_principals_are_denied() -> None:
    missing = evaluate(
        AccessRequest(
            actor=None,
            principal=None,
            permission=Permission.SOURCE_READ,
            workspace_id=HOME,
            resource=None,
        )
    )
    unknown = _decide(None, Permission.SOURCE_READ, HOME, actor=PrincipalRef.user(ALICE))
    assert missing.reason is ReasonCode.MISSING_PRINCIPAL
    assert unknown.reason is ReasonCode.UNKNOWN_PRINCIPAL
    assert missing.allowed is False


def test_non_member_and_revoked_member_are_denied() -> None:
    outsider = _decide(_facts(ALICE, HOME, None), Permission.SOURCE_READ, HOME)
    revoked = _decide(
        _facts(ALICE, HOME, WorkspaceRole.MEMBER, revoked=True), Permission.SOURCE_READ, HOME
    )
    assert outsider.reason is ReasonCode.NOT_A_MEMBER
    assert revoked.reason is ReasonCode.MEMBERSHIP_REVOKED


def test_member_reads_a_workspace_source_and_cannot_moderate() -> None:
    facts = _facts(BOB, HOME, WorkspaceRole.MEMBER)
    source = _source(ALICE, HOME, SourceVisibility.WORKSPACE)
    assert _decide(facts, Permission.SOURCE_READ, HOME, source).reason is ReasonCode.ALLOWED
    denied = _decide(
        facts, Permission.SOURCE_DELETE, HOME, _source(ALICE, HOME, SourceVisibility.WORKSPACE)
    )
    assert denied.reason is ReasonCode.NOT_OWNER


def test_cross_workspace_resource_is_denied() -> None:
    facts = _facts(ALICE, HOME, WorkspaceRole.ADMIN)
    foreign = _source(ALICE, OTHER, SourceVisibility.WORKSPACE)
    decision = _decide(facts, Permission.SOURCE_DELETE, HOME, foreign)
    assert decision.reason is ReasonCode.CROSS_WORKSPACE


def test_private_source_is_hidden_and_a_revoked_grant_does_not_count() -> None:
    facts = _facts(BOB, HOME, WorkspaceRole.MEMBER)
    private = _source(ALICE, HOME, SourceVisibility.PRIVATE)
    assert (
        _decide(facts, Permission.SOURCE_READ, HOME, private).reason
        is ReasonCode.SOURCE_NOT_VISIBLE
    )
    restricted = _source(ALICE, HOME, SourceVisibility.RESTRICTED)
    assert (
        _decide(facts, Permission.SOURCE_READ, HOME, restricted).reason
        is ReasonCode.SOURCE_NOT_VISIBLE
    )


def test_agent_cannot_exceed_or_invent_delegation() -> None:
    agent = Agent(
        id=AgentId("agt-helper"),
        workspace_id=HOME,
        controlling_user_id=ALICE,
        display_name="Helper",
        delegated_permissions=frozenset({Permission.SOURCE_READ}),
        state=AgentState.ACTIVE,
        created_at=NOW,
        revoked_at=None,
    )
    facts = _facts(ALICE, HOME, WorkspaceRole.ADMIN, agent=agent)
    source = _source(ALICE, HOME, SourceVisibility.WORKSPACE)
    assert _decide(facts, Permission.SOURCE_READ, HOME, source).reason is ReasonCode.ALLOWED
    assert (
        _decide(facts, Permission.SOURCE_DELETE, HOME, source).reason
        is ReasonCode.AGENT_NOT_DELEGATED
    )
    other = agent.model_copy(update={"workspace_id": OTHER})
    cross = _decide(
        _facts(ALICE, HOME, WorkspaceRole.ADMIN, agent=other), Permission.SOURCE_READ, HOME, source
    )
    assert cross.reason is ReasonCode.CROSS_WORKSPACE


def test_inactive_agent_is_denied() -> None:
    agent = Agent(
        id=AgentId("agt-helper"),
        workspace_id=HOME,
        controlling_user_id=ALICE,
        display_name="Helper",
        delegated_permissions=frozenset({Permission.SOURCE_READ}),
        state=AgentState.REVOKED,
        created_at=NOW,
        revoked_at=NOW,
    )
    decision = _decide(
        _facts(ALICE, HOME, WorkspaceRole.ADMIN, agent=agent), Permission.SOURCE_READ, HOME
    )
    assert decision.reason is ReasonCode.AGENT_INACTIVE


def test_delegation_cannot_exceed_the_controlling_user() -> None:
    member = _facts(BOB, HOME, WorkspaceRole.MEMBER)
    allowed = evaluate_delegation(
        actor=member.principal,
        principal=member,
        workspace_id=HOME,
        controlling_user_id=BOB,
        requested=frozenset({Permission.SOURCE_READ, Permission.MEMORY_CREATE}),
    )
    exceeded = evaluate_delegation(
        actor=member.principal,
        principal=member,
        workspace_id=HOME,
        controlling_user_id=BOB,
        requested=frozenset({Permission.MEMBERSHIP_MANAGE}),
    )
    on_behalf = evaluate_delegation(
        actor=member.principal,
        principal=member,
        workspace_id=HOME,
        controlling_user_id=ALICE,
        requested=frozenset({Permission.SOURCE_READ}),
    )
    assert allowed.reason is ReasonCode.ALLOWED
    assert exceeded.reason is ReasonCode.DELEGATION_EXCEEDS_PRINCIPAL
    assert on_behalf.reason is ReasonCode.NOT_CONTROLLING_PRINCIPAL


def test_agent_cannot_delegate_further() -> None:
    agent = Agent(
        id=AgentId("agt-helper"),
        workspace_id=HOME,
        controlling_user_id=ALICE,
        display_name="Helper",
        delegated_permissions=frozenset({Permission.AGENT_REGISTER, Permission.SOURCE_READ}),
        state=AgentState.ACTIVE,
        created_at=NOW,
        revoked_at=None,
    )
    facts = _facts(ALICE, HOME, WorkspaceRole.ADMIN, agent=agent)
    decision = evaluate_delegation(
        actor=facts.principal,
        principal=facts,
        workspace_id=HOME,
        controlling_user_id=ALICE,
        requested=frozenset({Permission.SOURCE_READ}),
    )
    assert decision.reason is ReasonCode.AGENT_CANNOT_DELEGATE


def test_revoked_memory_and_forged_deletion_claim_are_rejected() -> None:
    content = "extracted"
    memory = Memory(
        id=MemoryId("mem-000001"),
        workspace_id=HOME,
        memory_type=MemoryType.PRIMARY,
        state=MemoryState.REVOKED,
        visibility=MemoryVisibility.INHERIT_SOURCE,
        owner_user_id=None,
        content=content,
        content_sha256=sha256_hex(content),
        source_revision_id="rev-000001",  # type: ignore[arg-type]
        transformation_id=None,
        derivation_round=0,
        created_at=NOW,
        revoked_at=NOW,
    )
    source = _source(ALICE, HOME, SourceVisibility.WORKSPACE)
    decision = _decide(
        _facts(ALICE, HOME, WorkspaceRole.ADMIN),
        Permission.MEMORY_READ,
        HOME,
        MemoryFacts(memory=memory, source=source),
    )
    assert decision.reason is ReasonCode.MEMORY_REVOKED
    with pytest.raises(ValidationError):
        DeletionRequest.model_validate(
            {
                "source_id": "src-notes",
                "policy": DeletionPolicy.SOURCE_AND_PRIMARY.value,
                "scenario": DeletionScenario.ATTACKER.value,
                "owner_user_id": "usr-mallory",
            }
        )
