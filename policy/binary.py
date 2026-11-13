"""Decision rule for binary contracts: the threshold is the market's own price plus a cost-derived
minimum edge, not a fixed probability.

    p_yes   = model_weight * P_formula(above strike) + (1 - model_weight) * P_jev(settles_yes)
    buy YES when p_yes >= yes_ask + min_edge(yes_ask),  buy NO when (1 - p_yes) >= (1 - yes_bid) + min_edge(1 - yes_bid)
    min_edge(price) = (1 + margin) * (taker fee per contract at that price + half the spread)

The expected edge is reported in bps of notional so the risk gate's fees check compares the same
dollars: edge_bps / 1e4 * qty * price = qty * (p - price).

Exits use the same price-derived rule from the other side. Holding a long YES to settlement is worth
p_yes per contract; selling now is worth the YES bid less its fee. So the threshold on P(the position
loses) is 1 - (bid - min_edge(bid)), the cost of being wrong in each direction weighed at the market's
price, and the desk sells early only when that probability clears it. A fixed threshold on P(loss)
would sell nearly every position right after buying it: one entered at p_yes 0.70 already carries a
0.30 chance of losing. The exit_now and pickoff answers are still asked, logged and scored for
calibration; they are reported beside the decision but do not move it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from kalshi.api import TAKER_RATE, taker_fee_usd
from policy.decide import HOLD, ActionScore, Pick, score_actions
from policy.thresholds import THRESHOLDS


@dataclass(frozen=True)
class BinaryCosts:
    taker_rate: float = TAKER_RATE
    maker_rate: float = 0.0
    margin: float = 0.5
    model_weight: float = 0.5
    max_pickoff: float = 0.5


def min_edge(price: float, spread: float, costs: BinaryCosts) -> float:
    """Minimum (probability - price) per contract that pays for the taker fee and half the spread, with margin."""
    return (1.0 + costs.margin) * (taker_fee_usd(1, price, costs.taker_rate) + 0.5 * max(spread, 0.0))


def edge_bps(p: float, price: float) -> float:
    return 0.0 if price <= 0 else (p - price) / price * 1e4


def _clamp(p: float) -> float:
    return min(1.0, max(0.0, float(p)))


def combined_p_yes(answers: Mapping[str, Mapping], contract: Mapping, costs: BinaryCosts) -> float | None:
    answer = answers.get("settles_yes")
    p_jev = None if answer is None or answer.get("type") != "noul" else _clamp(answer["noul"])
    model_p = contract.get("model_p_yes")
    if p_jev is None and model_p is None:
        return None
    if model_p is None:
        return p_jev
    if p_jev is None:
        return _clamp(model_p)
    return _clamp(costs.model_weight * float(model_p) + (1.0 - costs.model_weight) * p_jev)


def final_pick_binary(bot: str, phase: str, answers: Mapping[str, Mapping], snapshot: Mapping, contract: Mapping, costs: BinaryCosts, *, position_sign: int = 0) -> Pick:
    yes_bid, yes_ask = contract.get("yes_bid"), contract.get("yes_ask")
    p_yes = combined_p_yes(answers, contract, costs)
    if yes_bid is None or yes_ask is None or p_yes is None:
        return Pick(HOLD, 0.0, 1.0, 0.0, ())
    spread = max(0.0, float(yes_ask) - float(yes_bid))
    pickoff_answer = answers.get("pickoff") or {}
    pickoff = _clamp(pickoff_answer.get("noul", 0.0)) if pickoff_answer.get("type") == "noul" else 0.0
    if phase == "entry":
        no_price = 1.0 - float(yes_bid)
        candidates = (
            ActionScore("enter_long", p_yes, min(0.999, float(yes_ask) + min_edge(float(yes_ask), spread, costs)), edge_bps(p_yes, float(yes_ask))),
            ActionScore("enter_short", 1.0 - p_yes, min(0.999, no_price + min_edge(no_price, spread, costs)), edge_bps(1.0 - p_yes, no_price)),
        )
        best = max(candidates, key=lambda s: (s.prob - s.threshold, s.prob))
        blocked = not contract.get("tradable", True) or pickoff > costs.max_pickoff
        if not blocked and best.prob >= best.threshold:
            return Pick(best.action, best.prob, best.threshold, best.expected_edge_bps, candidates)
        return Pick(HOLD, best.prob, best.threshold, best.expected_edge_bps, candidates)
    judged = score_actions(bot, "manage", answers, snapshot)[0]  # Jev's exit_now/pickoff blend: logged, not deciding
    if position_sign == 0:
        return Pick(HOLD, 0.0, 1.0, 0.0, (judged,))
    if position_sign > 0:
        p_lose, sell_price = 1.0 - p_yes, float(yes_bid)
    else:
        p_lose, sell_price = p_yes, 1.0 - float(yes_ask)
    threshold = min(1.0, max(0.0, 1.0 - (sell_price - min_edge(sell_price, spread, costs))))
    scores = (ActionScore("exit", p_lose, threshold, 0.0), judged)
    if p_lose > threshold:
        return Pick("exit", p_lose, threshold, 0.0, scores)
    return Pick(HOLD, p_lose, threshold, 0.0, scores)
