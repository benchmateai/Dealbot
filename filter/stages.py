"""The five stages, cheapest first.

1. FreeCut    uses only the snapshot already in hand: bench, staleness, sanity, spread, vol band.
2. OneCall    one cheap call each: feed health, resting orders, account equity.
3. HardFacts  code only: best-case edge vs fees+gas, and a risk pre-check with a full-size order.
4. JevStage   one Jev call per surviving candidate (bounded), with the block deadline.
5. FinalPick  the policy scores actions; below-threshold candidates are logged as hold decisions;
              exactly one candidate survives.
"""

from __future__ import annotations

import math
from dataclasses import replace

from broker.base import Order
from filter.funnel import Candidate, FunnelContext, Rejection
from judge.client import Backoff, Judge, JudgeError, JudgeMalformed, JudgeRateLimited, JudgeTimeout
from policy.decide import final_pick
from policy.thresholds import EdgeModel
from policy.weights import PolicyError
from questions.schema import Battery
from risk.gate import RiskContext, RiskGate


class FreeCut:
    name = "free_cut"

    def __init__(self, *, max_spread_bps: float, rv_min_bps: float, rv_max_bps: float, min_ticks: int, max_stale_ms: int, manage: bool = False) -> None:
        self._max_spread = max_spread_bps
        self._rv_min = rv_min_bps
        self._rv_max = rv_max_bps
        self._min_ticks = min_ticks
        self._max_stale = max_stale_ms
        self._manage = manage

    def _check(self, c: Candidate, ctx: FunnelContext) -> Rejection | None:
        s = c.snapshot
        if ctx.bench is not None:
            entry = ctx.bench.is_benched(c.sym, block=ctx.block, now_ms=ctx.now_ms)
            if entry is not None:
                return Rejection(c.sym, self.name, "benched", f"benched since block {entry.since_block} for {entry.reason}")
        age = ctx.now_ms - s.as_of
        if age < 0 or age > self._max_stale:
            return Rejection(c.sym, self.name, "stale_data", f"snapshot age {age} ms, limit {self._max_stale}")
        if not (math.isfinite(s.mid) and s.mid > 0):
            return Rejection(c.sym, self.name, "mid_invalid", f"mid {s.mid!r}")
        if s.n < self._min_ticks:
            return Rejection(c.sym, self.name, "insufficient_ticks", f"{s.n} ticks, need {self._min_ticks}")
        if self._manage:
            return None
        if s.rv_bps is None:
            return Rejection(c.sym, self.name, "rv_unavailable", "not enough history for realized vol")
        if s.spr_bps > self._max_spread:
            return Rejection(c.sym, self.name, "spread_too_wide", f"spread {s.spr_bps} bps, limit {self._max_spread}")
        if not (self._rv_min <= s.rv_bps <= self._rv_max):
            return Rejection(c.sym, self.name, "rv_out_of_band", f"rv {s.rv_bps} bps outside [{self._rv_min}, {self._rv_max}]")
        return None

    def run(self, candidates: list[Candidate], ctx: FunnelContext) -> tuple[list[Candidate], list[Rejection]]:
        kept, rejected = [], []
        for c in candidates:
            r = self._check(c, ctx)
            (rejected if r else kept).append(r or c)
        return kept, rejected


class OneCall:
    name = "one_call"

    def __init__(self, broker, feed, *, min_equity_usd: float, max_feed_lag_ms: int) -> None:
        self._broker = broker
        self._feed = feed
        self._min_equity = min_equity_usd
        self._max_lag = max_feed_lag_ms

    def run(self, candidates: list[Candidate], ctx: FunnelContext) -> tuple[list[Candidate], list[Rejection]]:
        kept, rejected = [], []
        for c in candidates:
            age = self._feed.last_tick_age_ms(c.sym, ctx.now_ms)
            if age is None or age > self._max_lag:
                rejected.append(Rejection(c.sym, self.name, "feed_lagging", f"last tick age {age} ms, limit {self._max_lag}"))
            elif self._broker.open_orders(c.sym):
                rejected.append(Rejection(c.sym, self.name, "order_already_resting", "an order is already resting for this symbol"))
            elif ctx.equity_usd < self._min_equity:
                rejected.append(Rejection(c.sym, self.name, "insufficient_equity", f"equity {ctx.equity_usd:.2f} USD below {self._min_equity}"))
            else:
                kept.append(c)
        return kept, rejected


class HardFacts:
    name = "hard_facts"

    def __init__(self, gate: RiskGate, edge: EdgeModel, order_qty: float, *, order_type: str = "market") -> None:
        self._gate = gate
        self._edge = edge
        self._qty = order_qty
        self._order_type = order_type

    def run(self, candidates: list[Candidate], ctx: FunnelContext) -> tuple[list[Candidate], list[Rejection]]:
        lim = self._gate.limits
        kept, rejected = [], []
        for c in candidates:
            s = c.snapshot
            notional = self._qty * s.mid
            cost = 2 * lim.fee_bps_for(self._order_type) / 1e4 * notional + 2 * lim.gas_usd
            best_edge = self._edge.target_bps / 1e4 * notional
            if best_edge < cost * (1 + lim.min_edge_margin):
                rejected.append(Rejection(c.sym, self.name, "fees_exceed_best_case_edge", f"best case edge {best_edge:.4f} USD vs required {cost * (1 + lim.min_edge_margin):.4f} USD"))
                continue
            rctx = RiskContext(
                now_ms=ctx.now_ms,
                snapshot_as_of_ms=s.as_of,
                mid=s.mid,
                reference_mid=c.reference_mid,
                position_units=ctx.position_units,
                equity_usd=ctx.equity_usd,
                day_pnl_usd=ctx.day_pnl_usd,
                expected_edge_bps=self._edge.target_bps,
                model_version=lim.pinned_model,
            )
            vetoed_sides = {}
            for side in ("buy", "sell"):
                order = Order(f"precheck-{ctx.block}-{c.sym}-{side}", c.sym, side, self._qty, "market", decision_id=ctx.decision_id(c.sym))
                vetoes = self._gate.evaluate(order, rctx, skip=frozenset({"fees_plus_gas", "model_version"}))
                if vetoes:
                    vetoed_sides[side] = vetoes
            if len(vetoed_sides) == 2:
                first = vetoed_sides["buy"][0]
                rejected.append(Rejection(c.sym, self.name, f"risk_precheck:{first.check}", first.detail))
            else:
                kept.append(c)
        return kept, rejected


class JevStage:
    name = "jev"

    def __init__(self, judge: Judge, battery: Battery, backoff: Backoff, *, max_candidates: int = 1) -> None:
        self._judge = judge
        self._battery = battery
        self._questions = battery.wire()
        self._battery_version = battery.version()
        self._backoff = backoff
        self._max = max_candidates
        self._logged_versions: set[str] = set()

    def run(self, candidates: list[Candidate], ctx: FunnelContext) -> tuple[list[Candidate], list[Rejection]]:
        kept, rejected = [], []
        for i, c in enumerate(candidates):
            if ctx.fault:
                rejected.append(Rejection(c.sym, self.name, "battery_fault", ctx.fault))
                continue
            if i >= self._max:
                rejected.append(Rejection(c.sym, self.name, "jev_budget", f"at most {self._max} candidates per block go to Jev"))
                continue
            if self._backoff.is_blocked(ctx.now_ms):
                rejected.append(Rejection(c.sym, self.name, "jev_backoff", f"rate-limit backoff until {self._backoff.blocked_until_ms}"))
                continue
            if ctx.now_ms >= ctx.deadline_ms:
                rejected.append(Rejection(c.sym, self.name, "jev_deadline_passed", "no time left before the next block"))
                continue
            decision_id = ctx.decision_id(c.sym)
            if ctx.log is not None:
                ctx.log.write("snapshot", {"decision_id": decision_id, "bot": ctx.bot, "phase": ctx.phase, "sym": c.sym, "blk": ctx.block, "snapshot": c.snapshot.to_dict(), "tokens": c.snapshot.tokens(), "state": c.state}, ts_ms=ctx.now_ms)
                first_time = self._battery_version not in self._logged_versions
                self._logged_versions.add(self._battery_version)
                ctx.log.write("question", {"decision_id": decision_id, "bot": ctx.bot, "battery_version": self._battery_version, "questions": self._questions if first_time else None, "question_ids": list(self._questions)}, ts_ms=ctx.now_ms)
            try:
                answer = self._judge.ask(decision_id=decision_id, bot=ctx.bot, state=c.state, questions=self._questions, deadline_ms=ctx.deadline_ms, now_ms=ctx.now_ms)
            except JudgeTimeout as exc:
                rejected.append(Rejection(c.sym, self.name, "jev_timeout", f"hold: {exc}"))
                continue
            except JudgeRateLimited as exc:
                delay = self._backoff.note_rate_limited(ctx.now_ms, exc.retry_after_ms)
                rejected.append(Rejection(c.sym, self.name, "jev_rate_limited", f"backing off {delay} ms: {exc}"))
                continue
            except JudgeMalformed as exc:
                ctx.fault = f"malformed question battery (never retried, desk holds until restart): {exc}"
                rejected.append(Rejection(c.sym, self.name, "battery_fault", ctx.fault))
                continue
            except JudgeError as exc:
                rejected.append(Rejection(c.sym, self.name, "jev_unavailable", str(exc)))
                continue
            self._backoff.note_ok()
            labeled = replace(c, decision_id=decision_id, answers=answer.answers, judge=answer.to_dict())
            if ctx.log is not None:
                ctx.log.write("answer", {"decision_id": decision_id, "bot": ctx.bot, "phase": ctx.phase, "sym": c.sym, "blk": ctx.block, **answer.to_dict(), "answers": answer.answers}, ts_ms=ctx.now_ms)
            if ctx.on_labeled is not None:
                ctx.on_labeled(labeled)
            kept.append(labeled)
        return kept, rejected


class FinalPick:
    name = "final_pick"

    def run(self, candidates: list[Candidate], ctx: FunnelContext) -> tuple[list[Candidate], list[Rejection]]:
        picked, rejected = [], []
        for c in candidates:
            try:
                pick = final_pick(ctx.bot, ctx.phase, c.answers or {}, c.snapshot.to_dict())
            except PolicyError as exc:
                rejected.append(Rejection(c.sym, self.name, "policy_error", str(exc)))
                continue
            if pick.is_hold:
                if ctx.log is not None:
                    ctx.log.write("decision", {"decision_id": c.decision_id, "trial_id": ctx.trial_id, "bot": ctx.bot, "phase": ctx.phase, "mode": ctx.mode, "sym": c.sym, "blk": ctx.block, **pick.to_dict(), "order": None, "approved": None, "vetoes": [], "executed": False, "exec_status": "hold"}, ts_ms=ctx.now_ms)
                rejected.append(Rejection(c.sym, self.name, "below_threshold", f"best action p={pick.prob:.3f} < threshold {pick.threshold:.3f}"))
                continue
            picked.append(replace(c, pick=pick))
        if not picked:
            return [], rejected
        best = max(picked, key=lambda c: (c.pick.prob - c.pick.threshold, c.pick.prob))
        for c in picked:
            if c is not best:
                rejected.append(Rejection(c.sym, self.name, "not_best", f"{best.sym} scored higher this block"))
        return [best], rejected
