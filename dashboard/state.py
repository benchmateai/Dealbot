"""Aggregates the event stream into what the page shows: summary tiles, the equity series, the moves
feed, funnel counts, judge stats, calibration and per-decision detail (snapshot, questions, answers
with probabilities, policy scores, vetoes). Bounded memory: deques and an LRU of decision details."""

from __future__ import annotations

import time
from collections import Counter, OrderedDict, deque
from collections.abc import Mapping

from reports.calibration import brier, buckets, forecasts_from_outcomes

TRADE_KINDS = frozenset({"fill", "order", "would_execute", "position_opened", "position_closed", "order_expired"})
MOVE_KINDS = frozenset({"decision", "veto", "trial", "error"}) | TRADE_KINDS


def _num(value, digits: int = 2):
    return None if value is None else round(float(value), digits)


class DeskState:
    def __init__(self, *, max_moves: int = 500, max_rejections: int = 300, max_details: int = 200, max_equity: int = 4000, max_outcomes: int = 20_000) -> None:
        self.summary: dict = {
            "mode": None, "bot": None, "trial_id": None, "model": None, "block": None, "block_ts": None, "last_event_ms": None,
            "equity_usd": None, "day_pnl_usd": None, "position": None, "pending_order": None, "fault": None, "benched": [],
            "pending_outcomes": 0, "registered_trials": None, "realized_pnl_usd": 0.0, "fees_usd": 0.0,
        }
        self.counts: Counter = Counter()
        self.equity: deque = deque(maxlen=max_equity)
        self.moves: deque = deque(maxlen=max_moves)
        self.rejections: deque = deque(maxlen=max_rejections)
        self.details: OrderedDict[str, dict] = OrderedDict()
        self.batteries: dict[str, dict] = {}
        self.funnel_by_stage: Counter = Counter()
        self.funnel_by_check: Counter = Counter()
        self.decisions_by_action: Counter = Counter()
        self.vetoes_by_check: Counter = Counter()
        self.judge: dict = {"calls": 0, "models": Counter(), "latency": deque(maxlen=200), "timeouts": 0, "rate_limited": 0, "unavailable": 0, "backoff": 0}
        self.outcomes: deque = deque(maxlen=max_outcomes)
        self._max_details = max_details
        self._calibration_cache: tuple[int, dict] | None = None
        self._seq = 0

    # ---- ingest -----------------------------------------------------------------------------

    def ingest(self, rec: Mapping) -> None:
        kind = rec.get("kind")
        ts = rec.get("ts")
        if ts is not None and (self.summary["last_event_ms"] is None or ts >= self.summary["last_event_ms"]):
            self.summary["last_event_ms"] = ts
        handler = getattr(self, f"_on_{kind}", None)
        if handler is not None:
            handler(rec)

    def _detail(self, decision_id: str | None) -> dict | None:
        if not decision_id:
            return None
        detail = self.details.get(decision_id)
        if detail is None:
            detail = {"decision_id": decision_id, "snapshot": None, "answer": None, "decision": None, "vetoes": [], "battery_version": None}
            self.details[decision_id] = detail
            while len(self.details) > self._max_details:
                self.details.popitem(last=False)
        else:
            self.details.move_to_end(decision_id)
        return detail

    def _move(self, rec: Mapping, *, title: str, detail: str, status: str, data: dict | None = None) -> None:
        self._seq += 1
        self.moves.append({
            "id": f"m{self._seq}", "ts": rec.get("ts"), "blk": rec.get("blk"), "kind": rec.get("kind"), "sym": rec.get("sym"),
            "title": title, "detail": detail, "status": status, "decision_id": rec.get("decision_id"), "data": data or {},
        })

    def _on_trial(self, rec: Mapping) -> None:
        self.summary["trial_id"] = rec.get("trial_id")
        self.summary["registered_trials"] = rec.get("registered_trials")
        if rec.get("mode"):
            self.summary["mode"] = rec["mode"]
        spec = rec.get("spec") or {}
        if spec.get("bot"):
            self.summary["bot"] = spec["bot"]
        self.counts["trial_runs"] += 1
        self._move(rec, title=f"desk started: run {rec.get('run')} of trial {rec.get('trial_id')}", detail=f"mode {rec.get('mode')}, {rec.get('registered_trials')} trials registered", status="neutral", data={"spec": spec})

    def _on_heartbeat(self, rec: Mapping) -> None:
        s = self.summary
        for key in ("mode", "bot", "trial_id"):
            if rec.get(key):
                s[key] = rec[key]
        s["block"] = rec.get("blk")
        s["block_ts"] = rec.get("ts")
        s["equity_usd"] = rec.get("equity_usd")
        s["day_pnl_usd"] = rec.get("day_pnl_usd")
        s["position"] = rec.get("position")
        s["pending_order"] = rec.get("pending_order")
        s["fault"] = rec.get("fault")
        s["benched"] = rec.get("benched") or []
        s["pending_outcomes"] = rec.get("pending_outcomes") or 0
        if rec.get("equity_usd") is not None:
            self.equity.append({"ts": rec.get("ts"), "blk": rec.get("blk"), "equity": rec["equity_usd"], "day_pnl": rec.get("day_pnl_usd")})
        self.counts["heartbeats"] += 1

    def _on_snapshot(self, rec: Mapping) -> None:
        detail = self._detail(rec.get("decision_id"))
        if detail is not None:
            detail["snapshot"] = {k: v for k, v in rec.items() if k not in ("kind",)}
        self.counts["snapshots"] += 1

    def _on_question(self, rec: Mapping) -> None:
        version = rec.get("battery_version")
        if version and version not in self.batteries:
            self.batteries[version] = rec.get("questions") or {}
        detail = self._detail(rec.get("decision_id"))
        if detail is not None:
            detail["battery_version"] = version

    def _on_answer(self, rec: Mapping) -> None:
        self.judge["calls"] += 1
        self.counts["judge_calls"] += 1
        if rec.get("model"):
            self.judge["models"][rec["model"]] += 1
            self.summary["model"] = rec["model"]
        if rec.get("latency_ms") is not None:
            self.judge["latency"].append(rec["latency_ms"])
        detail = self._detail(rec.get("decision_id"))
        if detail is not None:
            detail["answer"] = {k: v for k, v in rec.items() if k not in ("kind",)}

    def _on_decision(self, rec: Mapping) -> None:
        action = rec.get("action")
        status_text = rec.get("exec_status") or ("hold" if action == "hold" else "unknown")
        self.counts["decisions"] += 1
        self.decisions_by_action[action] += 1
        if action == "hold":
            self.counts["holds"] += 1
            status = "neutral"
        elif rec.get("approved") is False:
            self.counts["vetoed"] += 1
            status = "critical"
        elif rec.get("executed"):
            self.counts["executed"] += 1
            status = "good"
        elif status_text == "shadow":
            self.counts["shadow_approved"] += 1
            status = "info"
        elif status_text == "resting":
            status = "warning"
        else:
            status = "neutral"
        detail = self._detail(rec.get("decision_id"))
        if detail is not None:
            detail["decision"] = {k: v for k, v in rec.items() if k not in ("kind",)}
        prob, threshold = rec.get("prob"), rec.get("threshold")
        edge = rec.get("expected_edge_bps")
        text = f"p {prob:.2f} vs threshold {threshold:.2f}" if isinstance(prob, (int, float)) and isinstance(threshold, (int, float)) else ""
        if isinstance(edge, (int, float)) and action != "hold":
            text += f", edge {edge:+.0f} bps"
        self._move(rec, title=f"{action} {rec.get('sym')} ({rec.get('phase')})", detail=f"{status_text}. {text}".strip(), status=status, data={"scores": rec.get("scores"), "order": rec.get("order"), "vetoes": rec.get("vetoes"), "model": rec.get("model")})

    def _on_veto(self, rec: Mapping) -> None:
        self.counts["vetoes"] += 1
        self.vetoes_by_check[rec.get("check")] += 1
        detail = self._detail(rec.get("decision_id"))
        if detail is not None:
            detail["vetoes"].append({k: v for k, v in rec.items() if k not in ("kind",)})
        self._move(rec, title=f"veto {rec.get('check')} on {rec.get('sym')}", detail=str(rec.get("detail") or ""), status="critical", data={"value": rec.get("value"), "limit": rec.get("limit")})

    def _on_rejection(self, rec: Mapping) -> None:
        check = str(rec.get("check"))
        self.counts["rejections"] += 1
        self.funnel_by_stage[rec.get("stage")] += 1
        self.funnel_by_check[check] += 1
        if check == "jev_timeout":
            self.judge["timeouts"] += 1
        elif check == "jev_rate_limited":
            self.judge["rate_limited"] += 1
        elif check == "jev_unavailable":
            self.judge["unavailable"] += 1
        elif check == "jev_backoff":
            self.judge["backoff"] += 1
        self._seq += 1
        self.rejections.append({"id": f"r{self._seq}", "ts": rec.get("ts"), "blk": rec.get("blk"), "kind": "rejection", "sym": rec.get("sym"), "title": f"{rec.get('stage')}: {check} ({rec.get('sym')})", "detail": str(rec.get("detail") or ""), "status": "neutral", "decision_id": None, "data": {"stage": rec.get("stage"), "check": check, "phase": rec.get("phase")}})

    def _on_order(self, rec: Mapping) -> None:
        order = rec.get("order") or {}
        status = {"filled": "good", "resting": "warning", "rejected": "critical"}.get(rec.get("status"), "neutral")
        self._move(rec, title=f"order {rec.get('status')}: {order.get('side')} {order.get('qty')} {order.get('sym')} {order.get('type')}", detail=f"{'price ' + str(order.get('price')) if order.get('price') is not None else 'market'}{', ' + str(rec.get('reason')) if rec.get('reason') else ''}", status=status, data={"order": order})

    def _on_fill(self, rec: Mapping) -> None:
        self.counts["fills"] += 1
        fee = float(rec.get("fee_usd") or 0) + float(rec.get("gas_usd") or 0)
        realized = float(rec.get("realized_pnl_usd") or 0)
        self.summary["fees_usd"] = round(self.summary["fees_usd"] + fee, 6)
        self.summary["realized_pnl_usd"] = round(self.summary["realized_pnl_usd"] + realized, 6)
        self._move(rec, title=f"fill {rec.get('side')} {rec.get('qty')} {rec.get('sym')} at {rec.get('price')}", detail=f"fees+gas {fee:.4f} USD" + (f", realized {realized:+.4f} USD" if realized else ""), status="good", data={"fee_usd": rec.get("fee_usd"), "gas_usd": rec.get("gas_usd"), "realized_pnl_usd": realized, "order_id": rec.get("order_id")})

    def _on_would_execute(self, rec: Mapping) -> None:
        self.counts["would_execute"] += 1
        order = rec.get("order") or {}
        self._move(rec, title=f"shadow: would {order.get('side')} {order.get('qty')} {order.get('sym')}", detail="approved by risk, not executed (shadow mode)", status="info", data={"order": order})

    def _on_position_opened(self, rec: Mapping) -> None:
        pos = rec.get("position") or {}
        self._move(rec, title=f"position opened: {pos.get('side')} {abs(float(pos.get('qty') or 0))} {rec.get('sym')} at {pos.get('entry_price')}", detail="", status="good", data={"position": pos})

    def _on_position_closed(self, rec: Mapping) -> None:
        pos = rec.get("position") or {}
        self._move(rec, title=f"position closed: {pos.get('side')} {rec.get('sym')}", detail=f"symbol realized to date {float(rec.get('realized_pnl_usd') or 0):+.2f} USD, fees {float(rec.get('fees_usd') or 0):.2f} USD", status="neutral", data={"position": pos})

    def _on_order_expired(self, rec: Mapping) -> None:
        self._move(rec, title=f"order expired: {rec.get('order_id')}", detail="resting entry cancelled after its time to live", status="warning", data={})

    def _on_error(self, rec: Mapping) -> None:
        self.counts["errors"] += 1
        self.summary["fault"] = rec.get("detail")
        self._move(rec, title=f"error in {rec.get('where')}", detail=str(rec.get("detail") or ""), status="critical", data={"action": rec.get("action")})

    def _on_outcome(self, rec: Mapping) -> None:
        if rec.get("status") == "resolved":
            self.counts["outcomes_resolved"] += 1
        else:
            self.counts["outcomes_unresolvable"] += 1
        self.outcomes.append(rec)
        self._calibration_cache = None

    # ---- views ------------------------------------------------------------------------------

    def calibration(self) -> dict:
        key = len(self.outcomes) + self.counts["outcomes_resolved"]
        if self._calibration_cache is not None and self._calibration_cache[0] == key:
            return self._calibration_cache[1]
        forecasts = forecasts_from_outcomes(self.outcomes)
        bks = buckets(forecasts)
        score = brier(forecasts)
        base_rate = (sum(f.y for f in forecasts) / len(forecasts)) if forecasts else None
        view = {
            "n": len(forecasts),
            "brier": _num(score, 4),
            "base_rate": _num(base_rate, 4),
            "buckets": [{"lo": b.lo, "hi": b.hi, "n": b.n, "mean_p": _num(b.mean_p, 4), "observed": _num(b.observed, 4)} for b in bks],
        }
        self._calibration_cache = (key, view)
        return view

    def decision_detail(self, decision_id: str) -> dict | None:
        detail = self.details.get(decision_id)
        if detail is None:
            return None
        questions = self.batteries.get(detail.get("battery_version") or "", {})
        return {**detail, "questions": questions}

    def recent_rejections_by_check(self, since_ms: int | None = None) -> dict[str, int]:
        counter: Counter = Counter()
        for r in self.rejections:
            if since_ms is None or (r.get("ts") or 0) >= since_ms:
                counter[r["data"]["check"]] += 1
        return dict(counter.most_common())

    def to_payload(self, *, include_details: bool = False, now_ms: int | None = None) -> dict:
        latency = list(self.judge["latency"])
        counts = dict(self.counts)
        payload = {
            "generated_ms": int(time.time() * 1000) if now_ms is None else now_ms,
            "summary": {**self.summary, "counts": counts, "judge_latency_ms_mean": _num(sum(latency) / len(latency), 1) if latency else None},
            "equity": list(self.equity),
            "moves": list(self.moves),
            "rejections": list(self.rejections),
            "funnel": {"by_stage": dict(self.funnel_by_stage), "by_check": dict(self.funnel_by_check.most_common()), "recent_by_check": self.recent_rejections_by_check()},
            "decisions_by_action": dict(self.decisions_by_action),
            "vetoes_by_check": dict(self.vetoes_by_check.most_common()),
            "judge": {"calls": self.judge["calls"], "models": dict(self.judge["models"]), "latency": latency, "timeouts": self.judge["timeouts"], "rate_limited": self.judge["rate_limited"], "unavailable": self.judge["unavailable"], "backoff": self.judge["backoff"]},
            "calibration": self.calibration(),
        }
        if include_details:
            payload["details"] = {did: self.decision_detail(did) for did in self.details}
            payload["batteries"] = dict(self.batteries)
        return payload
