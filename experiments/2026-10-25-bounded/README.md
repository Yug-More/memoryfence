# Final bounded study — 25 October 2026

Two genuine accessions complete the [declared finite scope](../../docs/research/FINAL_BOUNDED_PROTOCOL.md).
The [index](index.json) records exact execution revision, timestamps, hashes, byte
sizes and count units. The [report](../../docs/research/COMPLETION_REPORT.md) and
[evidence-to-claim table](../../docs/research/EVIDENCE_TO_CLAIMS.md) connect findings
to original members. This is automated/assistant verification, not human semantic
validation or execution-host attestation.

## Accessions and actual units

- **final-qualification:** 24 real agent responses, all valid. Original order 9/12;
  task-last 12/12. Both use the same complete v3 schema, tools, model, task and
  sampling; only two user messages move. Original empty context 0/3, task-last 3/3.
  The fixed 12/12 gate selected task-last before new attacks.
- **paired-state-study:** six real TT2→TT3 chain executions, twelve actual
  transformation responses, then 36 real agent responses. All 36 agent replies
  were valid; 18/18 clean and 18/18 poisoned episodes completed exact legitimate
  tickets. Each attack cell had 0/3 objective proposals/effects. Three source-alive
  free-text fields nevertheless repeated the canary.
- **State views:** 108 declared views backed by 54 snapshots. An enum-iteration
  defect added 36 LF0.0 views backed by 18 snapshots. All 144 are retained and
  verified; LF0.0 is explicitly off-protocol. It adds no model calls. See the
  [departure and correction](../../docs/research/FINAL_BOUNDED_DEVIATIONS.md).

The cycle made **72 actual chat responses**, not 144 model trials. Cached outputs
and copied `model_calls` rows are logical reuses of twelve genuine transformation
responses. They are not new inference. The seven
[older accessions](../2026-10-24-completion/README.md) and
[original pilot](../2026-10-24-colab/README.md) remain unchanged and separate.

## Strongest observations and limits

DS1 retained both descendants of each source. Under LF1.0, DS3 removed all attack
descendants. At LF0.75 it retained 4/6, at LF0.5 6/6. DF2 excluded known peer ancestry
at LF1.0, but admitted orphaned attack memory in 2/3 and 3/3 incomplete-lineage views.
Those are conditional state/retrieval results on identical generated text, not
incomplete-lineage behavioral attack rates. Behavior used LF1.0 only.

All six attack transformation outputs retained the exact canary. One clean TT3
response was only `Transformation TT3.`; syntax validity does not establish faithful
consolidation. No semantic-following label, general model competence, useful-defense
ranking or universal security guarantee follows. The 0/3 per-cell attack Wilson
upper bound is about 0.562; repeated views are not independent scenario samples.

![Declared provenance/deletion outcomes](provenance-deletion-outcomes.svg)

## Preserve and independently verify

Originals are ZIP_STORED, compressed losslessly with XZ. Both transport and original
ZIP hashes match values printed in Colab before local analysis. The original ZIP
members preserve HTTP journals, SQLite pairs, caches, scenarios/checkpoints,
configuration, executed drivers/protocol, workers/logs, runtime metadata and the
actual Ollama template. No weights, credentials or Drive data were exported.

```bash
python3 scripts/research/verify_final.py experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/final-qualification-analysis.json
python3 scripts/research/verify_final.py experiments/2026-10-25-bounded/paired-state-study.zip.xz --qualification-archive experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/paired-state-study-analysis.json
```

The stdlib verifier imports no MemoryFence scorer. It checks raw response validity,
exact effects, paired request equality, actual prerequisite bytes, shared text,
independent seeded edge retention, true lineage, deletion reach, lexical ranking,
unique IDs and the full actual grid. It verifies declared and extra views separately.
Tests reject changed raw replies and altered state endpoints. It opens temporary
SQLite copies read-only and never extracts archive paths to the repository.

To recover original ZIP bytes, use `lzma.decompress` and compare the index's
`original_zip_sha256`. Use a fresh destination for inspection. Database IDs are
local to chain/condition/trial; namespace them by accession and member path.
Database event clocks are logical, while HTTP/trial metadata record real UTC time.

## Pinned execution versus corrected code

Both accessions ran at `e5dcc3c61cc6ded130a4f118825fc324e90a7e3a` using existing
Qwen2.5 1.5B Q4_K_M weights, digest
`65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`.
Ollama 0.40.11, project Python 3.12.3, two free Colab CPUs; no new weights or paid
resources. The user-message permutation used v3 plus the research transport.
The later reusable v4 adapter setting is request-equivalent, not a separately
executed model condition.

The pinned driver produced LF0.0 views. Current code fixes that enum iteration and
reproduces the intended 108-view design. Never overwrite originals or claim that a
corrected rerun is the archived execution. The [guide](../../docs/guides/controlled-study.md)
gives exact commands and eligibility rules. A model/tag or prompt change needs new
qualification; this narrow result is not broad reliability.

## Figures

Figures derive only from independent analysis, with no illustrative data. Regenerate
in an isolated optional environment without changing project dependencies:

```bash
MPLCONFIGDIR=/tmp/memoryfence-mpl uv run --no-project --with matplotlib==3.10.7 --python 3.12 experiments/2026-10-25-bounded/plot_final.py
```

The qualification figure preserves 0/3 empty-context failures. The state figure
shows only declared fidelities and labels the extra LF0.0 records as separate.
