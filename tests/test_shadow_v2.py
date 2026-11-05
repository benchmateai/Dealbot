"""The owner's two paper rules on desk v2's own bets (reports/shadow_v2.py)."""

import json

import pytest

from kalshi.api import taker_fee_usd
from reports.shadow_v2 import FAVOURITE_ABOVE, UNDERDOG_BELOW, evaluate

V2 = 1_793_852_388_000          # desk v2's first block
REG = V2 + 3_600_000            # the rules count bets from here on


def write(tmp_path, records):
    with open(tmp_path / "events-2026-11-05.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def bet(did, ticker, ts, *, yes, price, qty=10, sold_at=None, payout):
    """One v2 position as the desk logs it; sold_at is the side's sell price when the late stop sold it."""
    sign = 1 if yes else -1
    fill_yes = price if yes else 1.0 - price
    fee = taker_fee_usd(qty, price)
    rows = [
        {"kind": "snapshot", "ts": ts, "decision_id": did, "sym": "KXETH15M", "phase": "entry",
         "state": {"contract": {"ticker": ticker, "yes_bid": fill_yes - 0.01, "yes_ask": fill_yes + 0.01, "expires_in_s": 400}}},
        {"kind": "fill", "ts": ts - 1_000, "decision_id": did, "sym": "KXETH15M", "side": "buy" if yes else "sell", "qty": qty, "price": fill_yes, "fee_usd": fee, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": ts, "decision_id": did, "sym": "KXETH15M", "position": {"qty": sign * qty, "entry_price": fill_yes}},
        {"kind": "decision", "ts": ts, "decision_id": did, "sym": "KXETH15M", "action": "enter_long" if yes else "enter_short", "executed": True, "prob": price + 0.05},
    ]
    end = ts + 400_000
    if sold_at is not None:
        exit_fee = taker_fee_usd(qty, sold_at)
        rows += [
            {"kind": "fill", "ts": end - 50_000, "decision_id": f"x-{did}", "sym": "KXETH15M", "side": "sell" if yes else "buy", "qty": qty,
             "fee_usd": exit_fee, "realized_pnl_usd": round(qty * (sold_at - price), 4)},
            {"kind": "position_closed", "ts": end - 50_000, "decision_id": did, "sym": "KXETH15M", "settled": False},
        ]
    else:
        won = payout if yes else 1.0 - payout
        rows += [
            {"kind": "fill", "ts": end, "decision_id": did, "sym": "KXETH15M", "side": "settle", "qty": qty, "fee_usd": 0.0, "realized_pnl_usd": round(qty * (won - price), 4)},
            {"kind": "position_closed", "ts": end, "decision_id": did, "sym": "KXETH15M", "settled": True, "payout": payout},
        ]
    rows.append({"kind": "settlement", "ts": end + 12_000, "sym": "KXETH15M", "ticker": ticker, "payout": payout, "official": True,
                 "decision_id": None if sold_at is not None else did})
    return rows


def test_the_two_rules_on_v2_bets(tmp_path):
    records = [{"kind": "trial", "ts": V2, "trial_id": "v2", "mode": "paper", "spec": {"kalshi": {"forecast": "anchored"}}}]
    # a favourite (YES at 90c) the late stop sold at 80c in its last minute; it then won at the close
    records += bet("fav-sold", "M-1", REG + 1_000, yes=True, price=0.90, sold_at=0.80, payout=1.0)
    # a long shot (NO at 15c) the late stop sold at 5c; it went on to lose
    records += bet("dog-sold", "M-2", REG + 500_000, yes=False, price=0.15, sold_at=0.05, payout=1.0)
    # a favourite held to a win (NO at 92c), and one opened before the rules' registration (in sample)
    records += bet("fav-won", "M-3", REG + 1_000_000, yes=False, price=0.92, payout=0.0)
    records += bet("early", "M-4", V2 + 60_000, yes=True, price=0.20, payout=1.0)
    write(tmp_path, records)
    report = evaluate(tmp_path, registered_ms=REG)
    by = {t["id"]: t for t in report["trades"]}
    sold_fav = round(10 * (0.80 - 0.90) - taker_fee_usd(10, 0.90) - taker_fee_usd(10, 0.80), 2)
    assert by["fav-sold"]["desk"] == {"result": "sold", "pnl_usd": sold_fav}
    # late stop only under 50c: the favourite is held to its result, paying no exit fee
    assert 0.90 >= UNDERDOG_BELOW and by["fav-sold"]["late_stop_underdogs"] == {"result": "won", "pnl_usd": round(10 * (1.0 - 0.90) - taker_fee_usd(10, 0.90), 2)}
    assert by["dog-sold"]["late_stop_underdogs"] == by["dog-sold"]["desk"] and by["dog-sold"]["desk"]["result"] == "sold"
    # skip favourites: both bets bought above 70c count nothing
    assert by["fav-won"]["skip_favourites"] == {"result": "skipped", "pnl_usd": 0.0} and 0.92 > FAVOURITE_ABOVE
    assert by["fav-sold"]["skip_favourites"]["result"] == "skipped" and by["dog-sold"]["skip_favourites"] == by["dog-sold"]["desk"]
    s = report["strategies"]
    assert s["desk"]["test"]["trades"] == 3 and s["desk"]["since_v2"]["trades"] == 4     # "early" is in sample only
    assert s["skip_favourites"]["test"]["skipped"] == 2 and s["skip_favourites"]["test"]["trades"] == 1
    assert s["late_stop_underdogs"]["test"]["pnl_usd"] == pytest.approx(s["desk"]["test"]["pnl_usd"] - sold_fav + (10 * 0.10 - taker_fee_usd(10, 0.90)), abs=0.011)


def test_nothing_to_judge_before_v2_starts(tmp_path):
    write(tmp_path, [{"kind": "heartbeat", "ts": V2, "equity_usd": 10_000.0}])
    report = evaluate(tmp_path)
    assert report["v2_start_ms"] is None and report["strategies"] == {}
