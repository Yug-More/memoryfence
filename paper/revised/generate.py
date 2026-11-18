"""Verify archived evidence and regenerate revised-manuscript tables; no inference."""

import hashlib
import io
import json
import lzma
import runpy
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "generated"


def module(name: str) -> dict:
    return runpy.run_path(str(ROOT / "scripts/research" / name))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    preservation = module("verify_release.py")["verify"]()
    previous = json.loads(
        (ROOT / "experiments/2026-11-08-finalization/release-manifest.json").read_text()
    )
    for item in previous["files"]:
        data = (ROOT / item["path"]).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"prior finalization changed: {item['path']}")
    original = ROOT / "experiments/2026-10-25-bounded"
    verify = module("verify_final.py")["verify"]
    q = verify(original / "final-qualification.zip.xz")
    study = verify(original / "paired-state-study.zip.xz", original / "final-qualification.zip.xz")
    for name, value in [("final-qualification", q), ("paired-state-study", study)]:
        if value != json.loads((original / f"{name}-analysis.json").read_text()):
            raise ValueError(f"archived analysis differs: {name}")
    sensitivity = module("sensitivity.py")["enumerate_chains"]()
    if sensitivity != json.loads((ROOT / "paper/generated/chain-sensitivity.json").read_text()):
        raise ValueError("abstract graph enumeration differs")
    expanded_path = ROOT / "experiments/2026-11-07-expanded/expanded-v1.zip.xz"
    expanded = module("verify_expanded.py")["verify"](expanded_path)
    with zipfile.ZipFile(io.BytesIO(lzma.decompress(expanded_path.read_bytes()))) as archive:
        records = json.loads(archive.read("records.json"))
    repeated_path = ROOT / "experiments/2026-11-08-finalization/reproduction.zip.xz"
    with tempfile.TemporaryDirectory(prefix="memoryfence-paper-verify-") as directory:
        temp = Path(directory)
        module("analyze_release.py")["analyze"](
            expanded_path, repeated_path, temp / "reproduction.json"
        )
        reproduction = json.loads((temp / "reproduction.json").read_text())
        model_path = ROOT / "experiments/2026-11-09-model-followup/model-followup.zip.xz"
        model_directory = temp / "model"
        model_directory.mkdir()
        with zipfile.ZipFile(io.BytesIO(lzma.decompress(model_path.read_bytes()))) as archive:
            for info in archive.infolist():
                path = model_directory / info.filename
                if not path.resolve().is_relative_to(model_directory.resolve()):
                    raise ValueError("unsafe archive member")
                if info.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read(info))
        model = module("verify_model_followup.py")["verify"](model_directory, expanded_path)
        expected = json.loads(
            (
                ROOT / "experiments/2026-11-09-model-followup/independent-verification.json"
            ).read_text()
        )
        if model != expected:
            raise ValueError("independent model recomputation differs")
    facts = {
        "original": {
            "qualification_calls": q["planned"],
            "chains": study["chains"],
            "transformation_responses": study["actual_transform_responses"],
            "declared_state_views": study["primary_state_views"],
            "off_protocol_state_views": study["exploratory_state_views"],
            "behavior_responses": study["behavior_valid"],
            "attack_episodes": sum(r["attack"] for r in study["behavior"]),
            "legitimate_effects": sum(r["success"] for r in study["behavior"]),
            "attacker_effects": sum(
                r["objective_executed"] for r in study["behavior"] if r["attack"]
            ),
            "text_echoes": sum(r["output_text_canary"] for r in study["behavior"]),
        },
        "sensitivity": {k: sensitivity[k] for k in ("configurations", "depths", "model_calls")},
        "expanded": expanded,
        "semantic_reproduction_matches": reproduction["semantic_records_equal"],
        "model": model,
        "preservation": dict(preservation, finalization=len(previous["files"])),
        "new_inference": False,
    }
    for fidelity in ("LF1.0", "LF0.75", "LF0.5"):
        groups = study["state_groups"]
        values = [
            groups[f"attack/{fidelity}/{p}/DF0"]["active_derived_total"] for p in ("DS1", "DS3")
        ]
        exposures = [groups[f"attack/{fidelity}/DS3/{d}"]["exposed_views"] for d in ("DF0", "DF2")]
        with (OUT / "state-rows.tex").open("a" if fidelity != "LF1.0" else "w") as stream:
            stream.write(
                f"{fidelity[2:]} & {values[0]}/6 & {values[1]}/6 & "
                f"{exposures[0]}/3 & {exposures[1]}/3 " + r"\\" + "\n"
            )
    with (OUT / "state-rows.tex").open("a") as stream:
        stream.write("\\bottomrule\n")
    behavior_rows = []
    for policy in ("DS0", "DS1", "DS3"):
        for defense in ("DF0", "DF2"):
            cells = [
                r for r in study["behavior"] if r["policy"] == policy and r["defense"] == defense
            ]
            clean, attack = [r for r in cells if not r["attack"]], [r for r in cells if r["attack"]]
            values = [
                sum(r["success"] for r in clean),
                sum(r["success"] for r in attack),
                sum(r["objective_proposed"] for r in attack),
                sum(r["objective_executed"] for r in attack),
                sum(r["output_text_canary"] for r in attack),
            ]
            behavior_rows.append(
                f"{policy}/{defense} & " + " & ".join(f"{v}/3" for v in values) + r" \\"
            )
    (OUT / "behavior-rows.tex").write_text("\n".join(behavior_rows) + "\n\\bottomrule\n")
    qualification_rows = []
    for family in sorted({t["family"] for t in q["trials"]}):
        values = [
            sum(
                t["success"]
                for t in q["trials"]
                if t["family"] == family and t["interface"] == interface
            )
            for interface in ("original", "task-last")
        ]
        qualification_rows.append(
            f"{family.replace('_', '-')} & {values[0]}/3 & {values[1]}/3 " + r"\\"
        )
    totals = []
    for interface in ("original", "task-last"):
        trials = [t for t in q["trials"] if t["interface"] == interface]
        totals.append(f"{sum(t['success'] for t in trials)}/{len(trials)}")
    (OUT / "qualification-rows.tex").write_text(
        "\n".join(qualification_rows)
        + "\n"
        + r"\midrule Total & "
        + " & ".join(totals)
        + r"\\"
        + "\n"
        + r"\bottomrule"
        + "\n"
    )
    names = {
        "source_only": "Source only",
        "keyword": "Keyword",
        "direct": "Direct",
        "cascade": "Cascade",
        "rederive": "Re-derive",
        "quarantine": "Quarantine",
        "memoryfence": "Guarded re-derive",
    }
    expanded_rows = []
    for control, label in [
        ("attack_complete", "Complete lineage"),
        ("attack_marked", "Marked gaps"),
        ("attack_silent", "Silent gaps"),
    ]:
        expanded_rows.append(r"\multicolumn{6}{l}{\textit{" + label + r"}} \\")
        for strategy, name in names.items():
            cells = [
                r
                for r in records
                if r["split"] == "evaluation"
                and r["control"] == control
                and r["strategy"] == strategy
            ]
            values = []
            for metric in (
                "persistence",
                "accessible_persistence",
                "benign_retention",
                "fact_lookup_success",
            ):
                values.append(
                    "/".join(
                        str(sum(r["metrics"][metric][k] for r in cells))
                        for k in ("numerator", "denominator")
                    )
                )
            exposure = f"{sum(r['metrics']['exposure'] for r in cells)}/{len(cells)}"
            expanded_rows.append(
                name + " & " + " & ".join([*values[:2], exposure, *values[2:]]) + r" \\"
            )
        expanded_rows.append(r"\addlinespace[3pt]")
    (OUT / "expanded-rows.tex").write_text("\n".join(expanded_rows) + "\n\\bottomrule\n")
    headers = {
        "state-rows.tex": (
            "lrrrr",
            "Nominal retention & DS1 active & DS3 active & DF0 exposed & DF2 exposed",
        ),
        "qualification-rows.tex": ("lrr", "Qualification condition & Original & Task-last"),
        "behavior-rows.tex": (
            "lrrrrr",
            "Policy/filter & Clean task & Attack task & "
            "Attack proposal & Attack effect & Text echo",
        ),
        "expanded-rows.tex": (
            "lrrrrr",
            "Strategy & Physical & Accessible & Exposed & Benign facts & Lookups",
        ),
    }
    for name, (columns, header) in headers.items():
        path = OUT / name
        rows = path.read_text()
        path.write_text(
            r"\begin{tabular}{"
            + columns
            + "}\n"
            + r"\toprule"
            + "\n"
            + header
            + r"\\\midrule"
            + "\n"
            + rows
            + r"\end{tabular}"
            + "\n"
        )
    (OUT / "facts.json").write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")
    inputs = [
        original / "final-qualification.zip.xz",
        original / "paired-state-study.zip.xz",
        expanded_path,
        repeated_path,
        model_path,
        ROOT / "paper/generated/chain-sensitivity.json",
        Path(__file__),
        OUT.parent / "main.tex",
        OUT.parent / "references.bib",
    ]
    provenance = {
        "classification": (
            "deterministic verification of supplied evidence; no new inference or host attestation"
        ),
        "inputs_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs
        },
        "generated_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT.glob("*"))
            if p.name != "provenance.json"
        },
    }
    (OUT / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "original": facts["original"],
                "graph_masks": sensitivity["configurations"],
                "expanded_runs": expanded["verified_runs"],
                "model_requests": model["chat_requests"],
                "valid_model_probes": model["valid_probes"],
                "new_inference": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
