"""Creating the two databases for one episode."""

from pathlib import Path

from memoryfence.domain.time import Clock
from memoryfence.groundtruth.recorder import SqlGroundTruthRecorder
from memoryfence.groundtruth.schema import GroundTruthBase
from memoryfence.storage.database import EpisodeDatabase

SYSTEM_DATABASE = "system.sqlite"
GROUND_TRUTH_DATABASE = "groundtruth.sqlite"


def open_episode(directory: Path, clock: Clock) -> EpisodeDatabase:
    """Create (or reopen) an episode's databases in ``directory`` and initialize them."""
    directory.mkdir(parents=True, exist_ok=True)
    database = EpisodeDatabase(
        system_path=directory / SYSTEM_DATABASE,
        ground_truth_path=directory / GROUND_TRUTH_DATABASE,
        ground_truth_metadata=GroundTruthBase.metadata,
        recorder_factory=SqlGroundTruthRecorder,
        clock=clock,
    )
    database.initialize()
    return database
