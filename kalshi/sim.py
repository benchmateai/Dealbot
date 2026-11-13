"""A simulated Kalshi series for offline runs. Never used by a live or paper run.

Contracts roll every `cycle_ms` from `epoch_ms`; each one's strike is fixed per series. The book is
either fixed or, with `fair`, quoted one cent either side of a fair probability that moves with the
underlying, the way a real 15-minute binary's price does. Nothing settles officially unless
`official_result` says so (the feed then settles from the underlying, as it does when Kalshi has not
published a result yet). The client answers the same calls the real one does: markets(), market()
and orderbook().
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from kalshi.api import ContractInfo

CYCLE_MS = 900_000


class SimKalshiClient:
    def __init__(
        self,
        now_ms: Callable[[], int],
        *,
        strikes: Mapping[str, float],
        epoch_ms: int,
        book: tuple[float, float, float, float] = (0.28, 0.30, 500.0, 500.0),
        cycle_ms: int = CYCLE_MS,
        official_result: str | None = None,
        fair: Callable[[str, ContractInfo, int], float | None] | None = None,
    ) -> None:
        self._now = now_ms
        self.strikes = dict(strikes)
        self.epoch_ms = epoch_ms
        self.book = book
        self.cycle_ms = cycle_ms
        self.official_result = official_result
        self.fair = fair
        self.calls: list[tuple[str, str]] = []

    def _quote(self, series: str, contract: ContractInfo) -> tuple[float | None, float | None, float, float]:
        if self.fair is None:
            return self.book
        p = self.fair(series, contract, self._now())
        if p is None:
            return None, None, 0.0, 0.0
        bid = min(0.98, max(0.01, round(p - 0.01, 2)))
        return bid, round(bid + 0.02, 2), self.book[2], self.book[3]

    @property
    def authenticated(self) -> bool:
        return False

    def _contract(self, series: str, idx: int, *, settled: bool = False) -> ContractInfo:
        open_ts = self.epoch_ms + idx * self.cycle_ms
        base = ContractInfo(f"{series}-SIM{idx}", f"{series}-SIM{idx}", "", self.strikes[series], "greater_or_equal", open_ts, open_ts + self.cycle_ms, "active", None, None, None, None, None)
        bid, ask = self._quote(series, base)[:2] if not settled else (None, None)
        return ContractInfo(
            ticker=f"{series}-SIM{idx}",
            event_ticker=f"{series}-SIM{idx}",
            title=f"{series} above {self.strikes[series]} (simulated #{idx})",
            strike=self.strikes[series],
            strike_type="greater_or_equal",
            open_ts=open_ts,
            close_ts=open_ts + self.cycle_ms,
            status="settled" if settled else "active",
            yes_bid=bid,
            yes_ask=ask,
            last_price=None if bid is None or ask is None else round((bid + ask) / 2, 4),
            volume=1000.0,
            result=self.official_result if settled else None,
        )

    def markets(self, series: str, *, status: str | None = "open", limit: int = 50) -> list[ContractInfo]:
        self.calls.append(("markets", series))
        idx = (self._now() - self.epoch_ms) // self.cycle_ms
        return [self._contract(series, idx), self._contract(series, idx + 1)]

    def market(self, ticker: str) -> ContractInfo:
        self.calls.append(("market", ticker))
        series, _, rest = ticker.rpartition("-SIM")
        return self._contract(series, int(rest), settled=True)

    def orderbook(self, ticker: str, *, depth: int = 1) -> tuple[float | None, float | None, float, float]:
        self.calls.append(("orderbook", ticker))
        series, _, rest = ticker.rpartition("-SIM")
        open_ts = self.epoch_ms + int(rest) * self.cycle_ms
        contract = ContractInfo(ticker, ticker, "", self.strikes[series], "greater_or_equal", open_ts, open_ts + self.cycle_ms, "active", None, None, None, None, None)
        return self._quote(series, contract)
