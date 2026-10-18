"""Execute the DS4 tasks Phase 2 recorded.

Inputs are the task snapshot: surviving memory identifiers and replacements of
dependency tasks. Deleted content is not read. The evaluator ledger is not read.
A task that is ``not_regenerated`` stays that way. A ``completed`` task is not run
again. A failed fixture leaves the task ``pending`` so a later call can retry it.
"""

from sqlalchemy import select

from memoryfence.domain.deletion import RederivationTask
from memoryfence.domain.enums import RederivationStatus, TransformationType
from memoryfence.domain.errors import InvalidTransitionError, ResourceNotFound
from memoryfence.domain.ids import DeletionId, MemoryId, TaskId
from memoryfence.domain.model import LanguageModel
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.memory.transforms import TransformService
from memoryfence.observability import Auditor
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.storage.mappers import to_rederivation_task
from memoryfence.storage.schema import RederivationTaskRow, TransformationRow


class RederivationExecutor:
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
        self._transforms = TransformService(database, auditor, degradation, backend, seed=seed)

    def execute(
        self, actor: PrincipalRef | None, deletion_id: DeletionId
    ) -> tuple[RederivationTask, ...]:
        """Run pending tasks in identifier order, which is the recorded topological order."""
        tasks = self._load(deletion_id)
        completed: dict[str, RederivationTask] = {}
        finished: list[RederivationTask] = []
        for task in tasks:
            if task.status is not RederivationStatus.PENDING:
                finished.append(task)
                if task.status is RederivationStatus.COMPLETED:
                    completed[task.id] = task
                continue
            self._transforms.transform(
                actor,
                task.workspace_id,
                transformation_type=_transformation_type(self._database, task),
                parent_ids=_resolved_parents(task, completed),
                complete_task_id=TaskId(task.id),
            )
            updated = self._one(TaskId(task.id))
            finished.append(updated)
            completed[updated.id] = updated
        return tuple(finished)

    def _load(self, deletion_id: DeletionId) -> tuple[RederivationTask, ...]:
        with self._database.system_read_session() as session:
            rows = session.scalars(
                select(RederivationTaskRow)
                .where(RederivationTaskRow.deletion_id == deletion_id)
                .order_by(RederivationTaskRow.id)
            )
            return tuple(to_rederivation_task(row) for row in rows)

    def _one(self, task_id: TaskId) -> RederivationTask:
        with self._database.system_read_session() as session:
            row = session.get(RederivationTaskRow, task_id)
            if row is None:
                raise ResourceNotFound("rederivation task", task_id)
            return to_rederivation_task(row)


def _resolved_parents(
    task: RederivationTask, completed: dict[str, RederivationTask]
) -> tuple[MemoryId, ...]:
    parents = [MemoryId(memory_id) for memory_id in task.surviving_input_ids]
    for dependency_id in task.depends_on_task_ids:
        dependency = completed.get(dependency_id)
        if (
            dependency is None
            or dependency.status is not RederivationStatus.COMPLETED
            or dependency.replacement_memory_id is None
        ):
            raise InvalidTransitionError(f"task {dependency_id} has no replacement to build on")
        parents.append(MemoryId(dependency.replacement_memory_id))
    return tuple(parents)


def _transformation_type(database: EpisodeDatabase, task: RederivationTask) -> TransformationType:
    with database.system_read_session() as session:
        row = session.get(TransformationRow, task.transformation_id)
        if row is None:
            raise ResourceNotFound("transformation", task.transformation_id)
        return row.transformation_type
