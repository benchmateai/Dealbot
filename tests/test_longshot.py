import pytest

from lab import longshot as ls

DAY = 86_400
T0 = 1_780_000_000  # a market opens at T0 (2026-05-28)


def iso(ts):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def market(ticker="M1", event="E1", result="no", days_open=20, series="S1"):
    return {"ticker": ticker, "event_ticker": event, "series_ticker": series, "result": result, "market_type": "binary",
            "open_time": iso(T0), "close_time": iso(T0 + days_open * DAY), "volume_fp": "5000.00"}


def candle(day, bid, ask, high=None):
    c = {"end_period_ts": T0 + day * DAY, "yes_bid": {"close": f"{bid:.4f}"}, "yes_ask": {"close": f"{ask:.4f}"}, "price": {"high": None if high is None else f"{high:.4f}"}}
    return c


SERIES = {"S1": {"ticker": "S1", "category": "Entertainment", "fee_type": "quadratic", "fee_multiplier": 1, "frequency": "one_off"}}


def test_the_taker_fee_is_rounded_up_to_the_cent_on_the_order():
    assert ls.fee(0.07, 0.95) == 0.0034  # 0.07 x 100 x 0.95 x 0.05 = 33.25 cents, charged 34
    assert ls.fee(0.07, 0.99) == 0.0007 and ls.fee(0.0, 0.95) == 0.0


def test_a_long_shot_seven_days_after_the_open_is_bought_at_the_no_ask_and_a_resting_bid_fills_on_a_later_trade():
    candles = [candle(6.5, 0.05, 0.06), candle(9, 0.05, 0.07, high=0.07), candle(12, 0.05, 0.06, high=0.06)]
    b = ls.bets(market(), candles, SERIES["S1"], 7)
    assert b["taker"] == (0.95, 0.0034, 1.0)
    assert b["maker_strict"] == (0.94, 0.0, 1.0) and b["maker_loose"] == (0.94, 0.0, 1.0)  # a trade at 7c went through the 6c offer
    only_touch = [candle(6.5, 0.05, 0.06), candle(9, 0.05, 0.06, high=0.06)]
    b = ls.bets(market(), only_touch, SERIES["S1"], 7)
    assert "maker_strict" not in b and b["maker_loose"] == (0.94, 0.0, 1.0)


def test_no_bet_when_the_market_closed_before_entry_the_quote_is_stale_or_the_yes_side_is_no_long_shot():
    assert ls.bets(market(days_open=5), [candle(6.5, 0.05, 0.06)], SERIES["S1"], 7) == {}  # a fresh quote, but closed before entry
    assert ls.bets(market(), [candle(5.5, 0.05, 0.06)], SERIES["S1"], 7) == {}  # a day and a half old at entry
    assert ls.bets(market(), [candle(6.5, 0.20, 0.22)], SERIES["S1"], 7) == {}
    assert "taker" not in ls.bets(market(), [candle(6.5, 0.0, 0.01)], SERIES["S1"], 7)  # no YES bid: no NO ask under $1


def test_a_maker_fee_is_charged_only_where_the_series_has_one_and_a_zero_multiplier_is_fee_free():
    candles = [candle(6.5, 0.05, 0.06), candle(9, 0.05, 0.07, high=0.07)]
    makers = {**SERIES["S1"], "fee_type": "quadratic_with_maker_fees"}
    assert ls.bets(market(), candles, makers, 7)["maker_strict"][1] == ls.fee(0.0175, 0.94)
    free = {**SERIES["S1"], "fee_multiplier": 0}
    assert ls.bets(market(), candles, free, 7)["taker"][1] == 0.0


def test_every_contract_on_an_event_is_one_bet_and_an_upset_costs_its_stake():
    ms = [market("A", "E1", "no"), market("B", "E1", "yes"), market("C", "E2", "no")]
    candles = {t: [candle(6.5, 0.05, 0.06)] for t in "ABC"}
    evs = {e["event"]: e for e in ls.event_bets(ms, candles, SERIES, 7, "taker")}
    assert evs["E1"]["contracts"] == 2 and evs["E1"]["pnl"] == pytest.approx((1 - 0.9534) + (0 - 0.9534))
    assert evs["E2"]["pnl"] == pytest.approx(1 - 0.9534) and evs["E1"]["group"] == "recreational"


def _run(upsets, n=40):
    ms, candles = [], {}
    for i in range(n):  # events an hour apart, YES at 5 cents
        m = market(f"M{i}", f"E{i}", "yes" if i in upsets else "no")
        m["open_time"] = iso(T0 + i * 3600)
        m["close_time"] = iso(T0 + i * 3600 + 20 * DAY)
        ms.append(m)
        candles[m["ticker"]] = [{**candle(6.5, 0.05, 0.06), "end_period_ts": T0 + i * 3600 + int(6.5 * DAY)}]
    return ls.evaluate(ms, candles, SERIES)


def test_the_main_test_passes_with_steady_wins_and_fails_when_a_half_loses():
    win = _run(set())
    stake = 0.95 + ls.fee(0.07, 0.95)
    assert win["results"]["taker/7d/recreational"]["return"] == pytest.approx((1 - stake) / stake, abs=1e-5)
    assert win["main_test"]["passed"] and win["main_test"]["ci95"][0] > 0
    late = _run(set(range(300, 316)), n=600)  # 16 upsets, all in the second half: the whole is clearly ahead, that half is not
    mt = late["main_test"]
    assert mt["ci95"][0] > 0 and mt["halves"][0] > 0 > mt["halves"][1] and not mt["passed"]  # only the halves rule fails it


def test_the_live_endpoint_s_candle_shape_is_read_too():
    live = [{"end_period_ts": T0 + int(6.5 * DAY), "yes_bid": {"close_dollars": "0.0500"}, "yes_ask": {"close_dollars": "0.0600"}, "price": {}},
            {"end_period_ts": T0 + 9 * DAY, "yes_bid": {"close_dollars": "0.0500"}, "yes_ask": {"close_dollars": "0.0700"}, "price": {"high_dollars": "0.0700"}}]
    b = ls.bets(market(), live, SERIES["S1"], 7)
    assert b["taker"] == (0.95, 0.0034, 1.0) and b["maker_strict"] == (0.94, 0.0, 1.0)


def test_a_resting_bid_fills_on_the_close_s_own_day_but_not_on_trades_before_entry():
    m = market(days_open=19, result="yes")  # the long shot comes in on its last day
    m["close_time"] = iso(T0 + 19 * DAY + 21 * 3600)  # closes at 21:00 on day 19
    closing_day = [candle(6.5, 0.05, 0.06), candle(20, 0.05, 0.99, high=0.99)]  # the candle that holds the close ends after it
    b = ls.bets(m, closing_day, SERIES["S1"], 7)
    assert b["maker_strict"] == (0.94, 0.0, 0.0)  # the upset fills the bid, and it loses
    same_day = [candle(6.5, 0.05, 0.06), candle(7.5, 0.05, 0.08, high=0.08)]  # that day began before entry
    assert "maker_strict" not in ls.bets(market(), same_day, SERIES["S1"], 7)


def test_an_entry_before_the_window_is_left_out_and_a_market_listed_twice_counts_once(tmp_path):
    early = market()
    early["open_time"], early["close_time"] = "2025-04-20T00:00:00Z", "2025-06-01T00:00:00Z"
    start = ls._ts(early["open_time"])
    assert ls.bets(early, [{**candle(0, 0.05, 0.06), "end_period_ts": start + int(6.5 * DAY)}], SERIES["S1"], 7) == {}
    import json
    (tmp_path / "markets").mkdir()
    (tmp_path / "markets" / "S1.json").write_text(json.dumps([market("A"), market("A"), market("B")]))
    assert [m["ticker"] for m in ls.load_markets(tmp_path)] == ["A", "B"]


def test_prices_are_fetched_for_every_market_open_a_week_and_a_fixed_sample_of_shorter_ones():
    week = [market(f"L{i}", days_open=30) for i in range(5)]
    short = [market(f"S{i}", days_open=3) for i in range(ls.CANDLE_SHORT_SAMPLE + 50)]
    tiny = [{**market("T"), "close_time": iso(T0 + 3600)}]
    picked = ls.to_price(week + short + tiny)
    assert [m["ticker"] for m in picked[:5]] == [f"L{i}" for i in range(5)] and len(picked) == 5 + ls.CANDLE_SHORT_SAMPLE
    assert "T" not in {m["ticker"] for m in picked} and picked == ls.to_price(list(reversed(week + short + tiny)))


def test_the_series_sample_is_fixed_by_the_seed_and_leaves_out_intraday_series_and_other_categories():
    series = [{"ticker": f"R{i}", "category": "Sports", "frequency": "custom"} for i in range(900)]
    series += [{"ticker": f"Q{i}", "category": "Sports", "frequency": "hourly"} for i in range(50)]
    series += [{"ticker": f"C{i}", "category": "Economics", "frequency": "monthly"} for i in range(300)]
    series += [{"ticker": f"X{i}", "category": "Exotics", "frequency": "one_off"} for i in range(10)]
    a, b = ls.sample_series(series), ls.sample_series(list(reversed(series)))
    assert [s["ticker"] for s in a] == [s["ticker"] for s in b]
    assert sum(s["category"] == "Sports" for s in a) == 700 and sum(s["category"] == "Economics" for s in a) == 200
    assert not any(s["frequency"] == "hourly" or s["category"] == "Exotics" for s in a)


def test_a_sampled_short_lived_event_counts_for_its_share_of_the_population():
    long_ev = market("L", "EL", "no", days_open=30)
    short_ev = market("S", "ES", "yes", days_open=5)
    candles = {"L": [candle(0.5, 0.05, 0.06)], "S": [candle(0.5, 0.05, 0.06)]}
    stake = 0.95 + ls.fee(0.07, 0.95)
    plain = ls.evaluate([long_ev, short_ev], candles, SERIES)["results"]["taker/1d/recreational"]["return"]
    weighted = ls.evaluate([long_ev, short_ev], candles, SERIES, short_weight=3.0)["results"]["taker/1d/recreational"]["return"]
    assert plain == pytest.approx((1 - 2 * stake) / (2 * stake), abs=1e-5)
    assert weighted == pytest.approx((1 - 4 * stake) / (4 * stake), abs=1e-5)  # the short event's loss counts three times
