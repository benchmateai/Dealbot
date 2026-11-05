import json

from dashboard.money import WEEK_START_MS as WEEK_START, build

T0 = 1_793_686_800_000


def write(tmp_path, records):
    with open(tmp_path / "events-2026-11-03.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def test_trades_read_like_kalshi_bets_with_fees_netted(tmp_path):
    d1, d2 = "kalshi-877-KXETH15M", "kalshi-950-KXBTC15M"
    write(tmp_path, [
        {"kind": "heartbeat", "ts": T0, "equity_usd": 10000.0},
        {"kind": "answer", "ts": T0 + 1, "usage": {"input_tokens": 1500, "output_tokens": 100}},
        # the opening fill is logged before the position, as the desk does
        {"kind": "fill", "ts": T0 + 2, "decision_id": d1, "side": "sell", "qty": 10, "price": 0.79, "fee_usd": 0.12, "gas_usd": 0.0, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": T0 + 3, "decision_id": d1, "sym": "KXETH15M", "position": {"qty": -10.0, "entry_price": 0.79}},
        {"kind": "settlement", "ts": T0 + 600_000, "decision_id": d1, "official": True, "payout": 1.0},
        {"kind": "fill", "ts": T0 + 600_000, "decision_id": d1, "side": "settle", "qty": 10, "price": 1.0, "fee_usd": 0.0, "gas_usd": 0.0, "realized_pnl_usd": -2.1},
        {"kind": "position_closed", "ts": T0 + 600_000, "decision_id": d1, "settled": True, "payout": 1.0},
        {"kind": "fill", "ts": T0 + 700_000, "decision_id": d2, "side": "buy", "qty": 10, "price": 0.40, "fee_usd": 0.17, "gas_usd": 0.0, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": T0 + 700_001, "decision_id": d2, "sym": "KXBTC15M", "position": {"qty": 10.0, "entry_price": 0.40}},
        {"kind": "heartbeat", "ts": T0 + 720_000, "equity_usd": 9997.51},
    ])
    rows = build(tmp_path, now_ms=T0 + 800_000, since_ms=T0)
    summary = rows[0]
    trades = [r for r in rows if r["table"] == "trade"]
    assert [t["id"] for t in trades] == [d2, d1], "newest first"
    lost = trades[1]
    assert lost["bet"] == "NO" and lost["price_cents"] == 21.0 and lost["stake_usd"] == 2.1 and lost["fees_usd"] == 0.12
    assert lost["result"] == "lost" and lost["pnl_usd"] == -2.22 and lost["official"] is True and lost["market"] == "ETH 15-min"
    assert trades[0]["bet"] == "YES" and trades[0]["result"] == "open" and trades[0]["pnl_usd"] is None
    assert summary["trades_closed"] == 1 and summary["trades_open"] == 1 and summary["wins"] == 0 and summary["win_rate"] == 0.0
    assert summary["realized_pnl_usd"] == -2.22 and summary["fees_usd"] == 0.29 and summary["net_pnl_usd"] == -2.49
    assert summary["jev_calls"] == 1 and summary["jev_cost_usd"] == round(1500 * 0.042 / 1e6, 4)
    assert [r["table"] for r in rows].count("equity") == 2 and [r for r in rows if r["table"] == "day"][0]["pnl_usd"] == -2.49


def test_an_exit_fill_counts_for_the_position_it_closes_and_the_window_starts_clean(tmp_path):
    carried, bet = "kalshi-900-KXETH15M", "kalshi-950-KXETH15M"
    write(tmp_path, [
        # before the window: a position the week inherits (it shows in equity, not as a bet)
        {"kind": "heartbeat", "ts": T0 - 60_000, "equity_usd": 9_990.0},
        {"kind": "fill", "ts": T0 - 50_000, "decision_id": carried, "sym": "KXETH15M", "side": "buy", "qty": 10, "fee_usd": 0.1, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": T0 - 50_000, "decision_id": carried, "sym": "KXETH15M", "position": {"qty": 10.0, "entry_price": 0.5}},
        {"kind": "heartbeat", "ts": T0, "equity_usd": 9_994.0},
        {"kind": "fill", "ts": T0 + 1_000, "decision_id": "kalshi-901-KXETH15M", "sym": "KXETH15M", "side": "sell", "qty": 10, "fee_usd": 0.1, "realized_pnl_usd": 2.0},
        {"kind": "position_closed", "ts": T0 + 1_000, "decision_id": carried, "sym": "KXETH15M", "settled": False},
        # in the window: short YES at 96.8c (a NO bet at 3.2c), bought back at 20c by a separate exit decision
        {"kind": "fill", "ts": T0 + 2_000, "decision_id": bet, "sym": "KXETH15M", "side": "sell", "qty": 10, "price": 0.968, "fee_usd": 0.03, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": T0 + 2_000, "decision_id": bet, "sym": "KXETH15M", "position": {"qty": -10.0, "entry_price": 0.968}},
        {"kind": "fill", "ts": T0 + 400_000, "decision_id": "kalshi-990-KXETH15M", "sym": "KXETH15M", "side": "buy", "qty": 10, "price": 0.20, "fee_usd": 0.12, "realized_pnl_usd": 7.68},
        {"kind": "position_closed", "ts": T0 + 400_000, "decision_id": bet, "sym": "KXETH15M", "settled": False},
        {"kind": "heartbeat", "ts": T0 + 400_000, "equity_usd": 10_003.43},
    ])
    rows = build(tmp_path, now_ms=T0 + 500_000, since_ms=T0)
    summary, trades = rows[0], [r for r in rows if r["table"] == "trade"]
    assert [t["id"] for t in trades] == [bet]
    sold = trades[0]
    assert (sold["bet"], sold["price_cents"], sold["result"], sold["fees_usd"], sold["pnl_usd"]) == ("NO", 3.2, "sold", 0.15, 7.53)
    assert summary["start_usd"] == 9_994.0 and summary["net_pnl_usd"] == 9.43 and summary["wins"] == 1 and summary["win_rate"] == 1.0


def test_the_shadow_rows_count_only_bets_after_the_rules_were_registered(tmp_path):
    from reports.shadow import LATE_STOP_REGISTERED_MS, REGISTERED_MS

    write(tmp_path, [{"kind": "heartbeat", "ts": REGISTERED_MS - 60_000, "equity_usd": 9_990.0}])
    rows = build(tmp_path, now_ms=REGISTERED_MS, since_ms=REGISTERED_MS - 120_000)
    shadows = {r["id"]: r for r in rows if r["table"] == "shadow"}
    assert set(shadows) == {"desk", "capped", "capped_exit", "late_stop"}
    assert shadows["capped"]["cap_points"] == 10 and shadows["capped_exit"]["exit_minutes"] == 3 and shadows["late_stop"]["late_seconds"] == 60
    assert shadows["desk"]["test_trades"] == 0 and shadows["desk"]["registered_ms"] == REGISTERED_MS
    # the late stop has its own test window, and carries the desk's result on the same bets
    assert shadows["late_stop"]["registered_ms"] == LATE_STOP_REGISTERED_MS and shadows["late_stop"]["desk_same_trades"] == 0


def test_once_v2_takes_over_the_page_counts_v2_and_keeps_the_first_desk_as_one_line(tmp_path):
    from reports.shadow import evaluate

    T0 = WEEK_START  # the first desk's week starts here; v2 takes over a little later
    v2 = T0 + 1_000_000
    d1, d2 = "kalshi-1-KXETH15M", "kalshi-90-KXBTC15M"
    write(tmp_path, [
        {"kind": "trial", "ts": T0, "trial_id": "v1", "mode": "paper", "spec": {"kalshi": {"model_weight": 0.5}}},
        {"kind": "heartbeat", "ts": T0, "equity_usd": 10_000.0},
        {"kind": "fill", "ts": T0 + 2, "decision_id": d1, "side": "buy", "qty": 10, "price": 0.40, "fee_usd": 0.17, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": T0 + 3, "decision_id": d1, "sym": "KXETH15M", "position": {"qty": 10.0, "entry_price": 0.40}},
        {"kind": "fill", "ts": T0 + 600_000, "decision_id": d1, "side": "settle", "qty": 10, "price": 0.0, "fee_usd": 0.0, "realized_pnl_usd": -4.0},
        {"kind": "position_closed", "ts": T0 + 600_000, "decision_id": d1, "sym": "KXETH15M", "settled": True, "payout": 0.0},
        {"kind": "heartbeat", "ts": T0 + 700_000, "equity_usd": 9_995.83},
        {"kind": "trial", "ts": v2, "trial_id": "v2", "mode": "paper", "spec": {"kalshi": {"forecast": "anchored"}}},
        {"kind": "heartbeat", "ts": v2, "equity_usd": 9_995.83},
        {"kind": "fill", "ts": v2 + 2, "decision_id": d2, "side": "buy", "qty": 10, "price": 0.70, "fee_usd": 0.15, "realized_pnl_usd": 0.0},
        {"kind": "position_opened", "ts": v2 + 3, "decision_id": d2, "sym": "KXBTC15M", "position": {"qty": 10.0, "entry_price": 0.70}},
        {"kind": "fill", "ts": v2 + 300_000, "decision_id": d2, "side": "settle", "qty": 10, "price": 1.0, "fee_usd": 0.0, "realized_pnl_usd": 3.0},
        {"kind": "position_closed", "ts": v2 + 300_000, "decision_id": d2, "sym": "KXBTC15M", "settled": True, "payout": 1.0},
        {"kind": "heartbeat", "ts": v2 + 300_000, "equity_usd": 9_998.68},
    ])
    rows = build(tmp_path, now_ms=v2 + 400_000)
    s = rows[0]
    assert s["desk"] == "v2" and s["week_started_ms"] == v2 and s["start_usd"] == 9_995.83 and s["net_pnl_usd"] == 2.85
    assert [r["id"] for r in rows if r["table"] == "trade"] == [d2] and not [r for r in rows if r["table"] == "shadow"]
    prev = [r for r in rows if r["table"] == "previous"]
    assert len(prev) == 1 and prev[0]["id"] == "v1" and prev[0]["to_ms"] == v2 and prev[0]["trades_closed"] == 1 and prev[0]["net_pnl_usd"] == -4.17
    # the shadow rules judge the first desk's bets only
    assert [t["id"] for t in evaluate(tmp_path, since_ms=T0)["trades"]] == [d1]
    # before the switch nothing changes: the first desk's week and its shadow rows
    before = build(tmp_path, now_ms=v2 + 400_000, v2_ms=None)
    assert before[0]["desk"] == "v1" and before[0]["week_started_ms"] == WEEK_START and {r["table"] for r in before} >= {"summary", "trade", "shadow"}


def test_lab_rows_carry_each_strategy_s_numbers_and_name_the_dropped():
    from dashboard.lab import rows

    report = {"strategies": {"E": {"line": "E ...", "summary": {"net_usd_realistic": 25.12, "hours": 23.5, "capital_avg_usd": 2431.69, "nested": {"x": 1}}},
                             "A": {"line": "A ...", "summary": {"pnl_usd": 25.33, "trades": 141, "scores": {"60": {}}}}},
              "dropped": {"B": "late-window harvest, dropped 2026-11-05: ..."}}
    out = rows(report, now_ms=T0)
    assert [r["id"] for r in out] == ["A", "E", "B"]
    e = out[1]
    assert e["net_usd_realistic"] == 25.12 and e["capital_avg_usd"] == 2431.69 and "nested" not in e and e["updated_ms"] == T0 and e["dropped"] is False
    assert out[0]["trades"] == 141 and "scores" not in out[0] and out[2]["dropped"] is True
