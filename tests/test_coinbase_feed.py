import pytest

from feed import make_feed
from feed.base import FeedError
from feed.coinbase import CoinbaseFeed, parse_book
from tests.helpers import T0

BOOK = {"bids": [["2500.01", "0.52", 3]], "asks": [["2500.11", "1.20", 2]], "sequence": 1, "time": "2023-11-14T22:13:20.123456Z"}


def test_parse_book_uses_exchange_time_and_sizes():
    tick = parse_book(BOOK, received_ms=T0 + 999_999)
    assert (tick.bid, tick.ask, tick.bid_qty, tick.ask_qty) == (2500.01, 2500.11, 0.52, 1.20)
    assert tick.ts == 1700000000123 and tick.is_sane()
    assert parse_book({**BOOK, "time": None}, received_ms=T0).ts == T0
    with pytest.raises(FeedError):
        parse_book({"bids": [], "asks": []}, received_ms=T0)
    with pytest.raises(FeedError):
        parse_book({"bids": [["2500.5", "1", 1]], "asks": [["2500.1", "1", 1]], "time": None}, received_ms=T0)


def test_feed_buffers_then_hands_over_point_in_time():
    calls = []
    quotes = iter([
        {**BOOK, "time": "2023-11-14T22:13:20Z"},
        {**BOOK, "time": "2023-11-14T22:13:22Z"},
        {"bids": [], "asks": []},
        {**BOOK, "time": "2023-11-14T22:13:22Z"},
        {**BOOK, "time": "2023-11-14T22:13:24Z"},
    ])

    def fetch(url):
        calls.append(url)
        return next(quotes)

    feed = CoinbaseFeed(("ETH-USD",), fetch=fetch, now_ms=lambda: T0)
    for _ in range(5):
        feed.poll_once()
    assert calls[0] == "https://api.exchange.coinbase.com/products/ETH-USD/book?level=1"
    assert feed.polls == 5 and feed.errors == 1
    # T0 is 2023-11-14T22:13:20Z, so the quotes above are at T0, T0+2s (twice: the repeat is dropped) and T0+4s
    first = feed.advance(T0 + 2_500)
    assert [t.ts for t in first["ETH-USD"]] == [T0, T0 + 2_000]
    assert feed.history("ETH-USD") == first["ETH-USD"] and feed.last_tick_age_ms("ETH-USD", T0 + 10_000) == 8_000
    rest = feed.advance(T0 + 60_000)
    assert [t.ts for t in rest["ETH-USD"]] == [T0 + 4_000] and len(feed.history("ETH-USD")) == 3


def test_make_feed_and_validation():
    feed = make_feed("coinbase", ("ETH-USD", "BTC-USD"), start_ms=0, poll_ms=100, base_url="https://api-public.sandbox.exchange.coinbase.com/")
    assert isinstance(feed, CoinbaseFeed) and feed.symbols == ("ETH-USD", "BTC-USD") and feed.last_tick_age_ms("ETH-USD", 1) is None
    with pytest.raises(FeedError):
        CoinbaseFeed(("ethusd",))
    with pytest.raises(FeedError):
        CoinbaseFeed(())


def test_background_poller_starts_and_stops():
    feed = CoinbaseFeed(("ETH-USD",), poll_ms=500, fetch=lambda url: BOOK, now_ms=lambda: T0).start()
    import time

    deadline = time.monotonic() + 3
    while feed.polls == 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    feed.close()
    assert feed.polls >= 1 and feed.advance(T0 + 10_000_000)["ETH-USD"]
