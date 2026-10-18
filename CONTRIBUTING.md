# Contributing to MemoryFence

Thank you for your interest. MemoryFence is a research project, so contributions are held to standards of **research integrity** as well as code quality.

> [!NOTE]
> **Licensing status: not granted.** The repository does not yet have a license (see the [README](README.md#citation-and-licensing)). Until the owner adds one, external code contributions cannot be accepted, because their terms would be undefined. Issues, discussion, and review comments are welcome now.

## Ground rules

1. **No unsupported claims.** Do not add experimental results, statistics, benchmarks, test counts, or performance figures unless they come from committed code and configuration in this repository and can be regenerated.
2. **Verify citations.** Check every new reference against its original source (arXiv, DOI, or publisher page). Record its review depth as in [`literature-review.md`](docs/research/literature-review.md#13-review-depth), and mark anything you could not verify.
3. **Planned is not implemented.** Documentation must distinguish planned components from implemented ones. Diagrams use the *planned* style until the component exists and is tested.
4. **Protect ground truth.** Code in the system under test, including defenses, must never read true provenance, attack labels, or the deletion ledger (see the [security invariants](docs/architecture/overview.md#5-security-invariants)).
5. **Protect the evaluation split.** Do not tune attacks, defenses, prompts, or thresholds on evaluation-split data (see [`experimental-protocol.md`](docs/research/experimental-protocol.md#11-data-separation)).
6. **Responsible use.** Payloads must be synthetic, inert, and limited to the simulated sandbox. Never target real services or people. See [`SECURITY.md`](SECURITY.md).
7. **Accurate authorship.** Commits must carry the real author's identity. Do not add tool-generated attribution trailers, watermarks, or badges.

## Development workflow

1. Set up the environment as described in [`docs/development.md`](docs/development.md).
2. Create a branch from `main` named by type, for example `feat/provenance-graph`, `fix/acl-check`, `docs/threat-model`, or `chore/tooling`.
3. Make small, focused commits using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new functionality
   - `fix:` bug fix
   - `docs:` documentation only
   - `test:` tests only
   - `refactor:` behavior-preserving change
   - `chore:` tooling and maintenance
   - `ci:` continuous integration
4. Run `make check` and `make pre-commit` locally, and `make diagrams` if you changed a diagram. All must pass.
5. Open a pull request using the template and fill in every section truthfully, including the commands you ran and their actual results.

## Code standards

- Python 3.12+, fully type-annotated, passing `mypy --strict`.
- Ruff-formatted and lint-clean under the project configuration.
- Small modules with a single responsibility that respect the [import contracts](docs/architecture/overview.md#62-import-contracts). In particular, `defenses` must never import `attacks`, `evaluation`, or `groundtruth`.
- No placeholder implementations presented as complete, and no empty modules created ahead of the phase that implements them.
- Errors are explicit: raise specific exceptions with actionable messages, and never silently swallow failures.
- No secrets in code, tests, fixtures, or logs. Configuration comes from environment variables (see `.env.example`).
- Every new runtime dependency must be justified in the pull request.

## Tests

- New behavior requires tests. Branch coverage must stay at or above 90%.
- Tests must not call paid APIs or the network. Use the deterministic model backend once it exists.
- Prefer deterministic tests, and seed any randomness explicitly.

## Architecture changes

Significant design changes need an Architecture Decision Record in `docs/architecture/decisions/`, numbered sequentially (`ADR-0002-...`). An ADR that changes an earlier decision must state which ADR it supersedes.

## Changes to the research design

Changes to hypotheses, factors, metrics, controls, or the data split must update the relevant document under `docs/research/`, add an entry to the protocol change log, and explain the reason in the pull request. After preregistration, such changes are recorded in a deviations log, and the affected analyses become exploratory.
