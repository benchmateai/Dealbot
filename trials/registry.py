"""Persistent registry of every trial ever run, keyed by the configuration fingerprint.

A JSON file next to the event log. Each entry keeps the spec, how many times it ran, in which modes,
and the latest evaluation written by `reports.trials`. The count of entries is the N that deflates
every survivor's Sharpe, which is why nothing is ever deleted from it.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from trials.fingerprint import trial_id as fingerprint_id


@dataclass
class TrialEntry:
    trial_id: str
    spec: dict
    first_seen_ms: int
    last_seen_ms: int
    runs: int = 0
    modes: list[str] = field(default_factory=list)
    evaluation: dict | None = None

    def to_dict(self) -> dict:
        return {"trial_id": self.trial_id, "spec": self.spec, "first_seen_ms": self.first_seen_ms, "last_seen_ms": self.last_seen_ms, "runs": self.runs, "modes": list(self.modes), "evaluation": self.evaluation}

    @classmethod
    def from_dict(cls, data: dict) -> TrialEntry:
        return cls(data["trial_id"], data["spec"], int(data["first_seen_ms"]), int(data["last_seen_ms"]), int(data.get("runs", 0)), list(data.get("modes", [])), data.get("evaluation"))


class TrialRegistry:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._entries: dict[str, TrialEntry] = {}
        if self._path.exists():
            with open(self._path, encoding="utf-8") as fh:
                raw = json.load(fh)
            for item in raw.get("trials", []):
                entry = TrialEntry.from_dict(item)
                self._entries[entry.trial_id] = entry

    @property
    def path(self) -> Path:
        return self._path

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "trials": [e.to_dict() for e in self.entries()]}
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, prefix=".trials-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=1, sort_keys=True)
            os.replace(tmp, self._path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def register_run(self, spec: dict, *, mode: str, ts_ms: int) -> TrialEntry:
        """Record one run of a configuration. The same spec always maps to the same trial id."""
        tid = fingerprint_id(spec)
        entry = self._entries.get(tid)
        if entry is None:
            entry = TrialEntry(tid, spec, ts_ms, ts_ms)
            self._entries[tid] = entry
        entry.runs += 1
        entry.last_seen_ms = max(entry.last_seen_ms, ts_ms)
        if mode not in entry.modes:
            entry.modes.append(mode)
        self.save()
        return entry

    def record_evaluation(self, tid: str, evaluation: dict) -> TrialEntry:
        entry = self._entries[tid]
        entry.evaluation = evaluation
        self.save()
        return entry

    def get(self, tid: str) -> TrialEntry | None:
        return self._entries.get(tid)

    def entries(self) -> list[TrialEntry]:
        return sorted(self._entries.values(), key=lambda e: (e.first_seen_ms, e.trial_id))

    def count(self) -> int:
        return len(self._entries)

    def sharpes(self) -> list[float]:
        """Per-period Sharpe of every evaluated trial, for the cross-trial variance."""
        return [e.evaluation["sharpe"] for e in self._entries.values() if e.evaluation and e.evaluation.get("sharpe") is not None]
