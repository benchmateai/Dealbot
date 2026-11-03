"""Pre-flight for an unattended chunk: prove, before a single live block runs, that the desk can trade.

Two halves, both read-only:

* scenario (no network): the desk is built from this environment's real configuration, fed a sane
  simulated market and a judge that is confident, and run across one full Kalshi contract (or a spot
  stretch of the same length). It must open a position. On sane data with a confident judge nothing
  should stop it, so any rejection or veto that does is named: that is a configuration defect of the
  kind that would otherwise leave a chunk running empty for hours.
* live (public market data only, never signed): every configured series has a current contract that
  parses with a strike and open/close times and shows a sane two-sided quote within a few tries, and
  every underlying product answers with a sane book.

    python -m desk.preflight            # both halves; exit 0 on pass, 1 on failure, 2 on bad config
    python -m desk.preflight --offline  # scenario only
"""

from __future__ import annotations

import argparse
import collections
import math
import os
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from desk.clock import BlockClock
from desk.config import ConfigError, DeskConfig

# Checks that fire on healthy data at the start of every contract or by design; never a defect alone.
BENIGN_CHECKS = frozenset(
    {"insufficient_data", "insufficient_ticks", "rv_unavailable", "outside_trade_window", "no_contract", "benched", "not_best", "below_threshold", "jev_budget"}
)
SCENARIO_EPOCH_MS = 1_700_000_100_000  # any fixed instant; contract 0 of the simulated series opens here


@dataclass
class ScenarioResult:
    ok: bool
    opened: int
    would_execute: int
    judge_calls: int
    blocks: int
    decisions: dict[str, int]
    blockers: dict[str, int]
    benign: dict[str, int]
    details: dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        head = "PASS" if self.ok else "FAIL"
        lines = [f"scenario {head}: {self.blocks} blocks, judge calls {self.judge_calls}, positions opened {self.opened}, would-execute {self.would_execute}, decisions {self.decisions}"]
        for check, n in sorted(self.blockers.items(), key=lambda kv: -kv[1]):
            lines.append(f"  blocked by {check} x{n}: {self.details.get(check, '')}")
        if not self.ok and not self.blockers:
            lines.append("  nothing was rejected or vetoed, yet no position opened: look at the decisions above")
        return "\n".join(lines)


def run_scenario(env: Mapping[str, str], *, blocks: int | None = None) -> ScenarioResult:
    """Run the desk on simulated, sane data with this environment's configuration and a confident judge."""
    from feed.synthetic import DEFAULT_PRICES, SyntheticFeed
    from judge.scripted import ScriptedJudge
    from logs.writer import read_events

    with tempfile.TemporaryDirectory(prefix="dealbot-preflight-") as tmp:
        cfg = DeskConfig.from_env({**env, "LOG_DIR": f"{tmp}/logs", "TRIALS_FILE": f"{tmp}/trials.json", "JUDGE_URL": "stub://local"})
        t0 = SCENARIO_EPOCH_MS
        clock = {"now": t0}
        binary = cfg.fee_model == "kalshi"
        if binary:
            from kalshi.feed import KalshiFeed
            from kalshi.sim import SimKalshiClient

            products = tuple(sorted(set(cfg.kalshi_underlying[s] for s in cfg.symbols)))
            prices = {p: DEFAULT_PRICES.get(p, 100.0) for p in products}
            under = SyntheticFeed(products, start_ms=t0 - 30 * cfg.block_ms, tick_ms=1000, seed=5, start_prices=prices)
            under.advance(t0)
            from kalshi.model import p_above

            def fair(series: str, contract, now: int) -> float | None:
                hist = under.history(cfg.kalshi_underlying[series])
                if not hist or contract.close_ts is None or contract.strike is None:
                    return None
                return p_above(hist[-1].mid, contract.strike, max(1.0, (contract.close_ts - now) / 1000), 3.0 * math.sqrt(cfg.block_ms / 1000), cfg.block_ms / 1000)

            sim = SimKalshiClient(lambda: clock["now"], strikes={s: prices[cfg.kalshi_underlying[s]] for s in cfg.symbols}, epoch_ms=t0, fair=fair)
            feed = KalshiFeed(
                cfg.symbols,
                underlying={s: cfg.kalshi_underlying[s] for s in cfg.symbols},
                client=sim,
                underlying_feed=under,
                poll_ms=cfg.feed_poll_ms,
                block_ms=cfg.block_ms,
                trade_window_s=cfg.kalshi_trade_window_s,
                min_time_left_s=cfg.kalshi_min_time_left_s,
                rv_window_blocks=cfg.rv_window_blocks,
                now_ms=lambda: clock["now"],
            )
            judge = ScriptedJudge(cfg.jev_model, nouls={"settles_yes": 0.99})
            n_blocks = blocks or math.ceil((sim.cycle_ms + 60_000) / cfg.block_ms)
        else:
            feed = SyntheticFeed(cfg.symbols, start_ms=t0 - cfg.warmup_blocks * cfg.block_ms, tick_ms=cfg.synthetic_tick_ms, seed=5)
            judge = ScriptedJudge(cfg.jev_model)
            n_blocks = blocks or 80

        from desk.run import build_desk

        desk, log = build_desk(cfg, start_ms=t0 + cfg.block_ms, judge=judge, feed=feed, trial_id="preflight")
        polls = max(1, round(cfg.block_ms / max(1, cfg.feed_poll_ms)))
        try:
            for block in BlockClock(cfg.block_ms, t0 + cfg.block_ms, realtime=False).blocks(n_blocks):
                if binary:
                    for k in range(polls):
                        clock["now"] = block.ts_ms - cfg.block_ms + int((k + 0.5) * cfg.block_ms / polls)
                        feed.poll_once()
                desk.step(block)
        finally:
            log.close()
        events = list(read_events(cfg.log_dir))

    kinds = collections.Counter(e["kind"] for e in events)
    checks: collections.Counter[str] = collections.Counter()
    details: dict[str, str] = {}
    for e in events:
        if e["kind"] in ("rejection", "veto"):
            check = str(e.get("check") or "?")
            checks[check] += 1
            details.setdefault(check, str(e.get("detail") or "")[:200])
    decisions = collections.Counter(str(e.get("action")) for e in events if e["kind"] == "decision")
    blockers = {c: n for c, n in checks.items() if c not in BENIGN_CHECKS}
    benign = {c: n for c, n in checks.items() if c in BENIGN_CHECKS}
    opened, would = kinds.get("position_opened", 0), kinds.get("would_execute", 0)
    return ScenarioResult(opened > 0 or would > 0, opened, would, len(judge.calls), n_blocks, dict(decisions), blockers, benign, {c: details[c] for c in blockers})


@dataclass
class LiveResult:
    ok: bool
    lines: list[str]

    def summary(self) -> str:
        return "\n".join([f"live {'PASS' if self.ok else 'FAIL'}"] + [f"  {line}" for line in self.lines])


def check_live(cfg: DeskConfig, *, client=None, book_fetch: Callable[[str], dict] | None = None, attempts: int = 4, wait_s: float = 5.0, now_ms: Callable[[], int] | None = None, sleep: Callable[[float], None] = time.sleep) -> LiveResult:
    """Public market data only: every series has a sane current contract and quote; every product answers."""
    from feed.coinbase import DEFAULT_BASE_URL, http_fetch, parse_book

    now = now_ms or (lambda: int(time.time() * 1000))
    lines: list[str] = []
    ok = True
    products: tuple[str, ...]
    if cfg.fee_model == "kalshi":
        from kalshi.api import KalshiApiError, KalshiClient
        from kalshi.feed import pick_current

        client = client or KalshiClient(cfg.kalshi_base_url)  # unsigned: market data is public
        for series in cfg.symbols:
            problem = ""
            for attempt in range(attempts):
                try:
                    current = pick_current(client.markets(series), now())
                    if current is None:
                        problem = "no open contract"
                    elif current.strike is None or current.close_ts is None or current.open_ts is None:
                        problem = f"{current.ticker} parsed without strike/open/close: strike={current.strike} open={current.open_ts} close={current.close_ts}"
                    else:
                        bid, ask, bid_qty, ask_qty = client.quote(current) if hasattr(client, "quote") else client.orderbook(current.ticker)
                        if bid is None or ask is None or not (0 < bid <= ask < 1):
                            problem = f"{current.ticker} quote is not two-sided and sane: bid={bid} ask={ask}"
                        else:
                            lines.append(f"{series}: {current.ticker} strike {current.strike} closes in {(current.close_ts - now()) / 1000:.0f} s, YES {bid:.2f}/{ask:.2f} ({bid_qty:g} x {ask_qty:g})")
                            problem = ""
                            break
                except KalshiApiError as exc:
                    problem = f"Kalshi: {exc}"
                except (ValueError, TypeError, KeyError) as exc:
                    problem = f"could not parse Kalshi's answer: {type(exc).__name__}: {exc}"
                if attempt + 1 < attempts:
                    sleep(wait_s)
            if problem:
                ok = False
                lines.append(f"{series}: {problem}")
        products = tuple(sorted(set(cfg.kalshi_underlying[s] for s in cfg.symbols)))
    elif cfg.feed == "coinbase":
        products = cfg.symbols
    else:
        return LiveResult(True, [f"feed {cfg.feed} has no live endpoint to check"])
    base = cfg.feed_base_url or DEFAULT_BASE_URL
    fetch = book_fetch or (lambda product: http_fetch(f"{base}/products/{product}/book?level=1"))
    for product in products:
        try:
            tick = parse_book(fetch(product), received_ms=now())
            if not tick.is_sane():
                raise ValueError(f"book not sane: bid={tick.bid} ask={tick.ask}")
            lines.append(f"{product}: {tick.bid:g}/{tick.ask:g}")
        except Exception as exc:  # noqa: BLE001 - any failure here means the underlying is not usable
            ok = False
            lines.append(f"{product}: {type(exc).__name__}: {exc}")
    return LiveResult(ok, lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-flight: prove the desk can trade before a chunk starts (read-only)")
    parser.add_argument("--offline", action="store_true", help="scenario only, no network")
    args = parser.parse_args(argv)
    env = dict(os.environ)
    try:
        cfg = DeskConfig.from_env(env)
    except (ConfigError, ValueError) as exc:
        print(f"preflight: configuration refused: {exc}", file=sys.stderr)
        return 2
    scenario = run_scenario(env)
    print(scenario.summary())
    ok = scenario.ok
    if not args.offline:
        live = check_live(cfg)
        print(live.summary())
        ok = ok and live.ok
    print(f"preflight: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
