"""Score every action for the phase, then make one final pick or hold. Deterministic and logged."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from policy.thresholds import EDGE, THRESHOLDS
from policy.weights import WEIGHTS, PolicyError, combine

ENTRY_ACTIONS = ("enter_long", "enter_short")
MANAGE_ACTIONS = ("exit",)
HOLD = "hold"


@dataclass(frozen=True)
class ActionScore:
    action: str
    prob: float
    threshold: float
    expected_edge_bps: float

    def to_dict(self) -> dict:
        return {"action": self.action, "prob": round(self.prob, 4), "threshold": round(self.threshold, 4), "expected_edge_bps": round(self.expected_edge_bps, 2)}


@dataclass(frozen=True)
class Pick:
    action: str
    prob: float
    threshold: float
    expected_edge_bps: float
    scores: tuple[ActionScore, ...]

    @property
    def is_hold(self) -> bool:
        return self.action == HOLD

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "prob": round(self.prob, 4),
            "threshold": round(self.threshold, 4),
            "expected_edge_bps": round(self.expected_edge_bps, 2),
            "scores": [s.to_dict() for s in self.scores],
        }


def _actions_for(phase: str) -> tuple[str, ...]:
    if phase == "entry":
        return ENTRY_ACTIONS
    if phase == "manage":
        return MANAGE_ACTIONS
    raise PolicyError(f"unknown phase {phase!r}")


def score_actions(bot: str, phase: str, answers: Mapping[str, Mapping], snapshot: Mapping) -> tuple[ActionScore, ...]:
    if bot not in WEIGHTS:
        raise PolicyError(f"no weights for bot {bot!r}")
    out = []
    for action in _actions_for(phase):
        prob = combine(WEIGHTS[bot][action], answers, snapshot)
        out.append(ActionScore(action, prob, THRESHOLDS[bot][action].threshold, EDGE[bot].expected_edge_bps(prob)))
    return tuple(out)


def final_pick(bot: str, phase: str, answers: Mapping[str, Mapping], snapshot: Mapping) -> Pick:
    """The single best action whose probability clears its threshold; otherwise hold."""
    scores = score_actions(bot, phase, answers, snapshot)
    best = max(scores, key=lambda s: (s.prob - s.threshold, s.prob))
    if best.prob >= best.threshold:
        return Pick(best.action, best.prob, best.threshold, best.expected_edge_bps, scores)
    return Pick(HOLD, best.prob, best.threshold, best.expected_edge_bps, scores)
