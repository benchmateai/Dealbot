"""Best Buy official Products API. Free key at https://developer.bestbuy.com.

We ask the API directly for items whose sale price is a huge percentage off
the regular price, which is exactly what a mis-keyed price looks like.
"""
from __future__ import annotations

from typing import Iterable

from dealbot.models import Deal
from dealbot.sources.base import Source

BASE = "https://api.bestbuy.com/v1/products"
SHOW = "sku,name,salePrice,regularPrice,percentSavings,url,onlineAvailability,inStoreAvailability,condition"


def parse_products(data: dict, source_name: str = "bestbuy") -> list[Deal]:
    deals: list[Deal] = []
    for p in data.get("products") or []:
        if not p.get("name") or p.get("salePrice") is None:
            continue
        tags = ["online" if p.get("onlineAvailability") else "online-unavailable"]
        if p.get("condition") and p["condition"].lower() != "new":
            tags.append(p["condition"])
        deals.append(Deal(
            title=p["name"], url=p.get("url") or f"https://www.bestbuy.com/site/{p['sku']}.p",
            source=source_name, price=float(p["salePrice"]),
            list_price=float(p["regularPrice"]) if p.get("regularPrice") else None,
            retailer="Best Buy", sku=str(p.get("sku")), tags=tags,
        ))
    return deals


class BestBuy(Source):
    name = "bestbuy"
    requires = ("api_key",)

    def fetch(self) -> Iterable[Deal]:
        pct = int(self.options.get("min_percent_savings", 70))
        min_regular = float(self.options.get("min_regular_price", 15))
        pages = int(self.options.get("pages", 2))
        query = f"(onSale=true&percentSavings>{pct}&regularPrice>{min_regular}&onlineAvailability=true)"
        for page in range(1, pages + 1):
            url = (f"{BASE}{query}?apiKey={self.options['api_key']}&format=json&show={SHOW}"
                   f"&pageSize=100&page={page}&sort=percentSavings.desc")
            try:
                resp = self.http.get(url)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:  # noqa: BLE001
                self.log.warning("page %d failed: %s", page, e)
                return
            deals = parse_products(data, self.name)
            self.log.info("page %d: %d products", page, len(deals))
            yield from deals
            if page >= int(data.get("totalPages", 1)):
                break
