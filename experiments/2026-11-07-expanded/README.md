# Expanded Study v1 accession — 7 November 2026

**Deterministic memory-system study; zero model inference.** 80 configurations,
16 manually specified structural families, seven paired strategies, 560 completed
runs and zero invalids. 12 development and four held-out families. Outcomes include
unfavorable silent-gap exposure and marked-gap benign loss; no broad efficacy claim.

- `expanded-v1.zip.xz`: raw dataset, manifest, checkpoints and before/after SQLite.
- `execution-manifest.json`: code revision, dates, versions, seeds/config reference,
  dataset/lock hashes and working-tree state. Only preexisting PDF deletion was dirty.
- `independent-verification.json`: stdlib raw-state recomputation, 560 verified runs,
  archive transport/decompressed ZIP SHA256, dataset identity.
- `summary.json`: split/control/strategy case-macro metrics and family-paired deltas.
- `derived/aggregates.json`: pooled count pairs, timing/size descriptive observations.
- `derived/count-tables.md`: all 70 split/control/strategy count rows.
- `derived/*.svg` and `*.png`: scientific plots from actual verified structured records.

Archive paths: `runs/{scenario_id}/input/input.json`, `system.sqlite`,
`groundtruth.sqlite`; `runs/{scenario_id}/{strategy}/result.json` and both after-state
SQLite files. `records.json` duplicates the per-cell structured result for checkpoint
integrity. Logical database time differs deliberately from UTC wall execution time.

Execution revision: `4a430fa9939b1fa6438c64508368006e1e8b3fc6`.
Transport SHA256: `bf9d2e5f1df71d2c97d668f62b734c1a644f9a7e4045c3624295c3616570cea2`.
Dataset SHA256: `6470b3c2ae3cb8fdf702bf797ea6cf63237db99c1e6a2ac5efdaf145ca140b34`.

Verify with `scripts/research/verify_expanded.py`; reproduce or regenerate figures
using `docs/REPRODUCIBILITY.md`. The new archive never replaces the Original Study
or represents new LLM responses. `tests/test_expanded_evidence.py` checks raw data,
dataset identity, saved summary and original 53-file preservation in CI.
