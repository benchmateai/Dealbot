import json

from reports.health import HOUR_MS, MINUTE_MS, check

T0 = 1_793_686_800_000


def write(tmp_path, records):
    with open(tmp_path / "events-2026-11-03.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def heartbeats(start, minutes, **fields):
    return [{"kind": "heartbeat", "ts": start + m * MINUTE_MS, "equity_usd": 10_000.0, "day_pnl_usd": 0.0, "fault": None, "position": None, **fields} for m in range(0, minutes + 1, 5)]


def test_a_deciding_desk_that_pushed_recently_is_ok(tmp_path):
    end = T0 + 2 * HOUR_MS
    write(tmp_path, heartbeats(T0, 120) + [{"kind": "answer", "ts": end - m * MINUTE_MS} for m in range(1, 40, 2)])
    r = check(tmp_path, commit_ms=end - 10 * MINUTE_MS, now_ms=end)
    assert r["status"] == "OK", r["line"]
    assert r["stats"]["jev_calls_1h"] == 20
    assert r["line"].startswith("OK · pushed 10 min ago, last hour: 20 Jev calls")


def test_stale_pushes_a_fault_and_a_stuck_position_each_raise_an_alert(tmp_path):
    end = T0 + 2 * HOUR_MS
    stuck = {"sym": "KXETH15M", "qty": -10.0, "entry_ts": end - 50 * MINUTE_MS}
    write(tmp_path, heartbeats(T0, 120, position=stuck, fault="feed down") + [{"kind": "answer", "ts": end - MINUTE_MS}])
    r = check(tmp_path, commit_ms=end - 80 * MINUTE_MS, now_ms=end)
    assert r["status"] == "ALERT"
    assert any("nothing pushed" in a for a in r["alerts"])
    assert any("fault: feed down" in a for a in r["alerts"])
    assert any("KXETH15M position open 50 min" in a for a in r["alerts"])
    assert "open: NO KXETH15M" in r["line"]


def test_quiet_judge_warns_after_an_hour_and_alerts_after_two(tmp_path):
    end = T0 + 2 * HOUR_MS
    write(tmp_path, heartbeats(T0, 120) + [{"kind": "answer", "ts": end - 90 * MINUTE_MS}])
    assert check(tmp_path, commit_ms=end, now_ms=end)["warnings"] == ["no Jev calls in the last hour"]
    write(tmp_path, heartbeats(T0, 120))
    assert check(tmp_path, commit_ms=end, now_ms=end)["alerts"] == ["no Jev calls in two hours"]
    write(tmp_path, heartbeats(T0, 30))  # a run younger than the window is not judged quiet
    assert check(tmp_path, commit_ms=T0 + 30 * MINUTE_MS, now_ms=T0 + 30 * MINUTE_MS)["status"] == "OK"


def test_judge_failures_losses_and_provisional_settlements(tmp_path):
    end = T0 + HOUR_MS
    records = heartbeats(T0, 60, day_pnl_usd=-60.0, equity_usd=9_940.0)
    records += [{"kind": "answer", "ts": end - m * MINUTE_MS} for m in range(1, 5)]
    records += [{"kind": "rejection", "check": "jev_timeout", "ts": end - m * MINUTE_MS} for m in range(1, 3)]
    records += [{"kind": "settlement", "ts": end - 5 * MINUTE_MS, "decision_id": "kalshi-1-KXETH15M", "official": False}]
    write(tmp_path, records)
    r = check(tmp_path, commit_ms=end, now_ms=end)
    assert r["alerts"] == ["2 of 6 Jev calls failed in the last hour"]
    assert any("past half the 100 USD daily loss limit" in w for w in r["warnings"])
    assert any("1 position settlement(s) in 24 h were provisional" in w for w in r["warnings"])


def test_an_empty_log_is_an_alert(tmp_path):
    (tmp_path / "events-2026-11-03.jsonl").write_text("")
    assert check(tmp_path, commit_ms=None, now_ms=T0)["line"] == "ALERT · no heartbeat in the log"
