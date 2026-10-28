"""Order, fill and position types, and the broker interface a live broker would also implement."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from feed.base import Tick

SIDES = ("buy", "sell")
ORDER_TYPES = ("market", "limit")


class BrokerError(RuntimeError):
    pass


@dataclass(frozen=True)
class Order:
    id: str
    sym: str
    side: str
    qty: float
    type: str = "market"
    price: float | None = None
    reduce_only: bool = False
    decision_id: str = ""

    def __post_init__(self) -> None:
        if self.side not in SIDES:
            raise ValueError(f"side must be one of {SIDES}")
        if self.type not in ORDER_TYPES:
            raise ValueError(f"type must be one of {ORDER_TYPES}")
        if not self.qty > 0:
            raise ValueError("qty must be positive")
        if self.type == "limit" and not (self.price is not None and self.price > 0):
            raise ValueError("limit orders need a positive price")

    @property
    def signed_qty(self) -> float:
        return self.qty if self.side == "buy" else -self.qty

    def to_dict(self) -> dict:
        return {"id": self.id, "sym": self.sym, "side": self.side, "qty": self.qty, "type": self.type, "price": self.price, "reduce_only": self.reduce_only, "decision_id": self.decision_id}


@dataclass(frozen=True)
class Fill:
    order_id: str
    sym: str
    side: str
    qty: float
    price: float
    fee_usd: float
    gas_usd: float
    realized_pnl_usd: float
    ts: int

    def to_dict(self) -> dict:
        data = dict(self.__dict__)
        data["fill_ts"] = data.pop("ts")  # "ts" is the log writer's record timestamp
        return data


@dataclass
class Position:
    sym: str
    qty: float = 0.0
    avg_price: float = 0.0
    realized_pnl_usd: float = 0.0
    fees_usd: float = 0.0

    def to_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass(frozen=True)
class OrderAck:
    order_id: str
    status: str
    fill: Fill | None = None
    reason: str | None = None


class Broker(Protocol):
    """What the desk needs from any broker. A live implementation would wrap a venue's API behind the
    same calls; `on_tick` would become a no-op or a poll for fills."""

    kind: str

    def place_order(self, order: Order, approval: object) -> OrderAck: ...
    def cancel(self, order_id: str) -> bool: ...
    def open_orders(self, sym: str | None = None) -> list[Order]: ...
    def position(self, sym: str) -> Position: ...
    def positions(self) -> dict[str, Position]: ...
    def equity(self, marks: Mapping[str, float]) -> float: ...
    def on_tick(self, sym: str, tick: Tick) -> list[Fill]: ...
