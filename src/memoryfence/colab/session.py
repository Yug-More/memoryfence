"""Colab session checks for the four-cell development pilot.

These helpers refuse remote endpoints and do not download model weights.
The notebook calls them only after it is already running inside Colab.
"""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Protocol, Self

from pydantic import model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import ModelPurpose
from memoryfence.domain.errors import DomainValidationError, ModelBackendError
from memoryfence.domain.ids import WorkspaceId
from memoryfence.domain.model import ModelRequest
from memoryfence.domain.serialization import canonical_json
from memoryfence.evaluation.config import ExperimentConfig, load_config
from memoryfence.evaluation.matrix import RunMatrix
from memoryfence.evaluation.runner import MANIFEST_NAME, ExperimentManifest, preview
from memoryfence.llm.endpoint import require_loopback
from memoryfence.llm.ollama import ModelIdentity, OllamaBackend, doctor
from memoryfence.llm.transport import HttpTransport

OFFICIAL_REPOSITORY = "https://github.com/Yug-More/memoryfence"
PILOT_MODEL_TAG = "qwen2.5:0.5b"
LOOPBACK_ENDPOINT = "http://127.0.0.1:11434"
MIN_FREE_DISK_BYTES = 4 * 1024**3
MIN_AVAILABLE_RAM_BYTES = 2 * 1024**3
_SHA = re.compile(r"^[0-9a-f]{40}$")
_STAMP = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")
_BINDINGS = frozenset({"127.0.0.1:11434", "localhost:11434", "[::1]:11434"})
_PROXY_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
NOTEBOOK_SECTIONS = (
    "A. Introduction",
    "B. Runtime diagnostics",
    "C. Repository setup",
    "D. Ollama installation",
    "E. Model selection",
    "F. Backend smoke test",
    "G. Experiment preview",
    "H. Real-model pilot",
    "I. Results and interpretation",
    "J. Artifact export",
)
REQUIRED_NOTEBOOK_SNIPPETS = (
    OFFICIAL_REPOSITORY,
    PILOT_MODEL_TAG,
    "plan_checkout(",
    "require_colab_runtime(",
    LOOPBACK_ENDPOINT,
    "collect_runtime(",
    "pull_command(",
    '"experiment", "preview"',
    '"experiment", "run"',
    '"model", "doctor"',
    '"model", "smoke"',
    "export_pilot_archive(",
    "Exploratory development pilot — not confirmatory evidence.",
    "configs/ollama-pilot.json",
    "SAVE_TO_DRIVE = False",
    "files.download(",
    '"checkout", "--detach"',
    "https://ollama.com/install.sh",
    "https://astral.sh/uv/install.sh",
    "interrupt_note(",
    "read_model_metadata(",
    "reject_prose_tool_request(",
    "record_smoke_identity(",
    "FROZEN = False",
    "not a frozen revision",
)
FORBIDDEN_NOTEBOOK_SNIPPETS = (
    "0.0.0.0",  # noqa: S104 - rejected notebook text, not a bind address
    "heldout",
    "api.openai.com",
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "shell=True",
    "ngrok",
    "cloudflared",
    "ollama.com/api",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "SAVE_TO_DRIVE = True",
)
_EXPORT_FILES = (
    "config.json",
    MANIFEST_NAME,
    "matrix.json",
    "runs.jsonl",
    "summary.json",
    "report.md",
)


class ColabSessionError(Exception):
    """A pilot step cannot continue. The message names the step, not model text."""


class RuntimeReport(DomainModel):
    python_version: str
    ram_bytes: int | None
    ram_available_bytes: int | None
    disk_free_bytes: int | None
    cpu_count: int | None
    gpu_available: bool
    gpu_name: str | None
    limitations: tuple[str, ...]


class CheckoutPlan(DomainModel):
    repository: str
    revision: str
    frozen: bool


class PilotEnvironment(DomainModel):
    repository: str
    revision: str
    python_version: str
    gpu_available: bool
    gpu_name: str | None = None
    disk_free_bytes: int | None = None
    ram_available_bytes: int | None = None
    model_tag: str
    endpoint: str
    label: str = "exploratory-development-pilot"

    @model_validator(mode="after")
    def _official_loopback(self) -> Self:
        if self.repository != OFFICIAL_REPOSITORY:
            raise ValueError("the repository is not the official MemoryFence repository")
        if self.model_tag != PILOT_MODEL_TAG:
            raise ValueError("the environment model tag is not the pilot model")
        if self.label != "exploratory-development-pilot":
            raise ValueError("the pilot label is wrong")
        if _SHA.fullmatch(self.revision) is None:
            raise ValueError("the environment revision must be a full commit SHA")
        try:
            require_loopback(self.endpoint)
        except DomainValidationError as error:
            raise ValueError("the model endpoint must be http on loopback") from error
        return self


class OllamaLauncher(Protocol):
    def start(self, argv: tuple[str, ...], env: Mapping[str, str]) -> None: ...

    def poll_ready(self) -> bool: ...


class _StaticTransport:
    def __init__(self, chat: bytes) -> None:
        self._chat = chat

    def request(
        self, method: str, url: str, payload: bytes | None, timeout: float
    ) -> tuple[int, bytes]:
        del method, payload, timeout
        if url.endswith("/api/version"):
            return 200, b'{"version":"0"}'
        if url.endswith("/api/tags"):
            return 200, b'{"models":[{"name":"qwen2.5:0.5b","digest":"sha256:abc","size":1}]}'
        if url.endswith("/api/show"):
            return 200, (
                b'{"digest":"sha256:abc","details":{"parameter_size":"0.5B",'
                b'"quantization_level":"Q4_0"},"size":1}'
            )
        if url.endswith("/api/chat"):
            return 200, self._chat
        return 404, b"{}"


def collect_runtime(
    *,
    python_version: str | None = None,
    meminfo_text: str | None = None,
    meminfo_path: Path | None = None,
    disk_path: Path | None = None,
    cpu_count: int | None = None,
    detect_cpu: bool = True,
    gpu_checked: bool = False,
    gpu_available: bool = False,
    gpu_name: str | None = None,
) -> RuntimeReport:
    """Read CPU, memory, disk, and GPU facts. A missing GPU is a CPU runtime."""
    limitations: list[str] = []
    version = platform.python_version() if python_version is None else python_version
    if meminfo_text is None:
        path = Path("/proc/meminfo") if meminfo_path is None else meminfo_path
        meminfo_text = path.read_text(encoding="utf-8") if path.is_file() else ""
    total, available = _parse_meminfo(meminfo_text)
    if total is None or available is None:
        limitations.append("memory counters are unavailable")
    try:
        disk_free = shutil.disk_usage(Path("/") if disk_path is None else disk_path).free
    except OSError:
        disk_free = None
        limitations.append("free disk could not be measured")
    cpus = os.cpu_count() if detect_cpu else cpu_count
    if cpus is None:
        limitations.append("cpu count is unavailable")
    if gpu_checked:
        has_gpu = gpu_available
        name = gpu_name
    else:
        has_gpu, name = detect_gpu()
    if not has_gpu:
        limitations.append("no NVIDIA GPU was detected; the pilot will use the CPU")
    return RuntimeReport(
        python_version=version,
        ram_bytes=total,
        ram_available_bytes=available,
        disk_free_bytes=disk_free,
        cpu_count=cpus,
        gpu_available=has_gpu,
        gpu_name=name,
        limitations=tuple(limitations),
    )


def detect_gpu(
    *,
    which: Callable[[str], str | None] | None = None,
    run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str | None]:
    locator = shutil.which if which is None else which
    binary = locator("nvidia-smi")
    if binary is None:
        return False, None
    execute = subprocess.run if run is None else run
    try:
        completed = execute(
            [binary, "--query-gpu=name", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, None
    if completed.returncode != 0:
        return False, None
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        return False, None
    return True, lines[0]


def require_python(version: str) -> None:
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.\d+)?", version)
    if match is None:
        raise ColabSessionError("the Python version could not be read")
    if (int(match.group(1)), int(match.group(2))) < (3, 12):
        raise ColabSessionError("MemoryFence needs Python 3.12 or newer in this runtime")


def require_colab_runtime(*, colab: bool) -> None:
    if not colab:
        raise ColabSessionError(
            "model installation runs only inside Google Colab and does not download files "
            "on this computer"
        )


def runtime_can_attempt_pilot(report: RuntimeReport) -> tuple[bool, str]:
    if report.disk_free_bytes is None:
        return False, "free disk could not be measured"
    if report.disk_free_bytes < MIN_FREE_DISK_BYTES:
        return False, "not enough free disk for the pilot model"
    if report.ram_available_bytes is None:
        return False, "available memory could not be measured"
    if report.ram_available_bytes < MIN_AVAILABLE_RAM_BYTES:
        return False, "not enough available memory for the pilot model"
    return True, "gpu" if report.gpu_available else "cpu"


def require_pilot_resources(report: RuntimeReport) -> str:
    allowed, message = runtime_can_attempt_pilot(report)
    if not allowed:
        raise ColabSessionError(message)
    return message


def plan_checkout(revision: str, *, frozen: bool) -> CheckoutPlan:
    cleaned = revision.strip()
    if frozen:
        if _SHA.fullmatch(cleaned) is None:
            raise ColabSessionError(
                "a frozen experiment requires the full 40-character commit; main is not used"
            )
    elif cleaned in {"", "HEAD", ".", "origin/HEAD"}:
        raise ColabSessionError("the checkout revision is missing")
    elif cleaned != "main" and _SHA.fullmatch(cleaned) is None:
        raise ColabSessionError("revision must be main or a full commit SHA")
    return CheckoutPlan(repository=OFFICIAL_REPOSITORY, revision=cleaned, frozen=frozen)


def checkout_argv(plan: CheckoutPlan, destination: Path) -> tuple[tuple[str, ...], ...]:
    dest = str(destination)
    return (
        ("git", "clone", "--no-tags", OFFICIAL_REPOSITORY, dest),
        ("git", "-C", dest, "checkout", "--detach", plan.revision),
        ("git", "-C", dest, "rev-parse", "HEAD"),
    )


def assert_checked_out(head: str, plan: CheckoutPlan) -> str:
    cleaned = head.strip()
    if _SHA.fullmatch(cleaned) is None:
        raise ColabSessionError("git did not return a commit SHA")
    if _SHA.fullmatch(plan.revision) is not None and cleaned != plan.revision:
        raise ColabSessionError("the checkout is not the requested commit")
    return cleaned


def perform_checkout(
    plan: CheckoutPlan,
    destination: Path,
    runner: Callable[[tuple[str, ...]], str],
) -> str:
    if destination.exists():
        raise ColabSessionError("the checkout directory already exists")
    if not destination.parent.is_dir():
        raise ColabSessionError("the checkout parent is missing")
    commands = checkout_argv(plan, destination)
    for argv in commands[:-1]:
        runner(argv)
    return assert_checked_out(runner(commands[-1]), plan)


def run_git(argv: tuple[str, ...]) -> str:
    if not argv or argv[0] != "git":
        raise ColabSessionError("only git commands are allowed")
    try:
        completed = subprocess.run(argv, check=True, capture_output=True, text=True)  # noqa: S603
    except (OSError, subprocess.CalledProcessError) as error:
        raise ColabSessionError("git checkout failed") from error
    return completed.stdout


def ollama_environment() -> dict[str, str]:
    """Environment for a daemon that listens on loopback and ignores proxies."""
    values = {
        "OLLAMA_HOST": "127.0.0.1:11434",
        "OLLAMA_ORIGINS": LOOPBACK_ENDPOINT,
        "NO_PROXY": "127.0.0.1,localhost,::1",
        "no_proxy": "127.0.0.1,localhost,::1",
    }
    for key in _PROXY_KEYS:
        values[key] = ""
    return values


def assert_loopback_bind(env: Mapping[str, str]) -> None:
    if env.get("OLLAMA_HOST") not in _BINDINGS:
        raise ColabSessionError("Ollama must bind to loopback")
    for key in _PROXY_KEYS:
        if env.get(key):
            raise ColabSessionError("proxy variables must be empty for the local daemon")


def start_ollama(
    *,
    executable: Path | None,
    launcher: OllamaLauncher,
    timeout_seconds: float = 30,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    if timeout_seconds < 0.5 or timeout_seconds > 60:
        raise ColabSessionError("the Ollama startup timeout is out of range")
    if executable is None or not executable.is_file():
        raise ColabSessionError("Ollama is not installed in this runtime")
    env = ollama_environment()
    assert_loopback_bind(env)
    launcher.start((str(executable), "serve"), env)
    attempts = int(timeout_seconds / 0.5)
    for _ in range(attempts):
        if launcher.poll_ready():
            return
        sleep(0.5)
    raise ColabSessionError("Ollama did not become ready before the timeout")


def ensure_loopback_ollama(
    *,
    executable: Path | None,
    launcher: OllamaLauncher,
    timeout_seconds: float = 30,
    sleep: Callable[[float], None] = time.sleep,
    probe: Callable[[str], tuple[int, str]] | None = None,
) -> str:
    check = doctor if probe is None else probe
    status, message = check(LOOPBACK_ENDPOINT)
    if status == 0:
        return message
    start_ollama(
        executable=executable,
        launcher=launcher,
        timeout_seconds=timeout_seconds,
        sleep=sleep,
    )
    status, message = check(LOOPBACK_ENDPOINT)
    if status != 0:
        raise ColabSessionError("Ollama is not reachable on loopback")
    return message


class LoopbackOllamaProcess:
    """Starts `ollama serve` with the loopback environment. It does not publish a port."""

    def __init__(self, ready: Callable[[str], tuple[int, str]] | None = None) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._ready = doctor if ready is None else ready

    def start(self, argv: tuple[str, ...], env: Mapping[str, str]) -> None:
        if self._process is not None:
            raise ColabSessionError("Ollama is already starting")
        assert_loopback_bind(env)
        merged = os.environ.copy()
        merged.update(env)
        self._process = subprocess.Popen(  # noqa: S603
            argv,
            env=merged,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def poll_ready(self) -> bool:
        if self._process is None or self._process.poll() is not None:
            return False
        status, _message = self._ready(LOOPBACK_ENDPOINT)
        return status == 0


def pull_command(tag: str, report: RuntimeReport) -> tuple[str, ...]:
    """Return the one approved pull. This function does not run it."""
    if tag != PILOT_MODEL_TAG:
        raise ColabSessionError("only qwen2.5:0.5b may be downloaded for this pilot")
    require_pilot_resources(report)
    return ("ollama", "pull", tag)


def use_project_environment(root: Path) -> Path:
    sites = sorted((root / ".venv").glob("lib/python*/site-packages"))
    if len(sites) != 1 or not sites[0].is_dir():
        raise ColabSessionError("the project environment was not created")
    site = str(sites[0])
    if site not in sys.path:
        sys.path.insert(0, site)
    return sites[0]


def memoryfence_command(
    root: Path,
    args: tuple[str, ...],
    *,
    which: Callable[[str], str | None] | None = None,
) -> tuple[str, ...]:
    locator = shutil.which if which is None else which
    uv = locator("uv")
    if uv is None:
        raise ColabSessionError("uv is not installed")
    if not args or any(any(char in item for char in "\n\r;|&$`") for item in args):
        raise ColabSessionError("the command arguments are not allowed")
    return (uv, "run", "--project", str(root), "--frozen", "memoryfence", *args)


def load_pilot(root: Path, *, schema_output: bool = False) -> ExperimentConfig:
    filename = "ollama-schema-pilot.json" if schema_output else "ollama-pilot.json"
    path = root / "configs" / filename
    try:
        config = load_config(path)
    except DomainValidationError as error:
        raise ColabSessionError("the pilot configuration is invalid") from error
    if config.split != "development" or config.backend != "ollama":
        raise ColabSessionError("the Colab pilot must use the development Ollama backend")
    if config.transformation_backend != "scripted":
        raise ColabSessionError("the Colab pilot keeps scripted transformations")
    if config.model_tag != PILOT_MODEL_TAG:
        raise ColabSessionError("the Colab pilot model tag does not match the approved tag")
    if set(config.scenarios) != {"clean-note", "direct-note"}:
        raise ColabSessionError("the Colab pilot scenarios changed")
    return config


def preview_pilot(root: Path, *, schema_output: bool = False) -> RunMatrix:
    config = load_pilot(root, schema_output=schema_output)
    matrix = preview(config)
    scenarios = {run.scenario_id for run in matrix.runs}
    if matrix.valid_count != 4 or matrix.exclusions or scenarios != {"clean-note", "direct-note"}:
        raise ColabSessionError("the Colab pilot is not the four-cell development matrix")
    return matrix


def pilot_output_directory(parent: Path, stamp: str) -> Path:
    if _STAMP.fullmatch(stamp) is None:
        raise ColabSessionError("the run stamp must be UTC YYYYMMDDTHHMMSSZ")
    if not parent.is_absolute():
        raise ColabSessionError("the pilot output parent must be absolute")
    return parent / stamp


def resume_or_refuse(directory: Path, *, new_run: bool) -> str:
    saved = (directory / "config.json").is_file()
    if new_run and saved:
        raise ColabSessionError(
            "this directory already has trials; use a new directory so runs are not mixed"
        )
    if not new_run and not saved:
        raise ColabSessionError("there is no saved experiment to resume")
    return "run" if new_run else "resume"


def interrupt_note(directory: Path) -> str:
    location = str(directory)
    return (
        "The pilot was interrupted or the runtime may disconnect. Partial trials are not a result. "
        f"Download any archive that was already written for {location}. "
        "Start a new directory for another run so old and new trials stay separate."
    )


def read_model_metadata(directory: Path) -> ExperimentManifest:
    path = directory / MANIFEST_NAME
    if not path.is_file():
        raise ColabSessionError("the experiment manifest is missing")
    try:
        manifest = ExperimentManifest.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise ColabSessionError("the experiment manifest is invalid") from error
    if manifest.backend != "ollama" or manifest.model_tag != PILOT_MODEL_TAG:
        raise ColabSessionError("the manifest is not the pilot model")
    if not manifest.model_digest:
        raise ColabSessionError("the manifest has no model digest")
    if (
        manifest.prompt_template not in {"agent-v1", "agent-v2-json-schema"}
        or manifest.judge_version != "rubric-v1"
    ):
        raise ColabSessionError("the manifest prompt or judge version is unexpected")
    if not manifest.code_version:
        raise ColabSessionError("the manifest has no code version")
    return manifest


def record_smoke_identity(
    endpoint: str,
    model: str,
    transport: HttpTransport | None = None,
    *,
    schema_output: bool = False,
) -> ModelIdentity:
    if model != PILOT_MODEL_TAG:
        raise ColabSessionError("only qwen2.5:0.5b may be used for this pilot")
    status, message = doctor(endpoint, transport)
    if status != 0:
        raise ColabSessionError(message)
    backend = OllamaBackend(
        endpoint=endpoint,
        model=model,
        temperature=0,
        num_ctx=2048 if schema_output else 256,
        num_predict=256 if schema_output else 64,
        timeout=30,
        max_calls=2,
        transport=transport,
        output_mode="json_schema" if schema_output else "native",
    )
    try:
        backend.complete(
            ModelRequest(
                purpose=ModelPurpose.AGENT,
                seed=1,
                workspace_id=WorkspaceId("ws-local"),
                task="Reply with JSON decision respond and text ok.",
            )
        )
    except ModelBackendError as error:
        raise ColabSessionError("the local model smoke call failed") from error
    return _require_identity(backend.identity)


def reject_prose_tool_request() -> str:
    """A sentence is not a tool call. This check uses a fake response and no network."""
    chat = json.dumps({"message": {"content": "Please share_document now."}}).encode()
    backend = OllamaBackend(
        endpoint=LOOPBACK_ENDPOINT,
        model=PILOT_MODEL_TAG,
        temperature=0,
        num_ctx=256,
        num_predict=64,
        timeout=30,
        max_calls=2,
        transport=_StaticTransport(chat),
    )
    try:
        backend.complete(
            ModelRequest(
                purpose=ModelPurpose.AGENT,
                seed=1,
                workspace_id=WorkspaceId("ws-local"),
                task="Reply with JSON decision respond and text ok.",
            )
        )
    except ModelBackendError as error:
        return error.code.value
    raise ColabSessionError("a prose tool request was accepted")


def export_pilot_archive(
    experiment_dir: Path,
    destination_dir: Path,
    *,
    revision: str,
    environment: PilotEnvironment,
    stamp: str,
) -> Path:
    missing = [name for name in _EXPORT_FILES if not (experiment_dir / name).is_file()]
    if missing:
        raise ColabSessionError("experiment output is missing: " + ", ".join(missing))
    results = list(experiment_dir.glob("runs/*/benchmark-result.json"))
    if not results:
        raise ColabSessionError("experiment output has no benchmark result")
    if (experiment_dir / "environment.json").exists():
        raise ColabSessionError("the experiment directory already has an environment file")
    try:
        config = load_config(experiment_dir / "config.json")
    except DomainValidationError as error:
        raise ColabSessionError("the saved experiment configuration is invalid") from error
    source = experiment_dir.resolve()
    dest_dir = destination_dir.resolve()
    if dest_dir == source or source in dest_dir.parents:
        raise ColabSessionError("the archive directory must be outside the experiment directory")
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = _archive_name(config.experiment_id, revision, stamp)
    target = dest_dir / name
    if target.exists():
        raise ColabSessionError("the archive already exists; choose a new directory for a rerun")
    files = _export_files(source)
    payload = canonical_json(environment.model_dump(mode="json")).encode()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
        env_info = zipfile.ZipInfo("environment.json")
        env_info.date_time = (1980, 1, 1, 0, 0, 0)
        env_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(env_info, payload)
    verify_archive(target)
    return target


def verify_archive(path: Path) -> tuple[str, ...]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ColabSessionError("the archive is missing or empty")
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise ColabSessionError("the archive failed its integrity check")
            names = tuple(archive.namelist())
    except zipfile.BadZipFile as error:
        raise ColabSessionError("the archive failed its integrity check") from error
    for required in (*_EXPORT_FILES, "environment.json"):
        if required not in names:
            raise ColabSessionError("the archive is missing an expected file")
    if not any(name.endswith("benchmark-result.json") for name in names):
        raise ColabSessionError("the archive has no benchmark result")
    return names


def validate_notebook(path: Path) -> None:
    text = _notebook_text(path)
    cursor = 0
    for heading in NOTEBOOK_SECTIONS:
        found = text.find(heading, cursor)
        if found < 0:
            raise ColabSessionError("the notebook is missing a required section")
        cursor = found
    for snippet in REQUIRED_NOTEBOOK_SNIPPETS:
        if snippet not in text:
            raise ColabSessionError("the notebook is missing a required step")
    for snippet in FORBIDDEN_NOTEBOOK_SNIPPETS:
        if snippet in text:
            raise ColabSessionError("the notebook contains a forbidden endpoint or split")


def _notebook_text(path: Path) -> str:
    if not path.is_file():
        raise ColabSessionError("the notebook is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ColabSessionError("the notebook is not valid JSON") from error
    if not isinstance(payload, dict) or payload.get("nbformat") != 4:
        raise ColabSessionError("the notebook format is not supported")
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ColabSessionError("the notebook has no cells")
    chunks: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict) or cell.get("cell_type") not in {"markdown", "code"}:
            raise ColabSessionError("the notebook has an unsupported cell")
        source = cell.get("source", "")
        if isinstance(source, list):
            if not all(isinstance(item, str) for item in source):
                raise ColabSessionError("the notebook source is malformed")
            text = "".join(source)
        elif isinstance(source, str):
            text = source
        else:
            raise ColabSessionError("the notebook source is malformed")
        chunks.append(text)
    return "\n".join(chunks)


def _parse_meminfo(text: str) -> tuple[int | None, int | None]:
    total = None
    available = None
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            total = _kib_to_bytes(line)
        elif line.startswith("MemAvailable:"):
            available = _kib_to_bytes(line)
    return total, available


def _kib_to_bytes(line: str) -> int | None:
    parts = line.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return int(parts[1]) * 1024


def _require_identity(identity: ModelIdentity | None) -> ModelIdentity:
    if identity is None or not identity.digest:
        raise ColabSessionError("the model identity has no digest")
    return identity


def _archive_name(experiment_id: str, revision: str, stamp: str) -> str:
    if _SHA.fullmatch(revision) is None or _STAMP.fullmatch(stamp) is None:
        raise ColabSessionError("the archive name needs a commit and a UTC stamp")
    return f"memoryfence-colab-pilot-{experiment_id}-{revision[:12]}-{stamp}.zip"


def _export_files(experiment_dir: Path) -> tuple[Path, ...]:
    files = [
        path
        for path in experiment_dir.rglob("*")
        if path.is_file() and "_verify" not in path.parts and "__pycache__" not in path.parts
    ]
    return tuple(sorted(files))
