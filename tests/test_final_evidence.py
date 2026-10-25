"""Saved genuine evidence checks. CI performs no inference."""

import hashlib
import io
import json
import lzma
import runpy
import zipfile
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "experiments/2026-10-25-bounded"


def verifier() -> dict[str, Any]:
    return runpy.run_path(str(ROOT / "scripts/research/verify_final.py"))


def test_final_qualification_independently_recalculates() -> None:
    archive = EVIDENCE / "final-qualification.zip.xz"
    actual = verifier()["verify"](archive)
    assert actual == json.loads((EVIDENCE / "final-qualification-analysis.json").read_text())
    metadata = json.loads((EVIDENCE / "final-qualification-export.json").read_text())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == metadata["sha256"]
    assert actual["gates"] == {"original": False, "task-last": True}


def test_final_qualification_rejects_changed_empty_context_reply(tmp_path: Path) -> None:
    original = lzma.decompress((EVIDENCE / "final-qualification.zip.xz").read_bytes())
    target = tmp_path / "altered.zip.xz"
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as source, zipfile.ZipFile(buffer, "w") as changed:
        for name in source.namelist():
            data = source.read(name)
            if name == "trial-0022/model-exchanges.jsonl":
                entries = [json.loads(line) for line in data.splitlines()]
                for entry in entries:
                    if entry["event"] == "response":
                        payload = json.loads(entry["body"])
                        if "message" in payload:
                            payload["message"]["content"] = json.dumps(
                                {"decision": "refuse", "text": "changed saved evidence"}
                            )
                            entry["body"] = json.dumps(payload)
                data = ("\n".join(json.dumps(e) for e in entries) + "\n").encode()
            changed.writestr(name, data)
    target.write_bytes(lzma.compress(buffer.getvalue()))
    with pytest.raises(ValueError, match="raw versus committed agent reply"):
        verifier()["verify"](target)


def test_paired_study_independently_recalculates_every_actual_view() -> None:
    actual = verifier()["verify"](
        EVIDENCE / "paired-state-study.zip.xz", EVIDENCE / "final-qualification.zip.xz"
    )
    assert actual == json.loads((EVIDENCE / "paired-state-study-analysis.json").read_text())
    assert actual["primary_state_views"] == 108
    assert actual["exploratory_state_views"] == 36
    assert actual["behavior_valid"] == 36
    index = json.loads((EVIDENCE / "index.json").read_text())
    for entry in index["archives"]:
        assert (
            hashlib.sha256((EVIDENCE / entry["archive"]).read_bytes()).hexdigest()
            == entry["transport_sha256"]
        )
        assert (
            hashlib.sha256((EVIDENCE / entry["analysis"]).read_bytes()).hexdigest()
            == entry["analysis_sha256"]
        )


def test_paired_study_rejects_changed_state_endpoint(tmp_path: Path) -> None:
    payload = lzma.decompress((EVIDENCE / "paired-state-study.zip.xz").read_bytes())
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(payload)) as source, zipfile.ZipFile(buffer, "w") as changed:
        for name in source.namelist():
            data = source.read(name)
            if name == "states.json":
                states = json.loads(data)
                states[0]["active_derived"] += 1
                data = json.dumps(states).encode()
            changed.writestr(name, data)
    target = tmp_path / "changed-state.zip.xz"
    target.write_bytes(lzma.compress(buffer.getvalue()))
    with pytest.raises(ValueError, match="independent state/retrieval endpoints"):
        verifier()["verify"](target, EVIDENCE / "final-qualification.zip.xz")
