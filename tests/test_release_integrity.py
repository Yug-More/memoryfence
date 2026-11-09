"""Adversarial reporting/export checks, not model-performance experiments."""

import io
import json
import lzma
import zipfile
from pathlib import Path

import pytest

from memoryfence.cli import main
from memoryfence.domain.errors import MemoryFenceError
from memoryfence.evaluation.expanded.cli import export
from memoryfence.evaluation.expanded.report import summarize

ROOT = Path(__file__).resolve().parents[1]


def materialize(path: Path) -> list[dict[str, object]]:
    archive = ROOT / "experiments/2026-11-07-expanded/expanded-v1.zip.xz"
    with zipfile.ZipFile(io.BytesIO(lzma.decompress(archive.read_bytes()))) as saved:
        for name in ("records.json", "manifest.json", "dataset.json"):
            (path / name).write_bytes(saved.read(name))
    result: list[dict[str, object]] = json.loads((path / "records.json").read_text())
    return result


@pytest.mark.parametrize(
    "fault", ["strategy", "case", "cohort", "nan", "fraction", "behavior", "missing"]
)
def test_reporting_rejects_corrupt_complete_count_grid(tmp_path: Path, fault: str) -> None:
    records = materialize(tmp_path)
    if fault == "strategy":
        records[0]["strategy"] = "invented"
    elif fault == "case":
        records[0]["scenario_id"] = "undeclared"
    elif fault == "cohort":
        records[0]["split"] = "evaluation"
    else:
        metrics = records[0]["metrics"]
        assert isinstance(metrics, dict)
        if fault == "nan":
            metrics["persistence"]["rate"] = float("nan")
        elif fault == "fraction":
            metrics["persistence"]["numerator"] = 999
        elif fault == "behavior":
            metrics["attack_success"] = 0
        else:
            del metrics["benign_retention"]
    (tmp_path / "records.json").write_text(json.dumps(records))
    with pytest.raises(ValueError, match=r"strategy|grid|metadata|metric|inference"):
        summarize(tmp_path)
    assert main(["expanded", "summarize", "--directory", str(tmp_path)]) == 2


def test_duplicate_and_missing_observations_are_not_replaced_by_equal_row_count(
    tmp_path: Path,
) -> None:
    records = materialize(tmp_path)
    records[-1] = records[0]
    (tmp_path / "records.json").write_text(json.dumps(records))
    with pytest.raises(ValueError, match="duplicate"):
        summarize(tmp_path)
    (tmp_path / "records.json").write_text("[")
    assert main(["expanded", "summarize", "--directory", str(tmp_path)]) == 2


@pytest.mark.parametrize("directory_link", [False, True])
def test_export_rejects_symlinks_without_creating_output(
    tmp_path: Path, directory_link: bool
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.txt").write_text("public test sentinel")
    run = tmp_path / "run"
    run.mkdir()
    (run / "escape").symlink_to(outside if directory_link else outside / "sentinel.txt")
    archive = tmp_path / "output.zip.xz"
    with pytest.raises(MemoryFenceError, match="symbolic"):
        export(run, archive)
    assert not archive.exists()


def test_both_historical_accessions_are_immutable() -> None:
    import runpy

    verify = runpy.run_path(str(ROOT / "scripts/research/verify_release.py"))["verify"]
    assert verify() == {"original": 53, "expanded": 12}


def test_dataset_rejects_path_traversal_scenario_id() -> None:
    from pydantic import ValidationError

    from memoryfence.evaluation.expanded.dataset import Benchmark

    data = json.loads((ROOT / "benchmarks/expanded-v1/scenarios.json").read_text())
    data["scenarios"][0]["id"] = "../outside"
    with pytest.raises(ValidationError, match="pattern"):
        Benchmark.model_validate_json(json.dumps(data))
