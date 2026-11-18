# MemoryFence research manuscripts

The current work sample is **MemoryFence: Provenance Gaps, Source Deletion, and
Information Retention in Agent Memory**, by **Yug Amol More**, revised 18 November 2026.

[Current PDF](revised/memoryfence-manuscript.pdf) · [LaTeX](revised/main.tex) ·
[Build instructions](revised/README.md) ·
[Evidence verification](../docs/MANUSCRIPT_VERIFICATION_2026_11_18.md) ·
[Authorship and AI assistance](../docs/AUTHORSHIP_AND_DISCLOSURE.md)

This is an unpublished research manuscript, not an accepted or peer-reviewed paper.
The current synthesis separates model-generated chains, deterministic memory-state
comparisons and the later exploratory local-model follow-up. Its tables are
regenerated from independently verified supplied evidence; no new inference is
required to build it.

```bash
uv sync --frozen
make paper TECTONIC=/path/to/tectonic
```

Tectonic 0.17.0 is an optional free LaTeX compiler. Its first run may fetch TeX
resources. The current build does not restore the deleted historical PDF, alter
raw experiments or rewrite historical manuscript sources.

## Historical versions

- [October bounded-study source](main.tex), original [bibliography](references.bib)
  and [claim map](../docs/research/CLAIM_EVIDENCE_MATRIX.md).
- [Preserved 8 November synthesis](finalization/README.md), including its ten-page PDF.

Historical versions retain dated limitations and contribution notes. The dated
confirmation in the current authorship record establishes the author-reported
research roles without implying unaided implementation. No project license has
been selected.
