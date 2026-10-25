# Reproduce the bounded study and inspect historical conditions

The saved evidence can be verified without a model, GPU, Google account or paid API.
New inference used free Colab CPU. Do not enable billing, buy credits or upgrade a
runtime. Free availability/duration are not guaranteed; export before session expiry.

## Verify saved evidence first

From the repository root, with Python 3.12 or newer (the locked uv environment is
recommended):

```bash
uv sync --frozen
uv run python scripts/research/verify_final.py \
  experiments/2026-10-25-bounded/final-qualification.zip.xz \
  --output /tmp/final-qualification-analysis.json
uv run python scripts/research/verify_final.py \
  experiments/2026-10-25-bounded/paired-state-study.zip.xz \
  --qualification-archive experiments/2026-10-25-bounded/final-qualification.zip.xz \
  --output /tmp/paired-state-study-analysis.json
uv run python experiments/2026-10-24-colab/analyze.py
```

`verify_final.py` uses only the standard library and a standard-library helper;
it imports no production scorer. It reads archives without extracting their paths
and opens temporary SQLite copies read-only. Raw validity, exact effects, graph
reach, seeded retention, cached text, retrieval and prerequisite bytes are checked.
It rejects incomplete/missing records rather than manufacturing completed counts.
Checksums establish supplied-byte consistency, not execution-host attestation.

The [new inventory](../../experiments/2026-10-25-bounded/README.md) contains complete
hashes. Decompress XZ with `lzma.decompress` to recover original ZIP bytes and compare
`original_zip_sha256`. Inspect only in a fresh directory. IDs are local to accession
and chain/condition/trial. Database clocks are logical; HTTP/trial times are real UTC.

## Resources and model identity

Actual execution used two CPUs, approximately 12.67 GiB RAM, no GPU, project Python
3.12.3 and Ollama 0.40.11. The only model used in this cycle was the previously
approved `qwen2.5:1.5b` Q4_K_M artifact, 986,061,892 bytes, digest
`65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`.
Its upstream [model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) supplies
model/license context. No project license is inferred from the model's license.

Use an appropriate free cloud host with at least 6 GiB free disk and adequate RAM;
**do not pull weights onto a space-constrained Mac**. The executed runtime already
had this model. A deliberate fresh setup can use the official
[Ollama installer](https://ollama.com/download), Ubuntu `zstd` if required, then
`ollama pull qwen2.5:1.5b`. Bind the daemon only to `127.0.0.1:11434`. Never expose a
tunnel. Read `/api/tags` and `/api/show` to verify the exact digest/template before
using prior qualification claims; tags can change. No key or paid endpoint is needed.

On Colab, run project commands through the checkout's locked `.venv/bin/python`
subprocess. Do not import Python 3.12 binary dependencies into a Python 3.13 kernel.
The [historical Colab guide](google-colab-pilot.md) explains the interpreter boundary.

## Pin the executed condition

Both new accessions ran at:

```text
e5dcc3c61cc6ded130a4f118825fc324e90a7e3a
```

Use a separate cloud checkout:

```bash
git clone https://github.com/Yug-More/memoryfence.git memoryfence-pinned
git -C memoryfence-pinned checkout --detach e5dcc3c61cc6ded130a4f118825fc324e90a7e3a
cd memoryfence-pinned
uv sync --frozen --python 3.12.3
.venv/bin/python scripts/research/final_cycle.py qualification /tmp/memoryfence-final-qualification-new
.venv/bin/python scripts/research/final_cycle.py study /tmp/memoryfence-paired-study-new \
  --qualification /tmp/memoryfence-final-qualification-new
```

Use fresh output directories; both modes refuse to replace a completed directory.
The [prospective protocol](../research/FINAL_BOUNDED_PROTOCOL.md) fixes 24 benign
calls, six two-call transformation chains, 108 primary state views and at most 36
conditional agent calls. Qualification requires 12/12 valid exact successes per
layout, including empty retrieval. No threshold changes or manual selection edits.
If neither layout passes, state measurements still run, but agent calls do not.
Inspect every failed reply and preserve partial records if resources disappear.

### Archived departure versus current code

The pinned execution iterates the complete fidelity enum, including unplanned
LF0.0. Its archive therefore contains 144 views: 108 primary plus 36 extra. The
[deviation log](../research/FINAL_BOUNDED_DEVIATIONS.md) records discovery, preservation
and a full-run regression. The fixed current driver explicitly lists three levels
and produces the intended 108 views. The independent verifier recognizes the
archived 144-view departure and the corrected 108-view design. Do not overwrite the
original or represent a new corrected run as its bytes.

The later reusable adapter exposes the tested request layout with these explicit
configuration fields:

```json
{
  "output_mode": "json_schema",
  "agent_output_contract": "complete",
  "agent_message_order": "task_last",
  "prompt_template": "agent-v4-task-last"
}
```

These are a fragment of an experiment configuration, not a standalone complete
matrix. Historical inference used v3 plus the `task-last` transport; request-equivalence
tests support the integration, not an invented extra v4 run. Other tasks/models still
require qualification. Legacy defaults/fingerprints remain unchanged.

## Export complete records

Retain both qualification and study roots. Include:

- `manifest.json`, qualification trials/gate and the exact prerequisite copies.
- `chains/` raw exchanges, full request/response caches and original SQLite pairs.
- `prepared/` cached-output constructions and `states/` policy snapshots.
- `states.json`, `behavior.json`, each actual agent journal/database and `status.json`.
- Exact `final_cycle.py`, imported `study.py`, protocol, worker/log/status, `/api/tags`,
  `/api/version`, `/api/show` and runtime metadata.

A cache use or copied `model_calls` row is not an additional model invocation.
The actual journals in qualification, original chains and behavior count live
responses. Preserve unsuccessful attacks, content failures and all extra views.
Use ZIP_STORED then lossless XZ; print original/transport hashes before transfer.
No weights or account data belong in the export. A nonzero worker status is an
incomplete run requiring inspection, not a completed result to fill with fixtures.

## Historical accessions

The original qualification/diagnostics used `cfb86165da1dc80cef0df908918ca8003ac4d09b`;
literal qualification/native study used `cd858ba0433de07a661e2eefe318330ad2498100`;
transformation-schema conditions used `cde45335ff0c1d04a3cb2be01fe38fbb809d5f79`;
the failed complete-contract gate used `baa29fac9156c1e6e4a68eea013eb2a79d6a138a`.
The [historical inventory](../../experiments/2026-10-24-completion/README.md) gives all
seven independent-verifier commands and hashes. Their gates, failures, 11 source-alive
attack effects and interpretations remain separate from this final cycle.

## Recreate figures and quality checks

```bash
MPLCONFIGDIR=/tmp/memoryfence-mpl uv run --no-project --with matplotlib==3.10.7 --python 3.12 experiments/2026-10-25-bounded/plot_final.py
make check
make pre-commit
make diagrams
```

Plotting is optional and isolated from project dependencies. Figures consume only
verified analysis. The [report](../research/COMPLETION_REPORT.md) distinguishes exact
canary retention, ancestry exposure, semantic uncertainty, raw textual echoes,
objective proposals/effects and legitimate utility. State views are not model trials;
no human-rater agreement or universal protection follows from these counts.
