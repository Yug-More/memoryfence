"""Defense configuration. Behavior lives in ``memoryfence.defenses``.

The configuration names a protocol condition. It does not carry attack labels or true
provenance. An oracle allowlist is data supplied by the harness; this module does not
look one up.
"""

from typing import Self

from pydantic import Field, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import DefenseId, PolicySource, RetrievalVariant

_RETRIEVAL = frozenset({DefenseId.RETRIEVAL, DefenseId.COMBINED})
_POLICY = frozenset({DefenseId.ACTION, DefenseId.COMBINED})


class DefenseConfiguration(DomainModel):
    """One defense condition and the variants the protocol attaches to it."""

    defense: DefenseId = DefenseId.NONE
    retrieval_variant: RetrievalVariant | None = None
    policy_source: PolicySource = PolicySource.GENERATED
    oracle_tools: tuple[str, ...] = ()
    risk_threshold: int = Field(default=1, ge=0, le=3)

    @model_validator(mode="after")
    def _variants_match_the_defense(self) -> Self:
        uses_retrieval = self.defense in _RETRIEVAL
        uses_policy = self.defense in _POLICY
        if uses_retrieval and self.retrieval_variant is None:
            raise ValueError("DF2 and DF4 require a retrieval variant")
        if not uses_retrieval and self.retrieval_variant is not None:
            raise ValueError("a retrieval variant applies only to DF2 and DF4")
        if self.policy_source is PolicySource.ORACLE and not uses_policy:
            raise ValueError("an oracle policy applies only to DF3 and DF4")
        if self.oracle_tools and self.policy_source is not PolicySource.ORACLE:
            raise ValueError("oracle tools require the oracle policy source")
        if self.policy_source is PolicySource.ORACLE and not self.oracle_tools:
            raise ValueError("an oracle policy requires at least one tool")
        if tuple(self.oracle_tools) != tuple(sorted(set(self.oracle_tools))):
            raise ValueError("oracle tools must be unique and sorted")
        return self
