"""Kalshi 15-minute crypto binaries as a venue for the desk: market data, request signing, the
code-owned baseline probability, a binary paper broker with Kalshi's fee formula and settlement.
Paper only here; no order endpoint is wired to the trading loop."""

from kalshi.api import ContractInfo, KalshiApiError, KalshiClient, maker_fee_usd, parse_market, taker_fee_usd
from kalshi.auth import KEY_ID_ENV, PRIVATE_KEY_ENV, KalshiAuth, KalshiAuthError, load_private_key_bytes, load_private_key_pem
from kalshi.broker import BinaryPaperBroker
from kalshi.feed import KalshiFeed, Settlement
from kalshi.model import distance_bps, p_above

__all__ = [
    "KEY_ID_ENV", "PRIVATE_KEY_ENV", "BinaryPaperBroker", "ContractInfo", "KalshiApiError", "KalshiAuth", "KalshiAuthError",
    "KalshiClient", "KalshiFeed", "Settlement", "distance_bps", "load_private_key_bytes", "load_private_key_pem", "maker_fee_usd", "p_above", "parse_market", "taker_fee_usd",
]
