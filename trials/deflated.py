"""Deflated Sharpe ratio, after Bailey and López de Prado (2014), "The Deflated Sharpe Ratio".

Searching N strategy variants and keeping the best produces a Sharpe ratio even when every variant
is noise. With V the variance of the Sharpe estimates across trials and g the Euler-Mascheroni
constant, the expected maximum Sharpe of N independent noise trials is

    SR0 = sqrt(V) * ((1 - g) * Z^-1(1 - 1/N) + g * Z^-1(1 - 1/(N e)))

The probabilistic Sharpe ratio PSR(SR*) is the probability that the true Sharpe exceeds SR*, given the
estimate SR over T observations with skewness s and (non-excess) kurtosis k:

    PSR(SR*) = Z[ (SR - SR*) * sqrt(T - 1) / sqrt(1 - s * SR + (k - 1)/4 * SR^2) ]

The deflated Sharpe ratio is DSR = PSR(SR0): the probability that the survivor beats the best noise
trial. The haircut Sharpe is SR - SR0. Everything is per period, not annualized; SR, T and V must
share the same period. Annualize only for display.

The minimum backtest length (Bailey, Borwein, López de Prado and Zhu, 2014) is the sample length in
years below which the expected maximum of N noise trials matches a given true annualized Sharpe.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist

EULER_GAMMA = 0.5772156649015329
_NORMAL = NormalDist()


@dataclass(frozen=True)
class ReturnStats:
    n: int
    mean: float
    std: float
    sharpe: float
    skew: float
    kurt: float

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def return_stats(returns: Sequence[float]) -> ReturnStats | None:
    """Per-period moments of a return series. None when there are fewer than three returns or no variance."""
    n = len(returns)
    if n < 3:
        return None
    mean = sum(returns) / n
    dev = [r - mean for r in returns]
    sum_sq = sum(d * d for d in dev)
    var_sample = sum_sq / (n - 1)
    if var_sample <= 0:
        return None
    m2 = sum_sq / n
    m3 = sum(d**3 for d in dev) / n
    m4 = sum(d**4 for d in dev) / n
    std = math.sqrt(var_sample)
    return ReturnStats(n, mean, std, mean / std, m3 / m2**1.5, m4 / m2**2)


def _expected_max_standard_normal(n_trials: int) -> float:
    return (1 - EULER_GAMMA) * _NORMAL.inv_cdf(1 - 1 / n_trials) + EULER_GAMMA * _NORMAL.inv_cdf(1 - 1 / (n_trials * math.e))


def expected_max_sharpe(n_trials: int, var_sharpe: float) -> float:
    """Expected maximum Sharpe among n_trials independent noise trials whose Sharpe estimates have variance var_sharpe."""
    if n_trials <= 1 or var_sharpe <= 0:
        return 0.0
    return math.sqrt(var_sharpe) * _expected_max_standard_normal(n_trials)


def probabilistic_sharpe(sharpe: float, benchmark: float, n_obs: int, skew: float = 0.0, kurt: float = 3.0) -> float | None:
    """Probability that the true Sharpe exceeds `benchmark`, given the estimate over n_obs returns."""
    if n_obs < 2:
        return None
    inner = 1 - skew * sharpe + (kurt - 1) / 4 * sharpe**2
    if inner <= 0 or not math.isfinite(inner):
        return None
    return _NORMAL.cdf((sharpe - benchmark) * math.sqrt(n_obs - 1) / math.sqrt(inner))


def null_sharpe_variance(n_obs: int) -> float:
    """Sampling variance of a per-period Sharpe estimate under zero true Sharpe and normal returns."""
    return 1.0 / (n_obs - 1) if n_obs > 1 else math.inf


@dataclass(frozen=True)
class Deflated:
    sharpe: float
    n_obs: int
    n_trials: int
    var_sharpe: float
    noise_max_sharpe: float
    haircut_sharpe: float
    dsr: float
    psr_zero: float
    passes_95: bool

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def deflated_sharpe(sharpe: float, n_obs: int, n_trials: int, var_sharpe: float, skew: float = 0.0, kurt: float = 3.0) -> Deflated | None:
    """Deflate a per-period Sharpe by the expected maximum of n_trials noise trials."""
    noise_max = expected_max_sharpe(n_trials, var_sharpe)
    dsr = probabilistic_sharpe(sharpe, noise_max, n_obs, skew, kurt)
    psr_zero = probabilistic_sharpe(sharpe, 0.0, n_obs, skew, kurt)
    if dsr is None or psr_zero is None:
        return None
    return Deflated(sharpe, n_obs, n_trials, var_sharpe, noise_max, sharpe - noise_max, dsr, psr_zero, dsr >= 0.95)


def min_backtest_years(n_trials: int, target_sharpe_annual: float) -> float:
    """Years of data needed before a true annualized Sharpe of `target` stands out from the best of n_trials noise trials."""
    if n_trials <= 1 or target_sharpe_annual <= 0:
        return 0.0
    return (_expected_max_standard_normal(n_trials) / target_sharpe_annual) ** 2
