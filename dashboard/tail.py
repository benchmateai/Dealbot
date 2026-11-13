"""Incremental reader for the JSONL event log. Remembers byte offsets per day file, so each poll
returns only new records, and never consumes a partially written last line."""

from __future__ import annotations

import json
from pathlib import Path


class EventTailer:
    def __init__(self, log_dir: str | Path) -> None:
        self._dir = Path(log_dir)
        self._offsets: dict[Path, int] = {}
        self._partial: dict[Path, bytes] = {}

    @property
    def log_dir(self) -> Path:
        return self._dir

    def poll(self) -> list[dict]:
        out: list[dict] = []
        if not self._dir.exists():
            return out
        for path in sorted(self._dir.glob("events-*.jsonl")):
            try:
                size = path.stat().st_size
            except FileNotFoundError:
                continue
            offset = self._offsets.get(path, 0)
            if size < offset:
                offset = 0
                self._partial[path] = b""
            if size == offset:
                continue
            with open(path, "rb") as fh:
                fh.seek(offset)
                chunk = fh.read(size - offset)
            self._offsets[path] = size
            data = self._partial.get(path, b"") + chunk
            lines = data.split(b"\n")
            self._partial[path] = lines.pop()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
        return out
