# Roadmap

Phases are sequential. Each phase ends with a reviewed pull request whose acceptance criteria are shown by passing checks and inspectable artifacts, not by assertion. Scope may change as the literature review is refreshed; any change is recorded here and, for research design, in the protocol change log.

| Phase | Title | Status |
|---|---|---|
| 1 | Research foundation and engineering architecture | Merged |
| 2 | Core domain, access control, provenance, and storage | Merged |
| 3 | Memory simulation, scripted backend, tools, gateway, and agent loop | In review |
| 4 | Attack scenarios and replay benchmark | Planned |
| 5 | Defenses | Planned |
| 6 | Evaluation runner, metrics, and reproducibility | Planned |
| 7 | Model integration, pilots, preregistration, and confirmatory study | Planned |
| 8 | Analysis, report, and audit | Planned |
| 9 | Release audit | Planned |

## Phase 1: Research foundation and engineering architecture

- **Objective:** Define the research problem, threat model, hypotheses, and experimental protocol, and establish an architecture and tooling baseline that later phases build on.
- **Deliverables:** literature review with research-gap matrix and novelty assessment; problem statement; threat model; hypotheses; experimental protocol; limitations; architecture overview with seven diagrams; ADR-0001; development guide; this roadmap; README, CONTRIBUTING, SECURITY, CITATION.cff, pull-request template; minimal installable package; tooling (uv, Ruff, mypy, pytest with coverage, pre-commit); CI.
- **Dependencies:** none.
- **Acceptance criteria:** every research document exists and is internally consistent; the central research question appears verbatim; the five deletion policies, three provenance conditions, and four outcome stages are defined operationally; planned and implemented components are clearly separated; no empty placeholder modules.
- **Validation:** `make check`, `make pre-commit`, and `make diagrams` pass locally and in CI on Python 3.12 and 3.13; documentation tests confirm links, anchors, condition codes, and diagrams; arXiv identifiers in the literature review were checked against the arXiv API.
- **Status:** Merged.

## Phase 2: Core domain, access control, provenance, and storage

- **Objective:** Implement the deterministic, model-free core: who can see what, where content came from, and the separation between true and recorded provenance.
- **Deliverables:** `memoryfence.domain`; `access`; `workspace` (membership, sources, immutable revisions, memories, and deletion-policy state transitions); `provenance` (recorded graph and seeded degradation); `groundtruth` (true provenance, deletion ledger, separate database); `storage` (SQLAlchemy 2 over SQLite); `observability` (structured events and run manifests); `import-linter` contracts in CI.
- **Dependencies:** Phase 1.
- **Acceptance criteria:** the import contracts in [`architecture/overview.md`](architecture/overview.md#62-import-contracts) pass in CI; degradation is nested across `LF` levels and leaves true provenance byte-identical; extraction links are never degraded; ACLs are enforced on every read path; deletion policies `DS0`–`DS4` follow the protocol. Phase 2 records DS4 tasks and does not generate their text; Phase 3 executes them. No language-model dependency.
- **Validation:** tests for authorization, degradation, nesting, lineage, deletion policies, and SQLite transactions; a byte-identity test of true provenance across `LF` levels; coverage of at least 90%.
- **Status:** Merged.

## Phase 3: Memory simulation, model backend, tools, gateway, and agent loop

- **Objective:** Build the system under test end to end on a deterministic backend. Phase 2 already records deletion-policy state transitions and DS4 work items; this phase executes transformations and re-derivation.
- **Deliverables:** `llm` (`LanguageModel` protocol and scripted backend); memory ingestion and transformations `TT1`–`TT4`, with `TT0` as retrieval of an untransformed primary; lexical retrieval with ACL filtering; execution of `DS4` re-derivation tasks; sandbox tools; an authorization gateway; a victim agent loop; one offline episode, `memoryfence demo`. Defense hooks and an AgentDojo adapter remain later work. The scripted transformations are deterministic fixtures, not model reasoning.
- **Dependencies:** Phase 2.
- **Acceptance criteria:** each deletion policy reaches exactly the memories that recorded provenance connects to the deleted source, including under degraded provenance; the gateway always applies the ACL and ignores natural-language justifications; agents cannot reach tools except through the gateway; transformations record one true edge per input.
- **Validation:** tests for every deletion policy at every `LF` level; adversarial-justification tests for the gateway; a deterministic end-to-end episode test with a recorded event log; coverage of at least 90%.
- **Status:** In review.

## Phase 4: Attack scenarios and replay benchmark

- **Objective:** Author the synthetic scenarios and a replayable benchmark that exercises them without a live model.
- **Deliverables:** scenario families SF1–SF5 with benign twins, payload styles, canaries, and objective predicates; controls `C-CLEAN`, `C-RAW`, `C-NULL`, `C-PREDEL`, `C-LEGIT`, `C-SELF`, `C-UCC`; template-level development and evaluation split with the evaluation split committed by hash; outcome classifier for S0–S4; judge prompt and human-audit tooling; a replay benchmark of scripted model responses.
- **Dependencies:** Phase 3.
- **Acceptance criteria:** every objective predicate is deterministic and written before any empirical run; development tooling cannot load evaluation templates; all recipients use the `.invalid` domain; the classifier reproduces expected stage labels on replayed episodes.
- **Validation:** classifier tests on hand-labeled replayed episodes; a test that evaluation templates are unreadable from development entry points; a secret and real-address scan over all scenario content.
- **Status:** Planned.

## Phase 5: Defenses

- **Objective:** Implement the defense configurations behind the hook protocol.
- **Deliverables:** `DF1` prompt-level delimiting; `DF2` provenance-aware retrieval (label and exclude); `DF3` independent action authorization (generated and oracle policy); `DF4` combined; `DF5` lineage-gated authorization; overhead instrumentation.
- **Dependencies:** Phases 3 and 4.
- **Acceptance criteria:** defenses read recorded provenance only and pass the import contracts; the `DF3` policy step cannot see retrieved content; each defense behaves as specified on replayed episodes, including legitimate-instruction controls.
- **Validation:** unit tests per defense; replay-benchmark runs reporting stage rates and false positives on the scripted backend; overhead measured on the deterministic backend.
- **Status:** Planned.

## Phase 6: Evaluation runner, metrics, and reproducibility

- **Objective:** Run experiment blocks from configuration and compute every planned metric and statistic reproducibly.
- **Deliverables:** configuration schemas; seeded episode runner for blocks E1–E4; seed hierarchy and matching; metrics (survival, stage rates, PD-ASR, persistence ratio, utility, false positives, overhead); statistical analysis code (Wilson intervals, exact McNemar, mixed-effects models, cluster bootstrap, trend and equivalence tests, Holm–Bonferroni); run manifests.
- **Dependencies:** Phases 4 and 5.
- **Acceptance criteria:** rerunning a configuration on the scripted backend reproduces the event log byte for byte; matched episodes share seeds as specified in the protocol; statistics code is validated against known reference values.
- **Validation:** reproducibility tests; statistics tests against reference implementations or published examples; coverage of at least 90%.
- **Status:** Planned.

## Phase 7: Model integration, pilots, preregistration, and confirmatory study

- **Objective:** Connect real models, size the study, freeze the plan, and run the confirmatory experiments.
- **Deliverables:** local open-weight adapters (hosted adapters only with budget approval); development-split pilots and power analysis; judge reliability study; literature review refresh; preregistration of hypotheses, analysis code, sample sizes, and the evaluation-split hash; evaluation-split runs.
- **Dependencies:** Phase 6 and the protocol's entry criteria ([`experimental-protocol.md`](research/experimental-protocol.md#17-entry-criteria-for-empirical-runs)).
- **Acceptance criteria:** the preregistration is frozen and timestamped before any evaluation-split run; pinned model identifiers and weights; no paid API usage without owner approval.
- **Validation:** run manifests and event logs for every run; a check that evaluation runs used the preregistered commit and configuration.
- **Status:** Planned.

## Phase 8: Analysis, report, and audit

- **Objective:** Analyze and report the results honestly.
- **Deliverables:** every preregistered analysis, including nulls; exploratory analyses labeled as such; the deviations log; failed-run accounting; human audit results; a written report; an internal audit tracing reported numbers to event logs.
- **Dependencies:** Phase 7.
- **Acceptance criteria:** every reported number is regenerated from committed code and logs; claims match the evidence; limitations are updated.
- **Validation:** an end-to-end regeneration of all tables and figures from logs; independent review of the report against the preregistration.
- **Status:** Planned.

## Phase 9: Release audit

- **Objective:** Prepare a responsible public release of the harness and artifacts.
- **Deliverables:** security and responsible-use review; secret and personal-data scans; responsible disclosure of any product-specific findings; release of code, configurations, and event logs; final citation metadata; versioned release.
- **Dependencies:** Phase 8 and an owner decision on licensing.
- **Acceptance criteria:** a license chosen by the owner is in place; no secrets or real personal data in the repository or artifacts; disclosure periods have elapsed for any vendor findings.
- **Validation:** scan reports; a clean-environment reproduction of a sample of results from the release artifacts.
- **Status:** Planned.

## Optional later work

- FastAPI service for interactive exploration
- Hosted-model comparisons, subject to budget approval
- Embedding-based retrieval
- Adaptive attacks against each defense
- Replacement-style merging, where transformation inputs are overwritten

## Open decisions for the repository owner

| Decision | Recommendation | Status |
|---|---|---|
| License | Apache-2.0 for code and CC BY 4.0 for documentation | Awaiting owner; no license is granted |
| Branch protection on `main` | Require the CI checks to pass before merging | Awaiting owner |
| Private vulnerability reporting | Enable it in the repository's security settings | Awaiting owner |
| Hosted-model budget | None by default | Awaiting owner |
| ORCID and affiliation in `CITATION.cff` | Add only if the owner provides them | Awaiting owner |
