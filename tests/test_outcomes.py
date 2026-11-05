import math

import pytest

from feed.synthetic import SyntheticFeed
from judge.jev import StubBackend
from logs.writer import LogWriter, read_events
from outcomes.resolver import OutcomeResolver
from outcomes.rules import RULES, PathStats, RuleContext, parse_param
from questions import load_battery
from state import AccountState, build_snapshot
from tests.helpers import BLOCK_MS, T0


def bps(a: float, b: float) -> float:
    return 1e4 * math.log(b / a)


def test_path_stats():
    s = PathStats(100.0, (100.5, 101.0, 99.0, 98.5, 100.0), (100.0, 101.0, 98.5, 100.0))
    assert s.end_ret_bps == pytest.approx(0.0)
    assert s.max_up_bps == pytest.approx(bps(100, 101)) and s.max_down_bps == pytest.approx(-bps(100, 98.5))
    assert s.first_touch(50) == 1 and s.first_touch(120) == -1 and s.first_touch(1000) == 0
    assert s.touches_both(50) and not s.touches_both(120)
    assert s.rv_after_bps is not None and s.rv_after_bps > 0


def test_rules_are_declarative_and_never_see_the_answer():
    ctx = RuleContext(snapshot={"ret_bps": {"w5": 12.0, "w20": -40.0}, "imb": -0.5}, pos_sign=1, rv_bps=10.0, cost_bps=24.0)
    up = PathStats(100.0, (100.1, 100.5, 101.0), (100.0, 100.5, 101.0))
    down = PathStats(100.0, (99.9, 99.5, 99.0), (100.0, 99.5, 99.0))
    assert RULES["direction_first_touch"].fn(up, 50, ctx) == "up" and RULES["direction_first_touch"].fn(down, 50, ctx) == "down"
    assert RULES["continues_w5"].fn(up, 50, ctx) is True and RULES["against_w5_first"].fn(down, 50, ctx) is True
    assert RULES["with_imbalance_first"].fn(down, 50, ctx) is True
    assert RULES["pos_loses_more_than"].fn(down, 50, ctx) is True and RULES["pos_gains"].fn(up, 0, ctx) is True
    assert RULES["pos_gains"].fn(up, 0, RuleContext({}, 0, None, 24.0)) is None
    assert RULES["revert_or_continue"].fn(up, 50, ctx) == "revert" and RULES["revert_or_continue"].fn(down, 50, ctx) == "continue"
    assert RULES["danger_level"].fn(up, 30, ctx) == 2 and RULES["danger_level"].fn(up, 200, ctx) == 0
    assert RULES["lean_realized"].fn(up, 50, ctx) == "bid"
    chop = PathStats(100.0, (101.0, 99.0, 100.0), (100.0, 101.0, 99.0, 100.0))
    assert RULES["regime_realized"].fn(chop, 30, ctx) == "volatile_chop" and RULES["touches_both"].fn(chop, 50, ctx) is True
    assert all(spec.kind in ("noul", "choice", "score") for spec in RULES.values())


def test_parse_param():
    assert parse_param("cost", cost_bps=24.0, rv_bps=10.0) == 24.0
    assert parse_param("2cost", cost_bps=24.0, rv_bps=10.0) == 48.0
    assert parse_param("1.5rv", cost_bps=24.0, rv_bps=10.0) == 15.0
    assert parse_param("rv", cost_bps=24.0, rv_bps=None) is None
    assert parse_param(0, cost_bps=24.0, rv_bps=None) == 0.0 and parse_param("12.5", cost_bps=0, rv_bps=None) == 12.5
    with pytest.raises(ValueError):
        parse_param("twice the cost", cost_bps=24.0, rv_bps=None)


def test_resolver_grades_after_the_horizon_from_the_realized_path(tmp_path):
    feed = SyntheticFeed(("ETH-USD",), start_ms=T0, tick_ms=1000, seed=3)
    as_of = T0 + 40 * BLOCK_MS
    feed.advance(as_of)
    account = AccountState(0.0, 10_000, 10_000, 10_000)
    snap = build_snapshot("ETH-USD", feed.history("ETH-USD"), as_of, 40, account, block_ms=BLOCK_MS)
    battery = load_battery("gambler")
    state = {"mkt": snap.to_dict(), "pos": None, "desk": {"bot": "gambler", "phase": "entry", "cost_bps": 24.0}}
    answers = StubBackend().ask(state, battery.wire(), timeout_s=1).answers
    log = LogWriter(tmp_path)
    resolver = OutcomeResolver(log, block_ms=BLOCK_MS)
    assert resolver.register(decision_id="gambler-40-ETH-USD", bot="gambler", sym="ETH-USD", block=40, snapshot=snap.to_dict(), state=state, battery=battery, answers=answers) == 7
    assert resolver.resolve_due(45, feed) == [] and resolver.pending_count == 7
    feed.advance(as_of + 21 * BLOCK_MS)
    resolved = resolver.resolve_due(50, feed)
    assert {r["qid"] for r in resolved} == {"thesis_broken", "keep_running"} and all(r["status"] == "unresolvable:context" for r in resolved)
    resolved = resolver.resolve_due(60, feed)
    assert {r["qid"] for r in resolved} == {"dir_20", "continuation", "late_entry", "whipsaw", "regime"} and resolver.pending_count == 0
    log.close()
    by_qid = {r["qid"]: r for r in read_events(tmp_path, kinds=("outcome",))}
    assert by_qid["dir_20"]["qkind"] == "choice" and by_qid["dir_20"]["status"] == "resolved" and by_qid["dir_20"]["realized"] in {"up", "down", "flat"}
    assert by_qid["dir_20"]["predicted"] == answers["dir_20"]["probabilities"] and by_qid["dir_20"]["threshold_bps"] == 24.0
    assert isinstance(by_qid["whipsaw"]["realized"], bool) and by_qid["whipsaw"]["predicted"] == answers["whipsaw"]["noul"]
    assert by_qid["dir_20"]["path"]["n"] > 0
