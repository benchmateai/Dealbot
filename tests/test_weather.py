from datetime import UTC, date, datetime, timedelta

import pytest

from lab import weather as wx

H = 3_600


def iso(ts):
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def bracket(ticker, kind, lo=None, hi=None, result="no", twc=63, day=date(2026, 10, 5), series="KXHIGHNY"):
    start = wx.day_start(day, wx.SERIES[series][1])
    ev = f"{series}-{day.strftime('%y%b%d').upper()}"
    return {"ticker": f"{ev}-{ticker}", "event_ticker": ev, "series_ticker": series, "strike_type": kind, "floor_strike": lo, "cap_strike": hi,
            "result": result, "expiration_value": f"{twc:.2f}", "open_time": iso(start - 9 * H), "close_time": iso(start + 25 * H),
            "rules_primary": "If the maximum temperature recorded at New York City (CLINYC) ... according to The Weather Company, ..."}


def day_brackets(twc, day, series="KXHIGHNY", base=59):
    """Six brackets like Kalshi's: below base, four 2-degree ranges, above base + 7."""
    ms = [bracket(f"T{base}", "less", hi=base, twc=twc, day=day, series=series)]
    for lo in range(base, base + 8, 2):
        ms.append(bracket(f"B{lo + 0.5:.1f}", "between", lo=lo, hi=lo + 1, twc=twc, day=day, series=series))
    ms.append(bracket(f"T{base + 7}", "greater", lo=base + 7, twc=twc, day=day, series=series))
    for m in ms:
        m["result"] = "yes" if wx.covers(m, twc) else "no"
    return ms


def candle(end, bid, ask, dollars=True):
    k = "close_dollars" if dollars else "close"
    return {"end_period_ts": end, "yes_bid": {k: f"{bid:.4f}"}, "yes_ask": {k: f"{ask:.4f}"}}


def test_event_day_reads_kalshis_ticker():
    assert wx.event_day("KXHIGHNY-26NOV11") == date(2026, 11, 11)
    assert wx.event_day("KXHIGHTDC-26AUG14") == date(2026, 8, 14)
    assert wx.event_day("KXHIGHNY-26XYZ11") is None and wx.event_day("nope") is None


def test_brackets_follow_kalshis_rules():
    assert wx.covers({"strike_type": "greater", "floor_strike": 66}, 67) and not wx.covers({"strike_type": "greater", "floor_strike": 66}, 66)
    assert wx.covers({"strike_type": "less", "cap_strike": 59}, 58) and not wx.covers({"strike_type": "less", "cap_strike": 59}, 59)
    between = {"strike_type": "between", "floor_strike": 63, "cap_strike": 64}
    assert wx.covers(between, 63) and wx.covers(between, 64) and not wx.covers(between, 65)
    assert wx.covers({"strike_type": "between", "floor_strike": 63}, 63) is None


def test_the_climate_day_starts_at_midnight_local_standard_time():
    assert iso(wx.day_start(date(2026, 11, 11), -5)) == "2026-11-11T05:00:00Z"
    assert iso(wx.day_start(date(2026, 8, 14), -8)) == "2026-08-14T08:00:00Z"  # 1 AM daylight time in Los Angeles


def test_the_running_high_uses_readings_published_before_the_entry_and_needs_enough_of_them():
    start = wx.day_start(date(2026, 10, 5), -5)
    t = start + 19 * H
    hourly = [(start + h * H + 51 * 60, 60.0) for h in range(19)]  # :51 past each hour, through 18:51
    assert wx.running_high(hourly + [(start + 15 * H, 62.5)], start, t) == 63  # rounded half up
    assert wx.running_high(hourly + [(t - 60, 70.0)], start, t) == 60  # a reading 1 minute before the entry isn't out yet
    assert wx.running_high(hourly + [(start - 60, 75.0)], start, t) == 60  # yesterday's reading doesn't count
    assert wx.running_high(hourly[:10], start, t) is None  # 10 readings in 19 hours is too few


def test_the_quote_is_the_hourly_candle_that_ended_in_the_hour_up_to_the_entry():
    t = 1_790_000_000
    cs = [candle(t - 2 * H, 0.10, 0.12), candle(t, 0.40, 0.45, dollars=False), candle(t + H, 0.9, 0.95)]
    assert wx.quote(cs, t) == (0.40, 0.45)
    assert wx.quote([candle(t - H, 0.10, 0.12)], t) == (None, None)  # over an hour old


def test_the_offset_model_adds_a_little_to_every_offset_and_sums_to_one():
    m = wx.offset_model([1, 1, 1, 0])
    assert sum(m.values()) == pytest.approx(1.0)
    assert m[1] > m[0] > m[2] > 0 and m[wx.OFFSET_MIN] > 0 and m[wx.OFFSET_MAX] > 0
    assert m[1] == pytest.approx(3.5 / (4 + 0.5 * (wx.OFFSET_MAX - wx.OFFSET_MIN + 1)))


def test_a_bracket_is_bought_only_when_the_model_beats_the_price_and_fee_by_the_margin():
    assert wx.fee(0.07, 0.50) == 0.0175  # $1.75 on 100 contracts, already whole cents
    assert wx.fee(0.07, 0.12) == 0.0074  # 73.92 cents on 100, charged 74
    assert wx.decide(0.5675, 0.48, 0.50, 1.0) == ("yes", 0.5, 0.0175)  # 0.50 + 0.0175 + 0.05
    assert wx.decide(0.5670, 0.48, 0.50, 1.0) is None
    assert wx.decide(0.4325, 0.50, 0.52, 1.0) == ("no", 0.5, 0.0175)  # NO at 1 - the 50c bid
    assert wx.decide(0.99, 0.0, 1.0, 1.0) is None  # no offer on either side
    assert wx.decide(0.57, 0.40, 0.50, 1.0, tight=True) is None  # a 10c-wide book is not tight


def test_a_day_is_bet_at_the_entry_and_settled_on_kalshis_result():
    day = date(2026, 10, 5)
    ms = day_brackets(64, day)  # TWC said 64; the sensors topped out at 63
    ev = {"event": ms[0]["event_ticker"], "series": "KXHIGHNY", "code": "NYC", "offset_h": -5, "day": day, "twc": 64, "markets": ms}
    start = wx.day_start(day, -5)
    t = start + 19 * H
    readings = [(start + h * H + 51 * 60, 63.0) for h in range(19)]
    # the market prices the sensor reading: 63-64 at 88/90c, everything else 2/4c. The model puts TWC at 63, 64 or 65
    # (0.2, 0.6, 0.2): 63-64 is 0.8 and 65-66 is 0.2.
    candles = {m["ticker"]: [candle(t, 0.02, 0.04)] for m in ms}
    candles[ms[3]["ticker"]] = [candle(t, 0.88, 0.90)]  # B63.5
    model = {0: 0.2, 1: 0.6, 2: 0.2}
    b = wx.bets(ev, 19, model, readings, candles, {})
    f12, f04 = wx.fee(0.07, 0.12), wx.fee(0.07, 0.04)
    assert (f12, f04) == (0.0074, 0.0027)
    # NO on 63-64 at 12c (0.2 >= 0.12 + fee + 0.05) loses, as TWC said 64; YES on 65-66 at 4c (0.2 >= 0.04 + fee + 0.05)
    # loses too; the rest have no chance under the model and their 98c NO costs more than 1 less the margin
    assert b["contracts"] == 2
    assert b["stake"] == pytest.approx(0.12 + f12 + 0.04 + f04) and b["pnl"] == pytest.approx(-(0.12 + f12 + 0.04 + f04))
    assert b["bands"]["under 20c"][2] == 2
    late = dict(ev, markets=[dict(m, close_time=iso(t)) for m in ms])
    assert wx.bets(late, 19, model, readings, candles, {}) is None  # no entry at the close


def test_bets_pay_out_on_the_side_bought():
    day = date(2026, 10, 5)
    ms = day_brackets(64, day)
    ev = {"event": ms[0]["event_ticker"], "series": "KXHIGHNY", "code": "NYC", "offset_h": -5, "day": day, "twc": 64, "markets": ms}
    start = wx.day_start(day, -5)
    t = start + 19 * H
    readings = [(start + h * H + 51 * 60, 63.0) for h in range(19)]
    only = ms[3]["ticker"]  # 63-64, which TWC's 64 makes yes
    candles = {only: [candle(t, 0.60, 0.62)]}
    b = wx.bets(ev, 19, {0: 0.5, 1: 0.5}, readings, candles, {})  # the model gives 63-64 a 100% chance
    f = wx.fee(0.07, 0.62)
    assert b["contracts"] == 1 and b["stake"] == pytest.approx(0.62 + f) and b["pnl"] == pytest.approx(1 - 0.62 - f)
    b = wx.bets(ev, 19, {3: 1.0}, readings, candles, {})  # now it gives 63-64 no chance: NO at 40c, which loses
    f = wx.fee(0.07, 0.40)
    assert b["contracts"] == 1 and b["pnl"] == pytest.approx(-0.40 - f)


def test_events_keep_twc_city_days_in_range_and_leave_out_brackets_that_disagree_with_the_result():
    ms = day_brackets(64, date(2026, 10, 5))
    ms[0] = dict(ms[0], result="yes")  # below 59 can't be yes with 64
    old = day_brackets(64, date(2026, 8, 13))
    nws = [dict(m, rules_primary="... according to the National Weather Service ...") for m in day_brackets(64, date(2026, 10, 6))]
    evs, bad = wx.events_of(ms + old + nws)
    assert len(evs) == 1 and bad == 1 and len(evs[0]["markets"]) == 5 and evs[0]["twc"] == 64 and evs[0]["code"] == "NYC"


def synthetic(days, offset, sensor=60):
    """A city-day per date: sensors top out at `sensor`, TWC says sensor + offset, the market prices the sensor reading."""
    markets, candles, readings = [], {}, []
    for day in days:
        twc = sensor + offset
        ms = day_brackets(twc, day, base=sensor - 3)
        markets += ms
        start = wx.day_start(day, -5)
        readings += [(start + h * H + 51 * 60, float(sensor)) for h in range(24)]
        for hour in wx.ENTRY_HOURS:
            t = start + hour * H
            for m in ms:
                yes_at_sensor = wx.covers(m, sensor)
                bid, ask = (0.90, 0.92) if yes_at_sensor else (0.03, 0.05)
                candles.setdefault(m["ticker"], []).append(candle(t, bid, ask))
    return markets, candles, sorted(readings)


def test_the_model_learns_only_from_training_days_and_the_main_test_needs_enough_events(monkeypatch):
    train = [wx.DAY_FROM + timedelta(days=i) for i in range((wx.SPLIT - wx.DAY_FROM).days)]
    test = [wx.SPLIT + timedelta(days=i) for i in range((wx.DAY_TO - wx.SPLIT).days + 1)]
    m1, c1, r1 = synthetic(train, 2)  # TWC runs 2 above the sensors on training days
    m2, c2, r2 = synthetic(test, 2)
    d = {"series": {}, "markets": m1 + m2, "candles": {**c1, **c2}, "cli": {"NYC": {}}, "asos": {"NYC": sorted(r1 + r2)}}
    r = wx.evaluate(d)
    main = r["by_hour"][str(wx.MAIN_HOUR)]
    assert r["train_events"] == len(train) and r["test_events"] == len(test)
    assert main["training_days_used"] == len(train)
    assert main["offsets"]["2"] == pytest.approx((len(train) + wx.PSEUDO) / (len(train) + wx.PSEUDO * (wx.OFFSET_MAX - wx.OFFSET_MIN + 1)), abs=1e-4)
    assert main["return"] > 0 and main["events"] == len(test)
    assert not r["main_test"]["passed"]  # 41 test days is under MIN_EVENTS
    monkeypatch.setattr(wx, "MIN_EVENTS", 10)
    assert wx.passed(main)
    # if test days ran differently from training (TWC equal to the sensors), the model's buys lose
    m3, c3, r3 = synthetic(test, 0)
    d = {"series": {}, "markets": m1 + m3, "candles": {**c1, **c3}, "cli": {"NYC": {}}, "asos": {"NYC": sorted(r1 + r3)}}
    r = wx.evaluate(d)
    assert max(r["by_hour"][str(wx.MAIN_HOUR)]["offsets"].items(), key=lambda kv: kv[1])[0] == "2"
    assert r["by_hour"][str(wx.MAIN_HOUR)]["return"] < 0


def test_the_settlement_gap_is_counted_against_the_nws_report_and_the_sensor_high():
    day = date(2026, 10, 5)
    ms = day_brackets(64, day)
    evs, _ = wx.events_of(ms)
    start = wx.day_start(day, -5)
    d = {"cli": {"NYC": {"2026-10-05": 63.0}}, "asos": {"NYC": [(start + h * H, 62.0) for h in range(24)] + [(start + 24 * H, 80.0)]}}
    g = wx.gap(evs, d)
    assert g["vs_nws_report"]["off_by_1"] == 1.0 and g["vs_nws_report"]["twc_higher"] == 1.0
    assert g["vs_sensor_high"]["off_by_2_plus"] == 1.0  # 64 against 62; the next day's midnight reading isn't counted


def test_sensor_csv_skips_missing_readings():
    rows = wx.parse_asos("station,valid,tmpf\nNYC,2026-11-11 00:51,57.00\nNYC,2026-11-11 01:51,M\n")
    assert rows == [(int(datetime(2026, 11, 11, 0, 51, tzinfo=UTC).timestamp()), 57.0)]


def test_fetch_stamps_the_series_stops_paging_the_archive_at_old_days_and_saves_prices_and_weather(tmp_path, monkeypatch):
    monkeypatch.setattr(wx, "SERIES", {"KXHIGHNY": ("NYC", -5)})
    live = {k: v for k, v in bracket("B63.5", "between", lo=63, hi=64, result="yes", day=date(2026, 10, 5)).items() if k != "series_ticker"}
    hist = {k: v for k, v in bracket("B63.5", "between", lo=63, hi=64, result="yes", day=date(2026, 8, 20)).items() if k != "series_ticker"}
    old = dict(hist, ticker="KXHIGHNY-26AUG01-B63.5", event_ticker="KXHIGHNY-26AUG01")
    asked = []

    class FakeFetcher:
        requests = limited = failed = 0

        def __init__(self, rate, log):
            pass

        def get(self, path, params=None):
            asked.append((path, (params or {}).get("cursor")))
            if path == "/series":
                return {"series": [{"ticker": "KXHIGHNY", "fee_multiplier": 1}, {"ticker": "OTHER"}]}
            if path == "/markets":
                return {"markets": [live], "cursor": ""}
            if path == "/historical/markets":
                return {"markets": [hist], "cursor": "p2"} if not params.get("cursor") else {"markets": [old], "cursor": "p3"}
            if path.endswith(f"/events/{live['event_ticker']}/candlesticks"):
                return {"market_tickers": [live["ticker"]], "market_candlesticks": [[candle(1, 0.5, 0.52)]]}
            if path == f"/historical/markets/{hist['ticker']}/candlesticks":
                return {"candlesticks": [candle(2, 0.4, 0.42, dollars=False)]}
            return None

    monkeypatch.setattr(wx, "Fetcher", FakeFetcher)
    monkeypatch.setattr(wx, "_iem", lambda url, log: '{"results": [{"valid": "2026-10-05", "high": 63}]}' if "cli.py" in url
                        else "station,valid,tmpf\nNYC,2026-10-05 18:51,62.00\n")
    wx.fetch(tmp_path)
    import json
    saved = json.loads((tmp_path / "markets" / "KXHIGHNY.json").read_text())
    assert {m["ticker"]: (m["series_ticker"], m["_src"]) for m in saved} == {live["ticker"]: ("KXHIGHNY", "live"), hist["ticker"]: ("KXHIGHNY", "historical")}
    assert ("/historical/markets", "p3") not in asked  # page 2 was all before DAY_FROM
    assert json.loads((tmp_path / "series.json").read_text()) == [{"ticker": "KXHIGHNY", "fee_multiplier": 1}]
    assert json.loads((tmp_path / "candles" / f"{live['event_ticker']}.json").read_text())[live["ticker"]][0]["end_period_ts"] == 1
    assert json.loads((tmp_path / "candles" / f"{hist['event_ticker']}.json").read_text())[hist["ticker"]][0]["end_period_ts"] == 2
    d = wx.load(tmp_path)
    assert d["cli"]["NYC"] == {"2026-10-05": 63.0} and len(d["asos"]["NYC"]) == 1 and len(d["markets"]) == 2
    n = len(asked)
    wx.fetch(tmp_path)  # resumes: nothing left to ask Kalshi for
    assert len(asked) == n


def test_coverage_counts_hours_with_a_reading_not_readings():
    start = wx.day_start(date(2026, 10, 5), -5)
    t = start + 19 * H
    burst = [(start + i * 9 * 60, 55.0) for i in range(15)]  # 15 special reports in the first 2 hours 15 minutes
    assert wx.running_high(burst, start, t) is None
    most = [(start + h * H + 51 * 60, 60.0) for h in range(14)] + [(start + 13 * H + 55 * 60, 61.0)]  # 14 of 19 hours
    assert wx.running_high(most, start, t) is None
    enough = [(start + h * H + 51 * 60, 60.0) for h in range(15)]  # 15 of 19 hours
    assert wx.running_high(enough, start, t) == 60


def test_a_day_settled_with_a_text_figure_is_kept_for_bets_but_not_for_the_model_or_the_gap():
    day = date(2026, 10, 22)
    ms = [dict(m, expiration_value="70° to 71°") for m in day_brackets(70, day, base=67)]
    evs, bad = wx.events_of(ms)
    assert len(evs) == 1 and evs[0]["twc"] is None and len(evs[0]["markets"]) == 6 and bad == 0
    assert wx.gap(evs, {"cli": {"NYC": {"2026-10-22": 70.0}}, "asos": {}})["vs_nws_report"]["days"] == 0
    split = day_brackets(70, day, base=67)
    split[0] = dict(split[0], expiration_value="71.00")  # brackets disagreeing on the figure
    evs, bad = wx.events_of(split)
    assert evs == [] and bad == 6
    train = [dict(m, expiration_value="x") for m in day_brackets(60, wx.DAY_FROM, base=57)]
    start = wx.day_start(wx.DAY_FROM, -5)
    readings = [(start + h * H + 51 * 60, 60.0) for h in range(24)]  # a full day, so a running high exists at every hour
    r = wx.evaluate({"series": {}, "markets": train, "candles": {}, "cli": {}, "asos": {"NYC": readings}})
    assert r["events_without_figure"] == 1 and r["by_hour"][str(wx.MAIN_HOUR)]["training_days_used"] == 0


def test_an_empty_weather_download_is_not_saved_and_is_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(wx, "SERIES", {"KXHIGHNY": ("NYC", -5)})

    class NoKalshi:
        requests = limited = failed = 0

        def __init__(self, rate, log):
            pass

        def get(self, path, params=None):
            return {"series": []} if path == "/series" else {"markets": [], "cursor": ""}

    calls = []
    monkeypatch.setattr(wx, "Fetcher", NoKalshi)
    monkeypatch.setattr(wx, "_iem", lambda url, log: calls.append(url) or ('{"results": []}' if "cli.py" in url else "station,valid,tmpf\n"))
    wx.fetch(tmp_path)
    assert calls and not (tmp_path / "cli" / "NYC.json").exists() and not (tmp_path / "asos" / "NYC.csv").exists()
    assert "1 stations missing weather data" in (tmp_path / "fetch.log").read_text()
    (tmp_path / "asos" / "NYC.csv").write_text("station,valid,tmpf\n")  # empty files left by an earlier run
    (tmp_path / "cli" / "NYC.json").write_text('{"results": []}')
    n = len(calls)
    wx.fetch(tmp_path)
    assert len(calls) == n + 2  # both asked for again
    assert (tmp_path / "fetch.log").read_text().strip().splitlines()[-1].count("1 stations missing weather data") == 1
