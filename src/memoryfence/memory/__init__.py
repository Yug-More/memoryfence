"""Ingestion, scripted transformations, retrieval, and DS4 task execution.

Transformations are deterministic approximations selected by an explicit model fixture.
They validate the experimental mechanics. They are not language-model reasoning and
they are not evidence of model susceptibility.
"""

from memoryfence.memory.ingest import IngestionService
from memoryfence.memory.rederive import RederivationExecutor
from memoryfence.memory.retrieve import RetrievalService
from memoryfence.memory.transforms import PROMPT_VERSION, TransformService

__all__ = [
    "PROMPT_VERSION",
    "IngestionService",
    "RederivationExecutor",
    "RetrievalService",
    "TransformService",
]
