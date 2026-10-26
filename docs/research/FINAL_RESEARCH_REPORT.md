# Final research report: publication pass

25 October 2026 · Complete with explicit scientific and publication limitations.

## Motivation and questions

How does provenance completeness affect persistence and security implications of
poisoned long-term agent memory? The manuscript separates deletion (RQ1), retrieval
(RQ2), behavior (RQ3), and transformation/interface interpretation (RQ4). These
organize the existing bounded endpoints, not a retroactive replacement protocol.
The original full confirmatory program remains incomplete.

## Method and evidence

The [full empirical report](COMPLETION_REPORT.md) remains the detailed record.
The [LaTeX manuscript](../../paper/main.tex) and [PDF](../../paper/memoryfence-paper.pdf)
provide the academic synthesis. Both genuine accessions were independently
reverified in a fresh Python 3.12.12 environment; their analysis JSON matched the
committed results byte for byte. No new inference or model download occurred.

The preserved cycle contains 72 actual Qwen2.5 1.5B responses: 24 qualification,
12 transformations and 36 behavioral calls. Three clean and three attack chain
executions each produced two derived memories. The same generated text supports
108 declared state views; 36 accidental LF0.0 views remain separately labeled.

## Main findings

Source-only deletion retained both poisoned descendants in all three attack chains.
Cascade deletion retained 0/6 attack descendants at LF1.0, 4/6 at LF0.75 and 6/6 at
LF0.5. These are six descendants, not six attack chains. DF2-exclude admitted
orphaned attack ancestry in 2/3 and 3/3 incomplete-lineage views. Nominal LF is an
edge-retention probability, not the realized fraction in a two-edge chain.

The paired qualification comparison changed only message order: original 9/12,
task-last 12/12, including empty retrieval 0/3 versus 3/3. All 36 subsequent replies
were valid and completed legitimate tickets, with zero objective proposals/effects
in each 3-call attack cell (0/18 effects overall). Three free-text fields echoed
the canary; one clean TT3 output lost useful content. No defense ranking follows
from a zero-effect baseline, and behavior was tested only at LF1.0.

## Mechanical extension

A [finite protocol](PUBLICATION_SENSITIVITY_PROTOCOL.md) preceded a zero-inference
exhaustive graph exercise: all 278 masks at depths 1, 2, 4 and 8. Production graph
traversal agreed with an independent contiguous-prefix formula for every mask.
At depth 2, one retained edge yields either 1 or 2 survivors depending on position.
At depth 8, four retained edges yield 4–8 survivors across 70 masks. These are
abstract graph configurations, not new model chains, database episodes, DF2 trials
or production missingness estimates. All rows are in
[chain-sensitivity.json](../../paper/generated/chain-sensitivity.json).

## Practical implications and limitations

Cascade deletion and author filtering can share a recorded-path dependency.
Unknown ancestry should be an explicit policy state; fail-closed handling or
quarantine requires separate utility evaluation. Source deletion, retrieval
exposure, free-text contamination and tool effects require distinct checks.

One source pattern, three chain seeds, one small quantized model, lexical retrieval,
literal tickets and one-input TT3 limit generalization. There is no human semantic
validation, broad held-out study, independent execution attestation, or demonstrated
incomplete-lineage behavioral exploit. The 278 masks establish only their abstract
linear-graph property. The three primary preprints support context, not novelty or
acceptance claims. The manuscript is not submitted, published or peer reviewed.

Future work: richer memory-dependent tasks, multi-source graphs, correlated losses,
broader models, human semantic labels and utility-aware unknown-ancestry controls.
See [claim matrix](CLAIM_EVIDENCE_MATRIX.md), [reproduction](REPRODUCIBILITY_REPORT.md),
[publication audit](FINAL_PUBLICATION_AUDIT.md), and [plain outcome](FINAL_OUTCOME.md).
