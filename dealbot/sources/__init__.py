from dealbot.sources.base import Source
from dealbot.sources.bestbuy import BestBuy
from dealbot.sources.feeds import DealNews, FeedSource, Slickdeals, Woot
from dealbot.sources.keepa import Keepa
from dealbot.sources.reddit import Reddit
from dealbot.sources.walmart import Walmart
from dealbot.sources.watchlist import Watchlist

REGISTRY: dict[str, type[Source]] = {
    cls.name: cls for cls in (Reddit, Slickdeals, DealNews, Woot, FeedSource, BestBuy, Walmart, Keepa, Watchlist)
}

__all__ = ["REGISTRY", "Source"]
