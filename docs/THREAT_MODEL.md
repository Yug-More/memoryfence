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
