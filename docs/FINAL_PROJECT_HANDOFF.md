# Project handoff

24 October 2026 · Capability controls and bounded study preserved; confirmatory program incomplete

## Delivered and preserved

The original [recovery](PROJECT_STATE_RECOVERY.md) and
[28-cell pilot](research/COLAB_PILOT_RESULTS.md) remain intact. Their zero attacks
never established protection because legitimate task performance failed.
PRs [#9](https://github.com/Yug-More/memoryfence/pull/9)–[#14](https://github.com/Yug-More/memoryfence/pull/14)
delivered recovery, durable evidence/scoring, dependency audit, documentation,
Colab execution repair and genuine pilot preservation.

New merged PRs:

- [#15](https://github.com/Yug-More/memoryfence/pull/15): prospective benign gate and
  bounded lifecycle driver.
- [#16](https://github.com/Yug-More/memoryfence/pull/16): literal-task clarification
  with unchanged qualification threshold and fresh seeds.
- [#17](https://github.com/Yug-More/memoryfence/pull/17): explicit transformation
  schema and separate interoperability gate, preserving native defaults/hashes.
- [#18](https://github.com/Yug-More/memoryfence/pull/18): complete qualification,
  diagnostic and native-failure archives with independent analysis and figure.
- [#19](https://github.com/Yug-More/memoryfence/pull/19): opt-in complete action
  contract and a new 12/12 benign gate including empty retrieval.

All four CI checks passed before each merge. PR #18 passed 210 tests on Python
3.12/3.13 at 91.62% combined coverage. Final report/evidence QA supplies subsequent
verification; a document cannot contain its own eventual merge commit hash.

## Genuine empirical status

Two real model artifacts ran: Qwen2.5 0.5B and 1.5B Q4_K_M. Native/schema conditions
and task versions remain separate. Version-1 qualification had 54 valid trials,
with no qualified condition. Twenty-four diagnostic probes had 21 valid failures
and three malformed outputs. Literal qualification had 18 valid trials: 1.5B
passed 9/9; 0.5B passed 3/9. Nine subsequent transformation-schema checks passed.
The [evidence index](../experiments/2026-10-24-completion/index.json) records exact
hashes, revisions, times and per-population counts.

The 80-episode native-transformation study completed with 13 valid and 67 invalid
outcomes. Direct cases include three actual canary ticket effects. DF3 also blocks
clean utility, and DF2-exclude attack output has no valid denominator. Native
transformation failures support no persistence or successful-defense conclusion.
Corrected schema-controlled execution completed 80 episodes: 52 valid, 28 invalid,
11 source-alive canary effects and 21/40 clean completions. DS1 retains canary-bearing
derived memory without observed post-deletion objective execution. DS3 removes
descendants but every corresponding agent reply is invalid. This does not establish
behavioral protection. All raw records and independent analysis are preserved.

## Reproduce and inspect

```bash
uv sync --frozen
make check
make pre-commit
uv run python experiments/2026-10-24-colab/analyze.py
python3 scripts/research/verify.py experiments/2026-10-24-completion/literal-qualification.zip.xz --output /tmp/memoryfence-qualified-analysis.json
```

Use the [bounded-study guide](guides/controlled-study.md) for pinned drivers, free
runtime setup, qualification gates and fresh execution directories. On Colab use
the locked `.venv/bin/python` in subprocesses; do not import 3.12 binary packages
into a 3.13 kernel. Actual runs used archived notebook drivers, not a claimed
unattended Run All of the historical notebook. No model weights were downloaded
onto the Mac or committed. No Drive mount or paid API was used.

Original archives include raw HTTP journals, databases, inputs, evaluator keys,
events, results, checkpoints, exact driver/protocol sources and runtime/model
metadata. XZ preserves ZIP bytes losslessly. The independent standard-library
verifier checks original evidence against actual effects without importing the
production evaluator. It does not attest the server or replace human validation.
Never overwrite historical archives, normalize failed replies into success or
resume completed runs under a different revision.

## Interpretation and remaining work

See the [limited-scope empirical report](research/COMPLETION_REPORT.md),
[integrity audit](FINAL_RESEARCH_INTEGRITY_AUDIT.md) and
[protocol/amendments](research/COMPLETION_PROTOCOL.md). The capable-model issue is
resolved for a narrow literal task, not arbitrary tasks. DF3 requires a literal tool
identifier; its natural-language task rejection is a measured utility limitation,
not a validated discriminating defense.

The original full study still needs representative scenarios/held-outs, semantic
survival and judge validation, human reliability, cached paired transformations,
incomplete-lineage comparisons, broader models/utility, sample-size/statistical
planning, external preregistration and independent replication. The inherited
bibliography has not received a complete new audit. Owner licensing is unresolved.
No release or publication is implied. Next research scope must be declared without
chasing favorable attacks or treating invalid calls as protection.

Local author/committer identity remains `Yug-More <yugmore20@gmail.com>`, without
assistant co-author trailers or rewritten history. GitHub-generated merge records
remain legitimate platform records. Permissions and collaboration settings were
not expanded. Only free Colab CPU, approved weights, local checks and public CI
were used; no billing, paid service or upgrade was enabled.

## Complete-contract stopping gate

The [version-4 amendment](research/ACTION_CONTRACT_AMENDMENT.md) required twelve
exact benign successes, including empty retrieval. The completed condition produced
12 valid replies but only 9 successes: three each in direct, memory and response
families, and zero of three empty-context tasks. All three empty cases refused.
The independent verifier confirms empty raw and stored context and the failed
gate. No contract-controlled security matrix ran. Earlier invalids remain unchanged.
The archive, hash metadata and analysis are in the [evidence inventory](../experiments/2026-10-24-completion/README.md).
This is a concrete remaining capability limitation, not a budget or billing blocker.


## Readiness

**Research pilot complete; full study not yet established.** The software checks,
preserved evidence and bounded report are reviewable. Empty-context capability,
semantic/human validation, broad held-outs and independent replication remain
unresolved. No publication or release readiness is asserted.


## Final local verification snapshot

`UV_CACHE_DIR=/tmp/memoryfence-uv-cache make check` passed with **222 tests** and
**91.57% combined line/branch coverage**, including eight independent saved-evidence
checks. Ruff, formatting, strict mypy, wheel/sdist metadata, citation schema and all
six import contracts passed. `make pre-commit` passed every hook. Both research
scripts also passed explicit strict mypy. PR #19 passed 218 tests and PR #20 passed
219 tests on Python 3.12/3.13, both at 91.57%; four checks passed before each merge.
Final-PR CI validates this final committed scope independently.

All twelve Mermaid diagrams rendered with mermaid-cli 12.0.0. Chromium PNGs were
visually inspected with text present, rather than relying on SVG rasterizers that
omit foreignObject labels. Scientific capability/lifecycle figures and the new
editable provenance SVG were inspected for labels, counts and denominator caveats.
The [Colab screenshot](assets/colab-contract-qualification.png) shows the genuine
completed gate, all three empty-context failures and the decision to stop scaling.
Bounded private-key/Google-key/GitHub-token pattern scans returned no matches in
all seven expanded archives; this is not a universal secret-detection guarantee.
