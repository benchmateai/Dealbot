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
