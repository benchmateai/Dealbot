"""The shadow lab: records Kalshi market data and replays shadow strategies on it, beside the live paper desk.

It only reads. There is no order code anywhere in this package: public GET requests, and with a key
(KALSHI_PROD_API_KEY_ID / KALSHI_PROD_PRIVATE_KEY) WebSocket market-data subscriptions. Its data lives
in lab/data on the shadow-run branch, apart from the paper desk's record.

Strategies (registered in lab/strategies, judged only on data after their registration time):
  A  the repaired model as a control: market-anchored, settlement-aware, index-corrected (taker)
  B  late-window tail harvesting in the 15-minute contracts (taker)
  C  settlement-aware crypto market making, bounded from above (maker)
  D  consistency scanner: hourly ladders, range brackets, and the 15-minute contract against the hourly ladder
  E  liquidity-incentive capture, reward rebuilt from Kalshi's formula less markouts (maker)
  F  maker long-shot fade: resting NO bids at 90-99 cents in markets heavy with recreational YES buying (maker)
"""
