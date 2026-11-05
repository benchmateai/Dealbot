"""Risk limits. Values come from the environment (see desk/config.py); nothing here is tunable by a model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    max_position_units: float
    max_notional_usd: float
    daily_loss_limit_usd: float
    max_leverage: float
    range_guard_bps: float
    range_guard_ref_bps: float
    fee_bps: float
    maker_fee_bps: float
    gas_usd: float
    min_edge_margin: float
    pinned_model: str
    max_stale_ms: int
    fee_model: str = "bps"
    kalshi_taker_rate: float = 0.07
    kalshi_maker_rate: float = 0.0

    def validate(self) -> RiskLimits:
        positive = {
            "max_position_units": self.max_position_units,
            "max_notional_usd": self.max_notional_usd,
            "daily_loss_limit_usd": self.daily_loss_limit_usd,
            "max_leverage": self.max_leverage,
            "range_guard_bps": self.range_guard_bps,
            "range_guard_ref_bps": self.range_guard_ref_bps,
            "max_stale_ms": self.max_stale_ms,
        }
        for name, value in positive.items():
            if not value > 0:
                raise ValueError(f"risk limit {name} must be positive, got {value}")
        for name, value in {"fee_bps": self.fee_bps, "maker_fee_bps": self.maker_fee_bps, "gas_usd": self.gas_usd, "min_edge_margin": self.min_edge_margin}.items():
            if value < 0:
                raise ValueError(f"risk limit {name} must not be negative, got {value}")
        if not self.pinned_model:
            raise ValueError("risk limits need the pinned model version")
        if self.fee_model not in ("bps", "kalshi"):
            raise ValueError("fee_model must be bps or kalshi")
        return self

    def round_trip_cost_usd(self, qty: float, price: float, order_type: str) -> float:
        """Entry plus exit cost in dollars. bps: fees on notional plus gas each way. kalshi: the exchange's
        per-contract formula each way (settlement itself is free, so this is the conservative case)."""
        if self.fee_model == "kalshi":
            from kalshi.api import maker_fee_usd, taker_fee_usd

            one_way = maker_fee_usd(qty, price, self.kalshi_maker_rate) if order_type == "limit" else taker_fee_usd(qty, price, self.kalshi_taker_rate)
            return 2.0 * one_way
        return 2.0 * self.fee_bps_for(order_type) / 1e4 * qty * price + 2.0 * self.gas_usd

    def fee_bps_for(self, order_type: str) -> float:
        """Maker fee for orders that rest (limit), taker fee for everything else."""
        return self.maker_fee_bps if order_type == "limit" else self.fee_bps

    def to_dict(self) -> dict:
        return dict(self.__dict__)
