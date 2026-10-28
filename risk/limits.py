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
        return self

    def fee_bps_for(self, order_type: str) -> float:
        """Maker fee for orders that rest (limit), taker fee for everything else."""
        return self.maker_fee_bps if order_type == "limit" else self.fee_bps

    def to_dict(self) -> dict:
        return dict(self.__dict__)
