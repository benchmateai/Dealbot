"""The desk loop. Each block: advance the feed, mark equity, resolve due outcomes, then either scan
for a new position (no position open, nothing resting) or manage the one open position. Exactly one
Jev call per candidate per block and at most one order per block.
"""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Sequence

from book.bench import Bench
from book.book import Book, OpenPosition
from broker.base import Broker, Fill, Order
from desk.clock import Block
from desk.config import DeskConfig
from desk.persist import save_checkpoint
from desk.modes import Executor
from feed.base import MarketFeed, Tick
from filter.funnel import Candidate, Funnel, FunnelContext, Rejection
from filter.stages import FinalPick, FreeCut, HardFacts, JevStage, OneCall
from judge.client import Backoff, Judge
from logs.writer import LogWriter
from outcomes.resolver import OutcomeResolver
from policy.thresholds import EDGE
from questions.schema import Battery
from risk.gate import RiskContext, RiskGate
from state.snapshot import InsufficientData, Snapshot, build_snapshot


def round_trip_cost_bps(fee_bps: float, gas_usd: float, notional_usd: float) -> float:
    if notional_usd <= 0:
        return math.inf
    return 2 * fee_bps + 2 * gas_usd / notional_usd * 1e4


def make_state(snapshot: Snapshot, position: OpenPosition | None, *, bot: str, phase: str, cost_bps: float, fee_bps: float, gas_usd: float, block: int) -> dict:
    pos = None
    if position is not None:
        pos = {
            "side": position.side,
            "qty": abs(position.qty),
            "entry": position.entry_price,
            "upnl_bps": round(position.upnl_bps(snapshot.mid), 1),
            "age_blocks": block - position.entry_block,
        }
    return {
        "mkt": snapshot.to_dict(),
        "pos": pos,
        "desk": {"bot": bot, "phase": phase, "cost_bps": round(cost_bps, 2), "fee_bps": fee_bps, "gas_usd": gas_usd},
    }


class Desk:
    def __init__(
        self,
        cfg: DeskConfig,
        *,
        feed: MarketFeed,
        gate: RiskGate,
        broker: Broker,
        book: Book,
        bench: Bench,
        battery: Battery,
        judge: Judge,
        backoff: Backoff,
        resolver: OutcomeResolver,
        executor: Executor,
        log: LogWriter,
        trial_id: str = "",
    ) -> None:
        if battery.bot != cfg.bot:
            raise ValueError(f"battery is for {battery.bot!r}, desk is configured for {cfg.bot!r}")
        self._cfg = cfg
        self._feed = feed
        self._gate = gate
        self._broker = broker
        self._book = book
        self._bench = bench
        self._battery = battery
        self._judge = judge
        self._backoff = backoff
        self._resolver = resolver
        self._executor = executor
        self._log = log
        self._fault: str | None = None
        self._order_seq = 0
        self._trial_id = trial_id
        self._state_file: str | None = None
        self._last_block: int | None = None
        self._order_type = "limit" if cfg.bot == "house" else "market"
        self._bot_fee_bps = cfg.limits.fee_bps_for(self._order_type)
        free_cut = dict(max_spread_bps=cfg.max_spread_bps, rv_min_bps=cfg.rv_min_bps, rv_max_bps=cfg.rv_max_bps, min_ticks=cfg.min_ticks, max_stale_ms=cfg.max_stale_ms)
        self._scan_funnel = Funnel([
            FreeCut(**free_cut),
            OneCall(broker, feed, min_equity_usd=cfg.min_equity_usd, max_feed_lag_ms=cfg.max_feed_lag_ms),
            HardFacts(gate, EDGE[cfg.bot], cfg.order_qty, order_type=self._order_type),
            JevStage(judge, battery, backoff, max_candidates=cfg.max_jev_candidates),
            FinalPick(),
        ])
        self._manage_funnel = Funnel([
            FreeCut(**free_cut, manage=True),
            JevStage(judge, battery, backoff, max_candidates=1),
            FinalPick(),
        ])

    @property
    def fault(self) -> str | None:
        return self._fault

    @property
    def trial_id(self) -> str:
        return self._trial_id

    @property
    def feed(self) -> MarketFeed:
        return self._feed

    @property
    def last_block(self) -> int | None:
        return self._last_block

    # ---- checkpoints --------------------------------------------------------------------------

    def enable_checkpoints(self, path: str) -> None:
        self._state_file = path

    def checkpoint(self) -> dict:
        tail_ms = (self._cfg.rv_window_blocks + 5) * self._cfg.block_ms
        feed_tail = {}
        for sym in self._cfg.symbols:
            hist = self._feed.history(sym)
            if hist:
                cutoff = hist[-1].ts - tail_ms
                feed_tail[sym] = [t.__dict__ for t in hist if t.ts >= cutoff]
        return {
            "saved_ms": int(time.time() * 1000),
            "trial_id": self._trial_id,
            "mode": self._cfg.mode,
            "bot": self._cfg.bot,
            "last_block": self._last_block,
            "order_seq": self._order_seq,
            "fault": self._fault,
            "broker": self._broker.to_state(),
            "book": self._book.to_state(),
            "bench": self._bench.to_state(),
            "outcomes": self._resolver.to_state(),
            "feed": feed_tail,
        }

    def restore(self, data: dict) -> None:
        self._broker.restore_state(data["broker"])
        self._book.restore_state(data["book"])
        self._bench.restore_state(data.get("bench", []))
        self._resolver.restore_state(data.get("outcomes", []))
        self._order_seq = int(data.get("order_seq", 0))
        self._last_block = data.get("last_block")
        self._fault = data.get("fault")
        seed = getattr(self._feed, "seed_history", None)
        if seed is not None:
            for sym, ticks in (data.get("feed") or {}).items():
                seed(sym, [Tick(**t) for t in ticks])
        saved_ms = data.get("saved_ms")
        if self._fault:
            self._log.write("error", {"where": "desk", "blk": self._last_block, "detail": f"resumed with fault: {self._fault}"}, ts_ms=saved_ms)
        else:
            self._log.write("heartbeat", {"blk": self._last_block, "resumed": True, "saved_ms": saved_ms, "position": data["book"].get("position"), "equity_usd": data["book"].get("equity")}, ts_ms=saved_ms)

    @property
    def book(self) -> Book:
        return self._book

    # ---- block loop -------------------------------------------------------------------------

    def warmup(self, until_ms: int) -> None:
        self._ingest(self._feed.advance(until_ms), None)

    def step(self, block: Block) -> None:
        self._ingest(self._feed.advance(block.ts_ms), block)
        marks = self._marks()
        equity = self._broker.equity(marks)
        self._book.mark(equity, block.ts_ms)
        self._resolver.resolve_due(block.number, self._feed, ts_ms=block.ts_ms)
        self._sync_book(block)
        if self._fault is None:
            if self._book.can_scan():
                self._scan(block, equity)
            elif self._book.position is not None:
                self._manage(block, equity)
        if block.number % self._cfg.heartbeat_every_blocks == 0 or self._fault is not None:
            self._heartbeat(block, equity)
        self._last_block = block.number
        if self._state_file:
            save_checkpoint(self._state_file, self.checkpoint())

    def _ingest(self, new_ticks: dict[str, list[Tick]], block: Block | None) -> None:
        for sym, ticks in new_ticks.items():
            for tick in ticks:
                for fill in self._broker.on_tick(sym, tick):
                    self._log.write("fill", {**fill.to_dict(), "decision_id": fill.order_id.rsplit(":", 1)[0], "blk": None if block is None else block.number}, ts_ms=fill.ts)

    def _marks(self) -> dict[str, float]:
        marks = {}
        for sym in self._cfg.symbols:
            hist = self._feed.history(sym)
            if hist:
                marks[sym] = hist[-1].mid
        return marks

    def _sync_book(self, block: Block) -> None:
        pos = self._book.position
        if pos is not None and self._broker.position(pos.sym).qty == 0:
            closed = self._book.close()
            bpos = self._broker.position(closed.sym)
            self._log.write("position_closed", {"decision_id": closed.decision_id, "sym": closed.sym, "blk": block.number, "position": closed.to_dict(), "realized_pnl_usd": bpos.realized_pnl_usd, "fees_usd": bpos.fees_usd}, ts_ms=block.ts_ms)
        pending = self._book.pending
        if pending is not None:
            bpos = self._broker.position(pending.order.sym)
            if bpos.qty != 0:
                self._book.clear_pending()
                self._open_position(pending.order, block)
            elif block.number - pending.placed_block >= self._cfg.pending_order_ttl_blocks:
                self._broker.cancel(pending.order.id)
                self._book.clear_pending()
                self._log.write("order_expired", {"order_id": pending.order.id, "decision_id": pending.order.decision_id, "sym": pending.order.sym, "blk": block.number}, ts_ms=block.ts_ms)

    # ---- candidates and context -----------------------------------------------------------

    def _candidate(self, sym: str, block: Block, phase: str, position: OpenPosition | None) -> Candidate | Rejection:
        hist = self._feed.history(sym)
        account = self._book.account_state(inventory=self._broker.position(sym).qty)
        try:
            snap = build_snapshot(sym, hist, block.ts_ms, block.number, account, block_ms=self._cfg.block_ms, ret_windows_blocks=self._cfg.ret_windows_blocks, rv_window_blocks=self._cfg.rv_window_blocks)
        except InsufficientData as exc:
            return Rejection(sym, "free_cut", "insufficient_data", str(exc))
        cost = round_trip_cost_bps(self._bot_fee_bps, self._cfg.gas_usd, self._cfg.order_qty * snap.mid)
        state = make_state(snap, position, bot=self._cfg.bot, phase=phase, cost_bps=cost, fee_bps=self._bot_fee_bps, gas_usd=self._cfg.gas_usd, block=block.number)
        return Candidate(sym=sym, snapshot=snap, state=state, reference_mid=self._reference_mid(hist, block.ts_ms), cost_bps=cost)

    def _reference_mid(self, hist: Sequence[Tick], as_of_ms: int) -> float | None:
        window = self._cfg.rv_window_blocks * self._cfg.block_ms
        mids = [t.mid for t in hist if as_of_ms - window <= t.ts < as_of_ms]
        return statistics.median(mids) if len(mids) >= 2 else None

    def _context(self, block: Block, phase: str, equity: float, position: OpenPosition | None) -> FunnelContext:
        return FunnelContext(
            block=block.number,
            now_ms=block.ts_ms,
            deadline_ms=block.next_ts_ms - int(self._cfg.deadline_margin_frac * self._cfg.block_ms),
            bot=self._cfg.bot,
            phase=phase,
            mode=self._cfg.mode,
            equity_usd=equity,
            day_pnl_usd=self._book.day_pnl(equity),
            position_units=0.0 if position is None else position.qty,
            position=position,
            bench=self._bench if phase == "entry" else None,
            log=self._log,
            on_labeled=self._register_outcomes,
            trial_id=self._trial_id,
        )

    def _register_outcomes(self, c: Candidate) -> None:
        self._resolver.register(decision_id=c.decision_id, bot=self._cfg.bot, sym=c.sym, block=c.snapshot.blk, snapshot=c.snapshot.to_dict(), state=c.state, battery=self._battery, answers=c.answers or {}, ts_ms=c.snapshot.as_of)

    # ---- scan (no position) ------------------------------------------------------------------

    def _scan(self, block: Block, equity: float) -> None:
        ctx = self._context(block, "entry", equity, None)
        candidates: list[Candidate] = []
        for sym in self._cfg.symbols:
            c = self._candidate(sym, block, "entry", None)
            if isinstance(c, Rejection):
                ctx.reject(c)
            else:
                candidates.append(c)
        result = self._scan_funnel.run(candidates, ctx)
        if ctx.fault:
            self._set_fault(ctx.fault, block)
            return
        for c in result.survivors[:1]:
            self._act_entry(c, block, equity)

    def _act_entry(self, c: Candidate, block: Block, equity: float) -> None:
        pick, snap = c.pick, c.snapshot
        side = "buy" if pick.action == "enter_long" else "sell"
        last = self._feed.history(c.sym)[-1]
        if self._order_type == "limit":
            price = last.bid if side == "buy" else last.ask
        else:
            price = None
        order = Order(self._next_order_id(c.decision_id), c.sym, side, self._cfg.order_qty, self._order_type, price, False, c.decision_id)
        rctx = RiskContext(
            now_ms=block.ts_ms,
            snapshot_as_of_ms=snap.as_of,
            mid=snap.mid,
            reference_mid=c.reference_mid,
            position_units=self._broker.position(c.sym).qty,
            equity_usd=equity,
            day_pnl_usd=self._book.day_pnl(equity),
            expected_edge_bps=pick.expected_edge_bps,
            model_version=(c.judge or {}).get("model"),
        )
        self._decide_and_execute(c, order, rctx, block, "entry")

    # ---- manage (one open position) --------------------------------------------------------

    def _manage(self, block: Block, equity: float) -> None:
        position = self._book.position
        ctx = self._context(block, "manage", equity, position)
        c = self._candidate(position.sym, block, "manage", position)
        if isinstance(c, Rejection):
            ctx.reject(c)
            return
        result = self._manage_funnel.run([c], ctx)
        if ctx.fault:
            self._set_fault(ctx.fault, block)
            return
        for picked in result.survivors[:1]:
            if picked.pick.action == "exit":
                self._act_exit(picked, block, equity, position)

    def _act_exit(self, c: Candidate, block: Block, equity: float, position: OpenPosition) -> None:
        side = "sell" if position.qty > 0 else "buy"
        order = Order(self._next_order_id(c.decision_id), position.sym, side, abs(position.qty), "market", None, True, c.decision_id)
        rctx = RiskContext(
            now_ms=block.ts_ms,
            snapshot_as_of_ms=c.snapshot.as_of,
            mid=c.snapshot.mid,
            reference_mid=c.reference_mid,
            position_units=position.qty,
            equity_usd=equity,
            day_pnl_usd=self._book.day_pnl(equity),
            expected_edge_bps=c.pick.expected_edge_bps,
            model_version=(c.judge or {}).get("model"),
        )
        self._decide_and_execute(c, order, rctx, block, "manage")

    # ---- risk, execution, bookkeeping -------------------------------------------------------

    def _decide_and_execute(self, c: Candidate, order: Order, rctx: RiskContext, block: Block, phase: str) -> None:
        verdict = self._gate.check(order, rctx)
        for veto in verdict.vetoes:
            self._log.write("veto", {"decision_id": c.decision_id, "bot": self._cfg.bot, "phase": phase, "sym": c.sym, "blk": block.number, **veto.to_dict()}, ts_ms=block.ts_ms)
            if phase == "entry":
                self._bench.bench(c.sym, f"risk_veto:{veto.check}", block=block.number, now_ms=block.ts_ms)
        executed, status, reason = False, "vetoed", None
        if verdict.approved:
            result = self._executor.execute(order, verdict.approval, block=block)
            executed, status, reason = result.executed, result.status, result.reason
            if result.executed and result.fill is not None:
                self._after_fill(order, block, phase)
            elif status == "resting":
                self._book.set_pending(order, block.number)
        self._log.write(
            "decision",
            {
                "decision_id": c.decision_id,
                "trial_id": self._trial_id,
                "bot": self._cfg.bot,
                "phase": phase,
                "mode": self._cfg.mode,
                "sym": c.sym,
                "blk": block.number,
                **c.pick.to_dict(),
                "order": order.to_dict(),
                "approved": verdict.approved,
                "vetoes": [v.to_dict() for v in verdict.vetoes],
                "executed": executed,
                "exec_status": status,
                "exec_reason": reason,
                "model": (c.judge or {}).get("model"),
            },
            ts_ms=block.ts_ms,
        )

    def _after_fill(self, order: Order, block: Block, phase: str) -> None:
        bpos = self._broker.position(order.sym)
        if phase == "entry":
            if bpos.qty != 0:
                self._open_position(order, block)
        elif bpos.qty == 0 and self._book.position is not None:
            closed = self._book.close()
            self._log.write("position_closed", {"decision_id": closed.decision_id, "sym": closed.sym, "blk": block.number, "position": closed.to_dict(), "realized_pnl_usd": bpos.realized_pnl_usd, "fees_usd": bpos.fees_usd, "exit_decision_id": order.decision_id}, ts_ms=block.ts_ms)

    def _open_position(self, order: Order, block: Block) -> None:
        bpos = self._broker.position(order.sym)
        position = OpenPosition(order.sym, bpos.qty, bpos.avg_price, block.ts_ms, block.number, order.decision_id, self._cfg.bot)
        self._book.open(position)
        self._log.write("position_opened", {"decision_id": order.decision_id, "sym": order.sym, "blk": block.number, "position": position.to_dict()}, ts_ms=block.ts_ms)

    def _set_fault(self, fault: str, block: Block) -> None:
        self._fault = fault
        self._log.write("error", {"where": "desk", "blk": block.number, "detail": fault, "action": "holding every block until restart"}, ts_ms=block.ts_ms)

    def _next_order_id(self, decision_id: str) -> str:
        self._order_seq += 1
        return f"{decision_id}:{self._order_seq}"

    def _heartbeat(self, block: Block, equity: float) -> None:
        position = self._book.position
        self._log.write(
            "heartbeat",
            {
                "blk": block.number,
                "trial_id": self._trial_id,
                "mode": self._cfg.mode,
                "bot": self._cfg.bot,
                "equity_usd": round(equity, 4),
                "day_pnl_usd": round(self._book.day_pnl(equity), 4),
                "position": None if position is None else position.to_dict(),
                "pending_order": None if self._book.pending is None else self._book.pending.order.id,
                "benched": [e.to_dict() for e in self._bench.entries()],
                "pending_outcomes": self._resolver.pending_count,
                "fault": self._fault,
            },
            ts_ms=block.ts_ms,
        )
