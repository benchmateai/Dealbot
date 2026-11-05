"""The lab's live-feed recorder: Kalshi's authenticated WebSocket, market data only (docs/lab/kalshi_interfaces.md).

It needs the production key in KALSHI_PROD_API_KEY_ID / KALSHI_PROD_PRIVATE_KEY and exits with code 2
without it. One connection carries:
  orderbook_delta     the full book of every watched market, from a snapshot and its deltas, checked by seq;
                      on a gap it asks for fresh snapshots of every market (use_yes_price is set explicitly)
  trade               every print in the watched markets
  cfbenchmarks_value  BRTI and ETHUSD_RTI about once a second, with Kalshi's trailing 60-second average
                      and, in the last minute of each quarter hour, the settlement window's average so far

Watched markets, found over public REST at the lab's request budget (in a worker thread, so the socket is
always read; slow lookups wait while a quarter-hour is near, so the new 15-minute contracts are found
within seconds of opening). A market can be in more than one set:
  15m  the open KXBTC15M and KXETH15M contracts                  book every 2 s in the last 3 minutes, else 10 s
  E    the markets with the largest active liquidity-incentive pools
                                     full-depth book when it changes, at most every 15 s, at least every 60 s
  F    markets closing in 1-30 days with a 1-10 cent YES ask, by 24-hour volume
                                                  book when it changes, at most every 60 s, at least every 5 min

A book is written only while the feed is provably alive (a message or an answered ping within STALE_MS),
only once it has a snapshot, and never while crossed. A book still waiting for its snapshot is asked for
again, then dropped; every book is re-snapshotted every SNAPSHOT_REFRESH_S, counting any drift. A
subscription Kalshi ends (or any error that leaves its state in doubt) drops the connection, which is
set up again from scratch. Settlements of F markets are fetched after the close with growing waits.

It writes the normalized records lab/strategies/maker_common.py describes (book, trade, index, settled,
incentives, lab_status) to its own hour files (<HH>.ws.jsonl) and sends Kalshi nothing but subscribe and
update_subscription. The watched markets and the settlements still due are kept in <data>/ws_state.json,
so a restart subscribes at once. Exit codes: 0 done, 2 no key, 3 never connected, 4 no book or trade
message for the last NO_DATA_EXIT_MS while markets were watched.

    python -m lab.ws_recorder --until <unix seconds> --data lab/data
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from lab.recorder import _num, _ts
from lab.rest import Budget, LabRest
from lab.store import LabStore
from lab.ws_auth import load_signer, ws_headers

log = logging.getLogger("lab.ws")

URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"  # Kalshi's other documented host; the cloud proxy allows this one
STREAM = "ws"
CRYPTO = ("KXBTC15M", "KXETH15M")
INDEXES = ("BRTI", "ETHUSD_RTI")
MARKET_CHANNELS = ("orderbook_delta", "trade")
SEQUENCED = ("orderbook_snapshot", "orderbook_delta", "trade", "cfbenchmarks_value")
SETS = ("15m", "E", "F")
META_FIELDS = ("series", "event", "close_ms", "strike", "strike_type")
LEVELS = 10  # levels written per side (B, C and F use the top); a book in set E is written in full: its reward depends on the depth
# C trades the ETH 15-minute book, so that book is written every 10 s and its trades kept; the BTC one is
# needed only in its last three minutes (B), and no strategy fills from BTC 15-minute trades
C_SERIES = ("KXETH15M",)
CADENCE_S = {"15m": 10.0, "15m_other": 60.0, "15m_late": 2.0, "E": 15.0, "F": 60.0}     # a changed book at most this often
HEARTBEAT_S = {"15m": 10.0, "15m_other": 60.0, "15m_late": 2.0, "E": 60.0, "F": 300.0}  # any book at least this often
TRADE_FLUSH_MS = 200  # prints at one price, side and millisecond within this are written as one record (count summed)
PING_S, PONG_TIMEOUT_S = 5.0, 5.0
STALE_MS = 12_000
SNAPSHOT_RETRY_S = (10, 20, 40, 80, 160, 320)  # waits before asking again for a missing snapshot; then the market is dropped
SNAPSHOT_REFRESH_S, REFRESH_BATCH = 1200, 20
QUARTER_TRIES_S = (2, 10, 30, 90)  # 15-minute discovery after each quarter-hour, until both new contracts are found
CRYPTO_FALLBACK_S = 300
INCENTIVES_S, FADE_S, SETTLE_CHECK_S = 1800, 6 * 3600, 60
QUIET_S = {"settle": 60, "incentives": 90, "fade": 150}  # slow lookups wait when the next quarter-hour is closer than this
E_MAX, F_MAX = 12, 30
F_MIN_DAYS, F_MAX_DAYS, F_YES_ASK = 1, 30, (0.01, 0.10)  # close within the month so some settle during the test
F_EXCLUDE = ("KXMVE", "KXBTC", "KXETH", "KXSOL", "KXXRP", "KXDOGE", "KXINX", "KXNASDAQ")  # combos; finance, where the bias is near zero
F_PAGES, INCENTIVE_PAGES = 5, 3
STATUS_S = 300
SETTLE_WAITS_MS = (120_000, 300_000, 900_000, 3_600_000)  # first try after the close, then the wait after each miss
SETTLE_PER_PASS = 3
SETTLE_GIVE_UP_MS = 3 * 86_400_000
RESET_CODES = (7, 10, 25)  # unknown subscription id; channel error and buffer overflow (Kalshi ends the subscription)
NO_DATA_EXIT_MS = 1_800_000  # no book or trade message for this long, with markets watched: exit 4
NEVER_CONNECTED_EXIT_MS = 600_000  # no connection at all for this long: exit 3 (the chunk restarts it, then escalates)
MAX_DROPS = 5  # markets dropped for being refused twice; past this many a refusal is only noted (it may be our request)
MAX_TRACKED_COMMANDS = 2000


class Reconnect(Exception):
    """The subscription state can no longer be trusted: drop the connection and set it up again."""


def _hundredths(text) -> int:
    return int(round(float(text) * 100))


class Book:
    """One market's book: YES bids and NO bids, each price -> hundredths of a contract (NO bids in NO-leg
    prices). Integer sizes, so a level emptied by its deltas is exactly empty."""

    def __init__(self) -> None:
        self.yes: dict[float, int] = {}
        self.no: dict[float, int] = {}
        self.ready = False
        self.changed = False  # since it was last written
        self.snapshot_ms = 0

    def snapshot(self, msg: dict, now_ms: int = 0) -> bool:
        """Replace the book; returns True when a ready book disagreed with the snapshot (it had drifted)."""
        yes = {round(float(p), 4): n for p, s in msg.get("yes_dollars_fp") or [] if (n := _hundredths(s)) > 0}
        no = {round(float(p), 4): n for p, s in msg.get("no_dollars_fp") or [] if (n := _hundredths(s)) > 0}
        drift = self.ready and (yes != self.yes or no != self.no)
        self.yes, self.no = yes, no
        self.ready = self.changed = True
        self.snapshot_ms = now_ms
        return drift

    def delta(self, msg: dict) -> bool:
        """Apply one delta; False when it would leave a level below zero (the book has lost track)."""
        self.changed = True
        side = self.yes if msg.get("side") == "yes" else self.no
        p = round(float(msg["price_dollars"]), 4)
        size = side.get(p, 0) + _hundredths(msg["delta_fp"])
        if size > 0:
            side[p] = size
        else:
            side.pop(p, None)
        return size >= 0

    def crossed(self) -> bool:
        return bool(self.yes and self.no) and max(self.yes) + max(self.no) > 1.0 + 1e-9

    def normalized(self, levels: int | None = LEVELS) -> dict:
        return {"yes": [[p, s / 100] for p, s in sorted(self.yes.items(), reverse=True)[:levels]],
                "no": [[p, s / 100] for p, s in sorted(self.no.items(), reverse=True)[:levels]]}


class Feed:
    """Everything but the socket: books, sequence checks, subscriptions, records and the watched markets.
    It runs on the event loop's thread; only the fetch_* methods, which touch nothing but REST, run in a
    worker thread, and their results are applied back on the loop."""

    def __init__(self, store: LabStore, rest: LabRest, *, now_ms=lambda: int(time.time() * 1000), state_path: Path | None = None,
                 halt: threading.Event | None = None) -> None:
        self.store, self.rest, self.now_ms, self.state_path = store, rest, now_ms, state_path
        self.halt = halt or threading.Event()
        self.meta: dict[str, dict] = {}            # ticker -> {series, event, close_ms, strike, strike_type, sets}
        self.books: dict[str, Book] = {}
        self.sid_channel: dict[int, str] = {}
        self.expected_seq: dict[int, int] = {}
        self.subscribing: dict[int, str] = {}      # command id -> market channel, for subscribes not yet confirmed
        self.sent: dict[str, set[str]] = {}        # market channel -> the tickers its subscribe carried
        self.commands: dict[int, dict] = {}        # command id -> command, while Kalshi may still answer it
        self.snap_asked: dict[str, tuple[int, int]] = {}  # ticker -> (last asked, times asked) while its book is not ready
        self.last_written: dict[str, int] = {}
        self.pending_settle: dict[str, list[int]] = {}    # F ticker -> [close, next try, tries]
        self.counters = defaultdict(int)
        self.errors: deque[str] = deque(maxlen=5)
        self.outbox: list[dict] = []               # commands for the socket loop to send
        self.hold_until = 0                        # Kalshi asked us to slow down: commands wait until then
        self.alive_ms = 0
        self.last_data_ms = 0      # any market data or index value
        self.last_market_ms = 0    # a book or trade message
        self.connected_ms = 0
        self.split_mode: set[str] = set()  # market channels whose markets go in one at a time, to find one Kalshi refuses
        self.refusals: dict[str, int] = defaultdict(int)
        self.stale_since: int | None = None
        self.retry_subscribe_at = 0
        self._last_check = 0
        self._next_id = 0
        self._trades: dict[tuple, dict] = {}  # (ticker, price, taker side, trade time) -> merged print, until flushed
        self._trades_since = 0
        self._load_state()

    # ---- state that outlives a restart ---------------------------------------------------------------
    def _load_state(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            state = json.loads(self.state_path.read_text())
            for t, v in (state.get("pending_settle") or {}).items():
                close, nxt, tries = (v + [0, 0])[:3] if isinstance(v, list) else (int(v), int(v) + SETTLE_WAITS_MS[0], 0)
                self.pending_settle[t] = [int(close), int(nxt), int(tries)]
            for t, m in (state.get("watched") or {}).items():
                sets = [s for s in m.get("sets") or [] if s in SETS]
                if sets:
                    self.meta[t] = {**{k: m.get(k) for k in META_FIELDS}, "sets": sets}
        except (OSError, ValueError, AttributeError, TypeError):
            self.note("ws_state.json unreadable; starting without it")

    def _save_state(self) -> None:
        if self.state_path is None:
            return
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"pending_settle": self.pending_settle, "watched": self.meta}, sort_keys=True))
        tmp.replace(self.state_path)

    def note(self, text: str) -> None:
        self.errors.append(text[:300])
        log.warning("%s", text)

    def mark_alive(self, now_ms: int) -> None:
        if self.stale_since is not None:
            self.write_status(now_ms, note=f"feed back after {(now_ms - self.stale_since) / 1000:.0f} s silent")
            self.stale_since = None
        self.alive_ms = now_ms

    # ---- subscriptions -------------------------------------------------------------------------------
    def _command(self, cmd: str, params: dict, *, again: bool = False) -> int:
        self._next_id += 1
        command = {"id": self._next_id, "cmd": cmd, "params": params}
        if again:
            command["again"] = True
        self.outbox.append({k: command[k] for k in ("id", "cmd", "params")})
        self.commands[self._next_id] = command
        if len(self.commands) > MAX_TRACKED_COMMANDS:
            for cid in sorted(self.commands)[: len(self.commands) - MAX_TRACKED_COMMANDS]:
                del self.commands[cid]
        return self._next_id

    def _sid(self, channel: str) -> int | None:
        return next((s for s, c in self.sid_channel.items() if c == channel), None)

    def _wants(self, channel: str, ticker: str) -> bool:
        """Every watched market's book; trades only where a strategy fills from them (E, F and C's series)."""
        if channel != "trade":
            return ticker in self.meta
        m = self.meta.get(ticker)
        return m is not None and (bool({"E", "F"} & set(m["sets"])) or m.get("series") in C_SERIES)

    def _carried(self, channel: str) -> list[str]:
        return sorted(t for t in self.meta if self._wants(channel, t))

    def _subscribe_markets(self, channel: str) -> None:
        tickers = self._carried(channel)
        if channel in self.split_mode:  # one market first, one Kalshi has not refused if there is one; the rest after
            tickers = sorted(tickers, key=lambda t: (self.refusals[t], t))[:1]
        if not tickers:
            return
        params: dict = {"channels": [channel], "market_tickers": tickers}
        if channel == "orderbook_delta":
            params["use_yes_price"] = False  # NO bids in NO prices, as Book and lab/fills.py expect
        self.sent[channel] = set(tickers)
        self.subscribing[self._command("subscribe", params)] = channel

    def connected(self, now_ms: int | None = None) -> list[dict]:
        """Forget the previous connection and return the commands that set up a new one."""
        now_ms = self.now_ms() if now_ms is None else now_ms
        for d in (self.sid_channel, self.expected_seq, self.subscribing, self.sent, self.commands, self.snap_asked, self.split_mode):
            d.clear()
        self.outbox.clear()  # anything queued for the old connection names its subscription ids
        for b in self.books.values():
            b.ready = False
        self.connected_ms = now_ms
        self.hold_until = self.retry_subscribe_at = 0
        self.mark_alive(now_ms)
        self._command("subscribe", {"channels": ["cfbenchmarks_value"], "index_ids": list(INDEXES)})
        if self.meta:
            for channel in MARKET_CHANNELS:
                self._subscribe_markets(channel)
        cmds, self.outbox = self.outbox, []
        return cmds

    def _confirmed(self, channel: str | None, sid: int | None) -> None:
        if sid is None:
            return
        self.sid_channel[sid] = channel
        if channel not in MARKET_CHANNELS:
            return
        for cid in [c for c, ch in self.subscribing.items() if ch == channel]:
            del self.subscribing[cid]
        carried = self.sent.pop(channel, set())
        wanted = set(self._carried(channel))
        missing, gone = sorted(wanted - carried), sorted(carried - wanted)  # watched or dropped while it was on its way
        for batch in ([[t] for t in missing] if channel in self.split_mode else [missing] if missing else []):
            self._command("update_subscription", {"sids": [sid], "market_tickers": batch, "action": "add_markets"})
        if gone:
            self._command("update_subscription", {"sids": [sid], "market_tickers": gone, "action": "delete_markets"})

    def watch(self, ticker: str, info: dict) -> None:
        """Watch `ticker` for set info["set"]; a market already watched joins the set and takes any field
        this sighting fills in (a 15-minute strike appears only after the contract opens)."""
        set_name = info["set"]
        fields = {k: info.get(k) for k in META_FIELDS}
        m = self.meta.get(ticker)
        if m is not None:
            trades_before = self._wants("trade", ticker)
            for k, v in fields.items():
                if v is not None:
                    m[k] = v
            if set_name not in m["sets"]:
                m["sets"] = sorted(m["sets"] + [set_name], key=SETS.index)
            if not trades_before and self._wants("trade", ticker):  # it joined a set that fills from trades
                self._add("trade", ticker)
            return
        self.meta[ticker] = {**fields, "sets": [set_name]}
        self.books.pop(ticker, None)  # a book kept from an earlier watch is stale
        self.counters["watched"] += 1
        for channel in MARKET_CHANNELS:
            if self._wants(channel, ticker):
                self._add(channel, ticker)

    def _add(self, channel: str, ticker: str) -> None:
        sid = self._sid(channel)
        if sid is not None:
            self._command("update_subscription", {"sids": [sid], "market_tickers": [ticker], "action": "add_markets"})
        elif channel not in self.subscribing.values() and self.now_ms() >= self.retry_subscribe_at:
            self._subscribe_markets(channel)
        # else the subscribe on its way is topped up when Kalshi confirms it, or the retry carries it

    def unwatch(self, ticker: str, set_name: str | None = None) -> None:
        """Take `ticker` out of `set_name` (or out of every set); it stops being recorded when it is in none."""
        m = self.meta.get(ticker)
        if m is None or (set_name is not None and set_name not in m["sets"]):
            return
        carried = [c for c in MARKET_CHANNELS if self._wants(c, ticker)]
        if set_name is not None and len(m["sets"]) > 1:
            m["sets"] = [s for s in m["sets"] if s != set_name]
            carried = [c for c in carried if not self._wants(c, ticker)]  # the trades it no longer needs
        else:
            del self.meta[ticker]
            for d in (self.books, self.last_written, self.snap_asked):
                d.pop(ticker, None)
        for channel in carried:
            sid = self._sid(channel)
            if sid is not None:
                self._command("update_subscription", {"sids": [sid], "market_tickers": [ticker], "action": "delete_markets"})

    def crypto_found(self, close_ms: int) -> bool:
        """Whether a contract closing at `close_ms` is watched in each 15-minute series."""
        return all(any(m.get("series") == s and m.get("close_ms") == close_ms for m in self.meta.values()) for s in CRYPTO)

    # ---- market discovery: fetch_* in a worker thread (they wait on the REST budget), apply_* on the loop
    def fetch_crypto(self) -> dict[str, dict | None]:
        return {s: self.rest.get("/markets", {"series_ticker": s, "status": "open", "limit": 20}) for s in CRYPTO}

    def apply_crypto(self, fetched: dict[str, dict | None], now_ms: int) -> None:
        for series, payload in fetched.items():
            for m in (payload or {}).get("markets") or []:
                close = _ts(m.get("close_time"))
                if close and close > now_ms:
                    self.watch(m["ticker"], {"series": series, "event": m.get("event_ticker"), "close_ms": close, "strike": _num(m.get("floor_strike")),
                                             "strike_type": m.get("strike_type"), "set": "15m"})
        self._save_state()

    def fetch_incentives(self) -> list[dict] | None:
        """Every active liquidity program, or None if any page failed: a partial list is never used."""
        programs, cursor = [], None
        for _ in range(INCENTIVE_PAGES):  # about 5,000 active programs on 2026-11-04: one page of 10,000
            payload = self.rest.get("/incentive_programs", {"status": "active", "type": "liquidity", "limit": 10_000, "cursor": cursor})
            if payload is None:
                return None
            programs += payload.get("incentive_programs") or []
            cursor = payload.get("next_cursor")
            if not cursor:
                return programs
        return None  # more pages than we read: incomplete

    def apply_incentives(self, programs: list[dict] | None, now_ms: int) -> None:
        if programs is None:
            self.counters["incentive_fetch_failed"] += 1
            return
        programs = [p for p in programs if p.get("incentive_type") == "liquidity" and p.get("market_ticker")]

        def per_day(p):
            start, end = _ts(p.get("start_date")), _ts(p.get("end_date"))
            live = start and end and start <= now_ms < end
            return (p.get("period_reward") or 0) / 10_000 / max(1.0, (end - start) / 86_400_000) if live else 0.0
        chosen = [p for p in sorted(programs, key=per_day, reverse=True) if per_day(p) > 0][:E_MAX]
        keep = {p["market_ticker"] for p in chosen}
        # the full list runs to megabytes; E needs only the programs of the markets it watches
        self.store.write("incentives", {"programs": [p for p in programs if p["market_ticker"] in keep], "active_programs": len(programs)}, ts_ms=now_ms)
        for t, m in list(self.meta.items()):
            if "E" in m["sets"] and t not in keep:
                self.unwatch(t, "E")
        for p in chosen:
            self.watch(p["market_ticker"], {"set": "E"})
        self._save_state()

    def fetch_fade(self, now_ms: int) -> list[dict] | None:
        """The F candidates, or None if any page failed."""
        found, cursor = [], None
        for _ in range(F_PAGES):
            payload = self.rest.get("/markets", {"status": "open", "limit": 1000, "min_close_ts": int(now_ms / 1000 + F_MIN_DAYS * 86_400),
                                                 "max_close_ts": int(now_ms / 1000 + F_MAX_DAYS * 86_400), "cursor": cursor})
            if payload is None:
                return None
            for m in payload.get("markets") or []:
                ask, vol = _num(m.get("yes_ask_dollars")), _num(m.get("volume_24h_fp")) or 0.0
                if ask is not None and F_YES_ASK[0] <= ask <= F_YES_ASK[1] and vol > 0 and not str(m.get("ticker", "")).startswith(F_EXCLUDE):
                    found.append((vol, m))
            cursor = payload.get("cursor")
            if not cursor:
                break
        return [m for _, m in sorted(found, key=lambda x: -x[0])[:F_MAX]]

    def apply_fade(self, chosen: list[dict] | None, now_ms: int) -> None:
        if not chosen:
            self.counters["fade_fetch_failed" if chosen is None else "fade_none_found"] += 1
            return
        keep = {m["ticker"] for m in chosen}
        for t, m in list(self.meta.items()):
            if "F" in m["sets"] and t not in keep:
                if m.get("close_ms"):
                    self._settle_later(t, m["close_ms"])  # F may hold contracts in it: keep its result coming
                self.unwatch(t, "F")
        for m in chosen:
            self.watch(m["ticker"], {"event": m.get("event_ticker"), "close_ms": _ts(m.get("close_time")), "strike_type": m.get("strike_type"), "set": "F"})
        self._save_state()

    def _settle_later(self, ticker: str, close_ms: int) -> None:
        if ticker not in self.pending_settle:
            self.pending_settle[ticker] = [close_ms, close_ms + SETTLE_WAITS_MS[0], 0]

    def due_settlements(self, now_ms: int) -> list[str]:
        due = sorted((nxt, t) for t, (_, nxt, _) in self.pending_settle.items() if now_ms >= nxt)
        return [t for _, t in due[:SETTLE_PER_PASS]]

    def fetch_settlements(self, tickers: list[str]) -> dict[str, dict | None]:
        return {t: self.rest.get(f"/markets/{t}") for t in tickers}

    def apply_settlements(self, fetched: dict[str, dict | None], now_ms: int) -> None:
        for t, payload in fetched.items():
            entry = self.pending_settle.get(t)
            if entry is None:
                continue
            close, _, tries = entry
            m = (payload or {}).get("market") or {}
            if m.get("result") in ("yes", "no"):
                self.store.write("settled", {"series": t.split("-")[0], "event": m.get("event_ticker"), "close_ms": close,
                                             "rows": [[t, m["result"], _num(m.get("expiration_value"))]]}, ts_ms=now_ms)
                del self.pending_settle[t]
            elif now_ms > close + SETTLE_GIVE_UP_MS:
                self.note(f"{t} closed without a result; giving up on it")
                del self.pending_settle[t]
            else:
                tries += 1
                self.pending_settle[t] = [close, now_ms + SETTLE_WAITS_MS[min(tries, len(SETTLE_WAITS_MS) - 1)], tries]
        self._save_state()

    def refresh_crypto(self, now_ms: int) -> None:
        self.apply_crypto(self.fetch_crypto(), now_ms)

    def refresh_incentives(self, now_ms: int) -> None:
        self.apply_incentives(self.fetch_incentives(), now_ms)

    def refresh_fade(self, now_ms: int) -> None:
        self.apply_fade(self.fetch_fade(now_ms), now_ms)

    def settle_due(self, now_ms: int) -> None:
        due = self.due_settlements(now_ms)
        if due:
            self.apply_settlements(self.fetch_settlements(due), now_ms)

    # ---- upkeep on the socket loop: closes, snapshot requests ---------------------------------------
    def tick(self, now_ms: int) -> None:
        changed = False
        for t, m in list(self.meta.items()):
            close = m.get("close_ms")
            if close and close <= now_ms and ("15m" in m["sets"] or "F" in m["sets"]):
                if "F" in m["sets"]:
                    self._settle_later(t, close)
                self.unwatch(t, "15m")
                self.unwatch(t, "F")
                changed = True
        if changed:
            self._save_state()
        if self.retry_subscribe_at and now_ms >= self.retry_subscribe_at:
            self.retry_subscribe_at = 0
            for channel in MARKET_CHANNELS:
                if self.meta and self._sid(channel) is None and channel not in self.subscribing.values():
                    self._subscribe_markets(channel)
        if now_ms - self._last_check >= 5000:
            self._last_check = now_ms
            self.check_books(now_ms)

    def check_books(self, now_ms: int) -> None:
        """Ask again for snapshots that have not come (with growing waits; a market that never gets one is
        dropped) and refresh every book that has gone SNAPSHOT_REFRESH_S without one."""
        sid = self._sid("orderbook_delta")
        if sid is None:
            return
        ask, refresh, drop = [], [], []
        for t in self.meta:
            book = self.books.get(t)
            if book is not None and book.ready:
                if now_ms - book.snapshot_ms >= SNAPSHOT_REFRESH_S * 1000 and len(refresh) < REFRESH_BATCH:
                    refresh.append(t)
                continue
            asked, times = self.snap_asked.get(t, (self.connected_ms, 0))
            if now_ms - asked < SNAPSHOT_RETRY_S[min(times, len(SNAPSHOT_RETRY_S) - 1)] * 1000:
                continue
            if times >= len(SNAPSHOT_RETRY_S):
                drop.append(t)
                continue
            ask.append(t)
            self.snap_asked[t] = (now_ms, times + 1)
        for t in drop:
            self.counters["dropped_no_snapshot"] += 1
            self.note(f"{t} never sent a snapshot; no longer watched")
            self.unwatch(t)
        for t in refresh:
            self.books[t].snapshot_ms = now_ms  # not asked again before the answer comes
        self.counters["snapshot_retries"] += len(ask)
        tickers = ask + refresh
        for i in range(0, len(tickers), 100):  # the most tickers one get_snapshot takes is not documented
            self._command("update_subscription", {"sids": [sid], "market_tickers": tickers[i:i + 100], "action": "get_snapshot"})
        if drop:
            self._save_state()

    def _resnapshot_all(self, sid: int) -> None:
        for book in self.books.values():
            book.ready = False
        tickers = sorted(self.meta)
        now = self.now_ms()
        for t in tickers:
            self.snap_asked[t] = (now, 1)
        for i in range(0, len(tickers), 100):
            self._command("update_subscription", {"sids": [sid], "market_tickers": tickers[i:i + 100], "action": "get_snapshot"})

    # ---- messages ----------------------------------------------------------------------------------
    def _sequence(self, kind: str, sid: int, seq: int) -> None:
        # Kalshi does not say whether replies (ok, error) take numbers in a subscription's sequence. A data
        # message whose seq runs ahead of the next one expected is a gap; a reply that carries exactly the
        # next number takes it; any other reply number is only counted, so it can never hide a gap.
        expected = self.expected_seq.get(sid)
        if kind in SEQUENCED:
            if expected is not None and seq > expected:
                channel = self.sid_channel.get(sid)
                self.counters["gaps" if channel == "orderbook_delta" else f"{channel}_gaps"] += 1
                if channel == "orderbook_delta":
                    self._resnapshot_all(sid)
            self.expected_seq[sid] = max(expected or 0, seq + 1)
        elif expected is not None:
            if seq == expected:
                self.expected_seq[sid] = seq + 1
                self.counters["replies_in_sequence"] += 1
            else:
                self.counters["replies_off_sequence"] += 1

    def _error(self, m: dict, body: dict) -> None:
        """An error that ends a subscription, or leaves our view of one in doubt, drops the connection. One
        that answers a command of ours never does: a refused command naming many markets is sent again one
        market at a time, so a market Kalshi will not serve is found and dropped without stopping the rest."""
        code, text = body.get("code"), body.get("msg")
        self.counters["errors"] += 1
        self.note(f"kalshi ws error {code}: {text}")
        cid = m.get("id")
        command = self.commands.pop(cid, None) if cid is not None else None
        if code in RESET_CODES or (command is None and m.get("sid") is not None):
            raise Reconnect(f"kalshi ended or lost a subscription (error {code}: {text})")
        if command is None:
            return
        if code in (18, 27):  # a command timeout, or too many commands: hold the queue a moment, send it once more
            if code == 27:
                self.hold_until = self.now_ms() + 5000
            if not command.get("again"):
                self._command(command["cmd"], command["params"], again=True)
            return
        params = command["params"]
        tickers = params.get("market_tickers") or []
        if command["cmd"] == "subscribe":
            channels = params.get("channels") or []
            if "cfbenchmarks_value" in channels:
                self.counters["index_refused"] += 1  # e.g. an entitlement: not retried on this connection
                return
            channel = self.subscribing.pop(cid, None) or (channels[0] if channels else None)
            self.sent.pop(channel, None)
            self.split_mode.add(channel)
            if code == 9:  # not allowed at all: try again in a while
                self.retry_subscribe_at = self.now_ms() + 300_000
                return
            if len(tickers) == 1:
                self.refusals[tickers[0]] += 1  # the next try leads with another market
                self.counters["refusals"] += 1
            self.retry_subscribe_at = self.now_ms() + 5_000
            return
        if command["cmd"] == "update_subscription" and tickers:
            if len(tickers) > 1:
                for t in tickers:
                    self._command("update_subscription", {**params, "market_tickers": [t]})
            elif params.get("action") == "add_markets":
                self._refused(tickers[0], f"add_markets, error {code}")
            # a refused single get_snapshot is asked again by check_books, which drops the market after a while

    def _refused(self, ticker: str, why: str) -> None:
        """A market Kalshi refused on its own: dropped the second time, unless many have been (then the fault
        is more likely ours, and dropping more would empty the feed)."""
        self.refusals[ticker] += 1
        self.counters["refusals"] += 1
        if self.refusals[ticker] >= 2 and self.counters["markets_dropped"] < MAX_DROPS:
            self.counters["markets_dropped"] += 1
            self.note(f"kalshi refused {ticker} twice ({why}); no longer watched")
            self.unwatch(ticker)
            self._save_state()
        elif self.refusals[ticker] == 1 and ticker in self.meta:
            for channel in MARKET_CHANNELS:  # once more, on its own
                sid = self._sid(channel)
                if sid is not None:
                    self._command("update_subscription", {"sids": [sid], "market_tickers": [ticker], "action": "add_markets"})

    def handle(self, m: dict) -> None:
        kind, sid, seq = m.get("type"), m.get("sid"), m.get("seq")
        body = m.get("msg") if isinstance(m.get("msg"), dict) else {}
        now = self.now_ms()
        self.counters["messages"] += 1
        self.mark_alive(now)
        if m.get("id") is not None and kind != "error":
            self.commands.pop(m["id"], None)
        if sid is not None and isinstance(seq, int):
            self._sequence(kind, sid, seq)
        if kind == "subscribed":
            self._confirmed(body.get("channel"), body.get("sid", sid))
        elif kind == "error":
            self._error(m, body)
        elif kind == "orderbook_snapshot":
            t = body.get("market_ticker")
            if t not in self.meta:
                return  # not watched (any more)
            if self.books.setdefault(t, Book()).snapshot(body, now):
                self.counters["snapshot_drift"] += 1
            self.snap_asked.pop(t, None)
            self.last_data_ms = self.last_market_ms = now
        elif kind == "orderbook_delta":
            t = body.get("market_ticker")
            book = self.books.get(t)
            self.last_data_ms = self.last_market_ms = now
            if t not in self.meta or book is None or not book.ready:
                return
            try:
                ok = book.delta(body)
            except (KeyError, TypeError, ValueError):
                ok = False
                self.counters["bad_deltas"] += 1
            if not ok:
                book.ready = False  # check_books asks for a fresh snapshot
                self.counters["books_lost"] += 1
        elif kind == "trade":
            self.last_data_ms = self.last_market_ms = now
            t = body.get("market_ticker")
            if not self._wants("trade", t):
                return
            price, side, at, count = _num(body.get("yes_price_dollars")), body.get("taker_outcome_side") or body.get("taker_side"), body.get("ts_ms"), _num(body.get("count_fp")) or 0.0
            merged = self._trades.get((t, price, side, at, bool(body.get("is_block_trade"))))
            if merged is not None:  # another fill of the same sweep: one record
                merged["count"] = round(merged["count"] + count, 2)
                merged["n"] += 1
            else:
                self._trades[(t, price, side, at, bool(body.get("is_block_trade")))] = {
                    "ticker": t, "yes_price": price, "count": count, "taker_side": side, "trade_ts": at, "sent_ts": m.get("sending_ts_ms"),
                    "block": body.get("is_block_trade"), "n": 1}
                self._trades_since = self._trades_since or now
        elif kind == "cfbenchmarks_value":
            self.last_data_ms = now
            try:
                data = json.loads(body.get("data") or "{}")
                value = float(data.get("value"))
            except (TypeError, ValueError, AttributeError):
                self.counters["bad_index"] += 1
                return
            q = body.get("last_60s_windowed_average_15min") or {}
            self.store.write("index", {"symbol": body.get("index_id"), "value": value, "avg60": _num((body.get("avg_60s_data") or {}).get("value")),
                                       "qavg": _num(q.get("value")), "qn": q.get("window_size"), "src_ts": data.get("time"),
                                       "sent_ts": m.get("sending_ts_ms")}, ts_ms=now)

    def flush_trades(self, now_ms: int) -> None:
        for rec in self._trades.values():
            self.store.write("trade", rec, ts_ms=now_ms)
        self._trades.clear()
        self._trades_since = 0

    def write_books(self, now_ms: int) -> None:
        if self._trades and now_ms - self._trades_since >= TRADE_FLUSH_MS:
            self.flush_trades(now_ms)
        if now_ms - self.alive_ms > STALE_MS:
            if self.stale_since is None:
                self.stale_since = now_ms
                self.counters["stale_spells"] += 1
                self.write_status(now_ms, note="feed silent: no books are written until it is back")
            return
        for t, m in self.meta.items():
            book = self.books.get(t)
            if book is None or not book.ready:
                continue
            if book.crossed():
                book.ready = False  # a book that cannot exist on the exchange: ask for a fresh one
                self.counters["crossed_books"] += 1
                continue
            keys = [s if s != "15m" else "15m_late" if m.get("close_ms") and m["close_ms"] - now_ms <= 180_000 else "15m" if m.get("series") in C_SERIES else "15m_other"
                    for s in m["sets"]]
            since = now_ms - self.last_written.get(t, 0)
            if since >= min(CADENCE_S[k] for k in keys) * 1000 and (book.changed or since >= min(HEARTBEAT_S[k] for k in keys) * 1000):
                self.store.write("book", {"ticker": t, **{k: m.get(k) for k in META_FIELDS}, "set": m["sets"][0], "sets": m["sets"],
                                          **book.normalized(None if "E" in m["sets"] else LEVELS)}, ts_ms=now_ms)
                self.last_written[t] = now_ms
                book.changed = False

    def write_status(self, now_ms: int, note: str | None = None) -> None:
        rec = {"source": "ws", "ws": dict(self.counters), "rest": self.rest.counters(), "errors": list(self.errors), "use_yes_price": False,
               "watched": {s: sum(1 for m in self.meta.values() if s in m["sets"]) for s in SETS}, "pending_settle": len(self.pending_settle),
               "connected": bool(self.sid_channel), "stale": self.stale_since is not None, "last_data_ms": self.last_data_ms}
        if note:
            rec["note"] = note
        self.store.write("lab_status", rec, ts_ms=now_ms)

    def exit_code(self, now_ms: int, started_ms: int) -> int:
        if not self.counters["connects"]:
            return 3
        silent_since = max(self.last_market_ms, started_ms)
        return 4 if self.meta and now_ms - silent_since > NO_DATA_EXIT_MS else 0

    def failing(self, now_ms: int, started_ms: int) -> int:
        """3 or 4 once the feed has plainly failed (never connected in NEVER_CONNECTED_EXIT_MS, or no market
        data for NO_DATA_EXIT_MS), so the recorder stops early and the chunk script can restart or escalate."""
        if not self.counters["connects"]:
            return 3 if now_ms - started_ms > NEVER_CONNECTED_EXIT_MS else 0
        return self.exit_code(now_ms, started_ms)


class Schedule:
    """When each REST lookup is due. The 15-minute contracts are looked for QUARTER_TRIES_S after each
    quarter-hour until both are found (and every CRYPTO_FALLBACK_S); the slow lookups wait while the next
    quarter-hour is near, so they never delay that."""

    def __init__(self) -> None:
        self.next = {"crypto": 0, "settle": 0, "incentives": 0, "fade": 0, "status": 0}
        self.tried: set[tuple[int, int]] = set()

    def due(self, now_ms: int, found) -> str | None:
        q = now_ms - now_ms % 900_000
        self.tried = {x for x in self.tried if x[0] == q}
        tries = [s for s in QUARTER_TRIES_S if (q, s) not in self.tried and now_ms >= q + s * 1000]
        if now_ms >= self.next["crypto"] or (tries and not found(q + 900_000)):
            self.tried.update((q, s) for s in tries)
            self.next["crypto"] = now_ms + CRYPTO_FALLBACK_S * 1000
            return "crypto"
        to_next_quarter = (q + 900_000 - now_ms) / 1000
        settled_in = found(q + 900_000) or now_ms >= q + QUARTER_TRIES_S[-1] * 1000
        for job, every in (("settle", SETTLE_CHECK_S), ("incentives", INCENTIVES_S), ("fade", FADE_S)):
            if now_ms >= self.next[job] and settled_in and to_next_quarter > QUIET_S[job]:
                self.next[job] = now_ms + every * 1000
                return job
        if now_ms >= self.next["status"]:
            self.next["status"] = now_ms + STATUS_S * 1000
            return "status"
        return None


async def maintain(feed: Feed, until_ms: int, *, stop: asyncio.Event) -> None:
    """Market discovery, settlements and status records beside the socket loop; a REST wait never stalls the
    feed. Stops the recorder early once the feed has plainly failed."""
    schedule = Schedule()
    started = feed.now_ms()
    while not stop.is_set() and feed.now_ms() < until_ms:
        now = feed.now_ms()
        code = feed.failing(now, started)
        if code:
            feed.note("never connected" if code == 3 else "no book or trade message for half an hour")
            feed.write_status(now, note=f"stopping early (exit {code})")
            stop.set()
            break
        try:
            job = schedule.due(now, feed.crypto_found)
            if job == "crypto":
                feed.apply_crypto(await asyncio.to_thread(feed.fetch_crypto), feed.now_ms())
            elif job == "settle":
                due = feed.due_settlements(now)
                if due:
                    feed.apply_settlements(await asyncio.to_thread(feed.fetch_settlements, due), feed.now_ms())
            elif job == "incentives":
                feed.apply_incentives(await asyncio.to_thread(feed.fetch_incentives), feed.now_ms())
            elif job == "fade":
                feed.apply_fade(await asyncio.to_thread(feed.fetch_fade, now), feed.now_ms())
            elif job == "status":
                feed.write_status(now)
            if job is not None:
                continue
        except Exception as exc:  # noqa: BLE001 - discovery failing must not stop the recording
            if stop.is_set():
                break
            feed.counters["maintenance_errors"] += 1
            feed.note(f"market refresh failed: {type(exc).__name__}: {exc}")
        try:
            await asyncio.wait_for(stop.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pass


async def keepalive(ws, feed: Feed) -> None:
    """Ping every PING_S; an answer proves the link is alive even when no market moves. Returns (and the
    socket loop reconnects) when one goes unanswered."""
    while True:
        await asyncio.sleep(PING_S)
        pong = await ws.ping()
        try:
            await asyncio.wait_for(pong, PONG_TIMEOUT_S)
        except asyncio.TimeoutError:
            feed.counters["pong_timeouts"] += 1
            return
        feed.mark_alive(feed.now_ms())


async def run(feed: Feed, until_ms: int, sign, key_id: str, *, stop: asyncio.Event) -> None:
    from websockets.asyncio.client import connect

    upkeep = asyncio.create_task(maintain(feed, until_ms, stop=stop))
    backoff = 2.0
    try:
        while not stop.is_set() and feed.now_ms() < until_ms:
            try:
                async with connect(URL, additional_headers=ws_headers(key_id, sign), max_size=2 ** 26, max_queue=4096,
                                   open_timeout=20, close_timeout=2, ping_interval=None) as ws:
                    feed.counters["connects"] += 1
                    for cmd in feed.connected():
                        await ws.send(json.dumps(cmd))
                    pinger = asyncio.create_task(keepalive(ws, feed))
                    try:
                        while not stop.is_set() and feed.now_ms() < until_ms:
                            try:
                                raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            except asyncio.TimeoutError:
                                raw = None
                            if raw is not None:
                                try:
                                    feed.handle(json.loads(raw))
                                except Reconnect:
                                    raise
                                except Exception as exc:  # noqa: BLE001 - one unreadable message is counted, not fatal
                                    feed.counters["bad_messages"] += 1
                                    feed.note(f"unreadable message ({type(exc).__name__}: {exc})")
                            if pinger.done():
                                raise Reconnect("a ping went unanswered")
                            now = feed.now_ms()
                            feed.tick(now)
                            if now >= feed.hold_until:
                                while feed.outbox:
                                    await ws.send(json.dumps(feed.outbox.pop(0)))
                            feed.write_books(now)
                            if backoff > 2.0 and now - feed.connected_ms >= 60_000 and feed.last_data_ms > feed.connected_ms:
                                backoff = 2.0  # only a link that lived a minute with data resets the wait
                    finally:
                        pinger.cancel()
            except Exception as exc:  # noqa: BLE001 - reconnect on anything the socket throws
                feed.counters["disconnects"] += 1
                for b in feed.books.values():
                    b.ready = False
                feed.note(f"kalshi ws disconnected ({type(exc).__name__}: {exc}); reconnecting in {backoff:.0f} s")
                try:
                    await asyncio.wait_for(stop.wait(), timeout=backoff)
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, 120.0)
    finally:
        stop.set()
        feed.halt.set()
        try:
            await asyncio.wait_for(upkeep, timeout=15)
        except (asyncio.TimeoutError, Exception):  # noqa: BLE001 - shutdown is bounded either way
            upkeep.cancel()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record Kalshi market data over the authenticated WebSocket (read-only)")
    parser.add_argument("--minutes", type=float, default=110.0)
    parser.add_argument("--until", type=float, default=None, help="stop at this Unix time (seconds) instead of after --minutes")
    parser.add_argument("--data", default="lab/data")
    parser.add_argument("--rate", type=float, default=0.2, help="average public REST requests a second, for market discovery")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    signer = load_signer()
    if signer is None:
        print("lab ws recorder: no production key in KALSHI_PROD_API_KEY_ID / KALSHI_PROD_PRIVATE_KEY; nothing to do")
        return 2
    key_id, sign = signer
    Path(args.data).mkdir(parents=True, exist_ok=True)
    halt = threading.Event()
    store = LabStore(args.data, stream=STREAM)
    feed = Feed(store, LabRest(budget=Budget(args.rate, 3.0, halt=halt)), state_path=Path(args.data) / "ws_state.json", halt=halt)
    now = feed.now_ms()
    until_ms = int(args.until * 1000) if args.until else int(now + args.minutes * 60_000)
    stop = asyncio.Event()

    async def go():
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)
        await run(feed, until_ms, sign, key_id, stop=stop)

    try:
        asyncio.run(go())
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)  # the last seal finishes before the process goes
        end = feed.now_ms()
        feed.flush_trades(end)
        feed.write_status(end, note="ws recorder stopped")
        store.close()
        store.seal_closed_hours()
        print(f"lab ws recorder: {dict(feed.counters)}")
    code = feed.exit_code(end, now)
    if code:
        print(f"lab ws recorder: {'never connected' if code == 3 else 'no book or trade message for the last half hour'} (exit {code})")
    return code


if __name__ == "__main__":
    sys.exit(main())
