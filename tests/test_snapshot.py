import pytest

from feed.base import Tick
from state import TOKEN_BUDGET, AccountState, InsufficientData, build_snapshot
from tests.helpers import BLOCK_MS, make_ticks

ACCOUNT = AccountState(inventory=0.0, equity_usd=10_000, peak_equity_usd=10_000, day_peak_equity_usd=10_000)
FIELDS = {"sym", "as_of", "blk", "mid", "spr_bps", "imb", "rv_bps", "ret_bps", "n", "inv", "inv_usd", "dd_bps", "dd_day_bps"}


def test_uses_only_ticks_strictly_before_as_of():
    ticks = make_ticks(400)
    as_of = ticks[300].ts
    clean = build_snapshot("ETH-USD", ticks[:300], as_of, 7, ACCOUNT, block_ms=BLOCK_MS)
    poisoned = ticks[:300] + [Tick(as_of, 1.0, 1.01, 1, 1), Tick(as_of + 1, 99_999.0, 99_999.5, 1, 1)] + ticks[301:]
    assert build_snapshot("ETH-USD", poisoned, as_of, 7, ACCOUNT, block_ms=BLOCK_MS).to_json() == clean.to_json()
    assert clean.n == 300


def test_deterministic_and_complete():
    ticks = make_ticks(400)
    a = build_snapshot("ETH-USD", ticks, ticks[-1].ts + 1, 3, ACCOUNT, block_ms=BLOCK_MS)
    b = build_snapshot("ETH-USD", list(reversed(ticks)), ticks[-1].ts + 1, 3, ACCOUNT, block_ms=BLOCK_MS)
    assert a == b and a.to_json() == b.to_json()
    assert set(a.to_dict()) == FIELDS
    assert set(a.ret_bps) == {"w1", "w5", "w20"}
    assert a.rv_bps is not None and a.rv_bps > 0
    assert a.spr_bps == pytest.approx(2.0, abs=0.05)
    assert a.imb == pytest.approx((5 - 4) / 9, abs=1e-3)


def test_token_budget_holds_under_adversarial_values():
    ticks = [Tick(1_700_000_000_000 + i * 1000, 123_456_789.123456, 123_457_001.987654, 987_654_321.123, 0.001) for i in range(400)]
    account = AccountState(inventory=-123_456.654321, equity_usd=1_234_567_890.12, peak_equity_usd=2_234_567_890.12, day_peak_equity_usd=1_334_567_890.12)
    snap = build_snapshot("VERYLONGSYMBOLNAME-PERP-USDC", ticks, ticks[-1].ts + 1, 123_456_789, account, block_ms=BLOCK_MS)
    assert snap.tokens() <= TOKEN_BUDGET
    assert snap.dd_bps < 0 and snap.dd_day_bps < 0


def test_insufficient_data_raises():
    ticks = make_ticks(3)
    with pytest.raises(InsufficientData):
        build_snapshot("ETH-USD", ticks, ticks[1].ts, 0, ACCOUNT, block_ms=BLOCK_MS)


def test_returns_reference_the_right_window():
    ticks = make_ticks(400)
    as_of = ticks[-1].ts + 1
    snap = build_snapshot("ETH-USD", ticks, as_of, 0, ACCOUNT, block_ms=BLOCK_MS)
    import math
    ref = [t for t in ticks if t.ts < as_of - BLOCK_MS][-1]
    assert snap.ret_bps["w1"] == pytest.approx(1e4 * math.log(ticks[-1].mid / ref.mid), abs=0.11)
