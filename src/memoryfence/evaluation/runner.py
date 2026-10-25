"""Execute an isolated scripted matrix. Completed runs are not overwritten."""

import json
import os
import platform
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from memoryfence import __version__
from memoryfence.benchmark.catalog import load_scenario
from memoryfence.benchmark.result import BenchmarkResult, canonical_outcome
from memoryfence.benchmark.runner import run_case
from memoryfence.domain.base import DomainModel
from memoryfence.domain.errors import DomainValidationError, MemoryFenceError
from memoryfence.domain.serialization import canonical_json, sha256_hex
from memoryfence.evaluation.config import ExperimentConfig, load_config
from memoryfence.evaluation.heldout import load_heldout
from memoryfence.evaluation.matrix import PlannedRun, RunMatrix, build_matrix, require_run_limit
from memoryfence.llm.ollama import OllamaBackend
from memoryfence.llm.recording import RecordingTransport
from memoryfence.llm.transport import UrllibTransport

MANIFEST_NAME = "experiment.json"
MATRIX_NAME = "matrix.json"
SUMMARY_NAME = "summary.json"


class RunRecord(DomainModel):
    ordinal: int
    scenario_id: str
    status: str
    failure_reason: str | None
    retrieved: bool | None
    followed: bool | None
    proposed: bool | None
    executed: bool | None
    legitimate_task: bool | None
    control: str | None
    judge_status: str = "not_applicable"
    directory: str
    result_sha256: str | None = None


class ExperimentManifest(DomainModel):
    experiment_id: str
    config_hash: str
    code_version: str
    python_version: str
    package_version: str
    backend: str
    split: str
    model_tag: str | None = None
    model_digest: str | None = None
    prompt_template: str | None = None
    judge_version: str | None = None
    created_at_utc: str | None = None
    lock_sha256: str | None = None
    platform: str | None = None


def code_version() -> str:
    git = shutil.which("git")
    if git is None:
        return "unknown"
    try:
        completed = subprocess.run(  # noqa: S603
            [git, "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip() or "unknown"


def preview(config: ExperimentConfig) -> RunMatrix:
    return build_matrix(config)


def execute(config: ExperimentConfig, directory: Path, *, resume: bool) -> tuple[RunRecord, ...]:
    matrix = build_matrix(config)
    require_run_limit(config, matrix)
    directory.mkdir(parents=True, exist_ok=True)
    _store_plan(directory, config, matrix)
    records: list[RunRecord] = []
    for planned in matrix.runs:
        records.append(_one(directory, config, planned, resume=resume))
        _write_records(directory, records)
    _write_records(directory, records)
    _attach_digest(directory)
    return tuple(records)


def load_records(directory: Path) -> tuple[RunRecord, ...]:
    path = directory / "runs.jsonl"
    if not path.exists():
        raise DomainValidationError("experiment has no run records")
    records: list[RunRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        records.append(RunRecord.model_validate_json(line))
    return tuple(records)


def verify(directory: Path, scratch: Path) -> bool:
    """Rerun the first completed cell and compare its canonical outcome."""
    manifest = ExperimentManifest.model_validate_json((directory / MANIFEST_NAME).read_text())
    config = load_config(directory / "config.json")
    if config.fingerprint() != manifest.config_hash:
        return False
    if config.backend == "ollama":
        return audit(directory)
    records = [record for record in load_records(directory) if record.status == "completed"]
    if not records:
        return False
    first = records[0]
    matrix = build_matrix(config)
    planned = next(run for run in matrix.runs if run.ordinal == first.ordinal)
    fresh = _execute_cell(scratch, config, planned)
    previous = BenchmarkResult.model_validate_json(
        (directory / "runs" / f"{first.ordinal:04d}" / "benchmark-result.json").read_text()
    )
    return canonical_outcome(previous) == canonical_outcome(fresh)


def _store_plan(directory: Path, config: ExperimentConfig, matrix: RunMatrix) -> None:
    config_path = directory / "config.json"
    payload = canonical_json(config.stored_json())
    if config_path.exists() and config_path.read_text(encoding="utf-8") != payload:
        raise DomainValidationError("directory already holds a different experiment")
    manifest_path = directory / MANIFEST_NAME
    if manifest_path.exists():
        manifest = ExperimentManifest.model_validate_json(manifest_path.read_text())
        if manifest.config_hash != config.fingerprint():
            raise DomainValidationError("saved manifest does not match configuration")
        if manifest.code_version != code_version():
            raise DomainValidationError("resume requires the original code revision")
        if (directory / MATRIX_NAME).read_text() != canonical_json(matrix.model_dump(mode="json")):
            raise DomainValidationError("saved matrix does not match configuration")
        return
    config_path.write_text(payload, encoding="utf-8")
    manifest = ExperimentManifest(
        created_at_utc=datetime.now(UTC).isoformat(),
        lock_sha256=sha256_hex(Path("uv.lock").read_text()) if Path("uv.lock").exists() else None,
        platform=platform.platform(),
        experiment_id=config.experiment_id,
        config_hash=config.fingerprint(),
        code_version=code_version(),
        python_version=platform.python_version(),
        package_version=__version__,
        backend=config.backend,
        split=config.split,
        model_tag=config.model_tag,
        prompt_template=None if config.backend == "scripted" else config.prompt_template,
        judge_version=None if config.backend == "scripted" else config.judge_version,
    )
    (directory / MANIFEST_NAME).write_text(manifest.model_dump_json(), encoding="utf-8")
    (directory / MATRIX_NAME).write_text(
        canonical_json(matrix.model_dump(mode="json")), encoding="utf-8"
    )


def _one(
    directory: Path, config: ExperimentConfig, planned: PlannedRun, *, resume: bool
) -> RunRecord:
    run_dir = directory / "runs" / f"{planned.ordinal:04d}"
    result_path = run_dir / "benchmark-result.json"
    if result_path.exists():
        saved = BenchmarkResult.model_validate_json(result_path.read_text(encoding="utf-8"))
        return _record(planned, saved, run_dir)
    if run_dir.exists() and not resume:
        raise DomainValidationError(f"incomplete run {planned.ordinal} needs resume")
    if run_dir.exists():
        archive = directory / "interrupted" / f"{planned.ordinal:04d}"
        archive.mkdir(parents=True, exist_ok=True)
        attempt = archive / f"attempt-{len(tuple(archive.iterdir())) + 1:04d}"
        run_dir.rename(attempt)
    try:
        saved = _execute_cell(run_dir, config, planned)
    except MemoryFenceError as error:
        return RunRecord(
            ordinal=planned.ordinal,
            scenario_id=planned.scenario_id,
            status="invalid",
            failure_reason=error.code.value,
            retrieved=None,
            followed=None,
            proposed=None,
            executed=None,
            legitimate_task=None,
            control=None,
            judge_status="invalid",
            directory=str(run_dir),
        )
    return _record(planned, saved, run_dir)


def _execute_cell(run_dir: Path, config: ExperimentConfig, planned: PlannedRun) -> BenchmarkResult:
    if config.split == "evaluation":
        spec, key = load_heldout(planned.scenario_id)
    else:
        spec, key = load_scenario(planned.scenario_id)
    agent_backend = None
    transform_backend = None
    if config.backend == "ollama":
        if config.model_tag is None:
            raise DomainValidationError("an ollama experiment requires a model tag")
        agent_backend = OllamaBackend(
            endpoint=config.endpoint,
            model=config.model_tag,
            temperature=config.temperature,
            num_ctx=config.num_ctx,
            num_predict=config.num_predict,
            timeout=config.timeout_seconds,
            max_calls=config.max_model_calls,
            output_mode=config.output_mode,
            agent_output_contract=config.agent_output_contract,
            transformation_output_mode=config.transformation_output_mode,
            transport=RecordingTransport(UrllibTransport(), run_dir / "model-exchanges.jsonl"),
        )
        if config.transformation_backend == "ollama":
            transform_backend = agent_backend
    return run_case(
        spec,
        key,
        run_dir,
        policy=planned.deletion_policy,
        fidelity=planned.fidelity,
        defense=planned.defense,
        code_version=code_version(),
        agent_backend=agent_backend,
        transform_backend=transform_backend,
        trial=planned.trial,
    )


def _record(planned: PlannedRun, result: BenchmarkResult, run_dir: Path) -> RunRecord:
    stages = result.stages
    status = "completed" if result.failure_reason is None and stages is not None else "invalid"
    return RunRecord(
        result_sha256=sha256_hex((run_dir / "benchmark-result.json").read_text()),
        ordinal=planned.ordinal,
        scenario_id=planned.scenario_id,
        status=status,
        failure_reason=result.failure_reason,
        retrieved=None if stages is None else stages.retrieved,
        followed=None if stages is None else stages.followed,
        proposed=None if stages is None else stages.proposed,
        executed=None if stages is None else stages.executed,
        legitimate_task=result.legitimate_task,
        control=result.control,
        judge_status=result.judge_status,
        directory=str(run_dir),
    )


def _attach_digest(directory: Path) -> None:
    manifest_path = directory / MANIFEST_NAME
    if not manifest_path.exists():
        return
    manifest = ExperimentManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    if manifest.backend != "ollama" or manifest.model_digest:
        return
    for record in load_records(directory):
        path = directory / "runs" / f"{record.ordinal:04d}" / "benchmark-result.json"
        if not path.exists():
            continue
        result = BenchmarkResult.model_validate_json(path.read_text(encoding="utf-8"))
        if result.model_digest is None:
            continue
        updated = manifest.model_copy(update={"model_digest": result.model_digest})
        manifest_path.write_text(updated.model_dump_json(), encoding="utf-8")
        return


def audit(directory: Path) -> bool:
    """Check completeness and internal consistency; never certify authenticity."""
    try:
        return _audit(directory)
    except (OSError, ValueError, MemoryFenceError):
        return False


def _audit(directory: Path) -> bool:
    manifest = ExperimentManifest.model_validate_json((directory / MANIFEST_NAME).read_text())
    config = load_config(directory / "config.json")
    if config.fingerprint() != manifest.config_hash or manifest.backend != config.backend:
        return False
    if manifest.model_tag != config.model_tag:
        return False
    matrix = build_matrix(config)
    if (directory / MATRIX_NAME).read_text() != canonical_json(matrix.model_dump(mode="json")):
        return False
    records = load_records(directory)
    if tuple(record.ordinal for record in records) != tuple(run.ordinal for run in matrix.runs):
        return False
    for record, planned in zip(records, matrix.runs, strict=True):
        run_dir = directory / "runs" / f"{record.ordinal:04d}"
        result_path = run_dir / "benchmark-result.json"
        if not result_path.exists():
            return False
        result = BenchmarkResult.model_validate_json(result_path.read_text())
        expected = _record(planned, result, run_dir).model_copy(
            update={"directory": record.directory}
        )
        if record != expected:
            return False
        if (
            result.scenario_id != planned.scenario_id
            or result.defense != planned.defense.defense.value
            or result.deletion_policy != planned.deletion_policy
            or result.fidelity != planned.fidelity
            or result.agent_backend != config.backend
        ):
            return False
        if config.backend == "ollama" and record.status == "completed":
            if not result.model_digest or result.model_digest != manifest.model_digest:
                return False
            if (
                result.model_tag != config.model_tag
                or result.kind != "local-model-benchmark"
                or result.prompt_template != config.prompt_template
            ):
                return False
            if not _has_chat_response(run_dir / "model-exchanges.jsonl"):
                return False
    return True


def _has_chat_response(path: Path) -> bool:
    requests: set[int] = set()
    for line in path.read_text().splitlines():
        item = json.loads(line)
        if not isinstance(item, dict) or not isinstance(item.get("sequence"), int):
            return False
        if not isinstance(item.get("url", ""), str):
            return False
        if item.get("event") == "request" and item.get("url", "").endswith("/api/chat"):
            requests.add(item["sequence"])
        if (
            item.get("event") == "response"
            and item.get("sequence") in requests
            and item.get("status") == 200
        ):
            return True
    return False


def _write_records(directory: Path, records: list[RunRecord]) -> None:
    lines = [record.model_dump_json() for record in records]
    path = directory / "runs.jsonl"
    temporary = directory / ".runs.jsonl.tmp"
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write("".join(f"{line}\n" for line in lines))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def export_json(directory: Path) -> str:
    records = load_records(directory)
    return json.dumps([json.loads(record.model_dump_json()) for record in records])
