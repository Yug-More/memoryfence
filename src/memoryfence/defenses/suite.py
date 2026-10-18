"""DF0-DF5 decisions from recorded provenance and the requester's own task.

True provenance is not an input. A missing recorded edge is not filled in.
"""

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from memoryfence.defenses.policy import authorize_tool, tool_risk
from memoryfence.domain.defenses import DefenseConfiguration
from memoryfence.domain.enums import (
    AgentState,
    DefenseId,
    EventCategory,
    Operation,
    PrincipalKind,
    RetrievalVariant,
)
from memoryfence.domain.errors import MemoryFenceError, ReasonCode
from memoryfence.domain.ids import MemoryId, UserId, WorkspaceId
from memoryfence.domain.model import ContextMemory
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.provenance import RecordedLineageView
from memoryfence.memory.retrieve import RetrievalHit
from memoryfence.observability import Auditor
from memoryfence.provenance.recorded import RecordedProvenanceReader
from memoryfence.storage.schema import AgentRow, InstructionAuthorityRow

_RETRIEVAL = frozenset({DefenseId.RETRIEVAL, DefenseId.COMBINED})
_ACTION = frozenset({DefenseId.ACTION, DefenseId.COMBINED, DefenseId.LINEAGE})


class DefenseSuite:
    """One configured defense. It holds no episode state of its own."""

    def __init__(self, config: DefenseConfiguration, auditor: Auditor) -> None:
        self._config = config
        self._auditor = auditor

    @property
    def config(self) -> DefenseConfiguration:
        return self._config

    def filter_retrieval(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        hits: tuple[RetrievalHit, ...],
    ) -> tuple[RetrievalHit, ...]:
        """Apply ``DF2-exclude``. Other conditions return the ACL-filtered hits."""
        variant = self._config.retrieval_variant
        if self._config.defense not in _RETRIEVAL or variant is not RetrievalVariant.EXCLUDE:
            return hits
        started = time.perf_counter_ns()
        with self._auditor.operation(
            EventCategory.DEFENSE,
            Operation.DEFENSE_DECIDE,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            requester = _requester(scope.uow.session, actor, workspace_id)
            trusted = _authorities(scope.uow.session, workspace_id, requester)
            reader = RecordedProvenanceReader(scope.uow.session, workspace_id)
            kept: list[RetrievalHit] = []
            excluded: list[str] = []
            for hit in hits:
                authors = _authors(reader, hit.memory_id)
                if _untrusted(authors, requester, trusted):
                    excluded.append(hit.memory_id)
                else:
                    kept.append(hit)
            scope.details["defense"] = self._config.defense.value
            scope.details["stage"] = "retrieve"
            scope.details["result"] = "exclude" if excluded else "allow"
            scope.details["excluded_ids"] = tuple(str(item) for item in excluded)
            scope.details["kept_ids"] = tuple(str(hit.memory_id) for hit in kept)
            scope.details["elapsed_us"] = (time.perf_counter_ns() - started) // 1000
        return tuple(kept)

    def render_context(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        hits: tuple[RetrievalHit, ...],
    ) -> tuple[ContextMemory, ...]:
        """Apply ``DF1`` delimiting or ``DF2-label``. Stored memories are unchanged."""
        mode = _label_mode(self._config)
        if mode is None:
            return tuple(
                ContextMemory(memory_id=hit.memory_id, content=hit.content) for hit in hits
            )
        started = time.perf_counter_ns()
        with self._auditor.operation(
            EventCategory.DEFENSE,
            Operation.DEFENSE_DECIDE,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            reader = RecordedProvenanceReader(scope.uow.session, workspace_id)
            rendered: list[ContextMemory] = []
            for hit in hits:
                authors = _authors(reader, hit.memory_id)
                rendered.append(
                    ContextMemory(
                        memory_id=hit.memory_id,
                        content=_render(mode, hit.memory_id, authors, hit.content),
                    )
                )
            scope.details["defense"] = self._config.defense.value
            scope.details["stage"] = "context"
            scope.details["result"] = "label"
            scope.details["memory_ids"] = tuple(str(hit.memory_id) for hit in hits)
            scope.details["elapsed_us"] = (time.perf_counter_ns() - started) // 1000
        return tuple(rendered)

    def authorize_action(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        task: str,
        tool_name: str,
        arguments: tuple[tuple[str, str], ...],
        context_ids: tuple[MemoryId, ...],
    ) -> ReasonCode:
        """Return OK or a denial. ``DF3`` does not read ``context_ids`` contents."""
        if self._config.defense not in _ACTION:
            return ReasonCode.OK
        started = time.perf_counter_ns()
        with self._auditor.operation(
            EventCategory.DEFENSE,
            Operation.DEFENSE_DECIDE,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            reason = ReasonCode.OK
            if self._config.defense is DefenseId.LINEAGE:
                requester = _requester(scope.uow.session, actor, workspace_id)
                trusted = _authorities(scope.uow.session, workspace_id, requester)
                reader = RecordedProvenanceReader(scope.uow.session, workspace_id)
                foreign = False
                for memory_id in context_ids:
                    authors = _authors(reader, memory_id)
                    if _untrusted(authors, requester, trusted):
                        foreign = True
                        break
                if foreign and tool_risk(tool_name) >= self._config.risk_threshold:
                    reason = ReasonCode.DEFENSE_LINEAGE
            else:
                reason = authorize_tool(
                    task,
                    tool_name,
                    arguments,
                    source=self._config.policy_source,
                    oracle_tools=self._config.oracle_tools,
                )
            scope.details["defense"] = self._config.defense.value
            scope.details["stage"] = "action"
            scope.details["result"] = "allow" if reason is ReasonCode.OK else "block"
            scope.details["policy_source"] = self._config.policy_source.value
            scope.details["tool_name"] = tool_name
            scope.details["elapsed_us"] = (time.perf_counter_ns() - started) // 1000
        return reason


def _label_mode(config: DefenseConfiguration) -> str | None:
    if config.defense is DefenseId.PROMPT:
        return "delimit"
    if config.defense in _RETRIEVAL and config.retrieval_variant is RetrievalVariant.LABEL:
        return "authors"
    return None


def _render(mode: str, memory_id: str, authors: tuple[str, ...], content: str) -> str:
    listed = ",".join(authors) if authors else "none"
    if mode == "delimit":
        opening = f"<<untrusted-memory {memory_id} authors={listed}>>"
        return f"{opening}\n{content}\n<</untrusted-memory>>"
    return f"recorded-authors: {listed}\n{content}"


def _authors(reader: RecordedProvenanceReader, memory_id: MemoryId) -> tuple[str, ...]:
    try:
        view: RecordedLineageView = reader.lineage(memory_id)
    except MemoryFenceError as error:
        raise MemoryFenceError(
            ReasonCode.DEFENSE_FAILED, "recorded lineage is unavailable"
        ) from error
    return tuple(str(author) for author in view.author_user_ids)


def _untrusted(authors: tuple[str, ...], requester: UserId, trusted: set[str]) -> bool:
    """True when any recorded author is neither the requester nor an authority."""
    requester_id = str(requester)
    return any(author != requester_id and author not in trusted for author in authors)


def _requester(session: Session, actor: PrincipalRef | None, workspace_id: WorkspaceId) -> UserId:
    if actor is None:
        raise MemoryFenceError(ReasonCode.DEFENSE_FAILED, "a defense requires a principal")
    if actor.kind is PrincipalKind.USER:
        return UserId(actor.id)
    row = session.get(AgentRow, actor.id)
    if row is None or row.workspace_id != workspace_id or row.state is not AgentState.ACTIVE:
        raise MemoryFenceError(ReasonCode.DEFENSE_FAILED, "the acting agent cannot be resolved")
    return UserId(row.controlling_user_id)


def _authorities(session: Session, workspace_id: WorkspaceId, requester: UserId) -> set[str]:
    statement = select(InstructionAuthorityRow.authority_user_id).where(
        InstructionAuthorityRow.workspace_id == workspace_id,
        InstructionAuthorityRow.subject_user_id == requester,
    )
    return set(session.scalars(statement))
