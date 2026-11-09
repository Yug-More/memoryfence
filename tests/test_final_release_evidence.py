"""Independently recompute the new accession and availability failure evidence."""

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_reproduction_and_failure_analysis(tmp_path: Path) -> None:
    accession = ROOT / "experiments/2026-11-08-finalization"
    analyze = runpy.run_path(str(ROOT / "scripts/research/analyze_release.py"))["analyze"]
    output = tmp_path / "analysis.json"
    analyze(
        ROOT / "experiments/2026-11-07-expanded/expanded-v1.zip.xz",
        accession / "reproduction.zip.xz",
        output,
    )
    assert json.loads(output.read_text()) == json.loads(
        (accession / "failure-analysis.json").read_text()
    )
    manifest = json.loads((accession / "model-availability/manifest.json").read_text())
    assert manifest["status"] == "blocked"
    assert manifest["actual_chat_requests"] == 0
    assert manifest["attack_success"] is None
    events = [
        json.loads(line)
        for line in (accession / "model-availability/http.jsonl").read_text().splitlines()
    ]
    assert not any(e["event"] == "request" and e["url"].endswith("/api/chat") for e in events)
