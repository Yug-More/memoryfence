# Expanded Study v1 — prospective finite protocol

Declared 7 November 2026, before Expanded Study execution. Original Study bytes and
findings are pinned separately. Stop after the declared matrix; preserve failures.

## Questions and design

RQ1: Under what lineage conditions does deleted-source content remain in operational
derived memory or retrieval? RQ2: Does it cause behavioral influence? RQ3: How do
containment and selective re-derivation change security/utility/overhead?

This expansion addresses RQ1 and the **deterministic memory-utility** part of RQ3.
RQ2/new model behavior is unavailable without a free model runtime and remains
unmeasured. No scripted output is represented as genuine inference.

Freeze 16 distinct DAG/operation families, each with five counterfactual cases:
attack/complete, attack/marked partial, attack/silent partial, clean/complete and
never-exposed/complete. Total 80 case configurations, **16 primary family clusters**.
Twelve families are development; four whole families are held out. All variants of
a family stay in one split; topology/operation signatures cannot cross splits.
Source kinds cover five fixture formats. Node graphs include single-source copies,
chains, fan-outs, joins, diamonds, late/multiple-source merges and repeated updates.
Complete and partial loss use the existing seeded nested provenance writer. Partial
LF0.5 is nominal, with actual edges recorded. No incorrect-edge or partial-source
redaction claim is made. No new embedding index is necessary.

80 cases deliberately fall below the 150–300 planning target: structural diversity,
controlled counterfactuals and verifiable annotations take precedence over padding.
Queries and fixture facts are versioned. They are synthetic and deterministic,
not human-annotated natural-language semantic outcomes. Held-outs share the protocol
and attack objective; the split checks structural-template leakage, not universal
semantic independence. No tuning after held-out inspection; a confirmed design
change requires a new version and disclosed re-evaluation.

## Fair baselines and proposed mechanism

All strategies clone the **same built input** for each case and see the same recorded
graph/metadata and text. Strategy order is deterministically hash-shuffled per case.

- `source_only`: production DS1, no extra filter.
- `keyword`: DS1, exact-canary exclusion. This strong keyword baseline is explicitly
  payload-aware, not weakened to make the new method win; paraphrase robustness is
  not established by this dataset.
- `direct`: DS1 plus revocation of immediate recorded children only.
- `cascade`: production DS3 over available transitive links. Complete-provenance
  cases implement the complete-tracking comparator; partial cases do not become an
  oracle. True-graph diagnostic completeness is evaluator-only.
- `rederive`: production DS4 and deterministic surviving-input fact projection,
  without new containment checks (missing-metadata/recomputation ablation).
- `quarantine`: DS3 plus completeness/lifecycle retrieval guard (no recomputation).
- `memoryfence`: DS4 plus the same retrieval guard and guarded re-derivation inputs.

The guard rejects marked-incomplete ancestry, orphan derived memories and ancestry
from unavailable sources. It does not reject arbitrary readable peers before source
deletion. Re-derivation projects only actually supplied surviving facts; it neither
recovers deleted content nor uses evaluator labels. Blocked re-derivation remains
pending and is reported. The proposed method is explicitly a composition of existing
selective re-derivation with observable-lineage containment, **not an invented
alternative to graph reachability**. At complete lineage it can be equivalent to
existing DS4; the analysis must report equivalence rather than manufacture novelty.

Matrix: 80 cases ×7 strategies =560 paired deterministic runs; one fixed seed per
family/case. No stochastic trials or model responses. Evaluate development first,
then held-outs once the implementation passes tests. Keep all predefined cases.

## Metric definitions

For each run preserve numerator, denominator and unit; zero denominator is undefined.

- Persistence: live original target-dependent derived artifacts / original target-
  dependent derived artifacts. Include attack or clean source deletion, report
  populations separately. Evaluator true ancestry defines targets.
- Accessible persistence: target-dependent original artifacts allowed after guard /
  same denominator. Physical survival and containment are different.
- Target-fact persistence: unique deleted-source facts accessible in any derived
  memory (including replacements) / original deleted-source facts. This catches
  reintroduction that original-ID persistence alone would miss.
- Malicious retrieval: retrieved canary-bearing derived artifacts / all retrieved
  derived artifacts; also case exposure indicator over eligible attack cases.
- Deletion completeness: removed or revoked original true target descendants /
  target descendants. Retrieval quarantine alone does not count as physical deletion.
- Recorded coverage: captured true derivation edges / required true derivation
  edges; primary source links excluded. False edges are separately unsupported.
- Benign retention: unique unrelated-source fact IDs accessible in derived memories /
  unique unrelated fact IDs available in derived memories before deletion.
- Fact lookup success: exact predeclared unrelated target fact in derived answer
  context / one eligible lookup. **Not LLM legitimate-task success**.
- Benign fact loss: unavailable eligible unrelated fact IDs / same benign denominator;
  a factual-utility measure, not all-cause artifact over-deletion.
- Pure benign artifact over-deletion: original derived memories with only unrelated
  facts that become inaccessible / such originals. Mixed artifacts reported via
  fact loss rather than arbitrarily classifying their removal as wrong.
- Precision/recall: selected derived memories containing the exact target fact /
  selected derived memories; selected relevant / accessible relevant derived
  memories, with exact fixture relevance and explicit empty denominators.
- ASR, unauthorized tool action, LLM utility, output contamination: null/unmeasured
  in Expanded Study v1; historical genuine values are never substituted.

Measure build/ingestion once per case; deletion, recomputation, guarded retrieval,
SQLite byte footprint and recorded/true edge counts per strategy. Report raw timings
and hardware, medians and dispersion descriptively; no production performance claim.
No new token usage or model cost beyond zero calls. Timings/storage are not scientific
independent samples of model performance and vary across machines/cache order.

## Validation and analysis

Validate graph acyclicity, parent existence, stable IDs, source/fact annotation,
never-exposure controls, family-group splits and unique structural signatures.
Compare evaluator recomputation of raw snapshots with saved metrics; include tamper
checks. Retain real SQLite before/after pairs and structured results in an XZ ZIP
accession. Stable outcomes exclude timings/host paths; rerun software fixtures in CI,
never inference. Paired deltas aggregate **within family first**, then across families;
report split/family denominators and deterministic descriptive ranges, not binomial
CIs treating 560 records as independent. No significance or broad efficacy claim.

Log code/config/dataset hashes, dependency hash, seed, UTC time, status/error and all
strategy conditions. Original protocols, originals and previous manuscript stay
unchanged. Source-type adapters are benchmark fixture renderings, not production
email/repository connectors or independent source-type generalization evidence.
