"""Recorded and true provenance.

*Recorded* provenance is what the system under test captured and is the only lineage a
defense may read. *True* provenance is evaluator-only ground truth. The true types are
defined here only so that the write-only recorder protocol can name them; no
defense-facing interface returns them.
"""

from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import LineageFidelity, MemoryType, MissingnessMode
from memoryfence.domain.ids import (
    MemoryIdField,
    RevisionIdField,
    SourceIdField,
    UserIdField,
    WorkspaceIdField,
)
from memoryfence.domain.time import UtcDatetime

SeedKey = Annotated[str, StringConstraints(min_length=1, max_length=200)]


def _check_node_shape(
    memory_type: MemoryType, source_id: str | None, author_user_id: str | None
) -> None:
    is_primary = memory_type is MemoryType.PRIMARY
    if is_primary != (source_id is not None) or is_primary != (author_user_id is not None):
        raise ValueError("source_id and author_user_id are set exactly for primary nodes")


class RecordedProvenanceNode(DomainModel):
    """A memory as known to recorded provenance. Nodes outlive deleted memories, so a
    deletion policy never silently erases provenance as a side effect.

    The extraction link (source and platform-recorded author) of a primary memory is
    always recorded; only derivation edges are subject to degradation.
    """

    memory_id: MemoryIdField
    workspace_id: WorkspaceIdField
    memory_type: MemoryType
    source_id: SourceIdField | None
    author_user_id: UserIdField | None
    marked_incomplete: bool
    created_at: UtcDatetime

    @model_validator(mode="after")
    def _shape(self) -> Self:
        _check_node_shape(self.memory_type, self.source_id, self.author_user_id)
        if self.marked_incomplete and self.memory_type is MemoryType.PRIMARY:
            raise ValueError("only derived memories can lose derivation edges")
        return self


class RecordedProvenanceLink(DomainModel):
    child_id: MemoryIdField
    parent_id: MemoryIdField

    @model_validator(mode="after")
    def _not_self_loop(self) -> Self:
        if self.child_id == self.parent_id:
            raise ValueError("a memory cannot derive from itself")
        return self


class RecordedLineageView(DomainModel):
    """Defense-facing lineage of one memory, computed from recorded provenance only."""

    memory_id: MemoryIdField
    workspace_id: WorkspaceIdField
    memory_type: MemoryType
    parent_ids: tuple[MemoryIdField, ...]
    ancestor_ids: tuple[MemoryIdField, ...]
    source_ids: tuple[SourceIdField, ...]
    author_user_ids: tuple[UserIdField, ...]
    marked_incomplete: bool


class TrueProvenanceNode(DomainModel):
    """Evaluator-only snapshot of a memory at creation."""

    memory_id: MemoryIdField
    workspace_id: WorkspaceIdField
    memory_type: MemoryType
    source_id: SourceIdField | None
    source_revision_id: RevisionIdField | None
    author_user_id: UserIdField | None
    created_at: UtcDatetime

    @model_validator(mode="after")
    def _shape(self) -> Self:
        _check_node_shape(self.memory_type, self.source_id, self.author_user_id)
        if (self.memory_type is MemoryType.PRIMARY) != (self.source_revision_id is not None):
            raise ValueError("source_revision_id is set exactly for primary nodes")
        return self


class TrueProvenanceLink(DomainModel):
    """Evaluator-only derivation edge. ``ordinal`` is the parent's position in the input."""

    child_id: MemoryIdField
    parent_id: MemoryIdField
    ordinal: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def _not_self_loop(self) -> Self:
        if self.child_id == self.parent_id:
            raise ValueError("a memory cannot derive from itself")
        return self


class ProvenanceDegradationConfiguration(DomainModel):
    """Seeded degradation of recorded provenance (protocol sections 3.3 and 10).

    The lineage component seed is keyed by template, payload variant, replicate, and the
    edge's identifiers, and deliberately not by the fidelity level, so levels are nested.
    """

    fidelity: LineageFidelity
    missingness: MissingnessMode = MissingnessMode.SILENT
    master_seed: Annotated[int, Field(ge=0, lt=2**63)]
    scenario_template: SeedKey
    payload_variant: SeedKey
    replicate: Annotated[int, Field(ge=0)]

    @property
    def is_confirmatory(self) -> bool:
        return self.missingness is MissingnessMode.SILENT
