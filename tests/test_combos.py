import json
import math
import random
from datetime import UTC, date, datetime

import pytest

from lab import combos as cb

H = 3_600


def iso(ts):
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def combo(ticker, legs=6, same_game=False, value="0.0000", status="finalized", expected="2026-10-06T04:00:00Z"):
    ls = [{"event_ticker": f"EV{i}", "market_ticker": f"EV{i}-A", "side": "yes"} for i in range(legs)]
    if same_game:
        ls[1] = dict(ls[1], event_ticker="EV0", market_ticker="EV0-B")
    return {"ticker": ticker, "mve_selected_legs": ls, "status": status, "settlement_value_dollars": value, "expected_expiration_time": expected}


def trade(ticker, price, n=10.0, side="yes", at=1_791_000_000):
    return {"ticker": ticker, "yes_price_dollars": f"{price:.4f}", "no_price_dollars": f"{1 - price:.4f}", "count_fp": f"{n:.2f}",
            "taker_side": side, "created_time": iso(at), "trade_id": f"{ticker}-{at}"}


def test_the_maker_fee_is_half_the_taker_rate_rounded_up_to_the_cent_per_fill():
    assert cb.maker_fee(0.08, 10) == 0.03  # 0.035 x 10 x 0.08 x 0.92 = 2.576 cents, charged 3
    assert cb.maker_fee(0.5, 100) == 0.88  # 87.5 cents, charged 88
    assert cb.maker_fee(0.5, 100, coeff=0.0) == 0.0 and cb.maker_fee(0.5, 0) == 0.0


def test_quotes_round_up_to_kalshis_combo_price_grid():
    assert cb.grid_up(0.00431) == 0.0044 and cb.grid_up(0.0812) == 0.082 and cb.grid_up(0.081) == 0.081


def test_leg_bands_and_cross_game():
    assert [cb.band(n) for n in (2, 4, 5, 7, 8, 12, 13, 40)] == ["2-4", "2-4", "5-7", "5-7", "8-12", "8-12", "13+", "13+"]
    assert cb.cross_game(combo("C", 3)) and not cb.cross_game(combo("C", 3, same_game=True)) and not cb.cross_game({"mve_selected_legs": []})


def test_windows_are_seeded_and_inside_the_day():
    a, b = cb.windows_of(date(2026, 10, 5)), cb.windows_of(date(2026, 10, 5))
    start = datetime(2026, 10, 5, tzinfo=UTC).timestamp()
    assert a == b and len(a) == cb.WINDOWS and all(start <= t < start + 86_400 for t in a) and a == sorted(a)
    assert cb.windows_of(date(2026, 10, 6)) != a


def test_the_seller_makes_the_price_when_the_combo_misses_and_loses_the_rest_when_it_comes_in():
    combos = {"MISS": combo("MISS", value="0.0000"), "HIT": combo("HIT", value="1.0000"), "HALF": combo("HALF", value="0.5000")}
    w = [{"day": "2026-10-05", "trades": [trade("MISS", 0.08), trade("HIT", 0.08), trade("HALF", 0.08)]}]
    rows, left = cb.seller_rows(w, combos, {})
    f = cb.maker_fee(0.08, 10)
    by = {r["payout"]: r for r in rows}
    assert by[0.0]["pnl"] == pytest.approx(10 * 0.08 - f) and by[0.0]["stake"] == pytest.approx(10 * 0.92 + f)
    assert by[1.0]["pnl"] == pytest.approx(-10 * 0.92 - f)
    assert by[0.5]["pnl"] == pytest.approx(10 * (0.08 - 0.5) - f)  # a combo settled at a fraction pays that fraction
    assert left == {"no_record": 0, "settles_late": 0, "unsettled": 0, "bad_price": 0}


def test_a_taker_buying_no_leaves_the_seller_holding_yes():
    rows, _ = cb.seller_rows([{"day": "2026-10-05", "trades": [trade("C", 0.30, side="no")]}], {"C": combo("C", value="1.0000")}, {})
    f = cb.maker_fee(0.30, 10)
    assert rows[0]["pnl"] == pytest.approx(10 * 0.70 - f) and rows[0]["stake"] == pytest.approx(10 * 0.30 + f)


def test_combos_expected_to_settle_late_or_not_yet_settled_or_unlisted_are_left_out_and_counted():
    combos = {"LATE": combo("LATE", expected="2026-12-01T00:00:00Z"), "OPEN": combo("OPEN", status="active"), "OK": combo("OK")}
    w = [{"day": "2026-10-05", "trades": [trade("LATE", 0.1), trade("OPEN", 0.1), trade("GONE", 0.1), trade("OK", 0.0), trade("OK", 0.1)]}]
    rows, left = cb.seller_rows(w, combos, {})
    assert len(rows) == 1 and left == {"no_record": 1, "settles_late": 1, "unsettled": 1, "bad_price": 1}


def test_the_bootstrap_resamples_days_and_the_main_test_needs_both_halves_and_enough_days(monkeypatch):
    rows = [{"day": f"2026-10-{d:02d}", "pnl": 1.0, "stake": 10.0} for d in range(1, 31)]
    r = cb.summarize(rows, random.Random(1))
    assert r["days"] == 30 and r["return"] == 0.1 and r["ci95"] == [0.1, 0.1]
    r["halves"] = cb.halves(rows)
    assert not cb.passed(r)  # 30 days < MIN_DAYS
    monkeypatch.setattr(cb, "MIN_DAYS", 20)
    assert cb.passed(r)
    worse = rows[:15] + [dict(x, pnl=-1.0) for x in rows[15:]]
    r = cb.summarize(worse, random.Random(1))
    r["halves"] = cb.halves(worse)
    assert r["halves"][1]["return"] < 0 and not cb.passed(r)


def test_the_calibration_fit_recovers_a_known_curve_and_falls_back_to_the_raw_mid():
    rng = random.Random(3)
    pts = []
    for _ in range(4000):
        m = rng.uniform(0.05, 0.95)
        p = cb._sig(0.3 + 1.2 * cb._logit(m))
        pts.append((m, 1.0 if rng.random() < p else 0.0))
    a, b = cb.fit_calibration(pts)
    assert a == pytest.approx(0.3, abs=0.12) and b == pytest.approx(1.2, abs=0.12)
    assert cb.fit_calibration(pts[:10]) == (0.0, 1.0) and cb.fit_calibration([(0.5, 1.0)] * 50) == (0.0, 1.0)


def leg_candles(t, mid, spread=0.02):
    end = (t // H) * H
    return [{"end_period_ts": end, "yes_bid": {"close_dollars": f"{mid - spread / 2:.4f}"}, "yes_ask": {"close_dollars": f"{mid + spread / 2:.4f}"}}]


def test_a_leg_is_priced_at_its_last_hourly_mid_and_only_from_a_real_two_sided_book():
    t = 1_791_001_800
    assert cb.leg_mid(leg_candles(t, 0.60), t) == pytest.approx(0.60)
    assert cb.leg_mid(leg_candles(t, 0.60, spread=0.2), t) is None  # a 20-cent spread
    assert cb.leg_mid([{"end_period_ts": (t // H) * H, "yes_bid": {"close_dollars": "0.0000"}, "yes_ask": {"close_dollars": "0.0300"}}], t) is None
    assert cb.leg_mid(leg_candles(t - 2 * H, 0.60), t) is None  # over an hour old
    legs = {"EV0-A": leg_candles(t, 0.5), "EV1-A": leg_candles(t, 0.8)}
    c = {"mve_selected_legs": [{"market_ticker": "EV0-A", "side": "yes"}, {"market_ticker": "EV1-A", "side": "no"}]}
    assert cb.leg_prices({"created_time": iso(t)}, c, legs) == [("yes", 0.5), ("no", pytest.approx(0.8))]
    assert cb.leg_prices({"created_time": iso(t)}, c, {"EV0-A": legs["EV0-A"]}) is None


def stage2_world(n_train=40, n_test=40, paid=0.30, hit_every=4):
    """Two-leg cross-game combos: each leg's mid 0.5, so a fair price of 0.25; buyers pay `paid`; every `hit_every`th comes in."""
    windows, combos, legs, results, settled = [], {}, {}, {}, {}
    for k, day in enumerate([date(2026, 9, 13 + j % 18) for j in range(n_train)] + [date(2026, 10, 1 + j % 31) for j in range(n_test)]):
        t = int(datetime(day.year, day.month, day.day, 12, 30, tzinfo=UTC).timestamp())
        tk = f"C{k}"
        hit = k % hit_every == 0
        c = {"ticker": tk, "status": "finalized", "settlement_value_dollars": "1.0000" if hit else "0.0000",
             "expected_expiration_time": "2026-11-05T00:00:00Z",
             "mve_selected_legs": [{"event_ticker": f"E{k}a", "market_ticker": f"E{k}a-X", "side": "yes"},
                                   {"event_ticker": f"E{k}b", "market_ticker": f"E{k}b-X", "side": "yes"}]}
        combos[tk] = c
        for leg in c["mve_selected_legs"]:
            legs[leg["market_ticker"]] = leg_candles(t, 0.5)
            results[leg["market_ticker"]] = 1.0 if hit else float(k % 2)
            settled[leg["market_ticker"]] = t + 6 * H
        windows.append({"day": day.isoformat(), "index": 0, "trades": [trade(tk, paid, n=10, at=t)]})
    return windows, combos, legs, results, settled


def test_stage2_quotes_from_the_legs_and_wins_only_the_prints_it_undercuts():
    windows, combos, legs, results, settled = stage2_world(paid=0.30)
    sample = cb.stage2_sample(windows, combos)
    assert len(sample) == 80
    r = cb.stage2(sample, legs, results, settled, {}, random.Random(1))
    # every training mid is 0.5, so no slope can be fitted and the calibration falls back to the raw mid: fair 0.25,
    # quote 0.275, which beats the 0.30 paid
    assert r["calibration"] == {"a": 0.0, "b": 1.0, "points": 80}
    q = r["quote_rule"]
    assert q["prints"] == 40 and r["unpriced"] == 0
    assert r["by_band"]["2-4"]["paid"] == pytest.approx(0.30) and r["by_band"]["2-4"]["raw_fair"] == pytest.approx(0.25)
    windows, combos, legs, results, settled = stage2_world(paid=0.26)
    r = cb.stage2(cb.stage2_sample(windows, combos), legs, results, settled, {}, random.Random(1))
    assert r["quote_rule"]["prints"] == 0  # 0.275 doesn't beat 0.26


def test_the_calibration_never_sees_a_test_day():
    windows, combos, legs, results, settled = stage2_world()
    a = cb.stage2(cb.stage2_sample(windows, combos), legs, results, settled, {}, random.Random(1))["calibration"]
    for tk in list(results):  # flip every leg's result on the test days only
        k = int(tk[1:].split("a")[0].split("b")[0])
        if k >= 40:
            results[tk] = 1.0 - results[tk]
    b = cb.stage2(cb.stage2_sample(windows, combos), legs, results, settled, {}, random.Random(1))["calibration"]
    assert a == b


def test_stage2_samples_only_cross_game_taker_yes_prints_in_the_first_windows_from_its_start(monkeypatch):
    monkeypatch.setattr(cb, "STAGE2_COMBOS", 2)
    combos = {f"C{i}": combo(f"C{i}") for i in range(5)}
    combos["SG"] = combo("SG", same_game=True)
    w = [{"day": "2026-10-05", "index": 0, "trades": [trade("SG", 0.1), trade("C0", 0.1, side="no"), trade("C1", 0.1), trade("C1", 0.12),
                                                      trade("C2", 0.1)]},
         {"day": "2026-10-05", "index": 2, "trades": [trade("C3", 0.1)]},
         {"day": "2026-09-01", "index": 0, "trades": [trade("C4", 0.1)]}]
    s = cb.stage2_sample(w, combos)
    assert sorted(c["ticker"] for _, c in s) == ["C1", "C2"]


def test_evaluate_runs_end_to_end_and_reports_the_main_test(monkeypatch):
    monkeypatch.setattr(cb, "MIN_DAYS", 5)
    windows, combos, legs, results, settled = stage2_world()
    for c in combos.values():
        c["mve_selected_legs"] = c["mve_selected_legs"] * 3  # six legs: in the main test's band
        c["mve_selected_legs"] = [dict(leg, event_ticker=f"{leg['event_ticker']}{i}") for i, leg in enumerate(c["mve_selected_legs"])]
    r = cb.evaluate({"windows": windows, "combos": combos, "legs": legs, "leg_results": results, "leg_due": settled, "series": {}})
    assert r["main_test"]["prints"] == 80 and r["stage1"]["main"]["days"] > 5
    expect = sum(10 * (0.30 - (1.0 if int(t["trades"][0]["ticker"][1:]) % 4 == 0 else 0.0)) - cb.maker_fee(0.30, 10) for t in windows)
    assert r["stage1"]["main"]["pnl_usd"] == pytest.approx(round(expect, 2))
    json.dumps(r)


def test_fetch_writes_windows_combos_and_leg_prices_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setattr(cb, "DAY_FROM", date(2026, 10, 5))
    monkeypatch.setattr(cb, "DAY_TO", date(2026, 10, 5))
    monkeypatch.setattr(cb, "STAGE2_FROM", date(2026, 9, 13))
    at = cb.windows_of(date(2026, 10, 5))[0]
    c = combo("KXMVEX-1", legs=2)
    asked = []

    class FakeFetcher:
        requests = limited = failed = 0

        def __init__(self, rate, log):
            pass

        def get(self, path, params=None):
            asked.append(path)
            if path == "/historical/cutoff":
                return {"trades_created_ts": "2026-09-13T00:00:00Z", "market_settled_ts": "2026-09-13T00:00:00Z"}
            if path == "/series":
                return {"series": [{"ticker": "KXMVEX", "fee_type": "quadratic", "fee_multiplier": 1}, {"ticker": "OTHER"}]}
            if path == "/markets/trades":
                return {"trades": [trade("KXMVEX-1", 0.2, at=params["max_ts"] - 5), trade("KXNFLGAME-1", 0.5, at=params["max_ts"] - 6)]}
            if path == "/markets":
                return {"markets": [c] if "KXMVEX-1" in params["tickers"] else [{"ticker": t, "status": "finalized", "settlement_value_dollars": "1.0000",
                                                                                    "expected_expiration_time": "2026-10-06T00:00:00Z"}
                                                                                   for t in params["tickers"].split(",")]}
            if path.startswith(("/series/EV0/events/", "/series/EV1/events/")):
                ev = path.split("/")[4]
                return {"market_tickers": [f"{ev}-A"], "market_candlesticks": [leg_candles(at, 0.5)]}
            return {"markets": []}

    monkeypatch.setattr(cb, "Fetcher", FakeFetcher)
    cb.fetch(tmp_path)
    w = json.loads((tmp_path / "windows" / "2026-10-05_0.json").read_text())
    assert [t["ticker"] for t in w["trades"]] == ["KXMVEX-1"] and w["prints"] == 2  # only combo prints are kept
    d = cb.load(tmp_path)
    assert "KXMVEX-1" in d["combos"] and set(d["legs"]) == {"EV0-A", "EV1-A"} and d["leg_results"] == {"EV0-A": 1.0, "EV1-A": 1.0}
    assert math.isclose(cb.leg_mid(d["legs"]["EV0-A"], at), 0.5)
    assert d["series"] == {"KXMVEX": {"ticker": "KXMVEX", "fee_type": "quadratic", "fee_multiplier": 1}}
    assert d["leg_due"]["EV0-A"] == int(datetime(2026, 10, 6, tzinfo=UTC).timestamp())
    n = len(asked)
    cb.fetch(tmp_path)
    assert asked[n:] == ["/historical/cutoff"]  # nothing left to fetch


def test_a_games_winner_total_and_props_are_one_game():
    assert cb.game("KXNFLGAME-26SEP20INDKC") == cb.game("KXNFLTOTAL-26SEP20INDKC") == "26SEP20INDKC"
    c = {"mve_selected_legs": [{"event_ticker": "KXMLBGAME-26SEP201920MILBAL"}, {"event_ticker": "KXMLBKS-26SEP201920MILBAL"},
                               {"event_ticker": "KXNFLGAME-26SEP20INDKC"}]}
    assert not cb.cross_game(c)
    c["mve_selected_legs"][1] = {"event_ticker": "KXMLBGAME-26SEP201905NYYBOS"}
    assert cb.cross_game(c)


def test_the_maker_fee_follows_the_combo_series_fee_type():
    series = {"KXMVECROSSCATEGORY": {"fee_type": "quadratic_with_combo_maker_fees", "fee_multiplier": 1},
              "KXMVECROSSCATEGORY0-SHARD1": {"fee_type": "quadratic", "fee_multiplier": 1},
              "KXMVEOTHER": {"fee_type": "quadratic_with_maker_fees", "fee_multiplier": 2}}
    assert cb.series_of({"event_ticker": "KXMVECROSSCATEGORY0-SHARD1-S20260BFD1960352"}) == "KXMVECROSSCATEGORY0-SHARD1"
    assert cb.series_of({"event_ticker": "KXMVECROSSCATEGORY-S2026VAB3"}) == "KXMVECROSSCATEGORY"
    assert cb.series_of({"ticker": "KXMVEX-1"}) == "KXMVEX"
    assert cb.maker_rate("KXMVECROSSCATEGORY", series) == 0.035 and cb.maker_rate("KXMVECROSSCATEGORY0-SHARD1", series) == 0.0
    assert cb.maker_rate("KXMVEOTHER", series) == 0.035  # 0.0175 x 2
    assert cb.maker_rate("KXMVEUNLISTED", series) == cb.MAKER
    free = dict(combo("KXMVECROSSCATEGORY0-SHARD1-S1-X"), event_ticker="KXMVECROSSCATEGORY0-SHARD1-S1")
    paid = dict(combo("KXMVECROSSCATEGORY-S1-X"), event_ticker="KXMVECROSSCATEGORY-S1")
    rows, _ = cb.seller_rows([{"day": "2026-10-05", "trades": [trade(free["ticker"], 0.08), trade(paid["ticker"], 0.08)]}],
                             {free["ticker"]: free, paid["ticker"]: paid}, series)
    assert rows[0]["pnl"] == pytest.approx(10 * 0.08)  # no maker fee in a quadratic series
    assert rows[1]["pnl"] == pytest.approx(10 * 0.08 - cb.maker_fee(0.08, 10))


def test_a_quote_never_rounds_below_the_grids_lowest_step():
    assert cb.grid_up(0.3 ** 20 * 1.1) == 0.0001 and cb.grid_up(0.0) == 0.0001


def test_the_calibration_skips_a_training_leg_that_settles_in_the_test_period():
    windows, combos, legs, results, settled = stage2_world()
    for tk in list(settled)[:40]:  # half the training legs are games played after the split
        settled[tk] = int(datetime(2026, 10, 3, tzinfo=UTC).timestamp())
    r = cb.stage2(cb.stage2_sample(windows, combos), legs, results, settled, {}, random.Random(1))
    assert r["calibration"]["points"] == 40
    a = r["calibration"]
    for tk in list(settled)[:40]:
        results[tk] = 1.0 - results[tk]  # their results can't move the fit
    assert cb.stage2(cb.stage2_sample(windows, combos), legs, results, settled, {}, random.Random(1))["calibration"] == a


def test_stage2_counts_the_test_prints_it_drops():
    windows, combos, legs, results, settled = stage2_world()
    for k in (40, 41, 42):
        combos[f"C{k}"]["status"] = "active"
    r = cb.stage2(cb.stage2_sample(windows, combos), legs, results, settled, {}, random.Random(1))
    assert r["test_prints_unsettled_or_bad"] == 3 and r["quote_rule"]["prints"] == 37


def test_the_bootstrap_resamples_whole_days():
    # two days with opposite returns: resampling days gives only -0.1, 0 or +0.1; resampling prints would give a narrow band
    rows = [{"day": "2026-10-01", "pnl": 1.0, "stake": 10.0}] * 10 + [{"day": "2026-10-02", "pnl": -1.0, "stake": 10.0}] * 10
    assert cb.summarize(rows, random.Random(5))["ci95"] == [-0.1, 0.1]


def test_records_prefer_a_settled_copy_and_fetch_asks_again_for_an_unsettled_one_and_for_a_wider_leg_span(tmp_path, monkeypatch):
    (tmp_path / "recs").mkdir()
    (tmp_path / "recs" / "00000.json").write_text(json.dumps([combo("A", status="active")]))
    (tmp_path / "recs" / "00001.json").write_text(json.dumps([combo("A", value="1.0000")]))
    assert cb.payout(cb.records(tmp_path / "recs")["A"]) == 1.0
    p = tmp_path / "EV0.json"
    p.write_text(json.dumps({"range": [100, 200], "markets": {"EV0-A": []}}))
    assert cb._covers(p, [("EV0-A", 100 + 2 * H)]) is False  # needs from 100 + 2h - 2h = 100 to 100 + 2h + 1 > 200
    p.write_text(json.dumps({"range": [0, 10 * H], "markets": {"EV0-A": []}}))
    assert cb._covers(p, [("EV0-A", 5 * H)]) and not cb._covers(p, [("EV0-B", 5 * H)])
    p.write_text(json.dumps({"EV0-A": []}))  # the old shape, without its span
    assert not cb._covers(p, [("EV0-A", 5 * H)])


def test_a_resumed_fetch_widens_a_shared_leg_games_span_and_asks_again_for_a_record_saved_unsettled(tmp_path, monkeypatch):
    monkeypatch.setattr(cb, "DAY_FROM", date(2026, 10, 5))
    monkeypatch.setattr(cb, "DAY_TO", date(2026, 10, 5))
    w0, w1 = cb.windows_of(date(2026, 10, 5))[:2]
    a = dict(combo("KXMVEX-A", legs=2), status="active")
    b = combo("KXMVEX-B", legs=2)
    b["mve_selected_legs"][1] = {"event_ticker": "EV2", "market_ticker": "EV2-A", "side": "yes"}  # shares EV0 with A
    state = {"run": 1}
    asked = []

    class FakeFetcher:
        requests = limited = failed = 0

        def __init__(self, rate, log):
            pass

        def get(self, path, params=None):
            asked.append((state["run"], path, dict(params or {})))
            if path == "/historical/cutoff":
                return {"trades_created_ts": "2026-09-13T00:00:00Z", "market_settled_ts": "2026-09-13T00:00:00Z"}
            if path == "/series":
                return {"series": []}
            if path == "/markets/trades":
                if params["max_ts"] == w0:
                    return {"trades": [trade("KXMVEX-A", 0.2, at=w0 - 5)]}
                if params["max_ts"] == w1:
                    return None if state["run"] == 1 else {"trades": [trade("KXMVEX-B", 0.2, at=w1 - 5)]}
                return {"trades": []}
            if path == "/markets":
                tks = params["tickers"].split(",")
                if "KXMVEX-A" in tks or "KXMVEX-B" in tks:
                    return {"markets": [x for x in (dict(a, status="finalized") if state["run"] == 2 else a, b) if x["ticker"] in tks]}
                return {"markets": [{"ticker": t, "status": "finalized", "settlement_value_dollars": "1.0000", "close_time": "2026-10-06T00:00:00Z"}
                                    for t in tks]}
            if "/events/" in path:
                ev = path.split("/")[4]
                return {"market_tickers": [f"{ev}-A"], "market_candlesticks": [[]]}
            return {"markets": []}

    monkeypatch.setattr(cb, "Fetcher", FakeFetcher)
    cb.fetch(tmp_path)
    first = json.loads((tmp_path / "legs" / "EV0.json").read_text())["range"]
    assert first[1] == w0 - 5 + 1 and cb.payout(cb.records(tmp_path / "combos")["KXMVEX-A"]) is None
    state["run"] = 2
    cb.fetch(tmp_path)
    again = [p for r, path, p in asked if r == 2 and path == "/series/EV0/events/EV0/candlesticks"]
    assert len(again) == 1 and again[0]["start_ts"] == first[0] and again[0]["end_ts"] == w1 - 5 + 1
    assert json.loads((tmp_path / "legs" / "EV0.json").read_text())["range"] == [first[0], w1 - 5 + 1]
    assert cb.payout(cb.records(tmp_path / "combos")["KXMVEX-A"]) == 0.0  # the settled copy, asked for again
    assert "0 leg games missing" in (tmp_path / "fetch.log").read_text().strip().splitlines()[-1]


def varied_world():
    """stage2_world with training mids spread from 0.2 to 0.8, so the calibration has a slope to fit."""
    windows, combos, legs, results, due = stage2_world()
    for k in range(40):
        t = cb._ts(windows[k]["trades"][0]["created_time"])
        for j, leg in enumerate(combos[f"C{k}"]["mve_selected_legs"]):
            mid = 0.2 + 0.6 * ((k * 2 + j) % 7) / 6
            legs[leg["market_ticker"]] = leg_candles(t, round(mid, 2))
    return windows, combos, legs, results, due


def test_the_calibration_uses_the_schedule_not_the_outcome_and_a_flip_of_its_own_legs_moves_it():
    windows, combos, legs, results, due = varied_world()
    base = cb.stage2(cb.stage2_sample(windows, combos), legs, results, due, {}, random.Random(1))["calibration"]
    assert base["points"] == 80 and base["b"] != 1.0  # a real fit
    flipped = dict(results)
    for tk in list(due)[:40]:
        flipped[tk] = 1.0 - flipped[tk]
    assert cb.stage2(cb.stage2_sample(windows, combos), legs, flipped, due, {}, random.Random(1))["calibration"] != base  # the check can fail
    late = dict(due)
    for tk in list(due)[:40]:
        late[tk] = int(datetime(2026, 10, 3, tzinfo=UTC).timestamp())  # scheduled after the split, however early it settled
    a = cb.stage2(cb.stage2_sample(windows, combos), legs, results, late, {}, random.Random(1))["calibration"]
    assert a["points"] == 40
    assert cb.stage2(cb.stage2_sample(windows, combos), legs, flipped, late, {}, random.Random(1))["calibration"] == a


def test_load_reads_leg_files_from_the_first_version(tmp_path):
    for sub in ("windows", "combos", "legs", "leg_markets"):
        (tmp_path / sub).mkdir()
    (tmp_path / "legs" / "OLD.json").write_text(json.dumps({"OLD-A": leg_candles(1_791_001_800, 0.5)}))
    (tmp_path / "legs" / "NEW.json").write_text(json.dumps({"range": [0, 1], "markets": {"NEW-A": leg_candles(1_791_001_800, 0.4)}}))
    d = cb.load(tmp_path)
    assert set(d["legs"]) == {"OLD-A", "NEW-A"} and d["series"] == {}
    r = cb.evaluate(d)
    assert r["series_with_fees"] == 0 and "0 combo series with fees" in cb.lines(r)[0]


def test_stage2_charges_the_newcomer_its_series_fee():
    windows, combos, legs, results, due = stage2_world(paid=0.30)
    for c in combos.values():
        c["event_ticker"] = "KXMVEFREE-" + c["ticker"]
    free = cb.stage2(cb.stage2_sample(windows, combos), legs, results, due, {"KXMVEFREE": {"fee_type": "quadratic"}}, random.Random(1))
    paid = cb.stage2(cb.stage2_sample(windows, combos), legs, results, due, {}, random.Random(1))
    assert free["quote_rule"]["prints"] == paid["quote_rule"]["prints"] == 40
    assert free["quote_rule"]["pnl_usd"] - paid["quote_rule"]["pnl_usd"] == pytest.approx(40 * cb.maker_fee(0.275, 10), abs=0.011)


def test_fetch_asks_again_for_a_leg_record_saved_without_a_result(tmp_path, monkeypatch):
    monkeypatch.setattr(cb, "DAY_FROM", date(2026, 10, 5))
    monkeypatch.setattr(cb, "DAY_TO", date(2026, 10, 5))
    w0 = cb.windows_of(date(2026, 10, 5))[0]
    c = combo("KXMVEX-1", legs=2)
    state = {"run": 1}

    class FakeFetcher:
        requests = limited = failed = 0

        def __init__(self, rate, log):
            pass

        def get(self, path, params=None):
            if path == "/historical/cutoff":
                return {"trades_created_ts": "2026-09-13T00:00:00Z", "market_settled_ts": "2026-09-13T00:00:00Z"}
            if path == "/series":
                return {"series": []}
            if path == "/markets/trades":
                return {"trades": [trade("KXMVEX-1", 0.2, at=w0 - 5)]} if params["max_ts"] == w0 else {"trades": []}
            if path == "/markets":
                tks = params["tickers"].split(",")
                if "KXMVEX-1" in tks:
                    return {"markets": [c]}
                done = state["run"] == 2
                return {"markets": [{"ticker": t, "status": "finalized" if done else "active", "settlement_value_dollars": "1.0000" if done else "0",
                                     "expected_expiration_time": "2026-10-06T00:00:00Z"} for t in tks]}
            if "/events/" in path:
                ev = path.split("/")[4]
                return {"market_tickers": [f"{ev}-A"], "market_candlesticks": [[]]}
            return {"markets": []}

    monkeypatch.setattr(cb, "Fetcher", FakeFetcher)
    cb.fetch(tmp_path)
    assert cb.load(tmp_path)["leg_results"] == {}
    state["run"] = 2
    cb.fetch(tmp_path)
    assert cb.load(tmp_path)["leg_results"] == {"EV0-A": 1.0, "EV1-A": 1.0}
