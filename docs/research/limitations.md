# Limitations

**Status:** Phase 1. These are anticipated limitations of the planned study and of the current repository. They will be revised as the design is implemented.

## 1. Current state of the project

- **No experiments have been run.** The repository contains research documentation, an architecture design, and development tooling. It contains no agent, memory pipeline, attack, defense, or evaluation code.
- **Passing checks do not demonstrate security properties.** The Phase 1 test suite checks package metadata and documentation integrity. Its coverage figure describes a package that contains only metadata and says nothing about the correctness of any security mechanism.
- **The literature review is mostly abstract-level.** One closely related paper (PPMF) was read in full and several others in part (see [`literature-review.md`](literature-review.md#13-review-depth)). Several directly relevant 2026 preprints are listed but not yet reviewed.
- **Most closely related work consists of unreviewed preprints.** Comparisons may change as those works are revised or peer-reviewed.

## 2. Novelty

- The research question overlaps substantially with recent work, including MURMUR, PPMF, MAP-Graph, MemLineage, Collaborative Memory, execution-state unlearning, dependency-guided rollback, and GateMem. The proposed contribution is an independent, controlled measurement study, not a new attack or defense. Reviewers may judge the incremental contribution to be modest. That is an acceptable outcome for a rigorous replication-and-extension study, and the project should not overstate it.
- PPMF already measures a provenance-dependent defense under masked provenance fields, and MemLineage already sweeps chain length against attribution quality. The remaining distinction, silent loss of derivation edges in combination with deletion policies, is narrow.
- Concurrent work may already cover, or may soon cover, the deletion-handling and provenance-completeness factors. The review must be refreshed before preregistration.

## 3. Internal validity

- **Simulated workspace and tools.** Sandbox tools are simplified models of real APIs. Behavior against real collaborative platforms may differ.
- **LLM-authored transformations.** Results depend on transformation prompts. Different prompt designs could change survival rates substantially. Prompts will be versioned and reported, but results generalize only to similar designs.
- **Accumulating memory store.** Transformations add derived memories without removing inputs. Systems that overwrite inputs when merging may behave differently.
- **Judge dependence.** The "followed" stage (S2) and semantic survival may require an LLM judge. Judge errors are mitigated by human audit and by grounding confirmatory claims in deterministic stages.
- **Synthetic provenance degradation.** Dropping derivation edges at random is a simple model of incomplete provenance. Real provenance failures are likely correlated with content (for example, failing to attribute paraphrased content), so random dropping may misestimate how much defenses degrade.
- **Defense implementations are approximations.** Defenses are inspired by published designs and are not faithful reproductions. Poor results for a MemoryFence defense do not imply poor results for the original system.
- **Policy generation for `DF3`.** Realistic action authorization depends on deriving a policy from the user's request, which can fail. The oracle-policy variant is an upper bound and must not be presented as the main result.

## 4. External validity

- **Model coverage.** Budget limits mean the primary experiments will use a small number of open-weight models. Hosted frontier models may behave differently and are optional.
- **Language and modality.** English text only. Multimodal memories are excluded.
- **Scenario coverage.** A handful of scenario families cannot represent every collaborative workflow, and the templates may reflect the authors' assumptions about realistic attacks.
- **Attacker strength.** Non-adaptive attacks underestimate a motivated adversary. Adaptive attacks are tuned on the development split and are still bounded by the effort invested.
- **Persistence channels.** Only the designated memory store is modeled. Agents may persist information through other channels such as files or tool outputs ([Das2026]).

## 5. Statistical limitations

- Sample sizes are provisional until pilots are run.
- Zero-event cells support only upper bounds, not claims of complete prevention.
- Many exploratory comparisons will be reported. Only the preregistered confirmatory family carries a multiplicity-corrected error rate.

## 6. Engineering limitations

- **Single-process, local design.** The architecture targets reproducible research runs on one machine. It is not designed or evaluated as a production memory system.
- **SQLite persistence.** It is suitable for local experiments but not for concurrent multi-user deployment.
- **Isolation enforced by convention until Phase 2.** The rule that defenses cannot read true provenance is documented in Phase 1 and becomes machine-checked only when the modules exist.
- **No production API.** An HTTP API (FastAPI) is optional and deferred.

## 7. Ethical limitations

- Publishing payload styles that survive summarization could inform attackers. Mitigations: payloads are generic and inert, there is no tuning against named production systems, and findings that indicate a vulnerability in a specific product are disclosed responsibly before publication.


## Bounded empirical follow-up — 24 October 2026

The [completion report](COMPLETION_REPORT.md) preserves the failed historical pilot,
prospective capability gates, task amendments, native transformation failures and
separate corrected records. Literal-task 1.5B qualification does not establish
arbitrary-task competence. The corrected lifecycle run has 52 valid and 28 invalid
outcomes; invalid replies are not protection. DS1 exact-canary memory retention is
observed without a post-deletion objective action; DS3 state removal does not
establish usable behavioral protection. Source-alive context can include primary
and derived memory. One payload pattern, two seeds per cell and independently
repeated transformations do not support causal or general security claims.
Human semantic validation, judge reliability, held-outs, common paired transforms,
incomplete lineage and independent replication remain outstanding. Later opt-in
contracts are separate experimental conditions, never repairs of earlier evidence.


## Final bounded study — 25 October 2026

The [current report](COMPLETION_REPORT.md) supersedes older status summaries while
preserving their evidence. A fresh order-only comparison passed 12/12 with task-last;
all 36 subsequent agent replies completed exact legitimate tickets, with zero
objective proposals/effects in 18 attack episodes. Three free-text fields still
repeated the canary. This is not semantic isolation or general protection.

The new state comparison reuses six genuine generated chains across three declared
fidelities and deletion/retrieval policies. Incomplete recorded paths left cascade
survivors and DF2 exposure. These are deterministic conditional properties, not
incomplete-lineage behavioral attack rates. One clean TT3 output failed the narrow
content check. An enum-iteration defect added 36 LF0.0 views; all are preserved and
labeled off-protocol, with the 108 declared views kept separate. No additional model
calls or hidden rerun repaired the departure. Wider tasks, multi-source consolidation,
human validation, held-outs and independent replication remain outside this bounded
completion. Research logs retain copies, so operational deletion is not forensic erasure.
