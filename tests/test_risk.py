import pytest

from broker import PaperBroker
from broker.base import Order
from feed.base import Tick
from risk import RiskApproval, RiskBypassError, RiskGate
from tests.helpers import LIMITS, T0, risk_ctx


def order(**overrides) -> Order:
    base = dict(id="gambler-1-ETH-USD:1", sym="ETH-USD", side="buy", qty=0.2, type="market", price=None, reduce_only=False, decision_id="gambler-1-ETH-USD")
    base.update(overrides)
    return Order(**base)


def test_clean_order_is_approved():
    verdict = RiskGate(LIMITS).check(order(), risk_ctx())
    assert verdict.approved and verdict.vetoes == () and verdict.approval.order_id == order().id


@pytest.mark.parametrize(
    "check,ctx_overrides,order_overrides",
    [
        ("max_position", {}, {"qty": 1.5}),
        ("max_position", {"mid": 60_000.0, "reference_mid": 60_000.0}, {"qty": 0.5}),
        ("daily_loss", {"day_pnl_usd": -150.0}, {}),
        ("leverage", {"equity_usd": 100.0}, {}),
        ("range_guard", {}, {"type": "limit", "price": 2600.0}),
        ("range_guard", {"reference_mid": 2000.0}, {}),
        ("fees_plus_gas", {"expected_edge_bps": 5.0}, {}),
        ("model_version", {"model_version": "jev-latest"}, {}),
        ("model_version", {"model_version": None}, {}),
        ("stale_data", {"now_ms": T0 + 100_000}, {}),
    ],
)
def test_each_veto_fires(check, ctx_overrides, order_overrides):
    verdict = RiskGate(LIMITS).check(order(**order_overrides), risk_ctx(**ctx_overrides))
    assert not verdict.approved and verdict.approval is None
    assert check in {v.check for v in verdict.vetoes}


def test_every_firing_veto_is_reported_not_just_the_first():
    verdict = RiskGate(LIMITS).check(order(), risk_ctx(day_pnl_usd=-500.0, model_version="jev-latest", expected_edge_bps=0.0))
    assert {v.check for v in verdict.vetoes} == {"daily_loss", "fees_plus_gas", "model_version"}


def test_reduce_only_exits_pass_daily_loss_and_fees_but_nothing_else():
    exit_order = order(side="sell", reduce_only=True)
    ok = RiskGate(LIMITS).check(exit_order, risk_ctx(position_units=0.2, day_pnl_usd=-500.0, expected_edge_bps=0.0))
    assert ok.approved
    bad_model = RiskGate(LIMITS).check(exit_order, risk_ctx(position_units=0.2, model_version="jev-9.9.9"))
    assert [v.check for v in bad_model.vetoes] == ["model_version"]


def test_broker_rejects_forged_reused_or_misbound_approvals():
    gate = RiskGate(LIMITS)
    broker = PaperBroker(gate, cash_usd=10_000, fee_bps=10, gas_usd=0.5)
    broker.on_tick("ETH-USD", Tick(T0, 2499.0, 2501.0, 5, 5))
    first = order()
    with pytest.raises(RiskBypassError):
        broker.place_order(first, RiskApproval(first.id, "deadbeef", T0))
    with pytest.raises(RiskBypassError):
        broker.place_order(first, None)
    approval = gate.check(first, risk_ctx()).approval
    assert broker.place_order(first, approval).status == "filled"
    with pytest.raises(RiskBypassError):
        broker.place_order(first, approval)
    second = order(id="gambler-2-ETH-USD:2")
    other = gate.check(second, risk_ctx(position_units=0.2)).approval
    with pytest.raises(RiskBypassError):
        broker.place_order(order(id="gambler-3-ETH-USD:3"), other)
