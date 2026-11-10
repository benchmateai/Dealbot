"""Bitcoin's option market as a yardstick for the Bitcoin prediction markets (lab, public data, no orders, no key).

Deribit's public API gives every listed BTC option's mark implied volatility (get_book_summary_by_currency,
one request) and the BTC index (get_index_price). From those this module keeps a compact surface, `opt_surface`:
  {index, expiries: [{exp (ms, 08:00Z on the expiry date), f (that expiry's forward), k: [strikes], v: [vols]}]}
with only the out-of-the-money options (calls above the forward, puts below) of expiries MIN_DAYS to MAX_DAYS
away, and prices the prediction markets' contracts on it:
  terminal  P(index above K at T), from the smile at T: minus the slope of the undiscounted Black-76 call price
            in the strike (Breeden-Litzenberger), so a year-end $5,000 range is P(above lo) - P(above hi). This
            is what the options themselves imply: a range is a call spread's slope.
  touch     P(index reaches B before T), for "how high / how low / hits $X by": a geometric Brownian motion from
            the index now, with the drift the forward implies and the volatility at the barrier's strike at T.
            This is a model's price, not one the options pin down.
Volatility between two expiries interpolates total variance (vol^2 x years) linearly in time at the same
log-moneyness; before the first kept expiry or after the last it is that expiry's smile. When the index has
moved since the surface was read, the forwards move with it and each smile keeps its shape in moneyness.
Deribit's index stands in for CF Benchmarks' BRTI, on which both venues settle (both are composite USD spot
indices), and the venues' 60-second settlement averages are ignored; prices are undiscounted.

    python -m lab.btc_options [--pairs lab/gap_pairs.json]   one live look: each Bitcoin pair beside its price
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache

from lab.rest import Budget

DERIBIT = "https://www.deribit.com"
YEAR_MS = 365.25 * 86_400_000
MIN_DAYS, MAX_DAYS = 2.0, 200.0   # expiries kept: near enough to read Dec 1 and Jan 1 from, not the noisiest dailies
MIN_STRIKES = 5
EXPIRY_HOUR_UTC = 8
STEP = 0.002                       # the strike step, as a share of the strike, for the call price's slope
MONTHS = {m: i + 1 for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"))}


def expiry_ms(code: str) -> int | None:
    """Deribit's expiry code to the moment its options expire: '25DEC26' -> 2026-12-25T08:00Z."""
    try:
        day, month, year = int(code[:-5]), MONTHS[code[-5:-2]], 2000 + int(code[-2:])
        return int(datetime(year, month, day, EXPIRY_HOUR_UTC, tzinfo=timezone.utc).timestamp() * 1000)
    except (KeyError, ValueError):
        return None


@lru_cache(maxsize=None)
def iso_ms(text: str) -> int:
    return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp() * 1000)


class Deribit:
    """Deribit's public market data, paced by its own budget; `get` returns the call's `result` or None."""

    def __init__(self, budget: Budget | None = None, *, opener=urllib.request.urlopen, base: str = DERIBIT) -> None:
        self.budget = budget or Budget(2.0, 4.0)
        self.opener, self.base = opener, base
        self.requests = self.errors = self.rate_limited = 0

    def get(self, method: str, params: dict) -> object | None:
        self.budget.take()
        self.requests += 1
        url = f"{self.base}/api/v2/public/{method}?{urllib.parse.urlencode(params)}"
        try:
            with self.opener(urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "dealbot-lab"}), timeout=20) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            self.errors += 1
            if exc.code == 429:
                self.rate_limited += 1
                self.budget.pause(10.0)
            return None
        except (OSError, ValueError):
            self.errors += 1
            return None
        return body.get("result") if isinstance(body, dict) else None

    def index(self) -> float | None:
        r = self.get("get_index_price", {"index_name": "btc_usd"})
        v = r.get("index_price") if isinstance(r, dict) else None
        return float(v) if isinstance(v, (int, float)) and v > 0 else None

    def summary(self) -> list[dict] | None:
        r = self.get("get_book_summary_by_currency", {"currency": "BTC", "kind": "option"})
        return r if isinstance(r, list) else None

    def counters(self) -> dict:
        return {"requests": self.requests, "errors": self.errors, "rate_limited": self.rate_limited}


def surface_record(rows: list[dict], index: float | None, now_ms: int, *, min_days: float = MIN_DAYS, max_days: float = MAX_DAYS) -> dict | None:
    """The `opt_surface` record from Deribit's option book summary: per expiry in the window, the forward and the
    out-of-the-money options' mark volatilities by strike. None when nothing usable came back."""
    by_exp: dict[int, dict[float, tuple[float, float]]] = defaultdict(dict)
    spots = []
    for r in rows or []:
        parts = str(r.get("instrument_name") or "").split("-")
        if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in ("C", "P"):
            continue
        exp = expiry_ms(parts[1])
        try:
            strike = float(parts[2])
        except ValueError:
            continue
        iv, fwd = r.get("mark_iv"), r.get("underlying_price")
        if isinstance(r.get("estimated_delivery_price"), (int, float)):
            spots.append(float(r["estimated_delivery_price"]))
        if exp is None or not isinstance(iv, (int, float)) or iv <= 0 or not isinstance(fwd, (int, float)) or fwd <= 0:
            continue
        if not min_days <= (exp - now_ms) / 86_400_000 <= max_days:
            continue
        if (parts[3] == "C") == (strike >= fwd):  # out of the money: a call above the forward, a put below it
            by_exp[exp][strike] = (iv / 100.0, float(fwd))
    expiries = []
    for exp in sorted(by_exp):
        strikes = by_exp[exp]
        if len(strikes) < MIN_STRIKES:
            continue
        ks = sorted(strikes)
        expiries.append({"exp": exp, "f": round(statistics.median(v[1] for v in strikes.values()), 2), "k": ks,
                         "v": [round(strikes[k][0], 4) for k in ks]})
    spot = index if index else (statistics.median(spots) if spots else None)
    if not expiries or not spot:
        return None
    return {"index": round(float(spot), 2), "expiries": expiries}


def _ncdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def _call(forward: float, strike: float, vol: float, years: float) -> float:
    """Black-76 call, undiscounted."""
    sd = vol * math.sqrt(years)
    if sd <= 0:
        return max(0.0, forward - strike)
    d1 = (math.log(forward / strike) + 0.5 * sd * sd) / sd
    return forward * _ncdf(d1) - strike * _ncdf(d1 - sd)


class Surface:
    """One `opt_surface` record, read at `ts_ms`; prices contracts at any later moment with the index then."""

    def __init__(self, rec: dict, ts_ms: int) -> None:
        self.ts = ts_ms
        self.index = float(rec["index"])
        self.exps = []
        for e in sorted(rec.get("expiries") or [], key=lambda e: e["exp"]):
            f = float(e["f"])
            self.exps.append((int(e["exp"]), f, [math.log(k / f) for k in e["k"]], [float(v) for v in e["v"]]))

    @staticmethod
    def _smile(xs: list[float], vs: list[float], x: float) -> float:
        if x <= xs[0]:
            return vs[0]
        if x >= xs[-1]:
            return vs[-1]
        i = bisect_left(xs, x)
        return vs[i - 1] + (vs[i] - vs[i - 1]) * (x - xs[i - 1]) / (xs[i] - xs[i - 1])

    def vol(self, strike: float, t_ms: int, now_ms: int, spot: float | None = None) -> tuple[float, float, float] | None:
        """(volatility, forward, years) for `strike` at maturity t_ms, seen at now_ms with the index at `spot`."""
        scale = spot / self.index if spot else 1.0
        live = [e for e in self.exps if e[0] > now_ms]
        if not live or t_ms <= now_ms:
            return None
        t = (t_ms - now_ms) / YEAR_MS
        times = [(e[0] - now_ms) / YEAR_MS for e in live]
        if t <= times[0] or t >= times[-1]:
            _, f, xs, vs = live[0] if t <= times[0] else live[-1]
            forward = f * scale
            return self._smile(xs, vs, math.log(strike / forward)), forward, t
        j = bisect_left(times, t)  # times[j-1] < t <= times[j]
        (_, f1, xs1, vs1), (_, f2, xs2, vs2) = live[j - 1], live[j]
        t1, t2 = times[j - 1], times[j]
        a = (t - t1) / (t2 - t1)
        forward = (f1 + (f2 - f1) * a) * scale
        x = math.log(strike / forward)
        w = (1 - a) * self._smile(xs1, vs1, x) ** 2 * t1 + a * self._smile(xs2, vs2, x) ** 2 * t2
        return math.sqrt(max(w, 1e-12) / t), forward, t

    def prob_above(self, strike: float, t_ms: int, now_ms: int, spot: float | None = None) -> float | None:
        """P(index above `strike` at t_ms): minus the call price's slope in the strike, on the smile."""
        h = strike * STEP
        lo, hi = self.vol(strike - h, t_ms, now_ms, spot), self.vol(strike + h, t_ms, now_ms, spot)
        if lo is None or hi is None:
            return None
        slope = (_call(lo[1], strike - h, lo[0], lo[2]) - _call(hi[1], strike + h, hi[0], hi[2])) / (2 * h)
        return min(1.0, max(0.0, slope))

    def prob_touch(self, barrier: float, t_ms: int, now_ms: int, spot: float, *, up: bool) -> float | None:
        """P(index reaches `barrier` before t_ms): a geometric Brownian motion from `spot` with the drift the
        forward implies and the volatility at the barrier's strike (a model's price)."""
        if (up and spot >= barrier) or (not up and spot <= barrier):
            return 1.0
        v = self.vol(barrier, t_ms, now_ms, spot)
        if v is None:
            return None
        s, forward, t = v
        sd = s * math.sqrt(t)
        mu = math.log(forward / spot) / t - 0.5 * s * s
        b = math.log(barrier / spot)
        tilt = math.exp(2 * mu * b / (s * s))
        if up:
            p = _ncdf((-b + mu * t) / sd) + tilt * _ncdf((-b - mu * t) / sd)
        else:
            p = _ncdf((b - mu * t) / sd) + tilt * _ncdf((b + mu * t) / sd)
        return min(1.0, max(0.0, p))


def fair(model: dict, surface: Surface, now_ms: int, spot: float) -> float | None:
    """What a contract's YES is worth on the surface, from its `model` in lab/gap_pairs.json:
    {kind: range|above|below, lo/hi or k, at} or {kind: touch_up|touch_down, k, by} (ISO times, UTC)."""
    kind = model.get("kind")
    if kind in ("range", "above", "below"):
        t = iso_ms(model["at"])
        if kind == "range":
            a, b = surface.prob_above(float(model["lo"]), t, now_ms, spot), surface.prob_above(float(model["hi"]), t, now_ms, spot)
            return None if a is None or b is None else max(0.0, a - b)
        a = surface.prob_above(float(model["k"]), t, now_ms, spot)
        return None if a is None else (a if kind == "above" else 1.0 - a)
    if kind in ("touch_up", "touch_down"):
        return surface.prob_touch(float(model["k"]), iso_ms(model["by"]), now_ms, spot, up=kind == "touch_up")
    return None


def main(argv: list[str] | None = None) -> int:
    from lab.gap_recorder import KALSHI_BATCH, PolyUS, kalshi_quote, load_pairs, poly_quote
    from lab.rest import LabRest

    parser = argparse.ArgumentParser(description="One live look: each Bitcoin pair's two venues beside the price Bitcoin's options imply")
    parser.add_argument("--pairs", default=None)
    args = parser.parse_args(argv)
    pairs = [p for p in (load_pairs(args.pairs) if args.pairs else load_pairs()) if p.get("model")]
    d = Deribit()
    now = int(time.time() * 1000)
    rec = surface_record(d.summary() or [], d.index(), now)
    if rec is None:
        print(f"no option surface from Deribit ({d.counters()})")
        return 1
    surface = Surface(rec, now)
    kalshi, poly = LabRest(budget=Budget(0.5, 2.0)), PolyUS()
    kq = {}
    for i in range(0, len(pairs), KALSHI_BATCH):
        batch = pairs[i:i + KALSHI_BATCH]
        for m in ((kalshi.get("/markets", {"tickers": ",".join(p["kalshi"] for p in batch), "limit": len(batch)}) or {}).get("markets") or []):
            kq[m.get("ticker")] = kalshi_quote(m, now)
    print(f"index {rec['index']:,.0f}; {len(rec['expiries'])} expiries; cents: fair | Kalshi bid/ask | Polymarket US bid/ask")
    for p in pairs:
        book = poly.get(f"/v1/markets/{urllib.parse.quote(p['polymarket_us'])}/book")
        pq = poly_quote(book, now) if book else {}
        k = kq.get(p["kalshi"]) or {}
        f = fair(p["model"], surface, now, rec["index"])
        c = lambda v: "  -  " if v is None else f"{100 * v:5.1f}"  # noqa: E731
        print(f"  {p['id']:<20} {c(f)} | {c(k.get('bid'))} {c(k.get('ask'))} | {c(pq.get('bid'))} {c(pq.get('ask'))}")
    print(f"Deribit {d.counters()}; Kalshi {kalshi.counters()}; Polymarket US {poly.counters()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
