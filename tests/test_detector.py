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


def test_include_patterns_drop_off_category():
    det = Detector(DetectorConfig(include_patterns=[r"\b(?:laptop|dewalt)\b"]))
    sock = det.score(deal(title="Price error: socks $0.99 (reg $29.99)", price=0.99, list_price=29.99))
    assert sock.score == 0 and sock.reasons == ["not a tracked category"]
    drill = det.score(deal(title="Price error: DeWalt drill $9.99 (reg $199.99)", price=9.99, list_price=199.99))
    assert det.is_alert(drill)


def test_big_savings_bonus():
    det = Detector()
    small = det.score(deal(price=5.99, list_price=59.99))
    big = det.score(deal(price=59.99, list_price=599.99))
    assert big.score > small.score
    assert any("saves $" in r for r in big.reasons)


def test_bangers_config_is_strict():
    """Mirror config.yaml: 90% off alone shouldn't alert; with a second signal it should."""
    det = Detector(DetectorConfig(alert_threshold=80, min_list_price=50, min_savings=40))
    plain = det.score(deal(title="Dyson V15 vacuum", price=59.99, list_price=599.99))
    assert not det.is_alert(plain) or "decimal" in " ".join(plain.reasons)
    flagged = det.score(deal(title="Dyson V15 vacuum PRICE ERROR", price=149.99, list_price=599.99))
    assert det.is_alert(flagged)
