"""Reformat verified measurements for readable single-column manuscript figures."""

import json
import runpy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "generated"
STRATEGIES = (
    "source_only",
    "keyword",
    "direct",
    "cascade",
    "rederive",
    "quarantine",
    "memoryfence",
)


def main() -> None:
    runpy.run_path(str(ROOT / "scripts/research/verify_release.py"))["verify"]()
    raw = ROOT / "experiments/2026-11-07-expanded/expanded-v1.zip.xz"
    runpy.run_path(str(ROOT / "scripts/research/verify_expanded.py"))["verify"](raw)
    data = json.loads(
        (ROOT / "experiments/2026-11-07-expanded/derived/aggregates.json").read_text()
    )
    groups = data["groups"]
    OUT.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 9})
    fig, axes = plt.subplots(2, 1, figsize=(7, 7.7), sharex=True)
    for control, label, color, marker in [
        ("attack_complete", "Complete", "#333333", "o"),
        ("attack_marked", "Marked partial", "#2266aa", "s"),
        ("attack_silent", "Silent partial", "#aa4422", "^"),
    ]:
        values = [groups[f"evaluation/{control}/{s}"] for s in STRATEGIES]
        axes[0].plot(
            range(7),
            [v["exposure"]["numerator"] / 4 * 100 for v in values],
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
    for ax in axes:
        ax.set_ylim(-5, 105)
        ax.grid(axis="y", alpha=0.2)
    axes[0].set(
        title="Malicious context exposure — 4 held-out cases per condition",
        ylabel="Exposed cases (%)",
    )
    axes[0].legend(loc="lower left")
    axes[1].set(
        title="Benign derived-fact retention — 8 eligible facts per condition",
        ylabel="Retained facts (%)",
        xlabel="Paired strategy",
    )
    axes[1].set_xticks(range(7), STRATEGIES, rotation=30, ha="right", fontsize=8)
    fig.suptitle("Expanded v1 · zero model inference · four fixed graph families")
    fig.text(
        0.5,
        0.015,
        "Source: verified Expanded v1 accession · 7 Nov 2026 · descriptive counts",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(OUT / "heldout-security-utility.png", dpi=160)
    plt.close(fig)
    timings = data["observations"]["timings_ms"]
    fig, ax = plt.subplots(figsize=(7, 4.3))
    for phase, offset, color in [
        ("deletion", -0.22, "#333333"),
        ("recomputation", 0, "#2266aa"),
        ("retrieval", 0.22, "#aa4422"),
    ]:
        selected = [timings[s][phase] for s in STRATEGIES]
        ax.bar(
            [i + offset for i in range(7)],
            [d["median"] for d in selected],
            width=0.2,
            color=color,
            label=phase,
            capsize=2,
            yerr=[
                [d["median"] - d["q1"] for d in selected],
                [d["q3"] - d["median"] for d in selected],
            ],
        )
    ax.set(
        title="Observed local latency — median and IQR",
        ylabel="Elapsed time (ms)",
        xlabel="Strategy — 80 paired runs each",
    )
    ax.set_xticks(range(7), STRATEGIES, rotation=30, ha="right", fontsize=8)
    ax.legend(fontsize=8)
    fig.text(
        0.5,
        0.015,
        "Source: 7 Nov 2026 local run · IQR is dispersion, not confidence",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT / "observed-latency.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
