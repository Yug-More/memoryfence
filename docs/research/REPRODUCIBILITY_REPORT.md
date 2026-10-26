# Observed reproducibility report

25 October 2026. Fresh environment: CPython 3.12.12 on macOS ARM64, created with
`UV_PROJECT_ENVIRONMENT=/tmp/memoryfence-publication-venv uv sync --frozen`.
61 locked packages installed, including the editable project. The application
lockfile and package requirements are unchanged. All commands below run from the
repository root; use new output directories. No command calls a model or downloads
weights. Optional plotting and TeX tools are free local tools, separate from the
application environment.

## Clean installation and core workflows

```bash
uv sync --frozen
uv run memoryfence --help
uv run memoryfence demo --directory /tmp/mf-publication-demo-new
uv run python scripts/research/reproduce_workflows.py --directory /tmp/mf-workflows-new
```

Observed: all 25 subprocess commands passed in a fresh directory. They include the
demo, catalog validation/list, 12 scripted post-deletion comparisons (LF1.0/LF0.5 ×
DS0/DS1/DS3 × DF0/DF2-exclude), inspect/export, deterministic benchmark replay,
experiment smoke/status/audit/verify/summarize/export. Replay returned
`equivalent: true`; manifest audit and experiment replay succeeded. These scripted
fixtures establish software mechanics, not empirical model performance. The
[sanitized complete outputs](../verification/2026-10-25-publication/workflows.json)
retain every command, exit code and output.

An initial workflow choice used `summary-note` with deletion, which correctly
rejected the unsupported configuration (`this scenario has no source to delete`).
The documented comparison uses `post-deletion`, which declares a deletable source.
This was a reproduction-script configuration correction, not a production bug or
an excluded experimental result.

Inspect the actual recorded graph without modifying the database:

```bash
uv run python - <<'PY'
import sqlite3
from pathlib import Path
p = Path('/tmp/mf-workflows-new/LF1.0-DS0-DF0/system.sqlite').resolve()
with sqlite3.connect(p.as_uri() + '?mode=ro', uri=True) as db:
    print(db.execute('SELECT child_id,parent_id FROM recorded_provenance_links ORDER BY child_id,parent_id').fetchall())
PY
```

Observed one recorded derivation edge in this one-summary scripted fixture;
[saved graph](../verification/2026-10-25-publication/recorded-graph.json).
Ground truth is separate and is not supplied to the defense.

## Verify genuine archives

```bash
uv run python scripts/research/verify_final.py experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/mf-qualification.json
uv run python scripts/research/verify_final.py experiments/2026-10-25-bounded/paired-state-study.zip.xz --qualification-archive experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/mf-state.json
cmp /tmp/mf-qualification.json experiments/2026-10-25-bounded/final-qualification-analysis.json
cmp /tmp/mf-state.json experiments/2026-10-25-bounded/paired-state-study-analysis.json
uv run python experiments/2026-10-24-colab/analyze.py
```

Observed both fresh independent analyses matched committed JSON byte for byte.
The original pilot regression also runs in the full test suite. Its historical
zero legitimate completion is not pooled with the final qualified study. The old
seven completion accessions and 28-cell pilot remain unchanged. The real execution
used e5dcc3c and the documented extra-level defect; current code intentionally
fixes its grid. Instructions for actual inference, including model digest and
free-runtime limitations, remain in [controlled-study.md](../guides/controlled-study.md).
No new inference was needed for this publication pass.

## Regenerate manuscript data and PDF

Prerequisites: optional Matplotlib 3.10.7, Tectonic 0.17.0, and its downloadable TeX
bundle. Obtain the compiler from the official release linked in the
[paper guide](../../paper/README.md). First compilation needs network access;
PDF metadata need not be byte-identical across builds.

```bash
uv run python scripts/research/sensitivity.py --output /tmp/mf-sensitivity.json
uv run --no-project --with matplotlib==3.10.7 --python .venv/bin/python paper/generate.py
mkdir -p /tmp/mf-paper-build
tectonic --keep-logs --outdir /tmp/mf-paper-build paper/main.tex
cp /tmp/mf-paper-build/main.pdf paper/memoryfence-paper.pdf
uv run python scripts/research/audit_paper.py --output /tmp/mf-paper-audit.json
```

`make paper TECTONIC=/absolute/path/to/tectonic` is the equivalent convenience
workflow. Observed: all 278 masks checked, numerical tables/facts regenerated,
three PNGs produced, BibTeX completed, 12-page PDF compiled (10 main, one references,
one appendix). All pages were rendered and visually inspected; no remaining
overfull/underfull boxes, undefined citations/references, clipped figures, blank
pages or overlapping text. The initial build's table-boundary error and long-hash
overflow were repaired before delivery. Publication audit includes output hashes.

The two original scientific figures can also be regenerated using the command in
[paper/README.md](../../paper/README.md); their PNG hashes matched the preserved
originals. SVG metadata timestamps are not experimental differences.

## Engineering and security checks

```bash
make check
make pre-commit
make diagrams
```

The complete check runs Ruff, strict mypy, branch coverage, build/twine, citation
metadata and all six import contracts. An initial sandboxed HTTP regression could
not open a loopback socket; the full run with local sockets permitted passed.
This environment restriction is not reported as a software defect. The final
run's exact test/coverage total is in the publication audit and committed check log.

A refreshed pip-audit 2.10.1 public advisory lookup found zero known vulnerabilities
among 60 applicable external locked packages. The dated
[raw lookup](../verification/2026-10-25-publication/dependency-audit.json) records the
unchanged uv.lock hash. Ruff includes security rules; endpoint, ACL, atomicity,
origin isolation and tamper regressions are covered by actual tests. This is not a
penetration test or security guarantee.

## Remaining reproduction boundaries

No weights are bundled. Actual free Colab availability and future package/advisory
services are external dependencies. Optional paper authoring requires network on
first use and is not a required application dependency. Hashes verify supplied
bytes, not inference-host attestation. There is no independent human semantic
validation, full held-out replication, project license or publication acceptance.
