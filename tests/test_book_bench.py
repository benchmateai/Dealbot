import pytest

from book import UNTIL_DAY_END, UNTIL_RESTART, Bench, Book, BookError, OpenPosition
from book.bench import DAY_MS
from broker.base import Order
from tests.helpers import T0


def test_one_open_position_at_a_time():
    book = Book()
    assert book.can_scan()
    book.open(OpenPosition("ETH-USD", 0.2, 2500.0, T0, 1, "d1", "gambler"))
    assert not book.can_scan()
    with pytest.raises(BookError, match="one open position"):
        book.open(OpenPosition("BTC-USD", 0.1, 60_000.0, T0, 1, "d2", "gambler"))
    with pytest.raises(BookError):
        book.set_pending(Order("d3:1", "ETH-USD", "buy", 0.1), 1)
    assert book.close().sym == "ETH-USD" and book.can_scan()
    book.set_pending(Order("d4:1", "ETH-USD", "buy", 0.1, "limit", 2400.0), 2)
    assert not book.can_scan() and book.clear_pending().placed_block == 2 and book.can_scan()


def test_equity_marks_track_peaks_and_day_rollover():
    book = Book()
    book.mark(10_000, T0)
    book.mark(10_500, T0 + 1000)
    book.mark(10_200, T0 + 2000)
    assert book.peak_equity == 10_500 and book.day_pnl() == 200
    state = book.account_state(inventory=0.3)
    assert state.peak_equity_usd == 10_500 and state.day_peak_equity_usd == 10_500 and state.inventory == 0.3
    book.mark(9_900, T0 + DAY_MS)
    assert book.day_pnl() == 0 and book.day_peak_equity == 9_900 and book.peak_equity == 10_500


def test_bench_durations_depend_on_the_reason():
    bench = Bench()
    assert bench.duration_for("spread_too_wide") == 5
    assert bench.duration_for("risk_veto:daily_loss") == UNTIL_DAY_END
    assert bench.duration_for("risk_veto:something_new") == 5
    assert bench.duration_for("risk_veto:model_version") == UNTIL_RESTART
    assert bench.duration_for("never_seen") == 3
    bench.bench("A", "spread_too_wide", block=10, now_ms=T0)
    assert bench.is_benched("A", block=14, now_ms=T0) is not None and bench.is_benched("A", block=15, now_ms=T0) is None
    bench.bench("B", "risk_veto:daily_loss", block=10, now_ms=T0)
    assert bench.is_benched("B", block=10_000, now_ms=T0 + 3600_000) is not None
    assert bench.is_benched("B", block=10_000, now_ms=(T0 // DAY_MS + 1) * DAY_MS) is None
    bench.bench("C", "battery_fault", block=1, now_ms=T0)
    bench.bench("C", "stale_data", block=2, now_ms=T0)
    assert bench.is_benched("C", block=10_000, now_ms=T0 + 10 * DAY_MS).reason == "battery_fault"
    bench.bench("D", "stale_data", block=1, now_ms=T0)
    assert [e.sym for e in bench.expire(block=50, now_ms=T0)] == ["D"]
