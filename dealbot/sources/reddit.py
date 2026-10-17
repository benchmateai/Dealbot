"""Reddit deal subreddits via the public JSON listing (no API key needed).

r/PriceErrors exists specifically for this. r/deals, r/buildapcsales and
friends flair posts and the titles carry the price + list price.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from dealbot.models import Deal
from dealbot.prices import parse_prices
from dealbot.sources.base import Source

DEFAULT_SUBREDDITS = [
    "PriceErrors", "deals", "buildapcsales", "frugalmalefashion", "GameDeals",
    "Flipping", "dealsreddit",
]


def parse_listing(data: dict, source_name: str = "reddit") -> list[Deal]:
    deals: list[Deal] = []
    for child in (data.get("data") or {}).get("children") or []:
        d = child.get("data") or {}
        title = (d.get("title") or "").strip()
        if not title or d.get("removed_by_category") or d.get("stickied"):
            continue
        permalink = "https://www.reddit.com" + (d.get("permalink") or "")
        url = d.get("url_overridden_by_dest") or d.get("url") or permalink
        if d.get("is_self") or url.startswith("https://www.reddit.com/r/"):
            url = permalink
        text = d.get("selftext") or ""
        price, list_price = parse_prices(title)
        if price is None:
            price, list_price = parse_prices(text[:500])
        elif list_price is None:
            _, lp = parse_prices(text[:500])
            if lp is not None and lp > price:
                list_price = lp
        tags = [t for t in (d.get("link_flair_text"), d.get("subreddit")) if t]
        created = d.get("created_utc")
        deals.append(Deal(
            title=title, url=url, source=source_name, price=price, list_price=list_price,
            text=text[:1000], tags=tags,
            posted_at=datetime.fromtimestamp(created, tz=timezone.utc) if created else None,
            extra={"permalink": permalink, "score": d.get("score", 0), "comments": d.get("num_comments", 0)},
        ))
    return deals


class Reddit(Source):
    name = "reddit"

    def fetch(self) -> Iterable[Deal]:
        subs = self.options.get("subreddits") or DEFAULT_SUBREDDITS
        limit = int(self.options.get("limit", 50))
        for sub in subs:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit={limit}&raw_json=1"
            try:
                resp = self.http.get(url, headers={"Accept": "application/json"})
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:  # noqa: BLE001
                self.log.warning("r/%s failed: %s", sub, e)
                continue
            deals = parse_listing(data, self.name)
            self.log.info("r/%s: %d posts", sub, len(deals))
            yield from deals
