"""Shared test helpers: deterministic ticks, a permissive risk context, and a fake judge."""

from __future__ import annotations

import math
import random

from feed.base import Tick
from judge.client import JudgeAnswer
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


class FakeJudge:
    """Answers every battery the same way: confident 'up', low risk, keep running. Records calls."""

    def __init__(self, model: str, *, nouls: dict[str, float] | None = None, default_noul: float = 0.05, favorite: str = "up", raise_exc: Exception | None = None) -> None:
        self.model = model
        self.calls: list[tuple[str, str]] = []
        self._nouls = {"keep_running": 0.95, **(nouls or {})}
        self._default_noul = default_noul
        self._favorite = favorite
        self._raise = raise_exc

    def ask(self, *, decision_id: str, bot: str, state: dict, questions: dict, deadline_ms: int, now_ms: int) -> JudgeAnswer:
        self.calls.append((decision_id, state["desk"]["phase"]))
        if self._raise is not None:
            raise self._raise
        answers: dict[str, dict] = {}
        for qid, q in questions.items():
            kind = q["type"]
            if kind == "noul":
                answers[qid] = {"type": "noul", "noul": self._nouls.get(qid, self._default_noul)}
            elif kind == "choice":
                labels = list(q["criteria"])
                fav = self._favorite if self._favorite in labels else ("trending" if "trending" in labels else labels[0])
                probs = {label: 0.02 for label in labels}
                probs[fav] = round(1 - 0.02 * (len(labels) - 1), 4)
                answers[qid] = {"type": "choice", "choice": fav, "confidence": probs[fav], "probabilities": probs}
            else:
                n = len(q["criteria"])
                probs = {str(i): (0.9 if i == 0 else round(0.1 / (n - 1), 4)) for i in range(n)}
                answers[qid] = {
                    "type": "score",
                    "score": sum(int(k) * v for k, v in probs.items()),
                    "confidence": 0.9,
                    "legend": {str(i): c for i, c in enumerate(q["criteria"])},
                    "probabilities": probs,
                }
        return JudgeAnswer(decision_id, self.model, self.model, answers, None, None, 1, "fake")
