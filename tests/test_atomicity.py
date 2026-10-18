"""Cross-database commit behavior of one attached SQLite connection."""

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import event

from memoryfence.domain.enums import MemoryType
from memoryfence.domain.errors import PersistenceError
from memoryfence.domain.time import StepClock
from memoryfence.groundtruth import open_episode
from memoryfence.groundtruth.schema import TrueNodeRow
from memoryfence.storage.database import GROUND_TRUTH_SCHEMA, EpisodeDatabase
from memoryfence.storage.schema import UserRow


def test_writer_uses_delete_journal_and_reader_omits_ground_truth(tmp_path: Path) -> None:
    clock = StepClock(datetime(2026, 1, 1, tzinfo=UTC), timedelta(seconds=1))
    database = open_episode(tmp_path, clock)
    try:
        with database.unit_of_work() as unit:
            mode = unit.session.connection().exec_driver_sql("PRAGMA journal_mode").scalar()
            names = {
                name
                for (_seq, name, _file) in unit.session.connection().exec_driver_sql(
                    "PRAGMA database_list"
                )
            }
            synchronous = unit.session.connection().exec_driver_sql("PRAGMA synchronous").scalar()
        assert mode == "delete"
        assert synchronous == 2  # FULL
        assert GROUND_TRUTH_SCHEMA in names
        with database.system_read_session() as session:
            visible = {
                name
                for (_seq, name, _file) in session.connection().exec_driver_sql(
                    "PRAGMA database_list"
                )
            }
        assert GROUND_TRUTH_SCHEMA not in visible
        with (
            pytest.raises(PersistenceError, match="no such table"),
            database.system_read_session() as session,
        ):
            session.connection().exec_driver_sql(
                "SELECT memory_id FROM groundtruth.true_provenance_nodes"
            ).all()
    finally:
        database.dispose()


def test_injected_commit_failure_rolls_back_both_databases(tmp_path: Path) -> None:
    clock = StepClock(datetime(2026, 1, 1, tzinfo=UTC), timedelta(seconds=1))
    database = open_episode(tmp_path, clock)
    seen = {"commit": 0}

    @event.listens_for(database._writer, "commit")
    def _fail_commit(_connection: object) -> None:
        # SQLAlchemy emits this event before the DB-API commit. Raising here aborts
        # the single COMMIT that would otherwise cover both attached databases.
        seen["commit"] += 1
        raise sqlite3.OperationalError("injected commit failure")

    try:
        with pytest.raises(sqlite3.OperationalError, match="injected commit failure"):
            _write_both_databases(database)
    finally:
        event.remove(database._writer, "commit", _fail_commit)
        database.dispose()

    assert seen["commit"] == 1
    # sqlite3's context manager commits but does not close. Python 3.13 warns if
    # the connection is left for the garbage collector.
    system = sqlite3.connect(tmp_path / "system.sqlite")
    ground_truth = sqlite3.connect(tmp_path / "groundtruth.sqlite")
    try:
        users = system.execute("SELECT COUNT(*) FROM users").fetchone()
        nodes = ground_truth.execute("SELECT COUNT(*) FROM true_provenance_nodes").fetchone()
    finally:
        system.close()
        ground_truth.close()
    assert users is not None
    assert users[0] == 0
    assert nodes is not None
    assert nodes[0] == 0


def _write_both_databases(database: EpisodeDatabase) -> None:
    with database.unit_of_work() as unit:
        unit.session.add(
            UserRow(
                id="usr-atom",
                display_name="Atom",
                created_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        unit.session.add(
            TrueNodeRow(
                memory_id="mem-atom",
                workspace_id="ws-atom",
                memory_type=MemoryType.DERIVED,
                source_id=None,
                source_revision_id=None,
                author_user_id=None,
                created_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        unit.session.flush()


def test_uncommitted_work_is_absent_after_reopen(tmp_path: Path) -> None:
    """Rollback on an exception is not a crash during SQLite's commit syscall.

    The injected-commit test above also stops before the database commit API.
    Neither test is evidence of crash atomicity across a power loss.
    """
    clock = StepClock(datetime(2026, 1, 1, tzinfo=UTC), timedelta(seconds=1))
    database = open_episode(tmp_path, clock)
    try:
        with pytest.raises(RuntimeError, match="stop before commit"), database.unit_of_work():
            raise RuntimeError("stop before commit")
    finally:
        database.dispose()
    reopened = open_episode(tmp_path, clock)
    try:
        with reopened.system_read_session() as session:
            count = session.connection().exec_driver_sql("SELECT COUNT(*) FROM users").scalar()
        assert count == 0
    finally:
        reopened.dispose()
