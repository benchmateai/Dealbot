"""Walmart Affiliate (walmart.io) product search API.

Needs a consumer id + RSA private key from https://walmart.io. We search a
configurable list of queries sorted by price and flag anything far below MSRP.
Requires the optional `cryptography` package.
"""
from __future__ import annotations

import base64
import time
from typing import Iterable

from dealbot.models import Deal
from dealbot.sources.base import Source

BASE = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2"
DEFAULT_QUERIES = ["clearance", "tv", "laptop", "headphones", "lego", "vacuum", "tools", "grill"]


def parse_search(data: dict, source_name: str = "walmart") -> list[Deal]:
    deals: list[Deal] = []
    for it in data.get("items") or []:
        price = it.get("salePrice")
        if not it.get("name") or price is None:
            continue
        deals.append(Deal(
            title=it["name"], url=it.get("productUrl") or f"https://www.walmart.com/ip/{it.get('itemId')}",
            source=source_name, price=float(price),
            list_price=float(it["msrp"]) if it.get("msrp") else None,
            retailer="Walmart", sku=str(it.get("itemId")),
            tags=[it.get("stock", ""), "marketplace" if it.get("marketplace") else "sold-by-walmart"],
        ))
    return deals


class Walmart(Source):
    name = "walmart"
    requires = ("consumer_id", "private_key_path")

    def _headers(self) -> dict[str, str]:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        consumer_id = self.options["consumer_id"]
        key_version = str(self.options.get("key_version", "1"))
        ts = str(int(time.time() * 1000))
        with open(self.options["private_key_path"], "rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        msg = f"{consumer_id}\n{ts}\n{key_version}\n".encode()
        sig = base64.b64encode(key.sign(msg, padding.PKCS1v15(), hashes.SHA256())).decode()
        return {
            "WM_CONSUMER.ID": consumer_id,
            "WM_CONSUMER.INTIMESTAMP": ts,
            "WM_SEC.KEY_VERSION": key_version,
            "WM_SEC.AUTH_SIGNATURE": sig,
            "Accept": "application/json",
        }

    def fetch(self) -> Iterable[Deal]:
        queries = self.options.get("queries") or DEFAULT_QUERIES
        for q in queries:
            url = f"{BASE}/search?query={q}&numItems=25&sort=price&order=ascending"
            try:
                resp = self.http.get(url, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:  # noqa: BLE001
                self.log.warning("query %r failed: %s", q, e)
                continue
            deals = parse_search(data, self.name)
            self.log.info("query %r: %d items", q, len(deals))
            yield from deals
