# Project handoff

24 October 2026 · Development pilot preparation complete; empirical work pending

## What is delivered

The [recovery report](PROJECT_STATE_RECOVERY.md) reconstructs baseline
`36cd67f214926e03081397fbd1e5b6a3e1522ed4`, merged PRs #1–#8, architecture,
research specification, artifacts and actual checks. It replaces inferred phase
completion with evidence-based readiness classifications.

[PR #9](https://github.com/Yug-More/memoryfence/pull/9) merged the recovery report
at `f451530`. [PR #10](https://github.com/Yug-More/memoryfence/pull/10) merged
experimental evidence and measurement repairs at `bab2b21`; implementation commit
`4a019c7` passed all four CI checks. The current documentation work adds the
preliminary report, integrity audit, independent verifier and project identity.
Use `git rev-parse HEAD` and the PR record for the final documentation revision;
a report cannot contain its own eventual commit hash.

## Architecture and features

Typed Python/Pydantic domain models, SQLAlchemy/SQLite, separate system/evaluator
state, ACL enforcement, recorded and true provenance, seeded edge loss,
TT1–TT4 transformations, DS0–DS4 deletion, lexical retrieval, a bounded agent loop,
gateway and sandbox, DF0–DF5 defenses, scripted benchmarking, Ollama over loopback,
and a structurally validated Colab notebook are implemented. No frontend or hosted
service was added. The [architecture overview](architecture/overview.md) and new
[lifecycle SVG](assets/memory-lifecycle.svg) describe those boundaries.

Repairs add raw HTTP journals, real UTC capture times, corrected Ollama identity,
per-cell checkpoints, preserved interrupted attempts and original manifests,
stronger audits, exact action predicates, separated populations/abstentions and
joint-event conditional rates. Confirmatory status is no longer inferred.
Three matched development templates supplement the eighteen historical fixtures.

## Experiments and report status

**Completed genuine model experiments: zero.** No genuine empirical result,
defense reduction or model generalization is claimed. Deterministic demos and
fixture tests ran. The 24-cell matched pilot is specified and previewed, not run.
The [technical report](research/PRELIMINARY_TECHNICAL_REPORT.md) is explicitly
preliminary. The [integrity audit](FINAL_RESEARCH_INTEGRITY_AUDIT.md) identifies
remaining requirements rather than certifying empirical completion.

Original RQs and draft protocol are preserved. Historical source/objective
mismatches are documented. The new pilot aligns source instructions, native
create_ticket arguments and predicates, but does not measure transformation or
deletion effects. S2 is heuristic and clean-summary quality lacks a checker.

## Reproduction and verification

```bash
uv sync --frozen
make check
make pre-commit
make diagrams
uv run memoryfence experiment smoke --directory /tmp/memoryfence-handoff-new
uv run memoryfence experiment summarize --directory /tmp/memoryfence-handoff-new
uv run memoryfence experiment verify --directory /tmp/memoryfence-handoff-new
uv run python scripts/recalculate.py /tmp/memoryfence-handoff-new
```

The baseline suite passed 171 tests at 92.17% combined coverage; repairs passed
180 tests at 91.65%. Ruff lint/format, strict mypy, six import contracts,
package build metadata and citation validation passed. PRs #9 and #10 passed CI
on Python 3.12 and 3.13, hygiene and Mermaid rendering. The independent verifier
matched primary stage arithmetic and Wilson intervals on a fresh scripted smoke
run; it does not attest authenticity or reconstruct every semantic label.
Final QA passed **183 tests** at **91.65%** combined coverage (the added cases are
documentation parametrizations). Verification logs are in
[the final QA record](verification/2026-10-24/handoff-tests.txt).

The README commands use fresh directories and keep simulation distinct from
inference. Editable SVGs were rendered and visually inspected. No empirical chart,
fake dashboard, PDF report or public release was generated.

## Execution still required

Use [execution readiness](research/EXECUTION_READINESS.md) and the
[Colab guide](guides/google-colab-pilot.md). Local Ollama/weights are absent and
storage headroom was about 2.4 GiB before tooling caches (about 1.9 GiB at final QA). On an adequate host,
freeze a full merged revision, install the candidate, record runtime/hardware,
run doctor/list/smoke, inspect the compatibility pilot, then execute all matched
pilot cells in a fresh directory. The notebook automatically runs only the older
four-cell compatibility configuration; invoke the matched pilot separately.

Preserve the entire output directory or exported archive: databases, raw journals,
invalid cells, manifest, config, matrix, result records and summaries. Independently
recalculate, manually inspect negative controls and abstentions, and publish only
conclusions supported by that evidence. Failed inference is not a defense success.

Do not run the confirmatory evaluation split until sample size, statistical
procedures, held-out design, paired transformations, judge reliability and
preregistration are complete. A complete literature refresh and the owner's
license choice also remain open. Public release/publication needs owner approval.

## Maintenance and ownership

New local commits use repository-local `Yug-More <yugmore20@gmail.com>` for author
and committer, with no assistant co-author. GitHub merge commits retain its
platform-generated committer record. No collaborators, apps or bots were added.
No history was rewritten. Changes use focused PRs and wait for all CI checks.
No dependencies or model weights were committed. Temporary run/build artifacts
stay outside tracked source; historical research records remain intact.

The project is **development-pilot ready**, not empirically complete. The next
handoff input is a genuine complete pilot archive from an adequate execution host.
