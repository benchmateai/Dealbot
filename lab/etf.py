"""ETF trend and rotation backtest: do published timing rules for stock, bond, real-estate, commodity and gold funds beat
simply holding the S&P 500, or a 60/40 mix, after costs, in the years after each rule was published? Paper only: public
daily prices, no orders, no key.

Background: the owner asked whether "regime rotation and volatility-filtered trend following" on liquid ETFs, ranked
first in a list of automated setups they found, would work. The cross-venue report (reports/Viable trading strategies
across venues.md) scored micro-futures trend following at 30% but did not research ETF rotation. These rules hold funds
most of the time, so the bar is holding the market, not cash.

The rules below were fixed at REGISTERED, before any price was downloaded, and are not tuned on what the test shows.
Faber's and Antonacci's rules keep the parameters their authors published; vol_target's were chosen here, before any
data (see below). Known beforehand, from memory and earlier research, not from this
data: the authors' own published results; that trend and timing rules are widely reported to have cut the 2008 losses
and to have lagged buy-and-hold through much of the 2010s; the SG Trend Index and Cboe PutWrite figures in the research
notes. To check the two sites could be read, one five-day Yahoo request for SPY (November 2023) and the whole T-bill
file were downloaded and only their sizes printed. After REGISTERED the full data was downloaded and the data check
run, printing only each fund's first day, row counts, gaps, jumps, dividend and split counts and the days off Yahoo's
adjusted close (none). No other price, return or result was read before the report.

On timing: the rules and this file were written by 22:41:02Z (when the tests were saved), and REGISTERED was stamped
just before the download, which began at 22:41:45Z, 15 seconds before the time it records; no rule changed between.

Amended at AMENDED after two reviews, before the report was run: every run now starts at the signal-day close before its
first purchase, worth 1 in cash, so that purchase's cost counts in every figure (before, the monthly and yearly returns
and the largest fall started after it, and cash did not accrue on the trade day); T-bill rates that stop more than
STALE_DAYS before END, or leave more than STALE_DAYS between two rates from SPY's first day on, or start after it, are a
data problem, as is a fund with no closes; the printed report adds each run's worst year and the longest periods' years
and rolling shares; a data problem makes the report exit with 1; and the text now says that the 10-month rule reads
the total-return level, not the price, that vol_target resets monthly and its parameters are not its authors', when
ACWX starts, what LEVEL buys, what a pass means, and that turnover counts the opening purchase and the worst year can
be a part year. No rule's trades changed.

Data: daily closes and dividends from Yahoo Finance's chart API for TICKERS. Each fund's total-return level grows by
(close + dividends that went ex since the last close) / last close, on SPY's trading days; a day without a close
carries the level forward. Cash earns the 3-month T-bill rate (FRED series DTB3, percent a year): the rate dated on or
before the previous trading day, times the calendar days since it, over 360. Days run to END, the last trading day of
October 2026.

Timing: every rule decides on the close of the last trading day of each month (its signal day), from levels up to that
close, and trades on the close of the next trading day, so the day after a signal still earns the old holdings. A trade
costs COST of the value of each fund bought or sold (moving cash is free), charged at the trade. Each run starts at a signal-day close
worth 1 in cash, so its first purchase is charged too and counts in every figure. Between trades, holdings drift with
prices.

Rules (cash means T-bills):
- spy_sma10 (Faber 2007, the timing rule on one fund): SPY if its total-return level (not its price) is above the
  mean of its last SMA_MONTHS month-end levels (this one included), else cash.
- gtaa5 (Faber 2007, "A Quantitative Approach to Tactical Asset Allocation"): a fifth each in GTAA: SPY (US stocks), EFA
  (foreign stocks), IEF (7-10 year Treasuries), VNQ (real estate) and DBC (commodities; Faber used the GSCI). Each fifth
  sits in its fund under the same 10-month rule and in cash otherwise, reset to fifths every month.
- gem (Antonacci 2014, "Dual Momentum Investing", Global Equities Momentum): if SPY's MOM_MONTHS-month return beats
  cash's, hold whichever of SPY and EFA returned more (EFA, developed markets only, stands in for ACWI ex-US: its fund,
  ACWX, starts only in 2008, and one fund serves both the main window and the longest period; a tie goes to SPY);
  otherwise AGG (US bonds).
- vol_target (volatility management after Moreira & Muir 2017, who scale by inverse variance, here in a simple
  practitioners' form whose parameters were chosen before any data, not taken from them): SPY at TARGET_VOL divided by
  its realized volatility over the last VOL_DAYS daily returns (annualized over 252 days), at most VOL_CAP (no margin),
  the rest in cash, reset monthly.
- qqq_gold (the owner's example, "QQQ vs. gold"): whichever of QQQ and GLD returned more over MOM_MONTHS months (a tie
  goes to QQQ), if that beat cash's return, else cash. Description only: the two funds were picked by people who knew
  how they had done, so the whole period is hindsight and no pass would count.
Benchmarks: spy (held), sixty_forty (60% SPY and 40% IEF, reset every month), and qqq (held) beside qqq_gold. Each is
run over the same days as the rule it is compared with, with the same costs.

Main test (pass or fail), for each of the four published rules over its own window: from the first trading day of
POST_FROM's month (the trade on the signal of the month before) to END.
(a) Its Sharpe ratio (the mean of the monthly returns over cash's, divided by their standard deviation, times the square
    root of 12) beats both spy's and sixty_forty's.
(b) Its Sharpe minus the better benchmark's (the one with the higher Sharpe in the window) is above zero across a LEVEL
    stationary-bootstrap interval over months (mean block BLOCK months, BOOTSTRAP draws, SEED; the rule and the
    benchmark drawn on the same months). LEVEL is 1 - 0.05 / 4 and only the interval's lower end counts. In the
    reviewer's simulations with no true gap (synthetic data, this resampling, 2,000 draws), (b) alone passed about 1-2.5%
    of the time per rule (noisy estimates), because the percentile bootstrap runs narrow; so the chance that any of the four passes by
    luck is a few percent.
(c) Its Sharpe beats both benchmarks' in each half of the window's months.
(d) Its largest fall from a peak (daily values) is smaller than spy's.
A rule passes only if all four hold. A pass means a better return for the risk taken and a smaller fall, not
necessarily more money: a rule can pass while compounding less than spy. Windows of 9 to 20 years can only show a large difference, so a rule that is truly
a little better can fail: a fail means "not shown", not "shown worse". If the data check finds a problem (a jump beyond
JUMP in a day, which suggests a misread split; more than MAX_GAP trading days in a row without a close; a fund with no
closes; END missing; T-bill rates that stop more than STALE_DAYS before END, start after SPY's first day, or leave
more than STALE_DAYS between two rates; or a fund missing when a rule
needs it), the report names it and runs no test.

Description, not pass or fail: each rule over the longest period its data allows, beside the benchmarks that existed at
its start; returns a year, volatility, the worst month and the worst calendar year; how much of the money sat in funds
rather than cash; turnover a year; each calendar year's return beside the benchmarks'; and the share of rolling
ROLL-month spans in which the rule's return beat each benchmark's. Taxes are left out: in a taxable account, frequent
switching turns long-term gains short-term. Turnover counts the opening purchase, and the worst calendar year can be a
part year (the first, or 2026 to October).

    python -m lab.etf fetch --data <dir>      (nine downloads, a pause before each; resumable)
    python -m lab.etf report --data <dir> [--out results.json]
"""

from __future__ import annotations

import argparse
import csv
import http.client
import io
import itertools
import json
import math
import random
import statistics
import sys
import time
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from lab.longshot import _write

REGISTERED = "2026-11-12T22:42:00Z"
AMENDED = "2026-11-12T23:22:00Z"
END = date(2026, 10, 30)
TICKERS = ("SPY", "QQQ", "EFA", "IEF", "AGG", "VNQ", "DBC", "GLD")
CASH = "CASH"
COST = 0.001
SMA_MONTHS = 10
MOM_MONTHS = 12
TARGET_VOL, VOL_DAYS, VOL_CAP = 0.15, 21, 1.0
GTAA = ("SPY", "EFA", "IEF", "VNQ", "DBC")
POST_FROM = {"spy_sma10": date(2007, 1, 1), "gtaa5": date(2007, 1, 1), "gem": date(2015, 1, 1), "vol_target": date(2018, 1, 1)}
BENCHMARKS = ("spy", "sixty_forty")
LEVEL = 1 - 0.05 / 4
BLOCK = 12
BOOTSTRAP = 5_000
SEED = 20261112
ROLL = 36
JUMP = 0.25
MAX_GAP = 5
STALE_DAYS = 10
ADJ_TOL = 0.002
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{}?period1={}&period2={}&interval=1d&events=div%2Csplit"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3"


class MissingData(Exception):
    """A rule was asked to decide on a month its funds' data does not reach."""


# --- data ---------------------------------------------------------------------------------------------------------

def parse_yahoo(raw: dict) -> dict:
    """A chart reply as {"rows": {day: (close, adjusted close)}, "dividends": {ex day: amount}}, days in the exchange's
    time; a missing or non-positive close is None."""
    res = raw["chart"]["result"][0]
    off = int((res.get("meta") or {}).get("gmtoffset") or 0)

    def day(t) -> date:
        return datetime.fromtimestamp(int(t) + off, UTC).date()

    ts = res.get("timestamp") or []
    ind = res.get("indicators") or {}
    closes = (ind.get("quote") or [{}])[0].get("close") or []
    adj = (ind.get("adjclose") or [{}])[0].get("adjclose") or []
    rows = {}
    for i, t in enumerate(ts):
        c = closes[i] if i < len(closes) else None
        a = adj[i] if i < len(adj) else None
        rows[day(t)] = (float(c) if c is not None and c > 0 else None, float(a) if a is not None and a > 0 else None)
    divs: dict[date, float] = {}
    for v in ((res.get("events") or {}).get("dividends") or {}).values():
        d = day(v["date"])
        divs[d] = divs.get(d, 0.0) + float(v["amount"])
    return {"rows": dict(sorted(rows.items())), "dividends": divs}


def tr_levels(fund: dict, calendar: list[date]) -> tuple[list[float | None], dict]:
    """The fund's total-return level on each calendar day (None before its first close) and notes for the data check:
    its first day, the longest run of days without a close, daily moves beyond JUMP, and days whose move differs from
    Yahoo's adjusted close by more than ADJ_TOL."""
    rows, divs = fund["rows"], sorted(fund["dividends"].items())
    notes: dict = {"first": None, "max_gap": 0, "jumps": [], "adj_off": 0}
    out: list[float | None] = []
    level = prev = prev_adj = None
    carry, gap, j = 0.0, 0, 0
    for d in calendar:
        while j < len(divs) and divs[j][0] <= d:
            carry += divs[j][1]
            j += 1
        close, adj = rows.get(d, (None, None))
        if close is None:
            if level is not None:
                gap += 1
                notes["max_gap"] = max(notes["max_gap"], gap)
            out.append(level)
            continue
        if level is None:  # the first close: dividends before it belong to no holder here
            level, notes["first"] = 1.0, d
        else:
            r = (close + carry) / prev - 1
            if abs(r) > JUMP:
                notes["jumps"].append((d.isoformat(), round(r, 4)))
            if adj is not None and prev_adj is not None and abs(adj / prev_adj - 1 - r) > ADJ_TOL:
                notes["adj_off"] += 1
            level *= 1 + r
        carry, prev, prev_adj, gap = 0.0, close, adj, 0
        out.append(level)
    return out, notes


def parse_fred(text: str) -> dict[date, float]:
    """FRED's CSV as {day: percent a year}; the header and missing values (".") are skipped."""
    out = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 2:
            continue
        try:
            out[date.fromisoformat(row[0].strip())] = float(row[1])
        except ValueError:
            continue
    return out


def cash_levels(rates: dict[date, float], calendar: list[date]) -> list[float]:
    """T-bills' level on each calendar day: from one trading day to the next, the rate dated on or before the first of
    them, times the calendar days between, over 360."""
    known, j, rate = sorted(rates.items()), 0, None
    out, level, prev = [], 1.0, None
    for d in calendar:
        if prev is not None:
            while j < len(known) and known[j][0] <= prev:
                rate = known[j][1]
                j += 1
            if rate is None:
                raise MissingData(f"no T-bill rate on or before {prev}")
            level *= 1 + rate / 100 * (d - prev).days / 360
        out.append(level)
        prev = d
    return out


class World:
    """Every fund's level and cash's on SPY's trading days, with the indices of each month's last trading day."""

    def __init__(self, days: list[date], levels: dict[str, list], cash: list[float], notes: dict | None = None,
                 cash_last: date | None = None, cash_gap: int = 0) -> None:
        self.days, self.notes, self.cash_last, self.cash_gap = days, notes or {}, cash_last, cash_gap
        self.levels = {**levels, CASH: cash}
        self.month_ends = [i for i in range(len(days)) if i == len(days) - 1 or days[i + 1].month != days[i].month]


def load(data: Path) -> World:
    funds = {t: parse_yahoo(json.loads((data / "yahoo" / f"{t}.json").read_text())) for t in TICKERS}
    rates = parse_fred((data / "DTB3.csv").read_text())
    days = [d for d, (c, _) in funds["SPY"]["rows"].items() if c is not None and d <= END]
    levels, notes = {}, {}
    for t in TICKERS:
        levels[t], notes[t] = tr_levels(funds[t], days)
    return World(days, levels, cash_levels(rates, days), notes, max(rates) if rates else None, rate_gap(rates, days[0]))


def rate_gap(rates: dict[date, float], first: date) -> int:
    """The most calendar days between two T-bill rates, counting from the last rate on or before `first`."""
    dates = sorted(rates)
    from_ = max((d for d in dates if d <= first), default=None)
    dates = [d for d in dates if from_ is not None and d >= from_]
    return max(((b - a).days for a, b in itertools.pairwise(dates)), default=0)


# --- rules: each takes the world and k, the position of a signal day in world.month_ends, and reads nothing after it --

def above_sma(w: World, fund: str, k: int) -> bool | None:
    if k < SMA_MONTHS - 1:
        return None
    vals = [w.levels[fund][i] for i in w.month_ends[k - SMA_MONTHS + 1:k + 1]]
    if any(v is None for v in vals):
        return None
    return vals[-1] > sum(vals) / len(vals)


def momentum(w: World, fund: str, k: int) -> float | None:
    if k < MOM_MONTHS:
        return None
    a, b = w.levels[fund][w.month_ends[k - MOM_MONTHS]], w.levels[fund][w.month_ends[k]]
    return None if a is None or b is None else b / a - 1


def rule_spy_sma10(w: World, k: int) -> dict | None:
    up = above_sma(w, "SPY", k)
    return None if up is None else ({"SPY": 1.0} if up else {CASH: 1.0})


def rule_gtaa5(w: World, k: int) -> dict | None:
    out: dict[str, float] = {}
    for f in GTAA:
        up = above_sma(w, f, k)
        if up is None:
            return None
        key = f if up else CASH
        out[key] = out.get(key, 0.0) + 1 / len(GTAA)
    return out


def rule_gem(w: World, k: int) -> dict | None:
    us, intl, cash = momentum(w, "SPY", k), momentum(w, "EFA", k), momentum(w, CASH, k)
    if us is None or intl is None or cash is None or w.levels["AGG"][w.month_ends[k]] is None:
        return None
    if us > cash:
        return {"SPY": 1.0} if us >= intl else {"EFA": 1.0}
    return {"AGG": 1.0}


def rule_vol_target(w: World, k: int) -> dict | None:
    i = w.month_ends[k]
    if i < VOL_DAYS:
        return None
    lv = w.levels["SPY"][i - VOL_DAYS:i + 1]
    if any(v is None for v in lv):
        return None
    vol = statistics.stdev([b / a - 1 for a, b in itertools.pairwise(lv)]) * math.sqrt(252)
    x = VOL_CAP if vol <= 0 else min(VOL_CAP, TARGET_VOL / vol)
    return {"SPY": x, CASH: 1 - x} if x < 1 else {"SPY": 1.0}


def rule_qqq_gold(w: World, k: int) -> dict | None:
    q, g, c = momentum(w, "QQQ", k), momentum(w, "GLD", k), momentum(w, CASH, k)
    if q is None or g is None or c is None:
        return None
    best, m = ("QQQ", q) if q >= g else ("GLD", g)
    return {best: 1.0} if m > c else {CASH: 1.0}


def hold(weights: dict[str, float]):
    def rule(w: World, k: int) -> dict | None:
        if any(w.levels[f][w.month_ends[k]] is None for f in weights if f != CASH):
            return None
        return dict(weights)
    return rule


RULES = {"spy_sma10": rule_spy_sma10, "gtaa5": rule_gtaa5, "gem": rule_gem, "vol_target": rule_vol_target,
         "qqq_gold": rule_qqq_gold, "spy": hold({"SPY": 1.0}), "sixty_forty": hold({"SPY": 0.6, "IEF": 0.4}),
         "qqq": hold({"QQQ": 1.0})}


# --- simulation and statistics ------------------------------------------------------------------------------------

def simulate(w: World, name: str, k0: int) -> dict:
    """Run a rule from the close of signal day k0 (its origin, worth 1 in cash) to the last day; its first trade (its
    start) is on the next day's close. Returns both day indices, daily values from the origin, and each trade's
    turnover and share in funds."""
    rule, me = RULES[name], w.month_ends
    origin = me[k0]
    start = origin + 1
    if start >= len(w.days):
        raise MissingData(f"{name}: no trading day after {w.days[origin]}")
    signals = {me[k] + 1: k for k in range(k0, len(me)) if me[k] + 1 < len(w.days)}
    holdings: dict[str, float] = {CASH: 1.0}
    values, turnover, invested = {origin: 1.0}, [], []
    for i in range(start, len(w.days)):
        for f in holdings:
            holdings[f] *= w.levels[f][i] / w.levels[f][i - 1]
        if i in signals:
            target = rule(w, signals[i])
            if target is None:
                raise MissingData(f"{name}: its funds' data does not reach the signal of {w.days[me[signals[i]]]}")
            v = sum(holdings.values())
            now = {f: x / v for f, x in holdings.items()}
            t = sum(abs(target.get(f, 0.0) - now.get(f, 0.0)) for f in set(target) | set(now) if f != CASH)
            v -= COST * t * v
            holdings = {f: x * v for f, x in target.items() if x > 0}
            turnover.append(t)
            invested.append(1 - target.get(CASH, 0.0))
        values[i] = sum(holdings.values())
    return {"name": name, "origin": origin, "start": start, "values": values, "turnover": turnover, "invested": invested}


def monthly(w: World, sim: dict) -> tuple[list[float], list[float]]:
    """The run's monthly returns, month end to month end from its origin, and cash's over the same spans."""
    pts = [sim["origin"]] + [i for i in w.month_ends if i > sim["origin"]]
    v, c = sim["values"], w.levels[CASH]
    return [v[b] / v[a] - 1 for a, b in itertools.pairwise(pts)], [c[b] / c[a] - 1 for a, b in itertools.pairwise(pts)]


def sharpe(excess: list[float]) -> float:
    if len(excess) < 2:
        return 0.0
    sd = statistics.stdev(excess)
    return 0.0 if sd == 0 else statistics.fmean(excess) / sd * math.sqrt(12)


def max_drawdown(values: dict[int, float]) -> float:
    peak, worst = 0.0, 0.0
    for i in sorted(values):
        peak = max(peak, values[i])
        worst = min(worst, values[i] / peak - 1)
    return worst


def year_returns(w: World, sim: dict) -> dict[int, float]:
    v, last = sim["values"], len(w.days) - 1
    pts = [sim["origin"]] + [i for i in range(sim["origin"], last + 1) if i == last or w.days[i + 1].year != w.days[i].year]
    return {w.days[b].year: v[b] / v[a] - 1 for a, b in itertools.pairwise(pts) if b > a}


def stats(w: World, sim: dict) -> dict:
    rets, cash = monthly(w, sim)
    last = len(w.days) - 1
    years = (w.days[last] - w.days[sim["origin"]]).days / 365.25
    yr = year_returns(w, sim)
    return {
        "from": w.days[sim["start"]].isoformat(), "to": w.days[last].isoformat(), "months": len(rets),
        "growth_of_1": sim["values"][last], "a_year": sim["values"][last] ** (1 / years) - 1 if years > 0 else 0.0,
        "volatility": statistics.stdev(rets) * math.sqrt(12) if len(rets) > 1 else 0.0,
        "sharpe": sharpe([a - b for a, b in zip(rets, cash)]), "max_drawdown": max_drawdown(sim["values"]),
        "worst_month": min(rets) if rets else 0.0, "worst_year": min(yr.items(), key=lambda kv: kv[1]) if yr else None,
        "in_funds": statistics.fmean(sim["invested"]) if sim["invested"] else 0.0,
        "turnover_a_year": sum(sim["turnover"]) / years if years > 0 else 0.0, "years": yr,
    }


def stationary_indices(n: int, block: int, rng: random.Random) -> list[int]:
    """One stationary-bootstrap draw of n positions: each step starts a new block with chance 1/block, else moves on
    (wrapping round)."""
    out = [rng.randrange(n)]
    while len(out) < n:
        out.append(rng.randrange(n) if rng.random() < 1 / block else (out[-1] + 1) % n)
    return out


def sharpe_gap_interval(a: list[float], b: list[float], rng: random.Random, draws: int | None = None) -> tuple[float, float]:
    """The LEVEL interval of Sharpe(a) - Sharpe(b), both drawn on the same months."""
    draws = draws or BOOTSTRAP
    gaps = []
    for _ in range(draws):
        idx = stationary_indices(len(a), BLOCK, rng)
        gaps.append(sharpe([a[i] for i in idx]) - sharpe([b[i] for i in idx]))
    return percentile_interval(gaps)


def percentile_interval(values: list[float]) -> tuple[float, float]:
    """The LEVEL percentile interval of the values, by sorted position."""
    v, tail = sorted(values), (1 - LEVEL) / 2
    return v[int(tail * len(v))], v[min(len(v) - 1, int((1 - tail) * len(v)))]


def rolling_share(a: list[float], b: list[float], n: int = ROLL) -> float | None:
    """The share of n-month spans in which a compounded to more than b."""
    if len(a) < n:
        return None
    spans = range(len(a) - n + 1)
    return sum(math.prod(1 + x for x in a[i:i + n]) > math.prod(1 + x for x in b[i:i + n]) for i in spans) / len(spans)


def compare(w: World, name: str, k0: int, benches: tuple[str, ...]) -> dict:
    runs = {n: simulate(w, n, k0) for n in (name, *benches)}
    rets = {n: monthly(w, s) for n, s in runs.items()}
    excess = {n: [a - b for a, b in zip(r, c)] for n, (r, c) in rets.items()}
    return {"stats": {n: stats(w, s) for n, s in runs.items()}, "excess": excess,
            "rolling": {b: rolling_share(rets[name][0], rets[b][0]) for b in benches}}


def checks(sh: dict[str, float], lo: float, halves: list[dict[str, float]], dd: dict[str, float], name: str) -> dict:
    """The main test's four conditions for rule `name`."""
    beats = all(sh[name] > sh[b] for b in BENCHMARKS)
    return {"beats_both": beats, "interval_above_zero": lo > 0,
            "both_halves": all(all(h[name] > h[b] for b in BENCHMARKS) for h in halves),
            "smaller_drawdown_than_spy": dd[name] > dd["spy"]}


def judge(w: World, name: str, rng: random.Random) -> dict:
    k0 = max(k for k, i in enumerate(w.month_ends) if w.days[i] < POST_FROM[name])
    c = compare(w, name, k0, BENCHMARKS)
    sh = {n: s["sharpe"] for n, s in c["stats"].items()}
    better = max(BENCHMARKS, key=lambda b: sh[b])
    lo, hi = sharpe_gap_interval(c["excess"][name], c["excess"][better], rng)
    h = len(c["excess"][name]) // 2
    halves = [{n: sharpe(ex[:h]) for n, ex in c["excess"].items()}, {n: sharpe(ex[h:]) for n, ex in c["excess"].items()}]
    ck = checks(sh, lo, halves, {n: s["max_drawdown"] for n, s in c["stats"].items()}, name)
    return {"post_from": POST_FROM[name].isoformat(), "stats": c["stats"], "rolling": c["rolling"], "better": better,
            "sharpe_gap": sh[name] - sh[better], "interval": [lo, hi], "halves": halves, "checks": ck,
            "passed": all(ck.values())}


def longest(w: World, name: str, benches: tuple[str, ...]) -> dict:
    """The rule from its first possible month, beside the benchmarks that existed then."""
    k0 = next((k for k in range(len(w.month_ends) - 1) if RULES[name](w, k) is not None), None)
    if k0 is None:
        raise MissingData(f"{name}: its funds' data never reaches a signal")
    have = tuple(b for b in benches if RULES[b](w, k0) is not None)
    c = compare(w, name, k0, have)
    return {"stats": c["stats"], "rolling": c["rolling"]}


def data_problems(w: World) -> list[str]:
    out = []
    if not w.days or w.days[-1] != END:
        out.append(f"END {END} is not SPY's last trading day in the data")
    if w.cash_last is None or (END - w.cash_last).days > STALE_DAYS:
        out.append(f"T-bill rates stop at {w.cash_last}, more than {STALE_DAYS} days before END")
    if w.cash_gap > STALE_DAYS:
        out.append(f"T-bill rates leave {w.cash_gap} days between two rates")
    for t, n in w.notes.items():
        if n.get("first") is None:
            out.append(f"{t}: no closes")
        if n.get("max_gap", 0) > MAX_GAP:
            out.append(f"{t}: {n['max_gap']} trading days in a row without a close")
        for d, r in n.get("jumps", []):
            out.append(f"{t}: a {r:+.1%} day on {d}")
    return out


def evaluate(w: World) -> dict:
    out: dict = {"registered": REGISTERED, "amended": AMENDED, "end": END.isoformat(), "cost": COST,
                 "data": {t: {"first": n["first"].isoformat() if n.get("first") else None, "max_gap": n.get("max_gap"),
                              "days_off_yahoo_adjusted": n.get("adj_off")} for t, n in w.notes.items()},
                 "problems": data_problems(w)}
    if out["problems"]:
        return out
    rng = random.Random(SEED)
    try:
        out["main"] = {n: judge(w, n, rng) for n in POST_FROM}
        out["longest"] = {n: longest(w, n, BENCHMARKS) for n in POST_FROM}
        out["longest"]["qqq_gold"] = longest(w, "qqq_gold", ("qqq", *BENCHMARKS))
    except MissingData as exc:
        out["problems"].append(str(exc))
        out.pop("main", None)
        out.pop("longest", None)
    return out


# --- report ---------------------------------------------------------------------------------------------------------

def _row(n: str, s: dict) -> str:
    return (f"  {n:<12} {s['a_year']:+7.2%} a year  sharpe {s['sharpe']:5.2f}  vol {s['volatility']:6.2%}  "
            f"worst fall {s['max_drawdown']:+7.2%}  worst month {s['worst_month']:+7.2%}  in funds {s['in_funds']:4.0%}  "
            f"turnover {s['turnover_a_year']:4.1f}/yr  worst year {_worst(s)}")


def _worst(s: dict) -> str:
    return "n/a" if not s["worst_year"] else f"{s['worst_year'][0]} {s['worst_year'][1]:+.1%}"


def _years(stats: dict, name: str) -> str:
    return "  ".join(f"{y} " + "/".join(f"{stats[b]['years'].get(y, 0):+.0%}" for b in stats) for y in sorted(stats[name]["years"]))


def lines(r: dict) -> list[str]:
    out = [(f"ETF trend and rotation backtest (rules registered {r['registered']}, amended {r['amended']}, costs "
            f"{r['cost']:.2%} a side, to {r['end']})")]
    for t, d in r["data"].items():
        out.append(f"  data {t}: from {d['first']}, longest gap {d['max_gap']} days, {d['days_off_yahoo_adjusted']} days off Yahoo's adjusted close")
    if r["problems"]:
        out.append("DATA PROBLEMS, no test run:")
        out += [f"  {p}" for p in r["problems"]]
        return out
    out.append("")
    out.append("Main test (after each rule was published). A pass means a better return for the risk and a smaller fall,")
    out.append("not necessarily more money; a fail means an edge was not shown, not that the rule is worse.")
    for n, m in r["main"].items():
        st = m["stats"][n]
        out.append(f"{n}: {'PASSED' if m['passed'] else 'FAILED'}  ({st['from']} to {st['to']}, {st['months']} months)")
        for b, s in m["stats"].items():
            out.append(_row(b, s))
        lo, hi = m["interval"]
        out.append(f"  sharpe gap vs {m['better']}: {m['sharpe_gap']:+.2f} ({LEVEL:.2%} interval {lo:+.2f} to {hi:+.2f})")
        out.append("  halves: " + "; ".join(", ".join(f"{k} {v:.2f}" for k, v in h.items()) for h in m["halves"]))
        out.append("  checks: " + ", ".join(f"{k} {'yes' if v else 'no'}" for k, v in m["checks"].items()))
        out.append("  beat over 3-year spans: " + ", ".join(f"{b} {v:.0%}" if v is not None else f"{b} n/a" for b, v in m["rolling"].items()))
        out.append(f"  years ({'/'.join(m['stats'])}): " + _years(m["stats"], n))
    out.append("")
    out.append("Longest period each rule's data allows (description):")
    for n, m in r["longest"].items():
        st = m["stats"][n]
        out.append(f"{n} ({st['from']} to {st['to']}, {st['months']} months)")
        for b, s in m["stats"].items():
            out.append(_row(b, s))
        out.append("  beat over 3-year spans: " + ", ".join(f"{b} {v:.0%}" if v is not None else f"{b} n/a" for b, v in m["rolling"].items()))
        out.append(f"  years ({'/'.join(m['stats'])}): " + _years(m["stats"], n))
    return out


# --- fetch ----------------------------------------------------------------------------------------------------------

def _get(url: str, log, agent: str | None = None, tries: int = 4) -> str | None:
    """A gentle GET: a pause before each try. Without `agent`, urllib's own Python-urllib name is sent."""
    for i in range(tries):
        time.sleep(2 + 4 * i)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": agent} if agent else {})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode()
        except (OSError, http.client.HTTPException) as exc:  # a timeout, a refusal, a dropped connection
            log(f"retry {i + 1}: {type(exc).__name__}")
    return None


def fetch(data: Path) -> None:
    (data / "yahoo").mkdir(parents=True, exist_ok=True)
    with open(data / "fetch.log", "a") as logf:
        def log(*a):
            print(datetime.now(UTC).strftime("%H:%M:%SZ"), *a, file=logf, flush=True)
        p1 = int(datetime(1990, 1, 1, tzinfo=UTC).timestamp())
        p2 = int((datetime(END.year, END.month, END.day, tzinfo=UTC) + timedelta(days=7)).timestamp())
        missing = []
        for t in TICKERS:
            p = data / "yahoo" / f"{t}.json"
            if p.exists():
                continue
            raw = _get(YAHOO.format(t, p1, p2), log, "Mozilla/5.0")  # Yahoo answers browsers
            try:
                got = json.loads(raw) if raw else None
                parse_yahoo(got)
            except (ValueError, KeyError, IndexError, TypeError):
                missing.append(t)
                continue
            _write(p, got)
        p = data / "DTB3.csv"
        if not p.exists():
            raw = _get(FRED, log)  # FRED drops names it does not know, a bare "Mozilla/5.0" among them
            if raw and parse_fred(raw):
                tmp = p.with_name(p.name + ".tmp")
                tmp.write_text(raw)
                tmp.replace(p)
            else:
                missing.append("DTB3")
        log(f"done: {len(missing)} missing {missing} (run again to retry)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Published ETF timing rules against holding SPY or a 60/40 mix")
    parser.add_argument("command", choices=("fetch", "report"))
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    data = Path(args.data)
    if args.command == "fetch":
        fetch(data)
        return 0
    try:
        w = load(data)
    except FileNotFoundError as exc:
        print(f"missing data ({exc.filename}): run fetch first")
        return 1
    except MissingData as exc:  # T-bill rates that start after SPY's first day
        r = {"registered": REGISTERED, "amended": AMENDED, "end": END.isoformat(), "cost": COST, "data": {},
             "problems": [str(exc)]}
    else:
        r = evaluate(w)
    if args.out:
        Path(args.out).write_text(json.dumps(r, indent=1, default=str))
    print("\n".join(lines(r)))
    return 1 if r["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
