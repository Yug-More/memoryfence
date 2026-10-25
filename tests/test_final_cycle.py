"""Finite-study fixtures. These tests never perform model inference."""

import json
import runpy
from pathlib import Path
from typing import Any

import pytest

from memoryfence.domain.enums import DecisionKind, LineageFidelity
from memoryfence.domain.model import ModelRequest, ModelResponse

ROOT = Path(__file__).resolve().parents[1]


def driver() -> dict[str, Any]:
    return runpy.run_path(str(ROOT / "scripts/research/final_cycle.py"))


class FixtureTransform:
    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            script_id="fixture-only", text=request.context[0].content, decision=DecisionKind.RESPOND
        )


def test_final_gate_requires_exact_fresh_grid_and_empty_successes() -> None:
    qualify = driver()["qualified"]
    records = [
        {"family": f, "seed": s, "valid": True, "success": True}
        for f in ("direct", "memory", "response", "empty")
        for s in (751, 752, 753)
    ]
    assert qualify(records)
    records[-1]["success"] = False
    assert not qualify(records)
    records[-1]["success"] = True
    records[-1]["seed"] = 651
    assert not qualify(records)


def test_cached_chain_reuses_exact_text_and_rejects_changed_requests(tmp_path: Path) -> None:
    functions = driver()
    cache: list[dict[str, Any]] = []
    captured = functions["CapturedTransform"](FixtureTransform(), cache)
    ids = functions["build_chain"](
        tmp_path / "actual-fixture", True, 901, LineageFidelity.LF1_0, captured
    )
    assert captured.used == 2
    replay = functions["CapturedTransform"](None, cache)
    fresh_ids = functions["build_chain"](
        tmp_path / "cached-fixture", True, 901, LineageFidelity.LF0_5, replay
    )
    assert ids == fresh_ids
    assert replay.used == 2
    request = ModelRequest.model_validate_json(json.dumps(cache[0]["request"]))
    changed = request.model_copy(update={"seed": 902})
    with pytest.raises(ValueError, match="request mismatch"):
        functions["CapturedTransform"](None, cache).complete(changed)
    with pytest.raises(ValueError, match="exhausted"):
        replay.complete(request)


def test_state_views_pair_deletion_and_filtering_without_agent_calls(tmp_path: Path) -> None:
    functions = driver()
    cache: list[dict[str, Any]] = []
    source = tmp_path / "chain"
    ids = functions["build_chain"](
        source,
        True,
        901,
        LineageFidelity.LF1_0,
        functions["CapturedTransform"](FixtureTransform(), cache),
    )
    query = functions["query"]
    contents = query(source, "select id,content from memories order by id")
    for policy, primary, derived in (("DS0", 1, 2), ("DS1", 0, 2), ("DS3", 0, 0)):
        target = tmp_path / policy
        views = functions["state_branch"](source, target, ids, policy)
        assert len(views) == 2
        assert all(v["active_primary"] == primary and v["active_derived"] == derived for v in views)
        assert views[1]["defense"] == "DF2"
        assert views[1]["retrieved_ids"] == []
        assert len(views[0]["retrieved_ids"]) == primary + derived
        assert query(target, "select count(*) from model_calls where purpose='agent'") == [(0,)]
        assert query(source, "select id,content from memories order by id") == contents
        if policy != "DS0":
            assert query(target, "select count(*) from source_revisions") == [(0,)]
        assert query(target, "select count(*) from recorded_provenance_links") == [(2,)]
    assert json.loads(json.dumps(cache))[0]["response"]["generation"] == "scripted"


def test_full_fixture_study_respects_declared_matrix_and_call_budget(tmp_path: Path) -> None:
    from memoryfence.domain.enums import ModelPurpose

    functions = driver()
    actual_calls = {"transform": 0, "agent": 0}

    class FixtureModel:
        def complete(self, request: ModelRequest) -> ModelResponse:
            if request.purpose is ModelPurpose.TRANSFORM:
                actual_calls["transform"] += 1
                return FixtureTransform().complete(request)
            actual_calls["agent"] += 1
            return ModelResponse(
                script_id="fixture-only",
                text="proposing",
                decision=DecisionKind.PROPOSE,
                tool_name="create_ticket",
                arguments=(("title", "review"), ("body", "status")),
            )

    functions["STUDY"]["backend"] = lambda *args, **kwargs: FixtureModel()
    qualification = tmp_path / "qualification"
    qualification.mkdir()
    records = [
        {"interface": v, "family": f, "seed": s, "valid": True, "success": True}
        for v in ("original", "task-last")
        for f in ("direct", "memory", "response", "empty")
        for s in (751, 752, 753)
    ]
    (qualification / "trials.jsonl").write_text("\n".join(json.dumps(r) for r in records))
    (qualification / "qualification.json").write_text(
        json.dumps(
            {"planned": 24, "gates": {"original": True, "task-last": True}, "selected": "original"}
        )
    )
    root = tmp_path / "study"
    root.mkdir()
    functions["study"](root, qualification)
    states = json.loads((root / "states.json").read_text())
    behaviors = json.loads((root / "behavior.json").read_text())
    assert len(states) == 108
    assert len({r["view_id"] for r in states}) == 108
    assert {r["fidelity"] for r in states} == {"LF1.0", "LF0.75", "LF0.5"}
    assert len(behaviors) == 36
    assert actual_calls == {"transform": 12, "agent": 36}
    assert all(r["success"] for r in behaviors)
