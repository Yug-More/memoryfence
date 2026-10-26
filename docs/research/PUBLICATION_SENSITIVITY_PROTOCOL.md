# Finite mechanical sensitivity protocol

Declared before execution in the publication pass (25 October 2026).
Exhaustively enumerate every retained-edge mask for linear chains with 1, 2, 4
and 8 derived nodes: 2 + 4 + 16 + 256 = 278 graph configurations. These are
abstract deterministic graphs, not generated memories, model calls, SQLite
end-to-end experiments or representative production samples. No random seed is
needed because enumeration is exhaustive. Use the production `descendants`
graph traversal; independently compare reach with the closed-form contiguous
retained prefix from the source. Preserve every mask and reached/surviving IDs.

Compare source-only retention with cascade reach. For a uniformly enumerated
mask, group by depth and number of retained edges; equal edge counts can have
different reach when missing positions differ. This weighting is a mathematical
sensitivity device, not a missingness prevalence estimate. Stop after all 278
configurations. Do not make behavioral or DF2 efficacy claims from this exercise.
The existing genuine archives remain the evidence for text, retrieval and behavior.
