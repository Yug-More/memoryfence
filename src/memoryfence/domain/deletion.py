"""Deletion requests, outcomes, re-derivation tasks, and ledger entries."""

from typing import Annotated, Self

from pydantic import Field, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import (
    DeletionEffect,
    DeletionPolicy,
    DeletionScenario,
    RederivationStatus,
    SourceDeletionState,
)
from memoryfence.domain.ids import (
    DeletionIdField,
    MemoryIdField,
    RevisionIdField,
    RunIdField,
    SourceIdField,
    TaskIdField,
    TransformationIdField,
    WorkspaceIdField,
)
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.sources import Sha256
from memoryfence.domain.time import UtcDatetime


class DeletionRequest(DomainModel):
    """A boundary request. Ownership and authority are never part of the request; they
    are read from trusted state, so a forged claim is rejected as an unknown field."""

    source_id: SourceIdField
    policy: DeletionPolicy
    scenario: DeletionScenario


class RederivationTask(DomainModel):
    """A ``DS4`` work record. Phase 2 plans re-derivation; Phase 3 executes it.

    ``surviving_input_ids`` are recorded parents that were not deleted.
    ``depends_on_task_ids`` are tasks for deleted recorded parents whose replacements
    will become inputs.
    """

    id: TaskIdField
    deletion_id: DeletionIdField
    workspace_id: WorkspaceIdField
    replaces_memory_id: MemoryIdField
    transformation_id: TransformationIdField
    surviving_input_ids: tuple[MemoryIdField, ...]
    depends_on_task_ids: tuple[TaskIdField, ...]
    status: RederivationStatus
    created_at: UtcDatetime
    replacement_memory_id: MemoryIdField | None = None

    @model_validator(mode="after")
    def _status_matches_inputs(self) -> Self:
        has_inputs = bool(self.surviving_input_ids or self.depends_on_task_ids)
        if self.status is RederivationStatus.PENDING:
            if not has_inputs or self.replacement_memory_id is not None:
                raise ValueError("a pending task has inputs and no replacement")
        elif self.status is RederivationStatus.NOT_REGENERATED:
            if has_inputs or self.replacement_memory_id is not None:
                raise ValueError("a task is not_regenerated only when no input can survive")
        elif not has_inputs or self.replacement_memory_id is None:
            raise ValueError("a completed task records its inputs and replacement")
        return self


class DeletionOutcome(DomainModel):
    """The auditable, system-visible result of one deletion. Lists only what the system
    under test changed; it contains no ground truth."""

    deletion_id: DeletionIdField
    source_id: SourceIdField
    workspace_id: WorkspaceIdField
    policy: DeletionPolicy
    scenario: DeletionScenario
    requested_by: PrincipalRef
    source_state: SourceDeletionState
    deleted_revision_ids: tuple[RevisionIdField, ...]
    deleted_memory_ids: tuple[MemoryIdField, ...]
    revoked_memory_ids: tuple[MemoryIdField, ...]
    rederivation_tasks: tuple[RederivationTask, ...]
    run_id: RunIdField | None
    occurred_at: UtcDatetime


class DeletionLedgerEvent(DomainModel):
    """Harness-only header of one deletion, written for every policy including ``DS0``."""

    deletion_id: DeletionIdField
    source_id: SourceIdField
    workspace_id: WorkspaceIdField
    policy: DeletionPolicy
    scenario: DeletionScenario
    requested_by: PrincipalRef
    run_id: RunIdField | None
    occurred_at: UtcDatetime


class DeletionLedgerEntry(DomainModel):
    """Harness-only record of one effect, with content retained for measurement."""

    deletion_id: DeletionIdField
    sequence: Annotated[int, Field(ge=1)]
    effect: DeletionEffect
    source_id: SourceIdField
    revision_id: RevisionIdField | None
    memory_id: MemoryIdField | None
    content: str | None
    content_sha256: Sha256 | None
