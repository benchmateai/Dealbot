"""The code-owned baseline for a binary on an underlying price: with no drift and lognormal moves,
P(S_T > K) = Phi( ln(S/K) / (sigma * sqrt(tau)) ). Jev is asked only about what this misses."""

from __future__ import annotations

import math
from statistics import NormalDist

_NORMAL = NormalDist()


def distance_bps(spot: float, strike: float) -> float:
    return 1e4 * math.log(spot / strike)


def sigma_for_horizon(sigma_block_bps: float, block_s: float, tau_s: float) -> float:
    """Per-block realized vol (bps) scaled to a horizon of tau_s seconds, as a fraction."""
    return sigma_block_bps / 1e4 * math.sqrt(max(tau_s, 0.0) / block_s)


def p_above(spot: float, strike: float, tau_s: float, sigma_block_bps: float | None, block_s: float, *, floor_sigma: float = 1e-6) -> float | None:
    """Probability the underlying ends above the strike after tau_s seconds; None without a vol estimate."""
    if sigma_block_bps is None or sigma_block_bps <= 0 or spot <= 0 or strike <= 0 or block_s <= 0:
        return None
    if tau_s <= 0:
        return 1.0 if spot > strike else 0.0
    sigma = max(sigma_for_horizon(sigma_block_bps, block_s, tau_s), floor_sigma)
    return _NORMAL.cdf(math.log(spot / strike) / sigma)
