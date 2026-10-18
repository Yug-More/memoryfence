"""Run manifests. Building a manifest records metadata; it does not run an experiment."""

import platform
import sqlite3
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version

from pydantic import JsonValue

from memoryfence.domain.enums import RunStatus
from memoryfence.domain.errors import InvalidTransitionError
from memoryfence.domain.experiments import ExperimentManifest, SoftwareVersion
from memoryfence.domain.ids import RunId
from memoryfence.storage.schema import SCHEMA_VERSION

_DISTRIBUTIONS = ("memoryfence", "pydantic", "pydantic-core", "sqlalchemy")


def collect_software_versions() -> tuple[SoftwareVersion, ...]:
    versions = {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version}
    for distribution in _DISTRIBUTIONS:
        try:
            versions[distribution] = version(distribution)
        except PackageNotFoundError:
            versions[distribution] = "not-installed"
    return tuple(
        SoftwareVersion(name=name, version=value) for name, value in sorted(versions.items())
    )


def new_manifest(
    *,
    run_id: RunId,
    scenario_ref: str,
    master_seed: int,
    code_version: str,
    configuration: dict[str, JsonValue],
    started_at: datetime,
    software: tuple[SoftwareVersion, ...] | None = None,
) -> ExperimentManifest:
    """``code_version`` is supplied by the caller (for example a Git commit); it is never
    guessed."""
    return ExperimentManifest(
        run_id=run_id,
        scenario_ref=scenario_ref,
        master_seed=master_seed,
        code_version=code_version,
        schema_version=SCHEMA_VERSION,
        configuration=configuration,
        software=software if software is not None else collect_software_versions(),
        status=RunStatus.RUNNING,
        started_at=started_at,
        finished_at=None,
    )


def finish_manifest(
    manifest: ExperimentManifest, status: RunStatus, finished_at: datetime
) -> ExperimentManifest:
    if manifest.status.is_terminal:
        raise InvalidTransitionError(f"run {manifest.run_id} is already {manifest.status.value}")
    if not status.is_terminal:
        raise InvalidTransitionError("a run can only finish with a terminal status")
    fields = dict(manifest) | {"status": status, "finished_at": finished_at}
    return ExperimentManifest(**fields)
