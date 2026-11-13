import pytest

from broker import BrokerError, PaperBroker, make_broker
from broker.base import Order
from feed.base import Tick
from risk import RiskGate
from tests.helpers import LIMITS, T0, risk_ctx


def setup():
    gate = RiskGate(LIMITS)
    broker = PaperBroker(gate, cash_usd=10_000, fee_bps=10, maker_fee_bps=2, gas_usd=0.5, slippage_bps=0)
    broker.on_tick("ETH-USD", Tick(T0, 2499.0, 2501.0, 5, 5))
    return gate, broker


def place(gate, broker, order, **ctx):
    verdict = gate.check(order, risk_ctx(**ctx))
    assert verdict.approved, verdict.vetoes
    return broker.place_order(order, verdict.approval)


def test_market_round_trip_books_fees_gas_and_realized_pnl():
    gate, broker = setup()
    ack = place(gate, broker, Order("d1:1", "ETH-USD", "buy", 0.2, decision_id="d1"))
    assert ack.status == "filled" and ack.fill.price == 2501.0
    assert broker.cash == pytest.approx(10_000 - 500.2 - 0.5002 - 0.5)
    assert broker.position("ETH-USD").qty == pytest.approx(0.2) and broker.position("ETH-USD").avg_price == 2501.0
    assert broker.equity({"ETH-USD": 2500.0}) == pytest.approx(10_000 - 0.5002 - 0.5 - 0.2)
    broker.on_tick("ETH-USD", Tick(T0 + 1000, 2509.0, 2511.0, 5, 5))
    ack = place(gate, broker, Order("d2:2", "ETH-USD", "sell", 0.2, reduce_only=True, decision_id="d2"), position_units=0.2, expected_edge_bps=0.0)
    assert ack.fill.realized_pnl_usd == pytest.approx(0.2 * (2509.0 - 2501.0))
    assert broker.position("ETH-USD").qty == 0 and broker.positions() == {}
    assert broker.position("ETH-USD").fees_usd == pytest.approx(0.5002 + 0.5 + 0.5018 + 0.5)


def test_limit_order_rests_then_fills_on_a_crossing_tick():
    gate, broker = setup()
    ack = place(gate, broker, Order("d1:1", "ETH-USD", "buy", 0.2, "limit", 2495.0, decision_id="d1"))
    assert ack.status == "resting" and [o.id for o in broker.open_orders("ETH-USD")] == ["d1:1"]
    assert broker.on_tick("ETH-USD", Tick(T0 + 1000, 2497.0, 2498.0, 5, 5)) == []
    fills = broker.on_tick("ETH-USD", Tick(T0 + 2000, 2493.0, 2494.0, 5, 5))
    assert len(fills) == 1 and fills[0].price == 2495.0 and broker.open_orders() == []
    assert fills[0].fee_usd == pytest.approx(0.2 * 2495.0 * 2 / 1e4)  # maker fee on a resting fill
    assert broker.cancel("d1:1") is False


def test_reduce_only_without_a_position_is_rejected():
    gate, broker = setup()
    ack = place(gate, broker, Order("d1:1", "ETH-USD", "sell", 0.2, reduce_only=True, decision_id="d1"))
    assert ack.status == "rejected" and ack.reason == "reduce_only_violation"


def test_only_the_paper_broker_exists():
    with pytest.raises(BrokerError, match="disabled by design"):
        make_broker("live", RiskGate(LIMITS), cash_usd=1)
    assert make_broker("paper", RiskGate(LIMITS), cash_usd=1, fee_bps=0, gas_usd=0).kind == "paper"
