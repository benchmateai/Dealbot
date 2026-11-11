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
    assert {r["table"] for r in rows[1:]} == {"cost_role", "cost_day"}
    assert [r["day"] for r in rows if r["table"] == "cost_day"] == ["2026-11-10"]  # 2:30 PM to 6:07 PM in Arizona


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


def test_daily_costs_are_measured_between_snapshots_across_arizona_midnight_and_estimated_before_them():
    budgets = {"coordinator": 40.0, "runner": 10.0}
    # 05:00Z and 09:00Z straddle Arizona midnight (07:00Z): half of each teammate's spend falls on each day
    snaps = [snap("2026-11-11T05:00:00Z", coordinator=100.0, runner=10.0), snap("2026-11-11T09:00:00Z", coordinator=120.0, runner=12.0)]
    before = {"until": "2026-11-11T05:00:00Z", "days": {"2026-11-09": {"coordinator": 30.0, "runner": 5.0}, "2026-11-10": {"coordinator": 50.0, "runner": 4.0}}}
    days = {r["day"]: r for r in dc.day_rows(snaps, budgets, before)}
    assert list(days) == ["2026-11-09", "2026-11-10", "2026-11-11"]
    assert days["2026-11-09"]["cost_usd"] == 35.0 and days["2026-11-09"]["estimated"] and not days["2026-11-09"]["measured"]
    nov10 = days["2026-11-10"]
    assert nov10["cost_usd"] == 54.0 + 11.0 and nov10["estimated"] and nov10["measured"] and nov10["over"] and nov10["budget_usd"] == 50.0
    assert nov10["coordinator_usd"] == 60.0 and nov10["breakdown"] == "coordinator $60.00, runner $5.00"
    nov11 = days["2026-11-11"]
    assert nov11["cost_usd"] == 11.0 and nov11["partial"] and not nov11["estimated"] and not days["2026-11-10"]["partial"]
    assert round(sum(r["cost_usd"] for r in days.values()), 2) == 35.0 + 54.0 + 22.0  # the estimate and the readings add up


def test_an_estimate_that_overlaps_the_readings_is_left_out_and_days_without_usage_are_zero():
    snaps = [snap("2026-11-08T12:00:00Z", coordinator=100.0), snap("2026-11-11T12:00:00Z", coordinator=130.0)]
    overlapping = {"until": "2026-11-10T00:00:00Z", "days": {"2026-11-07": {"coordinator": 99.0}}}
    days = dc.day_rows(snaps, {"coordinator": 40.0}, overlapping)
    assert [r["day"] for r in days] == ["2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"] and not any(r["estimated"] for r in days)
    assert round(sum(r["cost_usd"] for r in days), 2) == 30.0 and days[1]["cost_usd"] == 10.0  # a whole day of three, read as even
    gap = dc.day_rows([snap("2026-11-11T12:00:00Z", coordinator=100.0)], {"coordinator": 40.0},
                      {"until": "2026-11-11T12:00:00Z", "days": {"2026-11-08": {"coordinator": 20.0}, "2026-11-10": {"coordinator": 5.0}}})
    assert [(r["day"], r["cost_usd"]) for r in gap] == [("2026-11-08", 20.0), ("2026-11-09", 0.0), ("2026-11-10", 5.0), ("2026-11-11", 0.0)]
    assert gap[-1]["estimated"] and gap[-1]["partial"]  # midnight to 5 AM Arizona time, read once and no further


def test_days_inside_the_estimate_are_estimated_even_at_zero_and_a_gap_before_the_readings_is_partial():
    snaps = [snap("2026-11-11T12:00:00Z", coordinator=100.0), snap("2026-11-12T12:00:00Z", coordinator=110.0)]
    covered = {"until": "2026-11-11T12:00:00Z", "days": {"2026-11-08": {"coordinator": 20.0}, "2026-11-10": {"coordinator": 5.0}}}
    days = {r["day"]: r for r in dc.day_rows(snaps, {"coordinator": 40.0}, covered)}
    assert days["2026-11-09"]["cost_usd"] == 0.0 and days["2026-11-09"]["estimated"] and not days["2026-11-09"]["partial"]
    assert days["2026-11-11"]["estimated"] and days["2026-11-11"]["measured"] and not days["2026-11-11"]["partial"]
    short = {"until": "2026-11-10T07:00:00Z", "days": {"2026-11-09": {"coordinator": 80.0}}}  # ends a day before the readings
    days = {r["day"]: r for r in dc.day_rows(snaps, {"coordinator": 40.0}, short)}
    assert days["2026-11-10"]["partial"] and days["2026-11-11"]["partial"] and not days["2026-11-09"]["partial"]
    alone = dc.day_rows(snaps, {"coordinator": 40.0})
    assert alone[0]["day"] == "2026-11-11" and alone[0]["partial"]  # read only from 5 AM Arizona time


def test_a_teammate_first_seen_in_a_later_snapshot_counts_from_when_it_began():
    early = snap("2026-11-11T08:00:00Z", coordinator=100.0)
    later = snap("2026-11-11T20:00:00Z", coordinator=110.0, runner=30.0)
    later["sessions"]["runner"]["created_at"] = "2026-11-10T08:00:00Z"  # a day and a half of it before it was first read
    days = {r["day"]: r for r in dc.day_rows([early, later], {"coordinator": 40.0, "runner": 10.0})}
    assert days["2026-11-10"].get("runner_usd") == pytest.approx(30.0 * 23 / 36, abs=0.01)  # 08:00Z Nov 10 to 07:00Z Nov 11
    assert days["2026-11-11"]["runner_usd"] == pytest.approx(30.0 * 13 / 36, abs=0.01)
    assert days["2026-11-11"]["coordinator_usd"] == 10.0


def test_a_day_is_the_sum_of_its_split_and_a_bad_estimate_file_is_left_out(tmp_path, capsys):
    snaps = [snap("2026-11-11T08:00:00Z", coordinator=100.0, runner=10.0, watchdog=5.0),
             snap("2026-11-11T20:00:00Z", coordinator=100.004, runner=10.004, watchdog=5.004)]
    day = dc.day_rows(snaps, BUDGETS)[0]
    assert day["cost_usd"] == round(sum(day.get(f"{r}_usd", 0.0) for r in BUDGETS), 2)
    hist, out, snapfile, budgets = tmp_path / "history.jsonl", tmp_path / "costs.json", tmp_path / "now.json", tmp_path / "budgets.json"
    budgets.write_text(json.dumps({"daily_usd": BUDGETS}))
    hist.write_text(json.dumps(snap("2026-11-10T21:30:00Z", coordinator=750.0, runner=46.8, watchdog=23.6)) + "\n")
    snapfile.write_text(json.dumps(snap("2026-11-11T01:07:30Z", coordinator=775.2, runner=47.4, watchdog=24.1)))
    (tmp_path / "before.json").write_text(json.dumps({"until": "2026-11-10T21:30:00Z", "days": {"2026-11-09": {"coordinator": "n/a"}}}))
    assert dc.main(["--snapshot", str(snapfile), "--history", str(hist), "--budgets", str(budgets), "--append", "--out", str(out)]) == 0
    assert "left out" in capsys.readouterr().err and len(hist.read_text().splitlines()) == 2 and out.exists()


def test_an_estimate_with_a_day_that_is_not_a_padded_date_is_refused():
    good = {"until": "2026-11-10T21:30:00Z", "days": {"2026-11-09": {"coordinator": 5.0}}}
    assert dc.valid_before(good)
    for key in ("Nov 9", "2026-11-9", "2026-02-30"):
        assert not dc.valid_before({"until": good["until"], "days": {key: {"coordinator": 5.0}}})
