import json

from kalshi.api import taker_fee_usd
from reports.shadow import CAP, EXIT_BEFORE_S, evaluate

T0 = 1_793_700_000_000


def write(tmp_path, records):
    with open(tmp_path / "events-2026-11-03.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def trade(did, sym, ts, *, action, prob, yes_bid, yes_ask, left, fill_yes, qty, path, close):
    """One desk position as the desk logs it: entry decision and snapshot, opening fill, held-block snapshots, close."""
    sign = 1 if action == "enter_long" else -1
    rows = [
        {"kind": "snapshot", "ts": ts, "decision_id": did, "sym": sym, "phase": "entry", "state": {"contract": {"yes_bid": yes_bid, "yes_ask": yes_ask, "expires_in_s": left}}},
        {"kind": "fill", "ts": ts - 2_000, "decision_id": did, "sym": sym, "side": "buy" if sign > 0 else "sell", "qty": qty, "price": fill_yes, "fee_usd": 0.1, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": ts, "decision_id": did, "sym": sym, "position": {"qty": sign * qty, "entry_price": fill_yes}},
        {"kind": "decision", "ts": ts, "decision_id": did, "sym": sym, "action": action, "executed": True, "prob": prob},
    ]
    for i, (bid, ask, secs) in enumerate(path, start=1):
        rows.append({"kind": "snapshot", "ts": ts + i * 12_000, "decision_id": f"m{i}-{did}", "sym": sym, "phase": "manage", "state": {"contract": {"yes_bid": bid, "yes_ask": ask, "expires_in_s": secs}}})
    end = ts + (len(path) + 1) * 12_000
    rows += [
        {"kind": "fill", "ts": end, "decision_id": did, "sym": sym, "side": "settle", "qty": qty, "fee_usd": 0.0, "realized_pnl_usd": close["realized"]},
        {"kind": "position_closed", "ts": end, "decision_id": did, "sym": sym, "settled": True, "payout": close["payout"]},
    ]
    return rows


def test_the_cap_skips_far_disagreements_and_the_exit_sells_before_the_close(tmp_path):
    records = []
    # near the market (p_yes 0.70 against a 0.75 mid): kept; held to expiry, YES won, the NO bet lost 10 x 0.26
    records += trade("d1", "KXETH15M", T0, action="enter_short", prob=0.30, yes_bid=0.74, yes_ask=0.76, left=500, fill_yes=0.74, qty=10,
                     path=[(0.80, 0.82, 400), (0.88, 0.90, 200), (0.93, 0.95, 170), (0.99, 1.0, 60)], close={"realized": -2.6, "payout": 1.0})
    # far from the market (p_yes 0.20 against a 0.45 mid): the cap skips it
    records += trade("d2", "KXBTC15M", T0 + 600_000, action="enter_long", prob=0.20, yes_bid=0.44, yes_ask=0.46, left=500, fill_yes=0.46, qty=10,
                     path=[(0.40, 0.42, 300)], close={"realized": -4.6, "payout": 0.0})
    # entered with too little time left for the exit rule: capped keeps it, capped_exit skips it
    records += trade("d3", "KXETH15M", T0 + 1_200_000, action="enter_long", prob=0.40, yes_bid=0.34, yes_ask=0.36, left=EXIT_BEFORE_S - 30, fill_yes=0.36, qty=10,
                     path=[(0.50, 0.52, 100)], close={"realized": 6.4, "payout": 1.0})
    write(tmp_path, records)
    report = evaluate(tmp_path, since_ms=T0 - 60_000, registered_ms=T0 + 300_000)
    by_id = {t["id"]: t for t in report["trades"]}
    assert by_id["d1"]["gap"] == 0.05 and by_id["d2"]["gap"] == 0.25 > CAP
    assert by_id["d1"]["desk"] == {"result": "lost", "pnl_usd": -2.7}
    assert by_id["d2"]["capped"] == {"result": "skipped", "pnl_usd": 0.0}
    # sold at the first held block with 3 minutes or less left: NO's sell price is 1 - 0.95 = 0.05, against 0.26 paid
    assert by_id["d1"]["capped_exit"] == {"result": "sold_early", "pnl_usd": round(10 * (0.05 - 0.26) - 0.1 - taker_fee_usd(10, 0.05), 2)}
    assert by_id["d3"]["capped"]["result"] == "won" and by_id["d3"]["capped_exit"] == {"result": "skipped", "pnl_usd": 0.0}
    s = report["strategies"]
    assert s["desk"]["all"]["pnl_usd"] == round(-2.7 - 4.7 + 6.3, 2) and s["capped"]["all"]["skipped"] == 1
    assert s["capped_exit"]["all"]["skipped"] == 2 and s["capped_exit"]["all"]["sold_early"] == 1
    # d1 opened before registration (in-sample); d2 and d3 after it (the test)
    assert s["desk"]["in_sample"]["trades"] == 1 and s["desk"]["test"]["trades"] == 2


def test_the_late_stop_sells_only_bets_still_losing_in_the_last_minute_and_counts_only_after_its_registration(tmp_path):
    from reports.shadow import LATE_STOP_S

    records = []
    # a YES bet at 0.30 still losing with under a minute left: sold at the bid instead of expiring worthless
    records += trade("s1", "KXETH15M", T0, action="enter_long", prob=0.40, yes_bid=0.28, yes_ask=0.30, left=600, fill_yes=0.30, qty=10,
                     path=[(0.20, 0.22, 300), (0.12, 0.14, LATE_STOP_S - 10)], close={"realized": -3.0, "payout": 0.0})
    # a YES bet winning in the last minute: left alone, it settles as the desk had it
    records += trade("s2", "KXBTC15M", T0 + 600_000, action="enter_long", prob=0.60, yes_bid=0.48, yes_ask=0.50, left=600, fill_yes=0.50, qty=10,
                     path=[(0.40, 0.42, 300), (0.80, 0.82, LATE_STOP_S - 20)], close={"realized": 5.0, "payout": 1.0})
    # a NO bet losing at 5 minutes but not yet in the last minute when it settled: unchanged
    records += trade("s3", "KXETH15M", T0 + 1_200_000, action="enter_short", prob=0.40, yes_bid=0.58, yes_ask=0.60, left=600, fill_yes=0.58, qty=10,
                     path=[(0.70, 0.72, 300)], close={"realized": -4.2, "payout": 1.0})
    write(tmp_path, records)
    report = evaluate(tmp_path, since_ms=T0 - 60_000, registered_ms=T0 - 60_000, late_stop_registered_ms=T0 + 300_000)
    by_id = {t["id"]: t for t in report["trades"]}
    assert by_id["s1"]["late_stop"] == {"result": "sold_losing", "pnl_usd": round(10 * (0.12 - 0.30) - 0.1 - taker_fee_usd(10, 0.12), 2)}
    assert by_id["s2"]["late_stop"] == by_id["s2"]["desk"] and by_id["s2"]["late_stop"]["result"] == "won"
    assert by_id["s3"]["late_stop"] == by_id["s3"]["desk"]
    late = report["strategies"]["late_stop"]
    # only s2 and s3 opened after the late stop's registration: its test, and the desk's result on the same bets
    assert late["test"]["trades"] == 2 and late["test"]["sold_losing"] == 0 and late["desk_same"]["trades"] == 2
    assert late["test"]["pnl_usd"] == late["desk_same"]["pnl_usd"] and late["all"]["sold_losing"] == 1
    assert report["strategies"]["capped"]["registered_ms"] == T0 - 60_000 and late["registered_ms"] == T0 + 300_000
