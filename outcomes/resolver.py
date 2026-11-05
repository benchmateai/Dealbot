"""Registers every graded judgment at decision time and resolves it after its horizon from the
realized price path. Thresholds ("cost", "2rv") are frozen at decision time."""

from __future__ import annotations

from dataclasses import dataclass, field

from feed.base import MarketFeed
from logs.writer import LogWriter
from outcomes.rules import RULES, PathStats, RuleContext, parse_param
from questions.schema import Battery


@dataclass
class Pending:
    decision_id: str
    qid: str
    kind: str
    bot: str
    sym: str
    block: int
    as_of_ms: int
    horizon_blocks: int
    rule: str
    threshold_bps: float
    predicted: object
    chosen: object
    snapshot: dict
    pos_sign: int
    rv_bps: float | None
    cost_bps: float


def _pos_sign(state: dict) -> int:
    pos = state.get("pos") or {}
    side = pos.get("side")
    return 1 if side == "long" else -1 if side == "short" else 0


class OutcomeResolver:
    def __init__(self, log: LogWriter, *, block_ms: int, max_wait_factor: int = 2) -> None:
        self._log = log
        self._block_ms = block_ms
        self._max_wait_factor = max_wait_factor
        self._pending: list[Pending] = []

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def to_state(self) -> list[dict]:
        return [dict(p.__dict__) for p in self._pending]

    def restore_state(self, data: list[dict]) -> None:
        self._pending = [Pending(**p) for p in data]

    def register(self, *, decision_id: str, bot: str, sym: str, block: int, snapshot: dict, state: dict, battery: Battery, answers: dict, ts_ms: int | None = None, expiry_blocks: int | None = None, underlying_sym: str | None = None, underlying_snapshot: dict | None = None) -> int:
        """Queue every graded answer. Contract questions pass `expiry_blocks`; questions graded on the
        underlying pass its symbol and snapshot (with `strike` included for strike-relative rules)."""
        cost_bps = float((state.get("desk") or {}).get("cost_bps") or 0.0)
        registered = 0
        for q in battery.questions:
            res = q.resolution
            answer = answers.get(q.id)
            if res is None or answer is None:
                continue
            horizon = res.horizon_blocks
            if horizon == "expiry":
                if not expiry_blocks or expiry_blocks < 1:
                    self._log.write("outcome", {"decision_id": decision_id, "qid": q.id, "qkind": q.kind, "bot": bot, "sym": sym, "blk": block, "status": "unresolvable:horizon", "rule": res.rule}, ts_ms=ts_ms)
                    continue
                horizon = int(expiry_blocks)
            target_sym, target_snap = sym, snapshot
            if res.on == "underlying":
                if not underlying_sym or not underlying_snapshot:
                    self._log.write("outcome", {"decision_id": decision_id, "qid": q.id, "qkind": q.kind, "bot": bot, "sym": sym, "blk": block, "status": "unresolvable:underlying", "rule": res.rule}, ts_ms=ts_ms)
                    continue
                target_sym, target_snap = underlying_sym, underlying_snapshot
            rv_bps = target_snap.get("rv_bps")
            threshold = parse_param(res.param, cost_bps=cost_bps, rv_bps=rv_bps)
            if threshold is None:
                self._log.write("outcome", {"decision_id": decision_id, "qid": q.id, "qkind": q.kind, "bot": bot, "sym": sym, "blk": block, "status": "unresolvable:threshold", "rule": res.rule}, ts_ms=ts_ms)
                continue
            if q.kind == "noul":
                predicted, chosen = answer.get("noul"), None
            elif q.kind == "choice":
                predicted, chosen = answer.get("probabilities"), answer.get("choice")
            else:
                predicted, chosen = answer.get("probabilities"), answer.get("score")
            self._pending.append(Pending(decision_id, q.id, q.kind, bot, target_sym, block, int(target_snap["as_of"]), horizon, res.rule, threshold, predicted, chosen, target_snap, _pos_sign(state), rv_bps, cost_bps))
            registered += 1
        return registered

    def resolve_due(self, block: int, feed: MarketFeed, *, ts_ms: int | None = None) -> list[dict]:
        resolved: list[dict] = []
        keep: list[Pending] = []
        for p in self._pending:
            if block < p.block + p.horizon_blocks:
                keep.append(p)
                continue
            end_ms = p.as_of_ms + p.horizon_blocks * self._block_ms
            future = [t for t in feed.history(p.sym) if p.as_of_ms <= t.ts < end_ms]
            if not future:
                if block < p.block + p.horizon_blocks * self._max_wait_factor:
                    keep.append(p)
                else:
                    resolved.append(self._write(p, None, "unresolvable:no_data", ts_ms))
                continue
            stats = PathStats.from_ticks(float(p.snapshot["mid"]), future, p.as_of_ms, self._block_ms, p.horizon_blocks)
            ctx = RuleContext(snapshot=p.snapshot, pos_sign=p.pos_sign, rv_bps=p.rv_bps, cost_bps=p.cost_bps)
            realized = RULES[p.rule].fn(stats, p.threshold_bps, ctx)
            status = "resolved" if realized is not None else "unresolvable:context"
            resolved.append(self._write(p, realized, status, ts_ms, stats))
        self._pending = keep
        return resolved

    def _write(self, p: Pending, realized: object, status: str, ts_ms: int | None, stats: PathStats | None = None) -> dict:
        record = {
            "decision_id": p.decision_id,
            "qid": p.qid,
            "qkind": p.kind,
            "bot": p.bot,
            "sym": p.sym,
            "blk": p.block,
            "horizon_blocks": p.horizon_blocks,
            "rule": p.rule,
            "threshold_bps": round(p.threshold_bps, 2),
            "predicted": p.predicted,
            "chosen": p.chosen,
            "realized": realized,
            "status": status,
        }
        if stats is not None:
            record["path"] = {"end_ret_bps": round(stats.end_ret_bps, 2), "max_up_bps": round(stats.max_up_bps, 2), "max_down_bps": round(stats.max_down_bps, 2), "n": len(stats.mids)}
        return self._log.write("outcome", record, ts_ms=ts_ms)
