"""Mechanical sensitivity boundaries, independent of generated model text."""

import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def test_exhaustive_sensitivity_matches_preserved_results() -> None:
    enumerate_chains = runpy.run_path(str(ROOT / "scripts/research/sensitivity.py"))[
        "enumerate_chains"
    ]
    result: dict[str, Any] = enumerate_chains()
    assert result == json.loads((ROOT / "paper/generated/chain-sensitivity.json").read_text())
    assert result["configurations"] == 278
    assert result["model_calls"] == 0
    assert len({(r["depth"], r["mask"]) for r in result["rows"]}) == 278
    for depth in (1, 2, 4, 8):
        rows = [r for r in result["rows"] if r["depth"] == depth]
        assert len(rows) == 2**depth
        # Sum of connected prefix lengths over all masks = 2**d - 1.
        assert sum(depth - r["cascade_survivors"] for r in rows) == 2**depth - 1
        assert rows[0]["cascade_survivors"] == depth
        assert rows[-1]["cascade_survivors"] == 0


def test_equal_edge_counts_have_different_cascade_reach() -> None:
    data = json.loads((ROOT / "paper/generated/chain-sensitivity.json").read_text())
    pairs = {r["mask"]: r for r in data["rows"] if r["depth"] == 2}
    assert pairs[1]["retained_edges"] == pairs[2]["retained_edges"] == 1
    assert pairs[1]["cascade_survivors"] == 1
    assert pairs[2]["cascade_survivors"] == 2
