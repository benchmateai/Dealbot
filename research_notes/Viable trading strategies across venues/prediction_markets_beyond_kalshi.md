# Automated edges on US-legal prediction markets other than Kalshi, and price gaps between them and Kalshi (Arizona resident, as of 4 Nov 2026)

*How this was researched: about 30 web searches plus page fetches, run on 4 Nov 2026. This session's network blocked direct fetches of most primary pages: docs.polymarket.us, interactivebrokers.com, arxiv.org, dlapiper.com, predictmarketcap.com, agentbets.ai and polymarket101.com could not be reached. Many facts below therefore come from search-engine summaries of those pages, not from my own reading of them. Where a claim rests on one secondary site or I could not pin it to one URL, it is marked "(unverified)" or "(attribution uncertain)". Fee and incentive numbers change monthly, so re-check them live before coding fee logic. Kalshi itself is out of scope. Kalshi figures appear only as the other leg of a cross-venue trade.*

---

## Q1. Which event-contract venues are open to an Arizona resident today, with an API that allows automated trading? (fees, limits, API terms)

### Takeaway
Besides Kalshi, only two venues have a documented API that a retail bot can use:
- **Polymarket US**, a CFTC designated contract market (DCM). Its Retail API uses Ed25519 keys and has no retail withdrawal endpoint. Takers pay 0.0695·C·p(1−p); makers pay nothing.
- **Interactive Brokers' TWS API**. It trades ForecastEx contracts at $0.01 per contract per side with no IBKR commission. The same API also reaches Kalshi and CME event contracts.

Gemini Predictions says it has an API, and its fees copy Kalshi's (taker 0.07, maker 0.0175 × p(1−p)), but I did not verify its API terms or whether it serves Arizona. PredictIt has no trading API and its terms ban bots. Robinhood (which routes to Kalshi, ForecastEx or Rothera), Webull and Coinbase (both route to Kalshi), Crypto.com OG/CDNA, FanDuel Predicts on CME, Underdog, DraftKings and others are app-only for retail as far as I could find. Polymarket's international on-chain exchange is still closed to US persons.

Arizona is legally contested. A federal preliminary injunction issued 5 May 2026 bars Arizona from enforcing its gambling laws against contracts listed on a DCM. The Ninth Circuit's 28 Aug 2026 *KalshiEX v. Assad* ruling (a Nevada case) says sports event contracts are likely not swaps. That undercuts the preemption theory behind the Arizona injunction, and the Arizona appeal is pending. Sports contracts carry the most regulatory risk.

### Cited Findings

**Arizona legal backdrop**
- Arizona's gaming regulator sent cease-and-desist letters to Kalshi, Robinhood and Crypto.com in May 2025. Arizona filed a 20-count criminal case against Kalshi in March 2026; sources give the date as 17 or 18 March. Polymarket was not charged. Sources: [predictionmarketspicks AZ page](https://predictionmarketspicks.com/tools/state-map/az); [swrnn](https://www.swrnn.com/polymarket/arizona). Both are secondary, and they disagree on whether Polymarket got a cease-and-desist.
- The CFTC sued Arizona, Connecticut and Illinois on 2 Apr 2026. A temporary restraining order against Arizona followed on 10 Apr 2026 ([CFTC TRO filing](https://www.cftc.gov/media/13721/ENFArizonaTemporaryRestrainingOrder041026/download)).
- Judge Liburdi granted the CFTC a preliminary injunction on 5 May 2026. It bars Arizona from enforcing its gambling laws against event contracts listed on CFTC-regulated DCMs, and it paused the criminal prosecution of Kalshi ([Gambling Insider](https://www.gamblinginsider.com/news/158205/arizona-judge-grants-cftc-preliminary-injunction-kalshi-case)).
- Kalshi's appeal was stayed on 4 Jun 2026. Arizona appealed in July, and on 14 Sep 2026 asked the Ninth Circuit to vacate the preliminary injunction (docket 26-4281). I found no Ninth Circuit decision on the Arizona appeal ([litigation tracker, secondary](https://mickbransfield.com/2025/08/11/summary-of-legal-actions-involving-kalshis-sports-event-contracts/)).
- Ninth Circuit, 28 Aug 2026, *KalshiEX v. Assad*, No. 25-7516:
  - It affirmed the dissolution of Kalshi's injunction against Nevada. Sports event contracts are likely not "swaps", so state gaming law is not preempted.
  - CFTC Regulation 40.11 "remains in the books and controls the outcome."
  - Election contracts were remanded.
  - Sources: [opinion PDF](https://cdn.ca9.uscourts.gov/datastore/opinions/2026/08/28/25-7516.pdf); [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/08/ninth-circuit-upholds-state-and-tribal-authority-over-sports-related); [National Law Review](https://natlawreview.com/article/sports-bets-or-swaps-ninth-circuits-controversial-kalshi-ruling-deepens-divide).
  - The Third Circuit held the opposite on 6 Apr 2026 in the New Jersey case, which creates a circuit split ([The Defiant](https://thedefiant.io/news/regulation/ninth-circuit-says-kalshi-sports-contracts-aren-t-swaps-splitting-with-third-circuit)).
  - Coverage says the Ninth Circuit ruling "could undermine" the Arizona injunction ([Covers](https://www.covers.com/industry/circuit-court-rules-against-prediction-market-sports-event-contracts-august-28-2026&gsessionid=bn7v4dnmxe6wl3fohzhs1q2h5qbh3jmcn-_grk607l59ylycbdofbg)).
- Two further reports, both unverified:
  - A CFTC event-contract rule was proposed on 10 Jun 2026 and is not final. This came from a state-by-state guide surfaced in search, attribution uncertain ([lines.com](https://www.lines.com/guides/u-s-prediction-market-legal-status-state-by-state)).
  - Minnesota banned these markets by statute effective 1 Aug 2026, and the CFTC sued to block it ([startpolymarket](https://startpolymarket.com/countries/united-states/)).

**Polymarket US** (CFTC DCM through QCEX/QCX; fiat; no crypto)
- **Launch and access:**
  - Launched 2 Dec 2025.
  - The waitlist was removed in May 2026; the product is on iOS and Android, with web in beta.
  - The PUSD stablecoin from the international exchange is not part of the US product.
  - Sources: [Gambling Insider explainer](https://www.gamblinginsider.com/in-depth/106291/is-polymarket-legal-in-the-us); [startpolymarket](https://startpolymarket.com/countries/united-states/). Both secondary; dates differ slightly across sources.
- **State availability:**
  - One October 2026 guide says Polymarket US told it in writing on 23 Oct 2026 that it is available in every state except Nevada. Another guide listed Polymarket as blocked in Arizona as of July 2026. Sources: [predictionmarketspicks](https://predictionmarketspicks.com/learn/is-polymarket-legal-in-arizona) / [startpolymarket](https://startpolymarket.com/countries/united-states/) (attribution uncertain; conflicting).
  - The status needs live confirmation at signup.
- **Taker fee** (official fee schedule): 0.0695 × C × p × (1−p), so at most about $1.74 per 100 contracts at 50¢ ([docs.polymarket.us/fees](https://docs.polymarket.us/fees)).
  - Table tennis markets use 0.10.
  - Combos (parlays) have their own curve with a (1−p)^4 term, whose coefficient rose from 0.06 to 0.085 at 10:00 PM ET on 28 Oct 2026.
  - Earlier secondary guides quoted different numbers, such as 0.06 effective 1 Jul 2026, or a flat 0.30% taker with a 0.20% maker rebate ([agentbets, unverified](https://agentbets.ai/guides/polymarket-us-api-guide/); [sharpfootballanalysis](https://www.sharpfootballanalysis.com/prediction-markets/polymarket/)). They look outdated.
- **Taker rebates**, tiered by prior-month taker volume and effective 19 Oct 2026 ([docs.polymarket.us/fees](https://docs.polymarket.us/fees); [changelog](https://docs.polymarket.us/changelog)):

  | Prior-month taker volume | Rebate (share of taker fees paid) |
  |---|---|
  | Under $250k | 0% |
  | $250k–$1M | 3% |
  | $1M–$10M | 5% |
  | $10M–$25M | 10% |
  | $25M–$50M | 15% |
  | $50M and up | 30% |

  - Proof of 30-day volume on another prediction market can get you placed in a tier early ("accelerated placement").
- **Maker fees and rebates** ([docs.polymarket.us/fees](https://docs.polymarket.us/fees); [changelog](https://docs.polymarket.us/changelog)):
  - Makers pay no fee.
  - Since 19 Oct 2026, maker rebates are tiered by prior-month maker volume. These tiers replaced a flat −0.0125 rebate for everyone.

  | Maker tier | Prior-month maker volume | Rebate coefficient |
  |---|---|---|
  | Tier 1 | Under $10M | none |
  | Tier 2 | $10M–$50M | −0.0035 |
  | Tier 3 | $50M–$200M | −0.0070 |
  | Tier 4 | $200M and up | −0.0104 |

  - Combo fills earn no maker rebate.
- **API:**
  - Keys are Ed25519 and are generated in a developer portal after identity verification. Access tokens last 24 hours ([REST API overview](https://docs.polymarket.us/institutional/introduction)).
  - Retail API rate limit: the rate-limits page says 25 requests/s shared across endpoints, enforced per source IP ([rate limits](https://docs.polymarket.us/api-reference/rate-limits)). The changelog says it was cut to 20 requests/s per key ([changelog](https://docs.polymarket.us/changelog)). The two conflict.
  - WebSocket streams are recommended over polling.
  - Key scopes include read:orders, write:orders and read:positions.
  - Deposit and withdrawal "Transfers" appear only in the institutional/partner docs. A "PERMISSION_DENIED" error there means the firm is not set up for transfers. I found no retail withdrawal endpoint ([Transfers](https://docs.polymarket.us/partners/funding/transfers)).
  - Institutional FIX and RFQ APIs exist ([FIX](https://docs.polymarket.us/institutional/fix-api/fix-overview); [RFQ](https://docs.polymarket.us/institutional/rfqs/overview)).
- **Listings:** Polymarket US lists election contracts. DeFi Rate quoted a separate Polymarket US price, 85.8¢, for the midterms on 21 Oct 2026 ([DeFi Rate](https://defirate.com/odds/2026-midterms/)). It also lists sports, including table tennis and combos ([fees](https://docs.polymarket.us/fees)).

**Polymarket international** (polymarket.com, on-chain)
- Americans are still barred from the main exchange, under the 2022 CFTC settlement and US IP geoblocking. On 28 Apr 2026 Polymarket asked the CFTC to let US users trade on its main offshore exchange ([CoinDesk/Bloomberg](https://www.coindesk.com/policy/2026/04/28/polymarket-seeks-cftc-approval-to-reopen-main-exchange-to-u-s-traders)).
- I found no report of a CFTC vote or approval as of this search. One report mentions a new CFTC probe in June 2026 ([Gambling Insider](https://www.gamblinginsider.com/in-depth/106291/is-polymarket-legal-in-the-us), unverified single source).
- Reaching it would require a VPN and an on-chain wallet, so it is **excluded** under our constraints.

**Interactive Brokers: ForecastEx, plus Kalshi and CME through IBKR**
- **Fees:** ForecastEx charges $0.01 per contract on each side of each trade, and IBKR charges no commission ([kairos](https://kairos.trade/compare/forecastex-review); [predictgeek](https://predictgeek.com/prediction-markets/interactive-brokers/); secondary).
- **Eligibility:** clients aged 21 and over at eligible IBKR entities ([IBKR prediction markets page](https://www.interactivebrokers.com/predictionmarkets/en/home.php)).
- **Incentive coupon:**
  - 3.38% APY on the daily closing value of ForecastEx positions, YES or NO, accrued daily and paid monthly. That was the rate quoted on 30 Sep 2026.
  - Earlier quotes were 3.80% (March 2026) and 3.83% (April 2026). Some October pages give 3.12–3.14%.
  - Sources: [IBKR page](https://www.interactivebrokers.com/predictionmarkets/en/home.php); [safebet.ai comparison](https://safebet.ai/us/prediction-markets/kalshi-vs-interactive-brokers/).
- **TWS API:**
  - Event contracts use secType "OPT", with exchange FORECASTX, KALSHI or CME.
  - YES maps to a Call and NO to a Put.
  - ForecastEx contracts can only be bought. To exit, you buy the opposing contract and IB nets the two automatically.
  - Limit orders only, with Day, GTC or IOC time in force, in whole contracts.
  - Sources: [IBKR API event trading](https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/); [TWS API contracts doc](https://www.interactivebrokers.com/docs/tws-api/doc/event-trading/contracts).
- **Unified prediction-markets interface:** launched 14 May 2026, combining Kalshi, CME Group and ForecastEx. CME contracts were added on a rolling basis and were not all visible at launch ([DeFi Rate](https://defirate.com/news/interactive-brokers-expands-prediction-markets-kalshi-cme-group-integration/); [Finance Magnates](https://www.financemagnates.com/forex/interactive-brokers-bundles-kalshi-cme-forecastex-in-unified-event-trading-push/)).
- **Fee comparison with Kalshi:** a third-party comparison says ForecastEx's flat fee is cheaper than Kalshi's price-based fee for prices between about 8¢ and 92¢ ([marketmath](https://marketmath.io/compare/forecastex-vs-kalshi)).

**PredictIt** (Victoria University; operates under CFTC no-action relief, not as a DCM)
- **Limits:** in July 2025 the per-contract cap was raised from $850 to $3,500 and the 5,000-trader-per-market cap was removed ([Wikipedia](https://en.wikipedia.org/wiki/PredictIt); [PredictMarkets](https://predictmarkets.com/predictit/)).
- **Aristotle Exchange:** a DCM and clearinghouse approved as entities separate from PredictIt. Underdog later acquired the Aristotle exchange platform ([Gambling Insider](https://www.gamblinginsider.com/news/117033/underdog-aristotle-exchange-acquisition)).
- **Fees:** 10% of profits and 5% of withdrawals. One 2026 review says the 5% withdrawal fee was dropped on 23 Sep 2026, while other 2026 pages still list it (unverified; [eventtradinghub fees](https://eventtradinghub.com/predictit-fees-limits/); [cryptoslate](https://cryptoslate.com/prediction-markets/predictit-review/)).
- **No trading API, and bots are banned:**
  - Trading is manual through the web only, and the terms ban automated trading and scraping ([eventtradinghub guide](https://eventtradinghub.com/predictit-guide/); [nextpredict](https://nextpredict.io/platforms/predictit/); secondary).
  - The only programmatic access is a read-only feed at [predictit.org/api/marketdata/all/](https://www.predictit.org/api/marketdata/all/). It refreshes every 60 seconds and is licensed for non-commercial use with attribution (same sources).

**Robinhood** (Robinhood Derivatives LLC)
- Contracts are offered "through either KalshiEX LLC, ForecastEX, LLC or Rothera Exchange and Clearing LLC."
- Rothera is a Robinhood–Susquehanna joint venture. It bought MIAXdx (formerly LedgerX) in January 2026 ([Robinhood FY2025 8-K exhibit](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000013/q42025robinhoodexhibit991.htm)).
- Robinhood began routing contracts to Rothera in early June 2026, starting with the World Cup ([Robinhood newsroom](https://robinhood.com/newsroom/the-world-cup-is-now-trading-on-robinhood-and-rothera/); [Prediction News](https://predictionnews.com/story/robinhood-routes-event-contracts-to-cftc-licensed-exchange-rothera)).
- Rothera processed 3.5 billion contracts in Q2 ([Prediction News](https://predictionnews.com/story/rothera-processed-3-5-billion-contracts-for-robinhoods-prediction-market-in-q2)). Robinhood's CFO said most prediction-market flow will move to Rothera ([Next Event Horizon](https://nexteventhorizon.substack.com/p/robinhood-cfo-says-most-prediction-flow-moving-to-rothera)).
- I found no public API or programmatic order entry for Robinhood's event contracts.

**Webull**
- Partnered with Kalshi in February 2025. A March 2026 "Prediction Market Hub" offers sports, economic and crypto contracts at $0 commission plus exchange fees ([Barchart/PR](https://www.barchart.com/story/news/37249506/webull-introduces-0-commission-trading-on-pro-football-big-game-prediction-markets); [BrokerChooser](https://brokerchooser.com/news/webulls-2026-prediction-market-what-traders-need-to-know--3896f8aa)).
- Many contract types are mobile-only.
- I found no API for event contracts.

**Coinbase**
- Kalshi-powered prediction markets have been live in all 50 states since late January 2026. All flow goes to Kalshi at launch, with other venues planned ([The Block](https://www.theblock.co/post/387416/coinbase-prediction-markets-go-live-in-all-50-us-states-via-kalshi); [Invezz](https://invezz.com/news/2026/01/29/coinbase-rolls-out-kalshi-powered-prediction-markets-across-all-50-us-states/)).
- I found no Advanced Trade API support for event contracts.

**Crypto.com** (Crypto.com | Derivatives North America, "CDNA", a CFTC DCM and clearinghouse)
- In February 2026 its prediction markets moved into a standalone US-only app called "OG" ([Cointelegraph](https://cointelegraph.com/news/crypto-com-launches-new-prediction-market-platform-after-40x-growth)).
- Programmatic access is business-to-business through partners such as Plaee and white-label front ends like Truth Social ([Crypto.com/Plaee](https://crypto.com/company-news/plaee-partners-with-cryptocom-to-launch-cftc-compliant-prediction-market-technology-infrastructure-in-the-us)). I found no public retail API.
- Fee reports conflict:
  - A flat $0.02 per contract on crypto, FX and index markets ([polymarkettrader](https://polymarkettrader.com/best/prediction-markets-for-crypto-users/)).
  - 0.07·p(1−p) on sports ([DeFi Rate fees](https://defirate.com/prediction-markets/fees/)).
  - $0.01–$0.0175 per contract taker with no maker fee ([oddsassist](https://oddsassist.com/prediction-markets/crypto-com-fees/)).
- It left Nevada in November 2025 ([polymarkettrader](https://polymarkettrader.com/best/prediction-markets-for-crypto-users/)).

**CME / FanDuel Predicts**
- FanDuel Predicts is an FCM owned 51% by CME and 49% by FanDuel, and its contracts trade on CME. Fees are flat per contract per side; one review uses $0.01 as an example, plus possible FCM fees ([bonus.com](https://www.bonus.com/prediction-markets/fanduel-predicts/), secondary).
- CME event contracts can also be reached through IBKR's API (exchange "CME"; see above).
- An analysis cited in search results put Kalshi at about 91% of US regulated event-contract share and CME at about 0% (attribution uncertain; same search).

**Gemini Predictions** (Gemini Titan)
- Received its DCM licence on 10 Dec 2025 and its clearinghouse (DCO) licence on 30 Apr 2026 ([BettingUSA](https://www.bettingusa.com/prediction-markets/reviews/gemini/); [Crowdfund Insider](https://www.crowdfundinsider.com/2025/12/256349-digital-assets-firm-gemini-obtains-us-license-for-prediction-markets/)).
- Official fees for contracts listed on or after 18 Mar 2026: taker 0.07 and maker 0.0175, each × C × p(1−p). Contracts listed earlier used 0.05 taker and 0.01 maker ([Gemini fees](https://www.gemini.com/fees/predictions); [legacy schedule](https://www.gemini.com/fees/predictions-2026-03-18)).
- On its Q1 2026 call, Gemini said it launched an "agentic trading tool… allowing AI agents… to connect to our API" ([Q1 2026 transcript](https://www.insidermonkey.com/blog/gemini-space-station-inc-class-a-common-stock-nasdaqgemi-q1-2026-earnings-call-transcript-1765711/)).

**Newer DCMs and brands** (no public retail APIs found for any of them)
- **Underdog:** acquired a DCM/DCO in March 2026; its own exchange, UDX, launched on 18 Jul 2026 ([BusinessWire](https://www.businesswire.com/news/home/20260718201640/en/Underdog-Launches-Prediction-Markets-on-its-own-Exchange)).
- **Sporttrade:** received DCM and DCO designations in October–November 2026 and plans a phased launch through broker partners ([SportsBettingDime](https://www.sportsbettingdime.com/news/industry/sporttrade-granted-cftc-approval-as-dcm-and-dco-to-launch-prediction-market-offerings/)).
- **Novig:** its DCM is Ludlow Exchange, approved June 2026 and launched August 2026, clearing through Bitnomial.
- **ProphetX:** DCM on 11 Jun 2026.
- **Fanatics:** bought Water Street Labs' DCM/DCO in July 2026.
- **DraftKings Predict.**
- Sources for Novig, ProphetX, Fanatics and DraftKings: [mickbransfield CFTC list](https://mickbransfield.com/cftc-regulated-pms/); [ticker-tracker](https://ticker-tracker.com/learn/cftc-regulated-prediction-markets). Secondary trackers; dates are inconsistent.
- **Applicants:** Nasdaq (inflation contracts; [nextpredict](https://nextpredict.io/market-news/legal/nasdaq-seeks-cftc-exchange-approval-inflation-markets/)) and Blockchain.com ([CNBC, 9 Oct 2026](https://www.cnbc.com/2026/10/09/blockchain-com-cftc-prediction-markets.html)).

### Inferences
- **Venues a bot can actually use (my synthesis):**

  | Venue | Status for our bot |
  |---|---|
  | Polymarket US | Usable: retail API, fiat, no withdrawal via API, taker ≈ Kalshi's fee, maker free |
  | IBKR (ForecastEx + Kalshi + CME) | Usable: TWS API; ForecastEx $0.01 per side; coupon on positions; the API cannot transfer funds out *(my understanding of TWS API scope, not verified in this session)* |
  | Gemini Predictions | Possibly usable: API claimed; Kalshi-identical fees; Arizona availability and bot terms unverified |
  | PredictIt, Robinhood/Rothera, Webull, Coinbase, Crypto.com OG/CDNA, FanDuel Predicts, Underdog UDX, Novig, ProphetX, Sporttrade, DraftKings, Fanatics | Not botable for retail today. Use for read-only price signals at most, and PredictIt's feed is licensed non-commercial only |
- Reaching Kalshi contracts through IBKR's TWS API would let one account hold both legs of a Kalshi-vs-ForecastEx trade, so no money has to move between venues. I could not confirm whether IBKR adds its own commission on Kalshi contracts.
- **Arizona:**
  - Election, economics and climate contracts on DCMs are protected for now by the 5 May 2026 injunction.
  - Sports contracts are on weaker ground after *Assad*.
  - A ruling on Arizona's pending appeal could cut off sports access with little notice.
  - Positions held at that moment could face forced liquidation or close-only rules. That is a guess based on how venues handled Nevada, not something I sourced.

### Gaps
- I could not open docs.polymarket.us. The terms of use on automated trading, per-account position limits and any interest on idle cash or positions are unknown. Polymarket US's own published state list is also unknown.
- Gemini Predictions: API docs, rate limits, bot terms and Arizona availability are unverified.
- Whether IBKR charges a commission on Kalshi contracts routed through its API, and how much depth ForecastEx has, are unknown.
- I found no ForecastEx position limits or market-maker programme details.
- Robinhood, Webull and Coinbase: absence of an API is inferred because no documentation turned up, not confirmed by a statement.
- I found no Ninth Circuit ruling on Arizona's appeal (26-4281) and no Supreme Court action as of the search.

---

## Q2. Liquidity reward and maker programs: how they pay, how competitive, and realistic yield for small size

### Takeaway
- **Polymarket US maker rebates:** since 19 Oct 2026 they start only at $10M of monthly maker volume. A $1k–$25k account would need to turn its capital over 400–10,000 times a month to qualify, so for us they are effectively zero.
- **Polymarket US Liquidity Incentive Program:** pays a pro-rata share of a pool for resting orders at or near the best price, scored every second. It is open to small accounts, but pool sizes were not visible to me, the scoring pushes you to the touch where adverse selection is worst, and the evidence from Polymarket's international venue is that naive reward farmers lose money.
- **ForecastEx coupon (~3.4% APY on position value):** this offsets the cost of holding positions; it is not an edge in itself. YES+NO boxes are netted away automatically, so it cannot be harvested risk-free.

### Cited Findings
- **Polymarket US Liquidity Incentive Program** ([docs: liquidity](https://docs.polymarket.us/incentives/liquidity); [rewards page](https://polymarket.us/rewards)):
  - **Scoring:** each second, every resting order scores size × DiscountFactor^(ticks from best price). With a 0.30 factor, 1,000 contracts at the best price score 1,000, at one tick 300, and at two ticks 90. Each pool is split pro-rata by score.
  - **Target Size:** only orders inside the "Target Size" walked outward from the best price qualify.
  - **Max Spread:** optional. In a second that fails the check, that second's share is forfeited, not redistributed. The changelog said no live programme set a Max Spread yet (the note may be dated).
  - **Payout:** calculated within 5 business days after each period and credited within 2 business days after that. Amounts under $1 are not paid. There is no per-person cap.
  - Index metadata showed the docs page as about 230 days old.
- **Polymarket US Volume Incentive Program:** pays a share of eligible taker-side notional, counting only trades between 3¢ and 97¢ ([docs: volume](https://docs.polymarket.us/incentives/volume)).
- **Polymarket US Market Maker Program:** application-only, with contractual obligations. Terms are not published ([docs: market maker](https://docs.polymarket.us/incentives/market-maker); [overview](https://docs.polymarket.us/incentives/overview)).
- **Polymarket US maker and taker rebate tiers** ([fees](https://docs.polymarket.us/fees); [changelog](https://docs.polymarket.us/changelog)):
  - Maker tier 1 (under $10M a month) gets nothing.
  - Taker rebates start at 3% of taker fees from $250k a month.
  - For October only, tiers used the higher of September volume or 4× the 12–18 Oct volume. From 1 Nov 2026 they reset monthly on the prior calendar month.
- **Polymarket international, for context (not accessible to us):**
  - Official maker rebates are paid daily from taker fees, pro-rata to your share of executed maker liquidity, with a $1 minimum ([Polymarket help](https://help.polymarket.com/en/articles/13364471-maker-rebates-program)).
  - In July 2026 the sports taker coefficient rose from 0.03 to 0.05 and the sports maker rebate share fell from 25% to 15% ([docs.polymarket.com changelog](https://docs.polymarket.com/changelog); [fees](https://docs.polymarket.com/trading/fees); [iGaming Business](https://igamingbusiness.com/prediction-markets/polymarket-sports-fee-hike-2026/)).
- **Practitioner evidence on reward farming** (all from the international venue):
  - The original poly-maker README says market making "is competitive and can lose money", calls itself "a reference implementation and a research harness, not a guaranteed-profitable product", gives no P&L, and lists its replay backtester as "not yet built" ([warproxxx/poly-maker](https://github.com/warproxxx/poly-maker), fetched).
  - A fork's README says: "In today's market, this bot is not profitable and will lose money" ([itgoyo/poly-maker](https://github.com/itgoyo/poly-maker)).
  - A developer who ran a clone live reported that maker rewards and some spread income were outweighed by bugs, testing losses and directional hits, for a negative net ([dev.to](https://dev.to/fatherson/i-cloned-a-polymarket-market-making-bot-and-ran-it-heres-what-i-learned-46ag)).
  - Another writeup argues the rewards are pay for taking adverse-selection risk, not passive income ([dev.to](https://dev.to/fatherson/why-free-money-polymarket-liquidity-tricks-dont-actually-work-the-fragile-assumptions-dismantled-46on)).
- **ForecastEx coupon:** 3.38% APY on the daily closing value of YES or NO positions (30 Sep 2026; see Q1). Opposing YES and NO positions are netted automatically ([IBKR API](https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/)).
- **Gemini maker fee:** makers pay 0.0175·p(1−p), so there is no maker rebate ([Gemini fees](https://www.gemini.com/fees/predictions)).

### Inferences
- **Maker rebate arithmetic, Polymarket US** (my calculation):
  - The old flat −0.0125 rebate was worth about 18% of the taker fee, roughly 0.31¢ per contract at 50¢.
  - Tier 2's −0.0035 is about 0.09¢ per contract at 50¢.
  - Both are out of reach at our size, so a maker on Polymarket US earns only spread plus liquidity-incentive pool share.
- **Liquidity-incentive yield** cannot be estimated without the pool sizes on polymarket.us/rewards. It is structurally competitive:
  - Payout is pro-rata to size × time at the touch.
  - The 0.30-per-tick decay means quotes even 2 ticks back earn about 9% of the touch score.
  - A $1k–$25k bot competes with funded market makers for the same score.
  - Treat it as a fee offset on a market-making strategy that already breaks even, not as income.
- **ForecastEx coupon:** a YES+NO "box" costs $1.02 including fees and is netted away immediately, so it cannot capture the coupon. Even if it could, at 3.38% a year it would take about 7 months just to earn back the 2¢ in fees, and it would trail any cash yield at or above the coupon rate. The coupon's value is that directional or hedge legs on ForecastEx carry close to zero cost of carry, compared with a venue that pays nothing.

### Gaps
- Current Polymarket US pool sizes per market or category, discount factors, target sizes, and how many participants farm them. The page could not be reached.
- Whether Polymarket US pays interest on cash or positions. Unknown.
- I found no incentive programmes for Gemini, Crypto.com/CDNA or ForecastEx market makers.

---

## Q3. Cross-venue price differences vs Kalshi: frequency, size after fees, duration, and settlement-rule mismatches

### Takeaway
- **2024:** working-paper and preprint research (not peer-reviewed) finds persistent law-of-one-price violations across Kalshi, Polymarket, PredictIt and Robinhood in the 2024 election. These were driven by different resolution wording, platform segmentation and limits to arbitrage.
- **2025–26 gap sizes:** with Polymarket US and Kalshi both open to Americans, measured gaps on matched pairs are mostly tiny. One dataset gives a median of 0.78¢, with only 1.5% of pairs at 5¢ or more.
- **Fee hurdle:** a taker-on-both-sides lock needs about a 3.5¢ gap near 50¢ and about 1.3¢ near 10¢ or 90¢.
- **Other venues:** I found no measurement of gaps against ForecastEx or Gemini.
- **Hidden basis risk:** settlement-rule mismatches are well documented, so "the same event" is often not the same contract.

### Cited Findings
- **Ng, Peng, Tao & Zhou, "Price Discovery and Trading in Modern Prediction Markets"** (SSRN 5331995), on the 2024 election ([SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/5331995.pdf?abstractid=5331995&mirid=1)):
  - Polymarket leads Kalshi in price discovery. Polymarket prices predicted later Kalshi prices but not the reverse.
  - "Substantial price discrepancies persist" even in the most liquid pair.
  - Investors could often have captured the gaps by buying each side at the cheapest venue.
  - At the time Polymarket was open only to non-US users, which segmented the platforms.
  - I read only summaries ([citing paper, arXiv 2604.24147](https://arxiv.org/abs/2604.24147)). The citing paper's claim that PredictIt was the most accurate platform is a secondary claim.
- **"Semantic Non-Fungibility and Violations of the Law of One Price in Prediction Markets"** ([arXiv 2601.01706](https://arxiv.org/abs/2601.01706)):
  - Cross-platform prices failed to converge in the 2024 election.
  - It attributes this to heterogeneous resolution semantics, institutional segmentation and persistent limits to arbitrage.
  - I could not reach the full text, so magnitudes are missing.
- **PredictMarketCap analysis of 186 Polymarket–Kalshi pairs:**
  - Median price difference 0.78¢; only 1.5% of pairs differed by 5¢ or more.
  - It publishes a CC BY 4.0 CSV of 385 sustained gap episodes of 2¢ or more ([predictmarketcap](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study)).
  - Methodology unverified: page unreachable, and the date range and fee treatment are unknown.
  - A live gap page also exists ([predictmarketcap.com/arbitrage](https://predictmarketcap.com/arbitrage)).
- **Midterm snapshots (the general election was 3 Nov 2026):**
  - Oddschecker, 30 Oct: Democrats win the House at 92% on Kalshi and 94% on Polymarket; Senate 69% on both; Texas Senate 70% vs 72% ([Oddschecker](https://www.oddschecker.com/us/insight/specials/politics/20261030-kalshi-vs-polymarket-for-the-midterms-which-should-you-use)).
  - DeFi Rate, 21 Oct: Democratic control at 86.5¢ on Kalshi, 86¢ on Polymarket and 85.8¢ on Polymarket US. It noted long shots were "often priced higher on one venue" ([DeFi Rate](https://defirate.com/odds/2026-midterms/)).
  - Predictions.io, 28 Aug: "Blue tsunami" at 44.5% on Polymarket vs 36.0% on Kalshi. This is likely a definitional mismatch, not a true arbitrage ([EdgeX/Predictions.io release](https://pro.edgex.exchange/en-US/news/article/polymarket-vs-kalshi-midterm-price-gaps)).
  - State races showed gaps of 1–2 points, e.g. Florida governor ([SportsBettingDime](https://www.sportsbettingdime.com/news/politics/kalshi-polymarket-election-odds-comparison/)).
- **Kalshi vs CME fed funds futures:**
  - Kalshi priced less tightening than the futures in the month before the July and September 2026 FOMC decisions, by a median 2.9bp and 1.7bp.
  - CME futures reacted to CPI about 0.6 s before Kalshi ([BMLL](https://www.bmlltech.com/news/market-insight/when-kalshi-and-fed-funds-futures-disagree)).
- **Practitioner claims:**
  - Cross-venue spreads have narrowed to 1–2% on major markets, from 5–10% in 2024 ([blockeden forum](https://blockeden.xyz/forum/t/i-trade-both-polymarket-and-kalshi-here-is-my-honest-comparison-of-fees-liquidity-ux-and-which-one-actually-has-better-odds/418); anecdotal, attribution uncertain).
  - One builder reports capturing 1.5–4.5% spreads on Fed and election markets, with no realized P&L, and warns of being "filled on Polymarket but stuck on Kalshi" ([dev.to](https://dev.to/realfishsam/how-i-built-a-risk-free-arbitrage-bot-for-polymarket-kalshi-4f)).
  - "An edge that looks like 4% before fees might shrink to 1% or less" ([Trevor Lasn](https://www.trevorlasn.com/blog/how-prediction-market-polymarket-kalshi-arbitrage-works)).
- **Settlement and definition mismatches** (secondary compilations: [Oddsshopper](https://www.oddsshopper.com/articles/prediction-markets/kalshi-vs-polymarket-settlement-rules); [DeFi Rate](https://defirate.com/prediction-markets/how-contracts-settle/)):
  - **Cardi B halftime show:** Kalshi's rules separated "dancing" from "performing" and it settled at the last traded price, 26¢ YES / 74¢ NO. Polymarket paid YES at $1.
  - **Zelenskyy suit:** the market flipped after nine days of UMA oracle disputes on Polymarket (international).
  - **Kalshi Oscars viewership:** settled NO on the first print of 18M. A later revision to 19.7M crossed the 19.5M line, but the settlement stood, because Kalshi uses the source agency's first print.
  - **Expiry times:** Kalshi often expires in the morning ET, while Polymarket's markets often run to 11:59 PM ET.
  - **Settlement process:** UMA settlement takes at least about 2 hours and can take days or weeks. Kalshi settles under its own filed rules.
  - **FOMC example:** Polymarket uses change buckets while Kalshi uses a threshold ladder, and one venue resolves on the scheduled meeting where the other resolves on any action in the calendar month. This is how apparent arbitrage "disappears" ([settlerisk](https://settlerisk.com/blog/cross-platform-risk-arbitrage-polymarket-kalshi); attribution uncertain).
- **Fees:** the 0.07·p(1−p) formula is the "industry-standard" taker fee on Kalshi and Gemini, and close to Polymarket US's 0.0695 ([DeFi Rate fees](https://defirate.com/prediction-markets/fees/); [Polymarket US fees](https://docs.polymarket.us/fees); [Gemini fees](https://www.gemini.com/fees/predictions)).

### Inferences
- **Fee hurdle** (my calculation; per contract, before Kalshi's round-up per order):

  | YES price | Kalshi + Polymarket US, both taker | Polymarket US maker + Kalshi taker | ForecastEx + Kalshi taker |
  |---|---|---|---|
  | 50¢ | 3.49¢ | 1.75¢ | 2.75¢ |
  | 30¢ | 2.93¢ | 1.47¢ | 2.47¢ |
  | 20¢ | 2.23¢ | 1.12¢ | 2.12¢ |
  | 10¢ | 1.26¢ | 0.63¢ | 1.63¢ |
  | 5¢ | 0.66¢ | 0.33¢ | 1.33¢ |

  - Worked example: buying YES at 48¢ on Polymarket US and NO at 48¢ on Kalshi (a 4¢ gross gap) nets about 0.52¢ per pair after both taker fees.
- **Most gaps do not cover a two-taker lock.** A 0.78¢ median and 1.5% of pairs at 5¢ or more fall under a 3.5¢ hurdle at mid prices.
  - The tradable set is mostly gaps of 2¢ or more in tails (prices under 20¢ or over 80¢), where fees are small.
  - Or gaps where one leg rests as a maker on Polymarket US at zero fee.
  - Those are also exactly where rule mismatches and stale quotes cluster.
- **Capital lock-up kills long-dated gaps.** Both legs are fully collateralized until settlement, with no cross-venue margin.
  - A 1¢ net edge annualizes to about 12% over 30 days, 4% over 90 days and 1% over 365 days.
  - So 2028-cycle political gaps are not worth it unless both legs earn about 3–4% interest, as Kalshi and ForecastEx positions do and Polymarket US positions may not.
  - Short-dated economics, sports and crypto contracts are the only ones where small net edges compound.
- **Speed:** Kalshi's measured lag behind CME of about 0.6 s on CPI means a seconds-latency cloud bot will not win news-driven gaps. Only the slower, persistent gaps (minutes to hours) in thinner markets are realistic for us.
- **Legging risk** is the main operational hazard: one leg fills and the other moves. Mitigations:
  - Rest the passive leg on the thinner venue.
  - Hedge on the deeper venue with immediate-or-cancel (IOC) limit orders.
  - Cap size at the displayed depth.

### Gaps
- I found no published measurement of ForecastEx vs Kalshi, Gemini vs Kalshi, or Crypto.com vs Kalshi gaps. Recording them is cheap and is the main missing evidence.
- I could not see gap duration (half-life) distributions. PredictMarketCap's CSV may contain them, but the site was unreachable.
- Polymarket US's own settlement rulebook (docs.polymarket.us/learn/markets/contract-settlement) was not read. Whether Polymarket US uses its own rules and settlement agent, rather than the UMA oracle, is unconfirmed. The mismatch cases above are largely Kalshi vs Polymarket international.

---

## Q4. Settlement/rule mispricings and structural edges specific to these venues

### Takeaway
The strongest documented structural mispricing is PredictIt's: linked-market bids summing to more than 110 and long shots overpriced, caused by position caps and a fee on profits. It is not automatable, because PredictIt bans bots. On venues we can automate:
- Polymarket US: logical inconsistencies (multi-outcome sums, ladders, combos versus their legs) and the favourite–longshot bias.
- ForecastEx: the coupon and buy-only mechanics.

Fees on every leg (about 0.0695·p(1−p)) and the 3¢–97¢ volume-incentive window shape which of these survive.

### Cited Findings
- **PredictIt:**
  - Zitzewitz (NBER Working Paper 35845, October 2026): bid prices on the same event's contracts "often persistently added to more than 110, implying an immediate arbitrage profit even after fees." PredictIt showed overpricing and a longshot bias "much larger than in other markets", attributed to limits on arbitrage: position limits on downside risk (then $850) and fees ([NBER](https://www.nber.org/papers/w35845); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7505978)).
  - An earlier study compared PredictIt with the Iowa Electronic Markets for 2016 and 2020. It found PredictIt "chronically mispriced", with large arbitrage profits in 2016 and non-negligible ones in 2020, persisting even after linked-contract pricing was introduced in October 2015 ([Journal of Prediction Markets](https://www.ubplj.org/index.php/jpm/article/view/1796)).
  - Cap now $3,500 and no trading API (see Q1).
- **Polymarket (international) logical arbitrage:**
  - Saguillo, Ghafouri, Kiffer & Suarez-Tangil (arXiv 2508.03474, August 2025) estimate about $40M of realized arbitrage profit between April 2024 and April 2025.
  - It came from "market rebalancing" within one market (outcome prices not summing to $1) and "combinatorial" arbitrage across logically linked markets.
  - The sample was 8,659 single-condition and 1,578 multi-condition markets.
  - Sources: [arXiv abstract](https://arxiv.org/abs/2508.03474); [Decrypt](https://decrypt.co/339958/40-million-free-money-glitch-crypto-prediction-markets).
- **Favourite–longshot bias on Polymarket** (arXiv 2609.12878): fees reduce the expected profit from selling overpriced tokens, so overpricing can persist and longshot buyers lose more ([arXiv PDF](https://arxiv.org/pdf/2609.12878)). The midterm comparison also noted long shots priced higher on one venue than the other ([DeFi Rate](https://defirate.com/odds/2026-midterms/)).
- **ForecastEx mechanics:** buy-only, exits by buying the opposite side, automatic netting, limit orders only ([IBKR API](https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/)). The coupon accrues on the daily closing value of YES or NO positions ([IBKR](https://www.interactivebrokers.com/predictionmarkets/en/home.php)).
- **Polymarket US combos:** fee curve on (1−p)^4 with a coefficient of 0.085 from 28 Oct 2026; no maker rebate on combo fills ([fees](https://docs.polymarket.us/fees)). An RFQ API exists for institutions ([RFQ](https://docs.polymarket.us/institutional/rfqs/overview)).
- **Volume incentive window:** Polymarket US counts only trades between 3¢ and 97¢ toward its Volume Incentive Program ([volume](https://docs.polymarket.us/incentives/volume)).
- **Settlement-rule asymmetries** (Q3): last-traded-price settlements, first-print rules, different cut-off times, and bucket versus ladder definitions ([Oddsshopper](https://www.oddsshopper.com/articles/prediction-markets/kalshi-vs-polymarket-settlement-rules)).
- **Insider risk in election contracts:** CNBC reported suspicious election-contract trading on prediction markets on 30 Oct 2026 ([CNBC](https://www.cnbc.com/2026/10/30/gamble-on-democracy-inside-suspicious-election-contracts-trading-on-prediction-markets-.html)). This is an adverse-selection risk for anyone quoting election markets.

### Inferences
- **PredictIt:**
  - The edge is real and well documented: buy a NO basket when YES bids sum well above 100, and fade long shots.
  - The fee falls on each winning contract's profit, not on the net across the basket. That is why sums above 100 persist.
  - Under our constraints it is a manual side-activity at best: no API, bots banned, a $3,500 cap per contract.
- **PredictIt prices as a signal:** using PredictIt as a contrarian input on Kalshi or Polymarket US long shots is weak. The feed is 60 s, licensed non-commercial, and biased by construction.
- **Polymarket US intra-venue logical arbitrage** (outcomes summing to more or less than 100, ladder monotonicity, combo vs leg prices):
  - Each leg pays taker fees, so a 3-leg sum violation near 33¢ per leg needs about a 4.6¢ total gap (3 × 0.0695 × 0.22).
  - The Polymarket international profits Saguillo documents were earned when most markets had zero taker fees, so they overstate what is available on Polymarket US.
- **Favourite–longshot fade on Polymarket US** (buying NO at 95–98¢ on long shots):
  - Fees there are tiny, about 0.33¢ at 5¢.
  - This is directional, with fat-tailed loss risk.
  - Most of those trades fall outside the volume-incentive window.
- **Settlement-divergence trades** (betting that two venues resolve differently): these are bets on rule interpretation, not arbitrage. Rule-reading is a valid edge, but capacity is tiny and outcomes are binary.

### Gaps
- No study measures logical-arbitrage frequency on Polymarket US itself, or on Gemini or ForecastEx.
- I could not access the full text of NBER 35845 (magnitudes after the 2025 cap increase) or of arXiv 2609.12878.
- Whether Polymarket US multi-outcome markets have a "negative-risk" structure that lets a NO basket be collateralized at its maximum loss, as PredictIt's linked markets are, is unknown.

---

## Q5. Evidence that anyone makes money doing this, and strategy scorecards for us

### Takeaway
- **Documented aggregate profits exist** for sophisticated players: about $40M of logical arbitrage on Polymarket international in 2024–25 (Saguillo), PredictIt arbitrage in the academic literature, and 2024 cross-venue gaps (Ng et al.).
- **No verified, audited P&L exists for a small retail bot** doing cross-venue or reward-farming strategies on US-legal venues.
- **The best practitioner evidence is negative.** The poly-maker READMEs say "not profitable… will lose money", and one developer's live clone netted negative.
- **Vendor claims are marketing.** Examples: "$10–$50/day on $10k", "100+ daily arbs", "a trader made $5.3M in a month".

The overall picture fits a market where gaps shrank once Polymarket US and Kalshi both opened to Americans, and where rebates now flow to high-volume makers.

### Cited Findings
- **Academic and realized profits:**
  - About $40M realized arbitrage profit on Polymarket in April 2024–April 2025 ([arXiv 2508.03474](https://arxiv.org/abs/2508.03474)).
  - Persistent PredictIt arbitrage "even after fees" ([NBER w35845](https://www.nber.org/papers/w35845)).
  - Exploitable 2024 cross-platform gaps ([Ng et al., SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/5331995.pdf?abstractid=5331995&mirid=1)).
- **Practitioner evidence:**
  - "In today's market, this bot is not profitable and will lose money" ([itgoyo/poly-maker](https://github.com/itgoyo/poly-maker)).
  - "Competitive and can lose money… not a guaranteed-profitable product" ([warproxxx/poly-maker](https://github.com/warproxxx/poly-maker)).
  - A live clone's result was negative after bugs, testing losses and directional hits ([dev.to](https://dev.to/fatherson/i-cloned-a-polymarket-market-making-bot-and-ran-it-heres-what-i-learned-46ag)).
  - A builder reports 1.5–4.5% spreads but no realized P&L ([dev.to](https://dev.to/realfishsam/how-i-built-a-risk-free-arbitrage-bot-for-polymarket-kalshi-4f)).
  - I found no trader writeup with months of verified net P&L.
- **Marketing claims (do not rely on):**
  - "$10 to $50 daily… on $10,000" ([ClawArbs](https://clawarbs.com/blog/polymarket-arbitrage-bot/)).
  - "100+ daily arbs" and "1–8% per trade" ([getarbitragebets](https://getarbitragebets.com/)).
  - "$5.3 million in one month" from a Polymarket sports high-frequency bot, unverified and not cross-venue ([Predik](https://predik.io/en/blog/arbitraje-polymarket-kalshi-oportunidades-traders-cuantitativos-en)).
  - A simulated "99.6% win rate" open-source bot ([GitHub, chaybuilds](https://github.com/chaybuilds/prediction-market-arbitrage-trading-bot)).
- **Market structure:**
  - Susquehanna is the day-one liquidity provider at Rothera ([Yahoo/Reuters](https://finance.yahoo.com/news/robinhood-susquehanna-over-ledgerx-expand-213343433.html); attribution uncertain within the LedgerX deal coverage).
  - Polymarket US runs an application-only Market Maker Program ([docs](https://docs.polymarket.us/incentives/market-maker)).
  - Polymarket US maker rebates start at $10M a month ([fees](https://docs.polymarket.us/fees)).

### Inferences

#### Survivorship and selection bias
The $40M Saguillo figure is an aggregate over the whole market, earned mostly by a few fast, well-capitalized wallets on a then-zero-fee venue. It says little about a seconds-latency bot with $1k–$25k on a fee-charging DCM. Likewise, the academic PredictIt profits were capped at $850 per contract and are not automatable.

#### Strategy scorecards for us
Context for every card: a cloud bot with seconds latency, $1k–$25k, API keys that can trade but not withdraw, paper-tested first. Each card covers logic (and whether it is sound), evidence and its credibility, fees and capacity, infrastructure and capital, risks, fit, and my confidence that it nets positive after fees for us.

**S1. Kalshi ↔ Polymarket US, taker on both legs ("pure arb")**
- **Logic:** buy YES on the cheaper venue and NO on the other when the combined cost is under $1 minus fees. Sound only if the rules match exactly.
- **Evidence:** median gap 0.78¢; 1.5% of pairs at 5¢ or more; 385 sustained episodes of 2¢ or more (PredictMarketCap, methodology unverified). Gaps narrowed from 2024 (anecdotal).
- **Fees:** 3.5¢ hurdle at 50¢, 1.3¢ at 10¢ or 90¢.
- **Capacity:** small; limited by depth at the touch.
- **Infrastructure:** two funded accounts, both APIs, a market-matching layer with a human-reviewed rule map. Capital is split across venues and locked to settlement.
- **Risks:** legging, rule mismatch, Arizona sports exposure, capital lock-up.
- **Fit:** poor as a standalone strategy.
- **Confidence: 10%.**

**S2. Kalshi ↔ Polymarket US, maker on Polymarket US (0 fee) and taker hedge on Kalshi (or the reverse where Kalshi has no maker fee)**
- **Logic:** sound. It halves the fee hurdle to about 1.75¢ at 50¢ and about 0.6¢ in the tails.
- **Evidence:** same gap data as S1. No P&L evidence.
- **Main risk:** adverse selection. The resting order fills when the other venue has already moved, so the hedge costs more than expected.
- **Fit:** reasonable for paper-testing: start on short-dated economics, Fed and crypto contracts and the tails of election markets; avoid sports in Arizona.
- **Capacity:** perhaps tens to low hundreds of dollars a month at $10k (my guess, unmeasured).
- **Confidence: 25%.**

**S3. Kalshi ↔ ForecastEx through the IBKR TWS API** (Fed, CPI, jobs, climate and election contracts)
- **Logic:** sound if the contract definitions match. ForecastEx costs $0.01 per side and pays a 3.38% coupon on position value.
- **Infrastructure:** IBKR can route Kalshi contracts through the same API, which may allow both legs in one account.
- **Evidence:** none measured; ForecastEx is likely thinner, and stale quotes are plausible.
- **Fees:** hurdle about 2.75¢ at 50¢ and 1.6¢ at 10¢ or 90¢ (taker on Kalshi).
- **Risks:** IBKR commission on Kalshi contracts unknown; ForecastEx is buy-only and nets opposing positions; Day/GTC/IOC limit orders only.
- **Fit:** good, because the data is cheap to collect. Run a recorder first.
- **Confidence: 25%** (wide uncertainty; could move to 40%+ or under 10% after one month of recorded quotes).

**S4. Polymarket US Liquidity Incentive Program farming**
- **Logic:** be paid to rest size at or near the touch. Sound but competitive.
- **Evidence:** the official scoring rules are known; pool sizes are not. International-venue practitioners report net losses.
- **Fees:** none for makers.
- **Capacity:** pro-rata, so a small share at small size.
- **Infrastructure:** a quoting engine with fast cancel on news, inventory limits, and a rewards reconciler (`get-incentive-earnings`; [docs](https://docs.polymarket.us/api-reference/incentives/get-incentive-earnings)).
- **Risks:** adverse selection, especially in election markets (CNBC insider reporting) and sports.
- **Fit:** moderate, as a fee offset for S2 rather than standalone.
- **Confidence: 20%.**

**S5. Polymarket US maker and taker rebates**
- **Logic:** sound, but the thresholds are $10M a month for makers and $250k for takers. Out of reach.
- **Confidence: about 2% that they matter for us.**

**S6. ForecastEx coupon or interest carry as an edge**
- **Logic:** the coupon reduces carry cost but cannot be boxed, because positions net. It is not standalone alpha.
- **Fit:** use it to prefer ForecastEx for long-dated legs.
- **Confidence: 5%** as a standalone strategy.

**S7. Polymarket US intra-venue logical arbitrage** (outcomes summing to more or less than 1, ladder monotonicity, combos vs legs)
- **Logic:** sound and mechanical.
- **Evidence:** strong on the international venue (Saguillo) but earned before fees there.
- **Fees:** Polymarket US taker fees on every leg raise the hurdle to several cents.
- **Competition:** likely from professional market makers.
- **Fit:** moderate; easy to scan and paper-trade.
- **Confidence: 15%.**

**S8. PredictIt structural edges** (NO-basket when bids sum above 100; fading long shots)
- **Logic:** sound; the evidence is strong (NBER 2026; Journal of Prediction Markets).
- **Fit:** prohibited for bots (no API, terms ban automation). A $3,500 cap and a 10% profit fee apply.
- **Confidence:** 0% as an automated strategy. About 50% that a careful manual trader nets positive, which is outside our mandate.

**S9. Lead–lag signals from public data**
- **Logic:** read Polymarket international prices (public data, no trading), CME fed funds futures or the PredictIt feed, and trade the lagging Kalshi or Polymarket US price.
- **Evidence:** Polymarket led Kalshi in 2024 (Ng et al.); CME leads Kalshi by about 0.6 s on CPI (BMLL).
- **Fit:** poor at seconds latency for news-driven moves. It might work on slow, persistent divergences. The PredictIt feed's non-commercial licence is a problem.
- **Confidence: 10–15%.**

**S10. Gemini Predictions vs Kalshi or Polymarket US gaps**
- **Logic:** sound in principle. Fees are the same as Kalshi's, and a thinner book may leave stale quotes.
- **Unknowns:** API terms and Arizona availability are unverified.
- **Fit:** worth a data-only recorder once API access is confirmed.
- **Confidence: 15%.**

**S11. Sports cross-venue and live (in-play) gaps** (Polymarket US, Kalshi, Gemini)
- **Logic:** sound in principle, but latency-dominated.
- **Arizona:** high legal risk after *Assad*, with the Arizona appeal pending.
- **Fit:** poor.
- **Confidence: 5–10%.**

**S12. Settlement-divergence or rule-reading trades**
- **Logic:** a directional bet on interpretation, not an arbitrage.
- **Evidence:** documented divergences (Cardi B, Oscars first print).
- **Fit:** low capacity; manual review needed.
- **Confidence: 10%.**

**S13. Favourite–longshot fade on Polymarket US** (buy NO on long shots at 95–98¢)
- **Logic:** plausible given the favourite–longshot study (arXiv 2609.12878) and longshot overpricing across venues; fees are tiny in the tails.
- **Risk:** directional and fat-tailed; one upset wipes out many small wins.
- **Fit:** moderate, and it overlaps with the Kalshi-side research.
- **Confidence: 30%.**

**S14. Robinhood, Webull, Coinbase, Crypto.com OG, FanDuel Predicts, Underdog, Novig, ProphetX, Sporttrade, DraftKings, Fanatics**
- No retail API, so not automatable. They are useful only as manual or read-only references.
- **Confidence:** not applicable (0% automated).

#### Ranking for what to paper-test first
1. **Record quotes:** run a recorder of matched Kalshi / Polymarket US / ForecastEx (through IBKR) quotes, using a human-approved rule-equivalence map. Measure gap size, half-life and depth, net of the fee table in Q3.
2. **Paper-test S2 and S3** on short-dated economics and Fed contracts.
3. **Add S4 rewards** only as a fee offset once S2 breaks even on paper.
4. **Treat S13** as a separately sized directional sleeve.

### Gaps
- I found no audited or credible multi-month P&L for small cross-venue or reward-farming bots on Polymarket US, ForecastEx or Gemini. Every positive claim found is marketing or unrealized.
- I found no data on how many participants compete for Polymarket US liquidity pools, or how much the pools pay.
- Capacity estimates above are my inferences, not measurements. They need the recorder data.
