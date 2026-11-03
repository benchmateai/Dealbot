"""The pre-flight scenario runs the desk on its real default configuration with sane simulated data and a
confident judge. It must open a position; each defect found live on 2026-11-03 must make it fail by name."""

import pytest

from desk.preflight import run_scenario

KALSHI = {"DESK_MODE": "paper", "DESK_BOT": "kalshi", "FEED": "kalshi", "DESK_SYMBOLS": "KXETH15M,KXBTC15M", "FEED_POLL_MS": "5000", "JEV_MODEL": "jev-1.14.0"}


def test_the_default_kalshi_desk_opens_a_position_on_sane_data():
    result = run_scenario(KALSHI)
    assert result.ok, result.summary()
    assert result.opened == 1 and result.judge_calls > 10 and not result.blockers, result.summary()


@pytest.mark.parametrize(
    "override, check, blocks_everything",
    [
        ({"MAX_POSITION_UNITS": "1"}, "risk_precheck:max_position", True),  # the spot-sized limit that vetoed every order
        ({"MAX_SPREAD_BPS": "100"}, "spread_too_wide", True),  # 1 cent: tighter than the market ever quotes
        ({"RANGE_GUARD_REF_BPS": "50"}, "risk_precheck:range_guard", False),  # half a cent reads normal moves as bad data
    ],
)
def test_a_bad_setting_is_named_by_the_scenario(override, check, blocks_everything):
    result = run_scenario({**KALSHI, **override})
    assert check in result.blockers, result.summary()
    assert result.ok is not blocks_everything, result.summary()


def test_the_default_spot_desk_opens_a_position_on_sane_data():
    result = run_scenario({"DESK_MODE": "paper", "DESK_BOT": "gambler", "FEED": "coinbase", "DESK_SYMBOLS": "ETH-USD", "JEV_MODEL": "jev-1.14.0"})
    assert result.ok, result.summary()


def test_each_block_tapes_both_series_without_changing_what_the_desk_does(monkeypatch):
    from desk.desk import TAPE_FIELDS, Desk

    result = run_scenario(KALSHI)
    tapes = [e for e in result.events if e["kind"] == "tape"]
    assert [e["blk"] for e in tapes] == sorted({e["blk"] for e in tapes}) and len(tapes) == result.blocks
    live = [e for e in tapes if all(c["expires_in_s"] is not None and c["expires_in_s"] > 0 and c["yes_bid"] is not None for c in e["contracts"].values())]
    assert live, "some blocks have both series trading"
    for c in live[len(live) // 2]["contracts"].values():
        assert set(c) == set(TAPE_FIELDS) | {"yes_bid", "yes_ask", "quote_ts"}
        assert c["ticker"] and c["spot"] and c["strike"] and c["strike_type"] and c["underlying_rv_bps"] and c["model_p_yes"] is not None
        assert c["quote_ts"] <= next(e["ts"] for e in tapes if e is live[len(live) // 2])
    assert result.ok and result.opened == 1

    monkeypatch.setattr(Desk, "_tape", lambda self, block: None)
    without = run_scenario(KALSHI)
    assert [e for e in result.events if e["kind"] != "tape"] == without.events  # the tape changes nothing else


def test_a_failing_tape_never_stops_the_desk(monkeypatch):
    from logs.writer import LogWriter

    real = LogWriter.write

    def write(self, kind, record, *, ts_ms=None):
        if kind == "tape":
            raise OSError("disk full")
        return real(self, kind, record, ts_ms=ts_ms)

    monkeypatch.setattr(LogWriter, "write", write)
    result = run_scenario(KALSHI)
    assert result.ok and result.opened == 1 and not [e for e in result.events if e["kind"] == "tape"]


def test_the_tape_takes_quotes_only_from_the_current_contract():
    from types import SimpleNamespace

    from desk.clock import Block
    from desk.desk import Desk
    from feed.base import Tick

    class Feed:  # just rolled over: the series' last tick is the expired contract's, the new contract has none yet
        def __init__(self):
            self.ticks = []

        def extra_state(self, sym, ts, block=0):
            return {"ticker": f"{sym}-NEW", "strike": 2250.0, "strike_type": "greater_or_equal", "expires_in_s": 880, "yes_bid": 0.01, "yes_ask": 0.03, "spot": 2251.0, "underlying_rv_bps": 2.0, "model_p_yes": 0.55, "tradable": False}

        def snapshot_history(self, sym):
            return self.ticks

    records = []
    fake = SimpleNamespace(_feed=Feed(), _cfg=SimpleNamespace(symbols=("KXETH15M",)), _log=SimpleNamespace(write=lambda kind, rec, ts_ms=None: records.append(rec)))
    Desk._tape(fake, Block(number=7, ts_ms=1_000_000, next_ts_ms=1_012_000))
    c = records[-1]["contracts"]["KXETH15M"]
    assert (c["ticker"], c["yes_bid"], c["yes_ask"], c["quote_ts"]) == ("KXETH15M-NEW", None, None, None)
    fake._feed.ticks = [Tick(ts=1_005_000, bid=0.52, ask=0.54, bid_qty=10, ask_qty=10)]
    Desk._tape(fake, Block(number=8, ts_ms=1_012_000, next_ts_ms=1_024_000))
    c = records[-1]["contracts"]["KXETH15M"]
    assert (c["yes_bid"], c["yes_ask"], c["quote_ts"]) == (0.52, 0.54, 1_005_000)
