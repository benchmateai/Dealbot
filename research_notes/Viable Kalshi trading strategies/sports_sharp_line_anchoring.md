# Sports-contract trading on Kalshi: sharp-line anchoring and related sports strategies (status as of 2026-11-03)

*Source caveat: kalshi.com, docs.kalshi.com, help.kalshi.com, arxiv.org, SSRN, karlwhelan.com, ucd.ie, datagolf.com, the-odds-api.com, oddspapi.io and smartstake.app were all blocked in this research session. Anything from those hosts comes from search-engine summaries of the page, not a direct read, and is marked "(via search summary)". GitHub pages were read directly. Every return, P&L or edge figure below is an unverified claim unless it is marked otherwise.*

## Q1. What sports markets does Kalshi list in 2026, how liquid are they, and what fees apply?

### Takeaway
By late 2026 Kalshi lists game winners, spreads, totals, player props, futures, "Combos" (same-game-parlay-style bundles) and live in-game trading across 17+ sports. Sports are most of its volume: about $9.9B in March 2026 alone, and $58B+ in June–July 2026 around the World Cup. Liquidity is concentrated in headline game markets and thins sharply in-game and in props. Professional market makers quote the books, Susquehanna (SIG) among them.

The taker fee is 0.07 × C × P × (1−P), rounded up to the cent. That is 1.75¢ per contract at 50¢, a 1.75-percentage-point hurdle. A quarter-rate maker fee (0.0175) applies on a growing list of series, NFL and NBA games among them. Some series, such as MLB games according to one repo, reportedly carry a 0.5 multiplier.

### Cited Findings
**Market menu (2026)**
- Kalshi covers NFL, NBA, MLB, NHL, college sports, soccer, golf, UFC and tennis, plus player props. One guide counts "17+ sports" ([SI – Kalshi NFL](https://www.si.com/prediction-markets/reviews/kalshi-nfl); [Sharp Football Analysis review, Oct 2026](https://www.sharpfootballanalysis.com/prediction-markets/kalshi/)) (via search summary).
- Individual NFL matchups list game winners, point spreads and game totals ([SI – Kalshi NFL](https://www.si.com/prediction-markets/reviews/kalshi-nfl)).
- Player props are yes/no contracts on a player reaching a threshold. Coverage centers on star NFL and NBA players, and one review says the deep alt-line and role-player catalog "still lives at sportsbooks" ([SI – Kalshi NBA](https://www.si.com/prediction-markets/reviews/kalshi-nba); [OddsShopper – Kalshi player props](https://www.oddsshopper.com/articles/prediction-markets/kalshi-player-props)). Kalshi confirmed new player-prop markets in Sept 2025 ([Casino.com, Sept 2025](https://www.casino.com/news/sports-betting/kalshi-confirms-impending-launch-of-new-player-prop-markets/)) (older fact).
- Kalshi offers "Combos" (multi-leg bundles, including same-game prop + game-line combos), not traditional parlays ([SI – combos](https://www.si.com/prediction-markets/usa/combos); [TheLines – Kalshi parlay guide](https://www.thelines.com/prediction-markets/kalshi/parlay/)).
- Live in-game contracts exist, with in-game trading growing since 2025 ([Sportico, 2025](https://www.sportico.com/business/sports-betting/2025/kalshi-in-game-futures-trading-sportsbooks-1234828105/)). One 2026 review calls in-play markets "not nearly as deep" as sportsbooks' ([SI – Kalshi NBA](https://www.si.com/prediction-markets/reviews/kalshi-nba)) (via search summary).
- Sports-"mention" markets (broadcast mentions) were made "temporarily unavailable" amid a federal investigation ([Yahoo Sports](https://sports.yahoo.com/articles/sports-mention-markets-temporarily-unavailable-213029978.html)) (headline only; date not confirmed).

**Volume and liquidity**
- Monthly notional volume grew about 80x, from about $180M in early 2025 to $14.4B in March 2026, with sports at 68% ([Blockworks report](https://app.blockworks.com/report/from-betting-to-trading-how-kalshi-is-reshaping-sports-markets); [KuCoin summary](https://www.kucoin.com/news/flash/kalshi-s-sports-prediction-market-volume-surges-80x-in-one-year)). Blockworks puts Kalshi sports volume at $9.9B in March 2026 and Kalshi's share of sports prediction-market volume at about 70% (via search summary).
- Pew says sports trading topped $58B on Kalshi in June–July 2026, during the World Cup ([Pew Research, 2026-09-23](https://www.pewresearch.org/short-reads/2026/09/23/prediction-markets-trading-volume-doubled-between-may-and-july-largely-driven-by-sports/)). DeFiRate's tracker shows $345.0B of total Kalshi volume for 2026 through Nov 2 ([DeFiRate](https://defirate.com/prediction-markets/volume/kalshi/)).
- Estimates of sports' share run from 68% to over 90% depending on period and method ([iGaming Chronicle](https://igamingchronicle.com/kalshis-40bn-bet-depends-on-turning-sports-wagers-into-a-financial-exchange); [Blockworks](https://app.blockworks.com/report/from-betting-to-trading-how-kalshi-is-reshaping-sports-markets)).
- In-game order-book depth on Kalshi drops about 76% compared with pre-game, even though trading activity rises (Blockworks report via [X repost](https://x.com/Kunallegendd/status/2044780671839952949)) (via search summary).
- A vendor blog claims a single large buy can move a live Kalshi YES price 3–5¢, with no data shown ([ClawArbs – live arbitrage](https://clawarbs.com/blog/live-in-play-arbitrage-betting/)) (unverified).
- Combos are the recreational-flow sink. Kalshi combo takers' losses reportedly topped $1B, combo market makers' profit after fees was $519.8M, and Kalshi collected $88.9M in combo maker fees ([InGame](https://www.ingame.com/kalshi-parlay-taker-losses-top-1b/)) (via search summary; unverified).

**Who quotes**
- Susquehanna (SIG) became Kalshi's first official market maker, with reduced fees and higher position limits in exchange for liquidity ([Tradermath](https://www.tradermath.org/articles/prediction-markets-trading-at-quant-firms)). Part of Kalshi's volume is SIG's own trading ([Closing Line Substack](https://closingline.substack.com/p/the-takeaway-kalshi-hits-2b-in-sports)). (The SIG designation dates to 2024; this is an older fact.)
- ESPN reports that Kalshi fees are usually cheaper than sportsbook vig, and that this draws professional bettors and market makers who are "compensated to promote liquidity" ([ESPN, 2025](https://www.espn.com/espn/betting/story/_/id/45377686/kalshi-prediction-markets-disrupt-sports-betting)).
- Bloomberg reported in Feb 2026 that pro gamblers are moving to Kalshi and Polymarket. Pro bettor Rufus Peabody (Unabated co-founder) began trading heavily on Kalshi "in September" and said "there's a lot of alpha to be had on the prediction markets" ([Bloomberg, 2026-02-05](https://www.bloomberg.com/news/articles/2026-02-05/super-bowl-lx-is-bringing-professional-gamblers-to-prediction-markets)) (via search summary).
- Kalshi runs a Liquidity Incentive Program (LIP) that pays resting orders which improve prices, even when they don't fill. Rewards run $10–$1,000 per day per market. Members with a Market Maker Agreement and Kalshi affiliates are excluded. A July 2026 CFTC filing extended the program to all markets, and sources disagree on its end date ([CFTC filing, 2026-07-15](https://www.cftc.gov/filings/orgrules/rules07152610358.pdf); [GamingAmerica](https://gamingamerica.com/news/1006858/kalshi-launches-prediction-market-rebate-program-for-sports-event-contracts)) (via search summary).
- Under the Sports Prop Combo LIP, 25% of the fees from combos that contain a prop are paid to market makers in that prop's component leg. Payouts are monthly trading credits, the program runs to Jan 1 of next year, and only prop legs count, not winners, spreads or totals ([Kalshi help center](https://help.kalshi.com/en/articles/17184676-sports-prop-combo-market-component-legs-liquidity-incentive-program); [Kalshi CFTC notice, 2026-09-02](https://kalshi-public-docs.s3.amazonaws.com/regulatory/notices/Sports%20Prop%20Combo%20Market%20Component%20Legs%20Liquidity%20Incentive%20Program%20(Modification)%20(2).pdf); [NextPredict](https://nextpredict.io/market-news/industry/kalshi-files-prop-market-liquidity-incentives/)) (via search summary).

**Fees**
- Taker fee = 0.07 × contracts × price × (1 − price), rounded up. It peaks at 50¢, at $1.75 per 100 contracts ([QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained); [BettingUSA](https://www.bettingusa.com/prediction-markets/reviews/kalshi/fees/)) (third-party; the official PDF was blocked).
- Maker fee = 0.0175 × C × P × (1−P), a quarter of the taker rate, charged only on series that list maker fees and only when the resting order fills. As of Oct 10, 2026, the non-standard list reportedly included NFL and NBA game series, with 157 series carrying non-standard fees ([QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained)). A Nov 1, 2026 analysis counted 107 of 4,076 sports series with maker fees (via search summary; the counts conflict).
- Maker fees began in May 2025 as per-series surcharges. Across five schedule revisions, coverage rose from 8.0% to 14.4% of markets but from 61% to 66% of volume. In other words, the busiest series carry maker fees ([Vladosyna replication repo](https://github.com/Vladosyna/kalshi-makers-takers-persistence)) (read directly).
- Series fee multipliers exist. One open-source repo models a 0.5 multiplier for MLB game markets ([VV1Git/sportstrades](https://github.com/VV1Git/sportstrades)) (read directly), and another source says 24 series carry half or zero multipliers (via search summary; unverified).
- Combos: maker fees are 50% of the taker fee, except combos created after 11:59 PM ET on Aug 19, 2026 that are made entirely of independent NFL legs, which pay no maker fee ([Kalshi API changelog](https://docs.kalshi.com/changelog); [QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained)). Sources disagree on whether the Aug 2026 change took effect at 11:59 PM ET Aug 19 or 5:00 AM ET Aug 20 ([Tech-Insider](https://tech-insider.org/prediction-markets/how-does-kalshi-payout-work/)) (via search summary).
- Rounding bites on small or longshot fills. In June 2025 Peabody reported a flat 0.25%-per-contract maker fee on certain big events. He paid an average of 12.52% in fees on $1,000 matched at 2¢ on a golf longshot, up to 50% on individual fills, and $1,792.46 in fees in one week while market making ([Rufus Peabody on X, June 2025](https://x.com/RufusPeabody/status/1934732860352811388)) (older fact; the fee design may have changed since).

**API**
- Kalshi uses token-bucket rate limits by tier. Per the official docs (snippet about 132 days old): Basic 200 read / 100 write tokens per second, Advanced 300/300, Premier 1,200/1,200, Prime 4,800/4,800. Most requests cost 10 tokens, so Basic is roughly 20 reads and 10 writes per second. WebSocket connection caps are 200/200/500/1,000 ([Kalshi docs – rate limits](https://docs.kalshi.com/getting_started/rate_limits); [Predictefy](https://blog.predictefy.com/kalshi-api-rate-limits)) (via search summary). Third-party guides cite different numbers, and `GET /account/limits` returns your live limits.

**Jurisdiction (US trader)**
- On 2026-09-25 the Sixth Circuit ruled that Kalshi sports contracts are not swaps and that the CEA does not preempt state gambling law. That deepens a split with the Third Circuit, which ruled for Kalshi against New Jersey in April 2026 ([CNBC](https://www.cnbc.com/2026/09/25/appeals-court-rules-states-can-regulate-sports-prediction-markets.html); [NatLawReview](https://natlawreview.com/article/sixth-circuit-deepens-circuit-split-kalshi-sports-event-contracts-are-not-swaps-and)).
- A search summary of state-status coverage says the Ninth Circuit sided with Nevada on Aug 28 (presumably 2026; I couldn't pin it to a specific article). One outlet lists sports contracts as blocked in MA, NV, WA and MI, but Massachusetts status conflicts across sources ([CBS Sports state tracker](https://www.cbssports.com/prediction/news/prediction-market-legal-states/); [Startup Fortune](https://startupfortune.com/utah-files-criminal-charges-against-kalshi-and-its-two-co-founders/); [Yogonet](https://www.yogonet.com/international/news/2026/09/28/126603-us-court-rules-states-can-regulate-kalshi-sports-contracts)) (via search summary). One headline reports Utah criminal charges against Kalshi and its co-founders (headline only; unverified).

### Inferences
- **Fee hurdle by price, from the cited formula.** All figures are before per-order rounding.

  | Price | Taker fee / contract | Taker fee as % of cost (=7%×(1−p)) | Maker fee (0.0175) | Taker fee at 0.5 multiplier |
  |---|---|---|---|---|
  | 5¢ / 95¢ | 0.33¢ | 6.65% / 0.35% | 0.08¢ | 0.17¢ |
  | 10¢ / 90¢ | 0.63¢ | 6.3% / 0.7% | 0.16¢ | 0.32¢ |
  | 20¢ / 80¢ | 1.12¢ | 5.6% / 1.4% | 0.28¢ | 0.56¢ |
  | 30¢ / 70¢ | 1.47¢ | 4.9% / 2.1% | 0.37¢ | 0.74¢ |
  | 50¢ | 1.75¢ | 3.5% | 0.44¢ | 0.875¢ |

  A taker buying at ask *a* needs de-vigged fair *q* > *a* + 0.07·*a*·(1−*a*), plus a buffer for de-vig model error. Near 50¢ that is about 1.75 pp of probability, or about 0.9 pp in a half-multiplier series.
- Rounding up per order punishes small tickets. One contract at 50¢ pays 2¢ (4% of cost), and one at 10¢ pays 1¢ (10% of cost). Bots should send fewer, larger orders.
- With maker fees on about two-thirds of volume and the LIP excluding official market makers, the maker side carries a 0.44¢ fee at 50¢. That is still roughly a quarter of the taker cost, so the structural advantage stays with resting liquidity.
- Every edge in this file is gated by state availability. A US trader must check their own state, and the circuit split makes access a live risk rather than a settled question.

### Gaps
- I couldn't read Kalshi's official fee schedule PDF or the non-standard fee table (blocked host). The exact list of sports series with maker fees or multipliers, including whether MLB, NHL, college and soccer game series sit at 0.5x, is unverified.
- I found no per-market depth statistics: typical top-of-book size and spread for an NFL or NBA game, props or futures. Only aggregate volume and Blockworks' in-game depth figure were available.
- I found no current position-limit numbers for non-market-maker accounts, and no confirmation of whether Kalshi pays interest on collateral or positions in 2026. Both matter for capital-heavy futures strategies.
- I didn't verify which firms besides SIG quote Kalshi sports, or whether Kalshi has an in-house or affiliated trading arm.

## Q2. Do Kalshi sports prices lag or deviate from sharp sportsbook lines, by how much, and for how long?

### Takeaway
The best available evidence is vendor or industry analysis, not peer-reviewed, and none of it is a timestamped lead-lag study against Pinnacle. It says Kalshi's main pre-game markets sit within about 0.5–0.75 pp of de-vigged sharp prices on median, which is below the 1.75 pp taker fee at 50¢. In-game prices move in near lockstep with sportsbooks at 5-minute resolution but carry wider gaps of about 2.25% median versus FanDuel. Measured in-game gaps last about 6 seconds in one open-source scanner. Claims of 30–90-second lags come from tool vendors and are unverified. One vendor even claims Kalshi is the sharpest book on MLB player props.

### Cited Findings
- **Closeness to Pinnacle, pre-game:** An OddsPapi analysis of 88 fixtures found de-vigged median absolute gaps to Pinnacle of 0.59 pp for Polymarket, 0.75 pp for Kalshi and 0.83 pp for bet365. Prediction markets quoted winner markets at roughly a quarter of Pinnacle's overround on NFL, MMA and baseball ([OddsPapi](https://oddspapi.io/blog/polymarket-api-kalshi-api-vs-sportsbooks-the-developers-guide/)) (via search summary). OddsPapi is a data vendor, and its dates and price basis (mid or ask) are unknown.
- **Pre-game versus FanDuel:** Blockworks found an average pre-game difference of 0.54% between Kalshi and FanDuel in one featured game and 1.40% in a Bills–Broncos playoff game. It also says that two days before kickoff, Kalshi prices are "a strong predictor of outcomes" ([Blockworks](https://app.blockworks.com/report/from-betting-to-trading-how-kalshi-is-reshaping-sports-markets); [X repost](https://x.com/Kunallegendd/status/2044780671839952949)) (via search summary; the report appears to date from spring 2026).
- **In-game:** Once games started, Kalshi and FanDuel correlated at 0.9962, and at 0.9738 in the second game, with "no meaningful lead or lag at 5-minute resolution". The median in-game price gap was 2.25%, which the authors attribute largely to structural differences ([Blockworks via X repost](https://x.com/Kunallegendd/status/2044780671839952949)) (via search summary).
- **Open-source scanner, paper-only, scans from 2026-09-06:** Across 266 games live on both Kalshi and Polymarket, best bid and ask were "usually within one cent". No liquid game showed a gap large enough to clear an estimated 5–7% round-trip fee load for cross-venue hedges. Gaps between Vegas lines (ESPN/DraftKings) and prediction markets were 1–4 points, with inconsistent direction, and mostly within the sportsbook's vig. In-game pricing gaps "last about six seconds" ([VV1Git/sportstrades](https://github.com/VV1Git/sportstrades)) (read directly).
- **Lag claims, low quality:** ClawArbs says Pinnacle reprices "within milliseconds" while prediction markets show a stale price for 30–90 seconds ([ClawArbs – value betting](https://clawarbs.com/blog/kalshi-value-betting/); [ClawArbs – prediction markets](https://clawarbs.com/prediction-markets/)) (vendor marketing, no data).
- **Other vendor estimates of the opportunity window** range from 30–200 seconds ([Arbitrage Agent](https://arbitrage-agent.com/blog/do-you-need-vps-prediction-market-arbitrage)) to 2–15 seconds ([ClawArbs](https://clawarbs.com/blog/live-in-play-arbitrage-betting/)) to "well under a second" in liquid Kalshi markets ([TradoxVPS](https://tradoxvps.com/why-kalshi-traders-need-a-1ms-vps-in-chicago/)). Each vendor sells infrastructure that fits its own estimate.
- **Contrary claim:** SmartStake reports that a study of over 600 million MLB player-prop line movements found Kalshi posting the sharpest prices, ahead of the books it tracked including Pinnacle ([SmartStake](https://www.smartstake.app/learn/kalshi-vs-sportsbook)) (via search summary; vendor study, methodology unread).
- **In-play stale quotes:** A trader's blog says quotes can lag game state between plays, in timeouts and during commercial breaks, and calls these the "cleanest entries" ([PillarLab](https://pillarlabai.com/blog/trading-sports-contracts-kalshi-live-inplay/)) (anecdotal).
- **De-vig matters for measurement:** ClawArbs notes that comparing raw Pinnacle implied probability with Kalshi, without removing the vig, can show zero edge when a real gap of about 1% exists ([ClawArbs – devig](https://clawarbs.com/blog/devig-prediction-markets/)). The choice of de-vig method also matters: the power method may over-adjust longshots and under-adjust mid-range odds ([Pinnacle Odds Dropper](https://www.pinnacleoddsdropper.com/guides/how-to-devig-pinnacle-s-odds-for-betting-on-soft-books)).
- **Academic (all categories, not sports-specific):** Kalshi prices are informative, grow more accurate as markets near close, and show a favorite–longshot bias ([Bürgi, Deng & Whelan, UCD WP 2025](https://www.ucd.ie/economics/t4media/WP2025_19.pdf); [CEPR/VoxEU](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market)) (via search summary).
- **Measurement tools that exist:** An Apify/MCP connector lists Pinnacle no-vig fair odds against live Kalshi and Polymarket sports prices, with edge after fees, across 19 leagues ([mcpservers.org](https://mcpservers.org/servers/apify-com-sharplinelabs-polymarket-kalshi-odds-mcp); [Glama](https://glama.ai/mcp/connectors/io.github.mirowbek-droid/polymarket-kalshi-odds)). I found no published hit rates from it.

### Inferences
- Main Kalshi game markets behave like a sharp, market-maker-quoted exchange, not a slow "soft book". A median deviation of about 0.75 pp, probably measured on mid prices, is roughly half the taker fee at 50¢. Only the tail of the deviation distribution is tradeable, and that tail likely falls in fast-news moments, when the displayed ask is exactly the quote a faster market maker is about to pull.
- Blockworks' "no lead or lag at 5-minute resolution" can't rule out 10–90-second lags, because the sampling is too coarse. The roughly 6-second in-game gaps in sportstrades fit a regime where market makers update within seconds. Either way, in-game edges belong to whoever has the fastest data.
- The 2.25% median in-game gap against FanDuel is mostly FanDuel's own vig and live-pricing margin, not Kalshi mispricing. FanDuel isn't a sharp reference.
- If SmartStake's MLB-prop result holds, anchoring to Pinnacle on props may run backwards: Kalshi could be the price-setter there. Prop anchoring should first test which venue leads.

### Gaps
- I found no peer-reviewed or independently replicated timestamped (second-level) lead-lag study of Kalshi sports against Pinnacle, Circa or Betfair, pre-game or in-game.
- Not established: whether gaps are larger in early-week openers, overnight, low-tier leagues (WNBA, NCAA small schools, minor soccer), totals or spreads versus moneylines, or around injury and lineup news. No source quantified any of this.
- I couldn't read the OddsPapi and SmartStake methodologies (blocked hosts). I also couldn't open Kalshi's own calibration paper, whose search snippet says sports markets' close times "often lag the game's actual end" ([Kalshi research PDF](https://kalshi.com/research/kalshi-research-calibration.pdf)). That may matter for late-game and settlement-timing trades but couldn't be checked.

## Q3. What do practitioners and open-source bots report about trading Kalshi or Polymarket sports against Pinnacle or consensus lines, and what limits them?

### Takeaway
The few concrete practitioner reports point the same way. Simple de-vig-and-take scanners find little after fees in liquid games. The one bot with public P&L ran on Polymarket, made money as a market maker that hedged, not as a taker, lost money on its unhedged "+EV" leftovers, and was retired because it got "too slow". The binding limits are fresh sharp data, latency against professional market makers, thin depth outside headline markets, and fees. Since Pinnacle closed its public API in July 2025, getting sharp data costs real money and carries legal grey areas for US traders.

### Cited Findings
**Bots and write-ups**
- **kachence/polymm** (Polymarket, early 2026, read directly) de-vigs bookmaker odds from the-odds-api, quotes a cent above the best bid where edge against fair is at least 5% (`min_edge`), then hedges the other outcome after a fill. Claimed results: about $5k net, made up of +$8,293 on the arbitrage leg and −$3,184 on "forced directional residual" positions entered at 7%+ edge. The author says it "got too slow to defend its edge" and that "the code was never the hard part… the edge was fresh odds and speed". A private scraping pipeline, "half the edge", isn't released, and a Rust rewrite is in use ([GitHub – kachence/polymm](https://github.com/kachence/polymm)) (unverified P&L; wallet @b00k13 is claimed public). Polymarket's international venue may not be open to US persons, so check venue access.
- **VV1Git/sportstrades** (paper-only, Kalshi vs Polymarket vs sportsbook) found no liquid-game arbitrage worth taking. Its best finds were a $0.23 hedge (0.9%) in a thin book and a WNBA hedge of about 0.75% that assumed $500 of sportsbook liquidity. An early fuzzy team-name matcher produced 18 false "arbs" at 2–7%. Its limitations: Kalshi polled at about 8 requests per second, so snapshots can be about a minute stale; scheduled runs every 1–2 hours can't catch roughly 6-second in-game gaps; all legs are priced as takers ([GitHub – VV1Git/sportstrades](https://github.com/VV1Git/sportstrades)) (read directly).
- Other repos, such as Sparmon7/polymarket (sportsbook vs Polymarket via The Odds API) and several Polymarket–Kalshi arbitrage bots, are mostly code without audited results ([Sparmon7/polymarket](https://github.com/Sparmon7/polymarket); [ImMike/polymarket-arbitrage](https://github.com/ImMike/polymarket-arbitrage); [TopTrenDev bot](https://github.com/TopTrenDev/polymarket-kalshi-arbitrage-bot)) (snippets only).
- I found no first-hand Reddit P&L for a Kalshi sports bot that profits after fees. Vendor summaries of Reddit say most discussion is about hedging, and that "thin markets plus fees can erode" any edge ([SportBotAI – Kalshi Reddit](https://www.sportbotai.com/blog/kalshi-reddit); [sports-ai.dev](https://www.sports-ai.dev/blog/prediction-markets-vs-bookmakers-ai-betting-2026)) (vendor blogs).
- Professional bettors are active on Kalshi. Peabody is trading heavily, and Futurism and Bloomberg frame pros as moving into prediction markets to profit from recreational traders ([Bloomberg](https://www.bloomberg.com/news/articles/2026-02-05/super-bowl-lx-is-bringing-professional-gamblers-to-prediction-markets); [Futurism](https://futurism.com/future-society/professional-gamblers-prediction-markets)) (via search summary).

**Data access and cost (2026)**
- **Pinnacle API:** "Access to Pinnacle API suite has been closed for the general public since July 23rd, 2025." Pinnacle offers bespoke data services for select high-value bettors and commercial partners, and academics or pre-game handicapping projects can apply at api@pinnacle.com ([GitHub – pinnacleapi-documentation](https://github.com/pinnacleapi/pinnacleapi-documentation)) (read directly; primary source).
- **Pinnacle-derived third-party feeds:** PinnWire runs from $89/month, with a free key at 100 requests/day ([PyPI – pinnwire](https://pypi.org/project/pinnwire/)). An Apify scraper charges from $1.40 per 1,000 odds rows, reads Pinnacle's guest data, and "may break" ([Apify](https://apify.com/lergassy/pinnacle-odds-api)). pinnapi and pinnodds say they are unaffiliated with Pinnacle, and I found no prices for them ([GitHub – pinnapi](https://github.com/pinnapi/pinnapi)). Odds-API.io replaced Pinnacle with Betfair Exchange, SingBet and Polymarket ([Odds-API.io blog](https://odds-api.io/blog/pinnacle-api-shutdown-alternatives)). PS3838, Pinnacle's sister brand, may still give API access through brokers ([SportsAPIs.dev](https://sportsapis.dev/pinnacle-api)). That route is offshore and not for US persons. (Via search summary.)
- **The Odds API:** a free plan with 500 credits, then $30/month for 20K credits, $59 for 100K, $119 for 5M and $249 for 15M. Credits scale with markets × regions, and historical calls cost about 10x. Featured markets update every 60 seconds pre-match and 40 seconds in-play; exchanges every 20 seconds pre-match and 10 seconds in-play ([The Odds API](https://the-odds-api.com/); [update intervals](https://the-odds-api.com/sports-odds-data/update-intervals.html); [SportsAPIs.dev review](https://sportsapis.dev/apis/the-odds-api)) (via search summary). Whether it covers Pinnacle is unconfirmed, and sources conflict.
- **OddsJam / OpticOdds:** the developer API runs on OpticOdds' enterprise platform and is quote-only. Community reports put it around $5,000/month per sport, and OpticOdds claims under 800 ms delivery ([OddsPapi – OddsJam alternative](https://oddspapi.io/blog/oddsjam-api-alternative/); [Odds-API.io – OpticOdds](https://odds-api.io/compare/optic-odds); [TheRundown – OddsJam comparison](https://therundown.io/compare/oddsjam)) (unverified, from competitors' pages).
- **Unabated API:** a competitor describes it as a sales-gated plan of about $3,000/month covering about 8 US leagues ([SportsGameOdds – vs Unabated](https://sportsgameodds.com/compare/unabated)). Another summary cites self-serve plans at $799/month for 5 leagues and $2,999/month for all sports, with a free tier on a 15-second delay; I couldn't confirm that source. Delivery is REST plus SSE ([SportsAPIs.dev – Unabated](https://sportsapis.dev/apis/unabated)). The figures conflict.
- **Betfair Exchange:** a live API key needs a funded account and a one-off fee of £299 or £499 (sources conflict). Direct US access is listed as blocked, so it needs a non-US jurisdiction. Aggregators resell Betfair prices ([SportsGameOdds – Betfair](https://sportsgameodds.com/bookmakers/betfairexchange-odds-api); [OddsPapi – Betfair](https://oddspapi.io/blog/betfair-api-alternative-exchange-odds/)) (via search summary).
- **Circa:** no direct API. It appears only through aggregators that list Circa among their books ([SportsGameOdds – provider comparison](https://sportsgameodds.com/blog/comparing-odds-api-providers)) (via search summary). Commercial licensing terms are unclear.

**Latency and venue mechanics**
- A secondary source says live bets on Kalshi and Polymarket execute instantly, with no in-play delay ([Sportmarket help](https://help.sportmarket.com/en/articles/15201927-kalshi-and-polymarket-on-sportmarket-what-you-need-to-know)) (unverified against exchange rules).
- A VPS vendor claims Kalshi bots need a 1 ms VPS in Chicago ([TradoxVPS](https://tradoxvps.com/why-kalshi-traders-need-a-1ms-vps-in-chicago/)) (vendor claim; I didn't confirm Kalshi's matching-engine location).

### Inferences
- The polymm split is the key lesson: hedged market-making legs made +$8.3k while unhedged "+EV" legs entered at 7%+ edge lost $3.2k. That pattern is adverse selection. When you get filled against a sharp-anchored "edge", it's often because fair value just moved and your sharp data is the stale side.
- A US retail anchoring bot built on The Odds API, with 40–60-second update intervals, is likely to mistake its own data lag for Kalshi mispricing. Sub-second sharp data costs roughly $1k–$5k+ per month or needs scraping in a terms-of-service grey area, and it still competes with SIG-class market makers and pros like Peabody.
- Liquidity limits capacity more than it limits finding edges. In headline games depth is fine but edges are tiny. Where edges might be larger (props, small leagues, in-game), depth is thin: in-game depth is down 76%, and single orders reportedly move prices 3–5¢.

### Gaps
- I found no audited or verifiable track record of a Kalshi-specific sports anchoring bot. polymm's figures are Polymarket and self-reported.
- I couldn't read polymm's linked "autopsy" write-up on adverse selection.
- I couldn't confirm whether Kalshi applies any in-play order delay, speed bump or courtsiding protection.
- I couldn't confirm the licensing and legality of using scraped Pinnacle or Circa data commercially from the US.

## Q4. How well-established is "sharp book as truth" (closing-line value, Pinnacle efficiency), and does it transfer to Kalshi?

### Takeaway
The logic is well supported for pre-game closing lines in major markets, mostly soccer: de-vigged Pinnacle closing odds are well calibrated, and models struggle to add information beyond them. Closing-line value is the standard skill metric. The classic profitable application, consensus-anchored betting against soft books (Kaunitz et al., 2017), worked because soft books moved slowly, and winners got limited.

It transfers to Kalshi only partly. Kalshi doesn't limit winners, but its main markets aren't soft: market makers quote close to sharp lines, and on-exchange returns favor makers over takers. Since 2024 Q2, professional makers have earned the maker–taker transfer.

### Cited Findings
- **Pinnacle calibration:** an analysis built on football-data.co.uk data (193,803 matches; 1,970,653 sets of 1X2 odds) found Pinnacle closing odds well calibrated. Buchdahl tested Pinnacle's margin-free closing odds over three English seasons ([football-data.co.uk – Pinnacle efficiency](https://football-data.co.uk/blog/pinnacle_efficiency.php); [Pinnacle – market efficiency](https://www.pinnacle.com/betting-resources/en/educational/how-to-solve-a-problem-like-efficiency-part-one/rn8j5rnqj2p8t68p)) (via search summary).
- **Opening-to-closing ratio:** Buchdahl (2016) reportedly showed that the ratio of a bet's price to Pinnacle's closing price was a very reliable indicator of profitability, across about 10,000 matches ([Pinnacle Odds Dropper – Buchdahl on CLV](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl)) (via search summary).
- **Blind backing at Pinnacle's close:** a replication across 31,550 matches found a theoretical loss of 4.92% from backing everything at Pinnacle closing odds. Results sat about 1% from fair implied probabilities ([Football Trading Academy](https://footballtradinga.com/pinnacle-odds/)) (promotional; thin methodology).
- **Serie A preprint (2026):** a structural model's marginal information beyond a de-vigged closing price was "indistinguishable from zero" over 2,660 matches. The model was better calibrated but less sharp, and the authors say this is not proof of strong-form efficiency ([arXiv 2608.11505](https://arxiv.org/pdf/2608.11505)) (via search summary).
- Closing odds already fold in traders' information, which makes them harder to beat (Pinnacle 2010–2014 data) ([arXiv 2010.12508](https://arxiv.org/pdf/2010.12508)) (via search summary).
- Dissent: being efficient *on average* still allows skilled bettors to select prices that are off ([Sports Trading Network](https://www.sportstradingnetwork.com/article/do-pinnacle-closing-prices-in-tennis-tell-the-full-story-can-you-win-in-the-long-run-without-beating-them/); [Pyckio](https://blog.pyckio.com/en/eg-pinnacle-closing-odds/)). Data Golf compares Pinnacle and DraftKings calibration in golf, but I couldn't read its method ([Data Golf](https://datagolf.com/how-sharp-are-bookmakers)). A blog claim of r² = 0.997 on 397,935 games is unverified ([TradeMate](https://tradematesports.medium.com/closing-line-the-most-important-metric-in-sports-trading-58e56cdb4458)).
- **Consensus anchoring against soft books:** Kaunitz, Zhong & Kreiner (2017) beat bookmakers "consistently… across thousands of games" in simulation and with real money, using only the market's implied consensus odds. Bookmakers answered with "discriminatory practices against successful clients", meaning account limits. The dataset covers 479,440 games from 2005–2015 ([arXiv 1710.02824](https://arxiv.org/abs/1710.02824); [GitHub – BeatTheBookie](https://github.com/Lisandro79/BeatTheBookie)) (abstract via search; older but foundational).
- **De-vig methods:** Clarke, Kovalchik & Ingram on adjusting for overround are cited as the basis for multiplicative, additive, power and Shin methods. The power method can over-adjust longshots ([Pinnacle Odds Dropper](https://www.pinnacleoddsdropper.com/guides/how-to-devig-pinnacle-s-odds-for-betting-on-soft-books)).
- **Kalshi evidence on who wins (all categories):**
  - Bürgi, Deng & Whelan: the average pre-fee return is about −20%, and about −22% after fees. Buyers of contracts under 10¢ lose over 60%. Takers lose about 32% on average against about 10% for makers. The bias is more pronounced in prices takers accept, and it may be diminishing over time ([UCD WP2025_19](https://www.ucd.ie/economics/t4media/WP2025_19.pdf); [CEPR/VoxEU](https://cepr.org/voxeu/columns/economics-kalshi-prediction-market); [GWU 2026 version](https://www2.gwu.edu/~forcpgm/2026-001.pdf)) (via search summary; working paper; averages are likely unweighted and longshot-heavy).
  - Becker, using 72.1M trades from June 2021 to Nov 2025: takers' mean excess return is −1.12% per trade and makers' is +1.12%, gross of fees. The transfer ranges from 0.17 pp in finance to over 7 pp in media and geopolitics. From launch through 2023, takers were +2.0% and makers −2.0%; the sign flipped in 2024 Q2 as professional makers entered ([jbecker.dev](https://www.jbecker.dev/research/prediction-market-microstructure); [SSRN 7217640](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7217640); [replication – fatskier/prediction-marks](https://github.com/fatskier/prediction-marks)). The replication, read directly, adds that at a 1¢ cost basis takers win 0.43% of the time against 1% implied. No sports-specific table was available.
  - Vladosyna's replication (read directly) finds a maker margin of +2.09% at prices ≥50¢ (BDW: +2.6%), and +2.40% gross after the May 2025 fee boundary. A series-level difference-in-differences estimate of the fee's effect on the favorite–longshot slope is −0.0016 (SE 0.0064), a tight null. Sports went from 0.009% of the sample in 2024 to 58.8% after May 2025 ([GitHub – Vladosyna](https://github.com/Vladosyna/kalshi-makers-takers-persistence)) (unreviewed).

### Inferences
- The "sharp as truth" premise is strongest for de-vigged closing prices in liquid pre-game markets. It is weaker for opening lines, props (Pinnacle's prop markets are less battle-tested, and SmartStake claims Kalshi leads on MLB props), and in-game, where sharp books also reprice with latency and margin.
- The transfer to Kalshi works for valuation: de-vigged Pinnacle is a good fair-value estimate for Kalshi contracts. It breaks for edge sourcing. The Kaunitz edge came from soft-book price staleness, while Kalshi's main-market prices are set by makers who use the same sharp inputs. On Kalshi the residual inefficiency on record is structural (the favorite–longshot bias, recreational combo flow) and is earned mostly by *makers*, not by anchoring *takers*.
- CLV against the de-vigged Pinnacle or consensus close is the right fast diagnostic for any Kalshi sports strategy. If entries don't beat the close by more than the fee, P&L won't either.

### Gaps
- I found no academic study that applies a CLV test to Kalshi sports prices, for example Kalshi entry against Pinnacle close, or Kalshi close against Pinnacle close, by sport.
- There are no sports-specific maker/taker or favorite–longshot tables from BDW, Becker or the replications in what I could access.
- I couldn't read the primary Buchdahl, Data Golf and Clarke et al. texts (blocked hosts or not fetched). The calibration numbers above are secondhand.

## Q5 (Objective). Strategy-by-strategy assessment: do sports strategies on Kalshi win after fees?

### Takeaway
Pure sharp-line anchoring as a taker on Kalshi's main pre-game markets is unlikely to be a durable after-fee edge for a US trader. Typical deviations of about 0.5–0.75 pp sit below the 1.75 pp taker fee at 50¢, the counterparty is usually a professional market maker using the same sharp feed, and practitioners report edges vanishing to speed. The more plausible edges run through the maker side (sharp-anchored resting quotes plus incentive payments), structural biases (fading longshots in futures and props), and thin secondary markets. Capacity in each is limited and the confidence is moderate at best.

### Cited Findings
These are the inputs to the strategy cards below; full citations are in Q1–Q4.
- Taker fee is 0.07·p·(1−p), maker fee 0.0175·p·(1−p) on listed series, both rounded up ([QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained)). MLB game markets reportedly carry a 0.5 multiplier ([sportstrades](https://github.com/VV1Git/sportstrades)).
- Median gap between Kalshi and de-vigged Pinnacle is 0.75 pp ([OddsPapi](https://oddspapi.io/blog/polymarket-api-kalshi-api-vs-sportsbooks-the-developers-guide/)). Pre-game gap to FanDuel is 0.54–1.40%, and the in-game median is 2.25% ([Blockworks](https://app.blockworks.com/report/from-betting-to-trading-how-kalshi-is-reshaping-sports-markets)). In-game gaps last about 6 seconds ([sportstrades](https://github.com/VV1Git/sportstrades)).
- Makers beat takers since 2024 Q2 ([Becker](https://www.jbecker.dev/research/prediction-market-microstructure)). Longshots under 10¢ lose over 60% ([BDW](https://www.ucd.ie/economics/t4media/WP2025_19.pdf)). Combo makers made +$519.8M after fees while combo takers lost over $1B ([InGame](https://www.ingame.com/kalshi-parlay-taker-losses-top-1b/)).
- polymm: hedged market making +$8,293, unhedged "+EV" legs −$3,184, retired as too slow ([polymm](https://github.com/kachence/polymm)).
- Pinnacle's public API has been closed since 2025-07-23 ([Pinnacle docs](https://github.com/pinnacleapi/pinnacleapi-documentation)). Sharp data costs: The Odds API $30–$249/month with 40–60 s updates; Unabated about $800–$3,000/month; OpticOdds around $5k/month per sport (Q3 sources).

### Inferences

#### S1. Pre-game sharp-line anchoring as a taker, main markets (NFL/NBA/MLB/NHL winners, spreads, totals)
- **What:** Buy a Kalshi YES or NO when the ask is below the de-vigged Pinnacle, Circa or consensus fair probability by more than fee plus buffer, then hold to settlement or exit at the close.
- **Mechanism:** Assumes Kalshi is slow to update, or that recreational flow pushes it off fair. In practice, the resting ask you lift usually belongs to a professional market maker such as SIG or a pro bettor, quoting off the same sharp feeds. You only win when that maker is stale or deliberately skewing inventory.
- **Evidence:** Median gap of about 0.75 pp is below the 1.75 pp fee at 50¢. Kalshi and Polymarket bid/ask sit within 1¢. Vegas-versus-prediction-market gaps mostly fall inside the vig (all unverified vendor or OSS findings). No public track record.
- **Logic:** Sound as valuation, weak as an edge source. Fees consume the median gap, and the tail gaps are adversely selected.
- **Needs:** A sharp feed with updates of 1 second or better around line moves; at 40–60-second intervals you trade your own stale data. Exact contract mapping against each Kalshi market's rules: overtime inclusion, tie handling (one OSS repo models 0.50-per-side tie payouts; check the rulebook) and postponement rules ([ThinBlimp – postponed games](https://thinblimp.com/guides/postponed-games)). Kalshi API at Basic or Advanced tier is enough. Modest capital, since settlement is same-day.
- **Paper test:** Fairly honest if you record Kalshi WebSocket books and timestamped sharp odds, fill only at the displayed ask size after realistic latency, apply per-order fee rounding, and grade on CLV against the de-vigged Pinnacle close. P&L alone needs about 2,500 independent bets to detect a 2¢ edge at about 2σ, or about 10,000 for 1¢ (per-contract SD is about $0.50 near 50¢).
- **Confidence of a durable after-fee edge: 10%.**

#### S2. Anchoring in thin or secondary markets (minor leagues, WNBA, small-college games, early openers, alternate spreads and totals, player props)
- **What:** Same as S1, aimed where market makers quote wider and stale retail limit orders survive.
- **Mechanism:** Fewer professional quoters; recreational resting orders.
- **Evidence:** No measurements found. Kalshi prop depth is concentrated in star players. SmartStake claims Kalshi is the sharpest book on MLB props, which cuts against anchoring there.
- **Logic:** Plausible, but the sharp references are themselves weaker for props and alt lines.
- **Needs:** Multi-book consensus feeds including props, which raises the cost to the Unabated or OpticOdds tier. Pinnacle prop coverage needs to be checked. Capacity is small.
- **Paper test:** Same as S1, but fill realism matters more because size at the ask is tiny.
- **Confidence: 18%.** Most likely to work, but small and hard to scale.

#### S3. Pre-game steam and news sniping (react to Pinnacle or Circa moves and injury or lineup news before Kalshi quotes update)
- **What:** A latency race: lift stale Kalshi quotes in the seconds after the sharp market moves.
- **Mechanism:** Slow market makers or stale retail orders.
- **Evidence:** Vendors claim windows anywhere from under a second to 90 seconds (unverified). polymm, retired as "too slow", shows that speed was the edge and that it decays.
- **Logic:** Sound in principle, but you are racing SIG-class firms that see the same feeds.
- **Needs:** Sub-second sharp data. Pinnacle's API is closed, so this means scraping or an enterprise feed at roughly $1k–$5k+/month, a co-located VPS, and Premier-tier-or-better API limits.
- **Paper test:** Poor. Without synchronized tick data, a paper test will overstate fills.
- **Confidence: 7%** for a small US operator.

#### S4. In-game stale-quote trading
- **What:** Trade Kalshi live contracts when they lag game state or live sharp prices.
- **Mechanism:** Market makers widen or pull quotes in-game (depth down 76%). Recreational momentum trading.
- **Evidence:** In-game gaps last about 6 seconds. Correlation with FanDuel is 0.996 at 5-minute resolution. A blog anecdote describes stale prices during breaks.
- **Logic:** The edge belongs to whoever has faster-than-broadcast data, such as official league or scout feeds, which are expensive and possibly restricted. Integrity and investigation risk is rising: sports-mention markets were pulled.
- **Needs:** Low-latency event data, Kalshi WebSocket, automated risk controls.
- **Paper test:** Effectively not testable honestly on paper.
- **Confidence: 4%.**

#### S5. Sharp-anchored passive market making (rest quotes around de-vigged fair, earn spread plus incentive payments)
- **What:** Post bids and offers a little inside fair. Cancel or reprice on sharp moves. Optionally hedge across venues as polymm did.
- **Mechanism:** Capture the spread that recreational takers pay, with the lower maker fee of 0.44¢ at 50¢, and collect LIP rewards ($10–$1,000/day per market, excluding official market makers) or prop-combo fee-share credits.
- **Evidence:** Makers earn positive gross excess returns on Kalshi: +1.12% per trade (Becker); +2.1–2.4% at ≥50¢ (Vladosyna). Combo makers +$519.8M after fees. polymm's hedged leg was +$8.3k. All unverified.
- **Logic:** The most coherent edge, because it sits on the side of the documented wealth transfer. The main risk is adverse selection when sharp lines move, which is exactly where polymm lost money. You also compete with SIG-class market makers for queue priority.
- **Needs:** A fast sharp feed for cancels, the more important use of the feed. Kalshi WebSocket plus enough write capacity (Advanced or Premier tier). Inventory limits per game. Capital of $5k–$50k is enough to start in non-headline markets.
- **Paper test:** Unreliable. Queue position and adverse selection can't be simulated honestly, so run a small live test.
- **Confidence: 25%** in less-trafficked markets. Lower in headline NFL and NBA games.

#### S6. Favorite–longshot fade in sports futures and longshot props (sell overpriced longshots, i.e. buy NO at 90¢+, screened against sharp futures prices)
- **What:** Systematically buy NO on longshots whose Kalshi YES price exceeds the de-vigged sharp futures probability.
- **Mechanism:** Recreational demand for longshots; the bias is documented on Kalshi across categories.
- **Evidence:** Sub-10¢ contracts lose over 60%. Takers win 0.43% of the time at 1¢ against 1% implied. The bias showed no detectable change from fees (DiD null). BDW suggest it may be diminishing over time. No sports-futures-specific tables.
- **Logic:** Sound. The fee is small at 90¢+ (about 0.6¢ or less per contract), and fading as a maker is cheaper still.
- **Needs:** Sharp futures prices from Pinnacle, Circa or consensus. Capital locked for weeks to months, so check whether Kalshi pays interest on positions. Small per-trade edge with tail risk on each NO.
- **Paper test:** Reasonably honest from Kalshi's public trade history, but the sports-futures sample is small, at a few seasons.
- **Confidence: 28%** of a real after-fee edge. Small capital efficiency.

#### S7. Cross-venue arbitrage (Kalshi against Polymarket or US sportsbooks)
- **Evidence:** The paper scanner found essentially none in liquid games after an estimated 5–7% round-trip fee load. Sportsbook legs get limited, and Polymarket access for US persons needs a venue check.
- **Confidence: 4%.**

#### S8. Combos
- **Taking combos:** negative expectancy; takers lost over $1B. **Confidence: 1%.**
- **Making combos:** this is where the recreational edge sits, with makers +$519.8M after fees. It needs correlation models and an institutional set-up, and small-trader access to combo quoting is unverified. **Confidence: 10%** for a small trader.

#### Summary ranking (confidence of a real, durable after-fee edge for a US trader)
S6 longshot fade 28% > S5 sharp-anchored making 25% > S2 thin-market anchoring 18% > S1 main-market taker anchoring 10% ≈ S8 combo making 10% > S3 steam sniping 7% > S4 in-game 4% ≈ S7 cross-venue arbitrage 4% > combo taking 1%.

A practical first step: log Kalshi books against a de-vigged sharp feed, measure the distribution of ask-versus-fair gaps net of fees and their persistence in seconds, and grade every hypothetical entry by CLV. Only then risk capital, starting with S5 and S6 at small size.

### Gaps
- No independent, timestamped dataset of Kalshi-versus-Pinnacle gaps net of fees, by sport, market type and time-to-start. This is the single most important missing input, and the user would have to generate it.
- No verified Kalshi sports bot P&L.
- Unconfirmed: maker-fee and multiplier coverage per sports series; LIP end dates and amounts in late 2026; position limits; interest on collateral; any in-play order delay; whether non-market-maker accounts can quote combos.
- Data-feed prices are mostly from competitors' comparison pages and conflict. Pinnacle-derived scraping feeds carry unresolved terms-of-service and legal risk for US commercial use. Betfair and PS3838 need non-US jurisdictions.
- The state-level legality of Kalshi sports contracts is in flux (circuit split, state actions as of Sept–Oct 2026). Check your state before any live test.
