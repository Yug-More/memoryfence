# ADR-0002: expose the qualified task-last layout explicitly

25 October 2026 · Accepted for an opt-in research condition

## Context

The historical adapter sends system, task, then a separate user message containing
untrusted-memory data. With no retrieval hits, the final message still contains a
warning. In the [prospective paired comparison](../../research/FINAL_BOUNDED_PROTOCOL.md),
the same 1.5B model, schema, task, tools and sampling settings scored 9/12 with the
original order and 12/12 with the two user messages swapped. Empty-context tasks
changed from 0/3 to 3/3. This is a narrow interface result, not universal competence.

## Decision

Add explicit `agent_message_order=task_last`, requiring the complete JSON contract
and prompt identity `agent-v4-task-last`. It sends system, untrusted-memory message,
then trusted task. The system instruction and memory text are unchanged. Keep the
legacy default and omit its new field from canonical stored configurations so
historical fingerprints remain stable.

Tests compare the adapter's actual HTTP body with the qualified research
transport's message permutation for both empty and nonempty retrieval. They also
check template identity and reject inconsistent configuration. Historical runs used
`agent-v3-contract-schema` plus the recorded `task-last` transport; no v4 model run
is claimed. Request equivalence, rather than a new inferred performance number,
supports exposing the setting in the reusable adapter.

## Consequences

Callers can reproduce the tested message layout without replacing transports.
Task-last does not make stored content trustworthy, repair responses, authorize
tools or change the gateway. Other tasks/models still require qualification.
The [qualification originals](../../../experiments/2026-10-25-bounded/final-qualification.zip.xz)
and independent analysis preserve the exact executed condition. No default or
historical experiment is silently upgraded.
