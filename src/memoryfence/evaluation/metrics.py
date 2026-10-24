"""Stage rates. A conditional rate without a positive denominator is undefined."""

from memoryfence.domain.base import DomainModel
from memoryfence.evaluation.stats import Proportion, wilson


class StageCounts(DomainModel):
    trials: int
    retrieved: int
    followed: int
    proposed: int
    executed: int
    legitimate_trials: int
    legitimate_completed: int
    invalid: int
    followed_trials: int | None = None
    retrieved_adjudicated: int | None = None
    followed_and_retrieved: int | None = None
    proposed_and_followed: int | None = None
    executed_and_proposed: int | None = None


class StageRates(DomainModel):
    retrieved: Proportion
    followed: Proportion
    proposed: Proportion
    executed: Proportion
    followed_given_retrieved: Proportion
    proposed_given_followed: Proportion
    executed_given_proposed: Proportion
    legitimate_completion: Proportion


def rates(counts: StageCounts) -> StageRates:
    return StageRates(
        retrieved=wilson(counts.retrieved, counts.trials),
        followed=wilson(counts.followed, _fallback(counts.followed_trials, counts.trials)),
        proposed=wilson(counts.proposed, counts.trials),
        executed=wilson(counts.executed, counts.trials),
        followed_given_retrieved=wilson(
            _fallback(counts.followed_and_retrieved, counts.followed),
            _fallback(counts.retrieved_adjudicated, counts.retrieved),
        ),
        proposed_given_followed=wilson(
            _fallback(counts.proposed_and_followed, counts.proposed), counts.followed
        ),
        executed_given_proposed=wilson(
            _fallback(counts.executed_and_proposed, counts.executed), counts.proposed
        ),
        legitimate_completion=wilson(counts.legitimate_completed, counts.legitimate_trials),
    )


def _fallback(value: int | None, default: int) -> int:
    return default if value is None else value
