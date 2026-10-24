"""Colab pilot helpers. These tests do not install Ollama or download a model."""

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from memoryfence.cli import main
from memoryfence.colab.session import (
    LOOPBACK_ENDPOINT,
    PILOT_MODEL_TAG,
    CheckoutPlan,
    ColabSessionError,
    LoopbackOllamaProcess,
    PilotEnvironment,
    RuntimeReport,
    _require_identity,
    assert_checked_out,
    assert_loopback_bind,
    collect_runtime,
    detect_gpu,
    ensure_loopback_ollama,
    export_pilot_archive,
    interrupt_note,
    load_pilot,
    memoryfence_command,
    ollama_environment,
    perform_checkout,
    pilot_output_directory,
    plan_checkout,
    preview_pilot,
    pull_command,
    read_model_metadata,
    record_smoke_identity,
    reject_prose_tool_request,
    require_colab_runtime,
    require_pilot_resources,
    require_python,
    resume_or_refuse,
    run_git,
    start_ollama,
    use_project_environment,
    validate_notebook,
    verify_archive,
)
from memoryfence.domain.errors import ModelBackendError, ReasonCode
from memoryfence.evaluation.config import smoke_config
from memoryfence.evaluation.runner import ExperimentManifest
from memoryfence.llm.ollama import ModelIdentity
from memoryfence.llm.transport import HttpTransport

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "memoryfence_colab_pilot.ipynb"
SHA = "a" * 40
OTHER = "b" * 40
STAMP = "20261018T132500Z"
FINGERPRINT = "c9113f33c149efc1da746f69761b325b9aaa37dd38c3d39bcad09c14c480703a"


def _report(**overrides: object) -> RuntimeReport:
    values: dict[str, object] = {
        "python_version": "3.12.1",
        "ram_bytes": 8 * 1024**3,
        "ram_available_bytes": 4 * 1024**3,
        "disk_free_bytes": 8 * 1024**3,
        "cpu_count": 2,
        "gpu_available": False,
        "gpu_name": None,
        "limitations": ("no NVIDIA GPU was detected; the pilot will use the CPU",),
    }
    values.update(overrides)
    return RuntimeReport.model_validate(values)


def _environment() -> PilotEnvironment:
    return PilotEnvironment(
        repository="https://github.com/Yug-More/memoryfence",
        revision=SHA,
        python_version="3.12.1",
        gpu_available=False,
        model_tag=PILOT_MODEL_TAG,
        endpoint=LOOPBACK_ENDPOINT,
    )


def _manifest(**overrides: object) -> ExperimentManifest:
    values: dict[str, object] = {
        "experiment_id": "ollama-pilot",
        "config_hash": "abc",
        "code_version": SHA,
        "python_version": "3.12.1",
        "package_version": "0.1.0.dev0",
        "backend": "ollama",
        "split": "development",
        "model_tag": PILOT_MODEL_TAG,
        "model_digest": "sha256:abc",
        "prompt_template": "agent-v1",
        "judge_version": "rubric-v1",
    }
    values.update(overrides)
    return ExperimentManifest.model_validate(values)


def _fill(directory: Path, *, config: str | None = None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    text = config if config is not None else (ROOT / "configs" / "ollama-pilot.json").read_text()
    (directory / "config.json").write_text(text, encoding="utf-8")
    for name in ("experiment.json", "matrix.json", "runs.jsonl", "summary.json"):
        (directory / name).write_text("{}\n", encoding="utf-8")
    (directory / "report.md").write_text("report\n", encoding="utf-8")
    run = directory / "runs" / "0001"
    run.mkdir(parents=True)
    (run / "benchmark-result.json").write_text("{}\n", encoding="utf-8")


class _Ready:
    def __init__(self, ready: bool) -> None:
        self.ready = ready
        self.started = 0

    def start(self, argv: tuple[str, ...], env: object) -> None:
        self.started += 1
        assert argv[1] == "serve"

    def poll_ready(self) -> bool:
        return self.ready


class _Chat:
    def __init__(self, chat: bytes) -> None:
        self._chat = chat

    def request(
        self, method: str, url: str, payload: bytes | None, timeout: float
    ) -> tuple[int, bytes]:
        del method, payload, timeout
        if url.endswith("/api/version"):
            return 200, b'{"version":"test"}'
        if url.endswith("/api/tags"):
            return 200, b'{"models":[{"name":"qwen2.5:0.5b","digest":"sha256:abc"}]}'
        if url.endswith("/api/show"):
            return 200, b'{"digest":"sha256:abc","details":{"parameter_size":"0.5B"}}'
        if url.endswith("/api/chat"):
            return 200, self._chat
        return 404, b"{}"


def _executable(path: Path) -> Path:
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_runtime_reports_cpu_only_and_measured_memory(tmp_path: Path) -> None:
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal: 100 kB\nMemAvailable: 40 kB\n", encoding="utf-8")
    report = collect_runtime(
        python_version="3.12.1",
        meminfo_text=meminfo.read_text(encoding="utf-8"),
        disk_path=tmp_path,
        cpu_count=4,
        detect_cpu=False,
        gpu_checked=True,
        gpu_available=False,
    )
    assert report.ram_bytes == 100 * 1024
    assert report.ram_available_bytes == 40 * 1024
    assert report.disk_free_bytes is not None
    assert report.gpu_available is False
    assert "CPU" in report.limitations[-1]
    assert require_pilot_resources(_report(gpu_available=True, gpu_name="Tesla T4")) == "gpu"
    assert require_pilot_resources(_report()) == "cpu"


def test_runtime_records_missing_counters(tmp_path: Path) -> None:
    missing = tmp_path / "absent"
    report = collect_runtime(
        meminfo_path=missing,
        meminfo_text=None,
        disk_path=tmp_path / "no-such-disk",
        detect_cpu=False,
        cpu_count=None,
        gpu_checked=True,
        gpu_available=True,
        gpu_name="Tesla T4",
    )
    assert report.ram_bytes is None
    assert report.disk_free_bytes is None
    bad = collect_runtime(
        meminfo_text="MemTotal: bad\nMemAvailable: bad\nSwapTotal: 1 kB\n",
        disk_path=tmp_path,
        detect_cpu=False,
        cpu_count=1,
        gpu_checked=True,
        gpu_available=False,
    )
    assert bad.ram_bytes is None
    assert bad.ram_available_bytes is None
    assert report.cpu_count is None
    assert report.gpu_available is True
    assert report.gpu_name == "Tesla T4"
    assert any("memory" in item for item in report.limitations)
    assert any("disk" in item for item in report.limitations)
    assert any("cpu" in item for item in report.limitations)


def test_default_runtime_probe_does_not_require_a_gpu() -> None:
    report = collect_runtime()
    assert report.python_version
    assert isinstance(report.gpu_available, bool)


def test_gpu_detection_covers_missing_and_named_devices() -> None:
    assert detect_gpu(which=lambda _name: None) == (False, None)
    assert detect_gpu(which=lambda _name: "/no/such/nvidia-smi") == (False, None)

    def explode(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=5)

    assert detect_gpu(which=lambda _name: "nvidia-smi", run=explode) == (False, None)
    failed = subprocess.CompletedProcess(args=["nvidia-smi"], returncode=1, stdout="")
    assert detect_gpu(which=lambda _name: "nvidia-smi", run=lambda *_a, **_k: failed) == (
        False,
        None,
    )
    empty = subprocess.CompletedProcess(args=["nvidia-smi"], returncode=0, stdout="\n")
    assert detect_gpu(which=lambda _name: "nvidia-smi", run=lambda *_a, **_k: empty) == (
        False,
        None,
    )
    named = subprocess.CompletedProcess(args=["nvidia-smi"], returncode=0, stdout="Tesla T4\n")
    assert detect_gpu(which=lambda _name: "nvidia-smi", run=lambda *_a, **_k: named) == (
        True,
        "Tesla T4",
    )


def test_python_and_colab_guards() -> None:
    require_python("3.12.1")
    require_python("3.13")
    with pytest.raises(ColabSessionError, match=r"3\.12"):
        require_python("3.11.9")
    with pytest.raises(ColabSessionError, match="could not be read"):
        require_python("python")
    require_colab_runtime(colab=True)
    with pytest.raises(ColabSessionError, match="does not download"):
        require_colab_runtime(colab=False)


def test_resource_gate_stops_before_a_pull() -> None:
    with pytest.raises(ColabSessionError, match="free disk could not be measured"):
        pull_command(PILOT_MODEL_TAG, _report(disk_free_bytes=None))
    with pytest.raises(ColabSessionError, match="not enough free disk"):
        pull_command(PILOT_MODEL_TAG, _report(disk_free_bytes=1024))
    with pytest.raises(ColabSessionError, match="available memory could not be measured"):
        require_pilot_resources(_report(ram_available_bytes=None))
    with pytest.raises(ColabSessionError, match="not enough available memory"):
        require_pilot_resources(_report(ram_available_bytes=1024))
    with pytest.raises(ColabSessionError, match=r"only qwen2\.5:0\.5b"):
        pull_command("qwen2.5:7b", _report())
    assert pull_command(PILOT_MODEL_TAG, _report()) == ("ollama", "pull", PILOT_MODEL_TAG)


def test_checkout_pins_a_commit_and_rejects_a_moving_branch(tmp_path: Path) -> None:
    frozen = plan_checkout(SHA, frozen=True)
    seen: list[tuple[str, ...]] = []

    def runner(argv: tuple[str, ...]) -> str:
        seen.append(argv)
        return SHA + "\n"

    assert perform_checkout(frozen, tmp_path / "repo", runner) == SHA
    assert seen[0][2] == "--no-tags"
    assert seen[1][3:5] == ("checkout", "--detach")
    (tmp_path / "repo").mkdir()
    with pytest.raises(ColabSessionError, match="already exists"):
        perform_checkout(frozen, tmp_path / "repo", runner)
    with pytest.raises(ColabSessionError, match="parent is missing"):
        perform_checkout(frozen, tmp_path / "missing" / "repo", runner)
    with pytest.raises(ColabSessionError, match="main is not used"):
        plan_checkout("main", frozen=True)
    with pytest.raises(ColabSessionError, match="revision is missing"):
        plan_checkout(" HEAD ", frozen=False)
    with pytest.raises(ColabSessionError, match="main or a full commit"):
        plan_checkout("feature", frozen=False)
    moving = plan_checkout(" main ", frozen=False)
    assert moving.revision == "main"
    assert perform_checkout(moving, tmp_path / "moving", lambda _argv: OTHER) == OTHER
    with pytest.raises(ColabSessionError, match="not the requested commit"):
        perform_checkout(plan_checkout(SHA, frozen=True), tmp_path / "other", lambda _argv: OTHER)
    with pytest.raises(ColabSessionError, match="did not return"):
        assert_checked_out("main", CheckoutPlan(repository="x", revision="main", frozen=False))


def test_git_runner_rejects_other_programs() -> None:
    assert "true" in run_git(("git", "rev-parse", "--is-inside-work-tree"))
    with pytest.raises(ColabSessionError, match="only git"):
        run_git(("rm", "-rf", "/"))
    with pytest.raises(ColabSessionError, match="git checkout failed"):
        run_git(("git", "not-a-real-subcommand"))


def test_ollama_start_stays_on_loopback_and_times_out(tmp_path: Path) -> None:
    env = ollama_environment()
    assert_loopback_bind(env)
    assert env["OLLAMA_HOST"] == "127.0.0.1:11434"
    assert env["HTTP_PROXY"] == ""
    leaked = dict(env)
    leaked["https_proxy"] = "http://example.com:9"
    with pytest.raises(ColabSessionError, match="proxy"):
        assert_loopback_bind(leaked)
    public = dict(env)
    public["OLLAMA_HOST"] = "0.0.0.0:11434"
    with pytest.raises(ColabSessionError, match="loopback"):
        assert_loopback_bind(public)
    executable = _executable(tmp_path / "ollama")
    with pytest.raises(ColabSessionError, match="not installed"):
        start_ollama(executable=None, launcher=_Ready(True), timeout_seconds=0.5)
    with pytest.raises(ColabSessionError, match="not installed"):
        start_ollama(executable=tmp_path / "missing", launcher=_Ready(True), timeout_seconds=0.5)
    with pytest.raises(ColabSessionError, match="out of range"):
        start_ollama(executable=executable, launcher=_Ready(True), timeout_seconds=0.4)
    ready = _Ready(True)
    start_ollama(executable=executable, launcher=ready, timeout_seconds=0.5, sleep=lambda _s: None)
    assert ready.started == 1
    slept: list[float] = []
    with pytest.raises(ColabSessionError, match="timeout"):
        start_ollama(
            executable=executable,
            launcher=_Ready(False),
            timeout_seconds=1,
            sleep=slept.append,
        )
    assert slept == [0.5, 0.5]


def test_ensure_does_not_start_a_second_daemon(tmp_path: Path) -> None:
    executable = _executable(tmp_path / "ollama")
    launcher = _Ready(True)
    assert (
        ensure_loopback_ollama(
            executable=executable,
            launcher=launcher,
            probe=lambda _url: (0, "already"),
        )
        == "already"
    )
    assert launcher.started == 0
    calls = {"count": 0}

    def later(_url: str) -> tuple[int, str]:
        calls["count"] += 1
        if calls["count"] == 1:
            return 2, "down"
        return 0, "ready"

    started = _Ready(True)
    assert (
        ensure_loopback_ollama(
            executable=executable,
            launcher=started,
            timeout_seconds=0.5,
            sleep=lambda _s: None,
            probe=later,
        )
        == "ready"
    )
    assert started.started == 1
    with pytest.raises(ColabSessionError, match="not installed"):
        ensure_loopback_ollama(executable=None, launcher=_Ready(True), timeout_seconds=0.5)
    with pytest.raises(ColabSessionError, match="not reachable"):
        ensure_loopback_ollama(
            executable=executable,
            launcher=_Ready(True),
            timeout_seconds=0.5,
            sleep=lambda _s: None,
            probe=lambda _url: (2, "down"),
        )


def test_process_lifecycle_does_not_listen_publicly() -> None:
    exited = LoopbackOllamaProcess()
    exited.start((sys.executable, "-c", "import sys; sys.exit(0)"), ollama_environment())
    assert exited._process is not None
    exited._process.wait(timeout=5)
    assert exited.poll_ready() is False
    probed = LoopbackOllamaProcess()
    probed.start((sys.executable, "-c", "import time; time.sleep(5)"), ollama_environment())
    try:
        assert isinstance(probed.poll_ready(), bool)
    finally:
        assert probed._process is not None
        probed._process.terminate()
        probed._process.wait(timeout=5)
    running = LoopbackOllamaProcess(ready=lambda _url: (0, "ok"))
    running.start((sys.executable, "-c", "import time; time.sleep(30)"), ollama_environment())
    try:
        assert running.poll_ready() is True
        quiet = LoopbackOllamaProcess(ready=lambda _url: (2, "down"))
        assert quiet._process is None
        assert quiet.poll_ready() is False
        with pytest.raises(ColabSessionError, match="already starting"):
            running.start(
                (sys.executable, "-c", "import time; time.sleep(30)"),
                ollama_environment(),
            )
        with pytest.raises(ColabSessionError, match="loopback"):
            LoopbackOllamaProcess().start(("true",), {"OLLAMA_HOST": "0.0.0.0:11434"})
    finally:
        assert running._process is not None
        running._process.terminate()
        running._process.wait(timeout=5)


def test_project_environment_and_command(tmp_path: Path) -> None:
    site = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
    site.mkdir(parents=True)
    before = list(sys.path)
    try:
        assert use_project_environment(tmp_path) == site
        assert use_project_environment(tmp_path) == site
        assert sys.path.count(str(site)) == 1
    finally:
        sys.path[:] = before
    (tmp_path / ".venv" / "lib" / "python3.13" / "site-packages").mkdir(parents=True)
    with pytest.raises(ColabSessionError, match="was not created"):
        use_project_environment(tmp_path)
    command = memoryfence_command(
        tmp_path,
        ("model", "doctor"),
        which=lambda name: "/usr/bin/uv" if name == "uv" else None,
    )
    assert command[:5] == ("/usr/bin/uv", "run", "--project", str(tmp_path), "--frozen")
    with pytest.raises(ColabSessionError, match="uv is not installed"):
        memoryfence_command(tmp_path, ("model", "doctor"), which=lambda _name: None)
    with pytest.raises(ColabSessionError, match="not allowed"):
        memoryfence_command(tmp_path, ("model", "doctor;rm"), which=lambda _name: "/usr/bin/uv")
    with pytest.raises(ColabSessionError, match="not allowed"):
        memoryfence_command(tmp_path, (), which=lambda _name: "/usr/bin/uv")


def test_pilot_preview_is_the_four_development_cells(tmp_path: Path) -> None:
    config = load_pilot(ROOT)
    assert config.model_tag == PILOT_MODEL_TAG
    assert config.transformation_backend == "scripted"
    matrix = preview_pilot(ROOT)
    assert matrix.valid_count == 4
    assert {run.scenario_id for run in matrix.runs} == {"clean-note", "direct-note"}
    broken = tmp_path / "configs"
    broken.mkdir()
    (broken / "ollama-pilot.json").write_text("{", encoding="utf-8")
    with pytest.raises(ColabSessionError, match="invalid"):
        load_pilot(tmp_path)
    payload = json.loads((ROOT / "configs" / "ollama-pilot.json").read_text(encoding="utf-8"))
    payload["scenarios"] = ["heldout-clean"]
    (broken / "ollama-pilot.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ColabSessionError, match="scenarios changed"):
        load_pilot(tmp_path)
    payload["scenarios"] = ["clean-note", "direct-note"]
    payload["transformation_backend"] = "ollama"
    (broken / "ollama-pilot.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ColabSessionError, match="scripted transformations"):
        load_pilot(tmp_path)
    payload["transformation_backend"] = "scripted"
    payload["backend"] = "scripted"
    payload["model_tag"] = None
    (broken / "ollama-pilot.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ColabSessionError, match="development Ollama"):
        load_pilot(tmp_path)
    payload["backend"] = "ollama"
    payload["model_tag"] = "other:tag"
    (broken / "ollama-pilot.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ColabSessionError, match="approved tag"):
        load_pilot(tmp_path)


def test_trial_directories_stay_separate(tmp_path: Path) -> None:
    parent = tmp_path / "runs"
    parent.mkdir()
    output = pilot_output_directory(parent, STAMP)
    assert output == parent / STAMP
    assert resume_or_refuse(output, new_run=True) == "run"
    with pytest.raises(ColabSessionError, match="UTC"):
        pilot_output_directory(parent, "today")
    with pytest.raises(ColabSessionError, match="absolute"):
        pilot_output_directory(Path("relative"), STAMP)
    saved = tmp_path / "saved"
    saved.mkdir()
    (saved / "config.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ColabSessionError, match="new directory"):
        resume_or_refuse(saved, new_run=True)
    assert resume_or_refuse(saved, new_run=False) == "resume"
    with pytest.raises(ColabSessionError, match="no saved experiment"):
        resume_or_refuse(tmp_path / "empty", new_run=False)
    note = interrupt_note(saved)
    assert str(saved) in note
    assert "new directory" in note
    assert "not a result" in note


def test_metadata_requires_the_pilot_digest(tmp_path: Path) -> None:
    with pytest.raises(ColabSessionError, match="manifest is missing"):
        read_model_metadata(tmp_path)
    (tmp_path / "experiment.json").write_text("{", encoding="utf-8")
    with pytest.raises(ColabSessionError, match="manifest is invalid"):
        read_model_metadata(tmp_path)
    (tmp_path / "experiment.json").write_text(
        _manifest(backend="scripted", model_tag=None, model_digest=None).model_dump_json(),
        encoding="utf-8",
    )
    with pytest.raises(ColabSessionError, match="not the pilot model"):
        read_model_metadata(tmp_path)
    (tmp_path / "experiment.json").write_text(
        _manifest(model_digest=None).model_dump_json(),
        encoding="utf-8",
    )
    with pytest.raises(ColabSessionError, match="no model digest"):
        read_model_metadata(tmp_path)
    (tmp_path / "experiment.json").write_text(
        _manifest(prompt_template=None).model_dump_json(),
        encoding="utf-8",
    )
    with pytest.raises(ColabSessionError, match="judge version"):
        read_model_metadata(tmp_path)
    (tmp_path / "experiment.json").write_text(
        _manifest(code_version="").model_dump_json(),
        encoding="utf-8",
    )
    with pytest.raises(ColabSessionError, match="code version"):
        read_model_metadata(tmp_path)
    (tmp_path / "experiment.json").write_text(_manifest().model_dump_json(), encoding="utf-8")
    assert read_model_metadata(tmp_path).model_digest == "sha256:abc"


def test_smoke_identity_and_prose_rejection() -> None:
    chat = json.dumps(
        {"message": {"content": json.dumps({"decision": "respond", "text": "ok"})}}
    ).encode()
    identity = record_smoke_identity(LOOPBACK_ENDPOINT, PILOT_MODEL_TAG, _Chat(chat))
    assert identity.digest == "sha256:abc"
    with pytest.raises(ColabSessionError, match=r"only qwen2\.5:0\.5b"):
        record_smoke_identity(LOOPBACK_ENDPOINT, "other:tag", _Chat(chat))

    class Down:
        def request(
            self, method: str, url: str, payload: bytes | None, timeout: float
        ) -> tuple[int, bytes]:
            del method, url, payload, timeout
            raise ModelBackendError(ReasonCode.MODEL_UNAVAILABLE, "down")

    down: HttpTransport = Down()
    with pytest.raises(ColabSessionError, match="not reachable"):
        record_smoke_identity(LOOPBACK_ENDPOINT, PILOT_MODEL_TAG, down)
    prose = json.dumps({"message": {"content": "Please share_document now."}}).encode()
    with pytest.raises(ColabSessionError, match="smoke call failed"):
        record_smoke_identity(LOOPBACK_ENDPOINT, PILOT_MODEL_TAG, _Chat(prose))
    assert reject_prose_tool_request() == "error.model_output"
    with pytest.raises(ColabSessionError, match="no digest"):
        _require_identity(None)
    with pytest.raises(ColabSessionError, match="no digest"):
        _require_identity(ModelIdentity(tag=PILOT_MODEL_TAG, digest=""))


def test_archive_round_trip_and_refusals(tmp_path: Path) -> None:
    experiment = tmp_path / "experiment"
    _fill(experiment)
    destination = tmp_path / "exports"
    archive = export_pilot_archive(
        experiment,
        destination,
        revision=SHA,
        environment=_environment(),
        stamp=STAMP,
    )
    assert archive.name == f"memoryfence-colab-pilot-ollama-pilot-{SHA[:12]}-{STAMP}.zip"
    names = verify_archive(archive)
    assert "environment.json" in names
    assert "runs/0001/benchmark-result.json" in names
    with pytest.raises(ColabSessionError, match="already exists"):
        export_pilot_archive(
            experiment,
            destination,
            revision=SHA,
            environment=_environment(),
            stamp=STAMP,
        )
    with pytest.raises(ColabSessionError, match="outside the experiment"):
        export_pilot_archive(
            experiment,
            experiment / "nested",
            revision=SHA,
            environment=_environment(),
            stamp=STAMP,
        )
    with pytest.raises(ColabSessionError, match="commit and a UTC stamp"):
        export_pilot_archive(
            experiment,
            tmp_path / "elsewhere",
            revision="main",
            environment=_environment(),
            stamp=STAMP,
        )
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    with pytest.raises(ColabSessionError, match="output is missing"):
        export_pilot_archive(
            incomplete,
            destination,
            revision=SHA,
            environment=_environment(),
            stamp="20261018T132501Z",
        )
    no_result = tmp_path / "no-result"
    _fill(no_result)
    for path in (no_result / "runs").rglob("benchmark-result.json"):
        path.unlink()
    with pytest.raises(ColabSessionError, match="no benchmark result"):
        export_pilot_archive(
            no_result,
            destination,
            revision=SHA,
            environment=_environment(),
            stamp="20261018T132502Z",
        )
    owned = tmp_path / "owned"
    _fill(owned)
    (owned / "environment.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ColabSessionError, match="environment file"):
        export_pilot_archive(
            owned,
            destination,
            revision=SHA,
            environment=_environment(),
            stamp="20261018T132503Z",
        )
    invalid = tmp_path / "invalid"
    _fill(invalid, config="{")
    with pytest.raises(ColabSessionError, match="configuration is invalid"):
        export_pilot_archive(
            invalid,
            destination,
            revision=SHA,
            environment=_environment(),
            stamp="20261018T132504Z",
        )
    empty = tmp_path / "empty.zip"
    empty.write_bytes(b"")
    with pytest.raises(ColabSessionError, match="missing or empty"):
        verify_archive(empty)
    broken = tmp_path / "broken.zip"
    broken.write_text("not a zip", encoding="utf-8")
    with pytest.raises(ColabSessionError, match="integrity"):
        verify_archive(broken)
    partial = tmp_path / "partial.zip"
    with zipfile.ZipFile(partial, "w") as archive_file:
        archive_file.writestr("config.json", b"{}")
    with pytest.raises(ColabSessionError, match="missing an expected file"):
        verify_archive(partial)
    complete = tmp_path / "complete-names.zip"
    with zipfile.ZipFile(complete, "w") as archive_file:
        for name in (
            "config.json",
            "experiment.json",
            "matrix.json",
            "runs.jsonl",
            "summary.json",
            "report.md",
            "environment.json",
        ):
            archive_file.writestr(name, b"{}")
    with pytest.raises(ColabSessionError, match="no benchmark result"):
        verify_archive(complete)
    with pytest.raises(ValidationError):
        PilotEnvironment(
            repository="https://example.com/memoryfence",
            revision=SHA,
            python_version="3.12.1",
            gpu_available=False,
            model_tag=PILOT_MODEL_TAG,
            endpoint=LOOPBACK_ENDPOINT,
        )
    with pytest.raises(ValidationError):
        PilotEnvironment(
            repository="https://github.com/Yug-More/memoryfence",
            revision=SHA,
            python_version="3.12.1",
            gpu_available=False,
            model_tag="other",
            endpoint=LOOPBACK_ENDPOINT,
        )
    with pytest.raises(ValidationError):
        PilotEnvironment(
            repository="https://github.com/Yug-More/memoryfence",
            revision=SHA,
            python_version="3.12.1",
            gpu_available=False,
            model_tag=PILOT_MODEL_TAG,
            endpoint=LOOPBACK_ENDPOINT,
            label="confirmatory",
        )
    with pytest.raises(ValidationError):
        PilotEnvironment(
            repository="https://github.com/Yug-More/memoryfence",
            revision="main",
            python_version="3.12.1",
            gpu_available=False,
            model_tag=PILOT_MODEL_TAG,
            endpoint=LOOPBACK_ENDPOINT,
        )
    with pytest.raises(ValidationError):
        PilotEnvironment(
            repository="https://github.com/Yug-More/memoryfence",
            revision=SHA,
            python_version="3.12.1",
            gpu_available=False,
            model_tag=PILOT_MODEL_TAG,
            endpoint="https://example.com",
        )


def test_notebook_contract() -> None:
    validate_notebook(NOTEBOOK)
    text = NOTEBOOK.read_text(encoding="utf-8")
    assert "qwen2.5:7b" not in text
    assert "llama3" not in text.lower()
    assert text.count("pull_command(") == 1
    missing = NOTEBOOK.parent / "missing.ipynb"
    with pytest.raises(ColabSessionError, match="notebook is missing"):
        validate_notebook(missing)


def test_notebook_rejects_bad_documents(tmp_path: Path) -> None:
    payload = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    payload["cells"].append({"cell_type": "code", "metadata": {}, "source": "print('0.0.0.0')\n"})
    forbidden = tmp_path / "forbidden.ipynb"
    forbidden.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ColabSessionError, match="forbidden"):
        validate_notebook(forbidden)
    shortened = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    shortened["cells"] = [
        cell
        for cell in shortened["cells"]
        if "J. Artifact export" not in "".join(cell.get("source", []))
    ]
    cut = tmp_path / "cut.ipynb"
    cut.write_text(json.dumps(shortened), encoding="utf-8")
    with pytest.raises(ColabSessionError, match="required section"):
        validate_notebook(cut)
    stripped = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for cell in stripped["cells"]:
        source = cell.get("source", [])
        if isinstance(source, list):
            cell["source"] = [item.replace("pull_command(", "pull_skipped(") for item in source]
    step = tmp_path / "step.ipynb"
    step.write_text(json.dumps(stripped), encoding="utf-8")
    with pytest.raises(ColabSessionError, match="required step"):
        validate_notebook(step)
    raw = tmp_path / "raw.ipynb"
    raw.write_text("{", encoding="utf-8")
    with pytest.raises(ColabSessionError, match="not valid JSON"):
        validate_notebook(raw)
    for document, message in (
        ({"nbformat": 3, "cells": []}, "not supported"),
        ({"nbformat": 4, "cells": []}, "no cells"),
        ({"nbformat": 4, "cells": ["nope"]}, "unsupported cell"),
        ({"nbformat": 4, "cells": [{"cell_type": "raw", "source": ""}]}, "unsupported cell"),
        ({"nbformat": 4, "cells": [{"cell_type": "code", "source": 1}]}, "malformed"),
        (
            {"nbformat": 4, "cells": [{"cell_type": "code", "source": [1]}]},
            "malformed",
        ),
    ):
        path = tmp_path / f"{message}.ipynb"
        path.write_text(json.dumps(document), encoding="utf-8")
        with pytest.raises(ColabSessionError, match=message):
            validate_notebook(path)


def test_scripted_backend_and_cli_still_work(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert smoke_config().fingerprint() == FINGERPRINT
    preview = main(
        ["experiment", "preview", "--config", str(ROOT / "configs" / "ollama-pilot.json")]
    )
    assert preview == 0
    preview_text = capsys.readouterr().out
    assert "clean-note" in preview_text
    assert "direct-note" in preview_text
    directory = tmp_path / "smoke"
    assert main(["experiment", "smoke", "--directory", str(directory)]) == 0
    assert main(["model", "doctor", "--endpoint", "http://example.com"]) == 2


def test_notebook_project_steps_run_in_an_isolated_interpreter(tmp_path: Path) -> None:
    import ast

    notebook = json.loads(NOTEBOOK.read_text())
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            tree = ast.parse("".join(cell["source"]))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "run_project"
                    and node.args
                ):
                    ast.parse(ast.literal_eval(node.args[0]))
    setup = ast.parse("".join(notebook["cells"][4]["source"]))
    function = next(
        n for n in setup.body if isinstance(n, ast.FunctionDef) and n.name == "run_project"
    )
    state = tmp_path / "state.json"
    namespace = {
        "ROOT": ROOT,
        "STATE_FILE": state,
        "IN_COLAB": True,
        "REVISION": SHA,
        "FROZEN": True,
        "SCHEMA_OUTPUT": True,
        "PILOT_CONFIG": "configs/ollama-schema-pilot.json",
        "subprocess": subprocess,
    }
    exec(  # noqa: S102
        compile(ast.Module(body=[function], type_ignores=[]), "notebook-runner", "exec"), namespace
    )
    run = namespace["run_project"]
    assert callable(run)
    run('STAMP = "isolated-test"\nprint("project subprocess imported successfully")')
    assert json.loads(state.read_text())["STAMP"] == "isolated-test"
    with pytest.raises(RuntimeError, match="Project step failed"):
        run('STAMP = "failure-preserved"\nraise SystemExit(2)')
    assert json.loads(state.read_text())["STAMP"] == "failure-preserved"
