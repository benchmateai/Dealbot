"""Paper broker: simulated fills with fees, gas and slippage. Same interface a live broker would use.
Resting limit orders pay the maker fee when a tick crosses them; market and marketable orders pay the taker fee.

Every `place_order` first hands the approval back to the risk gate; without a valid, unused approval
for that exact order the call raises and nothing changes.
"""

from __future__ import annotations

from collections.abc import Mapping

from broker.base import BrokerError, Fill, Order, OrderAck, Position
from feed.base import Tick


class PaperBroker:
    kind = "paper"

    def __init__(self, gate, *, cash_usd: float, fee_bps: float, gas_usd: float, slippage_bps: float = 1.0, maker_fee_bps: float | None = None) -> None:
        if cash_usd <= 0:
            raise BrokerError("paper broker needs positive starting cash")
        self._gate = gate
        self.cash = float(cash_usd)
        self.starting_cash = float(cash_usd)
        self._fee_bps = fee_bps
        self._maker_fee_bps = fee_bps if maker_fee_bps is None else maker_fee_bps
        self._gas_usd = gas_usd
        self._slip = slippage_bps / 1e4
        self._positions: dict[str, Position] = {}
        self._resting: dict[str, Order] = {}
        self._last: dict[str, Tick] = {}
        self.fills: list[Fill] = []

    def on_tick(self, sym: str, tick: Tick) -> list[Fill]:
        self._last[sym] = tick
        fills = []
        for order in [o for o in self._resting.values() if o.sym == sym]:
            if order.side == "buy" and tick.ask <= order.price:
                fills.append(self._apply_fill(order, order.price, tick.ts, maker=True))
            elif order.side == "sell" and tick.bid >= order.price:
                fills.append(self._apply_fill(order, order.price, tick.ts, maker=True))
        return fills

    def place_order(self, order: Order, approval: object) -> OrderAck:
        self._gate.consume(approval, order)
        last = self._last.get(order.sym)
        if last is None:
            return OrderAck(order.id, "rejected", reason="no_market_data")
        pos = self.position(order.sym)
        if order.reduce_only and abs(pos.qty + order.signed_qty) > abs(pos.qty) + 1e-12:
            return OrderAck(order.id, "rejected", reason="reduce_only_violation")
        if order.type == "market":
            px = last.ask * (1 + self._slip) if order.side == "buy" else last.bid * (1 - self._slip)
            return OrderAck(order.id, "filled", self._apply_fill(order, px, last.ts))
        if order.side == "buy" and last.ask <= order.price:
            return OrderAck(order.id, "filled", self._apply_fill(order, last.ask, last.ts))
        if order.side == "sell" and last.bid >= order.price:
            return OrderAck(order.id, "filled", self._apply_fill(order, last.bid, last.ts))
        self._resting[order.id] = order
        return OrderAck(order.id, "resting")

    def cancel(self, order_id: str) -> bool:
        return self._resting.pop(order_id, None) is not None

    def open_orders(self, sym: str | None = None) -> list[Order]:
        return [o for o in self._resting.values() if sym is None or o.sym == sym]

    def position(self, sym: str) -> Position:
        return self._positions.get(sym) or Position(sym)

    def positions(self) -> dict[str, Position]:
        return {s: p for s, p in self._positions.items() if p.qty != 0}

    def equity(self, marks: Mapping[str, float]) -> float:
        value = self.cash
        for sym, pos in self._positions.items():
            if pos.qty != 0:
                value += pos.qty * marks.get(sym, pos.avg_price)
        return value

    def _apply_fill(self, order: Order, px: float, ts: int, *, maker: bool = False) -> Fill:
        qty, signed = order.qty, order.signed_qty
        notional = qty * px
        fee = notional * (self._maker_fee_bps if maker else self._fee_bps) / 1e4
        gas = self._gas_usd
        pos = self._positions.setdefault(order.sym, Position(order.sym))
        realized = 0.0
        if pos.qty == 0 or (pos.qty > 0) == (signed > 0):
            total = abs(pos.qty) + qty
            pos.avg_price = (abs(pos.qty) * pos.avg_price + qty * px) / total
            pos.qty += signed
        else:
            closed = min(qty, abs(pos.qty))
            realized = closed * (px - pos.avg_price) * (1 if pos.qty > 0 else -1)
            remaining = pos.qty + signed
            if abs(remaining) < 1e-12:
                remaining, pos.avg_price = 0.0, 0.0
            elif (remaining > 0) != (pos.qty > 0):
                pos.avg_price = px
            pos.qty = remaining
        pos.realized_pnl_usd += realized
        pos.fees_usd += fee + gas
        self.cash += (-notional if signed > 0 else notional) - fee - gas
        fill = Fill(order.id, order.sym, order.side, qty, px, fee, gas, realized, ts)
        self.fills.append(fill)
        self._resting.pop(order.id, None)
        return fill
