from logs.writer import LogWriter
from reports.calibration import Forecast, brier, buckets, forecasts_from_outcomes, reliability_svg, render_markdown
from reports.daily import render_markdown as daily_markdown, summarize
from tests.helpers import T0


def test_brier_and_buckets():
    assert brier([Forecast("b", "q", "yes", 1.0, 1), Forecast("b", "q", "yes", 0.0, 0)]) == 0.0
    assert brier([Forecast("b", "q", "yes", 0.5, 1)]) == 0.25
    assert brier([]) is None
    forecasts = [Forecast("b", "q", "yes", p, y) for p, y in ((0.05, 0), (0.12, 0), (0.18, 1), (0.95, 1), (1.0, 1), (0.55, 0))]
    bks = buckets(forecasts)
    assert len(bks) == 10 and sum(b.n for b in bks) == len(forecasts)
    assert bks[1].n == 2 and bks[1].observed == 0.5 and bks[9].n == 2 and bks[0].n == 1 and bks[4].n == 0 and bks[4].mean_p is None


def test_forecasts_expand_choice_answers_one_vs_rest():
    outcomes = [
        {"qkind": "noul", "bot": "spy", "qid": "stale_next", "predicted": 0.7, "realized": True, "status": "resolved"},
        {"qkind": "choice", "bot": "gambler", "qid": "dir_20", "predicted": {"up": 0.6, "down": 0.3, "flat": 0.1, "other": 0.0}, "realized": "down", "status": "resolved"},
        {"qkind": "score", "bot": "spy", "qid": "danger", "predicted": {"0": 0.8, "1": 0.2}, "realized": 1, "status": "resolved"},
        {"qkind": "noul", "bot": "spy", "qid": "exit_now", "predicted": 0.2, "realized": None, "status": "unresolvable:context"},
    ]
    fs = forecasts_from_outcomes(outcomes)
    assert [(f.qid, f.label, f.p, f.y) for f in fs] == [
        ("stale_next", "yes", 0.7, 1),
        ("dir_20", "up", 0.6, 0), ("dir_20", "down", 0.3, 1), ("dir_20", "flat", 0.1, 0), ("dir_20", "other", 0.0, 0),
        ("danger", "0", 0.8, 0), ("danger", "1", 0.2, 1),
    ]
    bks = buckets(fs)
    svg = reliability_svg(bks, title="Reliability", subtitle="test")
    assert svg.startswith("<svg") and "Perfect calibration" in svg and "prefers-color-scheme: dark" in svg and "<circle" in svg
    md = render_markdown(fs, bks, svg_name="r.svg")
    assert "Brier score" in md and "| gambler | dir_20 | down |" in md


def test_daily_summary_lists_every_veto(tmp_path):
    with LogWriter(tmp_path) as log:
        log.write("heartbeat", {"blk": 0, "equity_usd": 10_000.0}, ts_ms=T0)
        log.write("decision", {"decision_id": "d1", "bot": "gambler", "phase": "entry", "action": "enter_long", "approved": False, "executed": False}, ts_ms=T0 + 1)
        log.write("veto", {"decision_id": "d1", "sym": "ETH-USD", "check": "fees_plus_gas", "detail": "edge too small"}, ts_ms=T0 + 1)
        log.write("veto", {"decision_id": "d1", "sym": "ETH-USD", "check": "daily_loss", "detail": "day pnl below limit"}, ts_ms=T0 + 1)
        log.write("decision", {"decision_id": "d2", "bot": "gambler", "phase": "entry", "action": "enter_long", "approved": True, "executed": True}, ts_ms=T0 + 2)
        log.write("fill", {"order_id": "d2:1", "sym": "ETH-USD", "side": "buy", "qty": 0.2, "price": 2500.0, "fee_usd": 0.5, "gas_usd": 0.5, "realized_pnl_usd": 0.0}, ts_ms=T0 + 2)
        log.write("fill", {"order_id": "d3:2", "sym": "ETH-USD", "side": "sell", "qty": 0.2, "price": 2510.0, "fee_usd": 0.5, "gas_usd": 0.5, "realized_pnl_usd": 2.0}, ts_ms=T0 + 3)
        log.write("rejection", {"sym": "BTC-USD", "stage": "free_cut", "check": "spread_too_wide"}, ts_ms=T0 + 3)
        log.write("heartbeat", {"blk": 10, "equity_usd": 10_001.0}, ts_ms=T0 + 4)
    from logs.writer import read_events

    summary = summarize(list(read_events(tmp_path)))
    assert summary["decisions"] == 2 and summary["executed"] == 1 and summary["vetoed"] == 1 and summary["fills"] == 2
    assert summary["realized_after_fees_usd"] == 2.0 - 2.0 and summary["vetoes_by_check"] == {"fees_plus_gas": 1, "daily_loss": 1}
    text = daily_markdown("2023-11-14", summary)
    assert "fees_plus_gas" in text and "daily_loss" in text and "spread_too_wide" in text and "10000.00 -> 10001.00" in text
