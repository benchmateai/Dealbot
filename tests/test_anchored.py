"""Desk v2: the market-anchored forecast (policy/anchored.py), its pick and late stop, and the desk running on it."""

from dataclasses import replace

import pytest

from book.bench import Bench
from book.book import Book, OpenPosition
from broker.base import Order
from desk.clock import BlockClock
from desk.config import ConfigError, DeskConfig
from desk.desk import Desk
from desk.modes import make_executor
from judge.client import Backoff
from kalshi import BinaryPaperBroker
from kalshi.api import taker_fee_usd
from logs.writer import LogWriter, read_events
from outcomes.resolver import OutcomeResolver
from policy.anchored import DESK_RULES, LATE_STOP_BELOW, LATE_STOP_S, MODEL_VERSION, TRADE_WINDOW_S, AnchoredForecaster, final_pick_anchored, pool
from policy.binary import BinaryCosts
from questions import load_battery
from risk import RiskGate
from risk.gate import check_fees_plus_gas
from tests.helpers import LIMITS, T0, FakeJudge, risk_ctx
from tests.test_kalshi import BLOCK_MS, _kalshi_feed

COSTS = BinaryCosts(margin=0.5)
CONTRACT = {"ticker": "KXETH15M-0", "expires_in_s": 300, "yes_bid": 0.60, "yes_ask": 0.62, "tradable": True}


def forecast(q, *, w=0.5, bid=0.60, ask=0.62, ticker="KXETH15M-0"):
    return {"ticker": ticker, "tau": 300.0, "bid": bid, "ask": ask, "m": (bid + ask) / 2, "p": q, "w": w, "q": q}


def lab_a_side(q, bid, ask):
    """Lab strategy A's own entry rule, as written in lab/strategies/a_control.py."""
    edge = lambda price, spread: 1.5 * (taker_fee_usd(1, price) + spread / 2)  # noqa: E731
    if q - ask >= edge(ask, ask - bid):
        return "enter_long"
    if (1 - q) - (1 - bid) >= edge(1 - bid, ask - bid):
        return "enter_short"
    return "hold"


@pytest.mark.parametrize("q", [0.05, 0.30, 0.44, 0.45, 0.50, 0.62, 0.66, 0.665, 0.67, 0.80, 0.99])
def test_entry_rule_is_lab_a_rule(q):
    pick = final_pick_anchored("entry", forecast(q), CONTRACT, COSTS)
    assert pick.action == lab_a_side(q, 0.60, 0.62)
    if pick.action == "enter_long":
        assert pick.prob == q and pick.threshold == pytest.approx(0.62 + 1.5 * (0.02 + 0.01))
    if pick.action == "enter_short":
        assert pick.prob == pytest.approx(1 - q) and pick.threshold == pytest.approx(0.40 + 1.5 * (0.02 + 0.01))


def test_entries_only_inside_the_window_with_a_fitted_weight_on_this_contract():
    sure = forecast(0.95)
    for tau, ok in ((TRADE_WINDOW_S[0] - 1, False), (TRADE_WINDOW_S[0], True), (TRADE_WINDOW_S[1], True), (TRADE_WINDOW_S[1] + 1, False)):
        assert final_pick_anchored("entry", sure, {**CONTRACT, "expires_in_s": tau}, COSTS).is_hold is not ok
    assert final_pick_anchored("entry", forecast(0.95, w=0.0), CONTRACT, COSTS).is_hold          # weight 0: q is the market
    assert final_pick_anchored("entry", forecast(0.95, ticker="KXETH15M-1"), CONTRACT, COSTS).is_hold  # another contract's forecast
    assert final_pick_anchored("entry", None, CONTRACT, COSTS).is_hold
    assert final_pick_anchored("entry", sure, {**CONTRACT, "tradable": False}, COSTS).is_hold


def test_late_stop_sells_a_losing_long_shot_in_the_last_minute_and_holds_otherwise():
    long_shot = OpenPosition("KXETH15M", 10.0, 0.32, T0, 1, "d", "kalshi")    # YES bought at 0.32
    short_yes = OpenPosition("KXETH15M", -10.0, 0.60, T0, 1, "d", "kalshi")   # a NO bet bought at 0.40
    favourite = OpenPosition("KXETH15M", 10.0, 0.62, T0, 1, "d", "kalshi")    # YES bought at 0.62
    fav_no = OpenPosition("KXETH15M", -10.0, 0.20, T0, 1, "d", "kalshi")      # a NO bet bought at 0.80

    def pick(position, tau, bid, ask):
        return final_pick_anchored("manage", None, {**CONTRACT, "expires_in_s": tau, "yes_bid": bid, "yes_ask": ask}, COSTS, position=position)

    assert 0.32 < LATE_STOP_BELOW <= 0.62
    assert pick(long_shot, LATE_STOP_S, 0.20, 0.22).action == "exit"         # bid 0.20 < 0.32 paid
    assert pick(long_shot, 12, 0.20, 0.22).action == "exit"
    assert pick(long_shot, LATE_STOP_S + 1, 0.20, 0.22).is_hold              # not yet the last minute
    assert pick(long_shot, 0, 0.20, 0.22).is_hold                            # closed: wait for the settlement
    assert pick(long_shot, 30, 0.95, 0.97).is_hold                           # winning: hold to settlement
    assert pick(short_yes, 30, 0.68, 0.70).action == "exit"                  # NO worth 1 - 0.70 = 0.30 < 0.40
    assert pick(short_yes, 30, 0.48, 0.50).is_hold                           # NO worth 0.50 > 0.40
    # a favourite is held to the close however it stands in its last minute, on either side
    assert pick(favourite, 30, 0.40, 0.42).is_hold and pick(favourite, LATE_STOP_S, 0.10, 0.12).is_hold
    assert pick(fav_no, 30, 0.68, 0.70).is_hold                              # NO worth 0.30 < 0.80 paid, held
    assert final_pick_anchored("manage", None, CONTRACT, COSTS, position=None).is_hold


def _tape(ts, *, ticker="KXETH15M-0", tau=300, spot=2500.0, bid=0.60, ask=0.62, strike=2490.0):
    return {"KXETH15M": {"ticker": ticker, "strike": strike, "strike_type": "greater_or_equal", "expires_in_s": tau, "spot": spot,
                         "underlying_rv_bps": 2.0, "model_p_yes": 0.7, "tradable": True, "yes_bid": bid, "yes_ask": ask, "quote_ts": ts}}


def test_forecaster_records_horizons_resolves_on_settlement_and_refits():
    fc = AnchoredForecaster(min_rows=2, refit_every=1, track_index_gap=False)
    ts = T0
    for tau in range(480, 0, -12):
        out = fc.observe_tape(ts, _tape(ts, tau=tau, spot=2500.0 + (480 - tau) * 0.1))
        ts += 12_000
        assert out["KXETH15M"]["q"] == pytest.approx(out["KXETH15M"]["m"])   # weight 0 until fitted: q is the market
    assert [r["h"] for r in fc.pending_rows["KXETH15M-0"]] == [420, 300, 180, 60]
    assert fc.observe_settlement("KXETH15M-0", 1.0) == 1 and fc.observe_settlement("KXETH15M-0", 0.0) is None  # the first result counts
    assert len(fc.resolved_rows) == 4 and fc.weight != 0.0 and "KXETH15M-0" not in fc.window_spots
    f = fc.observe_tape(ts, _tape(ts, ticker="KXETH15M-1", tau=500))["KXETH15M"]
    assert f["q"] == pytest.approx(pool(f["m"], f["p"], fc.weight)) and f["w"] == fc.weight
    stale = _tape(ts, ticker="KXETH15M-1", tau=490)
    stale["KXETH15M"]["quote_ts"] = ts - 25_000
    assert fc.observe_tape(ts + 12_000, stale) == {} and fc.latest == {}       # a stale quote gives no forecast


def test_a_restarted_desk_forecasts_as_if_it_had_run_throughout(tmp_path):
    log = LogWriter(str(tmp_path))
    live = AnchoredForecaster(min_rows=2, refit_every=1, track_index_gap=False)
    ts = T0
    for n in range(3):
        for tau in range(480, 0, -12):
            rec = _tape(ts, ticker=f"KXETH15M-{n}", tau=tau, spot=2500.0 + n + tau * 0.01)
            log.write("tape", {"blk": ts // 12_000, "contracts": rec}, ts_ms=ts)
            live.observe_tape(ts, rec)
            ts += 12_000
        log.write("settlement", {"sym": "KXETH15M", "ticker": f"KXETH15M-{n}", "payout": float(n % 2)}, ts_ms=ts)
        live.observe_settlement(f"KXETH15M-{n}", float(n % 2))
    log.close()
    warmed = AnchoredForecaster(min_rows=2, refit_every=1, track_index_gap=False)
    assert warmed.warm_from_log(tmp_path) == 3 * 40 + 3
    assert warmed.weight == live.weight and warmed.resolved_rows == live.resolved_rows and warmed.outcomes == live.outcomes
    assert warmed.vols["KXETH15M"].var == live.vols["KXETH15M"].var


def test_config_defaults_to_v2_for_kalshi_and_pins_its_forecaster():
    base = {"DESK_MODE": "paper", "DESK_BOT": "kalshi", "FEED": "kalshi", "JUDGE_URL": "stub://local"}
    cfg = DeskConfig.from_env(base)
    assert cfg.kalshi_forecast == "anchored" and cfg.limits.pinned_model == MODEL_VERSION and cfg.jev_model
    v1 = DeskConfig.from_env({**base, "KALSHI_FORECAST": "blend"})
    assert v1.kalshi_forecast == "blend" and v1.limits.pinned_model == v1.jev_model
    with pytest.raises(ConfigError):
        DeskConfig.from_env({**base, "KALSHI_FORECAST": "jev"})
    with pytest.raises(ConfigError):
        DeskConfig.from_env({"DESK_MODE": "paper", "JUDGE_URL": "stub://local", "KALSHI_FORECAST": "anchored"})
    assert DeskConfig.from_env({"DESK_MODE": "paper", "JUDGE_URL": "stub://local"}).kalshi_forecast == "blend"


def test_trial_spec_marks_v2_and_leaves_the_first_desk_spec_unchanged():
    from questions import load_battery as lb
    from trials.fingerprint import strategy_spec

    base = {"DESK_MODE": "paper", "DESK_BOT": "kalshi", "FEED": "kalshi", "JUDGE_URL": "stub://local"}
    v2 = strategy_spec(DeskConfig.from_env(base), lb("kalshi"))["kalshi"]
    v1 = strategy_spec(DeskConfig.from_env({**base, "KALSHI_FORECAST": "blend"}), lb("kalshi"))["kalshi"]
    assert v2["forecast"] == "anchored" and v2["late_stop_s"] == LATE_STOP_S and v2["entry_window_s"] == list(TRADE_WINDOW_S)
    assert v2["rules"] == DESK_RULES == "v3" and v2["late_stop_below"] == LATE_STOP_BELOW and TRADE_WINDOW_S == (180, 600)
    assert "forecast" not in v1 and set(v1) == {"base_url", "underlying", "trade_window_s", "min_time_left_s", "taker_rate", "maker_rate", "model_weight"}


def test_the_fee_check_measures_a_no_bet_on_the_no_price():
    lim = replace(LIMITS, fee_model="kalshi", max_position_units=10.0)
    sell = Order("o", "KXETH15M", "sell", 10.0, "market", None, False, "d")   # short YES at 0.97 = NO at 0.03
    fee = taker_fee_usd(10, 0.03)
    # NO worth 0.05 bought at 0.03: 2 cents a contract, $0.20, against 1.5 x two fees
    edge_bps = (0.05 - 0.03) / 0.03 * 1e4
    assert check_fees_plus_gas(sell, risk_ctx(mid=0.97, expected_edge_bps=edge_bps), lim) is None and 0.20 >= 1.5 * 2 * fee
    # NO worth 0.035: half a cent a contract, $0.05; on the YES price it read as $1.62 and passed
    thin = (0.035 - 0.03) / 0.03 * 1e4
    veto = check_fees_plus_gas(sell, risk_ctx(mid=0.97, expected_edge_bps=thin), lim)
    assert veto is not None and veto.value == pytest.approx(0.05, abs=0.001)
    buy = Order("b", "KXETH15M", "buy", 10.0, "market", None, False, "d")
    assert check_fees_plus_gas(buy, risk_ctx(mid=0.03, expected_edge_bps=thin), lim) is not None   # YES side unchanged


def _v2_desk(tmp_path, clock, forecaster):
    env = {"DESK_MODE": "paper", "DESK_BOT": "kalshi", "FEED": "kalshi", "DESK_SYMBOLS": "KXETH15M", "JUDGE_URL": "stub://local", "LOG_DIR": str(tmp_path / "logs"),
           "ORDER_QTY": "10", "MAX_POSITION_UNITS": "50", "MAX_NOTIONAL_USD": "100", "PAPER_CASH_USD": "1000", "MIN_TICKS": "30"}
    cfg = DeskConfig.from_env(env)
    feed, fake, under = _kalshi_feed(clock)
    log = LogWriter(cfg.log_dir)
    gate = RiskGate(cfg.limits)
    broker = BinaryPaperBroker(gate, cash_usd=cfg.paper_cash_usd)
    judge = FakeJudge(cfg.jev_model)
    desk = Desk(cfg, feed=feed, gate=gate, broker=broker, book=Book(), bench=Bench(), battery=load_battery("kalshi"), judge=judge, backoff=Backoff(),
                resolver=OutcomeResolver(log, block_ms=cfg.block_ms), executor=make_executor("paper", broker, log), log=log, trial_id="t-v2", forecaster=forecaster)
    return cfg, desk, feed, fake, log, judge


def _run(cfg, desk, feed, fake, log, clock, blocks, *, book_after=None):
    for block in BlockClock(cfg.block_ms, T0 + BLOCK_MS, realtime=False).blocks(blocks):
        if book_after and block.ts_ms >= book_after[0]:
            fake.book = book_after[1]
        for k in range(6):
            clock["now"] = block.ts_ms - BLOCK_MS + 2000 * k + 1000
            feed.poll_once()
        desk.step(block)
    log.close()
    return list(read_events(cfg.log_dir))


def test_v2_desk_enters_on_the_forecast_and_late_stops_a_losing_long_shot_without_asking_jev(tmp_path):
    clock = {"now": T0}
    fc = AnchoredForecaster(fixed_weight=1.0, track_index_gap=False)   # q = the model: spot ~2500 against a 2400 strike, YES ~1
    cfg, desk, feed, fake, log, judge = _v2_desk(tmp_path, clock, fc)
    fake.official_result = "yes"
    fake.book = (0.30, 0.32, 100.0, 120.0)                             # YES at 32 cents: a long shot
    events = _run(cfg, desk, feed, fake, log, clock, 82, book_after=(T0 + 900_000 - LATE_STOP_S * 1000, (0.20, 0.22, 100.0, 120.0)))
    assert judge.calls == [] and not [e for e in events if e["kind"] == "answer"]
    entry = [e for e in events if e["kind"] == "decision" and e["action"] == "enter_long"][0]
    assert entry["executed"] and entry["model"] == MODEL_VERSION and entry["prob"] > 0.9
    opened = [e for e in events if e["kind"] == "position_opened"][0]
    assert 25 <= opened["blk"] <= 30, opened["blk"]          # the first block with 600 s or less to the close
    fills = [e for e in events if e["kind"] == "fill"]
    assert [f["side"] for f in fills] == ["buy", "sell"] and fills[0]["price"] == 0.32 and fills[1]["price"] == pytest.approx(0.20, abs=0.001)
    exit_ = [e for e in events if e["kind"] == "decision" and e["action"] == "exit"][0]
    assert exit_["executed"] and exit_["phase"] == "manage" and exit_["prob"] == pytest.approx(0.20) and exit_["threshold"] == pytest.approx(0.32)
    held = [e for e in events if e["kind"] == "decision" and e["phase"] == "manage" and e["action"] == "hold"]
    assert held and all(e["ts"] < exit_["ts"] for e in held)  # held, not churned, until the last minute
    assert desk.book.position is None and fc.outcomes == {"KXETH15M-0": 1}
    forecasts = [e for e in events if e["kind"] == "forecast"]
    assert forecasts and {f["model"] for f in forecasts} == {MODEL_VERSION} and all(f["weight"] == 1.0 for f in forecasts)


def test_v3_desk_holds_a_losing_favourite_through_its_last_minute_to_settlement(tmp_path):
    clock = {"now": T0}
    fc = AnchoredForecaster(fixed_weight=1.0, track_index_gap=False)
    cfg, desk, feed, fake, log, judge = _v2_desk(tmp_path, clock, fc)
    fake.official_result = "yes"                                       # YES bought at 62 cents, behind in its last minute, then wins
    events = _run(cfg, desk, feed, fake, log, clock, 82, book_after=(T0 + 900_000 - LATE_STOP_S * 1000, (0.40, 0.42, 100.0, 120.0)))
    fills = [e for e in events if e["kind"] == "fill"]
    assert [f["side"] for f in fills] == ["buy", "settle"] and fills[0]["price"] == 0.62 and fills[1]["price"] == 1.0
    assert not [e for e in events if e["kind"] == "decision" and e["action"] == "exit"]
    assert desk.book.position is None and judge.calls == []


def test_v2_desk_holds_a_winner_to_settlement(tmp_path):
    clock = {"now": T0}
    fc = AnchoredForecaster(fixed_weight=1.0, track_index_gap=False)
    cfg, desk, feed, fake, log, judge = _v2_desk(tmp_path, clock, fc)
    fake.official_result = "yes"
    events = _run(cfg, desk, feed, fake, log, clock, 82, book_after=(T0 + 700_000, (0.95, 0.97, 100.0, 120.0)))
    fills = [e for e in events if e["kind"] == "fill"]
    assert [f["side"] for f in fills] == ["buy", "settle"] and fills[1]["price"] == 1.0
    assert not [e for e in events if e["kind"] == "decision" and e["action"] == "exit"]
    assert desk.book.position is None and judge.calls == []


def test_v2_desk_waits_while_the_forecaster_has_no_fitted_weight(tmp_path):
    clock = {"now": T0}
    fc = AnchoredForecaster(track_index_gap=False)   # nothing resolved yet: weight 0
    cfg, desk, feed, fake, log, judge = _v2_desk(tmp_path, clock, fc)
    events = _run(cfg, desk, feed, fake, log, clock, 60)
    assert not [e for e in events if e["kind"] == "position_opened"]
    assert {e["check"] for e in events if e["kind"] == "rejection" and e["stage"] == "forecast"} == {"forecast_warming_up"}


def test_an_anchored_desk_must_be_given_its_forecaster(tmp_path):
    clock = {"now": T0}
    with pytest.raises(ValueError):
        _v2_desk(tmp_path, clock, None)


def test_health_counts_v2_forecasts_as_the_desk_thinking(tmp_path):
    from reports.health import check

    log = LogWriter(str(tmp_path))
    end = T0 + 3 * 3_600_000
    for k in range(0, 3 * 3600, 60):
        ts = T0 + k * 1000
        log.write("heartbeat", {"blk": k, "equity_usd": 10_000.0, "day_pnl_usd": 0.0}, ts_ms=ts)
        if ts < end - 2 * 3_600_000 - 60_000 or ts > end - 30 * 60_000:
            log.write("forecast", {"decision_id": f"d{k}", "sym": "KXETH15M", "model": MODEL_VERSION, "weight": 0.5}, ts_ms=ts)
    log.close()
    r = check(tmp_path, commit_ms=end, now_ms=end)   # the last heartbeat is a minute before `end`: 29 forecasts in its hour
    assert r["status"] == "OK" and r["stats"]["brain_calls_1h"] == 29 and "last hour: 29 forecasts" in r["line"], r["line"]


def test_health_alerts_when_v2_stops_forecasting(tmp_path):
    from reports.health import check

    log = LogWriter(str(tmp_path))
    end = T0 + 3 * 3_600_000
    for k in range(0, 3 * 3600, 60):
        ts = T0 + k * 1000
        log.write("heartbeat", {"blk": k, "equity_usd": 10_000.0, "day_pnl_usd": 0.0}, ts_ms=ts)
        if ts < T0 + 3_600_000:
            log.write("forecast", {"decision_id": f"d{k}", "sym": "KXETH15M", "model": MODEL_VERSION, "weight": 0.5}, ts_ms=ts)
    log.close()
    r = check(tmp_path, commit_ms=end, now_ms=end)
    assert r["status"] == "ALERT" and r["alerts"] == ["no forecasts in two hours"], r["line"]
