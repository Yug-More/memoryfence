"""UTC timestamps and injectable clocks."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Protocol

from pydantic import AfterValidator


def require_utc(value: datetime) -> datetime:
    offset = value.utcoffset()
    if offset is None:
        raise ValueError("timestamp must be timezone-aware")
    if offset != timedelta(0):
        raise ValueError("timestamp must be in UTC")
    return value.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(require_utc)]


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class StepClock:
    """Deterministic clock: each call returns the previous time plus a fixed step."""

    def __init__(self, start: datetime, step: timedelta = timedelta(seconds=1)) -> None:
        if step <= timedelta(0):
            raise ValueError("step must be positive")
        self._next = require_utc(start)
        self._step = step

    def now(self) -> datetime:
        current = self._next
        self._next = current + self._step
        return current
