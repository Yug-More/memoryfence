# Initial research audit — 7 November 2026

## Audited entry state

Entry main: `f51a8360aca39a428ca41bfc9afe10447d175d72`. The working tree already
has `paper/memoryfence-paper.pdf` deleted by the user. Preserve that change; the
committed PDF remains in Git history. No model executable/weights were found on
PATH; actual new inference is conditional on an available explicitly free local
runtime, not silently replaced by fixtures.

The existing typed Python/Pydantic/SQLAlchemy/SQLite framework implements two
provenance graphs, read-only defense views, DAG validation, nested seeded edge
loss, five deletion policies, selective re-derivation, lexical ACL retrieval,
role/delegation authorization, sandbox tool effects, loopback Ollama, explicit
native/schema contracts, exact response/effect scoring, raw journals, versioned
manifests and replay. There is no hosted application, embedding index or model
training pipeline. Sources: `src/memoryfence/{provenance,workspace,memory,defenses,
access,authorization,llm,evaluation}` and their tests.

## Original evidence and limits

Three historical accession directories remain in place and are hash-pinned in
[legacy baseline](../experiments/legacy_baseline/manifest.json). Final bounded
inference contains 24 qualification, 12 transformation and 36 agent responses;
three clean and three attack chains; 108 declared state views and 36 extra views.
Source-only deletion retains both descendants; cascade retains 0/6, 4/6, 6/6
attack descendants at nominal LF1.0/LF0.75/LF0.5. Behavior is only LF1.0: 36 exact
legitimate effects, 0/18 attacker objectives, three free-text echoes. A clean TT3
lost useful content. These are saved observations, not a general defense guarantee.
The precise claim status ledger is [RESEARCH_CLAIMS.md](RESEARCH_CLAIMS.md).

The entry publication stage records 246 tests at 91.58% coverage; 238 is a valid
historical pre-publication suite count, not the entry-current count. A fresh
pinned-suite run will be separately recorded. Evidence verification does not
constitute new model inference or independent execution-host attestation.

## Prioritized gaps and justified enhancement

1. DF2 permits a derived memory with an empty recorded author set. Silent lineage
   loss has no detectable marker. Implement explicit opt-in completeness-aware
   containment using operational metadata, with no evaluator oracle access.
2. Existing DS4 can recover mixed-source utility, but the final genuine experiment
   is a single-source chain. Evaluate multi-source deletion and safe re-derivation
   against fair source-only/keyword/direct/transitive alternatives on shared inputs.
3. Distinguish marked loss (observable) from silent loss (unobservable). Do not
   claim an observable-metadata defense solves unmarked missing or incorrect edges.
4. Replace a sample-size target with structural diversity and grouped splits.
   Report templates and counterfactual configurations separately; do not manufacture
   hundreds of near-duplicate independent scenarios.
5. Define security/utility denominators, missing behavior values and raw latency
   measurements. A deterministic content/retrieval study is not model ASR.
6. Preserve the old manuscript and results; create an expanded research synthesis
   that reports equivalence/utility failures and compute blockers explicitly.

No broad architectural rewrite or runtime dependency is justified. New model-backed
behavior, human semantic validation, large stochastic generalization and production
overhead claims cannot be substituted by passing tests or deterministic fixtures.
