from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone

from dealbot import __version__
from dealbot.config import load_config
from dealbot.http import Http
from dealbot.models import Alert, Deal
from dealbot.runner import build_notifiers, build_sources, run_once
from dealbot.store import Store


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def cmd_run(args, cfg) -> int:
    res = run_once(cfg, dry_run=args.dry_run)
    print(f"fetched={res.fetched} scored={res.scored} new_alerts={len(res.alerts)} "
          f"already_alerted={res.skipped_seen} errors={len(res.source_errors)}")
    return 0


def cmd_loop(args, cfg) -> int:
    interval = (args.interval or cfg.get("interval_minutes", 10)) * 60
    while True:
        started = time.monotonic()
        try:
            res = run_once(cfg)
            logging.info("pass done: fetched=%d new_alerts=%d", res.fetched, len(res.alerts))
        except Exception:  # noqa: BLE001
            logging.exception("pass failed")
        time.sleep(max(5.0, interval - (time.monotonic() - started)))


def cmd_sources(args, cfg) -> int:
    http = Http()
    enabled = {s.name for s in build_sources(cfg, http)}
    from dealbot.sources import REGISTRY
    for name in REGISTRY:
        opts = (cfg.get("sources") or {}).get(name)
        state = "enabled" if name in enabled else ("missing keys" if opts else "not configured")
        print(f"{name:<12} {state}")
    print()
    for n in build_notifiers(cfg, http):
        print(f"notifier {n.name}: ready")
    return 0


def cmd_test_notify(args, cfg) -> int:
    deal = Deal(title="TEST: Sony WH-1000XM5 Headphones $39.99 (reg $399.99)",
                url="https://www.bestbuy.com/site/test.p?skuId=0000", source="test",
                price=39.99, list_price=399.99)
    alert = Alert(deal, 90, ["90% off ($39.99 vs $399.99)", "looks like a decimal-point slip"])
    ns = build_notifiers(cfg, Http())
    if not ns:
        print("no notifiers configured; set webhook/env vars in .env", file=sys.stderr)
        return 1
    for n in ns:
        n.send([alert])
        print(f"sent test alert via {n.name}")
    return 0


def cmd_history(args, cfg) -> int:
    with Store(cfg.get("db_path", "data/dealbot.db")) as store:
        for title, url, score, ts in store.recent_alerts(args.limit):
            when = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            print(f"{when}  [{score:>3}] {title}\n{' ' * 24}{url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dealbot", description="Scour deal feeds and retailers for pricing errors.")
    p.add_argument("-c", "--config", default="config.yaml")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="one pass over every enabled source")
    r.add_argument("--dry-run", action="store_true", help="score and print, but don't notify or save state")
    r.set_defaults(fn=cmd_run)

    lp = sub.add_parser("loop", help="run forever on an interval")
    lp.add_argument("--interval", type=int, help="minutes between passes (default from config)")
    lp.set_defaults(fn=cmd_loop)

    sub.add_parser("sources", help="show which sources/notifiers are enabled").set_defaults(fn=cmd_sources)
    sub.add_parser("test-notify", help="send a fake alert through every notifier").set_defaults(fn=cmd_test_notify)
    h = sub.add_parser("history", help="show recent alerts")
    h.add_argument("--limit", type=int, default=20)
    h.set_defaults(fn=cmd_history)

    args = p.parse_args(argv)
    _setup_logging(args.verbose)
    cfg = load_config(args.config)
    return args.fn(args, cfg)
