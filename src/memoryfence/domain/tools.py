"""Tool proposals and their authorization. Tool execution itself is Phase 3."""

from typing import Annotated, Self

from pydantic import StringConstraints, model_validator

from memoryfence.domain.access import AuthorizationDecision
from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import ToolStage
from memoryfence.domain.ids import ProposalIdField, SourceIdField, WorkspaceIdField
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.time import UtcDatetime

ToolName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$")]
ArgumentName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class ToolArgument(DomainModel):
    name: ArgumentName
    value: Annotated[str, StringConstraints(max_length=10_000)]


class ToolProposal(DomainModel):
    """A structured tool call proposed by a principal.

    ``justification`` is model-generated free text. It is never an input to an
    authorization decision and is not copied into the event log.
    """

    id: ProposalIdField
    workspace_id: WorkspaceIdField
    proposer: PrincipalRef
    tool_name: ToolName
    arguments: tuple[ToolArgument, ...]
    target_source_id: SourceIdField | None
    justification: str | None
    proposed_at: UtcDatetime

    @model_validator(mode="after")
    def _arguments_are_unique(self) -> Self:
        names = [argument.name for argument in self.arguments]
        if len(names) != len(set(names)):
            raise ValueError("tool argument names must be unique")
        return self


class ToolAuthorizationDecision(DomainModel):
    proposal_id: ProposalIdField
    stage: ToolStage
    decision: AuthorizationDecision
