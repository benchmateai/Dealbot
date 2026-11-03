"""Minimal Kalshi Trade API v2 client (read endpoints only) and the fee formulas.

Prices on the wire are integer cents, or dollar strings in newer responses; `parse_market` turns a
market object into a `ContractInfo` with prices in dollars (0 to 1). Fees follow Kalshi's published
schedule: taker fee = ceil(rate * contracts * price * (1 - price)) to the cent with rate 0.07;
maker fee uses the maker rate, zero on most series. Confirm both on kalshi.com before relying on them.
"""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from kalshi.auth import KalshiAuth

DEFAULT_PROD_URL = "https://api.elections.kalshi.com"
DEFAULT_DEMO_URL = "https://demo-api.kalshi.co"
API_PREFIX = "/trade-api/v2"
USER_AGENT = "dealbot-desk/0.1 (paper trading research)"
TAKER_RATE = 0.07
Fetch = Callable[[str, Mapping[str, str]], dict]


class KalshiApiError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def taker_fee_usd(contracts: float, price: float, rate: float = TAKER_RATE) -> float:
    """Kalshi's taker fee in dollars, rounded up to the cent."""
    if contracts <= 0 or not 0 < price < 1:
        return 0.0
    raw = rate * contracts * price * (1.0 - price)
    return math.ceil(raw * 100 - 1e-9) / 100


def maker_fee_usd(contracts: float, price: float, rate: float = 0.0) -> float:
    return taker_fee_usd(contracts, price, rate) if rate > 0 else 0.0


def _timestamp_ms(text: object) -> int | None:
    if not isinstance(text, str) or not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def _price(market: Mapping, key: str) -> float | None:
    dollars = market.get(f"{key}_dollars")
    if dollars is not None:
        try:
            return float(dollars)
        except (TypeError, ValueError):
            return None
    cents = market.get(key)
    if cents is None:
        return None
    try:
        return float(cents) / 100.0
    except (TypeError, ValueError):
        return None


def _strike(market: Mapping) -> tuple[float | None, str]:
    strike_type = str(market.get("strike_type") or "greater").lower()
    for key in ("floor_strike", "cap_strike", "custom_strike"):
        value = market.get(key)
        if isinstance(value, (int, float)):
            return float(value), strike_type
        if isinstance(value, str):
            try:
                return float(value.replace(",", "")), strike_type
            except ValueError:
                continue
    return None, strike_type


@dataclass(frozen=True)
class ContractInfo:
    ticker: str
    event_ticker: str
    title: str
    strike: float | None
    strike_type: str
    open_ts: int | None
    close_ts: int | None
    status: str
    yes_bid: float | None
    yes_ask: float | None
    last_price: float | None
    volume: float | None
    result: str | None

    def expires_in_s(self, now_ms: int) -> float | None:
        return None if self.close_ts is None else (self.close_ts - now_ms) / 1000.0

    def settles_yes(self, underlying_price: float) -> bool | None:
        """Provisional result from the underlying's price at expiry; None when the strike is unknown."""
        if self.strike is None:
            return None
        if self.strike_type in ("less", "less_than", "below"):
            return underlying_price < self.strike
        return underlying_price > self.strike

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def parse_market(market: Mapping) -> ContractInfo:
    strike, strike_type = _strike(market)
    result = market.get("result")
    return ContractInfo(
        ticker=str(market.get("ticker") or ""),
        event_ticker=str(market.get("event_ticker") or ""),
        title=str(market.get("title") or market.get("subtitle") or ""),
        strike=strike,
        strike_type=strike_type,
        open_ts=_timestamp_ms(market.get("open_time")),
        close_ts=_timestamp_ms(market.get("close_time") or market.get("expected_expiration_time") or market.get("expiration_time")),
        status=str(market.get("status") or ""),
        yes_bid=_price(market, "yes_bid"),
        yes_ask=_price(market, "yes_ask"),
        last_price=_price(market, "last_price"),
        volume=float(market["volume"]) if isinstance(market.get("volume"), (int, float)) else None,
        result=result if result in ("yes", "no") else None,
    )


def parse_orderbook(payload: Mapping) -> tuple[float | None, float | None, float, float]:
    """Best yes bid, best yes ask (1 - best no bid), and their sizes, in dollars and contracts."""
    book = payload.get("orderbook") or payload
    yes_levels = book.get("yes") or []
    no_levels = book.get("no") or []

    def best(levels: list) -> tuple[float | None, float]:
        parsed = []
        for level in levels:
            try:
                price, count = level[0], level[1]
                parsed.append((float(price) / 100.0 if isinstance(price, int) or (isinstance(price, str) and price.isdigit()) else float(price), float(count)))
            except (TypeError, ValueError, IndexError):
                continue
        if not parsed:
            return None, 0.0
        return max(parsed, key=lambda pc: pc[0])

    yes_bid, yes_bid_qty = best(yes_levels)
    no_bid, no_bid_qty = best(no_levels)
    yes_ask = None if no_bid is None else round(1.0 - no_bid, 4)
    return yes_bid, yes_ask, yes_bid_qty, no_bid_qty


def http_fetch(url: str, headers: Mapping[str, str], *, timeout_s: float = 5.0) -> dict:
    request = urllib.request.Request(url, headers=dict(headers))
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode()[:200]
        except Exception:  # noqa: BLE001
            pass
        raise KalshiApiError(f"HTTP {exc.code} from Kalshi: {body}", status=exc.code) from None
    except urllib.error.URLError as exc:
        raise KalshiApiError(f"Kalshi unreachable: {exc.reason}") from None


class KalshiClient:
    def __init__(self, base_url: str = DEFAULT_PROD_URL, auth: KalshiAuth | None = None, *, fetch: Fetch | None = None, timeout_s: float = 5.0) -> None:
        self._base = base_url.rstrip("/")
        self._auth = auth
        self._fetch = fetch or (lambda url, headers: http_fetch(url, headers, timeout_s=timeout_s))

    @property
    def authenticated(self) -> bool:
        return self._auth is not None

    def get(self, path: str, params: Mapping[str, object] | None = None, *, signed: bool = False) -> dict:
        """GET an API path. Market data is public on every Kalshi host and is never signed, so a key
        issued for one host (the demo) cannot break reads from another (production); only the
        account endpoints ask for a signature."""
        api_path = API_PREFIX + path
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
        url = f"{self._base}{api_path}" + (f"?{query}" if query else "")
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if signed:
            if self._auth is None:
                raise KalshiApiError(f"{path} needs credentials")
            headers.update(self._auth.headers("GET", api_path))
        payload = self._fetch(url, headers)
        if not isinstance(payload, dict):
            raise KalshiApiError("unexpected response shape")
        return payload

    def markets(self, series_ticker: str, *, status: str | None = "open", limit: int = 50) -> list[ContractInfo]:
        payload = self.get("/markets", {"series_ticker": series_ticker, "status": status, "limit": limit})
        return [parse_market(m) for m in payload.get("markets") or [] if isinstance(m, Mapping)]

    def market(self, ticker: str) -> ContractInfo:
        payload = self.get(f"/markets/{ticker}")
        return parse_market(payload.get("market") or payload)

    def orderbook(self, ticker: str, *, depth: int = 1) -> tuple[float | None, float | None, float, float]:
        return parse_orderbook(self.get(f"/markets/{ticker}/orderbook", {"depth": depth}))

    def balance(self) -> dict:
        return self.get("/portfolio/balance", signed=True)
