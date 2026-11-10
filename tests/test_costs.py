"""The team's running cost against its budgets (reports/costs.py)."""

import json

from reports import costs


def snap(at, **sessions):
    return {"at": at, "sessions": {r: {"id": f"s_{r}" if not isinstance(v, tuple) else v[1], "cost_usd": v if not isinstance(v, tuple) else v[0],
                                       "created_at": "2026-11-03T00:00:00Z"} for r, v in sessions.items()}}


BUDGETS = {"coordinator": 40.0, "runner": 10.0, "watchdog": 5.0}


def test_a_first_look_shows_each_session_s_average_a_day_since_it_began():
    c = costs.compare(snap("2026-11-10T00:00:00Z", coordinator=210.0, runner=42.0, watchdog=21.0), None, BUDGETS)
    rows = {r["role"]: r for r in c["rows"]}
    assert rows["coordinator"]["per_day_usd"] == 30.0 and rows["runner"]["per_day_usd"] == 6.0 and not c["over"]
    assert costs.line(c).startswith("costs (first look") and "nobody over budget" in costs.line(c)


def test_a_day_s_spend_is_measured_against_each_budget_and_a_replaced_session_counts_in_full():
    before = snap("2026-11-10T13:30:00Z", coordinator=700.0, runner=40.0, watchdog=20.0)
    after = snap("2026-11-11T13:30:00Z", coordinator=745.0, runner=(3.0, "s_new_runner"), watchdog=24.0)
    c = costs.compare(after, before, BUDGETS)
    rows = {r["role"]: r for r in c["rows"]}
    assert (rows["coordinator"]["spent_usd"], rows["runner"]["spent_usd"], rows["watchdog"]["spent_usd"]) == (45.0, 3.0, 4.0)
    assert rows["runner"]["basis"] == "replaced" and c["over"] == ["coordinator"] and c["team_spent_usd"] == 52.0
    text = costs.line(c, paper_24h=8.89)
    assert "$52.00 over the last 24.0 hours (budget $55.00)" in text and "over budget: coordinator" in text and "+8.89 USD on paper" in text


def test_hours_after_the_morning_a_runaway_is_one_that_already_spent_a_whole_day_s_budget():
    morning = snap("2026-11-11T13:30:00Z", coordinator=745.0, runner=43.0, watchdog=24.0)
    evening = snap("2026-11-11T19:30:00Z", coordinator=760.0, runner=54.5, watchdog=25.0)
    c = costs.compare(evening, morning, BUDGETS)
    assert c["window_hours"] == 6.0 and c["over"] == ["runner"]  # $11.50 in 6 hours against $10 a day; the coordinator's $15 is within its $40


def test_the_ledger_keeps_one_line_a_morning_and_the_supervisor_only_reads_it(tmp_path, capsys):
    ledger, budgets = tmp_path / "ledger.jsonl", tmp_path / "budgets.json"
    budgets.write_text(json.dumps({"daily_usd": BUDGETS}))
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    first.write_text(json.dumps(snap("2026-11-10T13:30:00Z", coordinator=700.0, runner=40.0, watchdog=20.0)))
    second.write_text(json.dumps(snap("2026-11-10T19:30:00Z", coordinator=705.0, runner=41.0, watchdog=20.5)))
    assert costs.main(["--snapshot", str(first), "--ledger", str(ledger), "--budgets", str(budgets), "--record"]) == 0
    assert costs.main(["--snapshot", str(second), "--ledger", str(ledger), "--budgets", str(budgets)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("costs (first look") and out[1].startswith("costs: the team's usage came to $6.50 over the last 6.0 hours")
    assert len(ledger.read_text().splitlines()) == 1


def test_the_shipped_budgets_cover_every_teammate():
    shipped = json.loads(costs.BUDGETS.read_text())["daily_usd"]
    assert set(shipped) == set(costs.ORDER) and all(v > 0 for v in shipped.values())


def test_a_replaced_teammate_s_old_session_counts_for_what_it_spent_after_the_snapshot():
    morning = snap("2026-11-11T13:30:00Z", coordinator=745.0, runner=(40.0, "r1"), watchdog=24.0)
    later = snap("2026-11-11T19:30:00Z", coordinator=750.0, runner=(3.0, "r2"), watchdog=24.5)
    unread = costs.compare(later, morning, BUDGETS)
    assert unread["missing"] == ["runner"] and "not counted" in costs.line(unread)
    later["retired"] = {"r1": {"role": "runner", "cost_usd": 52.0}}  # r1 ran on to $52 before it was replaced
    c = costs.compare(later, morning, BUDGETS)
    rows = {r["role"]: r for r in c["rows"]}
    assert rows["runner"]["spent_usd"] == 15.0 and c["over"] == ["runner"] and c["team_spent_usd"] == 20.5 and not c["missing"]
    assert c["total_usd"] == 750.0 + 3.0 + 24.5 + 52.0


def test_a_teammate_replaced_twice_counts_all_three_sessions_and_the_lifetime_total_never_falls(tmp_path):
    morning = snap("2026-11-11T13:30:00Z", coordinator=745.0, runner=(40.0, "r1"), watchdog=24.0)
    later = snap("2026-11-11T19:30:00Z", coordinator=750.0, runner=(3.0, "r3"), watchdog=24.5)
    later["retired"] = {"r1": {"role": "runner", "cost_usd": 45.0}, "r2": {"role": "runner", "cost_usd": 8.0}}
    c = costs.compare(later, morning, BUDGETS)
    assert {r["role"]: r["spent_usd"] for r in c["rows"]}["runner"] == 16.0 and c["over"] == ["runner"]
    ledger, budgets = tmp_path / "ledger.jsonl", tmp_path / "budgets.json"
    budgets.write_text(json.dumps({"daily_usd": BUDGETS}))
    for name, s in (("m", morning), ("l", later), ("n", snap("2026-11-12T13:30:00Z", coordinator=780.0, runner=(9.0, "r3"), watchdog=27.0))):
        (tmp_path / f"{name}.json").write_text(json.dumps(s))
        costs.main(["--snapshot", str(tmp_path / f"{name}.json"), "--ledger", str(ledger), "--budgets", str(budgets), "--record"])
    last = json.loads(ledger.read_text().splitlines()[-1])
    assert last["retired_all"] == {"r1": 45.0, "r2": 8.0}  # carried into the next morning, so the total keeps them
    assert costs.compare(snap("2026-11-12T19:30:00Z", coordinator=790.0, runner=(10.0, "r3"), watchdog=27.5), last, BUDGETS)["total_usd"] == 790.0 + 10.0 + 27.5 + 53.0


def test_a_replaced_session_the_ledger_already_holds_is_not_counted_again():
    morning = snap("2026-11-11T13:30:00Z", coordinator=745.0, runner=(5.0, "r2"), watchdog=24.0)
    morning["retired_all"] = {"r1": 45.0}  # r1 was replaced by r2 before the morning and counted then
    later = snap("2026-11-11T19:30:00Z", coordinator=750.0, runner=(2.0, "r3"), watchdog=24.5)
    later["retired"] = {"r1": {"role": "runner", "cost_usd": 45.0}, "r2": {"role": "runner", "cost_usd": 7.0}}  # r1 left in by mistake
    c = costs.compare(later, morning, BUDGETS)
    assert {r["role"]: r["spent_usd"] for r in c["rows"]}["runner"] == 4.0  # r3's $2 and r2's $2 after the morning
    assert c["total_usd"] == 750.0 + 2.0 + 24.5 + 45.0 + 7.0
