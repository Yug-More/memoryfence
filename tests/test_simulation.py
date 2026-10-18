"""Phase 3 simulation: ingestion, scripted transforms, retrieval, DS4, and tools."""

import pytest
from sqlalchemy import func, select

from memoryfence.authorization.gateway import ToolGateway
from memoryfence.domain.deletion import DeletionRequest
from memoryfence.domain.enums import (
    DeletionPolicy,
    DeletionScenario,
    LineageFidelity,
    MemoryType,
    MemoryVisibility,
    ModelPurpose,
    RederivationStatus,
    SourceVisibility,
    TransformationType,
    WorkspaceRole,
)
from memoryfence.domain.errors import (
    AuthorizationDenied,
    DomainValidationError,
    ModelScriptError,
    PersistenceError,
    ProvenanceIntegrityError,
    ReasonCode,
    ResourceNotFound,
)
from memoryfence.domain.ids import MemoryId, WorkspaceId
from memoryfence.domain.memories import Memory
from memoryfence.domain.model import ModelRequest
from memoryfence.domain.principals import PrincipalRef, User
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.domain.serialization import sha256_hex
from memoryfence.domain.sources import SourceDocument, SourceRevision
from memoryfence.groundtruth.recorder import SqlGroundTruthRecorder
from memoryfence.groundtruth.schema import GroundTruthBase, TrueLinkRow
from memoryfence.llm.backend import ScriptedBackend, ScriptedReply
from memoryfence.memory.ingest import IngestionService
from memoryfence.memory.rederive import RederivationExecutor
from memoryfence.memory.retrieve import RetrievalService
from memoryfence.memory.transforms import PROMPT_VERSION, TransformService
from memoryfence.observability import Auditor
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.storage.schema import MemoryRow, SourceRevisionRow
from memoryfence.tools.sandbox import Sandbox
from memoryfence.workspace.tools import ToolService
from tests.conftest import DEGRADATION, Lab

ALPHA = "alpha report stays available"
BETA = "beta report is the one removed"
MERGED = "Scripted consolidation of alpha and beta."
ROUND2 = "Scripted reflection over the consolidation."


def _backend(*replies: ScriptedReply, fail_calls: frozenset[int] = frozenset()) -> ScriptedBackend:
    return ScriptedBackend(replies, seed=DEGRADATION.master_seed, fail_calls=fail_calls)


def _reply(
    purpose: ModelPurpose,
    text: str,
    *,
    transformation: TransformationType | None = None,
    hashes: tuple[str, ...] = (),
    task: str | None = None,
    script_id: str = "fixture-v1",
    error: str | None = None,
) -> ScriptedReply:
    return ScriptedReply(
        script_id=script_id,
        purpose=purpose,
        text=text,
        transformation_type=transformation,
        parent_content_hashes=hashes,
        task=task,
        error=error,  # type: ignore[arg-type]
    )


def _transforms(
    lab: Lab, backend: ScriptedBackend, degradation: object = DEGRADATION
) -> TransformService:
    assert isinstance(degradation, ProvenanceDegradationConfiguration)
    return TransformService(
        lab.database, lab.auditor, degradation, backend, seed=DEGRADATION.master_seed
    )


def _ingest(
    lab: Lab, owner: User, content: str, *, title: str = "Notes"
) -> tuple[SourceDocument, SourceRevision, Memory]:
    return IngestionService(lab.auditor).ingest(
        lab.actor(owner),
        lab.workspace.id,
        title=title,
        content=content,
        visibility=SourceVisibility.WORKSPACE,
    )


def test_request_schema_has_no_evaluator_fields() -> None:
    names = set(ModelRequest.model_fields)
    assert "origin" not in names
    assert "label" not in names
    assert "true_provenance" not in names


def test_viewer_cannot_ingest(lab: Lab) -> None:
    viewer = lab.add_user("Viewer", WorkspaceRole.VIEWER)
    with pytest.raises(AuthorizationDenied) as caught:
        IngestionService(lab.auditor).ingest(
            lab.actor(viewer),
            lab.workspace.id,
            title="Nope",
            content="secret",
            visibility=SourceVisibility.WORKSPACE,
        )
    assert caught.value.code is ReasonCode.PERMISSION_NOT_GRANTED
    with lab.database.system_read_session() as session:
        assert session.scalar(select(func.count()).select_from(SourceRevisionRow)) == 0


def test_ingestion_failure_rolls_back_the_source(lab: Lab) -> None:
    class FailingRecorder(SqlGroundTruthRecorder):
        def record_node(self, node: object) -> None:
            raise PersistenceError("injected ingest failure")

    failing = EpisodeDatabase(
        system_path=lab.database.system_path,
        ground_truth_path=lab.database.ground_truth_path,
        ground_truth_metadata=GroundTruthBase.metadata,
        recorder_factory=FailingRecorder,
        clock=lab.database._clock,
    )
    with pytest.raises(PersistenceError, match="injected ingest failure"):
        IngestionService(Auditor(failing)).ingest(
            lab.actor(lab.admin),
            lab.workspace.id,
            title="Rolled back",
            content="must not remain",
            visibility=SourceVisibility.WORKSPACE,
        )
    failing.dispose()
    with lab.database.system_read_session() as session:
        assert session.scalar(select(func.count()).select_from(SourceRevisionRow)) == 0


def test_each_ingest_creates_one_revision(lab: Lab) -> None:
    first, first_revision, _memory = _ingest(lab, lab.admin, "one")
    second, second_revision, _other = _ingest(lab, lab.admin, "two")
    assert first.id != second.id
    assert first_revision.sequence == 1
    assert second_revision.sequence == 1
    with pytest.raises(DomainValidationError):
        IngestionService(lab.auditor).ingest(
            lab.actor(lab.admin),
            lab.workspace.id,
            title="",
            content="x",
            visibility=SourceVisibility.WORKSPACE,
        )


def test_scripted_summary_is_labeled_and_workspace_visible(lab: Lab) -> None:
    _source, _revision, primary = _ingest(lab, lab.admin, ALPHA)
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "Scripted extractive summary of alpha.",
            transformation=TransformationType.EXTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
        )
    )
    derived = _transforms(lab, backend).transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
        parent_ids=(primary.id,),
    )
    assert derived.visibility is MemoryVisibility.WORKSPACE
    assert derived.derivation_round == 1
    assert derived.content.startswith("Scripted extractive summary")
    assert PROMPT_VERSION[TransformationType.EXTRACTIVE_SUMMARY] == "tt1-scripted-v1"
    assert backend.requests[0].parent_content_hashes == (primary.content_sha256,)
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    visible = lab.memories.read(lab.actor(member), derived.id)
    assert visible.id == derived.id


def test_merge_preserves_parent_order_and_second_round(lab: Lab) -> None:
    _a, _ar, alpha = _ingest(lab, lab.admin, ALPHA, title="Alpha")
    _b, _br, beta = _ingest(lab, lab.admin, BETA, title="Beta")
    merged_text = MERGED
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            merged_text,
            transformation=TransformationType.CONSOLIDATION,
            hashes=(alpha.content_sha256, beta.content_sha256),
            script_id="tt3-scripted-v1",
        ),
        _reply(
            ModelPurpose.TRANSFORM,
            ROUND2,
            transformation=TransformationType.REFLECTION,
            hashes=(sha256_hex(merged_text),),
            script_id="tt4-scripted-v1",
        ),
    )
    service = _transforms(lab, backend)
    merged = service.transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.CONSOLIDATION,
        parent_ids=(alpha.id, beta.id),
    )
    reflected = service.transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.REFLECTION,
        parent_ids=(merged.id,),
    )
    assert reflected.derivation_round == 2
    with lab.database.unit_of_work() as unit:
        links = list(
            unit.session.scalars(
                select(TrueLinkRow)
                .where(TrueLinkRow.child_id == merged.id)
                .order_by(TrueLinkRow.ordinal)
            )
        )
    assert [link.parent_id for link in links] == [alpha.id, beta.id]
    assert [link.ordinal for link in links] == [0, 1]


def test_private_parent_keeps_the_derived_memory_private(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    _source, revision = lab.add_source(
        member, content="private alpha note", visibility=SourceVisibility.PRIVATE
    )
    primary = lab.memories.extract(lab.actor(member), revision.id, "private alpha note")
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "Scripted abstractive summary.",
            transformation=TransformationType.ABSTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
            script_id="tt2-scripted-v1",
        )
    )
    derived = _transforms(lab, backend).transform(
        lab.actor(member),
        lab.workspace.id,
        transformation_type=TransformationType.ABSTRACTIVE_SUMMARY,
        parent_ids=(primary.id,),
    )
    assert derived.visibility is MemoryVisibility.PRIVATE
    assert derived.owner_user_id == member.id
    with pytest.raises(AuthorizationDenied) as caught:
        lab.memories.read(lab.actor(lab.admin), derived.id)
    assert caught.value.code is ReasonCode.MEMORY_NOT_VISIBLE


def test_transform_rejects_bad_parents_and_unknown_scripts(lab: Lab) -> None:
    _source, _revision, primary = _ingest(lab, lab.admin, ALPHA)
    service = _transforms(lab, _backend())
    with pytest.raises(ProvenanceIntegrityError) as empty:
        service.transform(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
            parent_ids=(),
        )
    assert empty.value.code is ReasonCode.LINEAGE_MALFORMED
    with pytest.raises(ProvenanceIntegrityError) as duplicate:
        _transforms(
            lab,
            _backend(
                _reply(
                    ModelPurpose.TRANSFORM,
                    "unused",
                    transformation=TransformationType.EXTRACTIVE_SUMMARY,
                    hashes=(primary.content_sha256, primary.content_sha256),
                )
            ),
        ).transform(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
            parent_ids=(primary.id, primary.id),
        )
    assert duplicate.value.code is ReasonCode.LINEAGE_MALFORMED
    with pytest.raises(ResourceNotFound):
        service.transform(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
            parent_ids=(MemoryId("mem-999999"),),
        )
    with pytest.raises(ModelScriptError) as missing:
        service.transform(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
            parent_ids=(primary.id,),
        )
    assert missing.value.code is ReasonCode.SCRIPT_MISS
    with lab.database.system_read_session() as session:
        derived = session.scalar(
            select(func.count())
            .select_from(MemoryRow)
            .where(MemoryRow.memory_type == MemoryType.DERIVED)
        )
    assert derived == 0


def test_cross_workspace_parent_is_rejected(lab: Lab) -> None:
    other, _membership = lab.directory.create_workspace(lab.admin.id, "Other")
    source, revision = lab.sources.create(
        lab.actor(lab.admin),
        other.id,
        title="Elsewhere",
        content=ALPHA,
        visibility=SourceVisibility.WORKSPACE,
    )
    del source
    primary = lab.memories.extract(lab.actor(lab.admin), revision.id, ALPHA)
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "should not be stored",
            transformation=TransformationType.EXTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
        )
    )
    with pytest.raises(ProvenanceIntegrityError) as caught:
        _transforms(lab, backend).transform(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
            parent_ids=(primary.id,),
        )
    assert caught.value.code is ReasonCode.LINEAGE_CROSS_WORKSPACE


def test_revoked_parent_cannot_be_transformed(lab: Lab) -> None:
    source, _revision, primary = _ingest(lab, lab.admin, ALPHA)
    lab.deletion.apply(
        lab.actor(lab.admin),
        DeletionRequest(
            source_id=source.id,
            policy=DeletionPolicy.TOMBSTONE_AND_REVOKE,
            scenario=DeletionScenario.RETENTION,
        ),
    )
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "should not be stored",
            transformation=TransformationType.EXTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
        )
    )
    with pytest.raises(AuthorizationDenied) as caught:
        _transforms(lab, backend).transform(
            lab.actor(lab.admin),
            lab.workspace.id,
            transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
            parent_ids=(primary.id,),
        )
    assert caught.value.code is ReasonCode.MEMORY_REVOKED


def test_retrieval_is_scoped_ranked_and_stable(lab: Lab) -> None:
    _source, _revision, primary = _ingest(lab, lab.admin, "alpha report shared")
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "zeta report shared later",
            transformation=TransformationType.EXTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
        )
    )
    derived = _transforms(lab, backend).transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
        parent_ids=(primary.id,),
    )
    retrieval = RetrievalService(lab.auditor)
    result = retrieval.retrieve(lab.actor(lab.admin), lab.workspace.id, "report shared", top_k=1)
    assert result.rank_basis == "token_overlap"
    assert result.candidate_count == 2
    assert [hit.memory_id for hit in result.hits] == [primary.id]
    assert result.hits[0].score == 2
    both = retrieval.retrieve(lab.actor(lab.admin), lab.workspace.id, "report", top_k=5)
    assert [hit.memory_id for hit in both.hits] == sorted(hit.memory_id for hit in both.hits)
    assert derived.id in {hit.memory_id for hit in both.hits}
    empty = retrieval.retrieve(lab.actor(lab.admin), lab.workspace.id, "", top_k=5)
    assert empty.hits == ()
    outsider = lab.directory.register_user("Outsider")
    with pytest.raises(AuthorizationDenied) as caught:
        retrieval.retrieve(PrincipalRef.user(outsider.id), lab.workspace.id, "report")
    assert caught.value.code is ReasonCode.NOT_A_MEMBER


def test_deletion_changes_what_retrieval_returns(lab: Lab) -> None:
    source, _revision, primary = _ingest(lab, lab.admin, ALPHA)
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "Scripted extractive summary of alpha.",
            transformation=TransformationType.EXTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
        )
    )
    derived = _transforms(lab, backend).transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
        parent_ids=(primary.id,),
    )
    lab.deletion.apply(
        lab.actor(lab.admin),
        DeletionRequest(
            source_id=source.id,
            policy=DeletionPolicy.SOURCE_AND_PRIMARY,
            scenario=DeletionScenario.RETENTION,
        ),
    )
    hits = RetrievalService(lab.auditor).retrieve(lab.actor(lab.admin), lab.workspace.id, "alpha")
    assert [hit.memory_id for hit in hits.hits] == [derived.id]


def test_ds4_executes_surviving_parents_and_skips_dead_ends(lab: Lab) -> None:
    kept, _kr, alpha = _ingest(lab, lab.admin, ALPHA, title="Alpha")
    removed, _rr, beta = _ingest(lab, lab.admin, BETA, title="Beta")
    del kept
    merged_hash = sha256_hex(MERGED)
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            MERGED,
            transformation=TransformationType.CONSOLIDATION,
            hashes=(alpha.content_sha256, beta.content_sha256),
            script_id="tt3-scripted-v1",
        ),
        _reply(
            ModelPurpose.TRANSFORM,
            ROUND2,
            transformation=TransformationType.REFLECTION,
            hashes=(merged_hash,),
            script_id="tt4-scripted-v1",
        ),
        _reply(
            ModelPurpose.TRANSFORM,
            "Regenerated from alpha only.",
            transformation=TransformationType.CONSOLIDATION,
            hashes=(alpha.content_sha256,),
            script_id="tt3-scripted-v1",
        ),
        _reply(
            ModelPurpose.TRANSFORM,
            "Regenerated reflection.",
            transformation=TransformationType.REFLECTION,
            hashes=(sha256_hex("Regenerated from alpha only."),),
            script_id="tt4-scripted-v1",
        ),
    )
    service = _transforms(lab, backend)
    merged = service.transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.CONSOLIDATION,
        parent_ids=(alpha.id, beta.id),
    )
    reflected = service.transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.REFLECTION,
        parent_ids=(merged.id,),
    )
    outcome = lab.deletion.apply(
        lab.actor(lab.admin),
        DeletionRequest(
            source_id=removed.id,
            policy=DeletionPolicy.CASCADE_AND_REDERIVE,
            scenario=DeletionScenario.RETENTION,
        ),
    )
    pending = [
        task for task in outcome.rederivation_tasks if task.status is RederivationStatus.PENDING
    ]
    assert len(pending) == 2
    executor = RederivationExecutor(
        lab.database, lab.auditor, DEGRADATION, backend, seed=DEGRADATION.master_seed
    )
    finished = executor.execute(lab.actor(lab.admin), outcome.deletion_id)
    replacements = [task.replacement_memory_id for task in finished if task.replacement_memory_id]
    assert len(replacements) == 2
    assert reflected.id not in replacements
    again = executor.execute(lab.actor(lab.admin), outcome.deletion_id)
    assert [task.replacement_memory_id for task in again] == [
        task.replacement_memory_id for task in finished
    ]
    calls_after_retry = len(backend.requests)
    executor.execute(lab.actor(lab.admin), outcome.deletion_id)
    assert len(backend.requests) == calls_after_retry


def test_ds4_timeout_retries_and_not_regenerated_skips_the_model(lab: Lab) -> None:
    source, _revision, primary = _ingest(lab, lab.admin, ALPHA)
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "Scripted extractive summary of alpha.",
            transformation=TransformationType.EXTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
        ),
        fail_calls=frozenset({1}),
    )
    derived = _transforms(lab, backend).transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
        parent_ids=(primary.id,),
    )
    outcome = lab.deletion.apply(
        lab.actor(lab.admin),
        DeletionRequest(
            source_id=source.id,
            policy=DeletionPolicy.CASCADE_AND_REDERIVE,
            scenario=DeletionScenario.RETENTION,
        ),
    )
    assert outcome.rederivation_tasks[0].status is RederivationStatus.NOT_REGENERATED
    executor = RederivationExecutor(
        lab.database, lab.auditor, DEGRADATION, backend, seed=DEGRADATION.master_seed
    )
    before = len(backend.requests)
    finished = executor.execute(lab.actor(lab.admin), outcome.deletion_id)
    assert finished[0].status is RederivationStatus.NOT_REGENERATED
    assert len(backend.requests) == before
    assert derived.id not in {task.replacement_memory_id for task in finished}


def test_ds4_retry_after_a_scripted_timeout(lab: Lab) -> None:
    kept_source, _revision, alpha = _ingest(lab, lab.admin, ALPHA, title="Alpha")
    removed, _other, beta = _ingest(lab, lab.admin, BETA, title="Beta")
    del kept_source
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            MERGED,
            transformation=TransformationType.CONSOLIDATION,
            hashes=(alpha.content_sha256, beta.content_sha256),
            script_id="tt3-scripted-v1",
        ),
        _reply(
            ModelPurpose.TRANSFORM,
            "Regenerated from alpha only.",
            transformation=TransformationType.CONSOLIDATION,
            hashes=(alpha.content_sha256,),
            script_id="tt3-scripted-v1",
        ),
        fail_calls=frozenset({1}),
    )
    _transforms(lab, backend).transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.CONSOLIDATION,
        parent_ids=(alpha.id, beta.id),
    )
    outcome = lab.deletion.apply(
        lab.actor(lab.admin),
        DeletionRequest(
            source_id=removed.id,
            policy=DeletionPolicy.CASCADE_AND_REDERIVE,
            scenario=DeletionScenario.RETENTION,
        ),
    )
    executor = RederivationExecutor(
        lab.database, lab.auditor, DEGRADATION, backend, seed=DEGRADATION.master_seed
    )
    with pytest.raises(ModelScriptError) as caught:
        executor.execute(lab.actor(lab.admin), outcome.deletion_id)
    assert caught.value.code is ReasonCode.SCRIPT_TIMEOUT
    finished = executor.execute(lab.actor(lab.admin), outcome.deletion_id)
    assert finished[0].status is RederivationStatus.COMPLETED
    assert finished[0].replacement_memory_id is not None


def test_missing_recorded_edge_is_outside_ds4_reach(lab: Lab) -> None:
    source, _revision, primary = _ingest(lab, lab.admin, ALPHA)
    degradation = ProvenanceDegradationConfiguration(
        fidelity=LineageFidelity.LF0_0,
        master_seed=DEGRADATION.master_seed,
        scenario_template=DEGRADATION.scenario_template,
        payload_variant=DEGRADATION.payload_variant,
        replicate=DEGRADATION.replicate,
    )
    backend = _backend(
        _reply(
            ModelPurpose.TRANSFORM,
            "Scripted extractive summary of alpha.",
            transformation=TransformationType.EXTRACTIVE_SUMMARY,
            hashes=(primary.content_sha256,),
        )
    )
    derived = _transforms(lab, backend, degradation).transform(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.EXTRACTIVE_SUMMARY,
        parent_ids=(primary.id,),
    )
    outcome = lab.deletion.apply(
        lab.actor(lab.admin),
        DeletionRequest(
            source_id=source.id,
            policy=DeletionPolicy.CASCADE_AND_REDERIVE,
            scenario=DeletionScenario.RETENTION,
        ),
    )
    assert outcome.rederivation_tasks == ()
    executor = RederivationExecutor(
        lab.database, lab.auditor, degradation, backend, seed=DEGRADATION.master_seed
    )
    assert executor.execute(lab.actor(lab.admin), outcome.deletion_id) == ()
    assert lab.memories.read(lab.actor(lab.admin), derived.id).content == derived.content


def test_gateway_blocks_an_unknown_tool_after_authorizing_the_proposal(lab: Lab) -> None:
    member = lab.add_user("Member", WorkspaceRole.MEMBER)
    gateway = ToolGateway(ToolService(lab.auditor), Sandbox(lab.auditor))
    denied = gateway.submit(
        lab.actor(member),
        lab.workspace.id,
        "share_document",
        (("recipient", "audit@vendor.invalid"),),
    )
    assert denied.executed is False
    assert denied.propose_reason is ReasonCode.ALLOWED
    assert denied.execute_reason is ReasonCode.UNKNOWN_TOOL
    assert denied.sandbox_record_id is None
    viewer = lab.add_user("Viewer", WorkspaceRole.VIEWER)
    blocked = gateway.submit(lab.actor(viewer), lab.workspace.id, "create_ticket", ())
    assert blocked.executed is False
    assert blocked.propose_reason is ReasonCode.PERMISSION_NOT_GRANTED
    assert blocked.proposal_id is None
    created = gateway.submit(
        lab.actor(member),
        lab.workspace.id,
        "create_ticket",
        (("title", "Review"), ("body", "Ready")),
    )
    assert created.executed is True
    assert created.sandbox_record_id is not None
    updated = gateway.submit(
        lab.actor(member),
        lab.workspace.id,
        "update_task",
        (("ticket_id", "tkt-000001"), ("status", "closed")),
    )
    assert updated.executed is True
    noted = gateway.submit(
        lab.actor(member),
        lab.workspace.id,
        "add_note",
        (("text", "synthetic note"),),
    )
    assert noted.executed is True


def test_scripted_backend_is_deterministic_and_seed_locked() -> None:
    reply = _reply(ModelPurpose.AGENT, "fixed", task="status", script_id="agent-v1")
    first = _backend(reply)
    second = _backend(reply)
    request = ModelRequest(
        purpose=ModelPurpose.AGENT,
        seed=DEGRADATION.master_seed,
        workspace_id=WorkspaceId("ws-000001"),
        task="status",
    )
    assert first.complete(request) == second.complete(request)
    mismatched = ModelRequest(
        purpose=ModelPurpose.AGENT,
        seed=99,
        workspace_id=WorkspaceId("ws-000001"),
        task="status",
    )
    with pytest.raises(ModelScriptError) as caught:
        first.complete(mismatched)
    assert caught.value.code is ReasonCode.SCRIPT_MISS
    timing = _backend(_reply(ModelPurpose.AGENT, "fixed", task="status", error="timeout"))
    with pytest.raises(ModelScriptError) as timeout:
        timing.complete(request)
    assert timeout.value.code is ReasonCode.SCRIPT_TIMEOUT
