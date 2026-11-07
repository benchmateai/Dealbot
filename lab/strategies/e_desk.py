"""The E desk: strategy E run as the paper desk of the round after desk v2's week (the owner's choice of
2026-11-07), with the risk rules E's lab replay does not have.

It quotes as lab/strategies/e_incentive.py does: QUOTE_FRACTION of each program's Target Size on both
sides at the side's Reference Price, behind the orders already there, re-joining when that price moves or
the order fills; fills come only from trade prints, by lab/fills.py's pessimistic rules; rewards accrue for
each recorded book while its orders stand, and a program's total under $1 is not paid. It runs on the live
feed the lab records, from START_MS on. Nothing is ever sent to Kalshi: each time it is asked, the desk
replays its rules over the recording in time order, using only what was recorded up to each moment, so it
never sees ahead.

The rules E lacks, fixed before the desk starts. Each stops the desk adding risk in a market; none stops it
quoting the side that pairs off what it already holds there (a YES and a NO pair off at $1), because a
desk that cannot work out of a position is stuck with it (a first draft that pulled both sides did worse
on the recording than E itself):
- MARKET_CAP_USD: no quote adds to a holding already worth this much at its side's mid (E caps contracts
  only, at 30% of the program's Target Size, and keeps that cap too);
- CAPITAL_CAP_USD: resting orders' collateral plus what the holdings are worth never passes this; a quote
  that would is cut to fit;
- the news rule (the news_pause variant, not the main desk): when a market's YES mid moves 5 cents or more
  within NEWS_WINDOW_S (2 minutes), nothing is added there for NEWS_PAUSE_S (15 minutes), and the pause
  runs on while it moves. On E's first 81 hours it paused 64 times and cost $18 against the same rules
  without it, so it runs beside the desk as a variant rather than in it;
- the close rule: nothing is added in the last CLOSE_BUFFER_S (3 hours) before a market closes, when the
  news that settles it arrives (a presidential-approval market E held on the losing side went to 98 cents
  in its last hours on 2026-11-06 and cost E about $109). It reads the close time on each book; the
  recorder has written E's close times only since 2026-11-07 (before, E's books carried none, so the rule
  could not act on the recording before then);
- the loss stop: a market whose fills are marked down LOSS_STOP_USD (40 dollars) or more takes no new risk
  for the rest of the round.

Two more variants, registered on 2026-11-07 from the owner's post-election research (reports/Post midterm
market trading ideas.md), stop adding risk the same way:
- calendar_blackout: nothing is added in a market from BLACKOUT_BEFORE_S before to BLACKOUT_AFTER_S after
  each dated catalyst in CATALYSTS that moves its kind of market (an hour either side of the inflation
  report, the Fed's minutes and decision, the jobs report and the end of the government's funding);
- headline_filter: nothing is added in markets whose value moves with every poll, call or headline:
  every market in Kalshi's Elections category (uncalled races, primaries, nominations) and Politics
  series about approval ratings, impeachment or officials leaving (HEADLINE_WORDS in the series title).
A fourth, no_close_rule, is the main desk without the close rule: the rule could not act on the recording
before 2026-11-07, and with Kalshi's close times filled in afterwards it cost about $12 on E's first 90
hours, in the two markets it quoted into their last hours (the approval brackets and Trump's endorsements).

Each market's kind comes from Kalshi's category for its series: the recorder's series_meta records (from
2026-11-07), else KNOWN_SERIES (looked up that day for the series E had quoted), else PREFIX_GROUPS. The
report splits its money by kind: sports, political, economic, crypto and other.

Equity is the paper bankroll plus the rewards payable plus the fills marked: holdings are valued at their
side's mid on the latest book (a YES and a NO in the same market pair off at $1), or at the result where
the market has settled. The capital tied up is the resting orders' collateral plus the holdings' value.

    python -m lab.strategies.e_desk --lab lab/data [--since-ms MS] [--until-ms MS] [--variants] [--out FILE]

The command line stops at the end of the week from --since-ms unless --until-ms says otherwise, so the
desk's numbers hold still once its week is over.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from lab.fills import EPS, apply_trade, place, side_mid
from lab.recorder import _ts
from lab.replay import live_records, settled_outcomes
from lab.store import read_lab
from lab.strategies.e_incentive import INVENTORY_CAP_FRACTION, MAX_GAP_S, MIN_PAYOUT_USD, QUOTE_FRACTION, _per_side_per_s, reference_price, side_share

START_MS = 1_794_459_600_000  # 2026-11-12T05:00:00Z, after desk v2's week (it ends 04:20Z) and its final report
WEEK_MS = 7 * 86_400_000
RULES = {
    "bankroll_usd": 10_000.0,
    "market_cap_usd": 250.0,
    "capital_cap_usd": 5_000.0,
    "news_move": None,  # off in the main desk; the news_pause variant turns it on at 0.05
    "news_window_s": 120,
    "news_pause_s": 900,
    "loss_stop_usd": 40.0,
    "close_buffer_s": 10_800,
    "min_quote": 1.0,  # contracts: a smaller quote is not placed
    "blackout": False,  # off in the main desk; the calendar_blackout variant turns it on
    "blackout_before_s": 3_600,
    "blackout_after_s": 3_600,
    "skip_headlines": False,  # off in the main desk; the headline_filter variant turns it on
}
SNAPSHOT_MS = 600_000
# rule sets reported beside the main desk on the same recording, registered with it before the start
VARIANTS = {"news_pause": {"news_move": 0.05}, "calendar_blackout": {"blackout": True}, "headline_filter": {"skip_headlines": True},
            "no_close_rule": {"close_buffer_s": 0}}

# the report's kinds of market, from Kalshi's category for the series
GROUPS = ("sports", "political", "economic", "crypto", "other")
CATEGORY_GROUPS = {"Sports": "sports", "Politics": "political", "Elections": "political", "World": "political",
                   "Economics": "economic", "Financials": "economic", "Companies": "economic", "Crypto": "crypto"}
# Kalshi's category and title for the series E quoted before the recorder kept them (looked up 2026-11-07)
KNOWN_SERIES = {
    "KXACTBLUETOP": ("Politics", "Top ActBlue fundraiser?"),
    "KXAPRPOTUS": ("Politics", "President RCP approval rating this week"),
    "KXEOWEEK": ("Politics", "EO this week?"),
    "KXGENERALCOUNTY": ("Elections", "General election county winners"),
    "KXHORMUZMAX": ("Politics", "Maximum traffic through the Strait of Hormuz?"),
    "KXONIONACT": ("Politics", "Onion Futures Act repeal"),
    "KXRAINDPARIS": ("Climate and Weather", "Daily Rain - Paris"),
    "KXRT": ("Entertainment", "Rotten Tomatoes Scores"),
    "KXSENATESEATSD": ("Elections", "Democratic Senate seat count"),
    "KXSTATELEG": ("Elections", "State legislature winners"),
    "KXTRUMPACT": ("Politics", "Will Trump do anything today?"),
    "KXTRUMPENDORSEMENTS": ("Politics", "How many people will Trump endorse this week?"),
}
PREFIX_GROUPS = (("KXBTC", "crypto"), ("KXETH", "crypto"), ("KXSOL", "crypto"), ("KXXRP", "crypto"), ("KXDOGE", "crypto"), ("KXMVE", "sports"))
# headline_filter: whole categories, and Politics series titled like these
HEADLINE_CATEGORIES = ("Elections",)
HEADLINE_WORDS = re.compile(r"approval|favorab|impeach|convict|resign|fired|depart|cabinet|\bout as\b|\bleaves?\b|leaving", re.I)
# calendar_blackout: dated catalysts (UTC) and the kinds of market each moves; from the research report
CATALYSTS = (
    ("2026-11-10T13:30:00Z", "October inflation report (8:30 AM ET)", ("economic", "crypto")),
    ("2026-11-18T19:00:00Z", "Fed minutes (2 PM ET)", ("economic", "crypto")),
    ("2026-12-04T13:30:00Z", "November jobs report (8:30 AM ET)", ("economic", "crypto")),
    ("2026-12-09T19:00:00Z", "Fed decision (2 PM ET)", ("economic", "crypto")),
    ("2026-12-12T05:00:00Z", "government funding runs out (midnight ET, Dec 11)", ("political", "economic")),
)


def series_of(ticker: str) -> str:
    return ticker.split("-")[0]


def describe(series: str, recorded: dict[str, dict] | None = None) -> tuple[str | None, str | None]:
    """(Kalshi's category, the series title): the recorder's series_meta record, else KNOWN_SERIES."""
    r = (recorded or {}).get(series)
    if r is not None:
        return r.get("category"), r.get("title")
    return KNOWN_SERIES.get(series, (None, None))


def group_of(category: str | None, series: str) -> str:
    if category in CATEGORY_GROUPS:
        return CATEGORY_GROUPS[category]
    if category is None:
        for prefix, group in PREFIX_GROUPS:
            if series.startswith(prefix):
                return group
    return "other"


def is_headline(category: str | None, title: str | None) -> bool:
    return category in HEADLINE_CATEGORIES or (category == "Politics" and bool(HEADLINE_WORDS.search(title or "")))


def blackout_at(ts: int, group: str, rule: dict) -> int | None:
    """The index of the catalyst whose blackout covers `ts` for a market of `group`, or None."""
    for i, (when, _, groups) in enumerate(CATALYSTS):
        at = _ts(when)
        if group in groups and at - rule["blackout_before_s"] * 1000 <= ts < at + rule["blackout_after_s"] * 1000:
            return i
    return None


class Holding:
    """One market's contracts and what they cost."""

    __slots__ = ("yes", "yes_cost", "no", "no_cost", "contracts", "fills")

    def __init__(self) -> None:
        self.yes = self.yes_cost = self.no = self.no_cost = self.contracts = 0.0
        self.fills = 0

    @property
    def net(self) -> float:
        return self.yes - self.no

    @property
    def cost(self) -> float:
        return self.yes_cost + self.no_cost

    def value(self, yes_mid: float | None, payout: float | None = None) -> float:
        if payout is not None:
            return self.yes * payout + self.no * (1.0 - payout)
        pairs = min(self.yes, self.no)
        rest_yes, rest_no = self.yes - pairs, self.no - pairs
        if yes_mid is None:  # no quote seen yet: count what is unpaired at cost
            return pairs + (self.yes_cost * rest_yes / self.yes if self.yes else 0.0) + (self.no_cost * rest_no / self.no if self.no else 0.0)
        return pairs + rest_yes * yes_mid + rest_no * (1.0 - yes_mid)


def _yes_mid(book: dict) -> float | None:
    return side_mid(book, "yes")


def evaluate(lab_dir: str | Path, *, since_ms: int = START_MS, until_ms: int | None = None, rules: dict | None = None) -> dict:
    rule = {**RULES, **(rules or {})}
    programs: dict[str, list[dict]] = {}
    prog_market: dict[str, str] = {}
    live: dict[str, dict] = defaultdict(dict)          # ticker -> side -> resting order
    held: dict[str, Holding] = defaultdict(Holding)
    standing: dict[str, tuple[int, dict[str, float]]] = {}
    earned: dict[str, float] = defaultdict(float)      # program id -> USD
    last_mid: dict[str, float] = {}
    recent: dict[str, deque] = defaultdict(deque)       # ticker -> (ts, YES mid) within the news window
    paused_until: dict[str, int] = {}
    stopped: dict[str, int] = {}
    quoted: set[str] = set()
    capped: set[str] = set()                            # markets where the new caps cut a quote
    events: list[dict] = []
    counts = {"news_pauses": 0, "loss_stops": 0, "capped_quotes": 0}
    # series details recorded before the start count from the start: a series looked up on day 1 keeps them
    recorded = {r["series"]: r for r in read_lab(lab_dir, until_ms=since_ms, kinds=("series_meta",)) if r.get("series")}
    kinds: dict[str, tuple[str, bool]] = {}             # series -> (group, headline), until a newer record
    blacked: set[tuple[str, int]] = set()               # (market, catalyst) where the blackout held it
    headlined: set[str] = set()                         # markets the headline filter kept from adding

    def kind(t: str) -> tuple[str, bool]:
        series = series_of(t)
        if series not in kinds:
            category, title = describe(series, recorded)
            kinds[series] = (group_of(category, series), is_headline(category, title))
        return kinds[series]
    equity: list[list] = []
    next_snap = None
    capital_sum = capital_peak = 0.0
    capital_n = 0
    first_ts = last_ts = None

    def payable() -> float:
        return sum(math.floor(v * 100) / 100 for v in earned.values() if v >= MIN_PAYOUT_USD)

    def marked() -> float:
        return sum(h.value(last_mid.get(t)) - h.cost for t, h in held.items())

    def capital() -> float:
        resting = sum(o.price * o.remaining for side in live.values() for o in side.values() if o.remaining > 0)
        return resting + sum(h.value(last_mid.get(t)) for t, h in held.items())

    for r in live_records(lab_dir, since_ms=since_ms, kinds=("book", "trade", "incentives", "series_meta")):
        ts = r["ts"]
        if until_ms is not None and ts >= until_ms:
            break
        first_ts = ts if first_ts is None else first_ts
        last_ts = ts
        if next_snap is None:
            next_snap = ts
        while ts >= next_snap:  # one equity point every SNAPSHOT_MS of recording
            equity.append([next_snap, round(rule["bankroll_usd"] + payable() + marked(), 2)])
            next_snap += SNAPSHOT_MS
        if r["kind"] == "series_meta":
            if r.get("series"):
                recorded[r["series"]] = r
                kinds.pop(r["series"], None)
            continue
        if r["kind"] == "incentives":
            programs = defaultdict(list)
            for p in r.get("programs") or []:
                if p.get("incentive_type") == "liquidity" and p.get("target_size_fp") and _per_side_per_s(p) > 0:
                    programs[p["market_ticker"]].append(p)
                    prog_market[p["id"]] = p["market_ticker"]
            continue
        if r["kind"] == "trade":
            for side, o in live.get(r["ticker"], {}).items():
                q = apply_trade(o, {**r, "ts": r.get("trade_ts") or ts})
                if q:
                    h = held[r["ticker"]]
                    if side == "yes":
                        h.yes += q
                        h.yes_cost += q * o.price
                    else:
                        h.no += q
                        h.no_cost += q * o.price
                    h.contracts += q
                    h.fills += 1
            continue
        if r["kind"] != "book":
            continue
        t = r["ticker"]
        mid = _yes_mid(r)
        if mid is not None:
            last_mid[t] = mid  # every set's books mark the holdings: a market E has left may still be recorded for F
        if "E" not in (r.get("sets") or [r.get("set")]):
            continue
        if mid is not None and rule["news_move"] is not None:
            window = recent[t]
            window.append((ts, mid))
            while window and ts - window[0][0] > rule["news_window_s"] * 1000:
                window.popleft()
            if max(abs(mid - m) for _, m in window) >= rule["news_move"] - EPS:
                if paused_until.get(t, 0) <= ts:
                    counts["news_pauses"] += 1
                    events.append({"ts": ts, "ticker": t, "kind": "news_pause", "yes_mid": round(mid, 4)})
                paused_until[t] = max(paused_until.get(t, 0), ts + rule["news_pause_s"] * 1000)  # news still moving: the pause runs on
        if t in standing:  # the previous book, and the desk's orders against it, stood until now
            since, rates = standing.pop(t)
            dt = min(MAX_GAP_S, (ts - since) / 1000.0)
            for pid, rate in rates.items():
                earned[pid] += rate * dt
        h = held.get(t)
        if h is not None and t not in stopped and h.value(last_mid.get(t)) - h.cost <= -rule["loss_stop_usd"]:
            stopped[t] = ts
            counts["loss_stops"] += 1
            events.append({"ts": ts, "ticker": t, "kind": "loss_stop", "pnl_usd": round(h.value(last_mid.get(t)) - h.cost, 2)})
        active = [p for p in programs.get(t, []) if (_ts(p.get("start_date")) or 0) <= ts < (_ts(p.get("end_date")) or 0)]
        if not active:
            live.pop(t, None)
        else:
            target = float(max(active, key=_per_side_per_s)["target_size_fp"])
            net = held[t].net if t in held else 0.0
            close_ms = r.get("close_ms")
            closing = isinstance(close_ms, (int, float)) and close_ms - ts <= rule["close_buffer_s"] * 1000
            group, headline = kind(t)
            held_off = None
            if rule["blackout"]:
                held_off = blackout_at(ts, group, rule)
                if held_off is not None and (t, held_off) not in blacked:
                    blacked.add((t, held_off))
                    events.append({"ts": ts, "ticker": t, "kind": "blackout", "catalyst": CATALYSTS[held_off][1]})
            skip = rule["skip_headlines"] and headline
            if skip and t not in headlined:
                headlined.add(t)
                events.append({"ts": ts, "ticker": t, "kind": "headline_filter"})
            # the rules stop the desk adding risk; they never stop it pairing off what it holds
            can_add = t not in stopped and paused_until.get(t, 0) <= ts and not closing and held_off is None and not skip
            mine: dict[str, tuple[float, float]] = {}
            for side in ("yes", "no"):
                ref = reference_price(r.get(side) or [], target / 5)
                if ref is None:
                    live[t].pop(side, None)
                    continue
                toward = net if side == "yes" else -net  # held in this side's direction (negative: on the other side)
                pair_off = max(0.0, -toward)
                room = INVENTORY_CAP_FRACTION * target - max(0.0, toward)  # E's own cap, in contracts
                want = QUOTE_FRACTION * target
                add = 0.0
                if can_add:
                    side_value = mid if side == "yes" else (None if mid is None else 1.0 - mid)
                    exposure = max(0.0, toward) * (side_value if side_value is not None else ref)
                    cap_room = max(0.0, rule["market_cap_usd"] - exposure) / max(ref, 0.01)
                    old = live[t].get(side)
                    spare = rule["capital_cap_usd"] - (capital() - (old.price * old.remaining if old is not None else 0.0))
                    cash_room = max(0.0, spare) / max(ref, 0.01)
                    add = max(0.0, min(room, cap_room, cash_room))
                    if min(want, pair_off + add) < min(want, pair_off + max(0.0, room)) - EPS:  # the new caps cut this quote
                        counts["capped_quotes"] += 1
                        capped.add(t)
                size = min(want, pair_off + add)
                old = live[t].get(side)
                if size < rule["min_quote"]:
                    live[t].pop(side, None)
                    continue
                if old is None or abs(old.price - ref) > EPS or old.remaining <= 0 or old.remaining > size + 1.0:
                    old = place(t, side, ref, size, ts, r)
                    live[t][side] = old
                    quoted.add(t)
                mine[side] = (old.price, old.remaining)
            rates = {}
            for p in active:
                discount = (p.get("discount_factor_bps") or 10_000) / 10_000
                shares = [side_share(r.get(side) or [], float(p["target_size_fp"]), discount, mine.get(side)) for side in ("yes", "no")]
                if None not in shares and mine:
                    rates[p["id"]] = _per_side_per_s(p) * sum(shares)
            standing[t] = (ts, rates)
        cap_now = capital()
        capital_sum, capital_n, capital_peak = capital_sum + cap_now, capital_n + 1, max(capital_peak, cap_now)

    settled = settled_outcomes(lab_dir, until_ms=until_ms) if held else {}
    markets = []
    value = cost = 0.0
    reward_by_market: dict[str, float] = defaultdict(float)
    for pid, v in earned.items():
        reward_by_market[prog_market.get(pid, pid)] += v
    for t in sorted(set(held) | set(reward_by_market) | quoted):
        h = held.get(t) or Holding()
        payout = settled.get(t, (None, None))[0]
        v = h.value(last_mid.get(t), payout)
        value, cost = value + v, cost + h.cost
        status = ("settled" if payout is not None else "stopped" if t in stopped else
                  "paused" if paused_until.get(t, 0) > (last_ts or 0) else "quoting" if t in live and live[t] else "idle")
        category = describe(series_of(t), recorded)[0]
        markets.append({"ticker": t, "group": kind(t)[0], "category": category, "reward_usd": round(reward_by_market.get(t, 0.0), 2),
                        "contracts": round(h.contracts, 1), "fills": h.fills, "net_yes": round(h.net, 1), "cost_usd": round(h.cost, 2),
                        "value_usd": round(v, 2), "pnl_usd": round(v - h.cost, 2), "status": status})
    pay = payable()
    categories = split_by_group(markets, earned, prog_market, kind)
    summary = {
        "started": first_ts is not None, "start_ms": since_ms, "end_ms": last_ts,
        "hours": round((last_ts - first_ts) / 3.6e6, 1) if first_ts is not None else 0.0,
        "markets_quoted": len(quoted), "programs_paying": sum(1 for v in earned.values() if v > 0),
        "reward_usd": round(sum(earned.values()), 2), "payable_usd": round(pay, 2),
        "fills": sum(h.fills for h in held.values()), "contracts_filled": round(sum(h.contracts for h in held.values()), 1),
        "cost_usd": round(cost, 2), "value_usd": round(value, 2), "fills_marked_usd": round(value - cost, 2),
        "net_usd": round(pay + value - cost, 2), "equity_usd": round(rule["bankroll_usd"] + pay + value - cost, 2),
        "bankroll_usd": rule["bankroll_usd"], "capital_now_usd": round(capital(), 2),
        "capital_avg_usd": round(capital_sum / capital_n, 2) if capital_n else 0.0, "capital_peak_usd": round(capital_peak, 2),
        "held_markets": sum(1 for h in held.values() if abs(h.yes - h.no) > 0.5), **counts, "capped_markets": len(capped),
        "stopped_markets": sorted(stopped), "maker_fees_usd": 0.0,
        "blackout_markets": len({t for t, _ in blacked}), "headline_markets": len(headlined),
    }
    if last_ts is not None:
        equity.append([last_ts, summary["equity_usd"]])
    return {"rules": rule, "summary": summary, "markets": markets, "categories": categories, "equity": equity, "events": events}


def split_by_group(markets: list[dict], earned: dict[str, float], prog_market: dict[str, str], kind) -> list[dict]:
    """The money by kind of market: payments (each program's total, paid only from $1), fills and their value."""
    rows = {g: {"group": g, "markets": 0, "reward_usd": 0.0, "payable_usd": 0.0, "contracts": 0.0, "fills": 0, "cost_usd": 0.0, "value_usd": 0.0}
            for g in GROUPS}
    for m in markets:
        row = rows[m["group"]]
        row["markets"] += 1
        for k_out, k_in in (("reward_usd", "reward_usd"), ("contracts", "contracts"), ("fills", "fills"), ("cost_usd", "cost_usd"), ("value_usd", "value_usd")):
            row[k_out] += m[k_in]
    for pid, v in earned.items():
        if v >= MIN_PAYOUT_USD:
            rows[kind(prog_market.get(pid, pid))[0]]["payable_usd"] += math.floor(v * 100) / 100
    out = []
    for g in GROUPS:
        row = rows[g]
        if not row["markets"]:
            continue
        marked = row["value_usd"] - row["cost_usd"]
        out.append({**{k: round(v, 2) if isinstance(v, float) else v for k, v in row.items()},
                    "fills_marked_usd": round(marked, 2), "net_usd": round(row["payable_usd"] + marked, 2)})
    return out


def compare(lab_dir: str | Path, *, since_ms: int = START_MS, until_ms: int | None = None, workers: int | None = None) -> dict:
    """The main desk's full report, plus each variant's summary on the same recording, replayed side by side
    (a week's replay takes about a minute each)."""
    jobs = {"": None, **VARIANTS}
    workers = workers or min(len(jobs), os.cpu_count() or 1)
    if workers > 1:
        with ProcessPoolExecutor(workers) as pool:
            futures = {name: pool.submit(evaluate, lab_dir, since_ms=since_ms, until_ms=until_ms, rules=rules) for name, rules in jobs.items()}
            done = {name: f.result() for name, f in futures.items()}
    else:
        done = {name: evaluate(lab_dir, since_ms=since_ms, until_ms=until_ms, rules=rules) for name, rules in jobs.items()}
    main = done.pop("")
    main["variants"] = {name: r["summary"] for name, r in done.items()}
    return main


def one_line(s: dict) -> str:
    if not s["started"]:
        return f"E desk: starts {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime(s['start_ms'] / 1000))}; nothing recorded since"
    extra = "".join(f", {s[k]} {label}" for k, label in (("blackout_markets", "markets held off by the calendar"),
                                                          ("headline_markets", "markets kept out by the headline filter")) if s.get(k))
    return (f"E desk: net {s['net_usd']:+.2f} USD over {s['hours']:.1f} h (payments {s['payable_usd']:.2f}, fills marked {s['fills_marked_usd']:+.2f}); "
            f"{s['markets_quoted']} markets quoted, {s['contracts_filled']:.0f} contracts filled, {s['held_markets']} held; "
            f"{s['capital_avg_usd']:,.0f} USD tied up on average ({s['capital_peak_usd']:,.0f} at most); "
            f"{s['news_pauses']} news pauses, {s['loss_stops']} loss stops, caps cut quotes in {s['capped_markets']} markets{extra}")


def category_lines(categories: list[dict]) -> list[str]:
    return [f"  {c['group']}: net {c['net_usd']:+.2f} (payments {c['payable_usd']:.2f}, fills marked {c['fills_marked_usd']:+.2f}) "
            f"in {c['markets']} markets, {c['contracts']:.0f} contracts" for c in categories]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The E desk: strategy E with the next round's risk rules, from its start")
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--since-ms", type=int, default=START_MS)
    parser.add_argument("--until-ms", type=int, default=None, help="where the replay stops (default: a week after --since-ms)")
    parser.add_argument("--out", default=None)
    parser.add_argument("--variants", action="store_true", help="also replay each variant (VARIANTS) on the same recording")
    args = parser.parse_args(argv)
    until = args.until_ms if args.until_ms is not None else args.since_ms + WEEK_MS
    report = compare(args.lab, since_ms=args.since_ms, until_ms=until) if args.variants else evaluate(args.lab, since_ms=args.since_ms, until_ms=until)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=1))
    print(one_line(report["summary"]))
    for line in category_lines(report.get("categories") or []):
        print(line)
    for name, v in (report.get("variants") or {}).items():
        print(f"  variant {name}: " + one_line(v).removeprefix("E desk: "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
