"""Containment boundaries and real production-service deterministic workflows."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from memoryfence.defenses.containment import ContainmentGuard, GuardedTransformBackend
from memoryfence.domain.enums import (
    LineageFidelity,
    MemoryVisibility,
    MissingnessMode,
    ModelPurpose,
    TransformationType,
)
from memoryfence.domain.errors import MemoryFenceError
from memoryfence.domain.ids import MemoryId
from memoryfence.domain.model import ContextMemory, ModelRequest
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.evaluation.expanded.cli import export
from memoryfence.evaluation.expanded.dataset import Benchmark, load
from memoryfence.evaluation.expanded.report import summarize
from memoryfence.evaluation.expanded.runner import (
    STRATEGIES,
    ProjectionBackend,
    build,
    fraction,
    run_cell,
    write,
)
from memoryfence.provenance.degradation import retains_edge
from memoryfence.workspace.memories import MemoryService
from tests.conftest import Lab

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "benchmarks/expanded-v1/scenarios.json"


def test_dataset_grouping_and_annotation_rejection() -> None:
    benchmark = load(DATASET)
    assert len(benchmark.scenarios) == 80
    assert len({s.family for s in benchmark.scenarios if s.split == "evaluation"}) == 4
    data = json.loads(DATASET.read_text())
    data["scenarios"][1]["split"] = "evaluation"
    with pytest.raises(ValidationError, match="family leaks"):
        Benchmark.model_validate_json(json.dumps(data))
    data = json.loads(DATASET.read_text())
    data["scenarios"][0]["nodes"][0]["parents"] = ["n0"]
    with pytest.raises(ValidationError, match="parents must exist"):
        Benchmark.model_validate_json(json.dumps(data))
    data = json.loads(DATASET.read_text())
    data["scenarios"][4]["nodes"][0]["parents"] = ["target"]
    with pytest.raises(ValidationError, match="never-exposure"):
        Benchmark.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("marked", [False, True])
def test_mixed_silent_gap_is_not_falsely_certified_complete(lab: Lab, marked: bool) -> None:
    source, revision = lab.add_source(lab.admin, content="untrusted instructions")
    _clean, clean_rev = lab.add_source(lab.admin, content="legitimate fact")
    primary = lab.memories.extract(lab.actor(lab.admin), revision.id, "untrusted instructions")
    clean = lab.memories.extract(lab.actor(lab.admin), clean_rev.id, "legitimate fact")
    # Find a deterministic writer treatment losing only the first parent. No graph
    # mutation or evaluator oracle is used by the defense.
    config = None
    for seed in range(100):
        candidate = ProvenanceDegradationConfiguration(
            fidelity=LineageFidelity.LF0_5,
            missingness=MissingnessMode.MARKED if marked else MissingnessMode.SILENT,
            master_seed=seed,
            scenario_template="guard-test",
            payload_variant="v1",
            replicate=0,
        )
        if not retains_edge(candidate, MemoryId("mem-000003"), primary.id) and retains_edge(
            candidate, MemoryId("mem-000003"), clean.id
        ):
            config = candidate
            break
    assert config is not None
    derived = MemoryService(lab.auditor, config).derive(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.CONSOLIDATION,
        prompt_version="guard-fixture-v1",
        parent_ids=(primary.id, clean.id),
        content="untrusted instructions and legitimate fact",
        visibility=MemoryVisibility.WORKSPACE,
    )
    guard = ContainmentGuard(lab.database, lab.auditor)
    decision = guard.assess(lab.actor(lab.admin), lab.workspace.id, derived.id)
    assert decision.allowed is not marked
    assert decision.reason == ("marked_incomplete" if marked else "no_observed_gap")
    if marked:
        request = ModelRequest(
            purpose=ModelPurpose.TRANSFORM,
            seed=1,
            workspace_id=lab.workspace.id,
            context=(ContextMemory(memory_id=derived.id, content=derived.content),),
        )
        with pytest.raises(MemoryFenceError, match="quarantined"):
            GuardedTransformBackend(ProjectionBackend(), guard, lab.actor(lab.admin)).complete(
                request
            )
    assert source.id


def test_guard_inherits_gap_and_does_not_override_acl(lab: Lab) -> None:
    _source, revision = lab.add_source(lab.admin)
    primary = lab.memories.extract(lab.actor(lab.admin), revision.id, "input")
    partial = MemoryService(
        lab.auditor,
        ProvenanceDegradationConfiguration(
            fidelity=LineageFidelity.LF0_0,
            missingness=MissingnessMode.MARKED,
            master_seed=1,
            scenario_template="mark",
            payload_variant="v1",
            replicate=0,
        ),
    )
    derived = partial.derive(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.ABSTRACTIVE_SUMMARY,
        prompt_version="fixture-v1",
        parent_ids=(primary.id,),
        content="child",
    )
    grandchild = lab.memories.derive(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.REFLECTION,
        prompt_version="fixture-v1",
        parent_ids=(derived.id,),
        content="grandchild",
    )
    guard = ContainmentGuard(lab.database, lab.auditor)
    assert not guard.assess(lab.actor(lab.admin), lab.workspace.id, grandchild.id).allowed
    with pytest.raises(MemoryFenceError):
        guard.assess(None, lab.workspace.id, grandchild.id)


def test_multi_source_rederivation_preserves_utility_and_reports_equivalence(
    tmp_path: Path,
) -> None:
    case = next(s for s in load(DATASET).scenarios if s.id == "exp-v1-f06-attack_complete")
    base = tmp_path / "input"
    base.mkdir()
    build(case, base)
    records = {
        strategy: run_cell(case, strategy, base, tmp_path / strategy) for strategy in STRATEGIES
    }
    assert records["source_only"]["metrics"]["exposure"]
    assert records["cascade"]["metrics"]["benign_retention"]["numerator"] == 0
    assert records["memoryfence"]["metrics"]["benign_retention"]["rate"] == 1
    assert records["memoryfence"]["metrics"] == records["rederive"]["metrics"]
    assert not records["memoryfence"]["metrics"]["exposure"]
    assert records["memoryfence"]["metrics"]["attack_success"] is None
    write(tmp_path / "records.json", list(records.values()))
    write(tmp_path / "manifest.json", {"planned_runs": 7})
    summary = summarize(tmp_path)
    assert summary["valid_runs"] == 7
    assert summary["attack_success"] is None
    write(tmp_path / "records.json", [])
    with pytest.raises(ValueError, match="partial"):
        summarize(tmp_path)


def test_metric_empty_denominator_is_undefined_and_export_refuses_overwrite(tmp_path: Path) -> None:
    assert fraction(0, 0)["rate"] is None
    with pytest.raises(MemoryFenceError, match="invalid"):
        fraction(2, 1)
    directory = tmp_path / "run"
    directory.mkdir()
    (directory / "test.json").write_text("{}")
    output = tmp_path / "evidence.zip.xz"
    export(directory, output)
    with pytest.raises(MemoryFenceError, match="new and outside"):
        export(directory, output)
    with pytest.raises(MemoryFenceError, match="new and outside"):
        export(directory, directory / "nested.zip.xz")


def test_cli_fresh_run_archive_verification_and_metric_tamper(tmp_path: Path) -> None:
    import io
    import lzma
    import runpy
    import zipfile

    from memoryfence.cli import main

    cases = load(DATASET).scenarios
    development = next(s for s in cases if s.id == "exp-v1-f06-attack_complete")
    # A synthetic unit split based on a development graph, not the real held-out
    # scenarios. This exercises execution without inspecting held-out outcomes.
    fixture_eval = next(s for s in cases if s.id == "exp-v1-f10-attack_complete")
    fixture_eval = fixture_eval.model_copy(update={"split": "evaluation"})
    fixture = load(DATASET).model_copy(update={"scenarios": (development, fixture_eval)})
    path = tmp_path / "fixture.json"
    path.write_text(fixture.model_dump_json())
    assert main(["expanded", "validate", "--dataset", str(path)]) == 0
    directory = tmp_path / "run"
    assert main(["expanded", "run", "--dataset", str(path), "--directory", str(directory)]) == 0
    assert main(["expanded", "summarize", "--directory", str(directory)]) == 0
    archive = tmp_path / "study.zip.xz"
    assert (
        main(["expanded", "export", "--directory", str(directory), "--output", str(archive)]) == 0
    )
    verifier = runpy.run_path(str(ROOT / "scripts/research/verify_expanded.py"))["verify"]
    result = verifier(archive)
    assert result["verified_runs"] == 14
    assert result["model_calls"] == 0
    payload = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(lzma.decompress(archive.read_bytes()))) as source,
        zipfile.ZipFile(payload, "w") as changed,
    ):
        for name in source.namelist():
            data = source.read(name)
            if name == "records.json":
                records = json.loads(data)
                records[0]["metrics"]["model_calls"] = 99
                data = json.dumps(records).encode()
            changed.writestr(name, data)
    altered = tmp_path / "altered.zip.xz"
    altered.write_bytes(lzma.compress(payload.getvalue()))
    with pytest.raises(ValueError, match="checkpoint consistency"):
        verifier(altered)


def test_contained_agent_adapter_blocks_a_context_after_source_deletion(lab: Lab) -> None:
    from memoryfence.defenses.containment import ContainedDefense
    from memoryfence.domain.defenses import DefenseConfiguration
    from memoryfence.domain.deletion import DeletionRequest
    from memoryfence.domain.enums import DeletionPolicy, DeletionScenario
    from memoryfence.domain.errors import ReasonCode

    source, revision = lab.add_source(lab.admin)
    primary = lab.memories.extract(lab.actor(lab.admin), revision.id, "task")
    child = lab.memories.derive(
        lab.actor(lab.admin),
        lab.workspace.id,
        transformation_type=TransformationType.ABSTRACTIVE_SUMMARY,
        prompt_version="fixture-v1",
        parent_ids=(primary.id,),
        content="task",
    )
    suite = ContainedDefense(DefenseConfiguration(), lab.auditor, lab.database)
    assert (
        suite.authorize_action(
            lab.actor(lab.admin),
            lab.workspace.id,
            "task",
            "create_ticket",
            (("title", "review"), ("body", "status")),
            (child.id,),
        )
        is ReasonCode.OK
    )
    lab.deletion.apply(
        lab.actor(lab.admin),
        DeletionRequest(
            source_id=source.id,
            policy=DeletionPolicy.SOURCE_AND_PRIMARY,
            scenario=DeletionScenario.ATTACKER,
        ),
    )
    assert (
        suite.authorize_action(
            lab.actor(lab.admin),
            lab.workspace.id,
            "task",
            "create_ticket",
            (("title", "review"), ("body", "status")),
            (child.id,),
        )
        is ReasonCode.DEFENSE_LINEAGE
    )
