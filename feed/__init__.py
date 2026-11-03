"""Raw market data feeds. A feed only delivers ticks; it never decides anything."""

from feed.base import FeedError, MarketFeed, Tick
from feed.coinbase import CoinbaseFeed
from feed.replay import ReplayFeed
from feed.synthetic import SyntheticFeed

__all__ = ["CoinbaseFeed", "FeedError", "MarketFeed", "ReplayFeed", "SyntheticFeed", "Tick", "make_feed"]


def make_feed(
    kind: str,
    symbols: tuple[str, ...],
    *,
    start_ms: int,
    replay_path: str | None = None,
    seed: int = 7,
    tick_ms: int = 1000,
    start_prices: dict[str, float] | None = None,
    base_url: str | None = None,
    poll_ms: int = 2000,
    kalshi: dict | None = None,
) -> MarketFeed:
    if kind == "synthetic":
        return SyntheticFeed(symbols, start_ms=start_ms, seed=seed, tick_ms=tick_ms, start_prices=start_prices)
    if kind == "kalshi":
        from kalshi.api import KalshiClient
        from kalshi.feed import KalshiFeed

        opts = dict(kalshi or {})
        underlying = opts.get("underlying") or {}
        products = tuple(sorted(set(underlying.get(s) for s in symbols if underlying.get(s))))
        if len(products) != len([s for s in symbols]):
            pass  # several series may share an underlying product; that is fine
        if not products:
            raise FeedError("kalshi feed needs KALSHI_UNDERLYING entries for every series")
        under = CoinbaseFeed(products, poll_ms=poll_ms)
        # The feed only reads public market data, so it carries no credentials whatever the environment holds.
        client = KalshiClient(opts.get("base_url") or "https://api.elections.kalshi.com")
        return KalshiFeed(symbols, underlying=underlying, client=client, underlying_feed=under, poll_ms=poll_ms, block_ms=int(opts.get("block_ms") or 12_000), trade_window_s=float(opts.get("trade_window_s") or 600.0), min_time_left_s=float(opts.get("min_time_left_s") or 30.0), rv_window_blocks=int(opts.get("rv_window_blocks") or 20), settle_wait_s=float(opts.get("settle_wait_s") or 120.0))
    if kind == "coinbase":
        return CoinbaseFeed(symbols, poll_ms=poll_ms, **({"base_url": base_url} if base_url else {}))
    if kind == "replay":
        if not replay_path:
            raise FeedError("FEED=replay needs FEED_REPLAY_PATH")
        return ReplayFeed(replay_path, symbols)
    raise FeedError(f"unknown feed kind {kind!r}")
