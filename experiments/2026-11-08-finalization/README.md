# Finalization validation accession — 8 November 2026

No new scientific model result. This accession preserves new deterministic
reproduction, independent checks, clean-suite logs, dependency scan and actual
blocked model availability. Original accessions remain byte-identical.

- `reproduction.zip.xz`: fresh560-run matrix atd00fa66 with input/after SQLite,
  actual host/timing/version metadata, results and summary. Zero model calls.
- `reproduction-verification.json`: independent raw-state verification560/560.
- `reproduction-comparison.json`:560 semantic records equal; timings and SQLite
  sizes excluded. This repeat execution does not increase independent sample size.
- `failure-analysis.json`: reproducible post-hoc categorization of all70 original
  split/control/strategy groups with denominators and representative raw members;
  produced by `scripts/research/analyze_release.py`.
- `qualification.json`, `original-state.json`: original raw model evidence
  independently recomputed again; byte-identical to committed historical analyses.
- `model-availability/` and `model-availability-final/`: frozen exploratory config, manifest and raw HTTP journal.
  Actual status blocked,error.model_unavailable,zero chat requests; no behavioral
  denominator or synthetic success was substituted. GET/availability calls are
  not inference. Database timestamps elsewhere use a logical clock; availability
  UTC dates are9 November, corresponding to8 November in Los Angeles.
- `dependency-audit-corrected.json`: installed-environment public-advisory scan;
 61 listed distributions:60 audited,one editable project skipped,zero reported
  known vulnerabilities.
  This is not proof of vulnerability absence or a penetration test.
- `logs/`: actual test/install/execution/check logs. The first dependency-audit
  invocation failed on unsupported flags; its log remains alongside the corrected
  invocation. Text diagnostics may have trailing whitespace normalized by hooks;
  raw study archives and JSON evidence remain unchanged.

Clean pinned historical suite:238 passed,91.58% coverage. Clean merged expansion
baseline:266 passed,91.64%. Final current suite:287 passed,91.41%; all quality checks passed. The separate
expanded manuscript has10 rendered/reviewed pages. Exact commands/logs are in
`docs/FINAL_RESEARCH_VALIDATION.md`.

Recompute failure categories/comparison to a fresh output path:

```bash
uv run --frozen python scripts/research/analyze_release.py --original experiments/2026-11-07-expanded/expanded-v1.zip.xz --repeated experiments/2026-11-08-finalization/reproduction.zip.xz --output /tmp/memoryfence-release-analysis-new.json
```

The preservation checker pins53 Original Study files and12 prior Expanded Study
files. New finalization evidence is a separate accession; it never replaces either
original study. New helper, model and reporting code has adversarial software tests,
not newly generated model outcomes. No paid service, weights or external side effect.
