"""Recorded provenance: the only lineage the system under test and defenses can read.

This package never imports :mod:`memoryfence.groundtruth` (enforced by import-linter).
"""

from memoryfence.provenance.degradation import component_seed, edge_uniform, retains_edge
from memoryfence.provenance.graph import descendants, topological_order
from memoryfence.provenance.recorded import RecordedProvenanceReader, RecordedProvenanceWriter

__all__ = [
    "RecordedProvenanceReader",
    "RecordedProvenanceWriter",
    "component_seed",
    "descendants",
    "edge_uniform",
    "retains_edge",
    "topological_order",
]
