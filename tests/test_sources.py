import json
from pathlib import Path

from dealbot.models import canonical_url, retailer_from_url
from dealbot.sources.bestbuy import parse_products
from dealbot.sources.feeds import parse_feed
from dealbot.sources.reddit import parse_listing
from dealbot.sources.watchlist import extract_product

FIX = Path(__file__).parent / "fixtures"


def test_reddit_listing():
    deals = parse_listing(json.loads((FIX / "reddit_new.json").read_text()))
    assert len(deals) == 3  # sticky skipped
    sony = deals[0]
    assert sony.price == 39.99 and sony.list_price == 399.99
    assert sony.retailer == "Amazon"
    assert "Price Error" in sony.tags
    assert sony.extra["comments"] == 44
    dyson = deals[2]
    assert dyson.retailer == "Target" and dyson.price == 74.90


def test_slickdeals_feed():
    deals = parse_feed((FIX / "slickdeals.rss").read_bytes(), "slickdeals")
    assert [d.retailer for d in deals] == ["Walmart", "Best Buy", "Target"]
    lego = deals[0]
    assert lego.price == 84.99 and lego.list_price == 849.99
    assert lego.tags == ["Toys"]
    assert lego.posted_at is not None
    tv = deals[1]
    assert tv.price == 999.99 and tv.list_price == 1299.99  # list from description


def test_bestbuy_products():
    deals = parse_products(json.loads((FIX / "bestbuy.json").read_text()))
    assert deals[0].sku == "6418599" and deals[0].retailer == "Best Buy"
    assert deals[0].discount == 0.9
    assert "Refurbished" in deals[1].tags


def test_watchlist_jsonld():
    info = extract_product((FIX / "product_page.html").read_text())
    assert info["price"] == 39.99
    assert info["list_price"] == 399.0
    assert info["sku"] == "3005-22"
    assert info["name"].startswith("Milwaukee")


def test_canonical_url_strips_tracking():
    a = canonical_url("https://www.amazon.com/dp/B09XS7JWHH?tag=slick-20&ref_=foo&psc=1")
    b = canonical_url("https://www.amazon.com/dp/B09XS7JWHH/")
    assert a == b == "https://www.amazon.com/dp/B09XS7JWHH"


def test_retailer_from_url():
    assert retailer_from_url("https://www.homedepot.com/p/1") == "Home Depot"
    assert retailer_from_url("https://amzn.to/abc") == "Amazon"
    assert retailer_from_url("https://shop.example.org/x") == "shop.example.org"


def test_ebay_search():
    from dealbot.sources.ebay import parse_search as parse_ebay
    deals = parse_ebay(json.loads((FIX / "ebay.json").read_text()))
    assert [d.sku for d in deals] == ["v1|1111|0", "v1|3333|0"]  # zero-feedback seller dropped
    sony = deals[0]
    assert sony.retailer == "eBay"
    assert sony.price == 39.99            # item + shipping
    assert sony.list_price == 399.99
    assert "top-rated" in sony.tags and sony.extra["seller"] == "bigstore"
    assert deals[1].list_price is None
