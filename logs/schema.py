"""Record kinds and the keys each must carry. Kept small on purpose; extra keys are always allowed."""

from __future__ import annotations

from collections.abc import Mapping

KINDS: dict[str, tuple[str, ...]] = {
    "snapshot": ("decision_id", "sym", "snapshot"),
    "question": ("decision_id", "battery_version"),
    "answer": ("decision_id", "model", "answers"),
    "decision": ("decision_id", "action", "approved"),
    "veto": ("decision_id", "check"),
    "rejection": ("sym", "stage", "check"),
    "order": ("decision_id", "order", "status"),
    "fill": ("order_id", "sym", "side", "qty", "price"),
    "outcome": ("decision_id", "qid", "qkind", "status"),
    "heartbeat": ("blk",),
    "trial": ("trial_id", "spec"),
    "would_execute": ("decision_id", "order"),
    "position_opened": ("decision_id", "sym"),
    "position_closed": ("decision_id", "sym"),
    "order_expired": ("order_id",),
    "error": ("where",),
}


class LogSchemaError(ValueError):
    pass


def check_record(kind: str, record: Mapping) -> None:
    required = KINDS.get(kind)
    if required is None:
        raise LogSchemaError(f"unknown log kind {kind!r}")
    missing = [k for k in required if k not in record]
    if missing:
        raise LogSchemaError(f"{kind} record is missing {missing}")
    for reserved in ("ts", "kind"):
        if reserved in record:
            raise LogSchemaError(f"{reserved!r} is set by the writer")
