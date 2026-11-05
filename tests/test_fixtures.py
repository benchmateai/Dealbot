"""Parsers and the feed against responses recorded from the live exchanges on 2026-11-03.

The mocks the Kalshi path was first built against differed from the real API in small ways (the
orderbook moved to `orderbook_fp` with dollar strings), and each difference left a live run empty.
These fixtures are the real thing; when Kalshi or Coinbase changes shape again, these tests break
instead of a paper run going quiet. Refresh them with tests/fixtures/record.py.
"""

import json
from pathlib import Path

import pytest

from feed.coinbase import parse_book
from kalshi.api import parse_market, parse_orderbook
from kalshi.feed import KalshiFeed, pick_current
from feed.synthetic import SyntheticFeed

FIX = Path(__file__).parent / "fixtures"
SERIES = ("KXETH15M", "KXBTC15M")


def load(name: str) -> dict:
    return json.loads((FIX / name).read_text())


@pytest.mark.parametrize("series", SERIES)
def test_open_markets_parse_into_tradable_contracts(series):
    contracts = [parse_market(m) for m in load(f"kalshi/markets_open_{series}.json")["markets"]]
    assert contracts
    for c in contracts:
        assert c.ticker.startswith(series) and c.strike is not None and c.strike > 0
        assert c.strike_type == "greater_or_equal"
        assert c.open_ts is not None and c.close_ts is not None and c.close_ts - c.open_ts == 900_000
        assert c.yes_bid is not None and c.yes_ask is not None and 0 < c.yes_bid <= c.yes_ask < 1
        assert c.volume is not None and c.result is None
    current = pick_current(contracts, contracts[0].open_ts + 1)
    assert current is not None and current.ticker == min(contracts, key=lambda c: c.close_ts).ticker


@pytest.mark.parametrize("series", SERIES)
def test_the_live_orderbook_gives_a_sane_two_sided_quote(series):
    bid, ask, bid_qty, ask_qty = parse_orderbook(load(f"kalshi/orderbook_{series}.json"))
    assert bid is not None and ask is not None and 0 < bid < ask < 1, (bid, ask)
    assert ask - bid <= 0.05 and bid_qty > 0 and ask_qty > 0


def test_the_market_list_quote_lags_the_orderbook():
    """Recorded back to back: the list said 0.81/0.82 while the book already held YES bids at 0.84.
    Quotes therefore come from the orderbook; the list only names the contracts."""
    listed = parse_market(load("kalshi/market_KXETH15M.json")["market"])
    bid, ask, _, _ = parse_orderbook(load("kalshi/orderbook_KXETH15M.json"))
    assert listed.yes_bid < bid, "if this starts failing, the list may have become live; re-measure before switching"


def test_the_at_or_above_rule_reproduces_every_official_result():
    markets = load("kalshi/markets_settled_KXETH15M.json")["markets"]
    assert len(markets) >= 10
    for raw in markets:
        c = parse_market(raw)
        assert c.result in ("yes", "no") and raw["status"] in ("settled", "finalized")
        assert c.settles_yes(float(raw["expiration_value"])) == (c.result == "yes"), raw["ticker"]


@pytest.mark.parametrize("product", ("ETH-USD", "BTC-USD"))
def test_coinbase_books_parse(product):
    tick = parse_book(load(f"coinbase/book_{product}.json"), received_ms=1_793_680_000_000)
    assert tick.is_sane() and tick.ask - tick.bid < tick.mid * 0.001


class FixtureClient:
    """Serves the recorded responses the way the real client would."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def markets(self, series, *, status="open", limit=50):
        self.calls.append("markets")
        return [parse_market(m) for m in load(f"kalshi/markets_open_{series}.json")["markets"]]

    def market(self, ticker):
        self.calls.append("market")
        return parse_market(load(f"kalshi/market_{ticker.split('-')[0]}.json")["market"])

    def orderbook(self, ticker, *, depth=1):
        self.calls.append("orderbook")
        return parse_orderbook(load(f"kalshi/orderbook_{ticker.split('-')[0]}.json"))


def test_the_feed_turns_recorded_responses_into_ticks_and_contract_state():
    client = FixtureClient()
    first = parse_market(load("kalshi/markets_open_KXETH15M.json")["markets"][0])
    t = first.close_ts - 400_000  # inside the last ten minutes: tradable
    clock = {"now": t - 200_000}
    under = SyntheticFeed(("ETH-USD", "BTC-USD"), start_ms=clock["now"] - 600_000, tick_ms=1000, seed=3, start_prices={"ETH-USD": first.strike, "BTC-USD": 76800.0})
    under.advance(clock["now"])
    feed = KalshiFeed(SERIES, underlying={"KXETH15M": "ETH-USD", "KXBTC15M": "BTC-USD"}, client=client, underlying_feed=under, poll_ms=5000, now_ms=lambda: clock["now"])
    for _ in range(45):
        clock["now"] += 5000
        under.advance(clock["now"])
        out = feed.poll_once()
        assert all(tick is not None for tick in out.values()), out
    feed.advance(clock["now"] + 1)
    assert len(feed.snapshot_history("KXETH15M")) == 45
    state = feed.extra_state("KXETH15M", clock["now"] + 1, block=1)
    assert state["ticker"] == first.ticker and state["tradable"] is True and 0 < state["yes_bid"] < state["yes_ask"] < 1
    assert state["model_p_yes"] is not None and 0.0 <= state["model_p_yes"] <= 1.0
    assert client.calls.count("markets") <= 2 * 10, "the contract list is refreshed every 30 s, not every poll"


def test_the_live_preflight_check_passes_on_recorded_responses():
    from desk.config import DeskConfig
    from desk.preflight import check_live

    cfg = DeskConfig.from_env({"DESK_BOT": "kalshi", "FEED": "kalshi", "DESK_SYMBOLS": "KXETH15M,KXBTC15M", "JUDGE_URL": "stub://local", "LOG_DIR": "/tmp/unused"})
    first = parse_market(load("kalshi/markets_open_KXETH15M.json")["markets"][0])
    result = check_live(cfg, client=FixtureClient(), book_fetch=lambda p: load(f"coinbase/book_{p}.json"), now_ms=lambda: first.open_ts + 60_000, sleep=lambda s: None)
    assert result.ok, result.summary()
    assert len(result.lines) == 4


def test_the_live_preflight_check_names_a_broken_quote():
    from desk.config import DeskConfig
    from desk.preflight import check_live

    class OneSided(FixtureClient):
        def orderbook(self, ticker, *, depth=1):
            return (0.40, None, 10.0, 0.0)

    cfg = DeskConfig.from_env({"DESK_BOT": "kalshi", "FEED": "kalshi", "DESK_SYMBOLS": "KXETH15M", "JUDGE_URL": "stub://local", "LOG_DIR": "/tmp/unused"})
    first = parse_market(load("kalshi/markets_open_KXETH15M.json")["markets"][0])
    result = check_live(cfg, client=OneSided(), book_fetch=lambda p: load(f"coinbase/book_{p}.json"), now_ms=lambda: first.open_ts + 60_000, sleep=lambda s: None)
    assert not result.ok and "not two-sided" in result.summary()
