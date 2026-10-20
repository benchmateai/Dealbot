import pytest

from policy import EDGE, THRESHOLDS, WEIGHTS, ActionCost, PolicyError, combine, extract_prob, final_pick, score_actions
from questions import BOTS, ChoiceQ, NoulQ, ScoreQ, load_battery

SNAP = {"ret_bps": {"w1": 1.0, "w5": 5.0, "w20": -30.0}, "imb": 0.2, "rv_bps": 10.0}


def test_threshold_is_cost_ratio():
    assert ActionCost(70, 30).threshold == pytest.approx(0.7)
    assert ActionCost(10, 30).threshold == pytest.approx(0.25)
    with pytest.raises(ValueError):
        ActionCost(0, 1)


@pytest.mark.parametrize("bot", BOTS)
def test_every_action_has_one_threshold_and_weights_that_sum_to_one(bot):
    by_id = load_battery(bot).by_id()
    assert set(THRESHOLDS[bot]) == {"enter_long", "enter_short", "exit"} == set(WEIGHTS[bot])
    assert bot in EDGE
    kinds = {"noul": NoulQ, "not_noul": NoulQ, "score_norm": ScoreQ, "inv_score_norm": ScoreQ}
    for action, terms in WEIGHTS[bot].items():
        assert sum(t.weight for t in terms) == pytest.approx(1.0), action
        for t in terms:
            assert t.qid in by_id, (bot, action, t.qid)
            expected = ChoiceQ if t.extract.startswith(("choice:", "not_choice:")) else kinds[t.extract]
            assert isinstance(by_id[t.qid], expected), (bot, action, t.qid)
            if expected is ChoiceQ:
                assert t.extract.split(":", 1)[1] in by_id[t.qid].criteria


def test_extractors():
    assert extract_prob({"type": "noul", "noul": 0.8}, "not_noul") == pytest.approx(0.2)
    assert extract_prob({"type": "choice", "choice": "up", "confidence": 0.6, "probabilities": {"up": 0.6, "down": 0.4}}, "choice:down") == pytest.approx(0.4)
    assert extract_prob({"type": "score", "score": 1.5, "confidence": 0.5, "probabilities": {"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}}, "inv_score_norm") == pytest.approx(0.5)
    with pytest.raises(PolicyError):
        extract_prob({"type": "noul", "noul": 0.8}, "choice:up")


def _gambler_answers(p_up: float) -> dict:
    return {
        "dir_20": {"type": "choice", "choice": "up", "confidence": p_up, "probabilities": {"up": p_up, "down": 0.02, "flat": 1 - p_up - 0.04, "other": 0.02}},
        "late_entry": {"type": "noul", "noul": 0.05},
        "whipsaw": {"type": "noul", "noul": 0.05},
        "regime": {"type": "choice", "choice": "trending", "confidence": 0.9, "probabilities": {"trending": 0.9, "ranging": 0.05, "volatile_chop": 0.03, "other": 0.02}},
        "thesis_broken": {"type": "noul", "noul": 0.1},
        "keep_running": {"type": "noul", "noul": 0.9},
    }


def test_final_pick_enters_when_confident_and_holds_otherwise():
    pick = final_pick("gambler", "entry", _gambler_answers(0.95), SNAP)
    assert pick.action == "enter_long" and pick.prob >= pick.threshold == pytest.approx(0.7)
    assert pick.expected_edge_bps == pytest.approx(EDGE["gambler"].expected_edge_bps(pick.prob))
    hold = final_pick("gambler", "entry", _gambler_answers(0.4), SNAP)
    assert hold.is_hold and hold.action == "hold" and len(hold.scores) == 2
    manage = final_pick("gambler", "manage", _gambler_answers(0.5), SNAP)
    assert manage.is_hold and [s.action for s in manage.scores] == ["exit"]


def test_missing_answer_fails_closed():
    answers = _gambler_answers(0.95)
    del answers["whipsaw"]
    with pytest.raises(PolicyError, match="missing answer"):
        score_actions("gambler", "entry", answers, SNAP)


def test_conditional_term_contributes_zero_when_condition_fails():
    answers = {
        "spread_edge": {"type": "noul", "noul": 1.0},
        "revert_10": {"type": "choice", "choice": "revert", "confidence": 1.0, "probabilities": {"revert": 1.0, "continue": 0.0, "stay": 0.0, "other": 0.0}},
        "informed_flow": {"type": "noul", "noul": 0.0},
        "toxic_tape": {"type": "noul", "noul": 0.0},
    }
    assert combine(WEIGHTS["house"]["enter_long"], answers, {"ret_bps": {"w20": -10.0}}) == pytest.approx(1.0)
    assert combine(WEIGHTS["house"]["enter_long"], answers, {"ret_bps": {"w20": +10.0}}) == pytest.approx(0.75)
