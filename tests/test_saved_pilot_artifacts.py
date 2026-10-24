"""Check preserved evidence integrity without inference or production evaluators."""

import hashlib
import json
import lzma
import runpy
from pathlib import Path


def test_saved_pilot_hashes_and_independent_analysis() -> None:
    folder = Path(__file__).resolve().parents[1] / "experiments" / "2026-10-24-colab"
    manifest = json.loads((folder / "manifest.json").read_text())
    analyze = runpy.run_path(str(folder / "analyze.py"))["analyze"]
    regenerated = []
    for run in manifest["runs"]:
        path = folder / run["archive"]
        transport = path.read_bytes()
        assert hashlib.sha256(transport).hexdigest() == run["transport_sha256"]
        original = lzma.decompress(transport)
        assert hashlib.sha256(original).hexdigest() == run["original_zip_sha256"]
        assert len(original) == run["original_zip_bytes"]
        result = analyze(path)
        assert len(result["trials"]) == run["completed_cells"]
        regenerated.append(result)
    diagnostic = manifest["diagnostics"]
    assert (
        hashlib.sha256((folder / diagnostic["archive"]).read_bytes()).hexdigest()
        == diagnostic["sha256"]
    )
    assert regenerated == json.loads((folder / "independent-analysis.json").read_text())
