"""One pass: fetch from every enabled source, score, dedupe, notify."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from dealbot import notifiers as notif_mod
from dealbot import sources as src_mod
from dealbot.config import detector_config
from dealbot.detector import Detector
from dealbot.http import Http
from dealbot.models import Alert, Deal
from dealbot.store import Store

log = logging.getLogger("dealbot")


@dataclass
class RunResult:
    fetched: int = 0
    scored: int = 0
    alerts: list[Alert] = field(default_factory=list)
    skipped_seen: int = 0
    source_errors: list[str] = field(default_factory=list)


def build_sources(cfg: dict[str, Any], http: Http) -> list[src_mod.Source]:
    out = []
    for name, opts in (cfg.get("sources") or {}).items():
        opts = opts or {}
        if not opts.get("enabled", True):
            continue
        cls = src_mod.REGISTRY.get(name)
        if cls is None:
            log.warning("unknown source %r (known: %s)", name, ", ".join(src_mod.REGISTRY))
            continue
        src = cls(http, opts)
        missing = src.missing_requirements()
        if missing:
            log.info("source %s disabled: missing %s", name, ", ".join(missing))
            continue
        out.append(src)
    return out


def build_notifiers(cfg: dict[str, Any], http: Http) -> list[notif_mod.Notifier]:
    out = []
    for name, opts in (cfg.get("notifiers") or {}).items():
        opts = opts or {}
        if not opts.get("enabled", True):
            continue
        cls = notif_mod.REGISTRY.get(name)
        if cls is None:
            log.warning("unknown notifier %r (known: %s)", name, ", ".join(notif_mod.REGISTRY))
            continue
        n = cls(http, opts)
        missing = n.missing_requirements()
        if missing:
            log.info("notifier %s disabled: missing %s", name, ", ".join(missing))
            continue
        out.append(n)
    return out


def run_once(cfg: dict[str, Any], dry_run: bool = False, http: Http | None = None) -> RunResult:
    http = http or Http(min_interval=float(cfg.get("http", {}).get("min_interval_seconds", 1.0)))
    detector = Detector(detector_config(cfg))
    result = RunResult()
    sources = build_sources(cfg, http)
    if not sources:
        log.warning("no sources enabled; check config")
    seen_this_run: set[str] = set()

    with Store(cfg.get("db_path", "data/dealbot.db")) as store:
        for src in sources:
            try:
                deals: list[Deal] = list(src.fetch())
            except Exception as e:  # noqa: BLE001
                log.exception("source %s crashed", src.name)
                result.source_errors.append(f"{src.name}: {e}")
                continue
            result.fetched += len(deals)
            for deal in deals:
                if deal.key in seen_this_run:
                    continue
                seen_this_run.add(deal.key)
                alert = detector.score(deal, prior_low=store.prior_low(deal))
                result.scored += 1
                is_alert = detector.is_alert(alert)
                already = store.was_alerted(deal)
                if is_alert and already:
                    result.skipped_seen += 1
                if not dry_run:
                    store.record(deal, alert.score, alerted=is_alert and not already)
                if is_alert and not already:
                    result.alerts.append(alert)
                    log.info("ALERT %d %s", alert.score, deal.title)
                else:
                    log.debug("score %d %s", alert.score, deal.title)
        if not dry_run:
            store.prune(int(cfg.get("prune_days", 30)))

    result.alerts.sort(key=lambda a: a.score, reverse=True)
    cap = int(cfg.get("max_alerts_per_run", 25))
    to_send = result.alerts[:cap]
    if to_send and not dry_run:
        for n in build_notifiers(cfg, http):
            try:
                n.send(to_send)
            except Exception:  # noqa: BLE001
                log.exception("notifier %s failed", n.name)
    elif to_send:
        notif_mod.Console(http).send(to_send)
    return result
