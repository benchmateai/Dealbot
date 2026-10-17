"""Amazon via Keepa's Deals endpoint (paid API, https://keepa.com/#!api).

Keepa tracks every Amazon price. Its /deal endpoint returns items whose
current price dropped by a given percentage versus their recent average,
which is the cleanest signal of an Amazon mis-price.
"""
from __future__ import annotations

import json
from typing import Iterable

from dealbot.models import Deal
from dealbot.sources.base import Source

BASE = "https://api.keepa.com/deal"
DOMAIN_TLD = {1: "com", 2: "co.uk", 3: "de", 4: "fr", 5: "co.jp", 6: "ca", 8: "it", 9: "es"}


def parse_deals(data: dict, source_name: str = "keepa", domain: int = 1) -> list[Deal]:
    deals: list[Deal] = []
    tld = DOMAIN_TLD.get(domain, "com")
    for d in (data.get("deals") or {}).get("dr") or []:
        asin, title = d.get("asin"), d.get("title")
        current = d.get("current") or []
        avg = d.get("avg") or []
        if not asin or not title or not current:
            continue
        # Index 0 = Amazon price, 1 = marketplace New. Prices are in cents, -1 = none.
        price_c = next((c for c in current[:2] if c and c > 0), None)
        if price_c is None:
            continue
        avg_c = next((a for a in (avg[0] if avg and isinstance(avg[0], list) else avg)[:2]
                      if a and a > 0), None) if avg else None
        deals.append(Deal(
            title=title, url=f"https://www.amazon.{tld}/dp/{asin}", source=source_name,
            price=price_c / 100, list_price=(avg_c / 100) if avg_c else None,
            retailer="Amazon", sku=asin, tags=["amazon-sold" if current[0] and current[0] > 0 else "3p"],
        ))
    return deals


class Keepa(Source):
    name = "keepa"
    requires = ("api_key",)

    def fetch(self) -> Iterable[Deal]:
        domain = int(self.options.get("domain", 1))
        selection = {
            "page": 0, "domainId": domain, "priceTypes": [0, 1],
            "deltaPercentRange": [int(self.options.get("min_percent_drop", 70)), 100],
            "currentRange": [int(float(self.options.get("min_price", 1)) * 100), 1_000_000_00],
            "isRangeEnabled": True, "isFilterEnabled": True,
            "filterErotic": True, "sortType": 4, "dateRange": 0,
        }
        url = f"{BASE}?key={self.options['api_key']}&selection={json.dumps(selection)}"
        try:
            resp = self.http.get(url)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:  # noqa: BLE001
            self.log.warning("request failed: %s", e)
            return
        deals = parse_deals(data, self.name, domain)
        self.log.info("%d deals", len(deals))
        yield from deals
