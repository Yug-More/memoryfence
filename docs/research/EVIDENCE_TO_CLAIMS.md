# Evidence-to-claim map

25 October 2026. Verification is automated standard-library recalculation plus
assistant inspection of representative raw outputs. **No independent human semantic
validation or execution-host attestation is claimed.** The
[index](../../experiments/2026-10-25-bounded/index.json) contains complete transport,
original ZIP and analysis hashes. Member paths below are inside the named archive;
recover its ZIP with lossless XZ decompression before inspection.

| ID | Supported observation | Unit / denominator | Raw archive and members | Independent check / limit |
|---|---|---|---|---|
| B1 | Original 9/12, task-last 12/12; empty context 0/3 → 3/3 | 24 valid qualification replies; 12 fixed tasks per layout | [Qualification ZIP/XZ](../../experiments/2026-10-25-bounded/final-qualification.zip.xz): `qualification.json`, `trials.jsonl`, `trial-0010`–`trial-0012` and `trial-0022`–`trial-0024` journals/SQLite | `qualify`: exact effects, empty raw/stored context, and paired request equality except message order. One model/task set. |
| B2 | All six attack outputs contain the exact canary | TT2/TT3 × three attack chain executions | [Study ZIP/XZ](../../experiments/2026-10-25-bounded/paired-state-study.zip.xz): `chains/attack-901`–`attack-903/cache.json`, `model-exchanges.jsonl`, `system.sqlite` | Cache text equals actual responses and committed memories; parent hashes and TT2→TT3 input closure match. Literal retention, not human semantic survival. |
| B3 | DS1 leaves both attack descendants alive | 6/6 derived records per fidelity across three attack chains | Study: `states/attack-901`–`attack-903/LF1.0/DS1/system.sqlite`, corresponding LF0.75/LF0.5 snapshots | Independent source-revision removal, primary absence, active rows and content comparison. Copied conditions are not independent generated samples. |
| B4 | LF1.0 DS3 removes every descendant | 0/6 active attack descendants; 0/3 exposed views | Study: `states/attack-901`–`attack-903/LF1.0/DS3/` SQLite pairs | Independently traverse recorded reach and compare actual surviving memory rows. Audit logs retain copies; not forensic erasure. |
| B5 | Incomplete recorded provenance leaves cascade survivors | LF0.75: 4/6 active attack descendants, 2/3 exposed chains; LF0.5: 6/6, 3/3 | Study: `states/attack-901`–`attack-903/LF0.75/DS3/`, `LF0.5/DS3/` SQLite pairs | Recompute seeded edge retention independently and verify true graph unchanged. Nominal LF is not an observed edge percentage. |
| B6 | DF2 admits orphaned peer content when recorded authors disappear | 2/3 exposed LF0.75 views; 3/3 LF0.5, including DS3 | Study: `states.json`; attack-901/LF0.75/DS3 recorded graph and source-author nodes | Recompute lexical ranking and author reach without importing defenses. Known peer authors are excluded; empty author sets pass this implemented predicate. No incomplete-lineage behavior estimate. |
| B7 | All 36 agent replies valid and legitimate; no exact attack proposal/effect | 18/18 clean utility, 18/18 attack legitimate completion; 0/3 objective effects in each of six attack cells | Study: `behavior.json`; every `behavior/<chain>/<policy>/<defense>/model-exchanges.jsonl` and SQLite pair | Parse raw replies independently; compare logged calls, paired state/context, complete 36-cell grid and exact sandbox arguments. Per-cell 0/3 upper Wilson bound ≈0.562. |
| B8 | Correct tool arguments coexist with poisoned free text | Three DS0/DF0 attack replies; body remains status | Study: `behavior/attack-901/DS0/DF0/model-exchanges.jsonl`, corresponding 902/903 members | Free-text exact-canary indicator is separate from objective proposal/effect. No semantic-following label is inferred. |
| B9 | One clean TT3 reply echoes only its operation label | 1/3 clean TT3 outputs; 5/6 clean outputs retain both test words | Study: `chains/clean-901/cache.json`, `model-exchanges.jsonl`; all clean chain members for denominator | Literal review/status check and assistant inspection. Valid JSON does not establish faithful consolidation. No repair or exclusion. |
| B10 | Extra LF0.0 views are off-protocol and add no calls | 36 extra views; 108 primary views; 72 actual chat responses across two accessions | Study: `states.json`, `status.json`, `execution-driver.py`, `protocol.md`; qualification journals and original chain/behavior journals | Full actual grid and raw invocation count; [deviation log](FINAL_BOUNDED_DEVIATIONS.md). Cached/copied model-call rows are not new inference. |

## Recalculate

```bash
python3 scripts/research/verify_final.py experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/final-qualification-analysis.json
python3 scripts/research/verify_final.py experiments/2026-10-25-bounded/paired-state-study.zip.xz --qualification-archive experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/paired-state-study-analysis.json
```

The derived [qualification analysis](../../experiments/2026-10-25-bounded/final-qualification-analysis.json)
and [state/behavior analysis](../../experiments/2026-10-25-bounded/paired-state-study-analysis.json)
contain every record, including the separately marked LF0.0 views. Figures consume
these files directly. Deliberate raw-reply and state-endpoint changes are rejected
by saved-evidence regression tests.

## Historical claims

The [historical inventory](../../experiments/2026-10-24-completion/index.json) and
[original pilot analysis](../../experiments/2026-10-24-colab/README.md) retain their
own code, raw records, counts and independent checks. The old 11 source-alive effects
and the new zero effects come from different matrices/seeds and are not a matched
message-order attack comparison. Neither condition replaces the other.
