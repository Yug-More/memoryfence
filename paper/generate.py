"""Regenerate paper numbers, tables and plots from independently verified archives."""

import json
import runpy
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper"
EVIDENCE = ROOT / "experiments/2026-10-25-bounded"


def main() -> None:
    verify = runpy.run_path(str(ROOT / "scripts/research/verify_final.py"))["verify"]
    qualification = verify(EVIDENCE / "final-qualification.zip.xz")
    study = verify(EVIDENCE / "paired-state-study.zip.xz", EVIDENCE / "final-qualification.zip.xz")
    for name, result in (("final-qualification", qualification), ("paired-state-study", study)):
        if result != json.loads((EVIDENCE / f"{name}-analysis.json").read_text()):
            raise ValueError(f"independent analysis differs: {name}")
    sensitivity = runpy.run_path(str(ROOT / "scripts/research/sensitivity.py"))[
        "enumerate_chains"
    ]()
    generated = OUT / "generated"
    generated.mkdir(exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)
    (generated / "chain-sensitivity.json").write_text(json.dumps(sensitivity, indent=2) + "\n")
    rows = []
    for fidelity in ("LF1.0", "LF0.75", "LF0.5"):
        groups = study["state_groups"]
        values = [
            groups[f"attack/{fidelity}/{p}/DF0"]["active_derived_total"] for p in ("DS1", "DS3")
        ]
        exposures = [groups[f"attack/{fidelity}/DS3/{d}"]["exposed_views"] for d in ("DF0", "DF2")]
        rows.append(
            f"{fidelity} & {values[0]}/6 & {values[1]}/6 & {exposures[0]}/3 & {exposures[1]}/3 "
            + r"\\"
        )
    (generated / "state-rows.tex").write_text("\n".join(rows) + "\n\\bottomrule\n")
    rows = []
    for policy in ("DS0", "DS1", "DS3"):
        for defense in ("DF0", "DF2"):
            cells = [
                r for r in study["behavior"] if r["policy"] == policy and r["defense"] == defense
            ]
            clean = [r for r in cells if not r["attack"]]
            attack = [r for r in cells if r["attack"]]
            echo = sum(r["output_text_canary"] for r in attack)
            rows.append(
                f"{policy}/{defense} & {sum(r['success'] for r in clean)}/3 & "
                f"{sum(r['success'] for r in attack)}/3 & "
                f"{sum(r['objective_proposed'] for r in attack)}/3 & "
                f"{sum(r['objective_executed'] for r in attack)}/3 & {echo}/3 " + r"\\"
            )
    (generated / "behavior-rows.tex").write_text("\n".join(rows) + "\n\\bottomrule\n")
    facts = {
        "qualification_calls": qualification["planned"],
        "original_success": sum(
            r["success"] for r in qualification["trials"] if r["interface"] == "original"
        ),
        "task_last_success": sum(
            r["success"] for r in qualification["trials"] if r["interface"] == "task-last"
        ),
        "chains": study["chains"],
        "transform_calls": study["actual_transform_responses"],
        "primary_views": study["primary_state_views"],
        "extra_views": study["exploratory_state_views"],
        "behavior_calls": study["behavior_planned"],
        "behavior_valid": study["behavior_valid"],
        "legitimate_effects": sum(r["success"] for r in study["behavior"]),
        "attack_effects": sum(r["objective_executed"] for r in study["behavior"] if r["attack"]),
        "attack_episodes": sum(r["attack"] for r in study["behavior"]),
        "text_echoes": sum(r["output_text_canary"] for r in study["behavior"]),
        "sensitivity_configurations": sensitivity["configurations"],
    }
    (generated / "facts.json").write_text(json.dumps(facts, indent=2) + "\n")
    for name in ("message-order-qualification", "provenance-deletion-outcomes"):
        shutil.copyfile(EVIDENCE / f"{name}.png", OUT / "figures" / f"{name}.png")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, ax = plt.subplots(figsize=(7, 3.1))
    for depth in (1, 2, 4, 8):
        groups = [g for g in sensitivity["groups"] if g["depth"] == depth]
        ax.plot(
            [g["retained_edges"] / depth for g in groups],
            [g["sum_survivors"] / g["masks"] / depth for g in groups],
            marker="o",
            label=f"{depth} derived nodes",
        )
    ax.set(
        xlabel="Retained derivation edges / depth",
        ylabel="Mean surviving descendant fraction",
        ylim=(-0.03, 1.03),
    )
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "figures/chain-sensitivity.png", dpi=220)
    plt.close(fig)
    print(json.dumps(facts, indent=2))


if __name__ == "__main__":
    main()
