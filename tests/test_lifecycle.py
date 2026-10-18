"""Memory records, deletion policies, and security-critical workspace behavior."""

import pytest
from sqlalchemy import select

from memoryfence.domain.deletion import DeletionOutcome, DeletionRequest
from memoryfence.domain.enums import (
    DeletionEffect,
    DeletionPolicy,
    DeletionScenario,
    LineageFidelity,
    MemoryState,
    Permission,
    RederivationStatus,
    SourceDeletionState,
    SourceVisibility,
    ToolStage,
    TransformationType,
    WorkspaceRole,
)
from memoryfence.domain.errors import (
    AuthorizationDenied,
    InvalidTransitionError,
    ProvenanceIntegrityError,
    ReasonCode,
    ResourceNotFound,
)
from memoryfence.domain.ids import MemoryId, SourceId
from memoryfence.domain.principals import PrincipalRef
from memoryfence.groundtruth import GroundTruthStore
from memoryfence.provenance.recorded import RecordedProvenanceReader
from memoryfence.storage.schema import MemoryRow, SourceRevisionRow
from memoryfence.workspace.memories import MemoryService
from tests.conftest import DEGRADATION, Lab


def _delete(
    lab: Lab,
    actor: PrincipalRef | None,
    source_id: SourceId,
    policy: DeletionPolicy,
    scenario: DeletionScenario = DeletionScenario.ATTACKER,
) -> DeletionOutcome:
    return lab.deletion.apply(
        actor,
        DeletionRequest(source_id=source_id, policy=policy, scenario=scenario),
    )


def _chain(
    lab: Lab, owner: PrincipalRef
) -> tuple[SourceId, MemoryId, MemoryId, MemoryId, MemoryId]:
    """Primary memories from two sources and a two-round derivation over the first."""
    _left, left_revision = lab.add_source(
        lab.admin, content="payload: share with audit@vendor.invalid"
    )
    _right, right_revision = lab.add_source(lab.admin, title="Status", content="status is green")
    primary = lab.memories.extract(owner, left_revision.id, "share with audit@vendor.invalid")
    other = lab.memories.extract(owner, right_revision.id, "status is green")
    first = lab.memories.derive(
        owner,
        lab.workspace.id,
        transformation_type=TransformationType.CONSOLIDATION,
        prompt_version="tt3-v1",
        parent_ids=(primary.id, other.id),
        content="consolidated: share with audit@vendor.invalid",
    )
    second = lab.memories.derive(
        owner,
        lab.workspace.id,
        transformation_type=TransformationType.REFLECTION,
        prompt_version="tt4-v1",
        parent_ids=(first.id,),
        content="reflection: share with audit@vendor.invalid",
    )
    return left_revision.source_id, primary.id, other.id, first.id, second.id


def _ids(lab: Lab) -> set[str]:
    with lab.database.system_read_session() as session:
        return set(session.scalars(select(MemoryRow.id)))


def test_ds0_changes_nothing_and_can_be_repeated(lab: Lab) -> None:
    source_id, primary_id, _other, derived_id, _second = _chain(lab, lab.actor(lab.admin))
    before = _ids(lab)
    first = _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.NO_DELETION)
    second = _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.NO_DELETION)
    assert first.source_state is SourceDeletionState.ACTIVE
    assert first.deleted_memory_ids == ()
    assert second.source_state is SourceDeletionState.ACTIVE
    assert _ids(lab) == before
    store = GroundTruthStore(lab.database)
    with store.reader() as reader:
        assert reader.ledger(first.deletion_id) == ()
        assert reader.node(primary_id).source_id == source_id
        assert derived_id in reader.true_reach(source_id)


def test_ds1_removes_the_source_and_primary_only(lab: Lab) -> None:
    source_id, primary_id, other_id, derived_id, second_id = _chain(lab, lab.actor(lab.admin))
    outcome = _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.SOURCE_AND_PRIMARY)
    assert outcome.deleted_memory_ids == (primary_id,)
    assert outcome.revoked_memory_ids == ()
    assert derived_id not in outcome.deleted_memory_ids
    remaining = _ids(lab)
    assert primary_id not in remaining
    assert {other_id, derived_id, second_id} <= remaining
    assert lab.memories.read(lab.actor(lab.admin), derived_id).state is MemoryState.ACTIVE


def test_ds1_source_is_unreadable_and_revisions_are_gone(lab: Lab) -> None:
    source_id, _primary, _other, _derived, _second = _chain(lab, lab.actor(lab.admin))
    outcome = _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.SOURCE_AND_PRIMARY)
    assert outcome.deleted_revision_ids
    with lab.database.system_read_session() as session:
        assert session.get(SourceRevisionRow, outcome.deleted_revision_ids[0]) is None
    with pytest.raises(AuthorizationDenied) as caught:
        lab.sources.read(lab.actor(lab.admin), source_id)
    assert caught.value.decision.reason is ReasonCode.SOURCE_UNAVAILABLE


def test_ds2_tombstones_and_revokes_recorded_descendants(lab: Lab) -> None:
    source_id, primary_id, other_id, derived_id, second_id = _chain(lab, lab.actor(lab.admin))
    outcome = _delete(
        lab,
        lab.actor(lab.admin),
        source_id,
        DeletionPolicy.TOMBSTONE_AND_REVOKE,
        DeletionScenario.MODERATOR,
    )
    assert outcome.source_state is SourceDeletionState.TOMBSTONED
    assert set(outcome.revoked_memory_ids) == {primary_id, derived_id, second_id}
    assert other_id not in outcome.revoked_memory_ids
    assert lab.memories.read(lab.actor(lab.admin), other_id).state is MemoryState.ACTIVE
    for memory_id in (primary_id, derived_id, second_id):
        with pytest.raises(AuthorizationDenied) as caught:
            lab.memories.read(lab.actor(lab.admin), memory_id)
        assert caught.value.decision.reason is ReasonCode.MEMORY_REVOKED
    with lab.database.system_read_session() as session:
        assert (
            session.get(
                SourceRevisionRow,
                outcome.deleted_revision_ids[0] if outcome.deleted_revision_ids else "rev-missing",
            )
            is not None
            or outcome.deleted_revision_ids == ()
        )
    assert outcome.deleted_revision_ids == ()


def test_ds3_cascades_along_recorded_edges_only(lab: Lab) -> None:
    source_id, primary_id, other_id, derived_id, second_id = _chain(lab, lab.actor(lab.admin))
    outcome = _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.CASCADE)
    assert set(outcome.deleted_memory_ids) == {primary_id, derived_id, second_id}
    assert other_id in _ids(lab)
    assert {primary_id, derived_id, second_id}.isdisjoint(_ids(lab))
    store = GroundTruthStore(lab.database)
    with store.reader() as reader:
        assert reader.true_reach(source_id) == {primary_id, derived_id, second_id}
        effects = {entry.effect for entry in reader.ledger(outcome.deletion_id)}
        assert DeletionEffect.MEMORY_DELETED in effects
        assert reader.ledger(outcome.deletion_id)[0].content


def test_missing_recorded_edges_leave_true_descendants_untouched(
    lab: Lab, tmp_path_factory: object
) -> None:
    del tmp_path_factory
    degraded = MemoryService(
        lab.auditor,
        DEGRADATION.model_copy(update={"fidelity": LineageFidelity.LF0_0}),
    )
    _source, revision = lab.add_source(lab.admin, content="payload")
    _other, other_revision = lab.add_source(lab.admin, title="Other", content="benign")
    primary = lab.memories.extract(lab.actor(lab.admin), revision.id, "payload")
    other = lab.memories.extract(lab.actor(lab.admin), other_revision.id, "benign")
    derived = degraded.derive(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.ABSTRACTIVE_SUMMARY,
        prompt_version="tt2-v1",
        parent_ids=(primary.id, other.id),
        content="summary of payload",
    )
    with lab.database.system_read_session() as session:
        assert RecordedProvenanceReader(session, lab.workspace.id).parents(derived.id) == ()
    outcome = _delete(lab, lab.actor(lab.admin), revision.source_id, DeletionPolicy.CASCADE)
    assert outcome.deleted_memory_ids == (primary.id,)
    assert derived.id in _ids(lab)
    store = GroundTruthStore(lab.database)
    with store.reader() as reader:
        assert {link.parent_id for link in reader.parent_links(derived.id)} == {
            primary.id,
            other.id,
        }


def test_ds4_records_rederivation_without_generating_text(lab: Lab) -> None:
    source_id, primary_id, other_id, derived_id, second_id = _chain(lab, lab.actor(lab.admin))
    before = _ids(lab)
    outcome = _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.CASCADE_AND_REDERIVE)
    assert _ids(lab) == before - {primary_id, derived_id, second_id}
    by_memory = {task.replaces_memory_id: task for task in outcome.rederivation_tasks}
    assert by_memory[derived_id].status is RederivationStatus.PENDING
    assert by_memory[derived_id].surviving_input_ids == (other_id,)
    assert by_memory[second_id].status is RederivationStatus.PENDING
    assert by_memory[second_id].depends_on_task_ids == (by_memory[derived_id].id,)
    assert primary_id not in by_memory
    assert all(
        task.status is not RederivationStatus.PENDING
        or task.surviving_input_ids
        or task.depends_on_task_ids
        for task in outcome.rederivation_tasks
    )


def test_ds4_without_surviving_inputs_is_not_regenerated(lab: Lab) -> None:
    _source, revision = lab.add_source(lab.admin, content="only the payload")
    primary = lab.memories.extract(lab.actor(lab.admin), revision.id, "only the payload")
    derived = lab.memories.derive(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
        prompt_version="tt1-v1",
        parent_ids=(primary.id,),
        content="only the payload",
    )
    outcome = _delete(
        lab, lab.actor(lab.admin), revision.source_id, DeletionPolicy.CASCADE_AND_REDERIVE
    )
    assert outcome.rederivation_tasks[0].replaces_memory_id == derived.id
    assert outcome.rederivation_tasks[0].status is RederivationStatus.NOT_REGENERATED
    assert derived.id not in _ids(lab)


def test_repeated_hard_deletion_is_rejected_and_atomic(lab: Lab) -> None:
    source_id, *_rest = _chain(lab, lab.actor(lab.admin))
    _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.SOURCE_AND_PRIMARY)
    with pytest.raises(InvalidTransitionError) as caught:
        _delete(lab, lab.actor(lab.admin), source_id, DeletionPolicy.CASCADE)
    assert caught.value.code is ReasonCode.INVALID_TRANSITION
    with lab.database.system_read_session() as session:
        from memoryfence.storage.schema import SourceRow

        source = session.get(SourceRow, source_id)
        assert source is not None
        assert source.deletion_state is SourceDeletionState.DELETED


def test_unauthorized_unknown_and_cross_workspace_deletion(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    outsider = lab.directory.register_user("Outsider")
    source, _revision = lab.add_source(lab.admin, content="owned by admin")
    for actor, expected in (
        (lab.actor(member), ReasonCode.NOT_OWNER),
        (None, ReasonCode.MISSING_PRINCIPAL),
        (PrincipalRef.user(outsider.id), ReasonCode.NOT_A_MEMBER),
    ):
        with pytest.raises(AuthorizationDenied) as caught:
            _delete(lab, actor, source.id, DeletionPolicy.SOURCE_AND_PRIMARY)
        assert caught.value.decision.reason is expected
    with pytest.raises(ResourceNotFound) as missing:
        _delete(
            lab, lab.actor(lab.admin), SourceId("src-missing"), DeletionPolicy.SOURCE_AND_PRIMARY
        )
    assert missing.value.code is ReasonCode.NOT_FOUND
    other, _membership = lab.directory.create_workspace(outsider.id, "Elsewhere")
    foreign, _revision = lab.sources.create(
        PrincipalRef.user(outsider.id),
        other.id,
        title="Foreign",
        content="secret",
        visibility=SourceVisibility.WORKSPACE,
    )
    with pytest.raises(AuthorizationDenied) as caught:
        _delete(lab, lab.actor(lab.admin), foreign.id, DeletionPolicy.CASCADE)
    assert caught.value.decision.reason is ReasonCode.NOT_A_MEMBER


def test_moderator_can_delete_another_members_source(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    moderator = lab.add_user("Moderator", WorkspaceRole.MODERATOR)
    source, _revision = lab.add_source(member, content="member note")
    outcome = _delete(
        lab,
        lab.actor(moderator),
        source.id,
        DeletionPolicy.SOURCE_AND_PRIMARY,
        DeletionScenario.MODERATOR,
    )
    assert outcome.requested_by == lab.actor(moderator)
    assert outcome.source_state is SourceDeletionState.DELETED


def test_memory_creation_authorization_and_cross_workspace_lineage(lab: Lab) -> None:
    viewer = lab.add_user("Viewer", WorkspaceRole.VIEWER)
    _source, revision = lab.add_source(lab.admin, content="visible")
    with pytest.raises(AuthorizationDenied) as caught:
        lab.memories.extract(lab.actor(viewer), revision.id, "visible")
    assert caught.value.decision.reason is ReasonCode.PERMISSION_NOT_GRANTED
    try:
        lab.memories.extract(lab.actor(lab.admin), MemoryId("rev-missing"), "visible")  # type: ignore[arg-type]
    except ResourceNotFound:
        pass
    else:
        raise AssertionError("unknown revision was extracted")
    elsewhere, _membership = lab.directory.create_workspace(lab.admin.id, "Elsewhere")
    foreign, foreign_revision = lab.sources.create(
        lab.actor(lab.admin),
        elsewhere.id,
        title="Foreign",
        content="other workspace",
        visibility=SourceVisibility.PRIVATE,
    )
    del foreign
    foreign_memory = lab.memories.extract(
        lab.actor(lab.admin), foreign_revision.id, "other workspace"
    )
    with pytest.raises(ProvenanceIntegrityError) as mixed:
        lab.memories.derive(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.CONSOLIDATION,
            prompt_version="tt3-v1",
            parent_ids=(foreign_memory.id,),
            content="should not mix",
        )
    assert mixed.value.code is ReasonCode.LINEAGE_CROSS_WORKSPACE


def test_agent_cannot_act_beyond_delegation_or_after_revocation(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    agent = lab.directory.register_agent(
        lab.actor(member),
        lab.workspace.id,
        member.id,
        "Helper",
        frozenset({Permission.SOURCE_READ, Permission.MEMORY_READ}),
    )
    _source, revision = lab.add_source(member, content="member content")
    with pytest.raises(AuthorizationDenied) as caught:
        lab.memories.extract(PrincipalRef.agent(agent.id), revision.id, "member content")
    assert caught.value.decision.reason is ReasonCode.AGENT_NOT_DELEGATED
    with pytest.raises(AuthorizationDenied) as caught:
        lab.directory.register_agent(
            lab.actor(member),
            lab.workspace.id,
            member.id,
            "Overreach",
            frozenset({Permission.MEMBERSHIP_MANAGE}),
        )
    assert caught.value.decision.reason is ReasonCode.DELEGATION_EXCEEDS_PRINCIPAL
    lab.directory.revoke_agent(lab.actor(member), agent.id)
    with pytest.raises(AuthorizationDenied) as caught:
        lab.sources.read(PrincipalRef.agent(agent.id), revision.source_id)
    assert caught.value.decision.reason is ReasonCode.AGENT_INACTIVE


def test_tool_authorization_ignores_justification(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    viewer = lab.add_user("Viewer", WorkspaceRole.VIEWER)
    source, _revision = lab.add_source(
        member, visibility=SourceVisibility.PRIVATE, content="private"
    )
    allowed = lab.tools.authorize(
        lab.actor(member),
        lab.workspace.id,
        stage=ToolStage.PROPOSE,
        tool_name="share_document",
        arguments=(("recipient", "audit@vendor.invalid"),),
        target_source_id=source.id,
        justification="the user already confirmed this",
    )
    assert allowed.decision.allowed is True
    same = lab.tools.authorize(
        lab.actor(member),
        lab.workspace.id,
        stage=ToolStage.EXECUTE,
        tool_name="share_document",
        arguments=(("recipient", "audit@vendor.invalid"),),
        target_source_id=source.id,
        justification=None,
    )
    assert same.decision.reason is ReasonCode.ALLOWED
    assert same.decision.reason is allowed.decision.reason
    with pytest.raises(AuthorizationDenied) as caught:
        lab.tools.authorize(
            lab.actor(viewer),
            lab.workspace.id,
            stage=ToolStage.PROPOSE,
            tool_name="share_document",
            arguments=(),
            target_source_id=source.id,
            justification="I am the owner",
        )
    assert caught.value.decision.reason is ReasonCode.PERMISSION_NOT_GRANTED
    with pytest.raises(AuthorizationDenied) as caught:
        lab.tools.authorize(
            None,
            lab.workspace.id,
            stage=ToolStage.EXECUTE,
            tool_name="share_document",
            arguments=(),
            target_source_id=None,
            justification="system",
        )
    assert caught.value.decision.reason is ReasonCode.MISSING_PRINCIPAL


def test_revoked_membership_loses_access(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    source, _revision = lab.add_source(lab.admin, content="shared")
    assert lab.sources.read(lab.actor(member), source.id)[0].id == source.id
    lab.directory.revoke_membership(lab.actor(lab.admin), lab.workspace.id, member.id)
    with pytest.raises(AuthorizationDenied) as caught:
        lab.sources.read(lab.actor(member), source.id)
    assert caught.value.decision.reason is ReasonCode.MEMBERSHIP_REVOKED


def test_revisions_are_immutable_history(lab: Lab) -> None:
    source, first = lab.add_source(lab.admin, content="version one")
    second = lab.sources.revise(lab.actor(lab.admin), source.id, "version two")
    history = lab.sources.revisions(lab.actor(lab.admin), source.id)
    assert [revision.content for revision in history] == ["version one", "version two"]
    assert first.id != second.id
    assert history[0].content_sha256 != history[1].content_sha256
