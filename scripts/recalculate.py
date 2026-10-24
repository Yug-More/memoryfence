"""Independently recalculate condition counts using only the Python standard library.

No MemoryFence evaluator imports. Checks exported summaries against per-cell result
files. This checks arithmetic and populations, not authenticity of model execution.
"""

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist


def recalculate(directory: Path) -> dict[str, object]:
    config = json.loads((directory / "config.json").read_text())
    matrix = json.loads((directory / "matrix.json").read_text())
    grouped: dict[str, list[dict[str, object]]] = {}
    for planned in matrix["runs"]:
        result = json.loads(
            (directory / "runs" / f"{planned['ordinal']:04d}" / "benchmark-result.json").read_text()
        )
        key = "/".join(
            str(result[name])
            for name in (
                "scenario_id",
                "defense",
                "retrieval_variant",
                "deletion_policy",
                "fidelity",
            )
        )
        grouped.setdefault(key, []).append(result)
    reported = json.loads((directory / "condition-summary.json").read_text())
    recomputed: dict[str, object] = {}
    for key, rows in grouped.items():
        complete = [r for r in rows if r["failure_reason"] is None and r["stages"] is not None]
        adjudicated = [r for r in complete if r["judge_status"] not in {"abstain", "invalid"}]
        condition = reported[key]
        measured: dict[str, object] = {}
        for name in ("retrieved", "followed", "proposed", "executed"):
            sample = adjudicated if name == "followed" else complete
            # JSON boundary: every input is validated independently here.
            stages = [r["stages"] for r in sample]
            if not all(isinstance(s, dict) and isinstance(s.get(name), bool) for s in stages):
                raise ValueError("invalid stage record")
            successes = sum(bool(s[name]) for s in stages if isinstance(s, dict))
            count = len(sample)
            expected = condition["rates"][name]
            if expected["successes"] != successes or expected["trials"] != count:
                raise ValueError(f"denominator or numerator mismatch: {key}/{name}")
            bounds = _wilson(successes, count)
            if count and any(
                not math.isclose(expected[field], value, abs_tol=1e-12)
                for field, value in zip(("lower", "upper"), bounds, strict=True)
            ):
                raise ValueError(f"interval mismatch: {key}/{name}")
            measured[name] = {"successes": successes, "trials": count, "wilson95": bounds}
        if condition["counts"]["invalid"] != len(rows) - len(complete):
            raise ValueError(f"invalid-count mismatch: {key}")
        recomputed[key] = measured
    if set(recomputed) != set(reported):
        raise ValueError("condition inventory mismatch")
    return {
        "analysis_kind": "independent arithmetic verification",
        "backend": config["backend"],
        "planned_cells": len(matrix["runs"]),
        "conditions": recomputed,
        "authenticity_verified": False,
    }


def _wilson(successes: int, trials: int) -> list[float]:
    if not trials:
        return []
    z = NormalDist().inv_cdf(0.975)
    fraction = successes / trials
    denominator = 1 + z * z / trials
    center = (fraction + z * z / (2 * trials)) / denominator
    radius = (
        z
        / denominator
        * math.sqrt(fraction * (1 - fraction) / trials + z * z / (4 * trials * trials))
    )
    return [max(0, center - radius), min(1, center + radius)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(recalculate(args.directory), indent=2))
