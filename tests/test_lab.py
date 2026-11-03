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
    store.write("x", {"n": 2}, ts_ms=T0 + H + 1)  # a new hour seals the old one
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
