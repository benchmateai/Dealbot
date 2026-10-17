"""RSS/Atom based sources: Slickdeals, DealNews, Woot, and any custom feed.

These are the fastest places pricing errors surface: the community posts a
mistake within minutes, usually with "price error" right in the title.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timezone
from typing import Iterable

import feedparser

from dealbot.models import Deal
from dealbot.prices import parse_prices
from dealbot.sources.base import Source


def _entry_time(entry) -> datetime | None:
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc) if t else None


def _strip_html(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", " ", s or "")


def parse_feed(content: bytes | str, source_name: str) -> list[Deal]:
    parsed = feedparser.parse(content)
    deals: list[Deal] = []
    for e in parsed.entries:
        title = (e.get("title") or "").strip()
        link = (e.get("link") or "").strip()
        if not title or not link:
            continue
        summary = _strip_html(e.get("summary") or e.get("description") or "")
        price, list_price = parse_prices(title)
        if price is None:
            price, list_price = parse_prices(summary[:400])
        elif list_price is None:
            # Title has only the sale price; the body often says "Regularly $X".
            _, lp = parse_prices(summary[:400])
            if lp is not None and lp > price:
                list_price = lp
        tags = [t.get("term", "") for t in e.get("tags", []) if t.get("term")]
        deals.append(Deal(
            title=title, url=link, source=source_name, price=price, list_price=list_price,
            text=summary[:1000], tags=tags, posted_at=_entry_time(e),
        ))
    return deals


class FeedSource(Source):
    name = "feed"

    def feeds(self) -> list[str]:
        return list(self.options.get("feeds") or [])

    def fetch(self) -> Iterable[Deal]:
        for url in self.feeds():
            try:
                resp = self.http.get(url)
                resp.raise_for_status()
            except Exception as e:  # noqa: BLE001
                self.log.warning("feed %s failed: %s", url, e)
                continue
            deals = parse_feed(resp.content, self.name)
            self.log.info("%s: %d entries", url, len(deals))
            yield from deals


class Slickdeals(FeedSource):
    name = "slickdeals"
    DEFAULT_FEEDS = [
        # Front page + popular deals.
        "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1",
        "https://slickdeals.net/newsearch.php?mode=popdeals&searcharea=deals&searchin=first&rss=1",
        # Live search for the words people use when they spot a mistake.
        "https://slickdeals.net/newsearch.php?q=price+error&searcharea=deals&searchin=first&rss=1",
        "https://slickdeals.net/newsearch.php?q=price+mistake&searcharea=deals&searchin=first&rss=1",
        "https://slickdeals.net/newsearch.php?q=glitch&searcharea=deals&searchin=first&rss=1",
    ]

    def feeds(self) -> list[str]:
        return list(self.options.get("feeds") or self.DEFAULT_FEEDS)


class DealNews(FeedSource):
    name = "dealnews"
    DEFAULT_FEEDS = ["https://www.dealnews.com/rss/"]

    def feeds(self) -> list[str]:
        return list(self.options.get("feeds") or self.DEFAULT_FEEDS)


class Woot(FeedSource):
    name = "woot"
    DEFAULT_FEEDS = ["https://www.woot.com/feed/all"]

    def feeds(self) -> list[str]:
        return list(self.options.get("feeds") or self.DEFAULT_FEEDS)
