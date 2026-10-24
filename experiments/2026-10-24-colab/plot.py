"""Render the two matched-pilot endpoints from independently checked saved data.

Optional authoring dependency only: matplotlib==3.10.7. Not a runtime dependency.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

root = Path(__file__).resolve().parent
study = json.loads((root / "independent-analysis.json").read_text())[1]
conditions = study["condition_summary"]
defenses = ["DF0", "DF1", "DF2", "DF3"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.7), sharey=True)
for axis, scenario, endpoint, title, color in zip(
    axes,
    ["pilot-ticket-attack", "pilot-ticket-utility"],
    ["objective_executed", "legitimate_exact_ticket"],
    ["Attack-objective execution", "Legitimate ticket completion"],
    ["#334c59", "#178675"],
    strict=True,
):
    for index, defense in enumerate(defenses):
        rate = conditions[f"{scenario}/{defense}"][endpoint]
        successes, count = rate["successes"], rate["trials"]
        point = successes / count
        lower, upper = rate["interval95"]
        axis.errorbar(
            index,
            point,
            yerr=[[point - lower], [upper - point]],
            fmt="o",
            color=color,
            capsize=6,
            markersize=7,
            linewidth=1.8,
        )
        axis.annotate(
            f"{successes}/{count}",
            (index, 0.03),
            xytext=(11, 0),
            textcoords="offset points",
            ha="left",
            va="bottom",
            color=color,
        )
    axis.set_title(title, loc="left", fontsize=14, fontweight="bold", pad=14)
    axis.set_xticks(range(4), ["DF0", "DF1", "DF2-exclude", "DF3"])
    axis.set_xlabel("Defense condition", labelpad=12)
    axis.set_xlim(-0.5, 3.5)
    axis.set_ylim(-0.04, 1)
    axis.yaxis.set_major_formatter(PercentFormatter(1))
    axis.set_ylabel("Completed episodes meeting objective (%)")
    axis.grid(axis="y", alpha=0.18)
    axis.spines[["top", "right"]].set_visible(False)
fig.suptitle(
    "Matched development pilot: execution and utility",
    x=0.075,
    y=0.965,
    ha="left",
    fontsize=17,
    fontweight="bold",
)
fig.text(
    0.075,
    0.865,
    "Baseline utility also failed. These data cannot establish defense effectiveness.",
    fontsize=11,
    color="#334c59",
)
fig.text(
    0.075,
    0.07,
    "Source: independent-analysis.json · 24 Oct 2026 · qwen2.5:0.5b · agent-v2-json-schema",
    fontsize=9,
)
fig.text(
    0.075,
    0.035,
    "Two seeds per cell; one template per population. Descriptive 95% Wilson intervals; "
    "no scenario-level generalization.",
    fontsize=9,
)
fig.subplots_adjust(top=0.78, bottom=0.23, left=0.075, right=0.98, wspace=0.25)
for suffix in ("svg", "png"):
    fig.savefig(root / f"pilot-outcomes.{suffix}", dpi=170, facecolor="white")
print("Rendered pilot-outcomes.svg and pilot-outcomes.png with matplotlib", matplotlib.__version__)
