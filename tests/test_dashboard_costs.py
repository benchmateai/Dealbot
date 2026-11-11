import json

import pytest

from dashboard import costs as dc
from reports import costs

BUDGETS = {"coordinator": 40.0, "runner": 10.0, "watchdog": 5.0}


def snap(at, **roles):
    """roles: cost, or (cost, session id); every session began at 2026-11-03T00:00Z."""
    out = {}
    for role, v in roles.items():
        cost, sid = v if isinstance(v, tuple) else (v, f"s-{role}")
        out[role] = {"id": sid, "cost_usd": cost, "created_at": "2026-11-03T00:00:00Z"}
    return {"at": at, "sessions": out}


def test_the_window_starts_at_the_snapshot_nearest_a_day_back_and_matches_the_cost_report():
    history = [snap("2026-11-10T01:00:00Z", coordinator=700.0, runner=40.0, watchdog=20.0),
               snap("2026-11-10T07:00:00Z", coordinator=710.0, runner=41.0, watchdog=21.0),
               snap("2026-11-10T13:30:00Z", coordinator=720.0, runner=42.0, watchdog=22.0)]
    now = snap("2026-11-11T07:30:00Z", coordinator=760.0, runner=45.0, watchdog=23.5)
    rows = dc.rows(now, history, BUDGETS)
    s = rows[0]
    assert s["window_start_ms"] == costs._ms("2026-11-10T07:00:00Z") and s["window_hours"] == 24.5
    assert s["spent_usd"] == 50.0 + 4.0 + 2.5 and s["daily_budget_usd"] == 55.0
    assert s["budget_usd"] == round(sum(r["limit_usd"] for r in rows[1:]), 2) == 40.83 + 10.21 + 5.1  # the column adds up to the tile
    assert s["spent_usd"] == costs.compare(now, history[1], BUDGETS)["team_spent_usd"]
    by = {r["id"]: r for r in rows[1:]}
    assert [r["id"] for r in rows[1:]] == ["coordinator", "runner", "watchdog"]
    assert by["coordinator"]["spent_usd"] == 50.0 and by["coordinator"]["over"] and s["over"] == ["coordinator"]
    assert by["runner"]["limit_usd"] == round(10.0 * 24.5 / 24, 2) and by["runner"]["total_usd"] == 45.0
    assert s["total_usd"] == 760.0 + 45.0 + 23.5 and s["first_since_ms"] == costs._ms("2026-11-03T00:00:00Z")


def test_the_first_look_has_no_window_and_a_snapshot_less_than_an_hour_old_is_not_one():
    history = [snap("2026-11-11T07:00:00Z", coordinator=750.0, runner=45.0, watchdog=23.0)]
    s, *roles = dc.rows(snap("2026-11-11T07:30:00Z", coordinator=751.0, runner=45.1, watchdog=23.1), history, BUDGETS)
    assert s["spent_usd"] is None and s["window_start_ms"] is None and s["over"] == [] and s["total_usd"] == 819.2
    assert all(r["spent_usd"] is None and not r["over"] for r in roles)


def test_a_teammate_replaced_inside_the_window_counts_every_session_even_one_named_by_an_earlier_check():
    start = snap("2026-11-10T07:00:00Z", coordinator=700.0, runner=(40.0, "r1"), watchdog=20.0)
    middle = snap("2026-11-10T13:30:00Z", coordinator=720.0, runner=(2.0, "r2"), watchdog=21.0)
    middle["retired"] = {"r1": {"role": "runner", "cost_usd": 43.0}}  # r1 was replaced between the two checks
    now = snap("2026-11-11T07:00:00Z", coordinator=760.0, runner=(5.0, "r2"), watchdog=22.0)  # names no retired session
    s, *roles = dc.rows(now, [start, middle], BUDGETS)
    runner = next(r for r in roles if r["id"] == "runner")
    assert runner["spent_usd"] == 3.0 + 5.0 and s["missing"] == []  # r1's last $3, and r2's $5
    assert runner["total_usd"] == 48.0 and s["total_usd"] == 760.0 + 5.0 + 22.0 + 43.0


def test_a_session_replaced_before_the_window_is_not_counted_in_it_again():
    old = snap("2026-11-09T07:00:00Z", coordinator=600.0, runner=(2.0, "r2"), watchdog=10.0)
    old["retired"] = {"r1": {"role": "runner", "cost_usd": 43.0}}
    start = snap("2026-11-10T07:00:00Z", coordinator=700.0, runner=(3.0, "r2"), watchdog=20.0)
    now = snap("2026-11-11T07:00:00Z", coordinator=760.0, runner=(4.0, "r3"), watchdog=22.0)
    now["retired"] = {"r1": {"role": "runner", "cost_usd": 43.0}, "r2": {"role": "runner", "cost_usd": 6.0}}  # r1 carried by mistake
    s, *roles = dc.rows(now, [old, start], BUDGETS)
    assert next(r for r in roles if r["id"] == "runner")["spent_usd"] == 3.0 + 4.0  # r2's last $3 and r3's $4, not r1's $43
    assert s["total_usd"] == 760.0 + 4.0 + 22.0 + 43.0 + 6.0


def test_the_command_appends_once_and_writes_the_dataset(tmp_path):
    hist, out, snapfile, budgets = tmp_path / "history.jsonl", tmp_path / "costs.json", tmp_path / "now.json", tmp_path / "budgets.json"
    budgets.write_text(json.dumps({"daily_usd": BUDGETS}))
    hist.write_text(json.dumps(snap("2026-11-10T21:30:00Z", coordinator=750.0, runner=46.8, watchdog=23.6)) + "\n")
    snapfile.write_text(json.dumps(snap("2026-11-11T01:07:30Z", coordinator=775.2, runner=47.4, watchdog=24.1)))
    for _ in range(2):
        assert dc.main(["--snapshot", str(snapfile), "--history", str(hist), "--budgets", str(budgets), "--append", "--out", str(out)]) == 0
    assert len(hist.read_text().splitlines()) == 2
    rows = json.loads(out.read_text())
    assert rows[0]["table"] == "cost_summary" and rows[0]["spent_usd"] == pytest.approx(25.2 + 0.6 + 0.5)
    assert {r["table"] for r in rows[1:]} == {"cost_role"}


def test_a_bad_snapshot_is_refused_before_it_reaches_the_history_and_a_bad_line_cannot_block_later_runs(tmp_path):
    hist, out, snapfile, budgets = tmp_path / "history.jsonl", tmp_path / "costs.json", tmp_path / "now.json", tmp_path / "budgets.json"
    budgets.write_text(json.dumps({"daily_usd": BUDGETS}))
    first = json.dumps(snap("2026-11-10T21:30:00Z", coordinator=750.0, runner=46.8, watchdog=23.6))
    hist.write_text(first + "\nnot json\n" + first[:-1])  # a hand edit: a broken line, and no newline at the end
    bad = snap("2026-11-11T01:07:30Z", coordinator=775.2, runner=47.4, watchdog=24.1)
    bad["retired"] = {"r1": {"role": "runner", "cost_usd": None}}
    snapfile.write_text(json.dumps(bad))
    args = ["--snapshot", str(snapfile), "--history", str(hist), "--budgets", str(budgets), "--append", "--out", str(out)]
    assert dc.main(args) == 2 and not out.exists() and hist.read_text().count("\n") == 2  # refused, nothing appended
    snapfile.write_text(json.dumps(snap("2026-11-11T01:07:30Z", coordinator=775.2, runner=47.4, watchdog=24.1)))
    assert dc.main(args) == 0
    kept = dc.load_history(hist)
    assert [x["at"] for x in kept] == ["2026-11-10T21:30:00Z", "2026-11-11T01:07:30Z"]  # the unfinished line ended, not glued
    assert json.loads(out.read_text())[0]["spent_usd"] == pytest.approx(25.2 + 0.6 + 0.5)


def test_a_corrected_re_run_replaces_the_check_it_corrects(tmp_path):
    hist, out, snapfile, budgets = tmp_path / "history.jsonl", tmp_path / "costs.json", tmp_path / "now.json", tmp_path / "budgets.json"
    budgets.write_text(json.dumps({"daily_usd": BUDGETS}))
    hist.write_text(json.dumps(snap("2026-11-11T07:30:00Z", coordinator=700.0, runner=(43.0, "r1"), watchdog=20.0)) + "\n")
    morning = snap("2026-11-11T13:30:00Z", coordinator=720.0, runner=(1.0, "r2"), watchdog=21.0)
    args = ["--snapshot", str(snapfile), "--history", str(hist), "--budgets", str(budgets), "--append", "--out", str(out)]
    snapfile.write_text(json.dumps(morning))
    dc.main(args)
    assert json.loads(out.read_text())[0]["missing"] == ["runner"]
    morning["retired"] = {"r1": {"role": "runner", "cost_usd": 44.0}}  # the coordinator reads r1 and runs it again
    snapfile.write_text(json.dumps(morning))
    dc.main(args)
    kept = dc.load_history(hist)
    assert len(kept) == 2 and kept[-1]["retired"] == morning["retired"]
    later = snap("2026-11-11T19:30:00Z", coordinator=730.0, runner=(3.0, "r2"), watchdog=21.5)
    s, *roles = dc.rows(later, kept, BUDGETS)
    assert s["missing"] == [] and next(r for r in roles if r["id"] == "runner")["spent_usd"] == 1.0 + 3.0 and s["total_usd"] == 730.0 + 3.0 + 21.5 + 44.0


def test_a_replaced_session_nobody_named_keeps_its_last_reading_in_the_totals_and_the_window_says_it_is_missing():
    start = snap("2026-11-11T07:30:00Z", coordinator=700.0, runner=(43.0, "r1"), watchdog=20.0)
    now = snap("2026-11-12T07:30:00Z", coordinator=760.0, runner=(1.0, "r2"), watchdog=22.0)  # r1 never named under retired
    s, *roles = dc.rows(now, [start], BUDGETS)
    runner = next(r for r in roles if r["id"] == "runner")
    assert s["missing"] == ["runner"] and runner["spent_usd"] == 1.0  # r1's spend in the window is not known
    assert runner["total_usd"] == 44.0 and s["total_usd"] == 760.0 + 1.0 + 22.0 + 43.0


def test_since_is_when_the_first_session_the_history_has_seen_began():
    old = snap("2026-11-10T07:00:00Z", coordinator=(730.0, "c1"), runner=40.0, watchdog=20.0)
    old["sessions"]["coordinator"]["created_at"] = "2026-10-17T22:45:09Z"
    now = snap("2026-11-11T07:00:00Z", coordinator=(2.0, "c2"), runner=45.0, watchdog=22.0)
    now["retired"] = {"c1": {"role": "coordinator", "cost_usd": 735.0}}
    s, *roles = dc.rows(now, [old], BUDGETS)
    assert s["first_since_ms"] == costs._ms("2026-10-17T22:45:09Z") and s["total_usd"] == 2.0 + 45.0 + 22.0 + 735.0
