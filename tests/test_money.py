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
    rows = build(tmp_path, now_ms=T0 + 800_000)
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
