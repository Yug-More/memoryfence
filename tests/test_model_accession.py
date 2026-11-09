"""Actual saved inference evidence, recomputed without making inference calls."""

import io
import json
import lzma
import runpy
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_actual_model_accession_from_raw_journal_and_sqlite(tmp_path: Path) -> None:
    accession = ROOT / "experiments/2026-11-09-model-followup"
    with zipfile.ZipFile(
        io.BytesIO(lzma.decompress((accession / "model-followup.zip.xz").read_bytes()))
    ) as archive:
        for name in archive.namelist():
            target = tmp_path / name
            assert tmp_path in target.resolve().parents
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    verify = runpy.run_path(str(ROOT / "scripts/research/verify_model_followup.py"))["verify"]
    result = verify(tmp_path, ROOT / "experiments/2026-11-07-expanded/expanded-v1.zip.xz")
    assert result == json.loads((accession / "independent-verification.json").read_text())
