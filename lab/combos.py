"""Combo backtest: is selling Kalshi's combos (parlays) to the people who request them profitable after the maker fee,
and could a newcomer quoting from the legs' own prices win some of it? Paper only: public data, no orders, no key.

Background (scratchpad audit/new-angles.md, idea 1): combo buyers are said to have lost over $1 billion to the few firms
that answer Kalshi's requests for quote (RFQs). Kalshi charges combo makers half the taker rate since Aug 20, 2026 (its
series fee change for KXMVECROSSCATEGORY to quadratic_with_combo_maker_fees at 09:01Z). Combos are almost all sports
legs, and Arizona's case over Kalshi's sports contracts is open, so this stays on paper.

The rules below were fixed at REGISTERED, before any result was read, and are not tuned on what the test shows. Before
that, to check the data could be read: one hour's trade prints on Oct 19 and Sep 1 were listed and their combos' records
read for structure only (legs, games, price grid, settlement fields); no combo's result, payout or price against its
legs was looked at. A research note had earlier sampled 96 combos' prices against their legs on Nov 12 (outside the
test days) and reported the hold by leg count; no settlement was used there. After the rules were fixed, a smoke test
fetched Sep 20 (a training day for stage 2) and printed only counts.

Amended at AMENDED after a review, before any result was read:
- A leg's game is its event ticker without the series prefix, so a game's winner, total and props are one game. So are
  the 15-minute crypto and metal windows of different assets for the same quarter-hour, which move together. Of the 267
  combos with 5 or more legs on Sep 20 that the event-ticker rule called cross-game, 60 are not by this one.
- The maker fee follows each combo's series, its event ticker without the last part, from Kalshi's full series list.
  Kalshi lists KXMVECROSSCATEGORY0, a quarter of the Sep 20 prints, as charging makers nothing, and has never changed its
  fee type.
- Stage 2 calibrates only on legs whose markets were scheduled (expected_expiration_time) to settle before SPLIT, as
  the actual settlement time would pick legs by their outcome. It counts every test print it drops.
- A quote is never below the grid's lowest step.
- The fetch re-fetches a leg game whose candles don't cover a later sample, and a record saved before it settled.
- The report says how many combo series it has fees for.

Sample: for each day from DAY_FROM to DAY_TO, WINDOWS seeded random moments; at each, the last page of up to 1,000
public trades before it (within an hour). The combo prints in it (tickers starting KXMVE) are the sample, each with its
combo's record: legs, the payout per YES contract when settled (settlement_value_dollars), and when its last leg was
expected to settle. A combo is kept only if that expected time is before SETTLE_BY, so every kept combo has had time to
settle either way: combos close early when a leg loses, and keeping only the settled ones would favour the seller. A
kept combo that has not settled is counted.

Stage 1, the main test (pass or fail): the seller's side of every print where the taker bought YES on a combo whose legs
are all in different games (cross-game: a leg's game is its event ticker without the series prefix) and number at
least MIN_LEGS. The seller bought NO at 1 - the YES price P on the print's count n: money made n x (P - payout) - fee,
money staked n x (1 - P) + fee. The maker fee is the combo series' rate at the fetch (the series is the combo's event
ticker without its last part) x its multiplier x n x P x (1 - P), rounded up to the cent: MAKER (half the taker rate) under quadratic_with_combo_maker_fees, 0.0175 under
quadratic_with_maker_fees, none under quadratic, and MAKER for a series not listed. It passes if money made over money staked is above zero across a 95% bootstrap over days
(the day is the unit, as prints share legs), above zero in each half of the days (split at the median day), with at
least MIN_DAYS days. Description: every leg-count band, same-game combos, the taker buying NO, and no maker fee.

Stage 2, description only: can a newcomer win part of it? From STAGE2_FROM, in the first STAGE2_WINDOWS windows of each
day, STAGE2_COMBOS seeded random cross-game combos where the taker bought YES (one print per combo). Each leg is priced at
the print from Kalshi's hourly candle of that leg that ended in the hour up to it: the mid, if the bid is at least 1 cent,
the ask at most 99 cents and the spread at most LEG_SPREAD; a combo with any leg unpriced is left out and counted. The
mid is calibrated by a logistic fit of the legs' results on their logit mids, fitted on prints before SPLIT and only on
legs scheduled to settle before it. The
combo's fair YES price is the product of its calibrated legs. A quote at fair x (1 + MARGIN), rounded up to Kalshi's
price grid, wins the print if it is below the price paid, and then sells YES at the quote on the print's count, with
the maker fee. Reported on the days from SPLIT: fills, money made over money staked with a 95% bootstrap over days and
its halves, and how the raw and calibrated fair prices compare with what was paid and with how often combos came in.
It is description, as a few hundred fills can't settle a margin of a few percent, and paper can't see the competing
quotes, the 3-second confirmation, or the requests that never traded.

    python -m lab.combos fetch --data <dir>      (resumable; Kalshi's public API, gently)
    python -m lab.combos report --data <dir> [--out results.json]
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from lab.longshot import Fetcher, _num, _ts, _write
from lab.weather import quote

REGISTERED = "2026-11-12T19:59:00Z"
AMENDED = "2026-11-12T20:41:00Z"
DAY_FROM, DAY_TO = date(2026, 8, 21), date(2026, 11, 10)
STAGE2_FROM, SPLIT = date(2026, 9, 13), date(2026, 10, 1)
SETTLE_BY = "2026-11-11T12:00:00Z"
WINDOWS = 4
STAGE2_WINDOWS = 2
STAGE2_COMBOS = 12
MIN_LEGS = 5
MIN_DAYS = 40
MAKER = 0.035
RATES = {"quadratic_with_combo_maker_fees": MAKER, "quadratic_with_maker_fees": 0.0175, "quadratic": 0.0}
LEG_SPREAD = 0.10
MARGIN = 0.10
BATCH = 50
BOOTSTRAP = 2_000
SEED = 20261112
DAY_S, HOUR_S = 86_400, 3_600
BANDS = ((2, 4), (5, 7), (8, 12), (13, 999))


def maker_fee(price: float, n: float, coeff: float = MAKER) -> float:
    """Kalshi's maker fee on one fill of n contracts at price, rounded up to the cent."""
    if coeff <= 0 or n <= 0:
        return 0.0
    return math.ceil(round(coeff * n * price * (1 - price) * 100, 6)) / 100


def series_of(combo: dict) -> str:
    """A combo's series: its event ticker without the last part (KXMVECROSSCATEGORY0-SHARD1-S2026... is
    KXMVECROSSCATEGORY0-SHARD1); its ticker's first part if it has no event ticker."""
    ev = combo.get("event_ticker") or ""
    return "-".join(ev.split("-")[:-1]) if "-" in ev else str(combo.get("ticker", "")).split("-")[0]


def maker_rate(series_ticker: str, series: dict[str, dict]) -> float:
    """The maker fee rate of a combo series at the fetch; MAKER if the series isn't listed."""
    s = series.get(series_ticker)
    if not s:
        return MAKER
    mult = _num(s.get("fee_multiplier"))
    return RATES.get(s.get("fee_type"), MAKER) * (1.0 if mult is None else mult)


def band(legs: int) -> str:
    for lo, hi in BANDS:
        if lo <= legs <= hi:
            return f"{lo}-{hi}" if hi < 999 else f"{lo}+"
    return "1"


def grid_up(p: float) -> float:
    """Up to Kalshi's combo price grid: 0.01 cent below 1 cent, 0.1 cent from 1 to 99 cents."""
    step = 0.0001 if p < 0.01 else 0.001
    return max(0.0001, round(math.ceil(round(p / step, 6)) * step, 4))


def windows_of(day: date) -> list[int]:
    rng = random.Random(f"{SEED}:{day.isoformat()}")
    start = int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())
    return sorted(start + int(rng.uniform(0, DAY_S)) for _ in range(WINDOWS))


def days() -> list[date]:
    return [DAY_FROM + timedelta(days=i) for i in range((DAY_TO - DAY_FROM).days + 1)]


def game(event_ticker: str) -> str:
    """A leg's game: its event ticker without the series prefix (KXNFLGAME-26SEP20INDKC and KXNFLTOTAL-26SEP20INDKC are
    one game)."""
    e = event_ticker or ""
    return e.split("-", 1)[1] if "-" in e else e


def cross_game(combo: dict) -> bool:
    legs = combo.get("mve_selected_legs") or []
    return bool(legs) and len({game(leg.get("event_ticker") or "") for leg in legs}) == len(legs)


def kept(combo: dict) -> bool:
    exp = combo.get("expected_expiration_time")
    return bool(exp) and _ts(exp) < _ts(SETTLE_BY)


def payout(combo: dict) -> float | None:
    if combo.get("status") not in ("finalized", "settled"):
        return None
    v = _num(combo.get("settlement_value_dollars"))
    return v if v is not None and 0 <= v <= 1 else None


# ---- stage 1 ----------------------------------------------------------------------------------------------------

def seller_rows(windows: list[dict], combos: dict[str, dict], series: dict[str, dict], fees: bool = True) -> tuple[list[dict], dict]:
    """One row per combo print: {day, legs, cross, taker, pnl, stake}; and counts of what was left out."""
    rows, left = [], {"no_record": 0, "settles_late": 0, "unsettled": 0, "bad_price": 0}
    for w in windows:
        for t in w["trades"]:
            c = combos.get(t["ticker"])
            if c is None:
                left["no_record"] += 1
                continue
            if not kept(c):
                left["settles_late"] += 1
                continue
            pay = payout(c)
            if pay is None:
                left["unsettled"] += 1
                continue
            price, n = _num(t.get("yes_price_dollars")), _num(t.get("count_fp"))
            if price is None or n is None or not (0 < price < 1) or n <= 0:
                left["bad_price"] += 1
                continue
            legs = len(c.get("mve_selected_legs") or [])
            f = maker_fee(price, n, maker_rate(series_of(c), series)) if fees else 0.0
            if t.get("taker_side") == "yes":  # the seller holds NO bought at 1 - price
                pnl, stake = n * (price - pay) - f, n * (1 - price) + f
            else:  # the taker bought NO, so the seller holds YES at price
                pnl, stake = n * (pay - price) - f, n * price + f
            rows.append({"day": w["day"], "legs": legs, "cross": cross_game(c), "taker": t.get("taker_side"), "pnl": pnl, "stake": stake,
                         "price": price, "n": n, "payout": pay})
    return rows, left


def summarize(rows: list[dict], rng: random.Random | None = None, draws: int = BOOTSTRAP) -> dict:
    stake, pnl = sum(r["stake"] for r in rows), sum(r["pnl"] for r in rows)
    out = {"prints": len(rows), "days": len({r["day"] for r in rows}), "stake_usd": round(stake, 2), "pnl_usd": round(pnl, 2),
           "return": round(pnl / stake, 5) if stake else None}
    by_day: dict[str, list[float]] = {}
    for r in rows:
        d = by_day.setdefault(r["day"], [0.0, 0.0])
        d[0] += r["pnl"]
        d[1] += r["stake"]
    if rng is not None and len(by_day) >= 2 and draws:
        cells = list(by_day.values())
        rs = []
        for _ in range(draws):
            pick = [cells[rng.randrange(len(cells))] for _ in cells]
            st = sum(c[1] for c in pick)
            rs.append(sum(c[0] for c in pick) / st if st else 0.0)
        rs.sort()
        out["ci95"] = [round(rs[int(0.025 * draws)], 5), round(rs[int(0.975 * draws) - 1], 5)]
    return out


def halves(rows: list[dict]) -> list[dict]:
    ds = sorted({r["day"] for r in rows})
    if not ds:
        return [summarize([]), summarize([])]
    mid = ds[len(ds) // 2]
    return [summarize([r for r in rows if r["day"] < mid]), summarize([r for r in rows if r["day"] >= mid])]


def passed(r: dict) -> bool:
    return bool(r.get("ci95") and r["ci95"][0] > 0 and r["days"] >= MIN_DAYS and all((h.get("return") or 0) > 0 for h in r["halves"]))


# ---- stage 2 ----------------------------------------------------------------------------------------------------

def stage2_sample(windows: list[dict], combos: dict[str, dict]) -> list[tuple[dict, dict]]:
    """(print, combo) pairs: in the first STAGE2_WINDOWS windows of each day from STAGE2_FROM, STAGE2_COMBOS seeded random
    cross-game combos kept for the test whose print had the taker buying YES, one print per combo."""
    out = []
    for w in windows:
        if date.fromisoformat(w["day"]) < STAGE2_FROM or w["index"] >= STAGE2_WINDOWS:
            continue
        seen, pool = set(), []
        for t in sorted(w["trades"], key=lambda t: (t.get("created_time", ""), t.get("trade_id", ""))):
            c = combos.get(t["ticker"])
            if c is None or t["ticker"] in seen or t.get("taker_side") != "yes" or not cross_game(c) or not kept(c):
                continue
            seen.add(t["ticker"])
            pool.append((t, c))
        rng = random.Random(f"{SEED}:s2:{w['day']}:{w['index']}")
        out += rng.sample(pool, min(STAGE2_COMBOS, len(pool)))
    return out


def leg_mid(candles: list[dict], t: int) -> float | None:
    bid, ask = quote(candles, t)
    if bid is None or ask is None or bid < 0.01 - 1e-9 or ask > 0.99 + 1e-9 or ask < bid or ask - bid > LEG_SPREAD + 1e-9:
        return None
    return (bid + ask) / 2


def _logit(p: float) -> float:
    p = min(max(p, 0.01), 0.99)
    return math.log(p / (1 - p))


def _sig(x: float) -> float:
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


def fit_calibration(points: list[tuple[float, float]], iters: int = 50) -> tuple[float, float]:
    """(a, b) of P(yes) = sigmoid(a + b logit(mid)), by Newton's method; (0, 1), the raw mid, if it can't be fitted."""
    if len(points) < 20 or len({y for _, y in points}) < 2:
        return 0.0, 1.0
    a, b = 0.0, 1.0
    for _ in range(iters):
        ga = gb = haa = hab = hbb = 0.0
        for m, y in points:
            x = _logit(m)
            p = _sig(a + b * x)
            w = p * (1 - p)
            ga += y - p
            gb += (y - p) * x
            haa += w
            hab += w * x
            hbb += w * x * x
        det = haa * hbb - hab * hab
        if det <= 1e-12:
            return 0.0, 1.0
        da, db = (hbb * ga - hab * gb) / det, (haa * gb - hab * ga) / det
        a, b = a + da, b + db
        if abs(da) < 1e-9 and abs(db) < 1e-9:
            break
    return (a, b) if math.isfinite(a) and math.isfinite(b) else (0.0, 1.0)


def leg_prices(t: dict, c: dict, legs: dict[str, list[dict]]) -> list[tuple[str, float]] | None:
    """[(side, mid)] for every leg at the print, or None if any leg can't be priced."""
    ts = _ts(t["created_time"])
    out = []
    for leg in c.get("mve_selected_legs") or []:
        m = leg_mid(legs.get(leg.get("market_ticker")) or [], ts)
        if m is None or leg.get("side") not in ("yes", "no"):
            return None
        out.append((leg["side"], m))
    return out or None


def stage2(sample: list[tuple[dict, dict]], legs: dict[str, list[dict]], leg_results: dict[str, float], leg_due: dict[str, int],
           series: dict[str, dict], rng: random.Random) -> dict:
    priced, unpriced = [], 0
    for t, c in sample:
        lp = leg_prices(t, c, legs)
        if lp is None:
            unpriced += 1
            continue
        priced.append((t, c, lp))
    points = []
    seen = set()
    split_ts = int(datetime(SPLIT.year, SPLIT.month, SPLIT.day, tzinfo=UTC).timestamp())
    for t, c, lp in priced:
        if date.fromisoformat(t["created_time"][:10]) >= SPLIT:
            continue
        hour = _ts(t["created_time"]) // HOUR_S
        for leg, (_, mid) in zip(c["mve_selected_legs"], lp, strict=True):
            y = leg_results.get(leg["market_ticker"])
            key = (leg["market_ticker"], hour)
            due = leg_due.get(leg["market_ticker"])
            if y in (0.0, 1.0) and key not in seen and due is not None and due < split_ts:  # scheduled before the test period
                seen.add(key)
                points.append((mid, y))
    a, b = fit_calibration(points)
    fills, check, dropped = [], {}, 0
    for t, c, lp in priced:
        day = t["created_time"][:10]
        if date.fromisoformat(day) < SPLIT:
            continue
        pay = payout(c)
        price, n = _num(t.get("yes_price_dollars")), _num(t.get("count_fp"))
        if pay is None or price is None or n is None or not (0 < price < 1) or n <= 0:
            dropped += 1
            continue
        raw = math.prod(m if s == "yes" else 1 - m for s, m in lp)
        cal = math.prod(_sig(a + b * _logit(m)) if s == "yes" else 1 - _sig(a + b * _logit(m)) for s, m in lp)
        k = check.setdefault(band(len(lp)), {"combos": 0, "paid": 0.0, "raw_fair": 0.0, "calibrated_fair": 0.0, "came_in": 0.0})
        k["combos"] += 1
        k["paid"] += price
        k["raw_fair"] += raw
        k["calibrated_fair"] += cal
        k["came_in"] += pay
        q = grid_up(cal * (1 + MARGIN))
        if q < price - 1e-9 and q < 0.99:
            f = maker_fee(q, n, maker_rate(series_of(c), series))
            fills.append({"day": day, "legs": len(lp), "pnl": n * (q - pay) - f, "stake": n * (1 - q) + f})
    for k in check.values():
        for f in ("paid", "raw_fair", "calibrated_fair", "came_in"):
            k[f] = round(k[f] / k["combos"], 5)
    r = summarize(fills, rng)
    r["halves"] = halves(fills)
    return {"sampled": len(sample), "unpriced": unpriced, "test_prints_unsettled_or_bad": dropped, "calibration": {"a": round(a, 4), "b": round(b, 4), "points": len(points)},
            "quote_rule": r, "by_band": dict(sorted(check.items()))}


# ---- loading and evaluating -------------------------------------------------------------------------------------

def load(data: Path) -> dict:
    windows = [json.loads(p.read_text()) for p in sorted((data / "windows").glob("*.json"))]
    combos = records(data / "combos")
    legs: dict[str, list[dict]] = {}
    for p in sorted((data / "legs").glob("*.json")):
        got = json.loads(p.read_text())
        for tk, cs in (got["markets"] if "markets" in got and "range" in got else got).items():  # the first version had no span
            legs[tk] = [{**c, "end_period_ts": int(c["end_period_ts"])} for c in cs if c.get("end_period_ts") is not None]
    leg_results, leg_due = {}, {}
    for tk, m in records(data / "leg_markets").items():
        v = payout(m)
        if v is not None:
            leg_results[tk] = v
            if m.get("expected_expiration_time"):  # the schedule, not when an early outcome closed it
                leg_due[tk] = _ts(m["expected_expiration_time"])
    series = {s["ticker"]: s for s in json.loads((data / "series.json").read_text())} if (data / "series.json").exists() else {}
    return {"windows": windows, "combos": combos, "legs": legs, "leg_results": leg_results, "leg_due": leg_due, "series": series}


def records(folder: Path) -> dict[str, dict]:
    """Market records by ticker; a settled record wins over one saved before it settled."""
    out: dict[str, dict] = {}
    for p in sorted(folder.glob("*.json")):
        for m in json.loads(p.read_text()):
            if m["ticker"] not in out or (payout(out[m["ticker"]]) is None and payout(m) is not None):
                out[m["ticker"]] = m
    return out


def evaluate(d: dict) -> dict:
    rng = random.Random(SEED)
    rows, left = seller_rows(d["windows"], d["combos"], d["series"])
    out = {"registered": REGISTERED, "amended": AMENDED, "series_with_fees": len(d["series"]), "windows": len(d["windows"]), "combo_prints": sum(len(w["trades"]) for w in d["windows"]),
           "left_out": left, "stage1": {}}
    main = [r for r in rows if r["taker"] == "yes" and r["cross"] and r["legs"] >= MIN_LEGS]
    m = summarize(main, rng)
    m["halves"] = halves(main)
    out["stage1"]["main"] = m
    for lo, hi in BANDS:
        name = band(lo)
        for cross in (True, False):
            g = [r for r in rows if r["taker"] == "yes" and r["cross"] == cross and lo <= r["legs"] <= hi]
            out["stage1"][f"taker_yes/{'cross' if cross else 'same_game'}/{name}"] = {**summarize(g, rng), "halves": [h.get("return") for h in halves(g)]}
    out["stage1"]["taker_no/all"] = summarize([r for r in rows if r["taker"] == "no"], rng)
    no_fee, _ = seller_rows(d["windows"], d["combos"], d["series"], fees=False)
    out["stage1"]["main_without_maker_fee"] = summarize([r for r in no_fee if r["taker"] == "yes" and r["cross"] and r["legs"] >= MIN_LEGS], rng)
    out["main_test"] = {"passed": passed(m), "return": m["return"], "ci95": m.get("ci95"), "halves": [h.get("return") for h in m["halves"]],
                        "days": m["days"], "prints": m["prints"]}
    out["stage2"] = stage2(stage2_sample(d["windows"], d["combos"]), d["legs"], d["leg_results"], d["leg_due"], d["series"], rng)
    return out


# ---- fetching ---------------------------------------------------------------------------------------------------

def fetch(data: Path, rate: float = 0.4) -> None:
    for sub in ("windows", "combos", "legs", "leg_markets"):
        (data / sub).mkdir(parents=True, exist_ok=True)
    with open(data / "fetch.log", "a") as logf:
        _fetch(data, rate, lambda *a: print(datetime.now(UTC).strftime("%H:%M:%SZ"), *a, file=logf, flush=True))


def _batch(f: Fetcher, tickers: list[str], first: str) -> list[dict] | None:
    """Market records for up to BATCH tickers: from `first` ("live" or "historical"), the rest from the other; None if a
    request failed."""
    got: dict[str, dict] = {}
    for src in (first, "historical" if first == "live" else "live"):
        need = [t for t in tickers if t not in got]
        if not need:
            break
        r = f.get("/markets" if src == "live" else "/historical/markets", {"limit": 100, "tickers": ",".join(need)})
        if r is None:
            return None
        got.update({m["ticker"]: m for m in r.get("markets") or []})
    return list(got.values())


def _span(stamps: list[tuple[str, int]]) -> tuple[int, int]:
    ts = [t for _, t in stamps]
    return min(ts) - 2 * HOUR_S, max(ts) + 1


def _read_legs(p: Path) -> dict | None:
    try:
        got = json.loads(p.read_text())
    except (OSError, ValueError):
        return None
    return got if isinstance(got, dict) and "range" in got and "markets" in got else None


def _covers(p: Path, needs: list[tuple[str, int]]) -> bool:
    """Whether a saved leg game has every market and the whole time span the sample needs."""
    got = _read_legs(p)
    if got is None:
        return False
    start, end = _span(needs)
    return got["range"][0] <= start and got["range"][1] >= end and {tk for tk, _ in needs} <= set(got["markets"])


def _fetch(data: Path, rate: float, log) -> None:
    f = Fetcher(rate, log)
    cut = f.get("/historical/cutoff") or {}
    trades_cut = _ts(cut["trades_created_ts"]) if cut.get("trades_created_ts") else None
    settled_cut = _ts(cut["market_settled_ts"]) if cut.get("market_settled_ts") else None
    if trades_cut is None or settled_cut is None:
        log("no historical cutoff; left for the next run")
        return
    if not (data / "series.json").exists():
        got = f.get("/series")  # every category: two combo series are under Mentions
        if got is not None:
            _write(data / "series.json", [x for x in got.get("series") or [] if str(x.get("ticker", "")).startswith("KXMVE")])
    # 1. the windows' combo prints
    for day in days():
        for i, t in enumerate(windows_of(day)):
            p = data / "windows" / f"{day.isoformat()}_{i}.json"
            if p.exists():
                continue
            r = f.get("/markets/trades" if t >= trades_cut else "/historical/trades", {"limit": 1000, "max_ts": t, "min_ts": t - HOUR_S})
            if r is None:
                continue
            ts = r.get("trades") or []
            _write(p, {"day": day.isoformat(), "index": i, "at": t, "prints": len(ts),
                       "span": [ts[-1]["created_time"], ts[0]["created_time"]] if ts else None,
                       "trades": [x for x in ts if str(x.get("ticker", "")).startswith("KXMVE")]})
    log("windows done")
    # 2. the combos' records
    windows = [json.loads(p.read_text()) for p in sorted((data / "windows").glob("*.json"))]
    have = {t for t, m in records(data / "combos").items() if payout(m) is not None or not kept(m)}  # a kept one saved unsettled is asked again
    first_seen: dict[str, int] = {}
    for w in windows:
        for x in w["trades"]:
            first_seen.setdefault(x["ticker"], w["at"])
    need = sorted(t for t in first_seen if t not in have)
    log(f"combos: {len(have)} have, {len(need)} to fetch")
    n_files = len(list((data / "combos").glob("*.json")))
    for i in range(0, len(need), BATCH):
        chunk = need[i:i + BATCH]
        got = _batch(f, chunk, "historical" if min(first_seen[t] for t in chunk) < settled_cut else "live")
        if got is not None:
            _write(data / "combos" / f"{n_files:05d}.json", got)
            n_files += 1
        if (i // BATCH) % 20 == 0:
            log(f"combos {i}/{len(need)}; requests {f.requests}, 429s {f.limited}, failed {f.failed}")
    # 3. stage 2: the sampled combos' legs, priced from hourly candles, and the legs' results
    combos = records(data / "combos")
    sample = stage2_sample(windows, combos)
    events: dict[str, list[tuple[str, int]]] = {}
    for t, c in sample:
        ts = _ts(t["created_time"])
        for leg in c.get("mve_selected_legs") or []:
            events.setdefault(leg["event_ticker"], []).append((leg["market_ticker"], ts))
    todo = [ev for ev in sorted(events) if not _covers(data / "legs" / f"{ev}.json", events[ev])]
    log(f"stage 2: {len(sample)} combos, {len(events)} leg games, {len(todo)} to fetch")
    for j, ev in enumerate(todo):
        start, end = _span(events[ev])
        old = _read_legs(data / "legs" / f"{ev}.json")
        if old is not None:  # a later sample needs more: fetch the whole span again
            start, end = min(start, old["range"][0]), max(end, old["range"][1])
        params = {"start_ts": start, "end_ts": end, "period_interval": 60}
        series = ev.split("-")[0]
        got: dict[str, list] | None = {}
        r = f.get(f"/series/{series}/events/{ev}/candlesticks", params)
        if r is not None and r.get("market_tickers"):
            got = dict(zip(r["market_tickers"], r.get("market_candlesticks") or [], strict=False))
        for tk in sorted({tk for tk, _ in events[ev]} - set(got)):
            r = f.get(f"/series/{series}/markets/{tk}/candlesticks", params) or f.get(f"/historical/markets/{tk}/candlesticks", params)
            if r is None:
                got = None
                break
            got[tk] = r.get("candlesticks") or []
        if got is not None:
            _write(data / "legs" / f"{ev}.json", {"range": [start, end], "markets": got})
        if j % 100 == 0:
            log(f"leg games {j}/{len(todo)}; requests {f.requests}, 429s {f.limited}, failed {f.failed}")
    have = {t for t, m in records(data / "leg_markets").items() if payout(m) is not None}
    need = sorted({tk for ev in events.values() for tk, _ in ev} - have)
    n_files = len(list((data / "leg_markets").glob("*.json")))
    for i in range(0, len(need), BATCH):
        got = _batch(f, need[i:i + BATCH], "live")
        if got is not None:
            _write(data / "leg_markets" / f"{n_files:05d}.json", got)
            n_files += 1
    missing_w = sum(1 for d in days() for i in range(WINDOWS) if not (data / "windows" / f"{d.isoformat()}_{i}.json").exists())
    combos = records(data / "combos")
    missing_c = sum(1 for t in first_seen if t not in combos)
    missing_l = sum(1 for ev in events if not _covers(data / "legs" / f"{ev}.json", events[ev]))
    no_series = "" if (data / "series.json").exists() else ", the series list missing (every maker fee at MAKER)"
    log(f"done: {missing_w} windows, {missing_c} combo records (some may be unlisted), {missing_l} leg games missing{no_series} "
        f"(run again to retry); requests {f.requests}, 429s {f.limited}, failed {f.failed}")


# ---- output -----------------------------------------------------------------------------------------------------

def lines(r: dict) -> list[str]:
    pct = lambda x: "-" if x is None else f"{100 * x:+.2f}%"
    out = [(f"combo backtest (rules registered {r['registered']}, amended {r['amended']}): {r['windows']} windows, {r['combo_prints']} combo prints, "
            f"{r['series_with_fees']} combo series with fees, left out {json.dumps(r['left_out'])}")]
    for k, v in r["stage1"].items():
        ci = v.get("ci95")
        out.append(f"  {k:32} {v['prints']:6d} prints {v['days']:3d} days  seller return {pct(v['return'])}"
                   + (f" (95%: {pct(ci[0])} to {pct(ci[1])})" if ci else ""))
    mt = r["main_test"]
    out.append(f"main test (seller, cross-game, {MIN_LEGS}+ legs): {'PASSED' if mt['passed'] else 'FAILED'}: return {pct(mt['return'])}"
               + (f", 95% {pct(mt['ci95'][0])} to {pct(mt['ci95'][1])}" if mt.get("ci95") else "")
               + f", halves {' / '.join(pct(h) for h in mt['halves'])}, {mt['days']} days, {mt['prints']} prints")
    s2 = r["stage2"]
    q = s2["quote_rule"]
    out.append(f"stage 2 (description): {s2['sampled']} combos sampled, {s2['unpriced']} unpriced, "
               f"{s2['test_prints_unsettled_or_bad']} test prints unsettled or bad, calibration {json.dumps(s2['calibration'])}; "
               f"quote rule {q['prints']} fills, return {pct(q['return'])}" + (f" (95%: {pct(q['ci95'][0])} to {pct(q['ci95'][1])})" if q.get("ci95") else ""))
    for k, v in s2["by_band"].items():
        out.append(f"  {k:6} {json.dumps(v)}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Selling Kalshi's combos: the seller's side by settlement, and a quoting rule")
    parser.add_argument("command", choices=("fetch", "report"))
    parser.add_argument("--data", required=True)
    parser.add_argument("--rate", type=float, default=0.4)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    data = Path(args.data)
    if args.command == "fetch":
        fetch(data, args.rate)
        return 0
    r = evaluate(load(data))
    if args.out:
        Path(args.out).write_text(json.dumps(r, indent=1))
    print("\n".join(lines(r)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
