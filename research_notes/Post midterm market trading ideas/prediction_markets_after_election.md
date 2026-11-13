# Prediction markets around and after the 2026-11-03 US midterms: activity, structure, and openings for a small paper-only Kalshi bot

Compiled 2026-11-07. Method caveat: WebFetch could not reach most source hosts in this session (help.kalshi.com, cnbc.com, covers.com, rg.org, news.bitcoin.com and predictionnews.com all failed DNS resolution under the session's network allowlist). Every finding below therefore comes from web-search result summaries of the cited pages, not from reading the full pages, and figures were not checked against full text. Dates in parentheses are publication dates or "as of" dates. "~" marks a date estimated from the search index (for example "about two days old"). No live data was pulled from the Kalshi or Polymarket APIs. Where a CFTC filing date is given, it is inferred from the filing URL's naming pattern (rulesMMDDYY...), not read from the document.

## 1. Volumes, records and price accuracy around the midterms (Kalshi, Polymarket / Polymarket US, others)

### Takeaway
The 2026 midterms were the largest election ever for US-regulated prediction markets. Kalshi reported more than $2.5B in midterm trading (Nov 4, 2026 recap, about double 2024) and about $729M in election contracts on Nov 3 alone. Polymarket US traded about $234M in political markets over the 30 days around the vote. Even so, election flow was small next to Kalshi's roughly $19–21B per week of total volume, most of it sports and 15-minute crypto. Markets called both chambers for Democrats (above 90% for the House before polls closed; the Senate went from about 75% to nearly 100% by 9 p.m. ET on Nov 3) and claimed 94–98% race-level accuracy. Polls and models were slightly more bullish on Democrats than markets on Election Day, and markets had notable misses (the South Carolina Senate race and the Texas governor's race). From Arizona, Kalshi is usable but under active litigation, and reports on whether Polymarket US is available in Arizona conflict.

### Cited Findings
**Kalshi volume**
- Kalshi's Nov 4, 2026 post-election recap cites more than $2.5B in midterm trading volume, against $1.3B for the whole 2024 election cycle (growth of more than 92%). — [crypto.news](https://crypto.news/kalshi-midterm-election-trading-volume-2-5-billion/); [Finwire](https://finwire.io/news/crypto-news/kalshi-tops-25b-in-midterm-trading-nearly-doubling-2024-volume); [KuCoin News](https://www.kucoin.com/news/flash/kalshi-midterm-election-market-volume-surpasses-2-5-billion)
- The recap is company-reported and measures notional volume. It did not disclose total trader profits, losses, individual account results or post-election payouts (reported ~Nov 5, 2026). — [KHOU](https://www.khou.com/article/news/politics/kalshi-2026-election-trading/285-1d5d55ec-d9d1-4e95-a53e-426c84fdf9d4)
- An earlier interim figure, $1.2B+ in midterm trading (already above the 2024 level), has been superseded by the $2.5B recap (date of interim report not captured, pre-Nov 4, 2026). — [Fox News](https://www.foxnews.com/politics/1-billion-midterm-betting-boom-uncovers-surprising-political-divide-across-us-jobs)
- Paradigm co-founder Matt Huang said Kalshi's election contracts traded $729M on Nov 3, 2026, against $244M on the 2024 presidential Election Day (reported ~Nov 4, 2026). — [ChainCatcher](https://www.chaincatcher.com/en/article/2302611)
- Kalshi's platform-wide notional volume on Election Day (Nov 3, 2026) was $4.15B, its biggest weekday yet but below the $5.30B record set in October 2026. That total includes non-election contracts. The five largest election series traded about $440M that day, led by the Texas Senate race, while the 15-minute bitcoin series alone traded $332.6M, more than any single election series. The article's internal dates are inconsistent: it cites both "Nov. 24" and "Nov. 3". — [Bitcoin.com News](https://news.bitcoin.com/igaming/kalshi-election-day-volume-hits-4-15b-short-october-record/)
- Kalshi's "Who will control the U.S. House" market passed $400M in cumulative volume (as of the ~Nov 4, 2026 recap coverage). — [KuCoin News](https://www.kucoin.com/news/flash/kalshi-midterm-election-market-volume-surpasses-2-5-billion); [crypto.news](https://crypto.news/kalshi-midterm-election-trading-volume-2-5-billion/)
- Kalshi users had wagered $33M on Michigan's Senate race (date of report not captured). — [Yahoo Finance](https://finance.yahoo.com/markets/options/articles/kalshi-users-wagered-33-million-171500541.html)
- Kalshi says viewers of its midterm market outnumbered traders 5:1 (~Nov 4, 2026). — [KuCoin News](https://www.kucoin.com/news/flash/kalshi-s-midterm-election-market-attracts-millions-of-viewers-outnumber-traders-5-1)

**Polymarket and Polymarket US volume**
- Polymarket US processed more than $234M in political trading volume over the 30 days to about Nov 5–6, 2026. The largest markets were the US House ($29.5M), the Texas Senate race ($26.1M) and the US Senate ($15.6M). About $110M of that volume (about 47%) came on Nov 3–4. — [The Block on X](https://x.com/TheBlockCo/status/2118436586098467182); [Bloomingbit](https://en.bloomingbit.io/feed/news/123770); [Prediction News](https://predictionnews.com/story/polymarket-trader-up-917k-on-midterm-blue-wave-pending-alaska-outcome)
- A blog post cites about $164M on Polymarket's three national markets (House, Senate, balance of power) and about $67M across 14 Senate race markets (~Nov 5, 2026). These figures are unconfirmed, and it is unclear whether they cover the international venue or the US venue. — [CryptoTicker](https://cryptoticker.io/en/polymarket-midterms-2026-senate-odds/)
- Polymarket's "Balance of Power: 2026 Midterms" event shows about $75.7M in lifetime volume since it opened in July 2025 (as viewed ~Nov 2026). — [Polymarket](https://polymarket.com/event/balance-of-power-2026-midterms)
- On election night, Kalshi traded $127.4M across 11 midterm markets against $30.6M on Polymarket, about 4:1. The window ran from midnight ET Nov 3 to 6 a.m. ET Nov 4, 2026, and the two venues' windows were not identical. Polymarket called the House first (~Nov 4–5, 2026). — [Gaming America](https://gamingamerica.com/news/1109871/kalshi-polymarket-midterms-night-volume-house-senate)
- DeFi Rate's headline reports that Polymarket US "triples fall trade volume" in the same report that logged Kalshi's record $19B week (Oct 5–11, 2026). — [DeFi Rate](https://defirate.com/news/kalshi-hits-record-19-billion-week-as-polymarket-us-triples-fall-trade-volume/)

**Other venues and market-wide totals**
- A CNN count cited by Trefis (Nov 2, 2026) put total midterm trading across US platforms at about $1.4B as of about Oct 23, 2026: about $1.1B on Kalshi and about $340M on Polymarket. The same piece cites about $104M across Kalshi, Polymarket US, ForecastEx and Gemini between Oct 1 and 20, up from about $41M over the same days in September. That figure's scope must be narrower than total midterm trading, because it is inconsistent with the $1.1B Kalshi total. Volume is counted at $1 per contract. — [Trefis](https://www.trefis.com/stock/hood/articles/621993/what-s-happening-with-prediction-markets/2026-11-02)
- Robinhood's midterm pages list about 19.2M contracts traded on the 2026 House party-winner market, about 9.0M on the Senate party-winner market and about 4.9M on a Balance of Power market (page ~Nov 3, 2026). These are contract counts, not dollars. — [Robinhood](https://robinhood.com/us/en/prediction-markets/midterms/control-of-congress/)
- Robinhood's prediction-market revenue rose more than sixfold year over year to $173M in Q3 2026 (Nov 6, 2026). — [Motley Fool](https://www.fool.com/investing/2026/11/06/robinhood-made-million-prediction-markets-stock/)
- Bloomberg's Election Day headline: "Midterm Election Trading on Kalshi and Polymarket Lags Prediction Market Boom" (Nov 3, 2026). — [Bloomberg](https://www.bloomberg.com/news/articles/2026-11-03/midterm-election-trading-on-kalshi-and-polymarket-lags-prediction-market-boom)

**Election volume in the context of total flow**
- Kalshi booked a record $21.5B in volume for the week ending Oct 18, 2026, per Artemis data. It was the 10th straight weekly record, and trades passed 100M for the first time. Combos (mostly sports parlays) were about 67.2% of that week, about $14.35B (published ~Oct 20, 2026). — [Cryptopolitan](https://www.cryptopolitan.com/kalshi-weekly-trading-volume-record-trades/)
- DeFi Rate counts by a different method (contracts at $1 face value). It recorded $19.03B for Oct 5–11, 2026 and $18.37B for Sept 28–Oct 4, 2026; in the latter week the crypto category was $2.42B. — [DeFi Rate (Oct 5–11)](https://defirate.com/news/kalshi-hits-record-19-billion-week-as-polymarket-us-triples-fall-trade-volume/); [DeFi Rate (Sept 28–Oct 4)](https://defirate.com/news/sept-28-oct-4-2026-volume-report/)

**Accuracy against results and polls**
- Kalshi and Polymarket both priced Democrats above 90% to take the House before the first polls closed, and Democrats won both chambers. Kalshi claims 95% accuracy on House races and 94% on Senate races. Polymarket claims 98.4% of resolved races, measured against prices on the day before the election. The figures are self-reported and use different methods (~Nov 4–5, 2026). — [The Hill](https://thehill.com/policy/sports-gaming/6199204-prediction-markets-midterm-accuracy/); [CNBC](https://www.cnbc.com/2026/11/04/prediction-markets-2026-midterms-election-results.html)
- Misses: markets did not have Democrats winning the South Carolina Senate race, traders did not see Democrat Gina Hinojosa winning the Texas governor's race, and Iowa's Senate race was priced near 50-50 (Nov 5–6, 2026). — [The Hill](https://thehill.com/policy/sports-gaming/6199204-prediction-markets-midterm-accuracy/); [Reason](https://reason.com/2026/11/06/prediction-markets-called-the-midterms-lawmakers-still-call-them-gambling/)
- Markets compared with poll-based models before the vote: the Senate gap between three markets (Kalshi, Polymarket, PredictIt) and two poll-based models (Nate Silver's and Harvard's ElectIt) averaged about 7.3 points from Sept 1, 2026 and narrowed to 2.9 points on the morning of Nov 3. The House gap averaged under 1 point. — [Yahoo Finance](https://finance.yahoo.com/economy/article/prediction-markets-vs-polls-election-forecasting-industry-faces-midterm-test-100000463.html)
- An Election Day snapshot put markets at 94% for a Democratic flip of "the chamber" against 96.2% from poll-based models, so polls were slightly more bullish on Democrats at that moment. The snippet did not name the chamber; the 94% matches House pricing. — [Yahoo Finance](https://finance.yahoo.com/economy/article/prediction-markets-vs-polls-election-forecasting-industry-faces-midterm-test-100000463.html)
- Right before the vote (Nov 4, 2026 coverage), Kalshi had the Democratic House at 93% and the Democratic Senate at 75%, against Polymarket's 94.5% and 75.5%. — [SportsBettingDime](https://www.sportsbettingdime.com/news/politics/kalshi-polymarket-election-odds-comparison/); [Newscord](https://newscord.org/article/kalshi-and-polymarket-price-democrats-favored-in-us-midterms-house-at-94--Story_20261104_USmidtermsPrediction8d2c8529)
- Democratic Senate control rose to 89% on Kalshi and 90% on Polymarket by 7 p.m. ET on election night (Nov 3, 2026). — [Covers](https://www.covers.com/politics/2026-midterm-prediction-market-odds-tracker)
- Reuters: by 9 p.m. ET Nov 3 (0200 GMT Nov 4), markets priced a Democratic takeover of both chambers close to 100%. Reuters also noted that academic work finds markets well calibrated overall. — [Yahoo Finance / Reuters](https://finance.yahoo.com/news/prediction-markets-face-us-midterms-110151053.html)
- A forecast-scoring write-up found that Polymarket scored slightly better than Kalshi on both chambers, by about one point (~Nov 5–6, 2026). — [First Sigma (Substack)](https://firstsigma.substack.com/p/midterm-elections-forecast-comparison-analysis)
- The Hill, citing The Atlantic, reports that polls undercounted Democrats this cycle (~Nov 6, 2026). I could not confirm from the snippet which Hill article carries this. — [The Hill](https://thehill.com/newsletters/whole-hog-politics/6202759-gop-midterm-defeat-trumpism)

**Access for an Arizona resident**
- Arizona's Attorney General filed a 20-count criminal case against Kalshi on Mar 17, 2026, the first state criminal case against a prediction market. — [NPR](https://www.npr.org/2026/03/17/nx-s1-5751165/kalshi-criminal-charges-arizona); [US News](https://www.usnews.com/news/us/articles/2026-03-17/arizona-hits-kalshi-with-criminal-charges-escalating-fight-between-states-and-prediction-markets)
- The CFTC sued Arizona on Apr 2, 2026. A federal judge halted the state case on Apr 10, 2026, and Judge Michael Liburdi later blocked the prosecution permanently (May 5, 2026). — [Arizona Mirror](https://azmirror.com/2026/05/05/arizonas-criminal-case-against-kalshi-permanently-blocked-by-federal-judge/)
- On Aug 28, 2026 a Ninth Circuit panel ruled in a Nevada case that sports event contracts are not "swaps" under the Commodity Exchange Act. That could revive Arizona's prosecution, but the panel remanded the election-wagering question to the district court, so Arizona's election-betting charge is the weaker part of its case. The ruling creates a split with the Third Circuit, which sided with Kalshi. — [Arizona Mirror](https://azmirror.com/2026/08/28/9th-circuit-sides-with-states-in-kalshi-gambling-fight-potentially-reviving-arizonas-prosecution/); [Axios Phoenix](https://www.axios.com/local/phoenix/2026/08/28/ninth-circuit-kalshi-nevada-online-sports-betting-arizona-kris-mayes)
- Kalshi has sought en banc rehearing, which pauses the panel ruling's mandate. The CFTC argued that lifting Liburdi's injunction now would be a "gamble". AG Mayes was pushing to revive the case as of Sept 25, 2026. — [Arizona Mirror](https://azmirror.com/2026/09/25/after-9th-circuit-ruling-mayes-pushes-to-revive-her-gambling-case-against-kalshi/); [InGame](https://www.ingame.com/ninth-circuit-states-plan-predictions-stopped/)
- Fox Sports' October 2026 state tracker lists Arizona as "Contested" but says prediction markets remain available there. — [Fox Sports](https://www.foxsports.com/stories/betting/prediction-markets-legal-states)
- Polymarket US access in Arizona conflicts by source. One guide says Polymarket US told it in writing on Oct 23, 2026 that it is available in every state except Nevada. An August 2026 check listed Arizona among blocked states (with Illinois, Massachusetts, Maryland, Michigan, Montana, Nevada and Ohio). The international Polymarket site blocks US users. — [PredictionMarketsPicks](https://predictionmarketspicks.com/learn/is-polymarket-legal-in-arizona); [Sharp Football Analysis (Nov 2026 review)](https://www.sharpfootballanalysis.com/prediction-markets/polymarket/); [StartPolymarket](https://startpolymarket.com/countries/united-states/)

### Inferences
- Election contracts brought a one-day surge ($729M on Nov 3) and are now winding down as races settle. A bot trading after the election is working in thinner political books than election night. Remaining depth is concentrated in the House and Senate control markets, which are near 100% or settling, and in a few marquee races.
- Polymarket called the House before Kalshi on election night despite a quarter of Kalshi's volume. That suggests a lead-lag relationship worth monitoring on future event nights (Polymarket US as the leading signal for Kalshi quotes). This is a single observation, not a tested edge.
- Calibration evidence is mostly self-reported. For model building, the independent comparisons (Yahoo's market-versus-model gap series and the First Sigma scoring) are more useful than the 94–98% accuracy claims. Those claims are dominated by uncompetitive races.
- For an Arizona resident, a paper-only bot that reads public market data carries little legal exposure. Moving to live trading would depend on the Ninth Circuit en banc and district-court outcomes, which could change access to Kalshi (sports contracts first) on short notice.

### Gaps
- Polymarket international (non-US) total midterm volume was not reliably found. The $164M and $67M figures are from a single unverified blog.
- No dollar volumes were found for ForecastEx (Interactive Brokers), Gemini, Crypto.com, PredictIt or Robinhood (contract counts only), and Arizona availability for those venues was not checked.
- The exact date of Kalshi's $5.30B October record day was not captured.
- No independent, race-level calibration study comparing markets with polls was found. Only chamber-level comparisons and company claims were available as of Nov 7, 2026.
- Full-page verification was not possible because fetches of the source hosts failed (see the method caveat at the top).

## 2. New or newly busy political and economic markets after the election

### Takeaway
Post-election attention has moved to the following markets:
- **Impeachment:** Kalshi's broad "impeached" contract was at 76.6% on Nov 4 and Polymarket's at about 80% on Nov 6.
- **Cabinet departures:** Hegseth's exit was at 57%.
- **The Dec 12, 2026 shutdown contract:** about 31–36%.
- **The Dec 9, 2026 FOMC:** a 25bp hike was priced at about 77–79%.
- **2028 nomination markets:** Ossoff at about 24–25% for the Democrats and Vance at about 31% for the GOP.
- **Approval-rating brackets:** these resolve on the RCP average.
- **The uncalled Mississippi and Alaska Senate races:** these carry recount and ranked-choice voting risk.

I found no current tariff market data.

### Cited Findings
**Impeachment and removal**
- Kalshi's "Trump impeached" contract rose from 70% before Election Day to 76.6% on Nov 4, 2026. Its "impeached and removed" contract rose from 22.3% to 28.3%. — [Kalshi News](https://news.kalshi.com/p/trump-impeachment-odds-climb-to-76-after-democratic-midterm-victories)
- Before the midterms, the Kalshi impeachment contract was at 61% (pre-Nov 3, 2026). — [Kalshi News](https://news.kalshi.com/p/trump-impeachment-odds-rises-ahead-of-midterms)
- Polymarket's impeachment contract moved from about 63.6% before Nov 3 to 80% by Nov 6, 2026. Removal requires a two-thirds Senate vote. — [Oddspedia](https://oddspedia.com/insights/features/trump-impeachment-odds)
- Kalshi's KXIMPEACH page shows dated term-structure contracts: House impeachment before Jul 1, 2027 at about 37% and before Oct 1, 2027 at about 46% (page date unclear, ~early Nov 2026). — [Kalshi market page](https://kalshi.com/markets/kximpeach/president-impeached/kximpeach)

**Cabinet departures**
- Kalshi's odds of Defense Secretary Hegseth leaving the cabinet hit 57% after the midterms (~Nov 4–5, 2026). — [Kalshi News](https://news.kalshi.com/p/hegseth-exit-impeachment-odds-jump-after-democratic-election-victories)
- Fortune reports bettors turning to markets on which Trump officials could leave first (Nov 6, 2026). — [Fortune](https://fortune.com/2026/11/06/prediction-markets-election-night-now-bettors-trump-officials-leave/)

**2028 nominations and presidency**
- Kalshi's Democratic nominee market (KXPRESNOMD-28): Jon Ossoff about 25%, Alexandria Ocasio-Cortez about 14%, Gavin Newsom about 13% (~Nov 5–6, 2026). — [Kalshi market page](https://kalshi.com/markets/kxpresnomd/democratic-primary-winner/kxpresnomd-28); [Federal News Network](https://federalnewsnetwork.com/prediction-markets/2026/11/democratic-nominee-odds-after-midterm-elections-prediction-markets-politics/)
- Polymarket: Ossoff about 24% for the Democratic nomination and Ocasio-Cortez about 15%. For the 2028 presidency itself, Ossoff leads at 18%, ahead of Vance at 15% and Ocasio-Cortez at 13% (~Nov 5–6, 2026). — [Covers](https://www.covers.com/politics/us-election-betting-odds); [Newsweek](https://www.newsweek.com/presidential-power-ranking-2028-frontrunners-assessed-midterms-12661279)
- On Kalshi, Vance's GOP nomination odds fell 7 points the morning after the midterms. He still leads that market at 31%, ahead of Rubio at 22% and DeSantis at 18% (~Nov 4–5, 2026). The search summary did not say which of these outlets carries the 31/22/18 split. — [The Daily Beast](https://www.thedailybeast.com/knives-out-for-jd-vance-as-his-2028-chances-tank-after-midterms); [Newsweek](https://www.newsweek.com/presidential-power-ranking-2028-frontrunners-assessed-midterms-12661279)
- Ossoff has said he has "zero interest" in a presidential run (as reported ~Nov 2026). The snippet did not say which of the 2028 pieces carries this quote. — [Covers](https://www.covers.com/politics/us-election-betting-odds); [Federal News Network](https://federalnewsnetwork.com/prediction-markets/2026/11/democratic-nominee-odds-after-midterm-elections-prediction-markets-politics/)

**Government shutdown (Dec 12, 2026)**
- Current federal funding runs through Dec 11, 2026, so Dec 12 is the first possible lapse. Kalshi's KXGOVTSHUTDOWN-26DEC12 contract settles on the OMB/OPM operating-status page, observed at 10 a.m. ET on Dec 12, 2026. — [Kalshi market page](https://kalshi.com/markets/kxgovtshutdown/will-the-government-shut-down/kxgovtshutdown-26dec12); [DeFi Rate](https://defirate.com/odds/government-shutdown/)
- Kalshi showed about 31% (~Nov 5, 2026), and another listing showed an implied 35.5–36%. — [Kalshi market page](https://kalshi.com/markets/kxgovtshutdown/will-the-government-shut-down/kxgovtshutdown-26dec12); [Prediction.com](https://prediction.com/odds/government-shutdown-on-dec-12-2026/53023)
- The contract was at about 33% on Oct 19, 2026. — [PredictionNerd](https://predictionnerd.com/government-shutdown-odds/)
- One tracker shows 31% on Kalshi against 32% on Polymarket US (~early Nov 2026). — [PredictionMarketsPicks shutdown tracker](https://predictionmarketspicks.com/tools/shutdown-tracker)
- Kalshi's earlier October shutdown contract peaked at 35% in late July 2026 and resolved No. Lines.com's headline cites a December risk of 24% at an earlier date (not captured). — [Lines.com](https://www.lines.com/kalshi-shutdown-odds-resolve-no-december-risk-at-24)

**Fed (Dec 9, 2026 FOMC)**
- Kalshi's Fed odds page puts a 25bp hike at the Dec 9, 2026 meeting at 77% (~Nov 6–7, 2026). — [Kalshi Fed odds](https://kalshi.com/fed-rate-odds); [Kalshi KXFEDDECISION-26DEC](https://kalshi.com/markets/kxfeddecision/fed-meeting/kxfeddecision-26dec)
- A Nov 6, 2026 analysis had Kalshi's hike contract at 78–79¢, hold at 21–22¢ and cut at 1–2¢, against Polymarket at 76.5% for a hike. Kalshi was at 73% on Nov 2. — [PredictionMarketsPicks Fed tracker](https://predictionmarketspicks.com/tools/fed-rate-tracker/december-2026); [Win Daily Sports](https://windailysports.com/fed-rate-decision-odds-december-2026/)
- Hike odds rose to 77% after the jobs report (~Nov 6, 2026). — [Rio Times](https://riotimesonline.com/fed-december-hike-odds-rise-after-jobs-report-2026)
- The Fed held at its Oct 28, 2026 meeting. A December hike would take the range to 4.00–4.25%. Upcoming catalysts are the Nov 10 inflation report, the October minutes on Nov 18 and the November jobs report on Dec 4, 2026. — [PredictionMarketsPicks Fed tracker](https://predictionmarketspicks.com/tools/fed-rate-tracker/december-2026); [24/7 Wall St. (Nov 6, 2026)](https://247wallst.com/investing/2026/11/06/rate-hikes-could-be-coming-history-likes-these-4-consumer-staples-stocks)
- Kalshi also lists a "fed funds rate after December meeting" ladder (KXFED-26DEC), and a comparison piece explains why Kalshi, Polymarket and CME futures odds differ. — [Kalshi KXFED-26DEC](https://kalshi.com/markets/kxfed/fed-funds-rate/kxfed-26dec); [PredictionMarketsPicks](https://predictionmarketspicks.com/articles/fed-odds-kalshi-vs-polymarket-vs-cme-futures-why-they-differ)

**Approval ratings**
- A Trump approval market resolving on the RealClearPolling average at 5 p.m. ET on Nov 6, 2026 had its leading bracket (39.0–39.4) at 66%. — [Lines.com](https://www.lines.com/prediction-markets/politics/trump/trump-approval-rating-on-november-6)
- Poll averages: Poliwave had 39.6% approve and 58.4% disapprove as of Nov 2, 2026. Nate Silver's average had 37/60 (~early Nov 2026). — [Poliwave](https://www.poliwave.com/us/approval/donald-trump); [Covers](https://www.covers.com/politics/trump-2026-midterm-odds-prediction-markets-approval)
- Polymarket's "how high will Trump's approval go in 2026" page was stale, last updated about 142 days before the search (~mid-2026). — [Polymarket](https://polymarket.com/event/how-high-will-trumps-approval-rating-go-in-2026)

**Uncalled races, recounts and Senate seat count**
- Mississippi Senate: Democrat Scott Colom led Sen. Cindy Hyde-Smith. Mississippi Today (Nov 4, 2026) described a lead of a few dozen votes; later coverage cites AP figures of about 2,000 votes with over 95% counted (~Nov 5–6, 2026). Mississippi has no statutory recount provisions; a challenger would need a court order, and any fight would run county by county across 82 counties. — [Mississippi Today](https://mississippitoday.org/2026/11/04/which-senate-and-governors-races-are-still-uncalled-by-the-associated-press/); [Dissenter](https://dissenter.com/elections/lawyers-fundraisers-swarm-uncalled-mississippi-alaska-senate-races)
- Betting markets had Colom near 94% as of the afternoon of Nov 4, 2026. — [Forbes](https://www.forbes.com/sites/antoniopequenoiv/2026/11/04/democrats-odds-of-winning-mississippi-near-94-in-betting-markets/)
- Alaska Senate: Mary Peltola led Sen. Dan Sullivan by 626 votes with about 74% counted. The race goes to ranked-choice tabulation if no one passes 50% (~Nov 5–6, 2026). — [Dissenter](https://dissenter.com/elections/lawyers-fundraisers-swarm-uncalled-mississippi-alaska-senate-races)
- Both major markets had Peltola at about 97–98% on the morning of Friday Nov 6, 2026. That is per an opinion Substack. — [Michael D. Sellers (Substack)](https://michaeldsellers.substack.com/p/mississippi-alaska-senate-races-a)
- Both party Senate committees (NRSC and DSCC) have set up recount funds (~Nov 5–6, 2026). — [Dissenter](https://dissenter.com/elections/lawyers-fundraisers-swarm-uncalled-mississippi-alaska-senate-races)
- Kalshi's Senate-control page showed Democrats at 100% on Nov 6, 2026, but did not state that the contract had formally settled. Kalshi traders had predicted Democrats would hold 52 seats. — [Kalshi Senate market](https://kalshi.com/markets/controls/senate-winner); [Kalshi News](https://news.kalshi.com/p/kalshi-traders-predict-democrats-will-hold-52-senate-seats-after-the-midterms)

**Tariffs**
- Only polling, not market data, was found: 35% approve and 58% oppose Trump's tariff policy (April 2026). — [US Polling Data](https://uspollingdata.com/polls/trump-tariffs-polling/)

### Inferences
- Impeachment markets offer term-structure consistency checks. For example, P(impeached before Jul 1, 2027) ≤ P(before Oct 1, 2027) ≤ P(broad "impeached" contract). Kalshi's 37% / 46% / 76.6% ladder is internally consistent, but a bot can watch for violations and for cross-venue differences such as Kalshi 76.6% (Nov 4) against Polymarket 80% (Nov 6). Contract wording and deadlines differ across venues, so these are not clean arbitrage. Constitutionally the new House is not seated until Jan 3, 2027, so near-dated impeachment contracts depend on the timing of the 120th Congress.
- The Dec 12 shutdown and Dec 9 FOMC contracts are the cleanest near-dated, well-specified binaries:
  - **Shutdown:** settles on a single observable source at a fixed time, and lame-duck CR news is the catalyst.
  - **FOMC:** has scheduled catalysts (Nov 10, Nov 18, Dec 4) and an external benchmark (CME fed funds futures), which suits a paper model that compares Kalshi prices with futures-implied odds.
- The 2028 nomination markets are long-dated with small edges, and capital would be locked for about 18–20 months, so they mainly serve as a sentiment or news-reaction feed. The 7-point drop in Vance's odds the morning after the election is the kind of overnight repricing a news-driven bot would target.
- The uncalled Mississippi and Alaska races carry resolution risk (no recount law in Mississippi, ranked-choice tabulation in Alaska). Prices of 94–98% leave little upside against tail risk unless the bot has a better read on the count.

### Gaps
- No Kalshi or Polymarket tariff markets (for example tariff rates or Section 232/122 actions) were found with current prices as of Nov 7, 2026.
- No volume figures were found for any post-election political market (impeachment, cabinet, 2028, shutdown, Fed). Only prices were available.
- No markets on control of Congress after special elections, or on a House speaker or leadership contest, were found in these searches.
- The current Mississippi and Alaska vote counts and the official ranked-choice tabulation date for Alaska were not confirmed.
- I could not confirm whether Kalshi's House and Senate control markets have formally settled.

## 3. How Kalshi's liquidity incentive programs work as of November 2026

### Takeaway
Kalshi's Liquidity Incentive Program (LIP) pays a separate pool for each market. The help center gives $1–$1,000 per market per day. Each participant's share is proportional to a per-second score of their resting orders, weighted by size and by a discount for distance from the best price (Discount Factor^ticks), within a depth window set by a per-program Target Size of 100–20,000 contracts. The separate Volume Incentive Program ends no earlier than Oct 13, 2026 under a Sept 28 filing, amid wash-trading scrutiny, so maker-side liquidity rewards are now the main incentive for a bot. I could not confirm which markets carry programs today or whether any were added for post-election markets. That has to be pulled from the Rewards page or the Trade API. A paper-only bot cannot earn rewards; it can only simulate them.

### Cited Findings
**How the LIP scores and pays**
- Each program has its own market, start and end time, reward pool, Target Size and Discount Factor. Rewards are rounded down to the nearest cent, and a final reward under $1 for an individual program is not paid. — [Kalshi Help Center: Liquidity Incentive Program](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program)
- Kalshi scores resting orders by size and closeness to the best prices, taking snapshots every second during trading hours. Participants earn a share of the reward pool based on their liquidity contribution, and an order can score without being filled. — [Kalshi Help Center](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program); [Fifty Cent Dollars (Substack)](https://fiftycentdollars.substack.com/p/kalshis-new-liquidity-incentives)
- The help center describes daily rewards of $1–$1,000 per market per day. A third-party summary gives the same range with a $1.00 minimum payout. — [Kalshi Help Center](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program); [0xInsider](https://0xinsider.com/learn/liquidity-rewards)
- The amount paid for a program can be less than the full displayed pool, depending on how the program's qualification conditions were met during the period. — [Kalshi Help Center](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program)
- Kalshi's CFTC self-certification filings for the LIP set out the formal rule text:
  - Target Size must be between 100 and 20,000 contracts.
  - The Discount Factor is capped at 1.00 (no distance penalty at 1.00, steeper as it falls).
  - A Reference Price is found by walking down from the best bid until cumulative resting size reaches a threshold tied to Target Size. The search summary says one-fifth of Target Size, which I could not verify.
  - Each qualifying order scores Discount Factor^N × size, where N is the number of ticks from the reference price, and scores are normalized across qualifying orders on each side (yes bids and no bids).
  - Snapshots without the required depth may be excluded.

  The summary did not say which filing holds which clause. — [CFTC filing (~Sep 15, 2026)](https://www.cftc.gov/filings/orgrules/rules09152625924.pdf); [CFTC filing (~Oct 14, 2026)](https://www.cftc.gov/filings/orgrules/rules10142633813.pdf); [CFTC filing (~Jul 15, 2026)](https://www.cftc.gov/filings/orgrules/rules07152610358.pdf); [CFTC filing (~Feb 11, 2026)](https://www.cftc.gov/sites/default/files/filings/orgrules/26/02/rules02112639183.pdf)
- Estimates appear on market pages (a rewards badge and popover), and the Rewards page at kalshi.com/incentives separates paid rewards from pending estimates. Estimates change as the book and remaining time change, and only a paid credit is final. — [Kalshi Help Center: where to find rewards and incentive info](https://help.kalshi.com/en/articles/16076644-where-to-find-rewards-and-incentive-info)
- Program definitions are available through the public Trade API. An `IncentiveProgram` model appears in the kalshi-typescript SDK docs (v3.11.0). — [Kalshi Help Center](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program); [kalshi-typescript docs (jsDelivr)](https://cdn.jsdelivr.net/npm/kalshi-typescript@3.11.0/docs/IncentiveProgram.md)
- Kalshi says its programs pay makers to keep bids and offers of a set size within defined spreads, as part of its response to wash-trading claims (~Sept 2026). — [Crypto Briefing](https://cryptobriefing.com/kalshi-wash-trading-claims-response/)

**Program dates and filings**
- Program windows conflict by source. One third-party source gives Sept 15, 2025 through Jan 1, 2027; an older one gives a Sept 1, 2026 end date. An amended filing reportedly bars any Incentive Period from extending past a Dec 1, 2027 termination date. — [0xInsider](https://0xinsider.com/learn/liquidity-rewards); [AlphaScope](https://www.alphascope.app/blog/kalshi-liquidity-rewards); [CFTC filing (~Oct 14, 2026)](https://www.cftc.gov/filings/orgrules/rules10142633807.pdf); [CFTC filing (~Oct 18, 2026)](https://www.cftc.gov/filings/orgrules/rules10182634499.pdf)
- A Kalshi-related CFTC rule filing whose URL implies Nov 3, 2026 appears in incentive-program search results, but its contents were not verified. — [CFTC filing (~Nov 3, 2026)](https://www.cftc.gov/filings/orgrules/rules11032642173.pdf)

**Volume Incentive Program termination (Sept–Oct 2026)**
- Under a Sept 28, 2026 filing, Kalshi told the CFTC it will end its Volume Incentive Program no earlier than Oct 13, 2026, moving the end date up from Oct 1, 2027. — [Gambling.com](https://www.gambling.com/us/news/kalshi-end-volume-incentive-program-october-13); [Legal Sports Report](https://www.legalsportsreport.com/279648/volume-rewards-program-on-kalshi-set-to-end-nearly-a-year-early/); [SBC Americas (Oct 2, 2026)](https://sbcamericas.com/2026/10/02/kalshi-end-volume-rewards-scrutiny/)
- Coverage ties the move to scrutiny of about $5B in near-identical ether trades, but the filing states no reason. Kalshi rejected the wash-trading claims in a Sept 22, 2026 blog post. A CFTC staff advisory in August 2026 warned that incentive programs could heighten wash-trading risk. The CFTC did not find a violation or order the program shut. Kalshi filed a separate Deposit and Trading Reward Incentive Program on Sept 25, 2026 (placed under 10-day review), and perpetual-futures incentives remain. — [DeFi Rate](https://defirate.com/news/kalshi-volume-rewards-cftc-scrutinizes-prediction-markets/); [crypto.news](https://crypto.news/kalshi-to-end-volume-rewards-amid-5b-trade-scrutiny/); [edgeX News](https://pro.edgex.exchange/en-US/news/article/kalshi-ends-volume-incentive-program-cftc-review)
- Naming conflict: The Block's Sept 30, 2026 headline says Kalshi will end its "liquidity incentive program". Most other outlets, and Kalshi's help center, indicate that only the volume program is ending and the LIP continues. — [The Block](https://theblock.co/news/business/2026-09-30-kalshi-ends-trader-incentive-program-417247); contradicted by [Gambling.com](https://www.gambling.com/us/news/kalshi-end-volume-incentive-program-october-13) and [Kalshi Help Center](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program)

**Other Kalshi programs**
- Kalshi also runs a Combo Incentive Program and a Liquidity Provider Program. Designated Liquidity Providers must sign a Market Maker Agreement. There is also a separate LIP for the component legs of sports prop combo markets, which shows programs extend into sports and combos. — [Kalshi Help Center: Combo Incentive Program](https://help.kalshi.com/en/articles/15410257-combo-incentive-program); [Kalshi Help Center: Liquidity Provider Program](https://help.kalshi.com/en/articles/15410219-liquidity-provider-program); [Kalshi Help Center: Sports prop combo legs LIP](https://help.kalshi.com/en/articles/17184676-sports-prop-combo-market-component-legs-liquidity-incentive-program)

**Practitioner commentary**
- A former Kalshi Trading (Kalshi's internal market maker) trader argued, before the LIP went live, that pro-rata liquidity rewards could create "garage-band market makers". The author's illustration of about $5M a month in incentive spending is hypothetical, not a reported budget. — [Fifty Cent Dollars (Substack)](https://fiftycentdollars.substack.com/p/kalshis-new-liquidity-incentives)
- Third-party calculators exist for estimating LIP rewards. — [AlphaScope Kalshi Liquidity Rewards Calculator](https://www.alphascope.app/tools/kalshi-liquidity-rewards-calculator)
- A non-Kalshi Medium post claims $24,000 per game on Champions League quarterfinals. That conflicts with the $1,000-per-market-per-day range and is unreliable. — [Medium](https://medium.com/mountain-movers/turning-polymarket-and-kalshi-into-a-500-monthly-side-income-to-fund-claude-max-perplexity-max-474ab67244d5)

### Inferences
- Rewards can only be simulated, because a paper bot posts no real orders. A realistic simulation would:
  1. Pull program definitions (market, pool, Target Size, Discount Factor, dates) from the Trade API.
  2. Snapshot both sides of the public order book every second.
  3. Compute the bot's hypothetical orders' score share against the rest of the book.
  4. Subtract simulated adverse-selection losses on fills.
- Pools are capped at about $1,000 per market per day and split pro rata, with a $1 minimum per program and round-down to the cent. A small bot spread across many programs could earn nothing in each, so concentrating on a few low-Target-Size programs where its quotes can be a meaningful share of depth makes more sense. For example, at a 100–500 contract target near 50¢, $50–$250 per side of resting collateral is enough to qualify.
- With the volume program ended (Oct 13, 2026 or later), strategies that relied on volume rebates no longer have them. The LIP rewards passive quoting, which is exactly what gets picked off on result nights, settlement calls and Fed or shutdown headlines. Simulated returns should net out adverse selection, especially in politically event-driven markets.
- Kalshi's incentive spend appears to lean toward sports and combos (dedicated programs for prop-combo legs, a Combo Incentive Program). Post-election political markets may carry few or small programs, but this is unverified.

### Gaps
- I could not determine which markets currently carry LIP programs, current pool sizes for political or economic markets, or whether programs were added for post-election markets (impeachment, shutdown, Fed, 2028). These require the Kalshi Rewards page or the Trade API, neither of which was reachable in this session.
- The exact current scoring formula (the reference-price threshold and the depth-qualification rule) could not be verified against the filing text because cftc.gov PDFs were not opened.
- No reporting on actual earnings of unaffiliated small makers under the LIP was found.
- The exact Trade API endpoint path and field names for incentive programs were not verified.

## 4. Cross-venue price gaps (Kalshi vs Polymarket US vs others), fees, and resolution or settlement issues

### Takeaway
Documented cross-venue gaps on headline midterm markets were small:
- **Chamber control:** about 0.5–1.5 points (Kalshi House 93% against Polymarket 94.5%; Senate 75% against 75.5%).
- **Nevada governor:** about 3 points.
- **Post-election markets:** about 1–3 points (Fed hike 78–79¢ on Kalshi against 76.5% on Polymarket on Nov 6; shutdown 31% against 32%).

An independent six-month audit found a median real gap of 0.8¢, every headline "arbitrage" above 8¢ was a stale quote, and combined taker fees of about 3–3.5¢ near 50¢ wipe out most gaps. I found no formal UMA or Kalshi settlement dispute on a November 2026 midterm contract as of Nov 7. The live settlement risks are:
- the uncalled Mississippi and Alaska races;
- payout delays from recounts and legal challenges;
- wording mismatches (an Alaska Senate rules-versus-title complaint was raised in September 2026);
- Polymarket's investigation of dozens of suspicious midterm bets.

### Cited Findings
**Documented price differences**
- Around Nov 3–4, 2026, Kalshi priced Democratic House control at 93% and Senate control at 75%, against Polymarket's 94.5% and 75.5%. A comparison found a 3% gap between the two venues on the Nevada governor's race. — [SportsBettingDime](https://www.sportsbettingdime.com/news/politics/kalshi-polymarket-election-odds-comparison/); [Newscord (Nov 4, 2026)](https://newscord.org/article/kalshi-and-polymarket-price-democrats-favored-in-us-midterms-house-at-94--Story_20261104_USmidtermsPrediction8d2c8529)
- On election night, Senate control was 89% on Kalshi against 90% on Polymarket at 7 p.m. ET (Nov 3, 2026). — [Covers](https://www.covers.com/politics/2026-midterm-prediction-market-odds-tracker)
- Polymarket called the House first, even though Kalshi traded 4x the volume on election night (Nov 3–4, 2026). — [Gaming America](https://gamingamerica.com/news/1109871/kalshi-polymarket-midterms-night-volume-house-senate)
- Post-election gaps:
  - **Dec 9 FOMC hike:** Kalshi 78–79¢ against Polymarket 76.5% (Nov 6, 2026). — [PredictionMarketsPicks Fed tracker](https://predictionmarketspicks.com/tools/fed-rate-tracker/december-2026)
  - **Dec 12 shutdown:** Kalshi 31% against Polymarket US 32% (~early Nov 2026). — [PredictionMarketsPicks shutdown tracker](https://predictionmarketspicks.com/tools/shutdown-tracker)
  - **Ossoff for the Democratic nomination:** Kalshi about 25% against Polymarket about 24% (~Nov 5–6, 2026). — [Covers](https://www.covers.com/politics/us-election-betting-odds)

**Arbitrage studies**
- A six-month audit of Polymarket against Kalshi found a median real gap of 0.8¢, and every headline "arbitrage" above 8¢ was a stale quote. Near 50¢, a gap must exceed roughly 3–3.5¢ per $1 set to be profitable after fees (2026; exact date not captured). — [PredictMarketCap](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study); [LaunchPoly](https://launchpoly.com/blog/polymarket-kalshi-arbitrage-guide)
- A practitioner's Polymarket–Kalshi monitor found one 2¢ gap, which lost 1.4¢ after real fees (2026). The page also contained embedded instructions aimed at AI tools; these were ignored, and the source should be treated with caution. — [DEV Community](https://dev.to/botcookery/our-polymarket-kalshi-arbitrage-monitor-found-one-2c-gap-after-real-fees-it-lost-14c-41b7)

**Fees**
- Kalshi's taker fee is round-up(0.07 × C × P × (1−P)), where C is contracts and P is price in dollars (fee schedule PDF dated Feb 5, 2026). That is about $1.75 on 100 contracts at 50¢. A revised schedule reportedly took effect Jul 7, 2026. — [Kalshi fee schedule PDF](https://kalshi.com/docs/kalshi-fee-schedule.pdf); [QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained); [chudi.dev](https://chudi.dev/blog/kalshi-fees)
- Kalshi maker fees conflict by source: 0.0175 in place of 0.07 on series listed with maker fees; zero on most series; or 25% of the taker fee. ACH deposits and withdrawals are reportedly free, settlement is free, and card deposits cost up to 2%. — [QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained); [chudi.dev](https://chudi.dev/blog/kalshi-fees); [pm.wiki](https://pm.wiki/uk/learn/kalshi-fees-explained); [SailGP Kalshi fees](https://sailgp.com/prediction-markets/kalshi/fees)
- Polymarket US's taker fee is highest near 50¢. One comparison site gives 6.95% × P × (1−P), capped at about 1.74¢ per contract at 50¢. An August 2026 check put it at $1.50 per 100 contracts at 50¢. Makers receive a rebate, and no settlement, deposit or withdrawal fee is published. A flat 0.01% figure on another guide looks outdated. — [PredictionMarketsPicks (Polymarket US)](https://predictionmarketspicks.com/polymarket-us); [Sharp Football Analysis](https://www.sharpfootballanalysis.com/prediction-markets/polymarket/); [OddsShopper](https://www.oddsshopper.com/articles/betting-101/polymarket-fees)

**Settlement rules and disputes**
- Kalshi midterm contracts can resolve once at least 4 of 8 designated media sources have declared a winner and none has issued a contradictory call. The 2026 Senate Control market has a fallback date if no media consensus forms. Payouts can be delayed if recounts or legal challenges are possible (~Nov 4, 2026). — [Covers: midterm payout rules](https://www.covers.com/politics/midterm-election-prediction-markets-payout-rules-2026)
- Polymarket US's Senate market settles to Yes if Democrats win control, with outcomes sourced from state electoral authorities and the US Senate. — [Polymarket US](https://polymarket.us/event/usse-midterms-2026-11-03)
- Polymarket's UMA oracle has a two-hour challenge window. A disputed market moves to a 24–48 hour debate and then a roughly 48-hour vote, so settlement can take days or weeks. Some platforms give traders no dispute mechanism, and Gemini holds settlement while an official result is delayed or disputed. — [DeFi Rate: how contracts settle](https://defirate.com/prediction-markets/how-contracts-settle/); [Idea Usher](https://ideausher.com/blog/prediction-market-resolve-disputes/)
- Base rate: of 529,408 dispute-observable Polymarket markets, 1,634 (0.31%) had their resolution formally challenged (arXiv, Oct 2026). Related work covers oracle adjudication (Sept 2026) and settlement manipulation (June 2026). — [arXiv 2610.29578](https://arxiv.org/html/2610.29578v1); [arXiv 2609.15368](https://arxiv.org/pdf/2609.15368); [arXiv 2606.31675](https://arxiv.org/pdf/2606.31675)
- In September 2026 a trader argued that the official rules of the Alaska Senate market did not match its title, raising questions about post-election settlement. The outcome and the venue were not given in the snippet. — [CNN (Sept 24, 2026)](https://www.cnn.com/2026/09/24/politics/midterm-elections-prediction-markets-kalshi-polymarket)
- Polymarket has investigated "dozens" of midterm-related bets, and at least two cases were referred to the CFTC (Oct 27, 2026). These are insider-trading probes, not oracle disputes. — [NPR](https://www.npr.org/2026/10/27/nx-s1-6012304/polymarket-election-betting-surveillance); [Yahoo Finance](https://finance.yahoo.com/markets/options/articles/polymarket-investigates-dozens-bets-tied-162500883.html)
- Background, not the midterms: in a 2024 Venezuela election market, UMA token holders reportedly overrode Polymarket's written rules (opinion piece). — [Frank Muci (Substack)](https://frankmuci.substack.com/p/polymarket-settles-bet-against-its)

### Inferences
- Worked fee math uses the published coefficients (Kalshi 0.07; Polymarket US about 0.0695 if the 6.95% figure is right). It assumes the quoted levels were executable, which may not hold if they were mid or last prices.
  - **House:** buy Kalshi YES at 93¢ plus Polymarket US NO at 5.5¢, total 98.5¢, gross 1.5¢. Fees are about 0.46¢ (Kalshi) plus 0.36¢ (Polymarket US), so net is about 0.7¢ per $1 pair before spreads, with capital locked until settlement. That is marginal.
  - **Senate:** 75¢ plus 24.5¢ gives a gross of 0.5¢ against about 2.6¢ in fees, so the trade loses.
  - **Nevada governor:** a 3-point gap near mid-prices gives about 3¢ gross against about 3.5¢ in fees, which is break-even or negative.

  Overall, only gaps at extreme prices, where P(1−P) is small, or gaps above about 3.5 points at mid-prices survive taker fees.
- Small-order rounding: Kalshi rounds the fee up to the next cent. A 1-contract order at 50¢ pays 2¢ instead of 1.75¢, and at 93¢ pays 1¢ instead of about 0.46¢. A small bot should size orders so rounding does not dominate. This assumes rounding applies per order or fill, which should be checked against the live fee schedule.
- Kalshi's media-consensus rule (4 of 8 outlets) and Polymarket's official-source rule can diverge in contested races such as Mississippi or Alaska. "Arbitrage" across them carries basis risk: one venue may settle while the other waits for certification.
- Maker rebates on Polymarket US, and possibly zero maker fees on most Kalshi series, imply that maker-maker cross-venue quoting (rest on both venues, hedge on fill) is the only structurally viable form of cross-venue arbitrage for a small bot. A paper bot can simulate it, but fill probability is the key unknown.

### Gaps
- No documentation was found of how long midterm cross-venue gaps persisted (minutes against hours); the cited gaps are point-in-time snapshots.
- Comparisons with other venues (ForecastEx, Gemini, Robinhood, PredictIt) were not found.
- No formal settlement dispute or reversal on a November 2026 midterm contract (Kalshi or Polymarket) was found as of Nov 7, 2026.
- The outcome of the Alaska rules-versus-title complaint is unknown.
- The current Kalshi maker-fee schedule and the exact Polymarket US fee coefficient remain unverified because of conflicting sources and pages that could not be fetched.

## 5. How election volatility affected Kalshi's 15-minute and hourly crypto contracts (BTC, ETH)

### Takeaway
Election night did not displace crypto as Kalshi's dominant flow. The 15-minute BTC series traded $332.6M on Election Day, more than any single election series. BTC had a short V-shaped move: a dip to about $75.6K overnight on Nov 3–4 (a seven-week low), a rebound above $80K on Nov 4–5, then a reversal to about $75.7K by Nov 6 alongside a tech-stock sell-off. I found no election-week data on spreads or on hourly-contract volumes. Before the election, vendor data showed the 15-minute BTC book usually one tick wide (about 0.6–1.1¢), which leaves little spread to capture.

### Cited Findings
**Volumes**
- On Election Day (Nov 3, 2026), Kalshi's 15-minute bitcoin contracts traded $332.6M, more than any single election series. The five largest election series traded about $440M combined, and platform-wide volume was $4.15B. — [Bitcoin.com News](https://news.bitcoin.com/igaming/kalshi-election-day-volume-hits-4-15b-short-october-record/)
- Crypto contracts on Kalshi and Polymarket combined hit a record $2.7B week (fall 2026; exact week not captured). — [Bitcoin.com News](https://news.bitcoin.com/market-updates/kalshi-polymarket-crypto-volume-record-2-7-billion/)
- Kalshi's crypto category traded $2.42B in Sept 28–Oct 4, 2026 (up 7.37% week over week), with BTC-tagged series the largest identified subset. A prior week was $2.16B. — [DeFi Rate](https://defirate.com/news/sept-28-oct-4-2026-volume-report/)
- Within bitcoin-related markets, the 15-minute up/down series made up 80.6% of volume (undated scoreboard, 2026). Other sources conflict: one search summary claims 86% of Kalshi crypto volume (about $7B of $8.17B, Sept 1–28) came from 15-minute markets, which could not be traced to a source, and another says short-term crypto contracts are "roughly half" of Kalshi crypto flow. — [PM Pulse (Substack)](https://pmpulse.substack.com/p/the-pm-scoreboard-001)

**BTC and ETH price path around the election**
- Bitcoin dipped to $75,618 on election night (Nov 3–4, 2026) as Democrats took the House and Senate, its weakest price in seven weeks. — [KuCoin News](https://www.kucoin.com/news/flash/bitcoin-price-dips-to-75-6k-amid-us-midterm-election-results)
- It made a V-shaped recovery toward $78,000 as midterm uncertainty faded (Nov 4, 2026). Analysts cited in coverage said real yields, dollar liquidity and ETP flows matter more than the election. — [CoinDesk](https://www.coindesk.com/markets/2026/11/04/bitcoin-knocks-on-usd78-000-in-v-shaped-comeback-as-midterm-uncertainty-fades)
- It then rose above $80,000 in a post-midterm risk-asset rally, reaching about $80,400, described as a short squeeze (Nov 4–5, 2026). — [Cointelegraph](https://cointelegraph.com/markets/bitcoin-price-us-stocks-rally-midterm-election-result); [KuCoin News](https://www.kucoin.com/news/flash/bitcoin-rebounds-above-80-000-amid-democratic-sweep-in-u-s-midterm-elections); [Analytics Insight](https://www.analyticsinsight.net/price-analysis/crypto-prices-today-bitcoin-climbs-to-usd-80400-as-midterm-clarity-sparks-short-squeeze)
- The rally reversed on a tech-stock sell-off. BTC, ETH and XRP extended losses, BTC traded around $75,712 and was heading for a fifth straight weekly loss (Nov 6, 2026). Sources disagree on whether the rally peaked on Wednesday Nov 4 or Thursday Nov 5. — [FXStreet](https://www.fxstreet.com/cryptocurrencies/news/crypto-today-bitcoin-ethereum-and-xrp-extend-losses-as-post-midterm-elections-rally-reverses-202611061036)

**Microstructure of 15-minute BTC contracts (pre-election baselines)**
- Vendor tape data from June to August 2026 show an average quoted spread of about 1.1¢ near the open, falling to about 0.6¢ in the final minutes, and the book one tick wide 98% of the time in a June 2026 sample. A broader September 2026 scan of all Kalshi markets found a median spread of 5.1¢ on two-sided books. The snippet did not say which vendor page carries which figure. — [PredictionMarketsPicks: the 12:30 rule vs our tape](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-last-60-seconds); [PredictionMarketsPicks: KXBTC15M explainer](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-markets)
- Sources disagree on intra-window liquidity. One says the first five minutes are wider, the middle is tightest, and depth thins in the last five minutes as makers pull risk. A separate test found spreads do not widen late even though top-of-book size thins. — [Kalshi BTC 15-minute guide (KalshiBacktest)](https://kalshibacktest.com/resources/kalshi-btc-15-minute-markets); [PredictionMarketsPicks](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-last-60-seconds)
- Market makers reprice within seconds off the same real-time indexes the contracts settle on, which makes stale-quote sniping hard. Prices can re-price by 30 cents or more in a single minute. No listed option expires in 15 minutes, so options-implied volatility cannot anchor pricing, and any edge must clear spread plus fee. — [OddsShopper](https://www.oddsshopper.com/articles/prediction-markets/kalshi-15-minute-markets); [SailGP: Kalshi 15-minute markets](https://sailgp.com/prediction-markets/kalshi/15-minute-markets); [Bot for Kalshi](https://www.botforkalshi.com/blog/kalshi-15-minute-bitcoin-markets)
- Each 15-minute bitcoin window settles on the average of 60 one-second index prints. — [KalshiBacktest](https://kalshibacktest.com/resources/kalshi-btc-15-minute-markets); [PredictionMarketsPicks: KXBTC15M explainer](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-markets)
- Live cross-venue comparisons of 15-minute BTC odds (Kalshi against Polymarket) are published by aggregators (snapshots dated Oct 22–26, 2026). — [DeFi Rate crypto odds](https://defirate.com/odds/crypto/)

### Inferences
- The election's direct effect on crypto contracts looks like a short burst of overnight volatility (Nov 3–4), followed by a return to a tech-equity-driven regime (Nov 6). For a 15-minute or hourly bot, scheduled macro events matter more than politics: the Nov 10 inflation report, the Nov 18 FOMC minutes, the Dec 4 jobs report and the Dec 9 FOMC (dates from Section 2).
- With books usually one tick wide and makers repricing within seconds, spread capture is unlikely to be the edge for a small paper bot. The more plausible edge is a short-horizon volatility forecast compared with contract-implied probabilities, with the 60-second settlement averaging modeled explicitly, tested around scheduled events.
- Because 15-minute BTC volume ($332.6M) beat any election series on Election Day, election nights do not appear to drain crypto liquidity, so a crypto bot would not have faced unusually thin books that day. This is not directly verified.

### Gaps
- No data were found on Kalshi's hourly BTC or ETH contracts (volume, spreads or pricing) around the election, and none on ETH 15-minute contracts specifically.
- No election-week (Nov 2–7, 2026) spread, depth or realized-versus-implied volatility measurements were found for the 15-minute contracts. The available microstructure data are pre-election baselines from June to September 2026.
- The $8.17B / 86% figure (Sept 1–28) could not be traced to a source and conflicts with the "80.6%" and "roughly half" figures.
- Exact intraday timestamps of the BTC low and rebound relative to race calls were not captured.
