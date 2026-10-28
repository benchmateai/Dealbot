"""Checkpoints: the paper account, the book, the bench, pending outcomes, the block counter and a
tail of recent ticks, saved after every block so an unattended run survives a restart. JSON, atomic."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

STATE_VERSION = 1


def save_checkpoint(path: str | Path, data: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".state-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"version": STATE_VERSION, **data}, fh, separators=(",", ":"))
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_checkpoint(path: str | Path) -> dict | None:
    target = Path(path)
    if not target.exists():
        return None
    with open(target, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("version") != STATE_VERSION:
        raise ValueError(f"checkpoint {target} has version {data.get('version')}, expected {STATE_VERSION}")
    return data
