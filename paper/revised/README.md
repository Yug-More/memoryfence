# Current research manuscript

**MemoryFence: Provenance Gaps, Source Deletion, and Information Retention in Agent Memory**
Yug Amol More · 18 November 2026 · Unpublished manuscript

[PDF](memoryfence-manuscript.pdf) · [LaTeX](main.tex) · [References](references.bib) ·
[Verification](../../docs/MANUSCRIPT_VERIFICATION_2026_11_18.md) ·
[Contributions and disclosure](../../docs/AUTHORSHIP_AND_DISCLOSURE.md)

This synthesis distinguishes the October generated-chain study, the November
560-run deterministic comparison and the separate 74-request local-model follow-up.
It includes the runner deviation, failed early controls, silent-gap failures,
utility costs and absence of behavioral separation between final model strategies.
It is not submitted, accepted or peer reviewed.

## Model-free verification and build

From the repository root, with Python 3.12+, Git and the frozen project environment:

```bash
uv sync --frozen
uv run --frozen python paper/revised/generate.py
make paper TECTONIC=/path/to/tectonic
```

`generate.py` independently recomputes the preserved analyses, checks all 278 graph
masks, verifies 560 expanded records and their saved semantic reproduction, and
reconciles all 74 later model requests with contexts/proposals/sandbox effects.
It writes only this folder's generated tables and hash ledgers. It makes no model
request and needs no model weights or plotting package. Run the full software suite
separately with `make check`; software checks are not scientific validation.

The optional compiler is [Tectonic 0.17.0](https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.17.0).
It is free; its initial run may download TeX resources. `make paper` writes its
intermediate files under `.paper-build/revised/` and the PDF in this folder. No shell
escape is used. TeX bundle/font metadata can differ across hosts; source/evidence
reproducibility does not require byte-identical PDFs.

## Evidence preservation

`../main.tex` is the historical October paper. `../finalization/` is the preserved
8 November synthesis, whose blocked-runtime account predates the completed model
follow-up. Neither is rewritten by this build. The preexisting deletion of
`../memoryfence-paper.pdf` is not restored. Historical internal contribution notes
are superseded for the current manuscript by the dated author confirmation, but
remain in historical sources to preserve their development record.
