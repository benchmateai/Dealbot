"""Wire protocol between the desk and the judge service."""

from __future__ import annotations

from dataclasses import dataclass

JUDGE_PATH = "/v1/judge"
HEALTH_PATH = "/healthz"
SECRET_HEADER = "X-Desk-Secret"
QUESTION_TYPES = frozenset({"noul", "choice", "score"})
MAX_BODY_BYTES = 262_144
MAX_QUESTIONS = 64


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class JudgeRequest:
    decision_id: str
    bot: str
    state: dict
    questions: dict[str, dict]
    deadline_ms: int | None


def request_body(*, decision_id: str, bot: str, state: dict, questions: dict, deadline_ms: int | None) -> dict:
    return {"decision_id": decision_id, "bot": bot, "state": state, "questions": questions, "deadline_ms": deadline_ms}


def parse_request(body: object) -> JudgeRequest:
    if not isinstance(body, dict):
        raise ProtocolError("body must be a JSON object")
    decision_id = body.get("decision_id")
    bot = body.get("bot")
    state = body.get("state")
    questions = body.get("questions")
    deadline = body.get("deadline_ms")
    if not isinstance(decision_id, str) or not decision_id:
        raise ProtocolError("decision_id must be a non-empty string")
    if not isinstance(bot, str) or not bot:
        raise ProtocolError("bot must be a non-empty string")
    if not isinstance(state, dict) or not state:
        raise ProtocolError("state must be a non-empty JSON object")
    if not isinstance(questions, dict) or not questions:
        raise ProtocolError("questions must be a non-empty JSON object")
    if len(questions) > MAX_QUESTIONS:
        raise ProtocolError(f"at most {MAX_QUESTIONS} questions per request")
    for qid, q in questions.items():
        if not isinstance(q, dict) or q.get("type") not in QUESTION_TYPES:
            raise ProtocolError(f"question {qid!r} must be an object with type in {sorted(QUESTION_TYPES)}")
    if deadline is not None and (isinstance(deadline, bool) or not isinstance(deadline, int)):
        raise ProtocolError("deadline_ms must be an integer number of milliseconds remaining")
    return JudgeRequest(decision_id, bot, state, questions, deadline)
