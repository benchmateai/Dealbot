"""Weather settlement backtest: do Kalshi's daily high-temperature markets price The Weather Company's figure, or the
airport sensor readings most traders watch? Paper only: public data, no orders, no key.

Background (reports/Viable Kalshi trading strategies.md, strategy 6): on Aug 14, 2026 Kalshi moved daily high-temperature
settlement from the National Weather Service's climate report (CLI) to The Weather Company (TWC). If TWC's figure
differs from the sensor readings in a way the prices miss, a taker who models the difference can buy the bracket TWC
settles on for less than it is worth, late in the day when the high is mostly known.

The rules below were fixed at REGISTERED and are not tuned on what the test shows. Before that, to check the data could
be read:
- the settled listings of all 24 series were downloaded and only counted per series (markets, days, the first TWC day,
  the station code);
- in New York, two days' settlements were seen (Nov 10: TWC 62, Nov 11: TWC 63, each the same as the NWS report; Nov 10
  is a test day), with the last hours of Nov 11's prices (after the test days);
- one August hour's prices for one bracket were seen;
- a smoke test, run from 19:13 to 19:15Z, fetched New York's prices for Sep 10-16 (training days), its NWS reports for all
  of 2026 and its sensor readings for Sep 9-18, and printed only counts.
No other price, figure or result was read before the report.

Amended at AMENDED after a review, before the report was run: the coverage rule counts hours with a reading, not
readings (a burst of special reports no longer passes for a day); a city-day whose settlement Kalshi recorded as text
("70 to 71") is kept for betting, as bets settle on Kalshi's results, and left out of the model and the gap counts;
and an empty weather download is neither saved nor counted as done.

Markets: every settled market in SERIES (Kalshi's daily high-temperature series for 24 US cities whose rules name TWC
and an NWS climate station) whose rules name The Weather Company, for days DAY_FROM to DAY_TO. An event is one city-day
and its markets are the day's brackets: "greater" settles yes above its floor, "less" below its cap, "between" from its
floor to its cap inclusive (checked against Kalshi's results; a market that disagrees is left out and counted).

Data at an entry: the city's airport sensor readings (routine and special METARs from the Iowa Environmental Mesonet
archive) from the start of the day in local standard time, the NWS climate day, up to ENTRY_LAG before the entry; the
running high is their maximum rounded to a whole degree, and needs at least COVERAGE of the hours so far reported.
Each bracket's bid and ask are the closes of Kalshi's hourly candle that ended in the hour up to the entry; no older
candle is used, and there is no entry at or after a market's close.

Model: the settled TWC figure is the running high plus an offset. The offset's distribution is counted on the training
days (DAY_FROM to before SPLIT, all cities pooled, each entry hour apart) with PSEUDO added to every offset from
OFFSET_MIN to OFFSET_MAX, so it never sees a test day. A bracket's probability is the total over the figures it covers.

Trade (taker, one contract a market, held to settlement): buy YES at the ask if the model's probability is at least the
ask plus the taker fee plus EDGE; otherwise buy NO at 1 - the bid if the model's NO probability is at least that price
plus the fee plus EDGE. Kalshi's taker fee is 0.07 x the series' multiplier x price x (1 - price) a contract, rounded up
to the cent on an order of ORDER_CONTRACTS. Each event is one bet: every market bought on it, settled together on
Kalshi's results.

Main test (pass or fail): entry at MAIN_HOUR local standard time, test days (SPLIT to DAY_TO), all cities. It passes if
the money made over the money staked is above zero across a 95% bootstrap interval over events, above zero in each half
of the test days (split at the median day), and at least MIN_EVENTS events were bet. Everything else is description:
the other entry hours, the settlement gap (TWC against the NWS climate report and against the sensors' full-day high),
the model's and the market's accuracy, cities, price bands, and only books no wider than TIGHT.

    python -m lab.weather fetch --data <dir>      (resumable; Kalshi at about 0.5 requests a second, backing off on 429)
    python -m lab.weather report --data <dir> [--out results.json]
"""

from __future__ import annotations

import argparse
import csv
import http.client
import io
import json
import math
import random
import re
import sys
import time
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from lab.longshot import Fetcher, _close, _num, _ts, _write, fee

REGISTERED = "2026-11-12T19:15:00Z"
AMENDED = "2026-11-12T19:32:00Z"
DAY_FROM, SPLIT, DAY_TO = date(2026, 8, 14), date(2026, 10, 1), date(2026, 11, 10)
# series: (NWS climate station, hours from UTC in local standard time)
SERIES = {
    "KXHIGHAUS": ("AUS", -6), "KXHIGHCHI": ("MDW", -6), "KXHIGHDEN": ("DEN", -7), "KXHIGHLAX": ("LAX", -8),
    "KXHIGHMIA": ("MIA", -5), "KXHIGHNY": ("NYC", -5), "KXHIGHPHIL": ("PHL", -5), "KXHIGHTATL": ("ATL", -5),
    "KXHIGHTBOS": ("BOS", -5), "KXHIGHTDAL": ("DFW", -6), "KXHIGHTDC": ("DCA", -5), "KXHIGHTEWR": ("EWR", -5),
    "KXHIGHTHOU": ("HOU", -6), "KXHIGHTLV": ("LAS", -8), "KXHIGHTMIN": ("MSP", -6), "KXHIGHTNOLA": ("MSY", -6),
    "KXHIGHTOKC": ("OKC", -6), "KXHIGHTPHX": ("PHX", -7), "KXHIGHTSAN": ("SAN", -8), "KXHIGHTSATX": ("SAT", -6),
    "KXHIGHTSDF": ("SDF", -5), "KXHIGHTSEA": ("SEA", -8), "KXHIGHTSFO": ("SFO", -8), "KXHIGHTTTN": ("TTN", -5),
}
ENTRY_HOURS = (13, 16, 19, 22)
MAIN_HOUR = 19
ENTRY_LAG = 300
COVERAGE = 0.75
OFFSET_MIN, OFFSET_MAX = -5, 15
PSEUDO = 0.5
EDGE = 0.05
TIGHT = 0.05
TAKER = 0.07
ORDER_CONTRACTS = 100
MIN_EVENTS = 100
BOOTSTRAP = 2_000
SEED = 20261112
HOUR_S = 3_600
IEM = "https://mesonet.agron.iastate.edu"
MONTHS = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}


def event_day(event_ticker: str) -> date | None:
    """KXHIGHNY-26NOV11 -> 2026-11-11."""
    m = re.search(r"-(\d{2})([A-Z]{3})(\d{2})$", event_ticker or "")
    if not m or m.group(2) not in MONTHS:
        return None
    try:
        return date(2000 + int(m.group(1)), MONTHS[m.group(2)], int(m.group(3)))
    except ValueError:
        return None


def is_twc(m: dict) -> bool:
    return "Weather Company" in (m.get("rules_primary") or "")


def covers(m: dict, v: int) -> bool | None:
    """Whether a settled figure v makes this bracket yes; None if its strikes can't be read."""
    kind, lo, hi = m.get("strike_type"), _num(m.get("floor_strike")), _num(m.get("cap_strike"))
    if kind == "greater" and lo is not None:
        return v > lo
    if kind == "less" and hi is not None:
        return v < hi
    if kind == "between" and lo is not None and hi is not None:
        return lo <= v <= hi
    return None


def day_start(d: date, offset_h: int) -> int:
    """The start of the NWS climate day (midnight local standard time) as a UTC timestamp."""
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp()) - offset_h * HOUR_S


def running_high(readings: list[tuple[int, float]], start: int, t: int) -> int | None:
    """The highest sensor reading from the day's start to ENTRY_LAG before t, rounded; None unless at least COVERAGE of
    the hours so far have a reading."""
    got = [(ts, v) for ts, v in readings if start <= ts <= t - ENTRY_LAG]
    hours = {(ts - start) // HOUR_S for ts, _ in got}
    if not got or len(hours) < COVERAGE * (t - start) / HOUR_S:
        return None
    return math.floor(max(v for _, v in got) + 0.5)


def quote(candles: list[dict], t: int) -> tuple[float | None, float | None]:
    """(yes bid, yes ask) from the hourly candle that ended in the hour up to t."""
    best = None
    for c in candles:
        end = c.get("end_period_ts")
        if end is not None and t - HOUR_S < end <= t and (best is None or end > best["end_period_ts"]):
            best = c
    return (None, None) if best is None else (_close(best, "yes_bid"), _close(best, "yes_ask"))


def offset_model(offsets: list[int]) -> dict[int, float]:
    """The offset's distribution: counts plus PSEUDO on every offset in OFFSET_MIN..OFFSET_MAX."""
    counts: dict[int, float] = {k: PSEUDO for k in range(OFFSET_MIN, OFFSET_MAX + 1)}
    for k in offsets:
        counts[k] = counts.get(k, 0.0) + 1
    total = sum(counts.values())
    return {k: c / total for k, c in counts.items()}


def prob(m: dict, high: int, model: dict[int, float]) -> float | None:
    p = 0.0
    for k, w in model.items():
        c = covers(m, high + k)
        if c is None:
            return None
        p += w * c
    return p


def decide(p: float, bid: float | None, ask: float | None, mult: float, tight: bool = False) -> tuple[str, float, float] | None:
    """(side, price, fee) to buy, or None."""
    if tight and (bid is None or ask is None or ask - bid > TIGHT + 1e-9):
        return None
    if ask is not None and 0.01 - 1e-9 <= ask <= 0.99 + 1e-9:
        f = fee(TAKER * mult, ask, ORDER_CONTRACTS)
        if p >= ask + f + EDGE - 1e-9:
            return ("yes", round(ask, 4), f)
    if bid is not None and 0.01 - 1e-9 <= bid <= 0.99 + 1e-9:
        price = round(1 - bid, 4)
        f = fee(TAKER * mult, price, ORDER_CONTRACTS)
        if 1 - p >= price + f + EDGE - 1e-9:
            return ("no", price, f)
    return None


# ---- loading ----------------------------------------------------------------------------------------------------

def load(data: Path) -> dict:
    series = {s["ticker"]: s for s in json.loads((data / "series.json").read_text())} if (data / "series.json").exists() else {}
    markets: dict[str, dict] = {}
    for p in sorted((data / "markets").glob("*.json")):
        for m in json.loads(p.read_text()):
            markets.setdefault(m["ticker"], m)
    candles = {}
    for p in (data / "candles").glob("*.json"):
        candles.update({t: [{**c, "end_period_ts": int(c["end_period_ts"])} for c in cs if c.get("end_period_ts") is not None]
                        for t, cs in json.loads(p.read_text()).items()})
    cli, asos = {}, {}
    for code, _ in SERIES.values():
        p = data / "cli" / f"{code}.json"
        if p.exists():
            cli[code] = {r["valid"]: _num(r.get("high")) for r in json.loads(p.read_text()).get("results", []) if r.get("valid")}
        p = data / "asos" / f"{code}.csv"
        if p.exists():
            asos[code] = parse_asos(p.read_text())
    return {"series": series, "markets": list(markets.values()), "candles": candles, "cli": cli, "asos": asos}


def parse_asos(text: str) -> list[tuple[int, float]]:
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        v = _num(row.get("tmpf"))
        try:
            ts = int(datetime.strptime(row["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC).timestamp())
        except (KeyError, TypeError, ValueError):
            continue
        if v is not None:
            out.append((ts, v))
    return sorted(out)


def events_of(markets: list[dict]) -> tuple[list[dict], int]:
    """City-days in range with their brackets and TWC figure (None where Kalshi recorded it as text, as "70 to 71"); and
    how many markets disagreed with the bracket rule."""
    by: dict[str, list[dict]] = {}
    for m in markets:
        d = event_day(m.get("event_ticker", ""))
        if m.get("series_ticker") in SERIES and is_twc(m) and d and DAY_FROM <= d <= DAY_TO and m.get("result") in ("yes", "no"):
            by.setdefault(m["event_ticker"], []).append(m)
    out, bad = [], 0
    for ev, ms in sorted(by.items()):
        vals = {_num(m.get("expiration_value")) for m in ms} - {None}
        if len(vals) > 1:  # brackets of one day disagreeing on the figure: none can be trusted
            bad += len(ms)
            continue
        v = math.floor(vals.pop() + 0.5) if vals else None
        good = []
        for m in ms:
            c = covers(m, v if v is not None else 0)  # without a figure, only that its strikes can be read
            if c is None or (v is not None and c != (m["result"] == "yes")):
                bad += 1
            else:
                good.append(m)
        code, off = SERIES[ms[0]["series_ticker"]]
        out.append({"event": ev, "series": ms[0]["series_ticker"], "code": code, "offset_h": off, "day": event_day(ev), "twc": v, "markets": good})
    return out, bad


# ---- the test ---------------------------------------------------------------------------------------------------

def bets(ev: dict, hour: int, model: dict[int, float], readings: list[tuple[int, float]], candles: dict[str, list[dict]],
         series: dict, tight: bool = False) -> dict | None:
    """One event's bet at an entry hour: {event, day, code, contracts, stake, pnl, bands: {band: [stake, pnl, n]}}, or None."""
    t = day_start(ev["day"], ev["offset_h"]) + hour * HOUR_S
    high = running_high(readings, day_start(ev["day"], ev["offset_h"]), t)
    if high is None:
        return None
    mult = _num((series.get(ev["series"]) or {}).get("fee_multiplier"))
    mult = 1.0 if mult is None else mult
    out = {"event": ev["event"], "day": ev["day"], "code": ev["code"], "contracts": 0, "stake": 0.0, "pnl": 0.0, "bands": {}}
    for m in ev["markets"]:
        if not (_ts(m["open_time"]) <= t < _ts(m["close_time"])):
            continue
        p = prob(m, high, model)
        bid, ask = quote(candles.get(m["ticker"]) or [], t)
        d = None if p is None else decide(p, bid, ask, mult, tight)
        if d is None:
            continue
        side, price, f = d
        pnl = (1.0 if m["result"] == side else 0.0) - price - f
        out["contracts"] += 1
        out["stake"] += price + f
        out["pnl"] += pnl
        b = out["bands"].setdefault("under 20c" if price < 0.2 else "over 80c" if price > 0.8 else "20-80c", [0.0, 0.0, 0])
        b[0] += price + f
        b[1] += pnl
        b[2] += 1
    return out if out["contracts"] else None


def summarize(evs: list[dict], rng: random.Random | None = None, draws: int = BOOTSTRAP) -> dict:
    stake, pnl = sum(e["stake"] for e in evs), sum(e["pnl"] for e in evs)
    out = {"events": len(evs), "contracts": sum(e["contracts"] for e in evs), "stake_usd": round(stake, 2), "pnl_usd": round(pnl, 2),
           "return": round(pnl / stake, 5) if stake else None}
    if rng is not None and len(evs) >= 2 and draws:
        rs = []
        for _ in range(draws):
            pick = [evs[rng.randrange(len(evs))] for _ in evs]
            st = sum(e["stake"] for e in pick)
            rs.append(sum(e["pnl"] for e in pick) / st if st else 0.0)
        rs.sort()
        out["ci95"] = [round(rs[int(0.025 * draws)], 5), round(rs[int(0.975 * draws) - 1], 5)]
    return out


def halves(evs: list[dict]) -> list[dict]:
    if not evs:
        return [summarize([]), summarize([])]
    mid = sorted(e["day"] for e in evs)[len(evs) // 2]
    return [summarize([e for e in evs if e["day"] < mid]), summarize([e for e in evs if e["day"] >= mid])]


def passed(r: dict) -> bool:
    return bool(r.get("ci95") and r["ci95"][0] > 0 and r["events"] >= MIN_EVENTS and all((h.get("return") or 0) > 0 for h in r["halves"]))


def evaluate(d: dict) -> dict:
    rng = random.Random(SEED)
    events, bad = events_of(d["markets"])
    train = [e for e in events if e["day"] < SPLIT]
    test = [e for e in events if e["day"] >= SPLIT]
    out = {"registered": REGISTERED, "amended": AMENDED, "events": len(events), "train_events": len(train), "test_events": len(test),
           "markets": sum(len(e["markets"]) for e in events), "markets_left_out": bad,
           "events_without_figure": sum(e["twc"] is None for e in events),
           "with_prices": sum(1 for e in events for m in e["markets"] if d["candles"].get(m["ticker"])),
           "gap": gap(events, d), "by_hour": {}}
    for hour in ENTRY_HOURS:
        offs = []
        for e in (e for e in train if e["twc"] is not None):
            rd = d["asos"].get(e["code"]) or []
            h = running_high(rd, day_start(e["day"], e["offset_h"]), day_start(e["day"], e["offset_h"]) + hour * HOUR_S)
            if h is not None:
                offs.append(e["twc"] - h)  # a test-day figure is never read here
        model = offset_model(offs)
        evs = [b for e in test if (b := bets(e, hour, model, d["asos"].get(e["code"]) or [], d["candles"], d["series"])) is not None]
        r = summarize(evs, rng)
        r["halves"] = halves(evs)
        r["training_days_used"] = len(offs)
        r["offsets"] = {str(k): round(v, 4) for k, v in sorted(model.items()) if v >= 0.005}
        r["accuracy"] = accuracy(test, hour, model, d)
        if hour == MAIN_HOUR:
            r["by_city"] = {c: summarize([e for e in evs if e["code"] == c]) for c in sorted({e["code"] for e in evs})}
            r["by_band"] = {}
            for band in ("under 20c", "20-80c", "over 80c"):
                st = sum(e["bands"].get(band, [0, 0, 0])[0] for e in evs)
                pl = sum(e["bands"].get(band, [0, 0, 0])[1] for e in evs)
                r["by_band"][band] = {"contracts": sum(e["bands"].get(band, [0, 0, 0])[2] for e in evs), "return": round(pl / st, 5) if st else None}
            tight = [b for e in test if (b := bets(e, hour, model, d["asos"].get(e["code"]) or [], d["candles"], d["series"], tight=True)) is not None]
            r["tight_books"] = {**summarize(tight, rng), "halves": halves(tight)}
        out["by_hour"][str(hour)] = r
    main = out["by_hour"][str(MAIN_HOUR)]
    out["main_test"] = {"passed": passed(main), "return": main["return"], "ci95": main.get("ci95"),
                        "halves": [h.get("return") for h in main["halves"]], "events": main["events"]}
    return out


def gap(events: list[dict], d: dict) -> dict:
    """How TWC's figure compared with the NWS climate report and with the sensors' full-day high, over every day."""
    def tally(diffs: list[int]) -> dict:
        n = len(diffs)
        return {"days": n, "same": round(sum(x == 0 for x in diffs) / n, 4) if n else None,
                "off_by_1": round(sum(abs(x) == 1 for x in diffs) / n, 4) if n else None,
                "off_by_2_plus": round(sum(abs(x) >= 2 for x in diffs) / n, 4) if n else None,
                "twc_higher": round(sum(x > 0 for x in diffs) / n, 4) if n else None,
                "twc_lower": round(sum(x < 0 for x in diffs) / n, 4) if n else None}
    vs_cli, vs_sensor, by_city = [], [], {}
    for e in (e for e in events if e["twc"] is not None):
        c = (d["cli"].get(e["code"]) or {}).get(e["day"].isoformat())
        if c is not None:
            x = e["twc"] - math.floor(c + 0.5)
            vs_cli.append(x)
            by_city.setdefault(e["code"], []).append(x)
        start = day_start(e["day"], e["offset_h"])
        h = running_high(d["asos"].get(e["code"]) or [], start, start + 24 * HOUR_S + ENTRY_LAG - 1)
        if h is not None:
            vs_sensor.append(e["twc"] - h)
    return {"vs_nws_report": tally(vs_cli), "vs_sensor_high": tally(vs_sensor), "vs_nws_report_by_city": {c: tally(x) for c, x in sorted(by_city.items())}}


def accuracy(test: list[dict], hour: int, model: dict[int, float], d: dict) -> dict:
    """Log loss and Brier of the model and of the market's mid on every quoted bracket of the test days at this hour."""
    rows = []
    for e in test:
        start = day_start(e["day"], e["offset_h"])
        t = start + hour * HOUR_S
        high = running_high(d["asos"].get(e["code"]) or [], start, t)
        if high is None:
            continue
        for m in e["markets"]:
            if not (_ts(m["open_time"]) <= t < _ts(m["close_time"])):
                continue
            bid, ask = quote(d["candles"].get(m["ticker"]) or [], t)
            p = prob(m, high, model)
            if p is None or bid is None or ask is None or not (0 <= bid <= ask <= 1):
                continue
            rows.append((p, (bid + ask) / 2, 1.0 if m["result"] == "yes" else 0.0))
    if not rows:
        return {"brackets": 0}
    ll = lambda q, y: -math.log(min(max(q if y else 1 - q, 1e-3), 1.0))
    n = len(rows)
    return {"brackets": n, "model_log_loss": round(sum(ll(p, y) for p, _, y in rows) / n, 4),
            "market_log_loss": round(sum(ll(q, y) for _, q, y in rows) / n, 4),
            "model_brier": round(sum((p - y) ** 2 for p, _, y in rows) / n, 4),
            "market_brier": round(sum((q - y) ** 2 for _, q, y in rows) / n, 4)}


# ---- fetching ---------------------------------------------------------------------------------------------------

def _has_cli(p: Path) -> bool:
    try:
        return bool(json.loads(p.read_text()).get("results"))
    except (OSError, ValueError, AttributeError):
        return False


def _has_asos(p: Path) -> bool:
    try:
        return bool(parse_asos(p.read_text()))
    except OSError:
        return False


def _iem(url: str, log, tries: int = 4) -> str | None:
    """The Iowa Environmental Mesonet archive, gently: a pause before each request and a few retries."""
    for i in range(tries):
        time.sleep(2 + 4 * i)
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read().decode()
        except (OSError, http.client.HTTPException) as exc:  # a timeout, a dropped connection or a server error
            log(f"IEM retry {i + 1}: {type(exc).__name__}")
    return None


def fetch(data: Path, rate: float = 0.5) -> None:
    for sub in ("markets", "candles", "cli", "asos"):
        (data / sub).mkdir(parents=True, exist_ok=True)
    with open(data / "fetch.log", "a") as logf:
        _fetch(data, rate, lambda *a: print(datetime.now(UTC).strftime("%H:%M:%SZ"), *a, file=logf, flush=True))


def _fetch(data: Path, rate: float, log) -> None:
    f = Fetcher(rate, log)
    if not (data / "series.json").exists():
        got = f.get("/series", {"category": "Climate and Weather"})
        if got is not None:
            _write(data / "series.json", [s for s in got.get("series") or [] if s["ticker"] in SERIES])
    for s in SERIES:
        p = data / "markets" / f"{s}.json"
        if p.exists():
            continue
        kept, ok = [], True
        for src, path in (("live", "/markets"), ("historical", "/historical/markets")):
            cursor = None
            while True:
                params = {"series_ticker": s, "limit": 1000, **({"status": "settled"} if src == "live" else {}), **({"cursor": cursor} if cursor else {})}
                got = f.get(path, params)
                if got is None:
                    ok = False
                    break
                page = got.get("markets") or []
                for m in page:
                    d = event_day(m.get("event_ticker", ""))
                    if is_twc(m) and d and DAY_FROM <= d <= DAY_TO:
                        kept.append({**m, "series_ticker": m.get("series_ticker") or s, "_src": src})  # listings may leave it out
                cursor = got.get("cursor")
                # the archive ignores date filters and lists newest first: a page wholly before DAY_FROM ends it
                if not cursor or (src == "historical" and page and all((event_day(m.get("event_ticker", "")) or date.min) < DAY_FROM for m in page)):
                    break
        if ok:
            _write(p, kept)
        log(f"series {s}: {len(kept)} markets" + ("" if ok else "; a listing page failed, left for the next run"))
    by: dict[str, list[dict]] = {}
    for p in sorted((data / "markets").glob("*.json")):
        for m in json.loads(p.read_text()):
            by.setdefault(m["event_ticker"], []).append(m)
    todo = [ev for ev in sorted(by) if not (data / "candles" / f"{ev}.json").exists()]
    log(f"prices: {len(by) - len(todo)} of {len(by)} events already fetched")
    for j, ev in enumerate(todo):
        ms = by[ev]
        params = {"start_ts": min(_ts(m["open_time"]) for m in ms), "end_ts": max(_ts(m["close_time"]) for m in ms), "period_interval": 60}
        got: dict[str, list] | None = {}
        if all(m.get("_src") == "live" for m in ms):
            r = f.get(f"/series/{ms[0]['series_ticker']}/events/{ev}/candlesticks", params)
            if r is not None and r.get("market_tickers"):
                got = dict(zip(r["market_tickers"], r.get("market_candlesticks") or []))
        for m in ms:
            if m["ticker"] in got:
                continue
            first = f"/historical/markets/{m['ticker']}/candlesticks" if m.get("_src") == "historical" else f"/series/{m['series_ticker']}/markets/{m['ticker']}/candlesticks"
            second = f"/series/{m['series_ticker']}/markets/{m['ticker']}/candlesticks" if m.get("_src") == "historical" else f"/historical/markets/{m['ticker']}/candlesticks"
            r = f.get(first, params) or f.get(second, params)
            if r is None:
                got = None
                break
            got[m["ticker"]] = r.get("candlesticks") or []
        if got is not None:
            _write(data / "candles" / f"{ev}.json", got)
        if j % 50 == 0:
            log(f"prices {j}/{len(todo)}; requests {f.requests}, 429s {f.limited}, failed {f.failed}")
    y0, y1 = DAY_FROM - timedelta(days=1), DAY_TO + timedelta(days=2)
    for code in sorted({c for c, _ in SERIES.values()}):
        p = data / "cli" / f"{code}.json"
        if not _has_cli(p):
            txt = _iem(f"{IEM}/json/cli.py?station=K{code}&year={DAY_FROM.year}", log)
            try:
                got = json.loads(txt) if txt is not None else None
            except ValueError:
                got = None
            if got and got.get("results"):
                _write(p, got)
        p = data / "asos" / f"{code}.csv"
        if not _has_asos(p):
            txt = _iem(f"{IEM}/cgi-bin/request/asos.py?station={code}&data=tmpf&year1={y0.year}&month1={y0.month}&day1={y0.day}"
                       f"&year2={y1.year}&month2={y1.month}&day2={y1.day}&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&trace=T"
                       f"&direct=no&report_type=3&report_type=4", log)
            if txt is not None and txt.startswith("station,") and parse_asos(txt):
                tmp = p.with_name(p.name + ".tmp")
                tmp.write_text(txt)
                tmp.replace(p)
    missing = [ev for ev in by if not (data / "candles" / f"{ev}.json").exists()]
    no_wx = [c for c, _ in SERIES.values() if not _has_cli(data / "cli" / f"{c}.json") or not _has_asos(data / "asos" / f"{c}.csv")]
    no_series = [s for s in SERIES if not (data / "markets" / f"{s}.json").exists()]
    log(f"done: {len(by) - len(missing)} of {len(by)} events priced ({len(missing)} missing), {len(no_series)} series not listed, "
        f"{len(no_wx)} stations missing weather data (run again to retry); requests {f.requests}, 429s {f.limited}, failed {f.failed}")


# ---- output -----------------------------------------------------------------------------------------------------

def lines(r: dict) -> list[str]:
    pct = lambda x: "-" if x is None else f"{100 * x:+.2f}%"
    g = r["gap"]
    out = [(f"weather settlement backtest (rules registered {r['registered']}, amended {r['amended']} before the report): "
            f"{r['events']} city-days ({r['train_events']} training, {r['test_events']} test; {r['events_without_figure']} settled "
            f"with a text figure), {r['markets']} markets, {r['with_prices']} with prices, {r['markets_left_out']} left out"),
           "TWC vs NWS report: " + json.dumps(g["vs_nws_report"]), "TWC vs sensor high: " + json.dumps(g["vs_sensor_high"])]
    for hour, v in r["by_hour"].items():
        ci = v.get("ci95")
        out.append(f"{hour}:00 entry  {v['events']:4d} events {v['contracts']:5d} contracts  return {pct(v['return'])}"
                   + (f" (95%: {pct(ci[0])} to {pct(ci[1])})" if ci else "")
                   + f"  halves {pct(v['halves'][0].get('return'))} / {pct(v['halves'][1].get('return'))}  accuracy {json.dumps(v['accuracy'])}")
    mt = r["main_test"]
    out.append(f"main test ({MAIN_HOUR}:00, test days): {'PASSED' if mt['passed'] else 'FAILED'}: return {pct(mt['return'])}"
               + (f", 95% {pct(mt['ci95'][0])} to {pct(mt['ci95'][1])}" if mt.get("ci95") else "")
               + f", halves {' / '.join(pct(h) for h in mt['halves'])}, {mt['events']} events")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kalshi's daily high-temperature markets against The Weather Company's settlement")
    parser.add_argument("command", choices=("fetch", "report"))
    parser.add_argument("--data", required=True)
    parser.add_argument("--rate", type=float, default=0.5)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    data = Path(args.data)
    if args.command == "fetch":
        fetch(data, args.rate)
        return 0
    r = evaluate(load(data))
    if args.out:
        Path(args.out).write_text(json.dumps(r, indent=1, default=str))
    print("\n".join(lines(r)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
