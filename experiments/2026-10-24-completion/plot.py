"""Render verified capability counts; requires optional matplotlib 3.10.7."""

import json
from pathlib import Path
from statistics import NormalDist

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
original = json.loads((ROOT / "qualification-v1-analysis.json").read_text())
literal = json.loads((ROOT / "literal-qualification-analysis.json").read_text())
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.8), sharey=True)
fig.patch.set_facecolor("white")
fig.suptitle(
    "Capability before security evaluation", x=0.07, y=0.98, ha="left", fontsize=21, weight="bold"
)
for ax, model in zip(axes, ("qwen2.5:0.5b", "qwen2.5:1.5b"), strict=True):
    for x, (source, interface, _label) in enumerate(
        (
            (original, "original", "Original"),
            (original, "task-last", "Task last"),
            (original, "example", "Example"),
            (literal, "original", "Literal task"),
        )
    ):
        cells = [t for t in source["trials"] if t["model"] == model and t["interface"] == interface]
        count = len(cells)
        success = sum(c["success"] for c in cells)
        invalid = sum(not c["valid"] for c in cells)
        p = success / count
        z = NormalDist().inv_cdf(0.975)
        scale = 1 + z * z / count
        center = (p + z * z / (2 * count)) / scale
        radius = z / scale * (p * (1 - p) / count + z * z / (4 * count * count)) ** 0.5
        lower, upper = max(0, center - radius), min(1, center + radius)
        color = "#138b7b" if x == 3 else "#344f5d"
        ax.errorbar(
            x,
            100 * p,
            yerr=[[max(0, 100 * (p - lower))], [max(0, 100 * (upper - p))]],
            fmt="o",
            capsize=6,
            color=color,
            markersize=9,
            linewidth=2,
        )
        ax.annotate(
            f"{success}/{count}",
            (x, 100 * p),
            xytext=(10, 0),
            textcoords="offset points",
            fontsize=11,
            color=color,
        )
        ax.text(x, -17, f"invalid: {invalid}", ha="center", fontsize=9, color="#526875")
    ax.set_title(model, loc="left", weight="bold", pad=16)
    ax.set_xticks(range(4), ("Original", "Task last", "Example", "Literal task"))
    ax.set_ylim(-3, 105)
    ax.set_xlim(-0.45, 3.6)
    ax.set_yticks(range(0, 101, 20), [f"{p}%" for p in range(0, 101, 20)])
    ax.grid(axis="y", alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)
    ax.axhline(800 / 9, color="#78918f", linestyle="--", linewidth=1)
axes[0].set_ylabel("Exact benign success / all planned trials")
fig.text(
    0.07,
    0.11,
    "Gate: ≥8/9 overall, ≥2/3 in each family, no invalid calls. "
    "Dashed line shows only the overall requirement.",
    fontsize=9,
)
fig.text(
    0.07,
    0.065,
    "Three synthetic task families, three seeds. Wilson 95% intervals are descriptive; "
    "no population or scenario generalization.",
    fontsize=9,
)
fig.text(
    0.07,
    0.025,
    "Source: independently verified original and literal-task qualification archives "
    "· 24 October 2026 (PDT)",
    fontsize=9,
)
fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.3, wspace=0.13)
for suffix in ("png", "svg"):
    path = ROOT / f"capability-outcomes.{suffix}"
    fig.savefig(path, dpi=170, facecolor="white")
    if suffix == "svg":
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
