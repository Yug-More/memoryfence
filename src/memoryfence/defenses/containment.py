"""Opt-in containment from observable recorded metadata, never evaluator ancestry."""

from memoryfence.defenses.suite import DefenseSuite
from memoryfence.domain.base import DomainModel
from memoryfence.domain.defenses import DefenseConfiguration
from memoryfence.domain.enums import (
    EventCategory,
    MemoryType,
    ModelPurpose,
    Operation,
    Permission,
    SourceDeletionState,
)
from memoryfence.domain.errors import MemoryFenceError, ReasonCode
from memoryfence.domain.ids import MemoryId, WorkspaceId
from memoryfence.domain.model import LanguageModel, ModelRequest, ModelResponse
from memoryfence.domain.principals import PrincipalRef
from memoryfence.memory.retrieve import RetrievalHit
from memoryfence.observability import Auditor
from memoryfence.provenance.recorded import RecordedProvenanceReader
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.storage.schema import SourceRow
from memoryfence.workspace.authority import Authorizer


class ContainmentDecision(DomainModel):
    memory_id: MemoryId
    allowed: bool
    reason: str


class ContainmentGuard:
    """Quarantine known incomplete/orphan/stale lineage without repairing it.

    Marked incompleteness is trusted operational writer metadata. An unmarked lost
    branch can remain undetected if another active source path survives. This is
    not an assurance that every allowed graph is complete.
    """

    def __init__(self, database: EpisodeDatabase, auditor: Auditor) -> None:
        self._database = database
        self._auditor = auditor

    def assess(
        self, actor: PrincipalRef | None, workspace_id: WorkspaceId, memory_id: MemoryId
    ) -> ContainmentDecision:
        with self._database.system_read_session() as session:
            authorizer = Authorizer(session)
            _row, facts = authorizer.memory(memory_id, actor)
            authorizer.require(actor, Permission.MEMORY_READ, workspace_id, facts)
            reader = RecordedProvenanceReader(session, workspace_id)
            try:
                view = reader.lineage(memory_id)
                nodes = [reader.node(n) for n in (memory_id, *view.ancestor_ids)]
            except MemoryFenceError:
                return ContainmentDecision(
                    memory_id=memory_id, allowed=False, reason="lineage_unavailable"
                )
            if any(n.marked_incomplete for n in nodes):
                reason = "marked_incomplete"
            elif view.memory_type is MemoryType.DERIVED and not view.source_ids:
                reason = "orphan"
            elif any(
                (source := session.get(SourceRow, source_id)) is None
                or source.deletion_state is not SourceDeletionState.ACTIVE
                for source_id in view.source_ids
            ):
                reason = "source_unavailable"
            else:
                reason = "no_observed_gap"
        return ContainmentDecision(
            memory_id=memory_id, allowed=reason == "no_observed_gap", reason=reason
        )

    def filter(
        self, actor: PrincipalRef | None, workspace_id: WorkspaceId, hits: tuple[RetrievalHit, ...]
    ) -> tuple[RetrievalHit, ...]:
        decisions = [self.assess(actor, workspace_id, hit.memory_id) for hit in hits]
        allowed = {d.memory_id for d in decisions if d.allowed}
        with self._auditor.operation(
            EventCategory.DEFENSE, Operation.DEFENSE_DECIDE, actor=actor, workspace_id=workspace_id
        ) as scope:
            scope.details["stage"] = "expanded_containment"
            scope.details["kept_ids"] = tuple(str(i) for i in sorted(allowed))
            scope.details["excluded_ids"] = tuple(
                str(d.memory_id) for d in decisions if not d.allowed
            )
            scope.details["reasons"] = tuple(
                f"{d.memory_id}:{d.reason}" for d in decisions if not d.allowed
            )
        return tuple(hit for hit in hits if hit.memory_id in allowed)


class GuardedTransformBackend:
    """Re-check operational input lineage before requesting re-derivation."""

    def __init__(
        self, backend: LanguageModel, guard: ContainmentGuard, actor: PrincipalRef
    ) -> None:
        self._backend = backend
        self._guard = guard
        self._actor = actor

    def complete(self, request: ModelRequest) -> ModelResponse:
        if request.purpose is ModelPurpose.TRANSFORM:
            for item in request.context:
                decision = self._guard.assess(self._actor, request.workspace_id, item.memory_id)
                if not decision.allowed:
                    raise MemoryFenceError(
                        ReasonCode.DEFENSE_FAILED,
                        f"re-derivation input quarantined: {decision.reason}",
                    )
        return self._backend.complete(request)


class ContainedDefense(DefenseSuite):
    """Opt-in AgentLoop/gateway adapter; legacy DefenseSuite defaults are unchanged."""

    def __init__(
        self, config: DefenseConfiguration, auditor: Auditor, database: EpisodeDatabase
    ) -> None:
        super().__init__(config, auditor)
        self._containment = ContainmentGuard(database, auditor)

    def filter_retrieval(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        hits: tuple[RetrievalHit, ...],
    ) -> tuple[RetrievalHit, ...]:
        return self._containment.filter(
            actor, workspace_id, super().filter_retrieval(actor, workspace_id, hits)
        )

    def authorize_action(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        task: str,
        tool_name: str,
        arguments: tuple[tuple[str, str], ...],
        context_ids: tuple[MemoryId, ...],
    ) -> ReasonCode:
        for memory_id in context_ids:
            if not self._containment.assess(actor, workspace_id, memory_id).allowed:
                return ReasonCode.DEFENSE_LINEAGE
        return super().authorize_action(
            actor, workspace_id, task, tool_name, arguments, context_ids
        )
