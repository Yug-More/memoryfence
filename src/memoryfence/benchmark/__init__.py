"""Scripted memory-poisoning scenarios and replay.

Outcomes from this package are fixture results. They are not measurements of a
language model.
"""

from memoryfence.benchmark.catalog import list_scenarios, load_scenario, validate_catalog
from memoryfence.benchmark.runner import load_events, load_result, replay, run_scenario

__all__ = [
    "list_scenarios",
    "load_events",
    "load_result",
    "load_scenario",
    "replay",
    "run_scenario",
    "validate_catalog",
]
