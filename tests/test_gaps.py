"""The gap recorder and report (lab/gap_recorder.py, lab/gap_report.py): Kalshi beside Polymarket US."""

import io
import json
import urllib.parse

import pytest

from lab.gap_recorder import GapRecorder, PolyUS, kalshi_quote, load_pairs, poly_quote
from lab.gap_report import locks, report
from lab.rest import Budget, LabRest
from lab.store import LabStore, read_lab

T0 = 1_794_172_800_000  # 2026-11-08T21:20:00Z
PAIRS = [{"id": "sb-sf", "kalshi": "KXSB-27-SF", "polymarket_us": "tec-nfl-champ-sf", "category": "sports", "rules": "same game"},
         {"id": "fed-h25", "kalshi": "KXFEDDECISION-26DEC-H25", "polymarket_us": "rdc-fed-hike25", "category": "economic", "rules": "same meeting"}]


class FakeKalshi:
    def __init__(self):
        self.quotes = {"KXSB-27-SF": ("0.1400", "0.1500"), "KXFEDDECISION-26DEC-H25": ("0.7600", "0.7700")}
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(path)
        if path.startswith("/series/"):
            return {"series": {"fee_multiplier": 1}}
        tickers = (params or {}).get("tickers", "").split(",")
        return {"markets": [{"ticker": t, "yes_bid_dollars": self.quotes[t][0], "yes_ask_dollars": self.quotes[t][1], "yes_bid_size_fp": "100.00",
                             "yes_ask_size_fp": "200.00", "status": "active", "close_time": "2027-02-15T00:00:00Z",
                             "expected_expiration_time": "2027-02-15T00:00:00Z"} for t in tickers if t in self.quotes]}


class FakePoly:
    """Polymarket US's public endpoints, answered from a dict of books."""

    def __init__(self):
        self.books = {"tec-nfl-champ-sf": ([("0.1600", "50")], [("0.1700", "80")]), "rdc-fed-hike25": ([("0.7500", "10")], [("0.7700", "10")])}
        self.urls = []

    def __call__(self, request, timeout=None):
        url = request.full_url
        self.urls.append(url)
        parts = urllib.parse.urlparse(url)
        if parts.path == "/v1/markets":
            slugs = urllib.parse.parse_qs(parts.query).get("slug", [])
            body = {"markets": [{"slug": s, "feeCoefficient": 0.095, "endDate": "2027-03-01T04:00:00Z"} for s in slugs]}
        else:
            slug = parts.path.split("/")[3]
            bids, offers = self.books[slug]
            body = {"marketData": {"marketSlug": slug, "bids": [{"px": {"value": p}, "qty": q} for p, q in bids],
                                   "offers": [{"px": {"value": p}, "qty": q} for p, q in offers], "state": "MARKET_STATE_OPEN"}}
        return io.BytesIO(json.dumps(body).encode())


def _recorder(tmp_path, clock):
    kalshi, poly = FakeKalshi(), FakePoly()
    rec = GapRecorder(LabStore(tmp_path, stream="gap"), LabRest(kalshi, Budget(1e9, 1e9)), PolyUS(Budget(1e9, 1e9), opener=poly), PAIRS,
                      now_ms=lambda: clock["ms"])
    return rec, kalshi, poly


def test_quotes_read_each_venue_s_best_prices_and_leave_empty_sides_empty():
    assert kalshi_quote({"yes_bid_dollars": "0.0000", "yes_ask_dollars": "1.0000", "status": "active"}, T0) == \
        {"bid": None, "ask": None, "bid_size": None, "ask_size": None, "status": "active", "ts": T0}
    book = {"marketData": {"bids": [{"px": {"value": "0.0100"}, "qty": "5"}, {"px": {"value": "0.0200"}, "qty": "7"}],
                           "offers": [{"px": {"value": "0.0400"}, "qty": "0"}, {"px": {"value": "0.0300"}, "qty": "9"}], "state": "MARKET_STATE_OPEN"}}
    q = poly_quote(book, T0)
    assert (q["bid"], q["bid_size"], q["ask"], q["ask_size"]) == (0.02, 7.0, 0.03, 9.0)  # an empty level is no quote


def test_the_recorder_writes_each_pair_with_its_fees_then_quotes_only_when_they_change(tmp_path):
    clock = {"ms": T0}
    rec, kalshi, poly = _recorder(tmp_path, clock)
    rec.describe()
    rec.poll()
    clock["ms"] += 60_000
    rec.poll()                                    # nothing moved: nothing written
    kalshi.quotes["KXSB-27-SF"] = ("0.1500", "0.1600")
    clock["ms"] += 60_000
    rec.poll()                                    # Kalshi moved in one pair: one record
    clock["ms"] += 601_000
    rec.poll()                                    # the heartbeat: both again
    rec.store.wait_sealed()
    rec.store.close()
    recs = list(read_lab(tmp_path))
    pairs = {r["pair"]: r for r in recs if r["kind"] == "gap_pair"}
    assert pairs["sb-sf"]["k_fee"] == 0.07 and pairs["sb-sf"]["p_fee"] == 0.095 and pairs["sb-sf"]["p_end"] and pairs["sb-sf"]["k_close"]
    quotes = [(r["ts"] - T0, r["pair"]) for r in recs if r["kind"] == "gap_quote"]
    assert quotes == [(0, "sb-sf"), (0, "fed-h25"), (120_000, "sb-sf"), (721_000, "sb-sf"), (721_000, "fed-h25")]
    first = next(r for r in recs if r["kind"] == "gap_quote")
    assert (first["k"]["bid"], first["k"]["ask"], first["p"]["bid"], first["p"]["ask"], first["p"]["bid_size"]) == (0.14, 0.15, 0.16, 0.17, 50.0)
    assert all(not u.startswith("https://gateway.polymarket.us/v1/orders") for u in poly.urls)  # public market data only


def test_pairs_must_be_unique_and_the_shipped_list_is():
    shipped = load_pairs()
    assert len(shipped) >= 100 and {p["category"] for p in shipped} <= {"crypto", "economic", "political", "sports"}


def test_a_series_kalshi_charges_no_fee_on_counts_as_free_not_as_unknown(tmp_path):
    clock = {"ms": T0}
    kalshi, poly = FakeKalshi(), FakePoly()
    kalshi.quotes["KXBTCY-27JAN0100-B67500"] = ("0.1360", "0.1530")
    poly.books["cpc-btc-eoy-67500"] = ([("0.1100", "40")], [("0.1200", "40")])
    free = {"id": "btc-eoy-65k-70k", "kalshi": "KXBTCY-27JAN0100-B67500", "polymarket_us": "cpc-btc-eoy-67500", "category": "crypto", "rules": "same minute"}
    listed = kalshi.get

    def get(path, params=None):  # Kalshi publishes a fee multiplier of 0 on its year-end Bitcoin ranges
        return {"series": {"fee_multiplier": 0}} if path == "/series/KXBTCY" else listed(path, params)
    kalshi.get = get
    rec = GapRecorder(LabStore(tmp_path, stream="gap"), LabRest(kalshi, Budget(1e9, 1e9)), PolyUS(Budget(1e9, 1e9), opener=poly), PAIRS + [free],
                      now_ms=lambda: clock["ms"])
    rec.describe()
    rec.poll()
    clock["ms"] += 300_000
    rec.write_status(note="end")
    rec.store.wait_sealed()
    rec.store.close()
    pairs = {r["pair"]: r for r in read_lab(tmp_path) if r["kind"] == "gap_pair"}
    assert pairs["btc-eoy-65k-70k"]["k_fee"] == 0.0 and pairs["sb-sf"]["k_fee"] == 0.07
    row = next(r for r in report(tmp_path)["pairs"] if r["pair"] == "btc-eoy-65k-70k")
    # NO on Kalshi at its 13.6-cent YES bid and YES on Polymarket US at 12 cents: 1.6 cents less Polymarket US's fee alone
    assert row["best"]["net"] == pytest.approx(0.016 - 0.095 * 0.12 * 0.88, abs=1e-4)


class Refusing:
    """Kalshi refusing the first request of each kind once, as its shared public limit does (LabRest then
    returns None after waiting out the refusal)."""

    def __init__(self, inner):
        self.inner, self.refused = inner, set()

    def get(self, path, params=None):
        kind = path.split("/")[1]
        if kind not in self.refused:
            self.refused.add(kind)
            return None
        return self.inner.get(path, params)

    def counters(self):
        return self.inner.counters()


def test_a_refused_lookup_is_tried_again_so_no_pair_loses_its_fee_or_settlement_date(tmp_path):
    kalshi, poly = FakeKalshi(), FakePoly()
    rec = GapRecorder(LabStore(tmp_path, stream="gap"), Refusing(LabRest(kalshi, Budget(1e9, 1e9))), PolyUS(Budget(1e9, 1e9), opener=poly), PAIRS,
                      now_ms=lambda: T0)
    rec.describe()
    rec.store.wait_sealed()
    rec.store.close()
    pairs = [r for r in read_lab(tmp_path) if r["kind"] == "gap_pair"]
    assert len(pairs) == 2 and all(r["k_close"] and r["k_fee"] == 0.07 for r in pairs)


def test_a_pair_listed_twice_is_refused(tmp_path):
    path = tmp_path / "pairs.json"
    path.write_text(json.dumps(PAIRS + [dict(PAIRS[0], id="again")]))
    with pytest.raises(ValueError):
        load_pairs(path)


def test_a_lock_pays_only_after_both_taker_fees():
    k = {"bid": 0.14, "ask": 0.15, "bid_size": 100.0, "ask_size": 200.0, "status": "active", "ts": T0}
    p = {"bid": 0.16, "ask": 0.17, "bid_size": 50.0, "ask_size": 80.0, "state": "MARKET_STATE_OPEN", "ts": T0 + 3000}
    lk = locks(k, p, 0.07, 0.095)
    gross, net, size = lk["a"]                   # buy YES on Kalshi at 0.15, short on Polymarket US at 0.16
    assert gross == pytest.approx(0.01) and net == pytest.approx(0.01 - 0.07 * 0.15 * 0.85 - 0.095 * 0.16 * 0.84) and size == 50.0
    assert lk["b"][0] == pytest.approx(0.14 - 0.17) and lk["mid_gap"] == pytest.approx(0.165 - 0.145)
    assert locks(k, dict(p, ts=T0 + 30_000), 0.07, 0.095) is None          # read too far apart
    assert locks(dict(k, status="closed"), p, 0.07, 0.095) is None          # a venue not trading


def _write(tmp_path, items):
    store = LabStore(tmp_path, stream="gap")
    for kind, rec, ts in sorted(items, key=lambda x: x[2]):
        store.write(kind, rec, ts_ms=ts)
    store.wait_sealed()
    store.close()


def _quote(ts, k, p):
    kb, ka = k
    pb, pa = p
    return ("gap_quote", {"pair": "x", "k": {"bid": kb, "ask": ka, "bid_size": 1000.0, "ask_size": 1000.0, "status": "active", "ts": ts},
                          "p": {"bid": pb, "ask": pa, "bid_size": 1000.0, "ask_size": 1000.0, "state": "MARKET_STATE_OPEN", "ts": ts}}, ts)


def test_the_report_times_the_gaps_and_charges_the_money_tied_up(tmp_path):
    soon, late = T0 + 2 * 86_400_000, T0 + int(2 * 365.25 * 86_400_000)
    for name, settles in (("soon", soon), ("late", late)):
        items = [("gap_pair", {"pair": "x", "kalshi": "K", "polymarket_us": "P", "category": "economic", "k_fee": 0.07, "p_fee": 0.095,
                               "k_close": settles, "p_end": settles}, T0),
                 _quote(T0, (0.50, 0.51), (0.50, 0.51)),             # level: no lock
                 _quote(T0 + 60_000, (0.50, 0.51), (0.57, 0.58)),    # 6 cents through Kalshi's ask, for 3 minutes (4 would not pay:
                 #                                                     the two taker fees come to about 4.1 cents here)
                 _quote(T0 + 240_000, (0.50, 0.51), (0.50, 0.51)),
                 ("gap_status", {"note": "end"}, T0 + 300_000)]       # the last moment holds until here
        _write(tmp_path / name, items)
    soon_r, late_r = report(tmp_path / "soon"), report(tmp_path / "late")
    row = soon_r["pairs"][0]
    assert row["hours"] == round(300 / 3600, 2) and row["crossed_share"] == pytest.approx(180 / 300, abs=1e-3)
    assert row["paying_share"] == row["paying_after_carry_share"] == pytest.approx(180 / 300, abs=1e-3)
    assert row["lasting_episodes"] == 1 and row["longest_episode_s"] == 180
    assert row["best"]["net"] == pytest.approx(0.06 - 0.07 * 0.51 * 0.49 - 0.095 * 0.57 * 0.43, abs=1e-4)
    # the same gap two years from settlement ties up 94 cents a contract at 4% a year: about 7.5 cents, more than it pays
    late_row = late_r["pairs"][0]
    assert late_row["paying_share"] > 0 and late_row["paying_after_carry_share"] == 0 and late_row["lasting_episodes"] == 0
    assert late_r["summary"]["pairs_seen"] == 1 and soon_r["summary"]["lasting_episodes"] == 1
    assert soon_r["summary"]["categories"]["economic"]["paying_share"] == soon_r["summary"]["paying_share"] == row["paying_share"]
    assert late_r["summary"]["categories"]["economic"]["paying_after_carry_share"] == 0
