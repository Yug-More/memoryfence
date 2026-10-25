"""Standalone figures from independently verified genuine records only."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
qualification = json.loads((ROOT / "final-qualification-analysis.json").read_text())
families = ("direct", "memory", "response", "empty")
fig, ax = plt.subplots(figsize=(8.5, 4.5))
for offset, layout, color, label in (
    (-0.17, "original", "#344f5d", "Task before memory message"),
    (0.17, "task-last", "#138b7b", "Task after memory message"),
):
    counts = [
        sum(
            r["success"]
            for r in qualification["trials"]
            if r["interface"] == layout and r["family"] == family
        )
        for family in families
    ]
    positions = np.arange(4) + offset
    ax.bar(positions, counts, width=0.3, color=color, label=label)
    for x, count in zip(positions, counts, strict=True):
        ax.text(x, count + 0.09, f"{count}/3", ha="center", fontsize=10)
ax.set(
    ylim=(0, 3.7),
    yticks=(0, 1, 2, 3),
    ylabel="Exact benign successes / 3 planned tasks",
    xticks=range(4),
    xticklabels=("Literal ticket", "Memory fields", "Exact response", "Empty context"),
)
ax.set_title(
    "One message-order change; a fixed capability gate",
    loc="left",
    fontsize=17,
    weight="bold",
    pad=38,
)
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.015), ncol=2, frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
fig.text(
    0.1,
    0.075,
    "Original: 9/12. Task-last: 12/12. Gate: all 12 valid and exact; no threshold change.",
    fontsize=9,
)
fig.text(
    0.1,
    0.025,
    "Source: final-qualification-analysis.json · Qwen2.5 1.5B · three seeds, "
    "one task set · 25 October 2026",
    fontsize=8,
)
fig.subplots_adjust(left=0.1, right=0.98, top=0.82, bottom=0.23)


def save(figure: object, name: str) -> None:
    for suffix in ("svg", "png"):
        path = ROOT / f"{name}.{suffix}"
        figure.savefig(path, dpi=170, facecolor="white")
        if suffix == "svg":
            path.write_text(
                "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
            )


save(fig, "message-order-qualification")
if (ROOT / "paired-state-study-analysis.json").exists():
    study = json.loads((ROOT / "paired-state-study-analysis.json").read_text())
    fidelities = ("LF1.0", "LF0.75", "LF0.5")
    policies = ("DS0", "DS1", "DS3")
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.8))
    panels = (
        ("attack", "DF0", "active_derived_total", 6, "Active attack descendants / 6"),
        ("attack", "DF0", "exposed_views", 3, "DF0 ancestry exposure / 3"),
        ("attack", "DF2", "exposed_views", 3, "DF2 ancestry exposure / 3"),
        ("clean", "DF2", "retrieved_total", None, "DF2 clean memories retrieved"),
    )
    cmap = LinearSegmentedColormap.from_list("memoryfence", ("#edf3f4", "#344f5d"))
    for ax, (population, defense, metric, denominator, title) in zip(axes, panels, strict=True):
        counts = [
            [study["state_groups"][f"{population}/{f}/{p}/{defense}"][metric] for p in policies]
            for f in fidelities
        ]
        values = np.array(counts)
        maximum = denominator or 9
        ax.imshow(values, vmin=0, vmax=maximum, cmap=cmap, aspect="auto")
        for row in range(3):
            for col in range(3):
                text = f"{values[row, col]}/{denominator}" if denominator else str(values[row, col])
                ax.text(
                    col,
                    row,
                    text,
                    ha="center",
                    va="center",
                    color="white" if values[row, col] > maximum / 2 else "#141e24",
                    fontsize=12,
                )
        ax.set_title(title, loc="left", fontsize=10, pad=14, weight="bold")
        ax.set_xticks(
            range(3), ("No deletion", "Source only", "Recorded cascade"), rotation=30, ha="right"
        )
        ax.set_yticks(range(3), fidelities)
        ax.spines[:].set_visible(False)
    fig.suptitle(
        "Recorded ancestry controls deletion reach and filtering",
        x=0.065,
        ha="left",
        fontsize=19,
        weight="bold",
    )
    fig.text(
        0.065,
        0.11,
        "Three generated chains per population; identical text across all "
        "paired conditions. LF is seeded edge retention, not measured completeness.",
        fontsize=9,
    )
    fig.text(
        0.065,
        0.06,
        "State/retrieval endpoints are deterministic conditional on those "
        "chains. Exposure is true ancestry, not semantic following or a tool effect.",
        fontsize=9,
    )
    fig.text(
        0.065,
        0.015,
        "Source: paired-state-study-analysis.json · six real TT2→TT3 chains, "
        "12 transformation responses, 108 primary state views · "
        "36 extra LF0.0 views retained separately · 25 October 2026",
        fontsize=8,
    )
    fig.subplots_adjust(left=0.065, right=0.99, top=0.78, bottom=0.32, wspace=0.55)
    save(fig, "provenance-deletion-outcomes")
