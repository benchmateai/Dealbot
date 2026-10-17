"""Funnel mechanics: ordered stages, candidates, rejections, logging and benching."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from book.bench import Bench
from logs.writer import LogWriter
from policy.decide import Pick
from state.snapshot import Snapshot


@dataclass(frozen=True)
class Candidate:
    sym: str
    snapshot: Snapshot
    state: dict
    reference_mid: float | None = None
    cost_bps: float = 0.0
    decision_id: str = ""
    answers: dict | None = None
    judge: dict | None = None
    pick: Pick | None = None


@dataclass(frozen=True)
class Rejection:
    sym: str
    stage: str
    check: str
    detail: str

    def to_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class FunnelContext:
    block: int
    now_ms: int
    deadline_ms: int
    bot: str
    phase: str
    mode: str
    equity_usd: float
    day_pnl_usd: float
    position_units: float = 0.0
    position: object | None = None
    bench: Bench | None = None
    log: LogWriter | None = None
    on_labeled: Callable[[Candidate], None] | None = None
    fault: str | None = None
    rejections: list[Rejection] = field(default_factory=list)

    def decision_id(self, sym: str) -> str:
        return f"{self.bot}-{self.block}-{sym}"

    def reject(self, rejection: Rejection) -> None:
        self.rejections.append(rejection)
        if self.log is not None:
            self.log.write("rejection", {**rejection.to_dict(), "blk": self.block, "bot": self.bot, "phase": self.phase}, ts_ms=self.now_ms)
        if self.bench is not None and rejection.check != "benched":
            self.bench.bench(rejection.sym, rejection.check, block=self.block, now_ms=self.now_ms)


class Stage(Protocol):
    name: str

    def run(self, candidates: list[Candidate], ctx: FunnelContext) -> tuple[list[Candidate], list[Rejection]]: ...


@dataclass(frozen=True)
class StageCount:
    stage: str
    entered: int
    survived: int


@dataclass(frozen=True)
class FunnelResult:
    survivors: list[Candidate]
    rejections: list[Rejection]
    counts: list[StageCount]


class Funnel:
    def __init__(self, stages: Sequence[Stage]) -> None:
        names = [s.name for s in stages]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate stage names: {names}")
        self._stages = list(stages)

    @property
    def stage_names(self) -> list[str]:
        return [s.name for s in self._stages]

    def run(self, candidates: list[Candidate], ctx: FunnelContext) -> FunnelResult:
        rejections: list[Rejection] = []
        counts: list[StageCount] = []
        current = list(candidates)
        for stage in self._stages:
            if not current:
                break
            survivors, rejected = stage.run(current, ctx)
            for r in rejected:
                ctx.reject(r)
            rejections.extend(rejected)
            counts.append(StageCount(stage.name, len(current), len(survivors)))
            current = survivors
        return FunnelResult(current, rejections, counts)
