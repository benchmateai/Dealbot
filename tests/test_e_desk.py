"""The E desk (lab/strategies/e_desk.py): strategy E with the next round's risk rules, and its dashboard rows."""

import json

import pytest

from dashboard.edesk import health, merge, rows
from lab.strategies import e_desk, e_incentive
from tests.test_lab import T0, _book, _program, _write

OFF = {"market_cap_usd": 1e12, "capital_cap_usd": 1e12, "loss_stop_usd": 1e12, "close_buffer_s": 0}  # E's own rules only
YES, NO = [[0.50, 300.0], [0.49, 900.0]], [[0.45, 300.0], [0.44, 900.0]]  # YES mid 0.525; a Target Size of 1000 quotes 100 a side


def _through_yes(ts, count=150.0):
    """A NO taker selling through a YES bid at 0.50."""
    return ("trade", {"ticker": "M", "yes_price": 0.49, "count": count, "taker_side": "no"}, ts)


def _through_no(ts, count=150.0):
    """A YES taker buying through a NO bid at 0.45 (a YES offer at 0.55)."""
    return ("trade", {"ticker": "M", "yes_price": 0.56, "count": count, "taker_side": "yes"}, ts)


def test_with_its_new_rules_off_the_desk_is_lab_e(tmp_path):
    yes, no = [[0.50, 100.0]], [[0.45, 100.0]]
    items = [("incentives", {"programs": [_program("M", 0.5, target="100.00")]}, T0)]
    for k in range(4):
        items.append(_book(T0 + 1000 + k * 2000, "M", None, None, yes=yes, no=no, set="E"))
        items.append(("trade", {"ticker": "M", "yes_price": 0.49, "count": 50.0, "taker_side": "no"}, T0 + 2000 + k * 2000))
    items.append(_book(T0 + 301_000, "M", None, None, yes=[[0.40, 100.0]], no=[[0.55, 100.0]], set="E"))
    items.append(_book(T0 + 400_000, "M", None, None, yes=[[0.40, 100.0]], no=[[0.55, 100.0]], set="E"))
    _write(tmp_path, items)
    lab = e_incentive.evaluate(tmp_path, registered_ms=0)["summary"]
    desk = e_desk.evaluate(tmp_path, since_ms=0, rules=OFF)["summary"]
    assert desk["contracts_filled"] == lab["contracts_filled"] == 30
    assert desk["payable_usd"] == lab["payable_usd"] and desk["fills_marked_usd"] == lab["fills_marked_usd"] == round(30 * (0.425 - 0.50), 2)
    assert desk["net_usd"] == lab["net_usd_realistic"] and desk["equity_usd"] == round(10_000 + desk["net_usd"], 2)


def test_lab_e_marks_a_closing_market_at_its_last_quoted_book_not_at_nothing(tmp_path):
    items = [("incentives", {"programs": [_program("M", 0.5, target="100.00")]}, T0),
             _book(T0 + 1000, "M", None, None, yes=[[0.50, 100.0]], no=[[0.45, 100.0]], set="E"),
             ("trade", {"ticker": "M", "yes_price": 0.49, "count": 10.0, "taker_side": "no"}, T0 + 2000),  # our 10 YES at 0.50
             _book(T0 + 3000, "M", None, None, yes=[[0.01, 100.0]], no=[[0.97, 100.0]], set="E"),        # YES mid 0.02
             _book(T0 + 4000, "M", None, None, yes=[], no=[], set="E")]                                   # the book empties at the close
    _write(tmp_path, items)
    assert e_incentive.evaluate(tmp_path, registered_ms=0)["summary"]["fills_marked_usd"] == round(10 * (0.02 - 0.50), 2)
    assert e_desk.evaluate(tmp_path, since_ms=0, rules=OFF)["summary"]["fills_marked_usd"] == round(10 * (0.02 - 0.50), 2)


def test_the_market_cap_stops_adding_but_the_desk_still_pairs_off(tmp_path):
    items = [("incentives", {"programs": [_program("M", 0.5)]}, T0),
             _book(T0 + 1000, "M", None, None, yes=YES, no=NO, set="E"),
             _through_yes(T0 + 1500),
             _book(T0 + 2000, "M", None, None, yes=YES, no=NO, set="E"),
             _through_yes(T0 + 2500),   # no YES bid any more: 60 held already reach the cap
             _through_no(T0 + 3000)]    # the NO bid pairs off what is held, and may add on the NO side
    _write(tmp_path, items)
    r = e_desk.evaluate(tmp_path, since_ms=0, rules={**OFF, "market_cap_usd": 30.0})
    m = next(x for x in r["markets"] if x["ticker"] == "M")
    # each first quote is cut to $30: 60 YES at 50 cents, 66.7 NO at 45; the 60 YES fill, and YES is not quoted
    # again (60 held at 52.5 cents are worth more than $30), while the NO bid stays up and pairs them off
    assert m["contracts"] == pytest.approx(60 + 66.7, abs=0.1) and m["net_yes"] == pytest.approx(60 - 66.7, abs=0.1)
    assert r["summary"]["capped_markets"] == 1 and r["summary"]["capped_quotes"] >= 1


def test_the_capital_cap_cuts_new_quotes_to_fit(tmp_path):
    items = [("incentives", {"programs": [_program("M", 0.5)]}, T0),
             _book(T0 + 1000, "M", None, None, yes=YES, no=NO, set="E"),
             _through_yes(T0 + 1500), _through_no(T0 + 1600)]
    _write(tmp_path, items)
    r = e_desk.evaluate(tmp_path, since_ms=0, rules={**OFF, "capital_cap_usd": 20.0})
    # $20 buys a 40-contract YES bid at 50 cents; nothing is left for a NO bid
    assert r["summary"]["contracts_filled"] == 40 and r["markets"][0]["net_yes"] == 40


def test_the_news_variant_adds_nothing_while_the_price_jumps(tmp_path):
    jumped_yes, jumped_no = [[0.60, 300.0], [0.59, 900.0]], [[0.35, 300.0], [0.34, 900.0]]  # YES mid 0.625, ten cents up
    items = [("incentives", {"programs": [_program("M", 0.5)]}, T0),
             _book(T0 + 1000, "M", None, None, yes=YES, no=NO, set="E"),
             _book(T0 + 31_000, "M", None, None, yes=jumped_yes, no=jumped_no, set="E"),
             ("trade", {"ticker": "M", "yes_price": 0.59, "count": 150.0, "taker_side": "no"}, T0 + 32_000),  # would fill a 0.60 bid
             _book(T0 + 932_000, "M", None, None, yes=jumped_yes, no=jumped_no, set="E"),                     # the pause is over
             ("trade", {"ticker": "M", "yes_price": 0.59, "count": 150.0, "taker_side": "no"}, T0 + 933_000)]
    _write(tmp_path, items)
    off = e_desk.evaluate(tmp_path, since_ms=0, rules=OFF)["summary"]
    news = e_desk.evaluate(tmp_path, since_ms=0, rules={**OFF, **e_desk.VARIANTS["news_pause"]})["summary"]
    assert e_desk.RULES["news_move"] is None and off["news_pauses"] == 0 and off["contracts_filled"] == 200
    assert news["news_pauses"] == 1 and news["contracts_filled"] == 100  # only the fill after the pause
    assert news["reward_usd"] < off["reward_usd"]                         # no payments while it stood aside


def test_the_loss_stop_takes_no_new_risk_but_keeps_pairing_off(tmp_path):
    crashed_yes, crashed_no = [[0.08, 1000.0]], [[0.88, 1000.0]]  # YES mid 0.10
    items = [("incentives", {"programs": [_program("M", 0.5)]}, T0),
             _book(T0 + 1000, "M", None, None, yes=YES, no=NO, set="E"),
             _through_yes(T0 + 1500),                                          # 100 YES at 0.50
             _book(T0 + 2000, "M", None, None, yes=crashed_yes, no=crashed_no, set="E"),  # marked 100 x (0.10 - 0.50) = -40
             ("trade", {"ticker": "M", "yes_price": 0.07, "count": 150.0, "taker_side": "no"}, T0 + 2500),   # through a 0.08 YES bid
             ("trade", {"ticker": "M", "yes_price": 0.13, "count": 60.0, "taker_side": "yes"}, T0 + 2600)]   # through a 0.88 NO bid
    _write(tmp_path, items)
    r = e_desk.evaluate(tmp_path, since_ms=0, rules={**OFF, "loss_stop_usd": 40.0})
    s, m = r["summary"], r["markets"][0]
    assert s["loss_stops"] == 1 and s["stopped_markets"] == ["M"] and m["status"] == "stopped"
    # no new YES; the NO bid, sized to what is held, pairs off 60 of the 100
    assert m["contracts"] == 160 and m["net_yes"] == 40
    assert [e["kind"] for e in r["events"]] == ["loss_stop"]


def test_the_close_rule_adds_nothing_in_a_market_s_last_three_hours(tmp_path):
    close = T0 + 2 * 3_600_000
    items = [("incentives", {"programs": [_program("M", 0.5)]}, T0),
             _book(T0 + 1000, "M", None, close, yes=YES, no=NO, set="E"),
             _through_yes(T0 + 1500)]
    _write(tmp_path, items)
    assert e_desk.evaluate(tmp_path, since_ms=0, rules=OFF)["summary"]["contracts_filled"] == 100
    s = e_desk.evaluate(tmp_path, since_ms=0, rules={**OFF, "close_buffer_s": 10_800})["summary"]
    assert s["contracts_filled"] == 0 and s["reward_usd"] == 0


def test_a_yes_and_a_no_pair_off_at_a_dollar_and_settled_markets_mark_at_their_result(tmp_path):
    items = [("incentives", {"programs": [_program("M", 0.5)]}, T0),
             _book(T0 + 1000, "M", None, None, yes=YES, no=NO, set="E"),
             _through_yes(T0 + 1500, 100.0), _through_no(T0 + 1600, 30.0),
             _book(T0 + 2000, "M", None, None, yes=[[0.20, 1000.0]], no=[[0.75, 1000.0]], set="E"),
             ("settled", {"series": "KXM", "event": "EV", "rows": [["M", "yes", None]]}, T0 + 3000)]
    _write(tmp_path, items)
    m = e_desk.evaluate(tmp_path, since_ms=0, rules=OFF)["markets"][0]
    # 100 YES at 0.50 and 30 NO at 0.45 cost 63.50; settled YES pays 100
    assert (m["contracts"], m["net_yes"], m["cost_usd"]) == (130, 70, 63.5) and m["value_usd"] == 100.0 and m["status"] == "settled"


def test_nothing_before_the_start_counts_and_the_rows_say_when_it_starts(tmp_path):
    items = [("incentives", {"programs": [_program("M", 0.5)]}, T0),
             _book(T0 + 1000, "M", None, None, yes=YES, no=NO, set="E"), _through_yes(T0 + 1500)]
    _write(tmp_path, items)
    report = e_desk.evaluate(tmp_path, since_ms=T0 + 10_000)
    assert report["summary"]["started"] is False and report["markets"] == []
    out = rows(report, now_ms=T0 + 20_000)
    assert [r["table"] for r in out] == ["edesk"] and out[0]["week_day"] == 1 and out[0]["ends_ms"] == T0 + 10_000 + e_desk.WEEK_MS
    assert e_desk.START_MS == 1_794_459_600_000  # 2026-11-12T05:00Z, after desk v2's week and its final report


def test_rows_replace_only_the_old_e_desk_rows(tmp_path):
    path = tmp_path / "money.json"
    path.write_text(json.dumps([{"table": "summary", "id": "summary"}, {"table": "edesk", "id": "edesk", "net_usd": 1.0}]))
    report = {"summary": {"start_ms": T0, "started": True, "net_usd": 2.0, "stopped_markets": []},
              "markets": [{"ticker": "M", "pnl_usd": 1.5}], "equity": [[T0, 10_002.0]], "variants": {"news_pause": {"net_usd": -1.0}}}
    merged = merge(path, rows(report, now_ms=T0 + 86_400_000 * 2))
    tables = [r["table"] for r in merged]
    assert tables == ["summary", "edesk", "edesk_market", "edesk_equity", "edesk_variant"]
    assert merged[1]["net_usd"] == 2.0 and merged[1]["week_day"] == 3 and "stopped_markets" not in merged[1]


def test_the_health_line_judges_how_fresh_the_live_feed_is(tmp_path):
    _write(tmp_path, [_book(T0, "M", None, None, yes=YES, no=NO, set="E")])
    assert health(tmp_path, now_ms=T0 + 10 * 60_000) == ("health: OK · newest E book 10 minutes old", 0)
    line, code = health(tmp_path, now_ms=T0 + 80 * 60_000)
    assert line.startswith("health: WARN") and code == 0
    line, code = health(tmp_path, now_ms=T0 + 160 * 60_000)
    assert line.startswith("health: ALERT") and code == 3
    assert health(tmp_path, now_ms=T0 + 7 * 3_600_000)[1] == 3


@pytest.mark.parametrize("name", sorted(e_desk.VARIANTS))
def test_each_variant_only_changes_registered_rules(name):
    assert set(e_desk.VARIANTS[name]) <= set(e_desk.RULES)
