"""Typed identifiers.

Identifiers are lowercase ``<prefix>-<suffix>`` strings. Principals and workspaces use
caller-chosen suffixes (for example ``usr-alice``) so fixtures are readable. All other
identifiers are allocated in creation order within an episode (``mem-000001``), which the
experimental protocol requires for reproducibility.
"""

import re
from collections.abc import Callable
from enum import StrEnum
from typing import Annotated, NewType

from pydantic import AfterValidator

UserId = NewType("UserId", str)
AgentId = NewType("AgentId", str)
WorkspaceId = NewType("WorkspaceId", str)
SourceId = NewType("SourceId", str)
RevisionId = NewType("RevisionId", str)
MemoryId = NewType("MemoryId", str)
TransformationId = NewType("TransformationId", str)
DeletionId = NewType("DeletionId", str)
TaskId = NewType("TaskId", str)
ProposalId = NewType("ProposalId", str)
EventId = NewType("EventId", str)
RunId = NewType("RunId", str)


class IdPrefix(StrEnum):
    """The prefix that identifies the kind of every identifier."""

    USER = "usr"
    AGENT = "agt"
    WORKSPACE = "ws"
    SOURCE = "src"
    REVISION = "rev"
    MEMORY = "mem"
    TRANSFORMATION = "trf"
    DELETION = "del"
    TASK = "task"
    PROPOSAL = "prop"
    EVENT = "evt"
    RUN = "run"


_SUFFIX = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_PATTERNS = {prefix: re.compile(rf"{prefix.value}-{_SUFFIX}") for prefix in IdPrefix}


def is_valid_id(prefix: IdPrefix, value: str) -> bool:
    return _PATTERNS[prefix].fullmatch(value) is not None


def sequential_id(prefix: IdPrefix, number: int) -> str:
    if number < 1:
        raise ValueError("sequence numbers start at 1")
    return f"{prefix.value}-{number:06d}"


def _validator(prefix: IdPrefix) -> Callable[[str], str]:
    def check(value: str) -> str:
        if not is_valid_id(prefix, value):
            raise ValueError(f"expected an identifier of the form '{prefix.value}-<suffix>'")
        return value

    return check


UserIdField = Annotated[UserId, AfterValidator(_validator(IdPrefix.USER))]
AgentIdField = Annotated[AgentId, AfterValidator(_validator(IdPrefix.AGENT))]
WorkspaceIdField = Annotated[WorkspaceId, AfterValidator(_validator(IdPrefix.WORKSPACE))]
SourceIdField = Annotated[SourceId, AfterValidator(_validator(IdPrefix.SOURCE))]
RevisionIdField = Annotated[RevisionId, AfterValidator(_validator(IdPrefix.REVISION))]
MemoryIdField = Annotated[MemoryId, AfterValidator(_validator(IdPrefix.MEMORY))]
TransformationIdField = Annotated[
    TransformationId, AfterValidator(_validator(IdPrefix.TRANSFORMATION))
]
DeletionIdField = Annotated[DeletionId, AfterValidator(_validator(IdPrefix.DELETION))]
TaskIdField = Annotated[TaskId, AfterValidator(_validator(IdPrefix.TASK))]
ProposalIdField = Annotated[ProposalId, AfterValidator(_validator(IdPrefix.PROPOSAL))]
EventIdField = Annotated[EventId, AfterValidator(_validator(IdPrefix.EVENT))]
RunIdField = Annotated[RunId, AfterValidator(_validator(IdPrefix.RUN))]
