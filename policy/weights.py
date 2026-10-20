"""Combination weights: how a bot's raw judgments combine into one probability per action.

Each action is a weighted average of probabilities extracted from the battery's answers. Weights for
an action sum to 1. A term with a `when` condition that does not hold contributes 0 (not "skipped"),
which pulls the action's probability down: the conservative direction.

Extractors (answer shapes are the TypeSafe wire answers):
    noul            P(yes)                           not_noul          1 - P(yes)
    choice:<label>  P(label)                         not_choice:<label> 1 - P(label)
    score_norm      expected score / (levels - 1)    inv_score_norm    1 - score_norm
Conditions: "<field><op><number>" with field in w1, w5, w20 (returns), imb, inv, spr_bps, rv_bps.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


class PolicyError(ValueError):
    pass


@dataclass(frozen=True)
class Term:
    qid: str
    extract: str
    weight: float
    when: str | None = None


WEIGHTS: dict[str, dict[str, tuple[Term, ...]]] = {
    "gambler": {
        "enter_long": (
            Term("dir_20", "choice:up", 0.5),
            Term("late_entry", "not_noul", 0.2),
            Term("whipsaw", "not_noul", 0.2),
            Term("regime", "choice:trending", 0.1),
        ),
        "enter_short": (
            Term("dir_20", "choice:down", 0.5),
            Term("late_entry", "not_noul", 0.2),
            Term("whipsaw", "not_noul", 0.2),
            Term("regime", "choice:trending", 0.1),
        ),
        "exit": (
            Term("thesis_broken", "noul", 0.6),
            Term("keep_running", "not_noul", 0.4),
        ),
    },
    "house": {
        "enter_long": (
            Term("spread_edge", "noul", 0.35),
            Term("revert_10", "choice:revert", 0.25, when="w20<0"),
            Term("informed_flow", "not_noul", 0.2),
            Term("toxic_tape", "not_noul", 0.2),
        ),
        "enter_short": (
            Term("spread_edge", "noul", 0.35),
            Term("revert_10", "choice:revert", 0.25, when="w20>0"),
            Term("informed_flow", "not_noul", 0.2),
            Term("toxic_tape", "not_noul", 0.2),
        ),
        "exit": (
            Term("exit_now", "noul", 0.5),
            Term("toxic_tape", "noul", 0.3),
            Term("informed_flow", "noul", 0.2),
        ),
    },
    "spy": {
        "enter_long": (
            Term("dir_if_any", "choice:up", 0.5),
            Term("danger", "inv_score_norm", 0.3),
            Term("anomaly", "not_noul", 0.2),
        ),
        "enter_short": (
            Term("dir_if_any", "choice:down", 0.5),
            Term("danger", "inv_score_norm", 0.3),
            Term("anomaly", "not_noul", 0.2),
        ),
        "exit": (
            Term("exit_now", "noul", 0.6),
            Term("danger", "score_norm", 0.4),
        ),
    },
}

_COND = re.compile(r"^(?P<field>w1|w5|w20|imb|inv|spr_bps|rv_bps)(?P<op><|>)(?P<num>-?\d+(?:\.\d+)?)$")


def _clamp(p: float) -> float:
    return min(1.0, max(0.0, float(p)))


def extract_prob(answer: Mapping, extract: str) -> float:
    kind = answer.get("type")
    if extract in ("noul", "not_noul"):
        if kind != "noul":
            raise PolicyError(f"extractor {extract!r} needs a noul answer, got {kind!r}")
        p = _clamp(answer["noul"])
        return p if extract == "noul" else 1.0 - p
    if extract.startswith("choice:") or extract.startswith("not_choice:"):
        if kind != "choice":
            raise PolicyError(f"extractor {extract!r} needs a choice answer, got {kind!r}")
        label = extract.split(":", 1)[1]
        p = _clamp(answer.get("probabilities", {}).get(label, 0.0))
        return p if extract.startswith("choice:") else 1.0 - p
    if extract in ("score_norm", "inv_score_norm"):
        if kind != "score":
            raise PolicyError(f"extractor {extract!r} needs a score answer, got {kind!r}")
        levels = len(answer.get("probabilities", {}))
        if levels < 2:
            raise PolicyError("score answer has fewer than two levels")
        p = _clamp(float(answer["score"]) / (levels - 1))
        return p if extract == "score_norm" else 1.0 - p
    raise PolicyError(f"unknown extractor {extract!r}")


def condition_holds(when: str | None, snapshot: Mapping) -> bool:
    if when is None:
        return True
    m = _COND.match(when)
    if not m:
        raise PolicyError(f"bad condition {when!r}")
    field = m["field"]
    value = (snapshot.get("ret_bps") or {}).get(field) if field in ("w1", "w5", "w20") else snapshot.get(field)
    if value is None:
        return False
    num = float(m["num"])
    return value < num if m["op"] == "<" else value > num


def combine(terms: Sequence[Term], answers: Mapping[str, Mapping], snapshot: Mapping) -> float:
    total_weight = sum(t.weight for t in terms)
    if abs(total_weight - 1.0) > 1e-9:
        raise PolicyError(f"weights sum to {total_weight}, expected 1")
    acc = 0.0
    for term in terms:
        answer = answers.get(term.qid)
        if answer is None:
            raise PolicyError(f"missing answer for {term.qid!r}")
        if not condition_holds(term.when, snapshot):
            continue
        acc += term.weight * extract_prob(answer, term.extract)
    return _clamp(acc)
