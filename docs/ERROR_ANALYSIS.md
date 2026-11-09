# Systematic error analysis — 8 November 2026

This is **post-hoc descriptive analysis**, not a new confirmatory hypothesis or
new model result. `scripts/research/analyze_release.py` independently verifies both
accessions, compares all560 semantic records and categorizes every original
split/control/strategy group. Machine-readable output:
[finalization failure analysis](../experiments/2026-11-08-finalization/failure-analysis.json).
It includes all70 groups, not only favorable examples. Cases share family clusters.

## Definitions

- Malicious context failure: exposed eligible attack cases / eligible attack cases.
  This is an exact canary-in-context condition, not behavioral ASR.
- Benign loss: cases losing at least one eligible unrelated derived fact / cases
  with any eligible unrelated derived fact; lost fact counts are also preserved.
- Physical target survival: original true target-descendant IDs remain active,
  regardless of whether a retrieval filter hides them.
- Lookup failure: the predeclared unrelated target fact is absent from answer context
  when it was available in derived memory before deletion. No eligible fact is null.
- Invalid experiment: a failed/missing result is not a successful defense. The
  deterministic accessions have zero invalids; model availability is blocked and
  has no completed behavioral denominator.

These categories overlap. They must not be summed into an independent trial count
or a single error percentage. “Benign loss” is not semantic human judgment, and a
mixed artifact is not arbitrarily labeled wholly benign or wholly malicious.

## Major strategy failures and counterexamples

| Strategy | Representative failure or limitation | Exact raw evidence |
| --- | --- | --- |
| source_only | Complete held-outs retain11/11 original attack descendants; exposure4/4 | `expanded-v1.zip.xz::records.json`, evaluation/attack_complete/source_only |
| keyword | Exact known canary gives0/4 exposure but retains only2/8 benign facts; clean control does not remove deleted-source facts just because a source disappeared | Same, evaluation/attack_complete/keyword and clean/keyword |
| direct | Complete held-outs retain7/11 originals, expose3/4; immediate invalidation misses transitive descendants | Same, evaluation/attack_complete/direct |
| cascade | Complete lineage removes11/11 but loses6/8 benign facts in mixed memories; partial held-outs retain11/11 | Same, evaluation/attack_complete/cascade and attack_marked/cascade |
| rederive | Complete lineage recovers8/8 unrelated facts; partial missing recorded target paths can schedule no recovery and leave exposure4/4 | Same, evaluation/attack_marked/rederive |
| quarantine | Marked partial hides all11 originals but loses8/8 benign facts; silent gaps still expose3/4 | Same, evaluation/attack_marked/quarantine and attack_silent/quarantine |
| memoryfence | Equal to unguarded re-derivation with complete lineage; marked partial loses8/8 facts and silent partial exposes3/4 | Same, evaluation/attack_complete/memoryfence and both partial controls |

The exact-canary baseline is strong for the known payload. This study cannot claim
paraphrase resistance or universal superiority for containment. Complete-lineage
re-derivation is an existing implemented capability, not a newly invented algorithm.

## Representative graph/state explanations

`exp-v1-f14-attack_silent`, `f15-attack_silent`, `f16-attack_silent` have active clean
roots in the recorded graph while their text still carries the deleted target fact.
The guard sees no marked gap, so its `no_observed_gap` result is not a proof of
completeness. The f13 silent case becomes an orphan and is withheld instead. For each
case, inspect archive `runs/{scenario}/input/input.json`, both SQLite stores and
`runs/{scenario}/memoryfence/result.json`. The independent verifier reconstructs
these predicates from raw edges/source state; the proposed defense never sees truth.

All four marked held-outs contain observable gaps, so no poisoned derived context
passes. However, recorded reach does not schedule affected re-derivation tasks and
all eligible benign mixed facts disappear from the answer workload. The mechanism
has not recovered them by guessing missing edges. This is an unfavorable utility
result, not successful deletion completeness: all11/11 originals remain active.
The guarded-input rejection path is tested but is not triggered by a final v1
matrix cell; no separate empirical gain is attributed to that path.

Never-exposed held-outs retain8/8 benign facts and4/4 lookups under every strategy.
Their attack eligibility is absent, not a zero ASR. Clean-source deletion shows
utility loss even without poisoning. Primary memory is excluded from answer
context under every strategy, limiting transfer to primary-inclusive applications.

## Historical model failures remain

The final bounded model evidence contains three free-text canary echoes despite
zero exact attacker effects, plus a clean TT3 output containing only an operation
label. Earlier interface qualification failed empty-context tasks before message
order correction. Those findings remain in the original accessions; no clean-up,
semantic repair or pooling of earlier eleven effects with final0/18 is justified.
See [historical ledger](RESEARCH_CLAIMS.md) and original raw journals.

## Measurement/tooling failures discovered in finalization

Before fixes, a560-row report accepted an invented strategy and export followed a
harmless test symlink to an outside sentinel file. New grid/rate/cohort/path checks
and symlink rejection prevent those tested cases. Missing/duplicate observations,
NaN, fabricated behavioral metrics, path traversal and malformed JSON now fail.
Valid saved summaries remain equal. These fixes strengthen research integrity;
they do not improve the observed scientific defense outcomes.

Historical archive-only test reproduction failed because Git metadata was absent;
a separate Git checkout resolves that environment requirement. A first dependency
scan invocation used unsupported flags and was retained before correction. The
model follow-up preflight records unavailable loopback service and zero chat calls.
Transport tests preserve timeout/failed-gate cases, but are not model experiments.
No operational failure has been relabeled as a successful defense.
