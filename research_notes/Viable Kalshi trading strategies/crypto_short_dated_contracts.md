# Automated strategies for Kalshi short-dated crypto contracts (15-minute, hourly, daily BTC/ETH), with Polymarket lessons

Research date: 2026-11-03. Every return, win rate or profit figure below is an unverified claim unless it says "own analysis". The own analysis was run in this session on public Kalshi and Coinbase data, and its method and limits are stated where it is cited.

Source-access caveat for the report writer: this session's network policy blocked full-text fetches from kalshi.com, docs.kalshi.com, help.kalshi.com, cfbenchmarks.com, docs.polymarket.com, arxiv.org, ssrn.com, karlwhelan.com, predictionmarketspicks.com, financemagnates.com, reddit.com, medium.com and most news sites. Findings from those domains come from search-engine result summaries, not the full text, and are marked "(search summary)". Primary sources read directly were: Kalshi's public API (market rules, series fee settings, order books, settled markets, candlesticks), Kalshi's public contract-terms bucket (kalshi-public-docs.s3.amazonaws.com), Coinbase Exchange public candles, and GitHub READMEs via raw.githubusercontent.com. To verify the search-summary items, these hosts would need to be allowed in the session network settings.

## Q1. How do Kalshi's 15-minute, hourly and daily crypto contracts settle, what does the 60-second average imply for late pricing, and do practitioners exploit the averaging window or the gap between the index and a single exchange?

### Takeaway
Every Kalshi BTC/ETH price contract settles on a simple average of 60 one-per-second CF Benchmarks Real-Time Index values (BRTI for BTC, ETHUSD_RTI for ETH) in the minute before the close. The 15-minute "up" contract resolves Yes if that closing average is at least the same 60-second average taken just before the window opened. That strike is published as `floor_strike`. The hourly and daily ladders use strictly "above" strikes set at xx99.99. The average has two effects. Before the last minute, the variance that remains is that of about τ − 40 s of point-spot time. Inside the last minute, part of the average is already fixed, so a point-spot model is badly wrong there, sometimes even about which side wins. Kalshi now streams the settlement index itself, including trailing 60-second averages, over an authenticated WebSocket. In own analysis, using a Coinbase last-trade price as the proxy got the settled outcome wrong in about 5% of 15-minute markets.

### Cited Findings
**Contract rules (primary, read directly)**
- KXBTC15M rule text, live market on 2026-11-03: "If the simple average of the sixty seconds of CF Benchmarks' BRTI before 2:30 PM EST on Nov 3, 2026 is at least the simple average of the sixty seconds of CF Benchmarks' BRTI before 2:15 PM EST on November 3, 2026, then the market resolves to Yes." strike_type = `greater_or_equal`. The opening average is published as `floor_strike` (77441.74 in that market). — [Kalshi API, open KXBTC15M markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=open)
- Secondary rule text, the same for BTC and ETH 15-minute markets: "Not all cryptocurrency price data is the same. While checking a source like Google or Coinbase may help guide your decision, the price used to determine this market is based on CF Benchmarks' corresponding Real Time Index (RTI). At the last minute before expiration, 60 RTI prices are collected. The official and final value is the average of these prices, rounded to the nearest 2 decimal places." KXETH15M uses "ETHUSDRTI". — [Kalshi API, open KXETH15M markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXETH15M&status=open)
- Hourly and daily ladder (KXBTCD, series frequency "hourly"): "If the simple average of the sixty seconds of CF Benchmarks' Bitcoin Real-Time Index (BRTI) before 3 PM EST is above 86799.99 at 3 PM EST on Nov 3, 2026, then the market resolves to Yes." strike_type = `greater`, which is strict. Strikes sit at xx99.99, so with two-decimal values this works out to "≥ round number". The range series KXBTC uses the same index rule. — [Kalshi API, KXBTCD markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTCD&status=open); [Kalshi API, KXBTC series](https://api.elections.kalshi.com/trade-api/v2/series/KXBTC)
- Generic crypto contract terms (the KXBTC15M/KXETH15M series point to CRYPTO.pdf):
  - The Underlying is "a simple average of the CF <cryptocurrency> <index> for the 60 seconds prior to <time>".
  - "Above X" means strictly greater, "at least X" means X or greater, and "between X and Y" includes both ends.
  - "If no data is available or incomplete on the Expiration Date at the Expiration Time, then affected strikes resolve to No."
  - The Position Accountability Level is $25,000 per strike per Member.
  - Source: [Kalshi contract terms CRYPTO15M.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/CRYPTO15M.pdf); [series contract_terms_url](https://api.elections.kalshi.com/trade-api/v2/series/KXBTC15M)
- Bitcoin hourly terms (BTC.pdf): "simple average of the CF Bitcoin Real-Time Index ('BRTI') for the minute (60 seconds) prior to <time>"; "If no data is available on the Expiration Date at the Expiration Time, then the market resolves to No." — [Kalshi contract terms BTC.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/BTC.pdf)
- Another contract family (CRYPTOPRICE) uses a 1-minute RTI price with backup sources (CoinMarketCap, then CoinGecko) and gives a worked example: "BTC spikes to $50,001 at 2:00:30 PM but the 1-minute average is $49,998", which shows a spike inside the minute does not settle a strike. — [Kalshi contract terms CRYPTOPRICE.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/CRYPTOPRICE.pdf)

**Market mechanics (primary)**
- Price grid ("tapered_deci_cent"): $0.001 ticks from 0 to 10¢ and from 90¢ to $1, and $0.01 ticks between. — [Kalshi API market object](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=open)
- A sample settled market (KXBTC15M-26NOV031300-00) shows the settlement timing:
  - It closed 18:00:00Z and the settlement timestamp was 18:00:02.8Z. `expected_expiration_time` is close + 5 min.
  - The record has `expiration_value` 77554.23 against `floor_strike` 77577.23, so the result was "no".
  - It carries `exchange_index` 2.
  - Source: [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled)
- Shard detail: one production bot notes that "Kalshi crypto markets live on exchange shard 2". Its preflight "move[s] idle cash onto the trading shard". — [MaxExtractoor/MERID README](https://github.com/MaxExtractoor/MERID)
- Consistency check (own analysis): for all 952 settled KXBTC15M and all 952 KXETH15M markets closing 2026-10-24 to 2026-11-03, `result` matched `expiration_value ≥ floor_strike`, with no exceptions. — [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled)

**The index**
- CF Benchmarks describes BRTI as "a once a second benchmark index price for Bitcoin that aggregates order data from Bitcoin-USD markets operated by major cryptocurrency exchanges that conform to the CME CF Constituent Exchange Criteria" (search summary). — [CF Benchmarks BRTI page](https://www.cfbenchmarks.com/data/indices/BRTI)
- The original methodology builds a mid price-volume curve from the constituent order books, with the index taken from that curve (search summary). — [CME/CF BRTI methodology PDF](https://www.cmegroup.com/trading/files/bitcoin-real-time-index-methodology.pdf)
- CF Benchmarks consulted on changes to the real-time index methodology, with a proposed implementation date of 2026-05-18 (search summary). — [CF Benchmarks consultation notice](https://www.cfbenchmarks.com/blog/announcement-of-consultation-on-changes-to-the-cme-cf-real-time-index-methodology)
- One CF blog post reportedly says the calculation now runs every 200 ms under methodology v17.0 (Sept 2026). That conflicts with "once a second" above and is unverified (search summary). — [CF Benchmarks blog](https://www.cfbenchmarks.com/blog/who-signs-the-price-the-cme-cf-real-time-indices-through-cfb-oracle)

**Kalshi now serves the settlement index directly**
- The `cfbenchmarks_value` WebSocket channel streams real-time CF Benchmarks index values. Each update carries the raw upstream frame plus trailing 60-second averages and quarter-hour final-minute averages. Indices are chosen with `index_ids` (e.g., BRTI, ETHUSD_RTI) (search summary). — [Kalshi docs: CF Benchmarks Value Feed](https://docs.kalshi.com/websockets/cfbenchmarks-value)
- A `cfbenchmarks_value_5hz` channel streams indices published at 200 ms granularity: BRTI, ETHUSD_RTI, SOLUSD_RTI, XRPUSD_RTI, DOGEUSD_RTI (search summary). — [Kalshi docs: 5 Hz feed](https://docs.kalshi.com/websockets/cfbenchmarks-value-5hz)
- Historical values are available through a REST passthrough at `/trade-api/v2/cfbenchmarks/*` (search summary). — [Kalshi docs: CF Benchmarks REST passthrough](https://docs.kalshi.com/cfbenchmarks/rest-passthrough.md)
- A third-party PR mentions frame fields `last_60s_windowed_average_15min` and `avg_60s_data`. These field names are unconfirmed (search summary). — [Strata-Backend PR #117](https://github.com/PatentFiles/Strata-Backend/pull/117)
- Open-source bots already record this feed. One records "CF Benchmarks BRTI ticks incl. Kalshi's rolling 60-second settlement average". — [milesiscool/edgebook README](https://github.com/milesiscool/edgebook)

**Practitioner use of the averaging window**
- Several bots model the averaging explicitly:
  - kalshi-lab's fair value prices "the partially-fixed average inside the last minute". — [RishabKalluri/kalshi-lab README](https://github.com/RishabKalluri/kalshi-lab)
  - One bot "in final minute… switches to BRTI 60-second average tracking" and "predicts settlement value with 99%+ accuracy". That figure is an unverified claim. — [papabrosio/kalshi-btc-15min-trader README](https://github.com/papabrosio/kalshi-btc-15min-trader)
  - MERID uses a "Bachelier/TWAP probability baseline" built on the "RTI/CF Benchmarks spot reference". — [MaxExtractoor/MERID README](https://github.com/MaxExtractoor/MERID)
  - One maker bot's model is "deliberately not Black-Scholes — these contracts have their own settlement mechanics". — [artyomderkach-bit/kalshi-15m-market-maker README](https://github.com/artyomderkach-bit/kalshi-15m-market-maker)
- A third-party tape study (1,258 KXBTC15M windows, Oct 13–27, 2026) found:
  - 80–99¢ favorites "won about what they cost at every minute".
  - Takers who bought them in the final 60 seconds netted +1.90¢ per contract.
  - It argues the outcome becomes more certain, not less, in the last minute because of the 60-print average.
  - Source (search summary; unverified): [predictionmarketspicks, "The 12:30 Rule vs Our Tape"](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-last-60-seconds)

**Own analysis: Coinbase vs the BRTI settlement average**
- Data: 952 KXBTC15M and 952 KXETH15M markets closing 2026-10-24 19:30Z to 2026-11-03 19:15Z, with Coinbase 1-minute candles.
- Gap between Coinbase and the BRTI settlement average:

  | Comparison | BTC median abs. gap | BTC 90th pct | ETH median abs. gap | ETH 90th pct |
  |---|---|---|---|---|
  | Coinbase last trade before close vs settlement average | 1.42 bps | 4.23 bps | 1.72 bps | 5.16 bps |
  | Coinbase final-minute OHLC average vs settlement average | 0.98 bps | 2.27 bps | 1.16 bps | 2.79 bps |

- Coinbase traded below the settlement average on average, by 0.90 bps for BTC and 1.23 bps for ETH. — [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled); [Coinbase Exchange candles](https://api.exchange.coinbase.com/products/BTC-USD/candles)
- Outcome errors from Coinbase proxies (own analysis, same data):

  | Proxy rule | BTC wrong outcome | ETH wrong outcome |
  |---|---|---|
  | Coinbase last trade at the close vs the Kalshi strike | 5.57% | 4.73% |
  | Coinbase final-minute OHLC average vs the Kalshi strike | 3.57% | 2.63% |
  | Coinbase close vs Coinbase price at the open (strike also from Coinbase) | 6.20% | 5.46% |

  Source: [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXETH15M&status=settled); [Coinbase Exchange candles](https://api.exchange.coinbase.com/products/ETH-USD/candles)

**Polymarket contrast**
- Polymarket's 5-minute BTC contract (launched 2026-02-12) settles on Chainlink prices at single timestamps. A Stanford/SMU paper found:
  - Spot order flow in the final ~10 s before close was about 50% above pre-launch levels, followed by rapid reversals.
  - Coverage cites 821 suspected traders earning $8.2M. Another outlet's headline says $1.28M, so the figure is unresolved.
  - The pattern was "much attenuated" in 15-minute contracts.
  - Polymarket said it plans to move some markets to averaged prices, and denied that manipulation occurred.
  - Sources (search summary): [arXiv 2606.31675](https://arxiv.org/abs/2606.31675); [Bitcoin Magazine coverage](https://bitcoinmagazine.com/news/traders-took-8-2-million-from-polymarkets); [Bitcoin.com coverage](https://news.bitcoin.com/stanford-study-polymarket-bitcoin-manipulation/)
- A Polymarket 15-minute market-making bot used "Coinbase… current underlying-price proxy and a locally sampled opening reference", with "Chainlink observations… recorded near window boundaries". — [QuantumSlayer/poly-15min README](https://github.com/QuantumSlayer/poly-15min)

### Inferences
- **Pricing math (Brownian approximation, σ per √second).** Let τ be the time left to the close.
  - At any time t with τ ≥ 60 s, the settlement average A has variance σ²[(τ − 60) + 60/3] = σ²(τ − 40 s). The right "time to expiry" is therefore about 40 s shorter than the clock says. At τ = 120 s this shrinks the standard deviation by √(80/120) ≈ 0.82, so z-scores are about 22% larger.
  - Inside the averaging minute, with r seconds left: E[A] = (sum of the prints already fixed + r·S_t)/60, and sd(A) = σ·√(r³/10,800).
  - At r = 30 s that is σ·1.58, against σ·5.48 for a point-spot model: about 3.5× smaller.
  - Worked case: the first 45 s of the window averaged $30 above the strike and spot is now $10 below it with 15 s left. Then E[A] − K = (45·30 − 15·10)/60 = +$20. The contract is a near-certain Yes while a point-spot model favours No.
- The 15-minute strike is not a Coinbase price. It is the BRTI 60-second average before the open, and it is known exactly from `floor_strike` once the window opens.
- Any model built on one exchange's spot carries a basis of about 1–2 bps median that is not centred on zero (Coinbase ran about 1 bp low in own data). In the last few minutes σ√τ is only a few bps, so that bias is a sizeable fraction of a standard deviation.
- The fix is mechanical: subscribe to `cfbenchmarks_value` (or the 5 Hz variant) and use Kalshi's own trailing 60-second average.
- The averaging window is not, by itself, an exploitable inefficiency. Top-of-book spreads collapse to 0.1¢ at ≤3 minutes, and the market's late calibration is excellent (Q3). Market makers clearly already price the partially-fixed average. The edge goes to whoever updates fastest from the real index, not to whoever merely knows about the averaging.
- The "no data → resolves No" clause is a small one-sided tail risk for YES holders at 99¢+. It only matters for strategies that collect 0.1–1¢ in the tails.
- The 60-second multi-exchange average is a design defence against the last-seconds manipulation documented on Polymarket's single-timestamp 5-minute contracts. Strategies that depend on pushing spot at the close should be treated as prohibited and impractical on Kalshi.

### Gaps
- Current BRTI and ETHUSD_RTI constituent exchanges and weights could not be verified (cfbenchmarks.com blocked).
- With a 5 Hz index published, it is unclear which tick per second Kalshi samples for its "60 RTI prices".
- Exact field names in the `cfbenchmarks_value` frames are unconfirmed.
- Whether the WebSocket index feed reaches clients with less delay than CF Benchmarks' own feed was not found.
- The own basis numbers use Coinbase 1-minute candles (last trade, OHLC average), not tick data. A true 1-second Coinbase average would likely shrink the gap somewhat.

## Q2. Latency arbitrage: do Kalshi crypto quotes lag spot exchanges, and can a bot pick off stale quotes?

### Takeaway
Latency arbitrage was real and lucrative on Polymarket's 15-minute markets in late 2025, while they had no fees. Polymarket then added taker fees in January 2026, and faster competitors arrived. Retail-grade bots report the edge vanishing once they were about 100 ms behind direct-feed participants. On Kalshi, own minute-level data shows quotes absorb almost all of a spot move within the same minute. A small leftover could be consistent with a lag of a few seconds, but 1-minute data cannot resolve that. Kalshi's taker fee (1.75¢ at 50¢), its deep professional books (more than 13,000 contracts at the best BTC bid in one snapshot) and write-rate limits make picking off stale quotes a speed race a small bot is unlikely to win.

### Cited Findings
**Polymarket: the latency-arbitrage episode and the fee response**
- Wallet "0x8dxd" reportedly grew $313 (Dec 2025) to about $438k by 2026-01-06, with a 98% win rate over 6,615 predictions, mostly on BTC/ETH/SOL 15-minute contracts. Commentary attributes this to reacting to spot faster than Polymarket's pricing. Other write-ups say about $414k. All of it is unverified (search summary). — [Medium summary](https://medium.com/@weare1010/claude-ai-trading-bots-are-making-hundreds-of-thousands-on-polymarket-2840efb9f2cd); [FinanceMagnates](https://www.financemagnates.com/cryptocurrency/polymarket-introduces-dynamic-fees-to-curb-latency-arbitrage-in-short-term-crypto-markets/)
- The fee response, reported early 2026 (search summaries):
  - Polymarket added dynamic taker fees on 15-minute BTC/ETH/SOL/XRP markets, funding maker rebates, explicitly to curb latency arbitrage.
  - The reported bot pattern was: watch for small delays between Polymarket prices and spot exchanges, enter near 50/50, and exit when prices converge.
  - The first formula reported was fee = C × 0.25 × (p(1−p))². Cointelegraph's example is about $1.56 per 100 shares at $0.50, just over 3% of notional.
  - Sources: [Cointelegraph via TradingView](https://www.tradingview.com/news/cointelegraph:e59c32089094b:0-polymarket-quietly-introduces-taker-fees-on-15-minute-crypto-markets/); [CoinMarketCap Academy](https://coinmarketcap.com/academy/article/polymarket-introduces-fees-on-15-minute-crypto-bets)
- Bot vendors claim Polymarket removed a 500 ms taker delay at the same time, which hurt existing taker bots. This is unverified, vendor-sourced (search summary). — [WEEX guide](https://www.weex.com/news/detail/polymarket-new-rule-release-how-to-build-a-new-trading-bot-348468)
- Polymarket's current docs give the taker fee as C × feeRate × p × (1−p), with crypto feeRate 0.07, makers never charged, and a 20% maker rebate share (search summary).
  - One third-party guide says the crypto rate eased from 0.072 to 0.07 in July 2026. Another says the 0.25-with-exponent-2 form applied before 2026-03-30. Both are unverified.
  - Sources: [Polymarket docs: Fees](https://docs.polymarket.com/trading/fees); [startpolymarket fee guide](https://startpolymarket.com/learn/polymarket-fees/); [predictionhunt fee guide](https://www.predictionhunt.com/blog/polymarket-fees-complete-guide)

**Measured or claimed reaction times**
- OpenMarket (arXiv, July 2026) reports Polymarket quotes react to large Binance moves after a median of 347 ms, using a clock-sync-free method. Top-of-book spreads are usually one tick (search summary). — [arXiv 2607.26245](https://arxiv.org/html/2607.26245v1)
- Another Polymarket order-book paper warns that timestamp gaps in archived data often measure the collector's pipeline ("archive ingestion latency"), not exchange latency (search summary). — [arXiv 2604.24366](https://arxiv.org/pdf/2604.24366)
- A Polymarket 15-minute market-making bot was "profitable on BTC for a period and stopped being profitable in late December 2025… This system relied on secondhand exchange data and was at least 100 milliseconds behind participants with direct exchange access. That delay erased its trading advantage." Its profits "were only a tiny fraction of those earned by the top accounts." — [QuantumSlayer/poly-15min README](https://github.com/QuantumSlayer/poly-15min)
- A Kalshi bot README asserts that "Kalshi contract prices reprice with a 3-7 second lag relative to spot movements" against Binance updates about every 200 ms. This is an unverified assertion with no measurement shown. — [brandononchain/kalshibot README](https://github.com/brandononchain/kalshibot)

**Infrastructure and limits**
- From a home connection, the Kalshi feed measured about 90 ms. The kalshi-lab author recommends an always-on box in AWS us-east-1 ("closest to Kalshi") and warns: "Re-run at 2–3× latency. An edge that disappears at 300ms is a latency race you'll lose live." — [RishabKalluri/kalshi-lab README](https://github.com/RishabKalluri/kalshi-lab)
- Kalshi rate-limit tiers (reads/writes per second), per Kalshi's official docs (search summary):

  | Tier | Reads/s | Writes/s | Requirement |
  |---|---|---|---|
  | Basic | 20 | 10 | Signup |
  | Advanced | 30 | 30 | Advanced API form |
  | Premier | 100 | 100 | 3.75% of monthly exchange volume |
  | Prime | 400 | 400 | 7.5% of monthly exchange volume |

  Only create, batch-create and cancel orders count as writes. An older Kalshi page says FIX access comes with premier access. No public colocation information was found. — [Kalshi docs: rate limits](https://docs.kalshi.com/getting_started/rate_limits); [legacy tiers page](https://trading-api.readme.io/reference/tiers-and-rate-limits)
- Kalshi's WebSocket requires authentication to connect, even for public channels. The connection needs headers KALSHI-ACCESS-KEY, -SIGNATURE and -TIMESTAMP. `orderbook_delta` sends a snapshot and then deltas. The production host is wss://external-api-ws.kalshi.com/trade-api/ws/v2 (search summary). — [Kalshi docs: WebSocket connection](https://docs.kalshi.com/websockets/websocket-connection); [Kalshi AsyncAPI spec](https://docs.kalshi.com/asyncapi.yaml)

**Kalshi order book and fee at 50¢**
- Order-book snapshot on 2026-11-03 for the 19:15–19:30Z window:

  | Market | Best YES bid | YES ask | Spread |
  |---|---|---|---|
  | KXBTC15M | 48¢ × 13,560 contracts | 49¢ (NO bid 51¢ × 4,507) | 1¢ |
  | KXETH15M | 44¢ × 999 contracts | 46¢ (NO bid 54¢ × 681) | 2¢ |

  The top ten levels on each side held tens of thousands of BTC contracts. — [Kalshi API orderbook](https://api.elections.kalshi.com/trade-api/v2/markets/KXBTC15M-26NOV031430-30/orderbook)
- The KXBTC15M/KXETH15M series have fee_type "quadratic" and fee_multiplier 1, so the taker fee is 0.07 × C × P × (1−P): 1.75¢ per contract at 50¢. — [Kalshi API series KXBTC15M](https://api.elections.kalshi.com/trade-api/v2/series/KXBTC15M); [coloshword/kalshi-15m-backtest README](https://github.com/coloshword/kalshi-15m-backtest)

**Own analysis: minute-level lead-lag**
- Each pair compares the change in logit(Kalshi mid) over a minute with Coinbase returns in the same and in the previous minute:

  | Asset | Minute pairs | Corr., same minute | Corr., previous minute | Previous/same OLS beta ratio |
  |---|---|---|---|---|
  | BTC | 10,175 | +0.695 | +0.049 | ≈ 0.076 |
  | ETH | 10,193 | +0.681 | +0.032 | ≈ 0.098 |

  Source: [Kalshi batch candlesticks](https://api.elections.kalshi.com/trade-api/v2/markets/candlesticks); [Coinbase candles](https://api.exchange.coinbase.com/products/BTC-USD/candles)
- Own taker simulation at 1-minute marks: a point-spot model with 4-minute realized vol (close to the requester's setup) lost money or broke even at every horizon and threshold tested, for both BTC and ETH. Examples:
  - BTC, 5 min left, 6¢ threshold: −4.28¢ per contract (t = −1.96).
  - ETH, 10 min left, 6¢ threshold: −6.28¢ per contract (t = −2.86).
  - Source: [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled)

**Cross-venue arbitrage**
- A Polymarket–Kalshi BTC 1-hour detector (257 stars) flags "risk-free" pairs when the combined cost of the two legs is under $1. It ignores the different settlement sources. — [CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot README](https://github.com/CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot)
- A vendor blog claims cross-platform Kalshi–Polymarket windows fell from an average 12.3 s in 2024 to 2.7 s in Q1 2026. It cites an arXiv estimate of about $40M of arbitrage extracted from Apr 2024 to Apr 2025. Both are unverified (search summary). — [Turbine blog](https://www.turbinefi.com/blog/prediction-market-arbitrage-latency-speed-2026)

### Inferences
- The minute-level carryover is small but statistically clear. Under a crude uniform-intraminute assumption, a beta ratio of 0.08–0.10 matches a lag of roughly 4–6 s. The same signature can also come from Kalshi's candle "close" being the last quote update in a minute, or from Coinbase leading or lagging BRTI. So it is an upper bound on the visible lag, not proof of tradable staleness. Telling the two apart needs tick-level WebSocket timestamps.
- Break-even arithmetic for a stale-quote taker at about 50¢: the edge captured must exceed 1.75¢ plus slippage. At a typical 15-minute BTC vol of about 20 bps per 15 minutes, a 1¢ change in fair value at 50¢ corresponds to a spot move of roughly 0.5 bps. Picking off a quote for 1.75¢ therefore needs a spot move of more than 1 bp that market makers have not yet re-quoted. Market makers re-quote that within seconds or less (Polymarket evidence: about 347 ms median).
- Latency arbitrage needs the whole fast stack: direct spot feeds (Coinbase/Binance/Kraken WebSockets; Binance perps lead price discovery in the Polymarket bots), the Kalshi authenticated WebSocket, and colocation-grade hosting (us-east-1). Basic-tier writes are only 10 per second. Paper testing cannot be honest because the outcome depends on live race results against other takers and on market-maker cancel speed.
- The Polymarket lesson transfers directly. Once fees appear, or once faster players with direct feeds arrive, a retail latency edge turns negative within weeks.

### Gaps
- No tick-level measurement of Kalshi crypto quote latency versus BRTI or exchange spot was found. Own data is 1-minute only.
- Whether Kalshi offers colocation or FIX to non-Premier members in 2026 is not confirmed.
- No Reddit or practitioner account of a successful Kalshi crypto latency-arb bot was found. Reddit was not reachable.

## Q3. Do option-style volatility models beat Kalshi prices, and is there a favorite-longshot bias or systematic mispricing in these contracts?

### Takeaway
Across every careful test found, including own analysis on 1,904 recent 15-minute markets, the Kalshi mid is as good as or better than option-style models (Black-Scholes or Bachelier digitals with realized or Deribit vol) as a forecast. From 7 minutes to 1 minute before close, the market's calibration slope is 0.96–1.04 for BTC and 0.96–1.10 for ETH. That is, prices are already about as confident as they should be. Kalshi-wide studies find a favorite-longshot bias driven partly by fees. In 15-minute crypto it is weak: favorites at 80–99¢ roughly earn their price, and only the sub-5¢ tail looks slightly overpriced. Model-versus-market taker strategies are negative or insignificant after fees.

### Cited Findings
**Academic studies**
- Whelan, "Makers and Takers: The Economics of the Kalshi Prediction Market" (CEPR DP20631 / UCD WP2025_19), all Kalshi markets (search summary):
  - Prices are informative but show a favorite-longshot bias.
  - Low-price contracts win far less often than break-even requires. High-price contracts yield small positive returns.
  - The average return is reported as about −20% before fees and −22% after fees. The summary did not make clear the scope of that average.
  - Makers earn higher returns than takers. The bias is much stronger for takers.
  - There is some evidence the bias is shrinking.
  - Sources: [Whelan paper PDF](https://www.karlwhelan.com/Papers/Kalshi.pdf); [VoxEU column](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market)
- A challenge argues composition shifts, not the 2025 maker fee, drive measured bias. The maker return advantage at prices ≥50¢ "survives every plausible fee rate" (search summary). — [Yurchyna, SSRN 7364100](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7364100)
- Theory: with fees, prediction markets show a form of favorite-longshot bias and participants lose on average (search summary). — [Whelan, Quantitative Finance 2023](https://www.tandfonline.com/doi/full/10.1080/14697688.2023.2257756)
- Lee, Lee & Lee (International Review of Financial Analysis, 2026) treat Kalshi and Polymarket crypto contracts as cash-or-nothing digitals and invert Black-Scholes to get implied vol. They report a "robust variance risk premium" only weakly correlated with Deribit's DVOL (search summary; abstract not read). — [ScienceDirect S1057521926003601](https://www.sciencedirect.com/science/article/abs/pii/S1057521926003601)

**Open-source tests against the market**
- KXBTCD hourly vs Deribit (milanroundraise):
  - It finds a "statistically significant gap between Kalshi-implied and Deribit-implied volatility (p ≈ 5.6×10⁻⁹, n=162)".
  - The model shows an "S-shaped bias", attributed to using 30-day DVOL for contracts expiring in minutes.
  - The first trading attempt had a 24% win rate, with the top 5 trades carrying 58% of profit. No trading fees were modelled.
  - Nearest-expiry Deribit IV has no historical archive, which makes backtests hard.
  - Source: [milanroundraise/kalshi-mispricing README](https://github.com/milanroundraise/kalshi-mispricing)
- A Deribit options-implied odds vs Kalshi hourly ladder test reports "no edge". The Kalshi mid was the best forecast in both periods, ahead of raw front-expiry IV and DVOL. After fees the effect was about −1.38¢ per contract, with a confidence interval spanning zero (search summary of PR). — [milesiscool/edgebook PR #31](https://github.com/milesiscool/edgebook/pull/31)
- KXBTC15M ML experiment at 10 minutes before close:
  - Market-mid log loss 0.5500 (development) and 0.5184 (lockbox), against 0.6931 for 50/50.
  - The best ML correction (LightGBM/XGBoost, shrunk 50% toward market) improved lockbox log loss by only 0.001432.
  - The day-clustered confidence interval crossed zero.
  - Source: [AllAboutAI-YT/kalshi-btc15-ml-experiment README](https://github.com/AllAboutAI-YT/kalshi-btc15-ml-experiment)
- A 67-day dataset of 6,336 KXBTC15M markets (Jun 15–Aug 20, 2026) led its author to conclude:
  - "Kalshi midpoint was already strongly predictive versus 50/50."
  - "The best model mostly recalibrated the market midpoint."
  - "The lockbox improvement over midpoint was tiny."
  - "Kalshi-only microstructure features did not show a robust independent edge."
  - A 31-trade hypothetical replay had about 53% maximum drawdown.
  - Source: [J0shusmc/Kalshi-BTC README](https://github.com/J0shusmc/Kalshi-BTC)
- Daily KXBTCD with Black-Scholes plus XGBoost: 24 out-of-sample trades, 58.3% win rate, +3.81% per trade. Costs were modelled at only 0.5¢ per side, below Kalshi's taker fee. The sample is too small to mean anything. — [wfquiroz/kalshi-btc-arbitrage README](https://github.com/wfquiroz/kalshi-btc-arbitrage)

**Favorite and longshot replays on 15-minute markets**
- coloshword replay, KXBTC15M Oct 12–27, 2026: buying the 70–88¢ side with 6 minutes left gave 536 bets, a 77.4% win rate and −2.97¢ per contract net (95% CI −6.47 to +0.52). A coin flip gave −2.22¢ (CI −4.12 to −0.33). — [coloshword/kalshi-15m-backtest README](https://github.com/coloshword/kalshi-15m-backtest)
- A third-party tape study says 80–99¢ favorites "won about what they cost at every minute". Last-60-second takers netted +1.90¢ per contract (search summary; unverified). — [predictionmarketspicks](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-last-60-seconds)
- One project tests selling the 1–15¢ longshot band on 1,000 BTC 15-minute markets. Its README reports no results. — [mpatout/kalshi-crypto-bot README](https://github.com/mpatout/kalshi-crypto-bot)
- Another bot runs a "Favorite-Longshot Bias" rule (buy a side above 70¢ with 3+ minutes left) without reported results. — [reedjacobp/kalshi-trading-bot README](https://github.com/reedjacobp/kalshi-trading-bot)

**Own analysis: market mid vs simple models**
- Data and method:
  - 952 KXBTC15M and 952 KXETH15M markets, Oct 24–Nov 3, 2026. BTC traded $76.3k–$81.7k; YES won 47.4% (BTC) and 49.5% (ETH).
  - Quotes are 1-minute candle closes, keeping only quotes with spread ≤5¢. Spot is Coinbase.
  - Models tested:
    - p1: point-spot, 4-minute realized vol.
    - p2: point-spot, 60-minute vol.
    - p3: 60-second-average-aware (τ − 40 s), 60-minute vol.
    - p1b: 50/50 blend of p1 with 0.5, which mimics adding an uninformative forecast.
  - Sources: [Kalshi batch candlesticks](https://api.elections.kalshi.com/trade-api/v2/markets/candlesticks); [Coinbase candles](https://api.exchange.coinbase.com/products/BTC-USD/candles)
- Log loss, BTC (lower is better):

  | Minutes left | Market mid | p1 | p2 | p3 | p1b |
  |---|---|---|---|---|---|
  | 10 | 0.578 | 0.635 | 0.578 | 0.579 | 0.616 |
  | 7 | 0.468 | 0.542 | 0.466 | 0.465 | 0.548 |
  | 5 | 0.407 | 0.485 | 0.412 | 0.412 | 0.512 |
  | 3 | 0.304 | 0.359 | 0.323 | 0.321 | 0.453 |
  | 2 | 0.253 | 0.321 | 0.290 | 0.288 | 0.434 |
  | 1 | 0.183 | 0.284 | 0.269 | 0.253 | 0.426 |

- ETH at 1 minute: market 0.166, p1 0.261, p2 0.271, p3 0.225, p1b 0.426. — [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXETH15M&status=settled)
- Calibration slope from a logistic fit, BTC (1 = calibrated; above 1 = too close to 50/50; below 1 = too extreme). Values in brackets are mean |p − 0.5|.

  | Minutes left | Market mid | p1 | p2 | p3 | p1b |
  |---|---|---|---|---|---|
  | 14 | 0.86 [0.104] | 0.59 [0.123] | 0.80 | 0.78 | 1.40 [0.062] |
  | 7 | 1.02 | 0.66 | 1.10 | 1.04 | 2.19 |
  | 2 | 0.96 | 0.79 | 1.19 | 0.96 | 2.97 |
  | 1 | 1.04 [0.427] | 1.10 [0.378] | 1.85 [0.342] | 0.99 [0.410] | 3.84 [0.189] |

  Source: [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled)
- In the final 1–3 minutes the Coinbase-based models had large positive intercepts (0.2–1.0 in logit units). That means YES happened more often than they predicted, matching the about −1 bp Coinbase basis. — [Coinbase candles](https://api.exchange.coinbase.com/products/BTC-USD/candles)
- Model-vs-market taker simulations (buy at the candle-close ask or bid when the model beats it by 3¢ or 6¢, minus the 0.07·P(1−P) fee):
  - BTC, 7 minutes left: positive for p2/p3, +5.5 to +6.8¢ per contract (about 250–500 trades, t = 2.4–3.3).
  - BTC at other horizons: weaker, with t from −1.3 to +1.4.
  - ETH: negative or zero at nearly every horizon, e.g. p3 at 7 minutes −2.6¢ to −5.7¢ (t −1.4 to −2.1).
  - p1, the requester-like model, never showed a reliable positive result.
  - Source: [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled)
- Market calibration by price bucket (own analysis):

  | Bucket | Minutes left | Asset | n | Mean mid | Realised YES | Favorite taker P&L after fee |
  |---|---|---|---|---|---|---|
  | 95–100¢ | 3 | BTC | 210 | 0.986 | 1.000 | +1.25¢ |
  | 95–100¢ | 2 | BTC | 215 | 0.989 | 0.986 | −0.38¢ |
  | 95–100¢ | 1 | BTC | 154 | 0.989 | 0.987 | −0.31¢ |
  | 95–100¢ | 2 | ETH | 257 | 0.988 | 0.996 | +0.59¢ |
  | 95–100¢ | 1 | ETH | 161 | 0.990 | 1.000 | +0.80¢ |
  | 0–5¢ | 1 | BTC | 188 | 0.010 | 0.000 | — |
  | 0–5¢ | 7 | ETH | 68 | 0.028 | 0.000 | — |
  | 85–95¢ | 2 | BTC | 74 | 0.906 | 0.865 | −4.9¢ |
  | 85–95¢ | 5 | BTC | 100 | 0.905 | 0.870 | — |

  Source: [Kalshi batch candlesticks](https://api.elections.kalshi.com/trade-api/v2/markets/candlesticks)

**Fee hurdle**
- Taker fee examples:

  | Price | Fee per contract | Note |
  |---|---|---|
  | 50¢ | 1.75¢ | |
  | 70¢ | 1.47¢ | Break-even win rate 71.47% |
  | 95¢ | 0.3325¢ | |

  Source: [coloshword/kalshi-15m-backtest README](https://github.com/coloshword/kalshi-15m-backtest)

### Inferences
- The market is well calibrated where the requester trades. A model whose probabilities sit closer to 50/50 than the market's is very likely underconfident (wrong), not cautious-and-right.
- The BTC 7-minute positive simulation is the only possible "model beats market" signal found. Reasons to distrust it:
  - It is one of 84 correlated tests.
  - It covers one 10-day, mildly down-trending stretch, with correlated neighbouring windows.
  - It fills at candle-close quotes, which flatters a taker.
  - It does not appear for ETH or at neighbouring horizons.
  - It may simply be the seconds-scale staleness from Q2 (model sees spot at t, while the quote is the last update before t).
  - It deserves at most a pre-registered forward test with real order-book timestamps.
- Favorite-longshot bias in these contracts is mostly a tail phenomenon (<5¢ longshots overpriced by tenths of a cent to about 2¢). Fees there are tiny: about 0.07¢ at 99¢ and 0.33¢ at 95¢. A maker or late taker can harvest only fractions of a cent per contract, with rare full losses. The 85–95¢ bucket was, if anything, overpriced in own data. Generic "buy favorites" rules lose after fees (coloshword).
- Deribit implied vol is the wrong horizon for 15-minute and 1-hour digitals: 30-day DVOL, with no historical front-expiry data. It adds little over realized vol plus the market's own implied vol. The variance-risk-premium finding (IRFA) suggests Kalshi digitals carry vol above realized. In principle a seller (maker on the cheap side) collects that premium. That is a market-making thesis, not a taker one.

### Gaps
- Full texts of Whelan, Yurchyna and the IRFA paper were not readable. Crypto-specific or 15-minute-specific favorite-longshot numbers from those papers are unknown.
- Hourly and daily ladder calibration (KXBTCD/KXBTC away-from-the-money strikes) was not analysed here; only the 15-minute series was.
- The own sample covers 10 days. Calibration in high-vol regimes (crashes, US data releases) is untested.

## Q4. Market making: who provides liquidity, what are spreads and fees, and can a small bot compete?

### Takeaway
BTC 15-minute markets are deep and tight: 1¢ spreads early, 0.1¢ late, about 3.1M contracts traded per window. That points to institutional market makers (SIG; Jump since late 2025; reportedly Akuna and Wintermute). The alt-coin 15-minute series list a single designated liquidity provider. Makers pay no fee on these "quadratic" series, and Kalshi-wide evidence says makers outperform takers. So passive quoting is the structurally right side to be on. But small-bot reports say in-sample maker edges decayed within weeks, and that latency to update quotes is decisive. A small bot can plausibly compete only in thinner niches, with a fair value that tracks the settlement index and strict adverse-selection controls.

### Cited Findings
**Who provides liquidity**
- Kalshi named Susquehanna (SIG) its first major institutional market maker in 2024. SIG committed liquidity in "indices, economics, crypto, FX, and ad-hoc events", about 30× the previous liquidity in select markets (search summary). — [Kalshi News, "Liquid Prediction Markets are (finally) here"](https://news.kalshi.com/p/liquid-prediction-markets-are-finally-here)
- Professional terms reportedly include reduced fees and higher position limits. Akuna Capital and Wintermute are named as active on Kalshi/Polymarket. Jump's prediction-markets team reportedly about doubled to around 20 people in 2026 (search summary). — [Tradermath](https://www.tradermath.org/articles/prediction-markets-trading-at-quant-firms)
- Jump Trading reportedly began making markets on Kalshi in late 2025 and is to receive small equity stakes in Kalshi and Polymarket for supplying liquidity, per Bloomberg. Jump was also the counterparty on Kalshi's first block trade (search summary). — [DeFi Rate](https://defirate.com/news/equity-for-liquidity-jump-trading-set-to-take-stakes-in-kalshi-and-polymarket/); [FinanceMagnates](https://www.financemagnates.com/forex/prop-firm-jump-trading-to-take-stakes-in-kalshi-and-polymarket-report/); [Bitcoin Foundation news](https://bitcoinfoundation.org/news/prediction-markets/kalshi-completes-first-block-trade-with-jump-trading/)
- Kalshi's Designated Liquidity Provider program table lists "Alt-Coin 15 Minute" markets (ETH, HYPE, SOL, XRP, SHIB, BNB, DOGE) with one designated provider (search summary). — [Kalshi Help: Liquidity Provider Program](https://help.kalshi.com/en/articles/15410219-liquidity-provider-program)

**Incentive programs**
- The Liquidity Incentive Program pays for resting orders that improve liquidity even if unfilled. Rewards are capped (one CFTC filing cites $10,000 per business day for the most volatile eligible markets). Amendments took effect 2026-10-28 (search summary). — [Kalshi Help: Liquidity Incentive Program](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program); [CFTC filing](https://www.cftc.gov/filings/orgrules/rules10142633813.pdf)
- Kalshi is ending its volume incentive program, effective no earlier than 2026-10-13, amid wash-trading allegations (search summary). — [The Block](https://theblock.co/news/business/2026-09-30-kalshi-ends-trader-incentive-program-417247); [Gambling.com](https://www.gambling.com/us/news/kalshi-end-volume-incentive-program-october-13)

**Distribution and venue**
- Coinbase began listing Kalshi's 15-minute and hourly crypto markets on 2026-10-06. Kalshi runs 15-minute contracts on BTC, ETH, SOL, XRP, HYPE, BNB and DOGE through a central limit order book with liquidity that varies by contract (search summary). — [next.io](https://next.io/prediction-markets/crypto/15-minute-markets/)

**Fees and price grid (primary)**
- The series records for KXBTC15M, KXETH15M, KXSOL15M, KXBTCD, KXETHD, KXBTC and KXETH all show fee_type "quadratic" and fee_multiplier 1. — [Kalshi API series KXETH15M](https://api.elections.kalshi.com/trade-api/v2/series/KXETH15M)
- Under the schedule effective 2026-07-07:
  - Takers pay M × 0.07 × C × P × (1−P).
  - Makers pay nothing unless the series is "quadratic_with_maker_fees" (then 0.0175).
  - The fee is rounded up to $0.000001, then to the balance precision: $0.0001 for an account held with Kalshi directly, $0.01 through an FCM. Rounding is tracked per order.
  - Source: [coloshword/kalshi-15m-backtest README](https://github.com/coloshword/kalshi-15m-backtest); [Kalshi docs: fee rounding](https://docs.kalshi.com/getting_started/fee_rounding)
  - Older bot code assumes a round-up to the next whole cent per execution. That is likely outdated. — [artyomderkach-bit/kalshi-15m-market-maker README](https://github.com/artyomderkach-bit/kalshi-15m-market-maker); [RishabKalluri/kalshi-lab README](https://github.com/RishabKalluri/kalshi-lab)
- Price grid: $0.001 ticks below 10¢ and above 90¢, $0.01 between. — [Kalshi API market object](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=open)

**Size and spreads (own analysis, Oct 24–Nov 3, 2026)**

| Measure | KXBTC15M | KXETH15M |
|---|---|---|
| Median volume per 15-minute market (contracts) | 3.11M (p10 1.75M, p90 4.32M) | 214k (p10 139k, p90 324k) |
| Total volume over 952 markets | 2.93B contracts | 215M contracts |
| Median open interest | ~948k | ~84k |
| Median spread at ≥5 min left | 1¢ | 1¢ |
| Median spread at ≤3 min left | 0.1¢ | 0.2–0.3¢ |

Source: [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled); [Kalshi batch candlesticks](https://api.elections.kalshi.com/trade-api/v2/markets/candlesticks)

**Context volumes**
- Kalshi crypto volume was $2.16B in the week of Sept 14–20, 2026 (total Kalshi $15.27B), and $4.1B in Kalshi crypto markets from Aug 28 to Sep 26, 2026 (search summary; aggregator data). — [DeFi Rate](https://defirate.com/news/kalshi-2026-volume-record-15b-week/)

**Small-bot maker reports**
- From the artyomderkach maker bot:
  - "Almost every edge that looked real in-sample decayed out-of-sample within a few weeks as the market makers on the other side sharpened up."
  - The shipped strategy rests a post-only offer on the longshot side when its ask is above model fair value, "equivalently a maker buy of the favorite at 1 − longshot_price ($0.80–0.99)". It is "roughly break-even under pessimistic fill assumptions".
  - "Requote latency (a couple of seconds in production vs a full minute in the candle backtest) is the variable the backtest can't resolve."
  - Paper mode counts a fill only when a trade prints through the resting level.
  - Source: [artyomderkach-bit/kalshi-15m-market-maker README](https://github.com/artyomderkach-bit/kalshi-15m-market-maker)
- Polymarket 15-minute Transformer-based market making was profitable on BTC until late December 2025 and then died of latency, as described in Q2. — [QuantumSlayer/poly-15min README](https://github.com/QuantumSlayer/poly-15min)
- A popular generic Kalshi market maker (456 stars) selects markets by 24-hour volume and spread. It is not crypto-specific and reports no results. — [rodlaf/KalshiMarketMaker README](https://github.com/rodlaf/KalshiMarketMaker)
- kalshi-lab's simulator ignores cancels ahead of the bot in the queue, so maker fills are a lower bound. Its post-only orders are rejected instead of crossing. — [RishabKalluri/kalshi-lab README](https://github.com/RishabKalluri/kalshi-lab)

### Inferences
- In BTC 15-minute markets at the money, a small bot competes with firms that have direct spot feeds, faster re-quoting and possibly fee or limit concessions. The likely outcome is adverse selection: getting filled exactly when the price is about to move.
- Better niches for a small maker:
  - Away-from-the-money strikes on the hourly and daily ladders (KXBTCD/KXBTC range), where hundreds of strikes split market-maker attention.
  - ETH/SOL/XRP 15-minute books, which are about 14× smaller than BTC with 2¢ spreads.
  - Deci-cent tail levels late in the window, using exact partial-average math.
- Inventory risk is binary: a contract jumps to $0 or $1 at expiry. Quoting should widen or stop as τ shrinks, unless the partial-average math makes the outcome near-certain. Correlated positions across strikes and windows (all BTC) need netting.
- What it needs to run:
  - The Kalshi authenticated WebSocket: `orderbook_delta`, `trade`, `fill` and `cfbenchmarks_value`/5 Hz.
  - Authenticated REST with RSA-PSS signing, post-only limit orders, batch create/cancel, and idempotent `client_order_id`.
  - Hosting in AWS us-east-1. Basic-tier writes are 10 per second, which is a real constraint on quote management. Advanced is 30 per second.
  - Capital of only a few thousand dollars is enough to test. Cash must sit on the crypto shard. The Position Accountability Level is $25k per strike.
- Paper testing is least honest for makers: there is no queue position, no adverse-selection feedback and no market impact. Treat paper P&L as optimistic, even with trade-through fill rules. A small live pilot, such as kalshi-lab's suggested 5 contracts per order and $25 max loss, is the only honest test.

### Gaps
- Which firms quote KXBTC15M/KXETH15M specifically, and their fee or rebate terms, are not public.
- Current Liquidity Incentive Program rewards for crypto 15-minute markets (if any) after the 2026-10-28 amendment are unknown.
- No audited small-maker P&L on Kalshi crypto was found.

## Q5. What do open-source Kalshi and Polymarket short-dated crypto bots and practitioner posts report, including failures?

### Takeaway
The public record is dominated by infrastructure-heavy repos with no audited results, tiny live samples, or explicit null results. The few careful efforts converge on the same conclusions:
- The Kalshi mid is hard to beat.
- Momentum, technical and ML taker rules lose about the fee.
- Large backtest sweeps produce chance winners that fail forward.
- Polymarket's profitable bot era (latency and market making, late 2025) ended with fees and faster competitors.

### Cited Findings
**Null and negative results**
- coloshword / Windmill:
  - Paper agents in August 2026, "mostly on the 15-minute crypto markets", lost 3.35¢ per contract after fees over 781 bets, against about −0.4¢ for a coin-flip control.
  - In a KXBTC15M re-run (Oct 12–27, 2026), none of five agents beat the coin-flip control. The control lost 0.65¢ per contract over 446 bets. The 70–88¢-favorite agent lost 4.73¢ over 234.
  - Stated limits: "a candle's close is not a fill"; neighbouring windows are correlated; "many rules tried on one stretch of data will produce a 'winner' by chance".
  - Source: [coloshword/kalshi-15m-backtest README](https://github.com/coloshword/kalshi-15m-backtest); [Windmill write-up](https://windmill.markets/research/kalshi-15-minute-momentum)
- Turbine (vendor) backtest sweeps (search summary; unverified):
  - Only 102 of 4,904 Kalshi BTC 15-minute strategies made money in April 2026.
  - Across 5,732 later variants, 2,154 were positive and 2,496 lost.
  - All 100 "panic-fade" variants lost, and the April panic-fade winner lost in a later test.
  - Sources: [Turbine 4,904 backtests](https://www.turbinefi.com/blog/5000-strategy-backtest-kalshi-btc-15m); [Turbine 5,732 backtests](https://www.turbinefi.com/blog/5732-backtests-kalshi-bitcoin-15-minute-bots-2026)
- The ML results (AllAboutAI-YT, J0shusmc) and the Deribit-vs-Kalshi null (edgebook) are detailed in Q3. All three found the market mid hard to improve on. — [AllAboutAI-YT](https://github.com/AllAboutAI-YT/kalshi-btc15-ml-experiment); [J0shusmc](https://github.com/J0shusmc/Kalshi-BTC); [edgebook PR #31](https://github.com/milesiscool/edgebook/pull/31)

**Positive claims (all small or unverified)**
- Small live pilot: 3 trades, 3 wins, +2.7% on an $8.86 balance. The author says it is "not statistically significant". — [danielsilvaperez/kalshi-trading-bot README](https://github.com/danielsilvaperez/kalshi-trading-bot)
- A "risk-averse and profitable" tagline with no evidence. — [Bh-Ayush/Kalshi-CryptoBot](https://github.com/Bh-Ayush/Kalshi-CryptoBot)

**Late-window favorite bots**
- Mystic-bot buys 93–95¢ "done-deal" favorites near the close. Its own README warns that break-even at 93–95¢ "requires a win rate in the mid-90s" and that dozens of trades are only "an operational smoke test". — [fabricio-sousa/mystic-bot README](https://github.com/fabricio-sousa/mystic-bot)

**Common bot designs (no results)**
- Momentum, previous-result, order-book skew and exchange order-flow-imbalance "consensus", plus a final-90-second "resolution rider", favorite-longshot and mean-reversion rules. Data: Coinbase spot, Kalshi production API, order book from Crypto.com. — [reedjacobp/kalshi-trading-bot README](https://github.com/reedjacobp/kalshi-trading-bot)
- A GBM directional model plus Kalshi-vs-Polymarket divergence plus "dual-side" YES+NO < $1 trades, using Binance WebSocket and RedStone oracle data. — [brandononchain/kalshibot README](https://github.com/brandononchain/kalshibot)
- A log-normal model blending Kraken realized vol with Deribit ATM IV, fractional Kelly, and maker-first execution (post at bid, cross only if edge clears fees). It is described as a "real, running project" trading a small live account; no P&L shown. — [utkarshp845/Kalshi-Trading-Bot README](https://github.com/utkarshp845/Kalshi-Trading-Bot)
- Production-hardening patterns: EV-gated entries, fail-closed preflight, "stale-decision revalidation… against fresh spot before submission", and calibration-artifact gating of models. — [MaxExtractoor/MERID README](https://github.com/MaxExtractoor/MERID)

**Polymarket transfer lessons**
- The "gabagool" style buys YES and NO separately when each is cheap so the pair costs under $1. Repos note legging and timing risk. Profit claims ($300k+, 95–98% win rates) are unverified marketing or anecdote. Fees now cut into thin pair margins (search summary). — [TradeSEB/Polymarket-Trading-Bot-Gabagool](https://github.com/TradeSEB/Polymarket-Trading-Bot-Gabagool)
- On Polymarket, 5-minute and 15-minute contracts are reportedly over 80% of crypto-only volume. Polymarket's 5- and 15-minute crypto markets traded over $4B within months of launch (search summary). — [DeFi Rate](https://defirate.com/news/kalshi-2026-volume-record-15b-week/); [arXiv 2606.31675](https://arxiv.org/abs/2606.31675)
- A third-party stats page reports about 50% UP across 8,637 settled Polymarket BTC 15-minute markets. Its time-of-day skews rest on about 90 markets per slot, which is likely noise (search summary). — [PolyEdgeFinder](https://polyedgefinder.co/en/stats/btc/15m)

### Inferences
- **Survivorship and marketing bias.** Bot-selling sites (botforkalshi, polbots, polymtradebot, turbinefi) dominate search results. The only quantified, method-disclosed results (coloshword, AllAboutAI-YT, J0shusmc, edgebook, and the own analysis here) are null or negative for takers.
- **Failure modes that recur:**
  - Candle-close fills that flatter taker rules.
  - Fee rounding modelled wrongly.
  - Tuning on one stretch.
  - Ignoring that neighbouring windows share a BTC path.
  - Using spot proxies instead of BRTI.
  - Latency (maker bots).
- On Kalshi, YES+NO < $1 at top of book cannot occur, because NO ask = 1 − YES bid in one book. "Dual-side" trades are really two separate maker fills with inventory risk, which makes them a form of market making.

### Gaps
- Reddit (r/Kalshi, r/Polymarket, r/algotrading) threads could not be retrieved, so no forum-reported failures are included.
- Several repo READMEs are AI-generated. One says so explicitly (poly-15min). Their descriptions may not match their code.

## Strategy scorecard: what wins after Kalshi fees (mechanism, evidence, soundness, requirements, paper-test honesty, confidence)

### Takeaway
No strategy has strong evidence of a durable after-fee edge for a small operator. Ranked by plausibility:
1. Settlement-index-aware passive market making in thinner niches.
2. Late-window tail harvesting with exact partial-average math, using the real BRTI feed.
3. Everything taker-side and directional (vol-model, momentum, ML, LLM). This is negative after the 1.5–1.75¢ near-the-money taker fee.

Latency arbitrage is real but belongs to the fastest firms.

### Cited Findings
- Taker fee at 50¢: 1.75¢; makers free on "quadratic" crypto series. — [Kalshi API series KXBTC15M](https://api.elections.kalshi.com/trade-api/v2/series/KXBTC15M); [coloshword README](https://github.com/coloshword/kalshi-15m-backtest)
- Makers earn more than takers on Kalshi, and favorite-longshot bias is much stronger for takers (search summary). — [Whelan paper](https://www.karlwhelan.com/Papers/Kalshi.pdf)
- Maker edges decayed within weeks, and the best surviving maker rule is about break-even under pessimistic fills. — [artyomderkach-bit README](https://github.com/artyomderkach-bit/kalshi-15m-market-maker)
- The market mid beats or ties every model tested by others and by own analysis. — [AllAboutAI-YT README](https://github.com/AllAboutAI-YT/kalshi-btc15-ml-experiment); [edgebook PR #31](https://github.com/milesiscool/edgebook/pull/31); [Kalshi batch candlesticks](https://api.elections.kalshi.com/trade-api/v2/markets/candlesticks)
- Late favorites (80–99¢) roughly earn their price; +1.90¢ for last-60-second takers (unverified). — [predictionmarketspicks](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-last-60-seconds)
- Polymarket latency arbitrage was killed by fees and by ≥100 ms disadvantages. — [QuantumSlayer/poly-15min README](https://github.com/QuantumSlayer/poly-15min); [Cointelegraph via TradingView](https://www.tradingview.com/news/cointelegraph:e59c32089094b:0-polymarket-quietly-introduces-taker-fees-on-15-minute-crypto-markets/)

### Inferences
Each strategy is scored with my own confidence (0–100%) that it has a real, durable edge after Kalshi fees for a small, well-engineered operator.

1. **Settlement-aware passive market making (post-only quotes around a BRTI/partial-average fair value).** Confidence: 20% in niches; about 8% in BTC 15-minute at the money.
   - **Mechanism:** earn the spread, pay no maker fee, and possibly collect the variance-risk premium and longshot overpricing.
   - **Evidence:** structural (Whelan maker > taker; zero maker fee), with small-bot reports of break-even and edge decay.
   - **Logic:** sound, but adverse selection from faster takers is the main risk.
   - **Needs:** authenticated WebSocket with order book, fills and `cfbenchmarks_value`; post-only plus batch cancel; us-east-1 hosting; Advanced-tier writes preferable; inventory netting; a few $k.
   - **Paper honesty:** low. Queue position and adverse selection cannot be simulated, so use a tiny live pilot.
2. **Late-window tail harvesting.** Confidence: 15%.
   - **What it is:** in the last 1–3 minutes, buy the near-certain side (or rest offers on the longshot) at 95–99.9¢ when the partially fixed average makes the outcome more certain than the price.
   - **Mechanism:** exact average math plus very low tail fees (0.07¢ at 99¢).
   - **Evidence:**
     - Third-party +1.90¢ for last-60-second favorites (unverified).
     - Own 95–100¢ buckets: −0.4¢ to +1.25¢ (BTC) and +0.35¢ to +0.80¢ (ETH).
     - Sub-5¢ longshots slightly overpriced.
   - **Logic:** sound, but crowded, and the payoff is skewed: many 0.1–1¢ wins against rare −95¢ losses, plus the "no data → No" clause.
   - **Needs:** the 5 Hz index feed, sub-second order placement and deci-cent pricing.
   - **Paper honesty:** medium if you use live order-book snapshots and trade-through fills; low with candles.
3. **Vol-model (Black-Scholes or Bachelier digital) taker trading using realized vol or Deribit IV.** Confidence: 7%.
   - **Evidence:** the market mid is the better forecast in every careful test; Deribit-vs-Kalshi null at −1.38¢. Own BTC 7-minute positives are likely multiple-testing or staleness artefacts. ETH is negative.
   - **Logic:** sound as a fair-value engine, but not an edge by itself.
   - **Paper honesty:** medium, but it overstates performance unless real quote timestamps and fees are used.
4. **Latency arbitrage (spot → stale Kalshi quotes).** Confidence: 5% for a home or retail bot; 12% for a colocated, direct-feed operation on alt-coin books.
   - **Evidence:** Polymarket 2025 episode ended by fees and speed; Kalshi minute-level carryover is small; 1.75¢ taker fee near 50¢.
   - **Logic:** sound, but it is a pure speed race against professional market makers.
   - **Needs:** direct exchange feeds (Binance or perp leaders, Coinbase, Kraken), the BRTI feed, colocation-grade latency and higher API tiers.
   - **Paper honesty:** none. Only live round-trips reveal the result.
5. **Favorite-longshot harvesting as a taker** (buy 70–90¢ favorites mid-window). Confidence: 5%.
   - **Evidence:** coloshword −2.97¢ and −4.73¢ per contract; own 85–95¢ bucket overpriced; Kalshi-wide bias is mainly in longshots and weaker for these markets.
   - **Logic:** weak once fees are included.
6. **Cross-venue Kalshi–Polymarket "arbitrage" on hourly or 15-minute BTC.** Confidence: 8%.
   - **Mechanism:** sum of opposite legs below $1.
   - **Logic:** not risk-free. The settlement sources differ: BRTI 60-second average versus Chainlink or exchange prints, so basis can flip both legs. Both venues now charge about 0.07·p(1−p) to takers. Windows are seconds long (vendor claim of 2.7 s).
   - **Needs:** accounts and fast execution on both venues. Polymarket US and global availability is a separate legal question.
   - **Paper honesty:** low, because of legging risk.
7. **Momentum, technical or ML directional taker rules** (RSI, order-flow imbalance, previous result, Transformers). Confidence: 3%.
   - **Evidence:** consistently negative or null (coloshword, Turbine sweeps, ML lockbox gains of about 0.001 log loss).
8. **LLM directional forecasts for 15-minute moves.** Confidence: 1–2%.
   - **Evidence:** no source shows LLM value at this horizon. Own emulation shows that blending an uninformative forecast shrinks probabilities toward 0.5 and badly hurts log loss.
9. **"Both sides < $1" pair accumulation (Polymarket gabagool style).** Confidence: 10%, and only as a variant of strategy 1.
   - On Kalshi it is equivalent to two-sided market making with inventory risk; a single book never offers both sides below $1 at once.
10. **Settlement manipulation (moving spot near the fix).** Not scored: prohibited, and the 60-second multi-exchange average makes it costly. Relevant only as a hazard for market makers on single-print venues.

### Gaps
- No audited live P&L for any Kalshi crypto bot was found, so all scores above are judgement on indirect evidence.
- Hourly and daily ladder market making (likely the best small-operator niche) has no public performance data.

## Implications for the requester's model (Coinbase spot, 4-minute realized vol, point-spot settlement, LLM forecast; loses because probabilities sit closer to 50/50 than the market)

### Takeaway
The market's extra confidence is justified. Kalshi mids are well calibrated from 7 minutes to 1 minute before close, so the model is underconfident. The most likely causes, in order:
1. Blending in a forecast with no skill (the LLM), which mechanically shrinks probabilities toward 0.5.
2. The point-spot assumption, which overstates the variance left in the last 1–3 minutes and gets the expected settlement wrong inside the averaging minute.
3. Using Coinbase instead of the settlement index. This adds a basis of about 1 bp that is not centred on zero, and gets outcomes wrong in about 5% of markets.
4. A noisy 4-minute vol estimate.

Fixing these should bring the model to roughly market-level calibration. It will not, by itself, create an edge over the market.

### Cited Findings
- Own emulation (BTC 15-minute, Oct 24–Nov 3, 2026):
  - Adding a 50/50 blend to a point-spot, 4-minute-vol model cut mean |p − 0.5| from 0.378 to 0.189 at 1 minute before close. The market's was 0.427.
  - It raised log loss from 0.284 to 0.426; the market's was 0.183.
  - Its calibration slope was 3.84, strongly underconfident. At 7 minutes before close the slope was 2.19 and log loss 0.548 versus the market's 0.468.
  - This reproduces the requester's "closer to 50/50 than the market" symptom.
  - Source: [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled); [Coinbase candles](https://api.exchange.coinbase.com/products/BTC-USD/candles)
- Own analysis: the point-spot 60-minute-vol model was underconfident at 1 minute (slope 1.85 BTC, 2.34 ETH). The averaging-aware version fixed most of it (slope 0.99 BTC, 1.26 ETH) and lowered log loss (BTC 0.269 → 0.253; ETH 0.271 → 0.225). The market still did better (0.183 and 0.166). — [Kalshi batch candlesticks](https://api.elections.kalshi.com/trade-api/v2/markets/candlesticks)
- Own analysis: the point-spot 4-minute-vol model was too extreme mid-window (slope 0.59–0.79 at 14–2 minutes). Its 4-minute RMS vol had a median ratio of 0.72–0.89 to 60-minute vol, so the estimator is noisy and usually low, with occasional spikes. — [Coinbase candles](https://api.exchange.coinbase.com/products/BTC-USD/candles)
- Own analysis: Coinbase traded about −0.9 bps (BTC) and −1.2 bps (ETH) below the BRTI settlement average on average. Coinbase-based outcome calls were wrong in 5.57% (BTC) and 4.73% (ETH) of markets. Coinbase-based models showed positive intercepts late in the window, under-predicting YES. — [Kalshi API settled markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXETH15M&status=settled)
- Kalshi streams the settlement index with trailing 60-second averages (`cfbenchmarks_value`, plus a 5 Hz variant) and serves history through REST (search summary). — [Kalshi docs: CF Benchmarks Value Feed](https://docs.kalshi.com/websockets/cfbenchmarks-value)
- The 15-minute strike is the opening 60-second BRTI average, published as `floor_strike`. — [Kalshi API open markets](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=open)
- Others who modelled the market mid found it "already strongly predictive". The best improvements over it are about 0.001 log loss. — [J0shusmc README](https://github.com/J0shusmc/Kalshi-BTC); [AllAboutAI-YT README](https://github.com/AllAboutAI-YT/kalshi-btc15-ml-experiment)
- One Polymarket bot calibrated its vol scale to the market by solving for the Student-t scale implied by size-weighted quotes, Kalman-smoothed. It noted that prices near 0.5 cannot identify vol. — [QuantumSlayer/poly-15min README](https://github.com/QuantumSlayer/poly-15min)

### Inferences
Concrete fixes, in priority order:
1. **Remove or zero-weight the LLM forecast** unless it shows out-of-sample log-loss improvement against the market mid at the same timestamp. A no-skill forecast is shrinkage toward 50/50 and is the strongest single cause of the symptom.
2. **Price the actual settlement:**
   - Strike = `floor_strike`.
   - Before the final minute, use effective time = τ − 40 s.
   - Inside the final minute, use E[A] = (sum of the prints already fixed + r·S)/60 and sd = σ·√(r³/10,800).
   - Simplest of all: use Kalshi's published trailing 60-second average from `cfbenchmarks_value`.
3. **Replace Coinbase with BRTI/ETHUSD_RTI from Kalshi's WebSocket.** If Coinbase stays, add a rolling basis correction and expect about 3–6% wrong calls near the strike.
4. **Replace 4-minute realized vol** with a longer EWMA (30–120 minutes) plus time-of-day scaling and fat tails (Student-t). Alternatively, back out the market-implied vol from the Kalshi mid and trade only large, persistent deviations.
5. **Evaluate like the market is the benchmark:**
   - Log loss, Brier and calibration slope versus the mid at identical timestamps.
   - Walk-forward splits with a lockbox.
   - Fills at real ask and bid from order-book snapshots, not candle closes.
   - The July 2026 fee formula (1.75¢ at 50¢; 1.47¢ at 70¢; 0.33¢ at 95¢).
   - Pre-register thresholds to avoid the multiple-testing "winners" that coloshword and Turbine report.
6. **If the corrected model only matches the market, switch roles.** Use it as the fair-value engine for post-only maker quotes, where there is no fee, rather than as a taker signal.

### Gaps
- The requester's exact vol estimator (tick or second data, demeaning) and the LLM blend weight are unknown. The emulation uses 1-minute Coinbase closes and a 50% blend as stand-ins.
- Own tests are 1-minute resolution over 10 days. A tick-level replay on the requester's own recorded tape (with Kalshi's BRTI feed) is needed to confirm the size of each correction.
