# MemoryFence — project presentation summary

Prepared for an admissions-advisor review, 25 October 2026. Project-level facts
are separated from individual contribution claims. This is research software and
bounded empirical evidence, not a published or peer-reviewed security guarantee.

## A. Research motivation

An assistant can store a colleague's note, summarize it, then retrieve that summary
long after the original note disappears. If the note contains an instruction, its
surviving text may be mistaken for a fresh request. MemoryFence makes the difference
between readable information, recorded ancestry and authority measurable in a
synthetic shared workspace.

## B. Technical contributions

The repository implements a typed Python/Pydantic system with SQLite storage,
workspace ACLs, source revisions, persistent primary/derived memories, model-backed
summarization and consolidation, lexical retrieval, five deletion policies and
retrieval/prompt/action defense controls. Recorded provenance drives the system;
evaluator-only true provenance measures what the system missed. An authorization
gateway mediates harmless local ticket/note effects. Versioned prompts, bounded
runners, raw HTTP journals and standard-library verifiers make execution inspectable.

These describe the project, not proof that one person independently implemented
every component. The owner should confirm their direct design, implementation,
analysis and review responsibilities before using personal-action wording.

## C. Experimental methodology

The project separates deterministic software fixtures from genuine Qwen2.5 0.5B
and 1.5B inference. It predeclares exact benign-task gates before attack evaluation,
keeps failed conditions, and scores exact sandbox effects rather than prose claims.
The final bounded protocol tests message ordering without changing the task or
schema, and pairs provenance/deletion/retrieval conditions on common generated text.
Raw responses and database state are independently recalculated without importing
the production scorer. Automated assistant inspection is not human judge validation.

## D. Verified findings

The final bounded study supports these specific findings:

- A fixed paired comparison scored original order 9/12 versus task-last 12/12,
  including 0/3 versus 3/3 empty-context tasks, without changing task, schema or model.
- Six real TT2→TT3 chains supplied common text across provenance/deletion/retrieval
  conditions. DS1 retained descendants; DS3 removed all with complete provenance,
  but left 4/6 attack descendants at LF0.75 and 6/6 at LF0.5. DF2 admitted the orphans.
- All 36 final agent replies were valid and completed exact legitimate tickets.
  No objective-matching proposal or effect occurred in 18 attack episodes, while
  three source-alive free-text fields repeated the canary. This is a narrow negative
  action result, not a universal security claim.
- One clean TT3 output echoed only its operation label. The project preserves that
  quality failure, previous invalid conditions and the original failed pilot.

The [report](research/COMPLETION_REPORT.md),
[evidence map](research/EVIDENCE_TO_CLAIMS.md) and
[new inventory](../experiments/2026-10-25-bounded/README.md) provide exact conditions,
raw records and verification. The [historical inventory](../experiments/2026-10-24-completion/README.md)
remains separate; its eleven source-alive effects are not a matched comparison
against the final zero.

## E. Limitations

Small quantized models, synthetic English content and a narrow source pattern limit
generalization. Exact string retention is not a semantic annotation of instruction
survival. Software tests do not establish stochastic model performance. There is
no independent human reliability study, broad held-out evaluation, trusted execution
attestation or completed original confirmatory program. An enum-iteration defect
produced 36 extra LF0.0 state views; these are preserved and labeled off-protocol,
with the 108 declared views analyzed separately and a regression preventing recurrence. No scholarly publication,
novel attack class, state-of-the-art defense or universal protection is claimed.

## F. Resume-ready descriptions

**Concise project description:** MemoryFence is a Python research harness for
measuring how generated agent memories retain untrusted content, and how recorded
provenance, retrieval filtering and deletion affect later exposure and sandbox actions.

**Potential resume bullets — use personal-action wording only after confirming the
owner's individual contribution:**

- Developed and evaluated a typed persistent-memory harness with separate recorded
  and true provenance, ACL-controlled retrieval, deletion propagation and an
  authorization gateway for simulated tool actions.
- Designed bounded model evaluations with prospective benign-task gates, preserved
  unsuccessful conditions, and independently verified raw model replies against
  SQLite memory state and exact sandbox effects.

**Project summary (104 words):**

MemoryFence studies how untrusted content persists in AI-agent memory. Its Python
harness separates recorded provenance from evaluator-only true ancestry, models
source revisions and derived memories, and mediates simulated tool actions through
an authorization gateway. A bounded study paired deletion and retrieval policies
on six genuinely generated memory chains. Recorded-lineage cascades removed all
descendants with complete provenance but left retrievable attack text when edges
were missing. A fixed qualification test exposed a message-order failure; task-last
passed twelve benign tasks. All 36 subsequent agent calls completed legitimate
tickets; none of eighteen attack episodes produced the target action. Raw records
and independent verifiers support explicitly limited findings.

This project summary attributes capabilities to the repository. Personal ownership,
collaboration and tool assistance should be described accurately in an application.

## G. SOP-relevant insights

These are technical discussion prompts, not fabricated personal reflections:

- Why separating true ancestry from recorded provenance avoids giving a defense an
  oracle, and makes missing-edge behavior measurable.
- How a failed benign baseline changes the interpretation of zero attack effects;
  why exact task competence must precede defense comparisons.
- Why shared generated text, complete raw records and independent scoring matter
  when a model interface changes during an empirical study.

The owner can connect these decisions to their actual work and interests in reliable
AI systems after confirming which experiences they personally had.
