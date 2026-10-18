"""Evaluator-only ground truth: true provenance, source labels, the deletion ledger, and
run manifests. The system under test reaches it only through the write-only recorder."""

from memoryfence.groundtruth.episode import open_episode
from memoryfence.groundtruth.recorder import SqlGroundTruthRecorder
from memoryfence.groundtruth.store import GroundTruthReader, GroundTruthStore, SourceLabel

__all__ = [
    "GroundTruthReader",
    "GroundTruthStore",
    "SourceLabel",
    "SqlGroundTruthRecorder",
    "open_episode",
]
