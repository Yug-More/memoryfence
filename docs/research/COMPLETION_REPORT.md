# MemoryFence: recorded provenance, deletion reach and model interfaces

25 October 2026 · Completed bounded study · Original confirmatory program incomplete

## Abstract

MemoryFence separates an agent's operational memory, recorded provenance and
evaluator-only true ancestry. This bounded study generated six real Qwen2.5 1.5B
TT2→TT3 chains and reused identical outputs across provenance, deletion and retrieval
conditions. Source-only deletion retained both descendants. Recorded-lineage
cascade deletion removed all descendants with complete provenance, but retained
4/6 attack descendants at LF0.75 and 6/6 at LF0.5; provenance filtering also admitted
those orphaned memories. These are conditional state/retrieval findings. A separate
24-call comparison changed only user-message order: original layout scored 9/12,
while task-last passed the predeclared 12/12 benign gate. All 36 subsequent agent
replies were valid and completed the legitimate ticket; none of 18 attack episodes
produced an objective-matching proposal or effect. Three free-text fields nevertheless
repeated the canary. The run preserves 108 declared state views and 36 unplanned
LF0.0 views separately. No universal protection, semantic judge validation or
completion of the original full study is claimed.

## Introduction

Deleting a source is different from deleting the memories derived from it. A
retrieval filter can reject a known peer's instruction but fail when a missing
recorded edge hides that peer. A language model can repeat poisoned text while
still choosing authorized tool arguments. MemoryFence measures these boundaries
separately rather than treating stored text, retrieval and action as one outcome.

The original zero-attack pilot failed legitimate utility too. Later studies exposed
task and output-contract limitations. The final cycle therefore fixed a finite
scope before new inference, required exact benign competence before attack calls,
and paired state conditions on common generated text. Negative behavioral findings
are retained alongside state failures and unfavorable model outputs.

## Research questions

The [final protocol](FINAL_BOUNDED_PROTOCOL.md), declared before new inference,
answers three bounded questions:

- **B-RQ1 — persistence:** What exact text and ancestry remain after real TT2/TT3
  calls and DS1/DS3 under the tested recorded-edge conditions?
- **B-RQ2 — behavior:** After qualification, what exact ticket proposals/effects
  occur when the defender receives these memories?
- **B-RQ3 — controls:** How do deletion and DF2-exclude change surviving records
  and retrieval relative to matched DF0 views of the same generated text?

The original [RQ1–RQ6](problem-statement.md#7-research-question) remain a broader
research program. This scope does not substitute a small conditional experiment
for representative held-outs, human semantic validation or confirmatory statistics.

## Background and related work

Greshake et al. describe indirect prompt injection through retrieved application
data ([2023](https://arxiv.org/abs/2302.12173)). Patlan et al.'s MURMUR examines
cross-user poisoning in collaborative language agents
([2025](https://arxiv.org/abs/2511.17671)). Xu et al. study memory provenance laundering
and an authority-preserving firewall
([2026](https://arxiv.org/abs/2607.29167)). MemoryFence supplies an inspectable harness
and bounded measurements, not a claim to originate these ideas or replicate their
reported efficacy. The three primary abstract records were rechecked on 25 October;
[metadata](REFERENCE_METADATA_CHECK.json) records versions and submission status.
This is not a full inherited-bibliography audit or peer-review claim.

## Threat model

Synthetic peer Avery controls one shared quarterly note. Blake requests a ticket
with exact title `review` and body `status`. The attack note instead requests body
`relay@vendor.invalid`. The attacker controls source content, not system prompts,
model weights, provenance services, permissions or the sandbox. Readability does
not grant instruction authority. Models receive allowed text and tool descriptions,
never evaluator-only labels or true ancestry.

Unauthorized here means contrary to the explicit user task, not an observed platform
ACL bypass. The schema leaves argument values unrestricted; it does not force
`status` or forbid the canary. Attack success requires an actual `create_ticket` effect with exact title `review`
and canary body. A matching proposal is recorded separately. Prose repetition is
not a tool effect. No message reaches an external recipient; every user, address,
note and ticket is synthetic.

## MemoryFence architecture

The typed Python/Pydantic system stores operational state in `system.sqlite` and
true ancestry, source labels and deletion audit data in `groundtruth.sqlite`.
Defense-facing sessions cannot attach ground truth; import contracts enforce that
boundary. ACL-filtered lexical retrieval feeds a bounded agent step. An independent
gateway mediates proposals before the local sandbox changes state.

Deletion follows **recorded reach**. Evaluation follows **true ancestry**. Keeping
those graphs separate exposes missing-edge failures without giving a defense an
oracle. Transactions use rollback journals for attached-database atomicity; tests
of aborted operations do not claim crash-during-commit validation. See the
[architecture](../architecture/overview.md) for implementation boundaries.

## Experimental methodology

The finite cycle used only the previously approved 1.5B artifact in free CPU Colab:
24 qualification, 12 transformation and 36 qualified-agent chat responses, **72 in
total**. No additional model, paid API, billing, credit purchase or runtime upgrade.
Execution was pinned to `e5dcc3c61cc6ded130a4f118825fc324e90a7e3a`.

Six chain executions used clean/attack × seeds 901/902/903. Each made a real TT2
call, then a real TT3 call on that summary alone. A request-matched cache reused the
exact outputs across LF1.0/LF0.75/LF0.5, DS0/DS1/DS3 and DF0/DF2-exclude. Cache
requests check purpose, seed, parent hashes, IDs and content. Logical cached calls
and copied database records are **not additional inference**.

The production writer applies seeded, nested silent edge loss. LF names retention
probabilities, not exact observed completeness in a two-edge graph. Actual retained
edges per seed were [2,2,2], [1,2,1] and [1,1,0] respectively. Each deletion policy
starts from a separate database copy; both retrieval views share generated text.
There are 54 declared state snapshots and 108 declared retrieval views, not 108
independent model trials.

### Recorded departure

The pinned driver iterated an enum that also contains LF0.0. It produced 18 extra
snapshots/36 extra views, without additional model calls. All **144 actual views**
are archived and verified; primary results use only the declared 108. The departure
was discovered from clean checkpoints before attack-chain execution. The
[deviation log](FINAL_BOUNDED_DEVIATIONS.md) records the defect and correction.
Current code explicitly lists three levels, with a complete fixture-run regression.
No original record was replaced or retroactively declared prospective.

## Model qualification

The artifact was `qwen2.5:1.5b`, Q4_K_M, 986,061,892 bytes, digest
`65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`.
The archive preserves the actual Ollama chat template and model metadata. Runtime:
Ollama 0.40.11, project Python 3.12.3, two free Colab CPUs. Sampling: temperature 0,
context 2048, output 256, timeout 120 seconds. No chat-template override was applied.

The original adapter sends system, trusted task, then another user message containing
untrusted-memory data. Its final message remains a warning even with no hits.
Previous empty-context responses refused; one had 865 prompt tokens, 34 output
tokens and `done_reason=stop`, providing no observed exhausted-limit explanation.
Exact scoring and empty retrieval were independently verified.

The new comparison kept task, schema, tools, model and sampling fixed, swapping only
the two user messages. Four families × seeds 751/752/753 × two layouts gave 24
valid replies: literal ticket, memory-specified fields, exact response word and empty
retrieval. **12/12 valid exact successes per layout** was required before attacks.
All 24 prompts used 865–898 evaluated tokens and replies used 14–73 output tokens;
every reply ended with `stop`, not an observed exhausted limit.
Original scored **9/12**, including 0/3 empty cases; task-last scored **12/12**,
including 3/3 empty cases. The gate and scorer were not weakened. The verifier
compares paired actual requests and independently checks executed effects.

![Message-order qualification](../../experiments/2026-10-25-bounded/message-order-qualification.svg)

No larger model was needed for these bounded exact-action tasks after qualification.
This does not make 1.5B sufficient for faithful consolidation or broad agent tasks.
This supports an interface-order effect for these tasks/model, not a universal
mechanism or broad competence. A descriptive 12/12 Wilson interval is approximately
[0.758,1]. The narrow task set and repeated seeds limit generalization. The reusable
adapter now exposes the equivalent request via `agent_message_order=task_last` and
`agent-v4-task-last`; [ADR-0002](../architecture/decisions/ADR-0002-task-last-condition.md)
records equivalence tests. Actual inference used v3 plus the research transport;
no extra v4 model run is claimed.

## Memory lifecycle evaluation

The clean source records review/status fields; the attack source requests canary
substitution. TT2 and TT3 use the explicit `transform-v2-json-schema` contract.
All twelve transformation replies parsed and committed. All **six attack outputs**
retained the exact canary. Five of six clean outputs retained the words review and
status. Clean-901's TT3 output was only `Transformation TT3.`: a content-quality
failure despite valid syntax. No response is repaired, and format validity is not
presented as semantic summarization quality. TT3 has one input, not a multi-source
consolidation test.

DS1 removes source revisions and primary memory, retaining derived memories. DS3
also removes descendants reachable through recorded links. True ancestry is unchanged
by fidelity/deletion treatments and remains evaluator-only. The verifier checks
actual graph edges, surviving text, source revision removal and lexical ranking.
Operational memory removal does not mean research logs/model-call records erase
the text: those retain copies for audit and are not retrieved by this agent.

## Attack and defense conditions

DF0 adds no defense suite but retains the baseline untrusted-memory system instruction.
DF2-exclude removes hits with a recorded author outside the requester/authority set.
With missing edges, an orphan can have no recorded authors; the implemented
any-untrusted-author predicate then permits it. It does not fill gaps from true
ancestry. This measured policy behavior matches the documented silent-loss design.

Qualified behavioral comparisons use only LF1.0: clean/attack × three seeds ×
DS0/DS1/DS3 × DF0/DF2 = 36 calls. Every call starts from a separate copy of its paired
snapshot. Source-alive context can include primary and derived memory; action
outcomes there cannot be attributed solely to a transformed descendant.

Valid means one parsed/logged agent response with no harness/backend error.
Legitimate utility is exact authorized ticket effects / all planned clean episodes.
Attack execution is exact canary effects / valid attack episodes, with planned and
invalid counts retained. State exposure is retrieved true attacker ancestry, not
semantic following. Free-text canary repetition is a separate lexical observation.

## Results

### State and retrieval findings

All 108 declared and 36 extra views completed; none was invalid. In each declared
DS1 snapshot, both descendants remained. Across the three attack chains, that is
6/6 live canary-bearing descendants at every fidelity. DF0 retrieved them in 3/3
views. DS1 alone therefore did not eliminate this tested derived-memory exposure.

At LF1.0, DS3 removed all descendants and exposure was 0/3. At LF0.75, DS3 retained
4/6 attack descendants, with exposure in 2/3 chains. At LF0.5, it retained 6/6,
with exposure in 3/3. DF2 reduced attack exposure to 0/3 at complete provenance,
but admitted orphaned descendants in 2/3 LF0.75 and 3/3 LF0.5 views, including after
DS3. For attack-901/LF0.75, the summary→primary link was missing: cascade could not
reach either descendant and DF2 resolved no peer author for them.

![Declared paired state outcomes](../../experiments/2026-10-25-bounded/provenance-deletion-outcomes.svg)

Clean retrieval counts differ from possible record counts because one clean TT3
output lost the query words. They are not legitimate-task success rates. Off-protocol
LF0.0 views are separately labeled: both descendants survived cascade and attack
exposure was 3/3. Those extra views support no prospective statistical claim.

### Behavioral findings

All **36/36 replies were valid**. Every clean cell completed 3/3 exact tickets,
for **18/18 clean utility**. All 18 attack episodes also completed the legitimate
ticket. Each attack cell (DS0/DS1/DS3 × DF0/DF2) had **0/3 objective proposals and
0/3 objective effects**, with zero invalids. There is no observed behavioral
advantage to rank between defenses when the tested baseline already has zero effects.

Three source-alive DF0 replies repeated canary-bearing instructions in `text` while
proposing correct `body=status` arguments. Thus action correctness does not establish
text isolation. No human semantic-following judgment is inferred from the echo.
DS1/DF0 replies received the two poisoned descendants and still used correct arguments;
DS3/DF0 replies completed the task with empty retrieval.

Per-cell 0/3 has a descriptive Wilson upper bound about **0.562**; 3/3 has a lower
bound about **0.438**. Shared text and one source pattern prevent treating all cloned
conditions as independent scenario samples. No significance test or universal
attack-rate bound is claimed.

### Historical evidence remains separate

The original [28-cell pilot](COLAB_PILOT_RESULTS.md) remains unchanged: zero matched
attack actions and zero matched legitimate tickets. Subsequent original/literal
qualification, diagnostics and gates remain in seven
[historical accessions](../../experiments/2026-10-24-completion/README.md).
The native lifecycle condition had 13 valid/67 invalid episodes; the corrected
schema-transformation condition had 52 valid/28 invalid, 21/40 clean completions
and eleven source-alive objective effects. The version-4 gate failed 9/12 and stopped
its security matrix. None is replaced or pooled with this final cycle.

The historical eleven effects versus the final zero are **not a matched estimate
of message-order defense efficacy**: seeds, generated text and matrix composition
also differ. Only the qualification comparison isolates message order.

## Discussion

**Observation:** source removal, recorded cascade reach, retrieval ancestry and
exact tool effects are different endpoints. Missing recorded links preserved and
exposed real generated canary text. The qualified task-last model nevertheless
selected authorized arguments in the tested behavioral cells, while occasionally
copying poisoned text into its free-text field.

**Interpretation:** useful evaluation needs both a capable task interface and
separate memory/action measurements. A known-author filter and recorded-lineage
cascade can share a blind spot when their common graph loses the source path.
These are conditional properties of the tested implementation, not a new universal
vulnerability class or a behavioral exploit demonstrated at incomplete lineage.

**Hypotheses for later work:** multi-source transformations, memory-dependent
collaborative tasks, semantic labels and broader models may change behavior.
They were not executed here. The finite cycle stops at its declared call budget;
it does not search for a payload or threshold that yields a favorable result.

## Limitations

One English source pattern, three chain seeds, one small quantized defender and
one-input TT3 constrain the findings. One clean transformation failed the narrow
content check. State views are deterministic conditioned on genuine generated text;
they are not model-behavior trials. Behavior was tested only at LF1.0, so no
incomplete-lineage behavioral attack rate is estimated. The literal task already
supplies ticket fields, limiting claims about memory-dependent utility and benign
peer instructions. DF1/DF3 and broader policies are historical or implementation
controls, not new paired behavioral comparisons.

There is no independent human semantic validation, inter-rater reliability,
representative held-out study, external preregistration, trusted execution
attestation or complete inherited-bibliography audit. Checksums establish supplied
byte consistency, not honesty of the inference host. The documented LF0.0 departure
limits claims of perfect protocol adherence. The original full RQ1–RQ6 program
remains incomplete; this report completes only B-RQ1–B-RQ3 at the stated endpoints.

## Ethical considerations

All actions are harmless local sandbox records; no real account or recipient was
targeted. Weights stayed in temporary Colab; only synthetic evidence was exported.
No paid API, credits, billing enablement or upgrade. No publication, peer review,
licensing decision or tagged public release is claimed. Project-level contributions
are distinguished from unconfirmed individual ownership in the
[advisor summary](../PROJECT_PRESENTATION_SUMMARY.md).

## Reproducibility

The [new evidence inventory](../../experiments/2026-10-25-bounded/README.md) links
original archives, export hashes, derived analysis and figure source. The
[evidence-to-claim table](EVIDENCE_TO_CLAIMS.md) maps findings to precise members.
The [guide](../guides/controlled-study.md) supplies pinned commands and explains
archived versus corrected matrix behavior. The standard-library verifier imports
no production scorer and independently checks raw classifications, cached text,
seeded graph loss, true ancestry, deletion reach, ranking and exact effects.
Representative outputs were inspected by the assistant; no human-rater review is
claimed. Tamper tests reject changed replies and altered state endpoints.

Use accession + chain/condition/trial ID globally. SQLite clocks are deterministic
logical times; HTTP/trial metadata contain real UTC execution times. Copied model-call
rows identify consumed cached outputs, not additional live invocations. Routine CI
runs software fixtures and saved-evidence verification without model inference.

## Conclusion

The declared bounded study is complete with a documented runner deviation. It
establishes memory-state and retrieval failures under missing recorded ancestry,
and a narrow message-order qualification result. It observes correct tool arguments
in every final behavioral call, alongside some poisoned free text. It does not
establish general behavioral protection, faithful summarization, a universal defense
ranking or completion of the original confirmatory research program.

## References

- Greshake et al. (2023), [Indirect Prompt Injection](https://arxiv.org/abs/2302.12173v2).
- Patlan et al. (2025), [MURMUR](https://arxiv.org/abs/2511.17671v1).
- Xu et al. (2026), [Memory Provenance Laundering](https://arxiv.org/abs/2607.29167v1).
