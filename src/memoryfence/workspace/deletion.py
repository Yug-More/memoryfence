"""Deletion policies DS0-DS4 (protocol section 3.2).

Reach is the source's primary memories plus the transitive closure of *recorded*
derivation edges. True provenance is copied into the deletion ledger and is not used to
decide which memories change. ``DS4`` records re-derivation work here and does not
generate replacement text; ``memoryfence.memory`` executes those tasks later.
"""

from datetime import datetime

from sqlalchemy import select

from memoryfence.domain.access import ResourceRef
from memoryfence.domain.deletion import (
    DeletionLedgerEntry,
    DeletionLedgerEvent,
    DeletionOutcome,
    DeletionRequest,
    RederivationTask,
)
from memoryfence.domain.enums import (
    DeletionEffect,
    DeletionPolicy,
    EventCategory,
    MemoryState,
    Operation,
    Permission,
    RederivationStatus,
    ResourceKind,
    SourceDeletionState,
)
from memoryfence.domain.errors import InvalidTransitionError
from memoryfence.domain.ids import (
    DeletionId,
    IdPrefix,
    MemoryId,
    RevisionId,
    SourceId,
    TaskId,
    TransformationId,
    WorkspaceId,
)
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.serialization import canonical_json
from memoryfence.observability import Auditor
from memoryfence.provenance.graph import topological_order
from memoryfence.provenance.recorded import RecordedProvenanceReader
from memoryfence.storage.database import UnitOfWork
from memoryfence.storage.mappers import to_source
from memoryfence.storage.schema import (
    MemoryRow,
    RederivationTaskRow,
    SourceDeletionRow,
    SourceRevisionRow,
    SourceRow,
)
from memoryfence.workspace.authority import Authorizer
from memoryfence.workspace.memories import memories_for_source

_HARD_DELETE = frozenset(
    {
        DeletionPolicy.SOURCE_AND_PRIMARY,
        DeletionPolicy.CASCADE,
        DeletionPolicy.CASCADE_AND_REDERIVE,
    }
)


class DeletionService:
    def __init__(self, auditor: Auditor) -> None:
        self._auditor = auditor

    def apply(self, actor: PrincipalRef | None, request: DeletionRequest) -> DeletionOutcome:
        """Apply one policy. Repeating ``DS0`` is a no-op; every other repeat is rejected."""
        with self._auditor.operation(
            EventCategory.DELETION,
            Operation.SOURCE_DELETE,
            actor=actor,
            workspace_id=None,
            resource=ResourceRef(kind=ResourceKind.SOURCE, id=request.source_id),
            policy=request.policy,
        ) as scope:
            uow = scope.uow
            authorizer = Authorizer(uow.session)
            row, facts = authorizer.source(request.source_id, actor)
            workspace_id = WorkspaceId(row.workspace_id)
            scope.workspace_id = workspace_id
            principal = authorizer.require(actor, Permission.SOURCE_DELETE, workspace_id, facts)
            if row.deletion_state is not SourceDeletionState.ACTIVE:
                raise InvalidTransitionError(f"source {request.source_id} is not active")
            outcome = _apply(uow, request, row, workspace_id, principal.principal, self._auditor)
            scope.details["scenario"] = request.scenario.value
            scope.details["deletion_id"] = str(outcome.deletion_id)
            scope.details["deleted_memory_ids"] = tuple(map(str, outcome.deleted_memory_ids))
            scope.details["revoked_memory_ids"] = tuple(map(str, outcome.revoked_memory_ids))
            scope.details["task_ids"] = tuple(str(task.id) for task in outcome.rederivation_tasks)
        return outcome


def _apply(
    uow: UnitOfWork,
    request: DeletionRequest,
    source: SourceRow,
    workspace_id: WorkspaceId,
    actor: PrincipalRef,
    auditor: Auditor,
) -> DeletionOutcome:
    session = uow.session
    reader = RecordedProvenanceReader(session, workspace_id)
    primaries = {MemoryId(row.id) for row in memories_for_source(session, request.source_id)}
    primaries |= set(reader.primary_nodes_for_source(request.source_id))
    derived = reader.descendants(primaries) - primaries
    if request.policy is DeletionPolicy.NO_DELETION:
        affected: set[MemoryId] = set()
    elif request.policy is DeletionPolicy.SOURCE_AND_PRIMARY:
        affected = set(primaries)
    else:
        affected = set(primaries) | set(derived)
    memory_rows = (
        {
            MemoryId(row.id): row
            for row in session.scalars(select(MemoryRow).where(MemoryRow.id.in_(affected)))
        }
        if affected
        else {}
    )
    deletion_id = DeletionId(uow.next_id(IdPrefix.DELETION))
    now = uow.now()
    tasks = (
        _plan_rederivation(
            uow, deletion_id, workspace_id, derived, affected, memory_rows, reader, now
        )
        if request.policy is DeletionPolicy.CASCADE_AND_REDERIVE
        else ()
    )
    revisions = tuple(
        session.scalars(
            select(SourceRevisionRow)
            .where(SourceRevisionRow.source_id == request.source_id)
            .order_by(SourceRevisionRow.sequence)
        )
    )
    entries: list[DeletionLedgerEntry] = []

    def entry(
        effect: DeletionEffect,
        *,
        revision_id: RevisionId | None = None,
        memory_id: MemoryId | None = None,
        content: str | None = None,
        content_sha256: str | None = None,
    ) -> None:
        entries.append(
            DeletionLedgerEntry(
                deletion_id=deletion_id,
                sequence=len(entries) + 1,
                effect=effect,
                source_id=request.source_id,
                revision_id=revision_id,
                memory_id=memory_id,
                content=content,
                content_sha256=content_sha256,
            )
        )

    hard_delete = request.policy in _HARD_DELETE
    if hard_delete:
        for revision in revisions:
            entry(
                DeletionEffect.REVISION_DELETED,
                revision_id=RevisionId(revision.id),
                content=revision.content,
                content_sha256=revision.content_sha256,
            )
    if request.policy is DeletionPolicy.TOMBSTONE_AND_REVOKE:
        source.deletion_state = SourceDeletionState.TOMBSTONED
        source.deletion_policy = request.policy
        source.deleted_at = now
        entry(DeletionEffect.SOURCE_TOMBSTONED)
    elif hard_delete:
        source.deletion_state = SourceDeletionState.DELETED
        source.deletion_policy = request.policy
        source.title = None
        source.deleted_at = now
        entry(DeletionEffect.SOURCE_DELETED)
    for memory_id in sorted(affected):
        row = memory_rows.get(memory_id)
        if row is None:
            continue
        if request.policy is DeletionPolicy.TOMBSTONE_AND_REVOKE:
            row.state = MemoryState.REVOKED
            row.revoked_at = now
            effect = DeletionEffect.MEMORY_REVOKED
        else:
            effect = DeletionEffect.MEMORY_DELETED
        entry(
            effect,
            memory_id=memory_id,
            content=row.content,
            content_sha256=row.content_sha256,
        )
        if effect is DeletionEffect.MEMORY_DELETED:
            session.delete(row)
    if hard_delete:
        for revision in revisions:
            session.delete(revision)
    session.flush()
    for task in tasks:
        effect = (
            DeletionEffect.REDERIVATION_PENDING
            if task.status is RederivationStatus.PENDING
            else DeletionEffect.NOT_REGENERATED
        )
        entry(effect, memory_id=task.replaces_memory_id)
    session.add(
        SourceDeletionRow(
            id=deletion_id,
            source_id=request.source_id,
            workspace_id=workspace_id,
            policy=request.policy,
            scenario=request.scenario,
            requested_by_kind=actor.kind,
            requested_by_id=actor.id,
            run_id=auditor.run_id,
            occurred_at=now,
        )
    )
    session.flush()
    for task in tasks:
        session.add(
            RederivationTaskRow(
                id=task.id,
                deletion_id=task.deletion_id,
                workspace_id=task.workspace_id,
                replaces_memory_id=task.replaces_memory_id,
                transformation_id=task.transformation_id,
                surviving_input_ids=canonical_json(list(task.surviving_input_ids)),
                depends_on_task_ids=canonical_json(list(task.depends_on_task_ids)),
                status=task.status,
                replacement_memory_id=None,
                created_at=task.created_at,
            )
        )
    session.flush()
    uow.ground_truth.record_deletion(
        DeletionLedgerEvent(
            deletion_id=deletion_id,
            source_id=request.source_id,
            workspace_id=workspace_id,
            policy=request.policy,
            scenario=request.scenario,
            requested_by=actor,
            run_id=auditor.run_id,
            occurred_at=now,
        ),
        tuple(entries),
    )
    revoked = request.policy is DeletionPolicy.TOMBSTONE_AND_REVOKE
    changed = tuple(memory_id for memory_id in sorted(affected) if memory_id in memory_rows)
    return DeletionOutcome(
        deletion_id=deletion_id,
        source_id=SourceId(request.source_id),
        workspace_id=workspace_id,
        policy=request.policy,
        scenario=request.scenario,
        requested_by=actor,
        source_state=to_source(source).deletion_state,
        deleted_revision_ids=tuple(RevisionId(revision.id) for revision in revisions)
        if hard_delete
        else (),
        deleted_memory_ids=() if revoked or not hard_delete else changed,
        revoked_memory_ids=changed if revoked else (),
        rederivation_tasks=tasks,
        run_id=auditor.run_id,
        occurred_at=now,
    )


def _plan_rederivation(
    uow: UnitOfWork,
    deletion_id: DeletionId,
    workspace_id: WorkspaceId,
    derived: set[MemoryId],
    affected: set[MemoryId],
    memory_rows: dict[MemoryId, MemoryRow],
    reader: RecordedProvenanceReader,
    created_at: datetime,
) -> tuple[RederivationTask, ...]:
    parents_of = {
        memory_id: reader.parents(memory_id)
        for memory_id in derived
        if memory_id in memory_rows and memory_rows[memory_id].transformation_id is not None
    }
    order = topological_order(parents_of)
    tasks: dict[MemoryId, RederivationTask] = {}
    planned: list[RederivationTask] = []
    for memory_id in order:
        row = memory_rows[memory_id]
        transformation_id = row.transformation_id
        if transformation_id is None:
            continue
        surviving: list[MemoryId] = []
        depends: list[TaskId] = []
        for parent_id in parents_of[memory_id]:
            if parent_id in affected:
                parent_task = tasks.get(parent_id)
                if parent_task is not None and parent_task.status is RederivationStatus.PENDING:
                    depends.append(parent_task.id)
            elif uow.session.get(MemoryRow, parent_id) is not None:
                surviving.append(parent_id)
        status = (
            RederivationStatus.PENDING
            if surviving or depends
            else RederivationStatus.NOT_REGENERATED
        )
        task = RederivationTask(
            id=TaskId(uow.next_id(IdPrefix.TASK)),
            deletion_id=deletion_id,
            workspace_id=workspace_id,
            replaces_memory_id=memory_id,
            transformation_id=TransformationId(transformation_id),
            surviving_input_ids=tuple(surviving),
            depends_on_task_ids=tuple(depends),
            status=status,
            created_at=created_at,
        )
        tasks[memory_id] = task
        planned.append(task)
    return tuple(planned)
