import pytest

from desk.clock import BlockClock
from desk.config import DeskConfig
from desk.persist import load_checkpoint
from desk.run import build_desk
from judge.pin_model import newest_pinned
from logs.writer import read_events
from tests.helpers import T0, FakeJudge


def env(tmp_path, **overrides) -> dict:
    base = {"DESK_MODE": "paper", "DESK_BOT": "gambler", "DESK_SYMBOLS": "ETH-USD", "JUDGE_URL": "stub://local", "LOG_DIR": str(tmp_path / "logs"), "WARMUP_BLOCKS": "30"}
    base.update(overrides)
    return base


def test_checkpoint_resumes_account_book_bench_outcomes_and_block_counter(tmp_path):
    cfg = DeskConfig.from_env(env(tmp_path))
    state = tmp_path / "state.json"
    desk1, log1 = build_desk(cfg, start_ms=T0, judge=FakeJudge(cfg.jev_model))
    desk1.enable_checkpoints(str(state))
    for block in BlockClock(cfg.block_ms, T0, realtime=False).blocks(4):
        desk1.step(block)
    log1.close()
    assert desk1.book.position is not None and desk1.last_block == 3
    saved = load_checkpoint(state)
    assert saved["last_block"] == 3 and saved["book"]["position"]["sym"] == "ETH-USD" and saved["feed"]["ETH-USD"] and saved["outcomes"]
    assert saved["broker"]["positions"]["ETH-USD"]["qty"] == pytest.approx(0.2) and saved["trial_id"] == desk1.trial_id

    desk2, log2 = build_desk(cfg, start_ms=T0 + 4 * cfg.block_ms, judge=FakeJudge(cfg.jev_model))
    desk2.restore(saved)
    desk2.enable_checkpoints(str(state))
    again = desk2.checkpoint()
    assert desk2.book.position == desk1.book.position
    assert again["broker"]["cash"] == pytest.approx(saved["broker"]["cash"]) and again["broker"]["positions"] == saved["broker"]["positions"]
    assert len(again["outcomes"]) == len(saved["outcomes"]) and again["order_seq"] == saved["order_seq"]
    assert desk2.feed.history("ETH-USD") and desk2.feed.history("ETH-USD")[-1].ts < T0 + 4 * cfg.block_ms
    for block in BlockClock(cfg.block_ms, T0 + 4 * cfg.block_ms, realtime=False, start_number=4).blocks(3):
        desk2.step(block)
    log2.close()
    assert desk2.last_block == 6 and load_checkpoint(state)["last_block"] == 6
    events = list(read_events(cfg.log_dir))
    resumed = [e for e in events if e["kind"] == "heartbeat" and e.get("resumed")]
    assert len(resumed) == 1 and resumed[0]["blk"] == 3 and resumed[0]["position"]["sym"] == "ETH-USD"
    manage = [e for e in events if e["kind"] == "decision" and e["phase"] == "manage"]
    assert manage and max(e["blk"] for e in manage) == 6 and all(e["blk"] >= 1 for e in manage)
    assert [e["blk"] for e in events if e["kind"] == "decision" and e["phase"] == "entry"] == [0]


def test_block_clock_continues_numbering():
    blocks = list(BlockClock(1000, 5_000, realtime=False, start_number=7).blocks(3))
    assert [(b.number, b.ts_ms) for b in blocks] == [(7, 5_000), (8, 6_000), (9, 7_000)]


def test_question_text_is_logged_once_per_battery_version(tmp_path):
    cfg = DeskConfig.from_env(env(tmp_path, DESK_MODE="shadow"))
    desk, log = build_desk(cfg, start_ms=T0, judge=FakeJudge(cfg.jev_model))
    for block in BlockClock(cfg.block_ms, T0, realtime=False).blocks(6):
        desk.step(block)
    log.close()
    questions = list(read_events(cfg.log_dir, kinds=("question",)))
    assert len(questions) == 6 and questions[0]["questions"] and all(q["questions"] is None for q in questions[1:])
    assert all(q["battery_version"] == questions[0]["battery_version"] and q["question_ids"] == list(questions[0]["questions"]) for q in questions)


def test_newest_pinned_model_skips_aliases():
    assert newest_pinned(["jev-latest", "jev", "jev-1.13.0", "jev-1.14-20261014", "jev-preview"]) == "jev-1.14-20261014"
    assert newest_pinned(["jev-1.13.0", "jev-1.13.2"]) == "jev-1.13.2"
    assert newest_pinned(["jev-latest", "jev"]) is None and newest_pinned([]) is None
