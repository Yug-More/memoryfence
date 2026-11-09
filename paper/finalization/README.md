# Expanded research manuscript

Working title: **MemoryFence: Investigating Persistent Prompt Injection in LLM
Agent Memory After Source Deletion**. Manuscript in preparation; not submitted,
accepted or peer reviewed. Personal contribution attribution requires confirmation.

This is a distinct synthesis of the Original Study, Expanded v1 and finalization.
It does not overwrite `paper/main.tex` or restore the user's deleted historical PDF.
The Markdown narrative remains `docs/RESEARCH_PAPER.md`; generated TeX includes its
methods/results and verified references. Additional sections describe finalization,
ethics, conclusions and reproduction. Tables derive from raw structured records;
figures are preserved measured plots, not imagined model results.

From the repository root:

```bash
uv sync --frozen
uv run --no-project --with matplotlib==3.10.7 --python .venv/bin/python paper/finalization/figures.py
uv run --frozen python paper/finalization/generate.py
mkdir -p /tmp/memoryfence-expanded-paper-new
tectonic --keep-logs --outdir /tmp/memoryfence-expanded-paper-new paper/finalization/main.tex
```

Tectonic0.17.0 is an optional free compiler; its first execution may fetch its TeX
bundle. No inference or project dependency change is involved. Never run the old
`make paper` target to generate this document: that target writes the historical PDF.
The [compiled finalization PDF](memoryfence-finalization.pdf) is in this folder.
Compilation may produce different PDF metadata across platforms/bundle versions.

`generated/provenance.json` binds the Markdown SHA256, preserved-study counts and
independent raw verification. `generated/heldout-tables.tex` reports all seven
strategies for complete/marked/silent held-out conditions, with denominators.
`architecture.tex` is editable TikZ. The generator changes only this new folder.
The final validation documents actual build/render review and unresolved research.

References were checked against seven primary arXiv/ACL records on8 November2026,
including current v2 title metadata for Cross-User Poisoning. This is a metadata/
abstract refresh, not a new full-text systematic review or independent replication.
No acceptance status is inferred from an arXiv comment.
