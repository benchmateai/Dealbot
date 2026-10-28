"""Bench for rejected candidates. The rejection reason sets how long a symbol stays benched.

Durations are in blocks, or the markers UNTIL_DAY_END (UTC midnight) and UNTIL_RESTART. A reason of
the form "prefix:detail" (for example "risk_veto:daily_loss") falls back to its prefix when there is
no exact entry.
"""

from __future__ import annotations

from dataclasses import dataclass

UNTIL_DAY_END = "day_end"
UNTIL_RESTART = "restart"
DAY_MS = 86_400_000

DEFAULT_BENCH_BLOCKS: dict[str, int | str] = {
    # free cut (data already in hand)
    "insufficient_data": 2,
    "stale_data": 1,
    "mid_invalid": 5,
    "insufficient_ticks": 2,
    "rv_unavailable": 1,
    "spread_too_wide": 5,
    "rv_out_of_band": 10,
    # one-call checks
    "feed_lagging": 2,
    "order_already_resting": 1,
    "insufficient_equity": 20,
    # hard facts in code
    "fees_exceed_best_case_edge": 30,
    "risk_precheck": 5,
    "risk_precheck:daily_loss": UNTIL_DAY_END,
    "risk_precheck:leverage": 10,
    # Jev
    "jev_budget": 1,
    "jev_backoff": 1,
    "jev_deadline_passed": 1,
    "jev_timeout": 1,
    "jev_rate_limited": 3,
    "jev_unavailable": 2,
    "battery_fault": UNTIL_RESTART,
    # final pick
    "below_threshold": 3,
    "policy_error": UNTIL_RESTART,
    "not_best": 1,
    # risk vetoes on the final order
    "risk_veto": 5,
    "risk_veto:daily_loss": UNTIL_DAY_END,
    "risk_veto:model_version": UNTIL_RESTART,
    "risk_veto:fees_plus_gas": 10,
    "risk_veto:stale_data": 1,
    "risk_veto:range_guard": 3,
}


@dataclass(frozen=True)
class BenchEntry:
    sym: str
    reason: str
    since_block: int
    until_block: int | None = None
    until_ms: int | None = None
    forever: bool = False

    def active(self, block: int, now_ms: int) -> bool:
        if self.forever:
            return True
        if self.until_block is not None and block < self.until_block:
            return True
        return self.until_ms is not None and now_ms < self.until_ms

    def to_dict(self) -> dict:
        return dict(self.__dict__)


class Bench:
    def __init__(self, durations: dict[str, int | str] | None = None, *, default_blocks: int = 3) -> None:
        self._durations = {**DEFAULT_BENCH_BLOCKS, **(durations or {})}
        self._default = default_blocks
        self._entries: dict[str, BenchEntry] = {}

    def duration_for(self, reason: str) -> int | str:
        if reason in self._durations:
            return self._durations[reason]
        prefix = reason.split(":", 1)[0]
        return self._durations.get(prefix, self._default)

    def bench(self, sym: str, reason: str, *, block: int, now_ms: int) -> BenchEntry:
        duration = self.duration_for(reason)
        if duration == UNTIL_RESTART:
            entry = BenchEntry(sym, reason, block, forever=True)
        elif duration == UNTIL_DAY_END:
            entry = BenchEntry(sym, reason, block, until_ms=(now_ms // DAY_MS + 1) * DAY_MS)
        else:
            entry = BenchEntry(sym, reason, block, until_block=block + int(duration))
        existing = self._entries.get(sym)
        if existing is not None and existing.forever and existing.active(block, now_ms):
            return existing
        self._entries[sym] = entry
        return entry

    def is_benched(self, sym: str, *, block: int, now_ms: int) -> BenchEntry | None:
        entry = self._entries.get(sym)
        if entry is None:
            return None
        if entry.active(block, now_ms):
            return entry
        del self._entries[sym]
        return None

    def expire(self, *, block: int, now_ms: int) -> list[BenchEntry]:
        released = [e for e in self._entries.values() if not e.active(block, now_ms)]
        for e in released:
            del self._entries[e.sym]
        return released

    def entries(self) -> list[BenchEntry]:
        return list(self._entries.values())

    def to_state(self) -> list[dict]:
        return [e.to_dict() for e in self._entries.values()]

    def restore_state(self, data: list[dict]) -> None:
        self._entries = {e["sym"]: BenchEntry(**e) for e in data}
