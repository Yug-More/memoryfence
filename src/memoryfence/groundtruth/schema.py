"""ORM mappings for the evaluator-only ground-truth database (attached as ``groundtruth``).

Tables are append-only, enforced by SQLite triggers rather than by convention. The only
permitted update is a run manifest's single transition from ``running`` to a terminal
status. SQLite cannot declare foreign keys across database files, so identifiers that
refer to the system-under-test database are plain columns.
"""

from datetime import datetime

from sqlalchemy import (
    DDL,
    CheckConstraint,
    Index,
    MetaData,
    String,
    Table,
    Text,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from memoryfence.domain.enums import (
    DeletionEffect,
    DeletionPolicy,
    DeletionScenario,
    MemoryType,
    PrincipalKind,
    RunStatus,
    SourceOrigin,
)
from memoryfence.storage.database import GROUND_TRUTH_SCHEMA
from memoryfence.storage.schema import NAMING_CONVENTION
from memoryfence.storage.types import UtcDateTime, enum_column, fk

Id = String(80)


class GroundTruthBase(DeclarativeBase):
    metadata = MetaData(schema=GROUND_TRUTH_SCHEMA, naming_convention=NAMING_CONVENTION)
    type_annotation_map = {datetime: UtcDateTime()}  # noqa: RUF012


class TrueNodeRow(GroundTruthBase):
    __tablename__ = "true_provenance_nodes"

    memory_id: Mapped[str] = mapped_column(Id, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(Id, index=True)
    memory_type: Mapped[MemoryType] = mapped_column(enum_column(MemoryType))
    source_id: Mapped[str | None] = mapped_column(Id, index=True)
    source_revision_id: Mapped[str | None] = mapped_column(Id)
    author_user_id: Mapped[str | None] = mapped_column(Id)
    created_at: Mapped[datetime]


class TrueLinkRow(GroundTruthBase):
    __tablename__ = "true_provenance_links"
    __table_args__ = (
        CheckConstraint("child_id <> parent_id", name="no_self_loop"),
        CheckConstraint("ordinal >= 0", name="nonnegative_ordinal"),
        Index("ix_true_provenance_links_parent", "parent_id"),
    )

    child_id: Mapped[str] = mapped_column(
        Id, fk("true_provenance_nodes.memory_id"), primary_key=True
    )
    parent_id: Mapped[str] = mapped_column(
        Id, fk("true_provenance_nodes.memory_id"), primary_key=True
    )
    ordinal: Mapped[int]


class SourceLabelRow(GroundTruthBase):
    __tablename__ = "source_labels"

    source_id: Mapped[str] = mapped_column(Id, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(Id)
    origin: Mapped[SourceOrigin] = mapped_column(enum_column(SourceOrigin))
    labeled_at: Mapped[datetime]


class DeletionEventRow(GroundTruthBase):
    __tablename__ = "deletion_events"

    deletion_id: Mapped[str] = mapped_column(Id, primary_key=True)
    source_id: Mapped[str] = mapped_column(Id, index=True)
    workspace_id: Mapped[str] = mapped_column(Id)
    policy: Mapped[DeletionPolicy] = mapped_column(enum_column(DeletionPolicy))
    scenario: Mapped[DeletionScenario] = mapped_column(enum_column(DeletionScenario))
    requested_by_kind: Mapped[PrincipalKind] = mapped_column(enum_column(PrincipalKind))
    requested_by_id: Mapped[str] = mapped_column(Id)
    run_id: Mapped[str | None] = mapped_column(Id)
    occurred_at: Mapped[datetime]


class DeletionLedgerRow(GroundTruthBase):
    __tablename__ = "deletion_ledger"
    __table_args__ = (CheckConstraint("sequence >= 1", name="positive_sequence"),)

    deletion_id: Mapped[str] = mapped_column(
        Id, fk("deletion_events.deletion_id"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(primary_key=True)
    effect: Mapped[DeletionEffect] = mapped_column(enum_column(DeletionEffect))
    source_id: Mapped[str] = mapped_column(Id)
    revision_id: Mapped[str | None] = mapped_column(Id)
    memory_id: Mapped[str | None] = mapped_column(Id)
    content: Mapped[str | None] = mapped_column(Text)
    content_sha256: Mapped[str | None] = mapped_column(String(64))


class ExperimentRunRow(GroundTruthBase):
    __tablename__ = "experiment_runs"
    __table_args__ = (
        CheckConstraint("(status = 'running') = (finished_at IS NULL)", name="finished_consistent"),
    )

    run_id: Mapped[str] = mapped_column(Id, primary_key=True)
    status: Mapped[RunStatus] = mapped_column(enum_column(RunStatus))
    manifest_json: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime]
    finished_at: Mapped[datetime | None]


def _ddl(statement: str) -> DDL:
    return DDL(statement)  # type: ignore[no-untyped-call]


def _append_only(table: Table) -> None:
    for action in ("UPDATE", "DELETE"):
        name = f"trg_{table.name}_no_{action.lower()}"
        event.listen(
            table,
            "after_create",
            _ddl(
                f"CREATE TRIGGER IF NOT EXISTS {GROUND_TRUTH_SCHEMA}.{name} "
                f"BEFORE {action} ON {table.name} "
                f"BEGIN SELECT RAISE(ABORT, '{table.name} is append-only'); END"
            ),
        )


for _row in (TrueNodeRow, TrueLinkRow, SourceLabelRow, DeletionEventRow, DeletionLedgerRow):
    _append_only(_row.__table__)  # type: ignore[arg-type]

_runs = ExperimentRunRow.__table__
event.listen(
    _runs,
    "after_create",
    _ddl(
        f"CREATE TRIGGER IF NOT EXISTS {GROUND_TRUTH_SCHEMA}.trg_experiment_runs_finish_once "
        "BEFORE UPDATE ON experiment_runs "
        "WHEN OLD.status <> 'running' OR OLD.run_id <> NEW.run_id "
        "OR OLD.started_at <> NEW.started_at "
        "BEGIN SELECT RAISE(ABORT, 'experiment_runs can only finish once'); END"
    ),
)
event.listen(
    _runs,
    "after_create",
    _ddl(
        f"CREATE TRIGGER IF NOT EXISTS {GROUND_TRUTH_SCHEMA}.trg_experiment_runs_no_delete "
        "BEFORE DELETE ON experiment_runs "
        "BEGIN SELECT RAISE(ABORT, 'experiment_runs is append-only'); END"
    ),
)
