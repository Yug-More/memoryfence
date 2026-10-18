"""SQLite integrity, transactions, and round trips."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from memoryfence.domain.enums import DeletionPolicy, DeletionScenario, MemoryType, Operation
from memoryfence.domain.errors import ConflictError, PersistenceError, ReasonCode
from memoryfence.domain.time import StepClock
from memoryfence.groundtruth.recorder import SqlGroundTruthRecorder
from memoryfence.groundtruth.schema import GroundTruthBase, TrueNodeRow
from memoryfence.observability import Auditor, read_events
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.storage.schema import UserRow
from memoryfence.workspace.deletion import DeletionService
from tests.conftest import Lab


def _database(
    tmp_path: Path, recorder: type[SqlGroundTruthRecorder] = SqlGroundTruthRecorder
) -> EpisodeDatabase:
    database = EpisodeDatabase(
        system_path=tmp_path / "system.sqlite",
        ground_truth_path=tmp_path / "groundtruth.sqlite",
        ground_truth_metadata=GroundTruthBase.metadata,
        recorder_factory=recorder,
        clock=StepClock(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    database.initialize()
    return database


def test_initialization_foreign_keys_and_reopen(tmp_path: Path) -> None:
    database = _database(tmp_path)
    assert database.integrity_problems() == ()
    database.dispose()
    reopened = _database(tmp_path)
    assert reopened.integrity_problems() == ()
    reopened.dispose()


def test_duplicate_identifier_and_foreign_key_failures_roll_back(tmp_path: Path) -> None:
    database = _database(tmp_path)

    def insert_duplicate() -> None:
        with database.unit_of_work() as uow:
            created_at = uow.now()
            uow.session.add(UserRow(id="usr-000001", display_name="A", created_at=created_at))
            uow.session.add(UserRow(id="usr-000001", display_name="B", created_at=created_at))

    def insert_orphan_membership() -> None:
        from memoryfence.domain.enums import MembershipState, WorkspaceRole
        from memoryfence.storage.schema import MembershipRow

        with database.unit_of_work() as uow:
            uow.session.add(
                MembershipRow(
                    workspace_id="ws-missing",
                    user_id="usr-missing",
                    role=WorkspaceRole.MEMBER,
                    state=MembershipState.ACTIVE,
                    granted_at=uow.now(),
                    revoked_at=None,
                )
            )

    with pytest.raises(ConflictError) as duplicate:
        insert_duplicate()
    assert duplicate.value.code is ReasonCode.DUPLICATE_IDENTIFIER
    with pytest.raises(PersistenceError):
        insert_orphan_membership()
    with database.system_read_session() as session:
        assert session.get(UserRow, "usr-000001") is None
    database.dispose()


def test_runtime_failure_rolls_back_both_databases(tmp_path: Path) -> None:
    database = _database(tmp_path)

    def insert_then_fail() -> None:
        with database.unit_of_work() as uow:
            uow.session.add(
                TrueNodeRow(
                    memory_id="mem-000001",
                    workspace_id="ws-home",
                    memory_type=MemoryType.DERIVED,
                    source_id=None,
                    source_revision_id=None,
                    author_user_id=None,
                    created_at=uow.now(),
                )
            )
            uow.session.flush()
            raise RuntimeError("injected")

    with pytest.raises(RuntimeError):
        insert_then_fail()
    with database.unit_of_work() as uow:
        assert uow.session.get(TrueNodeRow, "mem-000001") is None
    database.dispose()


def test_deletion_failure_does_not_apply_partially(lab: Lab, tmp_path: Path) -> None:
    class FailingRecorder(SqlGroundTruthRecorder):
        def record_deletion(self, event: object, entries: object) -> None:
            raise PersistenceError("injected deletion failure")

    del tmp_path
    source, revision = lab.add_source(lab.admin, content="must survive a failed deletion")
    memory = lab.memories.extract(lab.actor(lab.admin), revision.id, "must survive")
    failing = EpisodeDatabase(
        system_path=lab.database.system_path,
        ground_truth_path=lab.database.ground_truth_path,
        ground_truth_metadata=GroundTruthBase.metadata,
        recorder_factory=FailingRecorder,
        clock=lab.database._clock,
    )
    service = DeletionService(Auditor(failing))
    from memoryfence.domain.deletion import DeletionRequest

    with pytest.raises(PersistenceError):
        service.apply(
            lab.actor(lab.admin),
            DeletionRequest(
                source_id=source.id,
                policy=DeletionPolicy.CASCADE,
                scenario=DeletionScenario.ATTACKER,
            ),
        )
    with lab.database.system_read_session() as session:
        events = read_events(session)
    assert any(
        event.operation is Operation.SOURCE_DELETE
        and event.reason is ReasonCode.PERSISTENCE_FAILURE
        for event in events
    )
    assert (
        lab.sources.read(lab.actor(lab.admin), source.id)[1].content
        == "must survive a failed deletion"
    )
    assert lab.memories.read(lab.actor(lab.admin), memory.id).content == "must survive"
    failing.dispose()


def test_append_only_provenance_rejects_deletion(tmp_path: Path) -> None:
    database = _database(tmp_path)
    with database.unit_of_work() as uow:
        uow.session.add(
            TrueNodeRow(
                memory_id="mem-000001",
                workspace_id="ws-home",
                memory_type=MemoryType.DERIVED,
                source_id=None,
                source_revision_id=None,
                author_user_id=None,
                created_at=uow.now(),
            )
        )

    def delete_node() -> None:
        with database.unit_of_work() as uow:
            row = uow.session.get(TrueNodeRow, "mem-000001")
            assert row is not None
            uow.session.delete(row)

    with pytest.raises(PersistenceError):
        delete_node()
    database.dispose()


def test_integrity_error_type_is_translated(tmp_path: Path) -> None:
    database = _database(tmp_path)

    def flush_duplicate() -> None:
        with database.unit_of_work() as uow:
            created_at = uow.now()
            uow.session.add(UserRow(id="usr-same", display_name="A", created_at=created_at))
            uow.session.flush()
            uow.session.add(UserRow(id="usr-same", display_name="B", created_at=created_at))
            uow.session.flush()
            raise IntegrityError("stmt", {}, Exception("UNIQUE constraint failed: users.id"))

    with pytest.raises(ConflictError):
        flush_duplicate()
    database.dispose()
