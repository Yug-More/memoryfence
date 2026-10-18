"""Offline episode entry points.

This package opens both databases, so it is harness code. The agent, retrieval,
transformation, and sandbox packages do not import it and do not import ground truth.
"""

from memoryfence.harness.episode import DemoTrace, run_demo

__all__ = ["DemoTrace", "run_demo"]
