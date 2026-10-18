"""Membership, grants, manifests, and validation edges."""

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from memoryfence.domain.enums import (
    AgentState,
    MembershipState,
    RunStatus,
    SourceOrigin,
    SourceVisibility,
    ToolStage,
    TransformationType,
    WorkspaceRole,
)
from memoryfence.domain.errors import (
    AuthorizationDenied,
    ConflictError,
    DomainValidationError,
    InvalidTransitionError,
    PersistenceError,
    ProvenanceIntegrityError,
    ReasonCode,
    ResourceNotFound,
)
from memoryfence.domain.ids import AgentId, RunId, SourceId, UserId, WorkspaceId
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.time import StepClock, SystemClock
from memoryfence.groundtruth.recorder import SqlGroundTruthRecorder
from memoryfence.groundtruth.schema import GroundTruthBase
from memoryfence.groundtruth.store import GroundTruthStore
from memoryfence.observability.manifest import finish_manifest, new_manifest
from memoryfence.storage.database import EpisodeDatabase
from tests.conftest import Lab


def test_restricted_grants_and_revisions(lab: Lab) -> None:
    owner = lab.add_user("Owner", WorkspaceRole.MEMBER)
    reader = lab.add_user("Reader", WorkspaceRole.MEMBER)
    outsider = lab.directory.register_user("Outsider")
    source, _revision = lab.add_source(
        owner, visibility=SourceVisibility.RESTRICTED, content="limited"
    )
    with pytest.raises(AuthorizationDenied) as hidden:
        lab.sources.read(lab.actor(reader), source.id)
    assert hidden.value.decision.reason is ReasonCode.SOURCE_NOT_VISIBLE
    grant = lab.sources.grant_access(lab.actor(owner), source.id, reader.id)
    assert grant.is_active
    assert lab.sources.read(lab.actor(reader), source.id)[1].content == "limited"
    with pytest.raises(InvalidTransitionError):
        lab.sources.grant_access(lab.actor(owner), source.id, reader.id)
    revoked = lab.sources.revoke_access(lab.actor(owner), source.id, reader.id)
    assert revoked.is_active is False
    with pytest.raises(InvalidTransitionError):
        lab.sources.revoke_access(lab.actor(owner), source.id, reader.id)
    open_source, _revision = lab.add_source(owner, content="open")
    with pytest.raises(InvalidTransitionError):
        lab.sources.grant_access(lab.actor(owner), open_source.id, reader.id)
    with pytest.raises(ResourceNotFound):
        lab.sources.grant_access(lab.actor(owner), source.id, outsider.id)
    restored = lab.sources.grant_access(lab.actor(owner), source.id, reader.id)
    assert restored.is_active


def test_membership_lifecycle_and_directory_lookups(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    with pytest.raises(ConflictError):
        lab.directory.grant_membership(
            lab.actor(lab.admin), lab.workspace.id, member.id, WorkspaceRole.MEMBER
        )
    with pytest.raises(ResourceNotFound):
        lab.directory.grant_membership(
            lab.actor(lab.admin), lab.workspace.id, UserId("usr-missing"), WorkspaceRole.VIEWER
        )
    lab.directory.revoke_membership(lab.actor(lab.admin), lab.workspace.id, member.id)
    with pytest.raises(InvalidTransitionError):
        lab.directory.revoke_membership(lab.actor(lab.admin), lab.workspace.id, member.id)
    with pytest.raises(ResourceNotFound):
        lab.directory.revoke_membership(
            lab.actor(lab.admin), lab.workspace.id, UserId("usr-missing")
        )
    restored = lab.directory.grant_membership(
        lab.actor(lab.admin), lab.workspace.id, member.id, WorkspaceRole.VIEWER
    )
    assert restored.state is MembershipState.ACTIVE
    assert restored.role is WorkspaceRole.VIEWER
    with pytest.raises(ResourceNotFound):
        lab.directory.create_workspace(UserId("usr-missing"), "Missing")
    assert lab.directory.user(lab.admin.id).id == lab.admin.id
    assert lab.directory.workspace(lab.workspace.id).name == "Team"
    with pytest.raises(ResourceNotFound):
        lab.directory.user(UserId("usr-missing"))
    with pytest.raises(ResourceNotFound):
        lab.directory.workspace(WorkspaceId("ws-missing"))
    with pytest.raises(ResourceNotFound):
        lab.directory.agent(AgentId("agt-missing"))


def test_instruction_authority_and_agent_revocation(lab: Lab) -> None:
    lead = lab.add_user("Lead", WorkspaceRole.MEMBER)
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    authority = lab.directory.grant_instruction_authority(
        lab.actor(lab.admin), lab.workspace.id, lead.id, member.id
    )
    assert lab.directory.instruction_authorities(lab.workspace.id) == (authority,)
    with pytest.raises(ConflictError):
        lab.directory.grant_instruction_authority(
            lab.actor(lab.admin), lab.workspace.id, lead.id, member.id
        )
    with pytest.raises(DomainValidationError):
        lab.directory.grant_instruction_authority(
            lab.actor(lab.admin), lab.workspace.id, lead.id, lead.id
        )
    outsider = lab.directory.register_user("Outsider")
    with pytest.raises(ResourceNotFound):
        lab.directory.grant_instruction_authority(
            lab.actor(lab.admin), lab.workspace.id, lead.id, outsider.id
        )
    agent = lab.directory.register_agent(
        lab.actor(member),
        lab.workspace.id,
        member.id,
        "Helper",
        frozenset(),
    )
    revoked = lab.directory.revoke_agent(lab.actor(lab.admin), agent.id)
    assert revoked.state is AgentState.REVOKED
    with pytest.raises(InvalidTransitionError):
        lab.directory.revoke_agent(lab.actor(lab.admin), agent.id)
    with pytest.raises(ResourceNotFound):
        lab.directory.revoke_agent(lab.actor(lab.admin), AgentId("agt-missing"))


def test_manifests_labels_and_duplicate_lineage(lab: Lab) -> None:
    started = datetime(2025, 1, 1, tzinfo=UTC)
    manifest = new_manifest(
        run_id=RunId("run-000001"),
        scenario_ref="sf1",
        master_seed=7,
        code_version="phase-2",
        configuration={"fidelity": "LF1.0"},
        started_at=started,
    )
    assert len(manifest.configuration_sha256) == 64
    store = GroundTruthStore(lab.database)
    store.register_run(manifest)
    with store.reader() as reader:
        assert reader.manifest(manifest.run_id).status is RunStatus.RUNNING
        with pytest.raises(ResourceNotFound):
            reader.manifest(RunId("run-missing"))
    finished = store.finish_run(manifest.run_id, RunStatus.COMPLETED)
    assert finished.finished_at is not None
    with pytest.raises(InvalidTransitionError):
        finish_manifest(finished, RunStatus.FAILED, finished.finished_at)
    with pytest.raises(InvalidTransitionError):
        finish_manifest(manifest, RunStatus.RUNNING, started)
    with pytest.raises(ResourceNotFound):
        store.finish_run(RunId("run-missing"), RunStatus.ABORTED)
    source, revision = lab.add_source(lab.admin, content="labeled")
    label = store.label_source(source.id, lab.workspace.id, SourceOrigin.BENIGN)
    with store.reader() as reader:
        assert reader.label(source.id) == label
        with pytest.raises(ResourceNotFound):
            reader.label(SourceId("src-missing"))
    memory = lab.memories.extract(lab.actor(lab.admin), revision.id, "labeled")
    with pytest.raises(ProvenanceIntegrityError) as duplicate:
        lab.memories.derive(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.CONSOLIDATION,
            prompt_version="tt3-v1",
            parent_ids=(memory.id, memory.id),
            content="duplicated parents",
        )
    assert duplicate.value.code is ReasonCode.LINEAGE_MALFORMED
    with pytest.raises(ProvenanceIntegrityError) as empty:
        lab.memories.derive(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.CONSOLIDATION,
            prompt_version="tt3-v1",
            parent_ids=(),
            content="no parents",
        )
    assert empty.value.code is ReasonCode.LINEAGE_MALFORMED


def test_tool_proposal_validation_and_cross_workspace_target(lab: Lab) -> None:
    with pytest.raises(DomainValidationError):
        lab.tools.authorize(
            lab.actor(lab.admin),
            lab.workspace.id,
            stage=ToolStage.PROPOSE,
            tool_name="Not A Tool",
            arguments=(),
            target_source_id=None,
            justification=None,
        )
    with pytest.raises(DomainValidationError):
        lab.tools.authorize(
            lab.actor(lab.admin),
            lab.workspace.id,
            stage=ToolStage.PROPOSE,
            tool_name="share_document",
            arguments=(("recipient", "a@b.invalid"), ("recipient", "c@d.invalid")),
            target_source_id=None,
            justification=None,
        )
    elsewhere, _membership = lab.directory.create_workspace(lab.admin.id, "Elsewhere")
    foreign, _revision = lab.sources.create(
        lab.actor(lab.admin),
        elsewhere.id,
        title="Foreign",
        content="other",
        visibility=SourceVisibility.PRIVATE,
    )
    with pytest.raises(AuthorizationDenied) as crossed:
        lab.tools.authorize(
            PrincipalRef.user(lab.admin.id),
            lab.workspace.id,
            stage=ToolStage.EXECUTE,
            tool_name="share_document",
            arguments=(),
            target_source_id=foreign.id,
            justification=None,
        )
    assert crossed.value.decision.reason is ReasonCode.CROSS_WORKSPACE


def test_clocks_reject_bad_time() -> None:
    assert SystemClock().now().tzinfo is UTC
    with pytest.raises(ValueError, match="positive"):
        StepClock(datetime(2026, 1, 1, tzinfo=UTC), timedelta(0))
    with pytest.raises(ValueError, match="timezone-aware"):
        StepClock(datetime(2026, 1, 1))


def test_database_files_and_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "same.sqlite"
    with pytest.raises(PersistenceError, match="separate files"):
        EpisodeDatabase(
            system_path=path,
            ground_truth_path=path,
            ground_truth_metadata=GroundTruthBase.metadata,
            recorder_factory=SqlGroundTruthRecorder,
            clock=SystemClock(),
        )
    database = EpisodeDatabase(
        system_path=tmp_path / "system.sqlite",
        ground_truth_path=tmp_path / "groundtruth.sqlite",
        ground_truth_metadata=GroundTruthBase.metadata,
        recorder_factory=SqlGroundTruthRecorder,
        clock=SystemClock(),
    )
    database.initialize()
    database.dispose()
    connection = sqlite3.connect(tmp_path / "system.sqlite")
    try:
        connection.execute("UPDATE schema_info SET value = '999' WHERE key = 'schema_version'")
        connection.commit()
    finally:
        connection.close()
    mismatch = EpisodeDatabase(
        system_path=tmp_path / "system.sqlite",
        ground_truth_path=tmp_path / "groundtruth.sqlite",
        ground_truth_metadata=GroundTruthBase.metadata,
        recorder_factory=SqlGroundTruthRecorder,
        clock=SystemClock(),
    )
    with pytest.raises(PersistenceError) as error:
        mismatch.initialize()
    assert error.value.code is ReasonCode.SCHEMA_VERSION_MISMATCH
    mismatch.dispose()
