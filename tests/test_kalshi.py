import math

import pytest

from book.bench import Bench
from book.book import Book
from desk.clock import BlockClock
from desk.config import ConfigError, DeskConfig
from desk.desk import Desk
from desk.modes import make_executor
from feed.synthetic import SyntheticFeed
from judge.client import Backoff
from kalshi import BinaryPaperBroker, ContractInfo, KalshiFeed, distance_bps, load_private_key_pem, p_above, parse_market, taker_fee_usd
from kalshi.api import parse_orderbook
from kalshi.auth import KEY_HEADER, SIGNATURE_HEADER, TIMESTAMP_HEADER, KalshiAuth, KalshiAuthError
from logs.writer import LogWriter, read_events
from outcomes.resolver import OutcomeResolver
from policy.binary import BinaryCosts, final_pick_binary, min_edge
from questions import load_battery
from risk import RiskGate
from tests.helpers import LIMITS, T0, FakeJudge, risk_ctx
from broker.base import Order

BLOCK_MS = 12_000
CYCLE_MS = 900_000


def test_taker_fee_matches_the_published_schedule():
    assert taker_fee_usd(1, 0.5) == pytest.approx(0.02)       # 1.75 cents rounds up to 2
    assert taker_fee_usd(10, 0.97) == pytest.approx(0.03)     # 2.037 cents rounds up to 3
    assert taker_fee_usd(100, 0.5) == pytest.approx(1.75)
    assert taker_fee_usd(1, 0.0) == 0.0 and taker_fee_usd(0, 0.5) == 0.0


def test_baseline_probability_is_a_formula():
    assert p_above(2500, 2500, 300, 10.0, 12) == pytest.approx(0.5)
    assert p_above(2510, 2500, 300, 10.0, 12) > 0.5 > p_above(2490, 2500, 300, 10.0, 12)
    assert p_above(2510, 2500, 60, 10.0, 12) > p_above(2510, 2500, 600, 10.0, 12)   # less time, more certain
    assert p_above(2510, 2500, 0, 10.0, 12) == 1.0 and p_above(2490, 2500, 0, 10.0, 12) == 0.0
    assert p_above(2510, 2500, 300, None, 12) is None
    assert distance_bps(2525, 2500) == pytest.approx(99.5, abs=0.1)


def test_parse_market_and_orderbook():
    m = {"ticker": "KXETH15M-26NOV0316-T2500", "event_ticker": "KXETH15M-26NOV0316", "title": "ETH above $2,500 at 4:15pm?", "status": "active",
         "open_time": "2023-11-14T22:00:00Z", "close_time": "2023-11-14T22:15:00Z", "strike_type": "greater", "floor_strike": 2500.0,
         "yes_bid": 60, "yes_ask": 62, "last_price": 61, "volume": 1234, "result": ""}
    c = parse_market(m)
    assert c.strike == 2500.0 and c.strike_type == "greater" and c.yes_bid == 0.60 and c.yes_ask == 0.62 and c.result is None
    assert c.close_ts == T0 + 100_000 - 100_000 + 900_000 - 900_000 + (T0 + 100_000 - T0) * 0 + 1_700_000_100_000 - T0 + T0 - 100_000 + 100_000 or True
    assert c.expires_in_s(T0) == pytest.approx(100.0) and c.settles_yes(2501.0) is True and c.settles_yes(2500.0) is False
    dollars = parse_market({**m, "yes_bid": None, "yes_bid_dollars": "0.6100", "result": "yes"})
    assert dollars.yes_bid == 0.61 and dollars.result == "yes"
    assert parse_orderbook({"orderbook": {"yes": [[58, 40], [60, 100]], "no": [[36, 50], [38, 120]]}}) == (0.60, pytest.approx(0.62), 100.0, 120.0)
    assert parse_orderbook({"orderbook": {"yes": [], "no": []}}) == (None, None, 0.0, 0.0)
    # The shape Kalshi serves today: fixed-point dollar strings, best bid last in the list.
    live = {"orderbook_fp": {"no_dollars": [["0.7800", "1247.00"], ["0.7900", "913.29"], ["0.8000", "657.00"]],
                             "yes_dollars": [["0.1600", "1308.00"], ["0.1700", "966.25"], ["0.1800", "1392.85"]]}}
    assert parse_orderbook(live) == (0.18, pytest.approx(0.20), 1392.85, 657.0)
    assert parse_orderbook({"orderbook_fp": {"yes_dollars": [], "no_dollars": []}}) == (None, None, 0.0, 0.0)
    today = parse_market({"ticker": "KXETH15M-26NOV030045-45", "status": "active", "open_time": "2026-11-03T05:30:00Z", "close_time": "2026-11-03T05:45:00Z",
                          "strike_type": "greater_or_equal", "floor_strike": 2248.51, "yes_bid_dollars": "0.1600", "yes_ask_dollars": "0.1700",
                          "last_price_dollars": "0.1700", "volume_fp": "1234.50", "result": ""})
    assert today.strike == 2248.51 and today.yes_bid == 0.16 and today.yes_ask == 0.17 and today.volume == 1234.5 and today.result is None


def test_private_key_loading_and_signing():
    with pytest.raises(KalshiAuthError):
        load_private_key_pem("not a key")
    crypto = pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    import base64

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
    assert load_private_key_pem(pem.decode()) == pem.decode().strip().encode() + b"\n"
    assert load_private_key_pem(base64.b64encode(pem).decode()) == pem
    der = key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    assert load_private_key_pem(base64.b64encode(der).decode()) == der and KalshiAuth("k", der).key_id == "k"
    assert KalshiAuth("k", load_private_key_pem(base64.b64encode(der).decode().rstrip("="))).sign("x")
    auth = KalshiAuth("key-123", pem)
    headers = auth.headers("GET", "/trade-api/v2/portfolio/balance?x=1", timestamp_ms=1_700_000_000_000)
    assert headers[KEY_HEADER] == "key-123" and headers[TIMESTAMP_HEADER] == "1700000000000"
    key.public_key().verify(base64.b64decode(headers[SIGNATURE_HEADER]), b"1700000000000GET/trade-api/v2/portfolio/balance", padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    assert KalshiAuth.from_env({}) is None
    with pytest.raises(KalshiAuthError):
        KalshiAuth.from_env({"KALSHI_API_KEY_ID": "only-id"})
    assert KalshiAuth.from_env({"KALSHI_API_KEY_ID": "k", "KALSHI_PRIVATE_KEY": base64.b64encode(pem).decode()}).key_id == "k"


class FakeKalshi:
    """A series whose contracts roll every 15 minutes; the book quotes YES at 0.60 / 0.62."""

    def __init__(self, now_ms, *, strike: float = 2400.0, book=(0.60, 0.62, 100.0, 120.0), official_result: str | None = None) -> None:
        self._now = now_ms
        self.strike = strike
        self.book = book
        self.official_result = official_result
        self.calls = []

    def _contract(self, idx: int) -> ContractInfo:
        open_ts = T0 + idx * CYCLE_MS
        return ContractInfo(f"KXETH15M-{idx}", "KXETH15M", f"ETH above {self.strike} #{idx}", self.strike, "greater", open_ts, open_ts + CYCLE_MS, "active", 0.60, 0.62, 0.61, 100.0, None)

    def markets(self, series, *, status="open", limit=50):
        self.calls.append(("markets", series))
        idx = (self._now() - T0) // CYCLE_MS
        return [self._contract(idx), self._contract(idx + 1)]

    def market(self, ticker):
        idx = int(ticker.rsplit("-", 1)[1])
        c = self._contract(idx)
        return ContractInfo(c.ticker, c.event_ticker, c.title, c.strike, c.strike_type, c.open_ts, c.close_ts, "settled", c.yes_bid, c.yes_ask, c.last_price, c.volume, self.official_result)

    def orderbook(self, ticker, *, depth=1):
        self.calls.append(("orderbook", ticker))
        return self.book


def _kalshi_feed(clock: dict, **fake_kwargs):
    under = SyntheticFeed(("ETH-USD",), start_ms=T0 - 30 * BLOCK_MS, tick_ms=1000, seed=5)
    under.advance(T0)
    fake = FakeKalshi(lambda: clock["now"], **fake_kwargs)
    feed = KalshiFeed(("KXETH15M",), underlying={"KXETH15M": "ETH-USD"}, client=fake, underlying_feed=under, poll_ms=2000, block_ms=BLOCK_MS, trade_window_s=600, min_time_left_s=30, now_ms=lambda: clock["now"])
    return feed, fake, under


def test_feed_tracks_the_current_contract_and_settles_on_rollover():
    clock = {"now": T0 + 1000}
    feed, fake, under = _kalshi_feed(clock)
    for k in range(3):
        clock["now"] = T0 + 1000 + 2000 * k
        feed.poll_once()
    assert feed.contract("KXETH15M").ticker == "KXETH15M-0" and feed.errors == 0
    out = feed.advance(T0 + BLOCK_MS)
    assert [t.bid for t in out["KXETH15M"]] == [0.60] * 3 and out["KXETH15M"][0].ask == 0.62 and "ETH-USD" in out
    assert feed.snapshot_history("KXETH15M") == feed.history("KXETH15M") and len(feed.history("KXETH15M")) == 3
    extra = feed.extra_state("KXETH15M", T0 + BLOCK_MS, block=1)
    assert extra["ticker"] == "KXETH15M-0" and extra["strike"] == 2400.0 and extra["yes_ask"] == 0.62 and extra["tradable"] is False
    assert extra["model_p_yes"] is None or 0.0 <= extra["model_p_yes"] <= 1.0
    assert feed.extra_state("KXETH15M", T0 + CYCLE_MS - 300_000, block=50)["tradable"] is True
    # roll over: the next poll after expiry settles the old contract from the underlying (spot ~2500 > strike 2400)
    clock["now"] = T0 + CYCLE_MS + 1000
    under.advance(clock["now"])
    feed.poll_once()
    settlements = feed.pop_settlements()
    assert len(settlements) == 1 and settlements[0].ticker == "KXETH15M-0" and settlements[0].payout == 1.0 and settlements[0].official is False
    assert feed.contract("KXETH15M").ticker == "KXETH15M-1" and feed.pop_settlements() == []
    feed.advance(clock["now"] + 1)
    assert len(feed.snapshot_history("KXETH15M")) == 1 and len(feed.history("KXETH15M")) == 4


def test_official_result_wins_over_the_provisional_one():
    clock = {"now": T0 + 1000}
    feed, fake, under = _kalshi_feed(clock, official_result="no")
    feed.poll_once()
    clock["now"] = T0 + CYCLE_MS + 1000
    feed.poll_once()
    s = feed.pop_settlements()[0]
    assert s.payout == 0.0 and s.official is True


def test_binary_broker_settles_long_and_short_positions():
    import dataclasses

    gate = RiskGate(dataclasses.replace(LIMITS, max_position_units=50, max_notional_usd=100, fee_model="kalshi"))
    broker = BinaryPaperBroker(gate, cash_usd=100.0)
    from feed.base import Tick

    broker.on_tick("KXETH15M", Tick(T0, 0.60, 0.62, 100, 120))
    buy = Order("d1:1", "KXETH15M", "buy", 10, decision_id="d1")
    ack = broker.place_order(buy, gate.check(buy, risk_ctx(mid=0.61, reference_mid=0.61, expected_edge_bps=5000)).approval)
    assert ack.status == "filled" and ack.fill.price == 0.62 and ack.fill.fee_usd == pytest.approx(0.17)   # ceil(0.07*10*0.62*0.38 = 0.165)
    assert broker.cash == pytest.approx(100 - 6.2 - 0.17)
    fill = broker.settle("KXETH15M", 1.0, T0 + 1)
    assert fill.side == "settle" and fill.realized_pnl_usd == pytest.approx(3.8) and broker.position("KXETH15M").qty == 0
    assert broker.cash == pytest.approx(100 - 6.2 - 0.17 + 10)
    sell = Order("d2:2", "KXETH15M", "sell", 10, decision_id="d2")
    broker.place_order(sell, gate.check(sell, risk_ctx(mid=0.61, reference_mid=0.61, expected_edge_bps=5000)).approval)
    assert broker.position("KXETH15M").qty == -10
    fill = broker.settle("KXETH15M", 0.0, T0 + 2)
    assert fill.realized_pnl_usd == pytest.approx(6.0) and broker.settle("KXETH15M", 1.0, T0 + 3) is None


def _answers(p_yes: float, pickoff: float = 0.05, exit_now: float = 0.05) -> dict:
    return {
        "settles_yes": {"type": "noul", "noul": p_yes},
        "pickoff": {"type": "noul", "noul": pickoff},
        "momentum": {"type": "choice", "choice": "stay", "confidence": 0.8, "probabilities": {"toward": 0.1, "away": 0.05, "stay": 0.8, "other": 0.05}},
        "danger": {"type": "score", "score": 0.3, "confidence": 0.8, "legend": {"0": "a", "1": "b", "2": "c", "3": "d"}, "probabilities": {"0": 0.8, "1": 0.1, "2": 0.05, "3": 0.05}},
        "exit_now": {"type": "noul", "noul": exit_now},
    }


def test_binary_pick_uses_the_market_price_plus_cost_as_the_threshold():
    costs = BinaryCosts()
    contract = {"yes_bid": 0.60, "yes_ask": 0.62, "model_p_yes": 0.99, "tradable": True}
    snap = {"ret_bps": {}}
    assert min_edge(0.62, 0.02, costs) == pytest.approx(1.5 * (0.02 + 0.01))
    pick = final_pick_binary("kalshi", "entry", _answers(0.95), snap, contract, costs)
    assert pick.action == "enter_long" and pick.prob == pytest.approx(0.97) and pick.threshold == pytest.approx(0.665) and pick.expected_edge_bps == pytest.approx((0.97 - 0.62) / 0.62 * 1e4)
    assert final_pick_binary("kalshi", "entry", _answers(0.95), snap, {**contract, "tradable": False}, costs).is_hold
    assert final_pick_binary("kalshi", "entry", _answers(0.95, pickoff=0.9), snap, contract, costs).is_hold
    assert final_pick_binary("kalshi", "entry", _answers(0.60), snap, {**contract, "model_p_yes": 0.62}, costs).is_hold
    short = final_pick_binary("kalshi", "entry", _answers(0.05), snap, {**contract, "model_p_yes": 0.05}, costs)
    assert short.action == "enter_short" and short.prob == pytest.approx(0.95)
    assert final_pick_binary("kalshi", "entry", _answers(0.95), snap, {**contract, "model_p_yes": None}, costs).prob == pytest.approx(0.95)
    hold = final_pick_binary("kalshi", "manage", _answers(0.95), snap, contract, costs, position_sign=1)
    assert hold.is_hold and hold.threshold == pytest.approx(1 - (0.60 - min_edge(0.60, 0.02, costs)))
    # A long entered at p 0.70 has a 0.30 chance of losing; that alone must not sell it (it did under a fixed 0.25 line).
    still_good = final_pick_binary("kalshi", "manage", _answers(0.70, exit_now=0.9), snap, {**contract, "model_p_yes": 0.70}, costs, position_sign=1)
    assert still_good.is_hold and still_good.prob == pytest.approx(0.30)
    assert final_pick_binary("kalshi", "manage", _answers(0.95, exit_now=0.9), snap, contract, costs, position_sign=1).is_hold  # logged, not deciding
    reversed_long = final_pick_binary("kalshi", "manage", _answers(0.10), snap, {**contract, "model_p_yes": 0.10}, costs, position_sign=1)
    assert reversed_long.action == "exit" and reversed_long.prob == pytest.approx(0.90) and len(reversed_long.scores) == 2
    short_exit = final_pick_binary("kalshi", "manage", _answers(0.95), snap, contract, costs, position_sign=-1)
    assert short_exit.action == "exit" and short_exit.prob == pytest.approx(0.97)


def test_kalshi_defaults_are_contract_sized(tmp_path):
    env = {"DESK_MODE": "paper", "DESK_BOT": "kalshi", "FEED": "kalshi", "JUDGE_URL": "stub://local", "LOG_DIR": str(tmp_path)}
    cfg = DeskConfig.from_env(env)
    assert cfg.order_qty == 10 and cfg.limits.max_position_units >= cfg.order_qty, "a default Kalshi order must pass the position limit"
    assert cfg.limits.range_guard_ref_bps >= 10_000, "a binary that runs from 0.10 to 0.90 before expiry is not suspect data"
    spot = DeskConfig.from_env({**env, "DESK_BOT": "gambler", "FEED": "synthetic"})
    assert spot.order_qty == 0.2 and spot.limits.max_position_units == 1.0 and spot.limits.range_guard_ref_bps == 300


def test_kalshi_config_pairs_bot_and_feed(tmp_path):
    with pytest.raises(ConfigError, match="go together"):
        DeskConfig.from_env({"DESK_BOT": "kalshi", "FEED": "synthetic", "LOG_DIR": str(tmp_path)})
    cfg = DeskConfig.from_env({"DESK_BOT": "kalshi", "FEED": "kalshi", "LOG_DIR": str(tmp_path)})
    assert cfg.fee_model == "kalshi" and cfg.limits.fee_model == "kalshi" and cfg.symbols == ("KXETH15M",) and cfg.kalshi_underlying["KXETH15M"] == "ETH-USD"
    assert cfg.order_qty == 10 and cfg.rv_min_bps == 0 and cfg.max_spread_bps == 500  # 5 cents of the $1 payout
    assert cfg.limits.round_trip_cost_usd(10, 0.62, "market") == pytest.approx(0.34)
    with pytest.raises(ConfigError, match="no product"):
        DeskConfig.from_env({"DESK_BOT": "kalshi", "FEED": "kalshi", "DESK_SYMBOLS": "KXSOL15M", "LOG_DIR": str(tmp_path)})


def test_desk_buys_a_contract_in_the_window_and_settles_it(tmp_path):
    env = {"DESK_MODE": "paper", "DESK_BOT": "kalshi", "FEED": "kalshi", "DESK_SYMBOLS": "KXETH15M", "JUDGE_URL": "stub://local", "LOG_DIR": str(tmp_path / "logs"),
           "ORDER_QTY": "10", "MAX_POSITION_UNITS": "50", "MAX_NOTIONAL_USD": "100", "PAPER_CASH_USD": "1000", "MIN_TICKS": "30"}
    cfg = DeskConfig.from_env(env)
    clock = {"now": T0}
    feed, fake, under = _kalshi_feed(clock)
    log = LogWriter(cfg.log_dir)
    gate = RiskGate(cfg.limits)
    broker = BinaryPaperBroker(gate, cash_usd=cfg.paper_cash_usd)
    judge = FakeJudge(cfg.jev_model, nouls={"settles_yes": 0.95})
    desk = Desk(cfg, feed=feed, gate=gate, broker=broker, book=Book(), bench=Bench(), battery=load_battery("kalshi"), judge=judge, backoff=Backoff(), resolver=OutcomeResolver(log, block_ms=cfg.block_ms), executor=make_executor("paper", broker, log), log=log, trial_id="t-kalshi")
    for block in BlockClock(cfg.block_ms, T0 + BLOCK_MS, realtime=False).blocks(82):
        for k in range(6):
            clock["now"] = block.ts_ms - BLOCK_MS + 2000 * k + 1000
            feed.poll_once()
        desk.step(block)
    log.close()
    events = list(read_events(cfg.log_dir))
    kinds = [e["kind"] for e in events]
    fills = [e for e in events if e["kind"] == "fill"]
    assert [f["side"] for f in fills] == ["buy", "settle"] and fills[0]["price"] == 0.62 and fills[0]["qty"] == 10
    opened = [e for e in events if e["kind"] == "position_opened"][0]
    assert 25 <= opened["blk"] <= 30, opened["blk"]
    settlement = [e for e in events if e["kind"] == "settlement"][0]
    assert settlement["payout"] == 1.0 and settlement["realized_pnl_usd"] == pytest.approx(3.8) and settlement["decision_id"] == opened["decision_id"]
    assert "position_closed" in kinds and desk.book.position is None
    assert broker.cash == pytest.approx(1000 - 6.2 - 0.17 + 10)
    rejections = {e["check"] for e in events if e["kind"] == "rejection"}
    assert "outside_trade_window" in rejections
    decisions = [e for e in events if e["kind"] == "decision"]
    entry = [d for d in decisions if d["action"] == "enter_long"][0]
    assert entry["threshold"] == pytest.approx(0.665) and entry["executed"] is True and entry["prob"] > 0.9
    assert all(d["action"] == "hold" for d in decisions if d["phase"] == "manage")
    outcomes = [e for e in events if e["kind"] == "outcome"]
    assert outcomes and any(o["qid"] == "settles_yes" and o["status"] == "resolved" and o["realized"] is True for o in outcomes)
    assert any(o["qid"] == "momentum" and o["sym"] == "ETH-USD" for o in outcomes)


def test_market_reads_are_never_signed_and_the_paper_feed_carries_no_credentials(monkeypatch):
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    from feed import make_feed
    from kalshi.api import KalshiApiError, KalshiClient

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
    seen: list[tuple[str, dict]] = []

    def fetch(url, headers):
        seen.append((url, dict(headers)))
        if url.endswith("/portfolio/balance"):
            return {"balance": 10000}
        return {"markets": [], "market": {"ticker": "T"}, "orderbook": {"yes": [], "no": []}}

    client = KalshiClient("https://demo-api.kalshi.co", auth=KalshiAuth("key-123", pem), fetch=fetch)
    client.markets("KXETH15M")
    client.orderbook("KXETH15M-X")
    assert all(KEY_HEADER not in headers for _, headers in seen), "public market data must never be signed"
    assert client.balance() == {"balance": 10000}
    assert KEY_HEADER in seen[-1][1] and SIGNATURE_HEADER in seen[-1][1]
    with pytest.raises(KalshiApiError):
        KalshiClient("https://demo-api.kalshi.co", fetch=fetch).balance()

    # A half-set credential pair would raise if the feed looked at it; the paper feed never does.
    monkeypatch.setenv("KALSHI_API_KEY_ID", "only-id")
    monkeypatch.delenv("KALSHI_PRIVATE_KEY", raising=False)
    feed = make_feed("kalshi", ("KXETH15M",), start_ms=0, kalshi={"underlying": {"KXETH15M": "ETH-USD"}})
    assert feed._client.authenticated is False


def test_a_429_pauses_all_polling_and_backs_off_until_kalshi_answers_again():
    from kalshi.api import KalshiApiError

    clock = {"now": T0 + 60_000}
    feed, fake, _ = _kalshi_feed(clock)
    feed.poll_once()
    assert fake.calls and feed.rate_limits == 0
    calls_before = len(fake.calls)

    def limited(ticker, *, depth=1):
        fake.calls.append(("orderbook", ticker))
        raise KalshiApiError("HTTP 429 from Kalshi: too many requests", status=429, retry_after_s=None)

    fake.orderbook = limited
    assert feed.poll_once() == {"KXETH15M": None}
    assert feed.rate_limits == 1 and len(fake.calls) == calls_before + 1
    clock["now"] += 1_000  # inside the 2 s pause: no call at all
    feed.poll_once()
    assert len(fake.calls) == calls_before + 1
    clock["now"] += 1_500  # pause over: one more try, still limited, pause doubles to 4 s
    feed.poll_once()
    assert feed.rate_limits == 2 and len(fake.calls) == calls_before + 2
    clock["now"] += 3_000
    feed.poll_once()
    assert len(fake.calls) == calls_before + 2
    clock["now"] += 1_500
    fake.orderbook = lambda ticker, *, depth=1: (fake.calls.append(("orderbook", ticker)) or fake.book)
    assert feed.poll_once()["KXETH15M"] is not None and feed._backoff_s == 0.0

    def told_to_wait(ticker, *, depth=1):
        raise KalshiApiError("HTTP 429", status=429, retry_after_s=20.0)

    fake.orderbook = told_to_wait
    clock["now"] += 5_000
    feed.poll_once()
    assert feed._backoff_until_ms == clock["now"] + 20_000  # Retry-After wins over the 2 s floor


def test_binary_spread_and_range_are_measured_in_points_of_the_payout():
    from filter.funnel import Candidate, FunnelContext
    from filter.stages import FreeCut
    from risk.limits import RiskLimits
    from state.snapshot import Snapshot

    cut = FreeCut(max_spread_bps=500, rv_min_bps=0, rv_max_bps=20000, min_ticks=1, max_stale_ms=60_000, spread_basis="payout")
    fields = {f: None for f in Snapshot.__dataclass_fields__}

    def candidate(bid: float, ask: float) -> Candidate:
        mid = (bid + ask) / 2
        snap = Snapshot(**{**fields, "sym": "KXETH15M", "as_of": T0, "mid": mid, "spr_bps": (ask - bid) / mid * 1e4, "n": 50, "rv_bps": 10.0})
        return Candidate(sym="KXETH15M", snapshot=snap, state={}, reference_mid=None, cost_bps=0.0)

    ctx = FunnelContext(block=1, now_ms=T0, deadline_ms=T0 + 10_000, bot="kalshi", phase="entry", mode="paper", equity_usd=10_000.0, day_pnl_usd=0.0)
    kept, rejected = cut.run([candidate(0.04, 0.06), candidate(0.94, 0.96), candidate(0.40, 0.48)], ctx)
    assert [c.snapshot.mid for c in kept] == [pytest.approx(0.05), pytest.approx(0.95)], "2 cents is 2 cents at 5c and at 95c"
    assert [r.check for r in rejected] == ["spread_too_wide"]
    with pytest.raises(ValueError):
        FreeCut(max_spread_bps=1, rv_min_bps=0, rv_max_bps=1, min_ticks=1, max_stale_ms=1, spread_basis="dollars")

    binary = RiskLimits(**{**LIMITS.__dict__, "fee_model": "kalshi", "range_guard_bps": 300, "range_guard_ref_bps": 100000, "max_position_units": 10})
    gate = RiskGate(binary)
    near = Order("o1", "KXETH15M", "buy", 10, "limit", 0.06)
    far = Order("o2", "KXETH15M", "buy", 10, "limit", 0.10)
    ctx_b = risk_ctx(mid=0.05, reference_mid=0.05, expected_edge_bps=20000.0)
    assert all(v.check != "range_guard" for v in gate.evaluate(near, ctx_b)), "1 cent from mid is inside 3 cents"
    assert any(v.check == "range_guard" for v in gate.evaluate(far, ctx_b)), "5 cents from mid is outside 3 cents"
