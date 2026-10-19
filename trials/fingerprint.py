"""What makes a trial: the canonical description of one strategy configuration and its id.

Everything that changes what the desk would do is in the spec: bot, battery, thresholds, weights,
edge model, risk limits, clip size, symbols, feed, block cadence, funnel cut-offs and the pinned Jev
version. Deployment details that do not change the strategy (mode, log directory, judge URL,
secrets) are left out, so a shadow run and a paper run of the same configuration are the same trial.
"""

from __future__ import annotations

import hashlib
import json

from policy.thresholds import EDGE, THRESHOLDS
from policy.weights import WEIGHTS
from questions.schema import Battery


def strategy_spec(cfg, battery: Battery) -> dict:
    bot = cfg.bot
    return {
        "bot": bot,
        "battery_version": battery.version(),
        "question_ids": [q.id for q in battery.questions],
        "thresholds": {action: {"wrong_bps": c.wrong_bps, "missed_bps": c.missed_bps} for action, c in THRESHOLDS[bot].items()},
        "weights": {action: [[t.qid, t.extract, t.weight, t.when] for t in terms] for action, terms in WEIGHTS[bot].items()},
        "edge": {"target_bps": EDGE[bot].target_bps, "stop_bps": EDGE[bot].stop_bps},
        "limits": cfg.limits.to_dict(),
        "symbols": list(cfg.symbols),
        "block_seconds": cfg.block_seconds,
        "order_qty": cfg.order_qty,
        "fee_bps": cfg.fee_bps,
        "maker_fee_bps": cfg.maker_fee_bps,
        "gas_usd": cfg.gas_usd,
        "paper_cash_usd": cfg.paper_cash_usd,
        "paper_slippage_bps": cfg.paper_slippage_bps,
        "ret_windows_blocks": list(cfg.ret_windows_blocks),
        "rv_window_blocks": cfg.rv_window_blocks,
        "free_cut": {"max_spread_bps": cfg.max_spread_bps, "rv_min_bps": cfg.rv_min_bps, "rv_max_bps": cfg.rv_max_bps, "min_ticks": cfg.min_ticks, "max_stale_ms": cfg.max_stale_ms},
        "max_jev_candidates": cfg.max_jev_candidates,
        "max_feed_lag_ms": cfg.max_feed_lag_ms,
        "min_equity_usd": cfg.min_equity_usd,
        "deadline_margin_frac": cfg.deadline_margin_frac,
        "pending_order_ttl_blocks": cfg.pending_order_ttl_blocks,
        "warmup_blocks": cfg.warmup_blocks,
        "heartbeat_every_blocks": cfg.heartbeat_every_blocks,
        "jev_model": cfg.jev_model,
        "feed": {"kind": cfg.feed, "replay_path": cfg.replay_path, "synthetic_seed": cfg.synthetic_seed, "synthetic_tick_ms": cfg.synthetic_tick_ms},
    }


def trial_id(spec: dict) -> str:
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()[:16]
