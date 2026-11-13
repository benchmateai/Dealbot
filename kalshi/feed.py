"""Market data for Kalshi 15-minute binaries, with the underlying's own feed alongside.

Each configured series (for example KXETH15M) is a virtual symbol. The feed tracks the series' current
contract, polls its level-1 book into ticks whose bid and ask are the YES prices in dollars, and, when
the contract expires, records a settlement for the desk to apply: the official result when Kalshi has
published it, otherwise provisional from the underlying's last price against the strike.
`snapshot_history` returns only the current contract's ticks, so no snapshot spans a rollover;
`history` keeps every tick so outcomes registered on the previous contract can still be graded.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from feed.base import FeedError, MarketFeed, Tick
from kalshi.api import ContractInfo, KalshiApiError, KalshiClient
from kalshi.model import distance_bps, p_above
from state.snapshot import AccountState, InsufficientData, build_snapshot

log = logging.getLogger("feed.kalshi")


@dataclass(frozen=True)
class Settlement:
    sym: str
    ticker: str
    payout: float
    ts: int
    official: bool
    strike: float | None
    underlying_price: float | None

    def to_dict(self) -> dict:
        data = dict(self.__dict__)
        data["settled_ts"] = data.pop("ts")  # "ts" is the log writer's record timestamp
        return data


class _SeriesState:
    def __init__(self) -> None:
        self.contract: ContractInfo | None = None
        self.refreshed_ms = 0
        self.buffer: list[Tick] = []
        self.hist: list[Tick] = []
        self.contract_start = 0
        self.last_ts = -1
        self.settle_checked_ms = 0


def pick_current(markets: list[ContractInfo], now_ms: int) -> ContractInfo | None:
    """The live contract that expires first: the one being traded now."""
    live = [m for m in markets if m.close_ts is not None and m.close_ts > now_ms and m.status not in ("settled", "finalized", "closed")]
    return min(live, key=lambda m: m.close_ts) if live else None


class KalshiFeed:
    def __init__(
        self,
        series: tuple[str, ...],
        *,
        underlying: Mapping[str, str],
        client: KalshiClient,
        underlying_feed: MarketFeed,
        poll_ms: int = 2000,
        block_ms: int = 12_000,
        refresh_ms: int = 30_000,
        trade_window_s: float = 600.0,
        min_time_left_s: float = 30.0,
        rv_window_blocks: int = 20,
        now_ms: Callable[[], int] | None = None,
        max_history: int = 50_000,
        settle_wait_s: float = 120.0,
        settle_check_s: float = 5.0,
        settle_give_up_s: float = 900.0,
    ) -> None:
        if not series:
            raise FeedError("kalshi feed needs at least one series ticker such as KXETH15M")
        missing = [s for s in series if s not in underlying]
        if missing:
            raise FeedError(f"no underlying product configured for {missing}")
        self.series = tuple(series)
        self.symbols = self.series + tuple(underlying_feed.symbols)
        self._underlying = dict(underlying)
        self._client = client
        self._under = underlying_feed
        self._poll_ms = max(500, int(poll_ms))
        self._block_ms = block_ms
        self._refresh_ms = refresh_ms
        self._trade_window_s = trade_window_s
        self._min_time_left_s = min_time_left_s
        self._rv_window = rv_window_blocks
        self._now = now_ms or (lambda: int(time.time() * 1000))
        self._max_history = max_history
        self._settle_wait_ms = int(settle_wait_s * 1000)
        self._settle_check_ms = int(settle_check_s * 1000)
        self._settle_give_up_ms = int(settle_give_up_s * 1000)
        self._lock = threading.Lock()
        self._state = {s: _SeriesState() for s in self.series}
        self._settlements: list[Settlement] = []
        self.errors = 0
        self.polls = 0
        self.rate_limits = 0
        self._backoff_s = 0.0
        self._backoff_until_ms = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # ---- contract selection and settlement ---------------------------------------------------

    def _pick_current(self, markets: list[ContractInfo], now_ms: int) -> ContractInfo | None:
        return pick_current(markets, now_ms)

    # ---- rate limiting ---------------------------------------------------------------------
    # Kalshi answers 429 when the public endpoints are polled too hard (the egress address may be
    # shared). Every 429 pauses all polling: 2 s, then doubling to 30 s, or longer when Retry-After says
    # so; the first clean answer resets it. A paused feed simply yields no ticks, and the desk's
    # stale-data veto keeps it from trading on old quotes.

    def _paused(self, now_ms: int) -> bool:
        return now_ms < self._backoff_until_ms

    def _back_off(self, now_ms: int, exc: KalshiApiError, what: str) -> None:
        self.rate_limits += 1
        self._backoff_s = min(30.0, max(2.0, self._backoff_s * 2))
        pause = max(self._backoff_s, exc.retry_after_s or 0.0)
        self._backoff_until_ms = now_ms + int(pause * 1000)
        log.warning("%s: rate limited by Kalshi; pausing polls for %.0f s", what, pause)

    def _after_success(self) -> None:
        self._backoff_s = 0.0

    def _refresh(self, sym: str, st: _SeriesState, now_ms: int) -> None:
        expired = st.contract is not None and st.contract.close_ts is not None and now_ms >= st.contract.close_ts
        if expired:
            # Hold the rollover until the expired contract settles, so a position on it is never marked,
            # managed or exited against the next contract's prices. No quotes are polled meanwhile.
            if not self._settle_when_known(sym, st, now_ms):
                return
            st.contract = None
        elif now_ms - st.refreshed_ms < self._refresh_ms and st.contract is not None:
            return
        try:
            markets = self._client.markets(sym)
        except KalshiApiError as exc:
            self.errors += 1
            if exc.rate_limited:
                self._back_off(now_ms, exc, f"{sym}: markets")
            else:
                log.warning("%s: markets: %s", sym, exc)
            return
        self._after_success()
        st.refreshed_ms = now_ms
        current = self._pick_current(markets, now_ms)
        if current is not None and (st.contract is None or current.ticker != st.contract.ticker):
            with self._lock:
                st.contract_start = len(st.hist) + len(st.buffer)
            log.info("%s: current contract %s strike %s closes %s", sym, current.ticker, current.strike, current.close_ts)
        if current is not None or expired:
            st.contract = current

    def _settlement_average(self, sym: str, contract: ContractInfo) -> float | None:
        """Kalshi settles on the average of the last sixty seconds of the CF Benchmarks index before the
        close; the nearest thing the desk sees is the underlying's mid averaged over the same minute."""
        if contract.close_ts is None:
            return None
        hist = self._under.history(self._underlying[sym])
        minute = [t.mid for t in hist if contract.close_ts - 60_000 <= t.ts < contract.close_ts]
        if minute:
            return sum(minute) / len(minute)
        before = [t for t in hist if t.ts < contract.close_ts]
        return before[-1].mid if before else None

    def _settle_when_known(self, sym: str, st: _SeriesState, now_ms: int) -> bool:
        """Settle an expired contract from Kalshi's official result; after `settle_wait_s` without one,
        from the underlying's last-minute average (marked provisional). True once settled or given up."""
        contract = st.contract
        assert contract is not None and contract.close_ts is not None
        if now_ms - st.settle_checked_ms < self._settle_check_ms:
            return False
        st.settle_checked_ms = now_ms
        official = contract.result
        if official not in ("yes", "no"):
            try:
                official = self._client.market(contract.ticker).result
                self._after_success()
            except KalshiApiError as exc:
                self.errors += 1
                if exc.rate_limited:
                    self._back_off(now_ms, exc, f"{sym}: settlement of {contract.ticker}")
                official = None
        average = self._settlement_average(sym, contract)
        if official in ("yes", "no"):
            self._record_settlement(sym, contract, 1.0 if official == "yes" else 0.0, True, average)
            return True
        waited = now_ms - contract.close_ts
        if waited < self._settle_wait_ms:
            return False
        if average is not None:
            settled = contract.settles_yes(average)
            if settled is not None:
                log.warning("%s: no official result for %s after %d s; settling provisionally from the underlying's last-minute average", sym, contract.ticker, waited // 1000)
                self._record_settlement(sym, contract, 1.0 if settled else 0.0, False, average)
                return True
        if waited < self._settle_give_up_ms:
            return False
        log.error("%s: contract %s expired %d s ago without a determinable result; moving on", sym, contract.ticker, waited // 1000)
        return True

    def _record_settlement(self, sym: str, contract: ContractInfo, payout: float, official: bool, average: float | None) -> None:
        with self._lock:
            self._settlements.append(Settlement(sym, contract.ticker, payout, contract.close_ts or 0, official, contract.strike, average))

    def pop_settlements(self) -> list[Settlement]:
        with self._lock:
            out, self._settlements = self._settlements, []
        return out

    # ---- polling ---------------------------------------------------------------------------

    def poll_once(self) -> dict[str, Tick | None]:
        now = self._now()
        out: dict[str, Tick | None] = {}
        for sym, st in self._state.items():
            if self._paused(now):
                out[sym] = None
                continue
            self._refresh(sym, st, now)
            contract = st.contract
            if contract is None or self._paused(now) or (contract.close_ts is not None and now >= contract.close_ts):
                out[sym] = None
                continue
            try:
                yes_bid, yes_ask, bid_qty, ask_qty = self._client.orderbook(contract.ticker)
            except KalshiApiError as exc:
                self.errors += 1
                if exc.rate_limited:
                    self._back_off(now, exc, f"{sym}: orderbook")
                else:
                    log.warning("%s: orderbook: %s", sym, exc)
                out[sym] = None
                continue
            self._after_success()
            if yes_bid is None or yes_ask is None:
                out[sym] = None
                continue
            tick = Tick(now, yes_bid, yes_ask, bid_qty, ask_qty)
            if not tick.is_sane():
                out[sym] = None
                continue
            with self._lock:
                if tick.ts > st.last_ts:
                    st.buffer.append(tick)
                    st.last_ts = tick.ts
            out[sym] = tick
        self.polls += 1
        return out

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                self.poll_once()
            except Exception as exc:  # noqa: BLE001 - keep polling
                self.errors += 1
                log.warning("poll failed: %s", type(exc).__name__)
            self._stop.wait(max(0.0, self._poll_ms / 1000 - (time.monotonic() - started)))

    def start(self) -> KalshiFeed:
        if hasattr(self._under, "start"):
            self._under.start()
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="kalshi-feed", daemon=True)
            self._thread.start()
        return self

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if hasattr(self._under, "close"):
            self._under.close()

    # ---- MarketFeed ------------------------------------------------------------------------

    def advance(self, until_ms: int) -> dict[str, list[Tick]]:
        out = dict(self._under.advance(until_ms))
        with self._lock:
            for sym, st in self._state.items():
                ready = [t for t in st.buffer if t.ts < until_ms]
                st.buffer = [t for t in st.buffer if t.ts >= until_ms]
                st.hist.extend(ready)
                if len(st.hist) > self._max_history:
                    drop = len(st.hist) - self._max_history
                    del st.hist[:drop]
                    st.contract_start = max(0, st.contract_start - drop)
                out[sym] = ready
        return out

    def history(self, sym: str) -> list[Tick]:
        st = self._state.get(sym)
        return self._under.history(sym) if st is None else st.hist

    def snapshot_history(self, sym: str) -> list[Tick]:
        st = self._state.get(sym)
        if st is None:
            return self._under.history(sym)
        return st.hist[st.contract_start:]

    def seed_history(self, sym: str, ticks: list[Tick]) -> None:
        st = self._state.get(sym)
        if st is None:
            seed = getattr(self._under, "seed_history", None)
            if seed is not None:
                seed(sym, ticks)
        elif ticks:
            st.hist = sorted(ticks, key=lambda t: t.ts)
            st.contract_start = 0

    def last_tick_age_ms(self, sym: str, now_ms: int) -> int | None:
        st = self._state.get(sym)
        if st is None:
            return self._under.last_tick_age_ms(sym, now_ms)
        return None if not st.hist else now_ms - st.hist[-1].ts

    # ---- what the desk needs beyond ticks ----------------------------------------------------

    def contract(self, sym: str) -> ContractInfo | None:
        st = self._state.get(sym)
        return None if st is None else st.contract

    def underlying_symbol(self, sym: str) -> str | None:
        return self._underlying.get(sym)

    def extra_state(self, sym: str, now_ms: int, *, block: int = 0) -> dict | None:
        """The contract block for Jev's state: strike, time left, market prices, and the code-owned probability."""
        st = self._state.get(sym)
        if st is None or st.contract is None:
            return None
        c = st.contract
        expires_in = c.expires_in_s(now_ms)
        under_sym = self._underlying[sym]
        under_hist = self._under.history(under_sym)
        spot = under_hist[-1].mid if under_hist else None
        rv_bps = None
        under_snapshot = None
        if under_hist:
            try:
                snap = build_snapshot(under_sym, under_hist, now_ms, block, AccountState(0.0, 0.0, 0.0, 0.0), block_ms=self._block_ms, rv_window_blocks=self._rv_window)
                rv_bps, spot, under_snapshot = snap.rv_bps, snap.mid, snap.to_dict()
            except InsufficientData:
                pass
        last = st.hist[-1] if st.hist else None
        model_p = p_above(spot, c.strike, expires_in, rv_bps, self._block_ms / 1000) if spot and c.strike and expires_in is not None else None
        tradable = expires_in is not None and self._min_time_left_s <= expires_in <= self._trade_window_s
        return {
            "ticker": c.ticker,
            "title": c.title,
            "strike": c.strike,
            "strike_type": c.strike_type,
            "expires_in_s": None if expires_in is None else round(expires_in),
            "yes_bid": None if last is None else last.bid,
            "yes_ask": None if last is None else last.ask,
            "spread": None if last is None else round(last.ask - last.bid, 4),
            "underlying": under_sym,
            "spot": spot,
            "distance_bps": None if not (spot and c.strike) else round(distance_bps(spot, c.strike), 1),
            "underlying_rv_bps": rv_bps,
            "model_p_yes": None if model_p is None else round(model_p, 4),
            "tradable": tradable,
            "underlying_snapshot": under_snapshot,
        }
