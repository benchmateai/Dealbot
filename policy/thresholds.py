"""One threshold per action, derived from what being wrong costs.

Act when the expected cost of acting is below the expected cost of not acting:

    (1 - p) * wrong_bps  <  p * missed_bps      <=>      p  >  wrong_bps / (wrong_bps + missed_bps)

So each threshold is a pure function of two costs in basis points of notional:
- wrong_bps:  what it costs to take the action and be wrong (adverse move to the stop, plus round-trip
              fees and gas for entries; the profit given up for a premature exit);
- missed_bps: what it costs to skip the action when it was right (the move not captured for entries;
              the further loss suffered for a skipped exit).
Change a cost and the threshold follows. Nothing here reads a model answer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionCost:
    wrong_bps: float
    missed_bps: float

    def __post_init__(self) -> None:
        if self.wrong_bps <= 0 or self.missed_bps <= 0:
            raise ValueError("costs must be positive")

    @property
    def threshold(self) -> float:
        return self.wrong_bps / (self.wrong_bps + self.missed_bps)


THRESHOLDS: dict[str, dict[str, ActionCost]] = {
    # Gambler: wide stops, chases moves; wrong entries are expensive, missed ones merely annoying.
    "gambler": {
        "enter_long": ActionCost(wrong_bps=70, missed_bps=30),    # 0.70
        "enter_short": ActionCost(wrong_bps=70, missed_bps=30),   # 0.70
        "exit": ActionCost(wrong_bps=20, missed_bps=50),          # 0.29: exit on modest evidence
    },
    # House: thin edge per fill, so a wrong entry costs far more than a missed one.
    "house": {
        "enter_long": ActionCost(wrong_bps=35, missed_bps=8),     # 0.81
        "enter_short": ActionCost(wrong_bps=35, missed_bps=8),    # 0.81
        "exit": ActionCost(wrong_bps=10, missed_bps=30),          # 0.25
    },
    # Spy: trades rarely, only on a clear read.
    "spy": {
        "enter_long": ActionCost(wrong_bps=60, missed_bps=20),    # 0.75
        "enter_short": ActionCost(wrong_bps=60, missed_bps=20),   # 0.75
        "exit": ActionCost(wrong_bps=15, missed_bps=45),          # 0.25
    },
}


@dataclass(frozen=True)
class EdgeModel:
    """Expected move captured when right (target) and given up when wrong (stop), in bps of notional."""

    target_bps: float
    stop_bps: float

    def expected_edge_bps(self, p_right: float) -> float:
        return p_right * self.target_bps - (1.0 - p_right) * self.stop_bps


EDGE: dict[str, EdgeModel] = {
    "gambler": EdgeModel(target_bps=80, stop_bps=40),
    "house": EdgeModel(target_bps=15, stop_bps=25),
    "spy": EdgeModel(target_bps=50, stop_bps=30),
}


def threshold(bot: str, action: str) -> float:
    try:
        return THRESHOLDS[bot][action].threshold
    except KeyError as exc:
        raise KeyError(f"no threshold for bot={bot!r} action={action!r}") from exc
