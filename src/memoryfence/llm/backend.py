"""Fixture-driven backend behind :class:`~memoryfence.domain.model.LanguageModel`.

A reply matches a request by equality on purpose and on every field the fixture sets.
The first match wins. There is no keyword fallback. An unknown request fails closed.
"""

from typing import Literal

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import ModelPurpose, TransformationType
from memoryfence.domain.errors import ModelScriptError
from memoryfence.domain.memories import PromptVersion
from memoryfence.domain.model import ModelRequest, ModelResponse
from memoryfence.domain.sources import Content, Sha256
from memoryfence.domain.tools import ToolName


class ScriptedReply(DomainModel):
    """One explicit response. Unset match fields are wildcards; set fields must be equal."""

    script_id: PromptVersion
    purpose: ModelPurpose
    text: Content
    transformation_type: TransformationType | None = None
    parent_content_hashes: tuple[Sha256, ...] = ()
    task: str | None = None
    tool_name: ToolName | None = None
    arguments: tuple[tuple[str, str], ...] = ()
    error: Literal["timeout"] | None = None
    seed: int | None = None


class ScriptedBackend:
    """Selects a :class:`ScriptedReply`. ``seed`` is recorded and must match the request.

    The seed does not sample a response. Two runs with the same fixtures, seed, and
    requests return the same responses in the same order.
    """

    def __init__(
        self,
        replies: tuple[ScriptedReply, ...],
        *,
        seed: int,
        fail_calls: frozenset[int] = frozenset(),
    ) -> None:
        self._replies = replies
        self.seed = seed
        self._fail_calls = fail_calls
        self.requests: list[ModelRequest] = []

    def complete(self, request: ModelRequest) -> ModelResponse:
        index = len(self.requests)
        self.requests.append(request)
        if request.seed != self.seed:
            raise ModelScriptError("request seed does not match the backend seed")
        if index in self._fail_calls:
            raise ModelScriptError("scripted timeout", timeout=True)
        for reply in self._replies:
            if _matches(reply, request):
                if reply.error == "timeout":
                    raise ModelScriptError("scripted timeout", timeout=True)
                return ModelResponse(
                    script_id=reply.script_id,
                    text=reply.text,
                    tool_name=reply.tool_name,
                    arguments=reply.arguments,
                )
        raise ModelScriptError("no scripted response for this request")


def _matches(reply: ScriptedReply, request: ModelRequest) -> bool:
    if reply.purpose is not request.purpose:
        return False
    if reply.seed is not None and reply.seed != request.seed:
        return False
    if reply.transformation_type is not None and reply.transformation_type is not (
        request.transformation_type
    ):
        return False
    hashes = reply.parent_content_hashes
    if hashes and hashes != request.parent_content_hashes:
        return False
    return reply.task is None or reply.task == request.task
