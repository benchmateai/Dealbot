import pytest

from judge.client import Backoff, HttpJudge, JudgeAuthError, JudgeMalformed, JudgeRateLimited, JudgeTimeout, LocalStubJudge
from judge.jev import STUB_MODEL, MalformedQuestion, ModelNotPinnedError, RateLimited, StubBackend, UpstreamTimeout, ensure_pinned, map_sdk_error
from judge.service import JudgeConfig, JudgeConfigError, JudgeServer
from questions import load_battery
from tests.helpers import T0

SECRET = "s" * 40
STATE = {"mkt": {"mid": 2500.0, "spr_bps": 2.0}, "pos": None, "desk": {"bot": "gambler", "phase": "entry", "cost_bps": 24.0}}
QUESTIONS = load_battery("gambler").wire()


def test_model_must_be_pinned():
    for bad in ("", "jev", "jev-latest", "jev-preview", "jev-1-latest", "gpt-5"):
        with pytest.raises(ModelNotPinnedError):
            ensure_pinned(bad)
    for good in ("jev-1.13.0", "jev-1.14-20261014", STUB_MODEL):
        assert ensure_pinned(good) == good


def test_stub_backend_is_deterministic_and_well_formed():
    a = StubBackend().ask(STATE, QUESTIONS, timeout_s=1)
    b = StubBackend().ask(STATE, QUESTIONS, timeout_s=1)
    assert a.answers == b.answers and a.model == STUB_MODEL and set(a.answers) == set(QUESTIONS)
    assert a.answers != StubBackend().ask({**STATE, "mkt": {"mid": 1.0}}, QUESTIONS, timeout_s=1).answers
    choice = a.answers["dir_20"]
    assert choice["type"] == "choice" and choice["choice"] in choice["probabilities"] and sum(choice["probabilities"].values()) == pytest.approx(1.0, abs=0.01)
    assert 0 <= a.answers["whipsaw"]["noul"] <= 1
    with pytest.raises(MalformedQuestion):
        StubBackend().ask(STATE, {"x": {"type": "choice", "criteria": {}}}, timeout_s=1)


@pytest.fixture
def server():
    s = JudgeServer(StubBackend(), SECRET).start()
    yield s
    s.stop()


def test_wrong_desk_secret_is_rejected(server):
    with pytest.raises(JudgeAuthError):
        HttpJudge(server.url, "x" * 40).ask(decision_id="d", bot="gambler", state=STATE, questions=QUESTIONS, deadline_ms=T0 + 5000, now_ms=T0)


def test_round_trip_returns_raw_answers_and_the_model_string(server):
    answer = HttpJudge(server.url, SECRET).ask(decision_id="d1", bot="gambler", state=STATE, questions=QUESTIONS, deadline_ms=T0 + 5000, now_ms=T0)
    assert answer.decision_id == "d1" and answer.model == STUB_MODEL and answer.requested_model == STUB_MODEL
    assert set(answer.answers) == set(QUESTIONS) and answer.backend == "stub"
    assert answer.answers == LocalStubJudge().ask(decision_id="d1", bot="gambler", state=STATE, questions=QUESTIONS, deadline_ms=T0 + 5000, now_ms=T0).answers


def test_bad_request_is_not_retryable(server):
    with pytest.raises(JudgeMalformed) as exc:
        HttpJudge(server.url, SECRET).ask(decision_id="d", bot="gambler", state=STATE, questions={}, deadline_ms=T0 + 5000, now_ms=T0)
    assert exc.value.retryable is False and exc.value.status == 400


def test_deadline_passed_makes_no_network_call():
    with pytest.raises(JudgeTimeout):
        HttpJudge("http://127.0.0.1:9", SECRET).ask(decision_id="d", bot="gambler", state=STATE, questions=QUESTIONS, deadline_ms=T0 + 100, now_ms=T0)


class RateLimitingBackend:
    name, model = "stub", STUB_MODEL

    def ask(self, state, questions, *, timeout_s):
        raise RateLimited("slow down", retry_after_ms=1500)


def test_rate_limit_propagates_retry_after_and_drives_backoff():
    server = JudgeServer(RateLimitingBackend(), SECRET).start()
    try:
        with pytest.raises(JudgeRateLimited) as exc:
            HttpJudge(server.url, SECRET).ask(decision_id="d", bot="gambler", state=STATE, questions=QUESTIONS, deadline_ms=T0 + 5000, now_ms=T0)
    finally:
        server.stop()
    assert exc.value.retry_after_ms == 1500 and exc.value.retryable
    backoff = Backoff()
    assert backoff.note_rate_limited(T0, exc.value.retry_after_ms) == 1500
    assert backoff.is_blocked(T0 + 1000) and not backoff.is_blocked(T0 + 1600)
    assert backoff.note_rate_limited(T0 + 2000) == 4000
    backoff.note_ok()
    assert not backoff.is_blocked(T0 + 2001)


def test_judge_config_requires_a_long_secret_and_a_pinned_model():
    with pytest.raises(JudgeConfigError, match="DESK_SECRET"):
        JudgeConfig.from_env({"JUDGE_BACKEND": "stub", "DESK_SECRET": "short"})
    with pytest.raises(JudgeConfigError, match="pinned"):
        JudgeConfig.from_env({"JUDGE_BACKEND": "typesafe", "DESK_SECRET": SECRET, "JEV_MODEL": "jev-latest"})
    cfg = JudgeConfig.from_env({"JUDGE_BACKEND": "stub", "DESK_SECRET": SECRET})
    assert cfg.model == STUB_MODEL and "DESK_SECRET" not in repr(cfg) and SECRET not in repr(cfg)


def test_sdk_errors_map_to_retry_semantics():
    sdk = pytest.importorskip("typesafe_sdk")
    httpx2 = pytest.importorskip("httpx2")
    limited = map_sdk_error(sdk.TypeSafeRateLimitError(429, {"error": "slow"}, httpx2.Headers({"retry-after-ms": "2500"})))
    assert isinstance(limited, RateLimited) and limited.retry_after_ms == 2500 and limited.retryable
    bad = map_sdk_error(sdk.TypeSafeUnprocessableEntityError(422, {"detail": [{"loc": ["body", "questions", "x"], "msg": "bad"}]}, httpx2.Headers()))
    assert isinstance(bad, MalformedQuestion) and not bad.retryable and "questions.x" in str(bad)
    assert isinstance(map_sdk_error(sdk.TypeSafeBadRequestError(400, "nope", httpx2.Headers())), MalformedQuestion)
    assert isinstance(map_sdk_error(sdk.TypeSafeAPITimeoutError(5.0)), UpstreamTimeout)
    assert isinstance(map_sdk_error(sdk.TypeSafeError("At least one question is required.")), MalformedQuestion)


def test_real_backend_refuses_an_alias_before_touching_the_network():
    pytest.importorskip("typesafe_sdk")
    from judge.jev import TypeSafeBackend

    with pytest.raises(ModelNotPinnedError):
        TypeSafeBackend("not-a-real-key", "jev-latest")
