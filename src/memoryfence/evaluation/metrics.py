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
        followed=wilson(counts.followed, counts.trials),
        proposed=wilson(counts.proposed, counts.trials),
        executed=wilson(counts.executed, counts.trials),
        followed_given_retrieved=wilson(counts.followed, counts.retrieved),
        proposed_given_followed=wilson(counts.proposed, counts.followed),
        executed_given_proposed=wilson(counts.executed, counts.proposed),
        legitimate_completion=wilson(counts.legitimate_completed, counts.legitimate_trials),
    )
