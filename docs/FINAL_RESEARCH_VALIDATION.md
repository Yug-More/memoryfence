# Final research validation — 8 November 2026

> Current metrics are frozen in [FINAL_PROJECT_METRICS.md](FINAL_PROJECT_METRICS.md).
> This dated8 November snapshot is retained; actual local inference completed on
> 9 November in the separate [model follow-up](MODEL_FOLLOWUP_RESULTS.md).

## Executive assessment and baseline

MemoryFence is an independently inspectable research framework with a bounded
model study, a deterministic lifecycle study and a manuscript in preparation.
It is suitable for skeptical advisor/research review and evidence-qualified
application discussion; broad efficacy, publication readiness and individual sole
ownership are not established. Original and expanded unfavorable results remain.

Remote inspection found PR27 merged, no open PRs, and origin/main at
`1ecdb162e2de60b0522f9d610b638fe6eea8be2b`. Finalization branch:
`codex/final-research-release`. No merge into main is authorized. The user's
preexisting deletion of `paper/memoryfence-paper.pdf` remains unstaged; its
historical committed file and source are preserved. New manuscript is separate.

## Questions and falsifiable expectations

The eight request candidates below map to three narrower manuscript questions:
Q1 lifecycle persistence,Q2 behavioral influence,Q3 security/utility tradeoffs.
These candidate rows are a scope map, not a competing manuscript numbering.

| Request candidate | Answer supported now | Remaining scope |
| --- | --- | --- |
| Candidate 1: post-deletion persistence | Source-only removal leaves derived content; missing recorded links can defeat cascade | Real-world prevalence and long-delay duration |
| Candidate 2: memory architectures | Natural-language and structured representations exist; no matched architecture-wide result | Conversation, vector RAG and key-value causal comparison |
| Candidate 3: lineage deletion | Complete recorded reach removes the tested true descendants | Incorrect links/forged identities/writer compromise |
| Candidate 4: benign information loss | Mixed-source deletion/quarantine loses eligible facts under named conditions | Human semantic utility and representative tasks |
| Candidate 5: reconstruction tradeoff | Existing DS4 recovers complete-lineage fixture facts; containment can equal DS4 or lose utility | Faithful model-written recovery and missing-edge repair |
| Candidate 6: cross-model/retrieval robustness | One historical quantized model, fixed lexical retrieval; no broad generalization | Multiple qualified models/queries/sizes/repeated trials |
| Candidate 7: provenance uncertainty | Honest marked gaps can be withheld; silent clean-root paths can evade detection | Arbitrary missingness or incorrect-but-plausible lineage |
| Candidate 8: model versus simulation | Evidence classes are distinct; no matched new behavioral comparison | New capability-qualified inference; local runtime blocked |

The predeclared Expanded v1 expectations were conditional: source-only need not
remove descendants; complete cascade should invalidate its reachable targets;
surviving-input re-derivation can preserve unrelated facts; marked gaps permit
conservative withholding; silent loss may remain undetectable. Finalization is
reproduction and post-hoc failure/integrity analysis, not a new confirmatory efficacy
trial. No new unblinded held-out dataset is presented as fresh evidence.

## Evidence verification and exact findings

The new [preservation manifest](../experiments/legacy_baseline/expanded-v1-manifest.json)
pins12 prior expanded files, including the benchmark. The existing manifest pins53
original accession/config/dependency files. `verify_release.py` verifies both;
neither `pyproject.toml` nor `uv.lock` changed.

Original raw qualification and state analyses were recomputed again, byte-identical
to historical committed JSON. The final bounded cycle contains72 real responses
(24 qualification,12 transformation,36 final agent), with18 attack episodes at
complete lineage. Exact objective effects0/18; three free-text echoes remain. Three
attack chains have two descendants each:complete cascade removes6/6; nominal
retention0.75 and0.5 leaves4/6 and6/6. Nominal0.5 is not exactly50% realized edges.
The clean TT3 semantic failure and36 extra off-protocol views remain documented.
These supplied-artifact checks are not new model inference or host attestation.
[Historical claim ledger](RESEARCH_CLAIMS.md).

Fresh deterministic execution at `d00fa66b76c6d1466402019f083dd7ed909e0d63`:
**560 completed/560 planned,zero invalid,zero model calls**. All560 semantic records
match the old accession after excluding timing/storage observations. The independent
verifier checks all560 raw new states. Twelve development/four held-out families,
80 counterfactual configurations and seven strategies remain the scientific design;
rerunning it does not produce32 independent families or1120 independent trials.
[New accession and logs](../experiments/2026-11-08-finalization/README.md).

Held-out complete lineage:guarded and unguarded re-derivation both retain8/8 unrelated
facts and4/4 lookups with0/4 exposure, versus cascade2/8 and1/4. Their scored
complete-attack metrics equal across all16 families. Marked gaps:guarded0/4 exposure
but0/8 benign retention. Silent gaps:3/4 exposure,5/11 accessible originals and6/8
benign retention. All11/11 originals physically survive both partial conditions.
Exact-canary filtering gives0/4 exposure but2/8 retention in each attack condition.
No universal superiority is established. [Full results](RESULTS.md),
[all-strategy error analysis](ERROR_ANALYSIS.md).

## Actual model status and reproducible follow-up

Inspected resources: no Ollama executable/reachable loopback runtime, no cached
Hugging Face/Ollama weights, and no torch/transformers/mlx/llama_cpp in the inspected
system interpreter. An installed Hugging Face CLI alone supplies no model.
No credential contents were read or assumed. No paid API, hosted compute upgrade
or model-weight download was used.

New [model-followup-v1](../benchmarks/model-followup-v1/README.md) configuration plans
one already-inspected mixed-source family,five controls,seven strategies,two seeds:
70 probes plus4 qualification chats,cap74. It uses local Ollama task-last complete
contract,temperature0,context2048,output256,timeout120s and the historical Qwen
1.5B digest. Different already-installed models require distinct configurations
and recorded identities. Temperature0 does not guarantee deterministic inference.

The actual frozen-harness preflight is **blocked,error.model_unavailable,zero chat
requests**, with null ASR/effect/utility values. HTTP journal and manifest are saved.
No model qualification or attack probe ran. Transport fixtures exercise gates,
timeouts and sandbox execution as software tests only. The runner is an exploratory
hybrid state-to-action probe, not an LLM memory-generation experiment or a
memory-dependent utility benchmark. It supports fresh output directories and atomic
checkpoints, but not resume or hosted providers. Full raw outputs are researcher-
supplied evidence, not trusted execution attestation.

## Statistical methods and uncertainty

Sixteen fixed structural families with grouped counterfactuals and paired strategies
are the clustering units. Case deltas collapse within family before descriptive
family means/ranges. Exact counts, null empty denominators and timing IQR are
reported. No p-value or independent-binomial CI is applied to560 correlated records,
four fixed held-outs, or18 episodes sharing three attack-chain clusters. These
finite deterministic outcomes have no sampling uncertainty under the fixed program,
but broad external validity remains uncertain. The existing statistical library
contains methods for other designs; availability does not justify using them here.

The failure categorization is explicitly post hoc. Source type is confounded with
family/content; TT labels use the same fact-union semantics. Query, exact canary,
family authorship and primary-excluded answer context limit interpretation. No
human semantic judge, power analysis for new stochastic data or corrected family
of inferential tests was executed. No significance or universal defense ranking.

## Engineering validation and security

Confirmed pre-fix counterexamples:row-count-only summary accepted an unknown strategy;
export followed a benign symlink outside the selected tree. New validators reject
unknown/missing cells, duplicate observations, cohort mismatch, wrong dataset hash,
invalid ratios/NaN, fabricated deterministic behavioral metrics, unsafe scenario
paths and malformed files. CLI returns a domain error. Valid historical summaries
remain equal; raw independent verification still establishes state-derived metrics.
Dataset-less compatibility fixtures receive local grid checks, not a full declared-
dataset identity certificate. Export refuses symlinks; filesystem races remain outside
its guarantee.

Existing identity, ACL/delegation, true/recorded isolation, source lifecycle, sandbox
gateway and transactional tests remain. New fixtures check unavailable models,
failed gates and invalid timeout preservation without scripted fallback. Interrupted
probe output has atomic checkpoints and an incomplete status, but no crash-durability
certification or full-run resume. Future model-probe outcomes also require independent raw
response/effect verification before being promoted to scientific findings. No concurrent-request security guarantee, hostile
Python isolation, unsafe-pickle loading or external tool execution is claimed.

Installed-environment `pip-audit2.9.0` listed61 distributions:60 were audited
against public advisory metadata and one editable project was explicitly skipped.
Zero known vulnerabilities were reported in the60 audited distributions. The first
unsupported-flag invocation and corrected result are both retained. This scan is
neither proof of absence nor a substitute for code review. No pinned dependencies
were silently upgraded.

## Clean installation and test observations

Separate Git checkout `5ca7c2d45ba83334c85fc219f5d287ea8aed6f61` with locked clean
install: **238 passed in27.50s,91.58% coverage**. Separate clean clone of merged
baseline1ecdb16: **266 passed in27.53s,91.64%**. Logs include install/test output.
Final code targeted check:25 passed, including the new grid/export/model tests.
Final integrated results are appended after running the complete current suite.
Tests establish checked software properties; they do not validate scientific efficacy.

## Reproduction commands

From repository root, with fresh output paths:

```bash
uv sync --frozen
uv run --frozen python scripts/research/verify_release.py
uv run --frozen python scripts/research/verify_final.py experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/original-qualification-new.json
uv run --frozen python scripts/research/verify_final.py experiments/2026-10-25-bounded/paired-state-study.zip.xz --qualification-archive experiments/2026-10-25-bounded/final-qualification.zip.xz --output /tmp/original-state-new.json
uv run --frozen memoryfence expanded run --dataset benchmarks/expanded-v1/scenarios.json --directory /tmp/memoryfence-final-new --split all
uv run --frozen memoryfence expanded export --directory /tmp/memoryfence-final-new --output /tmp/memoryfence-final-new.zip.xz
uv run --frozen python scripts/research/analyze_release.py --original experiments/2026-11-07-expanded/expanded-v1.zip.xz --repeated /tmp/memoryfence-final-new.zip.xz --output /tmp/memoryfence-final-comparison-new.json
uv run --frozen python scripts/research/model_followup.py --config benchmarks/model-followup-v1/config.json --directory /tmp/memoryfence-model-new
uv run --frozen python paper/finalization/generate.py
make check
make pre-commit
make diagrams
```

The model command exits2 if blocked or qualification fails; that is not an attack
success rate. Exact metadata and hashes appear in the accession. The paper's
separate [build guide](../paper/finalization/README.md) never writes the old PDF.

## Research paper, README and application readiness

A separate evidence-derived expanded LaTeX manuscript includes verified tables,
measured figures, architecture diagram, threat/method/results/error/ethics sections,
references and reproducibility appendix. Seven primary reference metadata/abstracts
were refreshed on8 November; no new full-text systematic review or acceptance check
is implied. The old manuscript and citation version history remain distinct.
The final PDF is visually checked after compilation; build details are appended.

The README now presents three evidence classes, conditional security–utility results,
strong baseline equivalence, exact reproduction, model blocker and limitations.
[Application summary](GRADUATE_APPLICATION_SUMMARY.md) contains exact75/150/250-word
texts, three résumé candidates, SOP experiences and faculty Q&A. Sole authorship,
individual design/implementation responsibility, supervision and assistance require
personal confirmation. No graduate admission, faculty endorsement, publication or
novelty is inferred from this repository.

## Known defects, unresolved research and readiness

No unresolved measured v1 semantic discrepancy was found. Unresolved scope remains:
new actual inference, multiple models, representative semantic scenarios,150–300
meaningfully distinct configurations, wrong/conflicting edges, partial-source
redaction, long-delay behavior, embeddings, human judgment, model-faithful recovery,
production performance and concurrent action consistency. A true missing branch
can be observationally indistinguishable from a clean graph; this guard does not
solve it. Empty utility denominators, missing observations and invalid runs cannot
be promoted to successes.

The release is a reviewable research package with reproducible bounded evidence,
not a declaration of a secure defense or submission-ready general study. Highest
value next work is a new prospective semantic/model protocol with independent
scenario clusters, capability checks and validated behavioral/utility outcomes.
Preserve this negative result and create new accessions instead of tuning against
these inspected held-outs. Git delivery remains a feature-branch PR only.

## Final integrated verification

Fresh environment `/tmp/mf-final-release-20261108/clean-final-venv` installed from
the unchanged uv.lock. Command prefix: `UV_CACHE_DIR=/tmp/memoryfence-uv-cache
UV_PROJECT_ENVIRONMENT=/tmp/mf-final-release-20261108/clean-final-venv`.
`make check` passed **286 tests,0 failed,0 skipped in42.51s;91.41% coverage**.
Ruff lint/format, strict mypy129 files, wheel/sdist metadata, citation schema and
all six import contracts passed. `make diagrams` rendered all four diagram-bearing
Markdown files. The first integrated pass had285 passed/one documentation-anchor
failure after the README rewrite; the old citation anchor was restored rather than
weakening the test. Both failed and corrected check logs are retained.

Paper: Tectonic0.17.0, generated tables and manuscript-scale plots from the verified
accession;10-page separate PDF, all pages rendered and visually reviewed. Table
spacing, chart readability, duplicate hyperlink anchors and appendix pagination
were corrected before delivery. Final build has no warnings, unresolved references,
missing glyphs or overfull boxes. The optional compiler/plotting tools were isolated
from project dependencies and did not invoke inference or write the old PDF.

`GRADUATE_APPLICATION_SUMMARY.md` sectionsA/B/C were checked at exactly75/150/250
whitespace-separated words. Preservation still verifies53 original and12 expanded
files. Final hygiene output is retained with the new accession; remote CI/PR status
is reported from actual Git delivery rather than assumed by this document.

A final source-validity gate was added atf5a6b19: the model probe refuses any accession
with invalid observations before making qualification requests. Its adversarial
fixture preserves an invalid raw result and confirms zero calls. The final committed
harness was preflighted again:blocked,zero chats,null behavioral outcomes. Both
`model-availability/` (d00fa66) and `model-availability-final/` (f5a6b19) remain in the
accession; neither was overwritten. The last complete suite includes this additional
regression; its exact result follows in the final handoff below.

## Final handoff verification

Last complete `make check` in the fresh locked environment: **287 passed,0 failed,
0 skipped in44.85s;91.41% coverage**; strict mypy129 files and all build/citation/
import checks pass. The earlier286-pass run predates the additional invalid-source
regression. A final documentation-only check also passed81 tests after report
updates. Logs are `logs/final-clean-check-complete.log` and `logs/docs-last.log`
in the new accession. No preexisting test was weakened or historical result edited.

Current code milestones:d00fa66 (declared-grid/export/path hardening and bounded
model probe),f5a6b19 (invalid source gate). The subsequent evidence/manuscript commit
is identified in the final Git handoff. Required author and committer identity is
Yug-More <yugmore20@gmail.com>; no AI co-author trailer or contributor was added.
The feature branch is pushed for PR review only; actual remote CI status and URL
are reported after delivery, with no default-branch merge.

All final hygiene hooks passed, including large-file/private-key checks, whitespace,
Ruff, strict types, citation and workflow schemas. Final source/evidence paths are
listed in `experiments/2026-11-08-finalization/release-manifest.json`; this checksum
inventory is not a trusted-execution attestation or publication claim.
