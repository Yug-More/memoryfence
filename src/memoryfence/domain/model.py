"""Model-backend requests and responses.

These types are the only channel a language-model adapter receives. They carry memory
identifiers and content the caller is already allowed to see. They have no field for
attack labels, true provenance, or the deletion ledger.
"""

from typing import Literal, Protocol

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import DecisionKind, ModelPurpose, TransformationType
from memoryfence.domain.ids import MemoryIdField, ModelCallIdField, WorkspaceIdField
from memoryfence.domain.memories import PromptVersion
from memoryfence.domain.sources import Content, Sha256
from memoryfence.domain.time import UtcDatetime
from memoryfence.domain.tools import ToolName


class ContextMemory(DomainModel):
    """One memory placed in a model context. Identity and text only."""

    memory_id: MemoryIdField
    content: Content


class ModelRequest(DomainModel):
    purpose: ModelPurpose
    seed: int
    workspace_id: WorkspaceIdField
    transformation_type: TransformationType | None = None
    parent_content_hashes: tuple[Sha256, ...] = ()
    task: str | None = None
    context: tuple[ContextMemory, ...] = ()


class ModelResponse(DomainModel):
    """Structured output of one backend call.

    ``script_id`` names the fixture or adapter response. It is not evidence that a
    language model produced ``text``.
    """

    script_id: PromptVersion
    text: Content
    tool_name: ToolName | None = None
    arguments: tuple[tuple[str, str], ...] = ()
    decision: DecisionKind | None = None
    generation: Literal["scripted", "ollama"] = "scripted"


class ModelCallDraft(DomainModel):
    """A completed call waiting to be stored inside an existing transaction."""

    purpose: ModelPurpose
    seed: int
    script_id: PromptVersion
    transformation_type: TransformationType | None
    task: str | None
    parent_content_hashes: tuple[Sha256, ...]
    context_memory_ids: tuple[MemoryIdField, ...]
    output_text: Content
    tool_name: ToolName | None
    arguments: tuple[tuple[str, str], ...]


class ModelCallRecord(DomainModel):
    """The persisted copy of one request and response."""

    id: ModelCallIdField
    workspace_id: WorkspaceIdField
    purpose: ModelPurpose
    seed: int
    script_id: PromptVersion
    transformation_type: TransformationType | None
    task: str | None
    parent_content_hashes: tuple[Sha256, ...]
    context_memory_ids: tuple[MemoryIdField, ...]
    output_text: Content
    tool_name: ToolName | None
    arguments: tuple[tuple[str, str], ...]
    created_at: UtcDatetime


class LanguageModel(Protocol):
    """Adapter boundary for Phase 7 model backends.

    Implementations must not read evaluator-only ground truth. A scripted backend
    selects an explicit fixture; it does not infer a response from keywords.
    """

    def complete(self, request: ModelRequest) -> ModelResponse: ...
