import json

from kalshi.api import KalshiApiError
from reports.reconcile import one_line, reconcile

T0 = 1_793_686_800_000


class Result:
    def __init__(self, result):
        self.result = result


class FakeKalshi:
    def __init__(self, results, rate_limit_first=()):
        self.results, self.calls = results, []
        self._limited = set(rate_limit_first)

    def market(self, ticker):
        self.calls.append(ticker)
        if ticker in self._limited:
            self._limited.discard(ticker)
            raise KalshiApiError("HTTP 429", status=429)
        return Result(self.results.get(ticker))


def write(tmp_path, records):
    with open(tmp_path / "events-2026-11-03.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def test_only_provisional_settlements_are_looked_up_and_wrong_positions_come_first(tmp_path):
    write(tmp_path, [
        {"kind": "position_opened", "ts": T0, "decision_id": "d1", "position": {"qty": -10.0, "entry_price": 0.97}},
        {"kind": "settlement", "ts": T0 + 1, "ticker": "ETH-A", "sym": "KXETH15M", "official": True, "payout": 1.0, "decision_id": None},
        {"kind": "settlement", "ts": T0 + 2, "ticker": "ETH-B", "sym": "KXETH15M", "official": False, "payout": 0.0, "decision_id": None},
        {"kind": "settlement", "ts": T0 + 3, "ticker": "ETH-C", "sym": "KXETH15M", "official": False, "payout": 0.0, "decision_id": "d1", "contracts": 10.0},
        {"kind": "settlement", "ts": T0 + 4, "ticker": "BTC-D", "sym": "KXBTC15M", "official": False, "payout": 1.0, "decision_id": None},
    ])
    kalshi = FakeKalshi({"ETH-B": "no", "ETH-C": "yes", "BTC-D": None}, rate_limit_first={"ETH-B"})
    report = reconcile(tmp_path, kalshi, sleep=lambda s: None)
    assert kalshi.calls == ["ETH-B", "ETH-B", "ETH-C", "BTC-D"]  # never the official one; a 429 is retried
    first = report["rows"][0]
    assert (first["ticker"], first["status"], first["pnl_delta_usd"]) == ("ETH-C", "wrong", -10.0)  # short YES, paid out after all
    assert [r["status"] for r in report["rows"]] == ["wrong", "pending", "confirmed"]
    s = report["summary"]
    assert (s["settlements"], s["official_at_the_time"], s["provisional"], s["positions_wrong"], s["pnl_delta_usd"]) == (4, 1, 3, 1, -10.0)
    assert "positions settled the wrong way: 1 (realized P&L off by -10.00 USD)" in one_line(s)
