"""ORM mappings for the system-under-test database.

There are no ORM relationships and no cascading deletes: every multi-row change is an
explicit statement inside a unit of work, so provenance can never disappear as a side
effect. Foreign keys default to ``NO ACTION``, which rejects orphaning deletes.

Triggers make revisions, transformations, and memory content immutable, and make
recorded provenance and the event log append-only.
"""

from datetime import datetime

from sqlalchemy import (
    DDL,
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from memoryfence.domain.enums import (
    AgentState,
    DeletionPolicy,
    DeletionScenario,
    EventCategory,
    EventOutcome,
    MembershipState,
    MemoryState,
    MemoryType,
    MemoryVisibility,
    Operation,
    Permission,
    PrincipalKind,
    RederivationStatus,
    ResourceKind,
    SourceDeletionState,
    SourceVisibility,
    TransformationType,
    WorkspaceRole,
)
from memoryfence.domain.errors import ReasonCode
from memoryfence.storage.types import UtcDateTime, enum_column, fk

SCHEMA_VERSION = 1

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Id = String(80)


class SutBase(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {datetime: UtcDateTime()}  # noqa: RUF012


class SchemaInfoRow(SutBase):
    __tablename__ = "schema_info"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


class IdSequenceRow(SutBase):
    __tablename__ = "id_sequences"
    __table_args__ = (CheckConstraint("last_value >= 1", name="positive"),)

    prefix: Mapped[str] = mapped_column(String(16), primary_key=True)
    last_value: Mapped[int]


class UserRow(SutBase):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime]


class WorkspaceRow(SutBase):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime]


class MembershipRow(SutBase):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint(
            "(state = 'revoked') = (revoked_at IS NOT NULL)", name="revocation_consistent"
        ),
    )

    workspace_id: Mapped[str] = mapped_column(Id, fk("workspaces.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(Id, fk("users.id"), primary_key=True)
    role: Mapped[WorkspaceRole] = mapped_column(enum_column(WorkspaceRole))
    state: Mapped[MembershipState] = mapped_column(enum_column(MembershipState))
    granted_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]


class AgentRow(SutBase):
    __tablename__ = "agents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "controlling_user_id"],
            ["memberships.workspace_id", "memberships.user_id"],
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            "(state = 'revoked') = (revoked_at IS NOT NULL)", name="revocation_consistent"
        ),
    )

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(Id, index=True)
    controlling_user_id: Mapped[str] = mapped_column(Id)
    display_name: Mapped[str] = mapped_column(String(200))
    state: Mapped[AgentState] = mapped_column(enum_column(AgentState))
    created_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]


class AgentPermissionRow(SutBase):
    __tablename__ = "agent_permissions"

    agent_id: Mapped[str] = mapped_column(Id, fk("agents.id"), primary_key=True)
    permission: Mapped[Permission] = mapped_column(enum_column(Permission), primary_key=True)


class InstructionAuthorityRow(SutBase):
    __tablename__ = "instruction_authorities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "authority_user_id"],
            ["memberships.workspace_id", "memberships.user_id"],
            deferrable=True,
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "subject_user_id"],
            ["memberships.workspace_id", "memberships.user_id"],
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("authority_user_id <> subject_user_id", name="distinct_users"),
    )

    workspace_id: Mapped[str] = mapped_column(Id, primary_key=True)
    authority_user_id: Mapped[str] = mapped_column(Id, primary_key=True)
    subject_user_id: Mapped[str] = mapped_column(Id, primary_key=True)
    granted_at: Mapped[datetime]


class SourceRow(SutBase):
    __tablename__ = "sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "owner_user_id"],
            ["memberships.workspace_id", "memberships.user_id"],
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            "(deletion_state = 'active') = (deleted_at IS NULL)", name="deleted_at_consistent"
        ),
        CheckConstraint(
            "(deletion_state = 'active') = (deletion_policy IS NULL)", name="policy_consistent"
        ),
        CheckConstraint("(deletion_state = 'deleted') = (title IS NULL)", name="title_removed"),
    )

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(Id, index=True)
    owner_user_id: Mapped[str] = mapped_column(Id)
    title: Mapped[str | None] = mapped_column(String(500))
    visibility: Mapped[SourceVisibility] = mapped_column(enum_column(SourceVisibility))
    deletion_state: Mapped[SourceDeletionState] = mapped_column(enum_column(SourceDeletionState))
    deletion_policy: Mapped[DeletionPolicy | None] = mapped_column(enum_column(DeletionPolicy))
    created_at: Mapped[datetime]
    deleted_at: Mapped[datetime | None]


class SourceAccessGrantRow(SutBase):
    __tablename__ = "source_access_grants"

    source_id: Mapped[str] = mapped_column(Id, fk("sources.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(Id, fk("users.id"), primary_key=True)
    granted_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]


class SourceRevisionRow(SutBase):
    __tablename__ = "source_revisions"
    __table_args__ = (
        UniqueConstraint("source_id", "sequence"),
        CheckConstraint("sequence >= 1", name="positive_sequence"),
    )

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    source_id: Mapped[str] = mapped_column(Id, fk("sources.id"))
    sequence: Mapped[int]
    author_user_id: Mapped[str] = mapped_column(Id, fk("users.id"))
    content: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime]


class TransformationRow(SutBase):
    __tablename__ = "transformations"
    __table_args__ = (CheckConstraint("derivation_round >= 1", name="positive_round"),)

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(Id, fk("workspaces.id"))
    transformation_type: Mapped[TransformationType] = mapped_column(enum_column(TransformationType))
    prompt_version: Mapped[str] = mapped_column(String(64))
    derivation_round: Mapped[int]
    performed_by_kind: Mapped[PrincipalKind] = mapped_column(enum_column(PrincipalKind))
    performed_by_id: Mapped[str] = mapped_column(Id)
    created_at: Mapped[datetime]


class MemoryRow(SutBase):
    __tablename__ = "memories"
    __table_args__ = (
        CheckConstraint(
            "(memory_type = 'primary' AND source_revision_id IS NOT NULL"
            " AND transformation_id IS NULL AND derivation_round = 0"
            " AND visibility = 'inherit_source')"
            " OR (memory_type = 'derived' AND source_revision_id IS NULL"
            " AND transformation_id IS NOT NULL AND derivation_round >= 1"
            " AND visibility <> 'inherit_source')",
            name="shape",
        ),
        CheckConstraint(
            "(visibility = 'private') = (owner_user_id IS NOT NULL)", name="owner_consistent"
        ),
        CheckConstraint(
            "(state = 'revoked') = (revoked_at IS NOT NULL)", name="revocation_consistent"
        ),
        Index("ix_memories_workspace_state", "workspace_id", "state"),
    )

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(Id, fk("workspaces.id"))
    memory_type: Mapped[MemoryType] = mapped_column(enum_column(MemoryType))
    state: Mapped[MemoryState] = mapped_column(enum_column(MemoryState))
    visibility: Mapped[MemoryVisibility] = mapped_column(enum_column(MemoryVisibility))
    owner_user_id: Mapped[str | None] = mapped_column(Id, fk("users.id"))
    content: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    source_revision_id: Mapped[str | None] = mapped_column(
        Id, fk("source_revisions.id"), index=True
    )
    transformation_id: Mapped[str | None] = mapped_column(Id, fk("transformations.id"))
    derivation_round: Mapped[int]
    created_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]


class RecordedNodeRow(SutBase):
    """Recorded provenance node. Deliberately has no foreign key to ``memories``: nodes
    outlive deleted memories so that lineage is never erased as a side effect."""

    __tablename__ = "recorded_provenance_nodes"
    __table_args__ = (
        CheckConstraint(
            "(memory_type = 'primary') = (source_id IS NOT NULL)"
            " AND (memory_type = 'primary') = (author_user_id IS NOT NULL)",
            name="primary_shape",
        ),
        CheckConstraint(
            "NOT (marked_incomplete AND memory_type = 'primary')", name="marking_derived_only"
        ),
    )

    memory_id: Mapped[str] = mapped_column(Id, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(Id, fk("workspaces.id"), index=True)
    memory_type: Mapped[MemoryType] = mapped_column(enum_column(MemoryType))
    source_id: Mapped[str | None] = mapped_column(Id, fk("sources.id"), index=True)
    author_user_id: Mapped[str | None] = mapped_column(Id, fk("users.id"))
    marked_incomplete: Mapped[bool]
    created_at: Mapped[datetime]


class RecordedLinkRow(SutBase):
    __tablename__ = "recorded_provenance_links"
    __table_args__ = (
        CheckConstraint("child_id <> parent_id", name="no_self_loop"),
        Index("ix_recorded_provenance_links_parent", "parent_id"),
    )

    child_id: Mapped[str] = mapped_column(
        Id, fk("recorded_provenance_nodes.memory_id"), primary_key=True
    )
    parent_id: Mapped[str] = mapped_column(
        Id, fk("recorded_provenance_nodes.memory_id"), primary_key=True
    )


class SourceDeletionRow(SutBase):
    __tablename__ = "source_deletions"

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    source_id: Mapped[str] = mapped_column(Id, fk("sources.id"), index=True)
    workspace_id: Mapped[str] = mapped_column(Id, fk("workspaces.id"))
    policy: Mapped[DeletionPolicy] = mapped_column(enum_column(DeletionPolicy))
    scenario: Mapped[DeletionScenario] = mapped_column(enum_column(DeletionScenario))
    requested_by_kind: Mapped[PrincipalKind] = mapped_column(enum_column(PrincipalKind))
    requested_by_id: Mapped[str] = mapped_column(Id)
    run_id: Mapped[str | None] = mapped_column(Id)
    occurred_at: Mapped[datetime]


class RederivationTaskRow(SutBase):
    """``replaces_memory_id`` names a memory that no longer exists, so it has no foreign
    key. Input identifiers are a snapshot, re-validated when Phase 3 executes the task."""

    __tablename__ = "rederivation_tasks"

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    deletion_id: Mapped[str] = mapped_column(Id, fk("source_deletions.id"), index=True)
    workspace_id: Mapped[str] = mapped_column(Id, fk("workspaces.id"))
    replaces_memory_id: Mapped[str] = mapped_column(Id)
    transformation_id: Mapped[str] = mapped_column(Id, fk("transformations.id"))
    surviving_input_ids: Mapped[str] = mapped_column(Text)
    depends_on_task_ids: Mapped[str] = mapped_column(Text)
    status: Mapped[RederivationStatus] = mapped_column(enum_column(RederivationStatus))
    created_at: Mapped[datetime]


class EventRow(SutBase):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("(actor_kind IS NULL) = (actor_id IS NULL)", name="actor_complete"),
        CheckConstraint(
            "(resource_kind IS NULL) = (resource_id IS NULL)", name="resource_complete"
        ),
    )

    id: Mapped[str] = mapped_column(Id, primary_key=True)
    sequence: Mapped[int] = mapped_column(unique=True)
    category: Mapped[EventCategory] = mapped_column(enum_column(EventCategory))
    operation: Mapped[Operation] = mapped_column(enum_column(Operation))
    occurred_at: Mapped[datetime]
    actor_kind: Mapped[PrincipalKind | None] = mapped_column(enum_column(PrincipalKind))
    actor_id: Mapped[str | None] = mapped_column(Id)
    workspace_id: Mapped[str | None] = mapped_column(Id, index=True)
    resource_kind: Mapped[ResourceKind | None] = mapped_column(enum_column(ResourceKind))
    resource_id: Mapped[str | None] = mapped_column(Id)
    outcome: Mapped[EventOutcome] = mapped_column(enum_column(EventOutcome))
    reason: Mapped[ReasonCode] = mapped_column(enum_column(ReasonCode))
    policy: Mapped[DeletionPolicy | None] = mapped_column(enum_column(DeletionPolicy))
    run_id: Mapped[str | None] = mapped_column(Id)
    details_json: Mapped[str] = mapped_column(Text)


def _abort_trigger(table: Table, name: str, timing: str, message: str) -> None:
    statement = DDL(  # type: ignore[no-untyped-call]
        f"CREATE TRIGGER IF NOT EXISTS main.{name} {timing} ON {table.name} "
        f"BEGIN SELECT RAISE(ABORT, '{message}'); END"
    )
    event.listen(table, "after_create", statement)


def _table(row: type[SutBase]) -> Table:
    table = row.__table__
    if not isinstance(table, Table):
        raise TypeError(f"{row.__name__} is not mapped to a table")
    return table


_immutable_rows: tuple[type[SutBase], ...] = (SourceRevisionRow, TransformationRow)
for _row in _immutable_rows:
    _abort_trigger(
        _table(_row),
        f"trg_{_row.__tablename__}_immutable",
        "BEFORE UPDATE",
        f"{_row.__tablename__} are immutable",
    )
_append_only_rows: tuple[type[SutBase], ...] = (RecordedNodeRow, RecordedLinkRow, EventRow)
for _row in _append_only_rows:
    for _action in ("UPDATE", "DELETE"):
        _abort_trigger(
            _table(_row),
            f"trg_{_row.__tablename__}_no_{_action.lower()}",
            f"BEFORE {_action}",
            f"{_row.__tablename__} is append-only",
        )
_abort_trigger(
    _table(MemoryRow),
    "trg_memories_content_immutable",
    "BEFORE UPDATE OF id, workspace_id, memory_type, content, content_sha256,"
    " source_revision_id, transformation_id, derivation_round, created_at",
    "memory content and lineage fields are immutable",
)
