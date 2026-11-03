"""Re-record the live fixtures (public endpoints only, never signed). Run from the repository root:

    python tests/fixtures/record.py

Kalshi rate-limits unauthenticated reads per address, so the script paces itself and retries.
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
COINBASE = "https://api.exchange.coinbase.com"


def get(url: str) -> dict:
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "dealbot-desk/0.1"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("unreachable")


def save(name: str, data: dict) -> None:
    (HERE / name).parent.mkdir(parents=True, exist_ok=True)
    (HERE / name).write_text(json.dumps(data, indent=1))
    print("wrote", name)


def main() -> None:
    for series in ("KXETH15M", "KXBTC15M"):
        markets = get(f"{KALSHI}/markets?series_ticker={series}&status=open&limit=5")
        save(f"kalshi/markets_open_{series}.json", markets)
        live = sorted((m for m in markets["markets"] if m.get("status") == "active"), key=lambda m: m["close_time"])
        if live:
            ticker = live[0]["ticker"]
            save(f"kalshi/market_{series}.json", get(f"{KALSHI}/markets/{ticker}"))
            save(f"kalshi/orderbook_{series}.json", get(f"{KALSHI}/markets/{ticker}/orderbook"))
        save(f"kalshi/markets_settled_{series}.json", get(f"{KALSHI}/markets?series_ticker={series}&status=settled&limit=24"))
        time.sleep(3)
    for product in ("ETH-USD", "BTC-USD"):
        save(f"coinbase/book_{product}.json", get(f"{COINBASE}/products/{product}/book?level=1"))


if __name__ == "__main__":
    main()
