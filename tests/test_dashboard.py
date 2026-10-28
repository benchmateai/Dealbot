import json
import urllib.request

from dashboard.export import export
from dashboard.serve import Dashboard, DashboardServer, index_document
from dashboard.state import DeskState
from dashboard.tail import EventTailer
from desk.clock import BlockClock
from desk.config import DeskConfig
from desk.run import build_desk
from judge.client import DemoJudge, make_judge
from logs.writer import LogWriter, read_events
from questions import load_battery
from tests.helpers import T0


def test_tailer_returns_only_new_complete_lines(tmp_path):
    tailer = EventTailer(tmp_path)
    assert tailer.poll() == []
    path = tmp_path / "events-2023-11-14.jsonl"
    path.write_text('{"kind":"heartbeat","blk":0}\n{"kind":"heartbeat","blk":1}\n')
    assert [r["blk"] for r in tailer.poll()] == [0, 1]
    assert tailer.poll() == []
    with open(path, "a") as fh:
        fh.write('{"kind":"heartbeat","blk":2}\n{"kind":"heart')
    assert [r["blk"] for r in tailer.poll()] == [2]
    with open(path, "a") as fh:
        fh.write('beat","blk":3}\nnot json\n')
    assert [r["blk"] for r in tailer.poll()] == [3]
    (tmp_path / "events-2023-11-15.jsonl").write_text('{"kind":"heartbeat","blk":4}\n')
    assert [r["blk"] for r in tailer.poll()] == [4]


def _demo_run(tmp_path, blocks: int = 60):
    env = {"DESK_MODE": "paper", "DESK_BOT": "gambler", "DESK_SYMBOLS": "ETH-USD", "JUDGE_URL": "stub://demo", "LOG_DIR": str(tmp_path / "logs"), "WARMUP_BLOCKS": "30"}
    cfg = DeskConfig.from_env(env)
    desk, log = build_desk(cfg, start_ms=T0)
    for block in BlockClock(cfg.block_ms, T0, realtime=False).blocks(blocks):
        desk.step(block)
    log.close()
    return cfg, desk


def test_demo_judge_trades_through_the_paper_path(tmp_path):
    assert isinstance(make_judge("stub://demo", "", model="stub-jev-0.0"), DemoJudge)
    cfg, desk = _demo_run(tmp_path)
    events = list(read_events(cfg.log_dir))
    fills = [e for e in events if e["kind"] == "fill"]
    assert len(fills) >= 2 and {f["side"] for f in fills} == {"buy", "sell"}
    kinds = [e["kind"] for e in events]
    assert "position_opened" in kinds and "position_closed" in kinds
    assert all(a["model"] == cfg.jev_model for a in events if a["kind"] == "answer")


def test_state_aggregates_moves_funnel_judge_and_details(tmp_path):
    cfg, desk = _demo_run(tmp_path)
    dashboard = Dashboard(cfg.log_dir)
    assert dashboard.refresh() > 0
    payload = dashboard.payload()
    s = payload["summary"]
    assert s["mode"] == "paper" and s["bot"] == "gambler" and s["trial_id"] == desk.trial_id and s["model"] == cfg.jev_model
    assert s["counts"]["decisions"] > 0 and s["counts"]["fills"] >= 2 and s["counts"]["judge_calls"] == s["counts"]["decisions"] or s["counts"]["judge_calls"] >= s["counts"]["decisions"]
    assert s["equity_usd"] is not None and len(payload["equity"]) >= 6
    kinds = {m["kind"] for m in payload["moves"]}
    assert {"decision", "fill", "position_opened", "position_closed", "trial"} <= kinds
    assert all(m["status"] in ("good", "warning", "critical", "neutral", "info") for m in payload["moves"])
    assert payload["funnel"]["by_stage"] and payload["judge"]["calls"] > 0 and payload["judge"]["models"] == {cfg.jev_model: payload["judge"]["calls"]}
    assert payload["trials"]["n_registered"] == 1 and payload["trials"]["rows"][0]["trial_id"] == desk.trial_id
    assert "details" not in payload
    executed = [m for m in payload["moves"] if m["kind"] == "decision" and m["status"] == "good"][0]
    detail = dashboard.decision(executed["decision_id"])
    assert detail["snapshot"]["snapshot"]["sym"] == "ETH-USD" and detail["decision"]["executed"] is True
    assert set(detail["questions"]) == {q.id for q in load_battery("gambler").questions}
    assert set(detail["answer"]["answers"]) == set(detail["questions"]) and detail["answer"]["model"] == cfg.jev_model
    assert dashboard.decision("nope") is None


def test_state_handles_vetoes_errors_and_calibration():
    state = DeskState()
    state.ingest({"ts": T0, "kind": "veto", "decision_id": "d1", "sym": "ETH-USD", "check": "daily_loss", "detail": "day PnL -150 USD", "blk": 3})
    state.ingest({"ts": T0 + 1, "kind": "decision", "decision_id": "d1", "sym": "ETH-USD", "action": "enter_long", "phase": "entry", "approved": False, "executed": False, "exec_status": "vetoed", "prob": 0.9, "threshold": 0.7, "expected_edge_bps": 60, "blk": 3})
    state.ingest({"ts": T0 + 2, "kind": "error", "where": "desk", "detail": "malformed question battery", "blk": 4})
    state.ingest({"ts": T0 + 3, "kind": "rejection", "sym": "BTC-USD", "stage": "jev", "check": "jev_timeout", "detail": "slow", "blk": 4})
    state.ingest({"ts": T0 + 4, "kind": "outcome", "decision_id": "d1", "qid": "whipsaw", "qkind": "noul", "predicted": 0.9, "realized": True, "status": "resolved"})
    state.ingest({"ts": T0 + 5, "kind": "outcome", "decision_id": "d1", "qid": "dir_20", "qkind": "choice", "predicted": {"up": 0.7, "down": 0.3}, "realized": "down", "status": "resolved"})
    payload = state.to_payload(include_details=True, now_ms=T0 + 10)
    assert payload["vetoes_by_check"] == {"daily_loss": 1} and payload["summary"]["counts"]["vetoed"] == 1
    assert payload["summary"]["fault"] == "malformed question battery" and payload["judge"]["timeouts"] == 1
    statuses = [m["status"] for m in payload["moves"]]
    assert statuses == ["critical", "critical", "critical"]
    assert payload["calibration"]["n"] == 3 and payload["calibration"]["brier"] is not None and sum(b["n"] for b in payload["calibration"]["buckets"]) == 3
    assert payload["details"]["d1"]["vetoes"][0]["check"] == "daily_loss" and payload["rejections"][0]["data"]["check"] == "jev_timeout"


def test_server_serves_page_state_and_details(tmp_path):
    cfg, desk = _demo_run(tmp_path, blocks=20)
    server = DashboardServer(Dashboard(cfg.log_dir), poll_seconds=0.2).start()
    try:
        page = urllib.request.urlopen(server.url + "/").read()
        assert page.startswith(b"<!doctype html>") and b"<title>Dealbot Desk</title>" in page and b"api/state" in page
        state = json.loads(urllib.request.urlopen(server.url + "/api/state").read())
        assert state["source"]["mode"] == "live" and state["summary"]["bot"] == "gambler" and state["moves"]
        did = [m for m in state["moves"] if m["kind"] == "decision"][0]["decision_id"]
        detail = json.loads(urllib.request.urlopen(server.url + "/api/decision/" + did).read())
        assert detail["decision_id"] == did and "questions" in detail
        try:
            urllib.request.urlopen(server.url + "/api/decision/nope")
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("expected 404")
    finally:
        server.stop()
    assert len(index_document()) > 10_000


def test_export_writes_a_static_snapshot(tmp_path):
    cfg, desk = _demo_run(tmp_path, blocks=20)
    out = tmp_path / "out" / "data.json"
    payload = export(cfg.log_dir, out)
    saved = json.loads(out.read_text())
    assert saved["source"]["mode"] == "snapshot" and saved["source"]["exported_ms"] > 0
    assert saved["details"] and saved["batteries"] and saved["summary"]["trial_id"] == desk.trial_id
    assert payload["moves"] == saved["moves"]
