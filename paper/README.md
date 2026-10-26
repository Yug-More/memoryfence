# Research manuscript

**When Memory Outlives Its Source: A Bounded Empirical Study of Provenance Gaps in
Persistent AI-Agent Memory**

[Compiled PDF](memoryfence-paper.pdf) · [LaTeX](main.tex) ·
[Bibliography](references.bib) · [Claim map](../docs/research/CLAIM_EVIDENCE_MATRIX.md)

This is a project manuscript, not a published, accepted or peer-reviewed paper.
Its author line intentionally does not assert unconfirmed individual contributions
or an institutional affiliation. The owner must confirm authorship and any venue's
submission/disclosure requirements before submitting. No project license is established.

## Regenerate verified tables and figures

From the repository root, with Git, uv and Python 3.12+:

```bash
uv sync --frozen
uv run python scripts/research/sensitivity.py --output /tmp/mf-sensitivity.json
uv run --no-project --with matplotlib==3.10.7 --python .venv/bin/python paper/generate.py
```

`generate.py` independently verifies both genuine archives, requires equality with
committed analyses, generates both numerical result tables and `generated/facts.json`,
recomputes all 278 abstract graph masks, and writes three PNG figures. Two figures
are exact copies of the verified accession figures. To regenerate those originals:

```bash
uv run --no-project --with matplotlib==3.10.7 --python .venv/bin/python experiments/2026-10-25-bounded/plot_final.py
uv run --no-project --with matplotlib==3.10.7 --python .venv/bin/python paper/generate.py
```

Architecture, threat boundary, lifecycle/workflow and actual missing-edge example
are editable TikZ figures in `main.tex`; the question/evidence table is there too.
All numerical main-result rows are generated from independently verified evidence.
Plots use Matplotlib 3.10.7 and its DejaVu Sans font. No model weights or inference.

## Build the PDF

Install [Tectonic 0.17.0 from its official releases](https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.17.0)
for your platform. It is a free local compiler, not a paid API. The first run needs
network access to fetch the TeX bundle and fonts; subsequent runs can use its cache.
From the repository root:

```bash
mkdir -p /tmp/mf-paper-build
tectonic --keep-logs --outdir /tmp/mf-paper-build paper/main.tex
cp /tmp/mf-paper-build/main.pdf paper/memoryfence-paper.pdf
```

No shell escape is required.
Tectonic runs BibTeX and the necessary passes automatically. TeX bundle versions can
change; this is source reproducibility, not a promise of byte-identical PDF metadata.
A conventional XeLaTeX + BibTeX toolchain can also build the source inside `paper/`.
The project package itself needs neither Matplotlib nor TeX; optional authoring tools
are kept out of the application lockfile.

## Evidence boundaries

The 72 real responses belong to the preserved 25 October bounded cycle; this pass
adds zero inference. Six generated chains are three clean and three attack chains,
with two derived memories each. The 108 primary and 36 off-protocol views are
conditional state observations, not independent model trials. The new 278 masks
are abstract graph configurations, not generated chains or DF2 behavioral trials.
See the [reproduction record](../docs/research/REPRODUCIBILITY_REPORT.md) and
[publication audit](../docs/research/FINAL_PUBLICATION_AUDIT.md).
