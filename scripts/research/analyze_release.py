"""Categorize every expanded condition and compare a new deterministic execution."""

import argparse
import io
import json
import lzma
import runpy
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def records(path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(lzma.decompress(path.read_bytes()))) as archive:
        result: list[dict[str, Any]] = json.loads(archive.read("records.json"))
        return result


def analyze(original: Path, repeated: Path, output: Path) -> None:
    verifier = runpy.run_path(str(ROOT / "scripts/research/verify_expanded.py"))["verify"]
    old_verification, new_verification = verifier(original), verifier(repeated)
    old, new = records(original), records(repeated)

    def semantic(items: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
        return {
            (r["scenario_id"], r["strategy"]): {
                k: v for k, v in r.items() if k not in {"timings_ms", "sqlite_bytes"}
            }
            for r in items
        }

    left, right = semantic(old), semantic(new)
    if left != right:
        raise ValueError("deterministic semantic reproduction differs; preserve both accessions")
    groups = {}
    for key in sorted({f"{r['split']}/{r['control']}/{r['strategy']}" for r in old}):
        selected = [r for r in old if f"{r['split']}/{r['control']}/{r['strategy']}" == key]
        eligible = [r for r in selected if r["metrics"]["attack_eligible"]]
        benign = [r for r in selected if r["metrics"]["benign_retention"]["denominator"]]
        examples = {}
        for category, candidates in [
            ("malicious_context", [r for r in eligible if r["metrics"]["exposure"]]),
            (
                "benign_fact_loss",
                [r for r in benign if r["metrics"]["benign_fact_loss"]["numerator"]],
            ),
            (
                "physical_target_survival",
                [r for r in selected if r["metrics"]["persistence"]["numerator"]],
            ),
            (
                "lookup_failure",
                [
                    r
                    for r in selected
                    if r["metrics"]["fact_lookup_success"]["denominator"]
                    and not r["metrics"]["fact_lookup_success"]["numerator"]
                ],
            ),
        ]:
            examples[category] = (
                None
                if not candidates
                else {
                    "scenario_id": candidates[0]["scenario_id"],
                    "member": (
                        f"runs/{candidates[0]['scenario_id']}/"
                        f"{candidates[0]['strategy']}/result.json"
                    ),
                }
            )
        groups[key] = {
            "cases": len(selected),
            "families": len({r["family"] for r in selected}),
            "exposed_attack_cases": {
                "numerator": sum(r["metrics"]["exposure"] for r in eligible),
                "denominator": len(eligible),
            },
            "cases_losing_benign_facts": {
                "numerator": sum(r["metrics"]["benign_fact_loss"]["numerator"] > 0 for r in benign),
                "denominator": len(benign),
            },
            "lost_benign_facts": {
                "numerator": sum(r["metrics"]["benign_fact_loss"]["numerator"] for r in benign),
                "denominator": sum(r["metrics"]["benign_fact_loss"]["denominator"] for r in benign),
            },
            "representative_examples": examples,
        }
    result = {
        "classification": "post-hoc descriptive failure categorization, no new inference",
        "original_verification": old_verification,
        "repeated_verification": new_verification,
        "semantic_records_equal": len(left),
        "excluded_comparison_fields": ["timings_ms", "sqlite_bytes"],
        "interpretation": "Repeat execution does not increase independent scientific sample size",
        "groups": groups,
    }
    with output.open("x") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--repeated", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.original, args.repeated, args.output)
