"""Hard vetoes, checked before every order. No model output can override them.

Each check is a pure function of the order, hard facts (`RiskContext`) and the limits. The gate runs
every check so the log shows every veto that fired, not only the first. An order can only reach the
broker with a `RiskApproval` the gate issued for that exact order; approvals are single use and the
broker hands them back to the gate to be consumed. Nothing in policy/, questions/ or judge/ can
construct an approval that the gate recognizes.

Checks: max_position (units and notional), daily_loss, leverage, range_guard (order price vs mid and
mid vs slow reference), fees_plus_gas (expected edge must beat round-trip cost by a margin; maker fee for limit orders),
model_version (the decision came from the pinned Jev version), stale_data (snapshot age).
Exposure-reducing orders are exempt from daily_loss and fees_plus_gas, so a losing position can
always be closed. They are not exempt from anything else.
"""

from __future__ import annotations

import math
import secrets
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

from broker.base import Order
from risk.limits import RiskLimits

_EPS = 1e-12


@dataclass(frozen=True)
class Veto:
    check: str
    detail: str
    value: float | str | None = None
    limit: float | str | None = None

    def to_dict(self) -> dict:
        return {"check": self.check, "detail": self.detail, "value": self.value, "limit": self.limit}


@dataclass(frozen=True)
class RiskContext:
    """Hard facts as of before the order. Every number comes from the feed, book or broker; the only
    model-derived inputs are the expected edge (a policy number) and the model version string."""

    now_ms: int
    snapshot_as_of_ms: int
    mid: float
    reference_mid: float | None
    position_units: float
    equity_usd: float
    day_pnl_usd: float
    expected_edge_bps: float
    model_version: str | None


def _increases_exposure(order: Order, position_units: float) -> bool:
    return abs(position_units + order.signed_qty) > abs(position_units) + _EPS


def check_max_position(order: Order, ctx: RiskContext, lim: RiskLimits) -> Veto | None:
    after = ctx.position_units + order.signed_qty
    if abs(after) > lim.max_position_units + _EPS:
        return Veto("max_position", f"position after fill {after:.6f} units exceeds {lim.max_position_units}", abs(after), lim.max_position_units)
    notional = abs(after) * ctx.mid
    if notional > lim.max_notional_usd + 1e-9:
        return Veto("max_position", f"notional after fill {notional:.2f} USD exceeds {lim.max_notional_usd}", round(notional, 2), lim.max_notional_usd)
    return None


def check_daily_loss(order: Order, ctx: RiskContext, lim: RiskLimits) -> Veto | None:
    if ctx.day_pnl_usd <= -lim.daily_loss_limit_usd and _increases_exposure(order, ctx.position_units):
        return Veto(
            "daily_loss",
            f"day PnL {ctx.day_pnl_usd:.2f} USD is at or below -{lim.daily_loss_limit_usd}; only exposure-reducing orders are allowed",
            round(ctx.day_pnl_usd, 2),
            -lim.daily_loss_limit_usd,
        )
    return None


def check_leverage(order: Order, ctx: RiskContext, lim: RiskLimits) -> Veto | None:
    if not ctx.equity_usd > 0:
        return Veto("leverage", f"equity {ctx.equity_usd} USD is not positive", ctx.equity_usd, 0)
    lev = abs(ctx.position_units + order.signed_qty) * ctx.mid / ctx.equity_usd
    if lev > lim.max_leverage + 1e-9:
        return Veto("leverage", f"leverage after fill {lev:.3f}x exceeds {lim.max_leverage}x", round(lev, 3), lim.max_leverage)
    return None


def check_range_guard(order: Order, ctx: RiskContext, lim: RiskLimits) -> Veto | None:
    if not (math.isfinite(ctx.mid) and ctx.mid > 0):
        return Veto("range_guard", f"mid {ctx.mid!r} is not a positive finite number", str(ctx.mid), None)
    price = ctx.mid if order.price is None else order.price
    dev = abs(price - ctx.mid) / ctx.mid * 1e4
    if dev > lim.range_guard_bps:
        return Veto("range_guard", f"order price {price} is {dev:.1f} bps from mid {ctx.mid}; limit {lim.range_guard_bps}", round(dev, 1), lim.range_guard_bps)
    if ctx.reference_mid is not None and ctx.reference_mid > 0:
        ref_dev = abs(ctx.mid - ctx.reference_mid) / ctx.reference_mid * 1e4
        if ref_dev > lim.range_guard_ref_bps:
            return Veto(
                "range_guard",
                f"mid {ctx.mid} is {ref_dev:.1f} bps from reference mid {ctx.reference_mid}; suspect data; limit {lim.range_guard_ref_bps}",
                round(ref_dev, 1),
                lim.range_guard_ref_bps,
            )
    return None


def check_fees_plus_gas(order: Order, ctx: RiskContext, lim: RiskLimits) -> Veto | None:
    if order.reduce_only and not _increases_exposure(order, ctx.position_units):
        return None
    price = ctx.mid if order.price is None else order.price
    notional = order.qty * price
    cost = 2.0 * lim.fee_bps_for(order.type) / 1e4 * notional + 2.0 * lim.gas_usd
    required = cost * (1.0 + lim.min_edge_margin)
    edge = ctx.expected_edge_bps / 1e4 * notional
    if edge < required:
        return Veto(
            "fees_plus_gas",
            f"expected edge {edge:.4f} USD is below {required:.4f} USD (round-trip fees+gas {cost:.4f} USD x {1 + lim.min_edge_margin:.2f})",
            round(edge, 4),
            round(required, 4),
        )
    return None


def check_model_version(order: Order, ctx: RiskContext, lim: RiskLimits) -> Veto | None:
    if not ctx.model_version:
        return Veto("model_version", "decision carries no model version", None, lim.pinned_model)
    if ctx.model_version != lim.pinned_model:
        return Veto("model_version", f"decision was made by {ctx.model_version!r}; pinned version is {lim.pinned_model!r}", ctx.model_version, lim.pinned_model)
    return None


def check_stale_data(order: Order, ctx: RiskContext, lim: RiskLimits) -> Veto | None:
    age = ctx.now_ms - ctx.snapshot_as_of_ms
    if age < 0 or age > lim.max_stale_ms:
        return Veto("stale_data", f"snapshot age {age} ms is outside [0, {lim.max_stale_ms}]", age, lim.max_stale_ms)
    return None


CHECKS: tuple[tuple[str, Callable[[Order, RiskContext, RiskLimits], Veto | None]], ...] = (
    ("max_position", check_max_position),
    ("daily_loss", check_daily_loss),
    ("leverage", check_leverage),
    ("range_guard", check_range_guard),
    ("fees_plus_gas", check_fees_plus_gas),
    ("model_version", check_model_version),
    ("stale_data", check_stale_data),
)


@dataclass(frozen=True)
class RiskApproval:
    """Issued only by RiskGate.check. Single use, bound to one order id."""

    order_id: str
    nonce: str
    issued_ms: int


@dataclass(frozen=True)
class RiskVerdict:
    approved: bool
    vetoes: tuple[Veto, ...]
    approval: RiskApproval | None

    def to_dict(self) -> dict:
        return {"approved": self.approved, "vetoes": [v.to_dict() for v in self.vetoes]}


class RiskBypassError(RuntimeError):
    """An order reached the broker without a valid, unused approval from the gate."""


class RiskGate:
    def __init__(self, limits: RiskLimits, *, max_outstanding: int = 10_000) -> None:
        self._limits = limits.validate()
        self._issued: OrderedDict[str, str] = OrderedDict()
        self._max_outstanding = max_outstanding

    @property
    def limits(self) -> RiskLimits:
        return self._limits

    def evaluate(self, order: Order, ctx: RiskContext, *, skip: frozenset[str] = frozenset()) -> tuple[Veto, ...]:
        """Run every check (except `skip`, used by the funnel's pre-check) and return all vetoes that fired."""
        vetoes = []
        for name, check in CHECKS:
            if name in skip:
                continue
            veto = check(order, ctx, self._limits)
            if veto is not None:
                vetoes.append(veto)
        return tuple(vetoes)

    def check(self, order: Order, ctx: RiskContext) -> RiskVerdict:
        vetoes = self.evaluate(order, ctx)
        if vetoes:
            return RiskVerdict(False, vetoes, None)
        nonce = secrets.token_hex(16)
        self._issued[nonce] = order.id
        while len(self._issued) > self._max_outstanding:
            self._issued.popitem(last=False)
        return RiskVerdict(True, (), RiskApproval(order.id, nonce, ctx.now_ms))

    def consume(self, approval: object, order: Order) -> None:
        """Called by the broker. Raises unless `approval` was issued by this gate for `order` and is unused."""
        if not isinstance(approval, RiskApproval) or approval.order_id != order.id:
            raise RiskBypassError(f"order {order.id} has no approval issued for it")
        if self._issued.pop(approval.nonce, None) != order.id:
            raise RiskBypassError(f"approval for order {order.id} is unknown or already used")
