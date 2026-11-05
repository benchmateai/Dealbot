"""Pricing Kalshi's crypto contracts on their actual settlement rule, for the lab's shadow strategies.

The model now lives in policy/anchored.py, where the paper desk (v2) trades it; this module re-exports it
so the lab and its tests keep one copy. See that module for the derivation: every BTC and ETH contract here
settles on the simple average of the sixty one-second CF Benchmarks index prints before the close, and a
spot-price model with no averaging (the first desk's) overstates the remaining variance, which is one reason
its forecasts sat too close to 50/50. The market price is the anchor; a model enters only as a fitted,
shrunken deviation from it.
"""

from __future__ import annotations

from policy.anchored import (  # noqa: F401 - re-exported for the lab
    EPS,
    WINDOW_S,
    EwmaVol,
    brier,
    fit_weight,
    inv_logit,
    log_average_dist,
    log_loss,
    logit,
    p_contract,
    pool,
)
