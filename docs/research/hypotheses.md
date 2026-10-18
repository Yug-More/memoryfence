# Hypotheses

**Status:** Draft for preregistration. These hypotheses are predictions to be tested, not findings. They will be frozen, together with the analysis plan and sample sizes, before any run on the evaluation split (see [`experimental-protocol.md`](experimental-protocol.md#12-preregistration)).

## Conventions

- **ASR** means end-to-end attack success, the unconditional rate of stage S4 (executed). Stage definitions are in [`experimental-protocol.md`](experimental-protocol.md#41-stage-definitions).
- Condition codes (for example `DS1`, `DF3`, `LF0.5`) are defined in [`experimental-protocol.md`](experimental-protocol.md#3-independent-variables). Research questions RQ1–RQ6 are defined in [`problem-statement.md`](problem-statement.md#7-research-question).
- Confirmatory hypotheses form one family corrected with **Holm–Bonferroni at α = 0.05**. Exploratory analyses are reported without that correction and labeled exploratory.
- Where a hypothesis restates something prior work has already reported, it is marked **replication**. MemoryFence does not claim novelty for replications.
- Every hypothesis could turn out false. A falsified hypothesis is a result to report, not a failure to hide.

## Summary

| ID | RQ | Comparison | Outcome | Test | Block |
|---|---|---|---|---|---|
| H1 | RQ1 | TD = 1 vs. 2 vs. 3 | S0 | One-sided trend test | E1 |
| H2a | RQ2 | `DS1` vs. `DS0` | PD-ASR vs. ASR | Paired non-inferiority, margin δ | E2 |
| H2b | RQ2 | `DS2` vs. `DS1` at `LF1.0` | PD-ASR | One-sided exact McNemar | E2 |
| H3a | RQ3 | `DF2` vs. `DF0` | ASR | One-sided exact McNemar | E3 |
| H3b | RQ3 | `DF3` vs. `DF0` | ASR | One-sided exact McNemar | E3 |
| H3c | RQ6 | `DF2-exclude` vs. `DF0` in `C-LEGIT` | Legitimate-instruction compliance | One-sided exact McNemar | E3 |
| H4 | RQ4 | Defense × `LF` | ASR | Mixed-effects interaction; TOST on `DF3` slope | E4 |

## Confirmatory hypotheses

### H1: Survival declines with transformation depth (RQ1)

For LLM-mediated transformations, the payload survival rate (S0) decreases as transformation depth increases from 1 to 3 rounds.

- **Test:** One-sided Cochran–Armitage trend test on S0 across depth levels, pooled over transformation types. Mixed-effects logistic regression with a random intercept per scenario template serves as a robustness check.
- **Would be falsified by:** No significant decreasing trend, or a significant increasing trend.
- **Rationale:** Each lossy rewrite is an opportunity to drop or neutralize the instruction, but consolidation may also reinforce repeated content. A null or reversed result would itself be informative.

### H2a: Source-only deletion leaves post-deletion attack success largely intact (RQ2, replication-extension)

Under source-and-primary deletion (`DS1`) with no defense, post-deletion ASR is **non-inferior** to the no-deletion control (`DS0`): it is not lower by more than a margin δ = 5 percentage points.

- **Test:** Paired non-inferiority test (one-sided, α = 0.05) on matched episodes, using a confidence interval for the paired risk difference.
- **Would be falsified by:** The lower confidence bound of (ASR under `DS1` − ASR under `DS0`) falling below −δ.
- **Relationship to prior work:** [Yao2026] reports, in a privacy framing, that source redaction leaves derived influence active. H2a tests the analogous claim for cross-principal instruction payloads and unauthorized actions.

### H2b: Provenance-based revocation reduces post-deletion attack success when provenance is complete (RQ2)

With complete recorded provenance (`LF1.0`) and no other defense, tombstone revocation (`DS2`) yields lower post-deletion ASR than source-and-primary deletion (`DS1`).

- **Test:** Exact McNemar test on matched episodes (one-sided).
- **Would be falsified by:** No significant reduction.

### H3a: Provenance-aware retrieval reduces attack success (RQ3)

With complete recorded provenance, provenance-aware retrieval (`DF2`) yields lower ASR than no defense (`DF0`).

- **Test:** Exact McNemar test on matched episodes (one-sided).
- **Would be falsified by:** No significant reduction.

### H3b: Independent action authorization reduces attack success (RQ3)

Independent action authorization (`DF3`) yields lower ASR than no defense (`DF0`).

- **Test:** Exact McNemar test on matched episodes (one-sided).
- **Would be falsified by:** No significant reduction.

### H3c: Provenance-aware retrieval has a measurable false-positive cost on legitimate cross-principal instructions (RQ6)

In the legitimate-instruction control (`C-LEGIT`), provenance-aware retrieval in its exclusion variant (`DF2-exclude`) lowers legitimate-instruction compliance compared with no defense.

- **Test:** Exact McNemar test on matched episodes (one-sided).
- **Would be falsified by:** No significant reduction in compliance.
- **Rationale:** A defense that blocks all cross-principal content trivially lowers ASR. This hypothesis makes its cost visible.

### H4: Lineage-dependent defenses degrade with provenance completeness; independent authorization does not (RQ4)

The ASR reduction achieved by lineage-dependent defenses (`DF2`, `DF5`) shrinks as recorded provenance becomes less complete (`LF1.0` → `LF0.0`). The ASR reduction achieved by `DF3` shows no such dependence.

- **Test:** Mixed-effects logistic regression of S4 on defense × lineage fidelity (fidelity as an ordinal covariate), with random intercepts per scenario template. H4 is supported if the defense × fidelity interaction is significant for `DF2` and `DF5` in the predicted direction, and the `DF3` slope is equivalent to zero within a prespecified margin (TOST on the log-odds slope, margin fixed at preregistration).
- **Would be falsified by:** A non-significant interaction for `DF2` or `DF5`, or a `DF3` slope that is not equivalent to zero.
- **Note:** `DF3` does not read provenance by design, so H4's second clause mainly checks that the harness implementation matches that design.

## Exploratory analyses

These are reported descriptively with confidence intervals and are not used for confirmatory claims.

| ID | RQ | Question |
|---|---|---|
| X1 | RQ1 | Do transformation types (extractive, abstractive, consolidation, reflection) differ in payload survival? Our tentative expectation is that extractive summaries preserve payloads more often than abstractive ones, but we hold this weakly. |
| X2 | RQ1 | Which payload styles (explicit imperative, disguised workflow note, conditional trigger, authority impersonation) survive and execute most often? |
| X3 | RQ3 | Does combining provenance-aware retrieval with action authorization (`DF4`) lower ASR beyond either alone, and at what utility cost? |
| X4 | RQ5 | How do conditional rates differ across stages, for example P(S4 \| S3) under `DF3`, compared with prior reports of injection-execution dissociation ([Leong2026])? |
| X5 | RQ2 | How often does the victim agent re-seed the payload into new content (objective O4) after deletion? |
| X6 | RQ1 | How does distractor-memory volume affect retrieval and attack success ([Sunil2026])? |
| X7 | All | How do results vary across model backends? |
| X8 | RQ6 | Does cascade with re-derivation (`DS4`) preserve benign task success better than cascade hard deletion (`DS3`)? |
| X9 | RQ4 | How does residual retrievability under `DS2` and `DS3` change as recorded provenance becomes less complete? |
| X10 | RQ4 | Does marking memories with incomplete provenance (the "marked" variant) change the behavior of `DF2` and `DF5` compared with silent loss, and at what false-positive cost (compare [Xu2026])? |

## What would change the project's direction

- If H2a is falsified because source-only deletion largely removes attack success, the deletion factor is less important than expected, and the study should emphasize transformation and defense comparisons.
- If H1 shows near-zero survival for all LLM-mediated transformations, the threat is mostly limited to raw retrieval, and the study should focus on that path and on payload styles that survive transformation.
- If the legitimate-instruction control shows that every evaluated provenance defense has a prohibitive false-positive cost, that trade-off becomes a primary result.
