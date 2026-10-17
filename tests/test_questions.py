import pytest

from questions import BOTS, Battery, BatteryError, ChoiceQ, NoulQ, Resolution, ScoreQ, load_battery
from judge.protocol import QUESTION_TYPES


@pytest.mark.parametrize("bot", BOTS)
def test_battery_rules(bot):
    battery = load_battery(bot)
    assert battery.bot == bot
    for q in battery.questions:
        assert q.instructions.count("?") == 1 and q.instructions.endswith("?")
        if isinstance(q, ChoiceQ):
            assert "other" in q.criteria
    wire = battery.wire()
    assert list(wire) == [q.id for q in battery.questions]
    assert all(w["type"] in QUESTION_TYPES for w in wire.values())
    assert len(battery.version()) == 12 and battery.version() == load_battery(bot).version()


@pytest.mark.parametrize("bot", BOTS)
def test_wire_format_is_accepted_by_the_sdk(bot):
    sdk = pytest.importorskip("typesafe_sdk")
    builders = {"choice": sdk.Choice, "noul": sdk.Noul, "score": sdk.Score}
    for qid, w in load_battery(bot).wire().items():
        q = builders[w["type"]](**w)
        assert q.type == w["type"], qid


def test_choice_without_other_is_rejected():
    with pytest.raises(BatteryError, match="other"):
        Battery("gambler", (ChoiceQ("dir", "Which way does it go?", {"up": None, "down": None}),))


def test_two_judgments_in_one_question_are_rejected():
    with pytest.raises(BatteryError, match="one judgment"):
        Battery("gambler", (NoulQ("x", "Is it rising? Is it liquid?"),))


def test_unknown_or_mismatched_rule_is_rejected():
    with pytest.raises(BatteryError, match="unknown outcome rule"):
        Battery("gambler", (NoulQ("x", "Is it rising?", resolution=Resolution("nope", 5)),))
    with pytest.raises(BatteryError, match="grades a choice"):
        Battery("gambler", (NoulQ("x", "Is it rising?", resolution=Resolution("direction_first_touch", 5)),))


def test_duplicate_ids_and_bad_levels_are_rejected():
    with pytest.raises(BatteryError, match="duplicate"):
        Battery("spy", (NoulQ("x", "Is it rising?"), NoulQ("x", "Is it falling?")))
    with pytest.raises(BatteryError, match="levels"):
        Battery("spy", (ScoreQ("s", "How much?", ("only one",)),))
