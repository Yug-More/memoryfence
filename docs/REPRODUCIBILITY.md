# Reproducibility — separate evidence classes

7 November 2026. All commands below are free, local and zero inference unless
explicitly labeled otherwise. They never fetch model weights. Use fresh output
paths; named outputs must not already exist. `uv sync --frozen` may fetch free
Python packages. Original `uv.lock` and project dependencies are unchanged.

## Original evidence and software

```bash
uv sync --frozen
uv run --frozen python scripts/research/verify_legacy.py
uv run --frozen python scripts/research/verify_final.py experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/original-qualification-new.json
uv run --frozen python scripts/research/verify_final.py experiments/2026-10-25-bounded/paired-state-study.zip.xz --qualification-archive experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/original-state-new.json
```

Compare against the corresponding `*-analysis.json` accession files. Both matched
byte for byte on 7 November. This recomputes archived inference evidence; it does
not make new model calls or attest to the original machine independently.

The historical 238-test suite belongs to `5ca7c2d45ba83334c85fc219f5d287ea8aed6f61`,
not the current expanded revision. In a **separate Git checkout** of that revision:

```bash
uv sync --frozen
uv run --frozen pytest --cov --cov-report=term-missing
```

Observed: 238 passed, 91.58% branch-inclusive coverage. A plain archive first gave
237 passed/one failure because the notebook regression requires `git rev-parse`;
the subsequent Git checkout corrected the environment. Both logs are retained in
[verification record](research/VERIFICATION_2026_11_07.md). No old test was changed.

## Regenerate the finite Expanded Study

Protocol `9d56faa` predates implementation/evaluation. Execution revision is
`4a430fa9939b1fa6438c64508368006e1e8b3fc6`. The only dirty path during execution was
the preexisting user PDF deletion, recorded in the manifest. Source and dataset
were committed; no method was tuned after held-out inspection.

```bash
uv run --frozen memoryfence expanded validate --dataset benchmarks/expanded-v1/scenarios.json
uv run --frozen memoryfence expanded run --dataset benchmarks/expanded-v1/scenarios.json --directory /tmp/memoryfence-expanded-new --split all
uv run --frozen memoryfence expanded summarize --directory /tmp/memoryfence-expanded-new
uv run --frozen memoryfence expanded export --directory /tmp/memoryfence-expanded-new --output /tmp/memoryfence-expanded-new.zip.xz
uv run --frozen python scripts/research/verify_expanded.py /tmp/memoryfence-expanded-new.zip.xz --output /tmp/memoryfence-expanded-new-verification.json
```

`--split development` or `--split evaluation` selects whole families; all seven
strategies run for each case. This pipeline has no arbitrary per-case/model/repeat
selector or resume feature. A failed run retains checkpoint/error records. Finish
or diagnose it separately; rerunning requires a new directory, not overwriting it.
Unexpected unhandled failures can leave a partial manifest; the summarizer rejects
partial count grids. Historical benchmark/model commands remain separate.

Seeds, operation graphs, facts, query and canary are frozen in the benchmark. Stable
semantic counts, selected IDs and paired metrics should reproduce; timing, host,
UTC metadata and archive hashes may change. SQLite audit timestamps use a fixed
logical clock; actual execution wall time is separately recorded in UTC. Do not
compare compressed hash equality as a requirement for a new host's rerun.

## Verify the committed accession without rerunning experiments

```bash
uv run --frozen python scripts/research/verify_expanded.py experiments/2026-11-07-expanded/expanded-v1.zip.xz --output /tmp/expanded-saved-new-verification.json
uv run --frozen pytest tests/test_expanded.py tests/test_expanded_evidence.py
```

The stdlib verifier independently checks declared input DAGs/labels, recorded edge
retention/flags, raw before/after source/memory state, true graph preservation,
allowed/context lexical ranking and metric denominators against SQLite. This is
implementation-independent recomputation within this project, not a third-party
replication or proof against every shared design error. CI also compares the
recomputed family summary and frozen dataset to committed artifacts.

## Regenerate new figures without touching old ones

```bash
uv run --no-project --with matplotlib==3.10.7 --python .venv/bin/python scripts/research/plot_expanded.py experiments/2026-11-07-expanded/expanded-v1.zip.xz --output /tmp/expanded-figures-new
```

This optional temporary plotting dependency does not change `pyproject.toml` or
`uv.lock`. Figures and complete pooled count tables derive from verified raw
records. Family summaries remain separately in `summary.json`. IQR depicts observed
latency dispersion; it is not a statistical confidence interval.

## Model availability and cost

`memoryfence model doctor` reported loopback Ollama unavailable on 7 November.
No new inference, model download, hosted API or paid runtime was used. New ASR,
unauthorized-tool and LLM utility values are null. The historical free-Colab model
configuration is in [claims](RESEARCH_CLAIMS.md); a new genuinely model-backed study
requires qualification, a new accession and an available explicitly free runtime.
Do not substitute the projection backend's outcomes for model responses.

## Finalization validation — 8 November 2026

The [final validation](FINAL_RESEARCH_VALIDATION.md) and
[separate accession](../experiments/2026-11-08-finalization/README.md) preserve a fresh
560-run deterministic reproduction, clean historical/merged-baseline suites and
actual model-availability failure. `verify_release.py` checks both original53 and
prior expanded12 immutable files; `analyze_release.py` compares semantic records
and independently regenerates post-hoc error categories to a fresh output file.
The new [bounded model follow-up](../benchmarks/model-followup-v1/README.md) is a
separate exploratory command, not a change to the deterministic runner or evidence
of executed inference. It refuses invalid source accessions before qualification.
The [expanded LaTeX build](../paper/finalization/README.md) writes only the new
manuscript folder and never restores/overwrites the historical PDF.
