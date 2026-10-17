from collections import Counter

import pytest

from broker.base import Order
from desk.clock import Block, BlockClock
from desk.config import ConfigError, DeskConfig, assert_desk_cannot_see_jev_key, load_env_file
from desk.modes import PaperExecutor, ShadowExecutor, make_executor
from desk.run import build_desk
from logs.writer import LogWriter, read_events
from tests.helpers import T0, FakeJudge


def env(tmp_path, **overrides) -> dict:
    base = {"DESK_MODE": "shadow", "DESK_BOT": "gambler", "DESK_SYMBOLS": "ETH-USD", "JUDGE_URL": "stub://local", "LOG_DIR": str(tmp_path / "logs"), "BLOCK_SECONDS": "12", "WARMUP_BLOCKS": "30"}
    base.update(overrides)
    return base


def run_blocks(desk, cfg, n: int) -> None:
    for block in BlockClock(cfg.block_ms, T0, realtime=False).blocks(n):
        desk.step(block)


def test_config_defaults_and_guards(tmp_path):
    cfg = DeskConfig.from_env(env(tmp_path))
    assert cfg.mode == "shadow" and cfg.jev_model == "stub-jev-0.0" and cfg.limits.pinned_model == cfg.jev_model and cfg.block_ms == 12_000
    assert "desk_secret" not in repr(cfg) and cfg.public_dict()["desk_secret_set"] is False
    with pytest.raises(ConfigError, match="pinned"):
        DeskConfig.from_env(env(tmp_path, JEV_MODEL="jev-latest"))
    with pytest.raises(ConfigError, match="DESK_SECRET"):
        DeskConfig.from_env(env(tmp_path, JUDGE_URL="http://127.0.0.1:8787", JEV_MODEL="jev-1.13.0"))
    with pytest.raises(ConfigError, match="DESK_MODE"):
        DeskConfig.from_env(env(tmp_path, DESK_MODE="live"))
    with pytest.raises(ConfigError, match="never hold the Jev key"):
        assert_desk_cannot_see_jev_key({"TYPESAFE_API_KEY": "tsk-something"})
    assert_desk_cannot_see_jev_key({"TYPESAFE_API_KEY": "   "})
    (tmp_path / "env").write_text("# comment\nDESK_BOT=spy   # inline\nJEV_MODEL='jev-1.13.0'\n\n")
    assert load_env_file(tmp_path / "env") == {"DESK_BOT": "spy", "JEV_MODEL": "jev-1.13.0"}


def test_shadow_mode_labels_decisions_but_never_executes(tmp_path):
    cfg = DeskConfig.from_env(env(tmp_path))
    judge = FakeJudge(cfg.jev_model)
    desk, log = build_desk(cfg, start_ms=T0, judge=judge)
    run_blocks(desk, cfg, 12)
    log.close()
    events = list(read_events(cfg.log_dir))
    kinds = Counter(e["kind"] for e in events)
    assert kinds["would_execute"] >= 1 and kinds["order"] == 0 and kinds["fill"] == 0 and kinds["position_opened"] == 0
    decisions = [e for e in events if e["kind"] == "decision"]
    assert decisions and all(d["executed"] is False for d in decisions) and any(d["approved"] for d in decisions)
    assert all(a["model"] == cfg.jev_model for a in events if a["kind"] == "answer")
    assert desk.book.position is None and desk.fault is None
    assert {c[1] for c in judge.calls} == {"entry"}
    assert kinds["snapshot"] == kinds["question"] == kinds["answer"] == len(judge.calls)


def test_paper_mode_executes_then_manages_without_scanning(tmp_path):
    cfg = DeskConfig.from_env(env(tmp_path, DESK_MODE="paper", DESK_SYMBOLS="ETH-USD,BTC-USD"))
    judge = FakeJudge(cfg.jev_model)
    desk, log = build_desk(cfg, start_ms=T0, judge=judge)
    run_blocks(desk, cfg, 10)
    log.close()
    events = list(read_events(cfg.log_dir))
    fills = [e for e in events if e["kind"] == "fill"]
    assert len(fills) == 1 and fills[0]["side"] == "buy" and fills[0]["sym"] == "ETH-USD"
    assert desk.book.position is not None and desk.book.position.sym == "ETH-USD" and desk.book.position.qty == pytest.approx(0.2)
    opened = [e for e in events if e["kind"] == "position_opened"]
    assert len(opened) == 1
    opened_blk = opened[0]["blk"]
    assert [e for e in events if e.get("phase") == "entry" and e["kind"] in ("decision", "rejection", "answer") and e.get("blk", -1) > opened_blk] == []
    assert {c[1] for c in judge.calls if c[0].split("-")[1] != str(opened_blk)} == {"manage"}
    btc = [e for e in events if e["kind"] == "rejection" and e["sym"] == "BTC-USD"]
    assert btc and btc[0]["stage"] == "hard_facts" and btc[0]["check"] == "risk_precheck:max_position"
    manage_decisions = [e for e in events if e["kind"] == "decision" and e["phase"] == "manage"]
    assert manage_decisions and all(d["action"] == "hold" for d in manage_decisions)
    heartbeat = [e for e in events if e["kind"] == "heartbeat"][-1]
    assert heartbeat["position"]["sym"] == "ETH-USD" and heartbeat["pending_outcomes"] > 0


def test_paper_mode_exits_on_a_confident_exit_signal(tmp_path):
    cfg = DeskConfig.from_env(env(tmp_path, DESK_MODE="paper"))
    judge = FakeJudge(cfg.jev_model, nouls={"thesis_broken": 0.9, "keep_running": 0.1})
    desk, log = build_desk(cfg, start_ms=T0, judge=judge)
    run_blocks(desk, cfg, 2)  # block 0 enters, block 1 exits; a third block would re-enter, which is correct
    log.close()
    events = list(read_events(cfg.log_dir))
    assert [e["side"] for e in events if e["kind"] == "fill"] == ["buy", "sell"]
    assert [e["kind"] for e in events if e["kind"] in ("position_opened", "position_closed")] == ["position_opened", "position_closed"]
    assert desk.book.position is None
    exit_decision = [e for e in events if e["kind"] == "decision" and e["phase"] == "manage"][0]
    assert exit_decision["action"] == "exit" and exit_decision["order"]["reduce_only"] is True and exit_decision["executed"]


def test_model_version_mismatch_is_vetoed_not_executed(tmp_path):
    cfg = DeskConfig.from_env(env(tmp_path, DESK_MODE="paper"))
    judge = FakeJudge("stub-jev-9.9")
    desk, log = build_desk(cfg, start_ms=T0, judge=judge)
    run_blocks(desk, cfg, 2)
    log.close()
    events = list(read_events(cfg.log_dir))
    vetoes = [e for e in events if e["kind"] == "veto"]
    assert vetoes and {v["check"] for v in vetoes} == {"model_version"}
    assert [e for e in events if e["kind"] in ("fill", "order")] == [] and desk.book.position is None
    decision = [e for e in events if e["kind"] == "decision"][0]
    assert decision["approved"] is False and decision["executed"] is False and decision["exec_status"] == "vetoed"


class ExplodingBroker:
    kind = "paper"

    def place_order(self, order, approval):
        raise AssertionError("shadow mode must never touch the broker")


def test_executors(tmp_path):
    with LogWriter(tmp_path) as log:
        order = Order("d:1", "ETH-USD", "buy", 0.1, decision_id="d")
        result = ShadowExecutor(log).execute(order, None, block=Block(0, T0, T0 + 12_000))
        assert result.executed is False and result.status == "shadow"
        assert isinstance(make_executor("shadow", ExplodingBroker(), log), ShadowExecutor)
        assert isinstance(make_executor("paper", ExplodingBroker(), log), PaperExecutor)
        with pytest.raises(ValueError):
            make_executor("live", ExplodingBroker(), log)

        class NotPaper:
            kind = "live"

        with pytest.raises(ValueError):
            PaperExecutor(NotPaper(), log)
    assert [e["kind"] for e in read_events(tmp_path)] == ["would_execute"]
