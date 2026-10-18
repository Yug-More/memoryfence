"""Engines, units of work, and initialization for one episode's databases.

Each episode has two SQLite files:

* the **system-under-test database** (main schema), and
* the **ground-truth database**, attached as schema ``groundtruth`` *only* on the
  harness writer connection.

A unit of work is one ``BEGIN IMMEDIATE`` transaction on that writer connection. There
is no second commit. SQLite makes a commit that dirties attached databases atomic,
including across a crash, only while the main database uses a rollback journal: the
commit is coordinated by a master journal. That guarantee does not hold in WAL mode.
The writer therefore forces ``journal_mode=DELETE`` and ``synchronous=FULL`` and refuses
any other journal mode. This is SQLite's documented multi-file commit behavior, not a
separate two-phase commit we implement ourselves.

Defense-facing reads use a separate read-only engine that never attaches the
ground-truth file, so a privileged join is impossible rather than merely discouraged.
"""

import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import URL, Connection, Engine, MetaData, create_engine, event, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from memoryfence.domain.errors import ConflictError, PersistenceError, ReasonCode
from memoryfence.domain.ids import IdPrefix, sequential_id
from memoryfence.domain.protocols import GroundTruthRecorder
from memoryfence.domain.time import Clock
from memoryfence.storage.schema import SCHEMA_VERSION, IdSequenceRow, SchemaInfoRow, SutBase

GROUND_TRUTH_SCHEMA = "groundtruth"

RecorderFactory = Callable[[Session], GroundTruthRecorder]


class UnitOfWork:
    """One logical operation: a session inside a single transaction, the write-only
    ground-truth recorder bound to that transaction, a clock, and identifier allocation."""

    def __init__(self, session: Session, ground_truth: GroundTruthRecorder, clock: Clock) -> None:
        self.session = session
        self.ground_truth = ground_truth
        self._clock = clock

    def now(self) -> datetime:
        return self._clock.now()

    def next_number(self, prefix: IdPrefix) -> int:
        """Allocate the next number for ``prefix``; rolled back with the transaction."""
        row = self.session.get(IdSequenceRow, prefix.value)
        if row is None:
            row = IdSequenceRow(prefix=prefix.value, last_value=1)
            self.session.add(row)
        else:
            row.last_value += 1
        self.session.flush()
        return row.last_value

    def next_id(self, prefix: IdPrefix) -> str:
        return sequential_id(prefix, self.next_number(prefix))


def _configure(engine: Engine, *, attach: Path | None, read_only: bool) -> None:
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection: Any, _record: Any) -> None:  # noqa: ANN401 - DB-API
        if not isinstance(dbapi_connection, sqlite3.Connection):
            raise PersistenceError("expected a sqlite3 connection")
        # Let SQLAlchemy's "begin" event, not the driver, control transactions.
        dbapi_connection.isolation_level = None
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            if attach is not None:
                # journal_mode must be set outside a transaction. isolation_level None
                # above leaves the connection in autocommit until the begin handler.
                _require_rollback_journal(cursor)
                cursor.execute(f"ATTACH DATABASE ? AS {GROUND_TRUTH_SCHEMA}", (str(attach),))
            if read_only:
                cursor.execute("PRAGMA query_only = ON")
        finally:
            cursor.close()

    @event.listens_for(engine, "begin")
    def _on_begin(connection: Connection) -> None:
        connection.exec_driver_sql("BEGIN" if read_only else "BEGIN IMMEDIATE")


def _require_rollback_journal(cursor: sqlite3.Cursor) -> None:
    """Force the journal mode that makes an attached-database commit atomic.

    ``PRAGMA journal_mode = DELETE`` returns the mode actually in effect. Anything else
    means a later commit could persist one file and not the other.
    """
    cursor.execute("PRAGMA journal_mode = DELETE")
    row = cursor.fetchone()
    mode = "" if row is None else str(row[0]).lower()
    if mode != "delete":
        raise PersistenceError(
            "attached-database commits require SQLite rollback journal mode DELETE"
        )
    cursor.execute("PRAGMA synchronous = FULL")


def _translate(error: DBAPIError) -> PersistenceError | ConflictError:
    # Only the driver's constraint message is kept; SQL parameters (which may hold
    # content or ground truth) are never included.
    detail = str(error.orig).splitlines()[0] if error.orig is not None else type(error).__name__
    if isinstance(error, IntegrityError) and "UNIQUE constraint failed" in detail:
        return ConflictError(detail, ReasonCode.DUPLICATE_IDENTIFIER)
    return PersistenceError(detail)


class EpisodeDatabase:
    def __init__(
        self,
        *,
        system_path: Path,
        ground_truth_path: Path,
        ground_truth_metadata: MetaData,
        recorder_factory: RecorderFactory,
        clock: Clock,
    ) -> None:
        if system_path.resolve() == ground_truth_path.resolve():
            raise PersistenceError("system and ground-truth databases must be separate files")
        self.system_path = system_path
        self.ground_truth_path = ground_truth_path
        self._ground_truth_metadata = ground_truth_metadata
        self._recorder_factory = recorder_factory
        self._clock = clock
        self._writer = create_engine(URL.create("sqlite", database=str(system_path)))
        _configure(self._writer, attach=ground_truth_path, read_only=False)
        self._reader: Engine | None = None

    def initialize(self) -> None:
        """Create both schemas if absent and verify the schema version."""
        try:
            with self._writer.begin() as connection:
                if connection.exec_driver_sql("PRAGMA foreign_keys").scalar() != 1:
                    raise PersistenceError("SQLite foreign-key enforcement is not enabled")
                SutBase.metadata.create_all(connection)
                self._ground_truth_metadata.create_all(connection)
                stored = connection.execute(
                    select(SchemaInfoRow.value).where(SchemaInfoRow.key == "schema_version")
                ).scalar_one_or_none()
                if stored is None:
                    connection.execute(
                        insert(SchemaInfoRow).values(
                            key="schema_version", value=str(SCHEMA_VERSION)
                        )
                    )
                elif stored != str(SCHEMA_VERSION):
                    raise PersistenceError(
                        f"database schema version {stored} != {SCHEMA_VERSION}",
                        ReasonCode.SCHEMA_VERSION_MISMATCH,
                    )
        except DBAPIError as error:
            raise _translate(error) from None

    @contextmanager
    def unit_of_work(self) -> Iterator[UnitOfWork]:
        session = Session(self._writer, expire_on_commit=False, autoflush=True)
        try:
            with session.begin():
                yield UnitOfWork(session, self._recorder_factory(session), self._clock)
        except DBAPIError as error:
            raise _translate(error) from None
        finally:
            session.close()

    @contextmanager
    def system_read_session(self) -> Iterator[Session]:
        """A read-only session on the system-under-test database alone.

        The ground-truth file is not attached to this engine, so no query issued through
        this session can reach true provenance, labels, or the deletion ledger.
        """
        if self._reader is None:
            url = URL.create(
                "sqlite",
                database=f"file:{self.system_path}",
                query={"mode": "ro", "uri": "true"},
            )
            self._reader = create_engine(url)
            _configure(self._reader, attach=None, read_only=True)
        session = Session(self._reader)
        try:
            with session.begin():
                yield session
        except DBAPIError as error:
            raise _translate(error) from None
        finally:
            session.close()

    def integrity_problems(self) -> tuple[str, ...]:
        """Run SQLite's integrity and foreign-key checks on both databases."""
        problems: list[str] = []
        with self._writer.connect() as connection:
            for schema in ("main", GROUND_TRUTH_SCHEMA):
                for (result,) in connection.exec_driver_sql(f"PRAGMA {schema}.integrity_check"):
                    if result != "ok":
                        problems.append(f"{schema}: {result}")
                for row in connection.exec_driver_sql(f"PRAGMA {schema}.foreign_key_check"):
                    problems.append(f"{schema}: foreign key violation in {row[0]}")
        return tuple(problems)

    def dispose(self) -> None:
        self._writer.dispose()
        if self._reader is not None:
            self._reader.dispose()
