"""Paper broker for binaries: Kalshi's fee formula instead of basis points, and settlement at expiry
to $1 or $0 per contract. Positions are signed: long is YES bought, short is YES sold (NO bought)."""

from __future__ import annotations

from broker.base import Fill
from broker.paper import PaperBroker
from kalshi.api import TAKER_RATE, maker_fee_usd, taker_fee_usd


class BinaryPaperBroker(PaperBroker):
    kind = "paper"

    def __init__(self, gate, *, cash_usd: float, taker_rate: float = TAKER_RATE, maker_rate: float = 0.0, slippage_bps: float = 0.0) -> None:
        super().__init__(gate, cash_usd=cash_usd, fee_bps=0.0, gas_usd=0.0, slippage_bps=slippage_bps, maker_fee_bps=0.0)
        self._taker_rate = taker_rate
        self._maker_rate = maker_rate

    def _fee_usd(self, qty: float, px: float, maker: bool) -> float:
        return maker_fee_usd(qty, px, self._maker_rate) if maker else taker_fee_usd(qty, px, self._taker_rate)

    def settle(self, sym: str, payout: float, ts: int) -> Fill | None:
        """Settle the open position in `sym` at `payout` per contract (1.0 or 0.0). No fee."""
        pos = self._positions.get(sym)
        if pos is None or pos.qty == 0:
            return None
        qty = pos.qty
        realized = qty * (payout - pos.avg_price)
        self.cash += qty * payout
        pos.realized_pnl_usd += realized
        pos.qty, pos.avg_price = 0.0, 0.0
        for order_id in [o.id for o in self._resting.values() if o.sym == sym]:
            self._resting.pop(order_id, None)
        fill = Fill(f"settle:{sym}:{ts}", sym, "settle", abs(qty), payout, 0.0, 0.0, realized, ts)
        self.fills.append(fill)
        return fill
