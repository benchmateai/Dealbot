"""Desk-side judge client. Carries the desk secret only; never sees the Jev key.

- The call carries the block deadline; if the deadline has already passed the call is not made and
  the desk holds. A late answer is discarded.
- A rate limit answer starts an exponential backoff (honoring retry-after); the desk holds meanwhile.
- A malformed-question answer is never retried: it is a bug in the battery, so the desk holds until
  the battery is fixed and the process restarted.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from judge.jev import STUB_MODEL, StubBackend
from judge.protocol import JUDGE_PATH, SECRET_HEADER, request_body


class JudgeError(Exception):
    def __init__(self, message: str, *, code: str = "judge_error", status: int | None = None, retryable: bool = False, retry_after_ms: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.retryable = retryable
        self.retry_after_ms = retry_after_ms


class JudgeTimeout(JudgeError):
    pass


class JudgeRateLimited(JudgeError):
    pass


class JudgeMalformed(JudgeError):
    pass


class JudgeUnavailable(JudgeError):
    pass


class JudgeAuthError(JudgeError):
    pass


@dataclass(frozen=True)
class JudgeAnswer:
    decision_id: str
    model: str
    requested_model: str | None
    answers: dict[str, dict]
    usage: dict | None
    request_id: str | None
    latency_ms: int | None
    backend: str | None

    def to_dict(self) -> dict:
        return {"model": self.model, "requested_model": self.requested_model, "request_id": self.request_id, "latency_ms": self.latency_ms, "usage": self.usage, "backend": self.backend}


class Judge(Protocol):
    def ask(self, *, decision_id: str, bot: str, state: dict, questions: dict, deadline_ms: int, now_ms: int) -> JudgeAnswer: ...


def _map_status(status: int, payload: dict) -> JudgeError:
    code = str(payload.get("error") or "judge_error")
    detail = str(payload.get("detail") or "")
    retry_after = payload.get("retry_after_ms")
    message = f"judge {status} {code}: {detail}" if detail else f"judge {status} {code}"
    if status in (401, 403):
        return JudgeAuthError(message, code=code, status=status)
    if status == 400:
        return JudgeMalformed(message, code=code, status=status, retryable=False)
    if status == 429:
        return JudgeRateLimited(message, code=code, status=status, retryable=True, retry_after_ms=None if retry_after is None else int(retry_after))
    if status == 504:
        return JudgeTimeout(message, code=code, status=status, retryable=True)
    return JudgeUnavailable(message, code=code, status=status, retryable=bool(payload.get("retryable", True)))


class HttpJudge:
    def __init__(self, url: str, desk_secret: str, *, min_remaining_ms: int = 200) -> None:
        if not desk_secret:
            raise ValueError("the desk secret is required to call the judge")
        self._url = url.rstrip("/") + JUDGE_PATH
        self._secret = desk_secret
        self._min_remaining = min_remaining_ms

    def ask(self, *, decision_id: str, bot: str, state: dict, questions: dict, deadline_ms: int, now_ms: int) -> JudgeAnswer:
        remaining = deadline_ms - now_ms
        if remaining <= self._min_remaining:
            raise JudgeTimeout(f"deadline already passed ({remaining} ms left); holding", code="deadline_passed", retryable=False)
        body = json.dumps(request_body(decision_id=decision_id, bot=bot, state=state, questions=questions, deadline_ms=remaining)).encode()
        request = urllib.request.Request(self._url, data=body, headers={"Content-Type": "application/json", SECRET_HEADER: self._secret}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=remaining / 1000) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode() or "{}")
            except ValueError:
                payload = {}
            raise _map_status(exc.code, payload if isinstance(payload, dict) else {}) from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                raise JudgeTimeout("judge call timed out before the deadline; holding", code="timeout", retryable=True) from None
            raise JudgeUnavailable(f"judge unreachable: {exc.reason}", code="unreachable", retryable=True) from None
        except (socket.timeout, TimeoutError):
            raise JudgeTimeout("judge call timed out before the deadline; holding", code="timeout", retryable=True) from None
        return JudgeAnswer(
            decision_id=str(payload.get("decision_id", decision_id)),
            model=str(payload["model"]),
            requested_model=payload.get("requested_model"),
            answers=payload["answers"],
            usage=payload.get("usage"),
            request_id=payload.get("request_id"),
            latency_ms=payload.get("latency_ms"),
            backend=payload.get("backend"),
        )


class LocalStubJudge:
    """In-process stub for keyless dry runs (JUDGE_URL=stub://local). Same protocol, no network."""

    def __init__(self, model: str = STUB_MODEL) -> None:
        self._backend = StubBackend(model)

    def ask(self, *, decision_id: str, bot: str, state: dict, questions: dict, deadline_ms: int, now_ms: int) -> JudgeAnswer:
        if deadline_ms - now_ms <= 0:
            raise JudgeTimeout("deadline already passed; holding", code="deadline_passed")
        raw = self._backend.ask(state, questions, timeout_s=(deadline_ms - now_ms) / 1000)
        return JudgeAnswer(decision_id, raw.model, self._backend.model, raw.answers, raw.usage, raw.request_id, raw.latency_ms, "stub")


class Backoff:
    """Exponential backoff after rate limits, honoring the server's retry-after when given."""

    def __init__(self, *, base_ms: int = 2_000, max_ms: int = 120_000) -> None:
        self._base = base_ms
        self._max = max_ms
        self.consecutive = 0
        self.blocked_until_ms = 0

    def note_rate_limited(self, now_ms: int, retry_after_ms: int | None = None) -> int:
        self.consecutive += 1
        delay = retry_after_ms if retry_after_ms else min(self._max, self._base * 2 ** (self.consecutive - 1))
        self.blocked_until_ms = max(self.blocked_until_ms, now_ms + delay)
        return delay

    def note_ok(self) -> None:
        self.consecutive = 0
        self.blocked_until_ms = 0

    def is_blocked(self, now_ms: int) -> bool:
        return now_ms < self.blocked_until_ms


def make_judge(url: str, desk_secret: str, *, model: str) -> Judge:
    if url.startswith("stub://"):
        return LocalStubJudge(model)
    return HttpJudge(url, desk_secret)


def now_ms() -> int:
    return int(time.time() * 1000)
