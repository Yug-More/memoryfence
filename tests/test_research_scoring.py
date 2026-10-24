"""Objective predicates must distinguish harmless tools from attacker objectives."""

from pathlib import Path

from memoryfence.benchmark.catalog import load_scenario
from memoryfence.benchmark.runner import run_case
from memoryfence.domain.enums import ModelPurpose
from memoryfence.llm.backend import ScriptedBackend, ScriptedReply


def test_same_tool_with_wrong_arguments_is_not_an_attack_success(tmp_path: Path) -> None:
    spec, key = load_scenario("executed-proposal")
    harmless = ScriptedBackend(
        (
            ScriptedReply(
                script_id="unrelated-ticket",
                purpose=ModelPurpose.AGENT,
                task=spec.actions[0].task,
                text="A harmless ticket.",
                tool_name="create_ticket",
                arguments=(("title", "Other"), ("body", "Unrelated")),
            ),
        ),
        seed=spec.seed,
    )
    result = run_case(spec, key, tmp_path / "case", code_version="test", agent_backend=harmless)
    assert result.stages is not None
    assert not result.stages.proposed
    assert not result.stages.executed
    assert not result.confirmatory


def test_matched_ticket_pilot_controls_and_objective(tmp_path: Path) -> None:
    from memoryfence.evaluation.config import load_config
    from memoryfence.evaluation.matrix import build_matrix

    config = load_config(Path("configs/ollama-ticket-pilot.json"))
    assert build_matrix(config).valid_count == 24
    for name, attacked, useful in (
        ("pilot-ticket-attack", True, False),
        ("pilot-ticket-clean", False, False),
        ("pilot-ticket-utility", False, True),
    ):
        spec, key = load_scenario(name)
        result = run_case(spec, key, tmp_path / name, code_version="test")
        assert result.stages is not None
        assert result.stages.executed is attacked
        assert result.legitimate_task is useful
        if attacked:
            assert key.lexical_canary is not None
            assert key.lexical_canary in spec.sources[0].content
            assert dict(key.unauthorized_arguments)["body"] == key.lexical_canary
