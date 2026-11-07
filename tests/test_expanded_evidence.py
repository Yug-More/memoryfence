"""Regression of the committed accession, including independent raw-state checks."""

import io
import json
import lzma
import runpy
import zipfile
from pathlib import Path

from memoryfence.evaluation.expanded.report import summarize

ROOT = Path(__file__).resolve().parents[1]


def test_saved_expanded_evidence_and_family_summary(tmp_path: Path) -> None:
    accession = ROOT / "experiments/2026-11-07-expanded"
    archive = accession / "expanded-v1.zip.xz"
    verify = runpy.run_path(str(ROOT / "scripts/research/verify_expanded.py"))["verify"]
    assert verify(archive) == json.loads((accession / "independent-verification.json").read_text())
    with zipfile.ZipFile(io.BytesIO(lzma.decompress(archive.read_bytes()))) as saved:
        assert (
            saved.read("dataset.json")
            == (ROOT / "benchmarks/expanded-v1/scenarios.json").read_bytes()
        )
        for name in ("records.json", "manifest.json"):
            (tmp_path / name).write_bytes(saved.read(name))
        assert saved.read("summary.json") == (accession / "summary.json").read_bytes()
    assert summarize(tmp_path) == json.loads((accession / "summary.json").read_text())
    assert runpy.run_path(str(ROOT / "scripts/research/verify_legacy.py"))["verify"]() == 53
