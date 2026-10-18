"""Persist a model call in its own transaction.

Transformation calls are stored inside the derive transaction instead, so a failed
derive does not keep a call that has no memory.
"""

from memoryfence.domain.enums import EventCategory, Operation
from memoryfence.domain.ids import WorkspaceId
from memoryfence.domain.model import ModelCallDraft
from memoryfence.domain.principals import PrincipalRef
from memoryfence.observability import Auditor
from memoryfence.workspace.memories import _insert_model_call


class ModelCallLog:
    def __init__(self, auditor: Auditor) -> None:
        self._auditor = auditor

    def record(
        self, actor: PrincipalRef | None, workspace_id: WorkspaceId, draft: ModelCallDraft
    ) -> str:
        with self._auditor.operation(
            EventCategory.MODEL,
            Operation.MODEL_COMPLETE,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            call_id = _insert_model_call(scope.uow, workspace_id, draft)
            scope.details["model_call_id"] = call_id
            scope.details["script_id"] = draft.script_id
            scope.details["purpose"] = draft.purpose.value
            scope.details["seed"] = draft.seed
        return call_id
