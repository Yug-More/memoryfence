"""One bounded agent step: retrieve, call the backend, authorize, maybe execute.

The acting principal is an argument. Nothing in the model response can replace it.
The loop does not start another step from tool output. ``max_steps`` is the number of
``run`` calls this instance will accept.
"""

from memoryfence.authorization.gateway import ToolGateway, ToolGatewayResult
from memoryfence.defenses.suite import DefenseSuite
from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import EventCategory, ModelPurpose, Operation
from memoryfence.domain.errors import DomainValidationError, MemoryFenceError, ReasonCode
from memoryfence.domain.ids import (
    MemoryIdField,
    ProposalIdField,
    SandboxIdField,
    WorkspaceId,
)
from memoryfence.domain.memories import PromptVersion
from memoryfence.domain.model import ContextMemory, LanguageModel, ModelCallDraft, ModelRequest
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.sources import Content
from memoryfence.domain.tools import ToolName
from memoryfence.memory.calls import ModelCallLog
from memoryfence.memory.retrieve import RetrievalService
from memoryfence.observability import Auditor

_MAX_STEPS = 8


class AgentStep(DomainModel):
    task: str
    retrieved_memory_ids: tuple[MemoryIdField, ...]
    script_id: PromptVersion
    response_text: Content
    proposal_id: ProposalIdField | None
    tool_name: ToolName | None
    propose_reason: ReasonCode | None
    execute_reason: ReasonCode | None
    executed: bool
    sandbox_record_id: SandboxIdField | None
    arguments: tuple[tuple[str, str], ...] = ()


class AgentLoop:
    def __init__(
        self,
        retrieval: RetrievalService,
        backend: LanguageModel,
        gateway: ToolGateway,
        log: ModelCallLog,
        auditor: Auditor,
        *,
        seed: int,
        max_steps: int = 1,
        defense: DefenseSuite | None = None,
    ) -> None:
        if max_steps < 1 or max_steps > _MAX_STEPS:
            raise DomainValidationError("agent step limit must be from 1 to 8")
        self._retrieval = retrieval
        self._backend = backend
        self._gateway = gateway
        self._log = log
        self._auditor = auditor
        self._seed = seed
        self._max_steps = max_steps
        self._used = 0
        self._defense = defense

    def run(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        task: str,
        *,
        top_k: int = 5,
    ) -> AgentStep:
        if not task:
            raise DomainValidationError("an agent task is required")
        if self._used >= self._max_steps:
            raise MemoryFenceError(ReasonCode.STEP_LIMIT, "agent step limit reached")
        self._used += 1
        retrieved = self._retrieval.retrieve(actor, workspace_id, task, top_k=top_k)
        hits = retrieved.hits
        if self._defense is None:
            context = tuple(
                ContextMemory(memory_id=hit.memory_id, content=hit.content) for hit in hits
            )
        else:
            hits = self._defense.filter_retrieval(actor, workspace_id, hits)
            context = self._defense.render_context(actor, workspace_id, hits)
        request = ModelRequest(
            purpose=ModelPurpose.AGENT,
            seed=self._seed,
            workspace_id=workspace_id,
            task=task,
            context=context,
        )
        response = self._backend.complete(request)
        self._log.record(
            actor,
            workspace_id,
            ModelCallDraft(
                purpose=request.purpose,
                seed=request.seed,
                script_id=response.script_id,
                transformation_type=None,
                task=task,
                parent_content_hashes=(),
                context_memory_ids=tuple(item.memory_id for item in context),
                output_text=response.text,
                tool_name=response.tool_name,
                arguments=response.arguments,
            ),
        )
        outcome = _submit(
            self._gateway,
            actor,
            workspace_id,
            response.tool_name,
            response.arguments,
            task=task,
            context_ids=tuple(item.memory_id for item in context),
        )
        step = AgentStep(
            task=task,
            retrieved_memory_ids=tuple(item.memory_id for item in context),
            script_id=response.script_id,
            response_text=response.text,
            arguments=response.arguments,
            proposal_id=outcome.proposal_id,
            tool_name=outcome.tool_name,
            propose_reason=outcome.propose_reason if response.tool_name else None,
            execute_reason=outcome.execute_reason,
            executed=outcome.executed,
            sandbox_record_id=outcome.sandbox_record_id,
        )
        self._record(actor, workspace_id, step)
        return step

    def _record(
        self, actor: PrincipalRef | None, workspace_id: WorkspaceId, step: AgentStep
    ) -> None:
        with self._auditor.operation(
            EventCategory.AGENT,
            Operation.AGENT_STEP,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            scope.details["script_id"] = step.script_id
            scope.details["retrieved_ids"] = step.retrieved_memory_ids
            scope.details["executed"] = step.executed
            if step.tool_name is not None:
                scope.details["tool_name"] = step.tool_name
            if step.proposal_id is not None:
                scope.details["proposal_id"] = step.proposal_id


def _submit(
    gateway: ToolGateway,
    actor: PrincipalRef | None,
    workspace_id: WorkspaceId,
    tool_name: str | None,
    arguments: tuple[tuple[str, str], ...],
    *,
    task: str,
    context_ids: tuple[MemoryIdField, ...],
) -> ToolGatewayResult:
    if tool_name is None:
        return ToolGatewayResult(propose_reason=ReasonCode.OK)
    try:
        return gateway.submit(
            actor,
            workspace_id,
            tool_name,
            arguments,
            task=task,
            context_ids=context_ids,
        )
    except MemoryFenceError as error:
        return ToolGatewayResult(propose_reason=error.code, tool_name=None)
