from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Query params that only track the click and never change the product.
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "ref_", "tag", "linkcode", "linkid", "psc", "fbclid", "gclid",
    "cm_mmc", "irclickid", "irgwc", "afsrc", "sid", "src", "u1", "subid",
}

# Hostname -> human retailer name. Keys are matched as suffixes.
RETAILERS = {
    "amazon.com": "Amazon",
    "amzn.to": "Amazon",
    "walmart.com": "Walmart",
    "target.com": "Target",
    "bestbuy.com": "Best Buy",
    "homedepot.com": "Home Depot",
    "lowes.com": "Lowe's",
    "costco.com": "Costco",
    "samsclub.com": "Sam's Club",
    "ebay.com": "eBay",
    "newegg.com": "Newegg",
    "bhphotovideo.com": "B&H",
    "adorama.com": "Adorama",
    "microcenter.com": "Micro Center",
    "woot.com": "Woot",
    "macys.com": "Macy's",
    "kohls.com": "Kohl's",
    "nordstrom.com": "Nordstrom",
    "nordstromrack.com": "Nordstrom Rack",
    "jcpenney.com": "JCPenney",
    "wayfair.com": "Wayfair",
    "overstock.com": "Overstock",
    "gamestop.com": "GameStop",
    "staples.com": "Staples",
    "officedepot.com": "Office Depot",
    "dell.com": "Dell",
    "lenovo.com": "Lenovo",
    "hp.com": "HP",
    "apple.com": "Apple",
    "nike.com": "Nike",
    "adidas.com": "adidas",
    "chewy.com": "Chewy",
    "petsmart.com": "PetSmart",
    "walgreens.com": "Walgreens",
    "cvs.com": "CVS",
    "academy.com": "Academy Sports",
    "dickssportinggoods.com": "Dick's",
    "rei.com": "REI",
    "zappos.com": "Zappos",
    "lego.com": "LEGO",
    "steampowered.com": "Steam",
}


def retailer_from_url(url: str) -> str:
    host = urlsplit(url).netloc.lower()
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    for suffix, name in RETAILERS.items():
        if host == suffix or host.endswith("." + suffix):
            return name
    return host or "unknown"


def canonical_url(url: str) -> str:
    """Strip tracking params and fragments so the same product dedupes."""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
             if k.lower() not in _TRACKING_PARAMS]
    path = re.sub(r"/+$", "", parts.path) or "/"
    return urlunsplit((parts.scheme.lower() or "https", parts.netloc.lower(), path,
                       urlencode(sorted(query)), ""))


@dataclass
class Deal:
    title: str
    url: str
    source: str                      # which source module produced it
    price: Optional[float] = None
    list_price: Optional[float] = None
    retailer: Optional[str] = None
    text: str = ""                   # body / description, used for keyword signals
    tags: list[str] = field(default_factory=list)   # flair, categories, etc.
    sku: Optional[str] = None
    posted_at: Optional[datetime] = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.url = self.url.strip()
        if not self.retailer:
            self.retailer = retailer_from_url(self.url)
        if self.posted_at is None:
            self.posted_at = datetime.now(timezone.utc)

    @property
    def key(self) -> str:
        """Stable id used for de-duplication across runs and sources."""
        basis = self.sku and f"{self.retailer}:{self.sku}" or canonical_url(self.url)
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]

    @property
    def discount(self) -> Optional[float]:
        """Fractional discount (0.9 == 90% off), or None if unknown."""
        if self.price is None or not self.list_price or self.list_price <= 0:
            return None
        if self.price > self.list_price:
            return None
        return round(1 - self.price / self.list_price, 4)


@dataclass
class Alert:
    deal: Deal
    score: int
    reasons: list[str]

    @property
    def discount_pct(self) -> Optional[int]:
        d = self.deal.discount
        return None if d is None else int(round(d * 100))
