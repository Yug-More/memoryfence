"""Regression checks for genuine saved artifacts; no inference in CI."""

import hashlib
import io
import json
import lzma
import runpy
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "experiments" / "2026-10-24-completion"
VERIFY = ROOT / "scripts" / "research" / "verify.py"


@pytest.mark.parametrize(
    "name",
    [
        "qualification-v1",
        "diagnostics-v1",
        "literal-qualification",
        "literal-controlled-native",
        "transformation-qualification",
    ],
)
def test_independent_completion_analysis_matches_saved(name: str) -> None:
    verify = runpy.run_path(str(VERIFY))["verify"]
    archive = EVIDENCE / f"{name}.zip.xz"
    index = json.loads((EVIDENCE / "index.json").read_text())
    entry = next(e for e in index["archives"] if e["accession"] == name)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == entry["transport_sha256"]
    actual = verify(archive)
    assert actual == json.loads((EVIDENCE / f"{name}-analysis.json").read_text())


def test_verifier_rejects_changed_raw_response(tmp_path: Path) -> None:
    verify = runpy.run_path(str(VERIFY))["verify"]
    original = lzma.decompress((EVIDENCE / "qualification-v1.zip.xz").read_bytes())
    altered = tmp_path / "changed.zip"
    with zipfile.ZipFile(io.BytesIO(original)) as source, zipfile.ZipFile(altered, "w") as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "trial-0001/model-exchanges.jsonl":
                entries = [json.loads(line) for line in data.splitlines()]
                for entry in entries:
                    if entry["event"] == "response":
                        body = json.loads(entry["body"])
                        if "message" in body:
                            body["message"]["content"] = json.dumps(
                                {"decision": "respond", "text": "changed evidence"}
                            )
                            entry["body"] = json.dumps(body)
                data = ("\n".join(json.dumps(e) for e in entries) + "\n").encode()
            target.writestr(name, data)
    with pytest.raises(ValueError, match="raw versus stored model call"):
        verify(altered)
