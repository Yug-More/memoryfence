# Project state recovery

Audit date: 24 October 2026. Baseline: `36cd67f214926e03081397fbd1e5b6a3e1522ed4`.
This report separates inspected implementation, executed checks, and unexecuted research.

**Snapshot scope:** the recovery findings below describe the original baseline.
Later live Colab work is recorded in [the pilot results](research/COLAB_PILOT_RESULTS.md):
28 schema-condition cells completed after PR #13 repaired runtime integration.
The recovered checkout itself contained no prior genuine results.

## Repository and history

The initial working tree was clean on `main`, equal to the local `origin/main`.
An authenticated remote HEAD query returned the same full revision. GitHub lists
PRs #1–#8 as merged, covering research foundations, core memory, simulation,
benchmarking, defenses, evaluation, Ollama, and Colab respectively. There are no
local tags and no open issues returned by the GitHub query. The latest main CI
run, `39166188044`, completed successfully on 18 October 2026. This is historical
CI evidence, not validation of subsequent changes.

The historical phase claim needs qualification: the *implementation* of phases
1–7B is merged; real pilots, preregistration, and a confirmatory study are not
established by those merges. The roadmap incorrectly leaves 7B “In review” and
calls phase 7 “Merged” without making this distinction.

## Architecture inventory

Python >=3.12, a typed src-layout package, argparse CLI, Pydantic domain models,
and SQLAlchemy/SQLite are implemented. Runtime dependencies are Pydantic and
SQLAlchemy; uv.lock pins development and runtime dependencies. There is no
application frontend, hosted service, embedding index, or external agent adapter.

- `domain`: immutable validated identifiers, principals, sources, memories,
  provenance, policies, tools, model requests and responses.
- `storage`, `workspace`, `access`: SQLite persistence, immutable revisions,
  membership and ACLs, instruction authority, deletion state transitions.
- `provenance`: recorded derivation graph and seeded nested edge degradation.
- `groundtruth`: separate evaluator database with complete lineage and labels;
  import contracts prevent system-under-test access.
- `memory`: primary ingestion, TT1–TT4 transforms, lexical retrieval, and DS4
  re-derivation. Records accumulate rather than replacing their parents.
- `agents`, `authorization`, `tools`: retrieval and model decision, gateway checks,
  and synthetic sandbox effects. Proposal and execution are separate records.
- `llm`: deterministic explicit fixtures and loopback-only Ollama HTTP. No paid
  endpoint, transformer runtime, or automatic model download is implemented.
- `benchmark`: eighteen development templates, seven control classes, persisted
  stage outcomes, event export and deterministic replay.
- `defenses`: DF0 ACL; DF1 delimiters; DF2 recorded-author labeling/exclusion;
  DF3 task-token action policy (oracle variant separate); DF4 combined;
  DF5 lineage/risk gate. These approximate mechanisms, not published systems.
- `evaluation`: validated JSON matrices, two held-out templates, <=64 cells,
  resume, summary, Wilson intervals, exact McNemar, Holm and paired differences.
- `colab`: environment gates, frozen checkout support, resource preflight,
  pilot packaging; one notebook orchestrates local Ollama inside Colab.

DS0 retains state; DS1 removes source and primary; DS2 revokes recorded-reachable
memories; DS3 hard-deletes that reach; DS4 regenerates affected content from
remaining recorded inputs. Missing recorded edges can hide descendants from
propagation. Retrieval uses shared case-folded alphanumeric token counts, ID tie
breaking, zero-score exclusion, top-k and ACL filtering. No semantic search exists.

## Research specification and evidence

The original RQ asks how attacker-origin instructions persist after transformation
or deletion, and how deletion handling, provenance completeness and defenses affect
unauthorized downstream behavior. Its six subquestions concern depth, deletion,
defenses, incomplete lineage, staged actions, and utility. These remain the research
questions; the owner's broader framing is compatible and does not replace them.

The attacker is a peer author of shared synthetic content, without authority to
forge platform metadata, change policies, or access the victim's private state.
The evaluator knows true provenance; defenses see only recorded provenance.
Every action is a local sandbox effect. No external exfiltration is needed.

S1 measures retrieval of attacker *ancestry*, not survival of the instruction's
text. S2 is a fixture marker or a narrow commitment-and-canary rubric. S3/S4
measure objective-matching proposal/execution. Semantic S0 survival is proposed
but not implemented as a validated measured endpoint. An ancestry edge alone
cannot demonstrate lexical or semantic payload persistence.

No committed original run directories, raw genuine model responses, completed
empirical report, or empirical figures were found in the tracked inventory.
The notebook has no execution evidence establishing a completed pilot. Tests with
mock HTTP are synthetic fixtures. Scripted trials are deterministic simulation.
The four-cell `ollama-pilot.json` is development-only, clean/direct × DF0/DF1,
DS0, LF1.0, one replicate, with scripted transformations. It cannot answer the
transformation or deletion research questions or establish broad defense efficacy.
No real-model evidence is recovered from this checkout.

The protocol proposes substantially more than the implementation: cached paired
transformations, representative held-out scenarios, human judge agreement,
preregistered power and stopping rules, mixed-effects models, trend tests,
cluster bootstrap, equivalence testing, and semantic survival remain absent.
H1, H2a and H4 are explicitly not computable in the hypothesis registry. Available
statistical procedures do not establish that any hypothesis has been tested.

## Executed baseline verification

Locked installation succeeded using uv and CPython 3.12.12. No dependencies were
changed. `ruff check .` and `ruff format --check .` passed (123 files); strict mypy
passed (108 source files); all six import contracts passed.

The first `pytest --cov --cov-report=term-missing` invocation produced 170 passes
and one sandbox permission failure when a redirect test bound localhost. Its
92.14% combined statement/branch coverage is not evidence of scientific validity.
With localhost socket access, all **171 tests passed** and combined coverage was
**92.17%**. The unrestricted rerun is recorded separately in
[verification logs](verification/2026-10-24/baseline-tests-unrestricted.txt).
The historical 92.17% figure must not be described as newly measured branch-only
coverage. CLI demo, catalog validation, smoke/replay and pilot preview are checked
separately; generated smoke counts are fixture outcomes.

## Component readiness

- **Complete and verified:** baseline domain/ACL/storage invariants exercised by
  the suite, import isolation, lint/format/type checks, deterministic CLI mechanics.
  Verification is bounded by the checks above, not a guarantee of correctness.
- **Implemented but not fully verified:** Colab in its actual hosted environment,
  model adapter against a real server, full documented CLI surface, diagram
  rendering, Python 3.13 locally, clean-environment package reproduction.
- **Partially implemented:** real-model execution provenance and checkpointing,
  independent evidence validation, stage denominators, legitimate utility checking,
  original protocol statistical analysis and experiment design.
- **Planned but absent:** completed empirical study, preregistration, validated
  semantic judge, independent human ratings, research results/report and figures.
- **Blocked by external resources:** actual model execution here (Ollama absent,
  no installed model identified, approximately 2.4 GiB free disk); hosted Colab
  execution needs an owner session. No paid substitute is authorized or needed.
- **Obsolete or superseded:** roadmap 7B review status; treating phase 7 merge
  as evidence of completed empirical work.

## Technical and scientific findings requiring repair

1. Ollama identity assumes `/api/show` contains `digest`; the official model list
   supplies digest and size. Existing mocks conceal this compatibility failure.
2. Reports label all experiments scripted, including configured Ollama runs.
3. `_store_plan` rewrites original revision/environment metadata on resume.
   Run records are written only after the whole loop; interrupted partial cells
   are deleted during resume. This is not immutable research evidence handling.
4. `audit` checks config hash and existence, not matrix completeness, result/record
   agreement, backend provenance, response authenticity, or cryptographic integrity.
5. Pooled stage rates include clean/legitimate controls. Conditional rates use
   marginal counts rather than intersections, which can fail or mislead when
   stages are not nested. Abstentions are collapsed into false S2 labels.
6. `confirmatory` is inferred from silent missingness alone. Neither silent
   missingness nor a successful run establishes preregistration.
7. Model calls use synthetic January timestamps; actual wall-clock execution and
   raw malformed model responses are not adequately preserved for authenticity.
8. The request seed differs across agent trials but result seed is the scenario
   seed; transformations and lineage use fixed seeds. Replicates do not implement
   the full proposed seed hierarchy or shared transformation cache.

## Sources checked during recovery

The official [Ollama model list API](https://docs.ollama.com/api/tags) supplies
model identities. The [candidate model](https://ollama.com/library/qwen2.5:0.5b)
currently lists a 398 MB Q4_K_M artifact; runtime and download overhead are additional.
The tag is a pilot candidate, not a frozen model identity or generalization target.
Bibliographic spot checks resolve
[MURMUR](https://arxiv.org/abs/2511.17671) and
[provenance laundering](https://arxiv.org/abs/2607.29167) to the expected titles and
authors. This audit has not independently repeated the older review's claim of
79 verified references or read every cited full text; that claim remains historical.

## Completion roadmap

A. Commit recovery and correct status; retain original RQs and protocol.
B. Repair the concrete adapter, artifact integrity, resume, and reporting faults;
   regression-test them before executing any pilot.
C. Freeze a small development design and run actual model inference on a machine
   with adequate storage or in the existing owner-operated Colab notebook. Inspect
   raw failures as well as valid responses. Do not run held-out confirmatory work
   before preregistration and the missing methodology are resolved.
D. Independently recalculate each condition from raw records, assess utility and
   ambiguous judgments, then write a preliminary report limited to observed data.
E. Refine repository identity and documentation using accurate diagrams; no fake
   dashboard or empirical chart.
F. Produce integrity and handoff reports with explicit unfinished requirements.

A focused pilot can support a preliminary engineering report. It cannot substitute
for the original confirmatory design. Empirical completion remains blocked until
real runs and independent analysis exist.
