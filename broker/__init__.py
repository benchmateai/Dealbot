"""Brokers. Only the paper broker exists here; the interface is what a live one would implement."""

from broker.base import Broker, BrokerError, Fill, Order, OrderAck, Position
from broker.paper import PaperBroker

__all__ = ["Broker", "BrokerError", "Fill", "Order", "OrderAck", "PaperBroker", "Position", "make_broker"]


def make_broker(kind: str, gate, **kwargs) -> Broker:
    if kind == "paper":
        return PaperBroker(gate, **kwargs)
    raise BrokerError(f"broker kind {kind!r} is not available: only the paper broker exists in this repository; live trading is disabled by design")
