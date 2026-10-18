# Roadmap

Phases are sequential. Each phase ends with a reviewed pull request whose acceptance criteria are shown by passing checks and inspectable artifacts, not by assertion. Scope may change as the literature review is refreshed; any change is recorded here and, for research design, in the protocol change log.

| Phase | Title | Status |
|---|---|---|
| 1 | Research foundation and engineering architecture | Merged |
| 2 | Core domain, access control, provenance, and storage | Merged |
| 3 | Memory simulation, scripted backend, tools, gateway, and agent loop | Merged |
| 4 | Scripted scenarios and replay benchmark | Merged |
| 5 | Defense baselines | Merged |
| 6 | Evaluation runner, metrics, and reproducibility | Merged |
| 7 | Model integration, pilots, preregistration, and confirmatory study | Merged |
| 7B | Free Colab workflow for the development pilot | In review |
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
- **Status:** Merged.

## Phase 4: Scripted scenarios and replay benchmark

- **Objective:** Author synthetic scenarios and replay them on the scripted backend without a live model.
- **Deliverables:** `memoryfence.benchmark` with eighteen versioned scenarios in families A–H and protocol families `SF1`–`SF5`; controls `C-CLEAN`, `C-RAW`, `C-NULL`, `C-PREDEL`, `C-LEGIT`, `C-SELF`, and `C-UCC`; separate S1–S4 stage records; deletion policies `DS0`–`DS4` and lineage-fidelity overrides, including marked exploratory missingness; run manifests, `benchmark-result.json`, and `events.jsonl`; CLI commands `list`, `validate`, `run`, `replay`, `inspect`, and `export`. The followed-instruction marker and source origins stay in the evaluator. A development/evaluation template split, an audited judge, and statistics remain later phases.
- **Dependencies:** Phase 3.
- **Acceptance criteria:** each scenario validates before it runs; stage labels are computed from persisted ground truth and the event log, not from the agent's copy of the scenario; replay of a saved directory reproduces the canonical outcome; recipients use the `.invalid` domain; the system under test cannot import the benchmark.
- **Validation:** `tests/test_benchmark.py` covers the catalog, stage separation, controls, deletion and fidelity sweeps, timeout failure, replay, and the CLI. Coverage stays at least 90%.
- **Status:** Merged.

## Phase 5: Defense baselines

- **Objective:** Implement the protocol's defense conditions on the scripted benchmark without giving them true provenance.
- **Deliverables:** `DF0` platform ACL only; `DF1` prompt delimiting and recorded-author labels; `DF2` provenance-aware retrieval in `label` and `exclude` variants; `DF3` task-derived action authorization, with an injected oracle allowlist reported separately; `DF4` `DF2` and `DF3` together; `DF5` lineage-gated authorization. Decisions are structured events. The benchmark accepts `--defense`.
- **Dependencies:** Phases 3 and 4.
- **Acceptance criteria:** defenses read recorded provenance only and pass the import contracts; the `DF3` policy step cannot see retrieved content; missing recorded edges are not repaired from true provenance; each condition is selectable without reusing episode state.
- **Validation:** `tests/test_defenses.py` and the existing benchmark suite. Scripted stage labels are fixture results, not empirical defense effectiveness.
- **Status:** Merged.

## Phase 6: Evaluation runner, metrics, and reproducibility

- **Objective:** Run a scripted experiment from a validated configuration and summarize the four stages without treating fixture counts as model findings.
- **Deliverables:** `memoryfence.evaluation` with a versioned JSON configuration, an inspectable matrix, exclusions, a hard `max_runs` stop, isolated run directories, resume of an incomplete cell, a manifest with the configuration hash and git revision, Wilson intervals, exact McNemar, Holm adjustment, and a paired risk-difference interval. Legitimate-task completion is counted on `C-CLEAN`, `C-LEGIT`, and `C-SELF`. The development catalog and two held-out templates are separate loaders. CLI: `validate`, `preview`, `smoke`, `run`, `status`, `resume`, `export`, `summarize`, `verify`.
- **Dependencies:** Phases 4 and 5.
- **Acceptance criteria:** an oversized matrix is previewed and not silently truncated; invalid configurations fail before execution; a completed result file is not overwritten; `verify` reproduces the canonical outcome; held-out ids are absent from `benchmark list`; defenses still cannot import evaluator-only modules.
- **Validation:** `tests/test_evaluation.py`. Wilson and McNemar use known counts. Coverage stays at least 90%. Mixed-effects models, cluster bootstrap, Cochran–Armitage, and TOST are not implemented, so `H1`, `H2a`, and `H4` are marked not computable.
- **Status:** Merged.

## Phase 7: Model integration, pilots, preregistration, and confirmatory study

- **Objective:** Call a local model through the existing agent loop without hosted inference, and keep confirmatory evaluation frozen until the plan is ready.
- **Deliverables:** a loopback-only Ollama adapter; structured decisions; rubric-v1, which can abstain; repeated trials inside the existing 64-run cap; `memoryfence model doctor`, `list`, and `smoke`; `experiment audit`, which checks a manifest without calling the model. `configs/ollama-pilot.json` names a candidate tag and uses scripted transformations. The candidate was not downloaded in this phase.
- **Dependencies:** Phase 6.
- **Acceptance criteria:** CI passes with mocked HTTP and does not require Ollama; the scripted fingerprint of the smoke configuration is unchanged; remote endpoints are rejected; a model sentence is not authorization; confirmatory evaluation is not run.
- **Validation:** `tests/test_ollama.py`. A machine without Ollama and without enough free disk for a model is reported as integration-complete and empirical-pilot-pending.
- **Status:** Merged.

## Phase 7B: Free Colab workflow for the development pilot

- **Objective:** Run the existing four-cell Ollama pilot inside a free Google Colab runtime, without downloading a model onto a machine that lacks disk space and without opening a public inference endpoint.
- **Deliverables:** `notebooks/memoryfence_colab_pilot.ipynb`; `memoryfence.colab` checks for a pinned checkout, a loopback Ollama process, one approved model tag, and a zip of the experiment directory; [`guides/google-colab-pilot.md`](guides/google-colab-pilot.md). The notebook calls the existing experiment runner. Transformations in the pilot stay scripted.
- **Dependencies:** Phase 7.
- **Acceptance criteria:** CI does not install Colab, Ollama, or a model; the scripted backend and the loopback adapter still pass; the notebook refuses a remote endpoint and a second model; held-out scenarios are not used; no live model call is claimed unless one was recorded.
- **Validation:** `tests/test_colab.py`. A development machine that cannot open a Colab session is reported as Colab integration complete, with the live pilot awaiting the user.
- **Status:** In review.

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
