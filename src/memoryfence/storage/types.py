from datetime import datetime
from enum import StrEnum

from sqlalchemy import Dialect, ForeignKey, String, TypeDecorator
from sqlalchemy import Enum as SqlEnum

from memoryfence.domain.time import require_utc


class UtcDateTime(TypeDecorator[datetime]):
    """Stores UTC timestamps as fixed-width ISO 8601 text, which sorts chronologically.

    Naive or non-UTC values are rejected rather than silently converted.
    """

    impl = String(32)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return require_utc(value).isoformat(timespec="microseconds")

    def process_result_value(self, value: str | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return require_utc(datetime.fromisoformat(value))


def fk(column: str) -> ForeignKey:
    """A foreign key checked when the transaction commits.

    The ORM does not order inserts by foreign key unless a ``relationship()`` is
    configured, and these mappings deliberately have none. Deferring the check keeps
    a multi-row flush atomic without depending on statement order.
    """
    return ForeignKey(column, deferrable=True, initially="DEFERRED")


def enum_column[E: StrEnum](enum_type: type[E]) -> SqlEnum:
    """A text column constrained to the enum's values by a CHECK constraint."""
    return SqlEnum(
        enum_type,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        length=64,
        values_callable=lambda members: [member.value for member in members],
    )
