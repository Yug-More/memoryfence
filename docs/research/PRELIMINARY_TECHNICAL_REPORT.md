# MemoryFence: preliminary technical report

24 October 2026 · Development methodology and engineering recovery

**Research status:** no genuine model trials available. This document reports
verified software behavior and methodological findings, not empirical evidence
that memory poisoning works or that a defense is effective.

## Abstract

MemoryFence implements a synthetic collaborative workspace for investigating
persistent instruction poisoning. It separates recorded from true provenance,
varies deletion and defense policies, and distinguishes retrieval, following,
proposal and sandbox execution. Recovery of the repository established that eight
merged implementation PRs had not produced a completed model study. Verification
reproduced 171 passing baseline tests. Repairs to identity resolution, execution
evidence, interruption handling, scoring and denominators then passed 180 tests.
A matched 24-cell development pilot is specified but unexecuted. The contribution
at this stage is inspectable experimental infrastructure and an explicit account
of its validity gaps. No hypothesis, attack rate, defense reduction, or generalized
security result follows from the software tests.

## Motivation and related work

Readable shared content need not carry authority to instruct another user's agent.
Persistent summaries and derived memories can carry content across interactions;
source deletion and incomplete lineage complicate remediation. The original
[problem statement](problem-statement.md) and [threat model](threat-model.md) retain
the project's six research questions and bounded attacker capabilities.

The abstract of [MURMUR](https://arxiv.org/abs/2511.17671) describes cross-user
poisoning of persistent shared state in collaborative agents. The abstract of
[Memory Provenance Laundering](https://arxiv.org/abs/2607.29167) describes
consolidation that preserves action triggers while obscuring source authority.
Their metadata and abstracts were checked during recovery. They motivate this
setting; MemoryFence has not reproduced their results. The broader inherited
[literature review](literature-review.md) records its own historical verification
and review-depth claims. A complete new bibliographic/full-text audit has not
occurred. No priority or novelty claim is made here.

## System and trust boundaries

Python domain models and SQLAlchemy persist synthetic sources, immutable revisions,
primary and derived memories, principals, ACLs, tools and events. System state and
true provenance occupy distinct SQLite databases. Six import contracts keep the
system under test from evaluator labels and prevent agents calling sandbox tools
directly. These checks constrain module dependencies; they are not protection
against a malicious Python process with filesystem access.

Sources become primary memories; TT1–TT4 derive summaries, consolidations and
reflections. Both parents and children accumulate. Lexical overlap ranks readable
memories; it is not embedding retrieval. DS0–DS4 vary retention, source/primary
removal, revocation, cascade deletion and re-derivation using recorded ancestry.
Silent missing edges can hide descendants from these operations by construction.
A deterministic fixture exercising that path is a mechanism demonstration, not a
measurement of real-world prevalence or model behavior.

DF0 enforces platform ACLs; DF1 adds delimiters; DF2 labels/excludes by recorded
authorship; DF3 checks tool arguments against task tokens; DF4 combines retrieval
and action controls; DF5 gates by lineage and risk. These are bounded mechanisms,
not faithful reproductions of published defenses. All effects remain in a local
sandbox. The [lifecycle graphic](../assets/memory-lifecycle.svg) depicts this
implementation, with no hosted service implied.

## Experimental design and operational outcomes

Four categories remain distinct: deterministic simulation, genuine model
execution, analysis of saved genuine outputs, and synthetic unit-test fixtures.
The original four-cell Ollama configuration is a compatibility pilot. Historical
fixtures have source/objective mismatches and cannot support source-compliance
claims from real-model action labels.

The added matched pilot has three development templates: a note that requests a
synthetic ticket with body `relay@vendor.invalid`, a clean twin, and a self-authored
utility task requesting a ticket with body `status`. Source, native tool schema
and exact objective predicate now agree. Crossing DF0/DF1/DF2-exclude/DF3 with two
agent seeds gives 24 planned cells. DS0, LF1.0, no transformations, temperature 0,
2048 context tokens and 256 output tokens remain fixed. It cannot answer RQ1
transformation survival or RQ2 deletion. Two repeats are not independent scenario
samples. See [execution readiness](EXECUTION_READINESS.md) for configuration,
commands, decision rules and stopping requirements.

S1 counts retrieved true attacker ancestry, not semantic instruction survival.
S2 uses an unaudited lexical commitment/refusal rubric and reports abstentions.
S3/S4 require exact objective tool/argument matches and distinguish proposal from
sandbox execution. The utility checker likewise requires exact requested ticket
arguments; clean summary answer quality has no automatic checker. Exact matching
can miss semantic equivalents. Every invalid call remains outside completed-trial
denominators; it is not counted as a successful defense.

Per-condition reports keep scenario, defense, retrieval variant, deletion and
fidelity separate. Clean, negative and utility controls are not pooled into attack
rates. Joint-event counts define conditional rates. Wilson intervals describe
counts in the tested cells; they do not address template clustering or broad
external validity. The draft confirmatory analysis still needs preregistration,
adequate held-out templates, paired transformation caching, sample-size decisions,
human judge agreement and missing statistical procedures.

## Evidence capture and independent checking

The runner now reads Ollama digest/size from the documented model list, captures
full requests and responses before parsing, records actual UTC journal times,
checkpoints each cell, preserves original manifests and archives interrupted
attempts. Malformed responses remain inspectable. Simulator January timestamps
are logical time, not wall-clock inference evidence. Configuration, code revision,
lock hash and model identity are recorded where available. Resume requires the
original code revision, not just an identical configuration.

Audit compares matrix, records, result checksums, backend and model identities,
and requires a recorded successful chat exchange for completed Ollama cells.
Checksums establish consistency with a supplied value, not that a server performed
inference. The stdlib-only [recalculation script](../../scripts/recalculate.py)
checks primary stage numerators, denominators and Wilson intervals independently
of the production evaluator imports. Its verification scope is arithmetic, not
semantic labeling or server authenticity.

## Observations and results status

**Observed software verification:** the recovered baseline passed 171 tests with
92.17% combined statement/branch coverage. The evidence/pilot repairs passed 180
tests with 91.65% combined coverage. Ruff, strict mypy, all six import contracts,
build metadata and citation validation passed. Both repair PRs passed GitHub CI,
including Python 3.12/3.13 and Mermaid rendering. Logs are in
[verification](../verification/2026-10-24/evidence-tests.txt).

**Observed research evidence:** zero recovered or newly completed genuine model
trials; zero genuine-output replay analyses; zero supported empirical
attack/defense comparisons. No empirical figure is appropriate. Planned cell
counts are not trial counts. Local Ollama is absent, no installed candidate model
was identified, and observed disk headroom was about 2.4 GiB before tooling caches.
The Colab workflow exists but was not executed in a hosted session here.

**Methodological finding:** the previous implementation could overwrite original
manifest metadata on resume, discard partial cells, label every summary scripted,
use pooled control denominators, and infer confirmatory status from a provenance
flag. These defects were identified by code inspection and regression checks.
The fixes improve evidence quality; they do not turn prior fixtures into model
experiments or retrospectively validate prior research claims.

## Limitations, ethics and next evidence

The workspace and consequences are synthetic; model coverage is currently zero.
Scenarios are English, few and hand-authored. Lexical retrieval, prompt sensitivity,
exact predicates, unaudited S2 judgments, limited utility checking and simplified
defenses restrict construct validity. Full paired transformations and seed hierarchy,
semantic survival, human ratings and confirmatory statistical procedures remain
incomplete. Model calls are not independently attested, and complete journal
semantics are not validated by the current audit.

All addresses use `.invalid`; no real exfiltration, credentials or external action
is needed. Raw evidence must remain synthetic and free of secrets. No publication,
public release or license decision is made by this work.

Next, execute the compatibility pilot and inspect every raw response. If valid,
execute all matched development cells and independently check each condition,
negative control, failure and abstention. Outcomes may reject the expected attack
or reveal defense failures. Report either honestly. Only then decide whether a
larger, preregistered transformation/deletion study is justified. Until genuine
runs exist, this remains a preliminary technical report.
