# Automated trading edges for a small US retail bot: equities, options, futures and US forex (as of 4 Nov 2026)

Scope: a cloud bot with seconds-level latency, no colocation, $1k–$25k starting capital, API keys that can trade but not withdraw, and paper testing before live money. The trader is an Arizona resident using US-regulated brokers only.

Method note: this research used web search only. WebFetch could not reach www.finra.org or finance.yahoo.com because the hosts are outside this session's allowed network domains, so per instructions no further sites were fetched. Those hosts must be allowed in the session's network settings to read the FINRA notice and the Yahoo article directly. GitHub API access to the third-party repo japark22/kalshi-mispricing-engine is not enabled for this session either. Claims marked "(search summary)" come from search-engine digests of the linked pages, not from reading the full page. Kalshi fee and econ-market facts marked "(sibling notes)" come from the parallel Kalshi research files in `research_notes/Viable Kalshi trading strategies/` and were not re-verified here.

## 1. Which US brokers offer bot-suitable trading APIs to retail accounts, do they support trading-only keys, and what are the PDT, margin, options-approval and data-cost constraints?

### Takeaway
The biggest 2026 change: the FINRA pattern-day-trader (PDT) rule and its $25,000 minimum were replaced by a risk-based intraday margin standard, effective 4 June 2026. Brokers may phase it in through 20 October 2027, so whether a bot under $25k can day trade depends on the broker's rollout. Interactive Brokers is the only broker found that documents restricted-permission usernames (the closest thing to "trade but cannot withdraw"). Alpaca is the cheapest to start: free paper trading, free basic data and options Levels 0–3. Schwab's API needs a manual OAuth re-login every 7 days, which is a poor fit for an unattended bot. For CME micros, IBKR, tastytrade and Tradovate/NinjaTrader all work. Real-time data costs about $0–$15 a month at IBKR and $99 a month at Alpaca for full options data.

### Cited Findings

#### PDT rule replaced by intraday margin standard (2026)
- The SEC approved FINRA's amendments to Rule 4210 on 14 April 2026 (Release No. 34-105226). FINRA issued implementing Regulatory Notice 26-10 on 20 April 2026, and the change took effect 4 June 2026 (search summary; secondary sources). — [StockTitan](https://www.stocktitan.net/articles/pattern-day-trader-rule-eliminated-2026); [Angel Investors Network](https://angelinvestorsnetwork.com/regulatory-compliance/finra-eliminates-25k-pattern-day-trader-rule-june-2026). FINRA's weekly archive for 15 April 2026 is titled "FINRA Adopts New Intraday Margin Standards to Replace the Day Trading Margin Requirements" — [FINRA weekly archive 04/15/2026](https://www.finra.org/compliance-tools/weekly-archive/04152026) (title seen in search results; page not fetchable from this session).
- The amendments remove the "pattern day trader" designation, the 4-trades-in-5-days count and the $25,000 minimum equity. Customers must instead hold equity proportional to their actual intraday exposure. Maintenance margin requirements are unchanged; the new standard supplements them (search summary). — [WilmerHale client alert, 23 Apr 2026](https://www.wilmerhale.com/en/insights/client-alerts/20260423-sec-approves-amendments-to-finra-rule-4210-replacing-day-trading-margin-requirements-with-a-modernized-intraday-margin-standard); [Orrick InfoBytes, 1 May 2026](https://infobytes.orrick.com/2026-05-01/finra-replaces-day-trading-margin-requirements-with-new-intraday-margin-standards/); [ACA Group](https://www.acaglobal.com/industry-insights/finra-ends-the-pattern-day-trader-rule/)
- Firms must check each margin account for an "intraday margin deficit". They may use real-time systems that block trades before a breach, or a single end-of-day calculation. A phase-in is permitted through 20 October 2027, so constraints will vary by broker (search summary). — [CBH](https://www.cbh.com/insights/newsletters/alternative-investments-brief-finras-new-intraday-margin-rules/); [NICE Actimize](https://www.niceactimize.com/blog/goodbye-pdt-margin-threshold-hello-intraday-accountability); [Orrick](https://infobytes.orrick.com/2026-05-01/finra-replaces-day-trading-margin-requirements-with-new-intraday-margin-standards/)
- The $2,000 minimum still applies before borrowing on margin, maintenance requirements still apply, and a broker's own rules may be stricter (search summary). — [FINRA investor insight: Understanding the New Intraday Margin Requirements](https://www.finra.org/investors/insights/intraday-margin-requirements); [TradeZero](https://tradezero.com/en-us/blog/how-intraday-margin-replaced-the-pattern-day-trading-rule)
- Conflicts: one secondary source (Option Alpha) frames the new day-trading minimum as $2,000; others describe no fixed dollar minimum beyond the general margin minimum. — [Option Alpha](https://optionalpha.com/blog/pdt-rule-change-what-it-means-for-options-traders); [TradeZero](https://tradezero.com/en-us/blog/the-usd25-000-day-trading-minimum-is-gone-here-s-what-it-means-for-you)
- TradeStation published a customer piece on the change (6 May 2026). — [TradeStation Insights](https://www.tradestation.com/insights/2026/05/06/day-trade-rule-change/)

#### Interactive Brokers (IBKR)
- IBKR can set up a reduced-permission username, for example one without withdrawal access, by request to its Account Configuration team; it is not self-service. Trading, asset-class and market-data permissions belong to the IB username, not the account (search summary of IBKR docs). — [IBKR Web API: trading sessions](https://www.interactivebrokers.com/docs/web-api/trading/trading-sessions-in-the-web-api); [IBKR docs: multiple users](https://www.interactivebrokers.com/docs/general/market-data-subscriptions/market-data-users/multiple-users)
- In the Web API, portfolio endpoints work without a brokerage session, while order placement and market data sit behind `/iserver` and need one. — [IBKR Web API authentication](https://www.interactivebrokers.com/docs/web-api/authentication/trading)
- Market data: IBKR waives market-data charges for clients generating at least $30 a month in commissions (search summary of IBKR help page). Third-party 2026 guides list the non-pro "US Securities Snapshot and Futures Value Bundle" (NYSE/Nasdaq/AMEX plus CME/CBOT/NYMEX/COMEX) at $10 a month, the "US Equity and Options Add-On Streaming Bundle" at $4.50 a month non-pro ($125 pro), and OPRA top of book at $1.50 a month non-pro. API data needs the Market Data API Acknowledgement signed. — [IBKR market data page](https://www.interactivebrokers.com/ibis/marketData.php); [dev.to 2026 guide](https://dev.to/xqliu/interactive-brokers-market-data-subscription-which-one-do-i-actually-need-in-2026-164g); [PickMyTrade IBKR API cost 2026](https://blog.pickmytrade.io/ibkr-api-cost-every-charge-itemised-2026/)
- ForecastEx (IBKR's CFTC-regulated event-contract exchange) began operating 8 July 2024. Contracts pay $1.00 and cover Fed funds target rate, CPI, consumer sentiment, housing starts and retail sales. The TWS API supports trading forecast contracts. An "incentive coupon" was 4.33% APY at launch; a later page shows 3.14%. — [IBKR press release, 1 Aug 2024](https://www.interactivebrokers.com/en/general/about/mediaRelations/8-1-24.php); [IBKR forecast contracts page](https://www.interactivebrokers.com/en/index.php?f=66679); [ForecastTrader Learning Center](https://forecasttrader.interactivebrokers.ca/en/learn.php)

#### Alpaca
- Market data: Basic is free (indicative options quotes, 200 historical API calls per minute, latest-15-minutes restriction on historical data). Algo Trader Plus costs $99 a month: real-time OPRA options, 10,000 calls per minute, no 15-minute restriction. — [Alpaca docs: About Market Data API](https://docs.alpaca.markets/docs/about-market-data-api)
- Options approval: Level 0 (disabled), Level 1 (covered calls, cash-secured puts), Level 2 (long calls and puts), Level 3 (call and put spreads). Levels 2–3 need sufficient options buying power; the L2/L3 descriptions come from an older doc version. — [Alpaca docs: Options Trading](https://docs.alpaca.markets/docs/options-trading)
- Paper trading: options are enabled by default in paper, paper accounts start with $100,000, and each paper account gets its own API key. — [Alpaca docs: Options Trading](https://docs.alpaca.markets/docs/options-trading)
- One aggregator claims a $100,000 deposit gets Algo Trader Plus free (single third-party source, unverified). — [PricingSaaS](https://pricingsaas.com/companies/alpaca)

#### Charles Schwab (Trader API)
- Community sources consistently report that the refresh token lasts 7 days and the access token 30 minutes. A new refresh token needs an interactive OAuth login, so an unattended bot fails after 7 days without a manual re-login. Individual developer access covers one's own accounts. No official Schwab page was retrieved. — [schwabr CRAN docs](https://ftp.fau.de/cran/web/packages/schwabr/readme/README.html); [tda_to_schwab (GitHub)](https://github.com/48n116w/tda_to_schwab); [TradersPost blog](https://blog.traderspost.io/article/thinkorswim-api)

#### Tastytrade
- Official pricing: equity options $1 per contract to open, $0 to close, capped at $10 per leg. Futures $1.25 per contract, micro futures $0.85, options on futures $2.50, options on micro futures $1.50, plus exchange, clearing and regulatory fees. Some 2026 reviews list lower futures rates ($1.00, $0.75 micros, $1.25 futures options), which conflict with the official page. — [tastytrade pricing](https://tastytrade.com/pricing); [Investormint](https://investormint.com/company/tastytrade); [NexusFi](https://nexusfi.com/a/brokers/tastytrade-futures-trading)
- An Open API covers market data, order execution and portfolio management. — [Investormint 2026 review](https://investormint.com/software-tools/tastytrade-review-2026)

#### Tradier
- Third-party listings: Lite is free with API access at $0.35 per options contract. Pro is $10 a month with $0 equity, ETF and options commissions, except single-listed index options at $0.35. Pro Plus is listed at $35 a month in some sources. Tradier's pages say the rates are as of March 2026, with exchange, OCC and regulatory fees extra. A free sandbox is reported by a third-party FAQ. — [Tradier pricing](https://tradier.com/individuals/pricing); [MyBankTracker review](https://www.mybanktracker.com/blog/investing/tradier-brokerage-review-323257); [NexusFi on Tradier](https://nexusfi.com/a/brokers/tradier-futures-api-first-brokerage); [third-party Tradier FAQ](https://rithmic-html-css.pages.dev/broker-faq/tradier-faq/)

#### Futures brokers and CME micro sizing
- Tradovate (NinjaTrader Group) offers REST and WebSocket APIs. Sources conflict on API cost (about $25–$30 a month add-on, or included in a $99 a month plan) and on free-plan commissions ($1.29 standard and $0.35–$0.39 micro per side). One user reported no API add-on was visible. — [Tradovate community: API access](https://community.tradovate.com/t/api-access/12819); [DaneTrades: Tradovate API requirements](https://danetrades.freshdesk.com/support/solutions/articles/202000104289-tradovate-api-requirements-and-subscription); [TradingToolsHub](https://tradingtoolshub.com/blog/tradovate-pricing-guide-2026/)
- NinjaTrader advertises intraday margins as low as $50 on micro contracts, so an MES position is possible with a $1,000 account. — [NinjaTrader: account size](https://ninjatrader.com/futures/blogs/futures-trading-account-size/)
- MES is $5 per index point, with a 0.25 tick worth $1.25. Overnight initial margin figures conflict: about $1,700–$1,900 in one guide, $2,756 on a NinjaTrader margin page (period unclear). — [TradeZero MES specs](https://tradezero.com/en-us/support/questions/what-are-the-contract-specifications-for-the-micro-e-mini-s-and-p-500-mes-tradezero-america); [NinjaTrader MES margin](https://ninjatrader.com/margin-details/?symbol=MES); [FuturesHive](https://www.futureshive.com/blog/micro-emini-futures-mes-mnq-guide-2025)

#### US-regulated retail forex
- The CFTC caps retail forex leverage at 50:1 on major pairs and 20:1 on all others. — [OANDA US: spreads and margin](https://cloudflare-www.oanda.com/us-en/trading/spreads-margin)
- Commercial guides say US accounts are subject to FIFO and cannot hedge the same pair, and that only 4–5 firms serve US retail (OANDA, FOREX.com, IG US, tastyfx). The sources disagree on the count; NFA rule text was not retrieved. — [JournalPlus NFA rules](https://journalplus.co/regulations/nfa-forex-rules); [Track360](https://track360.io/blog/best-forex-brokers-usa-2026-cftc-nfa-regulated); [Benzinga](https://www.benzinga.com/money/nfa-forex-brokers)
- OANDA has a REST and streaming API (weak third-party source). — [broker review site](https://sites.google.com/view/broker-review/brokers/oanda-us)

### Inferences
- **The PDT change matters most for intraday strategies.** Intraday momentum and other same-day round trips were impractical under $25k in a margin account before June 2026. They become feasible once the bot's broker implements the intraday-margin standard. Because of the phase-in to October 2027, the bot should read the broker's live day-trade or buying-power status rather than assume the rule is gone.
- **The "trade but not withdraw" requirement is cleanest at IBKR.** The restricted-username route is documented. For the other brokers, the practical safeguard is to confirm that the specific API exposes no money-movement endpoints and to whitelist bank destinations at the broker. That still needs confirming for each broker (see Gaps).
- **Schwab is a poor fit for an unattended bot** because of the 7-day re-login, unless that has changed (unverified).
- **Low-friction stack for $1k–$25k:**
  - Alpaca (free paper and data) for equities, ETFs and simple options.
  - IBKR for everything else: options spreads, CME micros, ForecastEx, restricted user, about $10–$15 a month data, often waived.
  - Tastytrade or Tradovate as futures alternatives.
- **Contract sizes force defined-risk structures.** An unlevered MES is roughly $30k+ notional (at S&P ≈ 6,000+, my arithmetic), more than a $1k–$25k account. "Micro" still means meaningful leverage at this account size.

### Gaps
- Exact text of Regulatory Notice 26-10 and the intraday-margin formula: finra.org could not be fetched. How Alpaca, IBKR and tastytrade have implemented the change: not found.
- Unverified Schwab claim: one search digest (underlying page not identified) says Schwab stopped counting day trades on 8 June 2026 and introduced "Intraday Margin Buying Power" on 13 July 2026 for margin accounts of at least $2,000.
- Not confirmed from primary docs: whether Alpaca, Schwab, tastytrade, Tradier or Tradovate API credentials can initiate withdrawals or ACH transfers, or whether any offer scoped "trade-only" keys.
- Not researched: TradeStation API details and costs; Alpaca options commission schedule (secondary sources say $0 plus regulatory fees); current official CME margins for MCL, MGC and M2K.
- Not found: OANDA/FOREX.com API terms for US accounts; NFA FIFO and no-hedging rule text.
- Not researched: Arizona-specific restrictions for securities, futures or forex accounts (none surfaced in searches).

## 2. Which candidate strategies have credible after-cost evidence at small scale, and what does 2020–2026 evidence say about decay, crowding, drawdowns and tail risk?

### Takeaway
No strategy has strong, independent, after-cost evidence of alpha at retail scale in 2020–2026. The more robust candidates are risk premia, not anomalies: index put-writing (the volatility risk premium), merger arbitrage, trend following and carry. Each pays because it carries crash or crisis risk, and each has had sharp losses recently (Aug 2024, Apr 2025, the 2025 trend drawdown). Classic anomalies have largely decayed after publication: the S&P 500 index effect (7.4% to under 1%), PEAD in non-microcaps (gone by about 2006), the pre-FOMC drift (gone after 2015), turn-of-month (weakened) and pairs trading. Small size helps only where capacity is the binding constraint: closed-end fund discounts, small merger deals and microcap PEAD. Those are also where costs and data are hardest.

### Cited Findings

#### Cross-cutting: anomalies decay after publication
- McLean and Pontiff (Journal of Finance 2016) studied 97 published predictors. Returns were 26% lower out of sample and 58% lower after publication; they attribute about 32% of the decline to publication-informed trading. — [McLean & Pontiff PDF](https://Www.Gwern.net/doc/economics/2016-mclean.pdf)
- Jacobs and Müller (JFE 2020) studied 241 anomalies in 39 markets and found the US is the only country with a reliable post-publication decline in long-short returns. — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:135:y:2020:i:1:p:213-230)

#### A. Volatility risk premium (put-writing, spreads, short-dated options)
- Cboe PutWrite Index (PUT), July 1986–August 2023: 9.40% annualized vs 9.91% for the S&P 500, with standard deviation about 10.3% vs 15.4%. Cboe notes it can lag in fast-rising markets. — [Cboe: cash-secured put writing](https://www.cboe.com/insights/posts/generating-income-and-managing-risk-cash-secured-put-writing-in-a-low-equity-return-environment)
- Recent calendar years (PortfoliosLab, as parsed by search): PUT returned about 14.3% (2023), 17.8% (2024) and 9.2% (2025), vs S&P 500 TR about 26.3%, 25.0% and 17.9%. The parsed row also shows −0.98% (2022) and −1.08% (2026 YTD, snapshot date unknown), but the column alignment is uncertain. — [PortfoliosLab ^PUT vs ^SP500TR](https://portfolioslab.com/tools/stock-comparison/^PUT/^SP500TR)
- PUT's maximum drawdown was about −28.9% to −30% (COVID, 23 March 2020), with about 201 trading sessions to recover. — [PortfoliosLab ^PUT](https://portfolioslab.com/symbol/%5EPUT)
- WisdomTree: PUT's relative performance vs the S&P 500 is driven mainly by total premium collected, which tracks the average VIX level. — [WisdomTree](https://www.wisdomtree.com/us/insights/blog/a-strategy-for-volatile-markets)
- 0DTE: Vilkov's "0DTE Trading Rules" (SPX 0DTE, about 2016–2023/24; secondary summaries) found static hold-to-expiry rules showed no consistent profitability. Only risk reversals had slightly positive mean returns (about 0.01% of index value), and the premium is small enough that costs absorb it. The P&L is fat-tailed. — [CXO Advisory](https://cxoadvisory.com/equity-options/0dte-strategy-outcomes); [Hull Tactical, 8 Jul 2026](https://hulltactical.com/2026/07/08/0dte-options-tiny-edge-huge-distribution/)
- Retail 0DTE selling was profitable in aggregate; buying carried the losses (Beckmeyer, Branger, Gayda 2023). — [CXO Advisory](https://cxoadvisory.com/individual-investing/retail-0dte-option-trader-performance)
- **Tail event, 5 Aug 2024:** short-vol funds lost about 10% in a day; Reuters put top-10 short-vol ETF losses at $4.1B. The BIS calls it the VIX's biggest-ever one-day (intraday) spike, partly from quote-driven VIX mechanics and wide put spreads. A sponsor reports VIX +65% from 31 July to 5 August, the S&P 500 VIX Futures Inverse index −28.21% and its SVOL fund −10.2%. — [Hedgeweek](https://www.hedgeweek.com/volatility-short-leaves-traders-nursing-big-losses-after-stock-market-plunge); [Nasdaq/Reuters](https://www.nasdaq.com/articles/billions-lost-market-volatility-bet-vix-surge-hits-traders); [BIS Bulletin 95](https://www.bis.org/publ/bisbull95.htm); [Simplify](https://simplify.us/etfs-use-case/navigating-historic-vix-spike-svol)
- **Tail event, 5 Feb 2018 ("Volmageddon"):** the VIX's biggest spike since 1990, +53% or +20 points. — [BNP Paribas AM](https://www.bnpparibas-am.com/en-sk/front-of-mind/black-monday-5-august-2024-deja-vu-on-5-february-2018/)
- **Tail event, April 2025 tariff shock:** the VIX peaked at 52.33 on 8 April by one account and 60.13 intraday on 7 April by another. The options industry set a record 101 million contracts on 4 April. The BXM covered-call premium collected in April was 3.45%, 68% above March. — [Fortune](https://fortune.com/2025/04/07/stock-market-today-dow-nasdaq-vix-shorts-wall-street-bottom/); [Stocktwits](https://stocktwits.com/news-articles/markets/equity/trump-tariff-cause-more-volatility/chfreXkRb9R); [Cboe Index Insights](https://www.cboe.com/insights/posts/index-insights-april); [Natixis/Gateway](https://www.im.natixis.com/content/dam/natixis/website/insights/macro-views/2025/insulating-portfolios-with-index-options-during-stormy-weather/gateway-market-perspective-april-showers-ga152-0525.pdf)
- Earnings options: retail buys options before high expected-volatility announcements and loses 5–9% on average (10–14% for high-EAV events). Losses come from overpaying vs realized volatility, wide spreads and slow reactions; market makers absorb the flow (de Silva, Smith, So; Review of Finance 2025). — [Quantpedia](https://quantpedia.com/how-retail-losses-money-in-option-trading/); [Advisor Perspectives](https://www.advisorperspectives.com/articles/2023/02/19/the-wealth-destroying-behavior-of-retail-option-trading)

#### B. Index reconstitution and rebalancing
- S&P 500 additions' abnormal return fell from 7.4% in the 1990s to under 1% in the past decade; deletions fell to about −0.1% in 2010–2020 (−0.6% in the working paper). The main cause is that more than 70% of additions are now migrations from the S&P MidCap, so tracker buying is offset by tracker selling (Greenwood & Sammon, Journal of Finance 2025). — [SSRN](https://papers.ssrn.com/abstract=4294297); [NBER w30748](https://www.nber.org/system/files/working_papers/w30748/w30748.pdf); [Alpha Architect](https://alphaarchitect.com/disappearing-index-effect/)
- Russell reconstitution: about $220B of stock traded at the close on 2024 recon day. Russell's own research reports a diminishing effect. Older academic work (2000–2013) found positive post-event returns for additions, and a 2020/2022 arXiv paper documents crowding. No rigorous 2023–2026 study shows the trade still earns excess returns; a 2023 Seeking Alpha "study" is promotional (search summary). — [CME Group 2025](https://www.cmegroup.com/news/2025/the-annual-rebalancing-of-russell-indices.html); [InvestmentNews: "Slim pickings for Russell 2000 arbitrageurs"](https://www.investmentnews.com/etfs/slim-pickings-for-russell-2000-arbitrageurs/9302); [Seeking Alpha](https://seekingalpha.com/article/4609408-abnormal-returns-of-the-russell-index-reconstitution-anomaly-new-2023-study)

#### C. Closed-end fund (CEF) discount mean reversion
- Patro, Piccotti and Wu: most CEFs show significant discount mean reversion, international funds more so. A long-short strategy earned 17.3–18.2% a year (1998–2011 backtest per Quantpedia). The authors note higher-turnover variants are unlikely to survive transaction costs. The headline figures appear gross; treat them as an upper bound (older). — [vLex abstract](https://law-journals-books.vlex.com/vid/exploiting-closedend-fund-discounts-855659869); [ThreadReader summary](https://threadreaderapp.com/thread/1354923117898960896.html); [Quantpedia](https://vvv.quantpedia.com/?p=563)
- Gasbarro, Johnson and Zumwalt: CEFs deliver excess returns only when the discount narrows through share-price increases (older). — [Murdoch University](https://researchportal.murdoch.edu.au/esploro/outputs/journalArticle/Evidence-on-the-Mean-Reverting-Tendencies-of/991005541933907891)
- Gemmill and Thomas: discount levels are driven mainly by arbitrage costs and managerial expenses (2002, older). — [Warwick WP](https://text.www2.warwick.ac.uk/fac/soc/wbs/subjects/finance/research/wpaperseries/2002/02-119.pdf)

#### D. Merger arbitrage
- Mitchell and Pulvino (Journal of Finance 2001; 4,750 deals, 1963–1998): returns resemble selling uncovered index puts. They are uncorrelated with the market in flat or rising markets and positively correlated in severe declines. Excess returns are about 4% a year after transaction costs vs 10.3% without; costs are "substantial" (older). — [Mitchell & Pulvino PDF](https://www.johnhcochrane.com/s/mitchell-pulvino-characteristics-of-risk-and-return-JF.pdf); [IDEAS](https://ideas.repec.org/a/bla/jfinan/v56y2001i6p2135-2175.html)
- 2024 was "lackluster" for merger-arb funds. The HFRI ED Merger Arbitrage Index gained 8.2% through September 2025, its best three-quarter start since 2021. — [LPL Research](https://www.lpl.com/research/blog/merger-arbitrage-rebound.html)
- AllianceBernstein calls it the second-best first three quarters since 2009, driven by deal flow and "remarkably few" breaks. — [AllianceBernstein](https://www.alliancebernstein.com/americas/en/institutions/insights/investment-insights/merger-arbitrage-riding-the-wave-into-2026.html)
- Associated Capital's merger-arb team returned 16.1% gross and 12.0% net in 2025 (one manager). — [Barchart/ACG release](https://www.barchart.com/story/news/28282/associated-capital-group-inc-reports-fourth-quarter-and-full-year-results)
- Five-year rolling merger-arb returns have declined since 1995 but are about 10% recently. — [Hedge Fund Alpha](https://hedgefundalpha.com/strategies/merger-arbitrage-arbitraged-away/)

#### E. Post-earnings-announcement drift (PEAD)
- Martineau (Critical Finance Review 2022): PEAD began disappearing from non-microcap stocks in 2001 and was gone by 2006. — [CFR PDF](https://cfr.ivo-welch.info/published/papers/martineau2021rest.pdf); [IDEAS](https://ideas.repec.org/a/now/jnlcfr/104.00000122.html)
- A later replication with data through 2024 separates microcaps; a 2024 working paper calls the drift's demise "premature". It survives mainly in microcaps (search summary). — [UCLA Anderson Review](https://anderson-review.ucla.edu/is-post-earnings-announcement-drift-a-thing-again)

#### F. Overnight/intraday and calendar patterns
- Lou, Polk and Skouras (JFE 2019): momentum's abnormal returns occur overnight; most other anomalies' profits occur intraday, often with opposite-signed components. — [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/119010); [Polk PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- NightShares' overnight-only ETFs (NSPY, NIWM) closed in July 2023 and liquidated on 10 August 2023. NSPY returned −6.9% since inception vs +22% for the S&P 500. The CEO blamed day-session returns beating overnight after launch; Morningstar pointed to implementation and trading costs. — [InvestmentNews](https://www.investmentnews.com/industry-news/etf-strategy-designed-for-night-owls-gets-a-wake-up-call/240147); [etf.com](https://www.etf.com/sections/news/2-nightshares-etfs-close-after-struggling-gain-traction); [Bloomberg](https://www.bloomberg.com/news/articles/2023-07-19/-night-effect-funds-to-shut-down-with-overnight-returns-elusive)
- Intraday momentum on SPY (Zarattini, Aziz, Barbon; SFI WP 24-97, 2024, rev. 2025): the authors' 2007–early 2024 backtest shows 1,985% total return net of costs, 19.6% a year, Sharpe 1.33. It took 4th place in the 2025 Quantpedia Awards. There is no independent replication; one author runs a day-trading education business. — [SFI](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy); [Concretum](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/); [HSG/FSI](https://fsi.unisg.ch/de/newsdetail/news/quantpedia-awards-2025-fsis-barbon-and-team-secure-4th-place-with-intraday-momentum-strategy/)
- Pre-FOMC drift: Kurov, Wolfe and Gilbert (FRL 2021) find it essentially disappeared after 2015. Lucca and Moench's 2018 update found it only around press-conference meetings. — [Kurov et al. PDF](https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf); [IDEAS](https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html)
- Turn of month, conflicting evidence:
  - Quantpedia (1926–2005) says virtually all excess market return accrued in the 4-day window. — [Quantpedia](https://quantpedia.com/screener/Details/41)
  - An Atlanta Fed working paper finds the effect disappears in S&P 500 futures and spot after 1990. — [Fed in Print](https://fedinprint.org/item/fedawp/13394/original)
  - In the ETF era it is concentrated on the first trading day. — [FPA Journal](https://www.financialplanningassociation.org/article/journal/APR11-turn-month-anomaly-age-etfs-reexamination-return-enhancement-strategies)
  - A recent ETF test finds the narrow window weakening but a broader window still significant for most equity ETFs. — [QuantSeeker](https://www.quantseeker.com/p/turn-of-the-month-strategies-do-they)

#### G. Futures carry and roll yield
- Koijen, Moskowitz, Pedersen and Vrugt (JFE 2018; 1972–2012): within-asset-class carry averages a Sharpe of about 0.7, and a diversified cross-asset carry portfolio about 1.1. These are gross, monthly-rebalanced figures with some look-ahead in the vol weights. Carry does poorly in global recessions. — [Koijen et al. WP](https://www.bi.no/link/af8ef92ed3ee4896bc0cea7fc855b1ba.aspx); [CXO Advisory](https://www.cxoadvisory.com/?p=23627)

#### H. Trend following on futures
- Hurst, Ooi and Pedersen: time-series momentum explains most managed-futures returns. The sample is 58 instruments, 1985–2012, gross of costs; frictions hurt small investors more. The "Century of Evidence" extension finds trend profitable on average since 1903 (older). — [CXO Advisory](https://www.cxoadvisory.com/?p=24372)
- SG Trend Index 2025:
  - −4.89% in April (YTD −9.33%), about −10% YTD at end July, −7.6% at end August, +1.92% in December. — [Top Traders Unplugged, Apr 2025](https://www.toptradersunplugged.com/trend-following-performance-report-april-2025/); [Jul 2025](https://www.toptradersunplugged.com/trend-following-performance-report-july-2025/); [Aug 2025](https://www.toptradersunplugged.com/trend-following-performance-report-august-2025/); [Dec 2025](https://www.toptradersunplugged.com/trend-following-performance-report-december-2025/)
  - Long-run CAGR 4.88%, maximum drawdown 20.61%. — [Top Traders Unplugged, Jul 2025](https://www.toptradersunplugged.com/trend-following-performance-report-july-2025/)
  - Full-year 2025 is reported as +2.39% by one source; another shows the SG CTA Index at −0.2%. Unresolved. — [Wisdom Trading](https://wisdomtrading.com/insights/if-your-trend-system-has-been-struggling-youre-not-alone-heres-whats-going-on/); [Aussie Turtles](https://www.aussieturtles.com/battle-of-the-trend-following-indexes-december-2025/)
- Small accounts: Rob Carver is reported to recommend about $100k minimum for a diversified futures trend system (secondary). No academic study of trend following in sub-$1M accounts was found. — [The Algorithmic Advantage (Carver interview summary)](https://thealgorithmicadvantage.substack.com/p/033-rob-carver-the-comprehensive); [futures.io thread](https://futures.io/trading_member/31568-fcmreform.html)

#### I. Pairs and statistical arbitrage
- Gatev, Goetzmann and Rouwenhorst (RFS 2006; 1962–2002): up to 11% a year excess for self-financing pairs portfolios, surviving conservative cost estimates (older). — [EconPapers RFS](https://econpapers.repec.org/RePEc:oup:rfinst:v:19:y:2006:i:3:p:797-827); [Yale WP](https://ideas.repec.org/p/ysm/somwrk/ysm109.html)
- Do and Faff (secondhand): pairs profitability peaked in the 1970s–80s and has declined since the 1990s. It survives only in a few refined versions at much diminished levels, and the original rule loses profitability. — [2018 working paper summarizing Do & Faff](https://www.scribd.com/document/588965707/zhang2018)

### Inferences

#### Per-strategy assessment for us
Two confidence figures, both my judgment:
- **C1:** probability the strategy, as we would implement it, shows positive after-cost P&L over a 2–3 year live run (includes any market beta).
- **C2:** probability it earns a genuine edge, meaning after-cost returns above its passive or beta equivalent.

**A. VRP via defined-risk index put spreads or condors (30–45 DTE on SPY/XSP-style underlyings or micro-futures options), small size, no stacking.**
- **Logic:** sound. It is a documented insurance premium, but it is compensation for crash risk, not free alpha.
- **Evidence:** credible for index put-writing (Cboe, 37 years: similar return to the S&P at about two-thirds the volatility). It is weak for the spread and 0DTE variants: Vilkov finds no static 0DTE edge after costs.
- **2023–2025:** PUT lagged the S&P by 7–12 points a year. Tail events in 2018, 2020, 2024 and 2025 show losses come in clusters.
- **Capital:** a $1k–$25k account cannot cash-secure index puts, so it must use spreads, which give back part of the premium.
- **Infrastructure:** Level 3 options at Alpaca, or IBKR.
- **Fit:** moderate.
- **Confidence:** C1 55%, C2 25%.
- **Sub-variant, selling earnings straddles to retail buyers (de Silva et al.):** market makers already capture this flow. Spreads are wide and gap risk is large. C1 35%, C2 20%.

**B. Index reconstitution (S&P additions, Russell recon trades at the close).**
- **Logic:** was sound (forced, price-insensitive demand).
- **Evidence:** the S&P effect is largely gone. Russell is diminishing and crowded, and institutions pre-position.
- **Costs:** MOC auction fills are cheap, but the edge is close to zero.
- **Data:** free (index announcements).
- **Fit:** poor.
- **Confidence:** C1 20%, C2 10%.

**C. CEF discount reversion (rotate into funds trading at unusually wide discounts vs their own history; optional ETF hedge; monthly rebalance).**
- **Logic:** sound. Limits to arbitrage, and small size is an advantage because capacity limits big players.
- **Evidence:** academic and older (to 2011), mostly gross. Post-2011 evidence after costs was not found.
- **Costs:** wide CEF spreads; use limit orders; low turnover is essential.
- **Risks:** discounts blow out in crises; leverage inside the funds; hedge mismatch.
- **Data:** daily NAVs needed (free sources unverified).
- **Fit:** good for a slow bot.
- **Confidence:** C1 55%, C2 30%.

**D. Merger arbitrage (long targets in announced cash deals; 10–20 positions; skip deals with heavy regulatory risk; optional short of the acquirer in stock deals).**
- **Logic:** sound. It earns a deal-completion risk premium, with a short-put-like payoff.
- **Evidence:** credible. About 4% a year excess after costs in 1963–1998 (older), declining since 1995. 2025 was strong because breaks were rare, which could reverse.
- **Capital and data:** low capital per deal is feasible; data is free (EDGAR filings and prices).
- **Risks:** single-deal breaks of −20% to −40%; correlated losses in crashes.
- **Latency:** irrelevant.
- **Fit:** good.
- **Confidence:** C1 60%, C2 35%.

**E. PEAD.**
- **Logic:** behavioral underreaction.
- **Evidence:** credible, but the effect is dead outside microcaps since about 2006. Microcap spreads probably eat most of the drift.
- **Data:** consensus estimates are expensive, or a model-based surprise from free XBRL filings can stand in.
- **Fit:** poor to moderate.
- **Confidence:** C1 30%, C2 15%.

**F1. Overnight-only index exposure (buy at close, sell at open via auctions).**
- **Logic:** documented (most of the equity premium historically accrued overnight).
- **Evidence:** the 2022–2023 implementation failed (NightShares), and the effect has been unstable lately. Costs with $0 commissions and auction fills are small, but two trades a day.
- **Fit:** easy to test.
- **Confidence:** C1 50%, C2 20%.

**F2. Intraday momentum on SPY/QQQ (Zarattini et al.).**
- **Evidence:** a single practitioner-authored backtest (Sharpe 1.33 net), not independently replicated, and published in 2024, so decay is likely.
- **Feasibility:** now implementable under $25k at brokers that have adopted the new intraday-margin regime. Free 1-minute history from Alpaca's Basic plan makes it quick to test.
- **Fit:** good for testing.
- **Confidence:** C1 35%, C2 20%.

**F3. Calendar effects (turn of month, pre-FOMC).**
- **Evidence:** largely decayed.
- **Confidence:** C1 45% (part-time long equity), C2 15%.

**G. Futures carry with micros.**
- **Logic:** sound.
- **Evidence:** a gross, diversified, institutional-scale Sharpe of about 0.7–1.1. Our tiny universe (a few equity, metal, energy, rates and FX micros) removes most of the diversification. Short VIX-futures "roll yield" is really VRP with extreme tails (−28% in 3 days in 2024).
- **Confidence:** C1 40%, C2 20%. For short VIX futures specifically: C2 15%, and not recommended.

**H. Trend following on 6–10 micro futures, vol-targeted.**
- **Logic:** sound and the best documented of all (more than 100 years).
- **Evidence:** credible, but recent performance is weak: CAGR about 4.9%, a 20.6% maximum drawdown, and a −10% mid-2025 drawdown.
- **Capital:** small accounts face contract-granularity and diversification limits (Carver's about $100k minimum).
- **Value:** mainly as crisis diversification.
- **Confidence:** C1 45%, C2 30%.

**I. Pairs and stat arb (daily bars).**
- **Evidence:** decayed and crowded.
- **Fit:** a seconds-latency retail bot has no advantage.
- **Confidence:** C1 25%, C2 10%.

**K. Retail forex (OANDA/IBKR; carry or trend on majors).**
- **Evidence:** academic currency carry is gross and institutional. US retail account profitability was about 28–38% per quarter historically (Question 3). Leverage is capped at 50:1 and 20:1.
- **Confidence:** C1 30%, C2 15%.

#### Cross-cutting inferences
- The strongest after-cost evidence is for risk premia (VRP, merger arb, trend, carry). That evidence is about compensated risk, and over a 2–3 year window the market path dominates. Paper trading cannot show whether we have an edge. It can only check that the plumbing and cost model work.
- Post-publication decay (−58% on average in the US) should be applied to every published backtest we try, including the 2024 intraday-momentum paper.

#### Summary table

| Strategy | Logic sound? | Evidence quality (recency) | Main risk | Capital fit ($1k–$25k) | C1 | C2 |
|---|---|---|---|---|---|---|
| VRP: defined-risk index put spreads | Yes (risk premium) | Strong for PUT index (to 2023); weak for spreads and 0DTE | Crash clusters (2018/2020/2024/2025) | OK with spreads only | 55% | 25% |
| Earnings-vol selling | Partly | One strong paper (MM side) | Gap moves, wide spreads | OK | 35% | 20% |
| Index reconstitution | Was | Strong that it decayed | Crowding | OK | 20% | 10% |
| CEF discount reversion | Yes | Older, gross | Discount blowouts | Good (small size helps) | 55% | 30% |
| Merger arbitrage | Yes (risk premium) | Strong but older; 2025 strong | Deal breaks; crash beta | Good | 60% | 35% |
| PEAD | Was | Strong that it decayed (non-micro) | Microcap costs | Poor | 30% | 15% |
| Overnight-only index | Mixed | Implementation failed 2023 | Regime shifts | Good | 50% | 20% |
| Intraday momentum (SPY) | Plausible | Single practitioner backtest | Decay; overfitting | Good post-PDT | 35% | 20% |
| Calendar (TOM, pre-FOMC) | Weak | Decayed | Noise | Good | 45% | 15% |
| Futures carry (micros) | Yes | Gross, institutional | Recessions | Poor diversification | 40% | 20% |
| Trend (micros) | Yes | Very long history; weak recently | Long drawdowns | Marginal | 45% | 30% |
| Pairs / stat arb | Was | Decayed | Crowding, divergence | OK | 25% | 10% |
| Retail forex carry/trend | Partly | Gross academic; poor retail base rates | Leverage, spreads | OK | 30% | 15% |

### Gaps
- No 2020–2026 after-cost evidence was found for:
  - CEF discount strategies (post-2011);
  - Russell reconstitution (peer-reviewed);
  - retail-sized put-spread VRP;
  - merger arb deal spreads and break rates for 2024–2026.
- Not found: an official full-year 2025 SG Trend Index return (sources conflict); 2026 YTD for trend, PUT or merger arb (only an undated PUT snapshot of −1.08%).
- Primary Do & Faff and Vilkov papers were not read (secondary summaries only).
- Not checked: whether FTSE Russell's move to more frequent (semi-annual) reconstitution in 2026 changes the recon trade.
- Not researched: XSP/SPY option contract specs and current SPY or SPX levels (the notional figures above are approximate arithmetic); ETF sector or dual-momentum rotation; leveraged-ETF rebalancing flows.

## 3. What fraction of retail day or algorithmic traders make money, per credible studies (the base rate)?

### Takeaway
Very few. Among persistent day traders, about 1% (Taiwan) to 3% (Brazil) are reliably profitable after costs. US retail options traders lose billions in aggregate, mostly through spreads and overpaying for volatility. Historically only about 28–38% of US retail forex accounts were profitable in a given quarter. For algorithmic traders specifically, the Quantopian study found backtest Sharpe ratios almost useless for predicting live Sharpe (R² < 0.025).

### Cited Findings
- **Taiwan day traders** (Barber, Lee, Liu, Odean; Journal of Financial Markets 2014; 1992–2006):
  - Under 1% of day traders can predictably and reliably earn positive abnormal returns net of fees.
  - Aggregate day-trader performance net of fees was negative in every one of the 15 years.
  - An earlier version found more than 80% of day traders lose money in a typical six-month period.
  - Losing traders kept trading at nearly the same rate as winners.
  - Sources: [Berkeley PDF](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf); [EconPapers](https://econpapers.repec.org/RePEc:eee:finmar:v:18:y:2014:i:c:p:1-24); [CXO Advisory](https://www.cxoadvisory.com/individual-investing/do-day-traders-make-money/)
- **Brazilian mini-index futures day traders** (Chague, De-Losso, Giovannetti 2019/2020; started 2013–2015):
  - Of those who persisted more than 300 days, 97% lost money.
  - Only 1.1% earned more than the Brazilian minimum wage, and 0.5% more than a bank teller's starting salary.
  - Only 7.9% (1,551) persisted more than 300 sessions, and there was no evidence of learning.
  - The figures exclude taxes and course costs.
  - Sources: [EconPapers WP](https://econpapers.repec.org/paper/spawpaper/2019wpecon47.htm); [CXO Advisory](https://www.cxoadvisory.com/investing-expertise/day-trading-a-bust/); [Bloomberg](https://www.bloombergquint.com/onweb/day-traders-in-brazil-study-would-ve-done-better-with-9-to-5-job)
- **US retail options** (Bryzgalova, Pavlova, Sikorskaya; Journal of Finance):
  - Payment for order flow has pushed retail options trading above 60% of total volume, with nearly 90% of PFOF paid by three wholesalers.
  - Press coverage estimates retail losses of $1.14B from November 2019 to June 2021 (10-day holding assumption), plus about $4.13B in trading costs, about $5B in total.
  - Sources: [IDEAS / CEPR DP17688](https://ideas.repec.org/p/cpr/ceprdp/17688.html); [EliteTrader repost of Bloomberg coverage](https://www.elitetrader.com/et/threads/mom-and-pop-investors-took-a-billion-dollar-bath-trading-options-during-the-pandemic.366697)
- **US retail earnings options** (de Silva, Smith, So; Review of Finance 2025): 5–9% average losses around earnings, and 10–14% for high expected-volatility events. — [Quantpedia](https://quantpedia.com/how-retail-losses-money-in-option-trading/)
- **US retail 0DTE SPX** (Beckmeyer, Branger, Gayda 2023):
  - About 75% of retail SPX option trades were 0DTE.
  - Retail lost $184k a day on average from February 2021 to February 2023, and $358k a day after daily expirations began in May 2022.
  - More than $70M was lost in total, over $50M of it from transaction costs; buying caused the losses, selling was profitable.
  - The data ends February 2023.
  - Cboe estimates retail at about 50–60% of 0DTE volume.
  - A platform-selected sample (Option Alpha 0DTE bots) shows 49.64% of users profitable, which is self-selected and not market-wide.
  - Sources: [CXO Advisory](https://cxoadvisory.com/individual-investing/retail-0dte-option-trader-performance); [BNN Bloomberg](https://www.bnnbloomberg.ca/day-traders-lose-358-000-per-day-gambling-on-zero-day-options-1.1910634); [FOW](https://www.fow.com/insights/analysis-cboe-points-to-retail-flow-as-zero-day-options-grow); [Option Alpha](https://optionalpha.com/bots/0dte-research-insights-bot)
- **US retail forex disclosures** (CFTC/NFA quarterly profitable-account statistics; data from 2010–2018, older):
  - OANDA's reported profitable share fell from 51% (Q3 2010) to 43.5% (Q4 2010) to about 38% once interest-only accounts were excluded.
  - Critics note the statistics omit closed and new accounts.
  - Sources: [Finance Magnates on OANDA](https://www.financemagnates.com/forex/brokers/oandas-high-profitability-numbers-explained-include-interest/); [Finance Magnates Q4 report](https://financemagnates.com/forex/brokers/exclusive-q4-us-retail-forex-profitability-report-ib-1-again-while-oanda-slipping); [MechanicalForex critique](https://mechanicalforex.com/?p=1488)
- **Retail algorithmic traders** (Wiecki et al. 2016, Quantopian; 888 US-equity algorithms backtested 2010–2015, with 6–12+ months out of sample):
  - Backtest Sharpe had almost no power to predict out-of-sample performance (R² < 0.025).
  - Picking the highest in-sample Sharpe could produce negative out-of-sample Sharpe.
  - Machine-learning features reached R² of 0.17.
  - Sources: [Quantpedia](https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/); [CXO Advisory](https://www.cxoadvisory.com/big-ideas/in-sample-vs-out-of-sample-performance-of-888-trading-strategies)

### Inferences
- A reasonable prior is that a new retail strategy in a competitive, high-turnover niche loses after costs with about 90%+ probability. Low-turnover risk-premium strategies have a much better prior (around 50–60% positive over a few years), mostly because they carry beta.
- The studies agree that costs (spreads, commissions, overpaying for options) are the dominant cause of retail losses. A bot that makes liquidity (limit orders at mid) or trades rarely removes the largest documented loss channel. Taking liquidity in options and microcaps recreates it.
- Because a backtest Sharpe barely predicts live Sharpe, the paper-trading stage must check out-of-sample stability over months, not just fit.

### Gaps
- Unverified figure: a search digest states FOREX.com reported 35,139 active accounts for Q1 2018 with 28% profitable, but the page it came from was not identified.
- Not found: post-2018 US forex profitability statistics; a US equities day-trader study comparable to the Taiwan or Brazil work; any 2024–2026 study of retail API or bot traders; Cboe's Han (2024) retail paper (its P&L findings were not retrieved).

## 4. Which strategies can be paper-tested quickly and cheaply with free or low-cost data, and which need expensive data?

### Takeaway
Daily-bar strategies (merger arb, overnight and calendar effects, trend and carry via ETF proxies, CEF rotation, index-event studies) can be tested for about $0 using EDGAR, free daily prices and Alpaca's free minute-bar history; paper trading is free at Alpaca. Options strategies (VRP, earnings vol, Kalshi vs SPX options) need historical options chains: about $50 one-off (OptionsDX, unverified) up to about $99–$299 a month (ORATS). Intraday option quotes cost more. Futures-native tests need continuous-contract data: pay-per-query Databento, or vendor plans such as Massive's $999 a month per exchange group.

### Cited Findings
- **Alpaca:** paper trading with a $100k default balance and options enabled. The free Basic data tier allows historical requests except the latest 15 minutes, at 200 calls a minute. Real-time OPRA options data needs Algo Trader Plus at $99 a month. — [Alpaca docs: Options Trading](https://docs.alpaca.markets/docs/options-trading); [Alpaca docs: Market Data](https://docs.alpaca.markets/docs/about-market-data-api)
- **IBKR:** live data is about $10 a month (bundle including CME, CBOT, NYMEX and COMEX top of book) plus $4.50 for the options add-on (non-pro). It is waived with at least $30 a month in commissions (third-party guides and IBKR page). — [dev.to](https://dev.to/xqliu/interactive-brokers-market-data-subscription-which-one-do-i-actually-need-in-2026-164g); [IBKR market data](https://www.interactivebrokers.com/ibis/marketData.php)
- **Tradier:** the sandbox is free (third-party FAQ). — [Tradier FAQ](https://rithmic-html-css.pages.dev/broker-faq/tradier-faq/)
- **Databento:** CME Globex (GLBX.MDP3) history is pay-per-query, with the cost shown before a query runs. Anecdotal pulls cost a few cents. CME L2 and L3 (MBO) data is available for 14 years. — [FINM course page](https://finm-32900.github.io/Week7/databento.html); [Databento catalog](https://databento.com/catalog/cme/GLBX.MDP3/futures/ZC); [EliteTrader](https://elitetrader.com/et/threads/databento-l2-and-l3-mbo-cme-historical-data-now-available-for-14-years.382608)
- **Massive (formerly Polygon):** the futures business page lists CBOT and COMEX plans at $999 a month each (7+ years of history, futures options included); the startup price was not shown. — [Massive futures](https://massive.com/business-futures)
- **Options history:**
  - ORATS: data since 2007 including SPX and VIX, a near-end-of-day snapshot taken 14 minutes before the close, no intraday data. Third parties put it at $99–$299 a month, with a $49 a month individual tier. — [ORATS blog](https://orats.com/blog/pros-and-cons-of-orats-backtester); [FlashAlpha comparison](https://flashalpha.com/articles/flashalpha-vs-orats-options-data-api-backtesting)
  - OptionsDX: about $50 per data-year one-off per a forum post, vs "free to $20" per dataset in another document (conflict). — [QuantNet](https://quantnet.com/threads/backtesting-assistance-required.16099/latest); [Raxx vendor doc](https://raxx-internal-docs.pages.dev/data-science/historical-options-data-vendors.html)
  - Cboe DataShop: priced by quote. — [Cboe historical data](https://www.cboe.com/solutions/options-analytics/historical-data)
  - HistoricalOptionData.com: from 2002, SPX from 1990; prices not public. — [HistoricalOptionData](https://www.historicaloptiondata.com/)
  - ThetaData: described as cheaper per gigabyte for raw end-of-day data. — [Raxx vendor doc](https://raxx-internal-docs.pages.dev/data-science/historical-options-data-vendors.html)

### Inferences

**Cheap or fast to test (≈$0–$10 a month):**
- Overnight-only and calendar effects (daily OHLC).
- Intraday momentum (Alpaca free minute bars).
- Merger arb (EDGAR plus daily prices).
- Index-event studies (announcement dates plus daily prices).
- Trend and carry using ETF proxies (daily).
- Pairs on daily bars.

**Moderate ($50–$300 one-off or monthly):**
- VRP put-spread and condor backtests on end-of-day chains (OptionsDX or ORATS).
- Earnings-vol selling, which also needs an earnings calendar.
- CEF rotation, which needs a historical NAV and discount series (source and cost unverified).

**Expensive or hard:**
- PEAD done properly (consensus-estimate history).
- Microcap strategies, which need survivorship-free data.
- Intraday options strategies (0DTE, Kalshi-vs-SPXW), which need intraday OPRA quotes.
- Futures-native carry or roll tests, which need full term structures (Databento pay-per-use or Massive at about $999 a month).

**Paper-trading caveat:** paper fills ignore queue position and impact. Alpaca and IBKR paper fills on options, CEFs and microcaps will be optimistic, so the bot should log quoted spreads and model fills at the far side (or mid plus a haircut).

### Gaps
- Not verified in this session: free sources such as Yahoo/Stooq daily prices, FRED, the Kenneth French data library and CEFConnect NAVs (availability, terms and survivorship bias).
- Not found: ThetaData pricing, Databento's per-GB rates and any free credits, IBKR paper-account prerequisites, and whether Cboe publishes free daily PUT/BXM index history.

## 5. Prediction-market interactions: can Kalshi (or ForecastEx) economic and financial contracts be priced off options-implied distributions or futures for an exploitable edge?

### Takeaway
No credible evidence of an exploitable after-fee gap for a retail bot was found. Only student and practitioner projects compare Kalshi S&P 500 ranges with SPX/SPXW-implied probabilities. One open-source bot removed its S&P bracket strategy after a negative-edge backtest. A crypto analog (Deribit-implied vs Kalshi hourly ladders) found the Kalshi mid was the best forecast and no edge after fees. On Fed and CPI, a Fed staff paper finds Kalshi as accurate as or more accurate than fed funds futures and consensus. Futures move about 0.6–1.2 s before Kalshi after CPI releases, which is out of reach at seconds-level latency.

### Cited Findings
- A Stevens Institute student project (May 2025) used options-implied probabilities to flag mispricing in Kalshi year-end S&P 500 buckets and reported "persistent pricing inefficiencies", mainly in specific market environments (not peer-reviewed). — [Stevens FSC](https://fsc.stevens.edu/event-contract-mispricing-via-options-implied-probabilities/)
- The open-source "kalshi-mispricing-engine" compares Kalshi daily S&P 500 ranges with same-day SPXW-implied probabilities. It uses an "edge funnel" for bid-ask, fees and implied uncertainty, plus a risk-premium decomposition, and states that disagreement is not edge. Its results could not be read (repo access not enabled). — [GitHub: japark22/kalshi-mispricing-engine](https://github.com/japark22/kalshi-mispricing-engine)
- The-oracle bot removed its S&P 500 bracket strategy after a negative-edge backtest (sibling notes). — [the-oracle README](https://github.com/christurgeon/the-oracle)
- The crypto analog (Deribit options-implied odds vs Kalshi hourly ladder) found "no edge": the Kalshi mid was the best forecast, and the effect after fees was about −1.38¢ per contract with a confidence interval spanning zero (sibling notes, search summary of a PR). — [milesiscool/edgebook PR #31](https://github.com/milesiscool/edgebook/pull/31)
- An option-theoretic paper argues Kalshi's fixed-strike contracts yield well-specified digital-option-implied measures (crypto, 2026). — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1057521926003601)
- Diercks, Katz and Wright, "Kalshi and the Rise of Macro Markets" (FEDS 2026-010, 12 Feb 2026, not peer-reviewed): Kalshi's FOMC forecast error is lower than fed funds futures; Kalshi headline CPI beats consensus. — [FEDS PDF](https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf); [Federal Reserve page](https://federalreserve.gov/econres/feds/kalshi-and-the-rise-of-macro-markets.htm); [DeFi Rate summary](https://defirate.com/news/federal-reserve-study-finds-kalshi-markets-rival-traditional-economic-forecast-tools/)
- After the 11 September (2026) CPI print, CME fed funds futures moved about 0.6 s (1.2 s elsewhere in the same article) before Kalshi, and depth thinned on both venues before the release (sibling notes). — [BMLL](https://www.bmlltech.com/news/market-insight/when-kalshi-and-fed-funds-futures-disagree)
- Kalshi fees: the taker fee is round-up(0.07 × C × P × (1−P)), at most 1.75¢ per contract at 50¢. Index daily and hourly series (KXINX, KXINXU, KXNASDAQ100) are listed as taker-fee-only (sibling notes). — [QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained)
- Kalshi pricing biases:
  - A UCD working paper documents maker/taker economics and a favorite-longshot bias. A search digest says average contract returns are about −20% before fees, which is unverified. — [UCD WP2025_19](https://www.ucd.ie/economics/t4media/WP2025_19.pdf)
  - Another analysis finds contracts priced below 20¢ underperform their odds. — [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure)
- ForecastEx (IBKR) lists Fed funds and CPI contracts tradable through the TWS API. This is a second US-regulated venue a bot can reach from the same broker. — [IBKR press release](https://www.interactivebrokers.com/en/general/about/mediaRelations/8-1-24.php)

### Inferences
- **Most apparent gaps are risk premia, not mispricing.** Options-implied distributions are risk-neutral: they embed the variance and skew premia documented in Question 2(A), so left-tail ranges look expensive relative to real-world odds. If Kalshi prices near real-world odds, the two will disagree systematically without either being wrong. Trading Kalshi toward the options-implied number therefore buys the risk premium back.
- **A hedged version is the only arbitrage-like form.** The idea is to buy a Kalshi range and sell the matching option butterfly or call-spread digital replica, or the reverse. Its hurdle is:
  - the Kalshi fee (up to 1.75¢) plus the Kalshi spread;
  - SPX/XSP option spreads on multiple legs;
  - settlement-definition and timing mismatches;
  - contract-size granularity.

  These sum to several cents per $1 of payoff, more than the gaps reported in the projects above (my inference; no measured after-cost P&L found).
- **Fed and CPI markets:** the Fed paper and the BMLL latency measurement mean "Kalshi vs FedWatch" gaps mostly reflect futures term and risk premia (Kalshi was more accurate) or sub-second lags, which belong to co-located market makers.
- **Rough confidence for a seconds-latency retail bot (consistent with the sibling Kalshi research):**
  - unhedged "trade toward the options-implied probability": 10–15% chance of positive after-fee P&L;
  - hedged Kalshi-vs-XSP/SPX replication: about 15%;
  - Kalshi/ForecastEx Fed or CPI vs futures or nowcasts: about 10%.

### Gaps
- Not found: any peer-reviewed or audited P&L study of Kalshi S&P range contracts vs SPX options after fees; the actual results of the japark22 repo (access not enabled) or of the Stevens project (page not fetched); Kalshi INX settlement mechanics vs SPXW/XSP PM settlement; ForecastEx liquidity, fees and API contract codes.
- Kalshi availability for an Arizona resident: the sibling notes say state availability is contested (secondary reports of a CFTC suit against Arizona in April 2026 over preemption) and did not verify it.
