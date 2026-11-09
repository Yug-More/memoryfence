# MemoryFence

**Provenance-aware deletion and reconstruction for persistent AI-agent memory.**

MemoryFence studies whether lower-trust instructions survive source deletion and
how memory policies trade contamination reduction against benign information loss.
It combines controlled memory-state experiments with bounded local model evaluation.

> Under what conditions can attacker-origin instructions persist in derived AI memories after transformations or original-source deletion, and how do deletion handling, provenance completeness, and defense mechanisms influence unauthorized downstream agent behavior?

[![CI](https://github.com/Yug-More/memoryfence/actions/workflows/ci.yml/badge.svg)](https://github.com/Yug-More/memoryfence/actions/workflows/ci.yml)

## Key contributions

- **Two provenance graphs:** operational controls use recorded lineage; evaluator
  truth measures missed descendants without providing an oracle to defenses.
- **Paired policy evaluation:** seven strategies compare source deletion, direct and
  transitive invalidation, filtering, quarantine and selective reconstruction.
- **Security–utility measurement:** distinguish retained content, retrieved context,
  exact model proposals, sandbox effects and unrelated fact retention.
- **Reproducible evidence:** raw SQLite states, model journals, fixed configurations,
  independent verifiers and adversarial evidence-integrity tests.

## System architecture and threat model

![Memory lifecycle and authorization boundary](docs/assets/memory-lifecycle.svg)

A typed Python/Pydantic/SQLAlchemy framework stores operational state and evaluator
truth in separate SQLite databases. Source revisions and derived-memory DAGs support
lexical ACL retrieval, deletion, reconstruction and auditable lifecycle transitions.
A gateway authorizes structured proposals before local sandbox effects.

The attacker controls synthetic lower-trust content, not trusted tasks, identities,
permissions or protected databases. The defender knows recorded provenance and
source lifecycle. Honest incompleteness flags are observable; silently missing
branches can evade that evidence. [Architecture](docs/ARCHITECTURE.md) ·
[Threat model](docs/THREAT_MODEL.md).

## Experiments and verified findings

| Study | Scale | Findings |
| --- | --- | --- |
| Historical bounded model study | 72 responses, including 36 final agent replies/18 attack episodes | Cascade retained 4/6–6/6 malicious descendants under nominal partial lineage; final exact attacker effects 0/18 at complete lineage |
| Deterministic memory benchmark | 16 families, 80 configurations, 7 strategies, 560 paired runs | Complete reconstruction retained 8/8 held-out benign facts versus cascade's 2/8; marked containment lost 8/8; silent exposure 3/4 |
| Local model follow-up, 9 November | 4 qualification +70 actual Qwen2.5 1.5B probes | Gate 4/4; valid probes 70/70; literal legitimate effects 70/70; predefined attacker proposals/effects 0/42 |

The deterministic benchmark holds out four entire graph families and pairs each
strategy on identical state. The exploratory local model follow-up uses one
already-inspected family, five controls and two seeds, with frozen deterministic
memory contexts. Every strategy completed 10/10 literal tasks with 0/6 exact attack
effects; this provides no behavioral defense ranking.

![Measured security–utility tradeoff](experiments/2026-11-07-expanded/derived/heldout-security-utility.svg)

[Full state results](docs/RESULTS.md) · [Actual model results](docs/MODEL_FOLLOWUP_RESULTS.md)
· [Failure analysis](docs/ERROR_ANALYSIS.md) · [Authoritative frozen metrics](docs/FINAL_PROJECT_METRICS.md).

## Install and reproduce

Requires Git, Python 3.12+ and [uv](https://docs.astral.sh/uv/). Use fresh output paths.

```bash
uv sync --frozen
uv run --frozen python scripts/research/verify_release.py
uv run --frozen python scripts/research/verify_expanded.py experiments/2026-11-07-expanded/expanded-v1.zip.xz --output /tmp/expanded-verified-new.json
uv run --frozen memoryfence expanded run --dataset benchmarks/expanded-v1/scenarios.json --directory /tmp/expanded-run-new --split all
```

These commands require no model. For actual inference, install an explicitly free
local Ollama runtime and the pinned model, then run the bounded configuration:

```bash
uv run --frozen python scripts/research/model_followup.py --config benchmarks/model-followup-v1/config.json --directory /tmp/model-followup-new
```

The runner checks identity, enforces its 74-chat cap and requires capability
qualification before attack probes. It preserves raw failures and has no paid or
scripted fallback. Substantial local downloads require available disk/RAM and owner
approval. [Model protocol](benchmarks/model-followup-v1/README.md) ·
[Complete reproduction guide](docs/REPRODUCIBILITY.md).

## Run checks

```bash
make check
make pre-commit
make diagrams
```

CI checks Python 3.12/3.13, strict types, coverage, distributions, import boundaries,
repository hygiene, diagrams and saved evidence. It makes no inference requests.

## Research manuscript and documentation

- [Preserved 10-page LaTeX/PDF manuscript](paper/finalization/README.md) and
  [dated model follow-up addendum](docs/MODEL_FOLLOWUP_RESULTS.md).
- [Frozen application metrics and résumé/SOP text](docs/FINAL_PROJECT_METRICS.md).
- [Research audit](docs/RESEARCH_AUDIT.md), [methodology](docs/EXPERIMENTAL_METHODOLOGY.md),
  [historical claim ledger](docs/RESEARCH_CLAIMS.md), [validation](docs/FINAL_RESEARCH_VALIDATION.md).

## Evaluation scope and limitations

Studies use fixed synthetic scenarios and exact objectives. The 560 deterministic
runs are not model trials; the 42 new attack observations share one family and
repeated conditions. Counts and paired family summaries do not justify independent-
binomial significance claims. The local task is literal, not memory-dependent
utility; its contexts are deterministic fact projection, not model-written summaries.
Complete-lineage guarded reconstruction equals existing re-derivation on scored
metrics, while marked containment and silent lineage loss retain their unfavorable
results. Multiple models, semantic utility, incorrect lineage, long delays and
concurrency guarantees remain open. Operational deletion retains research journals;
it is not model-weight unlearning or forensic erasure. The manuscript is in
preparation, with no publication or general security guarantee claimed.
[Detailed limitations](docs/LIMITATIONS.md).

## Repository structure

```text
src/memoryfence/   Operational memory, provenance, authorization, evaluator and CLI
benchmarks/       Frozen structural cases and bounded model configuration
experiments/      Preserved archives, raw evidence, analysis and validation logs
scripts/research/ Experiment drivers, independent verifiers and plotting scripts
paper/            Original and expanded manuscript sources and generated figures
docs/             Methods, findings, frozen metrics and application material
tests/            Unit, integration, adversarial and saved-evidence checks
```

## Citation and licensing

[Citation metadata](CITATION.cff) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md).
Legitimate historical attribution remains in Git. Individual research responsibility,
collaboration and supervision require the applicant's confirmation; commit names do
not prove sole ownership. No project license has been selected, so public access
does not imply unrestricted reuse. Model/runtime license references are recorded
with their accession.
