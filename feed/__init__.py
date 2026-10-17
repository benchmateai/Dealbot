"""Raw market data feeds. A feed only delivers ticks; it never decides anything."""

from feed.base import FeedError, MarketFeed, Tick
from feed.replay import ReplayFeed
from feed.synthetic import SyntheticFeed

__all__ = ["FeedError", "MarketFeed", "ReplayFeed", "SyntheticFeed", "Tick", "make_feed"]


def make_feed(
    kind: str,
    symbols: tuple[str, ...],
    *,
    start_ms: int,
    replay_path: str | None = None,
    seed: int = 7,
    tick_ms: int = 1000,
    start_prices: dict[str, float] | None = None,
) -> MarketFeed:
    if kind == "synthetic":
        return SyntheticFeed(symbols, start_ms=start_ms, seed=seed, tick_ms=tick_ms, start_prices=start_prices)
    if kind == "replay":
        if not replay_path:
            raise FeedError("FEED=replay needs FEED_REPLAY_PATH")
        return ReplayFeed(replay_path, symbols)
    raise FeedError(f"unknown feed kind {kind!r}")
