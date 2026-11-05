from book.bench import Bench
from filter import Candidate, FinalPick, FreeCut, Funnel, FunnelContext, HardFacts, JevStage
from judge.client import Backoff, JudgeMalformed, JudgeRateLimited, JudgeTimeout
from logs.writer import LogWriter, read_events
from policy.thresholds import EDGE
from questions import load_battery
from risk import RiskGate
from state.snapshot import Snapshot
from tests.helpers import BLOCK_MS, LIMITS, PINNED, T0, FakeJudge

BATTERY = load_battery("gambler")


def snap(sym: str, *, spr_bps: float = 2.0, mid: float = 2500.0) -> Snapshot:
    return Snapshot(sym, T0, 5, mid, spr_bps, 0.1, 10.0, {"w1": 1.0, "w5": 5.0, "w20": -3.0}, 200, 0.0, 0.0, 0.0, 0.0)


def candidate(sym: str, **kw) -> Candidate:
    s = snap(sym, **kw)
    return Candidate(sym, s, {"mkt": s.to_dict(), "pos": None, "desk": {"bot": "gambler", "phase": "entry", "cost_bps": 24.0}}, reference_mid=s.mid, cost_bps=24.0)


def context(tmp_path, **kw) -> FunnelContext:
    base = dict(block=5, now_ms=T0 + 1000, deadline_ms=T0 + 10_000, bot="gambler", phase="entry", mode="shadow", equity_usd=10_000, day_pnl_usd=0.0, bench=Bench(), log=LogWriter(tmp_path / "logs"))
    base.update(kw)
    return FunnelContext(**base)


def free_cut(**kw) -> FreeCut:
    return FreeCut(max_spread_bps=20, rv_min_bps=1, rv_max_bps=500, min_ticks=30, max_stale_ms=2 * BLOCK_MS, **kw)


def test_cheapest_check_first_and_rejections_are_logged_and_benched(tmp_path):
    judge = FakeJudge(PINNED)
    funnel = Funnel([free_cut(), HardFacts(RiskGate(LIMITS), EDGE["gambler"], 0.2), JevStage(judge, BATTERY, Backoff()), FinalPick()])
    assert funnel.stage_names == ["free_cut", "hard_facts", "jev", "final_pick"]
    ctx = context(tmp_path)
    result = funnel.run([candidate("WIDE-USD", spr_bps=50.0), candidate("BIG-USD", mid=60_000.0), candidate("ETH-USD")], ctx)
    checks = {(r.sym, r.stage, r.check) for r in result.rejections}
    assert ("WIDE-USD", "free_cut", "spread_too_wide") in checks
    assert ("BIG-USD", "hard_facts", "risk_precheck:max_position") in checks
    assert [c.sym for c in result.survivors] == ["ETH-USD"] and result.survivors[0].pick.action == "enter_long"
    assert [c[0] for c in judge.calls] == ["gambler-5-ETH-USD"]
    assert [(c.stage, c.entered, c.survived) for c in result.counts] == [("free_cut", 3, 2), ("hard_facts", 2, 1), ("jev", 1, 1), ("final_pick", 1, 1)]
    ctx.log.close()
    logged = [(e["sym"], e["stage"], e["check"]) for e in read_events(tmp_path / "logs", kinds=("rejection",))]
    assert set(logged) == checks
    assert ctx.bench.is_benched("WIDE-USD", block=9, now_ms=T0).reason == "spread_too_wide"
    assert ctx.bench.is_benched("WIDE-USD", block=10, now_ms=T0) is None
    assert {e["kind"] for e in read_events(tmp_path / "logs")} >= {"snapshot", "question", "answer", "rejection"}


def test_benched_symbols_are_cut_for_free_without_a_jev_call(tmp_path):
    judge = FakeJudge(PINNED)
    ctx = context(tmp_path)
    ctx.bench.bench("ETH-USD", "below_threshold", block=5, now_ms=T0)
    result = Funnel([free_cut(), JevStage(judge, BATTERY, Backoff()), FinalPick()]).run([candidate("ETH-USD")], ctx)
    assert [r.check for r in result.rejections] == ["benched"] and judge.calls == []


def test_hold_decisions_are_logged_with_the_policy_numbers(tmp_path):
    judge = FakeJudge(PINNED, favorite="flat")
    ctx = context(tmp_path)
    result = Funnel([JevStage(judge, BATTERY, Backoff()), FinalPick()]).run([candidate("ETH-USD")], ctx)
    assert result.survivors == [] and result.rejections[0].check == "below_threshold"
    ctx.log.close()
    holds = list(read_events(tmp_path / "logs", kinds=("decision",)))
    assert len(holds) == 1 and holds[0]["action"] == "hold" and holds[0]["executed"] is False and holds[0]["scores"]


def test_jev_timeout_rate_limit_and_malformed_are_handled_distinctly(tmp_path):
    backoff = Backoff()
    ctx = context(tmp_path)
    timeout = Funnel([JevStage(FakeJudge(PINNED, raise_exc=JudgeTimeout("slow")), BATTERY, backoff)]).run([candidate("ETH-USD")], ctx)
    assert [r.check for r in timeout.rejections] == ["jev_timeout"] and ctx.fault is None
    limited = Funnel([JevStage(FakeJudge(PINNED, raise_exc=JudgeRateLimited("429", retry_after_ms=5000)), BATTERY, backoff)]).run([candidate("ETH-USD")], ctx)
    assert [r.check for r in limited.rejections] == ["jev_rate_limited"] and backoff.is_blocked(ctx.now_ms + 4000)
    healthy = FakeJudge(PINNED)
    blocked = Funnel([JevStage(healthy, BATTERY, backoff)]).run([candidate("ETH-USD")], ctx)
    assert [r.check for r in blocked.rejections] == ["jev_backoff"] and healthy.calls == []
    malformed = Funnel([JevStage(FakeJudge(PINNED, raise_exc=JudgeMalformed("bad question")), BATTERY, Backoff())]).run([candidate("ETH-USD")], ctx)
    assert [r.check for r in malformed.rejections] == ["battery_fault"] and "never retried" in ctx.fault
    again = Funnel([JevStage(healthy, BATTERY, Backoff())]).run([candidate("ETH-USD")], ctx)
    assert [r.check for r in again.rejections] == ["battery_fault"] and healthy.calls == []


def test_deadline_already_passed_means_hold_without_a_call(tmp_path):
    judge = FakeJudge(PINNED)
    ctx = context(tmp_path, now_ms=T0 + 20_000, deadline_ms=T0 + 10_000)
    result = Funnel([JevStage(judge, BATTERY, Backoff())]).run([candidate("ETH-USD")], ctx)
    assert [r.check for r in result.rejections] == ["jev_deadline_passed"] and judge.calls == []
