"""Run the desk.

    python -m desk.run --env-file .env.desk                 # 24/7, real block clock
    python -m desk.run --mode shadow --fast --blocks 200    # keyless dry run against the stub judge

Paper trading only. There is no live broker in this repository.
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time

from book.bench import Bench
from book.book import Book
from broker import make_broker
from desk.clock import BlockClock
from desk.config import ConfigError, DeskConfig, assert_desk_cannot_see_jev_key, load_env_file
from desk.desk import Desk
from desk.modes import make_executor
from desk.persist import load_checkpoint
from feed import make_feed
from judge.client import Backoff, make_judge
from logs.redact import Redactor
from logs.writer import LogWriter
from outcomes.resolver import OutcomeResolver
from questions import load_battery
from risk.gate import RiskGate
from trials.fingerprint import strategy_spec
from trials.registry import TrialRegistry


def build_desk(cfg: DeskConfig, *, start_ms: int, judge=None) -> tuple[Desk, LogWriter]:
    """Wire every component. `judge` can be injected (tests); by default it comes from JUDGE_URL."""
    assert_desk_cannot_see_jev_key(os.environ)
    log = LogWriter(cfg.log_dir, Redactor([cfg.desk_secret]))
    feed = make_feed(cfg.feed, cfg.symbols, start_ms=start_ms - cfg.warmup_blocks * cfg.block_ms, replay_path=cfg.replay_path, seed=cfg.synthetic_seed, tick_ms=cfg.synthetic_tick_ms, base_url=cfg.feed_base_url, poll_ms=cfg.feed_poll_ms)
    if hasattr(feed, "start"):
        feed.start()
    battery = load_battery(cfg.bot)
    registry = TrialRegistry(cfg.trials_file)
    spec = strategy_spec(cfg, battery)
    trial = registry.register_run(spec, mode=cfg.mode, ts_ms=start_ms)
    log.write("trial", {"trial_id": trial.trial_id, "spec": spec, "run": trial.runs, "mode": cfg.mode, "registered_trials": registry.count()}, ts_ms=start_ms)
    gate = RiskGate(cfg.limits)
    broker = make_broker("paper", gate, cash_usd=cfg.paper_cash_usd, fee_bps=cfg.fee_bps, maker_fee_bps=cfg.maker_fee_bps, gas_usd=cfg.gas_usd, slippage_bps=cfg.paper_slippage_bps)
    desk = Desk(
        cfg,
        feed=feed,
        gate=gate,
        broker=broker,
        book=Book(),
        bench=Bench(),
        battery=battery,
        judge=judge if judge is not None else make_judge(cfg.judge_url, cfg.desk_secret, model=cfg.jev_model),
        backoff=Backoff(),
        resolver=OutcomeResolver(log, block_ms=cfg.block_ms),
        executor=make_executor(cfg.mode, broker, log),
        log=log,
        trial_id=trial.trial_id,
    )
    desk.warmup(start_ms)
    return desk, log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dealbot desk (paper trading only)")
    parser.add_argument("--env-file", help="KEY=VALUE file; real environment variables take precedence")
    parser.add_argument("--mode", choices=("shadow", "paper"))
    parser.add_argument("--bot", choices=("gambler", "house", "spy"))
    parser.add_argument("--feed", choices=("synthetic", "replay", "coinbase"))
    parser.add_argument("--symbols", help="comma separated")
    parser.add_argument("--judge-url")
    parser.add_argument("--blocks", type=int, default=None, help="stop after N blocks (default: run forever)")
    parser.add_argument("--fast", action="store_true", help="do not wait for wall-clock blocks (dev and replay)")
    parser.add_argument("--start-ms", type=int, default=None, help="first block timestamp (default: now, aligned)")
    parser.add_argument("--state-file", default=None, help="checkpoint after every block and resume from it (default: off)")
    parser.add_argument("--no-resume", action="store_true", help="with --state-file: start fresh, overwriting the checkpoint")
    args = parser.parse_args(argv)

    env: dict[str, str] = {}
    if args.env_file:
        env.update(load_env_file(args.env_file))
    env.update(os.environ)
    overrides = {"DESK_MODE": args.mode, "DESK_BOT": args.bot, "FEED": args.feed, "DESK_SYMBOLS": args.symbols, "JUDGE_URL": args.judge_url}
    try:
        cfg = DeskConfig.from_env(env, overrides)
        if cfg.feed == "coinbase" and args.fast:
            raise ConfigError("--fast makes no sense with a live feed; the block clock must run in real time")
        if args.start_ms is not None:
            start_ms = args.start_ms
        else:
            now = int(time.time() * 1000)
            start_ms = now - now % cfg.block_ms + cfg.block_ms
        desk, log = build_desk(cfg, start_ms=start_ms)
        start_number = 0
        if args.state_file:
            checkpoint = None if args.no_resume else load_checkpoint(args.state_file)
            if checkpoint is not None:
                desk.restore(checkpoint)
                start_number = int(checkpoint.get("last_block") or -1) + 1
                print(f"desk: resumed from {args.state_file} (saved block {checkpoint.get('last_block')}, position={checkpoint['book'].get('position')})")
            desk.enable_checkpoints(args.state_file)
    except (ConfigError, ValueError, OSError) as exc:
        print(f"desk: {exc}", file=sys.stderr)
        return 2

    stop = {"requested": False}

    def request_stop(signum, frame) -> None:  # noqa: ARG001
        stop["requested"] = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, request_stop)

    print(f"desk: mode={cfg.mode} bot={cfg.bot} symbols={','.join(cfg.symbols)} feed={cfg.feed} judge={cfg.judge_url} model={cfg.jev_model} log_dir={cfg.log_dir} trial={desk.trial_id}")
    clock = BlockClock(cfg.block_ms, start_ms, realtime=not args.fast, start_number=start_number)
    blocks_done = 0
    try:
        for block in clock.blocks(args.blocks):
            desk.step(block)
            blocks_done += 1
            if stop["requested"]:
                print("desk: stop requested, finished the current block")
                break
    finally:
        if hasattr(desk.feed, "close"):
            desk.feed.close()
        log.close()
    print(f"desk: {blocks_done} blocks, fault={desk.fault!r}, position={None if desk.book.position is None else desk.book.position.to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
