import itertools
import random
from datetime import UTC, date, datetime, timedelta

import pytest

from lab import etf
from lab.etf import CASH, World


def _ts(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, 14, 30, tzinfo=UTC).timestamp())


def _weekdays(start: date, end: date) -> list[date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _world(days: list[date], paths: dict[str, list[float]], cash_daily: float = 0.0) -> World:
    cash, lv = [], 1.0
    for i in range(len(days)):
        if i:
            lv *= 1 + cash_daily
        cash.append(lv)
    return World(days, paths, cash)


def _path(n: int, daily: float, start: float = 1.0) -> list[float]:
    out, lv = [], start
    for i in range(n):
        if i:
            lv *= 1 + daily
        out.append(lv)
    return out


def test_parse_yahoo_days_closes_and_dividends():
    d1, d2, d3 = date(2024, 3, 1), date(2024, 3, 4), date(2024, 3, 5)
    raw = {"chart": {"result": [{
        "meta": {"gmtoffset": -18000},
        "timestamp": [_ts(d1), _ts(d2), _ts(d3)],
        "indicators": {"quote": [{"close": [100.0, None, 0]}], "adjclose": [{"adjclose": [99.0, None, 98.0]}]},
        "events": {"dividends": {"a": {"amount": 0.5, "date": _ts(d2)}, "b": {"amount": 0.25, "date": _ts(d2)}}},
    }]}}
    got = etf.parse_yahoo(raw)
    assert got["rows"] == {d1: (100.0, 99.0), d2: (None, None), d3: (None, 98.0)}
    assert got["dividends"] == {d2: 0.75}


def test_tr_levels_dividend_on_a_day_without_close_carries_to_the_next_close():
    days = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    fund = {"rows": {days[1]: (100.0, None), days[3]: (102.0, None)},
            "dividends": {days[0]: 9.0, days[2]: 1.0}}  # the first is before the first close: no holder
    lv, notes = etf.tr_levels(fund, days)
    assert lv[0] is None and lv[1] == 1.0 and lv[2] == 1.0
    assert lv[3] == pytest.approx(103.0 / 100.0)
    assert notes["first"] == days[1] and notes["max_gap"] == 1 and notes["jumps"] == []


def test_tr_levels_flags_jumps_and_moves_off_yahoos_adjusted_close():
    days = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
    fund = {"rows": {days[0]: (90.0, 90.0), days[1]: (30.0, 30.0), days[2]: (31.0, 30.0)}, "dividends": {}}
    _, notes = etf.tr_levels(fund, days)
    assert notes["jumps"] == [("2024-01-02", -0.6667)]
    assert notes["adj_off"] == 1  # day 3 rose 3.3% on the close, 0% on the adjusted close


def test_parse_fred_skips_header_and_missing():
    text = "observation_date,DTB3\n2024-01-01,.\n2024-01-02,5.25\n2024-01-03,\n"
    assert etf.parse_fred(text) == {date(2024, 1, 2): 5.25}


def test_cash_uses_the_rate_known_on_the_previous_trading_day():
    days = [date(2024, 1, 5), date(2024, 1, 8), date(2024, 1, 9)]
    rates = {date(2024, 1, 4): 3.6, date(2024, 1, 8): 36.0}
    lv = etf.cash_levels(rates, days)
    assert lv[1] == pytest.approx(1 + 0.036 * 3 / 360)  # Fri -> Mon at Thursday's rate; Monday's is not yet known
    assert lv[2] == pytest.approx(lv[1] * (1 + 0.36 / 360))
    with pytest.raises(etf.MissingData):
        etf.cash_levels({date(2024, 1, 6): 1.0}, days)


def test_month_ends():
    days = [date(2024, 1, 30), date(2024, 1, 31), date(2024, 2, 1), date(2024, 2, 29), date(2024, 3, 1)]
    assert World(days, {}, [1.0] * 5).month_ends == [1, 3, 4]


def _monthly_world(rets: dict[str, list[float]], cash_month: float = 0.0, start=date(2000, 1, 3)) -> World:
    """One trading day a month (the 3rd) plus a month end, so each month end carries that month's return."""
    days, d, n = [], start, max(len(v) for v in rets.values())
    for _ in range(n):
        days.append(d)
        d = (d.replace(day=1) + timedelta(days=32)).replace(day=3)
    paths = {}
    for f, rs in rets.items():
        lv, out = 1.0, []
        for r in rs:
            lv *= 1 + r
            out.append(lv)
        paths[f] = out
    return _world(days, paths, 0.0) if not cash_month else World(days, paths, _path(n, cash_month))


def test_above_sma_and_spy_rule():
    w = _monthly_world({"SPY": [0.0] * 9 + [0.05]})
    assert etf.above_sma(w, "SPY", 8) is None  # only nine month ends so far
    assert etf.above_sma(w, "SPY", 9) is True and etf.rule_spy_sma10(w, 9) == {"SPY": 1.0}
    w = _monthly_world({"SPY": [0.0] * 9 + [-0.05]})
    assert etf.rule_spy_sma10(w, 9) == {CASH: 1.0}


def test_gtaa5_puts_each_fifth_in_its_fund_or_cash():
    up, down = [0.0] * 9 + [0.05], [0.0] * 9 + [-0.05]
    w = _monthly_world({"SPY": up, "EFA": down, "IEF": up, "VNQ": down, "DBC": down})
    got = etf.rule_gtaa5(w, 9)
    assert got == pytest.approx({"SPY": 0.2, "IEF": 0.2, CASH: 0.6})
    w = _monthly_world({"SPY": up, "EFA": up, "IEF": up, "VNQ": up, "DBC": up})
    w.levels["DBC"][0] = None  # DBC's first month end is missing: no fifth can be judged
    assert etf.rule_gtaa5(w, 9) is None


def test_gem_branches():
    base = [0.0] * 12
    w = _monthly_world({"SPY": base + [0.10], "EFA": base + [0.20], "AGG": base + [0.0]}, cash_month=0.001)
    assert etf.rule_gem(w, 12) == {"EFA": 1.0}
    w = _monthly_world({"SPY": base + [0.10], "EFA": base + [0.10], "AGG": base + [0.0]}, cash_month=0.001)
    assert etf.rule_gem(w, 12) == {"SPY": 1.0}  # a tie goes to SPY
    w = _monthly_world({"SPY": base + [0.005], "EFA": base + [0.30], "AGG": base + [0.0]}, cash_month=0.001)
    assert etf.rule_gem(w, 12) == {"AGG": 1.0}  # SPY's 0.5% is below cash's 1.2%: bonds, whatever EFA did
    assert etf.rule_gem(w, 11) is None
    w.levels["AGG"][w.month_ends[12]] = None
    assert etf.rule_gem(w, 12) is None  # no bond fund to fall back on yet


def test_vol_target_scales_and_caps():
    days = _weekdays(date(2024, 1, 1), date(2024, 3, 29))
    calm = _path(len(days), 0.0005)
    w = _world(days, {"SPY": calm})
    k = len(w.month_ends) - 1
    assert etf.rule_vol_target(w, k) == {"SPY": 1.0}  # no volatility: capped at 1, no margin
    wild, lv = [], 1.0
    for i in range(len(days)):
        if i:
            lv *= 1.02 if i % 2 else 0.98
        wild.append(lv)
    w = _world(days, {"SPY": wild})
    got = etf.rule_vol_target(w, k)
    i = w.month_ends[k]
    rets = [b / a - 1 for a, b in zip(wild[i - 21:i + 1], wild[i - 20:i + 1])]
    x = 0.15 / (etf.statistics.stdev(rets) * 252 ** 0.5)
    assert got["SPY"] == pytest.approx(x) and got[CASH] == pytest.approx(1 - x) and x < 1


def test_qqq_gold_falls_back_to_cash():
    base = [0.0] * 12
    w = _monthly_world({"QQQ": base + [0.05], "GLD": base + [0.08]}, cash_month=0.001)
    assert etf.rule_qqq_gold(w, 12) == {"GLD": 1.0}
    w = _monthly_world({"QQQ": base + [-0.05], "GLD": base + [0.005]}, cash_month=0.001)
    assert etf.rule_qqq_gold(w, 12) == {CASH: 1.0}


def test_rules_on_a_world_cut_at_the_signal_day_decide_the_same():
    """A rule reading any day after its signal day would fail (an IndexError) on the cut world."""
    rng = random.Random(1)
    days = _weekdays(date(2001, 1, 1), date(2004, 12, 31))
    paths = {f: [] for f in etf.TICKERS}
    for f in etf.TICKERS:
        lv = 1.0
        for _ in days:
            lv *= 1 + rng.gauss(0.0003, 0.01)
            paths[f].append(lv)
    w = _world(days, paths, 0.0001)
    for name in ("spy_sma10", "gtaa5", "gem", "vol_target", "qqq_gold", "spy", "sixty_forty", "qqq"):
        for k in (20, 30, 40):
            cut = w.month_ends[k]
            short = World(days[:cut + 1], {f: v[:cut + 1] for f, v in w.levels.items() if f != CASH}, w.levels[CASH][:cut + 1])
            assert short.month_ends[:k + 1] == w.month_ends[:k + 1]
            assert etf.RULES[name](short, k) == etf.RULES[name](w, k), name


def test_simulate_trades_the_day_after_the_signal_and_charges_costs():
    days = [date(2024, 1, 30), date(2024, 1, 31), date(2024, 2, 1), date(2024, 2, 2), date(2024, 2, 29), date(2024, 3, 1)]
    spy = [1.0, 1.0, 1.10, 1.21, 1.21, 1.21]  # +10% on Feb 1 and Feb 2
    w = _world(days, {"SPY": spy})
    etf.RULES["_t"] = etf.hold({"SPY": 1.0})
    try:
        sim = etf.simulate(w, "_t", 0)  # the signal of Jan 31
    finally:
        del etf.RULES["_t"]
    assert w.month_ends == [1, 4, 5]
    # trade on Feb 1's close: Feb 1's +10% is not earned, Feb 2's is; buying costs COST of the value
    assert sim["origin"] == 1 and sim["start"] == 2 and sim["values"][1] == 1.0  # worth 1 in cash at Jan 31's close
    assert sim["values"][2] == pytest.approx(1 - etf.COST)
    assert sim["values"][3] == pytest.approx((1 - etf.COST) * 1.10)
    assert sim["turnover"] == [1.0, 0.0]  # Feb 29's signal trades on Mar 1 (nothing to do); Mar 1's would trade after the last day


def test_simulate_moving_to_cash_charges_only_the_fund_sold_and_resets_drift():
    days = _weekdays(date(2024, 1, 1), date(2024, 3, 29))
    spy = _path(len(days), 0.01)
    ief = [1.0] * len(days)
    w = _world(days, {"SPY": spy, "IEF": ief})
    sim = etf.simulate(w, "sixty_forty", 0)
    # second trade: SPY drifted above 60%; turnover is twice the drift, and costs follow it
    t1 = sim["turnover"][1]
    i0, i1 = w.month_ends[0] + 1, w.month_ends[1] + 1
    g = spy[i1] / spy[i0]
    drifted = 0.6 * g / (0.6 * g + 0.4)
    assert t1 == pytest.approx(2 * (drifted - 0.6))
    etf.RULES["_c"] = lambda w_, k: {CASH: 1.0} if k else {"SPY": 1.0}
    try:
        sim = etf.simulate(w, "_c", 0)
    finally:
        del etf.RULES["_c"]
    assert sim["turnover"] == [1.0, 1.0]  # buying SPY, then selling it; cash moves free


def test_simulate_raises_when_a_rule_lacks_data():
    days = _weekdays(date(2024, 1, 1), date(2024, 2, 29))
    w = _world(days, {"SPY": _path(len(days), 0.0)})
    with pytest.raises(etf.MissingData):
        etf.simulate(w, "spy_sma10", 0)


def test_sharpe_drawdown_and_years():
    assert etf.sharpe([0.01, 0.01]) == 0.0
    assert etf.sharpe([0.02, 0.0]) == pytest.approx(0.01 / (0.02 ** 2 / 2) ** 0.5 * 12 ** 0.5)
    assert etf.max_drawdown({0: 1.0, 1: 1.2, 2: 0.9, 3: 1.3}) == pytest.approx(0.9 / 1.2 - 1)
    days = [date(2023, 12, 28), date(2023, 12, 29), date(2024, 1, 2), date(2024, 12, 31), date(2025, 1, 2)]
    w = _world(days, {"SPY": [1.0, 1.1, 1.21, 1.331, 1.331]})
    sim = {"origin": 1, "start": 2, "values": {1: 1.0, 2: 1.1, 3: 1.21, 4: 1.21}}
    assert etf.year_returns(w, sim) == pytest.approx({2024: 0.21, 2025: 0.0})


def test_stationary_bootstrap_is_seeded_and_runs_in_blocks():
    a = etf.stationary_indices(500, 12, random.Random(7))
    assert a == etf.stationary_indices(500, 12, random.Random(7))
    assert len(a) == 500 and all(0 <= i < 500 for i in a)
    steps = sum((b - a_) % 500 == 1 for a_, b in itertools.pairwise(a))
    assert steps > 0.85 * 499  # about 11 in 12 steps continue a block


def test_sharpe_gap_interval_sees_a_clear_gap():
    rng = random.Random(3)
    base = [rng.gauss(0.005, 0.04) for _ in range(240)]
    better = [x + 0.01 for x in base]
    lo, hi = etf.sharpe_gap_interval(better, base, random.Random(5), draws=400)
    assert 0 < lo < hi
    lo, hi = etf.sharpe_gap_interval(base, base, random.Random(5), draws=200)
    assert lo == hi == 0.0


def test_checks_need_all_four():
    sh = {"r": 0.9, "spy": 0.6, "sixty_forty": 0.7}
    halves = [{"r": 0.8, "spy": 0.5, "sixty_forty": 0.6}, {"r": 1.0, "spy": 0.7, "sixty_forty": 0.8}]
    dd = {"r": -0.2, "spy": -0.5, "sixty_forty": -0.3}
    assert all(etf.checks(sh, 0.01, halves, dd, "r").values())
    assert not etf.checks(sh, -0.01, halves, dd, "r")["interval_above_zero"]
    assert not etf.checks({**sh, "sixty_forty": 0.95}, 0.01, halves, dd, "r")["beats_both"]
    assert not etf.checks(sh, 0.01, [halves[0], {**halves[1], "spy": 1.1}], dd, "r")["both_halves"]
    assert not etf.checks(sh, 0.01, halves, {**dd, "r": -0.6}, "r")["smaller_drawdown_than_spy"]


def _synthetic(seed: int = 11) -> World:
    rng = random.Random(seed)
    days = _weekdays(date(2003, 1, 1), date(2012, 12, 31))
    paths = {}
    for f in etf.TICKERS:
        lv, out = 1.0, []
        for _ in days:
            lv *= 1 + rng.gauss(0.0003, 0.012)
            out.append(lv)
        paths[f] = out
    notes = {f: {"first": days[0], "max_gap": 0, "jumps": [], "adj_off": 0} for f in etf.TICKERS}
    return World(days, paths, _path(len(days), 0.0001), notes, days[-1])


def test_evaluate_end_to_end_is_reproducible(monkeypatch):
    monkeypatch.setattr(etf, "END", date(2012, 12, 31))
    monkeypatch.setattr(etf, "BOOTSTRAP", 200)
    monkeypatch.setattr(etf, "POST_FROM", {"spy_sma10": date(2006, 1, 1), "gtaa5": date(2006, 1, 1),
                                           "gem": date(2008, 1, 1), "vol_target": date(2009, 1, 1)})
    a, b = etf.evaluate(_synthetic()), etf.evaluate(_synthetic())
    assert a["problems"] == [] and a == b
    m = a["main"]["gem"]
    assert m["stats"]["gem"]["from"] == "2008-01-01" and set(m["stats"]) == {"gem", "spy", "sixty_forty"}
    assert isinstance(m["passed"], bool) and len(m["interval"]) == 2
    assert set(a["longest"]) == {"spy_sma10", "gtaa5", "gem", "vol_target", "qqq_gold"}
    assert set(a["longest"]["qqq_gold"]["stats"]) == {"qqq_gold", "qqq", "spy", "sixty_forty"}
    assert etf.lines(a)[0].startswith("ETF trend")


def test_data_problems_stop_the_test(monkeypatch):
    monkeypatch.setattr(etf, "END", date(2012, 12, 31))
    w = _synthetic()
    w.notes["EFA"]["jumps"] = [("2005-06-09", -0.6667)]
    r = etf.evaluate(w)
    assert "main" not in r and r["problems"] == ["EFA: a -66.7% day on 2005-06-09"]
    assert "DATA PROBLEMS" in "\n".join(etf.lines(r))
    w = _synthetic()
    monkeypatch.setattr(etf, "END", date(2013, 1, 31))
    assert etf.evaluate(w)["problems"][0].startswith("END")


def test_dividend_counts_on_its_ex_day_and_gaps_are_runs():
    days = [date(2024, 1, d) for d in range(1, 7)]
    fund = {"rows": {d: (100.0, None) for d in days[:3]}, "dividends": {days[1]: 1.0}}
    lv, _ = etf.tr_levels(fund, days[:3])
    assert lv[1] == pytest.approx(1.01) and lv[2] == pytest.approx(1.01)
    fund = {"rows": {days[0]: (1.0, None), days[2]: (1.0, None), days[5]: (1.0, None)}, "dividends": {}}
    assert etf.tr_levels(fund, days)[1]["max_gap"] == 2


def test_momentum_spans_twelve_month_ends():
    w = _monthly_world({"SPY": [0.01 * (i + 1) for i in range(14)]})
    lv = w.levels["SPY"]
    assert etf.momentum(w, "SPY", 13) == pytest.approx(lv[13] / lv[1] - 1)
    assert etf.momentum(w, "SPY", 11) is None


def test_vol_window_is_the_last_vol_days_returns_ending_on_the_signal_day():
    days = _weekdays(date(2024, 1, 1), date(2024, 2, 29))
    w = _world(days, {"SPY": [1.0] * len(days)})
    k = len(w.month_ends) - 1
    i = w.month_ends[k]
    w.levels["SPY"][i] = 1.05  # a move on the signal day is inside the window
    assert etf.rule_vol_target(w, k)["SPY"] < 1
    w.levels["SPY"] = [1.0 if j < i - etf.VOL_DAYS else 1.05 for j in range(len(days))]  # one move just before it
    assert etf.rule_vol_target(w, k) == {"SPY": 1.0}


def test_ties_go_where_the_rules_say():
    w = _monthly_world({"SPY": [0.0] * 10})
    assert etf.rule_spy_sma10(w, 9) == {CASH: 1.0}  # a level equal to its mean is not above it
    base = [0.0] * 12
    w = _monthly_world({"QQQ": base + [0.05], "GLD": base + [0.05]}, cash_month=0.001)
    assert etf.rule_qqq_gold(w, 12) == {"QQQ": 1.0}


def test_percentile_interval_positions():
    assert etf.LEVEL == pytest.approx(0.9875)
    assert etf.percentile_interval(list(range(5000))[::-1]) == (31, 4968)


def test_stationary_bootstrap_wraps_round():
    for seed in range(10):  # one block from wherever it starts, running off the end and on from the start
        assert sorted(etf.stationary_indices(5, 10 ** 9, random.Random(seed))) == [0, 1, 2, 3, 4]


def _fake_compare(ex_rule):
    ex = {"r": ex_rule, "spy": [0.01, 0.0, 0.01, 0.0, 0.0, 0.01, -0.01, 0.0],
          "sixty_forty": [0.005, 0.01, 0.0, 0.01, 0.01, 0.0, 0.0, 0.01]}
    st = {"r": {"sharpe": 1.0, "max_drawdown": -0.1}, "spy": {"sharpe": 0.5, "max_drawdown": -0.3},
          "sixty_forty": {"sharpe": 0.8, "max_drawdown": -0.2}}
    return {"stats": st, "excess": ex, "rolling": {}}


@pytest.mark.parametrize("ex_rule, passes", [
    ([0.02, 0.01, 0.03, 0.02, -0.01, 0.0, 0.01, -0.02], False),  # the second half loses
    ([0.02, 0.01, 0.03, 0.02, 0.02, 0.03, 0.01, 0.02], True),
])
def test_judge_wiring(monkeypatch, ex_rule, passes):
    fake, seen = _fake_compare(ex_rule), {}
    monkeypatch.setattr(etf, "compare", lambda w, name, k0, benches: fake)

    def interval(a, b, rng):
        seen["a"], seen["b"] = a, b
        return 0.1, 0.9
    monkeypatch.setattr(etf, "sharpe_gap_interval", interval)
    monkeypatch.setitem(etf.POST_FROM, "r", date(2000, 3, 1))
    got = etf.judge(_monthly_world({"SPY": [0.0] * 6}), "r", random.Random(0))
    ex = fake["excess"]
    assert got["better"] == "sixty_forty" and seen["a"] is ex["r"] and seen["b"] is ex["sixty_forty"]
    assert got["sharpe_gap"] == pytest.approx(0.2) and got["interval"] == [0.1, 0.9]
    for n in ex:
        assert got["halves"][0][n] == pytest.approx(etf.sharpe(ex[n][:4]))
        assert got["halves"][1][n] == pytest.approx(etf.sharpe(ex[n][4:]))
    assert got["checks"]["both_halves"] is passes and got["passed"] is passes
    assert all(v for k, v in got["checks"].items() if k != "both_halves")


def test_stats_on_a_hand_run():
    w = _monthly_world({"SPY": [0.0, 0.10, -0.05, 0.02]})  # one day a month: Jan 3 to Apr 3, 2000
    sim = etf.simulate(w, "spy", 0)
    assert sim["origin"] == 0 and sim["start"] == 1 and sim["turnover"] == [1.0, 0.0, 0.0]
    rets, cash = etf.monthly(w, sim)
    assert rets == pytest.approx([-etf.COST, -0.05, 0.02]) and cash == [0.0] * 3  # Feb's +10% came before the trade
    st = etf.stats(w, sim)
    growth, years = (1 - etf.COST) * 0.95 * 1.02, 91 / 365.25
    assert st["from"] == "2000-02-03" and st["months"] == 3 and st["growth_of_1"] == pytest.approx(growth)
    assert st["a_year"] == pytest.approx(growth ** (1 / years) - 1)
    assert st["volatility"] == pytest.approx(etf.statistics.stdev(rets) * 12 ** 0.5)
    assert st["sharpe"] == pytest.approx(etf.sharpe(rets))
    assert st["max_drawdown"] == pytest.approx((1 - etf.COST) * 0.95 - 1) and st["worst_month"] == pytest.approx(-0.05)
    assert st["in_funds"] == 1.0 and st["turnover_a_year"] == pytest.approx(1 / years)
    assert st["worst_year"][0] == 2000 and st["worst_year"][1] == pytest.approx(growth - 1)


def test_rolling_share_compounds_every_span():
    assert etf.rolling_share([0.1, 0.0, 0.5, -0.34], [0.0] * 4, 2) == pytest.approx(2 / 3)
    assert etf.rolling_share([0.1], [0.0], 2) is None


def test_longest_starts_at_the_first_signal_beside_the_benchmarks_that_existed():
    w = _monthly_world({"SPY": [0.01] * 15, "IEF": [0.0] * 15})
    w.levels["IEF"][:12] = [None] * 12
    got = etf.longest(w, "spy_sma10", etf.BENCHMARKS)
    assert set(got["stats"]) == {"spy_sma10", "spy"} and got["stats"]["spy"]["from"] == w.days[10].isoformat()


def test_data_problems_name_gaps_missing_funds_stale_cash_and_short_rule_data(monkeypatch):
    monkeypatch.setattr(etf, "END", date(2012, 12, 31))
    w = _synthetic()
    w.notes["VNQ"]["max_gap"] = 6
    w.notes["DBC"]["first"] = None
    w.cash_last = date(2012, 12, 20)
    assert etf.data_problems(w) == ["T-bill rates stop at 2012-12-20, more than 10 days before END",
                                    "VNQ: 6 trading days in a row without a close", "DBC: no closes"]
    monkeypatch.setattr(etf, "BOOTSTRAP", 50)
    monkeypatch.setattr(etf, "POST_FROM", {"spy_sma10": date(2006, 1, 1), "gtaa5": date(2006, 1, 1),
                                           "gem": date(2008, 1, 1), "vol_target": date(2009, 1, 1)})
    w = _synthetic()
    cut = w.days.index(date(2007, 1, 1))
    w.levels["DBC"][:cut] = [None] * cut
    r = etf.evaluate(w)
    assert r["problems"] == ["gtaa5: its funds' data does not reach the signal of 2005-12-30"]
    assert "main" not in r and "longest" not in r


def test_report_names_tbill_rates_that_start_late(monkeypatch, tmp_path, capsys):
    def late(data):
        raise etf.MissingData("no T-bill rate on or before 1993-01-29")
    monkeypatch.setattr(etf, "load", late)
    out = tmp_path / "r.json"
    assert etf.main(["report", "--data", str(tmp_path), "--out", str(out)]) == 1
    assert "DATA PROBLEMS" in capsys.readouterr().out
    assert etf.json.loads(out.read_text())["problems"] == ["no T-bill rate on or before 1993-01-29"]


def test_simulate_accrues_cash_on_the_trade_day_and_charges_costs_on_the_value():
    days = [date(2024, 1, 30), date(2024, 1, 31), date(2024, 2, 1), date(2024, 2, 29), date(2024, 3, 1), date(2024, 3, 4)]
    w = _world(days, {"SPY": [1.0, 1.0, 1.0, 1.1, 1.1, 1.1]}, cash_daily=0.01)
    etf.RULES["_s"] = lambda w_, k: {"SPY": 1.0} if k == 0 else {CASH: 1.0}
    try:
        sim = etf.simulate(w, "_s", 0)
    finally:
        del etf.RULES["_s"]
    bought = 1.01 * (1 - etf.COST)  # Feb 1: a day's cash interest, then the purchase
    assert sim["values"][2] == pytest.approx(bought)
    sold = bought * 1.1 * (1 - etf.COST)  # Mar 1: the sale costs COST of the value sold, not of 1
    assert sim["values"][4] == pytest.approx(sold) and sim["values"][5] == pytest.approx(sold * 1.01)


def test_staleness_boundary(monkeypatch):
    monkeypatch.setattr(etf, "END", date(2012, 12, 31))
    w = _synthetic()
    w.cash_last = date(2012, 12, 21)  # 10 days: fine
    assert etf.data_problems(w) == []
    w.cash_gap = 11
    assert etf.data_problems(w) == ["T-bill rates leave 11 days between two rates"]


def test_rate_gap_counts_from_the_rate_in_force_on_the_first_day():
    rates = {date(2000, 1, 1): 1.0, date(2000, 3, 1): 1.0, date(2000, 3, 3): 1.0, date(2000, 3, 15): 1.0}
    assert etf.rate_gap(rates, date(2000, 3, 2)) == 12  # the 60 days before Mar 1 are before the first day
    assert etf.rate_gap(rates, date(2000, 1, 5)) == 60


def test_load_reads_the_files(monkeypatch, tmp_path):
    monkeypatch.setattr(etf, "END", date(2024, 3, 5))
    (tmp_path / "yahoo").mkdir()
    days = [date(2024, 3, 1), date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6)]
    for t in etf.TICKERS:
        raw = {"chart": {"result": [{"meta": {"gmtoffset": -18000}, "timestamp": [_ts(d) for d in days],
                                     "indicators": {"quote": [{"close": [100.0, 101.0, 102.0, 103.0]}]}}]}}
        (tmp_path / "yahoo" / f"{t}.json").write_text(etf.json.dumps(raw))
    (tmp_path / "DTB3.csv").write_text("observation_date,DTB3\n2024-02-29,5.0\n2024-03-04,.\n2024-03-06,5.1\n")
    w = etf.load(tmp_path)
    assert w.days == days[:3] and w.cash_last == date(2024, 3, 6) and w.cash_gap == 6
    assert w.levels["GLD"] == pytest.approx([1.0, 1.01, 1.02])
    assert w.levels[CASH][1] == pytest.approx(1 + 0.05 * 3 / 360)


def test_worst_year_is_the_lowest():
    days = [date(2022, 12, 30), date(2023, 1, 3), date(2023, 12, 29), date(2024, 1, 2), date(2024, 12, 31)]
    w = _world(days, {"SPY": [1.0, 1.0, 0.8, 0.8, 1.2]})
    st = etf.stats(w, etf.simulate(w, "spy", 0))
    assert st["worst_year"][0] == 2023 and st["worst_year"][1] == pytest.approx(0.8 * (1 - etf.COST) - 1)


def test_report_lines_print_every_section(monkeypatch):
    monkeypatch.setattr(etf, "END", date(2012, 12, 31))
    monkeypatch.setattr(etf, "BOOTSTRAP", 50)
    monkeypatch.setattr(etf, "POST_FROM", {"spy_sma10": date(2006, 1, 1), "gtaa5": date(2006, 1, 1),
                                           "gem": date(2008, 1, 1), "vol_target": date(2009, 1, 1)})
    r = etf.evaluate(_synthetic())
    text = "\n".join(etf.lines(r))
    assert text.count("beat over 3-year spans") == 9 and text.count("  years (") == 9  # 4 main, 5 longest
    st = r["main"]["gem"]["stats"]["gem"]
    assert f"worst year {st['worst_year'][0]} {st['worst_year'][1]:+.1%}" in text
    first = min(st["years"])
    assert f"{first} " + "/".join(f"{r['main']['gem']['stats'][b]['years'][first]:+.0%}" for b in ("gem", "spy", "sixty_forty")) in text
