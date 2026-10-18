"""Execute an isolated scripted matrix. Completed runs are not overwritten."""

import json
import platform
import shutil
import subprocess
from pathlib import Path

from memoryfence import __version__
from memoryfence.benchmark.catalog import load_scenario
from memoryfence.benchmark.result import BenchmarkResult, canonical_outcome
from memoryfence.benchmark.runner import run_case
from memoryfence.domain.base import DomainModel
from memoryfence.domain.errors import DomainValidationError, MemoryFenceError
from memoryfence.domain.serialization import canonical_json
from memoryfence.evaluation.config import ExperimentConfig, load_config
from memoryfence.evaluation.heldout import load_heldout
from memoryfence.evaluation.matrix import PlannedRun, RunMatrix, build_matrix, require_run_limit

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
    directory: str


class ExperimentManifest(DomainModel):
    experiment_id: str
    config_hash: str
    code_version: str
    python_version: str
    package_version: str
    backend: str
    split: str


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
    payload = canonical_json(config.model_dump(mode="json"))
    if config_path.exists() and config_path.read_text(encoding="utf-8") != payload:
        raise DomainValidationError("directory already holds a different experiment")
    config_path.write_text(payload, encoding="utf-8")
    manifest = ExperimentManifest(
        experiment_id=config.experiment_id,
        config_hash=config.fingerprint(),
        code_version=code_version(),
        python_version=platform.python_version(),
        package_version=__version__,
        backend=config.backend,
        split=config.split,
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
        for child in run_dir.iterdir():
            child.unlink()
        run_dir.rmdir()
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
            directory=str(run_dir),
        )
    return _record(planned, saved, run_dir)


def _execute_cell(run_dir: Path, config: ExperimentConfig, planned: PlannedRun) -> BenchmarkResult:
    if config.split == "evaluation":
        spec, key = load_heldout(planned.scenario_id)
    else:
        spec, key = load_scenario(planned.scenario_id)
    return run_case(
        spec,
        key,
        run_dir,
        policy=planned.deletion_policy,
        fidelity=planned.fidelity,
        defense=planned.defense,
        code_version=code_version(),
    )


def _record(planned: PlannedRun, result: BenchmarkResult, run_dir: Path) -> RunRecord:
    stages = result.stages
    status = "completed" if result.failure_reason is None and stages is not None else "invalid"
    return RunRecord(
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
        directory=str(run_dir),
    )


def _write_records(directory: Path, records: list[RunRecord]) -> None:
    lines = [record.model_dump_json() for record in records]
    (directory / "runs.jsonl").write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def export_json(directory: Path) -> str:
    records = load_records(directory)
    return json.dumps([json.loads(record.model_dump_json()) for record in records])
