"""Public Kalshi REST for the lab, under a strict request budget so it never crowds the live desk, which
shares this network address and Kalshi's per-address limit. GET only; a 429 pauses every request."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from kalshi.api import KalshiApiError, KalshiClient


class Budget:
    """Token bucket: `rate` requests a second on average, at most `burst` at once."""

    def __init__(self, rate: float, burst: float = 2.0, *, clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep) -> None:
        self.rate, self.burst = rate, burst
        self._tokens, self._last = burst, clock()
        self._clock, self._sleep = clock, sleep
        self.paused_until = 0.0

    def take(self) -> None:
        while True:
            now = self._clock()
            if now < self.paused_until:
                self._sleep(self.paused_until - now)
                continue
            self._tokens = min(self.burst, self._tokens + (now - self._last) * self.rate)
            self._last = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            self._sleep((1.0 - self._tokens) / self.rate)

    def pause(self, seconds: float) -> None:
        self.paused_until = max(self.paused_until, self._clock() + seconds)


class LabRest:
    def __init__(self, client: KalshiClient | None = None, budget: Budget | None = None) -> None:
        self.client = client or KalshiClient()
        self.budget = budget or Budget(0.25, 2.0)
        self.requests = self.errors = self.rate_limited = 0
        self._backoff = 30.0

    def get(self, path: str, params: Mapping[str, object] | None = None) -> dict | None:
        self.budget.take()
        self.requests += 1
        try:
            payload = self.client.get(path, params)
        except KalshiApiError as exc:
            self.errors += 1
            if exc.rate_limited:
                self.rate_limited += 1
                self.budget.pause(max(self._backoff, exc.retry_after_s or 0.0))
                self._backoff = min(self._backoff * 2, 300.0)
            return None
        self._backoff = 30.0
        return payload

    def counters(self) -> dict:
        return {"requests": self.requests, "errors": self.errors, "rate_limited": self.rate_limited}
