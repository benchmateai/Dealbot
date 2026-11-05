import json

from reports.chunk_summary import STALL_MS, one_line, summarize, write

T0 = 1_793_680_000_000


class RawLog:
    """Writes event lines the way the desk's log writer stores them, without its per-kind schema."""

    def __init__(self, directory) -> None:
        self._fh = open(directory / "events-2026-11-03.jsonl", "a", encoding="utf-8")

    def write(self, kind: str, record: dict, *, ts_ms: int) -> None:
        self._fh.write(json.dumps({"kind": kind, "ts": ts_ms, **record}) + "\n")

    def close(self) -> None:
        self._fh.close()


def test_a_chunk_that_never_asks_the_judge_is_flagged_as_stalled(tmp_path):
    log = RawLog(tmp_path)
    for i in range(40):
        log.write("rejection", {"check": "risk_precheck:max_position", "sym": "KXETH15M"}, ts_ms=T0 + i * 60_000)
    log.write("heartbeat", {"equity_usd": 10_000.0, "feed": {"polls": 10, "errors": 0, "rate_limits": 0}}, ts_ms=T0)
    log.write("heartbeat", {"equity_usd": 10_000.0, "feed": {"polls": 500, "errors": 3, "rate_limits": 2}}, ts_ms=T0 + STALL_MS + 60_000)
    log.close()
    s = summarize(tmp_path, since_ms=T0)
    assert s["stalled"] and s["judge_calls"] == 0 and s["rejections"] == {"risk_precheck:max_position": 40}
    assert s["feed"] == {"polls": 490, "errors": 3, "rate_limits": 2}
    assert "STALLED" in one_line(s)


def test_a_deciding_chunk_counts_calls_decisions_fills_and_settlements(tmp_path):
    log = RawLog(tmp_path)
    log.write("rejection", {"check": "outside_trade_window"}, ts_ms=T0 - 1)  # before the window: ignored
    log.write("answer", {"model": "jev-1.14.0", "answers": {}}, ts_ms=T0 + 1000)
    log.write("decision", {"action": "enter_long", "executed": True}, ts_ms=T0 + 1000)
    log.write("fill", {"side": "buy", "qty": 10, "fee_usd": 0.1, "realized_pnl_usd": 0.0}, ts_ms=T0 + 1000)
    log.write("position_opened", {"sym": "KXETH15M"}, ts_ms=T0 + 1000)
    log.write("rejection", {"check": "jev_timeout"}, ts_ms=T0 + 2000)
    log.write("settlement", {"official": True, "payout": 1.0}, ts_ms=T0 + 900_000)
    log.write("fill", {"side": "settle", "qty": 10, "fee_usd": 0.0, "realized_pnl_usd": 4.0}, ts_ms=T0 + 900_000)
    log.write("position_closed", {"realized_pnl_usd": 7.5}, ts_ms=T0 + 900_000)  # the symbol's realized to date: not summed
    log.close()
    s = summarize(tmp_path, since_ms=T0)
    assert not s["stalled"] and s["judge_calls"] == 1 and s["models"] == {"jev-1.14.0": 1}
    assert s["decisions"] == {"enter_long": 1} and s["executed"] == 1 and s["fills"] == {"buy": 1, "settle": 1}
    assert s["settlements"] == {"official": 1, "provisional": 0} and s["realized_pnl_usd"] == 3.9  # 4.00 gross less 0.10 fees
    assert s["judge_failures"] == {"jev_timeout": 1} and "outside_trade_window" not in s["rejections"]
    path = write(s, tmp_path / "summaries")
    assert json.loads(path.read_text())["judge_calls"] == 1 and (tmp_path / "summaries" / "latest.json").exists()


def test_feed_counters_add_up_across_desk_restarts(tmp_path):
    # each desk process counts from 0; the summary adds what every process counted inside the window
    log = RawLog(tmp_path)
    for ts, polls, errors in ((T0, 10, 0), (T0 + 60_000, 500, 3), (T0 + 120_000, 5, 0), (T0 + 180_000, 100, 2)):
        log.write("heartbeat", {"equity_usd": 10_000.0, "feed": {"polls": polls, "errors": errors, "rate_limits": 0}}, ts_ms=ts)
    log.close()
    s = summarize(tmp_path, since_ms=T0, until_ms=T0 + 200_000)
    assert s["feed"] == {"polls": 490 + 5 + 95, "errors": 3 + 0 + 2, "rate_limits": 0}


def test_a_v2_window_with_forecasts_and_no_judge_calls_is_not_stalled(tmp_path):
    log = RawLog(tmp_path)
    for k in range(40):
        ts = T0 + k * 60_000
        log.write("heartbeat", {"equity_usd": 10_000.0, "feed": {"polls": k, "errors": 0, "rate_limits": 0}}, ts_ms=ts)
        log.write("forecast", {"decision_id": f"d{k}", "sym": "KXETH15M", "model": "anchored-1", "weight": 0.5}, ts_ms=ts)
    log.close()
    s = summarize(tmp_path, since_ms=T0, until_ms=T0 + 41 * 60_000)
    assert s["judge_calls"] == 0 and s["forecasts"] == 40 and s["stalled"] is False
    assert "forecasts 40" in one_line(s) and "STALLED" not in one_line(s)
