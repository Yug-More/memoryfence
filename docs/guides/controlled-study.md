# Reproduce the bounded capability and lifecycle study

The saved evidence can be verified without a model, GPU, cloud account or paid API.
New inference uses an adequate local host or a free Colab CPU runtime. Do not enable
billing, purchase credits or upgrade a runtime to follow these instructions.
A Colab reset can erase its disk; export before ending the session.

## Recalculate the saved evidence

From the repository root, using Python 3.12 or newer:

```bash
python3 scripts/research/verify.py experiments/2026-10-24-completion/qualification-v1.zip.xz --output /tmp/qualification-v1-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/diagnostics-v1.zip.xz --output /tmp/diagnostics-v1-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/literal-qualification.zip.xz --output /tmp/literal-qualification-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/literal-controlled-native.zip.xz --output /tmp/literal-controlled-native-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/transformation-qualification.zip.xz --output /tmp/transformation-qualification-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/schema-controlled.zip.xz --output /tmp/schema-controlled-analysis.json
python3 scripts/research/verify.py experiments/2026-10-24-completion/contract-qualification.zip.xz --output /tmp/contract-qualification-analysis.json
```

The verifier uses only the standard library. It reads archives without extracting
untrusted paths and opens temporary SQLite copies in read-only mode. Checksums,
raw replies, stored calls, effects, lineage and qualification selection are checked.
No inference is replayed and no historical file is changed. The original ZIP can
be recovered using `lzma.decompress`; compare its hash with the evidence index.

## Runtime and model requirements

The observed free runtime had two CPUs, approximately 12.67 GiB RAM and no GPU.
The exact platform, Python 3.12.3, Ollama 0.40.11 and model digests are archived.
Model files are approximately 398 MB (0.5B) and 986 MB (1.5B), but the runtime and
installer need additional storage. Leave at least 6 GiB free disk and adequate RAM;
CPU execution takes time. Free Colab availability and session duration are not
promised. Stop and preserve partial records if resources disappear.

Use the official [Ollama installer](https://ollama.com/download) and
[uv installer](https://docs.astral.sh/uv/getting-started/installation/) on the
execution host. Colab may require Ubuntu `zstd` first. Start Ollama bound only to
`127.0.0.1:11434`; never create a tunnel or expose it publicly. No credentials or
API keys are needed. Download models only after intentionally choosing the
corresponding free cloud/local storage use:

```bash
ollama pull qwen2.5:0.5b
ollama pull qwen2.5:1.5b
```

Do not run these downloads on a space-constrained Mac. The executed work used only
the temporary Colab machine. The 1.5B artifact is Apache-2.0 according to its
[upstream model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct); inspect the
installed digest rather than assuming a mutable tag still names the same bytes.

## Pin the execution code and use fresh directories

Version-1 qualification and diagnostics ran at
`cfb86165da1dc80cef0df908918ca8003ac4d09b` (PR #15).
Literal qualification and native-transformation study ran at
`cd858ba0433de07a661e2eefe318330ad2498100` (PR #16).
Transformation-schema qualification uses
`cde45335ff0c1d04a3cb2be01fe38fbb809d5f79` (PR #17).
Each is a preserved local commit merged through a green PR. A later documentation
commit need not equal the executed code revision.

Clone a separate checkout for a pinned condition and run `uv sync --frozen --python
3.12`. On Colab, run **all project commands through that checkout's
`.venv/bin/python` subprocess**, never by importing project packages into a different
kernel interpreter. The kernel may be Python 3.13. Do not reuse output directories,
edit completed results or resume original archives under another revision.

At the version-1 revision:

```bash
.venv/bin/python scripts/research/study.py qualification /tmp/memoryfence-qualification-new
.venv/bin/python scripts/research/study.py diagnostics /tmp/memoryfence-diagnostics-new
```

At the literal-task revision or the schema repair revision:

```bash
.venv/bin/python scripts/research/study.py literal-qualification /tmp/memoryfence-literal-new
```

At the schema repair revision, after literal qualification completes:

```bash
.venv/bin/python scripts/research/study.py transformation-qualification /tmp/memoryfence-transform-new
```

Inspect the two qualification files, raw journals and all benign outputs. A false
gate is a failed condition; never change the threshold or replace failed cells.
The agent gate needs 8/9 overall, at least 2/3 per family and no invalid response.
The transformation gate needs 9/9 structured responses. The latter does not validate
semantic quality. Only if both gates pass:

```bash
.venv/bin/python scripts/research/study.py schema-controlled /tmp/memoryfence-schema-controlled-new --qualification /tmp/memoryfence-literal-new --transform-qualification /tmp/memoryfence-transform-new
```

The 80-episode matrix is fixed in the prospective protocols. No paid API is used.
The native-transformation comparison uses `literal-controlled` with the agent gate
only; its original 64 transformation failures are historical evidence, not a
recommended successful execution path. Never pool that condition with schema mode.

## Complete action contract follow-up

The [version-4 amendment](../research/ACTION_CONTRACT_AMENDMENT.md) addresses proposals
missing required tools/arguments. At pinned revision
`baa29fac9156c1e6e4a68eea013eb2a79d6a138a` (PR #19), run:

```bash
.venv/bin/python scripts/research/study.py contract-qualification /tmp/memoryfence-contract-qualification-new
```

This uses only 1.5B, a separate explicit action schema and seeds 651/652/653.
**All 12 benign tasks must pass**, including the empty-retrieval family. Stop if
any cell fails; never relax the threshold. Only after that gate and the independent
nine-call transformation gate pass, the optional `contract-controlled` mode accepts
both qualification directories, using the same flags as `schema-controlled`.
Every condition requires fresh output directories. No earlier record is replaced.

## Artifact layout and export

Each episode has `scenario.json`, `evaluation-key.json`, raw model journal(s),
`system.sqlite`, `groundtruth.sqlite`, events, benchmark result and `trial.json`.
`trials.jsonl` checkpoints each finished episode. Root manifests contain code,
driver/protocol/lock hashes, Python/platform information and the declared mode.
Benign transformation qualification has nine `transform-*` directories and separate
request/result/journal records. Incomplete directories and unmatched journal
requests must remain visible after an interruption.

Export the entire directory plus the exact executed driver, protocol(s), installed
`/api/tags` and `/api/version` outputs and runtime metadata. Existing archives include
these as `execution-driver.py`, `protocol.md`, applicable amendments,
`installed-models.json`, `ollama-version.json` and `runtime.json`. Use ZIP_STORED plus
lossless XZ for efficient compression of repeated SQLite structure. Preserve every
member, not just successful cells. The evidence README documents original hashes
and the explicit base64 output fallback used when browser downloads stalled.

## Figures and interpretation

The optional isolated figure environment does not change project dependencies:

```bash
MPLCONFIGDIR=/tmp/memoryfence-mpl uv run --no-project --with matplotlib==3.10.7 --python 3.12 experiments/2026-10-24-completion/plot.py
```

The [report](../research/COMPLETION_REPORT.md) separates genuine observations,
diagnostic invalids, task changes, transformation contracts, exact action metrics
and research limits. Generated-policy utility failures and missing denominators
must remain visible. A new model/tag, prompt, output contract or task is a new
experimental condition, even if it looks like an engineering repair.
