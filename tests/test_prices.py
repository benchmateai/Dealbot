import pytest

from dealbot.prices import parse_prices


@pytest.mark.parametrize("text,price,lst", [
    ("Sony WH-1000XM5 $39.99 (reg $399.99)", 39.99, 399.99),
    ("Dyson V15 - $74.90 (was $749.99)", 74.90, 749.99),
    ("LEGO set $84.99 at Walmart (reg. $849.99)", 84.99, 849.99),
    ("90% off: Headphones, $29.99", 29.99, 299.90),
    ("Samsung TV $999.99 + Free Shipping", 999.99, None),
    ("Get $20 off $100 at Target", 100.0, None),
    ("Keurig $9.99 ($99.99)", 9.99, 99.99),
    ("Mattress $1,299 MSRP $2,599", 1299.0, 2599.0),
    ("$399 now $29", 29.0, 399.0),
    ("Free shipping on everything", None, None),
])
def test_parse_prices(text, price, lst):
    assert parse_prices(text) == (price, lst)
