"""Question schema and battery validation.

Questions are stored in the TypeSafe wire format (`{"type": "noul"|"choice"|"score", ...}`) so the
desk never imports the SDK; the judge hands the dictionaries to `client.system_one` unchanged.

Rules enforced at construction time (fail fast, at import):
- one judgment per question: instructions are a single sentence with exactly one "?" at the end;
- every Choice has an "other" option;
- ids are snake_case and unique within a battery;
- a resolution names a known rule of the matching kind, so every graded answer can be scored later.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from outcomes.rules import RULES, parse_param

OTHER = "other"
OTHER_TEXT = "None of the listed outcomes fits, or `mkt` is too ambiguous or anomalous to say."
MAX_INSTRUCTION_CHARS = 400
_ID = re.compile(r"^[a-z][a-z0-9_]{0,40}$")


class BatteryError(ValueError):
    pass


@dataclass(frozen=True)
class Resolution:
    rule: str
    horizon_blocks: int
    param: float | str = "cost"


@dataclass(frozen=True)
class ChoiceQ:
    kind: ClassVar[str] = "choice"
    id: str
    instructions: str
    criteria: Mapping[str, str | None]
    resolution: Resolution | None = None

    def wire(self) -> dict:
        return {"type": "choice", "instructions": self.instructions, "criteria": dict(self.criteria)}


@dataclass(frozen=True)
class NoulQ:
    kind: ClassVar[str] = "noul"
    id: str
    instructions: str
    true: str | None = None
    false: str | None = None
    resolution: Resolution | None = None

    def wire(self) -> dict:
        q: dict = {"type": "noul", "instructions": self.instructions}
        criteria = {k: v for k, v in (("true", self.true), ("false", self.false)) if v is not None}
        if criteria:
            q["criteria"] = criteria
        return q


@dataclass(frozen=True)
class ScoreQ:
    kind: ClassVar[str] = "score"
    id: str
    instructions: str
    levels: tuple[str, ...]
    resolution: Resolution | None = None

    def wire(self) -> dict:
        return {"type": "score", "instructions": self.instructions, "criteria": list(self.levels)}


Question = ChoiceQ | NoulQ | ScoreQ


def _validate_instructions(qid: str, text: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise BatteryError(f"{qid}: instructions must be a non-empty string")
    if len(text) > MAX_INSTRUCTION_CHARS:
        raise BatteryError(f"{qid}: instructions longer than {MAX_INSTRUCTION_CHARS} chars")
    if text.count("?") != 1 or not text.rstrip().endswith("?"):
        raise BatteryError(f"{qid}: one judgment per question; instructions must contain exactly one '?' and end with it")


def _validate_question(q: Question) -> None:
    if not _ID.match(q.id):
        raise BatteryError(f"{q.id!r}: ids must be snake_case, 1-41 chars")
    _validate_instructions(q.id, q.instructions)
    if isinstance(q, ChoiceQ):
        if not isinstance(q.criteria, Mapping) or len(q.criteria) < 2:
            raise BatteryError(f"{q.id}: a Choice needs at least two options")
        for label, desc in q.criteria.items():
            if not _ID.match(label):
                raise BatteryError(f"{q.id}: option label {label!r} must be snake_case")
            if desc is not None and (not isinstance(desc, str) or not desc.strip()):
                raise BatteryError(f"{q.id}: option {label!r} description must be text or None")
        if OTHER not in q.criteria:
            raise BatteryError(f"{q.id}: every Choice must have an {OTHER!r} option")
    elif isinstance(q, NoulQ):
        for name, desc in (("true", q.true), ("false", q.false)):
            if desc is not None and (not isinstance(desc, str) or not desc.strip()):
                raise BatteryError(f"{q.id}: {name} description must be text or None")
    elif isinstance(q, ScoreQ):
        if not isinstance(q.levels, tuple) or len(q.levels) < 2 or not all(isinstance(l, str) and l.strip() for l in q.levels):
            raise BatteryError(f"{q.id}: a Score needs at least two non-empty levels, as a tuple")
    else:
        raise BatteryError(f"{q!r}: unknown question type")
    res = q.resolution
    if res is not None:
        spec = RULES.get(res.rule)
        if spec is None:
            raise BatteryError(f"{q.id}: unknown outcome rule {res.rule!r}")
        if spec.kind != q.kind:
            raise BatteryError(f"{q.id}: rule {res.rule!r} grades a {spec.kind} question, not a {q.kind}")
        if not isinstance(res.horizon_blocks, int) or res.horizon_blocks < 1:
            raise BatteryError(f"{q.id}: horizon_blocks must be a positive integer")
        try:
            parse_param(res.param, cost_bps=1.0, rv_bps=1.0)
        except ValueError as exc:
            raise BatteryError(f"{q.id}: {exc}") from exc


@dataclass(frozen=True)
class Battery:
    bot: str
    questions: tuple[Question, ...]

    def __post_init__(self) -> None:
        if not self.questions:
            raise BatteryError(f"{self.bot}: a battery needs at least one question")
        seen: set[str] = set()
        for q in self.questions:
            _validate_question(q)
            if q.id in seen:
                raise BatteryError(f"{self.bot}: duplicate question id {q.id!r}")
            seen.add(q.id)

    def wire(self) -> dict[str, dict]:
        """Questions keyed by id, in battery order, in the TypeSafe wire format."""
        return {q.id: q.wire() for q in self.questions}

    def by_id(self) -> dict[str, Question]:
        return {q.id: q for q in self.questions}

    def version(self) -> str:
        payload = json.dumps(self.wire(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()[:12]
