# Actual local model follow-up accession — 9 November 2026

74 actual Qwen2.5 1.5B requests:4 qualification +70 hybrid state-to-action probes.
Gate4/4; probes70 valid/zero invalid; literal legitimate effects70/70; exact attacker
proposals/effects0/42. One inspected mixed-source family,five controls,seven strategies,
two seeds. This is exploratory; not fresh model-written memory or general efficacy.

- `model-followup.zip.xz`: complete raw run directory, including HTTP journal,
  qualification/probe JSON and per-probe sandbox SQLite. No weights are committed.
- `execution-manifest.json`, `config.json`: source revision4a82416, exact unchanged
  protocol, model digest/runtime/settings, actual UTC timing and source-archive hash.
- `independent-verification.json`: recomputed journal/context/proposal/effect counts,
  all35 control/strategy strata and observed token totals.
- `hardware.json`: approved temporary local environment, artifact/runtime sources,
  license reference and zero paid API cost.

Archive paths: `http.jsonl`, `qualification.json`, `probes.json`, and
`{scenario_id}/{strategy}/{seed}/{result.json,system.sqlite,groundtruth.sqlite}`.
Raw prompts/replies are synthetic. No external message or tool effect occurred.

```bash
uv run --frozen python scripts/research/verify_model_followup.py /tmp/extracted-model-run --source experiments/2026-11-07-expanded/expanded-v1.zip.xz --output /tmp/model-verification-new.json
```

Extract only this trusted project archive to a fresh directory. The verifier makes
no model requests; host authenticity is not independently attested. Model setup and
full execution use `benchmarks/model-followup-v1/config.json`; weights require local
resources and explicit authorization if substantial. Historical studies and blocked
availability logs remain untouched. Full interpretation is in
`docs/MODEL_FOLLOWUP_RESULTS.md`; authoritative application metrics are separate.
