"""The offline scripted episode and the agent loop around it."""

import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from memoryfence.agents.loop import AgentLoop
from memoryfence.authorization.gateway import ToolGateway
from memoryfence.cli import main
from memoryfence.domain.enums import DeletionPolicy, ModelPurpose
from memoryfence.domain.errors import DomainValidationError, MemoryFenceError, ReasonCode
from memoryfence.domain.model import ModelRequest
from memoryfence.harness.episode import run_demo
from memoryfence.llm.backend import ScriptedBackend, ScriptedReply
from memoryfence.memory.calls import ModelCallLog
from memoryfence.memory.retrieve import RetrievalService
from memoryfence.storage.schema import SandboxEffectRow, SandboxTicketRow
from memoryfence.tools.sandbox import Sandbox
from memoryfence.workspace.tools import ToolService
from tests.conftest import DEGRADATION, Lab


def test_demo_is_reproducible_and_separates_proposal_from_execution(tmp_path: Path) -> None:
    first = run_demo(tmp_path / "one")
    second = run_demo(tmp_path / "two")
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.kind == "scripted-demo"
    assert first.deletion_policy is DeletionPolicy.SOURCE_AND_PRIMARY
    assert first.steps[0].executed is True
    assert first.steps[0].tool_name == "create_ticket"
    assert first.steps[0].retrieved_memory_ids == (first.derived_memory_id,)
    assert first.steps[1].executed is False
    assert first.steps[1].execute_reason is ReasonCode.UNKNOWN_TOOL
    assert first.steps[1].proposal_id is not None
    assert "origin" not in first.model_dump()


def test_cli_demo_prints_canonical_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    directory = tmp_path / "episode"
    assert main(["demo", "--directory", str(directory)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "scripted-demo"
    assert payload["steps"][0]["executed"] is True
    assert payload["steps"][1]["executed"] is False
    again = run_demo(tmp_path / "compare")
    assert payload == again.model_dump(mode="json")


def test_agent_step_limit_and_sandbox_effects(lab: Lab) -> None:
    reply = ScriptedReply(
        script_id="agent-v1",
        purpose=ModelPurpose.AGENT,
        task="status",
        text="No tool is required.",
    )
    backend = ScriptedBackend((reply,), seed=DEGRADATION.master_seed)
    loop = AgentLoop(
        RetrievalService(lab.auditor),
        backend,
        ToolGateway(ToolService(lab.auditor), Sandbox(lab.auditor)),
        ModelCallLog(lab.auditor),
        lab.auditor,
        seed=DEGRADATION.master_seed,
        max_steps=1,
    )
    step = loop.run(lab.actor(lab.admin), lab.workspace.id, "status")
    assert step.executed is False
    assert step.tool_name is None
    with pytest.raises(MemoryFenceError) as caught:
        loop.run(lab.actor(lab.admin), lab.workspace.id, "status")
    assert caught.value.code is ReasonCode.STEP_LIMIT
    with pytest.raises(DomainValidationError):
        AgentLoop(
            RetrievalService(lab.auditor),
            backend,
            ToolGateway(ToolService(lab.auditor), Sandbox(lab.auditor)),
            ModelCallLog(lab.auditor),
            lab.auditor,
            seed=DEGRADATION.master_seed,
            max_steps=0,
        )
    with lab.database.system_read_session() as session:
        assert session.scalar(select(func.count()).select_from(SandboxEffectRow)) == 0
        assert session.scalar(select(func.count()).select_from(SandboxTicketRow)) == 0
    request = ModelRequest(
        purpose=ModelPurpose.AGENT,
        seed=DEGRADATION.master_seed,
        workspace_id=lab.workspace.id,
        task="status",
    )
    assert backend.complete(request).text == "No tool is required."
