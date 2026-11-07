# Verification record — 7 November 2026

This record separates new software execution, supplied-artifact recomputation and
historical genuine model inference. No new model calls or weight downloads occurred.
All paths below logs are repository-relative; `/tmp` paths are original local run
locations, not required dependencies of the accession.

## Preserved baseline and source revisions

Entry `f51a8360aca39a428ca41bfc9afe10447d175d72`; preservation `19305b9`;
prospective protocol `9d56faa`; expanded execution code/dataset `4a430fa`.
The 53-file legacy manifest includes all original accession files, old configuration
files, `uv.lock` and `pyproject.toml`. `verify_legacy.py` passed after implementation.
The user's preexisting deletion of `paper/memoryfence-paper.pdf` remains outside
these commits; original manuscript source and committed historical PDF are preserved
in Git. Documentation links now point to source so that the user's missing local
PDF does not break link validation. No default-branch merge or history rewrite.

## Original artifact recomputation

Commands executed from the repository with Python3.12.12:

```bash
.venv/bin/python scripts/research/verify_final.py experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/mf-original-qualification-20261107.json
.venv/bin/python scripts/research/verify_final.py experiments/2026-10-25-bounded/paired-state-study.zip.xz --qualification-archive experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/mf-original-state-20261107.json
```

Both JSON outputs matched the committed corresponding analyses byte for byte.
Logs: `verification-2026-11-07/original-qualification-verifier.log` and
`original-state-verifier.log` in that directory. This confirms recomputed supplied
raw evidence, not new independent inference or original-host attestation.

## Historical 238-test reproduction

A plain `git archive` at the historical revision failed one notebook test because
Git metadata was missing: **237 passed /1 failed**. Retained log:
`verification-2026-11-07/legacy-archive-attempt.log`. An archive-only retry showed
the same environment issue; no original test was edited to conceal it.

Corrected environment: a separate Git clone at
`/tmp/memoryfence-legacy-git-20261107`, detached
`5ca7c2d45ba83334c85fc219f5d287ea8aed6f61`. After `uv sync --frozen`, executed
`uv run --frozen pytest --cov --cov-report=term-missing` in that checkout.
**238 passed in26.06s;91.58% coverage.** Log:
`verification-2026-11-07/legacy-pinned-tests.log`.
This independently reproduces the historical software suite; it does not prove
scientific performance. Entry publication-stage tests number246, not238.

## New deterministic execution and independent check

```bash
UV_CACHE_DIR=/tmp/memoryfence-uv-cache uv run --frozen memoryfence expanded validate --dataset benchmarks/expanded-v1/scenarios.json
UV_CACHE_DIR=/tmp/memoryfence-uv-cache uv run --frozen memoryfence expanded run --dataset benchmarks/expanded-v1/scenarios.json --directory /tmp/memoryfence-expanded-v1-20261107 --split all
UV_CACHE_DIR=/tmp/memoryfence-uv-cache uv run --frozen memoryfence expanded export --directory /tmp/memoryfence-expanded-v1-20261107 --output /tmp/mf-expanded-v1-20261107.zip.xz
python3 scripts/research/verify_expanded.py /tmp/mf-expanded-v1-20261107.zip.xz --output /tmp/mf-expanded-v1-verification.json
```

Observed:80 cases/16 families;560 completed/560 planned;zero invalids;zero model
calls;independent verification560/560. `experiments/2026-11-07-expanded` stores the
unchanged export, exact manifest, summary and verification. Execution log:
`verification-2026-11-07/expanded-execution.log`. Method was not retuned after held-out
inspection. Generator output compared byte-for-byte to frozen scenarios.json.

The frozen guard-input rejection path was unit-tested but did not trigger a blocked
recomputation in the final matrix. This distinction remains in the results.
`model doctor` found no loopback runtime; retained log:
`verification-2026-11-07/model-availability.log`. No paid fallback was used.

## Quality-check observations

Before correcting local missing-PDF links, `make check` reached **256 passed/2
failed**,91.64% coverage. Both failures were Markdown links to the user's already
missing PDF, not altered research outputs. Links were changed to LaTeX source;
the PDF deletion itself was neither restored nor staged. New focused tests at
that stage:8 passed. Final integrated observations are recorded below after the
complete documentation/evidence checks.

Integrated `make check` at the evidence/documentation stage passed **265 tests,
zero failed/skipped,91.64% coverage**; strict mypy125 files, both distribution
metadata checks, citation validation and six import contracts passed. `make diagrams`
rendered all four Markdown sources with Mermaid, including the new architecture.
A final handoff-report document is added subsequently and included in the last
full run below.

The first hygiene pass normalized trailing whitespace in two new SVGs and the
archive-attempt diagnostic log, and the final newline in generated count tables.
No raw experiment archive or pinned original byte changed. The plotting helper now
emits the same normalized text; diagnostic log normalization does not alter the
reported failure or traceback. Hygiene was rerun after staging these fixes.

Final integrated `UV_CACHE_DIR=/tmp/memoryfence-uv-cache make check`: **266 passed,
0 failed,0 skipped in28.11s;91.64% coverage**. Ruff lint/format, strict mypy125
source files, sdist/wheel metadata, citation schema and all six import contracts
passed. Logs: `verification-2026-11-07/final-quality.log` and
`final-diagrams.log`. Figure regeneration after text normalization matched all six
derived files byte for byte; no experiment was rerun. Legacy53-byte check still
passes. Hygiene's final result is retained in `final-hygiene.log`.
