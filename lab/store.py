"""Hour-sliced JSONL store: lab/data/<YYYY-MM-DD>/<HH>.jsonl while the hour is open, gzipped to <HH>.jsonl.gz
once it closes, so a committed file never changes again (a restart inside an hour appends a second gzip
member, which readers handle)."""

from __future__ import annotations

import calendar
import gzip
import json
import time
from collections.abc import Iterable, Iterator
from pathlib import Path


def _hour_path(root: Path, ts_ms: int) -> Path:
    t = time.gmtime(ts_ms / 1000)
    return root / time.strftime("%Y-%m-%d", t) / f"{t.tm_hour:02d}.jsonl"


class LabStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._fh = None
        self._path: Path | None = None

    def write(self, kind: str, record: dict, *, ts_ms: int) -> None:
        path = _hour_path(self.root, int(ts_ms))
        if path != self._path:
            previous = self._path
            self._open(path)
            if previous is not None and previous.exists():
                seal(previous)  # the hour is over: from here on its file never changes
        self._fh.write(json.dumps({"ts": int(ts_ms), "kind": kind, **record}, separators=(",", ":"), allow_nan=False) + "\n")
        self._fh.flush()

    def _open(self, path: Path) -> None:
        self.close()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "a", encoding="utf-8")
        self._path = path

    def seal_closed_hours(self) -> list[Path]:
        """Gzip every plain hour file except the one being written; returns the sealed .gz paths."""
        sealed = []
        for p in sorted(self.root.glob("*/*.jsonl")):
            if p != self._path:
                sealed.append(seal(p))
        return sealed

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None
            self._path = None


def seal(path: Path) -> Path:
    gz = path.with_name(path.name + ".gz")
    with open(path, "rb") as src, gzip.open(gz, "ab") as dst:
        dst.write(src.read())
    path.unlink()
    return gz


def read_lab(root: str | Path, *, since_ms: int = 0, until_ms: int | None = None, kinds: Iterable[str] | None = None) -> Iterator[dict]:
    """Records from every hour file (sealed or open) in time order of the hours, skipping a partial last line."""
    wanted = set(kinds) if kinds else None
    root = Path(root)
    files = sorted(set(root.glob("*/*.jsonl.gz")) | set(root.glob("*/*.jsonl")), key=lambda p: (p.parent.name, p.name.split(".")[0], p.suffix != ".gz"))
    for p in files:
        hour_start = calendar.timegm(time.strptime(f"{p.parent.name} {p.name[:2]}", "%Y-%m-%d %H")) * 1000
        if until_ms is not None and hour_start >= until_ms or hour_start + 3_600_000 <= since_ms:
            continue
        opener = gzip.open if p.suffix == ".gz" else open
        try:
            with opener(p, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = rec.get("ts")
                    if not isinstance(ts, int) or ts < since_ms or (until_ms is not None and ts >= until_ms):
                        continue
                    if wanted is None or rec.get("kind") in wanted:
                        yield rec
        except (EOFError, OSError):
            continue  # a gzip member cut off mid-write
