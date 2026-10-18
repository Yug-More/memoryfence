"""Pure, default-deny authorization policy.

Every decision is computed from trusted application state supplied as facts. Nothing in
this package reads memory content, model output, or provenance.
"""

from memoryfence.access.permissions import ROLE_PERMISSIONS
from memoryfence.access.policy import (
    AccessRequest,
    MemoryFacts,
    PrincipalFacts,
    SourceFacts,
    effective_permissions,
    evaluate,
    evaluate_delegation,
)

__all__ = [
    "ROLE_PERMISSIONS",
    "AccessRequest",
    "MemoryFacts",
    "PrincipalFacts",
    "SourceFacts",
    "effective_permissions",
    "evaluate",
    "evaluate_delegation",
]
