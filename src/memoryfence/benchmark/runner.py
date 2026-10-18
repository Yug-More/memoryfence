"""Run one isolated scripted episode and score it without showing labels to the agent."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import JsonValue
from sqlalchemy import select

from memoryfence.agents.loop import AgentLoop, AgentStep
from memoryfence.authorization.gateway import ToolGateway
from memoryfence.benchmark.catalog import load_scenario
from memoryfence.benchmark.labels import EvaluationKey
from memoryfence.benchmark.result import BenchmarkResult
from memoryfence.benchmark.score import StageRecord, legitimate_succeeded, score_stages
from memoryfence.benchmark.spec import ScenarioSpec
from memoryfence.domain.deletion import DeletionOutcome, DeletionRequest
from memoryfence.domain.enums import (
    DeletionPolicy,
    DeletionScenario,
    LineageFidelity,
    MissingnessMode,
    ModelPurpose,
    Permission,
    RunStatus,
    SourceOrigin,
    SourceVisibility,
    WorkspaceRole,
)
from memoryfence.domain.errors import DomainValidationError, MemoryFenceError
from memoryfence.domain.ids import IdPrefix, MemoryId, RunId, SourceId
from memoryfence.domain.principals import PrincipalRef, User
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.domain.serialization import sha256_hex
from memoryfence.domain.time import StepClock
from memoryfence.groundtruth import open_episode
from memoryfence.groundtruth.store import GroundTruthStore
from memoryfence.llm.backend import ScriptedBackend, ScriptedReply
from memoryfence.memory.calls import ModelCallLog
from memoryfence.memory.ingest import IngestionService
from memoryfence.memory.rederive import RederivationExecutor
from memoryfence.memory.retrieve import RetrievalService
from memoryfence.memory.transforms import TransformService
from memoryfence.observability import Auditor
from memoryfence.observability.manifest import new_manifest
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.storage.schema import EventRow
from memoryfence.tools.sandbox import Sandbox
from memoryfence.workspace.deletion import DeletionService
from memoryfence.workspace.directory import DirectoryService
from memoryfence.workspace.tools import ToolService

RESULT_NAME = "benchmark-result.json"
EVENTS_NAME = "events.jsonl"
_AGENT_PERMISSIONS = frozenset(
    {
        Permission.MEMORY_READ,
        Permission.SOURCE_READ,
        Permission.TOOL_PROPOSE,
        Permission.TOOL_EXECUTE,
    }
)


def run_scenario(
    scenario_id: str,
    directory: Path,
    *,
    policy: DeletionPolicy | None = None,
    fidelity: LineageFidelity | None = None,
    marked: bool = False,
    code_version: str,
) -> BenchmarkResult:
    spec, key = load_scenario(scenario_id)
    return run_case(
        spec,
        key,
        directory,
        policy=policy,
        fidelity=fidelity,
        marked=marked,
        code_version=code_version,
    )


def run_case(
    spec: ScenarioSpec,
    key: EvaluationKey,
    directory: Path,
    *,
    policy: DeletionPolicy | None = None,
    fidelity: LineageFidelity | None = None,
    marked: bool = False,
    code_version: str,
) -> BenchmarkResult:
    """Execute ``spec`` in a fresh directory. ``key`` is not passed to the agent."""
    if key.scenario_id != spec.id or key.version != spec.version:
        raise DomainValidationError("evaluation key does not match the scenario")
    chosen_policy = spec.deletion_policy if policy is None else policy
    chosen_fidelity = spec.fidelity if fidelity is None else fidelity
    if chosen_policy is not DeletionPolicy.NO_DELETION and spec.deletion_source_key is None:
        raise DomainValidationError("this scenario has no source to delete")
    directory.mkdir(parents=True, exist_ok=False)
    clock = StepClock(datetime(2026, 1, 1, tzinfo=UTC), timedelta(seconds=1))
    database = open_episode(directory, clock)
    store = GroundTruthStore(database)
    run_id = _allocate_run(database)
    missingness = MissingnessMode.MARKED if marked else MissingnessMode.SILENT
    store.register_run(
        new_manifest(
            run_id=run_id,
            scenario_ref=f"{spec.id}@{spec.version}",
            master_seed=spec.seed,
            code_version=code_version,
            configuration={
                "scenario_id": spec.id,
                "version": spec.version,
                "family": spec.family,
                "deletion_policy": chosen_policy.value,
                "fidelity": chosen_fidelity.value,
                "missingness": missingness.value,
                "seed": spec.seed,
            },
            started_at=clock.now(),
        )
    )
    status = RunStatus.COMPLETED
    try:
        result, events = _episode(
            database,
            spec,
            key,
            run_id=run_id,
            policy=chosen_policy,
            fidelity=chosen_fidelity,
            missingness=missingness,
            code_version=code_version,
            directory=directory,
        )
    except MemoryFenceError as error:
        status = RunStatus.FAILED
        result = _result(
            spec,
            run_id=run_id,
            policy=chosen_policy,
            fidelity=chosen_fidelity,
            missingness=missingness,
            code_version=code_version,
            directory=directory,
            stages=None,
            steps=(),
            legitimate=False,
            failure_reason=error.code.value,
        )
        events = _read_events(database)
    finally:
        store.finish_run(run_id, status)
        database.dispose()
    _write(directory, result, events)
    return result


def replay(
    saved: Path, into: Path, *, code_version: str
) -> tuple[BenchmarkResult, BenchmarkResult]:
    previous = load_result(saved)
    fresh = run_scenario(
        previous.scenario_id,
        into,
        policy=previous.deletion_policy,
        fidelity=previous.fidelity,
        marked=previous.missingness is MissingnessMode.MARKED,
        code_version=code_version,
    )
    return previous, fresh


def load_result(directory: Path) -> BenchmarkResult:
    path = directory / RESULT_NAME
    return BenchmarkResult.model_validate_json(path.read_text(encoding="utf-8"))


def load_events(directory: Path) -> list[dict[str, JsonValue]]:
    rows: list[dict[str, JsonValue]] = []
    text = (directory / EVENTS_NAME).read_text(encoding="utf-8")
    for line in text.splitlines():
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _episode(
    database: EpisodeDatabase,
    spec: ScenarioSpec,
    key: EvaluationKey,
    *,
    run_id: RunId,
    policy: DeletionPolicy,
    fidelity: LineageFidelity,
    missingness: MissingnessMode,
    code_version: str,
    directory: Path,
) -> tuple[BenchmarkResult, list[dict[str, JsonValue]]]:
    auditor = Auditor(database)
    directory_service = DirectoryService(database, auditor)
    casey = directory_service.register_user("Casey")
    avery = directory_service.register_user("Avery")
    blake = directory_service.register_user("Blake")
    workspace, _membership = directory_service.create_workspace(casey.id, "Northwind")
    admin = PrincipalRef.user(casey.id)
    directory_service.grant_membership(admin, workspace.id, avery.id, WorkspaceRole.MEMBER)
    directory_service.grant_membership(admin, workspace.id, blake.id, WorkspaceRole.MEMBER)
    agent = directory_service.register_agent(
        PrincipalRef.user(blake.id),
        workspace.id,
        blake.id,
        "Blake Assistant",
        _AGENT_PERMISSIONS,
    )
    users = {"avery": avery, "blake": blake}
    degradation = ProvenanceDegradationConfiguration(
        fidelity=fidelity,
        missingness=missingness,
        master_seed=spec.seed,
        scenario_template=spec.id,
        payload_variant=f"v{spec.version}",
        replicate=0,
    )
    backend = ScriptedBackend(_replies(spec), seed=spec.seed)
    ingestion = IngestionService(auditor)
    transforms = TransformService(database, auditor, degradation, backend, seed=spec.seed)
    labels = GroundTruthStore(database)
    source_ids: dict[str, SourceId] = {}
    memory_ids: dict[str, MemoryId] = {}
    for source in spec.sources:
        created, _revision, primary = ingestion.ingest(
            PrincipalRef.user(users[source.owner].id),
            workspace.id,
            title=source.title,
            content=source.content,
            visibility=SourceVisibility.WORKSPACE,
        )
        origin = key.origins.get(source.key)
        if origin is None:
            raise DomainValidationError(f"missing origin for {source.key}")
        labels.label_source(created.id, workspace.id, origin)
        source_ids[source.key] = created.id
        memory_ids[source.key] = primary.id
    if spec.delete_before_transform:
        _delete(auditor, users, spec, source_ids, policy)
    for step in spec.transforms:
        try:
            derived = transforms.transform(
                PrincipalRef.user(blake.id),
                workspace.id,
                transformation_type=step.transformation,
                parent_ids=tuple(memory_ids[name] for name in step.parent_keys),
            )
        except MemoryFenceError:
            if not spec.delete_before_transform:
                raise
            break
        else:
            memory_ids[step.key] = derived.id
    if not spec.delete_before_transform:
        deletion = _delete(auditor, users, spec, source_ids, policy)
        if deletion is not None and policy is DeletionPolicy.CASCADE_AND_REDERIVE:
            owner = _owner(users, spec)
            RederivationExecutor(database, auditor, degradation, backend, seed=spec.seed).execute(
                PrincipalRef.user(owner.id), deletion.deletion_id
            )
    loop = AgentLoop(
        RetrievalService(auditor),
        backend,
        ToolGateway(ToolService(auditor), Sandbox(auditor)),
        ModelCallLog(auditor),
        auditor,
        seed=spec.seed,
        max_steps=len(spec.actions),
    )
    actor = PrincipalRef.agent(agent.id)
    steps = tuple(loop.run(actor, workspace.id, action.task) for action in spec.actions)
    retrieved = tuple(memory_id for step in steps for memory_id in step.retrieved_memory_ids)
    stages = score_stages(
        retrieved_ids=retrieved,
        attacker_memory_ids=_attacker_memories(database, key),
        steps=steps,
        key=key,
    )
    result = _result(
        spec,
        run_id=run_id,
        policy=policy,
        fidelity=fidelity,
        missingness=missingness,
        code_version=code_version,
        directory=directory,
        stages=stages,
        steps=steps,
        legitimate=legitimate_succeeded(steps, key),
        failure_reason=None,
    )
    return result, _read_events(database)


def _delete(
    auditor: Auditor,
    users: dict[str, User],
    spec: ScenarioSpec,
    source_ids: dict[str, SourceId],
    policy: DeletionPolicy,
) -> DeletionOutcome | None:
    if policy is DeletionPolicy.NO_DELETION or spec.deletion_source_key is None:
        return None
    owner = _owner(users, spec)
    return DeletionService(auditor).apply(
        PrincipalRef.user(owner.id),
        DeletionRequest(
            source_id=source_ids[spec.deletion_source_key],
            policy=policy,
            scenario=DeletionScenario.ATTACKER,
        ),
    )


def _owner(users: dict[str, User], spec: ScenarioSpec) -> User:
    name = next(source.owner for source in spec.sources if source.key == spec.deletion_source_key)
    return users[name]


def _replies(spec: ScenarioSpec) -> tuple[ScriptedReply, ...]:
    text_by_key = {source.key: source.content for source in spec.sources}
    replies: list[ScriptedReply] = []
    for step in spec.transforms:
        hashes = tuple(sha256_hex(text_by_key[key]) for key in step.parent_keys)
        replies.append(
            ScriptedReply(
                script_id=step.script_id,
                purpose=ModelPurpose.TRANSFORM,
                transformation_type=step.transformation,
                parent_content_hashes=hashes,
                text=step.text,
            )
        )
        text_by_key[step.key] = step.text
    seen: set[str] = set()
    for step in spec.transforms:
        if step.transformation.value in seen:
            continue
        seen.add(step.transformation.value)
        replies.append(
            ScriptedReply(
                script_id=f"{step.script_id}-rederive",
                purpose=ModelPurpose.TRANSFORM,
                transformation_type=step.transformation,
                text=step.text,
            )
        )
    for index, action in enumerate(spec.actions):
        replies.append(
            ScriptedReply(
                script_id=action.script_id,
                purpose=ModelPurpose.AGENT,
                task=action.task,
                text=action.text,
                tool_name=action.tool_name,
                arguments=action.arguments,
                error="timeout" if spec.inject_timeout and index == 0 else None,
            )
        )
    return tuple(replies)


def _attacker_memories(database: EpisodeDatabase, _key: EvaluationKey) -> set[str]:
    """Reach of sources labeled attacker. The in-memory key is not consulted."""
    attacker: set[str] = set()
    with GroundTruthStore(database).reader() as reader:
        for label in reader.labels():
            if label.origin is not SourceOrigin.ATTACKER:
                continue
            attacker.update(str(memory_id) for memory_id in reader.true_reach(label.source_id))
    return attacker


def _result(
    spec: ScenarioSpec,
    *,
    run_id: RunId,
    policy: DeletionPolicy,
    fidelity: LineageFidelity,
    missingness: MissingnessMode,
    code_version: str,
    directory: Path,
    stages: StageRecord | None,
    steps: tuple[AgentStep, ...],
    legitimate: bool,
    failure_reason: str | None,
) -> BenchmarkResult:
    reason = _authorization_reason(steps, spec)
    return BenchmarkResult(
        kind="scripted-benchmark",
        scenario_id=spec.id,
        scenario_version=spec.version,
        family=spec.family,
        protocol_family=spec.protocol_family,
        control=spec.control,
        run_id=run_id,
        seed=spec.seed,
        code_version=code_version,
        deletion_policy=policy,
        fidelity=fidelity,
        missingness=missingness,
        confirmatory=missingness is MissingnessMode.SILENT,
        transformation_chain=tuple(step.transformation.value for step in spec.transforms),
        stages=stages,
        authorization_reason=reason,
        legitimate_task=legitimate,
        failure_reason=failure_reason,
        trace_path=str(directory / RESULT_NAME),
    )


def _authorization_reason(steps: tuple[AgentStep, ...], spec: ScenarioSpec) -> str | None:
    for step, action in zip(steps, spec.actions, strict=False):
        if action.tool_name is None:
            continue
        if step.execute_reason is not None:
            return step.execute_reason.value
        if step.propose_reason is not None:
            return step.propose_reason.value
    return None


def _allocate_run(database: EpisodeDatabase) -> RunId:
    with database.unit_of_work() as unit:
        return RunId(unit.next_id(IdPrefix.RUN))


def _read_events(database: EpisodeDatabase) -> list[dict[str, JsonValue]]:
    events: list[dict[str, JsonValue]] = []
    with database.system_read_session() as session:
        rows = session.scalars(select(EventRow).order_by(EventRow.sequence)).all()
        for row in rows:
            details = json.loads(row.details_json)
            events.append(
                {
                    "id": row.id,
                    "sequence": row.sequence,
                    "category": row.category.value,
                    "operation": row.operation.value,
                    "outcome": row.outcome.value,
                    "reason": row.reason.value,
                    "details": details if isinstance(details, dict) else {},
                }
            )
    return events


def _write(directory: Path, result: BenchmarkResult, events: list[dict[str, JsonValue]]) -> None:
    (directory / RESULT_NAME).write_text(result.model_dump_json(), encoding="utf-8")
    lines = [json.dumps(event, sort_keys=True) for event in events]
    (directory / EVENTS_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
