# ADR-0001: Modular monolith Python package for the MemoryFence research harness

- **Status:** Accepted
- **Date:** 2026-10-18
- **Deciders:** Repository owner (Yug-More)
- **Scope:** Overall structure, technology stack, and the boundaries that protect measurement validity

## Context

MemoryFence is a research harness for evaluating whether attacker-origin instructions persist in derived AI memories after transformations or source deletion, and whether they lead to unauthorized agent actions (see [`problem-statement.md`](../../research/problem-statement.md)). The architecture must support:

- **reproducible experiments:** byte-for-byte with a deterministic model backend, and statistically with real models;
- **controlled variation** of transformation type and depth, deletion policy, provenance completeness, and defense configuration;
- **valid measurement:** neither the system under test nor its defenses may see ground truth (true provenance, attack labels, the deletion ledger);
- **objective outcomes:** whether an unauthorized action executed must be decidable without an LLM judge;
- **low operational cost** for a small team on one machine, with no paid services required.

## Decision drivers

1. Measurement validity over feature breadth.
2. Determinism and traceability of every reported number.
3. Readability for independent reviewers.
4. Minimal dependencies, each justified by a concrete need.
5. Freedom to integrate external benchmarks (for example AgentDojo) later without being locked into their abstractions.

## Decision

1. **Structure: a modular monolith.** One installable Python package, `memoryfence`, in a `src/` layout, with small modules separated by explicit import contracts (see [`overview.md`](../overview.md#62-import-contracts)). No microservices, message brokers, or network boundaries between components.
2. **Language and runtime:** Python 3.12 or newer. CI tests 3.12 and 3.13.
3. **Two provenance views.** True provenance is recorded by the harness in an append-only, harness-only store. Recorded provenance, the only view the system under test and defenses can read, is derived from it by a seeded, nested degradation procedure. Lineage and deletion events reach the harness through write-only sink protocols, so system-under-test modules never import ground-truth code.
4. **Ground-truth isolation:** only `memoryfence.evaluation` and `memoryfence.attacks` may import `memoryfence.groundtruth`. `memoryfence.defenses` may not import `attacks`, `evaluation`, or `groundtruth`. `memoryfence.agents` may not import `memoryfence.tools`. These contracts will be enforced with `import-linter` from Phase 2.
5. **Authorization gateway.** Every side-effecting tool call passes through one gateway that always applies the platform ACL and then any configured action-authorization defense. The gateway decides from the structured call and requester only, never from the model's natural-language claims.
6. **Domain models:** Pydantic v2 with frozen models for domain objects and experiment configuration, so validation and serialization share one schema. *Added in Phase 2.*
7. **Persistence:** SQLite through SQLAlchemy 2, with one system-under-test database and one separate ground-truth database per run. *Added in Phase 2.*
8. **Model access:** a narrow `LanguageModel` protocol. The first implementation is a **deterministic scripted backend** used for tests, CI, and mechanism-isolation runs. Local open-weight and hosted adapters are optional and are never required by CI.
9. **Tools:** deterministic, code-defined simulations operating on sandbox state, rather than LLM-emulated tools ([Ruan2024]). This keeps the "executed" outcome objective.
10. **Defenses:** implementations of a hook protocol (`on_memory_write`, `on_retrieve`, `on_context_build`, `on_action_proposed`) selected by configuration.
11. **Retrieval:** a pluggable interface whose first implementation is a deterministic lexical ranker. Embedding-based retrieval is deferred until an experiment needs it.
12. **Tooling:** `uv` with a committed lockfile; `hatchling` as build backend; Ruff for linting and formatting; mypy in strict mode; pytest with pytest-cov (branch coverage, 90% minimum); pre-commit; `twine check` and Citation File Format validation in the build; GitHub Actions pinned by commit SHA.
13. **Dependency policy:** Phase 1 has **no runtime dependencies.** Pydantic and SQLAlchemy are added in Phase 2 together with the code that uses them. Every new dependency must be justified in its pull request.
14. **Documentation:** Markdown with Mermaid diagrams that render natively on GitHub and are render-checked in CI. Significant decisions are recorded as ADRs in `docs/architecture/decisions/`.

## Consequences

**Positive**

- One process and one pair of SQLite files per run make experiments easy to reproduce, archive, and inspect.
- Explicit module contracts make the ground-truth isolation requirement reviewable and, from Phase 2, machine-checked.
- The deterministic backend lets CI exercise the full pipeline without network access or cost.
- A small dependency footprint reduces supply-chain risk and maintenance burden.

**Negative**

- No built-in concurrency or distributed execution. Large sweeps parallelize at the process level.
- SQLite is unsuitable for a production multi-user deployment. That is a non-goal.
- Building the harness instead of extending an existing benchmark costs effort, and results are not automatically comparable to that benchmark.
- Sink protocols and separate databases add some indirection compared with a single shared store.
- Strict typing and coverage thresholds slow early prototyping somewhat.

**Follow-ups**

- Add the import-contract check to CI when the second internal module is created (Phase 2).
- Evaluate an AgentDojo adapter for comparability once the agent loop exists (Phase 3 or later).
- Record any change to these decisions in a superseding ADR.

## Alternatives considered

| Alternative | Why not chosen now |
|---|---|
| **Microservices** (separate memory, agent, and policy services) | Adds network nondeterminism, deployment overhead, and failure modes that do not serve research validity. The module boundaries allow a later split if ever needed. |
| **General agent frameworks** (for example LangChain, LangGraph, AutoGen) | Large dependency surfaces and abstractions that hide memory and prompt handling, which are exactly the variables under study. |
| **Building directly on AgentDojo or MURMUR** | Both influenced this design, but neither models LLM-mediated memory transformation, provenance, or deletion policies as first-class components. An adapter path stays open. |
| **A single provenance store with an "is degraded" flag** | Simpler, but makes it easy for a defense to read the complete graph by mistake. Separate stores and import contracts make the isolation structural. |
| **PostgreSQL** | Requires running a server. SQLite gives sufficient transactional integrity for single-process runs, and SQLAlchemy keeps migration possible. |
| **A vector database** (for example FAISS, Chroma) | Adds dependencies and nondeterminism before any experiment needs dense retrieval. |
| **LLM-emulated tools** | Would make the executed-action outcome depend on another model's judgment. |
| **Poetry or pip-tools** | Both work. `uv` provides fast, reproducible locking and Python version management in one tool, with first-party CI support. |
| **Plain dataclasses instead of Pydantic** | Lighter, but would require hand-written validation and serialization for configurations and logs. |
