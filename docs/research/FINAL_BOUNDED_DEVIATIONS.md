# Final bounded study deviations

25 October 2026. This log preserves departures from the prospective
[protocol](FINAL_BOUNDED_PROTOCOL.md), rather than changing the original declaration.

## Unplanned zero-provenance views

During execution at `e5dcc3c61cc6ded130a4f118825fc324e90a7e3a`, inspection of the
clean-901/clean-902 checkpoints showed LF0.0 views. The driver iterated the complete
`LineageFidelity` enum, which contains LF0.0 as well as the three declared levels.
The method's fixture tests had checked branch behavior but had not run the full
matrix. This is a runner defect, not an intentional design change.

The pinned execution is retained unchanged. The additional LF0.0 observations use
the same cached generated text and make **no additional model calls**. Preserve all
144 actual state views if execution completes: 108 at the declared levels and 36
unplanned LF0.0 views. Report and verify the latter separately as exploratory;
never describe them as prospectively declared or silently discard them. The cap
of 24 qualification + 12 transformation + 36 conditional agent calls is unchanged.
Discovery occurred before the attack-chain stage, from clean-run checkpoints.

The current driver explicitly lists LF1.0/LF0.75/LF0.5. A complete fixture-run
regression checks 108 state views, 36 agent calls and only 12 uncached transformation
calls. Do not rerun or replace the original execution to hide this departure.
Reproducing the archived execution requires its pinned revision; current code
reproduces the intended three-level design instead.
