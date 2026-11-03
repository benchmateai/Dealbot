"""The lab's recorder, public-REST mode (no key needed). Every POLL_S seconds, and every FAST_POLL_S in the
last FAST_WINDOW_S before a watched close, it records each watched series' nearest-closing event: one
`book_top` record with a compact row per market (ticker, strike type, floor, cap, YES bid and ask, and
their sizes). Each 15-minute contract is fetched together with its hourly ladder so the pair is close
to simultaneous. After an event closes it records the settlement (`settled`: result and settlement
value per market) once Kalshi has published it. Every few minutes it records its own request counters
(`lab_status`), so its load on Kalshi's per-address limit is visible next to the live desk's.

    python -m lab.recorder --minutes 110 --data lab/data
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import datetime

from lab.rest import Budget, LabRest
from lab.store import LabStore

log = logging.getLogger("lab.recorder")

# requested in this order, in pairs, so a 15-minute contract and its hourly ladder are fetched back to back
SERIES = (("KXBTC15M", "15m"), ("KXBTCD", "ladder"), ("KXETH15M", "15m"), ("KXETHD", "ladder"), ("KXBTC", "range"), ("KXETH", "range"))
ROW_FIELDS = ("ticker", "strike_type", "floor", "cap", "yes_bid", "yes_ask", "bid_size", "ask_size")
POLL_S, FAST_POLL_S, FAST_WINDOW_S = 60, 15, 180
MAX_PAGES = 3
DISCOVER_S, STATUS_S = 600, 300
SETTLE_AFTER_MS, SETTLE_GIVE_UP_MS = 120_000, 3_600_000


def _num(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ts(text) -> int | None:
    if not text:
        return None
    try:
        return int(datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None


def compact(m: dict) -> list:
    return [m.get("ticker"), m.get("strike_type"), _num(m.get("floor_strike")), _num(m.get("cap_strike")), _num(m.get("yes_bid_dollars")),
            _num(m.get("yes_ask_dollars")), _num(m.get("yes_bid_size_fp")), _num(m.get("yes_ask_size_fp"))]


class Recorder:
    def __init__(self, rest: LabRest, store: LabStore, *, now_ms=lambda: int(time.time() * 1000)) -> None:
        self.rest, self.store, self.now_ms = rest, store, now_ms
        self.events: dict[str, tuple[str, int]] = {}   # series -> (nearest open event, its close)
        self.pending: dict[str, tuple[int, str]] = {}  # event -> (close, series) awaiting settlement
        self._last_discover = 0
        self.stop = False

    def discover(self, now_ms: int) -> None:
        for series, _ in SERIES:
            payload = self.rest.get("/markets", {"series_ticker": series, "status": "open", "limit": 200})
            closes: dict[str, int] = {}
            for m in (payload or {}).get("markets") or []:
                c = _ts(m.get("close_time"))
                if c and c > now_ms and m.get("event_ticker"):
                    closes[m["event_ticker"]] = min(c, closes.get(m["event_ticker"], c))
            if closes:
                event = min(closes, key=closes.get)
                self.events[series] = (event, closes[event])
        self._last_discover = now_ms

    def snapshot(self, now_ms: int) -> None:
        for series, kind in SERIES:
            current = self.events.get(series)
            if current is None or current[1] <= now_ms:
                continue
            event, close_ms = current
            markets = self._event_markets(event)
            if markets is None:
                continue
            rows = [compact(m) for m in markets]
            self.store.write("book_top", {"series": series, "type": kind, "event": event, "close_ms": close_ms, "rows": rows}, ts_ms=self.now_ms())
            self.pending.setdefault(event, (close_ms, series))

    def settle(self, now_ms: int) -> None:
        for event, (close_ms, series) in list(self.pending.items()):
            if now_ms < close_ms + SETTLE_AFTER_MS:
                continue
            markets = self._event_markets(event) or []
            if markets and all(m.get("result") in ("yes", "no") for m in markets):
                rows = [[m.get("ticker"), m.get("result"), _num(m.get("expiration_value"))] for m in markets]
                self.store.write("settled", {"series": series, "event": event, "close_ms": close_ms, "rows": rows}, ts_ms=self.now_ms())
                del self.pending[event]
            elif now_ms > close_ms + SETTLE_GIVE_UP_MS:
                self.store.write("lab_status", {"note": f"gave up waiting for {event} to settle"}, ts_ms=self.now_ms())
                del self.pending[event]

    def _event_markets(self, event: str) -> list[dict] | None:
        markets: list[dict] = []
        cursor = None
        for _ in range(MAX_PAGES):
            payload = self.rest.get("/markets", {"event_ticker": event, "limit": 1000, "cursor": cursor})
            if payload is None:
                return None if not markets else markets
            markets += payload.get("markets") or []
            cursor = payload.get("cursor")
            if not cursor:
                break
        return markets

    def next_wait_s(self, now_ms: int) -> float:
        closes = [c for _, c in self.events.values() if c > now_ms]
        fast = any(c - now_ms <= FAST_WINDOW_S * 1000 for c in closes)
        return FAST_POLL_S if fast else POLL_S

    def run(self, until_ms: int, *, sleep=time.sleep) -> None:
        last_status = 0
        while not self.stop and self.now_ms() < until_ms:
            started = self.now_ms()
            if started - self._last_discover >= DISCOVER_S * 1000 or any(c <= started for _, c in self.events.values()) or not self.events:
                self.discover(started)
            self.snapshot(started)
            self.settle(started)
            if started - last_status >= STATUS_S * 1000:
                self.store.write("lab_status", {"rest": self.rest.counters(), "events": {s: e for s, (e, _) in self.events.items()}}, ts_ms=self.now_ms())
                last_status = started
            elapsed = (self.now_ms() - started) / 1000
            sleep(max(0.0, self.next_wait_s(started) - elapsed))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record Kalshi market data for the shadow lab (public REST, read-only)")
    parser.add_argument("--minutes", type=float, default=110.0)
    parser.add_argument("--data", default="lab/data")
    parser.add_argument("--rate", type=float, default=0.25, help="average Kalshi requests a second")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    store = LabStore(args.data)
    rec = Recorder(LabRest(budget=Budget(args.rate, 3.0)), store)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: setattr(rec, "stop", True))
    try:
        rec.run(int(time.time() * 1000 + args.minutes * 60_000))
    finally:
        store.write("lab_status", {"rest": rec.rest.counters(), "note": "recorder stopped"}, ts_ms=int(time.time() * 1000))
        store.close()
        sealed = store.seal_closed_hours()
        print(f"lab recorder: {rec.rest.counters()}; sealed {len(sealed)} hour files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
