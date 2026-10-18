"""Scripted TT1-TT4 transformations.

``TT0`` is the absence of a transformation: the primary memory is retrieved as stored.
These functions do not call a language model. The text comes from an explicit fixture.
"""

from memoryfence.domain.enums import (
    MemoryVisibility,
    ModelPurpose,
    SourceDeletionState,
    SourceVisibility,
    TransformationType,
)
from memoryfence.domain.errors import ProvenanceIntegrityError, ReasonCode
from memoryfence.domain.ids import MemoryId, TaskId, WorkspaceId
from memoryfence.domain.memories import Memory
from memoryfence.domain.model import LanguageModel, ModelCallDraft, ModelRequest
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.observability import Auditor
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.storage.schema import SourceRevisionRow, SourceRow
from memoryfence.workspace.memories import MemoryService

PROMPT_VERSION: dict[TransformationType, str] = {
    TransformationType.EXTRACTIVE_SUMMARY: "tt1-scripted-v1",
    TransformationType.ABSTRACTIVE_SUMMARY: "tt2-scripted-v1",
    TransformationType.CONSOLIDATION: "tt3-scripted-v1",
    TransformationType.REFLECTION: "tt4-scripted-v1",
}


class TransformService:
    """Apply one scripted transformation and store the derived memory."""

    def __init__(
        self,
        database: EpisodeDatabase,
        auditor: Auditor,
        degradation: ProvenanceDegradationConfiguration,
        backend: LanguageModel,
        *,
        seed: int,
    ) -> None:
        self._database = database
        self._memories = MemoryService(auditor, degradation)
        self._backend = backend
        self._seed = seed

    def transform(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        *,
        transformation_type: TransformationType,
        parent_ids: tuple[MemoryId, ...],
        complete_task_id: TaskId | None = None,
    ) -> Memory:
        """Read the parents, select a fixture, and persist one derived memory.

        The derived memory is workspace-visible only when every parent is. Otherwise
        it is private to the acting user. The fixture is matched on parent content
        hashes in parent order, never on evaluator labels.
        """
        if not parent_ids:
            raise ProvenanceIntegrityError(
                ReasonCode.LINEAGE_MALFORMED, "a transformation needs at least one parent"
            )
        parents = tuple(self._memories.read(actor, parent_id) for parent_id in parent_ids)
        for parent in parents:
            if parent.workspace_id != workspace_id:
                raise ProvenanceIntegrityError(
                    ReasonCode.LINEAGE_CROSS_WORKSPACE,
                    f"parent {parent.id} belongs to another workspace",
                )
        request = ModelRequest(
            purpose=ModelPurpose.TRANSFORM,
            seed=self._seed,
            workspace_id=workspace_id,
            transformation_type=transformation_type,
            parent_content_hashes=tuple(parent.content_sha256 for parent in parents),
        )
        response = self._backend.complete(request)
        visibility = (
            MemoryVisibility.WORKSPACE
            if _all_workspace_visible(self._database, parents)
            else MemoryVisibility.PRIVATE
        )
        return self._memories.derive(
            actor,
            workspace_id,
            transformation_type=transformation_type,
            prompt_version=PROMPT_VERSION[transformation_type],
            parent_ids=parent_ids,
            content=response.text,
            visibility=visibility,
            complete_task_id=complete_task_id,
            model_call=ModelCallDraft(
                purpose=request.purpose,
                seed=request.seed,
                script_id=response.script_id,
                transformation_type=transformation_type,
                task=None,
                parent_content_hashes=request.parent_content_hashes,
                context_memory_ids=tuple(parent.id for parent in parents),
                output_text=response.text,
                tool_name=response.tool_name,
                arguments=response.arguments,
            ),
        )


def _all_workspace_visible(database: EpisodeDatabase, parents: tuple[Memory, ...]) -> bool:
    with database.system_read_session() as session:
        for parent in parents:
            if parent.visibility is MemoryVisibility.PRIVATE:
                return False
            if parent.visibility is MemoryVisibility.WORKSPACE:
                continue
            revision = session.get(SourceRevisionRow, parent.source_revision_id)
            if revision is None:
                return False
            source = session.get(SourceRow, revision.source_id)
            if (
                source is None
                or source.visibility is not SourceVisibility.WORKSPACE
                or source.deletion_state is not SourceDeletionState.ACTIVE
            ):
                return False
    return True
