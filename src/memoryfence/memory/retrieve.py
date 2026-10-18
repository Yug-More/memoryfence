"""Deterministic lexical retrieval over the current memory state.

Ranking is the size of the intersection between case-folded alphanumeric tokens of the
query and of the memory. Ties break by memory identifier. A zero score is omitted.
This is not an embedding index. Results are limited to memories the principal may read
in the requested workspace. Revoked memories and other workspaces are not candidates.
"""

import re
import time

from sqlalchemy import select

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import EventCategory, MemoryState, Operation, Permission
from memoryfence.domain.errors import AuthorizationDenied, DomainValidationError, ReasonCode
from memoryfence.domain.ids import MemoryId, WorkspaceId
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.serialization import sha256_hex
from memoryfence.domain.sources import Content
from memoryfence.observability import Auditor
from memoryfence.storage.schema import MemoryRow
from memoryfence.workspace.authority import Authorizer

_TOKEN = re.compile(r"[a-z0-9]+")
RANK_BASIS = "token_overlap"


class RetrievalHit(DomainModel):
    memory_id: MemoryId
    content: Content
    score: int


class RetrievalResult(DomainModel):
    query_sha256: str
    candidate_count: int
    excluded_count: int
    rank_basis: str
    elapsed_us: int
    hits: tuple[RetrievalHit, ...]


class RetrievalService:
    def __init__(self, auditor: Auditor) -> None:
        self._auditor = auditor

    def retrieve(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        query: str,
        *,
        top_k: int = 5,
    ) -> RetrievalResult:
        if top_k < 1:
            raise DomainValidationError("top_k must be at least 1")
        started = time.perf_counter_ns()
        with self._auditor.operation(
            EventCategory.RETRIEVAL,
            Operation.MEMORY_RETRIEVE,
            actor=actor,
            workspace_id=workspace_id,
        ) as scope:
            authorizer = Authorizer(scope.uow.session)
            decision, _facts = authorizer.decide(actor, Permission.MEMORY_READ, workspace_id)
            # memory.read is only defined for a specific memory. A workspace-level probe
            # that returns unsupported means the principal cleared membership and role
            # checks, so per-memory decisions below are the real filter.
            if not decision.allowed and decision.reason is not ReasonCode.UNSUPPORTED_REQUEST:
                raise AuthorizationDenied(decision)
            rows = scope.uow.session.scalars(
                select(MemoryRow)
                .where(
                    MemoryRow.workspace_id == workspace_id,
                    MemoryRow.state == MemoryState.ACTIVE,
                )
                .order_by(MemoryRow.id)
            )
            query_tokens = _tokens(query)
            ranked: list[tuple[int, MemoryRow]] = []
            excluded = 0
            candidates = 0
            for row in rows:
                candidates += 1
                _row, facts = authorizer.memory(MemoryId(row.id), actor)
                decision, _principal = authorizer.decide(
                    actor, Permission.MEMORY_READ, workspace_id, facts
                )
                if not decision.allowed:
                    excluded += 1
                    continue
                score = _overlap(query_tokens, _tokens(row.content))
                if score > 0:
                    ranked.append((score, row))
            ranked.sort(key=lambda item: (-item[0], item[1].id))
            chosen = ranked[:top_k]
            hits = tuple(
                RetrievalHit(memory_id=MemoryId(row.id), content=row.content, score=score)
                for score, row in chosen
            )
            elapsed_us = (time.perf_counter_ns() - started) // 1000
            result = RetrievalResult(
                query_sha256=sha256_hex(query),
                candidate_count=candidates,
                excluded_count=excluded,
                rank_basis=RANK_BASIS,
                elapsed_us=elapsed_us,
                hits=hits,
            )
            scope.details["query_sha256"] = result.query_sha256
            scope.details["candidate_count"] = result.candidate_count
            scope.details["excluded_count"] = result.excluded_count
            scope.details["returned_ids"] = tuple(hit.memory_id for hit in hits)
            scope.details["rank_basis"] = RANK_BASIS
            scope.details["elapsed_us"] = result.elapsed_us
        return result


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.casefold()))


def _overlap(query: frozenset[str], content: frozenset[str]) -> int:
    if not query:
        return 0
    return sum(1 for token in query if token in content)
