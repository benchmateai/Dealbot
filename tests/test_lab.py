import json
import math

from kalshi.api import taker_fee_usd

from lab.model import EwmaVol, fit_weight, log_average_dist, p_contract, pool
from lab.recorder import Recorder, compact
from lab.rest import Budget, LabRest
from lab.store import LabStore, read_lab
from lab.strategies import a_control, d_scanner

H = 3_600_000
T0 = 1_793_736_000_000  # 2026-11-03T20:00:00Z


def test_store_seals_each_finished_hour_and_reads_back_in_order(tmp_path):
    store = LabStore(tmp_path)
    store.write("x", {"n": 1}, ts_ms=T0 + 1)
    store.write("x", {"n": 2}, ts_ms=T0 + H + 1)  # a new hour seals the old one, in a thread
    store.wait_sealed()
    assert (tmp_path / "2026-11-03" / "20.jsonl.gz").exists() and (tmp_path / "2026-11-03" / "21.jsonl").exists()
    store.close()
    store = LabStore(tmp_path)  # a restart inside hour 21 appends, then sealing adds a second gzip member
    store.write("x", {"n": 3}, ts_ms=T0 + H + 2)
    store.close()
    store.seal_closed_hours()
    store2 = LabStore(tmp_path)
    store2.write("x", {"n": 4}, ts_ms=T0 + H + 3)
    store2.close()
    store2.seal_closed_hours()
    assert [r["n"] for r in read_lab(tmp_path)] == [1, 2, 3, 4]
    assert [r["n"] for r in read_lab(tmp_path, since_ms=T0 + H)] == [2, 3, 4]


def test_budget_pauses_every_request_after_a_rate_limit():
    clock = {"t": 0.0}
    slept = []
    b = Budget(1.0, 1.0, clock=lambda: clock["t"], sleep=lambda s: (slept.append(s), clock.__setitem__("t", clock["t"] + s)))
    b.take()
    b.take()  # second token needs a second
    b.pause(30)
    b.take()
    assert round(sum(slept), 6) >= 31


class FakeKalshi:
    def __init__(self, now):
        self.now, self.calls = now, []

    def get(self, path, params=None):
        self.calls.append(params)
        p = params or {}
        if "series_ticker" in p:
            s = p["series_ticker"]
            return {"markets": [{"ticker": f"{s}-E1-T1", "event_ticker": f"{s}-E1", "close_time": "2026-11-03T21:00:00Z"}]}
        ev = p["event_ticker"]
        settled = self.now["ms"] > T0 + H + 130_000
        return {"markets": [{"ticker": f"{ev}-T1", "strike_type": "greater", "floor_strike": "77000", "yes_bid_dollars": "0.50", "yes_ask_dollars": "0.52",
                             "yes_bid_size_fp": "10.00", "yes_ask_size_fp": "20.00", "result": "yes" if settled else "", "expiration_value": "77100.5" if settled else None}]}


def test_recorder_snapshots_events_and_records_settlements(tmp_path):
    now = {"ms": T0 + 50 * 60_000}
    api = FakeKalshi(now)
    rec = Recorder(LabRest(api, Budget(1e9, 1e9)), LabStore(tmp_path), now_ms=lambda: now["ms"])
    rec.discover(now["ms"])
    rec.snapshot(now["ms"])
    now["ms"] = T0 + H + 200_000
    rec.settle(now["ms"])
    rec.store.close()
    kinds = [r["kind"] for r in read_lab(tmp_path)]
    assert kinds.count("book_top") == 6 and kinds.count("settled") == 6
    top = next(r for r in read_lab(tmp_path) if r["kind"] == "book_top")
    assert top["rows"][0][2:] == [77000.0, None, 0.5, 0.52, 10.0, 20.0]
    settled = next(r for r in read_lab(tmp_path) if r["kind"] == "settled")
    assert settled["rows"][0][1:] == ["yes", 77100.5]
    assert not any((c or {}).get("method") for c in api.calls)  # GET only, nothing else exists


def test_model_prices_the_sixty_second_average_not_the_spot():
    s2 = (1e-4) ** 2
    assert abs(log_average_dist(77500.0, 300, s2)[1] - math.sqrt(260) * 1e-4) < 1e-12
    # most of the average is in, comfortably above the strike: YES although spot is below the strike
    p = p_contract("greater_or_equal", 77510.0, None, 77505.0, 15, s2, observed_log_mean=math.log(77520.0))
    assert p > 0.9
    legs = [p_contract("less", None, 77000, 77500, 300, s2), p_contract("greater", 78000, None, 77500, 300, s2)]
    legs += [p_contract("between", 77000 + 100 * i, 77100 + 100 * i, 77500, 300, s2) for i in range(10)]
    assert abs(sum(legs) - 1) < 1e-9
    assert pool(0.7, 0.9, 0.0) == 0.7 and abs(pool(0.7, 0.9, 1.0) - 0.9) < 1e-9
    v = EwmaVol(half_life_s=60, floor_bps_per_sqrt_s=0.3)
    for i in range(200):
        v.update(i * 12_000, 100.0)
    assert abs(v.s2_per_s - (0.3e-4) ** 2) < 1e-15  # a flat price cannot make the model certain


def test_fit_weight_prefers_the_market_when_the_model_adds_nothing():
    rows = [(0.8, 0.5, 1)] * 80 + [(0.8, 0.5, 0)] * 20 + [(0.2, 0.5, 0)] * 80 + [(0.2, 0.5, 1)] * 20
    w, _ = fit_weight(rows)
    assert abs(w) < 0.05


def _row(ticker, stype, floor, cap, bid, ask, bsz=100.0, asz=100.0):
    return [ticker, stype, floor, cap, bid, ask, bsz, asz]


def test_scanner_finds_ladder_range_and_pair_locks_after_fees(tmp_path):
    store = LabStore(tmp_path)
    close = T0 + H
    ladder = [_row("H-T100", "greater", 100, None, 0.60, 0.62), _row("H-T110", "greater", 110, None, 0.70, 0.72)]  # higher strike bid 0.70 > lower ask 0.62
    store.write("book_top", {"series": "KXBTC15M", "type": "15m", "event": "M", "close_ms": close, "rows": [_row("M-1", "greater_or_equal", 105, None, 0.80, 0.82)]}, ts_ms=T0 + 50 * 60_000)
    store.write("book_top", {"series": "KXBTCD", "type": "ladder", "event": "H", "close_ms": close, "rows": ladder}, ts_ms=T0 + 50 * 60_000 + 2_000)
    brackets = [_row("R-L", "less", None, 100, 0.30, 0.32), _row("R-B", "between", 100, 109.99, 0.40, 0.42), _row("R-G", "greater", 110, None, 0.40, 0.42)]
    store.write("book_top", {"series": "KXBTC", "type": "range", "event": "R", "close_ms": close, "rows": brackets}, ts_ms=T0 + 50 * 60_000 + 3_000)
    store.close()
    report = d_scanner.scan(tmp_path)
    kinds = {r["kind"]: r for r in report["runs"]}
    fees = (taker_fee_usd(100, 0.62) + taker_fee_usd(100, 1 - 0.70)) / 100  # both legs, rounded up per order
    assert kinds["ladder"]["legs"] == ["YES H-T100", "NO H-T110"] and abs(kinds["ladder"]["best_net_100"] - round(0.08 - fees, 4)) < 1e-9
    assert kinds["range_no"]["best_net_100"] > 0  # bids sum to 1.10
    assert "pair_below" in kinds  # 15-minute YES bid 0.80 over the hourly above-100 ask 0.62, with 100 below its 105 strike
    assert report["summary"]["snapshots"]["pair_checks"] == 1


def test_control_holds_its_weight_at_zero_and_scores_against_the_market(tmp_path):
    lines = []
    for k in range(5):
        close = T0 + (k + 1) * 900_000
        for b in range(75):
            ts = close - 900_000 + b * 12_000
            tau = (close - ts) / 1000
            lines.append({"kind": "tape", "ts": ts, "blk": b, "contracts": {"KXETH15M": {
                "ticker": f"ETH-{k}", "strike": 2000.0, "strike_type": "greater_or_equal", "expires_in_s": tau, "spot": 2001.0,
                "yes_bid": 0.55, "yes_ask": 0.57, "quote_ts": ts - 1000, "model_p_yes": 0.5, "underlying_rv_bps": 2.0, "tradable": True}}})
        lines.append({"kind": "settlement", "ts": close + 10_000, "ticker": f"ETH-{k}", "payout": 1.0, "official": True, "sym": "KXETH15M"})
    (tmp_path / "events-2026-11-03.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    report = a_control.evaluate(tmp_path, None, registered_ms=0)
    s = report["summary"]
    assert s["resolved_forecasts"] == 20 and s["weight"] == 0.0 and not s["weight_active"] and s["trades"] == 0
    assert set(s["scores"]) == {"420", "300", "180", "60"} and s["scores"]["60"]["n"] == 5


def _book(ts, ticker, series, close_ms, yes, no, strike=None, **extra):
    return ("book", {"ticker": ticker, "series": series, "close_ms": close_ms, "strike": strike, "strike_type": "greater_or_equal", "yes": yes, "no": no, **extra}, ts)


def _write(tmp_path, items):
    store = LabStore(tmp_path)
    for kind, rec, ts in sorted(items, key=lambda x: x[2]):
        store.write(kind, rec, ts_ms=ts)
    store.close()


def test_b_buys_the_side_the_fixed_average_has_decided_and_scores_the_upset(tmp_path):
    from lab.strategies import b_late

    close = T0 + 900_000
    items = []
    for i in range(400):  # a steady index well above the strike, one print a second
        items.append(("index", {"symbol": "BRTI", "value": 77600.0 + (i % 3)}, close - 400_000 + i * 1000))
    # 30 seconds out, the market still offers YES at 90 cents although the average is nearly fixed above
    items.append(_book(close - 30_000, "BTC-A", "KXBTC15M", close, yes=[[0.88, 50.0]], no=[[0.10, 40.0]], strike=77500.0))
    items.append(("settled", {"series": "KXBTC15M", "event": "E", "rows": [["BTC-A", "yes", 77601.0]]}, close + 60_000))
    _write(tmp_path, items)
    rep = b_late.evaluate(tmp_path, registered_ms=0)
    t = rep["trades"][0]
    assert (t["side"], t["price"], t["qty"], t["won"]) == ("YES", 0.9, 40.0, True)
    assert rep["summary"]["pnl_usd"] == round(40 * 0.1 - taker_fee_usd(40, 0.9), 2)


def test_c_quotes_both_sides_fills_only_from_trades_and_respects_its_cap(tmp_path):
    from lab.strategies import c_crypto_mm

    close = T0 + 900_000
    items = [
        _book(T0 + 1000, "ETH-A", "KXETH15M", close, yes=[[0.50, 100.0]], no=[[0.48, 100.0]]),
        ("trade", {"ticker": "ETH-A", "yes_price": 0.50, "count": 130, "taker_side": "no", "trade_ts": T0 + 2000}, T0 + 2000),  # 100 ahead of our YES bid, then us
        ("trade", {"ticker": "ETH-A", "yes_price": 0.53, "count": 5, "taker_side": "yes", "trade_ts": T0 + 3000}, T0 + 3000),   # through our NO bid (YES offer at 52)
        ("settled", {"series": "KXETH15M", "event": "E", "rows": [["ETH-A", "yes", 1.0]]}, close + 60_000),
    ]
    _write(tmp_path, items)
    s = c_crypto_mm.evaluate(tmp_path, registered_ms=0)["summary"]
    assert s["contracts_filled"] == 15  # 10 on the YES bid (after the queue of 100), 5 on the NO bid
    assert s["pnl_usd_upper_bound"] == round(10 * (1.0 - 0.50) + 5 * (0.0 - 0.48), 2)


def test_f_rests_no_bids_only_on_long_shots_and_caps_each_event(tmp_path):
    from lab.strategies import f_fade

    items = []
    for k in range(5):  # five long-shot strikes on one event: the cap of 30 allows three orders of 10
        items.append(_book(T0 + k, f"EV-{k}", "KXSHOW", None, yes=[[0.02, 50.0]], no=[[0.95, 20.0]], set="F", event="EV"))
    items.append(_book(T0 + 10, "FAV", "KXSHOW", None, yes=[[0.60, 50.0]], no=[[0.38, 20.0]], set="F", event="OTHER"))  # not a long shot
    items.append(("trade", {"ticker": "EV-0", "yes_price": 0.06, "count": 12, "taker_side": "yes", "trade_ts": T0 + 100}, T0 + 100))  # through our 5-cent offer
    items.append(("settled", {"series": "KXSHOW", "event": "EV", "rows": [["EV-0", "no", None]]}, T0 + 200))
    _write(tmp_path, items)
    s = f_fade.evaluate(tmp_path, registered_ms=0)["summary"]
    assert s["markets"] == 3 and s["contracts_filled"] == 10 and s["filled_by_trade_through"] == 10
    assert s["pnl_usd_upper_bound"] == round(10 * (1.0 - 0.95), 2) and s["upset_contracts"] == 0


def test_e_side_share_follows_the_documented_scoring():
    from lab.strategies.e_incentive import reference_price, side_share

    deep = [[0.55, 10.0], [0.50, 300.0], [0.49, 900.0]]
    assert reference_price(deep, 200) == 0.50  # a small order alone at the top does not set it
    # ours (100 at 0.50) joins behind the 300 there; the 0.55 order counts in full, the whole 0.49 level at half
    assert abs(side_share(deep, 1000, 0.5, (0.50, 100.0)) - 100 / (10 + 300 + 100 + 450)) < 1e-12
    assert side_share(deep, 1000, 0.5, None) == 0.0
    assert side_share([[0.48, 50.0]], 1000, 0.5, (0.48, 100.0)) is None  # short of the Target Size even with ours


def _program(ticker, per_side_per_s, target="1000.00", pid=None):
    day = 86_400  # 2026-11-03T00:00Z to 2026-11-04T00:00Z
    return {"id": pid or ticker, "market_ticker": ticker, "incentive_type": "liquidity", "target_size_fp": target, "discount_factor_bps": 5000,
            "period_reward": round(per_side_per_s * 2 * day * 10_000), "start_date": "2026-11-03T00:00:00Z", "end_date": "2026-11-04T00:00:00Z"}


def test_e_pays_each_book_until_the_next_one_and_only_programs_worth_a_dollar(tmp_path):
    from lab.strategies import e_incentive

    deep = [[0.50, 300.0], [0.49, 900.0]]
    items = [("incentives", {"programs": [_program("M", 0.5), _program("SMALL", 0.01)]}, T0)]
    for k in range(5):
        thin = k == 3
        items.append(_book(T0 + 1000 + k * 10_000, "M", None, None, yes=deep, no=[[0.48, 50.0]] if thin else deep, set="E"))
    for k in range(4):
        items.append(_book(T0 + 1000 + k * 10_000, "SMALL", None, None, yes=deep, no=deep, set="E"))
    _write(tmp_path, items)
    report = e_incentive.evaluate(tmp_path, registered_ms=0)
    s, share = report["summary"], 100 / 850
    # M: three 10-second intervals after deep books pay 0.5 a second a side times our share; the interval after
    # the thin book pays nothing, and the last book has no interval after it. SMALL earns 7 cents: not paid.
    assert abs(report["by_program"]["M"] - 3 * 10 * 0.5 * 2 * share) < 1e-3
    assert abs(report["by_program"]["SMALL"] - 3 * 10 * 0.01 * 2 * share) < 1e-3
    assert (s["samples"], s["paying_samples"]) == (9, 8)
    assert s["payable_usd"] == math.floor(3 * 10 * 0.5 * 2 * share * 100) / 100
    assert s["contracts_filled"] == 0 and s["net_usd_upper_bound"] == s["payable_usd"]


def test_e_charges_fills_their_markout_and_stops_adding_past_its_cap(tmp_path):
    from lab.strategies import e_incentive

    yes, no = [[0.50, 100.0]], [[0.45, 100.0]]
    items = [("incentives", {"programs": [_program("M", 0.5, target="100.00")]}, T0)]
    for k in range(4):
        items.append(_book(T0 + 1000 + k * 2000, "M", None, None, yes=yes, no=no, set="E"))
        items.append(("trade", {"ticker": "M", "yes_price": 0.49, "count": 50.0, "taker_side": "no"}, T0 + 2000 + k * 2000))  # through our YES bid
    items.append(_book(T0 + 301_000, "M", None, None, yes=[[0.40, 100.0]], no=[[0.55, 100.0]], set="E"))  # YES mid 0.425 five minutes on
    items.append(_book(T0 + 400_000, "M", None, None, yes=[[0.40, 100.0]], no=[[0.55, 100.0]], set="E"))  # unchanged, rewritten
    _write(tmp_path, items)
    s = e_incentive.evaluate(tmp_path, registered_ms=0)["summary"]
    # 10 contracts a quote (a tenth of the target), refilled after each fill until the net position reaches 30
    assert s["contracts_filled"] == 30
    assert abs(s["markout_usd"] - 30 * (0.425 - 0.50)) < 1e-9


def test_ws_feed_keeps_books_detects_gaps_and_writes_normalized_records(tmp_path):
    from lab.ws_recorder import Feed

    store = LabStore(tmp_path)
    feed = Feed(store, LabRest(FakeKalshi({"ms": T0}), Budget(1e9, 1e9)), now_ms=lambda: T0 + 5_000)
    feed.watch("ETH-1", {"series": "KXETH15M", "event": "E", "close_ms": T0 + 900_000, "strike": 2000.0, "strike_type": "greater_or_equal", "set": "15m"})
    feed.handle({"type": "subscribed", "msg": {"channel": "orderbook_delta", "sid": 2}})
    feed.handle({"type": "orderbook_snapshot", "sid": 2, "seq": 1, "msg": {"market_ticker": "ETH-1", "yes_dollars_fp": [["0.5000", "100.00"], ["0.4900", "50.00"]], "no_dollars_fp": [["0.4800", "70.00"]]}})
    feed.handle({"type": "orderbook_delta", "sid": 2, "seq": 2, "msg": {"market_ticker": "ETH-1", "price_dollars": "0.5000", "delta_fp": "-100.00", "side": "yes"}})
    feed.handle({"type": "orderbook_delta", "sid": 2, "seq": 3, "msg": {"market_ticker": "ETH-1", "price_dollars": "0.5100", "delta_fp": "20.00", "side": "yes"}})
    assert feed.books["ETH-1"].normalized()["yes"] == [[0.51, 20.0], [0.49, 50.0]]
    feed.handle({"type": "orderbook_delta", "sid": 2, "seq": 9, "msg": {"market_ticker": "ETH-1", "price_dollars": "0.5100", "delta_fp": "5.00", "side": "yes"}})
    assert feed.counters["gaps"] == 1 and not feed.books["ETH-1"].ready
    assert feed.outbox[-1]["params"]["action"] == "get_snapshot" and feed.outbox[-1]["params"]["market_tickers"] == ["ETH-1"]
    feed.handle({"type": "orderbook_snapshot", "sid": 2, "seq": 10, "msg": {"market_ticker": "ETH-1", "yes_dollars_fp": [["0.5200", "10.00"]], "no_dollars_fp": [["0.4700", "10.00"]]}})
    feed.handle({"type": "trade", "sid": 3, "seq": 1, "msg": {"market_ticker": "ETH-1", "yes_price_dollars": "0.5200", "count_fp": "3.00", "taker_outcome_side": "no", "ts_ms": T0 + 4_000}})
    feed.handle({"type": "cfbenchmarks_value", "sid": 1, "seq": 1, "msg": {"index_id": "ETHUSD_RTI", "data": json.dumps({"value": "2001.5"}), "avg_60s_data": {"value": "2001.40000000"}}})
    feed.write_books(T0 + 5_000)
    feed.flush_trades(T0 + 5_000)
    store.close()
    recs = list(read_lab(tmp_path))
    book = next(r for r in recs if r["kind"] == "book")
    assert book["yes"] == [[0.52, 10.0]] and book["no"] == [[0.47, 10.0]] and book["set"] == "15m" and book["strike"] == 2000.0
    trade = next(r for r in recs if r["kind"] == "trade")
    assert (trade["yes_price"], trade["count"], trade["taker_side"], trade["trade_ts"]) == (0.52, 3.0, "no", T0 + 4_000)
    index = next(r for r in recs if r["kind"] == "index")
    assert (index["symbol"], index["value"], index["avg60"]) == ("ETHUSD_RTI", 2001.5, 2001.4)
    assert not [c for c in feed.outbox if c["cmd"] not in ("subscribe", "update_subscription", "unsubscribe")]  # market data commands only


def test_ws_feed_subscribes_once_tops_up_on_confirmation_and_finds_a_refused_market_one_at_a_time(tmp_path):
    from lab.ws_recorder import Feed

    clock = {"ms": T0}
    feed = Feed(LabStore(tmp_path, stream="ws"), LabRest(FakeKalshi({"ms": T0}), Budget(1e9, 1e9)), now_ms=lambda: clock["ms"])
    meta = {"series": "KXETH15M", "event": "E", "close_ms": T0 + 900_000, "strike": 1.0, "strike_type": "greater_or_equal", "set": "15m"}
    feed.watch("A", meta)
    feed.watch("B", meta)
    cmds = feed.connected()
    assert [c["params"]["channels"] for c in cmds] == [["cfbenchmarks_value"], ["orderbook_delta"], ["trade"]]
    book_sub, trade_sub = cmds[1], cmds[2]
    assert book_sub["params"]["use_yes_price"] is False and book_sub["params"]["market_tickers"] == ["A", "B"]
    feed.watch("C", meta)  # before Kalshi confirms: no second subscribe
    assert not [c for c in feed.outbox if c["cmd"] == "subscribe"]
    feed.handle({"id": book_sub["id"], "type": "subscribed", "msg": {"channel": "orderbook_delta", "sid": 7}})
    assert feed.outbox[-1]["params"] == {"sids": [7], "market_tickers": ["C"], "action": "add_markets"}
    # the trade subscribe naming A and B is refused: no reconnect; the next try leads with one market
    feed.handle({"id": trade_sub["id"], "type": "error", "msg": {"code": 11, "msg": "bad market"}})
    feed.outbox.clear()
    clock["ms"] += 5_000
    feed.tick(clock["ms"])
    retry = [c for c in feed.outbox if c["cmd"] == "subscribe"]
    assert len(retry) == 1 and retry[0]["params"]["market_tickers"] == ["A"]
    feed.outbox.clear()
    feed.handle({"id": retry[0]["id"], "type": "subscribed", "msg": {"channel": "trade", "sid": 8}})
    assert [c["params"]["market_tickers"] for c in feed.outbox] == [["B"], ["C"]]  # the rest one at a time
    b_add = feed.outbox[0]
    feed.handle({"id": b_add["id"], "type": "error", "msg": {"code": 11, "msg": "no such market"}})
    assert "B" in feed.meta and feed.outbox[-1]["params"]["market_tickers"] == ["B"]  # refused once: tried once more
    feed.handle({"id": feed.outbox[-1]["id"], "type": "error", "msg": {"code": 11, "msg": "no such market"}})
    assert "B" not in feed.meta and feed.counters["markets_dropped"] == 1  # refused twice: dropped, and only B
    feed.handle({"type": "orderbook_snapshot", "sid": 7, "seq": 1, "msg": {"market_ticker": "A", "yes_dollars_fp": [], "no_dollars_fp": []}})
    feed.handle({"type": "ok", "id": 50, "sid": 7, "seq": 2, "msg": {"market_tickers": ["A", "B"]}})  # a reply that may or may not take a number
    feed.handle({"type": "orderbook_delta", "sid": 7, "seq": 2, "msg": {"market_ticker": "A", "price_dollars": "0.5000", "delta_fp": "1.00", "side": "yes"}})
    feed.handle({"type": "orderbook_delta", "sid": 7, "seq": 3, "msg": {"market_ticker": "A", "price_dollars": "0.5000", "delta_fp": "1.00", "side": "yes"}})
    asked = feed._command("update_subscription", {"sids": [7], "market_tickers": ["A"], "action": "get_snapshot"})
    feed.handle({"type": "error", "id": asked, "sid": 7, "seq": 4, "msg": {"code": 11, "msg": "an error reply in sequence"}})
    feed.handle({"type": "orderbook_delta", "sid": 7, "seq": 5, "msg": {"market_ticker": "A", "price_dollars": "0.5000", "delta_fp": "1.00", "side": "yes"}})
    assert feed.counters["gaps"] == 0 and feed.counters["replies_in_sequence"] == 2


def test_ws_feed_reconnects_when_kalshi_ends_a_subscription_but_not_when_the_index_is_refused(tmp_path):
    import pytest

    from lab.ws_recorder import Feed, Reconnect

    feed = Feed(LabStore(tmp_path, stream="ws"), LabRest(FakeKalshi({"ms": T0}), Budget(1e9, 1e9)))
    feed.watch("A", {"series": "KXETH15M", "close_ms": T0 + 900_000, "set": "15m"})
    cmds = feed.connected()
    feed.handle({"id": cmds[0]["id"], "type": "error", "msg": {"code": 9, "msg": "no access to the index"}})
    assert feed.counters["index_refused"] == 1
    with pytest.raises(Reconnect):
        feed.handle({"type": "error", "sid": 2, "msg": {"code": 25, "msg": "subscription buffer overflow"}})
    with pytest.raises(Reconnect):
        feed.handle({"type": "error", "sid": 2, "msg": {"code": 4, "msg": "something about the subscription"}})


def test_ws_feed_settles_fade_markets_across_a_restart(tmp_path):
    from lab.ws_recorder import Feed

    class Api:
        def get(self, path, params=None):
            return {"market": {"ticker": "F-1", "event_ticker": "F", "result": "no", "expiration_value": None}} if path == "/markets/F-1" else {}

    state = tmp_path / "ws_state.json"
    close = "2026-11-03T20:01:00Z"
    feed = Feed(LabStore(tmp_path, stream="ws"), LabRest(Api(), Budget(1e9, 1e9)), state_path=state)
    feed.apply_fade([{"ticker": "F-1", "event_ticker": "F", "close_time": close}], T0)
    feed.apply_fade([{"ticker": "F-2", "event_ticker": "F", "close_time": "2026-11-20T00:00:00Z"}], T0 + 1000)  # F-1 dropped from the watch
    assert "F-1" not in feed.meta and feed.pending_settle["F-1"][0] == T0 + 60_000
    feed.store.close()
    again = Feed(LabStore(tmp_path, stream="ws"), LabRest(Api(), Budget(1e9, 1e9)), state_path=state)
    again.settle_due(T0 + 30_000)  # not yet: two minutes after the close
    assert again.pending_settle
    again.settle_due(T0 + 200_000)
    again.store.close()
    state_now = json.loads(state.read_text())
    assert again.pending_settle == {} and state_now["pending_settle"] == {} and list(state_now["watched"]) == ["F-2"]
    settled = [r for r in read_lab(tmp_path) if r["kind"] == "settled"]
    assert settled[0]["rows"] == [["F-1", "no", None]]


def test_two_recorders_write_and_seal_only_their_own_hour_files(tmp_path):
    rest_store, ws_store = LabStore(tmp_path), LabStore(tmp_path, stream="ws")
    rest_store.write("book_top", {"n": 1}, ts_ms=T0)
    ws_store.write("book", {"n": 2}, ts_ms=T0 + 1)
    ws_store.write("book", {"n": 3}, ts_ms=T0 + H)  # the ws stream rolls over and seals its own 20:00 file only
    ws_store.wait_sealed()
    names = sorted(p.name for p in (tmp_path / "2026-11-03").iterdir())
    assert names == ["20.jsonl", "20.ws.jsonl.gz", "21.ws.jsonl"]
    rest_store.close()
    ws_store.close()
    assert sorted(r["n"] for r in read_lab(tmp_path)) == [1, 2, 3]


def test_ws_signer_handles_rsa_and_ed25519_keys_from_the_environment():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519, rsa

    from lab.ws_auth import KEY_ENV, KEY_ID_ENV, load_signer, ws_headers

    assert load_signer({}) is None
    for key in (rsa.generate_private_key(public_exponent=65537, key_size=2048), ed25519.Ed25519PrivateKey.generate()):
        pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
        import base64

        # as pasted: the PEM itself, folded onto one line, with literal backslash-n, or the base64 of the file
        for raw in (pem, " ".join(pem.split("\n")), pem.replace("\n", "\\n"), base64.b64encode(pem.encode()).decode()):
            key_id, sign = load_signer({KEY_ID_ENV: "kid", KEY_ENV: raw})
            h = ws_headers(key_id, sign, now_ms=1_700_000_000_000)
            assert h["KALSHI-ACCESS-KEY"] == "kid" and h["KALSHI-ACCESS-TIMESTAMP"] == "1700000000000" and len(h["KALSHI-ACCESS-SIGNATURE"]) > 40


def test_report_waits_for_the_live_feed_then_scores_b_c_e_f(tmp_path):
    from lab import report

    lab, tape = tmp_path / "lab", tmp_path / "tape"
    tape.mkdir()
    store = LabStore(lab)
    store.write("lab_status", {"rest": {"requests": 3}}, ts_ms=T0)
    store.close()
    before = report.build(tape, lab)
    assert all("waits for the live feed" in before["strategies"][k]["line"] for k in "BCEF") and before["live_feed"] is None
    ws = LabStore(lab, stream="ws")
    ws.write("lab_status", {"source": "ws", "ws": {"connects": 1}, "rest": {"requests": 2}}, ts_ms=T0 + 1)
    ws.close()
    after = report.build(tape, lab)
    assert after["live_feed"]["ws"] == {"connects": 1} and after["recorder"]["rest"] == {"requests": 3}
    assert [after["strategies"][k]["line"].split(" ")[0] for k in "BCEF"] == ["B", "C", "E", "F"]
    assert not any("waits" in after["strategies"][k]["line"] for k in "BCEF") and after["strategies"]["E"]["summary"]["markets"] == 0


def test_ws_run_records_resubscribes_after_a_drop_and_stops_on_time(tmp_path):
    import asyncio

    import pytest

    websockets = pytest.importorskip("websockets")
    from websockets.asyncio.server import serve

    from lab import ws_recorder
    from lab.ws_recorder import Feed

    seen = []  # (connection number, the commands it received, the key header)

    class Quiet:  # market discovery finds nothing new
        def get(self, path, params=None):
            return {"markets": [], "incentive_programs": [], "cursor": "", "next_cursor": ""}

    async def kalshi(conn):
        n = len(seen) + 1
        cmds = [json.loads(await conn.recv()) for _ in range(3)]
        seen.append((n, cmds, conn.request.headers.get("KALSHI-ACCESS-KEY")))
        for c in cmds:
            channel = c["params"]["channels"][0]
            await conn.send(json.dumps({"id": c["id"], "type": "subscribed", "msg": {"channel": channel, "sid": {"cfbenchmarks_value": 1, "orderbook_delta": 2, "trade": 3}[channel]}}))
        await conn.send(json.dumps({"type": "orderbook_snapshot", "sid": 2, "seq": 1, "msg": {"market_ticker": "ETH-1", "yes_dollars_fp": [["0.4000", "5.00"]], "no_dollars_fp": [["0.5500", "6.00"]]}}))
        await conn.send(json.dumps({"type": "trade", "sid": 3, "seq": 1, "msg": {"market_ticker": "ETH-1", "yes_price_dollars": "0.4000", "count_fp": "1.00", "taker_outcome_side": "no", "ts_ms": 1}}))
        await conn.send(json.dumps({"type": "cfbenchmarks_value", "sid": 1, "seq": 1, "msg": {"index_id": "ETHUSD_RTI", "data": json.dumps({"value": "2000.0"})}}))
        if n == 1:
            await conn.close()  # the first connection drops; the recorder must come back and subscribe again
            return
        await conn.wait_closed()

    async def go():
        async with serve(kalshi, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            ws_recorder.URL = f"ws://127.0.0.1:{port}"
            store = LabStore(tmp_path, stream="ws")
            feed = Feed(store, LabRest(Quiet(), Budget(1e9, 1e9)))
            feed.watch("ETH-1", {"series": "KXETH15M", "event": "E", "close_ms": feed.now_ms() + 900_000, "strike": 1.0, "strike_type": "greater_or_equal", "set": "15m"})
            now = feed.now_ms()
            await ws_recorder.run(feed, now + 5_000, lambda msg: b"signature", "kid", stop=asyncio.Event())
            store.close()
            return feed

    url = ws_recorder.URL
    try:
        feed = asyncio.run(go())
    finally:
        ws_recorder.URL = url
    assert [n for n, _, _ in seen] == [1, 2] and all(key == "kid" for _, _, key in seen)
    assert seen[1][1][1]["params"]["market_tickers"] == ["ETH-1"]  # the second connection subscribes the book again
    assert feed.counters["connects"] == 2 and feed.counters["disconnects"] == 1
    kinds = {r["kind"] for r in read_lab(tmp_path)}
    assert {"book", "index", "lab_status", "trade"} <= kinds


def test_markouts_read_the_book_as_it_stood_then():
    from lab.fills import Resting, markouts

    o = Resting("M", "yes", 0.50, 10, 0, 0.0, filled=10, fills=[{"ts": 1_000, "qty": 10, "price": 0.50}])
    b = lambda bid: {"yes": [[bid, 1.0]], "no": [[1 - bid - 0.02, 1.0]]}  # YES mid = bid + 0.01
    m = markouts(o, [(1_000, b(0.50)), (50_000, b(0.60)), (200_000, b(0.70)), (400_000, b(0.70))], None)[0]
    assert (m["m60"], m["m300"]) == (0.11, 0.21)  # 61 s: the 50 s book; 301 s: the 200 s book, unchanged since
    late = Resting("M", "yes", 0.50, 10, 0, 0.0, filled=10, fills=[{"ts": 100_000, "qty": 10, "price": 0.50}])
    stale = markouts(late, [(0, b(0.50)), (2_000_000, b(0.60))], None)[0]
    assert stale["m60"] == 0.01 and stale["m300"] is None  # 400 s after the last book: no markout rather than a guess


def test_ws_feed_rewrites_an_unchanged_book_only_on_its_heartbeat(tmp_path):
    from lab.ws_recorder import Feed

    clock = {"ms": T0}
    store = LabStore(tmp_path, stream="ws")
    feed = Feed(store, LabRest(FakeKalshi({"ms": T0}), Budget(1e9, 1e9)), now_ms=lambda: clock["ms"])
    feed.watch("INC", {"series": None, "event": None, "close_ms": None, "strike": None, "strike_type": None, "set": "E"})
    feed.handle({"type": "orderbook_snapshot", "sid": 2, "seq": 1, "msg": {"market_ticker": "INC", "yes_dollars_fp": [["0.3000", "500.00"]], "no_dollars_fp": [["0.6000", "500.00"]]}})
    for second in range(0, 125, 5):
        clock["ms"] = T0 + second * 1000
        if second == 30:
            feed.handle({"type": "orderbook_delta", "sid": 2, "seq": 2, "msg": {"market_ticker": "INC", "price_dollars": "0.3000", "delta_fp": "1.00", "side": "yes"}})
        feed.mark_alive(clock["ms"])  # answered pings
        feed.write_books(clock["ms"])
    store.close()
    written = [(r["ts"] - T0) // 1000 for r in read_lab(tmp_path) if r["kind"] == "book"]
    assert written == [0, 30, 90]  # first sight, the change (15 s cadence passed), then the 60 s heartbeat


def test_streamed_markouts_match_markouts_with_every_book_in_hand():
    import random

    from lab.fills import Resting, markouts
    from lab.replay import Markouts

    rng = random.Random(7)
    books, t = [], 0
    for _ in range(400):
        t += rng.choice([2_000, 10_000, 60_000, 400_000])
        bid = round(rng.uniform(0.05, 0.9), 2)
        books.append((t, {"yes": [[bid, 1.0]], "no": [[round(1 - bid - 0.02, 2), 1.0]]}))
    fill_times = sorted(rng.randrange(0, t) for _ in range(150))
    for side, payout in (("yes", 1.0), ("no", 1.0), ("yes", None)):
        order = Resting("M", side, 0.5, 1e9, 0, 0.0, filled=150.0, fills=[{"ts": f, "qty": 1.0, "price": 0.5} for f in fill_times])
        expected = markouts(order, books, payout)
        tracker = Markouts()
        events = sorted([(f, 0, i) for i, f in enumerate(fill_times)] + [(bt, 1, i) for i, (bt, _) in enumerate(books)])
        for ts, is_book, i in events:
            if is_book:
                tracker.book("M", ts, books[i][1])
            else:
                tracker.fill("M", side, order.fills[i])
        got = tracker.settle({"M": (payout, None)} if payout is not None else {})
        assert [{k: r.get(k) for k in ("ts", "m60", "m300", "settle")} for r in got] == [{k: r.get(k) for k in ("ts", "m60", "m300", "settle")} for r in expected]
        assert any(r["m300"] is None for r in got) and any(r["m300"] is not None for r in got)


def test_store_survives_a_kill_mid_line_and_mid_seal(tmp_path):
    import gzip as gz

    from lab.store import seal

    day = tmp_path / "2026-11-03"
    store = LabStore(tmp_path)
    store.write("x", {"n": 1}, ts_ms=T0)
    store.close()
    with open(day / "20.jsonl", "a") as fh:
        fh.write('{"ts":1793736000001,"kind":"x","n":')  # a kill cut this line off
    again = LabStore(tmp_path)
    again.write("x", {"n": 2}, ts_ms=T0 + 2)  # the cut line is ended first, so this record survives
    again.close()
    assert [r["n"] for r in read_lab(tmp_path)] == [1, 2]
    seal(day / "20.jsonl")
    (day / "20.jsonl.gz.tmp").write_bytes(b"half a member")  # a seal killed before its swap leaves only a temp file
    assert [r["n"] for r in read_lab(tmp_path)] == [1, 2]
    with open(day / "20.jsonl.gz", "ab") as fh:  # an older, non-atomic seal could leave a cut member: readers carry on
        fh.write(gz.compress(b'{"ts":1793736000003,"kind":"x","n":3}\n')[:-9])
    (day / "21.jsonl").write_text('{"ts":1793739600000,"kind":"x","n":4}\n')
    assert [r["n"] for r in read_lab(tmp_path)][-1] == 4


def test_lab_rest_counts_network_failures_instead_of_raising():
    import http.client

    class Flaky:
        def __init__(self):
            self.errors = [TimeoutError("read timed out"), http.client.RemoteDisconnected("closed"), http.client.IncompleteRead(b""), ValueError("not JSON")]

        def get(self, path, params=None):
            if self.errors:
                raise self.errors.pop(0)
            return {"ok": True}

    rest = LabRest(Flaky(), Budget(1e9, 1e9))
    assert [rest.get("/x") for _ in range(5)] == [None, None, None, None, {"ok": True}]
    assert rest.counters()["network_errors"] == 4 and rest.counters()["errors"] == 4


def test_recorder_carries_on_after_a_poll_that_raises(tmp_path):
    now = {"ms": T0 + 50 * 60_000}
    rec = Recorder(LabRest(FakeKalshi(now), Budget(1e9, 1e9)), LabStore(tmp_path), now_ms=lambda: now["ms"])
    calls = {"n": 0}
    real = rec.snapshot

    def snapshot(ts):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        real(ts)

    rec.snapshot = snapshot

    def sleep(s):
        now["ms"] += int(s * 1000) or 1000

    rec.run(now["ms"] + 3 * 60_000, sleep=sleep)
    rec.store.close()
    assert rec.poll_errors == 1 and calls["n"] >= 3
    assert any(r["kind"] == "book_top" for r in read_lab(tmp_path))


def _feed(tmp_path, clock, api=None, **kw):
    from lab.ws_recorder import Feed

    return Feed(LabStore(tmp_path, stream="ws"), LabRest(api or FakeKalshi({"ms": T0}), Budget(1e9, 1e9)), now_ms=lambda: clock["ms"], **kw)


def _snap(ticker, yes, no, seq=1):
    return {"type": "orderbook_snapshot", "sid": 2, "seq": seq, "msg": {"market_ticker": ticker, "yes_dollars_fp": yes, "no_dollars_fp": no}}


def test_ws_feed_asks_again_for_a_missing_snapshot_then_drops_the_market_and_refreshes_ready_books(tmp_path):
    from lab.ws_recorder import SNAPSHOT_REFRESH_S, SNAPSHOT_RETRY_S

    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    for t in ("QUIET", "LIVE"):
        feed.watch(t, {"set": "E"})
    feed.connected()
    feed.handle({"type": "subscribed", "msg": {"channel": "orderbook_delta", "sid": 2}})
    feed.handle(_snap("LIVE", [["0.4000", "10.00"]], [["0.5000", "10.00"]]))
    asked = []
    for second in range(0, sum(SNAPSHOT_RETRY_S) + SNAPSHOT_RETRY_S[-1] + 30, 5):  # the last ask gets its wait too
        clock["ms"] = T0 + second * 1000
        feed.outbox.clear()
        feed.tick(clock["ms"])
        asked += [second for c in feed.outbox if c["params"].get("action") == "get_snapshot" and "QUIET" in c["params"]["market_tickers"]]
    assert asked == [10, 30, 70, 150, 310, 630] and "QUIET" not in feed.meta and feed.counters["dropped_no_snapshot"] == 1
    clock["ms"] = T0 + SNAPSHOT_REFRESH_S * 1000 + 5_000
    feed.outbox.clear()
    feed.tick(clock["ms"])
    assert [c["params"]["market_tickers"] for c in feed.outbox if c["params"].get("action") == "get_snapshot"] == [["LIVE"]]
    feed.handle(_snap("LIVE", [["0.4100", "10.00"]], [["0.5000", "10.00"]], seq=2))  # the refresh disagrees with the book kept
    assert feed.counters["snapshot_drift"] == 1


def test_ws_feed_writes_no_book_while_the_link_is_silent(tmp_path):
    from lab.ws_recorder import STALE_MS

    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    feed.watch("M", {"set": "E"})
    feed.handle(_snap("M", [["0.4000", "10.00"]], [["0.5000", "10.00"]]))
    feed.write_books(clock["ms"])
    clock["ms"] += STALE_MS + 60_000  # no message and no answered ping since
    feed.write_books(clock["ms"])
    feed.write_books(clock["ms"] + 5_000)
    feed.mark_alive(clock["ms"] + 10_000)
    feed.write_books(clock["ms"] + 10_000)
    feed.store.close()
    recs = list(read_lab(tmp_path))
    assert [(r["ts"] - T0) // 1000 for r in recs if r["kind"] == "book"] == [0, (STALE_MS + 70_000) // 1000]
    notes = [r["note"] for r in recs if r["kind"] == "lab_status"]
    assert len(notes) == 2 and notes[0].startswith("feed silent") and notes[1].startswith("feed back")


def test_ws_feed_fills_in_a_strike_published_after_discovery_and_keeps_one_market_in_two_sets(tmp_path):
    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    m = {"ticker": "ETH-Q", "event_ticker": "ETH", "close_time": "2026-11-03T20:15:00Z", "strike_type": "greater_or_equal"}
    feed.apply_crypto({"KXETH15M": {"markets": [{**m, "floor_strike": None}]}, "KXBTC15M": None}, T0)
    assert feed.meta["ETH-Q"]["strike"] is None
    feed.apply_crypto({"KXETH15M": {"markets": [{**m, "floor_strike": 2239.67}]}, "KXBTC15M": None}, T0 + 2_000)
    assert feed.meta["ETH-Q"]["strike"] == 2239.67
    feed.watch("BOTH", {"set": "F", "close_ms": T0 + 86_400_000, "event": "EV"})
    feed.watch("BOTH", {"set": "E"})
    assert feed.meta["BOTH"]["sets"] == ["E", "F"] and feed.meta["BOTH"]["close_ms"] == T0 + 86_400_000
    feed.handle(_snap("BOTH", [[f"0.{40 - i:02d}00", "10.00"] for i in range(40)], [["0.5000", "10.00"]]))
    feed.write_books(clock["ms"])
    feed.unwatch("BOTH", "F")
    assert feed.meta["BOTH"]["sets"] == ["E"]
    feed.connected()
    feed.handle({"type": "subscribed", "msg": {"channel": "orderbook_delta", "sid": 2}})
    feed.outbox.clear()
    feed.unwatch("BOTH", "E")
    assert "BOTH" not in feed.meta and feed.outbox[-1]["params"]["action"] == "delete_markets"
    feed.store.close()
    book = next(r for r in read_lab(tmp_path) if r["kind"] == "book")
    assert book["set"] == "E" and book["sets"] == ["E", "F"] and len(book["yes"]) == 40  # full depth for an incentive market


def test_ws_feed_ignores_a_partial_program_list_and_books_of_markets_it_does_not_watch(tmp_path):
    class Pages:
        def get(self, path, params=None):
            if (params or {}).get("cursor"):
                raise TimeoutError("page two timed out")
            return {"incentive_programs": [{"market_ticker": "INC-1", "incentive_type": "liquidity", "period_reward": 100, "start_date": "2026-11-03T00:00:00Z",
                                            "end_date": "2026-11-05T00:00:00Z", "target_size_fp": "100.00"}], "next_cursor": "more"}

    clock = {"ms": T0}
    feed = _feed(tmp_path, clock, api=Pages())
    feed.watch("INC-0", {"set": "E"})
    feed.refresh_incentives(T0)
    assert "INC-0" in feed.meta and feed.counters["incentive_fetch_failed"] == 1  # nothing written, nothing dropped
    feed.handle(_snap("STRAY", [["0.4000", "10.00"]], [["0.5000", "10.00"]]))
    assert "STRAY" not in feed.books
    feed.handle(_snap("INC-0", [["0.4000", "10.00"]], [["0.5000", "10.00"]]))
    feed.unwatch("INC-0")
    feed.watch("INC-0", {"set": "E"})
    assert "INC-0" not in feed.books  # a book kept from before is stale: it waits for a fresh snapshot
    feed.store.close()
    assert not [r for r in read_lab(tmp_path) if r["kind"] == "incentives"]


def test_ws_feed_settles_with_growing_waits_and_a_few_at_a_time(tmp_path):
    from lab.ws_recorder import SETTLE_PER_PASS

    class Unsettled:
        calls = []

        def get(self, path, params=None):
            self.calls.append(path)
            return {"market": {"result": ""}}

    clock = {"ms": T0}
    api = Unsettled()
    feed = _feed(tmp_path, clock, api=api)
    for i in range(5):
        feed._settle_later(f"F-{i}", T0)
    tries = []
    for minute in range(0, 100):
        now = T0 + minute * 60_000
        before = len(api.calls)
        feed.settle_due(now)
        if len(api.calls) > before:
            tries.append((minute, len(api.calls) - before))
    assert all(n <= SETTLE_PER_PASS for _, n in tries)
    f0 = [m for m, _ in tries]
    assert f0[:2] == [2, 3]  # three at two minutes after the close, the other two a minute later
    assert len(api.calls) == 5 * 4  # each tried at +2, then 5, 15 and 60 minutes after each miss: four times in 100 minutes


def test_ws_schedule_looks_for_new_contracts_right_after_each_quarter_and_keeps_slow_lookups_away(tmp_path):
    from lab.ws_recorder import Schedule

    s = Schedule()
    q = T0 + 900_000  # 20:15:00Z
    found = {"yes": False}
    jobs = {}
    for ms in range(q - 250_000, q + 200_000, 1000):
        job = s.due(ms, lambda close: found["yes"] and close == q + 900_000)
        if job:
            jobs.setdefault(job, []).append((ms - q) // 1000)
        if job == "crypto" and ms >= q + 10_000:
            found["yes"] = True  # both new contracts show up on the 10-second look
    assert [t for t in jobs["crypto"] if t >= 0] == [2, 10]  # no more tries once both are found
    from lab.ws_recorder import QUIET_S

    assert jobs.get("settle")  # it does run, just never close to the quarter
    assert not [(job, t) for job in ("settle", "incentives", "fade") for t in jobs.get(job, []) if -QUIET_S[job] < t < 10]


def test_ws_book_sizes_are_exact_and_a_crossed_book_is_never_written(tmp_path):
    from lab.ws_recorder import Book

    b = Book()
    b.snapshot({"yes_dollars_fp": [["0.0010", "795558.75"]], "no_dollars_fp": [["0.9900", "1.00"]]})
    for _ in range(3):
        b.delta({"side": "yes", "price_dollars": "0.0010", "delta_fp": "-265186.25"})
    assert b.yes == {} and b.normalized()["yes"] == []
    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    feed.watch("X", {"set": "E"})
    feed.handle(_snap("X", [["0.6000", "5.00"]], [["0.5000", "5.00"]]))  # a YES bid above the YES ask
    feed.write_books(clock["ms"])
    assert feed.counters["crossed_books"] == 1 and not feed.books["X"].ready


def test_ws_exit_code_says_when_it_never_connected_or_went_quiet(tmp_path):
    from lab.ws_recorder import NO_DATA_EXIT_MS

    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    assert feed.exit_code(T0 + 60_000, T0) == 3
    feed.counters["connects"] = 1
    feed.watch("M", {"set": "E"})
    assert feed.exit_code(T0 + 60_000, T0) == 0
    assert feed.exit_code(T0 + NO_DATA_EXIT_MS + 1, T0) == 4
    clock["ms"] = T0 + NO_DATA_EXIT_MS  # a book message near the end
    feed.handle(_snap("M", [["0.4000", "10.00"]], [["0.5000", "10.00"]]))
    assert feed.exit_code(T0 + NO_DATA_EXIT_MS + 1, T0) == 0


def test_markouts_use_each_set_s_book_age_and_block_trades_never_fill():
    from lab.fills import Resting, apply_trade, markouts

    o = Resting("M", "yes", 0.50, 10, 0, 0.0, filled=10, fills=[{"ts": 0, "qty": 10, "price": 0.50}])
    fast = {"yes": [[0.55, 1.0]], "no": [[0.43, 1.0]], "set": "15m", "sets": ["15m"]}
    assert markouts(o, [(0, fast), (400_000, fast)], None)[0]["m60"] is None  # a 15-minute book a minute old: the recording missed it
    slow = {**fast, "set": "F", "sets": ["F"]}
    assert markouts(o, [(0, slow), (400_000, slow)], None)[0]["m60"] == 0.06  # YES mid 0.56: an unchanged long-shot book is rewritten only every 5 min
    r = Resting("M", "yes", 0.50, 10, 0, 0.0)
    assert apply_trade(r, {"ts": 1, "yes_price": 0.40, "count": 5, "taker_side": "no", "block": True}) == 0
    assert apply_trade(r, {"ts": 1, "yes_price": 0.40, "count": 5, "taker_side": "no"}) == 5


def test_ws_feed_stops_early_once_it_has_plainly_failed(tmp_path):
    from lab.ws_recorder import NEVER_CONNECTED_EXIT_MS, NO_DATA_EXIT_MS

    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    assert feed.failing(T0 + NEVER_CONNECTED_EXIT_MS - 1, T0) == 0
    assert feed.failing(T0 + NEVER_CONNECTED_EXIT_MS + 1, T0) == 3
    feed.counters["connects"] = 1
    feed.watch("M", {"set": "E"})
    assert feed.failing(T0 + NEVER_CONNECTED_EXIT_MS + 1, T0) == 0
    assert feed.failing(T0 + NO_DATA_EXIT_MS + 1, T0) == 4


def test_ws_feed_keeps_only_the_programs_of_the_markets_it_watches(tmp_path):
    from lab.ws_recorder import E_MAX

    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    programs = [{"market_ticker": f"M{i}", "incentive_type": "liquidity", "period_reward": 1_000_000 * (i + 1), "start_date": "2026-11-03T00:00:00Z",
                 "end_date": "2026-11-05T00:00:00Z", "target_size_fp": "1000.00"} for i in range(40)]
    feed.apply_incentives(programs, T0)
    feed.store.close()
    rec = next(r for r in read_lab(tmp_path) if r["kind"] == "incentives")
    kept = {p["market_ticker"] for p in rec["programs"]}
    assert rec["active_programs"] == 40 and kept == {f"M{i}" for i in range(40 - E_MAX, 40)} == {t for t, m in feed.meta.items() if "E" in m["sets"]}


def test_ws_feed_keeps_trades_only_where_a_strategy_fills_and_merges_the_prints_of_one_sweep(tmp_path):
    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    feed.watch("BTC-Q", {"series": "KXBTC15M", "close_ms": T0 + 900_000, "set": "15m"})
    feed.watch("ETH-Q", {"series": "KXETH15M", "close_ms": T0 + 900_000, "set": "15m"})
    feed.watch("INC", {"set": "E"})
    cmds = feed.connected()
    subs = {c["params"]["channels"][0]: c["params"]["market_tickers"] for c in cmds if c["params"].get("market_tickers")}
    assert subs == {"orderbook_delta": ["BTC-Q", "ETH-Q", "INC"], "trade": ["ETH-Q", "INC"]}
    feed.handle({"type": "subscribed", "msg": {"channel": "trade", "sid": 3}})
    feed.watch("BTC-Q", {"set": "F"})  # joins a set that fills from trades: its trades are added
    assert feed.outbox[-1]["params"] == {"sids": [3], "market_tickers": ["BTC-Q"], "action": "add_markets"}
    feed.unwatch("BTC-Q", "F")
    assert feed.outbox[-1]["params"] == {"sids": [3], "market_tickers": ["BTC-Q"], "action": "delete_markets"} and "BTC-Q" in feed.meta
    sweep = {"market_ticker": "ETH-Q", "yes_price_dollars": "0.5200", "taker_outcome_side": "yes", "ts_ms": T0 + 10}
    for count in ("1.00", "0.50", "2.00"):
        feed.handle({"type": "trade", "sid": 3, "msg": {**sweep, "count_fp": count}})
    feed.handle({"type": "trade", "sid": 3, "msg": {**sweep, "yes_price_dollars": "0.5300", "count_fp": "1.00"}})  # through the next level
    feed.handle({"type": "trade", "sid": 3, "msg": {**sweep, "market_ticker": "BTC-Q", "count_fp": "9.00"}})  # not kept
    feed.write_books(T0 + 100)  # not yet: prints are gathered for TRADE_FLUSH_MS
    feed.write_books(T0 + 250)
    feed.store.close()
    trades = [r for r in read_lab(tmp_path) if r["kind"] == "trade"]
    assert [(r["yes_price"], r["count"], r["n"]) for r in trades] == [(0.52, 3.5, 3), (0.53, 1.0, 1)]


def test_ws_feed_writes_the_btc_book_slowly_until_its_last_three_minutes(tmp_path):
    clock = {"ms": T0}
    feed = _feed(tmp_path, clock)
    close = T0 + 900_000
    for t, series in (("BTC-Q", "KXBTC15M"), ("ETH-Q", "KXETH15M")):
        feed.watch(t, {"series": series, "close_ms": close, "set": "15m"})
        feed.handle(_snap(t, [[f"0.{40 + i:02d}00", "1.00"] for i in range(20)], [["0.4000", "1.00"]]))
    for second in range(0, 900, 1):
        clock["ms"] = T0 + second * 1000
        feed.mark_alive(clock["ms"])
        for t in ("BTC-Q", "ETH-Q"):
            feed.books[t].changed = True  # a busy book
        feed.write_books(clock["ms"])
    feed.store.close()
    books = [r for r in read_lab(tmp_path) if r["kind"] == "book"]
    times = {t: [(r["ts"] - T0) // 1000 for r in books if r["ticker"] == t] for t in ("BTC-Q", "ETH-Q")}
    assert [x for x in times["BTC-Q"] if x < 720] == list(range(0, 720, 60))  # once a minute ...
    assert [x for x in times["BTC-Q"] if x >= 720][:3] == [720, 722, 724]  # ... then every 2 s for B
    assert [x for x in times["ETH-Q"] if x < 720][:3] == [0, 10, 20]  # C's book every 10 s throughout
    assert all(len(r["yes"]) == 10 for r in books)
