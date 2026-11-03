"""The lab's live-feed recorder: Kalshi's authenticated WebSocket, market data only (docs/lab/kalshi_interfaces.md).

It needs the production key in KALSHI_PROD_API_KEY_ID / KALSHI_PROD_PRIVATE_KEY and exits with code 2
without it. One connection carries:
  orderbook_delta     the full book of every watched market, from a snapshot and its deltas, checked by seq;
                      on a gap it asks for fresh snapshots of every market (use_yes_price is set explicitly)
  trade               every print in the watched markets
  cfbenchmarks_value  BRTI and ETHUSD_RTI about once a second, with Kalshi's trailing 60-second average
                      and, in the last minute of each quarter hour, the settlement window's average so far

Watched markets, refreshed while it runs over public REST at the lab's request budget (in a worker thread,
so the socket is always being read):
  15m  the open KXBTC15M and KXETH15M contracts                  book every 2 s in the last 3 minutes, else 10 s
  E    the markets with the largest active liquidity-incentive pools
                                     full-depth book when it changes, at most every 15 s, at least every 60 s
  F    markets closing in 1-30 days with a 1-10 cent YES ask, by 24-hour volume
                                                  book when it changes, at most every 60 s, at least every 5 min

It writes the normalized records lab/strategies/maker_common.py describes (book, trade, index, settled,
incentives, lab_status) to its own hour files (<HH>.ws.jsonl), never one the REST recorder writes, and it
sends Kalshi nothing but subscribe and update_subscription. It settles F markets from REST after they
close (the REST recorder settles the 15-minute ones) and keeps the ones still waiting in
<data>/ws_state.json, so a restart does not lose them.

    python -m lab.ws_recorder --minutes 110 --data lab/data
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

from lab.recorder import _num, _ts
from lab.rest import Budget, LabRest
from lab.store import LabStore
from lab.ws_auth import load_signer, ws_headers

log = logging.getLogger("lab.ws")

URL = "wss://external-api-ws.kalshi.com/trade-api/ws/v2"
STREAM = "ws"
CRYPTO = ("KXBTC15M", "KXETH15M")
INDEXES = ("BRTI", "ETHUSD_RTI")
MARKET_CHANNELS = ("orderbook_delta", "trade")
DATA_KINDS = ("orderbook_snapshot", "orderbook_delta", "trade")
LEVELS = 30  # levels written per side; E books are written in full, since their reward depends on the depth
CADENCE_S = {"15m": 10.0, "15m_late": 2.0, "E": 15.0, "F": 60.0}       # a changed book at most this often
HEARTBEAT_S = {"15m": 10.0, "15m_late": 2.0, "E": 60.0, "F": 300.0}     # any book at least this often
REFRESH_S = {"crypto": 60, "incentives": 1800, "fade": 6 * 3600}  # seconds; the desk shares the REST limit
E_MAX, F_MAX = 12, 30
F_MIN_DAYS, F_MAX_DAYS, F_YES_ASK = 1, 30, (0.01, 0.10)  # close within the month so some settle during the test
F_EXCLUDE = ("KXMVE", "KXBTC", "KXETH", "KXSOL", "KXXRP", "KXDOGE", "KXINX", "KXNASDAQ")  # combos; finance, where the bias is near zero
F_PAGES, INCENTIVE_PAGES = 5, 3
STATUS_S = 300
SETTLE_AFTER_MS = 120_000
SETTLE_GIVE_UP_MS = 3 * 86_400_000


class Book:
    """One market's book: YES bids and NO bids, each price -> contracts (NO bids in NO-leg prices)."""

    def __init__(self) -> None:
        self.yes: dict[float, float] = {}
        self.no: dict[float, float] = {}
        self.ready = False
        self.changed = False  # since it was last written

    def snapshot(self, msg: dict) -> None:
        self.yes = {round(float(p), 4): float(s) for p, s in msg.get("yes_dollars_fp") or [] if float(s) > 0}
        self.no = {round(float(p), 4): float(s) for p, s in msg.get("no_dollars_fp") or [] if float(s) > 0}
        self.ready = self.changed = True

    def delta(self, msg: dict) -> None:
        self.changed = True
        side = self.yes if msg.get("side") == "yes" else self.no
        p = round(float(msg["price_dollars"]), 4)
        side[p] = side.get(p, 0.0) + float(msg["delta_fp"])
        if side[p] <= 1e-9:
            side.pop(p, None)

    def normalized(self, levels: int | None = LEVELS) -> dict:
        return {"yes": [[p, round(s, 2)] for p, s in sorted(self.yes.items(), reverse=True)[:levels]],
                "no": [[p, round(s, 2)] for p, s in sorted(self.no.items(), reverse=True)[:levels]]}


class Feed:
    """Everything but the socket: books, sequence checks, subscriptions, records and the watched markets.
    It runs on the event loop's thread; only the fetch_* methods, which touch nothing but REST, run in a
    worker thread, and their results are applied back on the loop."""

    def __init__(self, store: LabStore, rest: LabRest, *, now_ms=lambda: int(time.time() * 1000), state_path: Path | None = None) -> None:
        self.store, self.rest, self.now_ms, self.state_path = store, rest, now_ms, state_path
        self.meta: dict[str, dict] = {}         # ticker -> {series, event, close_ms, strike, strike_type, set}
        self.books: dict[str, Book] = defaultdict(Book)
        self.sid_channel: dict[int, str] = {}
        self.expected_seq: dict[int, int] = {}
        self.subscribing: dict[int, str] = {}   # command id -> market channel, for subscribes not yet confirmed
        self.sent: dict[str, set[str]] = {}     # market channel -> the tickers its subscribe carried
        self.last_written: dict[str, int] = {}
        self.pending_settle: dict[str, int] = {}  # F ticker -> close (ms), waiting for its result
        self.counters = defaultdict(int)
        self.errors: deque[str] = deque(maxlen=5)
        self.outbox: list[dict] = []            # commands for the socket loop to send
        self._next_id = 0
        self._load_state()

    # ---- state that outlives a restart ---------------------------------------------------------------
    def _load_state(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            self.pending_settle.update({t: int(c) for t, c in json.loads(self.state_path.read_text()).get("pending_settle", {}).items()})
        except (OSError, ValueError, AttributeError, TypeError):
            self.note("ws_state.json unreadable; starting without it")

    def _save_state(self) -> None:
        if self.state_path is None:
            return
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"pending_settle": self.pending_settle}, sort_keys=True))
        tmp.replace(self.state_path)

    def note(self, text: str) -> None:
        self.errors.append(text[:300])
        log.warning("%s", text)

    # ---- subscriptions -------------------------------------------------------------------------------
    def _command(self, cmd: str, params: dict) -> int:
        self._next_id += 1
        self.outbox.append({"id": self._next_id, "cmd": cmd, "params": params})
        return self._next_id

    def _sid(self, channel: str) -> int | None:
        return next((s for s, c in self.sid_channel.items() if c == channel), None)

    def _subscribe_markets(self, channel: str) -> None:
        tickers = sorted(self.meta)
        params: dict = {"channels": [channel], "market_tickers": tickers}
        if channel == "orderbook_delta":
            params["use_yes_price"] = False  # NO bids in NO prices, as Book and lab/fills.py expect
        self.sent[channel] = set(tickers)
        self.subscribing[self._command("subscribe", params)] = channel

    def connected(self) -> list[dict]:
        """Forget the previous connection and return the commands that set up a new one."""
        self.sid_channel.clear()
        self.expected_seq.clear()
        self.subscribing.clear()
        self.sent.clear()
        self.outbox.clear()  # anything queued for the old connection names its subscription ids
        for b in self.books.values():
            b.ready = False
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
        missing, gone = sorted(set(self.meta) - carried), sorted(carried - set(self.meta))  # watched or dropped while it was on its way
        if missing:
            self._command("update_subscription", {"sids": [sid], "market_tickers": missing, "action": "add_markets"})
        if gone:
            self._command("update_subscription", {"sids": [sid], "market_tickers": gone, "action": "delete_markets"})

    def watch(self, ticker: str, meta: dict) -> None:
        if ticker in self.meta:
            self.meta[ticker] = meta
            return
        self.meta[ticker] = meta
        self.counters["watched"] += 1
        for channel in MARKET_CHANNELS:
            sid = self._sid(channel)
            if sid is not None:
                self._command("update_subscription", {"sids": [sid], "market_tickers": [ticker], "action": "add_markets"})
            elif channel not in self.subscribing.values():
                self._subscribe_markets(channel)
            # else the subscribe on its way is topped up when Kalshi confirms it

    def unwatch(self, ticker: str) -> None:
        if self.meta.pop(ticker, None) is None:
            return
        self.books.pop(ticker, None)
        self.last_written.pop(ticker, None)
        for channel in MARKET_CHANNELS:
            sid = self._sid(channel)
            if sid is not None:
                self._command("update_subscription", {"sids": [sid], "market_tickers": [ticker], "action": "delete_markets"})

    # ---- market discovery: fetch_* in a worker thread (they wait on the REST budget), apply_* on the loop
    def fetch_crypto(self) -> dict[str, dict | None]:
        return {s: self.rest.get("/markets", {"series_ticker": s, "status": "open", "limit": 20}) for s in CRYPTO}

    def apply_crypto(self, fetched: dict[str, dict | None], now_ms: int) -> None:
        for series, payload in fetched.items():
            for m in (payload or {}).get("markets") or []:
                close = _ts(m.get("close_time"))
                if close and close > now_ms and m["ticker"] not in self.meta:
                    self.watch(m["ticker"], {"series": series, "event": m.get("event_ticker"), "close_ms": close, "strike": _num(m.get("floor_strike")),
                                             "strike_type": m.get("strike_type"), "set": "15m"})
        for t, m in list(self.meta.items()):
            if m["set"] in ("15m", "F") and m.get("close_ms") and m["close_ms"] <= now_ms:
                if m["set"] == "F":
                    self.pending_settle[t] = m["close_ms"]
                self.unwatch(t)
        self._save_state()

    def fetch_incentives(self) -> list[dict]:
        programs, cursor = [], None
        for _ in range(INCENTIVE_PAGES):
            payload = self.rest.get("/incentive_programs", {"status": "active", "type": "liquidity", "limit": 1000, "cursor": cursor})
            if not payload:
                break
            programs += payload.get("incentive_programs") or []
            cursor = payload.get("next_cursor")
            if not cursor:
                break
        return programs

    def apply_incentives(self, programs: list[dict], now_ms: int) -> None:
        programs = [p for p in programs if p.get("incentive_type") == "liquidity" and p.get("market_ticker")]
        if not programs:
            return
        self.store.write("incentives", {"programs": programs}, ts_ms=now_ms)

        def per_day(p):
            start, end = _ts(p.get("start_date")), _ts(p.get("end_date"))
            live = start and end and start <= now_ms < end
            return (p.get("period_reward") or 0) / 10_000 / max(1.0, (end - start) / 86_400_000) if live else 0.0
        chosen = [p for p in sorted(programs, key=per_day, reverse=True) if per_day(p) > 0][:E_MAX]
        keep = {p["market_ticker"] for p in chosen}
        for t, m in list(self.meta.items()):
            if m["set"] == "E" and t not in keep:
                self.unwatch(t)
        for p in chosen:
            if p["market_ticker"] not in self.meta:
                self.watch(p["market_ticker"], {"series": None, "event": None, "close_ms": None, "strike": None, "strike_type": None, "set": "E"})

    def fetch_fade(self, now_ms: int) -> list[dict]:
        found, cursor = [], None
        for _ in range(F_PAGES):
            payload = self.rest.get("/markets", {"status": "open", "limit": 1000, "min_close_ts": int(now_ms / 1000 + F_MIN_DAYS * 86_400),
                                                 "max_close_ts": int(now_ms / 1000 + F_MAX_DAYS * 86_400), "cursor": cursor})
            if not payload:
                break
            for m in payload.get("markets") or []:
                ask, vol = _num(m.get("yes_ask_dollars")), _num(m.get("volume_24h_fp")) or 0.0
                if ask is not None and F_YES_ASK[0] <= ask <= F_YES_ASK[1] and vol > 0 and not str(m.get("ticker", "")).startswith(F_EXCLUDE):
                    found.append((vol, m))
            cursor = payload.get("cursor")
            if not cursor:
                break
        return [m for _, m in sorted(found, key=lambda x: -x[0])[:F_MAX]]

    def apply_fade(self, chosen: list[dict], now_ms: int) -> None:
        if not chosen:
            return
        keep = {m["ticker"] for m in chosen}
        for t, m in list(self.meta.items()):
            if m["set"] == "F" and t not in keep:
                if m.get("close_ms"):
                    self.pending_settle[t] = m["close_ms"]  # F may hold contracts in it: keep its result coming
                self.unwatch(t)
        for m in chosen:
            if m["ticker"] not in self.meta:
                self.watch(m["ticker"], {"series": None, "event": m.get("event_ticker"), "close_ms": _ts(m.get("close_time")), "strike": None,
                                         "strike_type": m.get("strike_type"), "set": "F"})
        self._save_state()

    def due_settlements(self, now_ms: int) -> list[str]:
        return [t for t, close in self.pending_settle.items() if now_ms >= close + SETTLE_AFTER_MS]

    def fetch_settlements(self, tickers: list[str]) -> dict[str, dict | None]:
        return {t: self.rest.get(f"/markets/{t}") for t in tickers}

    def apply_settlements(self, fetched: dict[str, dict | None], now_ms: int) -> None:
        for t, payload in fetched.items():
            m = (payload or {}).get("market") or {}
            close = self.pending_settle.get(t)
            if m.get("result") in ("yes", "no"):
                self.store.write("settled", {"series": t.split("-")[0], "event": m.get("event_ticker"), "close_ms": close,
                                             "rows": [[t, m["result"], _num(m.get("expiration_value"))]]}, ts_ms=now_ms)
                self.pending_settle.pop(t, None)
            elif close is not None and now_ms > close + SETTLE_GIVE_UP_MS:
                self.note(f"{t} closed without a result; giving up on it")
                self.pending_settle.pop(t, None)
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

    # ---- messages ----------------------------------------------------------------------------------
    def handle(self, m: dict) -> None:
        kind, sid, seq, body = m.get("type"), m.get("sid"), m.get("seq"), m.get("msg") or {}
        self.counters["messages"] += 1
        if kind == "subscribed":
            self._confirmed(body.get("channel"), body.get("sid", sid))
            return
        if kind == "error":
            self.counters["errors"] += 1
            self.note(f"kalshi ws error {body.get('code')}: {body.get('msg')}")
            channel = self.subscribing.pop(m.get("id"), None)
            if channel:
                self.sent.pop(channel, None)  # the next market watched tries the subscribe again
            return
        if sid is not None and seq is not None:
            # Kalshi does not say whether ok/error replies take numbers in the data sequence, so only a data
            # message whose seq runs ahead of the next one expected is a gap, and the count never goes back
            expected = self.expected_seq.get(sid)
            if kind in DATA_KINDS and expected is not None and seq > expected:
                channel = self.sid_channel.get(sid)
                self.counters["gaps" if channel == "orderbook_delta" else "trade_gaps"] += 1
                if channel == "orderbook_delta":
                    self._resnapshot(sid)
            self.expected_seq[sid] = max(expected or 0, seq + 1)
        if kind == "orderbook_snapshot":
            self.books[body["market_ticker"]].snapshot(body)
        elif kind == "orderbook_delta":
            book = self.books.get(body["market_ticker"])
            if book is not None and book.ready:
                book.delta(body)
        elif kind == "trade":
            self.store.write("trade", {"ticker": body.get("market_ticker"), "yes_price": _num(body.get("yes_price_dollars")), "count": _num(body.get("count_fp")),
                                       "taker_side": body.get("taker_outcome_side") or body.get("taker_side"), "trade_ts": body.get("ts_ms"),
                                       "block": body.get("is_block_trade")}, ts_ms=self.now_ms())
        elif kind == "cfbenchmarks_value":
            try:
                value = float(json.loads(body.get("data") or "{}").get("value"))
            except (TypeError, ValueError):
                return
            q = body.get("last_60s_windowed_average_15min") or {}
            self.store.write("index", {"symbol": body.get("index_id"), "value": value, "avg60": _num((body.get("avg_60s_data") or {}).get("value")),
                                       "qavg": _num(q.get("value")), "qn": q.get("window_size")}, ts_ms=self.now_ms())

    def _resnapshot(self, sid: int) -> None:
        for book in self.books.values():
            book.ready = False
        tickers = sorted(self.meta)
        for i in range(0, len(tickers), 100):  # the most tickers one get_snapshot takes is not documented
            self._command("update_subscription", {"sids": [sid], "market_tickers": tickers[i:i + 100], "action": "get_snapshot"})

    def write_books(self, now_ms: int) -> None:
        for t, meta in self.meta.items():
            book = self.books.get(t)
            if book is None or not book.ready:
                continue
            s = meta["set"]
            if s == "15m" and meta.get("close_ms") and meta["close_ms"] - now_ms <= 180_000:
                s = "15m_late"
            since = now_ms - self.last_written.get(t, 0)
            if since >= CADENCE_S[s] * 1000 and (book.changed or since >= HEARTBEAT_S[s] * 1000):
                self.store.write("book", {"ticker": t, **meta, **book.normalized(None if meta["set"] == "E" else LEVELS)}, ts_ms=now_ms)
                self.last_written[t] = now_ms
                book.changed = False

    def write_status(self, now_ms: int, note: str | None = None) -> None:
        rec = {"source": "ws", "ws": dict(self.counters), "rest": self.rest.counters(), "errors": list(self.errors),
               "watched": {s: sum(1 for m in self.meta.values() if m["set"] == s) for s in ("15m", "E", "F")}, "pending_settle": len(self.pending_settle)}
        if note:
            rec["note"] = note
        self.store.write("lab_status", rec, ts_ms=now_ms)


async def maintain(feed: Feed, until_ms: int, *, stop: asyncio.Event, refreshed_ms: int) -> None:
    """Market discovery and settlement beside the socket loop; a REST wait never stalls the feed."""
    last = {k: refreshed_ms for k in REFRESH_S}
    while not stop.is_set() and feed.now_ms() < until_ms:
        now = feed.now_ms()
        try:
            if now - last["crypto"] >= REFRESH_S["crypto"] * 1000:
                last["crypto"] = now
                feed.apply_crypto(await asyncio.to_thread(feed.fetch_crypto), feed.now_ms())
                due = feed.due_settlements(feed.now_ms())
                if due:
                    feed.apply_settlements(await asyncio.to_thread(feed.fetch_settlements, due), feed.now_ms())
            if now - last["incentives"] >= REFRESH_S["incentives"] * 1000:
                last["incentives"] = now
                feed.apply_incentives(await asyncio.to_thread(feed.fetch_incentives), feed.now_ms())
            if now - last["fade"] >= REFRESH_S["fade"] * 1000:
                last["fade"] = now
                feed.apply_fade(await asyncio.to_thread(feed.fetch_fade, now), feed.now_ms())
        except Exception as exc:  # noqa: BLE001 - discovery failing must not stop the recording
            feed.counters["maintenance_errors"] += 1
            feed.note(f"market refresh failed: {type(exc).__name__}: {exc}")
        try:
            await asyncio.wait_for(stop.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass


async def run(feed: Feed, until_ms: int, sign, key_id: str, *, stop: asyncio.Event, refreshed_ms: int = 0) -> None:
    import websockets

    upkeep = asyncio.create_task(maintain(feed, until_ms, stop=stop, refreshed_ms=refreshed_ms))
    backoff, last_status = 2.0, 0
    try:
        while not stop.is_set() and feed.now_ms() < until_ms:
            try:
                async with websockets.connect(URL, additional_headers=ws_headers(key_id, sign), max_size=2 ** 26, open_timeout=20) as ws:
                    for cmd in feed.connected():
                        await ws.send(json.dumps(cmd))
                    feed.counters["connects"] += 1
                    backoff = 2.0
                    while not stop.is_set() and feed.now_ms() < until_ms:
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        except asyncio.TimeoutError:
                            raw = None
                        if raw is not None:
                            try:
                                feed.handle(json.loads(raw))
                            except (ValueError, KeyError, TypeError) as exc:
                                feed.counters["bad_messages"] += 1
                                feed.note(f"unreadable message ({type(exc).__name__}: {exc})")
                        while feed.outbox:
                            await ws.send(json.dumps(feed.outbox.pop(0)))
                        now = feed.now_ms()
                        feed.write_books(now)
                        if now - last_status >= STATUS_S * 1000:
                            feed.write_status(now)
                            last_status = now
            except Exception as exc:  # noqa: BLE001 - reconnect on anything the socket throws
                feed.counters["disconnects"] += 1
                feed.note(f"kalshi ws disconnected ({type(exc).__name__}: {exc}); reconnecting in {backoff:.0f} s")
                try:
                    await asyncio.wait_for(stop.wait(), timeout=backoff)
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, 120.0)
    finally:
        stop.set()
        await upkeep


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
    store = LabStore(args.data, stream=STREAM)
    Path(args.data).mkdir(parents=True, exist_ok=True)
    feed = Feed(store, LabRest(budget=Budget(args.rate, 3.0)), state_path=Path(args.data) / "ws_state.json")
    now = feed.now_ms()
    for refresh in (feed.refresh_crypto, feed.refresh_incentives, feed.refresh_fade):
        try:
            refresh(now)
        except Exception as exc:  # noqa: BLE001 - the loop retries discovery on its own schedule
            feed.note(f"first market refresh failed: {type(exc).__name__}: {exc}")
    stop = asyncio.Event()  # the first connection subscribes every market found (Feed.connected)

    async def go():
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)
        await run(feed, int(args.until * 1000) if args.until else int(now + args.minutes * 60_000), sign, key_id, stop=stop, refreshed_ms=now)

    try:
        asyncio.run(go())
    finally:
        feed.write_status(feed.now_ms(), note="ws recorder stopped")
        store.close()
        store.seal_closed_hours()
        print(f"lab ws recorder: {dict(feed.counters)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
