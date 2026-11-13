"""A scripted judge: answers every battery the same confident way, without a network or a key.

It exists for the pre-flight and for tests, never for a run. Noul questions get a fixed probability
(`nouls[qid]`, else `default_noul`), choice questions put almost all mass on `favorite`, and score
questions put almost all mass on the lowest criterion (low risk, nothing to exit for).
"""

from __future__ import annotations

from judge.client import JudgeAnswer


class ScriptedJudge:
    def __init__(self, model: str, *, nouls: dict[str, float] | None = None, default_noul: float = 0.05, favorite: str = "up", raise_exc: Exception | None = None) -> None:
        self.model = model
        self.calls: list[tuple[str, str]] = []
        self._nouls = {"keep_running": 0.95, **(nouls or {})}
        self._default_noul = default_noul
        self._favorite = favorite
        self._raise = raise_exc

    def ask(self, *, decision_id: str, bot: str, state: dict, questions: dict, deadline_ms: int, now_ms: int) -> JudgeAnswer:
        self.calls.append((decision_id, state["desk"]["phase"]))
        if self._raise is not None:
            raise self._raise
        answers: dict[str, dict] = {}
        for qid, q in questions.items():
            kind = q["type"]
            if kind == "noul":
                answers[qid] = {"type": "noul", "noul": self._nouls.get(qid, self._default_noul)}
            elif kind == "choice":
                labels = list(q["criteria"])
                fav = self._favorite if self._favorite in labels else ("trending" if "trending" in labels else labels[0])
                probs = {label: 0.02 for label in labels}
                probs[fav] = round(1 - 0.02 * (len(labels) - 1), 4)
                answers[qid] = {"type": "choice", "choice": fav, "confidence": probs[fav], "probabilities": probs}
            else:
                n = len(q["criteria"])
                probs = {str(i): (0.9 if i == 0 else round(0.1 / (n - 1), 4)) for i in range(n)}
                answers[qid] = {
                    "type": "score",
                    "score": sum(int(k) * v for k, v in probs.items()),
                    "confidence": 0.9,
                    "legend": {str(i): c for i, c in enumerate(q["criteria"])},
                    "probabilities": probs,
                }
        return JudgeAnswer(decision_id, self.model, self.model, answers, None, None, 1, "scripted")
