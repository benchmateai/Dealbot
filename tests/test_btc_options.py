"""The Bitcoin options test: prices from Deribit's option surface (lab/btc_options.py), its recording by the gap
recorder, and the paper test that buys whichever venue the options say is cheap (lab/strategies/btc_options.py)."""

import io
import json
import math
from datetime import datetime, timezone

import pytest

from lab.btc_options import YEAR_MS, Deribit, Surface, _ncdf, expiry_ms, fair, iso_ms, surface_record
from lab.gap_recorder import GapRecorder, PolyUS
from lab.rest import Budget, LabRest
from lab.store import LabStore, read_lab
from lab.strategies import btc_options as test
from tests.test_gaps import PAIRS, T0, FakeKalshi, FakePoly

DAY = 86_400_000
T = T0 + 45 * DAY  # a contract settling 45 days after T0


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def flat(vol=0.5, index=75_000.0, days=(30, 60)):
    """A surface with one volatility at every strike of two expiries, read at T0."""
    ks = [20_000 + 5_000 * i for i in range(40)]
    return {"index": index, "expiries": [{"exp": T0 + d * DAY, "f": index, "k": ks, "v": [vol] * len(ks)} for d in days]}


def test_with_one_volatility_the_terminal_price_is_black_scholes_and_the_ranges_add_up_to_one():
    s = Surface(flat(), T0)
    sd = 0.5 * math.sqrt(45 * DAY / YEAR_MS)
    for k in (60_000, 75_000, 90_000):
        d2 = (math.log(75_000 / k) - 0.5 * sd * sd) / sd
        assert s.prob_above(k, T, T0) == pytest.approx(_ncdf(d2), abs=2e-4)
    at = iso(T)
    parts = [fair({"kind": "below", "k": 20_000, "at": at}, s, T0, 75_000.0), fair({"kind": "above", "k": 150_000, "at": at}, s, T0, 75_000.0)]
    parts += [fair({"kind": "range", "lo": lo, "hi": lo + 5_000, "at": at}, s, T0, 75_000.0) for lo in range(20_000, 150_000, 5_000)]
    assert sum(parts) == pytest.approx(1.0, abs=1e-9) and min(parts) >= 0


def test_a_touch_is_about_twice_the_chance_of_finishing_past_the_barrier():
    s = Surface(flat(), T0)
    up, end = s.prob_touch(100_000, T, T0, 75_000.0, up=True), s.prob_above(100_000, T, T0, 75_000.0)
    down, below = s.prob_touch(60_000, T, T0, 75_000.0, up=False), 1 - s.prob_above(60_000, T, T0, 75_000.0)
    assert 1.8 * end < up < 2.2 * end and 1.8 * below < down < 2.2 * below  # the reflection rule, give or take the drift
    assert s.prob_touch(70_000, T, T0, 75_000.0, up=True) == 1.0 and s.prob_touch(80_000, T, T0, 75_000.0, up=False) == 1.0  # already there
    assert fair({"kind": "touch_up", "k": 100_000, "by": iso(T)}, s, T0, 75_000.0) == pytest.approx(up)


def test_volatility_between_two_expiries_interpolates_total_variance_and_moves_with_the_index():
    rec = flat()
    rec["expiries"][0]["v"] = [0.4] * 40
    rec["expiries"][1]["v"] = [0.6] * 40
    s = Surface(rec, T0)
    vol, forward, years = s.vol(75_000, T, T0)
    t1, t2 = 30 * DAY / YEAR_MS, 60 * DAY / YEAR_MS
    assert vol ** 2 * years == pytest.approx(0.4 ** 2 * t1 + (0.6 ** 2 * t2 - 0.4 ** 2 * t1) * (years - t1) / (t2 - t1))
    assert s.vol(75_000, T, T0, spot=82_500.0)[1] == pytest.approx(82_500.0)  # the index rose 10%: so did the forward


def test_the_surface_keeps_each_expiry_s_out_of_the_money_options_inside_its_window():
    rows = []
    for code, fwd in (("8DEC26", 76_000.0), ("25DEC26", 76_500.0), ("10NOV26", 75_100.0)):  # the last expires in under 2 days
        for k in range(60_000, 95_000, 5_000):
            for typ in ("C", "P"):
                iv = 50.0 + (k - 75_000) / 5_000 + (0.5 if typ == "P" else 0.0)
                rows.append({"instrument_name": f"BTC-{code}-{k}-{typ}", "mark_iv": iv, "underlying_price": fwd, "estimated_delivery_price": 75_000.0})
    rows.append({"instrument_name": "ETH-25DEC26-3000-C", "mark_iv": 60.0, "underlying_price": 3_000.0})
    rec = surface_record(rows, None, T0)
    assert [e["exp"] for e in rec["expiries"]] == [expiry_ms("8DEC26"), expiry_ms("25DEC26")] and rec["index"] == 75_000.0
    dec = rec["expiries"][1]
    assert dec["f"] == 76_500.0 and dec["k"] == list(range(60_000, 95_000, 5_000))
    assert dec["v"][dec["k"].index(70_000)] == pytest.approx(0.495) and dec["v"][dec["k"].index(80_000)] == pytest.approx(0.51)  # puts below, calls above
    assert expiry_ms("25DEC26") == iso_ms("2026-12-25T08:00:00Z") and expiry_ms("5JAN27") == iso_ms("2027-01-05T08:00:00Z")


class FakeDeribit:
    """Deribit's two public calls, answered with a small Dec 25 surface."""

    def __init__(self):
        self.urls = []

    def __call__(self, request, timeout=None):
        self.urls.append(request.full_url)
        if "get_index_price" in request.full_url:
            body = {"result": {"index_price": 75_000.0}}
        else:
            body = {"result": [{"instrument_name": f"BTC-25DEC26-{k}-{'C' if k >= 76_000 else 'P'}", "mark_iv": 50.0, "underlying_price": 76_000.0}
                               for k in range(60_000, 95_000, 5_000)]}
        return io.BytesIO(json.dumps(body).encode())


def test_the_gap_recorder_reads_the_index_every_pass_and_the_surface_every_five_minutes(tmp_path):
    clock = {"ms": T0}
    deribit = FakeDeribit()
    rec = GapRecorder(LabStore(tmp_path, stream="gap"), LabRest(FakeKalshi(), Budget(1e9, 1e9)), PolyUS(Budget(1e9, 1e9), opener=FakePoly()), PAIRS,
                      now_ms=lambda: clock["ms"], options=Deribit(Budget(1e9, 1e9), opener=deribit))
    for _ in range(6):
        rec.options_pass()
        clock["ms"] += 60_000
    rec.write_status()
    rec.store.wait_sealed()
    rec.store.close()
    recs = list(read_lab(tmp_path))
    assert sum(r["kind"] == "opt_index" for r in recs) == 6
    assert [r["ts"] - T0 for r in recs if r["kind"] == "opt_surface"] == [0, 300_000]
    assert next(r for r in recs if r["kind"] == "gap_status")["deribit"] == {"requests": 8, "errors": 0, "rate_limited": 0}
    assert all("/api/v2/public/" in u for u in deribit.urls)  # public market data only


def _quote(ts, kb, ka, pb, pa, *, result=None, status="active"):
    k = {"bid": kb, "ask": ka, "bid_size": 500.0, "ask_size": 500.0, "status": status, "result": result, "ts": ts}
    p = {"bid": pb, "ask": pa, "bid_size": 500.0, "ask_size": 500.0, "state": "MARKET_STATE_OPEN", "ts": ts}
    return ("gap_quote", {"pair": "btc-eoy-70k-75k", "k": k, "p": p}, ts)


def _paper_case(tmp_path):
    """One year-end range for an hour: Kalshi 4 cents under the options' price, Polymarket US 4.5 over, then Kalshi
    comes to the options' price and settles YES. Returns the options' price at the first quote."""
    model = {"kind": "range", "lo": 70_000, "hi": 75_000, "at": iso(T)}
    f = fair(model, Surface(flat(), T0), T0 + 1000, 75_000.0)
    items = [("gap_pair", {"pair": "btc-eoy-70k-75k", "kalshi": "K", "polymarket_us": "P", "category": "crypto", "k_fee": 0.0, "p_fee": 0.095,
                           "k_close": T, "p_end": T, "model": model}, T0),
             ("opt_surface", flat(), T0), ("opt_index", {"index": 75_000.0}, T0 + 500),
             _quote(T0 + 1000, round(f - 0.06, 3), round(f - 0.04, 3), round(f + 0.045, 3), round(f + 0.065, 3)),  # Kalshi 4c cheap, Polymarket US 4.5c rich
             ("opt_surface", flat(), T0 + 3_600_000), ("opt_index", {"index": 75_000.0}, T0 + 3_600_500),
             _quote(T0 + 3_601_000, round(f - 0.01, 3), round(f + 0.01, 3), round(f + 0.045, 3), round(f + 0.065, 3)),  # Kalshi came to the options' price
             _quote(T0 + 3_700_000, 1.0, 1.0, round(f + 0.045, 3), round(f + 0.065, 3), result="yes", status="settled")]
    store = LabStore(tmp_path, stream="gap")
    for kind, rec, ts in items:
        store.write(kind, rec, ts_ms=ts)
    store.wait_sealed()
    store.close()
    return f


def test_the_test_buys_the_cheap_side_on_either_venue_marks_it_and_settles_it(tmp_path):
    f = _paper_case(tmp_path)
    early = test.evaluate(tmp_path, since_ms=T0, until_ms=T0 + 3_650_000)["variants"]["hurdle_1c"]  # before Kalshi settles
    k_early = next(e for e in early["entries"] if e["venue"] == "kalshi")
    assert k_early["payout"] is None and k_early["worth_bid"] == pytest.approx(round(f - 0.01, 3)) and 0 < k_early["worth_fair"] < 1
    assert early["by_venue"]["kalshi"]["pnl_at_bids_usd"] == pytest.approx(
        k_early["n"] * (k_early["worth_bid"] - k_early["price"]) - k_early["fee"] - k_early["carry"], abs=0.01)
    assert early["by_venue"]["kalshi"]["pnl_at_options_usd"] == pytest.approx(
        k_early["n"] * (k_early["worth_fair"] - k_early["price"]) - k_early["fee"] - k_early["carry"], abs=0.01)
    r = test.evaluate(tmp_path, since_ms=T0)
    one, three = r["variants"]["hurdle_1c"], r["variants"]["hurdle_3c"]
    assert {(e["venue"], e["side"]) for e in one["entries"]} == {("kalshi", "yes"), ("poly", "no")}
    assert {(e["venue"], e["side"]) for e in three["entries"]} == {("kalshi", "yes")}  # Polymarket US's NO: about 2.6c after its fee and the money
    k_buy = next(e for e in one["entries"] if e["venue"] == "kalshi")
    assert k_buy["n"] == min(500, math.floor(100 / k_buy["price"])) and k_buy["payout"] == 1.0  # the size on offer, at most $100
    assert next(e for e in one["entries"] if e["venue"] == "poly")["payout"] == 0.0
    assert one["by_venue"]["kalshi"]["fees_usd"] == 0.0 and one["by_venue"]["poly"]["fees_usd"] > 0  # Kalshi's year-end ranges are fee-free
    assert one["by_venue"]["kalshi"]["pnl_at_options_usd"] == pytest.approx(k_buy["n"] * (1 - k_buy["price"]), abs=0.05)
    assert one["drift"]["1h"]["positions"] == 2 and one["drift"]["1h"]["gap_after_cents"] < one["drift"]["1h"]["gap_at_entry_cents"]
    d = r["deviation"]
    assert d["kalshi"]["terminal"]["mean_signed_cents"] < 0 < d["poly"]["terminal"]["mean_signed_cents"] and d["kalshi"]["edge_1c_share"] > 0
    assert test.one_line(r).startswith("options test: 1 of 1 Bitcoin pairs priced")


def test_the_shipped_bitcoin_pairs_each_say_what_they_pay_on():
    from lab.gap_recorder import load_pairs
    crypto = [p for p in load_pairs() if p["category"] == "crypto"]
    assert len(crypto) == 44 and all(p.get("model", {}).get("kind") in ("range", "above", "below", "touch_up", "touch_down") for p in crypto)
    ranges = sorted((p["model"]["lo"], p["model"]["hi"]) for p in crypto if p["model"]["kind"] == "range")
    assert ranges[0] == (20_000, 25_000) and ranges[-1] == (145_000, 150_000) and all(b == c for (_, b), (c, _) in zip(ranges, ranges[1:]))


def test_the_dashboard_gets_the_test_s_rows_in_plain_words_and_they_replace_the_old_ones(tmp_path):
    from dashboard.options import label, merge, rows
    _paper_case(tmp_path / "lab")
    r = test.evaluate(tmp_path / "lab", since_ms=T0)
    new = rows(r, now_ms=T0 + 4_000_000, models={"btc-eoy-70k-75k": {"kind": "range", "lo": 70_000, "hi": 75_000, "at": iso(T)}})
    tables = [x["table"] for x in new]
    assert tables.count("opt_summary") == 1 and tables.count("opt_variant") == 3 and tables.count("opt_market") == 1
    summary = new[0]
    assert summary["started"] and summary["kalshi_terminal_median_gap_cents"] is not None and summary["poly_edge_share"] >= 0
    market = next(x for x in new if x["table"] == "opt_market")
    assert market["label"] == "Year end $70k–75k" and market["group"] == "terminal"
    two = next(x for x in new if x["id"] == "hurdle_2c")
    assert two["hurdle_cents"] == 2 and two["positions"] == sum(1 for x in new if x["table"] == "opt_position")
    assert {x["venue"] for x in new if x["table"] == "opt_position"} == {"kalshi", "poly"}
    assert label("btc-high-100k", {"kind": "touch_up", "k": 100_000, "by": "2027-01-01T05:00:00Z"}) == "How high: $100k"
    assert label("btc-low-40k", {"kind": "touch_down", "k": 40_000, "by": "2027-01-01T05:00:00Z"}) == "How low: $40k"
    assert label("btc-100k-by-dec1", {"kind": "touch_up", "k": 100_000, "by": "2026-12-01T05:00:00Z"}) == "Hits $100k by Nov 30"
    assert label("btc-eoy-below-20k", {"kind": "below", "k": 20_000, "at": "x"}) == "Year end under $20k"
    path = tmp_path / "money.json"
    path.write_text(json.dumps([{"table": "summary", "id": "summary"}, {"table": "opt_summary", "id": "options", "stale": True}, {"table": "edesk", "id": "edesk"}]))
    merged = merge(path, new)
    assert [x["table"] for x in merged][:2] == ["summary", "edesk"] and not any(x.get("stale") for x in merged)
    assert json.loads(path.read_text()) == merged


def test_a_reader_can_open_one_stream_s_files_only(tmp_path):
    LabStore(tmp_path, stream="gap").write("gap_quote", {"pair": "x"}, ts_ms=T0)
    rest = LabStore(tmp_path)
    rest.write("book", {"ticker": "K"}, ts_ms=T0)
    rest.close()
    assert {r["kind"] for r in read_lab(tmp_path)} == {"gap_quote", "book"}
    assert [r["kind"] for r in read_lab(tmp_path, streams=("gap",))] == ["gap_quote"]
    assert [r["kind"] for r in read_lab(tmp_path, streams=("",))] == ["book"]


def test_a_yes_and_a_no_on_one_venue_pair_off_free_their_money_and_count_as_a_dollar():
    book = test.Book(0.01)
    book.offer(T0, "m", "kalshi", {"bid": 0.105, "ask": 0.115, "bid_size": 500.0, "ask_size": 500.0}, 0.155, 0.0, 0.1, "terminal")
    book.offer(T0 + 1_800_000, "m", "kalshi", {"bid": 0.195, "ask": 0.205, "bid_size": 500.0, "ask_size": 500.0}, 0.155, 0.0, 0.1, "terminal")
    yes, no = book.pos[("m", "kalshi", "yes")], book.pos[("m", "kalshi", "no")]
    assert (yes["n"], no["n"], yes["paired"], no["paired"]) == (500, 124, 124, 124)  # 124 NO at 80.5c pair off 124 of the 500 YES
    assert book.open_cost() == pytest.approx(376 * 0.115)  # $43.24 tied up, not $157.32
    end = T0 + 30 * DAY
    assert test.Book.carry(no, end) == 0.0  # paired the moment it was bought
    assert test.Book.carry(yes, end) == pytest.approx(0.115 * (376 * 30 * DAY + 124 * 1_800_000) * test.CARRY_RATE / YEAR_MS)
    bids = test.Book.worth(yes)[1] + test.Book.worth(no)[1]
    assert bids == pytest.approx(376 * 0.105 + 124 * 1.0)  # each pair counts at $1, not at the bids' 90c


def test_the_hurdle_counts_kalshi_s_fee_as_charged_rounded_up_per_order():
    q = {"bid": None, "ask": 0.071, "bid_size": None, "ask_size": 1.5}
    small = test.Book(0.01)
    small.offer(T0, "m", "kalshi", q, 0.0874, 0.07, 0.0, "touch")
    assert small.pos == {}  # one contract pays a whole cent of fee, so its edge is 0.6c, under the 1c hurdle
    big = test.Book(0.01)
    big.offer(T0, "m", "kalshi", dict(q, ask_size=500.0), 0.0874, 0.07, 0.0, "touch")
    assert big.pos[("m", "kalshi", "yes")]["fee"] == 2.31  # 500 contracts: the rounding is a rounding


def _touch_case(path, index_path):
    model = {"kind": "touch_up", "k": 100_000, "by": iso(T)}
    store = LabStore(path, stream="gap")
    store.write("gap_pair", {"pair": "btc-high-100k", "kalshi": "K", "polymarket_us": "P", "category": "crypto", "k_fee": 0.07, "p_fee": 0.095,
                             "k_close": T, "p_end": T, "model": model}, ts_ms=T0)
    store.write("opt_surface", flat(index=99_000.0), ts_ms=T0)
    for dt, level in index_path:
        store.write("opt_index", {"index": level}, ts_ms=T0 + dt)
    k = {"bid": 0.98, "ask": 0.99, "bid_size": 500.0, "ask_size": 500.0, "status": "active", "result": None, "ts": T0 + 130_000}
    p = {"bid": 0.98, "ask": 0.99, "bid_size": 500.0, "ask_size": 500.0, "state": "MARKET_STATE_OPEN", "ts": T0 + 130_000}
    store.write("gap_quote", {"pair": "btc-high-100k", "k": k, "p": p}, ts_ms=T0 + 130_000)
    store.wait_sealed()
    store.close()
    return test.evaluate(path, since_ms=T0)


def test_a_barrier_the_index_reached_stays_reached_and_is_not_traded_again(tmp_path):
    quiet = _touch_case(tmp_path / "quiet", [(1_000, 99_000.0), (60_000, 98_700.0), (120_000, 98_500.0)])
    assert quiet["variants"]["hurdle_3c"]["entries"]  # never reached: the options' price is about 0.9, so NO at 2c looks cheap
    touched = _touch_case(tmp_path / "touched", [(1_000, 99_000.0), (60_000, 100_050.0), (120_000, 98_500.0)])
    assert touched["summary"]["touched"] == ["btc-high-100k"] and not any(v["entries"] for v in touched["variants"].values())


def test_with_the_cap_full_a_buy_that_pairs_off_counts_the_money_its_pairing_frees():
    book = test.Book(0.01)
    book.pos[("other", "kalshi", "yes")] = {"n": 26_000, "paired": 0, "price": 0.11155, "payout": None}  # $2,900.30 of the cap elsewhere
    book.offer(T0, "m", "kalshi", {"bid": 0.115, "ask": 0.125, "bid_size": 112.0, "ask_size": 500.0}, 0.095, 0.0, 0.0, "terminal")  # NO at 88.5c
    assert book.pos[("m", "kalshi", "no")]["n"] == 112 and book.open_cost() == pytest.approx(2_900.3 + 112 * 0.885)  # 58 cents of room left
    book.offer(T0 + 1_800_000, "m", "kalshi", {"bid": 0.105, "ask": 0.115, "bid_size": 500.0, "ask_size": 2_000.0}, 0.195, 0.0, 0.0, "terminal")
    yes = book.pos[("m", "kalshi", "yes")]
    assert yes["n"] == 869 and yes["paired"] == 112  # the full $100 at 11.5c: 112 pair off and free $99.12 (without that, 117)
    assert book.open_cost() == pytest.approx(2_900.3 + 757 * 0.115) and book.open_cost() <= test.CAP_USD


def test_a_touch_after_the_market_s_deadline_does_not_count(tmp_path):
    model = {"kind": "touch_up", "k": 100_000, "by": iso(T0 + 60_000)}  # its window ends a minute in
    store = LabStore(tmp_path, stream="gap")
    store.write("gap_pair", {"pair": "btc-high-100k", "kalshi": "K", "polymarket_us": "P", "category": "crypto", "model": model}, ts_ms=T0)
    store.write("opt_surface", flat(index=99_000.0), ts_ms=T0)
    store.write("opt_index", {"index": 100_050.0}, ts_ms=T0 + 120_000)
    store.wait_sealed()
    store.close()
    assert test.evaluate(tmp_path, since_ms=T0)["summary"]["touched"] == []


def test_the_dashboard_marks_a_reached_or_closed_market_and_does_not_colour_it(tmp_path):
    from dashboard.options import label, rows
    r = _touch_case(tmp_path / "touch", [(1_000, 99_000.0), (60_000, 100_050.0), (120_000, 98_500.0)])
    models = {"btc-high-100k": {"kind": "touch_up", "k": 100_000, "by": iso(T)}}
    market = next(x for x in rows(r, now_ms=T0 + 200_000, models=models) if x["table"] == "opt_market")
    assert market["state"] == "reached" and market["fair"] == 1.0 and market["kalshi_mid"] == pytest.approx(0.985)
    assert market["label"] == "How high: $100k"
    _paper_case(tmp_path / "range")  # its last quote is Kalshi's settled market
    r = test.evaluate(tmp_path / "range", since_ms=T0)
    market = next(x for x in rows(r, now_ms=T0 + 3_800_000) if x["table"] == "opt_market")
    assert market["state"] == "closed" and market["ts"] == T0 + 3_601_000 == r["summary"]["priced_until_ms"]  # its last priced quote
    assert market["label"] == "btc-eoy-70k-75k" == label("btc-eoy-70k-75k", None)  # no model recorded: the pair's name, not an error
