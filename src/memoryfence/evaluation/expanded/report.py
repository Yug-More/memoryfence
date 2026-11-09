"""Cluster-aware descriptive summaries; deterministic results are not model ASR."""

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .validation import validate_records

METRICS = (
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
)


def summarize(directory: Path) -> dict[str, Any]:
    records = json.loads((directory / "records.json").read_text())
    manifest = json.loads((directory / "manifest.json").read_text())
    validate_records(records, manifest, directory)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in records:
        key = f"{r['split']}/{r['control']}/{r['strategy']}"
        grouped[key].append(r)
        if r["strategy"] in by_case[r["scenario_id"]]:
            raise ValueError("duplicate paired strategy record")
        by_case[r["scenario_id"]][r["strategy"]] = r
    groups = {}
    for key, values in sorted(grouped.items()):
        completed = [r for r in values if r["status"] == "completed"]
        metrics = {}
        for metric in METRICS:
            defined = [
                float(r["metrics"][metric]["rate"])
                for r in completed
                if r["metrics"][metric]["rate"] is not None
            ]
            metrics[metric] = {
                "defined_cases": len(defined),
                "undefined_cases": len(completed) - len(defined),
                "case_macro_mean": statistics.mean(defined) if defined else None,
            }
        eligible = [r for r in completed if r["metrics"]["attack_eligible"]]
        groups[key] = {
            "planned_cases": len(values),
            "valid_cases": len(completed),
            "invalid_cases": len(values) - len(completed),
            "metrics": metrics,
            "attack_exposed": sum(r["metrics"]["exposure"] for r in eligible),
            "attack_eligible": len(eligible),
            "model_calls": 0,
            "timing_medians_ms": {
                phase: statistics.median(r["timings_ms"][phase] for r in completed)
                if completed
                else None
                for phase in ("deletion", "recomputation", "retrieval")
            },
        }
    # Collapse all eligible counterfactual case deltas inside each family before
    # describing between-family variation. This is not 560 independent samples.
    paired: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for strategies in by_case.values():
        proposed = strategies.get("memoryfence")
        if proposed is None or proposed["status"] != "completed":
            continue
        for baseline, record in strategies.items():
            if baseline == "memoryfence" or record["status"] != "completed":
                continue
            for metric in METRICS:
                a = proposed["metrics"][metric]["rate"]
                b = record["metrics"][metric]["rate"]
                if a is None or b is None:
                    continue
                key = f"{record['split']}/{baseline}/{metric}"
                paired[key][record["family"]].append(a - b)
    pairs = {}
    for key, families in sorted(paired.items()):
        means = {family: statistics.mean(values) for family, values in sorted(families.items())}
        family_values = list(means.values())
        pairs[key] = {
            "families": len(family_values),
            "family_mean_deltas": means,
            "macro_delta": statistics.mean(family_values),
            "family_delta_range": [min(family_values), max(family_values)],
            "interpretation": "descriptive paired fixture deltas, not population efficacy",
        }
    return {
        "version": "expanded-v1",
        "model_calls": 0,
        "classification": "deterministic Expanded Study; behavior unmeasured",
        "planned_runs": len(records),
        "valid_runs": sum(r["status"] == "completed" for r in records),
        "invalid_runs": sum(r["status"] != "completed" for r in records),
        "distinct_families": len({r["family"] for r in records}),
        "groups": groups,
        "paired_family_deltas": pairs,
        "uncertainty": (
            "Finite fixed design: exact fixture outcomes, family ranges; "
            "no binomial CI or significance claim"
        ),
        "attack_success": None,
        "unauthorized_tool_action": None,
        "llm_utility": None,
    }
