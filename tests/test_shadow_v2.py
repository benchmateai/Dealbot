"""The owner's two paper rules on desk v2's own bets (reports/shadow_v2.py)."""

import json

import pytest

from kalshi.api import taker_fee_usd
from reports.shadow_v2 import FAVOURITE_ABOVE, LATE_ENTRY_S, UNDERDOG_BELOW, evaluate

V2 = 1_793_852_388_000          # desk v2's first block
REG = V2 + 3_600_000            # the rules count bets from here on


def write(tmp_path, records):
    with open(tmp_path / "events-2026-11-05.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def bet(did, ticker, ts, *, yes, price, qty=10, sold_at=None, payout, left=400):
    """One v2 position as the desk logs it; sold_at is the side's sell price when the late stop sold it, left the
    seconds to the close when it was opened."""
    sign = 1 if yes else -1
    fill_yes = price if yes else 1.0 - price
    fee = taker_fee_usd(qty, price)
    rows = [
        {"kind": "snapshot", "ts": ts, "decision_id": did, "sym": "KXETH15M", "phase": "entry",
         "state": {"contract": {"ticker": ticker, "yes_bid": fill_yes - 0.01, "yes_ask": fill_yes + 0.01, "expires_in_s": left}}},
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


def test_the_third_rule_skips_late_entries_from_its_own_start(tmp_path):
    late_reg = REG + 7_200_000      # the third rule counts bets from here on
    records = [{"kind": "trial", "ts": V2, "trial_id": "v2", "mode": "paper", "spec": {"kalshi": {"forecast": "anchored"}}}]
    # opened 2 minutes before the close, after the third rule's start: a long shot that lost
    records += bet("late", "M-1", late_reg + 1_000, yes=True, price=0.12, payout=0.0, left=120)
    # opened 7 minutes out, after the start: a favourite that won
    records += bet("early", "M-2", late_reg + 500_000, yes=False, price=0.80, payout=0.0, left=420)
    # opened 2 minutes out but before the third rule's start: in sample for it, a test bet for the first two
    records += bet("before", "M-3", REG + 1_000, yes=True, price=0.10, payout=1.0, left=100)
    write(tmp_path, records)
    report = evaluate(tmp_path, registered_ms=REG, late_entry_registered_ms=late_reg)
    by = {t["id"]: t for t in report["trades"]}
    assert 120 < LATE_ENTRY_S <= 420 and by["late"]["entry_left_s"] == 120
    assert by["late"]["skip_late_entries"] == {"result": "skipped", "pnl_usd": 0.0}
    assert by["early"]["skip_late_entries"] == by["early"]["desk"] and by["early"]["desk"]["result"] == "won"
    s = report["strategies"]["skip_late_entries"]
    assert s["registered_ms"] == late_reg and report["strategies"]["skip_favourites"]["registered_ms"] == REG
    assert s["test"]["trades"] == 1 and s["test"]["skipped"] == 1 and s["test"]["pnl_usd"] == by["early"]["desk"]["pnl_usd"]
    # v2 on exactly the same two bets, so the rule compares like for like
    assert s["desk_same"]["trades"] == 2 and s["desk_same"]["pnl_usd"] == round(by["late"]["desk"]["pnl_usd"] + by["early"]["desk"]["pnl_usd"], 2)
    # all of v2: the bet before the start is skipped too, but only in sample
    assert s["since_v2"]["skipped"] == 2 and report["strategies"]["desk"]["test"]["trades"] == 3
    # the next round's pick: the same skip, and the late stop only on long shots; same start, same comparison
    nxt = report["strategies"]["next_round"]
    assert nxt["registered_ms"] == late_reg and nxt["desk_same"] == s["desk_same"] and by["late"]["next_round"]["result"] == "skipped"
    assert nxt["test"] == s["test"]     # nothing here was late-stopped, so the two agree


def test_the_next_round_holds_a_favourite_the_late_stop_sold(tmp_path):
    late_reg = REG + 7_200_000
    records = [{"kind": "trial", "ts": V2, "trial_id": "v2", "mode": "paper", "spec": {"kalshi": {"forecast": "anchored"}}}]
    records += bet("fav", "M-1", late_reg + 1_000, yes=True, price=0.85, sold_at=0.70, payout=1.0, left=300)
    records += bet("fav-late", "M-2", late_reg + 500_000, yes=True, price=0.85, sold_at=0.70, payout=1.0, left=90)
    write(tmp_path, records)
    report = evaluate(tmp_path, registered_ms=REG, late_entry_registered_ms=late_reg)
    by = {t["id"]: t for t in report["trades"]}
    assert by["fav"]["next_round"] == by["fav"]["late_stop_underdogs"] and by["fav"]["next_round"]["result"] == "won"
    assert by["fav-late"]["next_round"] == {"result": "skipped", "pnl_usd": 0.0}


def test_nothing_to_judge_before_v2_starts(tmp_path):
    write(tmp_path, [{"kind": "heartbeat", "ts": V2, "equity_usd": 10_000.0}])
    report = evaluate(tmp_path)
    assert report["v2_start_ms"] is None and report["strategies"] == {}


def test_the_rules_judge_v2_s_bets_only_and_freeze_at_v3_s_start(tmp_path):
    v3 = REG + 3_600_000
    records = [{"kind": "trial", "ts": V2, "trial_id": "v2", "mode": "paper", "spec": {"kalshi": {"forecast": "anchored"}}}]
    records += bet("v2-bet", "M-1", REG + 1_000, yes=True, price=0.20, payout=1.0)
    records.append({"kind": "trial", "ts": v3, "trial_id": "v3", "mode": "paper", "spec": {"kalshi": {"forecast": "anchored", "rules": "v3"}}})
    records += bet("v3-bet", "M-2", v3 + 1_000, yes=True, price=0.20, payout=1.0, left=300)
    write(tmp_path, records)
    report = evaluate(tmp_path, registered_ms=REG)
    assert report["until_ms"] == v3 and [t["id"] for t in report["trades"]] == ["v2-bet"]
    assert report["strategies"]["desk"]["since_v2"]["trades"] == 1
