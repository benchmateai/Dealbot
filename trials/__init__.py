"""Trial registry and the deflated Sharpe haircut.

Every configuration the desk runs is a trial: a battery version, a set of weights and thresholds,
risk limits, clip size, symbols, feed. Searching many trials and keeping the best manufactures a
Sharpe ratio even when every trial is noise, so the registry counts every trial ever run and the
report deflates each survivor's Sharpe by the expected maximum of that many noise trials.
"""

from trials.deflated import Deflated, ReturnStats, deflated_sharpe, expected_max_sharpe, min_backtest_years, null_sharpe_variance, probabilistic_sharpe, return_stats
from trials.fingerprint import strategy_spec, trial_id
from trials.registry import TrialEntry, TrialRegistry

__all__ = [
    "Deflated", "ReturnStats", "TrialEntry", "TrialRegistry", "deflated_sharpe", "expected_max_sharpe", "min_backtest_years",
    "null_sharpe_variance", "probabilistic_sharpe", "return_stats", "strategy_spec", "trial_id",
]
