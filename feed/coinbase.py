"""Live quotes from Coinbase Exchange public market data. No API key: the level-1 order book endpoint
is public. A background thread polls every `poll_ms`; `advance` hands the desk the ticks collected so
far with `ts < until_ms`, exactly like the synthetic and replay feeds. Tick timestamps are the
exchange's own `time` when present, so the snapshot stays point-in-time correct.

Public rate limit is ten requests per second; the default poll of two seconds per symbol is far below it.
A dead or lagging feed produces no ticks, which the free cut and the one-call stage turn into holds.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone

from feed.base import FeedError, Tick

log = logging.getLogger("feed.coinbase")
DEFAULT_BASE_URL = "https://api.exchange.coinbase.com"
USER_AGENT = "dealbot-desk/0.1 (paper trading research)"
Fetch = Callable[[str], dict]


def http_fetch(url: str, *, timeout_s: float = 5.0) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        return json.loads(response.read().decode())


def parse_book(payload: dict, *, received_ms: int) -> Tick:
    """Turn a level-1 book response into a Tick. Raises FeedError on anything that is not a usable quote."""
    try:
        bid = payload["bids"][0]
        ask = payload["asks"][0]
        tick = Tick(_timestamp_ms(payload.get("time"), received_ms), float(bid[0]), float(ask[0]), float(bid[1]), float(ask[1]))
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise FeedError(f"unusable book payload: {exc}") from exc
    if not tick.is_sane():
        raise FeedError(f"insane quote bid={tick.bid} ask={tick.ask}")
    return tick


def _timestamp_ms(text: object, fallback_ms: int) -> int:
    if not isinstance(text, str) or not text:
        return fallback_ms
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return fallback_ms
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


class CoinbaseFeed:
    def __init__(self, symbols: tuple[str, ...], *, poll_ms: int = 2000, base_url: str = DEFAULT_BASE_URL, fetch: Fetch | None = None, max_history: int = 50_000, now_ms: Callable[[], int] | None = None) -> None:
        if not symbols:
            raise FeedError("coinbase feed needs at least one product id such as ETH-USD")
        for sym in symbols:
            if not sym or "-" not in sym or sym != sym.upper():
                raise FeedError(f"{sym!r} is not a Coinbase product id (expected BASE-QUOTE, upper case)")
        self.symbols = tuple(symbols)
        self._poll_ms = max(500, int(poll_ms))
        self._base_url = base_url.rstrip("/")
        self._fetch = fetch or http_fetch
        self._now = now_ms or (lambda: int(time.time() * 1000))
        self._max_history = max_history
        self._lock = threading.Lock()
        self._buffer: dict[str, list[Tick]] = {s: [] for s in self.symbols}
        self._hist: dict[str, list[Tick]] = {s: [] for s in self.symbols}
        self._last_ts: dict[str, int] = {}
        self.errors = 0
        self.polls = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # ---- polling ---------------------------------------------------------------------------

    def poll_once(self) -> dict[str, Tick | None]:
        """Fetch one quote per symbol into the buffer. Never raises; failures count in `errors`."""
        out: dict[str, Tick | None] = {}
        for sym in self.symbols:
            url = f"{self._base_url}/products/{sym}/book?level=1"
            try:
                tick = parse_book(self._fetch(url), received_ms=self._now())
            except (FeedError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                self.errors += 1
                log.warning("%s: %s", sym, exc)
                out[sym] = None
                continue
            with self._lock:
                if tick.ts > self._last_ts.get(sym, -1):
                    self._buffer[sym].append(tick)
                    self._last_ts[sym] = tick.ts
            out[sym] = tick
        self.polls += 1
        return out

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            self.poll_once()
            elapsed = time.monotonic() - started
            self._stop.wait(max(0.0, self._poll_ms / 1000 - elapsed))

    def start(self) -> CoinbaseFeed:
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="coinbase-feed", daemon=True)
            self._thread.start()
        return self

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    # ---- MarketFeed ------------------------------------------------------------------------

    def advance(self, until_ms: int) -> dict[str, list[Tick]]:
        out: dict[str, list[Tick]] = {}
        with self._lock:
            for sym in self.symbols:
                buffered = self._buffer[sym]
                ready = [t for t in buffered if t.ts < until_ms]
                self._buffer[sym] = [t for t in buffered if t.ts >= until_ms]
                hist = self._hist[sym]
                hist.extend(ready)
                if len(hist) > self._max_history:
                    del hist[: len(hist) - self._max_history]
                out[sym] = ready
        return out

    def history(self, sym: str) -> list[Tick]:
        return self._hist[sym]

    def seed_history(self, sym: str, ticks: list[Tick]) -> None:
        """Restore a tail of ticks from a checkpoint so the first blocks after a restart are not blind."""
        if sym in self._hist and ticks:
            self._hist[sym] = sorted(ticks, key=lambda t: t.ts)

    def last_tick_age_ms(self, sym: str, now_ms: int) -> int | None:
        hist = self._hist.get(sym)
        return None if not hist else now_ms - hist[-1].ts
