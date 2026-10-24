"""Scripted experiment runner. Counts are fixture calculations, not model findings."""

import json
from pathlib import Path

import pytest

from memoryfence.benchmark.catalog import list_scenarios, load_scenario
from memoryfence.cli import main
from memoryfence.domain.enums import DeletionPolicy, LineageFidelity
from memoryfence.domain.errors import DomainValidationError
from memoryfence.evaluation.config import ExperimentConfig, smoke_config
from memoryfence.evaluation.hypotheses import hypothesis_links
from memoryfence.evaluation.matrix import build_matrix, require_run_limit
from memoryfence.evaluation.metrics import StageCounts, rates
from memoryfence.evaluation.report import write_summary
from memoryfence.evaluation.runner import execute, export_json, load_records, verify
from memoryfence.evaluation.stats import holm, mcnemar_exact, paired_risk_difference, wilson


def test_wilson_zero_denominator_and_mcnemar() -> None:
    empty = wilson(0, 0)
    assert empty.undefined is True
    assert empty.point is None
    full = wilson(2, 2)
    assert full.point == 1
    assert full.lower is not None
    assert full.lower < 1
    assert mcnemar_exact(0, 2) == 0.5
    assert holm((0.01, 0.04)) == (0.02, 0.04)
    conditional = rates(
        StageCounts(
            trials=2,
            retrieved=0,
            followed=0,
            proposed=0,
            executed=0,
            legitimate_trials=0,
            legitimate_completed=0,
            invalid=1,
        )
    )
    assert conditional.executed.point == 0
    assert conditional.followed_given_retrieved.undefined is True


def test_development_catalog_cannot_load_heldout_templates() -> None:
    ids = {spec.id for spec in list_scenarios()}
    assert "heldout-clean" not in ids
    with pytest.raises(DomainValidationError):
        load_scenario("heldout-clean")


def test_matrix_reports_exclusions_and_refuses_an_oversized_block() -> None:
    config = ExperimentConfig(
        experiment_id="too-wide",
        version=1,
        block="e3",
        split="development",
        scenarios=("clean-note",),
        defenses=(smoke_config().defenses[0],),
        deletion_policies=(DeletionPolicy.NO_DELETION,),
        fidelities=(LineageFidelity.LF1_0,),
        max_runs=1,
    )
    matrix = build_matrix(config)
    assert matrix.candidates > matrix.valid_count
    assert matrix.exclusions
    with pytest.raises(DomainValidationError):
        require_run_limit(config, matrix)


def test_smoke_experiment_resumes_and_verifies(tmp_path: Path) -> None:
    directory = tmp_path / "exp"
    first = execute(smoke_config(), directory, resume=False)
    second = execute(smoke_config(), directory, resume=True)
    assert first[0].status == "completed"
    assert second[0].status == "completed"
    assert first[0].ordinal == second[0].ordinal
    summary = write_summary(directory)
    assert summary.exists()
    assert "not language-model attack rates" in (directory / "report.md").read_text()
    assert verify(directory, tmp_path / "scratch") is True
    links = {link.hypothesis_id: link.status for link in hypothesis_links()}
    assert links["H1"] == "not_computable"
    assert links["H4"] == "not_computable"
    assert links["H3a"] == "procedure_available"


def test_evaluation_split_uses_heldout_templates(tmp_path: Path) -> None:
    config = ExperimentConfig(
        experiment_id="heldout-check",
        version=1,
        block="custom",
        split="evaluation",
        scenarios=("heldout-clean",),
        defenses=smoke_config().defenses,
        deletion_policies=(DeletionPolicy.NO_DELETION,),
        fidelities=(LineageFidelity.LF1_0,),
        max_runs=1,
    )
    records = execute(config, tmp_path / "heldout", resume=False)
    assert records[0].status == "completed"
    assert records[0].control == "C-CLEAN"
    with pytest.raises(DomainValidationError):
        build_matrix(config.model_copy(update={"block": "e3", "experiment_id": "heldout-e3"}))


def test_experiment_cli_smoke(tmp_path: Path) -> None:
    directory = tmp_path / "cli"
    assert main(["experiment", "smoke", "--directory", str(directory)]) == 0
    assert main(["experiment", "status", "--directory", str(directory)]) == 0
    assert main(["experiment", "summarize", "--directory", str(directory)]) == 0
    assert main(["experiment", "verify", "--directory", str(directory)]) == 0
    records = load_records(directory)
    assert records[0].scenario_id == "clean-note"
    config_path = tmp_path / "wide.json"
    config_path.write_text(
        json.dumps(
            {
                "experiment_id": "wide",
                "version": 1,
                "block": "custom",
                "split": "development",
                "scenarios": ["clean-note"],
                "defenses": [{"defense": "DF0"}],
                "deletion_policies": ["DS1"],
                "fidelities": ["LF1.0"],
                "max_runs": 1,
            }
        ),
        encoding="utf-8",
    )
    assert main(["experiment", "validate", "--config", str(config_path)]) == 0
    preview = main(["experiment", "preview", "--config", str(config_path)])
    assert preview == 0
    assert main(["experiment", "export", "--directory", str(directory)]) == 0


def test_reference_counts_invalid_runs_and_resume(tmp_path: Path) -> None:
    with pytest.raises(DomainValidationError):
        wilson(-1, 1)
    with pytest.raises(DomainValidationError):
        mcnemar_exact(-1, 0)
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(1, 1) == 1.0
    undefined = paired_risk_difference(0, 0, 0)
    assert undefined.undefined is True
    difference = paired_risk_difference(1, 0, 2)
    assert difference.point == 0.5
    with pytest.raises(DomainValidationError):
        paired_risk_difference(2, 1, 2)
    with pytest.raises(DomainValidationError):
        holm((1.5,))
    assert holm(()) == ()

    failed = ExperimentConfig(
        experiment_id="timeout-cell",
        version=1,
        block="custom",
        split="development",
        scenarios=("script-timeout",),
        defenses=smoke_config().defenses,
        deletion_policies=(DeletionPolicy.NO_DELETION,),
        fidelities=(LineageFidelity.LF1_0,),
        max_runs=1,
    )
    directory = tmp_path / "timeout"
    records = execute(failed, directory, resume=False)
    assert records[0].status == "invalid"
    write_summary(directory)
    assert "Wilson interval is undefined" in (directory / "report.md").read_text()
    assert "script-timeout" in export_json(directory)

    smoke_dir = tmp_path / "resume"
    execute(smoke_config(), smoke_dir, resume=False)
    result = smoke_dir / "runs" / "0001" / "benchmark-result.json"
    result.unlink()
    with pytest.raises(DomainValidationError):
        execute(smoke_config(), smoke_dir, resume=False)
    resumed = execute(smoke_config(), smoke_dir, resume=True)
    assert resumed[0].status == "completed"
    other = smoke_config().model_copy(update={"experiment_id": "other-smoke"})
    with pytest.raises(DomainValidationError):
        execute(other, smoke_dir, resume=False)


def test_resume_preserves_manifest_and_interrupted_evidence(tmp_path: Path) -> None:
    directory = tmp_path / "exp"
    execute(smoke_config(), directory, resume=False)
    manifest = (directory / "experiment.json").read_bytes()
    run = directory / "runs" / "0001"
    (run / "benchmark-result.json").unlink()
    original_events = (run / "events.jsonl").read_bytes()
    execute(smoke_config(), directory, resume=True)
    assert (directory / "experiment.json").read_bytes() == manifest
    archived = directory / "interrupted" / "0001" / "attempt-0001"
    assert (archived / "events.jsonl").read_bytes() == original_events


def test_audit_detects_record_and_result_tampering(tmp_path: Path) -> None:
    from memoryfence.evaluation.runner import audit

    directory = tmp_path / "exp"
    execute(smoke_config(), directory, resume=False)
    assert audit(directory)
    records_path = directory / "runs.jsonl"
    records = records_path.read_text()
    records_path.write_text("")
    assert not audit(directory)
    records_path.write_text(records)
    result_path = directory / "runs" / "0001" / "benchmark-result.json"
    result = json.loads(result_path.read_text())
    result["legitimate_task"] = not result["legitimate_task"]
    result_path.write_text(json.dumps(result))
    assert not audit(directory)


def test_summary_handles_nonnested_stages_and_abstentions(tmp_path: Path) -> None:
    from memoryfence.evaluation.runner import RunRecord

    directory = tmp_path / "exp"
    execute(smoke_config(), directory, resume=False)
    record = load_records(directory)[0]
    changed = record.model_copy(
        update={
            "retrieved": False,
            "followed": False,
            "proposed": True,
            "executed": True,
            "judge_status": "abstain",
        }
    )
    (directory / "runs.jsonl").write_text(changed.model_dump_json() + "\n")
    write_summary(directory)
    summary = json.loads((directory / "summary.json").read_text())
    assert summary["followed"]["undefined"]
    assert summary["proposed_given_followed"]["undefined"]
    assert summary["executed_given_proposed"]["point"] == 1
    groups = json.loads((directory / "condition-summary.json").read_text())
    assert next(iter(groups.values()))["population"] == "control"
    assert RunRecord.model_validate_json(changed.model_dump_json()).judge_status == "abstain"
