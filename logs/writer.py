"""JSONL writer: one file per UTC day, every record stamped with ts and kind, every value redacted."""

from __future__ import annotations

import dataclasses
import json
import math
import time
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from logs.redact import Redactor
from logs.schema import check_record


def _clean(obj):
    if hasattr(obj, "to_dict"):
        return _clean(obj.to_dict())
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _clean(dataclasses.asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_clean(v) for v in (sorted(obj) if isinstance(obj, (set, frozenset)) else obj)]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def _day(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


class LogWriter:
    def __init__(self, directory: str | Path, redactor: Redactor | None = None, *, now_ms: Callable[[], int] | None = None) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._redactor = redactor or Redactor()
        self._now = now_ms or (lambda: int(time.time() * 1000))
        self._files: dict[str, object] = {}

    @property
    def directory(self) -> Path:
        return self._dir

    def write(self, kind: str, record: dict, *, ts_ms: int | None = None) -> dict:
        check_record(kind, record)
        rec = {"ts": self._now() if ts_ms is None else int(ts_ms), "kind": kind, **record}
        rec = self._redactor.redact(_clean(rec))
        line = json.dumps(rec, sort_keys=True, separators=(",", ":"), allow_nan=False)
        fh = self._file(_day(rec["ts"]))
        fh.write(line + "\n")
        fh.flush()
        return rec

    def _file(self, day: str):
        fh = self._files.get(day)
        if fh is None:
            fh = open(self._dir / f"events-{day}.jsonl", "a", encoding="utf-8")
            self._files[day] = fh
        return fh

    def close(self) -> None:
        for fh in self._files.values():
            fh.close()
        self._files.clear()

    def __enter__(self) -> LogWriter:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def read_events(directory: str | Path, *, date: str | None = None, kinds: Iterable[str] | None = None) -> Iterator[dict]:
    wanted = set(kinds) if kinds is not None else None
    for path in sorted(Path(directory).glob("events-*.jsonl")):
        if date is not None and path.name != f"events-{date}.jsonl":
            continue
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if wanted is None or rec.get("kind") in wanted:
                    yield rec
