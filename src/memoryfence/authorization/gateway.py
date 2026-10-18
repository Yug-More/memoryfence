"""Propose, authorize, and only then execute.

The gateway does not accept a justification. Model text cannot change the decision.
``tool.propose`` and ``tool.execute`` are checked separately. The sandbox then rejects
tool names outside its allowlist even if both permissions were granted.
"""

import re

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import ToolStage
from memoryfence.domain.errors import AuthorizationDenied, ReasonCode
from memoryfence.domain.ids import ProposalIdField, SandboxIdField, SourceId, WorkspaceId
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.tools import ToolName
from memoryfence.tools.sandbox import Sandbox
from memoryfence.workspace.tools import ToolService


class ToolGatewayResult(DomainModel):
    proposal_id: ProposalIdField | None = None
    tool_name: ToolName | None = None
    propose_reason: ReasonCode
    execute_reason: ReasonCode | None = None
    executed: bool = False
    sandbox_record_id: SandboxIdField | None = None


class ToolGateway:
    def __init__(self, tools: ToolService, sandbox: Sandbox) -> None:
        self._tools = tools
        self._sandbox = sandbox

    def submit(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        tool_name: str,
        arguments: tuple[tuple[str, str], ...],
        *,
        target_source_id: SourceId | None = None,
    ) -> ToolGatewayResult:
        try:
            proposed = self._tools.authorize(
                actor,
                workspace_id,
                stage=ToolStage.PROPOSE,
                tool_name=tool_name,
                arguments=arguments,
                target_source_id=target_source_id,
                justification=None,
            )
        except AuthorizationDenied as error:
            return ToolGatewayResult(tool_name=_tool_or_none(tool_name), propose_reason=error.code)
        try:
            self._tools.authorize(
                actor,
                workspace_id,
                stage=ToolStage.EXECUTE,
                tool_name=tool_name,
                arguments=arguments,
                target_source_id=target_source_id,
                justification=None,
            )
        except AuthorizationDenied as error:
            return ToolGatewayResult(
                proposal_id=proposed.proposal_id,
                tool_name=_tool_or_none(tool_name),
                propose_reason=ReasonCode.ALLOWED,
                execute_reason=error.code,
            )
        try:
            effect = self._sandbox.execute(
                actor, workspace_id, proposed.proposal_id, tool_name, arguments
            )
        except AuthorizationDenied as error:
            return ToolGatewayResult(
                proposal_id=proposed.proposal_id,
                tool_name=_tool_or_none(tool_name),
                propose_reason=ReasonCode.ALLOWED,
                execute_reason=error.code,
            )
        return ToolGatewayResult(
            proposal_id=proposed.proposal_id,
            tool_name=effect.tool_name,
            propose_reason=ReasonCode.ALLOWED,
            execute_reason=ReasonCode.ALLOWED,
            executed=True,
            sandbox_record_id=effect.id,
        )


_TOOL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def _tool_or_none(tool_name: str) -> str | None:
    if _TOOL_NAME.fullmatch(tool_name) is None:
        return None
    return tool_name
