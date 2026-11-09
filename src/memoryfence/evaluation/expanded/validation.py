"""Reject incomplete/corrupt comparisons before computing any summary."""

import math
from pathlib import Path
from typing import Any

from .dataset import dataset_hash, load
from .runner import STRATEGIES


def validate_records(
    records: list[dict[str, Any]], manifest: dict[str, Any], directory: Path
) -> None:
    if type(manifest.get("planned_runs")) is not int or len(records) != manifest["planned_runs"]:
        raise ValueError("partial Expanded Study: preserve records and report incomplete")
    if not records:
        raise ValueError("empty comparison has no planned case grid")
    cases: dict[str, dict[str, Any]] = {}
    if (directory / "dataset.json").exists():
        benchmark = load(directory / "dataset.json")
        if manifest.get("dataset_sha256") != dataset_hash(directory / "dataset.json"):
            raise ValueError("manifest dataset hash mismatch")
        split = manifest.get("split", "all")
        if split not in {"all", "development", "evaluation"}:
            raise ValueError("invalid manifest split")
        cases = {
            c.id: c.model_dump(mode="json")
            for c in benchmark.scenarios
            if split == "all" or c.split == split
        }
        if len(cases) * len(STRATEGIES) != manifest["planned_runs"]:
            raise ValueError("manifest and dataset grid disagree")
        if manifest.get("strategies") != list(STRATEGIES):
            raise ValueError("manifest strategies disagree")
    observed: dict[str, set[str]] = {}
    metadata: dict[str, tuple[object, ...]] = {}
    for record in records:
        case_id, strategy = record["scenario_id"], record["strategy"]
        if strategy not in STRATEGIES:
            raise ValueError("unknown paired strategy")
        seen = observed.setdefault(case_id, set())
        if strategy in seen:
            raise ValueError("duplicate paired strategy record")
        seen.add(strategy)
        signature = tuple(record[k] for k in ("family", "split", "control", "seed"))
        if metadata.setdefault(case_id, signature) != signature:
            raise ValueError("paired case metadata disagree")
        if cases and (
            case_id not in cases
            or signature != tuple(cases[case_id][k] for k in ("family", "split", "control", "seed"))
        ):
            raise ValueError("record is outside the declared case grid")
        if record["status"] not in {"completed", "invalid"}:
            raise ValueError("unknown execution status")
        if record["status"] == "invalid":
            if record.get("metrics") is not None or not record.get("error"):
                raise ValueError("invalid record must preserve an error and no metrics")
            continue
        metrics = record["metrics"]
        required = {
            "persistence",
            "accessible_persistence",
            "target_fact_persistence",
            "deletion_completeness",
            "benign_retention",
            "benign_fact_loss",
            "benign_artifact_overdeletion",
            "malicious_retrieval",
            "fact_lookup_success",
            "retrieval_precision",
            "retrieval_recall",
            "provenance_coverage",
        }
        if not required <= metrics.keys() or any(
            not isinstance(metrics[n], dict) for n in required
        ):
            raise ValueError("missing ratio metrics")
        if (
            type(metrics.get("attack_eligible")) is not bool
            or type(metrics.get("exposure")) is not bool
        ):
            raise ValueError("invalid attack eligibility or exposure")
        for name, metric in metrics.items():
            if not isinstance(metric, dict):
                continue
            numerator, denominator, rate = (metric[k] for k in ("numerator", "denominator", "rate"))
            if (
                type(numerator) is not int
                or type(denominator) is not int
                or not 0 <= numerator <= denominator
            ):
                raise ValueError(f"invalid metric counts: {name}")
            if denominator == 0:
                valid = rate is None
            else:
                valid = (
                    type(rate) in {int, float}
                    and math.isfinite(rate)
                    and math.isclose(rate, numerator / denominator, abs_tol=1e-12)
                )
            if not valid:
                raise ValueError(f"invalid metric rate: {name}")
        for name in ("attack_success", "unauthorized_tool_action", "llm_legitimate_success"):
            if metrics.get(name) is not None:
                raise ValueError("deterministic record contains behavioral inference")
        if metrics.get("model_calls") != 0:
            raise ValueError("deterministic record contains model calls")
        if set(record["timings_ms"]) != {"deletion", "recomputation", "retrieval"}:
            raise ValueError("missing phase timings")
        if any(not math.isfinite(v) or v < 0 for v in record["timings_ms"].values()):
            raise ValueError("invalid observed timing")
    if any(seen != set(STRATEGIES) for seen in observed.values()):
        raise ValueError("incomplete paired strategy grid")
    if cases and set(observed) != set(cases):
        raise ValueError("incomplete declared case grid")
