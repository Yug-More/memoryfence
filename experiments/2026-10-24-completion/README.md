# Capability and lifecycle evidence — 24 October 2026

These records are separate from the unchanged [historical 28-cell pilot](../2026-10-24-colab/README.md).
Original timestamps are UTC: these follow-ups ran on 25 October UTC, during
24 October in America/Los_Angeles. The [index](index.json) records each archive's
role, original code revision, timestamps, complete hashes, byte sizes and counts.

## Preserved runs

- **qualification-v1:** 54 benign trials, all valid; no model/interface passed the
  declared gate. 0.5B scored 3/9 original, 3/9 task-last and 2/9 example. 1.5B scored
  6/9, 3/9 and 6/9 respectively. Per-family counts remain separate in the analysis.
- **diagnostics-v1:** 24 probes, 21 valid failures and three invalid 0.5B no-tools
  replies. Native-tool omission, context 4096 and output 512 did not produce an
  exact direct-task success. These probes are not security benchmark trials.
- **literal-qualification:** 18 benign trials, all valid. The new literal-field task
  qualified 1.5B at 9/9, including 3/3 in every family. 0.5B remained at 3/9. The
  original gate (8/9, at least 2/3 per family, no invalid) and exact scoring stayed
  unchanged. Fresh seeds were used; no attack outcomes informed selection.
- **literal-controlled-native:** 80 planned and recorded episodes, 13 valid and
  67 invalid. Direct-memory outcomes include three exact canary ticket effects.
  DF3 also lost both clean tickets; DF2-exclude attack replies were invalid. All
  64 transformed/deleted episodes failed the native transformation contract. They
  establish no persistence, deletion or successful-defense result.
- **transformation-qualification:** nine benign calls, all valid under explicit
  `transform-v2-json-schema`. TT1/TT2/TT3 each used three seeds. All retained the
  test words `review` and `status`; this is interoperability and a narrow content
  check, not validated semantic quality or human evaluation.

- **schema-controlled:** 80 recorded episodes, 52 valid and 28 invalid; 112 valid
  committed model transformations and 80 agent responses. Eleven exact objective
  effects occurred at source-alive stages. DS1 retained canary-bearing derived
  memories, but no post-deletion objective action was observed. DS3 removed all
  descendants, yet all corresponding agent replies were invalid. Behavioral
  protection is not established; see the [full report](../../docs/research/COMPLETION_REPORT.md).

- **contract-qualification:** 12/12 valid replies, 9/12 exact successes. Direct,
  memory-field and response tasks each passed 3/3; empty retrieval passed 0/3,
  with three refusals. The predeclared 12/12 gate failed. No new security matrix
  was executed and no threshold was changed.

![Independently verified capability counts](capability-outcomes.svg)

The qualified task is unusually explicit, and nine trials cannot establish general
competence. A 9/9 Wilson 95% interval is approximately [0.701, 1]. The source pattern,
small models, repeated seeds and development amendments limit generalization.
No defense-efficacy claim follows from these pooled counts; populations and modes
must remain separate. The prospectively gated corrected schema-transformation run
is independently preserved, not a replacement for native failures.

The seven accessions contain 277 heterogeneous records and 389 recorded chat
responses. These are inventory totals, never a security denominator. The preserved
historical pilot and its diagnostics remain separate. The later free runtime was
reset and restored with only the previously approved 1.5B artifact.

## Originals and provenance

Every `.zip.xz` is a ZIP_STORED archive compressed losslessly using XZ. Raw members
are preserved, including requests/responses, SQLite state, scenarios, evaluator
keys, events, results, checkpoints and the executed driver/protocol. Benign
transformation qualification has request/result/journal records rather than
benchmark SQLite episodes. Installed-model, Ollama and runtime metadata are included.
Diagnostic export additionally preserves installer/daemon logs and its worker.

All transport and original ZIP hashes matched values printed inside Colab before
local analysis. Browser download handoff had stalled previously, so explicit
base64 notebook output was decoded locally. No model weights, credentials or Drive
files were exported. Hashes establish consistency with supplied originals, not
independent execution attestation. Actual HTTP records, not test fixtures, supply
these observations. Some transient notebook setup tracebacks were not retained;
all recorded trials and diagnostic invalids in these completed archives remain.

Executed code revisions:

- `cfb86165da1dc80cef0df908918ca8003ac4d09b`: original qualification/diagnostics.
- `cd858ba0433de07a661e2eefe318330ad2498100`: literal agent gate/native lifecycle.
- `cde45335ff0c1d04a3cb2be01fe38fbb809d5f79`: transformation-schema gate and corrected lifecycle.
- `baa29fac9156c1e6e4a68eea013eb2a79d6a138a`: complete-contract benign gate (failed).

Models actually executed are Qwen2.5 0.5B and 1.5B Q4_K_M, with exact digests in
`installed-models.json` in each archive. Ollama 0.40.11, project Python 3.12.3 and
free two-CPU Colab were used. No paid API, billing change or extra model was used.
Raw event times in SQLite are logical; journal/trial UTC timestamps are wall time.
Identifiers are namespaced by experiment accession and trial ID.

## Independent recalculation

From the repository root, using only the Python standard library:

```bash
python3 scripts/research/verify.py experiments/2026-10-24-completion/qualification-v1.zip.xz --output /tmp/qualification-v1-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/diagnostics-v1.zip.xz --output /tmp/diagnostics-v1-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/literal-qualification.zip.xz --output /tmp/literal-qualification-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/literal-controlled-native.zip.xz --output /tmp/literal-controlled-native-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/transformation-qualification.zip.xz --output /tmp/transformation-qualification-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/schema-controlled.zip.xz --output /tmp/schema-controlled-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/contract-qualification.zip.xz --output /tmp/contract-qualification-analysis.json
```

The verifier imports no MemoryFence evaluator. It checks unique trials, raw
sampling settings, prompts, installed model identity, raw replies versus stored
calls, exact sandbox effects, true-lineage retrieval, transformation text and
qualification numerators/denominators/selection. CI regenerates saved analysis and
rejects deliberately altered raw replies. It does not attest the inference host
or supply validated semantic labels or human inter-rater agreement.

To recover original ZIP bytes, use `lzma.decompress` and compare with
`original_zip_sha256` in the index. Extract only to a fresh directory; never replace
original trial data with regenerated summaries or resume it under another revision.

To regenerate the capability figure in an isolated optional environment:

```bash
MPLCONFIGDIR=/tmp/memoryfence-mpl uv run --no-project --with matplotlib==3.10.7 --python 3.12 experiments/2026-10-24-completion/plot.py
```

The [entry assessment](../../docs/research/COMPLETION_ASSESSMENT.md),
[original protocol](../../docs/research/COMPLETION_PROTOCOL.md),
[literal-task amendment](../../docs/research/LITERAL_TASK_AMENDMENT.md) and
[transformation amendment](../../docs/research/TRANSFORM_CONTRACT_AMENDMENT.md)
explain the decisions, unchanged gates, deviations and scientific limits.
