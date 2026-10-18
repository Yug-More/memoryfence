"""Descriptive intervals and paired tests named in the protocol.

Mixed-effects models, the Cochran-Armitage trend test, and TOST are not implemented.
A number returned here is a calculation on the supplied counts, not a study finding.
"""

import math

from memoryfence.domain.base import DomainModel
from memoryfence.domain.errors import DomainValidationError

_Z_95 = 1.959963984540054


class Proportion(DomainModel):
    successes: int
    trials: int
    point: float | None
    lower: float | None
    upper: float | None
    undefined: bool


def wilson(successes: int, trials: int, *, z: float = _Z_95) -> Proportion:
    """Two-sided Wilson interval. Zero trials are undefined, not a rate of zero."""
    if trials < 0 or successes < 0 or successes > trials:
        raise DomainValidationError("a proportion needs 0 <= successes <= trials")
    if trials == 0:
        return Proportion(successes=0, trials=0, point=None, lower=None, upper=None, undefined=True)
    phat = successes / trials
    z2 = z * z
    denom = 1 + z2 / trials
    center = (phat + z2 / (2 * trials)) / denom
    margin = z * math.sqrt(phat * (1 - phat) / trials + z2 / (4 * trials * trials)) / denom
    return Proportion(
        successes=successes,
        trials=trials,
        point=phat,
        lower=max(0.0, center - margin),
        upper=min(1.0, center + margin),
        undefined=False,
    )


def mcnemar_exact(discordant_b: int, discordant_c: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts b and c."""
    if discordant_b < 0 or discordant_c < 0:
        raise DomainValidationError("discordant counts cannot be negative")
    total = discordant_b + discordant_c
    if total == 0:
        return 1.0
    smaller = min(discordant_b, discordant_c)
    numerator = 0
    for index in range(smaller + 1):
        numerator += _binom(total, index)
    denominator = 1
    for _bit in range(total):
        denominator *= 2
    value = (2.0 * numerator) / denominator
    if value > 1.0:
        return 1.0
    return value


def _binom(total: int, choose: int) -> int:
    result = 1
    for index in range(choose):
        result = result * (total - index) // (index + 1)
    return result


def paired_risk_difference(discordant_b: int, discordant_c: int, pairs: int) -> Proportion:
    """Paired risk difference (b - c) / pairs, with a Wald interval. Not TOST."""
    if pairs <= 0:
        return Proportion(successes=0, trials=0, point=None, lower=None, upper=None, undefined=True)
    if discordant_b + discordant_c > pairs:
        raise DomainValidationError("discordant pairs cannot exceed the number of pairs")
    point = (discordant_b - discordant_c) / pairs
    variance = (discordant_b + discordant_c) / pairs - point**2
    margin = _Z_95 * math.sqrt(max(variance, 0.0) / pairs)
    return Proportion(
        successes=discordant_b,
        trials=pairs,
        point=point,
        lower=point - margin,
        upper=point + margin,
        undefined=False,
    )


def holm(p_values: tuple[float, ...]) -> tuple[float, ...]:
    """Holm adjusted p-values in the original order. Empty input stays empty."""
    if any(value < 0 or value > 1 for value in p_values):
        raise DomainValidationError("a p-value must be between 0 and 1")
    count = len(p_values)
    order = sorted(range(count), key=lambda index: (p_values[index], index))
    adjusted = [0.0] * count
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (count - rank) * p_values[index]))
        adjusted[index] = running
    return tuple(adjusted)
