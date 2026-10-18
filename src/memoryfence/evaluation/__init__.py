"""Scripted experiment matrix, metrics, and reproducibility checks.

Numbers from this package are calculations on fixture runs. They are not findings
about a language model, and they do not confirm the preregistered hypotheses.
"""

from memoryfence.evaluation.config import ExperimentConfig, load_config, smoke_config
from memoryfence.evaluation.runner import execute, preview, verify

__all__ = [
    "ExperimentConfig",
    "execute",
    "load_config",
    "preview",
    "smoke_config",
    "verify",
]
