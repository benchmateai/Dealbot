import json

from dashboard.money import build

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
