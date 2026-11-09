# Graduate application summary — MemoryFence

> Current metrics are frozen in [FINAL_PROJECT_METRICS.md](FINAL_PROJECT_METRICS.md).
> This dated8 November snapshot is retained; actual local inference completed on
> 9 November in the separate [model follow-up](MODEL_FOLLOWUP_RESULTS.md).

8 November 2026. These descriptions report project evidence, not publication or
sole authorship. Counts below use whitespace-separated words. The prose can support
research-oriented MS CS applications, but program fit and personal responsibility
must come from the applicant's actual interests and experience.

## A. Project description — 75 words

MemoryFence investigates whether malicious instructions survive source deletion in persistent agent memory. Its Python research framework separates evaluator ground truth from recorded provenance, compares deletion and reconstruction policies, and preserves reproducible evidence. A bounded model study and a separate deterministic benchmark reveal different questions: retained content does not necessarily cause unauthorized actions, and conservative containment can destroy useful information. The project emphasizes explicit threat models, controlled comparisons, independent verification, and transparent reporting of unfavorable findings.

## B. Technical description — 150 words

MemoryFence is a typed Python research framework for studying persistent instruction contamination after source deletion. It uses Pydantic, SQLAlchemy, and separate SQLite stores for operational memory and evaluator ground truth. Recorded dependency graphs drive deletion, retrieval controls, and selective reconstruction; defenses cannot consult true ancestry. The preserved bounded study includes 72 model responses, with 36 final agent responses spanning 18 attack episodes. A separate deterministic benchmark compares seven strategies across 80 configurations from 16 structural families, including four held out from development. Complete lineage permits reconstruction that preserves unrelated facts, while marked missingness can cause excessive quarantine and silent gaps can leave poisoned context accessible. The framework records raw state, exact outcome predicates, metric denominators, and reproducibility metadata. Independent verification recomputes graph reach, retrieval, and results. Finalization adds stricter evidence validation and a bounded local model follow-up, whose actual execution remains blocked by unavailable inference resources on the current machine.

## C. Research description — 250 words

MemoryFence began with a reliability question: when an agent learns from an untrusted source, does deleting that source also remove its influence from persistent memory? The project treats deletion, retrievability, behavioral influence, and unauthorized tool effects as distinct outcomes rather than assuming that one implies another. Its implementation separates true dependency graphs used by evaluation from recorded provenance available to defenses, enabling controlled investigation of incomplete lineage without giving the system an evaluator oracle. The preserved bounded model study contains three poisoned memory chains and 18 attack episodes, while a separate deterministic expansion compares seven strategies across 16 structural families. In four held-out complete-lineage attack cases, reconstruction retains eight of eight unrelated facts, compared with two of eight under cascade deletion. However, marked-gap containment loses all eight benign facts, and silent gaps still expose poisoned context in three of four cases. These negative findings make provenance uncertainty and utility preservation central research questions. The engineering work includes typed domain models, workspace authorization, sandboxed actions, durable evidence, exact metric definitions, and independent verification from raw SQLite artifacts. A final review also challenges the evaluation pipeline itself, rejecting malformed comparison grids and unsafe archive paths. New model-backed follow-up is capability-gated and bounded, but remains unexecuted because an appropriate free runtime is unavailable. The resulting contribution is a reproducible experimental framework and bounded investigation, not a universal defense or published paper. Its strongest lesson is that trustworthy intelligent systems require careful measurement of both security failures and the legitimate information sacrificed by mitigation.

## D. Three résumé candidates

Use these verbs only for work you personally performed and can defend. Git names
and this repository alone do not verify individual responsibility.

- Investigated post-deletion agent-memory contamination using separate true and recorded provenance graphs, preserving a bounded 18-episode model study and independently verifiable raw evidence.
- Evaluated seven memory-handling strategies in 560 paired deterministic runs over 16 graph families, documenting benign-fact loss and silent-lineage failures alongside complete-lineage reconstruction benefits.
- Strengthened a typed Python/SQLAlchemy research pipeline with adversarial metric-grid validation, safe archive handling, sandbox authorization, and capability-gated local model evaluation.

## E. Original question

Does deleting a lower-trust source remove its instructions from derived agent
memory, and can a defender contain surviving influence without discarding unrelated
legitimate information? Persistence, retrieval, model behavior and actual tool
effects are separate outcomes.

## F. Personal contribution — confirmation required

Project-level contribution: an inspectable research framework, controlled evidence,
provenance-sensitive deletion/reconstruction experiments and a transparent failure
analysis. Before using first person, confirm which research questions, design
choices, implementation, experiments and interpretations you personally led;
identify collaborators, supervision and tool assistance accurately. Do not claim
sole authorship or independent supervision status from Git metadata.

A safe editable template is: “My role focused on [confirmed responsibility]. I
made [specific confirmed decision] because [technical reason], evaluated it using
[actual evidence], and learned [supported limitation].” Replace every bracket with
an experience you can personally explain before submitting.

## G. Verified scale and evidence

- Original bounded cycle:72 genuine saved model responses;36 final agent replies,
  including18 attack episodes. Three attack chains ×two descendants. Complete
  cascade removes6/6; nominal LF0.75/LF0.5 retains4/6 and6/6. The final exact attacker
  objective has0/18 effects at LF1.0 only; textual echoes remain.
- Expanded deterministic design:80 configurations,16 structural families,seven
  strategies,560 paired runs. Four held-out complete cases:re-derivation8/8 benign
  facts versus cascade2/8; marked containment loses8/8; silent exposure3/4.
- Finalization reproduces all560 semantic records and clean historical238-test and
  merged266-test suites. Repetition does not increase independent scientific n.
- New real-model availability check:blocked,zero chat requests; no new model ASR.
  The executable follow-up harness and transport-fixture tests are software evidence.

Exact sources: [claims](RESEARCH_CLAIMS.md), [results](RESULTS.md),
[final validation](FINAL_RESEARCH_VALIDATION.md),
[raw expanded accession](../experiments/2026-11-07-expanded/README.md).

## H. Limitations

One historical small quantized model; three attack-chain clusters; fixed synthetic
payload and tools; no real-world deployment; no human semantic validation. Expanded
transforms union facts rather than paraphrasing. The source-type fixtures are not
connectors or independent domain evidence. Silent/incorrect provenance cannot be
assumed detectable. New model-backed generalization, vector-memory comparisons and
concurrent request guarantees remain unestablished. No peer-reviewed publication.

## I. Relevant skills demonstrated

Applied AI evaluation; agent trust boundaries; graph provenance; typed Python;
Pydantic validation; SQLAlchemy/SQLite transactions; role/delegation authorization;
local model contracts; controlled benchmarking; exact outcome scoring; paired
cluster-aware reasoning; reproducibility; adversarial testing; scientific writing.
Confirm personal proficiency separately from the technologies present in the repo.

## J. Faculty conversation explanation

“The interesting result is not that a filter blocks a payload. It is that missing
lineage can make a poisoned mixed memory look ordinary, while conservative rejection
can remove the useful facts too. I separate what is stored, what is retrieved and
what the agent actually does, and preserve the negative results. The next experiment
would test a capability-qualified real model under incomplete lineage without
mistaking deterministic memory behavior for model reasoning.” Use first person only
after confirming your role in that reasoning and work.

## K–L. Skeptical faculty questions and evidence-based answers

1. **What is new?** The defensible contribution is the inspectable two-graph
   measurement framework, paired deletion/reconstruction study and explicit
   observable-versus-silent missingness failures. Memory poisoning/provenance gating
   are prior ideas; no first-discovery or state-of-the-art claim is justified.
2. **Why two graphs?** Operational decisions use only recorded ancestry; evaluation
   uses the full graph to detect missed descendants. Read-only system connections
   and import contracts reduce oracle leakage. This is not an OS enclave.
3. **Why does silent loss evade the guard?** A mixed memory can retain a valid clean
   root while the malicious dependency is absent. “No observed gap” does not prove
   completeness. Trusted flags cannot reveal every unrecorded historical edge.
4. **Is560 a large LLM evaluation?** No. It is80 configurations ×seven strategies,
   grouped into16 fixed structural families. There are zero new LLM responses in
   that matrix. Family variants and strategies are correlated.
5. **Why not report a confidence interval around0/18?** Those episodes share three
   source-chain clusters and a small fixed design. An independent-binomial interval
   would imply assumptions the experiment does not support. Report conditions and
   counts; larger independent stochastic samples require a prospective design.
6. **Did your defense outperform all baselines?** No. It equals existing DS4 on
   complete-lineage scored metrics. Exact-canary filtering is stronger on the known
   silent-gap payload but loses benign facts. Conservative containment also loses
   all eight held-out benign facts with marked gaps.
7. **How was model competence checked?** The original task-last interface passed a
   twelve-case gate before the final attacks. The new harness requires four exact
   empty/clean-context qualifications, but no new gate inference ran because the
   local runtime was absent. Temperature0 does not guarantee determinism.
8. **What would you do next?** Preregister a new semantic/graph benchmark, qualify a
   free installed model, preserve raw invalid replies, test incomplete-lineage
   behavior and reconstruction faithfulness, and collect independent scenario
   clusters before selecting uncertainty methods.
9. **What does deletion mean?** Operational source/memory removal or invalidation
   under a named policy; research journals remain. No model-weight unlearning or
   forensic disk erasure is implemented.
10. **Can you prove this was solely your work?** No repository audit can. Explain
    your confirmed work and assistance accurately; do not infer sole ownership from
    author metadata or a polished manuscript.

## SOP experiences — use only after personal confirmation

- **Separating evidence stages.** Retained malicious content and exact tool effects
  diverged. The design keeps raw context, proposals and sandbox effects separate.
  Lesson: a low objective rate requires capability checks and does not prove absence
  of contamination. Evidence: Original Study raw exchanges and verifier.
- **Choosing security versus utility.** Complete reconstruction retained8/8 benign
  facts, but marked-gap containment lost8/8 and silent gaps exposed3/4. The result
  motivated a conditional uncertainty policy rather than a universal security claim.
  Lesson: trustworthy AI evaluation must measure what mitigation destroys.
- **Auditing the evaluator.** A full row count accepted an invented strategy, and an
  export followed a harmless test symlink. New validation rejects these cases while
  preserving valid outputs. Lesson: reproducibility depends on adversarially testing
  measurement and evidence tooling, not just the proposed defense.
