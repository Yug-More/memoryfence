"""Render the verified corrected study, retaining missing denominators and invalids."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent
study = json.loads((ROOT / "schema-controlled-analysis.json").read_text())
stages = ("direct", "summary", "consolidation", "deleted-ds1", "deleted-ds3")
defenses = ("DF0", "DF1", "DF2-exclude", "DF3")
fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
fig.suptitle("Controlled lifecycle outcomes", x=0.09, y=0.98, ha="left", fontsize=22, weight="bold")
for ax, population, metric, title, color in zip(
    axes,
    ("attack", "clean"),
    ("objective_executed_valid", "success_all_planned"),
    ("Attack execution / valid attack outcomes", "Legitimate completion / all planned clean tasks"),
    ("#344f5d", "#138b7b"),
    strict=True,
):
    values = np.zeros((4, 5))
    labels = []
    for row, defense in enumerate(defenses):
        labels.append([])
        for col, stage in enumerate(stages):
            key = f"qwen2.5:1.5b/original/study-{stage}-{population}/{defense}"
            condition = study["conditions"][key]
            count = condition[metric]["trials"]
            success = condition[metric]["successes"]
            invalid = condition["invalid"]
            values[row, col] = success / count if count else np.nan
            labels[row].append(
                (f"{success}/{count}" if count else "undefined") + f"\n{invalid} invalid"
            )
    cmap = LinearSegmentedColormap.from_list("restrained", ("#edf3f4", color))
    cmap.set_bad("#d8dee1")
    ax.imshow(values, vmin=0, vmax=1, cmap=cmap, aspect="auto")
    for row in range(4):
        for col in range(5):
            text_color = "white" if values[row, col] > 0.5 else "#141e24"
            ax.text(
                col, row, labels[row][col], ha="center", va="center", color=text_color, fontsize=10
            )
    ax.set_title(title, loc="left", fontsize=12, weight="bold", pad=15)
    ax.set_yticks(range(4), defenses)
    ax.set_xticks(
        range(5),
        ("Direct", "Summary", "Consolidated", "Source DS1", "Cascade DS3"),
        rotation=25,
        ha="right",
    )
    ax.set_xticks(np.arange(-0.5, 5, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 4, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.spines[:].set_visible(False)
fig.text(
    0.09,
    0.145,
    "Each cell: two planned seeds, one source pattern. Invalid replies remain visible; "
    "zero valid outcomes yield undefined ASR.",
    fontsize=9,
)
fig.text(
    0.09,
    0.095,
    "Descriptive Wilson 95% intervals: 0/2 [0, 0.658]; 2/2 [0.342, 1]; 1/2 [0.095, 0.905]. "
    "No significance or general security claim.",
    fontsize=9,
)
fig.text(
    0.09,
    0.045,
    "Source: schema-controlled-analysis.json · 1.5B, literal task, explicit transformation schema "
    "· 24 October 2026 (PDT)",
    fontsize=9,
)
fig.subplots_adjust(left=0.09, right=0.98, top=0.82, bottom=0.32, wspace=0.28)
for suffix in ("png", "svg"):
    path = ROOT / f"lifecycle-outcomes.{suffix}"
    fig.savefig(path, dpi=170, facecolor="white")
    if suffix == "svg":
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
