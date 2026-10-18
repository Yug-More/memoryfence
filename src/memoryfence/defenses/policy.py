"""DF3 policy checks. Inputs are the task text and the tool call, never retrieved memory."""

import re

from memoryfence.domain.enums import PolicySource
from memoryfence.domain.errors import ReasonCode

_TOKEN = re.compile(r"[a-z0-9]+")
_STANDING = frozenset({"add_note", "create_ticket", "update_task"})
_RISK = {"add_note": 1, "create_ticket": 2, "update_task": 2}


def tool_risk(tool_name: str) -> int:
    """Side-effecting sandbox tools are 1 or 2. An unknown name is treated as higher."""
    return _RISK.get(tool_name, 3)


def authorize_tool(
    task: str,
    tool_name: str,
    arguments: tuple[tuple[str, str], ...],
    *,
    source: PolicySource,
    oracle_tools: tuple[str, ...],
) -> ReasonCode:
    """Return OK or a denial. Generated checks use only ``task`` and the call."""
    if tool_name not in _STANDING:
        return ReasonCode.DEFENSE_POLICY
    if source is PolicySource.ORACLE:
        if tool_name not in oracle_tools:
            return ReasonCode.DEFENSE_POLICY
        return ReasonCode.OK
    task_tokens = _tokens(task)
    if re.search(rf"(?<![a-z0-9_]){re.escape(tool_name)}(?![a-z0-9_])", task.casefold()) is None:
        return ReasonCode.DEFENSE_POLICY
    for _name, value in arguments:
        if not _tokens(value) <= task_tokens:
            return ReasonCode.DEFENSE_POLICY
    return ReasonCode.OK


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.casefold()))
