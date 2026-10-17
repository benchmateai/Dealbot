"""Watch specific product pages at *any* retailer.

Most retailers (Target, Home Depot, Lowe's, Costco, Newegg, ...) embed
schema.org Product/Offer JSON-LD in the page, so we can read the live price
without a per-retailer scraper. Give it URLs and, optionally, what the item
normally costs. Price history is kept so a sudden drop is flagged even with
no `expected` given.

Note: heavily bot-protected sites (Amazon, Walmart) may serve a challenge page
instead; use the API sources for those.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterable, Optional

from dealbot.models import Deal, retailer_from_url
from dealbot.sources.base import Source

JSONLD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
META_PRICE_RE = re.compile(
    r'<meta[^>]+(?:property|itemprop|name)=["\'](?:product:price:amount|og:price:amount|price)["\'][^>]+content=["\']([\d.,]+)["\']', re.I)
META_PRICE_RE2 = re.compile(
    r'<meta[^>]+content=["\']([\d.,]+)["\'][^>]+(?:property|itemprop|name)=["\'](?:product:price:amount|og:price:amount|price)["\']', re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)


def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _num(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def extract_product(html: str) -> dict[str, Any]:
    """Return {'name','price','list_price','sku','availability'} best-effort."""
    out: dict[str, Any] = {}
    for block in JSONLD_RE.findall(html):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        for node in _walk(data):
            t = node.get("@type")
            types = t if isinstance(t, list) else [t]
            if "Product" in types and "name" not in out:
                out["name"] = node.get("name")
                out["sku"] = node.get("sku") or node.get("productID")
            if any(x in types for x in ("Offer", "AggregateOffer")) and "price" not in out:
                price = _num(node.get("price") or node.get("lowPrice"))
                if price is not None:
                    out["price"] = price
                    out["availability"] = str(node.get("availability") or "")
                    spec = node.get("priceSpecification")
                    if isinstance(spec, list):
                        spec = spec[0] if spec else None
                    if isinstance(spec, dict):
                        # Some sites put the strike-through price here.
                        for k in ("listPrice", "price"):
                            lp = _num(spec.get(k))
                            if lp and lp > price:
                                out["list_price"] = lp
                                break
    if "price" not in out:
        m = META_PRICE_RE.search(html) or META_PRICE_RE2.search(html)
        if m:
            out["price"] = _num(m.group(1))
    if "name" not in out:
        m = TITLE_RE.search(html)
        if m:
            out["name"] = re.sub(r"\s+", " ", m.group(1)).strip()[:200]
    return out


class Watchlist(Source):
    name = "watchlist"

    def fetch(self) -> Iterable[Deal]:
        items = self.options.get("items") or []
        headers = {"Accept": "text/html,application/xhtml+xml",
                   "Accept-Language": "en-US,en;q=0.9"}
        if self.options.get("browser_user_agent"):
            headers["User-Agent"] = self.options["browser_user_agent"]
        for item in items:
            if isinstance(item, str):
                item = {"url": item}
            url = item.get("url")
            if not url:
                continue
            try:
                resp = self.http.get(url, headers=headers)
                resp.raise_for_status()
            except Exception as e:  # noqa: BLE001
                self.log.warning("%s failed: %s", url, e)
                continue
            info = extract_product(resp.text)
            if info.get("price") is None:
                self.log.info("%s: no price found (bot wall or no structured data)", url)
                continue
            expected = _num(item.get("expected")) or info.get("list_price")
            yield Deal(
                title=item.get("name") or info.get("name") or url, url=url, source=self.name,
                price=info["price"], list_price=expected, retailer=retailer_from_url(url),
                sku=str(info["sku"]) if info.get("sku") else None,
                tags=[info.get("availability", "").rsplit("/", 1)[-1]] if info.get("availability") else [],
            )
