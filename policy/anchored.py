"""Desk v2's forecast: the market's own price, moved toward a model of Kalshi's actual settlement rule only
as far as that model has earned on contracts that already settled. The shadow lab's strategy A replays
exactly this class on the desk's tape; the paper desk trades it from 2026-11-05 (KALSHI_FORECAST=anchored).

Why: over the first measured week the market's price forecast these 15-minute contracts better than the
desk's 50/50 blend of a spot-price formula and Jev at every horizon, and the blend sat too close to 50/50,
so the desk bought fairly priced underdogs, sold its winners early and held its losers to zero.

The model. Every BTC and ETH contract here settles on the simple average of the sixty one-second CF
Benchmarks index prints before the close. With the log price a driftless random walk of variance s2 per
second, tau seconds before the close and W = 60:

  tau >= W       log A - log S ~ N(0, s2 * (tau - 2W/3))      the last minute's average moves a third as much
  0 < tau < W    log A = (e * m_obs + tau * log S) / W + N(0, s2 * tau^3 / (3 W^2)),  e = W - tau seconds
                 already averaged, m_obs their mean log price

with s2 from an exponentially weighted variance of the underlying's spot (30-minute half-life).

The forecast. q = pool(market mid, model, w): the market price moved toward the model by w in log-odds,
w fitted by maximum likelihood on forecasts recorded at fixed horizons (420, 300, 180 and 60 seconds before
each close) once their contracts settled, refitted every REFIT_EVERY new ones and held at 0 until MIN_ROWS
exist. With w = 0, q is the market and nothing trades, which is the right answer in a calibrated market.

The trade (final_pick_anchored), desk v3's rules (DESK_RULES), the owner's pick of 2026-11-06 for the round
after v2's week. Entries between 180 and 600 seconds before the close (v2 entered from 60: inside 3 minutes
its forecast graded worse than Kalshi's own mid), at the displayed price, when q clears the price by the
desk's edge bar: (1 + margin) x (the taker fee + half the spread). Then hold to settlement, except the
owner's late stop on long shots: a bet bought under LATE_STOP_BELOW (50 cents) still losing LATE_STOP_S
seconds before the close is sold; a favourite is held to the close (v2 sold three favourites in their last
minute and all three then won).
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from statistics import NormalDist, median

from policy.binary import BinaryCosts, edge_bps, min_edge
from policy.decide import HOLD, ActionScore, Pick

MODEL_VERSION = "anchored-1"
_N = NormalDist()
WINDOW_S = 60.0
EPS = 1e-6
HORIZONS_S = (420, 300, 180, 60)
HORIZON_SLACK_S = 24
MIN_ROWS = 300
REFIT_EVERY = 25
STALE_QUOTE_MS = 24_000
CORR_WINDOW = 50
DESK_RULES = "v3"              # the trade rules below; v2 traded (60, 600) and late-stopped every bet
TRADE_WINDOW_S = (180, 600)
LATE_STOP_S = 60
LATE_STOP_BELOW = 0.50         # the late stop sells only bets bought under this price (their own side's)


# ---- the settlement model ------------------------------------------------------------------------

def log_average_dist(spot: float, tau_s: float, s2_per_s: float, *, window_s: float = WINDOW_S, observed_log_mean: float | None = None) -> tuple[float, float]:
    """Mean and standard deviation of log(settlement average) seen from now."""
    x = math.log(spot)
    if tau_s >= window_s:
        return x, math.sqrt(max(s2_per_s * (tau_s - 2.0 * window_s / 3.0), 0.0))
    if tau_s <= 0:
        return (observed_log_mean if observed_log_mean is not None else x), 0.0
    elapsed = window_s - tau_s
    obs = observed_log_mean if observed_log_mean is not None else x
    mean = (elapsed * obs + tau_s * x) / window_s
    sd = math.sqrt(max(s2_per_s * tau_s ** 3 / (3.0 * window_s ** 2), 0.0))
    return mean, sd


def _p_above(log_k: float, mean: float, sd: float) -> float:
    if sd <= 0:
        return 1.0 if mean > log_k else 0.0
    return 1.0 - _N.cdf((log_k - mean) / sd)


def p_contract(strike_type: str, floor: float | None, cap: float | None, spot: float, tau_s: float, s2_per_s: float, *,
               window_s: float = WINDOW_S, observed_log_mean: float | None = None) -> float | None:
    """P(YES) for a contract on the settlement average: greater/greater_or_equal (floor), less/less_or_equal
    (cap, or floor when cap is absent) or between (floor..cap). None when a needed strike is missing."""
    if spot is None or spot <= 0 or s2_per_s is None or s2_per_s < 0:
        return None
    mean, sd = log_average_dist(spot, tau_s, s2_per_s, window_s=window_s, observed_log_mean=observed_log_mean)
    kind = (strike_type or "").lower()
    if kind in ("greater", "greater_or_equal", "greater_than_or_equal", "at_or_above", "above"):
        return None if not floor else _p_above(math.log(floor), mean, sd)
    if kind in ("less", "less_or_equal", "less_than", "less_than_or_equal", "at_or_below", "below"):
        k = cap if cap else floor
        return None if not k else 1.0 - _p_above(math.log(k), mean, sd)
    if kind == "between":
        if not floor or not cap:
            return None
        return max(0.0, _p_above(math.log(floor), mean, sd) - _p_above(math.log(cap), mean, sd))
    return None


class EwmaVol:
    """Per-second variance of log price from irregular samples, exponentially weighted with a half-life in
    seconds and floored, so one quiet stretch cannot make the model certain."""

    def __init__(self, half_life_s: float = 1800.0, floor_bps_per_sqrt_s: float = 0.3, initial_bps_per_sqrt_s: float = 1.0) -> None:
        self.half_life_s = half_life_s
        self.floor = (floor_bps_per_sqrt_s / 1e4) ** 2
        self.var = (initial_bps_per_sqrt_s / 1e4) ** 2
        self._last: tuple[int, float] | None = None

    def update(self, ts_ms: int, price: float) -> None:
        if price is None or price <= 0:
            return
        if self._last is not None:
            t0, p0 = self._last
            dt = (ts_ms - t0) / 1000.0
            if 0 < dt <= 600:
                r2 = math.log(price / p0) ** 2
                a = 1.0 - 0.5 ** (dt / self.half_life_s)
                self.var = (1 - a) * self.var + a * (r2 / dt)
            if dt <= 0:
                return
        self._last = (ts_ms, price)

    @property
    def s2_per_s(self) -> float:
        return max(self.var, self.floor)


def logit(p: float) -> float:
    p = min(1 - EPS, max(EPS, p))
    return math.log(p / (1 - p))


def inv_logit(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def pool(market: float, model: float, w: float) -> float:
    """The market price moved toward the model by weight w in log-odds; w = 0 is the market itself."""
    return inv_logit(logit(market) + w * (logit(model) - logit(market)))


def fit_weight(rows: Iterable[tuple[float, float, int]], *, lo: float = -1.0, hi: float = 2.0, steps: int = 61) -> tuple[float, float]:
    """The weight that maximizes the log-likelihood of outcomes y under pool(m, p, w), by grid search;
    returns (w, mean log loss at w). rows are (market, model, y)."""
    rows = list(rows)
    if not rows:
        return 0.0, float("nan")
    best = (0.0, float("inf"))
    for i in range(steps):
        w = lo + (hi - lo) * i / (steps - 1)
        loss = sum(log_loss(pool(m, p, w), y) for m, p, y in rows) / len(rows)
        if loss < best[1]:
            best = (w, loss)
    return best


def log_loss(p: float, y: int) -> float:
    p = min(1 - EPS, max(EPS, p))
    return -math.log(p if y else 1 - p)


def brier(p: float, y: int) -> float:
    return (p - y) ** 2


# ---- the forecaster ------------------------------------------------------------------------------

class AnchoredForecaster:
    """Turns the desk's per-block tape into a forecast for every series' current contract.

    observe_tape(ts, contracts) takes one block's tape record (series -> the contract fields the desk logs:
    ticker, strike, strike_type, expires_in_s, spot, yes_bid, yes_ask, quote_ts) and returns series ->
    {ticker, tau, bid, ask, m, p, q, w} for every contract with a usable quote; `latest` keeps that last
    answer. observe_settlement(ticker, payout) resolves the horizon rows recorded for the contract and
    refits the weight. observe_settlement_value(ticker, value) feeds Kalshi's settlement value (the index
    average), whose gap to the spot's last minute corrects later spots toward the index; the paper desk has
    no such value and runs without it (the gap was 0.1 to 0.2 bps over the first week).

    fixed_weight pins w (the pre-flight's scripted desk); otherwise w is fitted as described above."""

    def __init__(self, *, min_rows: int = MIN_ROWS, refit_every: int = REFIT_EVERY, fixed_weight: float | None = None, track_index_gap: bool = True) -> None:
        self.min_rows = min_rows
        self.refit_every = refit_every
        self.track_index_gap = track_index_gap
        self.vols: dict[str, EwmaVol] = defaultdict(EwmaVol)
        self.gaps: dict[str, list[float]] = defaultdict(list)          # series -> recent (settlement value - spot) in bps
        self.window_spots: dict[str, list[float]] = defaultdict(list)  # ticker -> log spots seen in its last minute
        self.sym_of: dict[str, str] = {}
        self.pending_rows: dict[str, list[dict]] = defaultdict(list)    # ticker -> horizon rows awaiting the outcome
        self.recorded: set[tuple[str, int]] = set()
        self.resolved_rows: list[dict] = []
        self.outcomes: dict[str, int] = {}
        self.fixed_weight = fixed_weight
        self.weight = 0.0 if fixed_weight is None else float(fixed_weight)
        self.weight_loss: float | None = None
        self._last_fit_n = 0
        self.latest: dict[str, dict] = {}

    def corr_bps(self, sym: str) -> float:
        g = self.gaps[sym][-CORR_WINDOW:]
        return median(g) if g else 0.0

    def observe_tape(self, ts: int, contracts: Mapping[str, Mapping]) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for sym, c in contracts.items():
            spot, ticker, tau = c.get("spot"), c.get("ticker"), c.get("expires_in_s")
            if not spot or not ticker or tau is None:
                continue
            self.vols[sym].update(ts, float(spot))
            self.sym_of[ticker] = sym
            log_spot = math.log(float(spot))
            if tau <= 60:
                self.window_spots[ticker].append(log_spot)
            bid, ask, qts = c.get("yes_bid"), c.get("yes_ask"), c.get("quote_ts")
            if bid is None or ask is None or qts is None or ts - qts > STALE_QUOTE_MS or not 0 < bid <= ask < 1 or tau <= 0:
                continue
            corr = self.corr_bps(sym)
            adj_spot = float(spot) * math.exp(corr / 1e4)
            obs = self.window_spots[ticker]
            obs_mean = (sum(obs) / len(obs) + corr / 1e4) if (tau < 60 and obs) else None
            p = p_contract(c.get("strike_type") or "greater_or_equal", c.get("strike"), None, adj_spot, float(tau), self.vols[sym].s2_per_s, observed_log_mean=obs_mean)
            if p is None:
                continue
            m = (bid + ask) / 2
            for h in HORIZONS_S:
                if (ticker, h) not in self.recorded and h - HORIZON_SLACK_S < tau <= h:
                    self.recorded.add((ticker, h))
                    self.pending_rows[ticker].append({"ticker": ticker, "sym": sym, "h": h, "ts": ts, "m": m, "p": p, "desk": c.get("model_p_yes")})
            out[sym] = {"ticker": ticker, "ts": ts, "tau": float(tau), "bid": bid, "ask": ask, "m": m, "p": p, "w": self.weight, "q": pool(m, p, self.weight)}
        self.latest = out
        return out

    def observe_settlement(self, ticker: str, payout: float | None) -> int | None:
        """The contract's outcome (1 YES, 0 NO); the first settlement of a ticker counts, repeats are ignored."""
        if ticker in self.outcomes:
            return None
        y = 1 if float(payout or 0.0) >= 0.5 else 0
        self.outcomes[ticker] = y
        for row in self.pending_rows.pop(ticker, []):
            self.resolved_rows.append({**row, "y": y})
        if not self.track_index_gap:
            self.window_spots.pop(ticker, None)
        if self.fixed_weight is None and len(self.resolved_rows) >= self.min_rows and len(self.resolved_rows) - self._last_fit_n >= self.refit_every:
            self.weight, self.weight_loss = fit_weight((r["m"], r["p"], r["y"]) for r in self.resolved_rows)
            self._last_fit_n = len(self.resolved_rows)
        return y

    def observe_settlement_value(self, ticker: str, value: float | None) -> None:
        sym = self.sym_of.get(ticker)
        spots = self.window_spots.pop(ticker, None)
        if sym and value and spots:
            self.gaps[sym].append(1e4 * (math.log(float(value)) - sum(spots) / len(spots)))

    def warm_from_log(self, log_dir: str | Path, *, until_ms: int | None = None) -> int:
        """Replay the desk's own log (tape and settlements, in order, settlements first at a shared time) so a
        restarted desk forecasts exactly as if it had run throughout. Returns the number of records replayed."""
        timeline: list[tuple[int, int, dict]] = []
        for path in sorted(Path(log_dir).glob("events-*.jsonl")):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if '"kind":"tape"' in line or '"kind": "tape"' in line:
                        order = 1
                    elif '"kind":"settlement"' in line or '"kind": "settlement"' in line:
                        order = 0
                    else:
                        continue
                    try:
                        e = json.loads(line)
                    except ValueError:
                        continue
                    ts = e.get("ts")
                    if not isinstance(ts, int) or (until_ms is not None and ts >= until_ms):
                        continue
                    if order == 0 and not e.get("ticker"):
                        continue
                    timeline.append((ts, order, e))
        timeline.sort(key=lambda t: (t[0], t[1]))
        for ts, order, e in timeline:
            if order == 0:
                self.observe_settlement(e["ticker"], e.get("payout"))
            else:
                self.observe_tape(ts, e.get("contracts") or {})
        self.latest = {}
        return len(timeline)

    def state(self) -> dict:
        return {"model": MODEL_VERSION, "weight": round(self.weight, 4), "resolved": len(self.resolved_rows), "min_rows": self.min_rows,
                "weight_fit_log_loss": None if self.weight_loss is None else round(self.weight_loss, 4)}


# ---- the decision --------------------------------------------------------------------------------

def _late_stop(position, contract: Mapping, forecast: Mapping | None) -> tuple[bool, float, float] | None:
    """(losing, sell price, price paid) for the position's own side, or None without a quote."""
    src = forecast if forecast and forecast.get("ticker") == contract.get("ticker") else contract
    bid, ask = src.get("bid", src.get("yes_bid")), src.get("ask", src.get("yes_ask"))
    if bid is None or ask is None:
        return None
    qty, entry = float(position.qty), float(position.entry_price)
    sell, paid = (float(bid), entry) if qty > 0 else (1.0 - float(ask), 1.0 - entry)
    return sell < paid, sell, paid


def final_pick_anchored(phase: str, forecast: Mapping | None, contract: Mapping, costs: BinaryCosts, *, position=None) -> Pick:
    """Entry: buy YES when q - ask >= min_edge(ask), or NO when (1 - q) - (1 - bid) >= min_edge(1 - bid), with
    TRADE_WINDOW_S (180 to 600) seconds left, on the forecast's own quote. Manage: hold to settlement, except
    sell a bet bought under LATE_STOP_BELOW still losing LATE_STOP_S seconds before the close."""
    tau = contract.get("expires_in_s")
    if phase == "entry":
        if not forecast or forecast.get("ticker") != contract.get("ticker") or float(forecast.get("w") or 0.0) == 0.0 or tau is None:
            return Pick(HOLD, 0.0, 1.0, 0.0, ())
        q, bid, ask = float(forecast["q"]), float(forecast["bid"]), float(forecast["ask"])
        spread = max(0.0, ask - bid)
        no_price = 1.0 - bid
        candidates = (
            ActionScore("enter_long", q, ask + min_edge(ask, spread, costs), edge_bps(q, ask)),
            ActionScore("enter_short", 1.0 - q, no_price + min_edge(no_price, spread, costs), edge_bps(1.0 - q, no_price)),
        )
        best = max(candidates, key=lambda s: (s.prob - s.threshold, s.prob))
        in_window = TRADE_WINDOW_S[0] <= float(tau) <= TRADE_WINDOW_S[1] and contract.get("tradable", True)
        if in_window and best.prob >= best.threshold:
            return Pick(best.action, best.prob, best.threshold, best.expected_edge_bps, candidates)
        return Pick(HOLD, best.prob, best.threshold, best.expected_edge_bps, candidates)
    if position is None or tau is None:
        return Pick(HOLD, 0.0, 1.0, 0.0, ())
    stop = _late_stop(position, contract, forecast)
    if stop is None:
        return Pick(HOLD, 0.0, 1.0, 0.0, ())
    losing, sell, paid = stop
    score = ActionScore("exit", round(sell, 4), round(paid, 4), 0.0)
    if losing and paid < LATE_STOP_BELOW and 0 < float(tau) <= LATE_STOP_S:
        return Pick("exit", sell, paid, 0.0, (score,))
    return Pick(HOLD, sell, paid, 0.0, (score,))
