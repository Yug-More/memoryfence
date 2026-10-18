"""Evaluator-side access to ground truth: labels, run manifests, and read-back.

Only the harness (and, in later phases, evaluation and attack fixtures) may import this
module; import-linter rejects imports from the system under test.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session

from memoryfence.domain.base import DomainModel
from memoryfence.domain.deletion import DeletionLedgerEntry
from memoryfence.domain.enums import RunStatus, SourceOrigin
from memoryfence.domain.errors import ResourceNotFound
from memoryfence.domain.experiments import ExperimentManifest
from memoryfence.domain.ids import (
    DeletionId,
    MemoryId,
    RevisionId,
    RunId,
    SourceId,
    SourceIdField,
    UserId,
    WorkspaceId,
    WorkspaceIdField,
)
from memoryfence.domain.provenance import TrueProvenanceLink, TrueProvenanceNode
from memoryfence.domain.serialization import canonical_json
from memoryfence.domain.time import UtcDatetime
from memoryfence.groundtruth.schema import (
    DeletionLedgerRow,
    ExperimentRunRow,
    SourceLabelRow,
    TrueLinkRow,
    TrueNodeRow,
)
from memoryfence.observability.manifest import finish_manifest
from memoryfence.storage.database import EpisodeDatabase


class SourceLabel(DomainModel):
    source_id: SourceIdField
    workspace_id: WorkspaceIdField
    origin: SourceOrigin
    labeled_at: UtcDatetime


class GroundTruthReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def node(self, memory_id: MemoryId) -> TrueProvenanceNode:
        row = self._session.get(TrueNodeRow, memory_id)
        if row is None:
            raise ResourceNotFound("true provenance node", memory_id)
        return TrueProvenanceNode(
            memory_id=MemoryId(row.memory_id),
            workspace_id=WorkspaceId(row.workspace_id),
            memory_type=row.memory_type,
            source_id=SourceId(row.source_id) if row.source_id is not None else None,
            source_revision_id=(
                RevisionId(row.source_revision_id) if row.source_revision_id is not None else None
            ),
            author_user_id=UserId(row.author_user_id) if row.author_user_id is not None else None,
            created_at=row.created_at,
        )

    def parent_links(self, memory_id: MemoryId) -> tuple[TrueProvenanceLink, ...]:
        statement = (
            select(TrueLinkRow)
            .where(TrueLinkRow.child_id == memory_id)
            .order_by(TrueLinkRow.ordinal)
        )
        return tuple(
            TrueProvenanceLink(
                child_id=MemoryId(row.child_id),
                parent_id=MemoryId(row.parent_id),
                ordinal=row.ordinal,
            )
            for row in self._session.scalars(statement)
        )

    def descendants(self, memory_id: MemoryId) -> set[MemoryId]:
        seen: set[MemoryId] = set()
        frontier = [memory_id]
        while frontier:
            current = frontier.pop()
            statement = select(TrueLinkRow.child_id).where(TrueLinkRow.parent_id == current)
            for child in self._session.scalars(statement):
                if child not in seen:
                    seen.add(MemoryId(child))
                    frontier.append(MemoryId(child))
        return seen

    def true_reach(self, source_id: SourceId) -> set[MemoryId]:
        """Memories truly derived, at any depth, from ``source_id``."""
        statement = select(TrueNodeRow.memory_id).where(TrueNodeRow.source_id == source_id)
        primaries = {MemoryId(value) for value in self._session.scalars(statement)}
        reach = set(primaries)
        for primary in primaries:
            reach |= self.descendants(primary)
        return reach

    def label(self, source_id: SourceId) -> SourceLabel:
        row = self._session.get(SourceLabelRow, source_id)
        if row is None:
            raise ResourceNotFound("source label", source_id)
        return _label(row)

    def labels(self) -> tuple[SourceLabel, ...]:
        statement = select(SourceLabelRow).order_by(SourceLabelRow.source_id)
        return tuple(_label(row) for row in self._session.scalars(statement))

    def ledger(self, deletion_id: DeletionId) -> tuple[DeletionLedgerEntry, ...]:
        statement = (
            select(DeletionLedgerRow)
            .where(DeletionLedgerRow.deletion_id == deletion_id)
            .order_by(DeletionLedgerRow.sequence)
        )
        return tuple(
            DeletionLedgerEntry(
                deletion_id=DeletionId(row.deletion_id),
                sequence=row.sequence,
                effect=row.effect,
                source_id=SourceId(row.source_id),
                revision_id=RevisionId(row.revision_id) if row.revision_id is not None else None,
                memory_id=MemoryId(row.memory_id) if row.memory_id is not None else None,
                content=row.content,
                content_sha256=row.content_sha256,
            )
            for row in self._session.scalars(statement)
        )

    def manifest(self, run_id: RunId) -> ExperimentManifest:
        row = self._session.get(ExperimentRunRow, run_id)
        if row is None:
            raise ResourceNotFound("experiment run", run_id)
        return ExperimentManifest.model_validate_json(row.manifest_json)


def _label(row: SourceLabelRow) -> SourceLabel:
    return SourceLabel(
        source_id=SourceId(row.source_id),
        workspace_id=WorkspaceId(row.workspace_id),
        origin=row.origin,
        labeled_at=row.labeled_at,
    )


class GroundTruthStore:
    def __init__(self, database: EpisodeDatabase) -> None:
        self._database = database

    @contextmanager
    def reader(self) -> Iterator[GroundTruthReader]:
        with self._database.unit_of_work() as uow:
            yield GroundTruthReader(uow.session)

    def label_source(
        self, source_id: SourceId, workspace_id: WorkspaceId, origin: SourceOrigin
    ) -> SourceLabel:
        with self._database.unit_of_work() as uow:
            label = SourceLabel(
                source_id=source_id,
                workspace_id=workspace_id,
                origin=origin,
                labeled_at=uow.now(),
            )
            uow.session.add(
                SourceLabelRow(
                    source_id=label.source_id,
                    workspace_id=label.workspace_id,
                    origin=label.origin,
                    labeled_at=label.labeled_at,
                )
            )
        return label

    def register_run(self, manifest: ExperimentManifest) -> None:
        with self._database.unit_of_work() as uow:
            uow.session.add(
                ExperimentRunRow(
                    run_id=manifest.run_id,
                    status=manifest.status,
                    manifest_json=_manifest_json(manifest),
                    started_at=manifest.started_at,
                    finished_at=manifest.finished_at,
                )
            )

    def finish_run(self, run_id: RunId, status: RunStatus) -> ExperimentManifest:
        with self._database.unit_of_work() as uow:
            row = uow.session.get(ExperimentRunRow, run_id)
            if row is None:
                raise ResourceNotFound("experiment run", run_id)
            stored = ExperimentManifest.model_validate_json(row.manifest_json)
            finished = finish_manifest(stored, status, uow.now())
            row.status = finished.status
            row.finished_at = finished.finished_at
            row.manifest_json = _manifest_json(finished)
        return finished


def _manifest_json(manifest: ExperimentManifest) -> str:
    return canonical_json(json.loads(manifest.model_dump_json()))
