"""Verify expanded raw evidence and generate descriptive tables and scientific plots.

Optional plotting environment only; no runtime dependency or inference is added.
"""

import argparse
import io
import json
import lzma
import runpy
import statistics
import zipfile
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
STRATEGIES = (
    "source_only",
    "keyword",
    "direct",
    "cascade",
    "rederive",
    "quarantine",
    "memoryfence",
)
CONTROLS = ("attack_complete", "attack_marked", "attack_silent", "clean", "never_exposed")


def describe(values: list[float]) -> dict[str, float | int]:
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {
        "n": len(values),
        "median": statistics.median(values),
        "q1": q1,
        "q3": q3,
        "min": min(values),
        "max": max(values),
    }


def generate(archive: Path, output: Path) -> None:
    verification = runpy.run_path(str(ROOT / "scripts/research/verify_expanded.py"))["verify"](
        archive
    )
    with zipfile.ZipFile(io.BytesIO(lzma.decompress(archive.read_bytes()))) as zipped:
        records = json.loads(zipped.read("records.json"))
        inputs = [
            json.loads(zipped.read(name))
            for name in zipped.namelist()
            if name.endswith("/input/input.json")
        ]
    output.mkdir(parents=True, exist_ok=False)
    groups: dict[str, Any] = {}
    lines = [
        "# Expanded v1 derived count tables",
        "",
        "Generated from independently verified raw evidence. Counts are pooled within",
        "each split/control/strategy. Cases share family variants; these are not independent",
        "model trials. Missing rates remain null. The summary.json accession separately",
        "reports case-macro means and within-family paired deltas.",
        "",
    ]
    for split in ("development", "evaluation"):
        for control in CONTROLS:
            lines.extend(
                [
                    f"## {split} / {control}",
                    "",
                    "| Strategy | Accessible originals | Target facts | Exposed eligible cases | "
                    "Benign facts | Fact lookups |",
                    "| --- | --- | --- | --- | --- | --- |",
                ]
            )
            for strategy in STRATEGIES:
                rows = [
                    r
                    for r in records
                    if r["split"] == split
                    and r["control"] == control
                    and r["strategy"] == strategy
                    and r["status"] == "completed"
                ]
                metrics = {}
                for name, value in rows[0]["metrics"].items():
                    if isinstance(value, dict):
                        numerator = sum(r["metrics"][name]["numerator"] for r in rows)
                        denominator = sum(r["metrics"][name]["denominator"] for r in rows)
                        metrics[name] = {
                            "numerator": numerator,
                            "denominator": denominator,
                            "rate": numerator / denominator if denominator else None,
                        }
                eligible = [r for r in rows if r["metrics"]["attack_eligible"]]
                exposure = {
                    "numerator": sum(r["metrics"]["exposure"] for r in eligible),
                    "denominator": len(eligible),
                }
                groups[f"{split}/{control}/{strategy}"] = {
                    "cases": len(rows),
                    "metrics": metrics,
                    "exposure": exposure,
                }
                cells = [
                    metrics["accessible_persistence"],
                    metrics["target_fact_persistence"],
                    exposure,
                    metrics["benign_retention"],
                    metrics["fact_lookup_success"],
                ]
                lines.append(
                    "| "
                    + strategy
                    + " | "
                    + " | ".join(f"{c['numerator']}/{c['denominator']}" for c in cells)
                    + " |"
                )
            lines.append("")
    timings = {
        s: {
            phase: describe([r["timings_ms"][phase] for r in records if r["strategy"] == s])
            for phase in ("deletion", "recomputation", "retrieval")
        }
        for s in STRATEGIES
    }
    # Actual ingestion and build observations are recorded once per input case.
    observations = {
        "input_build_ms": describe([i["input_build_ms"] for i in inputs]),
        "source_ingestion_ms": describe([v for i in inputs for v in i["source_ingestion_ms"]]),
        "timings_ms": timings,
        "sqlite_bytes": {
            s: describe([float(r["sqlite_bytes"]) for r in records if r["strategy"] == s])
            for s in STRATEGIES
        },
    }
    (output / "count-tables.md").write_text("\n".join(lines).rstrip() + "\n")
    (output / "aggregates.json").write_text(
        json.dumps(
            {"verification": verification, "groups": groups, "observations": observations},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    plt.rcParams.update({"font.size": 10, "svg.hashsalt": "memoryfence-expanded-v1"})
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.5))
    styles = [
        ("attack_complete", "Complete", "#333333", "o"),
        ("attack_marked", "Marked partial", "#2266aa", "s"),
        ("attack_silent", "Silent partial", "#aa4422", "^"),
    ]
    for control, label, color, marker in styles:
        values = [groups[f"evaluation/{control}/{s}"] for s in STRATEGIES]
        axes[0].plot(
            range(7),
            [v["exposure"]["numerator"] / v["exposure"]["denominator"] * 100 for v in values],
            label=label,
            color=color,
            marker=marker,
        )
        axes[1].plot(
            range(7),
            [v["metrics"]["benign_retention"]["rate"] * 100 for v in values],
            label=label,
            color=color,
            marker=marker,
        )
    for ax, title, ylabel in zip(
        axes,
        ["Held-out malicious context exposure", "Held-out benign derived-fact retention"],
        [
            "Exposed cases (%) — n = 4 per condition",
            "Retained eligible facts (%) — n = 8 per condition",
        ],
        strict=True,
    ):
        ax.set(title=title, ylabel=ylabel, xlabel="Paired strategy", ylim=(-5, 105))
        ax.set_xticks(range(7), STRATEGIES, rotation=40, ha="right")
        ax.grid(axis="y", alpha=0.2)
    axes[1].legend(loc="lower left")
    fig.suptitle("Expanded v1: four fixed held-out graph families; zero model inference")
    fig.text(
        0.5,
        0.015,
        "Source: expanded-v1.zip.xz · 7 Nov 2026 · deterministic descriptive counts, "
        "no population uncertainty interval",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(output / "heldout-security-utility.svg", metadata={"Date": None})
    fig.savefig(output / "heldout-security-utility.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for phase, offset, color in [
        ("deletion", -0.22, "#333333"),
        ("recomputation", 0, "#2266aa"),
        ("retrieval", 0.22, "#aa4422"),
    ]:
        data = [timings[s][phase] for s in STRATEGIES]
        ax.bar(
            [i + offset for i in range(7)],
            [d["median"] for d in data],
            width=0.2,
            color=color,
            label=phase,
            yerr=[[d["median"] - d["q1"] for d in data], [d["q3"] - d["median"] for d in data]],
            capsize=2,
        )
    ax.set(
        title="Observed local phase latency — median and IQR",
        ylabel="Elapsed time (ms)",
        xlabel="Strategy — 80 paired runs each",
    )
    ax.set_xticks(range(7), STRATEGIES, rotation=30, ha="right")
    ax.legend()
    fig.text(
        0.5,
        0.02,
        "Source: expanded-v1.zip.xz · macOS ARM64, Python 3.12.12 · 7 Nov 2026 · "
        "IQR is dispersion, not a confidence interval",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(output / "observed-latency.svg", metadata={"Date": None})
    fig.savefig(output / "observed-latency.png", dpi=160)
    plt.close(fig)
    # Match repository text hygiene without changing plotted data.
    for path in output.glob("*.svg"):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    generate(arguments.archive, arguments.output)
