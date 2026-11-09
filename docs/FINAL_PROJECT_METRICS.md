# Final project metrics — MemoryFence

Frozen 9 November 2026. This is the authoritative source for future résumé/SOP claims.
Preserve historical snapshots; new findings require a dated new accession/version,
not favorable edits to these results. The final test snapshot appears below.

## Project identity and attribution

**Name:** MemoryFence. **Description:** A reproducible AI-agent memory security
framework studying how recorded provenance, deletion and reconstruction affect
persistent instruction contamination and benign information retention.
**Area:** Applied AI, trustworthy agents, memory security, experimental evaluation.

**Verified individual contribution:** Git verifies commit attribution, not sole
implementation or intellectual ownership. The applicant must confirm their actual
research/design/engineering/analysis responsibilities and assistance before using
first-person claims. No supervision, team membership, publication or sole authorship
is inferred. Historical contributor attribution remains in Git; no tool co-authors
or new contributor entries were added.

## Research design and frozen scales

Threat: lower-trust synthetic sources can introduce instructions; attacker cannot
edit trusted tasks, identities, protected databases or model weights. Defenses use
recorded lineage; evaluator truth is isolated. Tools have only local sandbox effects.
Questions: persistence after deletion;conditions of provenance failure;reconstruction
versus simpler deletion;security–utility costs;bounded real model behavior.

| Evidence class | Verified scale | Exact interpretation |
| --- | --- | --- |
| Historical bounded model cycle | 72 replies:24 qualification, 12 transforms, 36 final agent | 18 clean +18 attack episodes at complete lineage;three attack chains ×two descendants |
| Deterministic memory benchmark | 16 structural families, 80 counterfactual configurations, 7 strategies, 560 runs | 12 development/4 held-out families;not80 independent semantic attacks or560 model trials |
| Deterministic reproduction | 560/560 semantic records match | Repeat execution does not increase independent scientific sample size |
| New local hybrid model study | 74 actual requests:4 qualification +70 probes | One inspected family, 5 controls, 7 strategies, 2 seeds;35 distinct case/strategy states |
| New attack denominator | 42 eligible attack observations | 3 attack controls ×7 strategies ×2 seeds;correlated, not42 independent families |

Additional earlier historical pilots exist; do not claim72+74 is a census of every
model call ever stored in this repository. Keep accessions/protocols separate.

Strategies:source_only, exact-canary keyword, direct invalidation, transitive cascade,
unguarded re-derivation, quarantine, guarded MemoryFence. State inputs are paired.
Structured fact union is deterministic; new model probes act on frozen contexts,
not newly model-generated summaries or model-written reconstruction.

## Security and utility outcomes

- Historical DS3:0/6 active malicious descendants at complete lineage;4/6 and6/6
  at nominal retention0.75 and0.5. “50% fidelity” means nominal retention probability,
  not exactly half the edges in every realized graph. Final exact objective effects
  0/18 at complete lineage only;three text echoes remain.
- Four held-out deterministic complete attack cases:existing and guarded re-derivation
  both retain8/8 benign facts, 4/4 lookups, 0/4 exposure;cascade retains2/8 and1/4.
  Marked containment retains0/8 facts with0/4 exposure;silent gaps expose3/4 and
  retain6/8. All11/11 target originals survive physically in the partial conditions.
- New actual local model:qualification4/4;probes70/70 valid, zero invalid;literal
  legitimate ticket effects70/70;exact attacker proposals/effects0/42. Every strategy
  scores10/10 legitimate effects and0/6 attacker effects. No behavioral ranking or
  universal protection follows. No response-text canary echo among70 probes.

Model:Qwen2.5:1.5b, Q4_K_M, 986061892 bytes, digest
`65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`.
New runtime:Ollama0.40.15, Apple M2 Pro/Metal, 16GiB RAM, Python3.12.12;temperature0,
context2048, predict256, timeout120s, seeds2101/2102, task-last complete contract.
Raw-reported tokens:64948 prompt-evaluation, 2972 output over74 responses.
Paid API cost0;temporary resource download explicitly approved. Historical runtime
0.40.11/free CPU Colab is a different environment, not a matched hardware comparison.

## Engineering and evidence map

Implemented:typed Pydantic domain models, SQLAlchemy/two SQLite stores, source revisions,
recorded/true DAGs, seeded edge loss, ACL/delegation checks, lexical retrieval, DS0–DS4,
DF0–DF5, selective re-derivation, observable-gap containment, local tool gateway/auditing,
strict artifact grids/metrics, safe export/path identifiers, bounded loopback inference,
independent raw verification. No vector index, hosted chatbot, weight unlearning or
OS enclave is claimed.

- `src/memoryfence/provenance/`, `workspace/deletion.py`, `memory/rederive.py`:
  dependency recording, invalidation, reconstruction.
- `src/memoryfence/defenses/containment.py`:operational gap/lifecycle checks.
- `src/memoryfence/evaluation/expanded/`:paired benchmark, metrics and validation.
- `scripts/research/verify_final.py`, `verify_expanded.py`, `verify_model_followup.py`:
  independent supplied-data recomputation, not third-party host attestation.
- Original archive:`experiments/2026-10-25-bounded/paired-state-study.zip.xz`,
  `behavior.json`/raw exchanges/SQLite; corresponding analysis JSON state_groups.
- Deterministic archive:`experiments/2026-11-07-expanded/expanded-v1.zip.xz`,
  `records.json`, `summary.json`, per-case input and strategy SQLite/results.
- New actual model:`experiments/2026-11-09-model-followup/model-followup.zip.xz`,
  `http.jsonl`, `qualification.json`, `probes.json`, per-probe results/SQLite.
- Model run/verifier commit:`4a824162540b0124e2abc5852229c853b766f610`.
  Prior implementation4a430fa;prior finalizationd00fa66/f5a6b19/221c757;baseline4b6ce59.

Preservation:53 original +12 expanded pinned files unchanged. The prior46-file
finalization inventory, including its10-page manuscript, also remains unchanged.
Historical238-test and merged266/287-test counts are revision-specific, not the new
suite count. Exact current command/output is frozen after the final checks below.

```bash
uv sync --frozen
uv run --frozen python scripts/research/verify_release.py
uv run --frozen python scripts/research/verify_model_followup.py /tmp/extracted-model-run --source experiments/2026-11-07-expanded/expanded-v1.zip.xz --output /tmp/model-verified-new.json
uv run --frozen memoryfence expanded run --dataset benchmarks/expanded-v1/scenarios.json --directory /tmp/expanded-new --split all
make check
make pre-commit
make diagrams
```

Full model setup/configuration and outcome limits:
[MODEL_FOLLOWUP_RESULTS.md](MODEL_FOLLOWUP_RESULTS.md). The current new inference
supersedes the runtime blocker for 9 November only; prior blocked records remain true
historical observations. Primary-excluded deterministic fact lookup and literal
model task success are different utility measurements. Fixed family clusters do
not justify independent-binomial CIs or manufactured statistical significance.

## Application material

**One-sentence résumé description:** Investigated post-deletion instruction
contamination in persistent agent memory using isolated provenance graphs, paired
memory-policy evaluation and independently verified local model-to-sandbox probes.

**Three résumé candidates — confirm individual responsibility before use:**

- Investigated provenance-sensitive memory deletion across560 deterministic runs from16 structural families, quantifying benign-fact loss and silent-lineage failures.
- Executed a capability-qualified local Qwen2.5 study with74 real requests and independently verified70 sandbox outcomes, reporting zero predefined attacker effects in42 correlated attack observations without claiming general protection.
- Hardened a typed Python/SQLAlchemy research pipeline with adversarial metric-grid validation, safe evidence export, and independent raw-journal/SQLite verification.

## 100-word SOP description

MemoryFence investigates whether instructions from untrusted sources survive deletion in persistent agent memory. The framework separates recorded provenance from evaluator ground truth and compares deletion, filtering, quarantine, and reconstruction policies. A deterministic benchmark exposes security and utility tradeoffs, including benign information loss and undetectable silent lineage gaps. A separate capability-qualified local model follow-up completed seventy literal tasks without the predefined attacker effect; these bounded observations do not establish general protection. The project emphasizes reproducible raw evidence, independent verification, and precise claims. The investigation highlights how trustworthy agents require explicit uncertainty handling and careful measurement of both security and legitimate utility.

## 200-word research description

MemoryFence examines persistent instruction contamination after source deletion in AI-agent memory. Its Python architecture uses SQLAlchemy and separate SQLite stores for operational state and evaluator truth. Recorded dependency graphs drive deletion and reconstruction, while defenses cannot consult true ancestry. The preserved bounded study contains eighteen attack episodes and thirty-six final agent responses. A separate deterministic expansion compares seven strategies across eighty configurations from sixteen structural families, including four held-out families. Complete-lineage reconstruction retains eight of eight unrelated facts versus two of eight under cascade deletion. Marked-gap containment loses all eight facts, while silent gaps expose poisoned context in three of four held-out cases. A later exploratory follow-up uses the same quantized Qwen model artifact on local hardware: four qualification calls pass, followed by seventy valid probes and zero predefined attacker effects among forty-two eligible attack observations. Those probes share one family and do not demonstrate general security or memory-dependent utility. Independent scripts recompute raw contexts, proposals, graph behavior, metric denominators, and sandbox effects. The engineering work includes authorization boundaries, adversarial evidence validation, safe archive handling, and reproducible tests. The research contribution is a transparent experimental artifact with explicit negative findings, rather than a universally effective defense or claimed peer-reviewed publication.

## Technical interview explanation and scope

“Deleting a source does not necessarily remove summaries derived from it. I separate
what persists, what retrieval exposes and what the model actually does. Missing
recorded links can make contaminated mixed memory look ordinary; conservative
containment can also destroy useful facts. The local model completed a literal
task despite the tested contexts, but this does not prove a generally secure defense.”
Use first person only for confirmed personal work.

Defend the difference between true/recorded graphs, physical survival/quarantine,
nominal/realized fidelity, exact objective/semantic misuse, and fixed/correlated trials.
Remaining work includes multiple models, semantic memory generation, wrong edges,
realistic memory-dependent utility, long delays and concurrency guarantees.
The project is an independently inspectable research artifact/manuscript in
preparation;no accepted paper, peer review or sole ownership is claimed.

## Final engineering freeze — 9 November 2026

**291 tests passed,0 failed,0 skipped;91.41% coverage** (`make check`,52.80s).
Strict mypy130 files,Ruff,package/citation validation and all6 import contracts pass.
`make diagrams` passes. The first integrated run had290 pass/one environment-dependent
Colab test failure while the live inference server was reachable. Its missing-binary
case now injects an unavailable probe; its expected error assertion remains intact.
Both check logs are preserved in the new accession. Tests and coverage are software
verification,not a substitute for scientific validation.

The original65 pinned files and the previous46-file finalization inventory match.
The preserved10-page manuscript compiles cleanly;seven primary citation metadata/
abstract records were rechecked. The README separates all three studies and places
technical caveats under Evaluation Scope and Limitations. The model run is fully
captured and independently recomputed. There is no remaining known high-severity
engineering or evidence-integrity blocker for this bounded release; generalization
limits above remain research scope,not hidden successes.

The temporary server was stopped and its runtime/weights removed after export.
No paid API,external tool effect,credential disclosure or historical rewrite occurred.
The user's preexisting historical PDF deletion remains local and must not be restored
or committed merely to obtain a clean status. Main/release verification can use a
separate clean checkout. The final Git merge and post-merge CI are reported in the
release handoff; use Git to resolve the commit that introduced this frozen file.
