"""Qualification checks are fixtures, never genuine inference evidence."""

import json
import runpy
from pathlib import Path
from typing import Any

import pytest

from memoryfence.benchmark.runner import run_case
from memoryfence.domain.enums import ModelPurpose
from memoryfence.llm.backend import ScriptedBackend, ScriptedReply

DRIVER = Path(__file__).resolve().parents[1] / "scripts" / "research" / "study.py"


def driver() -> dict[str, Any]:
    return runpy.run_path(str(DRIVER))


def test_qualification_gate_preserves_failed_and_missing_trials() -> None:
    qualify = driver()["qualified"]
    records = [
        {"family": f, "seed": s, "valid": True, "success": True}
        for f in ("direct", "memory", "response")
        for s in (151, 152, 153)
    ]
    assert qualify(records)
    records[0]["success"] = False
    assert qualify(records)
    records[1]["success"] = False
    assert not qualify(records)
    records[1]["success"] = True
    records[0]["valid"] = False
    assert not qualify(records)
    records[0]["valid"] = True
    assert not qualify(records[:-1])
    records[-1] = records[0]
    assert not qualify(records)


def test_interface_ablations_change_one_factor_without_mutating_input() -> None:
    alter = driver()["alter_body"]
    body: dict[str, Any] = {
        "messages": [{"content": "system"}, {"content": "task"}, {"content": "memory"}],
        "tools": ["tool"],
        "format": {"type": "object"},
        "options": {"num_ctx": 2048, "num_predict": 256},
    }
    original = json.loads(json.dumps(body))
    last = alter(body, "task-last")
    assert last["messages"] == [body["messages"][0], body["messages"][2], body["messages"][1]]
    for variant, changed in (
        ("example", "messages"),
        ("no-tools", "tools"),
        ("context-4096", "options"),
        ("output-512", "options"),
    ):
        result = alter(body, variant)
        assert {key for key in body if result.get(key) != body[key]} == {changed}
    assert body == original
    with pytest.raises(ValueError, match="Unknown"):
        alter(body, "combined")


@pytest.mark.parametrize(("body", "expected"), [("status", True), ("relay@vendor.invalid", False)])
def test_qualification_requires_exact_executed_utility(
    tmp_path: Path, body: str, expected: bool
) -> None:
    spec, key = driver()["case"]("direct", 151)
    scripted = ScriptedBackend(
        (
            ScriptedReply(
                purpose=ModelPurpose.AGENT,
                script_id="qualification-fixture",
                text="proposing",
                tool_name="create_ticket",
                arguments=(("title", "review"), ("body", body)),
            ),
        ),
        seed=151,
    )
    result = run_case(
        spec, key, tmp_path / "episode", code_version="fixture", agent_backend=scripted
    )
    assert result.legitimate_task is expected
    assert result.stages is not None
    assert result.stages.executed is (not expected)


def test_lifecycle_spec_pairs_keep_task_and_predicates_constant() -> None:
    load = driver()["lifecycle_case"]
    for stage in ("direct", "summary", "consolidation", "deleted-ds1", "deleted-ds3"):
        clean, clean_key = load(stage, False, 251)
        attack, attack_key = load(stage, True, 251)
        assert clean.actions == attack.actions
        assert clean_key.legitimate_arguments == attack_key.legitimate_arguments
        assert clean_key.unauthorized_arguments == attack_key.unauthorized_arguments
        assert clean.deletion_policy == attack.deletion_policy
        assert len(clean.transforms) == len(attack.transforms)


def test_episode_records_text_control_without_counting_it_as_tool_utility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    functions = driver()
    episode = functions["episode"]
    fixture = ScriptedBackend(
        (ScriptedReply(purpose=ModelPurpose.AGENT, script_id="text-fixture", text="ready"),),
        seed=151,
    )
    monkeypatch.setitem(episode.__globals__, "backend", lambda *args: fixture)
    spec, key = functions["case"]("response", 151)
    record = episode(tmp_path, 1, spec, key, "fixture", "original", "test-only")
    assert record["valid"]
    assert record["success"]
    assert record["result"]["legitimate_task"] is False
    assert json.loads((tmp_path / "trial-0001" / "trial.json").read_text()) == record
    with pytest.raises(FileExistsError, match="Refusing"):
        episode(tmp_path, 1, spec, key, "fixture", "original", "test-only")
