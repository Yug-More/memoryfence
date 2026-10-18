"""Tool-proposal and tool-execution authorization.

Decisions use the structured call, the requester, and trusted workspace state. The
proposal's justification is not an input and is not written to the event log. Phase 2
does not execute tools.
"""

from pydantic import ValidationError

from memoryfence.domain.access import AuthorizationDecision, ResourceRef
from memoryfence.domain.enums import EventCategory, Operation, Permission, ResourceKind, ToolStage
from memoryfence.domain.errors import AuthorizationDenied, DomainValidationError, ReasonCode
from memoryfence.domain.ids import IdPrefix, ProposalId, SourceId, WorkspaceId
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.tools import ToolArgument, ToolAuthorizationDecision, ToolProposal
from memoryfence.observability import Auditor
from memoryfence.workspace.authority import Authorizer


class ToolService:
    def __init__(self, auditor: Auditor) -> None:
        self._auditor = auditor

    def authorize(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        *,
        stage: ToolStage,
        tool_name: str,
        arguments: tuple[tuple[str, str], ...],
        target_source_id: SourceId | None,
        justification: str | None,
    ) -> ToolAuthorizationDecision:
        """Allow one stage, or raise :class:`AuthorizationDenied`."""
        permission = (
            Permission.TOOL_PROPOSE if stage is ToolStage.PROPOSE else Permission.TOOL_EXECUTE
        )
        with self._auditor.operation(
            EventCategory.TOOL,
            Operation.TOOL_AUTHORIZE,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            authorizer = Authorizer(scope.uow.session)
            resource = None
            if target_source_id is not None:
                source, resource = authorizer.source(target_source_id, actor)
                if source.workspace_id != workspace_id:
                    raise AuthorizationDenied(
                        AuthorizationDecision(
                            allowed=False,
                            reason=ReasonCode.CROSS_WORKSPACE,
                            permission=permission,
                            principal=actor,
                            workspace_id=workspace_id,
                            resource=ResourceRef(kind=ResourceKind.SOURCE, id=target_source_id),
                        )
                    )
            decision, _facts = authorizer.decide(actor, permission, workspace_id, resource)
            if not decision.allowed or actor is None:
                raise AuthorizationDenied(decision)
            try:
                proposal = ToolProposal(
                    id=ProposalId(scope.uow.next_id(IdPrefix.PROPOSAL)),
                    workspace_id=workspace_id,
                    proposer=actor,
                    tool_name=tool_name,
                    arguments=tuple(
                        ToolArgument(name=name, value=value) for name, value in arguments
                    ),
                    target_source_id=target_source_id,
                    justification=justification,
                    proposed_at=scope.uow.now(),
                )
            except ValidationError:
                raise DomainValidationError("tool proposal is invalid") from None
            scope.resource = ResourceRef(kind=ResourceKind.TOOL_PROPOSAL, id=proposal.id)
            scope.details["stage"] = stage.value
            scope.details["tool_name"] = tool_name
            if target_source_id is not None:
                scope.details["target_source_id"] = target_source_id
            result = ToolAuthorizationDecision(
                proposal_id=proposal.id, stage=stage, decision=decision
            )
        return result
