# Development Guide

This guide covers local setup, the quality checks that CI enforces, and repository conventions.

## Prerequisites

- **Git**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** 0.9 or newer. uv manages the Python interpreter, the virtual environment, and the lockfile.
- **GNU Make**, optional but convenient. Every Make target is a thin wrapper around the command shown below.
- **Node.js** 20 or newer, only for `make diagrams`.

You do not need to install Python separately. `.python-version` pins the local interpreter to 3.12, the minimum supported version, and uv downloads it if needed. CI also tests Python 3.13.

## Setup

```bash
git clone https://github.com/Yug-More/memoryfence.git
cd memoryfence
make setup
```

`make setup` runs:

```bash
uv sync --frozen                 # create .venv from uv.lock without re-resolving
uv run --frozen pre-commit install
```

`--frozen` guarantees that the environment matches the committed `uv.lock` exactly.

## Make targets

| Target | Underlying command | Purpose |
|---|---|---|
| `make setup` | `uv sync --frozen`, then `pre-commit install` | Create the environment and install git hooks |
| `make lint` | `uv run --frozen ruff check .` | Lint rules |
| `make format` | `ruff format .`, then `ruff check --fix .` | Apply formatting and safe fixes |
| `make format-check` | `uv run --frozen ruff format --check .` | Verify formatting without changing files |
| `make typecheck` | `uv run --frozen mypy` | Strict type checking of `src/` and `tests/` |
| `make test` | `uv run --frozen pytest` | Run the test suite |
| `make coverage` | `uv run --frozen pytest --cov --cov-report=term-missing` | Tests with branch coverage; fails below 90% |
| `make build` | `uv build`, then `twine check --strict dist/*` | Build the sdist and wheel and validate their metadata |
| `make citation` | `check-jsonschema --builtin-schema vendor.citation-file-format CITATION.cff` | Validate citation metadata |
| `make contracts` | `uv run --frozen lint-imports` | Forbid `domain` from importing other internal modules, and forbid the system under test from importing `groundtruth` or `benchmark` |
| `make check` | `lint`, `format-check`, `typecheck`, `coverage`, `build`, `citation`, `contracts` | **Everything the CI quality job runs** |
| `make pre-commit` | `uv run --frozen pre-commit run --all-files` | Repository hygiene hooks |
| `make diagrams` | `npx @mermaid-js/mermaid-cli@12.0.0` on every Markdown file containing Mermaid | Render-check all diagrams into `.diagrams/` |
| `make clean` | — | Remove caches and build artifacts |

Run `make help` for the list with descriptions.

## What the checks cover in Phase 1

| Check | What it verifies |
|---|---|
| `tests/test_package.py` | The package imports; `memoryfence.__version__` matches the installed metadata and `pyproject.toml`; `__all__` is explicit; the `py.typed` marker ships; the runtime dependencies are exactly Pydantic and SQLAlchemy |
| `tests/test_docs.py` | Required documents exist and are non-empty; every relative Markdown link and heading anchor resolves; condition codes used in the research documents are defined in the protocol; the architecture overview contains the required diagrams |
| `tests/test_authorization.py`, `tests/test_lifecycle.py`, `tests/test_provenance.py`, `tests/test_persistence.py` | Authorization, deletion policies, provenance isolation and degradation, and SQLite transactions |
| `tests/test_imports.py` | The import-linter contracts |
| Ruff | Style, import order, common bugs, naming, annotations, and security lint rules (flake8-bandit) |
| mypy `--strict` | Complete type annotations and no implicit `Any` |
| `make build` | The package builds as sdist and wheel, and its metadata passes `twine check --strict` |
| `make citation` | `CITATION.cff` conforms to the Citation File Format 1.2.0 schema |
| pre-commit | Whitespace, end-of-file newlines, YAML and TOML syntax, merge-conflict markers, large files, private keys, Ruff, mypy, citation schema, workflow schema |
| `make diagrams` | Every Mermaid block in the README and `docs/` renders without syntax errors |

Phase 2 tests exercise the authorization boundary, provenance split, and database transactions directly. Phase 3 adds scripted ingestion, transformations, retrieval, DS4 execution, sandbox tools, and `tests/test_demo.py`. Phase 4 adds `tests/test_benchmark.py`: the scenario catalog, separate stage labels, deletion and fidelity sweeps, replay, and the benchmark CLI. Those tests do not call an external model.

## Offline demo

After `make setup`:

```bash
uv run memoryfence demo --directory /tmp/memoryfence-demo
```

The command creates `system.sqlite` and `groundtruth.sqlite` in that directory and prints one canonical JSON trace. Two runs with the same code produce the same trace. The summary text is a named fixture (`demo-tt1`), not a generated summary. One proposed tool is executed. One proposed tool is denied by the sandbox allowlist after authorization records the proposal.

## Scripted benchmark

```bash
uv run memoryfence benchmark list
uv run memoryfence benchmark validate
uv run memoryfence benchmark run --scenario direct-note --directory /tmp/memoryfence-direct
uv run memoryfence benchmark replay --directory /tmp/memoryfence-direct --into /tmp/memoryfence-direct-replay
uv run memoryfence benchmark inspect --directory /tmp/memoryfence-direct
uv run memoryfence benchmark export --directory /tmp/memoryfence-direct
```

`run` refuses an existing directory. Optional `--policy`, `--fidelity`, and `--marked` override the scenario's deletion and provenance settings. `replay` reruns the saved scenario into a fresh directory and prints whether the canonical outcome matches. Comparison ignores the trace path, the code version, and retrieval latency.

The catalog has eighteen versioned fixtures. Families A–H cover a direct note, summary, merge, multi-round derivation, post-deletion retrieval, cross-user visibility, an unauthorized proposal, and an executed sandbox tool. Protocol families are `SF1`–`SF5`. Controls are `C-CLEAN`, `C-RAW`, `C-NULL`, `C-PREDEL`, `C-LEGIT`, `C-SELF`, and `C-UCC`. Scoring records four separate booleans: S1 Retrieved, S2 Followed, S3 Proposed, and S4 Executed. A failed scripted call stores `stages: null` and a failure reason. Public scenario objects and exported results omit source origins and the followed-instruction marker. Those stay in the evaluator. A stage label from this runner is a fixture result, not an attack rate.

### Defense conditions

```bash
uv run memoryfence benchmark run \
  --scenario direct-note --defense DF2 --retrieval exclude \
  --directory /tmp/memoryfence-df2
uv run memoryfence benchmark run \
  --scenario executed-proposal --defense DF3 \
  --directory /tmp/memoryfence-df3
uv run memoryfence benchmark run \
  --scenario executed-proposal --defense DF3 --policy-source oracle \
  --oracle-tool create_ticket --directory /tmp/memoryfence-oracle
```

`DF0` is the platform ACL with no extra defense. `DF1` delimits retrieved text and labels recorded authors. `DF2-label` annotates those authors. `DF2-exclude` drops a memory when any recorded author is neither the requester nor a user with instruction authority over the requester. `DF3` allows a standing sandbox tool only when the task text names it and every argument token appears in the task. The oracle source is an injected tool list and is not the main result. `DF4` applies `DF2` and `DF3` together. `DF5` blocks a tool at or above the risk threshold when retrieved context has an untrusted recorded author. Missing recorded edges are not filled from true provenance. The scripted backend does not read the delimited prompt, so `DF1` does not change its tool call.

Retrieval ranks memories by the count of shared case-folded alphanumeric tokens, breaks ties by memory identifier, drops a zero score, and returns at most `top_k` memories the principal may read. `TT0` is retrieval of a primary memory with no transformation. `TT1` through `TT4` ask the scripted backend for an explicit reply and store that text. Prompt version strings such as `tt1-scripted-v1` name the fixture, not a model prompt that was sent anywhere.

### Mermaid diagrams

GitHub renders Mermaid natively, and CI render-checks every diagram with `make diagrams`. Run it locally before changing a diagram. The first run downloads mermaid-cli and a headless browser, so it needs network access. The rendered output goes to the git-ignored `.diagrams/` directory.

## Dependency management

- Add a development dependency with `uv add --dev <package>`. Add a runtime dependency with `uv add <package>` **only** together with the code that uses it, and justify it in the pull request.
- Commit `pyproject.toml` and `uv.lock` together.
- To upgrade, run `uv lock --upgrade-package <package>` and review the diff.
- To update pre-commit hook revisions, run `uv run pre-commit autoupdate`. Keep the Ruff hook version consistent with the Ruff version in `uv.lock`.

## Continuous integration

`.github/workflows/ci.yml` runs on every pull request and on pushes to `main`:

- **quality** (Python 3.12 and 3.13): `uv sync --frozen`, Ruff lint, Ruff format check, mypy, pytest with coverage, package build and metadata check, citation validation;
- **hygiene**: all pre-commit hooks against all files;
- **diagrams**: render-check of every Mermaid diagram.

Third-party actions are pinned to full commit SHAs, with the version noted in a comment. The workflow token has read-only `contents` permission, checkout does not persist credentials, and every job has a timeout.

## Environment variables

Phase 1 reads no environment variables. [`.env.example`](../.env.example) documents the variables planned for later phases. Copy it to `.env` (which is git-ignored) for local use, and never commit real values.

## Conventions

- **Layout:** `src/memoryfence/` for the package, `tests/` mirroring package modules, and `docs/` for research and architecture.
- **Modules** are created only when they contain working, tested code. Planned modules are documented in [`architecture/overview.md`](architecture/overview.md#6-modules), not scaffolded as empty files.
- **Import contracts** in the architecture overview are binding from Phase 2 and will be checked in CI.
- **Commits** follow Conventional Commits (see [`CONTRIBUTING.md`](../CONTRIBUTING.md)).
- **Architecture decisions** are recorded as ADRs in [`architecture/decisions/`](architecture/decisions/).
