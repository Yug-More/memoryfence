"""Audited operations and the structured event log.

A successful operation writes its event inside the operation's own transaction, so an
event exists exactly when the change committed. A failed or denied operation is rolled
back first; its event is then written in a separate transaction and the original error
is re-raised. Failure events carry only the reason code, never partial details.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from pydantic import JsonValue
from sqlalchemy import select
from sqlalchemy.orm import Session

from memoryfence.domain.access import ResourceRef
from memoryfence.domain.enums import DeletionPolicy, EventCategory, EventOutcome, Operation
from memoryfence.domain.errors import AuthorizationDenied, MemoryFenceError, ReasonCode
from memoryfence.domain.experiments import EventDetailValue, StructuredEvent
from memoryfence.domain.ids import EventId, IdPrefix, RunId, WorkspaceId, sequential_id
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.serialization import canonical_json
from memoryfence.storage.database import EpisodeDatabase, UnitOfWork
from memoryfence.storage.mappers import principal_ref
from memoryfence.storage.schema import EventRow


class AuditScope:
    """Handle passed to the body of an audited operation."""

    def __init__(
        self, uow: UnitOfWork, workspace_id: WorkspaceId | None, resource: ResourceRef | None
    ) -> None:
        self.uow = uow
        self.workspace_id = workspace_id
        self.resource = resource
        self.details: dict[str, EventDetailValue] = {}


def _write_event(
    uow: UnitOfWork,
    *,
    category: EventCategory,
    operation: Operation,
    actor: PrincipalRef | None,
    workspace_id: WorkspaceId | None,
    resource: ResourceRef | None,
    outcome: EventOutcome,
    reason: ReasonCode,
    policy: DeletionPolicy | None,
    run_id: RunId | None,
    details: dict[str, EventDetailValue],
) -> StructuredEvent:
    sequence = uow.next_number(IdPrefix.EVENT)
    event = StructuredEvent(
        id=EventId(sequential_id(IdPrefix.EVENT, sequence)),
        sequence=sequence,
        category=category,
        operation=operation,
        occurred_at=uow.now(),
        actor=actor,
        workspace_id=workspace_id,
        resource=resource,
        outcome=outcome,
        reason=reason,
        policy=policy,
        run_id=run_id,
        details=details,
    )
    uow.session.add(
        EventRow(
            id=event.id,
            sequence=event.sequence,
            category=event.category,
            operation=event.operation,
            occurred_at=event.occurred_at,
            actor_kind=actor.kind if actor else None,
            actor_id=actor.id if actor else None,
            workspace_id=workspace_id,
            resource_kind=resource.kind if resource else None,
            resource_id=resource.id if resource else None,
            outcome=outcome,
            reason=reason,
            policy=policy,
            run_id=run_id,
            details_json=canonical_json({key: _json(value) for key, value in details.items()}),
        )
    )
    uow.session.flush()
    return event


def _json(value: EventDetailValue) -> JsonValue:
    if isinstance(value, tuple):
        encoded: list[JsonValue] = list(value)
        return encoded
    return value


class Auditor:
    def __init__(self, database: EpisodeDatabase, run_id: RunId | None = None) -> None:
        self._database = database
        self._run_id = run_id

    @property
    def run_id(self) -> RunId | None:
        return self._run_id

    @contextmanager
    def operation(
        self,
        category: EventCategory,
        operation: Operation,
        *,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId | None,
        resource: ResourceRef | None = None,
        policy: DeletionPolicy | None = None,
    ) -> Iterator[AuditScope]:
        scope: AuditScope | None = None
        try:
            with self._database.unit_of_work() as uow:
                scope = AuditScope(uow, workspace_id, resource)
                yield scope
                _write_event(
                    uow,
                    category=category,
                    operation=operation,
                    actor=actor,
                    workspace_id=scope.workspace_id,
                    resource=scope.resource,
                    outcome=EventOutcome.SUCCEEDED,
                    reason=ReasonCode.OK,
                    policy=policy,
                    run_id=self._run_id,
                    details=scope.details,
                )
        except MemoryFenceError as error:
            outcome = (
                EventOutcome.DENIED
                if isinstance(error, AuthorizationDenied)
                else EventOutcome.FAILED
            )
            try:
                with self._database.unit_of_work() as uow:
                    _write_event(
                        uow,
                        category=category,
                        operation=operation,
                        actor=actor,
                        workspace_id=scope.workspace_id if scope is not None else workspace_id,
                        resource=scope.resource if scope is not None else resource,
                        outcome=outcome,
                        reason=error.code,
                        policy=policy,
                        run_id=self._run_id,
                        details={},
                    )
            except MemoryFenceError as logging_error:
                error.add_note(f"recording the failure event also failed: {logging_error.code}")
            raise


def read_events(session: Session, run_id: RunId | None = None) -> tuple[StructuredEvent, ...]:
    statement = select(EventRow).order_by(EventRow.sequence)
    if run_id is not None:
        statement = statement.where(EventRow.run_id == run_id)
    return tuple(_to_event(row) for row in session.scalars(statement))


def _to_event(row: EventRow) -> StructuredEvent:
    raw = json.loads(row.details_json)
    details: dict[str, EventDetailValue] = {
        key: tuple(value) if isinstance(value, list) else value for key, value in raw.items()
    }
    actor = (
        principal_ref(row.actor_kind, row.actor_id)
        if row.actor_kind is not None and row.actor_id is not None
        else None
    )
    resource = (
        ResourceRef(kind=row.resource_kind, id=row.resource_id)
        if row.resource_kind is not None and row.resource_id is not None
        else None
    )
    return StructuredEvent(
        id=EventId(row.id),
        sequence=row.sequence,
        category=row.category,
        operation=row.operation,
        occurred_at=row.occurred_at,
        actor=actor,
        workspace_id=WorkspaceId(row.workspace_id) if row.workspace_id is not None else None,
        resource=resource,
        outcome=row.outcome,
        reason=row.reason,
        policy=row.policy,
        run_id=RunId(row.run_id) if row.run_id is not None else None,
        details=details,
    )


def export_jsonl(events: tuple[StructuredEvent, ...], path: Path) -> None:
    """Write events as JSON Lines, one canonical object per line, in sequence order."""
    lines = [
        canonical_json(event.model_dump(mode="json"))
        for event in sorted(events, key=lambda e: e.sequence)
    ]
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
