# Research integrity audit

24 October 2026 · **Interim closure with explicit external blockers**

The requested empirical definition of done is **not satisfied**. This document is
the audit of the current deliverable, not certification of a completed study.

## Scope and evidence inventory

Baseline `36cd67f214926e03081397fbd1e5b6a3e1522ed4` was compared with the code,
documentation, notebook, GitHub PRs and CI. Recovery changes are PR #9; evidence and
pilot-measurement repairs are PR #10. The documentation branch adds the preliminary
report, independent arithmetic verifier and editable SVG identity assets.

- **Software correctness:** baseline verification logs report 171 passing tests,
  92.17% combined statement/branch coverage. Repair verification logs report 180
  passing tests, 91.65% combined coverage. These are not branch-only percentages.
- **Deterministic simulation:** demo, catalog validation, smoke/replay and a
  condition-summary arithmetic check were executed. They use explicit fixtures.
- **Genuine model execution:** **0 recovered or newly completed trials**. No model
  responses are presented as findings. Mock HTTP tests are synthetic fixtures.
- **Replay of genuine model output:** **0**. The independent arithmetic smoke
  check uses deterministic simulation only.
- **Planned pilot:** 24 cells, 3 templates, 4 defenses, 2 repeats, candidate
  qwen2.5:0.5b. These are planned cells, not observations or an executed study.
- **Human reliability evidence:** none; no agreement coefficient is claimed.
- **Research figures:** none with empirical data. SVGs depict identity and actual
  architecture, not measured attack performance.

Final documentation QA passed **183 tests**, with the same **91.65%** combined
coverage; extra cases check the added documents. The arithmetic verifier also
rejected a deliberately altered numerator.

Source logs: [final QA](verification/2026-10-24/handoff-tests.txt), [baseline](verification/2026-10-24/baseline-tests-unrestricted.txt),
[repair suite](verification/2026-10-24/evidence-tests.txt), and
[independent deterministic check](verification/2026-10-24/independent-smoke.json).

## Authenticity screening and corrections

Tracked files contain synthetic catalog text, scripted responses and test-only
HTTP payloads. Those are legitimate fixtures, not evidence of genuine inference.
No original genuine model artifact was identified. No empirical success percentage
is asserted in the new README or report. Historical citations' numerical findings
remain attributed to their authors and are not MemoryFence replications.

Corrected issues include wrong endpoint assumptions for model digest, missing
judge canaries, implied confirmatory labels, tool-name-only objective checking,
backend-mislabeled reports, pooled control denominators, marginal conditional
counts, rewritten resume manifests and deletion of interrupted evidence. Original
fixture source/objective mismatches are retained and explicitly disqualified for
source-compliance interpretation; new matched templates support future pilots.

The initial sandbox test failure was not hidden: it remains in a separately
labeled baseline log. Rerunning with localhost socket access produced all 171
passes. Intermediate development failures were fixed; only the explicitly labeled
baseline failure and final passing verification are retained as project logs.
Logs omit the checkout's personal absolute path and normalize trailing whitespace;
commands, outcomes and test diagnostics remain legible.

## Independent recalculation

The stdlib-only `scripts/recalculate.py` imports no production evaluation module.
It reads planned cells and per-cell benchmark results, reconstructs primary S1–S4
counts by condition, separates unresolved S2 judgments, and compares numerators,
denominators and Wilson intervals with condition-summary.json. A fresh scripted
smoke directory passed this comparison: one clean control, zero attacker stages
in that one episode. This is a fixture arithmetic check, **not an empirical 0% ASR**.

The script does not independently re-label semantic following, reconstruct all
sandbox effects, verify every conditional/utility rate, attest model identity, or
prove raw-output authenticity. Genuine primary results cannot be independently
recalculated because no genuine trial records exist. Its limitations are explicit
rather than replaced with favorable estimates.

## Provenance and reproducibility

New experiments capture config and matrix, code revision, lock hash, platform,
actual creation time, model tag/digest, raw HTTP exchanges, logical events, results
and per-cell checksums. Agent request seeds and generation settings appear in raw
requests. Malformed output is retained before parsing. Checkpoint replacement is
atomic; interrupted directories are archived. Resume requires the saved revision.
Original manifests are retained. Deliberate reruns require separate directories.

Audit checks internal consistency and completed model chat evidence, not a trusted
execution attestation. A caller can fabricate a journal and matching checksum;
checksums are not independent proof. Older outputs without new evidence fields
need explicit review. No missing historical raw output has been fabricated.

Locked dependencies installed successfully; local Python 3.12 checks and remote
Python 3.12/3.13 CI passed for PRs #9 and #10. The Colab notebook passes structural
checks, not a hosted execution test. The independent verifier ran on a fresh
scripted directory. SVGs were rasterized and visually inspected for labels and
clipping. A PDF report is not generated or implied.

## Dependency security audit

A pip-audit 2.10.1 lookup covered six runtime and 60 applicable external
runtime/development packages exported from uv.lock (project excluded). Runtime
packages had no reported vulnerabilities. The full development set identified
certifi 2026.7.22 under
[GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).
[PR #12](https://github.com/Yug-More/memoryfence/pull/12) updates its lock entry to
2026.10.23; all 60 applicable packages then returned no known vulnerabilities.
Before/after records are preserved with that PR. Other platforms and unknown
vulnerabilities are outside this lookup; it is not a security guarantee.

## Unverified requirements and blockers

- Ollama and model weights are absent here; observed free disk was roughly 2.4 GiB
  before additional tooling. No paid infrastructure or substitute model was used.
- Owner-operated local/Colab execution is required to obtain genuine pilot output.
  Browser verification loaded the notebook, but Connect explicitly required Google
  sign-in. No browser runtime was allocated or inference performed.
- The matched pilot does not cover transformations, deletion, lineage degradation,
  adaptive attacks or multiple models. No empirical answers to those RQs exist.
- Semantic S0 and S2 judge validity, independent human review, broader utility,
  paired cached transformations, full component seed hierarchy and original
  confirmatory statistics remain incomplete.
- The inherited bibliography received key spot checks, not a complete new audit.
- A license remains an owner decision. No public release or submission is made.

## Readiness assessment

The repaired software is ready for an **inspected development pilot on an adequate
execution host**, with construct limitations documented. It is not empirically
complete, preregistered, publication-ready or a validated security guarantee.
Final research acceptance remains open until genuine raw runs, independent
recalculation, negative-control review and evidence-matched conclusions exist.
