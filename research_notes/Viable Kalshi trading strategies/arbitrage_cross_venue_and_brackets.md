# Arbitrage involving Kalshi: cross-venue (Polymarket, PredictIt, sportsbooks) and intra-event (brackets / mutually exclusive outcomes)

Research date: 2026-11-03. Every return, profit and "edge" figure below is an unverified claim by the party named. Method note: this session's network policy blocked direct fetches of arxiv.org, kalshi.com, docs.kalshi.com, help.kalshi.com and predictmarketcap.com, and GitHub API access to the bot repos was not enabled. Findings therefore come from search-engine summaries of those pages (often abstract-level). Read the full texts before relying on exact figures. Venue tags: **[Kalshi-only]** needs only the requester's Kalshi account. **[+Polymarket US]** needs a separate KYC'd Polymarket US account (US persons; reportedly not Nevada). **[+sportsbook]** needs licensed sportsbook accounts and physical presence in a legal state. **[+PredictIt]** needs a PredictIt account. **[non-US only]** means polymarket.com (international), which is close-only for US users.

## 1. How often do the same events trade at different prices on Kalshi and Polymarket (or sportsbooks), how large are the gaps after both venues' fees, and how long do they last?

### Takeaway
Gaps are common on displayed quotes but small once quotes are checked. The best audit found a median real Kalshi–Polymarket gap of about 0.8¢, against a fee wall of about 3–3.5¢ at mid prices, and none of its 12 headline "arbs" survived a freshness check. Gaps big enough to trade come in two kinds. Some are fleeting: in sports most close within seconds. Others are persistent but explained by differing contract semantics, settlement rules and capital lock-up, so they are not riskless. The academic work (Gebele & Matthes; Krause) finds persistent 2–4% "execution-aware" deviations and occasional 10–26 point spreads. It attributes them to structural frictions rather than free money.

### Cited Findings
**Academic / quasi-academic (all 2025–2026; abstract-level, unverified)**
- Gebele & Matthes, "Semantic Non-Fungibility and Violations of the Law of One Price in Prediction Markets" (arXiv 2601.01706, Jan 2026). They built a human-validated dataset of aligned markets covering more than 100,000 events across ten venues, 2018–2025. They find about 6% of events are listed concurrently across platforms, and semantically equivalent markets show "persistent execution-aware price deviations of 2–4% on average." They attribute this to the lack of a shared notion of event identity, so liquidity does not pool and "arbitrage becomes capital-intensive or unenforceable." — [arXiv abstract](https://arxiv.org/abs/2601.01706); [author thread on X](https://x.com/j9ebele/status/2008938480617849193)
- The same paper says that, depending on the assumed lock-up horizon, the gaps translate to "deterministic annualized returns ranging from single-digit percentages to several hundred percent." It notes positions must be held until resolution. — [arXiv HTML](https://arxiv.org/html/2601.01706v1)
- The paper's example of the same-looking market resolving differently is weather: Kalshi resolves on the Central Park station while the other venue uses a different station, and "these stations frequently disagree." — [arXiv PDF](https://arxiv.org/pdf/2601.01706)
- Krause, "Same Bet, Different Markets: Cross-Market Pricing Anomalies and the Limits of Arbitrage in Prediction Markets" (SSRN 6861841, listed June 1, 2026). The data is the "Digital Asset Market Clarity Act passes by Dec 31, 2026" market on Kalshi and Polymarket. The author claims "identical resolution criteria," yet finds a correlation of only 0.55 in probability levels and 0.22 in daily changes, with spreads reaching 26.1 percentage points. It attributes the mispricing to regulatory segmentation and predicts it shrinks as Polymarket gains CFTC-licensed US access. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6861841)
- Krause, "From Forecasting Tool to Financial Asset: Evidence of Persistent Arbitrage in Prediction Markets" (SSRN 6905683, June 11, 2026). Using the Clarity Act and July 2026 FOMC markets, it reports statistically significant persistent Kalshi–Polymarket arbitrage. It names capital lock-up, fiat-versus-crypto friction and regulatory segmentation as the barriers. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6905683)
- Krause, "Basis Risk Arbitrage in Prediction Markets: A Case Study of the Clarity Act" (SSRN 6984101). Kalshi YES plus Polymarket NO has a no-fee *expected* ROI of 5.08%. That falls to 4.82% after transaction fees and 2.67% after opportunity costs. The word "basis risk" in the title concedes the pair is not riskless. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6984101)

**Trackers / audits**
- PredictMarketCap, "Prediction Market Arbitrage: Polymarket vs Kalshi, Measured" (snapshot Aug 30, 2026, plus about six months of logged gaps). It covers 186 outcome pairs priced 2–98¢ on both venues. On raw quotes, the median gap was 1.2¢ and 59% of pairs showed paper profit after fees. After a freshness check, the "median real gap" was 0.78¢, and "0 of 12 headline arbitrages survived a one-day freshness check." It cites a "~3¢ fee wall at mid prices." The minimum viable gap "roughly doubled mid-study after Polymarket's fee rollout," and 54% of logged episodes peaked below 3¢. — [PredictMarketCap study](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study)
- A second search summary of the same study says 136 pairs were matched with fresh quotes and only 1.5% of pairs differed by 5¢ or more. The largest gap was Flávio Bolsonaro on May 13 (Polymarket 10.8¢ under Kalshi), which lasted 108 minutes. The released dataset has 385 sustained (≥2¢) gaps for two events (CC BY 4.0). The 186 vs 136 pair counts probably mean total pairs vs pairs with fresh quotes, but that is unconfirmed. — [PredictMarketCap study](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study); live tracker: [PredictMarketCap arbitrage page](https://predictmarketcap.com/arbitrage)
- Vendor scanners claim much more, for example "100+ daily arbs" (ArbBets, which sells a $149/month Pro tier scanning Polymarket, Kalshi, Opinion and Novig). That conflicts with the audit above and reflects commercial interest. — [ArbBets](https://getarbitragebets.com/); [ArbBets on OddsJam alternatives](https://getarbitragebets.com/blog/oddsjam-alternatives)
- Other tools exist (Apify actors that compute Kalshi–Polymarket spread after fees, Predik, PredTerminal, Kairos). These are marketing pages without audited results. — [Apify arb finder](https://apify.com/congism/polymarket-kalshi-arb-finder); [Apify spread-after-fees](https://apify.com/jpmarketdata/prediction-market-arbitrage); [Kairos](https://kairos.trade/blog/prediction-market-arbitrage)

**Builder logs (single-author, self-reported)**
- Michael Mustopo (dev.to) built a Kalshi–Polymarket *sports* matcher. He logged 870 cross-venue price gaps in one 24-hour window, with a median time open of about 9 seconds and 96% closed within 30 seconds. He found "no sizable arbitrage" and shipped the matcher as an API instead of a trading bot. — [dev.to](https://dev.to/michaelmustopo/built-a-prediction-market-arbitrage-no-sizable-arbitrage-found-36cf)
- An open-source scanner surfaced in the same search found 48 pairs under $1 after fees, worth about $339 in total on $49K of capital (about 0.7%). Of 100 pairs with a Kalshi midpoint of 10–90¢, only 8 had any gap after fees. The scanner is most likely lukeyin08/Prediction-Market-Scanner, which "prices the hedge after fees and order book depth"; that attribution was not directly verified. — [GitHub lukeyin08](https://github.com/lukeyin08/Prediction-Market-Scanner)
- Yash Kothari (June 24, 2026) counts about 44,400 open Kalshi markets and about 45,000 open Polymarket markets, so matching must be automated. His headline example is a "13¢ arb" on a Knicks game. His main lesson: "these look like arbs and they aren't." — [Kothari](https://www.yashkothari.ca/writing/polymarket-kalshi-arbitrage)

**Intra-Kalshi cross-representation (same underlying, different Kalshi contracts)**
- Talos research, cited by CryptoSlate, found an average spread of about 3.3 points across four Kalshi representations of Senate control, with a maximum of 9.7 points (October average 2.5). On Oct. 28 (2026 inferred), a four-contract hedge cost $3.02 before fees against a $3 gross payout, so there was no arb. — [CryptoSlate](https://cryptoslate.com/kalshis-senate-contracts-can-settle-on-different-answers-to-the-same-election/)

**Sportsbooks vs Kalshi**
- A Blockworks report found Kalshi–sportsbook gaps concentrated "during sharp momentum swings," up to 8.8%, but short-lived. It says thin in-game Kalshi liquidity limits executable size. Report date not confirmed. — [Blockworks](https://app.blockworks.com/report/from-betting-to-trading-how-kalshi-is-reshaping-sports-markets)
- In an NFL Week 1 2026 sample, Kalshi's implied vig was 4.32% vs FanDuel 4.44% and DraftKings 4.51%. In 2025 Kalshi trailed both by 30–40 bp. On combos (favourite plus over), Kalshi's implied vig was 23.8% vs 22.0% at both books, before Kalshi's transaction fees. — [Covers, Sept 16, 2026](https://www.covers.com/industry/kalshi-edges-fanduel-draftkings-sportsbooks-in-nfl-week-1-pricing-sept-16-2026); [Next.io](https://next.io/news/betting/kalshi-undercuts-draftkings-and-fanduel-in-nfl/)
- Conflicting, older: a Dec 29, 2025 analysis found Kalshi's pre-game NFL pricing lagged sportsbooks once all costs were included. — [SCCG](https://sccgmanagement.com/sccg-articles/2025/12/29/kalshi-pricing-vs-sportsbooks/)
- Anecdote: an arb seller on X (AdamkuArbs) reported a "sharp book → Kalshi" arb hit twice, with $1,619 staked for a "locked profit $17–$142." This is self-promotional. — [X post](https://x.com/AdamkuArbs/status/2016996453672235291)

**Fee wall inputs**
- Kalshi taker fee: ceil(0.07 × C × P × (1−P)), rounded up to the cent once per order, peaking at 1.75¢ per contract at 50¢. — [BotForKalshi guide](https://www.botforkalshi.com/blog/kalshi-arbitrage-guide); [OddsShopper](https://www.oddsshopper.com/articles/prediction-markets/kalshi-fees)
- Polymarket US taker fee coefficient: 0.0695 ($1.74 per 100 contracts at 50¢). — [Polymarket US fee schedule](https://docs.polymarket.us/fees)
- A 2026 guide puts the combined Polymarket + Kalshi taker fees at "roughly 3¢ to 3.5¢ per $1 set" near the middle of the price range. — [LaunchPoly](https://launchpoly.com/blog/polymarket-kalshi-arbitrage-guide)

### Inferences
- **Fee wall, my arithmetic from the formulas above.** Taking both legs costs about 0.1395 × p(1−p) per $1 set: about 3.5¢ at 50/50, 2.2¢ at 20/80 and 1.3¢ at 10/90, plus Kalshi's per-order round-up. A 0.78¢ median real gap is therefore negative after fees almost everywhere except near-certain prices. Those are exactly where lock-up and resolution risk dominate.
- **"Gap frequency" depends heavily on method.** Raw-quote scanners report many arbs (59% of pairs). Fresh-quote, depth-aware checks report almost none. Any scanner claim that does not state freshness and depth should be treated as an upper bound.
- **The gaps that persist for hours or months are structural.** Examples are the Clarity Act's 26-point spread, the 108-minute Bolsonaro gap and the 2–4% semantic deviations. They are mostly compensation for basis risk (wording, sources, deadlines) and capital lock-up, not riskless profit.
- **Sports gaps can be large, up to 8.8%, but last seconds.** Capturing them needs automated, co-located-grade execution on both sides, and a sportsbook will limit the account that does it (see §2).

### Gaps
- Could not read the full PredictMarketCap study (host blocked). Its duration distribution, per-category breakdown and exact fee model are unknown.
- No source measured gap *duration* for Kalshi vs Polymarket US specifically in politics or macro markets beyond the single 108-minute example.
- Search results mention a "2026 study of NBA markets" with a 3.6-second median arb window, and a claim that sports edges close in "15 to 30 seconds." Neither could be tied to an identifiable page, so they are excluded as findings.
- No measured data on Kalshi vs Robinhood, ForecastEx (Interactive Brokers), Crypto.com, DraftKings Predictions, FanDuel Predicts, Novig or ProphetX gaps. Robinhood is commonly understood to route some event contracts to Kalshi, which would make it the same book, but that was not verified here.

## 2. What are the real risks: resolution criteria/sources, settlement timing, withdrawals, capital lock-up, US access to Polymarket (incl. Polymarket US), and fees on each side?

### Takeaway
The dominant risk is **resolution divergence**: two contracts that read the same settle on different sources, deadlines or definitions, and a "locked" arb loses both legs. One audit's example turned an arb into a 74¢ loss. Second is **capital lock-up**. Prices embed a settlement discount, so part of any long-dated gap is just the cost of money, and Kalshi pays variable interest on positions while the other leg may not. For a US trader, Polymarket means the separate CFTC-regulated **Polymarket US** (fresh KYC, its own fee schedule), not polymarket.com. PredictIt's 10% profit fee and 5% withdrawal fee, and sportsbook account limiting, make those pairings structurally weak.

### Cited Findings
**Resolution / settlement divergence**
- PredictMarketCap warns that when "the same market" on Polymarket and Kalshi settles differently, a locked arbitrage becomes a 74¢ loss. — [PredictMarketCap study](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study)
- Kothari's example is a race where Kalshi paid if Connie Chan *advanced* and Polymarket paid if she got the *most votes*. If she finishes second, one venue pays YES and the other NO. — [Kothari](https://www.yashkothari.ca/writing/polymarket-kalshi-arbitrage); [OddsShopper on rule differences](https://www.oddsshopper.com/articles/prediction-markets/kalshi-vs-polymarket-settlement-rules)
- Kalshi binds each contract to a named Source Agency, while Polymarket criteria often allow "a consensus of credible reporting." Disputes go to the exchange (with the CFTC above it) on Kalshi, and to a bonded challenge window on Polymarket's oracle. — [DeFiRate](https://defirate.com/prediction-markets/how-contracts-settle/); [PredictReport](https://predictreport.io/blog/how-prediction-markets-resolve)
- Weather markets resolve on different stations that "frequently disagree." — [Gebele & Matthes](https://arxiv.org/pdf/2601.01706)
- Within Kalshi, Senate *control* contracts can resolve early on media calls, while *seat* contracts use the February composition. Seat-party contracts pay on who is sworn in, not who wins. A hedge across them can therefore settle on different facts. — [CryptoSlate](https://cryptoslate.com/kalshis-senate-contracts-can-settle-on-different-answers-to-the-same-election/); [Kalshi SENATEPARTY terms](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/SENATEPARTY.pdf)
- Coin Metrics counts up to 38 contracts across five event categories tied to Senate control. It says the "$8 arbitrage payout" holds only if both contract families settle on the same factual logic. — [TechFlow repost of Coin Metrics](https://techflowpost.com/en-US/article/34960)
- One guide claims a "2024 government shutdown" market resolved in opposite directions on the two venues. It is uncorroborated and suspect: to my knowledge, not from a source found here, no US federal shutdown occurred in 2024, while a long one ran Oct–Nov 2025. — [NYC Servers guide](https://newyorkcityservers.com/blog/prediction-market-arbitrage-guide)
- Related 2026 papers, titles seen only and not read: "Do prediction markets price events or adjudication? Evidence from the disputed Polymarket markets" (Economics Letters); "Settlement Manipulation in Prediction Markets" (arXiv 2606.31675); "From Public Evidence to Contractual Outcome: First and Stable Decidability on Kalshi" (arXiv 2609.16642). — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0165176526003721); [arXiv 2606.31675](https://arxiv.org/pdf/2606.31675); [arXiv 2609.16642](https://arxiv.org/pdf/2609.16642)

**Capital lock-up and interest**
- Gebele & Matthes, "When Certainty Is Not Worth It" (arXiv 2605.31431, May 29, 2026), argue prices are *discounted* probabilities because collateral is locked until settlement. They estimate a positive, maturity-dependent, time-varying "annualized settlement wedge." Adjusting for it cuts the near-certainty horizon gradient by about 48–88%. Polymarket's negRisk conversion shortens effective lock-up. — [arXiv abstract](https://arxiv.org/abs/2605.31431)
- Kalshi said it would pay 4.05% APY on cash *and open positions* starting October 10. The year is not shown in the result and is probably 2024, so treat it as an older fact. The rate is variable. Third-party pages in 2026 cite 3.50–4%. Interest accrues daily and is paid monthly, for eligible US users. — [Kalshi announcement](https://news.kalshi.com/p/interest-cash-open-positions); [Kalshi help: APY](https://help.kalshi.com/faq/interest-apy-on-kalshi); [DeFiRate (3rd-party rate)](https://defirate.com/?p=1823)
- Polymarket's international withdrawals are on-chain, taking minutes to hours. Capital cannot be shuttled between venues to chase arbs, so both sides must be pre-funded. — [Kothari search summary / guides](https://www.yashkothari.ca/writing/polymarket-kalshi-arbitrage)

**US access to Polymarket (2025–2026)**
- Polymarket US is a separate CFTC-regulated exchange. Its app opened to a waitlist on Dec 3, 2025 and, per secondary guides, to everyone by around May 13, 2026. KYC (legal name, DOB, US residential address, SSN) is mandatory and needs a fresh account. — [Polymarket101](https://www.polymarket101.com/en/docs/guides/polymarket-us-vs-international-2026/); [CopyTradeInsider KYC](https://www.copytradeinsider.com/blog/polymarket-kyc-requirements/)
- State availability is contested. Sources say 49 states plus DC excluding Nevada (which obtained a TRO in early 2026); an older guide says about 39 states as of April 2026. The CFTC reportedly sued Connecticut, Arizona and Illinois in April 2026 over preemption. All of this is secondary and unverified. — [StartPolymarket US](https://startpolymarket.com/countries/united-states/); [Predscope](https://predscope.com/guide/polymarket-us)
- polymarket.com (international) is close-only from the US, so existing positions can be exited but no new ones opened. This makes it **[non-US only]** for the requester. Polymarket US's web vs app-only status is reported inconsistently. — [Polymarket101](https://www.polymarket101.com/en/docs/guides/polymarket-us-vs-international-2026/); [Predscope](https://predscope.com/guide/polymarket-us)

**Fees on each side**
- **Kalshi.** Taker fee 0.07·C·P·(1−P), rounded up. Maker fees are zero except on listed series, where the coefficient is 0.0175. Third-party guides say that list includes Fed funds, CPI, jobs, GDP and NFL/NBA game series as of Oct 2026. One guide cites 7¢–$1.75 per 100 contracts for takers vs 2–44¢ per 100 for resting orders on NFL games. ACH is free; card deposits cost up to 2%. — [BettingPros](https://www.bettingpros.com/articles/how-kalshi-sports-betting-works/); [PredictionHunt Kalshi fees](https://www.predictionhunt.com/blog/kalshi-fees-complete-guide-2026); [BotForKalshi fees](https://www.botforkalshi.com/blog/kalshi-fees-explained)
- **Polymarket US.** Taker coefficient 0.0695. Maker *rebates* are tiered on prior-month maker volume: none below $10M, then −0.0035 ($10–49.9M), −0.0070 ($50–199.9M) and −0.0104 ($200M+), effective 1 PM ET Oct 19, 2026. Taker rebate tiers run up to 30% of fees at $50M+ monthly. — [Polymarket US fee schedule](https://docs.polymarket.us/fees); [Polymarket US changelog](https://docs.polymarket.us/changelog)
- **Conflicting third-party Polymarket US figures**: a flat 0.30% taker fee, or a 0.06 coefficient with a 0.0125 maker coefficient. These are superseded by the official page above. — [PredictionHunt](https://www.predictionhunt.com/blog/polymarket-fees-complete-guide); [OddsShopper](https://www.oddsshopper.com/articles/betting-101/polymarket-fees)
- **Polymarket international.** Category-based taker fees, from 0 on geopolitics up to about $1.75 per 100 at 50¢ on crypto. Taker fees on 15-minute crypto markets were introduced to curb latency arbitrage and are rebated to makers (date not confirmed here). — [Polymarket docs: fees](https://docs.polymarket.com/trading/fees); [Kairos](https://kairos.trade/compare/polymarket-fees); [Unchained](https://unchainedcrypto.com/polymarket-introduces-taker-fees-in-15-minute-markets/)
- **PredictIt.** 10% fee on net profit per contract plus 5% on withdrawals. The per-contract cap rose from $850 to $3,500 under CFTC Letter 25-20 (July 14, 2025). Regulatory status conflicts: Wikipedia cites approval to expand as a regulated exchange on Sept 5, 2025, and a Bloomberg Law headline (Jan 30, 2026) reads "PredictIt Gains CFTC Approval to Launch Regulated Exchange." — [Wikipedia](https://en.wikipedia.org/wiki/PredictIt); [CryptoSlate PredictIt review](https://cryptoslate.com/prediction-markets/predictit-review/); [Next Event Horizon](https://nexteventhorizon.substack.com/p/predictit-gets-upgrades)

**Sportsbook-specific**
- Sportsbooks limit sharp and arb accounts, for example cutting a $500 max stake to $50 and then $10, or restricting outright. Neither Kalshi nor Polymarket is reported to limit winners, but these claims come from vendors. — [ClawArbs on limits](https://clawarbs.com/blog/avoid-sportsbook-limits/); [ClawArbs on arb legality](https://clawarbs.com/blog/is-arbitrage-betting-legal/)
- State regulators (notably NJ and NV) have challenged Kalshi's sports contracts. Current status was not verified. — [Blockworks](https://app.blockworks.com/report/from-betting-to-trading-how-kalshi-is-reshaping-sports-markets)

### Inferences
- **Divergent resolution is asymmetric.** It costs about the full stake, not the spread. At a typical 1–3¢ net edge, one divergent settlement in 30–100 pairs wipes out the strategy. Every pair therefore needs a written rules audit: source, deadline, definition and edge cases such as postponements, ties or "advance vs win."
- **Interest mismatch is a hidden basis.** Kalshi's leg earns about 3.5–4% APY on open positions; whether Polymarket US pays any holding yield was not found. An apparent gap on long-dated pairs can simply be that interest difference, consistent with Gebele & Matthes' settlement wedge. A 1¢ net edge on a 3-month hold is about 4% annualized, roughly the Kalshi APY, so no excess return.
- **PredictIt is structurally hostile to arb.** If its leg wins at 40¢, the 10% profit fee takes 6¢, and the 5% withdrawal fee hits all capital that leaves. Gaps must exceed roughly 6–10¢ plus Kalshi fees.
- **Today (Nov 3, 2026) is US midterm election day.** Control, seat and margin markets on both venues are the textbook case where media-call and certification/swearing-in triggers differ. "Arbs" there are basis trades.

### Gaps
- Kalshi withdrawal limits and timing, and Polymarket US deposit/withdrawal rails and limits, were not found. One guide notes the US fee schedule is silent on deposit and withdrawal fees.
- Polymarket US's resolution process (exchange-determined vs UMA oracle) and its rulebook differences vs polymarket.com were not verified.
- Polymarket US API availability and terms for automated trading were not verified.
- The background to Polymarket's US re-entry (QCEX acquisition, CFTC no-action relief and amended designation, 2025) was not verified in this session.
- Current status of state litigation over Kalshi sports contracts was not verified.

## 3. Intra-event arbitrage on Kalshi: how often does the sum of YES asks fall below $1 (or the sum of NO asks below n−1), and does it survive per-leg fees? Any documented bots or measurements?

### Takeaway
**No independent, systematic measurement of Kalshi bracket-sum violations was found.** The only Kalshi-specific evidence is vendor scans. One reported a handful of genuine candidates, all "thin, longshot, and barely positive net of fees." Another, a scanner table, showed sums of 88–99% and claimed most were profitable after fees, which conflicts with the first and is likely last-price based. Per-leg taker fees make the YES-basket arb very hard: the fee wall grows toward 7¢ per set as legs increase. The NO-basket direction is structurally better. It is robust to non-exhaustive outcome sets and, with Kalshi's opt-in Collateral Return, capital-light. That also means professional market makers can capture it instantly. Polymarket analogs show that intra-market "rebalancing" was where most historical arb profit came from (about $40M, Apr 2024–Apr 2025, before fees existed there), and that executable single-market anomalies are now rare.

### Cited Findings
- **Mechanics.** In a Kalshi group where at most one outcome wins, buying every YES leg for under $1 is an arb on paper. Worked example: asks of 30¢, 28¢, 24¢ and 14¢ sum to 96¢, "a theoretical 4¢ field gap before fees and execution." — [BotForKalshi](https://www.botforkalshi.com/blog/kalshi-arbitrage-guide)
- **Exhaustiveness caveat.** Kalshi's `mutually_exclusive` flag guarantees that at most one leg resolves YES, not that one must. A YES-sum below $1 is not locked unless the legs cover every outcome. — [BotForKalshi](https://www.botforkalshi.com/blog/kalshi-arbitrage-guide)
- **Vendor live scan (Kalshi, undated).** A naive field-sum scan flagged 25 "arbitrage" events; gating to genuinely mutually exclusive events cut that to about 14. "Every genuine candidate was thin, longshot, and barely positive net of fees." Partial fills break the hedge, and maker fees apply on some series. — [BotForKalshi](https://www.botforkalshi.com/blog/kalshi-arbitrage-guide)
- **Conflicting vendor scanner.** PredictMarketCap's Kalshi "Overround Scanner" lists multi-outcome sums such as 88.3%, 97.0%, 98.0% and 99.0%, with a header like "33 markets with gap, 30 profitable after fees." The methodology (last price vs executable ask, depth, exhaustiveness) is unknown. — [PredictMarketCap arbitrage page](https://predictmarketcap.com/arbitrage)
- **Tools.** An Apify actor sells "Kalshi Arbitrage API — Group Profit After Fees." The GitHub repo MikhailPeganov/Kalshi-arbitrage detects "riskless complement and group arbitrage in Kalshi-style binary event markets" but "runs on simulated order books, not live data," so it offers no live evidence. — [Apify](https://apify.com/jpmarketdata/kalshi-odds-arbitrage); [GitHub](https://github.com/MikhailPeganov/Kalshi-arbitrage)
- **Kalshi Collateral Return.** This opt-in, per-event feature "gives you cash back early when you buy hedged positions" in mutually exclusive markets, mainly for No positions. The flag locks when your first order in the event is placed, even before a fill. You may be unable to sell positions whose collateral was returned. — [Kalshi help: Collateral Return](https://help.kalshi.com/en/articles/13823816-collateral-return)
- A trader on X reported collateral return on No positions across two mutually exclusive brackets (Fed Chair market) "just doesn't work sometimes," even when enabled. This is an anecdote. — [X post](https://x.com/tenad0me/status/2021851382735679525)
- Polymarket has the equivalent on by default through neg-risk. — [Vibe Trading Substack](https://vibetrading.substack.com/p/10x-your-kalshi-profits-with-this)
- **Polymarket analog, historical.** Saguillo, Ghafouri, Kiffer & Suarez-Tangil (AFT 2025; arXiv 2508.03474) estimate about $40M of realized arbitrage profit on Polymarket from April 2024 to April 2025. They split it into "Market Rebalancing" (within one market or condition) and "Combinatorial" (across markets). Combinatorial arb was rare: only 13 strict pairs in the election group. A peer-review commentary notes the estimate depends on heuristics not misclassifying trades. Polymarket charged essentially no trading fees in that period. — [Paper PDF](https://suarez-tangil.networks.imdea.org/papers/2025aft-arbitrage.pdf); [Dagstuhl/AFT](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.AFT.2025.27); [Peer review](https://jolalfissues.substack.com/p/peer-review-unravelling-the-probabilistic)
- **Polymarket analog, executable.** Gebele, Mutzel & Matthes, "Executable Arbitrage and Market Efficiency in Prediction Markets" (arXiv 2608.00666, Aug 1, 2026), separate payoff-implied arbitrage from arbitrage the protocol lets you execute before settlement. Polymarket's NegRisk Adapter supports only the NO→YES conversion. A third-party summary reports about $1.12M total arb profit, about 97% of it from converter-enabled strategies. That figure is unverified and conflicts in scale with Saguillo's $40M, probably because of different definitions and periods. — [arXiv abstract](https://arxiv.org/abs/2608.00666); [Moonlight review](https://www.themoonlight.io/en/review/executable-arbitrage-and-market-efficiency-in-prediction-markets)
- **Polymarket NBA (2026, order-book snapshots).** "Single-market anomalies are exceedingly rare," with only 7 executable in-game episodes. Aggregate capped profit was $559.59 across 290 combinatorial episodes. — [arXiv 2605.00864](https://arxiv.org/html/2605.00864v1); [UCLA PDF](http://www.stat.ucla.edu/~guangcheng/Arbitrage%20Analysis%20Cheng.pdf)
- **Intra-Kalshi cross-event representations.** A Senate four-contract hedge priced at $3.02 vs a $3 payout before fees, with an average 3.3-point spread across representations. — [CryptoSlate](https://cryptoslate.com/kalshis-senate-contracts-can-settle-on-different-answers-to-the-same-election/)
- Kalshi onboarded its first dedicated institutional market maker in April 2024 (older fact). — [BusinessWire, Apr 3, 2024](https://www.businesswire.com/news/home/20240403664852/en/Kalshi-Onboards-Its-First-Dedicated-Institutional-Market-Maker)

### Inferences
- **The worked example fails after fees** (my arithmetic). The taker fee per set on 30/28/24/14 is 0.07 × (0.21 + 0.2016 + 0.1824 + 0.1204) ≈ 5.0¢, or 5.02¢ per set at 100 contracts with per-order rounding. The "4¢ gap" is therefore about −1¢ net.
- **The YES-basket fee wall grows with the number of legs.** For n roughly equal legs, total taker fees are about 0.07 × (1 − 1/n) per set: 3.5¢ (n=2), 4.7¢ (3), 5.25¢ (4), 6.3¢ (10). Skewed fields (one favorite plus tails) have lower walls, but per-order round-up hurts small orders on the tails.
- **The NO basket is the better-structured direction** (my derivation). On Kalshi a NO ask equals 1 − YES bid, so "Σ NO asks < n−1" is the same as "Σ YES bids > 1." The NO basket pays at least n−1 whether or not the set is exhaustive: if nothing resolves YES, it pays n. It needs only mutual exclusivity, not exhaustiveness. With Collateral Return, Kalshi should release most of the guaranteed payout early, so capital lock-up nearly disappears. The exact amount returned is not documented in what I could read. Fees are symmetric: a NO leg at 1−b pays 0.07·b(1−b).
- **Threshold-ladder variant, untested.** Many Kalshi "how many" and level markets are nested thresholds ("above X," "above Y"), not exclusive brackets. If bid(>Y) > ask(>X) for Y > X, buying >X YES and >Y NO costs under $1 and pays at least $1. No source measured this; it is worth logging.
- **Competition is the likely reason scans come up empty.** Institutional market makers quote whole ladders and can net hedged NO collateral. Any Σ-bid > 1 condition is a free option to them, so it should be fleeting, which fits the vendor finding of only thin longshot residues.
- **The Polymarket $40M figure is not evidence for Kalshi today.** It came from a fee-free venue in 2024–25 with a native conversion primitive. Kalshi charges per-leg taker fees and has no conversion, only collateral release.

### Gaps
- No independent dataset of Kalshi bracket sums (Σ YES ask, Σ YES bid) by event type (Fed brackets, CPI, weather ranges, index ranges, "how many" counts), frequency or duration was found. This is the most important missing measurement, and it is measurable from Kalshi data alone.
- Not read: Krause, "Market Efficiency in Prediction Markets: A Multi-Event Analysis of Kalshi Fed Policy Decision Contracts" (SSRN 7442661), which may report bracket-sum deviations. — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7442661). Also Bürgi/Deng/Whelan, "Makers or Takers: The Economics of the Kalshi Prediction Market" (GWU WP 2026-001). — [GWU PDF](https://www2.gwu.edu/~forcpgm/2026-001.pdf)
- Not verified: whether Kalshi offers atomic multi-leg orders or RFQ for baskets. Without them, leg risk remains. Also the exact cash released by Collateral Return, and whether NO-basket positions can be exited early.

## 4. What do open-source arbitrage bots and practitioner write-ups report, and what made them stop working?

### Takeaway
The open-source landscape is large but evidence-poor. Repos advertise "risk-free" cross-venue arbs (often 15-minute or hourly crypto markets) and fuzzy market matching, but none found publishes audited live P&L. Builders who measured carefully report gaps that close in seconds, near-zero real edge after fees, and pivots to selling scanners or APIs. The recurring killers are fees (Polymarket's 2026 fee rollout, including 15-minute crypto taker fees aimed at latency arbitrage), speed competition, stale-quote illusions, resolution mismatches, leg risk and capital fragmentation.

### Cited Findings
- **ImMike/polymarket-arbitrage (Python).** "Watches 10,000+ markets" on and between platforms and describes a cross-platform mode (buy Polymarket, sell Kalshi) as a "6% edge (minus fees)." About 330 days old when indexed. This is a claim, not a result. — [GitHub](https://github.com/ImMike/polymarket-arbitrage)
- **CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot.** Targets hourly BTC price markets on both venues and flags opposing positions with a combined cost below $1.00 as "risk-free." — [GitHub](https://github.com/CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot)
- **defi-ape/polymarket-kalshi-arbitrage-bot and Composio-HQ/polymarket-kalshi-arbitrage-bot.** 15-minute market bots that poll the Kalshi Trade API and the Polymarket CLOB for spreads and "late-resolution gaps." — [defi-ape](https://github.com/defi-ape/polymarket-kalshi-arbitrage-bot); [Composio-HQ wiki](https://github.com/Composio-HQ/polymarket-kalshi-arbitrage-bot/wiki)
- **grzresearch/Polymarket-Kalshi-Arbitrage.** Fuzzy matching across venues, with Kalshi API-key and MetaMask wallet connections. — [GitHub](https://github.com/grzresearch/Polymarket-Kalshi-Arbitrage)
- **realfishsam/prediction-market-arbitrage-bot.** Labeled educational. Uses Jaccard and Levenshtein matching and has a dry-run mode, built on pmxt. The author's dev.to post reports a "2–5% spread" between platforms and warns about being filled on one venue while stuck on the other. — [GitHub](https://github.com/realfishsam/prediction-market-arbitrage-bot); [dev.to](https://dev.to/realfishsam/how-i-built-a-risk-free-arbitrage-bot-for-polymarket-kalshi-4f)
- **nexosdata/polymarket-kalshi-arbitrage-bot.** A scanner and dual-leg execution *simulator*. Its README calls the gap between executing the two legs "the key vulnerability" and includes fee modeling and an unwind safeguard. — [GitHub](https://github.com/nexosdata/polymarket-kalshi-arbitrage-bot)
- **Commercial "bot packs."** Po1yScripts sells 5- and 15-minute "arbitrage bot packs," a commercial pitch. A separate guide warns about bot scams. — [Po1yScripts wiki](https://github.com/Po1yScripts/polymarket-arbitrage-trading-bot-pack-5min-15min-kalshi/wiki); [PredictDesks](https://predictdesks.com/blog/guides/polymarket-trading-bots)
- **Mustopo.** Measured 870 sports gaps per day with a median life of about 9 seconds, found "no sizable arbitrage," and pivoted to selling the matcher API. — [dev.to](https://dev.to/michaelmustopo/built-a-prediction-market-arbitrage-no-sizable-arbitrage-found-36cf)
- **Kothari.** Built a matcher across about 89k open markets. His central lesson is that resolution-rule mismatches turn apparent arbs into losses. — [Kothari](https://www.yashkothari.ca/writing/polymarket-kalshi-arbitrage)
- **Fees as a killer.** PredictMarketCap reports that the minimum viable gap "roughly doubled mid-study after Polymarket's fee rollout." — [PredictMarketCap](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study)
- Polymarket's 15-minute crypto taker fees were framed as preventing latency arbitrage. Commentators say bot edges are "diminished," though some argue well-built bots become more dominant. No post-change P&L data was found. — [Unchained](https://unchainedcrypto.com/polymarket-introduces-taker-fees-in-15-minute-markets/)
- **Skeptical write-ups.** "The Myth of Risk-free Polymarket and Kalshi Hacks As Money Machine." Rajiv Sethi's posts on fee-structure distortions and the limits of arbitrage (not read). — [Medium](https://medium.com/@sipsnscale/the-myth-of-risk-free-polymarket-and-kalshi-hacks-as-money-machine-b487d86ea8ac); [Sethi: fee distortions](https://rajivsethi.substack.com/p/fee-structure-distortions-in-prediction-16-04-10); [Sethi: limits of arbitrage](https://rajivsethi.substack.com/p/the-limits-of-arbitrage)
- Related research seen by title only: "The Ghosts of Polymarket: When Off-Chain Matches Meet On-Chain Reverts" (arXiv 2606.16852), suggesting another execution risk on polymarket.com. Also the Flashbots Collective thread on prediction-market arbitrage strategies. — [arXiv 2606.16852](https://arxiv.org/pdf/2606.16852); [Flashbots Collective](https://collective.flashbots.net/t/arbitrage-in-prediction-markets-strategies-impact-and-open-questions/5198)

### Inferences
- **Survivorship and incentive bias.** The visible ecosystem is dominated by people selling scanners, APIs, VPS hosting or bot packs. The only careful builders found (Mustopo, Kothari, the PredictMarketCap audit) all report that the edge mostly isn't there for retail-grade execution.
- **Many "risk-free" crypto bots pair markets that use different reference prices or timestamps.** Those are basis trades. The repos do not document settlement-source equivalence.
- **What "stopped working," in order of evidence strength:** (1) fees on Polymarket's side, which roughly doubled the hurdle in 2026; (2) speed, with sports gaps living for seconds; (3) stale-quote illusions; (4) resolution mismatch losses; (5) capital fragmentation and lock-up.

### Gaps
- No repo README or issue thread with verified live P&L or a post-mortem was found. Repo contents could not be read directly; descriptions come from search summaries.
- No dated evidence on *when* specific bots stopped being profitable, beyond the fee-change timing.

## 5. Strategy-by-strategy assessment (objective): mechanism, evidence, soundness, what it needs, paper-testability, confidence of a real durable edge after fees

### Takeaway
None of the arbitrage variants shows credible evidence of a durable after-fee edge for a US retail Kalshi trader. The best-supported conclusion is that real gaps (median under 1¢) sit below the fee wall (about 2–3.5¢ cross-venue, 3.5–7¢ for Kalshi YES baskets). Larger gaps are either seconds-long or carry basis or resolution risk. The most worthwhile thing to do is cheap and Kalshi-only: shadow-log intra-event NO-basket (Σ YES bids > 1 + fees) and threshold-ladder violations. This is fully testable on paper and capital-light with Collateral Return. Expect to confirm that market makers already take them.

### Cited Findings
- Real cross-venue median gap 0.78¢; 0 of 12 headline arbs survived freshness; about 3¢ fee wall. — [PredictMarketCap](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study)
- Persistent 2–4% execution-aware deviations, attributed to semantic non-fungibility. — [Gebele & Matthes](https://arxiv.org/abs/2601.01706)
- Clarity Act basis trade: 5.08% → 4.82% after fees → 2.67% after opportunity cost (expected, not riskless). — [Krause SSRN 6984101](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6984101)
- Sports gaps: median life about 9 s, 96% under 30 s. — [Mustopo](https://dev.to/michaelmustopo/built-a-prediction-market-arbitrage-no-sizable-arbitrage-found-36cf). Kalshi vs books up to 8.8% in momentum swings, short-lived, thin liquidity. — [Blockworks](https://app.blockworks.com/report/from-betting-to-trading-how-kalshi-is-reshaping-sports-markets)
- Kalshi intra-event: genuine candidates "thin, longshot, barely positive net of fees." — [BotForKalshi](https://www.botforkalshi.com/blog/kalshi-arbitrage-guide). Collateral Return is available per event. — [Kalshi help](https://help.kalshi.com/en/articles/13823816-collateral-return)
- Polymarket fee-free era: about $40M realized arb, mostly within-market. — [Saguillo et al.](https://suarez-tangil.networks.imdea.org/papers/2025aft-arbitrage.pdf). Now: 7 executable single-market NBA episodes. — [arXiv 2605.00864](https://arxiv.org/html/2605.00864v1)

### Inferences (scorecards; confidence = my judgment that the strategy has a real, durable edge after fees, capital costs and resolution risk for a US-based Kalshi trader with modest capital and retail or VPS latency)

**A. Kalshi ↔ Polymarket US, taker–taker, fast markets (sports, 15-minute or hourly crypto)**
- *What / mechanism.* Buy YES on the cheaper venue and NO on the other when the combined cost plus both taker fees is under $1.
- *Evidence.* Gaps close in seconds; the 2026 fee rollout doubled the hurdle; repos claim "risk-free," with no audited P&L.
- *Soundness.* Sound only if settlement sources and timestamps are identical. Crypto up/down markets on the two venues may reference different price feeds (not verified).
- *Needs.* [+Polymarket US] KYC'd account (not Nevada), pre-funded capital on both venues, APIs on both (Polymarket US API not verified), sub-second automation, leg-risk unwind logic.
- *Paper test.* Poor. Fills inside a 9-second median window cannot be simulated honestly without real latency and queue data, so paper results overstate.
- **Confidence: 5%.**

**B. Kalshi ↔ Polymarket US, slow markets (politics, macro, regulatory), only after a written rules-equivalence audit**
- *Mechanism.* As A, but held to resolution or unwound when the gap closes.
- *Evidence.* Median real gap 0.78¢ vs a 2–3.5¢ fee wall; occasional 5–11¢ gaps lasting up to about 2 hours (1.5% of pairs ≥5¢).
- *Soundness.* Sound only for truly identical contracts, which are rare (about 6% of events are co-listed, fewer of them equivalent).
- *Needs.* [+Polymarket US], capital locked for weeks to months (the Kalshi leg earns about 3.5–4% APY; the PM leg's yield is unknown), API polling at minute-level latency.
- *Paper test.* Moderate. Slow markets make paper fills plausible, but settlement-divergence risk only shows at resolution, giving months-long, small-sample feedback.
- **Confidence: 10%.**

**C. Cross-venue "basis-risk" relative value on persistent gaps (e.g., Clarity Act spreads up to 26 points)**
- *Mechanism.* Bet that two near-equivalent contracts converge, accepting wording and timing risk.
- *Evidence.* Krause: 2.67% expected ROI after opportunity costs; the gaps persist because of segmentation, and Krause predicts they shrink with Polymarket US.
- *Soundness.* Not arbitrage. Positive EV is plausible but depends on rare-event resolution risk.
- *Needs.* [+Polymarket US], long lock-up.
- *Paper test.* Hard to test honestly: there are few independent episodes and the tail risk is unobservable in short samples.
- **Confidence: 15%** as positive-EV and **under 10%** as durable, since convergence pressure should erode it.

**D. Kalshi ↔ US sportsbooks (pre-game or live)**
- *Mechanism.* Take Kalshi's contract against the opposite side at a sportsbook when implied probabilities sum to under 1 after Kalshi fees and book vig.
- *Evidence.* Gaps up to 8.8% in momentum swings, short-lived; Kalshi's NFL vig is now comparable to books (4.32% vs 4.44–4.51%); self-promotional X anecdotes.
- *Soundness.* Arithmetically sound. Practically, books void obvious errors (not researched here) and limit arb accounts.
- *Needs.* [+sportsbook] accounts in a legal state with geolocation, fast execution, and tolerance for being limited. Kalshi sports legality is contested in some states.
- *Paper test.* Price gaps can be logged from odds feeds, but limiting, voids and live-bet delays cannot be simulated, so paper results overstate badly.
- **Confidence: 10%**, possible small edge until accounts are limited, but not durable.

**E. Kalshi ↔ PredictIt**
- *Mechanism.* As B.
- *Evidence.* No measurements found. The 10% profit fee and 5% withdrawal fee mean gaps must exceed about 6–10¢ plus Kalshi fees; the $3,500 per-contract cap limits size.
- *Needs.* [+PredictIt].
- *Paper test.* Easy, with deterministic fees.
- **Confidence: 5%.**

**F. Kalshi intra-event YES basket (Σ YES asks + per-leg fees < $1)**
- *Mechanism.* Buy every outcome of an exhaustive mutually exclusive set.
- *Evidence.* Vendor scans find only thin longshot residues; the worked 4¢ example is −1¢ after fees; the fee wall is 3.5–6.3¢ for 2–10 equal legs.
- *Soundness.* Sound only if the set is exhaustive; partial fills create leg risk.
- *Needs.* [Kalshi-only], capital locked until settlement (no collateral return on YES sets), WebSocket feed for simultaneous snapshots.
- *Paper test.* Good, since it uses single-venue data with deterministic fees. It must use executable asks and depth, per-order fee rounding, and snapshot simultaneity.
- **Confidence: 5%.**

**G. Kalshi intra-event NO basket (Σ YES bids > 1 + fees, i.e., Σ NO asks < n−1), with Collateral Return on**
- *Mechanism.* Buy NO on every outcome. This pays at least n−1 and is robust to non-exhaustive sets.
- *Evidence.* No Kalshi measurement found. The Polymarket analog (negRisk conversion) produced most historical arb profit there, but in a fee-free era.
- *Soundness.* The logic is the most robust of all the variants. Risks: the reported Collateral Return bug, the lock-in of the flag at first order, the inability to sell returned-collateral positions, and leg risk.
- *Needs.* [Kalshi-only], Collateral Return enabled before the first order in the event, fast multi-leg execution.
- *Paper test.* Good, but cannot verify collateral mechanics without small live trades.
- **Confidence: 8%.** Market makers quoting full ladders should arbitrage it first.

**H. Intra-Kalshi cross-event logical arbitrage (combinatorial or nested thresholds: Senate control vs seats, Fed decision vs target level, "above X" vs "above Y" ladders)**
- *Mechanism.* Exploit price inconsistencies between logically linked Kalshi contracts.
- *Evidence.* Senate representations averaged a 3.3-point spread, but the full hedge cost $3.02 vs a $3 payout before fees. Combinatorial arbs are rare even on Polymarket (13 strict pairs; $559.59 total in NBA episodes).
- *Soundness.* Nested-threshold monotonicity is sound and settlement-consistent within one event series. Cross-family pairs (control vs seats) carry settlement-logic risk.
- *Needs.* [Kalshi-only], a rules audit for each pair.
- *Paper test.* Good for threshold ladders; weak for cross-family pairs, where resolution risk only shows at settlement.
- **Confidence: 10%.**

**I. Maker-hybrid variants (rest a bid on one venue or leg, take the hedge when filled)**
- *Mechanism.* Earn the spread and rebates instead of paying two taker fees. Kalshi makers pay zero fees outside listed series. Polymarket US maker rebates start only at $10M+ monthly maker volume.
- *Evidence.* None audited.
- *Soundness.* This is market making with hedging, not arbitrage. Adverse selection means resting legs fill when the hedge price has moved.
- *Needs.* As for the corresponding taker version, plus order-management and cancel latency.
- *Paper test.* Notoriously optimistic. Count only fills where trades print *through* your price, and assume worst-case hedge slippage.
- **Confidence: 15%**, the most plausible source of any real edge, but it competes with institutional market makers.

### Gaps
- Exact current Kalshi maker-fee series list and APY rate, which are only in account or official pages that were blocked here.
- Polymarket US API, settlement process, holding-yield policy and state list, all from secondary sources only.
- A measured Kalshi bracket-sum time series is still missing and is the single most decision-relevant item. Suggested shadow test: from Kalshi WebSocket order-book snapshots, log every event's Σ YES ask, Σ YES bid and threshold-ladder violations. Size by executable depth, apply ceil-per-order fees, and record each violation's duration, to estimate frequency and capturable size before any capital is committed.
