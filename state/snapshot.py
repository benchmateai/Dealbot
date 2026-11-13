"""Deterministic market snapshot.

`build_snapshot` is a pure function of (ticks, as_of, account facts, parameters). It uses only ticks
with `ts < as_of`, so every field is known strictly before the decision it feeds. The serialized form
is compact JSON that must stay under `TOKEN_BUDGET` estimated tokens (see `state.tokens`).

Fields: mid, spread, top-of-book imbalance, realized vol, returns over three windows, inventory,
drawdown. Block-relative windows are converted to milliseconds with `block_ms`.
"""

from __future__ import annotations

import json
import math
import statistics
from bisect import bisect_left
from collections.abc import Sequence
from dataclasses import dataclass

from feed.base import Tick
from state.tokens import estimate_tokens

TOKEN_BUDGET = 400
DEFAULT_RET_WINDOWS_BLOCKS = (1, 5, 20)
DEFAULT_RV_WINDOW_BLOCKS = 20


class InsufficientData(ValueError):
    """Not enough point-in-time data to build a snapshot."""


class TokenBudgetExceeded(ValueError):
    """The serialized snapshot would exceed TOKEN_BUDGET tokens."""


@dataclass(frozen=True)
class AccountState:
    """Account facts known before the decision. Supplied by the book and broker, never by a model."""

    inventory: float
    equity_usd: float
    peak_equity_usd: float
    day_peak_equity_usd: float


@dataclass(frozen=True)
class Snapshot:
    sym: str
    as_of: int
    blk: int
    mid: float
    spr_bps: float
    imb: float
    rv_bps: float | None
    ret_bps: dict[str, float | None]
    n: int
    inv: float
    inv_usd: float
    dd_bps: float
    dd_day_bps: float

    def to_dict(self) -> dict:
        return {
            "sym": self.sym,
            "as_of": self.as_of,
            "blk": self.blk,
            "mid": self.mid,
            "spr_bps": self.spr_bps,
            "imb": self.imb,
            "rv_bps": self.rv_bps,
            "ret_bps": dict(self.ret_bps),
            "n": self.n,
            "inv": self.inv,
            "inv_usd": self.inv_usd,
            "dd_bps": self.dd_bps,
            "dd_day_bps": self.dd_day_bps,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True, allow_nan=False)

    def tokens(self) -> int:
        return estimate_tokens(self.to_json())


def _r(value: float, digits: int) -> float:
    rounded = round(value, digits)
    return 0.0 if rounded == 0 else rounded


def _drawdown_bps(equity: float, peak: float) -> float:
    if peak <= 0:
        return 0.0
    return min(0.0, 1e4 * (equity - peak) / peak)


def build_snapshot(
    sym: str,
    ticks: Sequence[Tick],
    as_of_ms: int,
    block: int,
    account: AccountState,
    *,
    block_ms: int,
    ret_windows_blocks: Sequence[int] = DEFAULT_RET_WINDOWS_BLOCKS,
    rv_window_blocks: int = DEFAULT_RV_WINDOW_BLOCKS,
) -> Snapshot:
    """Build the snapshot for `sym` as of `as_of_ms` using only ticks strictly before it."""
    hist = sorted((t for t in ticks if t.ts < as_of_ms and t.is_sane()), key=lambda t: t.ts)
    if len(hist) < 2:
        raise InsufficientData(f"{sym}: {len(hist)} sane ticks before {as_of_ms}, need at least 2")
    ts_list = [t.ts for t in hist]
    last = hist[-1]
    mid = last.mid
    spr_bps = (last.ask - last.bid) / mid * 1e4
    depth = last.bid_qty + last.ask_qty
    imb = (last.bid_qty - last.ask_qty) / depth if depth > 0 else 0.0

    def mid_before(t_ms: int) -> float | None:
        i = bisect_left(ts_list, t_ms) - 1
        return hist[i].mid if i >= 0 else None

    rets: dict[str, float | None] = {}
    for w in ret_windows_blocks:
        ref = mid_before(as_of_ms - w * block_ms)
        rets[f"w{w}"] = _r(1e4 * math.log(mid / ref), 1) if ref else None

    samples = [mid_before(as_of_ms - k * block_ms) for k in range(rv_window_blocks, -1, -1)]
    log_returns = [math.log(b / a) for a, b in zip(samples, samples[1:]) if a and b]
    rv = _r(1e4 * statistics.pstdev(log_returns), 1) if len(log_returns) >= 2 else None

    snap = Snapshot(
        sym=sym,
        as_of=as_of_ms,
        blk=block,
        mid=_r(mid, 6),
        spr_bps=_r(spr_bps, 2),
        imb=_r(imb, 3),
        rv_bps=rv,
        ret_bps=rets,
        n=len(hist),
        inv=_r(account.inventory, 6),
        inv_usd=_r(account.inventory * mid, 2),
        dd_bps=_r(_drawdown_bps(account.equity_usd, account.peak_equity_usd), 1),
        dd_day_bps=_r(_drawdown_bps(account.equity_usd, account.day_peak_equity_usd), 1),
    )
    tokens = snap.tokens()
    if tokens > TOKEN_BUDGET:
        raise TokenBudgetExceeded(f"snapshot is {tokens} tokens, budget is {TOKEN_BUDGET}")
    return snap
