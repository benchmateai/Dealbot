# Structural (market-microstructure) edges on Kalshi: the favorite-longshot bias, maker vs taker economics and fees, market making, and near-expiry "high-probability" buying

*Method note (researched 2026-11-03).* This session's network policy blocked direct reads of almost every primary page: ucd.ie, cepr.org, jbecker.dev, arxiv.org, ssrn.com, kalshi.com, help.kalshi.com, docs.kalshi.com and cftc.gov. GitHub access was limited to this project's own repository. Numbers attributed below to papers, blogs and Kalshi help pages therefore come from search-engine extraction of those pages, not from my own reading of the full text. Treat every one as "reported, needs checking against the PDF".

The one primary source I could read directly was Kalshi's public trading API (`api.elections.kalshi.com/trade-api/v2`). I pulled it on 2026-11-03 for:
- the current fee type and multiplier of every series;
- the fee-change log;
- the liquidity and volume incentive programs.

Those figures are first-hand and current. Every return figure quoted here is an unverified claim by whoever measured it.

---

## Q1. What do empirical studies of Kalshi (and Polymarket) trade data find about the favorite-longshot bias and maker vs taker returns?

### Takeaway
Three Kalshi datasets broadly agree:
- Bürgi, Deng and Whelan (about 300,000 contracts).
- Becker (72.1M trades, June 2021 to November 2025).
- Bartlett (41.6M trades).

What they agree on:
- **Longshots lose.** Cheap contracts (below about 10-20c) win much less often than their price implies.
- **Favorites win slightly more often than their price implies.** Contracts above about 50-80c win a little more often.
- **The side that rests orders (the maker) does better than the side that crosses the spread (the taker).** The damage is concentrated in takers buying YES longshots.

At the favorite end the mispricing is small: fractions of a cent to about 1 cent per contract, before fees. The maker advantage is fairly recent; in one study it only became consistent from about 2024 Q2.

### Cited Findings

**Bürgi, Deng and Whelan, "Makers and Takers: The Economics of the Kalshi Prediction Market" (University College Dublin)**
- **Versions:**
  - posted to SSRN September 2025 — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5502658)
  - UCD CER WP2025/19 — [UCD](https://www.ucd.ie/economics/t4media/WP2025_19.pdf)
  - CEPR DP20631, revised January 2026 — [CEPR](https://cepr.org/publications/dp20631)
  - CESifo WP 12122 — [CESifo](https://www.ifo.de/en/cesifo/publications/2026/working-paper/makers-and-takers-economics-kalshi-prediction-market)
  - GWU Research Program on Forecasting WP 2026-001, titled "Makers *or* Takers" — [GWU](https://www2.gwu.edu/~forcpgm/2026-001.pdf)
  - author copy — [karlwhelan.com](https://www.karlwhelan.com/Papers/Kalshi.pdf)
- **Data:** "over 300,000 Kalshi contracts" — [EconBiz record](https://www.econbiz.de/Record/makers-and-takers-the-economics-of-the-kalshi-prediction-market-b%C3%BCrgi-constantin/10015434529). The exact sample period was not retrieved.
- **Accuracy and the bias:**
  - Prices are informative and become more accurate as markets approach closing.
  - There is a clear favorite-longshot bias. Low-price contracts win far less often than needed to break even after fees.
  - High-price contracts win more often and "yield small positive returns."
  - Sources: [SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5502658); [VoxEU column](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market)
- **Longshots:** buyers of contracts costing less than 10c "lose over 60 percent of their money" (search extraction of the paper and column) — [VoxEU](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market); [Whelan PDF](https://www.karlwhelan.com/Papers/Kalshi.pdf)
- **Average return across all contracts:** about −20% before fees and about −22% after fees in one version. Another extraction cites −20% as the after-fee figure, so the number varies between versions — [GWU WP](https://www2.gwu.edu/~forcpgm/2026-001.pdf); [UCD WP](https://www.ucd.ie/economics/t4media/WP2025_19.pdf)
- **Maker vs taker averages:** takers lose "almost 32%" on average and makers about 10% — [VoxEU column](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market)
- **Maker vs taker by price:**
  - The pattern is "much stronger for takers than for makers, with far bigger losses for takers on their longshot contracts."
  - There is "some evidence that Makers who buy contracts priced above 50c earn statistically significant positive returns."
  - Sources: [GWU WP](https://www2.gwu.edu/~forcpgm/2026-001.pdf); [Whelan PDF](https://www.karlwhelan.com/Papers/Kalshi.pdf)
- **Explanation (their model):** modest disagreement among traders, plus a small tendency to overweight small probabilities, plus Kalshi's fee structure. Together these reproduce both the overall bias and the maker-taker gap — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5502658); [CEPR DP](https://cepr.org/publications/dp20631)
- **Trend:** "some evidence of a weakening in the favorite–longshot bias over time" (GWU version) — [GWU WP](https://www2.gwu.edu/~forcpgm/2026-001.pdf)

**Becker, "The Microstructure of Wealth Transfer in Prediction Markets" (independent; jbecker.dev)**
- **Data:** 72.1M Kalshi trades, $18.26B of volume, June 2021 to November 2025 — [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure); [HackingTheMarkets summary](https://hackingthemarkets.com/why-kalshi-takers-lose-money-72m-trades-analyzed/)
- **Dataset and code** are public — [Jon-Becker/prediction-market-analysis](https://github.com/jon-becker/prediction-market-analysis)
- **Date conflict:** listings show January 2026 and August 1, 2026 — [daily.dev](https://app.daily.dev/posts/the-microstructure-of-wealth-transfer-in-prediction-markets-ulhf5ydzn)
- **Author:** a senior software engineer on Coinbase's prediction-markets team, per his LinkedIn profile. That is an industry affiliation, so a possible interest — [LinkedIn](https://www.linkedin.com/in/jon--becker/)
- **Metric:** "excess return" is measured gross of platform fees — [fatskier/prediction-marks replication note](https://github.com/fatskier/prediction-marks)
- **Average excess returns:**
  - Takers about −1.12% and makers about +1.12%.
  - At 50c, takers −2.65% and makers +2.66% — [KuCoin news summary](https://www.kucoin.com/news/flash/analysis-reveals-systematic-wealth-transfer-in-prediction-markets)
  - Another summary says makers earn about +2.5% per trade, so the headline figure is inconsistent across write-ups — [HackingTheMarkets](https://hackingthemarkets.com/why-kalshi-takers-lose-money-72m-trades-analyzed/)
- **Breadth:** takers have negative excess returns at 80 of 99 price levels, and makers positive at those same levels — [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure)
- **The 1-cent extreme:**
  - Takers buying 1c contracts won about 0.43% of the time against 1% implied, a mispricing of about −57%.
  - Makers buying at 1c won 1.57% of the time, about +57% — [HackingTheMarkets](https://hackingthemarkets.com/why-kalshi-takers-lose-money-72m-trades-analyzed/); [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure)
- **Price buckets (all trades pooled):**
  - Every price below 20c underperformed its odds, and every price above 80c outperformed.
  - 5c contracts won 4.18% of the time; 95c contracts won 95.83%.
  - Source: [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure) (via search extraction)
- **YES vs NO:**
  - YES contracts underperform NO contracts of the same cost, especially at longshot prices. Becker calls this an "optimism tax" paid by takers.
  - In the 1-10c range, takers supply 41-47% of YES volume and makers only 20-24%.
  - At 99c, makers buy NO on 43% of volume.
  - Source: [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure)
- **Time variation:**
  - From launch through 2023, takers earned +2.0% and makers −2.0%. The sign flipped in 2024 Q2.
  - The transfer to makers became consistent only once depth grew enough to attract sophisticated makers.
  - Sources: [fatskier note](https://github.com/fatskier/prediction-marks); [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure)
- **By category:** Finance markets are near-efficient (a 0.17 percentage-point gap); Entertainment and Media show gaps of 7+ points — [KuCoin summary](https://www.kucoin.com/news/flash/analysis-reveals-systematic-wealth-transfer-in-prediction-markets)

**Bartlett (Stanford Law), "Adverse Selection in Prediction Markets: Evidence from Kalshi" (working paper)**
- **Dates and authors:** dated January 2026 on ResearchGate and April 21, 2026 on Stanford's page. One write-up also names Maureen O'Hara (Cornell) as co-author — [Stanford](https://law.stanford.edu/publications/adverse-selection-in-prediction-markets-evidence-from-kalshi/); [ResearchGate](https://www.researchgate.net/publication/404044013_Adverse_Selection_in_Prediction_Markets_Evidence_from_Kalshi); [InGame](https://www.ingame.com/study-kalshi-betting-yes/)
- **Data:** 41.6M trades across 478,167 markets — [InGame](https://www.ingame.com/study-kalshi-betting-yes/)
- **Findings** ([ResearchGate abstract](https://www.researchgate.net/publication/404044013_Adverse_Selection_in_Prediction_Markets_Evidence_from_Kalshi)):
  - "Single-name" markets (one candidate, one team) show more informed price impact than broad-based markets.
  - Yet their effective spreads are only modestly wider, and market makers earn **twice as much per contract** there.
  - The explanation offered: traders "systematically overbet YES in markets that predominantly settle NO." That behavioral surplus cross-subsidizes adverse selection.
  - One-sided order flow predicts maker losses in single-name markets but not in broad-based ones.

**Other Kalshi-specific checks (smaller, unreviewed)**
- **Kalshi unemployment markets** (July 2021 to March 2026): "clear evidence of the classic favorite-longshot bias" — [ResearchGate](https://www.researchgate.net/publication/409238145_Market_Efficiency_and_the_Favorite-Longshot_Bias_in_Unemployment_Prediction_Markets)
- **Cheap Kalshi NFL prop contracts:** resolved YES *more* often than priced, a mild reverse bias (an analysis in a GitHub pull request) — [lmaynor/mlb-betting PR #35](https://github.com/lmaynor/mlb-betting/pull/35)

**Polymarket evidence (a different venue with its own fee and regulatory structure; not directly transferable to Kalshi)**
- **Cardozo and Rivero-Wildemauwe** (arXiv 2609.12878; 588M trades by 2.48M accounts) — [arXiv](https://arxiv.org/abs/2609.12878):
  - Purchases below 10c lose 19.3 cents per dollar; purchases at or above 90c earn 0.83 cents per dollar.
  - Longshots lose 6.3 cents per dollar when each contract is weighted equally, but *gain* 4.1 cents when related contracts are first grouped by parent event.
  - The bias is robust in Crypto and Politics and "absent in Sports."
- **Qin and Yang, "Polymarket-v1 Database"** (arXiv 2606.04217, June 2026): mean (payout − price) by price decile, resolved markets only — [arXiv](https://arxiv.org/pdf/2606.04217):

  | Price decile | Mean (payout − price) |
  |---|---|
  | 0.00-0.10 | −0.0023 |
  | 0.10-0.20 | −0.0019 |
  | 0.20-0.30 | −0.0032 |
  | 0.30-0.40 | −0.0005 |
  | 0.40-0.50 | +0.0026 |

- **Qiu and Qiu** (arXiv 2610.13593; Polymarket daily maximum-temperature markets; accepted at the IEEE ICDM 2026 Teen Research Symposium, i.e. a student paper) — [arXiv](https://arxiv.org/abs/2610.13593):
  - The bias is "strongly time-asymmetric." Longshot overpricing mostly occurs at distant horizons.
  - Overpricing of *favorites* becomes much stronger in the final 1-12 hours. One extraction reported this window; another could not confirm it.
  - The main remaining error sits at the favorite end.

**Classic literature (mechanism)**
- **Page and Clemen (2013, *Economic Journal*)**, over 500,000 Intrade transactions — [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0297.2012.02561.x); [Duke PDF](https://people.duke.edu/~clemen/bio/Published%20Papers/45.PredictionMarkets-Page&Clemen-EJ-2013.pdf):
  - Markets were reasonably calibrated close to expiration but biased far from it.
  - With more than 100 days to expiry, the bias was 4.7-10.9 percentage points at prices of 0.20 and 0.80.
  - The mechanism is time discounting of a distant payout. The bias is exploitable only by traders with a low discount rate.
  - Bürgi et al. note that this result came from contracts traded well over 10 days before close, and that Page and Clemen found no significant price/probability deviations close to closing — [GWU WP](https://www2.gwu.edu/~forcpgm/2026-001.pdf)
- **Origin:** the favorite-longshot bias was first recorded by R. M. Griffith in 1949, in horse-race betting — [JSTOR Daily](https://daily.jstor.org/betting-on-the-longshot); [Wikipedia](https://en.wikipedia.org/wiki/Favourite-longshot_bias)

**Who is on the other side**
- More than three-quarters of Kalshi volume is sports-driven, per a WSJ report — [WSJ via iTiger repost](https://www.itiger.com/hans/news/2570847487)
- A Citizens Bank analysis (February 2026) found the lowest-performing Kalshi traders lost at a higher rate than sportsbook bettors. The same post argues that Kalshi, though not a counterparty, still needs users to lose because its revenue is fees — [Rose-Berman, "Kalshi's Favorite Lie"](https://howgamblingworks.substack.com/p/kalshis-favorite-lie)

### Inferences
- **Reading Whelan's averages correctly.** The −32% (takers) and −10% (makers) figures are averages of *percentage* returns per contract bought. Longshot losses (−60% and worse) dominate them. They are not dollar P&L.
  - Each trade has a maker and a taker holding opposite sides, so dollar P&L between them is zero-sum before fees.
  - Becker's "excess return" (win rate minus price) is closer to a per-contract dollar transfer. It shows makers gaining about 1-2.7 cents per contract at mid prices, *before fees*.
  - The writer should not present "makers lose 10%" as meaning market making loses money.
- **The edge is mostly a maker/taker effect, not a pure price effect.** Inverting Becker's 1-cent numbers:
  - The taker selling the 1c YES that a maker buys is effectively buying 99c NO. That taker wins about 98.43%, roughly −0.57 points against 99%.
  - The maker buying 99c NO against a taker's 1c YES wins about 99.57%, roughly +0.57 points.
  - So even at the "near-certain" end, takers lose and makers win. "Favorites are underpriced" holds mainly for whoever *rests* the favorite bid. (This inference assumes the pooled 1c statistics map one-to-one onto 99c NO counterparties.)
- **Who loses and why:**
  - Recreational takers buy YES on longshots out of lottery preference, overweighting of small probabilities, and optimism (Becker's "optimism tax"; Bartlett's YES overbetting in markets that mostly settle NO).
  - They pay a taker fee that is largest in proportion to stake at the extremes.
  - The beneficiaries are professional resting liquidity providers.
- **Durability.** The behavioral source has been documented since 1949 and is very persistent. The *share* of it a newcomer can capture is not:
  - the maker premium did not exist before 2024;
  - Whelan sees the bias weakening;
  - competition among makers, plus Kalshi's expanding maker fees (Q2), will compress it.
- **The grouping result is a warning.** Cardozo and Rivero-Wildemauwe found the Polymarket longshot loss flips sign when contracts are grouped by event. "Sell every longshot in a multi-strike ladder" may therefore look better in equal-weighted statistics than in correlated, event-level P&L.

### Gaps
- I could not retrieve the price-bucket tables (Total / Makers / Takers by 10c bin, including a 90-100c bin), the after-fee returns by bucket, the exact sample period of Bürgi-Deng-Whelan, or any breakdown by time to close.
- A truncated snippet ("for Makers, the pattern of returns generally worsening as the price rises…") could not be resolved against the claim that makers earn positive returns above 50c.
- No Kalshi sports-only favorite-longshot magnitudes were found, although sports dominate volume. Polymarket finds the bias absent in sports.
- Not retrieved:
  - arXiv 2607.14430, "Prices, Probabilities, and Parlays: Systematic Bias in Sports Prediction Markets" — [arXiv](https://arxiv.org/pdf/2607.14430)
  - arXiv 2602.19520 — [arXiv](https://arxiv.org/pdf/2602.19520)
  - the Ontario Securities Commission-funded Polymarket winners/losers paper (October 2026) — [OSC](https://www.osc.ca/sites/default/files/2026-10/research-grant-competition-2026-who-wins-and-who-loses-in-prediction-markets.pdf)
  - Kalshi's own research paper, "Calibration in Prediction Markets: Theory and Evidence." It is exchange-authored, so treat it as interested — [Kalshi](https://kalshi.com/research/kalshi-research-calibration.pdf)
- None of the headline Becker numbers has been independently replicated, as far as I could find.

---

## Q2. What is Kalshi's current fee schedule, how did it change in 2025-2026, and what break-even edge does it imply by price?

### Takeaway
- **Taker fee:** round_up(M × 0.07 × C × P × (1−P)), where C is the number of contracts, P the price and M a per-series multiplier. It peaks at 1.75c per contract at 50c.
- **Maker fee:** round_up(M × 0.0175 × C × P × (1−P)), a quarter of the taker rate. It applies only to series listed for maker fees.
- **Coverage today:** per Kalshi's own API on 2026-11-03, 160 of 15,679 series charge maker fees. They are concentrated in the deepest sports game lines and macro releases (Fed, CPI, payrolls, GDP). Daily weather highs, S&P and Nasdaq daily/hourly, crypto hourly, elections and "mentions" markets charge no maker fee.
- **What this means for favorites:** the fee is small in cents at the extremes but large relative to the upside. On a 95-99c favorite the taker fee is about 7% of the maximum profit.
- **Rounding is decisive and unresolved.** If fees round up to the cent per order, a 1-contract taker order at 99c pays 1c, the entire upside.

### Cited Findings
- **Official schedule.** Kalshi's "Fee Schedule for July 2026 – 7.7.26 Update" says:
  - trading fees are charged only on orders that immediately match resting orders;
  - resting orders are charged only in series listed under "Maker Fees";
  - there is a separate perpetuals schedule with tiered basis-point maker/taker fees.
  - Source: [Kalshi fee schedule PDF](https://kalshi.com/docs/kalshi-fee-schedule.pdf) (search extraction; the tables themselves were not visible)
- **Taker formula:** round_up(0.07 × C × P × (1−P)); maximum 1.75c per contract at 50c — [QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained); [Allium](https://www.allium.so/blog/kalshi-fees-why-the-cost-peaks-near-50-cents/); [Courtney, "Maker/Taker Math on Kalshi" (Sept 17, 2025)](https://whirligigbear.substack.com/p/makertaker-math-on-kalshi)
- **Maker formula:** 0.0175 × M × C × P × (1−P), with M defaulting to 0 unless a series is listed. That is about 0.44c per contract at 50c versus 1.75c for a taker — [DefiRate](https://defirate.com/prediction-markets/fees/); [BotForKalshi](https://www.botforkalshi.com/blog/kalshi-fees-explained)
- **Conflicting maker-fee label:** one review gives a "1.75%" maker fee, which conflicts with the 0.0175 coefficient — [MarketMath](https://marketmath.io/platforms/kalshi)
- **Rounding (conflict):**
  - Most guides say fees round up to the cent per order.
  - Another reading of the API docs says direct-member balances are aligned to $0.0001 and non-direct members to $0.01, with any overpayment rebated across the same order's fills.
  - Sources: [DefiRate](https://defirate.com/prediction-markets/fees/); [QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained)
- **Primary data: current fee type and multiplier by series**, from Kalshi's API pulled 2026-11-03 — [Kalshi API /series](https://api.elections.kalshi.com/trade-api/v2/series):

  | Fee type × multiplier | Series |
  |---|---|
  | Taker-only (`quadratic`) × 1 | 15,484 |
  | Maker fees (`quadratic_with_maker_fees`) × 1 | 159 |
  | Maker fees × 0.5 (KXMLBGAME only) | 1 |
  | Taker-only × 0.5 (MLB props: home runs, hits, totals, spreads, first-5-innings…) | 18 |
  | Fee-free (× 0) | 14 |
  | Combo maker fees (`quadratic_with_combo_maker_fees`) | 3 |

  - Fee-free series are mostly long-dated political and annual markets, e.g. KXTRUMPOUT, KXGREENLAND, KXBTCY, KXETHY, KXGDPYEAR, KXNEXTIRANLEADER, KXGAMBLINGREPEAL.
  - Combo maker-fee series: KXMVECROSSCATEGORY, its SHARD1, and KXMVESPORTSMULTIGAMEEXTENDED.
  - The 160 maker-fee series by category:
    - Sports 107 (NFL, NBA, NHL, MLB, WNBA, NCAA game lines, spreads and totals; soccer leagues; tennis; golf; F1; awards);
    - Science & Technology 21 (GPU rental-price series H100, H200, A100, B200, RTX5090);
    - Financials 13;
    - Economics 10 (KXFED, KXFEDDECISION, KXCPI, KXCPIYOY, KXGDP, KXPAYROLLS, KXU3, KXRATECUTCOUNT…);
    - Entertainment 7;
    - Crypto 2 (KXBTCMAX125/150).
  - Taker-only (no maker fee) examples: KXHIGHNY, KXHIGHCHI, KXHIGHMIA, KXHIGHAUS (weather); KXINX, KXINXU, KXNASDAQ100, KXNASDAQ100U (index daily/hourly); KXBTCD, KXBTC, KXETHD (crypto hourly); PRES; KXTRUMPSAY.
- **Primary data: fee-change log**, 107 entries — [Kalshi API /series/fee_changes](https://api.elections.kalshi.com/trade-api/v2/series/fee_changes?show_historical=true):

  | Effective (UTC) | Change |
  |---|---|
  | 2025-10-04 | KXMLBGAME → maker fees |
  | 2025-10-21 | KXTRUMPOUT → fee-free |
  | 2025-11-15 | 23 series → maker fees (NBA spreads/totals/awards, NCAA men's basketball, NCAAF spreads/totals/playoff, ATP/WTA matches, March Madness) |
  | 2026-01-01 | KXNFLGAME (plus NCAAF spread/total) → maker fees |
  | 2026-06-05 | KXWCGAME → maker fees |
  | 2026-07-03 | KXINX, KXINXU, KXINXMAXY, KXINXMINY, KXINXPOS, KXNASDAQ100, KXNASDAQ100U → taker-only × 1; yearly KXINXY and KXNASDAQ100Y → maker fees |
  | 2026-08-07 | KXMLBGAME maker-fee multiplier → 0.5, plus 18 MLB prop series → × 0.5 |
  | 2026-08-20 | multivariate/combo series → combo maker fees |
  | 2026-09-03 | 30 GPU-price series → maker fees |

- **The S&P/Nasdaq discount has ended:**
  - Kalshi halved fees on its S&P and Nasdaq markets in 2022 — [Kalshi News](https://news.kalshi.com/p/were-halving-the-fees)
  - 2026 guides still describe a 0.035 coefficient for those series — [ChanceMetrics](https://chancemetrics.com/prediction-market-fees)
  - But the index series moved to the standard multiplier on July 3, 2026 — [Predictefy API guide](https://blog.predictefy.com/kalshi-api-guide); [Oddsshopper fee audit](https://www.oddsshopper.com/articles/prediction-markets/kalshi-fee-schedule-by-market)
  - My API pull agrees: multiplier 1, no maker fee, since 2026-07-03T17:00Z.
- **Maker-fee coverage has grown:** guides from earlier in 2026 say "approximately 105" series; an August 2026 audit is titled "The 129 Markets That Cost More To Trade"; the API shows 160 today — [DefiRate](https://defirate.com/prediction-markets/fees/); [Oddsshopper](https://www.oddsshopper.com/articles/prediction-markets/kalshi-fee-schedule-by-market)

### Inferences
- **Fee and break-even table.** Computed by me from the formula, with cent round-up per order and multiplier 1. A favorite *buyer's* break-even win rate is price + fee.

  | Price | Exact taker fee per contract | Fee on a 1-contract order | Fee per contract, 100-lot | Maker fee per contract (listed series) | 100-lot taker fee as % of max profit | Taker break-even win rate (100-lot) |
  |---|---|---|---|---|---|---|
  | 1c | 0.069c | 1c | 0.07c | 0.017c | 0.1% | 1.07% |
  | 5c | 0.333c | 1c | 0.34c | 0.083c | 0.4% | 5.34% |
  | 10c | 0.630c | 1c | 0.63c | 0.158c | 0.7% | 10.63% |
  | 20c | 1.120c | 2c | 1.12c | 0.280c | 1.4% | 21.12% |
  | 50c | 1.750c | 2c | 1.75c | 0.438c | 3.5% | 51.75% |
  | 80c | 1.120c | 2c | 1.12c | 0.280c | 5.6% | 81.12% |
  | 90c | 0.630c | 1c | 0.63c | 0.158c | 6.3% | 90.63% |
  | 95c | 0.333c | 1c | 0.34c | 0.083c | 6.8% | 95.34% |
  | 97c | 0.204c | 1c | 0.21c | 0.051c | 7.0% | 97.21% |
  | 99c | 0.069c | 1c | 0.07c | 0.017c | 7.0% | 99.07% |

- **Small orders at the extremes are uneconomic if rounding is per order to the cent.** A 1-lot at 95-99c pays 1c, which is 20-100% of the maximum profit. Order sizes of tens to hundreds of contracts bring the fee down to the exact formula. If Kalshi really rounds to 1/100 of a cent with rebates (the July 2026 reading), this problem largely disappears. **Verify on a live fill before sizing any near-certainty strategy.**
- **Fees versus the measured mispricing:**
  - At 95c the pooled edge Becker measured (95.83% wins) is +0.83 points gross. The 100-lot taker fee takes 0.34 of that.
  - Paying the ask rather than the mid adds about half a cent more on a 1c-wide book. That puts a taker at roughly break-even, before noting that taker-specific win rates are below the pooled figure.
  - At 50c, Becker's maker excess return (+2.66c) comfortably beats the maker fee (0.44c) where one is charged.
- **The free-maker edge now sits mostly outside the deepest books.** Maker fees now cover the deepest, most liquid books (NFL/NBA/MLB game lines, Fed/CPI/payrolls). Fee-free market making is concentrated in thinner series: weather, index hourly, crypto hourly, politics, mentions, entertainment. Those are also where per-trade adverse selection is often higher (see Q3, Bartlett).
- **The fee regime is a moving target.** Kalshi has repriced fees by series in both directions within 13 months: maker fees added, MLB halved, long-dated politics made free. A bot should read `fee_type` and `fee_multiplier` from `/series` at runtime rather than hard-code them.

### Gaps
- The exact text of the July 7, 2026 schedule (the coefficient tables, per-fill versus per-order rounding, any fee cap) could not be read directly.
- One fee guide surfaced by search says maker fees "did not actually start charging traders until 11:59 PM ET on Wednesday, August 19, 2026" per Kalshi's changelog. That conflicts with the API log, which shows maker-fee changes from October 2025. I could not identify or verify the page.
- How volume-incentive payouts offset taker fees in subsidized series (e.g. 15-minute crypto) is not documented in anything I could read.
- The fee terms of Market Maker Agreements are confidential (Q3).

---

## Q3. How do Kalshi's market-maker and liquidity-incentive programs work, and what do practitioners report about running market-making bots?

### Takeaway
Kalshi has two layers.

**(a) A closed, negotiated tier.** This is the Market Maker Agreement program, with Susquehanna (SIG) reported as flagship since 2024. It offers confidential fee discounts, rebates or revenue shares and adjusted position limits, in exchange for two-sided quoting obligations. A "Liquidity Provider Program" runs reward auctions among agreement holders.

**(b) An open Liquidity Incentive Program (LIP).** This pays ordinary members a pro-rata share of a per-market pool for resting two-sided size near the inside, scored on 1-second snapshots. Agreement holders are excluded.

**Current scale of the LIP** (Kalshi API, 2026-11-03):
- about 4,400 markets with live pools, accruing about $92k/day in aggregate (median about $14 per market per day);
- about $12.5M of pools scheduled across September 21 to November 30, 2026.

**What practitioners report** (unaudited): for small bots, the subsidy is what pays, not spread capture. Raw realized spreads in major sports were below the maker fee.

### Cited Findings

**Market Maker Agreement tier**
- Kalshi's rulebook allows market makers financial benefits and reduced fees, and adjusted position limits — [KalshiEX Rulebook](https://cdn.robinhood.com/assets/robinhood/legal/KalshiEX_LLC_Rulebook.pdf)
- Initial program terms were filed with the CFTC in 2024 — [CFTC filing, Appendix A](https://www.cftc.gov/filings/orgrules/rules02262412176.pdf)
- The Market Maker Agreement is not public. Kalshi "publishes one liquidity subsidy and seals the other" — [Navnoor Bawa](https://www.navnoorbawaresearch.com/p/kalshi-publishes-one-liquidity-subsidy)
- **Liquidity Provider Program:** members who have signed a Market Maker Agreement may become a "Designated Liquidity Provider" for an incentivized series. Rewards are set by auction: you state the minimum Incentive Period Reward you would accept — [Kalshi Help: Liquidity Provider Program](https://help.kalshi.com/en/articles/15410219-liquidity-provider-program)
- Unverified third-party claims: a cap of $50,000 per series per week — [Navnoor Bawa (Medium)](https://medium.com/@navnoorbawa/kalshi-publishes-one-liquidity-subsidy-and-seals-the-other-polymarket-too-b59e8c9dffe8); and a 98% per-hour uptime obligation, which surfaced in search but was not confirmed against Kalshi documents.
- Susquehanna has been reported as Kalshi's first and flagship market maker since about April 2024. This rests on search summaries of secondary coverage (one result was Tradermath) and was not checked against a Kalshi announcement — [Tradermath](https://www.tradermath.org/articles/prediction-markets-trading-at-quant-firms)
- Hedge funds were reported to be entering prediction markets "in a big way" in August 2026 — [CNBC, Aug 19, 2026](https://www.cnbc.com/2026/08/19/hedge-funds-are-about-to-jump-in-big-to-prediction-markets.html)

**Liquidity Incentive Program (LIP) mechanics**
- **Scoring** ([Kalshi Help: LIP](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program); [CFTC filing Feb 11, 2026](https://www.cftc.gov/sites/default/files/filings/orgrules/26/02/rules02112639183.pdf); [CFTC update Jul 15, 2026](https://www.cftc.gov/filings/orgrules/rules07152610358.pdf)):
  - Kalshi snapshots each eligible book once per second.
  - Each side is scored by walking down from the best price, admitting whole price levels until resting size reaches the market's Target Size (more than 100 and fewer than 20,000 contracts).
  - An order's weight is Discount Factor^N × size, where N is the number of ticks from the reference price.
  - Snapshots without two-sided depth at the Target Size are excluded.
  - Resting orders earn whether or not they trade.
- **Payout** ([Kalshi Help: LIP](https://help.kalshi.com/en/articles/13823851-liquidity-incentive-program)):
  - your score ÷ all participants' scores × period reward × (non-excluded snapshots ÷ total snapshots), rounded down to the cent;
  - individual rewards under $1 are not paid;
  - daily rewards ran $1-$1,000 per market on the older help page;
  - Market Maker Agreement holders and Kalshi affiliates are excluded.
- A GitHub research note says an October 14, 2026 filing, effective October 28, raised pools to $10-$10,000 per business day with periods of 1-7 days (unconfirmed) — [rohanmalhotra0/kal PR #15](https://github.com/rohanmalhotra0/kal/pull/15)
- `GET /incentive_programs` is public and unauthenticated. The unit of `period_reward` is not documented; developer notes say centi-cents — [Kalshi docs](https://docs.kalshi.com/api-reference/incentive-programs/get-incentives); [Kalshi Help: where to find LIPs](https://help.kalshi.com/en/articles/16076644-liquidity-incentive-programs-where-to-find-them)
- Kalshi's changelog also lists newer program types, including margin maker and taker *volume* programs — [Kalshi API changelog](https://docs.kalshi.com/changelog)

**Primary data: incentive programs** ([Kalshi API /incentive_programs](https://api.elections.kalshi.com/trade-api/v2/incentive_programs), pulled 2026-11-03; dollar figures assume `period_reward` is in centi-cents, which the cross-check under Inferences supports)
- **Totals:** at least 170,000 liquidity programs (17 full pages of 10,000), with start dates from 2026-09-21 to 2026-11-30.
  - Pools: about $2.76M (Sept 21-30), $8.68M (October) and $1.02M scheduled so far for November.
  - 140,754 programs are marked paid out, with $10.28M of pools between them. These are pool sizes, not amounts actually paid.
- **Live now:** 4,385 markets had an active program at about 19:00 UTC on November 3, accruing about $92k/day combined.
  - Per market per day: median about $14, 90th percentile $36, maximum $168.
- **Parameters:**
  - every active program uses Discount Factor 0.5 (5000 bps), so each tick behind the reference price halves the weight;
  - Target Size is 1,000 contracts (4,315 programs) or 2,500 (70 programs).
- **Program sizes:** median $90, 90th percentile $100, 99th percentile $500, largest $2,000 (an NCAAF game-delay market). NYC Marathon programs ran $1,000-$1,480.
- **Where the pools are:** concentrated in election markets on midterm election day (KXMIDTERMMOV, KXVOTEGENERAL, KXVOTECOUNTY…), Rotten Tomatoes scores, YouTube views, shipping-chokepoint weeklies (Hormuz, Suez, Panama) and "Trump says" markets.
- **Volume programs:** at least 10,000 programs from April 4 to October 28, 2026, mostly on KXBTC15M and KXETH15M (15-minute crypto), totalling about $360k across the records retrieved.

**Practitioner and bot evidence (all self-reported and unaudited)**
- **geniuswang05/kalshi_alpha_search** — [GitHub](https://github.com/geniuswang05/kalshi_alpha_search):
  - Of the edges it searched for, "the one that survives is not a forecast at all: it is the exchange's own liquidity subsidy."
  - A passive market-making check in major sports leagues found realized spread of 0.02-0.14c per contract, below the 0.2-0.4c maker fee.
  - Its planned event study (12,109 subsidy-end and 2,411 subsidy-start events against never-subsidized controls) shows results "pending."
- A reward-farming bot write-up reports that on Kalshi "fills on their own lose money; the liquidity rewards carry the bot." Attribution is per search summary and I did not read it — [JosephWong333/prediction-market-bots](https://github.com/JosephWong333/prediction-market-bots)
- **mirabilis-agent/lip-ledger** reconstructs LIP scoring and matched real payouts closely: $4.44 modelled vs $4.57 paid for a weekly program, and $15.58 vs $15.73 for three hourly programs. It is "a $20 autonomous agent," so very small scale — [GitHub](https://github.com/mirabilis-agent/lip-ledger)
- A Kalshi bot project built a "liquidity-incentive shadow market maker" that logs without placing orders — [50thycal/kalshi_bot PR #415](https://github.com/50thycal/kalshi_bot/pull/415)
- **UFO Holdings** (opinion, about September 2025, written by a former trader at Kalshi's internal market maker) — [Substack](https://ufoholdings.substack.com/p/kalshis-new-liquidity-incentives):
  - LIP could enable "garage-band market makers";
  - intermittent quoting captures only a fraction of snapshots, about 10% of what steady makers earn.
- **Earnings anecdote:** one trader reports $20-80 per week, mostly from Polymarket rewards — [Medium](https://medium.com/mountain-movers/turning-polymarket-and-kalshi-into-a-500-monthly-side-income-to-fund-claude-max-perplexity-max-474ab67244d5). A further claim that about 95% of bid matches come from more than 2,000 smaller makers is a secondary claim, unverified.
- **Self-reported backtest:** an Avellaneda-Stoikov-style market maker claims a 0.7% average return across 49 NCAA markets, with a Sharpe ratio of 0.40 — [wittsmith/kalshi_market_making](https://github.com/wittsmith/kalshi_market_making). A vendor bot with inventory skew and order-book-imbalance signals also exists — [nexosdata](https://github.com/nexosdata/kalshi-market-maker-bot)
- **Vendor guides:**
  - spreads must cover fees *and* adverse selection, and a loss on held inventory can far exceed the spread earned — [BotForKalshi](https://www.botforkalshi.com/blog/kalshi-market-making-strategy);
  - posting both sides is not steady income when one-sided fills overwhelm the spread — [BotForKalshi strategies](https://www.botforkalshi.com/blog/kalshi-trading-strategies-guide);
  - cap inventory per market, skew quotes, pull quotes around news — [Medium](https://medium.com/@zegham.ali/kalshi-trading-bot-automate-arbitrage-crypto-contracts-ai-market-making-8c23ad62e0ea)
- **Academic:** market makers earn twice as much per contract in single-name markets, and one-sided flow predicts maker losses there — [Bartlett, ResearchGate](https://www.researchgate.net/publication/404044013_Adverse_Selection_in_Prediction_Markets_Evidence_from_Kalshi). Makers as a group lost before 2024 — [fatskier note](https://github.com/fatskier/prediction-marks)

### Inferences
- **The units are almost certainly centi-cents.** If `period_reward` were in cents, October's pools alone would be about $868M, which is implausible. In centi-cents, the Sept 21 to Nov 30 total of about $12.5M sits close to a secondary figure surfaced by search (about $13.4M for August-December 2026; page not identified).
- **The agreement tier is out of reach for a small operator; the LIP is open.** The exclusion of agreement holders from the LIP is a structural advantage for small players, since SIG-class firms do not take LIP share. They do still compete for fills.
- **Illustrative economics (speculative).** Take a market with a $14/day pool and two-sided book depth near the 1,000-contract target.
  - Supplying about 10% of the scored size (about 100 contracts per side at the inside) would earn about $1.40/day.
  - That requires about $100 of collateral at mid prices: a 100-contract YES bid at P plus a NO bid at about 1−P.
  - The headline is about 1%/day on capital *before* fill losses.
  - **The catch:** the 0.5-per-tick discount forces you to the inside, which is exactly where informed takers pick you off. Your share falls as others crowd in. Snapshots excluded for thin two-sided depth cut payouts. And pools move with Kalshi's calendar; this week's are election-heavy.
- **Where small-bot market making is most plausible:** series with no maker fee and an active LIP, avoiding news-driven single-name markets unless the subsidy is large. That matches Bartlett's finding that informed price impact is highest there.
- **Rate limits** (see Q5 sources): the Basic tier gives 100 write tokens/s at about 10 tokens per order action, about 10 placements or cancels per second. Advanced, which is self-serve, allows about 30/s. That is enough to quote tens of markets but not to re-quote hundreds on every tick.

### Gaps
- No audited, live, net-of-adverse-selection P&L for any Kalshi LIP or market-making bot was found. The best evidence is small-scale and self-reported.
- The terms of the Market Maker Agreement and Liquidity Provider Program (fee discounts, rebates, uptime) are confidential.
- The October 14, 2026 LIP filing and the `period_reward` unit are not confirmed from an official source.
- The rules for volume programs (who is paid, maker vs taker share) were not documented in anything I could read — [Kalshi changelog](https://docs.kalshi.com/changelog)
- The American Prospect's critique of Kalshi's market-maker arrangements was not retrieved — [American Prospect, Aug 26, 2026](https://prospect.org/2026/08/26/house-always-wins-kalshi-prediction-markets/)

---

## Q4. Does systematically buying favorites, or near-certain contracts near expiry, make money on Kalshi after fees?

### Takeaway
On Kalshi, favorites are on average slightly *under*priced: about +0.5 to +1 point gross at 90-95c in pooled data. But that edge is about the size of the taker fee plus half a 1c spread, and the documented positive returns accrue to *makers* who rest favorite bids, not takers who cross.

Near expiry, both classic evidence and the newest weather-market study suggest the bias shrinks or even reverses:
- markets are well calibrated close to expiry;
- favorites are overpriced in the last hours of Polymarket weather markets;
- there is little size to buy at 97-99c;
- one upset erases about 20 wins at 95c, or about 106 at 99c.

I found no rigorous, out-of-sample, after-fee Kalshi test of "buy at 95c or more near close." The only Kalshi-specific near-close result is a hobby backtest with very few losing trades.

### Cited Findings
- **Favorites in the Kalshi studies:**
  - High-price contracts win more often and "yield small positive returns"; makers buying above 50c show statistically significant positive returns — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5502658); [GWU WP](https://www2.gwu.edu/~forcpgm/2026-001.pdf)
  - Every price above 80c outperformed its odds in Becker's pooled data. 95c contracts won 95.83%. Makers take 43% of NO volume at 99c, a sign the favorite-bid queue is crowded — [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure)
- **Polymarket (not Kalshi):** purchases at or above 90c earned 0.83 cents per dollar — [arXiv 2609.12878](https://arxiv.org/abs/2609.12878). Favorite overpricing grows much stronger in the final 1-12 hours of weather markets (student paper; window not confirmed in every extraction) — [arXiv 2610.13593](https://arxiv.org/abs/2610.13593)
- **Classic:** Intrade markets were reasonably calibrated close to expiration; the bias was a long-horizon, time-discounting phenomenon of 4.7-10.9 points at 0.20/0.80 with more than 100 days to go — [Page & Clemen 2013](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0297.2012.02561.x). Bürgi et al. likewise report that Kalshi accuracy improves as close approaches — [VoxEU](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market)
- **The only Kalshi near-certainty backtest found** (a personal project auditing about 60,000 settled markets) — [leearthur56/kalshi-bot](https://github.com/leearthur56/kalshi-bot):
  - the favorite-longshot edge appears "real," but only on *sustained* quotes, not every 99c blip;
  - it is "tiny" in daily weather markets;
  - "few trade the last cent," so there is little size at 99c;
  - the near-close variant had zero losses, but on a very small number of potential losing trades.
- **Marketing and opinion, not evidence:**
  - "buy Yes at 90-95c" described as a time-decay trade with "5-10% profit per contract" — [Token Metrics](https://tokenmetrics.com/blog/7-prediction-market-strategies/)
  - a 95c price "may" reflect 88-92% (no data) — [FrenzyCapital, Medium](https://medium.com/@FrenzyCapital/trading-strategies-for-prediction-markets-4025a050e2e2)
  - exiting large positions in thin markets moves price against you — [Stokastic](https://www.stokastic.com/articles/prediction-markets/late-swap-skills-prediction-markets)
- **Tail and settlement risk is an active research topic** — [Dai, Jia & Yu, "Settlement Manipulation in Prediction Markets" (arXiv 2606.31675)](https://arxiv.org/pdf/2606.31675)
- **Time value:** whether interest-bearing positions fix the long-horizon problem has been modelled — [arXiv 2602.21091](https://arxiv.org/html/2602.21091). Kalshi runs an "APY" incentive whose terms I did not verify — [BlondiePredicts](https://blondiepredicts.substack.com/p/unpacking-kalshis-incentive-programs)

### Inferences
- **Taker favorite-buying is about break-even at best.**
  - At 95c, a 100-lot taker needs at least 95.34% wins (Q2 table). Pooled trades at 95c won 95.83%.
  - Takers do worse than the pool, and buying at the ask on a 1c-wide book adds about half a cent of cost.
  - Net expectancy is about zero, with a fat left tail.
  - At 99c, Becker's maker/taker split implies takers buying 99c NO win about 98.4%, below the 99.07% break-even. That is negative.
- **Upset arithmetic** (100-lot taker):
  - at 95c a win nets 4.66c and a loss costs 95.34c, so one upset cancels about 20.5 wins;
  - at 99c a win nets 0.93c, so one upset cancels about 106 wins;
  - with cent rounding on 1-lots at 99c, a win nets 0c, so the strategy cannot win.
- **Statistical power is the binding constraint for any test.** Detecting a +0.5 point edge at 95c with about 2 standard errors needs roughly 7,600 independent settled bets (variance 0.95 × 0.05). A +0.3 point edge at 99c needs about 4,400. Strikes in the same event are correlated, so the real requirement is higher. A one-week paper run cannot validate this.
- **Why near-expiry favorites may not be cheap:**
  - Close to settlement, the lottery-ticket demand that creates the favorite-longshot bias fades, and the time-value cost behind Page and Clemen's long-horizon bias disappears.
  - The remaining flow includes informed late traders watching the live game, temperature sensor or data release.
  - A resting 97c bid gets filled precisely when the outcome becomes doubtful: adverse selection.
  - Qiu and Qiu's late-hours favorite *over*pricing in weather is consistent with this, though it is a Polymarket student paper.
- **Long-dated favorites are the more interesting variant (speculative).**
  - Page and Clemen's large long-horizon bias is compensation for locking up capital.
  - Kalshi has made several long-dated political and annual series fee-free (multiplier 0).
  - If Kalshi's APY applies to position collateral, which I could not verify, holding long-dated favorites costs less than the classic explanation assumes.
  - That could make long-horizon favorite-buying more exploitable on Kalshi than it was on Intrade. Untested.

### Gaps
- No Kalshi calibration by hours-to-close was found (e.g. win rate of 95-99c contracts at T−60m, T−10m, T−1m), split by maker and taker and by category.
- No Kalshi upset frequencies at 97-99c by category were found.
- The terms of Kalshi's APY on open positions are unverified.
- The 15-minute crypto near-expiry research repo publishes "weekly results" that I did not retrieve — [Kalshibot98/kalshi15](https://github.com/Kalshibot98/kalshi15)

---

## Q5. How does resting a limit order (maker) instead of crossing (taker) change the economics, and why are paper fills for resting orders usually too optimistic?

### Takeaway
**What resting changes.** A taker pays half the spread plus the full taker fee. A maker instead earns half the spread, pays no fee (or a quarter-size fee in the 160 listed series), and may collect LIP rewards. In Kalshi data that switch is the biggest single determinant of returns: since 2024 makers beat takers at most price levels.

**The catch.** A maker's return is conditional on being filled, and fills are adversely selected.

**Why paper tests mislead.** A simulation that sees only top-of-book quotes cannot see:
- your place in the queue;
- whether the touch would have filled you;
- the fact that fills arrive disproportionately just before the price moves against you.

So it systematically overstates both how often you fill and how good those fills are.

### Cited Findings
- **Kalshi charges fees only on orders that immediately match.** Resting orders pay only in listed maker-fee series — [Kalshi fee schedule PDF](https://kalshi.com/docs/kalshi-fee-schedule.pdf). At 50c that is 0.44c (maker) versus 1.75c (taker) — [DefiRate](https://defirate.com/prediction-markets/fees/)
- **Makers outperform takers on Kalshi:**
  - at most price levels — [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure)
  - on average returns — [VoxEU](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market)
  - but makers *lost* in 2021-2023, before the books deepened — [fatskier note](https://github.com/fatskier/prediction-marks)
- **Adverse selection:** one-sided order flow predicts maker losses in single-name markets — [Bartlett](https://www.researchgate.net/publication/404044013_Adverse_Selection_in_Prediction_Markets_Evidence_from_Kalshi). Realized spread in major sports was below the maker fee — [geniuswang05](https://github.com/geniuswang05/kalshi_alpha_search). Fills alone lose and rewards carry the bot — [JosephWong333](https://github.com/JosephWong333/prediction-market-bots)
- **Practitioner framing:** the take-or-post decision is a trade-off between fees and adverse selection. The author runs Kalshinomics.com, which may earn Kalshi referral fees — [Courtney, Whirligig Bear](https://whirligigbear.substack.com/p/makertaker-math-on-kalshi)
- **Queue position is observable only for your own live resting orders.**
  - Endpoints: `GET /portfolio/orders/{order_id}/queue_position` and `GET /portfolio/orders/queue_positions`.
  - They return the contracts ahead of you (0-indexed) under price-time priority.
  - Sources: [Kalshi API changelog](https://docs.kalshi.com/changelog); [kalshi-typescript SDK](https://app.unpkg.com/kalshi-typescript@3.11.0/files/dist/api/orders-api.d.ts)
- **Order controls:**
  - a `post_only` option exists for quotes, and crossing with it repeatedly can trigger temporary rate limiting — [Kalshi changelog](https://docs.kalshi.com/changelog)
  - order groups, amends and cancels share the write bucket — [Predictefy rate limits](https://blog.predictefy.com/kalshi-api-rate-limits)
- **Rate limits** ([Predictefy](https://blog.predictefy.com/kalshi-api-rate-limits); [DEV Community](https://dev.to/deskbot_store/kalshi-api-rate-limits-and-websockets-a-bot-builders-guide-4kj5)):
  - token buckets; Basic is 200 read and 100 write tokens per second, Advanced 300/300 via a self-serve upgrade;
  - figures for higher tiers conflict between sources;
  - most requests cost 10 tokens, and each order in a batch counts separately.
- **Backtests:** an edge that exists only on settled history may not survive live markets — [Depthfeed](https://depthfeed.com/resources/how-to-backtest-prediction-markets). For the theory of inventory risk in market making, see [Guéant, Lehalle & Fernandez-Tapia (arXiv 1105.3115)](https://arxiv.org/pdf/1105.3115)

### Inferences
- **Why top-of-book paper fills are too optimistic:**
  1. **Queue.** The quote shows the price and perhaps size, not your place in line. Price-time priority means incumbents at the same price fill first.
  2. **Touch is not fill.** The price trading *at* your level does not mean you would have been filled.
  3. **Conditional fills.** Back-of-queue orders fill mainly on large sweeps, which are disproportionately informed. The aggregate maker returns in Becker and Bürgi et al. are earned by incumbents at the front of the queue, not by a newcomer behind them.
  4. **Your own impact.** Your size changes others' quoting and your LIP share.
  5. **Latency.** Cancels lag news.
  6. **Fee rounding** on small fills.
- **The direction of the bias is known; the size is not.** Paper maker P&L is an upper bound.
- **A more honest testing protocol:**
  - record full-depth order-book deltas from the WebSocket, not just top-of-book;
  - assume you join the *back* of the queue at your price and count a fill only once traded volume at that price exceeds the displayed size ahead of you, or only on a print through your price;
  - measure post-fill markouts (mid at +1 minute, +5 minutes and at settlement) to quantify adverse selection;
  - calibrate the fill model with a tiny live pilot that reads the queue-position endpoint;
  - estimate LIP rewards separately from full-depth 1-second snapshots using the published formula (lip-ledger shows reconstruction within about 3%).
- **With top-of-book quotes only:**
  - taker strategies can be paper-tested reasonably honestly: fill at the displayed ask for at most the displayed size, with exact fee and rounding;
  - maker strategies cannot. The paper result is an optimistic bound, and the realistic number could have the opposite sign.

### Gaps
- No Kalshi-specific measurement of the gap between paper and live fills was found.
- Fill probability as a function of queue position on Kalshi is undocumented.
- It is unclear whether `post_only` is available on standard orders, not just RFQ quotes. I saw only the quote-flow changelog entry.

---

## Q6 (overall). Which structural strategies have a real, durable edge on Kalshi after fees? Strategy scorecard

### Takeaway
Ranked by evidence of a real, durable after-fee edge for a small automated trader as of November 2026:

| Rank | Strategy | Confidence |
|---|---|---|
| 1 | Two-sided quoting in liquidity-incentive markets with no maker fee | about 40% |
| 2 | Maker-side "selling the longshot": resting 90-99c NO bids (or 1-10c YES asks), held to settlement | about 35% |
| 3 | Unsubsidized spread capture (classic market making) | about 15% |
| 4 | Near-expiry buying at 95c or more | about 10% as taker, about 20% as maker |
| 5 | Taker favorite-buying at any horizon | about 10% |
| — | Long-dated favorites in fee-free series (speculative) | about 20% |
| — | Taker longshot-buying, the flow everyone else harvests | about 1% |

The common thread is that the money comes from recreational YES and longshot takers and from Kalshi's own subsidies. It does not come from out-forecasting the market, and it accrues to whoever *rests* orders.

### Cited Findings
- Takers are the losers and makers the winners on Kalshi since 2024 — [jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure); [VoxEU](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market); [fatskier](https://github.com/fatskier/prediction-marks)
- YES overbetting subsidizes makers; single-name markets pay makers twice as much per contract despite more informed flow — [Bartlett](https://www.researchgate.net/publication/404044013_Adverse_Selection_in_Prediction_Markets_Evidence_from_Kalshi)
- The liquidity subsidy was the only edge that held up in one independent search — [geniuswang05](https://github.com/geniuswang05/kalshi_alpha_search)
- Live LIP scale: about 4,385 markets accruing about $92k/day on 2026-11-03; 160 maker-fee series — [Kalshi API /incentive_programs](https://api.elections.kalshi.com/trade-api/v2/incentive_programs); [Kalshi API /series](https://api.elections.kalshi.com/trade-api/v2/series)
- Near-expiry calibration is good on Intrade, and favorites are overpriced late in Polymarket weather markets — [Page & Clemen](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0297.2012.02561.x); [arXiv 2610.13593](https://arxiv.org/abs/2610.13593)
- The bias is weakening over time — [GWU WP](https://www2.gwu.edu/~forcpgm/2026-001.pdf)

### Inferences (strategy cards; the confidence scores are my own judgment)

**1. LIP-subsidized two-sided quoting (series with no maker fee and an active pool). Confidence about 40%.**
- **What it is:** rest bids on YES and NO near the inside, sized toward each market's 1,000-contract target, in markets listed by `/incentive_programs`. Collect the pro-rata reward and manage the inventory that fills create.
- **Mechanism:** Kalshi pays for displayed two-sided depth, about $92k/day across about 4,400 markets now. On top of that comes the maker's normal advantage against recreational takers. Agreement holders are excluded, which thins the competition for the reward.
- **Evidence:**
  - Kalshi's published pools (primary data);
  - lip-ledger's payout reconstruction (a $4-$16 scale);
  - geniuswang05's conclusion that this is the only edge that held up;
  - a reward bot reporting that rewards carry losing fills;
  - no audited net P&L.
- **Is the logic sound?** Yes for the reward, which is cash from the exchange. The open question is whether fill losses in thin, news-driven markets exceed it.
- **Needs:**
  - authenticated API key, Advanced rate tier, WebSocket full-depth book, queue-position endpoint, order groups or inventory caps;
  - about $100 of collateral per 100-contract two-sided pair per market;
  - 24/7 uptime, which matters more than latency given 1-second scoring;
  - fast cancel-on-news logic.
- **Paper-testable?** Reward side: only with full-depth snapshots, not top-of-book. Fill side: no. A tiny live pilot is needed.
- **Durability:** a discretionary marketing subsidy. Kalshi has amended it at least three times in 2026 (Feb, Jul and reportedly Oct filings), and it will be competed down.

**2. Maker "longshot selling" (rest NO bids at 90-99c, or YES asks at 1-10c), hold to settlement. Confidence about 35%.**
- **Mechanism:** you are the counterparty to the optimism tax. Becker's 1c takers won 0.43% against 1% implied, which puts the 99c-NO maker at about +0.57 points gross. Makers buying above 50c show significant positive returns (Bürgi et al.).
- **Evidence:** the two large Kalshi datasets (2021-2025), gross of fees. Maker fee at 99c is about 0.017c where charged and zero elsewhere. On Polymarket the result is grouping-dependent.
- **Is the logic sound?** Yes, on behavior that has persisted since 1949. But the measured returns belong to incumbents at the front of the queue, makers already take 43% of 99c NO volume, and outcomes within an event ladder are correlated.
- **Needs:**
  - resting good-till-cancelled limit orders; capital-heavy (99c tied up to earn under 1c, so annualized return depends on time to settlement);
  - per-event exposure caps;
  - cancel-on-news logic;
  - order sizes large enough to neutralize fee rounding.
- **Paper-testable?** Poorly. Use the trade-through-only fill rule plus markouts. A taker version is a pessimistic lower bound.
- **Durability:** a moderate behavioral source, eroding with maker competition and the spread of maker fees.

**3. Unsubsidized spread capture. Confidence about 15%.**
- **Mechanism:** earn the bid-ask spread.
- **Evidence against a small bot:**
  - realized spread below the maker fee in major sports (geniuswang05);
  - SIG-class incumbents;
  - maker fees on the 160 deepest series;
  - adverse selection concentrated in single-name markets (Bartlett);
  - only weak self-reported backtests (0.7% across 49 NCAA markets).
- **Needs:** everything in card 1 plus faster re-quoting.
- **Paper-testable?** Essentially no.

**4. Near-expiry buying at 95c or more. Confidence about 10% as taker, about 20% as maker.**
- **Mechanism:** the claim is that lottery-driven underpricing of favorites persists into the final minutes.
- **Evidence against:**
  - calibration is good near expiry (Page and Clemen; Bürgi et al.);
  - favorites were *over*priced in the last 1-12 hours of Polymarket weather markets (student paper);
  - the only Kalshi backtest has a tiny loss sample and finds little size at 99c;
  - the taker fee is about 7% of maximum profit;
  - one upset cancels 20-106 wins.
- **Who is on the other side late:** often better-informed live watchers, so fills are adversely selected.
- **Needs:** close-time awareness, a live event or data feed to avoid being last to know, and order sizes of at least tens of contracts.
- **Paper-testable?** The taker version, partly: use the displayed ask and size at fixed T−X snapshots with exact fees. But a valid test needs about 4,000-8,000 independent settled bets.

**5. Taker favorite-buying (any horizon). Confidence about 10%.**
- **Evidence:** the pooled edge of about +0.8 points at 95c is roughly consumed by fee plus spread. Takers lose at 80 of 99 price levels. At 99c the implied taker result is negative.
- **Paper-testable?** Mechanically honest, statistically weak.

**Variant: long-dated favorites in fee-free series. Confidence about 20%, speculative.**
- **Mechanism:** Page and Clemen's long-horizon bias of 4.7-10.9 points is time-value compensation. Kalshi's fee-free long-dated series, and possibly APY on collateral, may lower that cost.
- **Evidence:** no Kalshi-specific test.
- **Paper-testable?** Only over months to settlement.

**Anti-strategy: taker longshot-buying below 10c. Confidence about 1%.** Buyers of contracts under 10c lose more than 60% on Kalshi (Bürgi et al.). This is the flow that strategies 1 and 2 harvest.

### Gaps
- The scores rest on studies whose full tables I could not read.
- None of the maker-side results is net of the queue disadvantage a newcomer faces.
- No audited live track record exists for any of these strategies on Kalshi.
- The most useful next step is the project's own data: Kalshi candlesticks and trades for settled markets, used to measure win rate by price, time-to-close and category, plus a tiny live maker pilot reading the queue-position endpoint.
