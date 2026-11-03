"""Shared test helpers: deterministic ticks, a permissive risk context, and a fake judge."""

from __future__ import annotations

import math
import random

from feed.base import Tick
from judge.client import JudgeAnswer  # noqa: F401 - re-exported for tests
from judge.scripted import ScriptedJudge
from risk.gate import RiskContext
from risk.limits import RiskLimits

T0 = 1_700_000_000_000
BLOCK_MS = 12_000
PINNED = "jev-1.13.0"

LIMITS = RiskLimits(
    max_position_units=1.0,
    max_notional_usd=5000,
    daily_loss_limit_usd=100,
    max_leverage=1.0,
    range_guard_bps=50,
    range_guard_ref_bps=300,
    fee_bps=10,
    maker_fee_bps=2,
    gas_usd=0.5,
    min_edge_margin=0.5,
    pinned_model=PINNED,
    max_stale_ms=2 * BLOCK_MS,
)


def make_ticks(n: int, *, start_ms: int = T0, step_ms: int = 1000, px: float = 2500.0, drift_bps: float = 0.0, spread_bps: float = 2.0, seed: int = 1) -> list[Tick]:
    rng = random.Random(seed)
    mid, ticks = px, []
    for i in range(n):
        mid *= math.exp((drift_bps + rng.gauss(0.0, 2.0)) / 1e4)
        half = mid * spread_bps / 2e4
        ticks.append(Tick(start_ms + i * step_ms, mid - half, mid + half, 5.0, 4.0))
    return ticks


def risk_ctx(**overrides) -> RiskContext:
    base = dict(
        now_ms=T0 + 1000,
        snapshot_as_of_ms=T0,
        mid=2500.0,
        reference_mid=2500.0,
        position_units=0.0,
        equity_usd=10_000.0,
        day_pnl_usd=0.0,
        expected_edge_bps=80.0,
        model_version=PINNED,
    )
    base.update(overrides)
    return RiskContext(**base)


class FakeJudge(ScriptedJudge):
    """Answers every battery the same way: confident 'up', low risk, keep running. Records calls."""
