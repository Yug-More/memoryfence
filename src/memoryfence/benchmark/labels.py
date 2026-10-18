"""Evaluator-only predicates. The agent loop and the system under test do not import this."""

from pydantic import Field

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import SourceOrigin
from memoryfence.domain.tools import ToolName


class EvaluationKey(DomainModel):
    """Written with the fixture. Scoring reads it; defense-facing code does not."""

    scenario_id: str
    version: int = Field(ge=1)
    followed_marker: str = Field(min_length=1, max_length=200)
    unauthorized_tool: ToolName | None = None
    legitimate_tool: ToolName | None = None
    origins: dict[str, SourceOrigin]
    lexical_canary: str | None = None
