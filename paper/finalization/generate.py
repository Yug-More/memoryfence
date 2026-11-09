"""Generate the expanded manuscript body/tables from verified evidence and Markdown."""

import hashlib
import io
import json
import lzma
import re
import runpy
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "generated"
CITES = {
    "https://arxiv.org/abs/2302.12173": "greshake",
    "https://arxiv.org/abs/2407.12784": "agentpoison",
    "https://aclanthology.org/2024.findings-acl.624/": "injecagent",
    "https://arxiv.org/abs/2511.17671": "crossuser",
    "https://arxiv.org/abs/2607.29167": "laundering",
    "https://arxiv.org/abs/2606.04329": "mpbench",
    "https://arxiv.org/abs/1912.03817": "unlearning",
}


def escape(text: str) -> str:
    changes = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    text = text.replace(chr(0x2212), "-").replace(chr(0x2013), "--").replace(chr(0x2014), "---")
    text = text.replace(chr(0x2019), "'").replace(chr(0x201C), '"').replace(chr(0x201D), '"')
    changes[chr(0xD7)] = r"$\times$"
    return "".join(changes.get(c, c) for c in text)


def inline(text: str) -> str:
    chunks = re.split(r"(`[^`]+`|\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|(?<!\w)\*[^*]+\*(?!\w))", text)
    output = []
    for part in chunks:
        link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", part)
        if part.startswith("`"):
            output.append(r"\texttt{" + escape(part[1:-1]) + "}")
        elif link:
            label, url = link.groups()
            output.append(r"\cite{" + CITES[url] + "}" if url in CITES else escape(label))
        elif part.startswith("**"):
            output.append(r"\textbf{" + escape(part[2:-2]) + "}")
        elif part.startswith("*"):
            output.append(r"\emph{" + escape(part[1:-1]) + "}")
        else:
            output.append(escape(part))
    return "".join(output)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    preserved = runpy.run_path(str(ROOT / "scripts/research/verify_release.py"))["verify"]()
    raw = ROOT / "experiments/2026-11-07-expanded/expanded-v1.zip.xz"
    verification = runpy.run_path(str(ROOT / "scripts/research/verify_expanded.py"))["verify"](raw)
    markdown = ROOT / "docs/RESEARCH_PAPER.md"
    # The narrative source is the evidence-qualified expanded synthesis. Original
    # paper/main.tex remains unchanged. Reflow paragraphs before inline conversion.
    source = markdown.read_text().split("## Abstract", 1)[1]
    abstract, source = source.split("## 1. ", 1)
    paragraphs = re.split(r"\n\s*\n", "## 1. " + source)
    body = []
    for paragraph in paragraphs:
        paragraph = " ".join(paragraph.splitlines()).strip()
        if not paragraph:
            continue
        if paragraph.startswith("## "):
            heading = re.sub(r"^## \d+\.\s*", "", paragraph)
            if heading.startswith("Method:"):
                body.append(r"\input{architecture.tex}")
            body.append(r"\section{" + escape(heading) + "}")
        else:
            body.append(inline(paragraph))
    (OUT / "body.tex").write_text("\n\n".join(body) + "\n")
    (OUT / "abstract.tex").write_text(inline(" ".join(abstract.split())) + "\n")
    with zipfile.ZipFile(io.BytesIO(lzma.decompress(raw.read_bytes()))) as archive:
        records = json.loads(archive.read("records.json"))
    rows = []
    for control, label in (
        ("attack_complete", "Complete"),
        ("attack_marked", "Marked partial"),
        ("attack_silent", "Silent partial"),
    ):
        rows.extend(
            [
                r"\begin{table}[H]\centering\small\renewcommand{\arraystretch}{0.9}",
                r"\caption{"
                + label
                + r" lineage: four held-out families, eight eligible benign facts. "
                r"Exposure is context, not model ASR.}",
                r"\begin{tabular}{lrrr}\toprule Strategy & Exposed cases & "
                r"Benign facts & Fact lookups\\\midrule",
            ]
        )
        for strategy in (
            "source_only",
            "keyword",
            "direct",
            "cascade",
            "rederive",
            "quarantine",
            "memoryfence",
        ):
            selected = [
                r
                for r in records
                if r["split"] == "evaluation"
                and r["control"] == control
                and r["strategy"] == strategy
            ]
            cells = [f"{sum(r['metrics']['exposure'] for r in selected)}/{len(selected)}"]
            for metric in ("benign_retention", "fact_lookup_success"):
                n = sum(r["metrics"][metric]["numerator"] for r in selected)
                d = sum(r["metrics"][metric]["denominator"] for r in selected)
                cells.append(f"{n}/{d}")
            rows.append(escape(strategy) + " & " + " & ".join(cells) + r"\\")
        rows.extend([r"\bottomrule\end{tabular}\end{table}", ""])
    (OUT / "heldout-tables.tex").write_text("\n".join(rows).rstrip() + "\n")
    (OUT / "provenance.json").write_text(
        json.dumps(
            {
                "narrative_sha256": hashlib.sha256(markdown.read_bytes()).hexdigest(),
                "preserved": preserved,
                "figure_sha256": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(OUT.glob("*.png"))
                },
                "expanded_verification": verification,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
