from dealbot.detector import Detector, DetectorConfig
from dealbot.models import Deal


def deal(**kw):
    kw.setdefault("title", "Thing")
    kw.setdefault("url", "https://www.target.com/p/x")
    kw.setdefault("source", "test")
    return Deal(**kw)


def test_decimal_slip_is_high_score():
    a = Detector().score(deal(price=39.99, list_price=399.99))
    assert a.score >= 75
    assert any("decimal" in r for r in a.reasons)


def test_normal_sale_is_not_alert():
    det = Detector()
    a = det.score(deal(price=999.99, list_price=1299.99))
    assert not det.is_alert(a)


def test_keyword_and_flair_signal():
    det = Detector()
    a = det.score(deal(title="Price error? Vacuum $20", price=20, tags=["Price Error"]))
    assert det.is_alert(a)
    assert any("community" in r for r in a.reasons)


def test_cheap_junk_ignored():
    det = Detector()
    a = det.score(deal(price=0.50, list_price=5.00))
    assert not det.is_alert(a)


def test_expired_kills_score():
    det = Detector()
    a = det.score(deal(title="Expired: Keurig $9.99 (reg $99.99) - dead", price=9.99, list_price=99.99))
    assert not det.is_alert(a)


def test_history_drop():
    det = Detector()
    a = det.score(deal(price=50.0), prior_low=400.0)
    assert any("previous low" in r for r in a.reasons)


def test_ignore_patterns():
    det = Detector(DetectorConfig(ignore_patterns=[r"gift ?card"]))
    a = det.score(deal(title="$100 gift card for $10", price=10, list_price=100))
    assert a.score == 0


def test_sub_dollar_price():
    det = Detector()
    a = det.score(deal(title="Power drill $0.01 at Lowe's", price=0.01, list_price=129.0))
    assert det.is_alert(a)
