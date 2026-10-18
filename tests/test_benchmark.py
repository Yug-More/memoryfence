"""Scripted scenario benchmark. Outcomes are fixtures, not model measurements."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from memoryfence.benchmark.catalog import list_scenarios, load_scenario, validate_catalog
from memoryfence.benchmark.result import canonical_events, canonical_outcome
from memoryfence.benchmark.runner import load_events, replay, run_scenario
from memoryfence.benchmark.spec import CONTROLS, FAMILIES, PROTOCOL_FAMILIES, ScenarioSpec
from memoryfence.cli import main
from memoryfence.domain.enums import DeletionPolicy, LineageFidelity
from memoryfence.domain.errors import DomainValidationError


def test_catalog_is_versioned_and_covers_families() -> None:
    validate_catalog()
    specs = list_scenarios()
    assert len(specs) >= 16
    assert {spec.family for spec in specs} == set(FAMILIES)
    protocols = {spec.protocol_family for spec in specs if spec.protocol_family}
    assert protocols == set(PROTOCOL_FAMILIES)
    assert {spec.control for spec in specs if spec.control} == set(CONTROLS)
    assert all(spec.version >= 1 for spec in specs)
    public = specs[0].model_dump()
    assert "origins" not in public
    assert "followed_marker" not in public
    with pytest.raises(ValidationError):
        ScenarioSpec.model_validate({"id": "not a scenario"})


def test_stages_stay_separate_and_clean_controls_do_not_execute_the_attack(tmp_path: Path) -> None:
    direct = run_scenario("direct-note", tmp_path / "direct", code_version="test")
    withheld = run_scenario("retrieved-not-followed", tmp_path / "withheld", code_version="test")
    executed = run_scenario("executed-proposal", tmp_path / "executed", code_version="test")
    separated = run_scenario("separated-proposal", tmp_path / "separated", code_version="test")
    clean = run_scenario("clean-note", tmp_path / "clean", code_version="test")
    assert direct.stages is not None
    assert direct.stages.model_dump() == {
        "retrieved": True,
        "followed": True,
        "proposed": True,
        "executed": False,
    }
    assert withheld.stages is not None
    assert withheld.stages.retrieved
    assert not withheld.stages.followed
    assert executed.stages is not None
    assert executed.stages.executed
    assert separated.stages is not None
    assert separated.stages.proposed
    assert not separated.stages.executed
    assert separated.legitimate_task is True
    assert clean.stages is not None
    assert clean.stages.model_dump() == {
        "retrieved": False,
        "followed": False,
        "proposed": False,
        "executed": False,
    }
    assert clean.legitimate_task is True
    assert clean.confirmatory is True


def test_transformation_and_cross_user_fixtures(tmp_path: Path) -> None:
    summary = run_scenario("summary-note", tmp_path / "summary", code_version="test")
    merged = run_scenario("merged-notes", tmp_path / "merged", code_version="test")
    rounds = run_scenario("multi-round", tmp_path / "rounds", code_version="test")
    cross = run_scenario("cross-user", tmp_path / "cross", code_version="test")
    assert summary.transformation_chain == ("TT1",)
    assert merged.transformation_chain == ("TT3",)
    assert rounds.transformation_chain == ("TT1", "TT4")
    for result in (summary, merged, rounds, cross):
        assert result.stages is not None
        assert result.stages.retrieved
        assert result.failure_reason is None
    assert "origin" not in summary.model_dump()


def test_deletion_policies_and_fidelity(tmp_path: Path) -> None:
    retrieved: dict[str, bool] = {}
    for policy in DeletionPolicy:
        result = run_scenario(
            "post-deletion",
            tmp_path / policy.value,
            policy=policy,
            code_version="test",
        )
        assert result.stages is not None
        assert result.deletion_policy is policy
        retrieved[policy.value] = result.stages.retrieved
    assert retrieved["DS0"] is True
    assert retrieved["DS1"] is True
    assert retrieved["DS2"] is False
    assert retrieved["DS3"] is False
    assert retrieved["DS4"] is False
    complete = run_scenario(
        "post-deletion",
        tmp_path / "lf-complete",
        policy=DeletionPolicy.CASCADE,
        fidelity=LineageFidelity.LF1_0,
        code_version="test",
    )
    absent = run_scenario(
        "post-deletion",
        tmp_path / "lf-absent",
        policy=DeletionPolicy.CASCADE,
        fidelity=LineageFidelity.LF0_0,
        code_version="test",
    )
    marked = run_scenario(
        "post-deletion",
        tmp_path / "marked",
        marked=True,
        code_version="test",
    )
    assert complete.stages is not None
    assert absent.stages is not None
    assert complete.stages.retrieved is False
    assert absent.stages.retrieved is True
    assert marked.confirmatory is False
    assert marked.missingness.value == "marked"


def test_controls_predeletion_and_failed_run(tmp_path: Path) -> None:
    facts = run_scenario("facts-only", tmp_path / "facts", code_version="test")
    predel = run_scenario("pre-deletion", tmp_path / "pre", code_version="test")
    failed = run_scenario("script-timeout", tmp_path / "timeout", code_version="test")
    assert facts.stages is not None
    assert facts.stages.retrieved
    assert not facts.stages.proposed
    assert predel.stages is not None
    assert not predel.stages.retrieved
    assert failed.stages is None
    assert failed.failure_reason == "error.script_timeout"
    assert failed.legitimate_task is False


def test_replay_is_deterministic_and_runs_are_isolated(tmp_path: Path) -> None:
    first = run_scenario("summary-note", tmp_path / "one", code_version="abc")
    second = run_scenario("summary-note", tmp_path / "two", code_version="xyz")
    assert canonical_outcome(first) == canonical_outcome(second)
    left = canonical_events(load_events(tmp_path / "one"))
    right = canonical_events(load_events(tmp_path / "two"))
    assert left == right
    _previous, fresh = replay(tmp_path / "one", tmp_path / "three", code_version="xyz")
    assert canonical_outcome(first) == canonical_outcome(fresh)
    other = run_scenario("clean-note", tmp_path / "other", code_version="abc")
    assert other.scenario_id != first.scenario_id
    assert (tmp_path / "one" / "system.sqlite").is_file()
    assert (tmp_path / "other" / "system.sqlite").is_file()


def test_export_hides_evaluation_keys_and_cli_round_trip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory = tmp_path / "episode"
    assert main(["benchmark", "validate"]) == 0
    assert "valid" in capsys.readouterr().out
    assert main(["benchmark", "list"]) == 0
    assert "direct-note" in capsys.readouterr().out
    assert (
        main(
            [
                "benchmark",
                "run",
                "--scenario",
                "direct-note",
                "--directory",
                str(directory),
                "--code-version",
                "test",
            ]
        )
        == 0
    )
    exported = capsys.readouterr().out
    assert "followed_marker" not in exported
    assert "origins" not in exported
    assert main(["benchmark", "inspect", "--directory", str(directory)]) == 0
    assert "direct-note" in capsys.readouterr().out
    assert main(["benchmark", "export", "--directory", str(directory)]) == 0
    body = capsys.readouterr().out
    payload = json.loads(body.splitlines()[0])
    assert payload["kind"] == "scripted-benchmark"
    assert "events" in body
    assert (
        main(
            [
                "benchmark",
                "replay",
                "--directory",
                str(directory),
                "--into",
                str(tmp_path / "replay"),
                "--code-version",
                "test",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["equivalent"] is True
    missing = main(
        ["benchmark", "run", "--scenario", "missing", "--directory", str(tmp_path / "nope")]
    )
    assert missing == 2
    spec, key = load_scenario("direct-note")
    assert key.scenario_id == spec.id
    with pytest.raises(DomainValidationError):
        run_scenario("missing", tmp_path / "bad", code_version="test")
