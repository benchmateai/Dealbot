# Automated trading edges on US-accessible centralized crypto exchanges and US-regulated crypto derivatives: a small, seconds-latency, trading-only-key bot run by an Arizona resident (as of 4 Nov 2026)

*Method note: direct page fetches were blocked by this session's network allowlist (coinbase.com, help.coinbase.com, coindesk.com and financemagnates.com all failed DNS). Every finding below therefore comes from search-engine extracts of the cited pages, not from reading the full pages. Credibility tags: [primary] = exchange, regulator or paper; [trade press]; [secondary/low-cred] = review sites, blogs, aggregators; [older] = data before 2025 or of unclear date; [unconfirmed] = a single source or conflicting sources. Confidence figures are my own judgment and are labelled as inferences.*

## 1. Which venues can an Arizona resident use with trading-only API keys (withdrawal off), and what permission options does each one offer?

### Takeaway
As of November 2026 an Arizona resident can reach spot trading on Coinbase Advanced, Kraken, Gemini, Crypto.com, Binance.US (Arizona is explicitly supported) and Bitstamp. On the derivatives side the open venues are four US-regulated perpetual venues: Coinbase Financial Markets "perp-style" futures (since July 2025), Kraken perps listed on Bitnomial (since 15 June 2026), Crypto.com/OG.com perps (since 27 October 2026, up to 5x) and Kalshi BTCPERP (since 3 June 2026). CME micro BTC/ETH futures are also available through retail futures brokers and have traded 24/7 since 29 May 2026. Webull (listing on Kalshi) starts in November 2026 and Robinhood is "coming months". Every spot venue checked lets you make a key that can trade but not withdraw. The catches: at Coinbase, the same "transfer" scope that allows withdrawals is also needed to move funds between portfolios or sweep futures balances. It is also unconfirmed whether Kraken's or Crypto.com's new US perps can be reached by API at all.

### Cited Findings
#### Spot venues: access, API permissions, fees
- **Coinbase Advanced: API scopes.** A CDP API key carries `view`, `trade` and/or `transfer` — [Coinbase Advanced Trade API scopes](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/rest-scopes.md) [primary]. The key-permissions endpoint returns can_view, can_trade and can_transfer, and can_transfer covers deposits and withdrawals — [Coinbase API reference](https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/data-api/get-api-key-permissions.md) [primary]. "Move Portfolio Funds" and scheduling futures sweeps also require `transfer` — [Advanced Trade API permissions](https://docs.cloud.coinbase.com/advanced-trade/docs/rest-api-scopes) [primary]. A bot vendor's guide recommends View+Trade with Transfer disabled — [Bitsgap](https://bitsgap.com/helpdesk/article/9872088623516-How-to-Create-and-Set-Up-Coinbase-Advanced-API-Key) [secondary].
- **Coinbase Advanced: fees (sources conflict).**
  - US tiers were restructured on 16 Sept 2026. Accounts now start at 0.50% maker / 0.90% taker, fall to 0.35% / 0.75% from $10k of 30-day volume, and reach 0% maker at $50M — [Altrady](https://www.altrady.com/blog/crypto-trading-platforms/coinbase-advanced-trade); [DiarioBitcoin](https://www.diariobitcoin.com/exchanges/coinbase-reduce-sus-comisiones-de-advanced-y-baja-el-umbral-inicial-a-usd-10-000/) [secondary]. Coinbase's own page says only that tiers were restructured "to make lower rates kick in sooner" — [Coinbase](https://www.coinbase.com/en-gb/advanced-markets) [primary, no figures].
  - The earlier schedule was <$10k at 0.40% maker / 0.60% taker, down to 0% / 0.05% at $250M+ — [Financer](https://financer.com/review/coinbase) [secondary].
  - In early 2026 a user complained publicly that Coinbase's "Intro-1" tier charged 0.60% maker / 1.20% taker — [Stocktwits](https://stocktwits.com/news-articles/markets/cryptocurrency/coinbase-faces-criticism-for-fee-structure-again-nansen-ceo-calls-it-insane/cmUY2VlR49B) [trade press].
- **Kraken: API permissions.** Permissions are granular. Query Funds covers Balance, BalanceEx and TradeBalance. Create & Modify Orders covers AddOrder, EditOrder, AmendOrder and AddOrderBatch. Withdraw Funds covers WithdrawInfo, Withdraw and WithdrawCancel. Kraken's guidance is that a trading key "almost certainly" does not need Withdraw Funds — [Kraken API key guide](https://docs.kraken.com/exchange/guides/rest/api-keys.md); [Kraken support](https://support.kraken.com/gb/articles/360000919966-How-to-create-an-API-key) [primary]. HaasOnline says its bot never needs withdrawal permission — [HaasOnline](https://help.haasonline.com/usage/exchanges/kraken/) [secondary].
- **Kraken: fees (sources conflict).**
  - Kraken's fee page lists spot at 0.25% maker / 0.40% taker from $0, 0.20% / 0.35% from $10k and 0.14% / 0.24% from $50k — [Kraken fee schedule](https://www.kraken.com/help/fees) [primary, may predate July 2026].
  - On 9 July 2026 Kraken switched to cross-platform tiers, set by the better of 30-day spot volume or assets on platform — [Kraken support](https://support.kraken.com/sv-se/articles/cross-platform-fee-tier-changes) [primary].
  - Secondary sources put the new base tier at 0.40% / 0.80%, then 0.22% / 0.38% at $10k, down to 0.00% / 0.05% at $500M of volume or $100M of assets — [Datawallet](https://www.datawallet.com/crypto/kraken-fees-explained) [secondary; unconfirmed].
- **Gemini: API roles.**
  - Trader is the default role: it can check balances and place or cancel orders, but cannot call `/v1/withdraw`.
  - Fund Manager can withdraw crypto and make internal transfers.
  - Auditor is read-only and cannot be combined with other roles.
  - Sources: [Gemini API roles](https://docs.gemini.com/roles) [primary; developer pages last modified 17 Apr 2026 per the search extract]; [Gemini support](https://support.gemini.com/hc/en-us/articles/360055623512-Can-I-use-third-party-API-keys) [primary].
- **Gemini: fees (sources conflict).**
  - The schedule dated 9 July 2026 charges 0.00% maker / 0.01% taker on stablecoin pairs and 0.00% on RLUSD/USD, USDC/GUSD and GUSD/USD. Negative maker fees exist only in large-volume derivatives tiers — [Gemini ActiveTrader fee schedule](https://gemini.com/fees/activetrader-fee-schedule) [primary].
  - A different locale's page shows a base tier of 0.60% / 1.20% and 0.000% / 0.020% at $250M — [Gemini API fee schedule](https://www.gemini.com/pt-BR/fees/api-fee-schedule) [primary, format unclear].
  - A February 2026 review says 0.20% / 0.40% at the lowest tier — [Milk Road](https://milkroad.com/reviews/gemini/) [secondary; conflicts with Gemini's own pages].
- **Binance.US: Arizona access.** Arizona is on the official supported list and absent from the unsupported list. Unsupported states include AK, CT, GA, NY and TX — [Binance.US states](https://support.binance.us/en/articles/9842798-list-of-supported-and-unsupported-states-and-regions); [Binance.US unsupported](https://support.binance.us/hc/en-us/articles/360046786914-List-of-Unsupported-States) [primary]. As of 3 June 2026, 16 states and territories were unsupported — [Eco](https://eco.com/support/en/articles/15183698-binance-us-access-reserves-and-regulation-in-2026) [secondary].
- **Binance.US: fees.** Since April 2026 spot is 0% maker / 0.02% taker on all Advanced pairs — [Binance.US blog](https://blog.binance.us/zero-fee-trading/) [primary]; [Cointelegraph](https://cointelegraph.com/news/binance-us-cuts-spot-trading-fees-to-near-zero-in-push-to-undercut-rivals) [trade press]. The fee page also shows BNB/USD at 0% / 0.01% and a 0.01% taker rate from $500M of volume — [Binance.US fees](https://www.binance.us/fees) [primary; contradicts the "no tiers" press framing].
- **Binance.US: API keys.** The relevant type is the "Exchange API Key", with read, spot-trading and withdrawal toggles. A key left unused for 90 days without IP whitelisting is reset to read-only — [Binance.US API best practices](https://support.binance.us/en/articles/9842812-binance-us-api-keys-best-practices-safety-tips) [primary].
- **Binance.US: liquidity.** Kaiko found Binance.US had "the highest spreads and most outliers for most USD pairs" (about 2025; the exact Kaiko article is uncertain) — [Kaiko research](https://research.kaiko.com/insights/a-cheatsheet-for-bid-ask-spreads) [older]. Volumes were "abysmal" in 2025 — [The Block](https://www.theblock.co/post/370097/crypto-exchange-binance-us-cuts-fees-as-trading-volumes-remain-abysmal) [trade press, older].
- **Crypto.com Exchange.**
  - One comparison site lists spot at 0.25% maker / 0.50% taker below $10k and 0.20% / 0.40% from $10k (29 Aug 2026) — [comparison site](https://crypto-compare-site.vercel.app/vs/kraken-vs-crypto-com) [low-cred].
  - Sources conflict on whether US residents get API trading (one review lists API trading as restricted for US residents; another describes REST, WebSocket, bots and subaccounts) — [Skrumble](https://www.skrumble.com/crypto-exchanges/crypto-com-review/); [CryptoSlate](https://cryptoslate.com/crypto-exchanges/crypto-com-exchange-review/) [secondary; unconfirmed].
- **Bitstamp.** Robinhood completed its acquisition in June 2025 and the exchange now runs as "Bitstamp by Robinhood". Its US registrations include a NY BitLicense — [WhereLegalCrypto](https://wherelegalcrypto.pages.dev/exchanges/bitstamp/review/) [low-cred]. Spot is about 0.30% maker / 0.40% taker per reviews, though other reviews conflict — [CryptoNinjas](https://www.cryptoninjas.net/exchange/bitstamp-review/) [secondary]. No API permission documentation was found.

#### US-regulated derivatives venues
- **Coinbase Financial Markets (CFM) / Coinbase Derivatives: product and fees.**
  - "Perp-style" futures launched for US users in July 2025. They are 5-year contracts with up to 10x leverage. Funding accrues hourly and settles twice daily. Fees are "as low as 0.02%", include exchange, clearing and NFA fees, and carry a $0.15 minimum per contract — [Coinbase blog](https://www.coinbase.com/blog/perpetual-futures-have-arrived-in-the-us) [primary]; [The Block](https://www.theblock.co/post/363796/coinbase-launches-perpetual-futures) [trade press].
  - Coinbase's help page lists nano BTC, ETH, SOL and XRP perp-style contracts and says they have no expiration date. That conflicts with "5-year", although ticker names such as BIP-20DEC30-CDE imply a December 2030 expiry — [Coinbase contract specs](https://help.coinbase.com/en/derivatives/perpetual-style-futures/contract-specifications) [primary].
  - The fee schedule filed with the CFTC on 8 Oct 2025 is per side, per contract (amounts were not extracted) — [CFTC filing](https://www.cftc.gov/filings/orgrules/rules10082531658.pdf) [primary].
  - Launch material cites up to 10x intraday leverage on crypto perps and 20x on metals — [The Block](https://www.theblock.co/post/363796/coinbase-launches-perpetual-futures) [trade press].
- **CFM funding formula.** Each hourly rate is the average of twenty 3-minute samples of the futures-minus-spot gap, divided by 24. It accrues hourly and is cash-settled twice daily through Nodal Clear. Coinbase's worked example: +0.010% for one hour at a $100k mark price gives a $1.00 debit — [Coinbase US Perpetual-Style Futures 101](https://www.coinbase.com/learn/futures/us-perpetual-style-futures-101) [primary].
- **Other CFM perp-style listings.** Bitcoin Cash, Hyperliquid (HYP) and US500 — [Coinbase BCH](https://www.coinbase.com/futures/BCP-20DEC30-CDE); [Coinbase HYP](https://www.coinbase.com/futures/hyp-20dec30-cde); [Coinbase US500](https://www.coinbase.com/futures/US5-19DEC30-CDE) [primary]. The US500 perp-style future was slated for 17 Aug 2026 with 20x leverage — [Cryptonomist](https://en.cryptonomist.ch/2026/07/31/us500-perpetual-futures-coinbase/) [trade press].
- **CFM collateral.** Coinbase Derivatives and Nodal Clear aimed to accept USDC as US futures margin "sometime in 2026" — [The Block](https://www.theblock.co/post/358644/coinbase-derivatives-moves-to-add-usdc-as-collateral-for-us-futures-trading-by-2026) [trade press]. Whether this is live is unconfirmed. Coinbase Prime (institutional only) issues end-of-day margin calls funded automatically from a designated "Funding Portfolio", with optional USDC-to-USD auto-conversion — [Coinbase Prime help](https://help.coinbase.com/en/prime/derivatives-on-prime) [primary].
- **Coinbase International is not the US product.** BTC-PERP-INTX shows 0% maker / 0.03% taker and is a separate, non-US product — [Coinbase International](https://www.coinbase.com/advanced-trade/perpetuals/BTC-PERP-INTX) [primary].
- **Kraken US perps: launch and structure.** Live on Kraken Pro since 15 June 2026. The contracts are listed on Bitnomial, a CFTC-designated exchange that Payward (Kraken's parent) acquired in 2026, and orders route through NinjaTrader Clearing, doing business as Kraken Derivatives US (an FCM). At launch the assets were BTC, ETH, SOL, XRP, ADA, LINK, DOGE, LTC and AVAX. Kraken's US spot margin also runs on Bitnomial — [BusinessWire](https://www.businesswire.com/news/home/20260615010932/en/Kraken-Launches-Perpetual-Futures-for-US-Clients) [primary]; [CoinDesk](https://www.coindesk.com/markets/2026/06/15/kraken-debuts-u-s-perpetual-futures-as-crypto-derivatives-move-onshore); [FX News Group](https://fxnewsgroup.com/forex-news/cryptocurrency/kraken-launches-cfds-like-perpetual-futures-for-us-traders/) [trade press].
- **Kraken US perps: fees, collateral, funding.** Fees are a flat per-contract commission plus exchange, NFA and clearing fees (amounts not found) — [Kraken US futures fees](https://support.kraken.com/articles/us-futures-fees) [primary]. US collateral is USD only — [Kraken Perps support](https://support.kraken.com/articles/kraken-perps); [CCN](https://www.ccn.com/education/crypto/how-to-trade-crypto-perpetual-futures-on-kraken-us/) [mixed]. The funding interval conflicts: one Kraken page says a single cash adjustment at 3:00 pm CT daily — [Kraken Perps support](https://support.kraken.com/articles/kraken-perps) — while other sources say an 8-hour mechanism — [Bitcoin Magazine](https://bitcoinmagazine.com/news/kraken-launches-cftc-regulated-bitcoin) [unconfirmed]. Kraken's non-US derivatives fees (0.02% maker / 0.05% taker) do not apply to US clients — [Kraken derivatives fees](https://support.kraken.com/articles/360048917612) [primary].
- **Crypto.com / OG.com US perps.**
  - Launched 27 Oct 2026 for eligible US customers with up to 5x leverage, on BTC, ETH, SOL, HYPE, ZEC and SEI.
  - Trading and settlement fees were waived at launch; funding still applies. Collateral is USD cash only. Funding settles 3 times a day.
  - Retail reaches them through the Crypto.com App; advanced and institutional traders through the Crypto.com Exchange.
  - Crypto.com Derivatives North America received a CFTC clearing (DCO) license in Sept 2025, and Crypto.com registered as an NFA introducing broker.
  - Sources: [Cryptonomist](https://en.cryptonomist.ch/2026/10/28/crypto-perpetual-contracts-us/); [FinanceFeeds](https://financefeeds.com/og-com-and-crypto-com-bring-no-expiry-crypto-futures-to-u-s-traders-with-up-to-5x-leverage/); [Bitcoin.com News, "24/7 crypto perpetuals"](https://news.bitcoin.com/featured/og-com-and-crypto-com-launch-24-7-crypto-perpetuals-for-us-traders/) [trade press].
- **Kalshi BTCPERP.**
  - The CFTC approved it on 29 May 2026 and it went live on 3 June 2026. It tracks CF Benchmarks' BRTI, trades in units of 1/10,000 BTC, runs 24/7, is cash-settled, and had zero trading fees during the launch period — [DeFi Rate](https://defirate.com/news/kalshi-wins-cftc-approval-first-us-regulated-bitcoin-perps-opens-waitlist/); [Bankless Times](https://www.banklesstimes.com/articles/2026/06/04/kalshi-launches-first-u-s-regulated-bitcoin-perpetuals/); [crypto.news](https://crypto.news/bitcoin-perps-hit-kalshi-as-u-s-traders-get-long-awaited-access/) [trade press].
  - One source reports a "2% funding cap" without saying over what interval — [Datawallet](https://www.datawallet.com/crypto/best-regulated-perpetual-exchanges-usa) [secondary; unconfirmed].
  - Kalshi added gold and silver perps in Sept 2026 and a US 500 perp in Oct 2026 — [Wikipedia: Kalshi](https://en.wikipedia.org/wiki/Kalshi) [secondary].
  - An Unchained headline reports the CFTC's "first approvals at Kalshi and Coinbase" (details not extracted) — [Unchained](https://unchainedcrypto.com/cftc-opens-us-crypto-perpetuals-door-with-first-approvals-at-kalshi-and-coinbase/).
- **CME's lawsuit against the CFTC.** CME sued on 18 June 2026 in D.D.C. to vacate the Kalshi BTCPERP approval and the CFTC policy statement letting others list similar contracts, arguing they are swaps — [Lowenstein Sandler](https://www.lowenstein.com/news-insights/publications/client-alerts/fctm-breaking-news-cme-sues-cftc-over-approval-of-bitcoin-perpetual-futures-contract-fctm) [law firm]. The CFTC moved to dismiss for lack of standing — [Unchained](https://unchainedcrypto.com/cftc-asks-court-to-dismiss-cmes-lawsuit-over-kalshis-bitcoin-perpetual-futures/) [trade press]. A blog says the court ordered combined briefing and that a joint CFTC-SEC swap-definition comment period closed on 24 Aug — [De Silva Law](https://www.desilvalawoffices.com/articles/blog/2026/september/cme-perpetual-futures-lawsuit-cftc-moves-to-dism/) [unconfirmed]. One source notes the approval lacks formal rule status, so future leadership could reverse it — [Bitbo](https://bitbo.io/news/cftc-approves-bitcoin-perpetual-futures/) [secondary].
- **Webull and Robinhood perps.** Webull's perps are listed on KalshiEX and cleared through Kalshi Klear, with rollout to eligible Webull Futures customers from November 2026 — [FinanceFeeds](https://financefeeds.com/webull-sets-november-start-for-us-crypto-perpetual-futures/); [StockTitan](https://www.stocktitan.net/news/BULL/webull-puts-a-date-on-perpetual-futures-us-rollout-begins-in-y3p76wwye156.html). Robinhood announced on 29 Sept 2026 eight perp contracts, 10x for BTC and ETH and 3x for the rest, arriving in "coming months". One report says they will run via Bitstamp, but that is unconfirmed — [The Crypto Times](https://www.cryptotimes.io/2026/09/30/robinhood-plans-us-crypto-perpetual-futures-with-up-to-10x-leverage/); [CryptoDaily](https://cryptodaily.co.uk/2026/10/robinhood-us-crypto-perpetual-futures-ai-agents) [trade press].
- **Gemini derivatives.** Gemini Titan won CFTC approval in Dec 2025 for prediction markets only. Gemini said it would "explore" US futures, options and perps — [CoinDesk](https://www.coindesk.com/markets/2025/12/11/gemini-becomes-first-crypto-exchange-approved-by-cftc-to-offer-u-s-prediction-markets); [Gemini IR](https://investors.gemini.com/news-releases/news-release-details/gemini-receives-us-license-prediction-markets). Gemini's support page says it offers no dated futures or options at present — [Gemini support](https://support.gemini.com/hc/en-us/articles/12087160465051-Does-Gemini-offer-dated-futures-contracts-and-options-contracts). No US Gemini perps were found.
- **CME.**
  - 24/7 trading of crypto futures and options began on 29 May 2026 — [CME Group](https://investor.cmegroup.com/news-releases/news-release-details/cme-group-announces-launch-247-cryptocurrency-futures-and) [primary]. The first weekend traded about $50M notional — [CoinMarketCap Academy](https://coinmarketcap.com/academy/article/cme-launches-24-7-crypto-trading).
  - Micro Bitcoin (MBT) is 0.10 BTC with a $5 tick worth $0.50. CME's exchange minimum maintenance margin is 35%, and clearing firms may demand more — [CME education](https://www.cmegroup.com/education/articles-and-reports/how-to-trade-micro-bitcoin-futures) [primary]; [StoneX](https://futures.stonex.com/blog/understanding-cme-bitcoin-and-micro-bitcoin-futures-contract-specifications).
  - An April 2025 broker snapshot put MBT initial margin at about $3,267 — [Optimus Futures](https://optimusfutures.com/Micro-Bitcoin-Futures.php) [older; per search extract].
  - The CME exchange fee is about $2.50 per side per a trader forum post — [Elite Trader](https://www.elitetrader.com/et/threads/micro-bitcoin-commission-question.358314/post-5377198) [unverified, older].
  - Micro Bitcoin Cash and Micro Uniswap futures were set for 19 Oct 2026, pending review — [CME press release](https://www.cmegroup.com/media-room/press-releases/2026/9/22/cme_group_to_expandcryptoderivativessuitewithbitcoincashandunisw.html) [primary].
- **Equity perps.** On 3 Nov 2026 the CFTC let stock-linked perps for US venues be "deemed approved" under Reg 40.3, without naming venues or dates. Kalshi, Coinbase Derivatives, Bitnomial and OG.com have filed — [Cointelegraph](https://cointelegraph.com/news/cftc-equity-perpetual-futures-trading-us-exchanges); [crypto.news](https://crypto.news/equity-perpetual-futures-cftc-clearance-us-trading/) [trade press].

#### Arizona overlay
- **Arizona's criminal case against Kalshi.** In March 2026 Arizona AG Kris Mayes filed 20 misdemeanor counts in Maricopa County against KalshiEX LLC and Kalshi Trading LLC, over sports and election contracts. Kalshi argues the CFTC has exclusive jurisdiction. The CFTC filed a Ninth Circuit amicus brief (17 Feb 2026) backing preemption. Federal courts are split — [Morgan Lewis](https://www.morganlewis.com/pubs/2026/03/arizona-files-first-criminal-charges-against-a-prediction-market); [Covers](https://www.covers.com/industry/arizona-attorney-general-criminal-charges-at-kalshi-march-17-2026); [National Law Review](https://natlawreview.com/article/arizona-attorney-general-files-unprecedented-criminal-charges-against-prediction).
- **Binance.US in Arizona.** An Arizona outlet notes Binance.US's licensing does not cover every state and readers should check availability — [AZ Big Media](https://azbigmedia.com/blogs/binance-us-adds-0-maker-fees-self-custody-wallet-and-soc-2-type-ii-attestation-in-2026/).

### Inferences
#### Venue matrix (my synthesis, Nov 2026)
| Venue (entity) | What an AZ resident can trade | Trading-only key? | Small-account fees | Bot API? | Status / caveats |
|---|---|---|---|---|---|
| Coinbase Advanced | Spot | Yes: view+trade, no transfer | 0.50%/0.90% (0.35%/0.75% at ≥$10k) [secondary] | Yes | AZ exclusion not found but not verified |
| Coinbase Financial Markets (Nodal Clear) | Nano BTC/ETH/SOL/XRP perp-style, plus BCH, HYP, US500 | Probably the same CDP key with trade scope (inference) | "As low as 0.02%", $0.15 minimum per contract (2025 figure) | Likely via Advanced Trade API; its docs reference futures sweeps | Live since Jul 2025; current fee table not found |
| Kraken spot | Spot (spot margin via Bitnomial) | Yes: leave Withdraw Funds off | 0.25%/0.40% or 0.40%/0.80% (post-9 Jul 2026, secondary) | Yes | Fee data conflict |
| Kraken Derivatives US on Bitnomial | 9 perps, USD collateral only | Unknown | Flat per-contract fee (amount unknown) | Unconfirmed | Live since 15 Jun 2026 |
| Gemini | Spot; event contracts | Yes: Trader role | Conflicting; stablecoin pairs 0%/0.01% | Yes | No US perps |
| Crypto.com / OG.com | Spot; perps (6 assets, 5x) | Unknown | Spot 0.25%/0.50% (low-cred); perps fee holiday | Conflicting for US | Perps live since 27 Oct 2026 |
| Binance.US | Spot | Yes: read + spot trading; withdrawal off; IP whitelist | 0%/0.02% | Yes | AZ explicitly supported; thinnest books |
| Bitstamp by Robinhood | Spot | Not verified | ~0.30%/0.40% (conflicting) | Yes (not verified) | Possible future venue for Robinhood perps |
| Kalshi (KalshiEX / Kalshi Klear) | BTCPERP, gold, silver and US 500 perps | Kalshi API (parent project already uses it; not verified for perps) | 0 during launch promotion | Likely | CME lawsuit; AZ criminal case (non-perp) |
| CME via retail futures broker (Schwab, StoneX, Optimus/Tradovate, etc.) | MBT, MET and others, 24/7 | Broker-dependent | ~$2.50/side exchange fee (unverified) + commission | Broker API | Most settled legal footing; heaviest infrastructure |

#### Design implications of "trade but never withdraw"
- **The key can't move money between venues.** Every venue gives a trade-only key, so the binding constraint is that funds never move between venues automatically. Any multi-venue strategy needs a manual treasury runbook in which the owner moves USD and coins, plus bot alerts that fire well before margin thresholds.
- **Coinbase couples withdrawals with internal moves.** One `transfer` scope gates withdrawals, portfolio moves and futures sweeps. If CFM does not draw margin automatically from the spot USD balance, then even a same-venue spot+perp hedge needs owner action to keep the futures account funded. This must be verified on a small live account before any carry strategy depends on it.
- **Legal certainty, from most to least settled.** CME, then Coinbase CFM / Kraken-Bitnomial / Crypto.com-OG (designated exchanges self-certifying perps), then Kalshi BTCPERP, whose approval is being litigated by CME and whose operator is in a criminal dispute with Arizona.
- **The fresh opportunity set.** The newest venues (Kalshi, Crypto.com/OG, Webull from Nov 2026) combine zero-fee promotions with thin, retail-heavy books. Liquidity is small, though: onshore perp volume was estimated at about 0.15% of offshore — see Section 2.

### Gaps
- **Arizona eligibility not individually confirmed** for Coinbase CFM perps, Kraken spot and perps, Gemini, Crypto.com spot and perps, and Bitstamp. No source showed an Arizona exclusion.
- **API access and permission scopes not found** for Kraken US perps (Bitnomial/NinjaTrader), Crypto.com/OG perps, Bitstamp, Kalshi perps and CME retail brokers.
- **CFM details not found:** the current fee table, intraday versus overnight margin, whether margin draws automatically from spot USD, whether USDC collateral is live, and whether dated nano futures still trade in 2026.
- **Kraken US perps:** the funding interval conflict (daily at 3 pm CT versus 8-hourly) and the fee amounts.
- **Promotion end dates** for the Crypto.com/OG and Kalshi fee holidays.
- **Kalshi BTCPERP mechanics:** funding formula, leverage, and what the "2% cap" means.
- **Verification.** Primary pages could not be fetched (network allowlist), so every fee figure should be re-checked in-account before going live.

## 2. Funding-rate and basis carry: what US-accessible funding and CME/Coinbase basis paid in 2025–2026 after fees, margin and cost of capital; capital efficiency across venues; risks

### Takeaway
Carry has compressed to roughly cash-like levels.
- **Funding:** Ethena reported average perp funding of 11% in 2024, 4.9% in 2025 and 2.2% in 2026 (through 11 Aug).
- **CME basis:** 30-day annualized basis fell from a 15.3% peak in January 2025 to about 5% in April 2026 and about 3% in August 2026, against a 3.75–4% cash rate.
- **US perps:** single Coinbase snapshots imply about 5% annualized on BTC.

For our bot the spot leg cannot refill a short leg held at another venue. Hedged carry is therefore likely to be slightly profitable in absolute terms, but below T-bill yields in late-2026 conditions. It is a regime trade: switch it on only when funding or basis is sustained above roughly 6% annualized.

### Cited Findings
#### Academic evidence (mostly offshore and pre-2025)
- **Christin, Routledge, Soska & Zetlin-Jones, "The Crypto Carry Trade" (2022 draft):** the carry trade was "unusually profitable", with in-sample annual Sharpe ratios of about 7–10 — [CMU PDF](https://www.andrew.cmu.edu/user/azj/files/CarryTrade.v1.0.pdf) [primary, older, in-sample].
- **Schmeling, Schrimpf & Todorov, "Crypto carry", BIS WP 1087 (Apr 2023, revised Oct 2025):**
  - Average carry is above 10% p.a. and can reach more than 40% (PDF) or up to 60% (summary page).
  - Carry is driven mainly by convenience yield from trend-chasing smaller investors and scarce arbitrage capital, not by interest-rate differentials.
  - High carry predicts price crashes.
  - Margin spikes and liquidations during drawdowns make cash-and-carry risky.
  - Sources: [BIS](https://www.bis.org/publications/working-paper-1087-crypto-carry); [BIS PDF](https://www.bis.org/publ/work1087.pdf); [CEPR DP 20719](https://econpapers.repec.org/RePEc:cpr:ceprdp:20719) [primary].
- **He, Manela et al. on perpetual futures:** perp deviations from no-arbitrage prices are "considerably larger" than in currency markets — [arXiv](https://arxiv.org/pdf/2212.06888v2) [primary].

#### 2024–2026 funding levels (mostly offshore)
- **Ethena (via CoinDesk, 28 Aug 2026):** average funding was 11% in 2024, 4.9% in 2025 and 2.2% in 2026 through 11 Aug. Equity perps paid about 14% on Hyperliquid and 17.5% on Binance, against "low single digits for bitcoin" — [CoinDesk](https://www.coindesk.com/business/2026/08/28/ethena-looks-beyond-crypto-to-squeeze-yield-from-booming-equity-perpetuals) [trade press citing Ethena].
- **sUSDe yield:** about 4–30% across 2024–25 and "high single digits" by Q2 2026 — [Eco](https://eco.com/support/en/articles/15254002-ethena-usde-and-susde-2026-delta-neutral-yield) [secondary]. Another report gives about 3.72% in early 2026 per Messari — [Stablecoin Insider](https://stablecoininsider.org/ethena-usde-q1-2026-report/) [secondary]. The two conflict.
- **USDe supply** fell from about $14.8B (early Oct 2025) to $4.97B (7 Oct 2026) per DefiLlama. At early-October 2026 funding a basis trade nets about 3.5%, below the Fed's 3.75–4.00% range — [Panaprium guide](https://www.panaprium.com/blogs/i/crypto-basis-trading-evaluate-platforms-risk) [secondary].
- **Binance's baseline:** funding includes an interest component of 0.01% per 8 hours, and a blog reports "78% of a quarter at 0.01%" (which quarter is unclear) — [Coincub](https://coincub.com/blog/perpetual-futures-funding-rates-78-of-a-quarter-at-0-01/) [secondary]. Binance funding printed 0.0100 on 31 Oct 2026 — [CryptoQuant](https://cryptoquant.com/insights/quicktake/6ae77a721c48840a11173491-Coinbase-Premium-Index-Falls-to-0204-Near-Its-One-Year-Low).
- **Onshore versus offshore:** BTC perp funding was +0.0043% per 8 hours on 23 June 2026, and a guide claims positive onshore funding "tends to run lower than offshore" — [CoinUnited](https://coinunited.io/en/research/crypto/crypto-perpetual-futures-complete-traders-guide-2026) [low-cred].
- **Onshore scale:** leverage is about 5–10x onshore versus 50–125x offshore — [Datawallet](https://www.datawallet.com/crypto/best-regulated-perpetual-exchanges-usa). Onshore volume is about 0.15% of offshore, extrapolated from a two-week window — [MarketTrace](https://markettrace.ai/blog/regulated-us-perps-order-flow) [secondary].

#### US-venue funding snapshots (cached pages, roughly Oct 2026; single readings)
- **CFM snapshots:**
  - Coinbase CFM BTC: +0.0006% per hour, longs paying shorts, at a $78,005 mark — [Coinbase BIP](https://www.coinbase.com/futures/BIP-20DEC30-CDE).
  - Bitcoin Cash: +0.0005% per hour — [Coinbase BCP](https://www.coinbase.com/futures/BCP-20DEC30-CDE).
  - HYP: +0.0010% per hour — [Coinbase HYP](https://www.coinbase.com/futures/hyp-20dec30-cde).
  - US500: −0.0003% per hour, shorts paying longs — [Coinbase US500](https://www.coinbase.com/futures/US5-19DEC30-CDE).
- **Coinbase International (not US-accessible):** 0.0074% per hour — [Coinbase International](https://www.coinbase.com/advanced-trade/perpetuals/BTC-PERP-INTX).

#### CME basis 2025–2026
- **Peak to unwind:** Amberdata's reconstruction puts the 30-day annualized basis at a 15.3% peak in Jan 2025, 6.9% before the October break and 4.5% at the trough — [crypto.news](https://crypto.news/cme-bitcoin-futures-slump-as-basis-trade-unwinds-and-wall-street-steps-back/) [trade press].
- **April 2026:** about 5% annualized against about 4.5% risk-free. Average daily CME BTC open interest was under $8B in March and $7.2B in early April 2026, the lowest since Feb 2024 — [The Block](https://www.theblock.co/news/business/2026-04-09-cme-bitcoin-futures-activity-slumps-to-14-month-low-as-basis-trade-unwind-drains-institutional-demand-396722) [trade press].
- **August 2026:** 3-month annualized basis about 3%, below the 2-year Treasury's roughly 3.8%. Hedge funds flipped to net long, and BTC bottomed near $58k on 1 July — [CoinDesk](https://www.coindesk.com/markets/2026/08/10/a-rare-cme-shift-hedge-funds-abandon-structural-shorts-to-bet-on-a-bitcoin-rally) [trade press].
- **October 2026:** on 19 Oct the raw basis on the Dec 2026 contract was 0.86%, with spot near $81,850 — [ProveYourEdge](https://proveyouredge.com/articles/bitcoin-futures-basis-cme-spot-cash-and-carry) [low-cred, single calculation].

#### Collateral and margin facts relevant to cross-venue carry
- **Kraken US and Crypto.com/OG perps take USD only;** Crypto.com/OG goes to 5x at most (see Section 1). CME minimum maintenance margin is 35% — [CME education](https://www.cmegroup.com/education/articles-and-reports/how-to-trade-micro-bitcoin-futures).

#### Practitioner economics (vendor and educational sources)
- **Small accounts:** the strategy is "usually not suitable for small accounts", because fees and slippage take a larger share and net profit "may sit near zero or go negative" — [OneKey](https://onekey.so/blog/ecosystem/funding-rate-arbitrage-no-kyc/) [secondary; a no-KYC guide, cited only for this economics point].
- **Fees first:** fees must be cleared before funding contributes anything — [Chainstack](https://docs.chainstack.com/docs/hyperliquid-funding-rate-arbitrage).
- **Residual delta:** partial fills, differing contract sizes and settlement timing leave small unhedged exposure — [Mithril](https://mithril.money/blog/funding-rate-arbitrage-passive-income-perp-dex).
- **Early losses:** initial returns may be negative because of open, adjust and close fees — [Multiplesx](https://multiplesx.gitbook.io/help/how-to-create-a-funding-rate-arbitrage-bot).

### Inferences
#### Converting the numbers (my arithmetic)
- **Coinbase funding annualizes as hourly rate × 8,760.** The BTC snapshot of 0.0006%/h is about 5.3% a year; HYP about 8.8%; BCH about 4.4%; US500 about −2.6%. Coinbase International's 0.0074%/h is about 65% a year, but that product is not open to us. These are single readings, not averages.
- **CME, 19 Oct 2026:** 0.86% raw basis over about 66 days to a roughly 24 Dec 2026 expiry is about 4.8% simple annualized. That is only about 1 point above the 3.75–4% cash rate, and the input is low-credibility.
- **Ethena's 2.2% versus the Coinbase snapshot:** the Ethena average (offshore mix) and the ~5% Coinbase snapshot are not directly comparable. No US-venue average for 2026 was found.

#### Capital efficiency when the short leg sits at another venue
- **The constraint.** Spot gains at venue 1 cannot be moved to refill margin at venue 2 without the owner. Each short leg must survive a rally on its own.
- **The formula.** For short notional N, maintenance fraction m and an adverse rally x, starting equity needs E ≥ N·[m(1+x) + x].
  - CME, m = 0.35: a 30% rally needs E/N ≈ 0.76; a 50% rally needs about 1.03.
  - A 5–10x perp with m ≈ 0.10 (assumed; actual US perp maintenance levels not found): a 30% rally needs about 0.43; a 50% rally about 0.65.
- **Yield on total capital = carry ÷ (1 + E/N).** With 4% carry and E/N = 0.6 this is about 2.5%; with 2.2% carry it is about 1.4%.
- **Break-even against cash.** Funding needed to beat cash ≈ cash × (1 + E/N) + annual fee drag. That is about 3.9% × 1.6 + 0.1% ≈ 6.3% with a cheap spot leg at another venue, or about 3.9% × 1.25 + 1% ≈ 5.9% for the same-venue Coinbase version, if margin can be funded from spot. 2024's 11% average would have cleared this; 2025's 4.9% and 2026's 2.2% would not.
- **Interest on idle collateral matters.** If margin cash or USDC collateral earns interest (not found), the hurdle falls by roughly the yield on the margin portion.

#### Worked $10k example (illustrative, Nov-2026 conditions)
- **Configuration A, same venue (Coinbase):** about $8k spot BTC plus $2k USD margin, with $8k short on CFM.
  - Gross funding at 2.2–5.3% is about $176–$424 a year.
  - Fees: spot maker 0.35–0.50% each way is about $56–80 per round trip; the perp leg is about $3.
  - Net is about $90–$365 a year, or 0.9–3.7% on $10k.
  - Cash on the full $10k earns about $375–$400.
- **Configuration B, cross-venue:** about $6.2k spot on Binance.US (fees about 0%) plus $3.8k margin at the perp venue, which survives about a 50% rally at m = 0.10.
  - Gross is about $136–$330 a year; net is about 1.3–3.3%.
  - Again below cash, with two venues of counterparty risk.

#### Strategy cards (carry family)
**A. Same-venue cash-and-carry on Coinbase: long spot on Advanced, short a CFM nano perp-style future**
- **Logic:** sound. Shorts receive funding equal to the premium ÷ 24 each hour while the perp trades above the index, and the position is delta-neutral if sized correctly.
- **Evidence:** strong historical academic evidence (BIS, Christin), but levels have compressed sharply (Ethena: 2.2% in 2026). Coinbase-specific evidence is one ~5%-annualized snapshot. Credibility is medium for levels and low for US-specific levels.
- **Fees and capacity:** the spot leg dominates costs at about 0.7–1.0% per round trip as maker under the Sept-2026 tiers. The perp leg costs about 0.02% a side with a $0.15 minimum. Capacity is ample.
- **Infrastructure and capital:** one venue and one view+trade key. The critical unknown is whether futures margin draws automatically from spot USD; sweeps need `transfer`.
- **Risks:**
  - Short-leg liquidation in squeezes. Funding is highest when longs are crowded, which is exactly when further rallies drain short margin, and per BIS high carry also precedes crashes.
  - Funding turning negative, which happens in bear phases (the US500 reading was already negative).
  - Single-venue concentration and index/spot mismatch.
  - Fee-schedule changes: Coinbase changed tiers twice in 2026.
- **Fit:** the best structural fit for trading-only keys, and latency does not matter.
- **Confidence (my judgment):** about 50% that it nets positive after fees over 12 months; about 10% that it beats cash at Nov-2026 levels. It becomes attractive only above about 6% sustained funding.

**B. Cross-venue cash-and-carry: cheap spot leg on Binance.US (0% maker / 0.02% taker) or Kraken/Gemini, short perp at Coinbase CFM, Kraken-Bitnomial, Crypto.com/OG or Kalshi**
- **Logic:** sound, and it removes most of the spot-fee drag.
- **Evidence:** as for A. No US-venue funding history was found, and one low-credibility source says onshore funding runs below offshore.
- **Fees:** spot about 0–0.04% per round trip; perps about 0.02% a side at Coinbase, or 0 during the Kalshi and Crypto.com promotions.
- **Capital:** about 1.4–1.75× notional because of stranded margin (see the formula above).
- **Risks:**
  - Two counterparties; Binance.US has the thinnest books.
  - Liquidation if the owner misses a top-up.
  - Index mismatch: Kalshi settles on BRTI.
  - Kalshi's legal overhang.
  - Promotions ending.
- **Fit:** workable operationally but capital-inefficient, and it needs the owner treasury runbook.
- **Confidence:** about 55% net positive after fees; about 10% that it beats cash now.

**C. CME dated basis: long spot (exchange spot or a spot ETF at the futures broker) and short CME Micro BTC/ETH held to expiry**
- **Logic:** the cleanest trade. Convergence at expiry locks the basis, and CME has the most settled legal status.
- **Evidence:** basis of 15.3% in Jan 2025, about 5% in Apr 2026, about 3% in Aug 2026, and about 4.8% annualized on 19 Oct 2026 (low-credibility). Hedge funds exiting and open interest at a 2-year low corroborate the compression. Credibility is medium.
- **Fees:** about $2.50 a side exchange fee (unverified) plus commission. On one MBT (0.1 BTC, about $8.2k) that is about 0.05–0.06% a side; add spot-leg fees and roll costs.
- **Capital:** at a 35% minimum maintenance margin, surviving a 30% rally needs about 75% of notional at the futures broker, so about $14k of capital per MBT contract. Only the upper end of our budget fits even one contract (Micro ETH is smaller).
- **Infrastructure:** a separate futures brokerage plus its API; heavier than any CEX.
- **Risks:** margin calls in rallies (spot gains are stranded unless both legs sit at one broker), tracking error between spot and the CME CF Reference Rate, and thin basis.
- **Fit:** good on law and latency, poor on capital.
- **Confidence:** about 60% net positive after fees when held to expiry; about 10% that it beats cash at current basis. As a trigger-only deployment (enter only when annualized basis ≥ cash + about 5 points, as in Jan 2025), about 50% to beat cash on the occasions it triggers.

**D. Perp-versus-perp funding spread across US venues: long where funding is low or negative, short where it is high**
- **Logic:** sound in principle and needs no spot leg. Four US venues use different funding designs: Coinbase accrues hourly and settles twice daily; Kraken is daily or 8-hourly; Crypto.com settles 3 times a day; Kalshi reportedly has a 2% cap. Thin, retail-heavy books should produce differentials.
- **Evidence:** none measured. The only basis for expecting differentials is that onshore volume is tiny and one-sided.
- **Fees:** about 0 during promotions; about 0.02% a side at Coinbase.
- **Capital:** margin on both legs, each surviving moves on its own, so about 0.8–1.0× notional.
- **Risks:** different reference indices, funding-timing mismatch, liquidation, Kalshi legal risk, and API access at Kraken and Crypto.com still unconfirmed.
- **Fit:** good, since it is latency-insensitive.
- **Confidence:** about 20%. It is cheap to evaluate by logging public funding prints for 4–8 weeks first.

**E. Perp-versus-dated-future calendar carry on one venue (CFM perp versus dated nano futures, or CME calendar spreads)**
- **Logic:** captures the gap between expected cumulative funding and a fixed dated basis, with possible same-venue margin offsets.
- **Evidence:** none found, and 2026 availability of dated nano futures is unconfirmed.
- **Confidence:** about 15–20%.

**Adjacent lead (outside crypto scope):** offshore equity perps pay about 14–17.5% funding (Ethena). US equity-index perps exist (Coinbase US500, Kalshi US 500), and single-stock perps were cleared on 3 Nov 2026. But the one US500 snapshot was negative, so there is too little data to score this.

### Gaps
- No historical funding series was found for any US-regulated perp (Coinbase CFM, Kraken/Bitnomial, Crypto.com/OG, Kalshi), so averages, the share of negative-funding time and the gap to offshore are unknown.
- Missing CFM details: maintenance margin, intraday versus overnight requirements, and whether margin auto-funds from spot USD.
- Whether margin or USDC collateral earns interest at each venue.
- Whether US-listed perps qualify for Section 1256 (60/40) tax treatment, which would materially change after-tax carry. Not researched.
- No authoritative CME annualized-basis time series; the figures are third-party reconstructions.

## 3. Maker rebates and liquidity programs: which US venues pay makers, what volume it takes, and whether a small bot can earn net of adverse selection

### Takeaway
No US-accessible venue was found paying positive maker rebates to small accounts. The best available is zero maker fees:
- Binance.US on all spot pairs since April 2026.
- Gemini on stablecoin pairs.
- Launch fee holidays on Kalshi BTCPERP and Crypto.com/OG perps.

Coinbase reaches 0% maker only at about $50M a month (Sept-2026 tiers) and Kraken only at about $500M of volume or $100M of assets. Formal market-maker programs are institutional. Rebate farming is not a standalone edge for $1k–$25k; zero maker fees only lower the hurdle for spread capture.

### Cited Findings
- **Zero or near-zero maker fees:**
  - Binance.US: 0% maker / 0.02% taker on all spot pairs since April 2026 — [Binance.US blog](https://blog.binance.us/zero-fee-trading/).
  - Gemini: 0% maker on stablecoin pairs; negative (rebate) maker fees only in large-volume derivatives tiers — [Gemini fee schedule](https://gemini.com/fees/activetrader-fee-schedule).
- **Volume needed for 0% maker:**
  - Coinbase: $50M of monthly volume (post-Sept 2026; secondary), versus $250M before — [Altrady](https://www.altrady.com/blog/crypto-trading-platforms/coinbase-advanced-trade); [Financer](https://financer.com/review/coinbase).
  - Kraken: $500M of volume or $100M of assets (post-July 2026; secondary) — [Datawallet](https://www.datawallet.com/crypto/kraken-fees-explained).
- **Kraken derivatives tiers (non-US product):** 0.02% maker / 0.05% taker from $0, 0.0175% / 0.045% from $5M, 0.015% / 0.04% from $10M — [Kraken derivatives fees](https://support.kraken.com/articles/360048917612).
- **Coinbase Derivatives programs:**
  - A 2023 CFTC filing describes a lead market maker program "designed to incentivize liquidity and volume" (terms not extracted) — [CFTC filing](https://www.cftc.gov/filings/orgrules/rule021023lmxdcm001.pdf).
  - Broker rebate program renewals in 2022–23 — [CFTC filing](https://cftc.gov/filings/orgrules/rule121422lmxdcm003.pdf).
  - A CFTC exhibit titled "Crypto Market Maker Program", whose filename suggests a 30 Sep 2026 date, showed only its heading; exchange and terms unknown — [CFTC filing](https://www.cftc.gov/filings/orgrules/rules09302630733.pdf) [unconfirmed].
- **Coinbase's spot market maker program (Dec 2020)** required at least $500M in monthly volume — [Coinbase blog](https://www.coinbase.com/blog/coinbase-december-2020-market-maker-program) [older; likely outdated].
- **Coinbase International's liquidity program** (non-US) pays negative maker fees as a daily rebate at 00:00 UTC — [Coinbase International help](https://help.coinbase.com/en/international-exchange/trading-deposits-withdrawals/international-exchange-liquidity-program).
- **Launch fee holidays:** Kalshi BTCPERP had zero trading fees during launch — [Bankless Times](https://www.banklesstimes.com/articles/2026/06/04/kalshi-launches-first-u-s-regulated-bitcoin-perpetuals/). Crypto.com/OG perps waived trading and settlement fees at launch — [Cryptonomist](https://en.cryptonomist.ch/2026/10/28/crypto-perpetual-contracts-us/).
- **Third-party liquidity mining:** Hummingbot campaigns (2022) paid weekly reward pools; that is evidence on rewards, not trading profit — [Firo forum](https://forum.firo.org/t/2022-firo-hummingbot-campaign/2290?page=2) [older].

### Inferences
- **The volume tiers are out of reach.** $50M a month on $10k of capital is 5,000× monthly turnover; on $25k it is 2,000×. Rebate-tier economics belong to HFT firms.
- **"Rebate" for us means 0% maker on Binance.US.** That removes a cost but creates no income. Income must come from captured spread net of adverse selection, which Section 4 covers.
- **Fee holidays are the closest thing to a rebate.** They lower hurdles for market making and arbitrage on new perp venues, but are time-limited and come with thin flow.
- **F. Rebate or zero-fee capture as a standalone strategy:**
  - Logic: unsound, because there are no rebates at our size.
  - Evidence: fee schedules only.
  - Fit: none.
  - Confidence: about 5%.

### Gaps
- Current terms of Coinbase Derivatives' lead market maker program, and whether any US perp venue (Bitnomial, OG.com, Kalshi) runs a retail-accessible maker incentive.
- Binance.US market-maker program terms.
- When the Kalshi and Crypto.com promotions end.
- Whether Coinbase's stablecoin pairs are 0% maker; one review claims so, unconfirmed.

## 4. Market making on less-competitive pairs, and cross-exchange or triangular price gaps at seconds-level latency with pre-positioned inventory

### Takeaway
In normal markets, BTC and ETH spreads on Coinbase and Kraken are about 0.1–0.3 bps, so gaps between US venues are almost certainly far smaller than taker fees of 0.02–0.90% a leg. Spot-to-spot arbitrage is therefore fee-blocked, with two exceptions:
- **Stress events.** In the October 2025 crash BTC prices across major exchanges differed by more than $4,000 within minutes.
- **Near-zero-fee venue pairs.** These exist only where Binance.US spot (0.02% taker), Coinbase CFM perps (about 0.02%) or fee-holiday perps are combined.

Passive market making on thin pairs is only feasible where maker fees are 0% (Binance.US). The wide spreads there mostly price adverse selection, and no credible small-bot profit record was found.

### Cited Findings
- **Kaiko spread data:**
  - Spreads fell from about 1 to 0.3 bps on Coinbase, 0.4 to 0.1 bps on Kraken, and 2.3 to 1.9 bps on Bitstamp — [Kaiko](https://research.kaiko.com/insights/a-cheatsheet-for-bid-ask-spreads) [older, date unclear].
  - January 2026 average BTC and ETH spreads across tracked venues were 0.12 and 0.11 bps — [Kaiko snapshot](https://www.kaiko.com/resources/digital-asset-snapshot-2026-rally-etf-inflows-positioning-shifts?page=30).
  - During the October (2025) crash, BTC prices varied by more than $4,000 across major exchanges within minutes, and a Kraken-tied reference would have settled well below consensus — [Kaiko](https://kaiko.com/news/prediction-markets-face-a-pricing-infrastructure-problem).
- **Settlement-latency bounds (Hautsch, Scheuch & Voigt):** average arbitrage bounds of about 121 bps, set by blockchain settlement latency, explain 91% of cross-exchange BTC price differences in 2018–2019 data — [arXiv](https://arxiv.org/pdf/1812.00595.pdf) [primary, older].
- **Opportunity duration:** a 2023 Poloniex–Binance case study found significant opportunities "sporadic and short-lived", needing low-latency programs — [WatStreet paper](https://watstreet.netlify.app/researchPapers/CryptoArb.pdf) [student paper, older].
- **Hummingbot evidence:**
  - Anecdote: a market-making run on XEM/ETH lost about 1.2% (−$14.57) over a few days — [Hummingbot Academy](https://hummingbot.org/academy-content/sharing-is-caring-3-trading-pairs-i-picked/) [anecdote, older].
  - Vendor claim: users who tune parameters "tend to achieve higher profitability" — [Hummingbot docs](https://docs.hummingbot.org/academy-content/exploring-common-strategies/) [vendor].
  - Cross-exchange market making (XEMM) design: quote on one venue, hedge fills on another — [CoinAlpha/Hummingbot](https://coinalpha.notion.site/Cross-exchange-market-making-5bd7eb1d9831434a81176a5482309a87).
- **Adverse selection:** studied for AI-driven market makers in simulation only (2025) — [arXiv 2510.27334](https://arxiv.org/abs/2510.27334v1).
- **Coinbase Premium Index** (Coinbase versus offshore): −0.2037 on 31 Oct 2026 and negative 97 days in a row by late Aug 2026 — [CryptoQuant](https://cryptoquant.com/insights/quicktake/6ae77a721c48840a11173491-Coinbase-Premium-Index-Falls-to-0204-Near-Its-One-Year-Low); [KuCoin News](https://www.kucoin.com/news/flash/coinbase-bitcoin-premium-index-remains-in-negative-premium-for-97-consecutive-days) [aggregator]. This is a cross-border gap that offshore-excluded US traders cannot arbitrage.

### Inferences
#### Fee hurdles: minimum gap needed for two-venue taker arbitrage, small tiers
| Leg combination | Gap needed |
|---|---|
| Coinbase taker 0.75–0.90% + Kraken taker 0.40–0.80% | 1.15–1.70% |
| Binance.US taker 0.02% + Kraken taker 0.40–0.80% | 0.42–0.82% |
| Binance.US taker + Coinbase CFM perp (about 0.02%) | about 0.04% plus basis noise |
| Binance.US taker + Kalshi or Crypto.com perp during fee holidays | about 0.02% plus basis noise |

#### Inventory without withdrawals
- **Each venue's inventory changes only through trades.** After capturing a gap, inventory is skewed (coins on one venue, USD on the other) and only rebalances when the gap reverses or the owner moves funds. Capacity therefore equals the pre-positioned inventory, which is idle capital earning nothing between events.

#### Latency
- **We are the slowest participant.** Resting quotes get picked off when the reference price moves, and taker arbitrage on liquid pairs is gone within milliseconds. Seconds-level latency is only competitive when gaps last minutes, which means stress events.

#### Strategy cards (market making and arbitrage)
**G. Passive market making on thin pairs**
- **Logic:** earn the half-spread. Sound only if the spread exceeds adverse selection plus fees plus inventory risk.
- **Evidence:** Binance.US has the widest US spreads; there are no profitable small-bot records; the one numbers-bearing anecdote is a loss.
- **Fees:** only Binance.US (0% maker) is feasible. Coinbase (0.35–0.50%), Kraken (0.25–0.40%), Crypto.com (0.25%) and Gemini (uncertain, 0.20–0.60%) maker fees exceed typical spreads.
- **Capacity:** tiny, because volumes are "abysmal".
- **Infrastructure:** websocket order books, fast cancel/replace, inventory caps, and a reference price from Coinbase or Kraken.
- **Risks:** being picked off, alt crashes and delistings, Binance.US counterparty risk.
- **Confidence:** about 15% on Binance.US; about 5% elsewhere.
- **Variant, stablecoin pairs at 0% maker (Gemini, Binance.US):** tiny edge with depeg tail risk and no evidence; about 10–15%.

**H. Cross-exchange market making: quote Binance.US spot at 0% maker, hedge each fill on Coinbase CFM perps (about 0.02%) or fee-holiday perps**
- **Logic:** sound; this is Hummingbot's XEMM design. It converts inventory risk into hedge cost.
- **Evidence:** design documents only.
- **Economics:** the quoted edge must exceed the hedge fee plus the adverse move during a seconds-level hedge delay plus funding.
- **Capital:** coins and USD at Binance.US, plus margin at the perp venue. Both are static.
- **Risks:** hedge slippage, spot–perp basis, two counterparties.
- **Fit:** moderate.
- **Confidence:** about 20%.

**I. Cross-exchange spot arbitrage in normal markets**
- **Logic:** sound but fee-bounded.
- **Evidence:** modern spreads of 0.1–0.3 bps against fee hurdles of 0.4% or more, and opportunities that are short-lived.
- **Confidence:** about 5%.

**J. Stress-event dislocation capture**
- **Logic:** pre-positioned USD and coins on several venues, plus optional resting deep bids 5–10% below market, to catch cascades where venue prices diverge by 1% or more for minutes. Gaps then far exceed even Coinbase taker fees.
- **Evidence:** a single Kaiko observation (October 2025); no systematic study.
- **Risks:** API outages and rate limits exactly when needed, venue halts, stale data producing phantom gaps, catching a true crash, and inventory stuck on the wrong venue.
- **Fit:** seconds-level latency is acceptable when gaps last minutes; capital sits idle between events.
- **Confidence:** about 25% net positive over a year; event-dependent and lumpy.

**K. Triangular arbitrage within one venue**
- **Logic:** three taker legs. Only Binance.US's 3 × 0.02% = 0.06% hurdle is plausible. Liquid triangles close within milliseconds; stale quotes on thin Binance.US cross pairs would be tiny.
- **Confidence:** about 5%.

**L. New-venue fee-holiday microstructure: quote or take around BRTI/index on Kalshi BTCPERP (live since 3 Jun 2026) and Crypto.com/OG perps (since 27 Oct 2026); Webull flow arrives on KalshiEX from Nov 2026**
- **Logic:** plausible. Zero fees plus thin, retail-heavy books plus a public reference index (BRTI) may leave quotes that lag the index.
- **Evidence:** none on profitability; onshore volume is small (about 0.15% of offshore, extrapolated).
- **Risks:** promotions end, Kalshi litigation (CME suit; Arizona's criminal case is about other contracts), unconfirmed Crypto.com API access, and position limits.
- **Fit:** good where the API exists. The parent project already integrates Kalshi (an inference, not verified for perps).
- **Confidence:** about 25% while fee holidays last; about 10% after.

### Gaps
- No 2025–2026 measurement of the size and duration of price gaps between US venues (Coinbase vs Kraken vs Gemini vs Binance.US vs Crypto.com). Kaiko's cross-venue dislocation reports were not reachable.
- No current Binance.US depth or volume figures by pair.
- No statistics on triangular opportunities for US venues.
- No data on how closely Kalshi BTCPERP and Crypto.com/OG perp quotes track BRTI.
- No credible small-account market-making P&L records.

## 5. Statistical edges with real evidence (time-of-day, weekend, funding-driven mean reversion, listing effects): do they survive costs?

### Takeaway
The effects are documented but unstable, and almost always measured before costs:
- **Session returns flip.** Leadership switched between US and Asian hours across 2025–2026.
- **The CME weekend gap no longer forms**, because CME went 24/7 on 29 May 2026 (my inference).
- **Funding extremes** show at most a faint reversal tailwind.
- **Coinbase roadmap pops** (about 11–70% in 2025) fade quickly and are front-run; insider run-ups appear in 10–25% of listings.

Only near-zero fee venues (Binance.US maker or taker, about 0.02% US perps, fee-holiday perps) leave room to test any of them, and none reaches high confidence.

### Cited Findings
- **Baur, Cahill, Godfrey & Liu (2019, *Finance Research Letters*):** time-specific anomalies but no persistent effects, and lower activity on local evenings and weekends — [EconPapers](https://econpapers.repec.org/RePEc:eee:finlet:v:31:y:2019:i:c:p:78-92); [Quantpedia](https://quantpedia.com/are-there-any-simple-calendar-effects-in-bitcoin-market/) [primary, older].
- **Padyšák & Vojtko:** BTC intraday returns are stronger on days NYSE is closed (weekends and holidays). A 22:00–23:00 UTC rule earned about 33% annualized, with transaction costs "Not Reported" — [Quantpedia strategy](https://quantpedia.com/strategies/intraday-seasonality-in-bitcoin); [Quantpedia](https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/) [secondary summary; gross].
- **Session returns, 2025–2026 (crypto media and analytics, not peer-reviewed):**
  - 2025: US hours +8%, European +3%, Asian −1 to −2% — [CryptoRank](https://cryptorank.io/es/news/feed/5dd4f-bitcoin-us-trading-hours-strength-2025).
  - Late 2025 to early 2026: the pattern flipped in late 2025, with US sessions negative mid-to-late December, then North American hours led in early 2026, strongest from 2–4 pm UTC — [KuCoin News](https://www.kucoin.com/news/flash/bitcoin-gains-focused-on-north-american-trading-hours-in-2026-asian-session-weighs-on-performance) [aggregator].
  - August 2026: non-US hours still drive most of BTC's biggest moves. US hours' share of variance in big weeks rose from 24% before the Jan 2024 spot ETFs to 33% after — [Parafi](https://parafi.com/signals/bitcoin-biggest-moves-market-hours).
- **CME 24/7 trading since 29 May 2026** — [CME Group](https://investor.cmegroup.com/news-releases/news-release-details/cme-group-announces-launch-247-cryptocurrency-futures-and).
- **Funding as a return predictor:**
  - Brave New Coin found the link to next-period returns "loose" and "mixed" — [Brave New Coin](https://bravenewcoin.com/insights/testing-theory-is-perpetual-swap-funding-rate-predictive).
  - An independent analysis of Binance data from 2023–2026 found the factor's edge is the harvested funding spread, not a price forecast, with the crowded-long reversal "at best a faint tailwind" — [Bryan Vine](https://bryanvine.github.io/alpha-research/paper2.html) [non-peer-reviewed].
  - Presto Labs claims funding changes initially explain 12.5% of 7-day price variation — [Presto Labs](https://prestolabs.io/research/can-funding-rate-predict-price-change) [unverified method].
  - BIS: high carry predicts crashes — [BIS](https://www.bis.org/publications/working-paper-1087-crypto-carry).
- **Listing effects:**
  - Coin Metrics: new Coinbase markets averaged −1% to +14% from 10 days before to 10 days after announcement, and "under consideration" announcements had no significant effect — [Cointelegraph](https://cointelegraph.com/news/coinmetrics-finds-the-coinbase-effect-is-actually-pretty-lame) [older].
  - Messari: an average 29% 5-day return excluding outliers, 91% including them — [Cointelegraph](https://cointelegraph.com/news/messari-new-coinbase-listings-really-do-outperform-rival-exchanges); [Yahoo](https://www.yahoo.com/now/coinbase-effect-means-average-91-161123386.html) [older, 2021].
  - A UTS study estimates insider trading in 10–25% of listings, seen as a 19% higher abnormal return in the 7 days before announcement — [OODA Loop](https://oodaloop.com/briefs/cyber/study-insider-trading-occurs-in-10-to-25-of-cryptocurrency-listings).
  - A cross-listing study of 11 centralized exchanges finds positive abnormal returns before listing that turn negative from the first day after — [LIPIcs AFT 2025](https://drops.dagstuhl.de/storage/00lipics/lipics-vol354-aft2025/html/LIPIcs.AFT.2025.11/LIPIcs.AFT.2025.11.html) [primary].
  - Erasmus thesis: 9 of 10 event windows show significant positive cumulative abnormal returns — [EUR thesis](https://thesis.eur.nl/pub/59675/Final-Draft.pdf).
- **Roadmap examples:**
  - 2025: TOSHI about +70% before profit-taking; BNKR about +40%, still +29% after 24 hours; SKY about +11%, then fading. PENGU, POPCAT and MORPHO saw brief jumps that "quickly evaporated" — [BeInCrypto](https://beincrypto.com/coinbase-new-altcoin-listing-bnkr-jitosol-mplx) [trade press].
  - The listing moment often marks the top of the rally — [DailyCoin](https://dailycoin.com/coinbase-reveals-q2-listings-what-changes/).
  - SHIB rose 11% in an hour and 38% the next day, then retraced within weeks — [Decrypt](https://decrypt.co/97548?amp=1) [older].

### Inferences
#### Cost reality for daily-frequency signals
- **Round-trip cost per trade, annualized at one trade per day:**
  - Binance.US taker: 0.04% per round trip, about 14.6% a year.
  - US perps at about 0.02% a side: similar, plus funding.
  - Coinbase spot taker: 1.5–1.8% per round trip, which makes daily trading impossible.
- **Implication:** any daily or weekly stat signal must run on Binance.US (preferably maker fills), on US perps, or on fee-holiday perps.

#### Strategy cards (statistical)
**M. Time-of-day / session timing**
- **Logic:** plausible; driven by liquidity and flow timing.
- **Evidence:** regime-dependent, with leadership flipping within 12 months; the only quantified rule (about 33% a year) is gross and of unknown period.
- **Fit:** latency-insensitive.
- **Confidence:** about 10%.

**N. Weekend effect / CME gap fill**
- **Logic:** the CME-gap mechanism is obsolete now that CME trades 24/7. The weekend-return evidence is unstable.
- **Confidence:** about 5%.

**O. Funding-extreme reversal (directional)**
- **Logic:** weak. The evidence says the money is in harvesting funding, not predicting price.
- **Better use:** as a filter, not a signal. Avoid opening short carry legs after funding spikes, which per BIS precede crashes and squeezes.
- **Confidence:** about 10%.

**P. Listing and roadmap events**
- **Logic:** real, short-lived pops that a seconds-latency bot reaching Coinbase at 0.75–0.90% taker will mostly arrive late to.
- **The systematic side is the post-listing fade,** but we cannot short new alts: US perps cover only majors and there is no spot borrow.
- **Variant:** buying on Kraken or Binance.US when Coinbase adds a token to its roadmap faces faster bots.
- **Confidence:** about 10%.

### Gaps
- No peer-reviewed, out-of-sample, net-of-cost tests of crypto seasonality for 2025–2026.
- No 2026 listing-effect data.
- No study of funding-reversal on US-regulated venues.
- The Padyšák & Vojtko full text, including its cost treatment and sample period, was not read.

## 6. Who reports making money at small scale, how credible is it, and where is the survivorship bias?

### Takeaway
The only credible, sizable public evidence of carry profits comes from institutions and backtests:
- **Ethena** and **CME basis hedge funds** at scale.
- **Christin et al.** (in-sample Sharpe 7–10) and **BIS** (average carry above 10%) on paper.

The 2025–2026 record shows those profits shrinking: Ethena's funding fell from 11% to 4.9% to 2.2%, USDe supply fell about 66%, and hedge funds abandoned CME shorts. Small-scale "it works" claims are almost all vendor marketing, single illustrative trades or short anecdotes. No audited small-account track record was found. Survivorship and regime bias are pervasive.

### Cited Findings
- **Institutional carry is shrinking.** Ethena's funding averages fell 11% → 4.9% → 2.2% (2024 → 2026 YTD) and it is pivoting to equity perps — [CoinDesk](https://www.coindesk.com/business/2026/08/28/ethena-looks-beyond-crypto-to-squeeze-yield-from-booming-equity-perpetuals). USDe supply fell from $14.8B to $4.97B between Oct 2025 and Oct 2026 — [Panaprium](https://www.panaprium.com/blogs/i/crypto-basis-trading-evaluate-platforms-risk) [secondary]. Hedge funds abandoned structural CME shorts — [CoinDesk](https://www.coindesk.com/markets/2026/08/10/a-rare-cme-shift-hedge-funds-abandon-structural-shorts-to-bet-on-a-bitcoin-rally). CME open interest hit a 14-month low as the basis trade unwound — [The Block](https://www.theblock.co/news/business/2026-04-09-cme-bitcoin-futures-activity-slumps-to-14-month-low-as-basis-trade-unwind-drains-institutional-demand-396722).
- **Academic results come with caveats.** Christin et al.'s Sharpe of 7–10 is in-sample, from a 2022 draft, on offshore high-funding years — [CMU PDF](https://www.andrew.cmu.edu/user/azj/files/CarryTrade.v1.0.pdf). BIS flags crash risk and margin spikes — [BIS](https://www.bis.org/publ/work1087.pdf).
- **Vendor and educational economics:**
  - Mithril's example assumes about $12 a day on $10k at a 0.12% funding rate, with 0.02–0.05% round-trip fees — [Mithril](https://mithril.money/blog/funding-rate-arbitrage-passive-income-perp-dex).
  - A scanner tool advertises an example of about 41.3% APR after taker fees, a single illustrative trade on a thin market — [Funding Radar](https://apify.com/opaline_midge/funding-radar) [attribution uncertain].
  - Exchange-run arbitrage bots disclaim that returns depend on favorable funding — [Binance FAQ](https://www.binance.com/en/support/faq/detail/f330e17d6fc04679b9b21d6f9350e787) [offshore; cited only for the disclaimer].
  - Guides warn small accounts may net about zero or negative — [OneKey](https://onekey.so/blog/ecosystem/funding-rate-arbitrage-no-kyc/); [Multiplesx](https://multiplesx.gitbook.io/help/how-to-create-a-funding-rate-arbitrage-bot).
- **Market-making anecdotes:** the one numbers-bearing Hummingbot anecdote is a loss (about −1.2%) — [Hummingbot Academy](https://hummingbot.org/academy-content/sharing-is-caring-3-trading-pairs-i-picked/). Hummingbot's profitability claims are vendor statements — [Hummingbot docs](https://docs.hummingbot.org/academy-content/exploring-common-strategies/).

### Inferences
#### Credibility and bias
- **Credibility ranking:** peer-reviewed or central-bank work (BIS, Baur et al.) > academic drafts (Christin et al.) > institutional disclosures via trade press (Ethena, CME positioning) > analytics firms (Kaiko, Parafi, CryptoQuant) > vendor and exchange guides > anecdotes and scanners.
- **Regime bias.** Mithril's 0.12%-per-day example is about 44% a year, roughly 20 times 2026's 2.2% average. Most "funding arb pays" content was written in 2020–2021 or 2024.
- **Survivorship bias.** Losing small operators do not publish, and vendors (bot platforms, exchanges) profit from activity, not from user P&L.
- **Paper-trading caveat.** Paper tests are reliable for carry, because funding and basis are public and fills are not path-critical. They are unreliable for market making and arbitrage, because queue position, partial fills and adverse selection are not simulated. Those strategies need tiny live pilots after paper testing.

#### Overall scorecard (my judgment; confidence that it nets positive after all fees over 6–12 months at $1k–$25k under Nov-2026 conditions; "vs cash" = chance of beating ~3.75–4% T-bill yields)
| # | Strategy | Logic sound? | Evidence quality | Latency fit | Capital fit | Confidence net-positive | vs cash |
|---|---|---|---|---|---|---|---|
| A | Coinbase same-venue spot + CFM perp carry | Yes | Medium (compressed) | Good | Good if margin auto-funds | ~50% | ~10% |
| B | Cross-venue carry (Binance.US spot + US perp) | Yes | Medium | Good | Poor (1.4–1.75×) | ~55% | ~10% |
| C | CME micro basis held to expiry | Yes | Medium | Good | Poor (~$14k per MBT) | ~60% | ~10% (~50% if trigger-only) |
| D | US perp-vs-perp funding spread | Yes | None | Good | Medium | ~20% | ~10% |
| E | Perp vs dated calendar carry | Yes | None | Good | Medium | ~15–20% | <10% |
| F | Rebate/zero-fee capture alone | No | Fee schedules | n/a | n/a | ~5% | ~0% |
| G | Passive market making on thin pairs | Conditional | Weak/negative | Poor | Small | ~15% (Binance.US) / ~5% | <10% |
| H | XEMM (Binance.US maker + perp hedge) | Yes | Design only | Medium | Medium | ~20% | <10% |
| I | Spot cross-exchange arb, normal times | Yes but fee-bound | Weak | Poor | Idle inventory | ~5% | ~0% |
| J | Stress-event dislocation capture | Yes | One observation | OK | Idle inventory | ~25% | ~10% |
| K | Triangular, one venue | Yes but fee-bound | Weak | Poor | Small | ~5% | ~0% |
| L | Fee-holiday new perp venues (Kalshi, Crypto.com/OG) | Plausible | None | Medium | Small | ~25% while promos last / ~10% after | ~10% |
| M | Time-of-day | Weak | Unstable | Good | Small | ~10% | <10% |
| N | Weekend / CME gap | Weak (gap obsolete) | Unstable | Good | Small | ~5% | <5% |
| O | Funding-extreme reversal | Weak | Weak | Good | Small | ~10% | <10% |
| P | Listing / roadmap pops | Real but front-run | Medium (old) | Poor | Small | ~10% | <10% |

#### Implications for the paper-test plan (my recommendation)
1. **Start with data logging, which is cheap and decisive.** Record hourly and interval funding on Coinbase CFM, Kraken-Bitnomial, Crypto.com/OG and Kalshi BTCPERP, plus CME basis and the Binance.US-vs-Coinbase top of book. This produces the missing US funding history, sets triggers for A, B, C and D, and measures the edges behind H and L.
2. **Next, paper-trade A and D, then shadow-run L and H** with tiny live sizes while fee holidays last.
3. **Keep J as a dormant module** that wakes on volatility or dislocation alerts.
4. **Deprioritize G, I, K and M–P.**
5. **Default allocation.** In Nov-2026 conditions, holding idle capital in cash or T-bills beats every always-on strategy here. Switch on carry only when sustained funding or basis exceeds about 6% annualized.

### Gaps
- No audited or verifiable small-account track records for any strategy.
- Community sources (Reddit r/algotrading, Hummingbot Discord) were not mined in depth.
- No data on retail P&L on Coinbase CFM or the new US perp venues.
- No independent study quantifying survivorship bias in crypto-bot performance claims.
