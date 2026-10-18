"""Structured events and experiment run manifests."""

from typing import Annotated, Self

from pydantic import Field, JsonValue, StringConstraints, model_validator

from memoryfence.domain.access import ResourceRef
from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import (
    DeletionPolicy,
    EventCategory,
    EventOutcome,
    Operation,
    RunStatus,
)
from memoryfence.domain.errors import ReasonCode
from memoryfence.domain.ids import EventIdField, RunIdField, WorkspaceIdField
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.serialization import canonical_json, sha256_hex
from memoryfence.domain.time import UtcDatetime

EventDetailValue = str | int | bool | None | tuple[str, ...]


class StructuredEvent(DomainModel):
    """One audit event from the system under test. Never contains ground truth."""

    id: EventIdField
    sequence: Annotated[int, Field(ge=1)]
    category: EventCategory
    operation: Operation
    occurred_at: UtcDatetime
    actor: PrincipalRef | None
    workspace_id: WorkspaceIdField | None
    resource: ResourceRef | None
    outcome: EventOutcome
    reason: ReasonCode
    policy: DeletionPolicy | None
    run_id: RunIdField | None
    details: dict[str, EventDetailValue]

    @model_validator(mode="after")
    def _reason_matches_outcome(self) -> Self:
        if (self.outcome is EventOutcome.SUCCEEDED) != (self.reason is ReasonCode.OK):
            raise ValueError("successful events use reason OK, failures a specific code")
        if (self.outcome is EventOutcome.DENIED) != self.reason.is_denial:
            raise ValueError("denied events carry a denial reason code")
        return self


class SoftwareVersion(DomainModel):
    name: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    version: Annotated[str, StringConstraints(min_length=1, max_length=100)]


class ExperimentManifest(DomainModel):
    """What is needed to reproduce a run. Harness-only; persisted in the ground-truth
    database. Creating a manifest does not execute anything."""

    run_id: RunIdField
    scenario_ref: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    master_seed: Annotated[int, Field(ge=0, lt=2**63)]
    code_version: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    schema_version: Annotated[int, Field(ge=1)]
    configuration: dict[str, JsonValue]
    software: tuple[SoftwareVersion, ...]
    status: RunStatus
    started_at: UtcDatetime
    finished_at: UtcDatetime | None

    @model_validator(mode="after")
    def _status_is_consistent(self) -> Self:
        if self.status.is_terminal != (self.finished_at is not None):
            raise ValueError("finished_at is set exactly for terminal statuses")
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at precedes started_at")
        names = [item.name for item in self.software]
        if names != sorted(set(names)):
            raise ValueError("software versions must be unique and sorted by name")
        return self

    @property
    def configuration_sha256(self) -> str:
        return sha256_hex(canonical_json(self.configuration))
