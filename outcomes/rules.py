"""Outcome rules: how a logged judgment is graded later from the realized price path.

Rules are declarative. A question names a rule and a threshold parameter ("cost", "2cost", "rv",
or a number in bps). After the horizon passes, the resolver builds `PathStats` from the ticks that
followed the decision and calls the rule. Rules never see the model's answer, so grading cannot
leak the forecast into the outcome. A rule returns None when the outcome cannot be determined
(for example a position question asked while flat).
"""

from __future__ import annotations

import math
import re
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from feed.base import Tick


@dataclass(frozen=True)
class PathStats:
    mid0: float
    mids: tuple[float, ...]
    block_mids: tuple[float, ...]

    @classmethod
    def from_ticks(cls, mid0: float, ticks: Sequence[Tick], as_of_ms: int, block_ms: int, horizon_blocks: int) -> PathStats:
        mids = tuple(t.mid for t in ticks)
        samples = [mid0]
        for k in range(1, horizon_blocks + 1):
            edge = as_of_ms + k * block_ms
            last = None
            for t in ticks:
                if t.ts < edge:
                    last = t.mid
                else:
                    break
            if last is not None:
                samples.append(last)
        return cls(mid0, mids, tuple(samples))

    def _bps(self, mid: float) -> float:
        return 1e4 * math.log(mid / self.mid0)

    @property
    def end_ret_bps(self) -> float:
        return self._bps(self.mids[-1]) if self.mids else 0.0

    @property
    def max_up_bps(self) -> float:
        return max(0.0, max((self._bps(m) for m in self.mids), default=0.0))

    @property
    def max_down_bps(self) -> float:
        return max(0.0, -min((self._bps(m) for m in self.mids), default=0.0))

    def first_touch(self, thr_bps: float) -> int:
        """+1 if the path rises by thr first, -1 if it falls by thr first, 0 if neither within the horizon."""
        for m in self.mids:
            r = self._bps(m)
            if r >= thr_bps:
                return 1
            if r <= -thr_bps:
                return -1
        return 0

    def touches_both(self, thr_bps: float) -> bool:
        return self.max_up_bps >= thr_bps and self.max_down_bps >= thr_bps

    @property
    def rv_after_bps(self) -> float | None:
        log_returns = [math.log(b / a) for a, b in zip(self.block_mids, self.block_mids[1:])]
        return 1e4 * statistics.pstdev(log_returns) if len(log_returns) >= 2 else None


@dataclass(frozen=True)
class RuleContext:
    snapshot: Mapping
    pos_sign: int
    rv_bps: float | None
    cost_bps: float


RuleFn = Callable[[PathStats, float, RuleContext], bool | str | int | None]


@dataclass(frozen=True)
class RuleSpec:
    kind: str
    fn: RuleFn
    doc: str


def _sign(x: float) -> int:
    return 1 if x > 0 else -1 if x < 0 else 0


def _w(ctx: RuleContext, key: str) -> float | None:
    rets = ctx.snapshot.get("ret_bps") or {}
    return rets.get(key)


# ---- noul rules -----------------------------------------------------------------------------

def end_above(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return s.end_ret_bps > thr


def end_below(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return s.end_ret_bps < -thr


def abs_end_above(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return abs(s.end_ret_bps) > thr


def abs_end_below(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return abs(s.end_ret_bps) <= thr


def first_touch_up(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return s.first_touch(thr) == 1


def first_touch_down(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return s.first_touch(thr) == -1


def touches_both(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return s.touches_both(thr)


def range_bound(s: PathStats, thr: float, ctx: RuleContext) -> bool:
    return s.max_up_bps < thr and s.max_down_bps < thr


def continues_w5(s: PathStats, thr: float, ctx: RuleContext) -> bool | None:
    w5 = _w(ctx, "w5")
    if not w5:
        return None
    return _sign(w5) * s.first_touch(thr) == 1


def against_w5_first(s: PathStats, thr: float, ctx: RuleContext) -> bool | None:
    w5 = _w(ctx, "w5")
    if not w5:
        return None
    return _sign(w5) * s.first_touch(thr) == -1


def with_imbalance_first(s: PathStats, thr: float, ctx: RuleContext) -> bool | None:
    imb = ctx.snapshot.get("imb")
    if not imb:
        return None
    return _sign(imb) * s.first_touch(thr) == 1


def pos_loses_more_than(s: PathStats, thr: float, ctx: RuleContext) -> bool | None:
    if ctx.pos_sign == 0:
        return None
    return ctx.pos_sign * s.end_ret_bps < -thr


def pos_gains(s: PathStats, thr: float, ctx: RuleContext) -> bool | None:
    if ctx.pos_sign == 0:
        return None
    return ctx.pos_sign * s.end_ret_bps > thr


def vol_regime_differs(s: PathStats, thr: float, ctx: RuleContext) -> bool | None:
    after = s.rv_after_bps
    if not ctx.rv_bps or after is None:
        return None
    return after > 1.5 * ctx.rv_bps or after < 0.5 * ctx.rv_bps


# ---- choice rules ---------------------------------------------------------------------------

def direction_first_touch(s: PathStats, thr: float, ctx: RuleContext) -> str:
    return {1: "up", -1: "down", 0: "flat"}[s.first_touch(thr)]


def revert_or_continue(s: PathStats, thr: float, ctx: RuleContext) -> str:
    end = s.end_ret_bps
    if abs(end) <= thr:
        return "stay"
    w20 = _w(ctx, "w20")
    if not w20:
        return "other"
    return "revert" if _sign(end) == -_sign(w20) else "continue"


def regime_realized(s: PathStats, thr: float, ctx: RuleContext) -> str:
    if s.touches_both(2 * thr):
        return "volatile_chop"
    if abs(s.end_ret_bps) > 2 * thr:
        return "trending"
    if s.max_up_bps < 2 * thr and s.max_down_bps < 2 * thr:
        return "ranging"
    return "other"


def lean_realized(s: PathStats, thr: float, ctx: RuleContext) -> str:
    if s.touches_both(thr):
        return "neither"
    return {1: "bid", -1: "ask", 0: "both"}[s.first_touch(thr)]


# ---- score rules ----------------------------------------------------------------------------

def danger_level(s: PathStats, thr: float, ctx: RuleContext) -> int:
    a = abs(s.end_ret_bps)
    return 0 if a < thr else 1 if a < 2 * thr else 2 if a < 4 * thr else 3


def vol_level(s: PathStats, thr: float, ctx: RuleContext) -> int | None:
    after = s.rv_after_bps
    if not ctx.rv_bps or after is None:
        return None
    ratio = after / ctx.rv_bps
    return 0 if ratio < 0.5 else 1 if ratio < 1.5 else 2 if ratio < 3 else 3


RULES: dict[str, RuleSpec] = {
    "end_above": RuleSpec("noul", end_above, "end return above +thr"),
    "end_below": RuleSpec("noul", end_below, "end return below -thr"),
    "abs_end_above": RuleSpec("noul", abs_end_above, "absolute end return above thr"),
    "abs_end_below": RuleSpec("noul", abs_end_below, "absolute end return at or below thr"),
    "first_touch_up": RuleSpec("noul", first_touch_up, "+thr is hit before -thr"),
    "first_touch_down": RuleSpec("noul", first_touch_down, "-thr is hit before +thr"),
    "touches_both": RuleSpec("noul", touches_both, "both +thr and -thr are hit within the horizon"),
    "range_bound": RuleSpec("noul", range_bound, "neither +thr nor -thr is hit"),
    "continues_w5": RuleSpec("noul", continues_w5, "first touch is in the direction of ret_bps.w5"),
    "against_w5_first": RuleSpec("noul", against_w5_first, "first touch is against ret_bps.w5"),
    "with_imbalance_first": RuleSpec("noul", with_imbalance_first, "first touch is in the direction of imb"),
    "pos_loses_more_than": RuleSpec("noul", pos_loses_more_than, "open position loses more than thr by the horizon"),
    "pos_gains": RuleSpec("noul", pos_gains, "open position gains more than thr by the horizon"),
    "vol_regime_differs": RuleSpec("noul", vol_regime_differs, "realized vol after is >1.5x or <0.5x rv_bps"),
    "direction_first_touch": RuleSpec("choice", direction_first_touch, "up / down / flat by first touch of thr"),
    "revert_or_continue": RuleSpec("choice", revert_or_continue, "revert / continue / stay relative to ret_bps.w20"),
    "regime_realized": RuleSpec("choice", regime_realized, "trending / ranging / volatile_chop / other"),
    "lean_realized": RuleSpec("choice", lean_realized, "bid / ask / both / neither"),
    "danger_level": RuleSpec("score", danger_level, "0..3 by absolute end return in multiples of thr"),
    "vol_level": RuleSpec("score", vol_level, "0..3 by realized vol after relative to rv_bps"),
}

_PARAM = re.compile(r"^(?P<k>\d+(?:\.\d+)?)?(?P<base>cost|rv)$")


def parse_param(param: float | str, *, cost_bps: float, rv_bps: float | None) -> float | None:
    """Resolve a question's threshold parameter to bps at decision time. None when rv is unavailable."""
    if isinstance(param, (int, float)) and not isinstance(param, bool):
        return float(param)
    text = str(param).strip()
    try:
        return float(text)
    except ValueError:
        pass
    m = _PARAM.match(text)
    if not m:
        raise ValueError(f"bad threshold parameter {param!r}; use a number, 'cost', '2cost', 'rv' or '1.5rv'")
    k = float(m["k"]) if m["k"] else 1.0
    base = cost_bps if m["base"] == "cost" else rv_bps
    return None if base is None else k * base
