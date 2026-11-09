# Threat model — Original and Expanded Studies

7 November 2026. The central question is whether source-origin malicious instructions
remain accessible after deletion, influence behavior, and can be contained while
preserving unrelated legitimate memory utility.

The attacker controls lower-trust synthetic source text: document, email, repository
file, knowledge-base entry or simulated tool response. These are local fixtures,
not real account integrations. It may insert instructions into content consumed by
memory creation; it cannot edit trusted tasks, model weights, platform source
identity, permissions, code or protected databases. Edges may be lost by a controlled
recorder-fault treatment, not by granting the adversary database access.

The defender owns source/memory services, recorded provenance, completeness flags,
retrieval and deletion. The evaluator alone owns true ancestry and attack labels.
The new containment guard reads only operational recorded nodes, source lifecycle
and existing marked-incompleteness metadata. It cannot fill missing edges from truth.
A marked missing edge is observable; silent missingness may remain undetectable
when a mixed memory retains a path to an active clean source. Incorrect-but-plausible
edges, forged completeness flags and source-identity corruption are not solved or
included as completed fault treatments.

Goals are distinct: source removal, operational derived-memory removal, retrieval
containment, benign derived-fact availability and exact authorized tool effects.
The Expanded Study uses a derived-memory fact-lookup workload; primary source text
is not its answer context. Sources remain available as permitted inputs to selective
re-derivation. This scoped utility workload makes mixed-memory loss measurable;
it is not a general model-task benchmark. Original Study behavior remains separate.

The Expanded Study has no new model inference. Attack success, unauthorized tool
misuse and LLM legitimate-task success are **not measured**, never silently set to
zero. Real inference can use existing loopback tooling only in a separately gated
and explicitly labeled run. No paid endpoint, external side effect or weight
unlearning is implemented. Deletion does not erase research logs, model-call journals
or model parameters. Isolation is application/SQL/import isolation for trusted
harness code, not an OS enclave against hostile application code.

## Terminology and finalization scope — 8 November 2026

Direct prompt injection changes the immediate user-facing instruction channel;
it is not the main study treatment. Persistent contamination stores lower-trust
content in memory; propagation copies or derives it into another artifact.
Retrieval-time injection concerns the moment such content enters model context.
Tool-output injection is a possible ingestion surface represented by a synthetic
fixture, not a live tool compromise. Source-deletion persistence is survival after
an explicit operational lifecycle action. Direct tool misuse requires a separate
objective-matching proposal/effect, not merely a stored canary. Benign corruption
or loss can occur without any attack and requires utility measurements.

The finalization's exploratory model probe reuses verified deterministic states,
performs a real model request only if a free local model qualifies, and sends any
structured action through the existing local gateway. It does not create fresh
LLM-written summaries. The actual availability check was blocked, so no new
behavioral security or model-utility outcome is established. Trusted harness code
and filesystem inputs remain assumptions; path checks and symlink rejection do
not establish adversarial concurrency or hostile-process isolation.
