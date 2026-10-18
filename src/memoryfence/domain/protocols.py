"""Interfaces through which the system under test reaches harness-only storage.

The recorder is *write-only*: the system under test can report what truly happened but
can never read ground truth back.
"""

from collections.abc import Sequence
from typing import Protocol

from memoryfence.domain.deletion import DeletionLedgerEntry, DeletionLedgerEvent
from memoryfence.domain.provenance import TrueProvenanceLink, TrueProvenanceNode


class GroundTruthRecorder(Protocol):
    def record_node(self, node: TrueProvenanceNode) -> None: ...

    def record_links(self, links: Sequence[TrueProvenanceLink]) -> None: ...

    def record_deletion(
        self, event: DeletionLedgerEvent, entries: Sequence[DeletionLedgerEntry]
    ) -> None: ...
