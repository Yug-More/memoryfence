# Project handoff

24 October 2026 · Genuine development pilot completed; full study incomplete

## Delivered work

Recovery and architecture verification merged in [PR #9](https://github.com/Yug-More/memoryfence/pull/9).
[PR #10](https://github.com/Yug-More/memoryfence/pull/10) repaired model identity,
raw HTTP recording, durable checkpoints, scoring and denominators. Documentation
and identity assets merged in [PR #11](https://github.com/Yug-More/memoryfence/pull/11);
the dependency audit merged in [PR #12](https://github.com/Yug-More/memoryfence/pull/12).
[PR #13](https://github.com/Yug-More/memoryfence/pull/13) repaired the Colab interpreter
boundary and introduced explicit schema output as a separately identified condition.
Its merged revision, `38fd3da59688a7997b954a3308e89ba2a1f09bbd`, produced both genuine runs.

The typed Python/SQLite harness implements separate system and evaluator state,
provenance, transformations, deletion, retrieval, defenses, a bounded agent loop
and sandbox actions. Implemented mechanisms do not imply empirically validated
security. Original research questions and the draft protocol remain unchanged.

## Observed results

**28 genuine benchmark cells completed:** four compatibility cells and 24 matched
cells, with no invalid cells in the explicit schema condition. Three fully recorded
diagnostic probes are separate from those trials. The candidate remained
`qwen2.5:0.5b`; inference used free Colab CPU resources. No paid service was used.

Every matched defense condition had 0/2 attack-objective executions and **0/2
legitimate ticket completions**. The failed undefended utility control prevents a
useful defense-efficacy conclusion. All matched responses selected `respond`.
One compatibility response recommended forwarding to the synthetic address; its
lexical judgment remains an abstention, with no tool action. Transformation,
deletion and model-generalization questions were not tested.

The [results report](research/COLAB_PILOT_RESULTS.md) and
[evidence inventory](../experiments/2026-10-24-colab/README.md) contain exact
conditions, deviations, counts and limitations. Original archives retain raw
requests/responses, databases, manifests, results and drivers. Lossless XZ wrappers
preserve original ZIP bytes. Checksums matched the values exported from Colab.

## Reproduction and checks

```bash
uv sync --frozen
uv run python experiments/2026-10-24-colab/analyze.py
make check
make pre-commit
```

The independent stdlib analysis reconstructs retrieval from true lineage and
objective/utility actions from readonly SQLite effects, and matches stored calls
to raw responses. All 28 cells passed these consistency checks. It does not attest
the server or validate semantic judging. The older `scripts/recalculate.py`
checks exported stage arithmetic; deterministic test fixtures remain explicitly
separate from real inference. PR #13 passed 185 tests with 91.59% combined coverage.
Final local evidence QA passed 187 tests at 91.59% combined coverage, lint,
formatting, strict typing, package/citation validation and all six import contracts.
The evidence PR's CI record supplies remote verification for this workstream.

The actual Colab runs used archived project drivers in a notebook cell. An
unattended execution of every cell in the revised notebook was not independently
demonstrated. No model weights were committed or downloaded onto the Mac.

## Remaining research requirements

Do not scale this failed-capability condition into a confirmatory defense study.
First define a separate benign capability screen; any model or prompt change must
receive a new identity and fresh controls. Semantic survival and judging, human
reliability, paired cached transformations, component seed hierarchy, broader
utility, representative held-outs, sample-size planning, statistical procedures
and preregistration remain incomplete. The inherited bibliography received key
spot checks, not a complete refresh. Licensing remains the owner's decision.
No release, tag or publication is implied.

Local commits use `Yug-More <yugmore20@gmail.com>` as author and committer, without
assistant co-authors. Focused PRs require passing CI before merge. No direct runtime
dependency was added; the certifi audit was a separate lockfile fix. The optional
figure generator uses an isolated plotting environment. See the
[integrity audit](FINAL_RESEARCH_INTEGRITY_AUDIT.md) for the limits of acceptance.
