"""Check manuscript references, asset paths and generated numerical claims offline."""

import argparse
import hashlib
import json
import math
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def audit() -> dict[str, object]:
    paper = ROOT / "paper"
    tex = (paper / "main.tex").read_text()
    bibliography = (paper / "references.bib").read_text()
    cited = {k for block in re.findall(r"\\cite\w*\{([^}]+)\}", tex) for k in block.split(",")}
    defined = set(re.findall(r"@\w+\{([^,]+),", bibliography))
    metadata = json.loads((ROOT / "docs/research/PUBLICATION_CITATIONS.json").read_text())
    if cited != defined or cited != {s["key"] for s in metadata["sources"]}:
        raise ValueError("cited, defined and primary-checked references differ")
    labels = re.findall(r"\\label\{([^}]+)\}", tex)
    references = re.findall(r"\\ref\{([^}]+)\}", tex)
    if len(labels) != len(set(labels)) or not set(references) <= set(labels):
        raise ValueError("duplicate label or missing reference")
    assets = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", tex)
    inputs = re.findall(r"\\input\{([^}]+)\}", tex)
    if not all((paper / p).is_file() for p in assets + inputs):
        raise ValueError("missing manuscript figure or generated table")
    facts = json.loads((paper / "generated/facts.json").read_text())
    expected = {
        "qualification_calls": 24,
        "original_success": 9,
        "task_last_success": 12,
        "chains": 6,
        "transform_calls": 12,
        "primary_views": 108,
        "extra_views": 36,
        "behavior_calls": 36,
        "behavior_valid": 36,
        "legitimate_effects": 36,
        "attack_effects": 0,
        "attack_episodes": 18,
        "text_echoes": 3,
        "sensitivity_configurations": 278,
    }
    if facts != expected:
        raise ValueError(
            "paper fact ledger differs from reviewed claims; investigate, do not relabel"
        )
    sensitivity = runpy.run_path(str(ROOT / "scripts/research/sensitivity.py"))[
        "enumerate_chains"
    ]()
    if sensitivity != json.loads((paper / "generated/chain-sensitivity.json").read_text()):
        raise ValueError("preserved graph masks differ from fresh computation")
    z = 1.959963984540054

    def wilson(successes: int, n: int) -> list[float]:
        p = successes / n
        denominator = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denominator
        half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
        return [max(0, center - half), min(1, center + half)]

    targets = [paper / p for p in assets + inputs]
    targets += [paper / n for n in ("main.tex", "references.bib", "memoryfence-paper.pdf")]
    return {
        "classification": "algorithmic manuscript audit; no independent human review",
        "facts": facts,
        "citations_checked": sorted(cited),
        "unresolved_source_refs": 0,
        "wilson_descriptive": {"12/12": wilson(12, 12), "0/3": wilson(0, 3), "3/3": wilson(3, 3)},
        "sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in targets
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(audit(), indent=2) + "\n")
    print("manuscript source claims, references, assets and masks checked")
