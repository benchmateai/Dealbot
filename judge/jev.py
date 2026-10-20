"""Jev adapter: the only module in this repository that imports the TypeSafe SDK. Used by the judge
service alone; the desk never imports it.

- The model is pinned: aliases such as jev-latest are refused, because an alias moves and the
  risk gate compares every decision's model string with the pinned one.
- Rate limits and 5xx are retried by the SDK with exponential backoff and Retry-After, inside a
  fixed budget. 400/422 (a malformed question) and pre-send validation errors are never retried.
- The exact model string from every response is returned raw, next to the answers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

JEV_KEY_ENV = "TYPESAFE_API_KEY"
STUB_MODEL = "stub-jev-0.0"
_ALIASES = frozenset({"jev", "jev-latest", "jev-preview"})
_PINNED = re.compile(r"^(?:jev-\d+\.\d+[A-Za-z0-9.\-]*|stub-jev-\d+\.\d+)$")


class ModelNotPinnedError(ValueError):
    pass


def ensure_pinned(model: str | None) -> str:
    name = (model or "").strip()
    if not name:
        raise ModelNotPinnedError("JEV_MODEL is required: a pinned Jev version string, never jev-latest")
    if name in _ALIASES or "latest" in name or not _PINNED.match(name):
        raise ModelNotPinnedError(f"{name!r} is not a pinned Jev version; aliases move, pin an exact name from GET /v1/models (for example jev-1.13.0)")
    return name


class JudgeFault(Exception):
    code = "judge_error"
    status = 500
    retryable = True

    def __init__(self, message: str, *, retry_after_ms: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_ms = retry_after_ms


class MalformedQuestion(JudgeFault):
    code, status, retryable = "malformed_question", 400, False


class RateLimited(JudgeFault):
    code, status, retryable = "rate_limited", 429, True


class UpstreamTimeout(JudgeFault):
    code, status, retryable = "upstream_timeout", 504, True


class UpstreamUnavailable(JudgeFault):
    code, status, retryable = "upstream_unavailable", 502, True


class UpstreamAuth(JudgeFault):
    code, status, retryable = "upstream_auth", 502, False


@dataclass(frozen=True)
class RawAnswers:
    model: str
    answers: dict[str, dict]
    usage: dict
    request_id: str | None
    latency_ms: int


class JevBackend(Protocol):
    name: str
    model: str

    def ask(self, state: Mapping, questions: Mapping[str, Mapping], *, timeout_s: float) -> RawAnswers: ...


def _unit(digest: bytes, i: int) -> float:
    return int.from_bytes(digest[4 * i : 4 * i + 4], "big") / 2**32


def _dist(digest: bytes, n: int) -> list[float]:
    raw = [_unit(digest, i + 1) + 1e-6 for i in range(n)]
    total = sum(raw)
    return [round(r / total, 4) for r in raw]


class StubBackend:
    """Deterministic pseudo-answers from a hash of (state, question id). For keyless dry runs and tests."""

    name = "stub"

    def __init__(self, model: str = STUB_MODEL) -> None:
        self.model = ensure_pinned(model)

    def ask(self, state: Mapping, questions: Mapping[str, Mapping], *, timeout_s: float) -> RawAnswers:
        t0 = time.monotonic()
        seed = json.dumps(state, sort_keys=True, separators=(",", ":"))
        answers: dict[str, dict] = {}
        for qid, q in questions.items():
            digest = hashlib.sha256(f"{seed}|{qid}".encode()).digest()
            kind = q.get("type")
            if kind == "noul":
                answers[qid] = {"type": "noul", "noul": round(_unit(digest, 0), 4)}
            elif kind == "choice":
                labels = list(q.get("criteria") or {})
                if not labels:
                    raise MalformedQuestion(f"choice question {qid!r} has no criteria")
                probs = dict(zip(labels, _dist(digest, len(labels))))
                choice = max(probs, key=probs.get)
                answers[qid] = {"type": "choice", "choice": choice, "confidence": probs[choice], "probabilities": probs}
            elif kind == "score":
                levels = list(q.get("criteria") or [])
                if not levels:
                    raise MalformedQuestion(f"score question {qid!r} has no criteria")
                probs = _dist(digest, len(levels))
                answers[qid] = {
                    "type": "score",
                    "score": round(sum(i * p for i, p in enumerate(probs)), 4),
                    "confidence": max(probs),
                    "legend": {str(i): level for i, level in enumerate(levels)},
                    "probabilities": {str(i): p for i, p in enumerate(probs)},
                }
            else:
                raise MalformedQuestion(f"question {qid!r} has unsupported type {kind!r}")
        return RawAnswers(self.model, answers, {"input_tokens": None, "output_tokens": None}, None, int((time.monotonic() - t0) * 1000))


class TypeSafeBackend:
    """The real thing: typesafe-sdk's synchronous client with an explicit retry policy and pinned model."""

    name = "typesafe"

    def __init__(self, api_key: str, model: str, *, max_retries: int = 2, retry_budget_s: float = 20.0, timeout_s: float = 8.0) -> None:
        try:
            from typesafe_sdk import RetryPolicy, TypeSafeClient
        except ImportError as exc:
            raise RuntimeError("typesafe-sdk is not installed in the judge's environment: pip install 'dealbot-desk[judge]'") from exc
        self.model = ensure_pinned(model)
        policy = RetryPolicy(
            max_retries=max_retries,
            http_statuses={429, 500, 502, 503, 504},
            respect_retry_after=True,
            timeout=retry_budget_s,
        )
        self._client = TypeSafeClient(api_key=api_key, model=self.model, retry=policy, timeout=timeout_s)
        sdk_logger = logging.getLogger("typesafe_sdk")
        if sdk_logger.level < logging.WARNING:
            sdk_logger.setLevel(logging.WARNING)  # the SDK logs request and response bodies at DEBUG; never here

    def list_models(self) -> list[str]:
        return [m.name for m in self._client.models.list().models]

    def verify_model(self) -> None:
        names = self.list_models()
        if self.model not in names:
            raise ModelNotPinnedError(f"pinned model {self.model!r} is not offered to this account; available: {names}")

    def ask(self, state: Mapping, questions: Mapping[str, Mapping], *, timeout_s: float) -> RawAnswers:
        t0 = time.monotonic()
        try:
            response = self._client.system_one(state=state, questions=questions, model=self.model, timeout=timeout_s)
        except Exception as exc:
            raise map_sdk_error(exc) from None
        latency_ms = int((time.monotonic() - t0) * 1000)
        answers = {name: answer.model_dump(mode="json") for name, answer in response.answers.items()}
        usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
        return RawAnswers(response.model, answers, usage, response.__dict__.get("_request_id"), latency_ms)

    def close(self) -> None:
        self._client.close()


def map_sdk_error(exc: BaseException) -> JudgeFault:
    """Map SDK exceptions to judge faults. Order matters: subclasses before their bases."""
    try:
        import typesafe_sdk as sdk
    except ImportError:
        return UpstreamUnavailable(type(exc).__name__)
    if isinstance(exc, sdk.TypeSafeRateLimitError):
        return RateLimited(str(exc), retry_after_ms=None if exc.retry_after_ms is None else int(exc.retry_after_ms))
    if isinstance(exc, (sdk.TypeSafeBadRequestError, sdk.TypeSafeUnprocessableEntityError)):
        return MalformedQuestion(str(exc))
    if isinstance(exc, (sdk.TypeSafeAuthenticationError, sdk.TypeSafePermissionDeniedError)):
        return UpstreamAuth(f"{type(exc).__name__}: the judge's TypeSafe key was rejected")
    if isinstance(exc, sdk.TypeSafeAPITimeoutError):
        return UpstreamTimeout(str(exc))
    if isinstance(exc, sdk.TypeSafeAPIConnectionError):
        return UpstreamUnavailable(str(exc))
    if isinstance(exc, sdk.TypeSafeAPIResponseValidationError):
        return UpstreamUnavailable(f"invalid upstream response at {exc.field_path!r}")
    if isinstance(exc, sdk.TypeSafeAPIError):
        return UpstreamUnavailable(f"{type(exc).__name__}: status {exc.status}")
    if isinstance(exc, sdk.TypeSafeError):
        return MalformedQuestion(str(exc))
    return UpstreamUnavailable(type(exc).__name__)


def sdk_version() -> str | None:
    try:
        from typesafe_sdk import __version__
    except ImportError:
        return None
    return __version__
