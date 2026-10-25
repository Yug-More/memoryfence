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
