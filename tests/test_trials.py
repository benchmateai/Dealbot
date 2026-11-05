import json
import random

import pytest

from desk.config import DeskConfig
from logs.writer import LogWriter
from questions import load_battery
from reports.trials import evaluate, render_markdown, returns_from_heartbeats
from tests.helpers import T0
from trials import TrialRegistry, deflated_sharpe, expected_max_sharpe, min_backtest_years, null_sharpe_variance, probabilistic_sharpe, return_stats, strategy_spec, trial_id


def test_expected_max_sharpe_matches_the_closed_form():
    assert expected_max_sharpe(1, 1.0) == 0.0 and expected_max_sharpe(10, 0.0) == 0.0
    assert expected_max_sharpe(10, 1.0) == pytest.approx(1.5746, abs=0.005)
    assert expected_max_sharpe(10, 4.0) == pytest.approx(2 * 1.5746, abs=0.01)
    assert expected_max_sharpe(1000, 1.0) > expected_max_sharpe(100, 1.0) > expected_max_sharpe(10, 1.0)


def test_probabilistic_sharpe():
    assert probabilistic_sharpe(0.2, 0.2, 100) == pytest.approx(0.5)
    assert probabilistic_sharpe(0.1, 0.0, 101) == pytest.approx(0.8407, abs=0.003)
    assert probabilistic_sharpe(0.1, 0.0, 10_001) > 0.999
    assert probabilistic_sharpe(0.1, 0.0, 1) is None
    assert probabilistic_sharpe(0.1, 0.0, 101, skew=-1.0, kurt=6.0) < probabilistic_sharpe(0.1, 0.0, 101)


def test_deflation_grows_with_the_number_of_trials():
    few = deflated_sharpe(0.3, 250, 2, null_sharpe_variance(250))
    many = deflated_sharpe(0.3, 250, 500, null_sharpe_variance(250))
    assert few.passes_95 and few.dsr > many.dsr and many.noise_max_sharpe > few.noise_max_sharpe
    assert many.haircut_sharpe == pytest.approx(0.3 - many.noise_max_sharpe)
    at_noise = deflated_sharpe(many.noise_max_sharpe, 250, 500, null_sharpe_variance(250))
    assert at_noise.dsr == pytest.approx(0.5, abs=1e-9) and not at_noise.passes_95


def test_return_stats_and_minimum_backtest_length():
    rng = random.Random(1)
    stats = return_stats([rng.gauss(0.001, 0.01) for _ in range(4000)])
    assert stats.n == 4000 and abs(stats.sharpe - 0.1) < 0.05 and abs(stats.skew) < 0.2 and abs(stats.kurt - 3) < 0.5
    assert return_stats([0.0, 0.0, 0.0]) is None and return_stats([0.1, 0.2]) is None
    assert min_backtest_years(1, 1.0) == 0.0
    assert min_backtest_years(10, 1.0) == pytest.approx(1.5746**2, abs=0.02)
    assert min_backtest_years(1000, 1.0) > min_backtest_years(10, 1.0)
    assert min_backtest_years(10, 2.0) == pytest.approx(min_backtest_years(10, 1.0) / 4)
    assert null_sharpe_variance(101) == pytest.approx(0.01)


def _cfg(tmp_path, **overrides) -> DeskConfig:
    env = {"DESK_MODE": "shadow", "DESK_BOT": "gambler", "JUDGE_URL": "stub://local", "LOG_DIR": str(tmp_path / "logs")}
    env.update(overrides)
    return DeskConfig.from_env(env)


def test_fingerprint_ignores_deployment_but_not_strategy(tmp_path):
    base, battery = _cfg(tmp_path), load_battery("gambler")
    deployment_only = _cfg(tmp_path, DESK_MODE="paper", LOG_DIR=str(tmp_path / "elsewhere"))
    assert trial_id(strategy_spec(base, battery)) == trial_id(strategy_spec(deployment_only, battery))
    for key, value in (("ORDER_QTY", "0.3"), ("MAX_POSITION_UNITS", "2"), ("DESK_SYMBOLS", "BTC-USD"), ("FEE_BPS", "5"), ("BLOCK_SECONDS", "6"), ("DESK_BOT", "spy")):
        other = _cfg(tmp_path, **{key: value})
        assert trial_id(strategy_spec(other, load_battery(other.bot))) != trial_id(strategy_spec(base, battery)), key
    spec = strategy_spec(base, battery)
    assert spec["weights"]["enter_long"][0][0] == "dir_20" and spec["thresholds"]["exit"]["wrong_bps"] == 20 and spec["battery_version"] == battery.version()
    json.dumps(spec)


def test_changing_a_weight_is_a_new_trial(tmp_path, monkeypatch):
    import trials.fingerprint as fp
    from policy.weights import Term

    cfg, battery = _cfg(tmp_path), load_battery("gambler")
    before = trial_id(strategy_spec(cfg, battery))
    tweaked = {**fp.WEIGHTS, "gambler": {**fp.WEIGHTS["gambler"], "enter_long": (Term("dir_20", "choice:up", 0.6), Term("late_entry", "not_noul", 0.2), Term("whipsaw", "not_noul", 0.1), Term("regime", "choice:trending", 0.1))}}
    monkeypatch.setattr(fp, "WEIGHTS", tweaked)
    assert trial_id(strategy_spec(cfg, battery)) != before


def test_registry_counts_every_run_and_persists(tmp_path):
    path = tmp_path / "trials.json"
    reg = TrialRegistry(path)
    a = reg.register_run({"bot": "gambler", "x": 1}, mode="shadow", ts_ms=T0)
    a2 = reg.register_run({"bot": "gambler", "x": 1}, mode="paper", ts_ms=T0 + 5)
    b = reg.register_run({"bot": "gambler", "x": 2}, mode="shadow", ts_ms=T0 + 9)
    assert a.trial_id == a2.trial_id != b.trial_id and a2.runs == 2 and a2.modes == ["shadow", "paper"] and reg.count() == 2
    reg.record_evaluation(a.trial_id, {"sharpe": 0.1, "n_obs": 50})
    again = TrialRegistry(path)
    assert again.count() == 2 and again.get(a.trial_id).runs == 2 and again.sharpes() == [0.1]
    assert [e.trial_id for e in again.entries()] == [a.trial_id, b.trial_id]
    assert not list(tmp_path.glob(".trials-*"))


def _write_trial_log(log_dir, tid: str, spec: dict, equities: list[float], every: int = 10) -> None:
    with LogWriter(log_dir) as log:
        log.write("trial", {"trial_id": tid, "spec": spec, "run": 1}, ts_ms=T0)
        for i, equity in enumerate(equities):
            log.write("heartbeat", {"blk": i * every, "trial_id": tid, "equity_usd": equity}, ts_ms=T0 + i * every * 12_000)


def test_returns_only_between_consecutive_heartbeats_of_one_run():
    points = [(0, 100.0), (10, 101.0), (20, 101.0), (0, 100.0), (10, 99.0), (30, 120.0)]
    assert returns_from_heartbeats(points, 10) == pytest.approx([0.01, 0.0, -0.01])


def test_report_deflates_survivors_and_counts_every_trial(tmp_path):
    reg = TrialRegistry(tmp_path / "trials.json")
    spec_a = {"bot": "gambler", "heartbeat_every_blocks": 10, "block_seconds": 12}
    spec_b, spec_c = {**spec_a, "order_qty": 0.3}, {**spec_a, "order_qty": 0.5}
    a = reg.register_run(spec_a, mode="paper", ts_ms=T0)
    b = reg.register_run(spec_b, mode="paper", ts_ms=T0 + 1)
    c = reg.register_run(spec_c, mode="shadow", ts_ms=T0 + 2)
    rng = random.Random(7)
    drift, noise = [10_000.0], [10_000.0]
    for _ in range(800):
        drift.append(drift[-1] * (1 + rng.gauss(0.003, 0.01)))
        noise.append(noise[-1] * (1 + rng.gauss(0.0, 0.01)))
    log_dir = tmp_path / "logs"
    _write_trial_log(log_dir, a.trial_id, spec_a, drift)
    _write_trial_log(log_dir, b.trial_id, spec_b, noise)
    _write_trial_log(log_dir, c.trial_id, spec_c, [10_000.0] * 200)
    report = evaluate(reg, log_dir, now_ms=T0)
    assert report.n_registered == report.n_trials == 3 and report.n_evaluated == 2 and report.var_sharpe > 0
    rows = {r.trial_id: r for r in report.rows}
    assert rows[a.trial_id].passes_95 and not rows[b.trial_id].passes_95 and rows[a.trial_id].dsr > rows[b.trial_id].dsr
    assert rows[a.trial_id].haircut_annual == pytest.approx(rows[a.trial_id].sharpe_annual - rows[a.trial_id].noise_max_annual)
    assert rows[c.trial_id].sharpe_annual is None and "no variance" in rows[c.trial_id].note
    assert {r.trial_id: r for r in evaluate(reg, log_dir, effective_trials=5000, now_ms=T0).rows}[a.trial_id].dsr < rows[a.trial_id].dsr
    text = render_markdown(report)
    assert a.trial_id in text and "Minimum backtest length" in text and "| yes |" in text and "| no |" in text
    assert TrialRegistry(tmp_path / "trials.json").get(a.trial_id).evaluation["n_obs"] == 800
