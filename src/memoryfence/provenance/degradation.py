"""Seeded, nested degradation of recorded provenance (protocol sections 3.3 and 10).

A component seed is the first 8 bytes of SHA-256 over the canonical JSON array
``[master_seed, component, *keys]``, read as a big-endian unsigned integer. For the
``lineage`` component the keys are template, payload variant, replicate, child ID, and
parent ID. The edge's uniform value is that seed divided by 2**64, and the edge is
recorded if and only if the value is below the fidelity level. The fidelity level is not
a key, so every edge kept at a lower level is also kept at every higher level.
"""

import hashlib
from collections.abc import Sequence

from memoryfence.domain.ids import MemoryId
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.domain.serialization import canonical_json

LINEAGE_COMPONENT = "lineage"


def component_seed(master_seed: int, component: str, keys: Sequence[str | int]) -> int:
    payload = canonical_json([master_seed, component, *keys]).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def edge_uniform(
    config: ProvenanceDegradationConfiguration, child_id: MemoryId, parent_id: MemoryId
) -> float:
    seed = component_seed(
        config.master_seed,
        LINEAGE_COMPONENT,
        (config.scenario_template, config.payload_variant, config.replicate, child_id, parent_id),
    )
    return seed / 2**64


def retains_edge(
    config: ProvenanceDegradationConfiguration, child_id: MemoryId, parent_id: MemoryId
) -> bool:
    return edge_uniform(config, child_id, parent_id) < config.fidelity.retention_probability
