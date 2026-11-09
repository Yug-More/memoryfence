"""Transport fixtures validate the harness, never model behavior or attack efficacy."""

import json
import runpy
from pathlib import Path

import pytest
from pydantic import ValidationError

from memoryfence.domain.errors import DomainValidationError, ModelBackendError, ReasonCode

ROOT = Path(__file__).resolve().parents[1]
API = runpy.run_path(str(ROOT / "scripts/research/model_followup.py"))


class FixtureTransport:
    def __init__(
        self, *, missing: bool = False, gate: bool = False, fail_probe: bool = False
    ) -> None:
        self.missing, self.gate, self.fail_probe = missing, gate, fail_probe
        self.calls = 0

    def request(
        self, method: str, url: str, payload: bytes | None, timeout: float
    ) -> tuple[int, bytes]:
        result: dict[str, object]
        if url.endswith("/api/tags"):
            result = {
                "models": [] if self.missing else [{"name": "fixture:tiny", "digest": "fixture"}]
            }
        elif url.endswith("/api/show"):
            result = {"details": {"parameter_size": "fixture", "quantization_level": "fixture"}}
        elif url.endswith("/api/version"):
            result = {"version": "fixture"}
        else:
            assert url.endswith("/api/chat")
            assert method == "POST"
            assert payload
            self.calls += 1
            request = json.loads(payload)
            assert request["options"]["temperature"] == 0
            if self.fail_probe and self.calls == 5:
                raise ModelBackendError(ReasonCode.MODEL_TIMEOUT, "fixture timeout")
            result = {
                "message": {
                    "content": json.dumps(
                        {"decision": "respond", "text": "fixture abstention"}
                        if self.gate
                        else {
                            "decision": "propose",
                            "text": "fixture",
                            "tool": "create_ticket",
                            "arguments": {"title": "review", "body": "status"},
                        }
                    )
                }
            }
        return 200, json.dumps(result).encode()


def configuration() -> dict[str, object]:
    data: dict[str, object] = json.loads(
        (ROOT / "benchmarks/model-followup-v1/config.json").read_text()
    )
    data.update(model_tag="fixture:tiny", expected_digest=None)
    return data


def test_followup_configuration_is_local_bounded_and_finite(tmp_path: Path) -> None:
    data = configuration()
    data["endpoint"] = "https://example.com"
    with pytest.raises((ValueError, DomainValidationError), match=r"loopback|http"):
        API["ProbeConfig"].model_validate(data)
    data = configuration()
    data["temperature"] = float("nan")
    with pytest.raises(ValidationError, match="finite"):
        API["ProbeConfig"].model_validate(data)
    data = configuration()
    data["max_calls"] = 1
    config = API["ProbeConfig"].model_validate(data)
    with pytest.raises(ValueError, match="budget"):
        API["execute"](config, tmp_path / "budget", FixtureTransport())
    assert not (tmp_path / "budget").exists()


@pytest.mark.parametrize("failure", ["missing", "gate", "timeout"])
def test_model_probe_failure_evidence_and_no_scripted_fallback(
    tmp_path: Path, failure: str
) -> None:
    config = API["ProbeConfig"].model_validate(configuration())
    transport = FixtureTransport(
        missing=failure == "missing", gate=failure == "gate", fail_probe=failure == "timeout"
    )
    result = API["execute"](config, tmp_path / "run", transport)
    verifier = runpy.run_path(str(ROOT / "scripts/research/verify_model_followup.py"))["verify"]
    verified = verifier(tmp_path / "run", config.archive)
    assert verified["chat_requests"] == result["actual_chat_requests"]
    if failure == "missing":
        assert result["status"] == "blocked"
        assert result["actual_chat_requests"] == 0
        assert result["attack_success"] is None
    elif failure == "gate":
        assert result["status"] == "qualification_failed"
        assert result["actual_chat_requests"] == 4
        assert not (tmp_path / "run/probes.json").exists()
    else:
        assert result["status"] == "completed_with_invalids"
        assert result["valid_probes"] == 69
        assert result["invalid_probes"] == 1
        assert result["actual_chat_requests"] == 74
        records = json.loads((tmp_path / "run/probes.json").read_text())
        assert len(records) == 70
        assert sum(r["status"] == "invalid" for r in records) == 1
        assert result["legitimate_success"] == {"numerator": 69, "denominator": 69}
        with pytest.raises(FileExistsError):
            API["execute"](config, tmp_path / "run", transport)


def test_model_followup_rejects_invalid_source_before_any_request(tmp_path: Path) -> None:
    import io
    import lzma
    import zipfile

    source = ROOT / "experiments/2026-11-07-expanded/expanded-v1.zip.xz"
    stream = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(lzma.decompress(source.read_bytes()))) as saved,
        zipfile.ZipFile(stream, "w") as changed,
    ):
        records = json.loads(saved.read("records.json"))
        first = records[0]
        first.update(status="invalid", error="fixture failure", metrics=None)
        member = f"runs/{first['scenario_id']}/{first['strategy']}/result.json"
        for name in saved.namelist():
            payload = saved.read(name)
            if name == "records.json":
                payload = json.dumps(records).encode()
            elif name == member:
                payload = json.dumps(first).encode()
            changed.writestr(name, payload)
    archive = tmp_path / "invalid.zip.xz"
    archive.write_bytes(lzma.compress(stream.getvalue()))
    data = configuration()
    data["archive"] = archive
    config = API["ProbeConfig"].model_validate(data)
    transport = FixtureTransport()
    with pytest.raises(ValueError, match="valid source"):
        API["execute"](config, tmp_path / "run", transport)
    assert transport.calls == 0
    assert not (tmp_path / "run").exists()


def test_independent_model_verifier_detects_forged_effect(tmp_path: Path) -> None:
    config = API["ProbeConfig"].model_validate(configuration())
    directory = tmp_path / "model"
    API["execute"](config, directory, FixtureTransport())
    verifier = runpy.run_path(str(ROOT / "scripts/research/verify_model_followup.py"))["verify"]
    assert verifier(directory, config.archive)["valid_probes"] == 70
    outcomes = json.loads((directory / "probes.json").read_text())
    outcomes[0]["legitimate_effect"] = False
    row = outcomes[0]
    (
        directory / row["scenario_id"] / row["strategy"] / str(row["seed"]) / "result.json"
    ).write_text(json.dumps(row))
    (directory / "probes.json").write_text(json.dumps(outcomes))
    with pytest.raises(ValueError, match="objective score"):
        verifier(directory, config.archive)
