"""eBay via the official Browse API (free developer keys at https://developer.ebay.com).

eBay is mostly third-party sellers, so a "too cheap" listing is more often a
scam than a mistake. We only look at fixed-price, new-condition listings
from sellers with real feedback, and lean on eBay's own strike-through
`marketingPrice` as the list price.
"""
from __future__ import annotations

import base64
from typing import Iterable, Optional

from dealbot.models import Deal
from dealbot.sources.base import Source

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SCOPE = "https://api.ebay.com/oauth/api_scope"
DEFAULT_QUERIES = ["laptop", "gpu", "oled tv", "headphones", "dyson", "milwaukee m18", "dewalt 20v",
                   "kitchenaid mixer", "lego set", "ps5", "xbox series x", "nintendo switch", "ipad", "macbook"]


def _f(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def parse_search(data: dict, source_name: str = "ebay", min_feedback_score: int = 100,
                 min_feedback_pct: float = 98.0) -> list[Deal]:
    deals: list[Deal] = []
    for it in data.get("itemSummaries") or []:
        title, url = it.get("title"), it.get("itemWebUrl")
        price = _f((it.get("price") or {}).get("value"))
        if not title or not url or price is None:
            continue
        seller = it.get("seller") or {}
        fb_score = int(seller.get("feedbackScore") or 0)
        fb_pct = _f(seller.get("feedbackPercentage")) or 0.0
        if fb_score < min_feedback_score or fb_pct < min_feedback_pct:
            continue
        mp = it.get("marketingPrice") or {}
        list_price = _f((mp.get("originalPrice") or {}).get("value"))
        ship = _f(((it.get("shippingOptions") or [{}])[0].get("shippingCost") or {}).get("value"))
        tags = [it.get("condition") or "", f"seller:{seller.get('username', '?')}",
                f"feedback:{fb_score}/{fb_pct:g}%"]
        if it.get("topRatedBuyingExperience"):
            tags.append("top-rated")
        deals.append(Deal(
            title=title, url=url, source=source_name, price=price + (ship or 0.0), list_price=list_price,
            retailer="eBay", sku=str(it.get("itemId") or ""), tags=tags,
            extra={"item_price": price, "shipping": ship, "seller": seller.get("username")},
        ))
    return deals


class Ebay(Source):
    name = "ebay"
    requires = ("client_id", "client_secret")

    def _token(self) -> str:
        basic = base64.b64encode(f"{self.options['client_id']}:{self.options['client_secret']}".encode()).decode()
        resp = self.http.session.post(
            TOKEN_URL, data={"grant_type": "client_credentials", "scope": SCOPE},
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
            timeout=20)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def fetch(self) -> Iterable[Deal]:
        try:
            token = self._token()
        except Exception as e:  # noqa: BLE001
            self.log.warning("could not get OAuth token: %s", e)
            return
        headers = {"Authorization": f"Bearer {token}",
                   "X-EBAY-C-MARKETPLACE-ID": self.options.get("marketplace", "EBAY_US")}
        min_price = float(self.options.get("min_price", 50))
        min_fb = int(self.options.get("min_feedback_score", 100))
        min_pct = float(self.options.get("min_feedback_pct", 98))
        filt = (f"buyingOptions:{{FIXED_PRICE}},conditions:{{NEW}},itemLocationCountry:US,"
                f"priceCurrency:USD,price:[{min_price:g}..]")
        for q in self.options.get("queries") or DEFAULT_QUERIES:
            params = {"q": q, "filter": filt, "sort": "price", "limit": int(self.options.get("limit", 50))}
            try:
                resp = self.http.get(SEARCH_URL, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:  # noqa: BLE001
                self.log.warning("query %r failed: %s", q, e)
                continue
            deals = parse_search(data, self.name, min_fb, min_pct)
            self.log.info("query %r: %d listings", q, len(deals))
            yield from deals
