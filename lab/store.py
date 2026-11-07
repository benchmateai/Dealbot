"""Hour-sliced JSONL store: lab/data/<YYYY-MM-DD>/<HH>.jsonl while the hour is open, gzipped to <HH>.jsonl.gz
once it closes, so a committed file never changes again (a restart inside an hour appends a second gzip
member, which readers handle). A second writer names its own stream (<HH>.<stream>.jsonl), so two
recorders never append to, or seal, each other's files; readers take every stream.

Sealing is atomic (the .gz is rebuilt beside itself and swapped in, so a kill at any moment leaves the
old .gz or the new one, never a cut member) and, at an hour's end, runs in a thread so a live feed never
stalls on it. A line cut off by a kill is ended before the next record is appended."""

from __future__ import annotations

import calendar
import gzip
import json
import os
import shutil
import threading
import time
import zlib
from collections.abc import Iterable, Iterator
from pathlib import Path


def _hour_path(root: Path, ts_ms: int, stream: str = "") -> Path:
    t = time.gmtime(ts_ms / 1000)
    return root / time.strftime("%Y-%m-%d", t) / f"{t.tm_hour:02d}{'.' + stream if stream else ''}.jsonl"


class LabStore:
    def __init__(self, root: str | Path, *, stream: str = "") -> None:
        self.root = Path(root)
        self.stream = stream
        self._fh = None
        self._path: Path | None = None
        self._sealing: dict[Path, threading.Thread] = {}

    def write(self, kind: str, record: dict, *, ts_ms: int) -> None:
        path = _hour_path(self.root, int(ts_ms), self.stream)
        if path != self._path:
            previous = self._path
            self._open(path)
            if previous is not None and previous.exists():
                self._seal_later(previous)  # the hour is over: from here on its file never changes
        self._fh.write(json.dumps({"ts": int(ts_ms), "kind": kind, **record}, separators=(",", ":"), allow_nan=False) + "\n")
        self._fh.flush()

    def _seal_later(self, path: Path) -> None:
        thread = threading.Thread(target=seal, args=(path,), name=f"seal {path.name}")
        self._sealing[path] = thread
        thread.start()

    def wait_sealed(self, path: Path | None = None) -> None:
        for p in [path] if path is not None else list(self._sealing):
            thread = self._sealing.pop(p, None)
            if thread is not None:
                thread.join()

    def _open(self, path: Path) -> None:
        self.close()
        self.wait_sealed(path)  # a clock that stepped back into an hour being sealed
        path.parent.mkdir(parents=True, exist_ok=True)
        cut = False
        if path.exists() and path.stat().st_size:
            with open(path, "rb") as fh:
                fh.seek(-1, os.SEEK_END)
                cut = fh.read(1) != b"\n"
        self._fh = open(path, "a", encoding="utf-8")
        if cut:
            self._fh.write("\n")  # end the line a kill cut off, so the next record is not lost with it
        self._path = path

    def seal_closed_hours(self) -> list[Path]:
        """Gzip every plain hour file of this stream except the one being written; returns the sealed .gz paths."""
        self.wait_sealed()
        sealed = []
        for p in sorted(self.root.glob(f"*/[0-9][0-9]{'.' + self.stream if self.stream else ''}.jsonl")):
            if p != self._path:
                sealed.append(seal(p))
        return sealed

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None
            self._path = None


def seal(path: Path) -> Path:
    """Append `path` to its .gz as one more gzip member, atomically, then remove it."""
    gz = path.with_name(path.name + ".gz")
    tmp = gz.with_name(gz.name + ".tmp")
    with open(tmp, "wb") as out:
        if gz.exists():
            with open(gz, "rb") as old:
                shutil.copyfileobj(old, out)
        with open(path, "rb") as src, gzip.GzipFile(fileobj=out, mode="wb", compresslevel=6, mtime=0) as member:
            shutil.copyfileobj(src, member)
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, gz)
    path.unlink()
    return gz


def read_lab(root: str | Path, *, since_ms: int = 0, until_ms: int | None = None, kinds: Iterable[str] | None = None) -> Iterator[dict]:
    """Records from every hour file (sealed or open) in time order of the hours, skipping a partial last line.
    With `kinds`, a line the store wrote (compact JSON) for another kind is passed over unparsed: most of a
    recording is trades and index values that a replay of books does not read."""
    wanted = set(kinds) if kinds else None
    needles = tuple(f'"kind":"{k}"' for k in wanted) if wanted else ()
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
                    if needles and '"kind":"' in line and not any(n in line for n in needles):
                        continue  # some other kind; a line in any other layout is parsed and checked below
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = rec.get("ts")
                    if not isinstance(ts, int) or ts < since_ms or (until_ms is not None and ts >= until_ms):
                        continue
                    if wanted is None or rec.get("kind") in wanted:
                        yield rec
        except (EOFError, OSError, zlib.error):
            continue  # a gzip member cut off mid-write (sealing is atomic now, but older files may hold one)
