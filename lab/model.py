"""Pricing Kalshi's crypto contracts on their actual settlement rule, for the lab's shadow strategies.

Every BTC and ETH contract here (15-minute, hourly "above K", hourly ranges) settles on the simple average
of the sixty one-second CF Benchmarks index prints before the close. With the log price a driftless
random walk of variance s2 per second, tau seconds before the close and W = 60:

  tau >= W       log A - log S ~ N(0, s2 * (tau - 2W/3))      the last minute's average moves a third as much
  0 < tau < W    log A = (e * m_obs + tau * log S) / W + N(0, s2 * tau^3 / (3 W^2)),  e = W - tau seconds
                 already averaged, m_obs their mean log price

A spot-price model with no averaging (the paper desk's) overstates the remaining variance by 40 seconds'
worth before the last minute and by far more inside it, which is one reason its forecasts sat too close
to 50/50. The market price is the anchor; a model enters only as a fitted, shrunken deviation from it.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from statistics import NormalDist

_N = NormalDist()
WINDOW_S = 60.0
EPS = 1e-6


def log_average_dist(spot: float, tau_s: float, s2_per_s: float, *, window_s: float = WINDOW_S, observed_log_mean: float | None = None) -> tuple[float, float]:
    """Mean and standard deviation of log(settlement average) seen from now."""
    x = math.log(spot)
    if tau_s >= window_s:
        return x, math.sqrt(max(s2_per_s * (tau_s - 2.0 * window_s / 3.0), 0.0))
    if tau_s <= 0:
        return (observed_log_mean if observed_log_mean is not None else x), 0.0
    elapsed = window_s - tau_s
    obs = observed_log_mean if observed_log_mean is not None else x
    mean = (elapsed * obs + tau_s * x) / window_s
    sd = math.sqrt(max(s2_per_s * tau_s ** 3 / (3.0 * window_s ** 2), 0.0))
    return mean, sd


def _p_above(log_k: float, mean: float, sd: float) -> float:
    if sd <= 0:
        return 1.0 if mean > log_k else 0.0
    return 1.0 - _N.cdf((log_k - mean) / sd)


def p_contract(strike_type: str, floor: float | None, cap: float | None, spot: float, tau_s: float, s2_per_s: float, *,
               window_s: float = WINDOW_S, observed_log_mean: float | None = None) -> float | None:
    """P(YES) for a contract on the settlement average: greater/greater_or_equal (floor), less/less_or_equal
    (cap, or floor when cap is absent) or between (floor..cap). None when a needed strike is missing."""
    if spot is None or spot <= 0 or s2_per_s is None or s2_per_s < 0:
        return None
    mean, sd = log_average_dist(spot, tau_s, s2_per_s, window_s=window_s, observed_log_mean=observed_log_mean)
    kind = (strike_type or "").lower()
    if kind in ("greater", "greater_or_equal", "greater_than_or_equal", "at_or_above", "above"):
        return None if not floor else _p_above(math.log(floor), mean, sd)
    if kind in ("less", "less_or_equal", "less_than", "less_than_or_equal", "at_or_below", "below"):
        k = cap if cap else floor
        return None if not k else 1.0 - _p_above(math.log(k), mean, sd)
    if kind == "between":
        if not floor or not cap:
            return None
        return max(0.0, _p_above(math.log(floor), mean, sd) - _p_above(math.log(cap), mean, sd))
    return None


class EwmaVol:
    """Per-second variance of log price from irregular samples, exponentially weighted with a half-life in
    seconds and floored, so one quiet stretch cannot make the model certain."""

    def __init__(self, half_life_s: float = 1800.0, floor_bps_per_sqrt_s: float = 0.3, initial_bps_per_sqrt_s: float = 1.0) -> None:
        self.half_life_s = half_life_s
        self.floor = (floor_bps_per_sqrt_s / 1e4) ** 2
        self.var = (initial_bps_per_sqrt_s / 1e4) ** 2
        self._last: tuple[int, float] | None = None

    def update(self, ts_ms: int, price: float) -> None:
        if price is None or price <= 0:
            return
        if self._last is not None:
            t0, p0 = self._last
            dt = (ts_ms - t0) / 1000.0
            if 0 < dt <= 600:
                r2 = math.log(price / p0) ** 2
                a = 1.0 - 0.5 ** (dt / self.half_life_s)
                self.var = (1 - a) * self.var + a * (r2 / dt)
            if dt <= 0:
                return
        self._last = (ts_ms, price)

    @property
    def s2_per_s(self) -> float:
        return max(self.var, self.floor)


def logit(p: float) -> float:
    p = min(1 - EPS, max(EPS, p))
    return math.log(p / (1 - p))


def inv_logit(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def pool(market: float, model: float, w: float) -> float:
    """The market price moved toward the model by weight w in log-odds; w = 0 is the market itself."""
    return inv_logit(logit(market) + w * (logit(model) - logit(market)))


def fit_weight(rows: Iterable[tuple[float, float, int]], *, lo: float = -1.0, hi: float = 2.0, steps: int = 61) -> tuple[float, float]:
    """The weight that maximizes the log-likelihood of outcomes y under pool(m, p, w), by grid search;
    returns (w, mean log loss at w). rows are (market, model, y)."""
    rows = list(rows)
    if not rows:
        return 0.0, float("nan")
    best = (0.0, float("inf"))
    for i in range(steps):
        w = lo + (hi - lo) * i / (steps - 1)
        loss = sum(log_loss(pool(m, p, w), y) for m, p, y in rows) / len(rows)
        if loss < best[1]:
            best = (w, loss)
    return best


def log_loss(p: float, y: int) -> float:
    p = min(1 - EPS, max(EPS, p))
    return -math.log(p if y else 1 - p)


def brier(p: float, y: int) -> float:
    return (p - y) ** 2
