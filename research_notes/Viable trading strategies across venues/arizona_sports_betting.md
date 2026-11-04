# Sports betting edges an Arizona resident can legally automate or semi-automate: venues, promotions, arbitrage, +EV and model edges (status as of 2026-11-04)

Method note. Direct page fetches were blocked in this session for sbcnews.co.uk, predictionnews.com and legalsportsreport.com, so most facts below come from search-engine summaries of the cited pages ("via search summary"). They were not read in full and should be spot-checked before anything is decided on them. Facts tagged "(companion note)" were compiled by another researcher in `research_notes/Viable Kalshi trading strategies/sports_sharp_line_anchoring.md` (dated 2026-11-03). They are cited to that note's original sources and were not re-verified here. "Us" means a cloud-hosted bot with seconds-level latency, a $1k–$25k bankroll, trading-only API keys, and paper-testing before live money.

## Q1. Which sports betting venues are legal and licensed in Arizona today, and which offer an API or allow automated betting?

### Takeaway
As of early November 2026, the only venues that are clearly legal for an Arizona resident are the roughly 13–15 sportsbooks licensed by the Arizona Department of Gaming (ADG): FanDuel, DraftKings, BetMGM, Caesars, bet365, Fanatics, BetRivers, Hard Rock Bet, Desert Diamond, theScore Bet, Bally Bet and a few others. Circa Sports is licensed but not expected live until about early 2027. None of these books has a retail betting API, and their terms ban bots and "sniping" software.

Arizona has **no licensed peer-to-peer exchange**:
- Sporttrade's Arizona product was never an exchange, and Sporttrade shut all its US betting in mid-2026.
- Prophet/ProphetX, Novig and BetOpenly have all received ADG cease-and-desist orders.

Among CFTC-regulated venues:
- **Kalshi** is reachable from Arizona and has an official API, but only under a May 2026 federal injunction. Arizona is asking the Ninth Circuit to dissolve it, after that court ruled against Kalshi in the Nevada case on Aug 28, 2026.
- **Crypto.com** left Arizona in December 2025.
- **Polymarket US**: Arizona sports availability is contested.
- **Robinhood** has no API.

### Cited Findings
**Licensed sportsbooks (ADG event wagering)**
- Arizona law caps event-wagering operator licenses at 20: 10 for Arizona tribes and 10 for Arizona pro sports franchises. One article counted 14 licensed operators (article date unclear) — [G3 Newswire](https://g3newswire.com/?p=147675) (via search summary).
- The official roster is ADG's "Approved Operators & Retail Locations" page. Its table did not render in search results, so the official list could not be read — [ADG](https://www.azgaming.gov/approved-operators-retail-locations-0).
- The brands most consistently listed as live in Arizona in 2026 are FanDuel, DraftKings, BetMGM, Caesars, bet365, Fanatics and BetRivers, plus Bally Bet, Hard Rock Bet, Desert Diamond Sports and theScore Bet. Some guides also list BetCris and Golden Nugget, and counts range from 12 to 15 — [Covers, Nov 2026](https://www.covers.com/betting/usa/arizona); [BetArizona](https://www.betarizona.com/); [Dimers](https://www.dimers.com/betting/arizona) (via search summary; the lists conflict).
- Later license allocations:
  - bet365, for the Ak-Chin Indian Community, Aug 2023
  - Fanatics, for Tonto Apache, Mar 2024
  - Plannatech, for San Carlos Apache, Aug 2024
  
  Source: [ADG allocation-periods PDF](https://gaming.az.gov/sites/default/files/Event%20Wagering%20Operator%20Allocation%20Periods%20%281%29.pdf) (via search summary).
- A third application window ran June 26 – July 10, 2026 — [ADG](https://gaming.az.gov/ew-application-period).
- **Circa Sports:**
  - License allocation took effect July 27, 2026, through a partnership with the San Juan Southern Paiute Tribe.
  - Circa's operations director said it is targeting an early-2027 Arizona launch.
  - Sources disagree on whether Circa is Arizona's 13th, 14th or 15th licensee.
  
  Sources: [Rotowire](https://www.rotowire.com/news/circa-sports-approved-to-launch-in-arizona-126207); [Casino.org](https://www.casino.org/news/circa-lands-arizona-sports-betting-license/); [Gaming Intelligence](https://www.gamingintelligence.com/?p=234376); [Covers interview with Derek Stevens, Aug 2026](https://www.covers.com/industry/circa-ceo-derek-stevens-arizona-interview-sports-betting-license-august-2026) (via search summary).
- ADG warned its licensed sportsbooks that offering prediction markets (event contracts) puts their Arizona licenses at risk — [Legal Sports Report](https://www.legalsportsreport.com/242071/sportsbooks-running-prediction-markets-risk-arizona-licenses/); [InGame](https://www.ingame.com/arizona-warns-regulated-operators-prediction-markets/) (via search summary).

**Peer-to-peer exchanges and sweepstakes-style sports venues**
- **Sporttrade in Arizona:** licensed with the Quechan Tribe in Aug 2024 and live Sept 26, 2024. The Arizona product resembled a traditional sportsbook, not Sporttrade's exchange, and one report said it was "not apparent that Arizona allows exchange wagering" — [SBC Americas](https://sbcamericas.com/2024/09/26/sporttrade-goes-live-in-arizona/); [iGaming Business](https://igamingbusiness.com/sports-betting/sporttrade-virginia-arizona-evolution/) (via search summary).
- **Sporttrade's exit:**
  - On May 15, 2026 it announced it would close its sportsbook operations in NJ, AZ, CO, IA and VA. Closure dates were reported as May 25 or "by June 26, 2026".
  - It filed CFTC applications for a designated contract market (DCM) and a derivatives clearing organization (DCO), in January or February 2026 (sources differ).
  - An Oct 27, 2026 review says its CFTC registration was still unconfirmed.
  
  Sources: [Yogonet](https://www.yogonet.com/international/news/2026/05/19/121042-sporttrade-to-exit-us-online-sports-betting-markets-while-awaiting-cftc-decision); [Gambling.com](https://www.gambling.com/us/news/sporttrade-exits-us-sports-betting-market-in-pivot-to-prediction-markets); [Finance Magnates](https://www.financemagnates.com/forex/sporttrade-exits-sports-betting-to-rebuild-around-prediction-markets-under-cftc-oversight/); [Tech-Insider](https://tech-insider.org/sporttrade-promo-code/) (via search summary).
- **Prophet Exchange** was the first US regulated P2P sports exchange (NJ, Aug 2022). It stopped taking NJ bets on May 15, 2024, closed "for now" in June 2024 while criticizing the US market as anti-consumer, then relaunched as the sweepstakes app ProphetX — [Business Wire](https://www.businesswire.com/news/home/20220829005434/en/Prophet-Exchange-Launches-as-First-U.S.-Sports-Betting-Exchange%E2%80%94Giants-Legend-Victor-Cruz-Places-Inaugural-Bet); [SBC Americas](https://sbcamericas.com/2024/05/16/prophet-exchange-shut-new-jersey-ops/); [Covers](https://www.covers.com/industry/prophet-exchange-closes-up-shop-for-now-june-25-2024); [pm.wiki](https://pm.wiki/uk/projects/prophetx) (third-party directory).
- **ADG's April 2025 cease-and-desist wave** named ProphetX as a "peer-to-peer exchange" among six operators, citing promotion of gambling, illegal control of an enterprise and money laundering — [Legal Sports Report](https://www.legalsportsreport.com/231261/illegal-operators-arizona-sports-betting-cease-and-desists-apr-2025/); [Covers](https://www.covers.com/industry/arizona-issues-cease-and-desist-orders-to-unregulated-gambling-operators); [ADG press release](https://gaming.az.gov/sites/default/files/C%26D%28s%29%20Press%20Release%20Final.pdf) (via search summary).
- **ProphetX's federal pivot:** it moved from sweepstakes toward a CFTC-regulated sports exchange (Nov 2025). One outlet reports CFTC approval, and a review site says it was registered as a clearinghouse on June 10, 2026 (unverified) — [SBC Americas](https://sbcamericas.com/2025/11/10/prophetx-sports-prediction-market/); [DeFi Rate](https://defirate.com/news/prophetx-wins-cftc-approval-sports-focused-prediction-exchange/); [CoinStats](https://coinstats.app/prediction-markets/apps/prophetx/) (via search summary). I found no statement of ProphetX's Arizona availability.
- **Novig:**
  - ADG named it in a mid-2025 cease-and-desist wave alongside Stake.us — [SBC Americas](https://sbcamericas.com/2025/06/27/arizona-regulator-continues-crusade/).
  - Every 2026 state guide I found lists Arizona as excluded, alongside Michigan and Nevada. An October 2026 Dimers page lists seven excluded states — [Dimers](https://www.dimers.com/prediction-markets/novig/legal); [Gambling.com](https://www.gambling.com/us/prediction-markets/reviews/novig); [OddsShopper](https://www.oddsshopper.com/articles/prediction-markets/where-is-novig-legal-a-2025-guide-to-novig-legal-states-y16) (via search summary).
  - Novig sought CFTC approval in Jan 2026 — [Covers](https://www.covers.com/industry/novig-seeks-cftc-approval-to-operate-prediction-markets-jan-26-2026).
- **BetOpenly**, a P2P "reduced juice" exchange that in 2025 claimed a legal framework covering 45 states, received an ADG cease-and-desist on July 10, 2026, together with ClubWPT, Bookmaker, Kutt and Raffle Creator — [Lines.com (citing SBC Americas)](https://www.lines.com/arizona-orders-five-gambling-sites-to-shut-down); [Betting Startups podcast, June 2025](https://bettingstartups.podbean.com/e/ep-167-reduced-juice-for-all-w-gino-donati-from-betopenly) (via search summary).
- I found no Arizona sweepstakes-ban statute signed in 2026. Arizona has acted through ADG cease-and-desists instead, while other states passed bans — [Lines.com](https://www.lines.com/arizona-orders-five-gambling-sites-to-shut-down); [Sweepsy 2026 tracker](https://www.sweepsy.com/news/legislative-wins-losses-sweeps-2026/) (via search summary).

**CFTC-regulated sports event contracts**
- ADG sent cease-and-desist letters to Kalshi, Crypto.com and Robinhood, saying they are unlicensed and that their event wagering in Arizona is illegal — [Next Event Horizon](https://nexteventhorizon.substack.com/p/arizona-regulator-sends-cease-and); [SportsBettingDime](https://www.sportsbettingdime.com/news/betting/crypto-com-no-longer-offers-sport-event-contracts-in-arizona-eight-other-states/) (via search summary). ADG also filed a comment letter with the CFTC on June 2, 2025 — [CFTC](https://www.cftc.gov/media/12146/ArizonaDepartmentOfGaming060225/download).
- Crypto.com stopped offering sports event contracts in Arizona on Tuesday Dec 2 (2025), and its other prediction markets on Dec 12. ADG says its enforcement and licensing actions came first — [SportsBettingDime](https://www.sportsbettingdime.com/news/betting/crypto-com-no-longer-offers-sport-event-contracts-in-arizona-eight-other-states/); [ReadWrite](https://readwrite.com/crypto-com-pulls-prediction-market-sports-contracts-arizona/) (via search summary).
- **Kalshi, March 2026:** Kalshi sued Arizona preemptively (one source dates the filing to March 12), and Arizona filed the first-ever state criminal charges against Kalshi. The counts cover NFL, NBA, college basketball and Super Bowl contracts, plus election contracts — [Regulatory Oversight](https://www.regulatoryoversight.com/2026/03/arizona-files-first-ever-criminal-suit-against-kalshi/); [SportsBettingDime](https://www.sportsbettingdime.com/news/betting/kalshi-sues-arizona-in-preemptive-sports-event-contract-battle/); [Yahoo News](https://www.yahoo.com/news/articles/arizona-charges-prediction-market-kalshi-194029873.html) (via search summary).
- In April 2026 the DOJ and CFTC asked the federal court to block Arizona's prosecution, arguing that sports event contracts are swaps — [The Block](https://www.theblock.co/news/regulation/2026-04-09-doj-cftc-argue-sports-event-contracts-are-financial-swaps-396833).
- Judge Michael Liburdi (D. Ariz.) denied Kalshi's TRO and preliminary injunction (PI) in April. On May 5, 2026 he granted an injunction barring AG Kris Mayes and ADG from enforcement, finding that federal law preempts. Some outlets call it "permanent"; most call it preliminary. A separate report describes a preliminary injunction granted to the CFTC against Arizona — [SBC Americas](https://sbcamericas.com/2026/05/07/kalshi-receives-arizona-injunction/); [AZ Mirror](https://azmirror.com/2026/05/05/arizonas-criminal-case-against-kalshi-permanently-blocked-by-federal-judge/); [Yogonet](https://www.yogonet.com/international/news/2026/05/08/119835-federal-court-blocks-arizona-ags-criminal-case-against-kalshi); [Gambling Insider](https://www.gamblinginsider.com/news/158205/arizona-judge-grants-cftc-preliminary-injunction-kalshi-case) (via search summary).
- **Ninth Circuit, Aug 28, 2026,** *KalshiEX v. Assad* (No. 25-7516):
  - The panel was unanimous. It affirmed the dissolution of Kalshi's preliminary injunction against Nevada, finding Kalshi unlikely to show that the Commodity Exchange Act preempts state gaming law for sports contracts.
  - Crypto.com's and Robinhood Derivatives' consolidated appeals were decided the same way. Election contracts were remanded.
  - Platforms can no longer offer sports contracts in Nevada.
  
  Sources: [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/08/ninth-circuit-upholds-state-and-tribal-authority-over-sports-related); [National Law Review](https://natlawreview.com/article/sports-bets-or-swaps-ninth-circuits-controversial-kalshi-ruling-deepens-divide); [SportsBettingDime](https://www.sportsbettingdime.com/news/industry/ninth-circuit-unanimously-rules-against-kalshi-allowing-nevada-oversight-of-sports-event-contracts/); [AZ Mirror](https://azmirror.com/2026/08/28/9th-circuit-sides-with-states-in-kalshi-gambling-fight-potentially-reviving-arizonas-prosecution/) (via search summary).
- **Third Circuit, Apr 6, 2026:** a 2–1 panel affirmed Kalshi's preliminary injunction against New Jersey. NJ filed a petition for Supreme Court review (certiorari) on Sept 2, 2026, citing the circuit split. I found no report of Supreme Court action — [DeFi Rate](https://defirate.com/news/sports-prediction-market-fight-first-supreme-court-filing/); [Sportico](https://www.sportico.com/law/analysis/2026/kalshi-third-circuit-new-jersey-scotus-1234889561/); [Legal Sports Report](https://legalsportsreport.com/275556/new-jersey-asks-supreme-court-to-rule-on-kalshi-sports-predictions) (via search summary).
- In Sept 2026 Mayes asked the Ninth Circuit to dissolve Liburdi's injunction, arguing the Nevada ruling decides the same question. Arizona's appeal had been held pending related cases. The latest coverage I found (late September) reports no ruling — [AZ Mirror](https://azmirror.com/2026/09/25/after-9th-circuit-ruling-mayes-pushes-to-revive-her-gambling-case-against-kalshi/); [Gambling.com](https://www.gambling.com/us/news/arizona-attorney-general-seeks-to-restart-legal-fight-against-kalshi); [Bloomberg Law](https://news.bloomberglaw.com/business-and-practice/kalshi-will-return-to-ninth-circuit-this-time-against-arizona); [ReadWrite](https://readwrite.com/arizona-lawsuit-kalshi-paused-ninth-circuit-appeals/) (via search summary).
- Utah has filed 13 criminal charges against Kalshi and its co-founders (reported Nov 3, 2026) — [SBC News](https://sbcnews.co.uk/northamerica/2026/11/03/kalshi-utah-lawsuit/) (via search summary).
- CBS Sports' state guide says Kalshi offers sports contracts in Arizona but Polymarket does not. Fox Sports lists Arizona as "contested", with prediction markets still available for now — [CBS Sports](https://www.cbssports.com/prediction/news/prediction-market-legal-states/); [Fox Sports](https://www.foxsports.com/stories/betting/prediction-markets-legal-states) (via search summary).
- **Polymarket US**, conflicting reports:
  - Sports Illustrated (late Oct 2026) says sports markets are unavailable in AZ, CT, MD, MI and TN.
  - A guide verified Oct 23, 2026 says the company told it Polymarket US is available everywhere except Nevada.
  - CoinStats lists Arizona as "contested for sports contracts".
  
  Sources: [SI](https://www.si.com/prediction-markets/reviews/polymarket-california); [PredictionMarketsPicks](https://predictionmarketspicks.com/learn/is-polymarket-legal-in-arizona); [CoinStats](https://coinstats.app/prediction-markets/legal/polymarket/) (via search summary).
- **Robinhood:** a Sept 2026 guide lists Arizona as available with sports contracts — [OddsAssist](https://oddsassist.com/prediction-markets/robinhood-states/). Fox Sports calls Arizona "contested" (above).
- **Federal–state fight:** the CFTC published a proposed prediction-market rule on June 10, 2026 (comments were due July 27, 2026). Per one secondary source, the CFTC has taken legal action against nine states, and regulators in 11 states have issued cease-and-desists — [DeucesCracked blog](https://www.deucescracked.com/blog/cftc-vs-states-prediction-market-jurisdiction-battle-2026) (secondary; via search summary).

**APIs and automation rules**
- **Kalshi** has an official REST/WebSocket API with tiered token-bucket rate limits; the Basic tier is roughly 20 reads and 10 writes per second (companion note; [Kalshi docs – rate limits](https://docs.kalshi.com/getting_started/rate_limits)).
- **Polymarket US** has an official API reference:
  - REST and gRPC services for trading, market data, accounts and KYC/payments.
  - Access tokens expire after 3 minutes, and the rate limit is 20 requests per second per IP.
  - Access is arranged through an onboarding contact — [Polymarket Exchange API docs](https://apidocs.polymarketexchange.com/api-reference).
  - Third-party claims conflict on whether retail API keys are generally available ("developer portal after KYC" versus "close-only/invite") — [DEV Community](https://dev.to/ai-agent-economy/how-to-build-a-cftc-compliant-polymarket-bot-in-2026-o9h); [chudi.dev](https://chudi.dev/blog/kalshi-vs-polymarket) (via search summary).
- **Robinhood** charges a $0.01 per-contract commission plus an exchange fee of about $0.01 per contract, on both opening and closing trades. Review sites say its prediction hub has no API — [Robinhood support](https://robinhood.com/us/en/support/articles/event-contracts-overview/); [BettingUSA](https://www.bettingusa.com/prediction-markets/reviews/robinhood/fees/); [Finder](https://www.finder.com/investments/kalshi-vs-robinhood) (via search summary).
- **FanDuel's** Terms of Use restrict robots, scrapers and "sniping" software; a tracker shows the clause updated May 5, 2026. A separate clause bars points or prizes obtained through unauthorized scripts or automation — [ConductAtlas – FanDuel automated access](https://conductatlas.com/platform/fanduel/fanduel-terms-of-use/provision/CA-P-043908/prohibition-on-unauthorized-automated-access/); [ConductAtlas – FanDuel scripts](https://conductatlas.com/platform/fanduel/fanduel-terms-of-use/provision/CA-P-043820/prohibition-on-unauthorized-scripts-and-automation/).
- **DraftKings'** terms ban automated scraping and automated interaction with its site. The tracked clauses come from its daily-fantasy terms. State-specific sportsbook terms exist, including an Arizona version, but I did not read them — [ConductAtlas – DraftKings](https://conductatlas.com/platform/draftkings/draftkings-terms-of-use/provision/CA-P-039377/automated-means-to-interact-with-website-prohibited/); [DraftKings AZ terms](https://sportsbook.draftkings.com/legal/az-terms-of-use).
- Some states write bot bans into regulation. Michigan's R 432.752, for example, requires sportsbook account terms to prohibit bots — [Cornell LII](https://www.law.cornell.edu/regulations/michigan/Mich-Admin-Code-R-432-752).

### Inferences
- **Venue map for us (Nov 2026):**

| Venue | Type | Arizona status | Bot API | Automation under ToS | Possible role |
|---|---|---|---|---|---|
| FanDuel, DraftKings, BetMGM, Caesars, bet365, Fanatics, BetRivers, Hard Rock Bet, Desert Diamond, theScore Bet, Bally Bet (± BetCris, Golden Nugget) | ADG-licensed sportsbooks | Legal; 21+; must be physically in Arizona | None found | Bots, scrapers and "sniping" software banned (FanDuel; DraftKings) | Promo conversion, +EV vs sharp lines, middles, with a human placing bets |
| Circa Sports | ADG-licensed (effective 7/27/2026) | Not live; early-2027 target | Unknown | Unknown | Future sharp-ish reference and venue |
| Sporttrade | Was licensed; non-exchange in Arizona | Closed mid-2026; CFTC application pending | – | – | None now; watch list |
| ProphetX | Sweepstakes P2P moving to CFTC | ADG cease-and-desist Apr 2025; Arizona availability unknown | – | – | Exclude |
| Novig | P2P moving to CFTC | Not offered in Arizona; ADG cease-and-desist 2025 | – | – | Exclude |
| BetOpenly | P2P | ADG cease-and-desist 7/10/2026 | – | – | Exclude |
| Kalshi | CFTC DCM | Available under the 5/5/2026 federal injunction; Arizona's appeal pending at the Ninth Circuit after the adverse 8/28/2026 Nevada ruling | Yes (REST/WebSocket) | API trading is the intended use | Hedge leg, market making, structural trades; **high regulatory risk** |
| Robinhood | Broker front-end for Kalshi/ForecastEx | Conflicting reports | No | – | Manual only |
| Polymarket US | CFTC DCM | Conflicting; SI says Arizona sports unavailable | Yes (by onboarding) | API | Probably none for Arizona sports; check the state list |
| Crypto.com | CFTC DCM | Exited Arizona sports 12/2/2025 | – | – | None |

- The bot cannot be the one placing sportsbook bets. ToS ban automation, and every bet needs a geolocation check placing the device in Arizona (see Q7). A cloud server elsewhere would fail that check, and faking location is excluded. Every sportsbook strategy is therefore "bot scans and computes, human taps".
- Kalshi is the only venue where the bot itself can trade sports from Arizona today, and that rests on a district-court injunction. Given the unanimous Nevada ruling, there is a material chance the Ninth Circuit dissolves it. Kalshi would then likely stop sports trading for Arizona users, as platforms did in Nevada. Design for a forced exit: avoid long-dated sports futures in size, and never route around a future Arizona geofence through out-of-state servers.
- "Exchange" strategies in the Betfair sense (back/lay trading, in-play exchange trading, commission-tier market making) have no licensed Arizona venue at all. In practice "exchange" means Kalshi, and possibly Polymarket US.

### Gaps
- I could not read ADG's official roster, so the live sportsbook list as of Nov 2026 is unconfirmed (BetCris, Golden Nugget and Bally Bet in particular).
- I found nothing after late September 2026 on whether the Ninth Circuit has ruled on Mayes's motion to dissolve the Arizona injunction.
- I found no source on whether an Arizona bettor (as opposed to the operator) faces legal exposure under Arizona law for trading Kalshi sports contracts while the injunction stands. I did not find the text of Arizona's statute on bettor liability.
- Whether Kalshi decides state eligibility by KYC residence or by device location: unknown.
- Polymarket US and Robinhood Arizona sports status: sources conflict. ProphetX's CFTC status and Arizona availability: unconfirmed.
- DraftKings Predictions and FanDuel Predicts in Arizona: not checked. I infer they are not offered, given ADG's warning to licensees.
- I found no evidence that any Arizona sportsbook offers a retail betting API.

## Q2. Exchange commissions and liquidity: can market making or price-taking be profitable at small size?

### Takeaway
With no licensed exchange in Arizona, exchange economics means Kalshi, and maybe Polymarket US. Kalshi's taker fee is 0.07 × P × (1−P), about 1.75¢ on a 50¢ contract. At mid that is like a −107 sportsbook price; add a 1¢ spread and taking costs about the same as −110.

The evidence says makers, not takers, earn on Kalshi: makers make about +1.12% gross per trade since professional makers arrived in 2024 Q2. Main-market sports prices sit within about 0.5–0.75 percentage points (pp) of de-vigged Pinnacle, which is below the taker fee. Price-taking at our seconds-level latency is therefore close to zero-EV or negative. Small-size market making is plausible but contested by firms like SIG, and adverse selection around news is the main risk.

### Cited Findings
- **Kalshi fees:**
  - Taker fee = 0.07 × contracts × P × (1−P), rounded up: $1.75 per 100 contracts at 50¢.
  - Maker fee = 0.0175 × C × P × (1−P), charged only on listed series. As of Oct 2026 the list reportedly included NFL and NBA game series; counts conflict.
  - Some series carry a 0.5 multiplier, reportedly including MLB.
  
  Companion note; [QuantVPS](https://www.quantvps.com/blog/kalshi-fees-explained); [BettingUSA](https://www.bettingusa.com/prediction-markets/reviews/kalshi/fees/); [VV1Git/sportstrades](https://github.com/VV1Git/sportstrades).
- **Closeness to sharp prices:** a data-vendor study of 88 fixtures found de-vigged median absolute gaps to Pinnacle of 0.59 pp for Polymarket, 0.75 pp for Kalshi and 0.83 pp for bet365 (companion note; [OddsPapi](https://oddspapi.io/blog/polymarket-api-kalshi-api-vs-sportsbooks-the-developers-guide/); vendor study, via search summary).
- **Cross-venue gaps:** an open-source, paper-only scanner covering 266 games found Kalshi and Polymarket bid/ask "usually within one cent". No liquid game cleared an estimated 5–7% round-trip fee load, and in-game gaps lasted about 6 seconds (companion note; [VV1Git/sportstrades](https://github.com/VV1Git/sportstrades)).
- **Maker–taker transfer:** across 72.1M Kalshi trades (June 2021 – Nov 2025), takers' mean excess return was −1.12% per trade and makers' +1.12%, gross of fees. The sign flipped in 2024 Q2 as professional makers entered (companion note; [Becker](https://www.jbecker.dev/research/prediction-market-microstructure)).
- **Longshot losses:** Bürgi, Deng & Whelan find Kalshi buyers of contracts under 10¢ lose over 60%, and takers lose about 32% on average against about 10% for makers. These are working-paper figures, and the averages are likely unweighted (companion note; [UCD WP2025_19](https://www.ucd.ie/economics/t4media/WP2025_19.pdf)).
- **Professional makers:** SIG became Kalshi's first official market maker, with reduced fees and higher position limits (a 2024 fact) — companion note; [Tradermath](https://www.tradermath.org/articles/prediction-markets-trading-at-quant-firms).
- **Incentive programs:** under Kalshi's Sports Prop Combo liquidity incentive program (LIP), 25% of fees from combos that include a prop are paid as monthly trading credits to makers in that prop's leg. The program runs to Jan 1 of next year (companion note; [Kalshi help center](https://help.kalshi.com/en/articles/17184676-sports-prop-combo-market-component-legs-liquidity-incentive-program)).
- **Combos:** combo takers' losses reportedly topped $1B, combo market makers' profit after fees was $519.8M, and Kalshi collected $88.9M in combo maker fees (companion note; [InGame](https://www.ingame.com/kalshi-parlay-taker-losses-top-1b/); unverified).
- **Kalshi vs. sportsbook vig:** ESPN reports Kalshi fees are usually cheaper than sportsbook vig, drawing pros and market makers who are "compensated to promote liquidity" (companion note; [ESPN, 2025](https://www.espn.com/espn/betting/story/_/id/45377686/kalshi-prediction-markets-disrupt-sports-betting)).
- **Polymarket US fees,** conflicting reports:
  - A sports taker coefficient of 5% (capped at $1.25 per 100 contracts at 50¢) with zero maker fees and volume rebates, on a July 1, 2026 schedule.
  - An April 3, 2026 schedule with a uniform 0.05 taker fee and a −0.0125 maker rebate.
  - A flat 0.30% taker fee with a 0.20% maker rebate.
  - Developer docs say fees should be read from each market's `feeSchedule` field, not hard-coded.
  
  Sources: [RiverMarkets](https://www.rivermarkets.com/insights/polymarket-us-fees.html); [Polymarket docs – fees](https://docs.polymarket.com/trading/fees); [KuCoin flash](https://www.kucoin.com/news/flash/polymarket-us-announces-0-01-taker-fee-on-total-contract-premium) (via search summary; unresolved).
- **Robinhood** costs about $0.02 per contract all-in (commission plus exchange fee) and has no API (see Q1).
- **US exchanges have struggled:** Prophet closed in NJ in 2024, calling the market anti-consumer, and Sporttrade acknowledged that competition, especially from prediction markets, hurt it — [Covers](https://www.covers.com/industry/prophet-exchange-closes-up-shop-for-now-june-25-2024); [Yogonet](https://www.yogonet.com/international/news/2026/05/19/121042-sporttrade-to-exit-us-online-sports-betting-markets-while-awaiting-cftc-decision) (via search summary).

### Inferences
- **Fee equivalence (my arithmetic from the cited fee formulas), for a contract fairly priced at 50¢:**

| Action | All-in cost per $1 payout | Decimal odds | American odds |
|---|---|---|---|
| Kalshi taker at 50¢ (no spread) | 51.75¢ | 1.932 | −107 |
| Kalshi taker at a 51¢ ask | 52.75¢ | 1.896 | −112 |
| Kalshi maker at 49¢, maker-fee series | 49.44¢ | 2.023 | +102 |
| Kalshi maker at 49¢, no maker fee | 49.00¢ | 2.041 | +104 |
| Sportsbook −110 | 52.38¢ | 1.909 | −110 |

  Taking on Kalshi is about as costly as betting into a −110 book. Making is the only side with a structural cushion, and that cushion disappears if fills are adversely selected.
- **Price-taking:** only the tail of the gap distribution clears the fee. That tail sits in fast-news moments, where the quote we would lift belongs to a faster maker about to pull it. With seconds-level latency we are on the losing side of that race.
- **Market making at our size:** the plausible net edge is a fraction of a percent of matched notional, after maker fees and adverse selection. Capacity is set by depth in less-trafficked series (props, smaller leagues), where LIP credits help. For a $1k–$25k book this is plausibly tens to low hundreds of dollars a month. That is speculative: I found no small-maker sports P&L.
- **Arizona-specific overlay:** capital and inventory on Kalshi could be forced to unwind if the injunction falls. Keep positions short-dated.

### Gaps
- No sports-specific maker/taker P&L table for Kalshi, and no small-maker track record.
- Polymarket US's actual sports fee schedule as of Nov 2026, and whether retail API keys are available.
- Kalshi position limits for non-market-maker accounts, and whether Kalshi pays interest on collateral (companion note also lists these as gaps).
- No liquidity data specific to Arizona users. The venues are national, so this probably does not matter.

## Q3. Sportsbook promotions converted with hedges ("matched betting") in Arizona: realistic EV, how fast accounts get limited, and whether it can be automated within ToS

### Takeaway
Promo conversion is the most dependable edge open to an Arizona resident, but most of it is one-time and has to be placed by hand; the bot acts as calculator and alerter.
- Hedged bonus bets typically convert to cash at about 65–75%.
- Large "first-bet insurance" offers are worth a few hundred dollars each.
- A full Arizona sign-up sweep is plausibly worth about **$1.5k–$3k pre-tax**. This is my estimate from mid-2026 offers; November terms are unverified.
- Reload value then decays as books promo-restrict hedgers.

Hedging on Kalshi beats hedging at another sportsbook by about 5 points of conversion on longshots, but it brings in the Kalshi legal risk. Two things can erase the profit: promo terms (betting both sides on one account is banned, voiding is possible) and the 2026 tax rules (Q7).

### Cited Findings
- **Arizona welcome offers.** These come from mid-2026 roundups, and several "Nov 3" pages are from earlier years, so treat them as indicative:
  - bet365: Bet $5, Get $200 in bonus bets, 1x wagering.
  - BetMGM: up to $1,500 in bonus bets if the first bet loses, or a 20% deposit match up to $1,500.
  - Caesars: bet $1 for 100% profit boosts on your next 20 bets ($10 minimum deposit).
  - FanDuel: $250 in bonus bets, paid as $50 a day for five days after a $5 bet.
  - DraftKings: $150 in bonus bets over 14 days after a $5+ bet.
  - Fanatics: up to $1,000 in no-sweat bets or a FanCash deposit match.
  
  Sources: [Rotowire AZ promos](https://www.rotowire.com/betting/arizona-betting-promos); [Rotowire BetMGM AZ](https://web9.rotowire.com/news/betmgm-arizona-bonus-code-rotosports-get-1500-in-bonus-bets-for-mnf-cardinals-vs-cowboys-odds-98156); [Fox Sports AZ](https://www.foxsports.com/stories/betting/arizona-sports-betting) (via search summary).
- Rotowire headlines put Arizona promo face value at "$6,300 in bonuses" (Aug 2026) and "$8,900" (Jan 2026). Headline face values overstate cash value — [Rotowire Aug 2026](https://www.rotowire.com/betting/arizona-betting-promos); [Rotowire Jan 2026](https://apps.rotowire.com/betting/promos/arizona).
- **Conversion benchmarks:**
  - About 70% or more counts as a "good" bonus-bet conversion. Conversion rises with the odds: +200 gives roughly 62–70%, depending on the table, and about +300 gives roughly 75%.
  - One guide values a $100 bonus bet at $65–$75 in cash.
  - Hedging a +1000 longshot could reach about 90% in theory, but needs a large bankroll.
  
  Sources: [Action Network – bonus bet conversion](https://www.actionnetwork.com/education/bonus-bet-conversion); [TopEndSports calculator](https://www.topendsports.com/sport/betting-tools/bonus-bet-calculator.htm); [OddCompare course](https://oddcompare.pages.dev/learn/bonus-betting/how-welcome-offers-work); [Action Network – no-sweat promos](https://www.actionnetwork.com/education/best-ways-to-use-first-bet-insurance-no-sweat-promos) (via search summary).
- **Academic model:** Whelan's "The Economics of Free Bets" models hedged stake-not-returned free bets. Rising expected value combined with falling conversion efficiency gives an optimum at "low, but not very low" win probabilities. Tennis quotes from two sportsbooks fit the model. His lecture slides give guaranteed profit per $1 free bet as Π = (1−m−p)(p−m)/(p(1−m)) under constant-margin pricing, where m is the per-side margin and p the win probability. With m = 0, Π = 1−p, the free bet's full EV (my check of the algebra) — [Whelan paper (dated March 2026 in search summary)](https://www.karlwhelan.com/Papers/FreeBets.pdf); [Whelan slides](https://www.karlwhelan.com/Teaching/BettingMarkets/14.SpecialsandFreeBets.pdf) (via search summary; the main-results section was not read).
- **Older US practitioner benchmark:** a Jan 27, 2022 EA Forum guide estimated about $500/hour for up to 17 hours of new-user promos across twelve US states. That reflects 2022's much richer launch-era promos — [EA Forum guide](https://forum.nunosempere.com/posts/29EZBsbLovTgu6C3B/ea-fundraising-through-advantage-sports-betting-a-guide) (older; via search summary).
- **Promo terms:** sportsbooks generally bar betting both sides, and at least one promo's terms make two-sided wagers disqualifying. But a book cannot see bets placed at competitors — [Spokesman-Review, Dec 2022](https://www.spokesman.com/stories/2022/dec/26/sportsbooks-call-them-risk-free-bets-just-dont-rea/); [theScore Bet promo T&Cs (example)](https://thescorebethelp.zendesk.com/hc/en-us/articles/42270284401293-NHL-Bet-Reset) (via search summary).
- **Bonus-abuse penalties** listed in operator terms include bonus cancellation, voided winnings, withdrawal restrictions and account closure. Operator-side 2026 playbooks describe detecting matched betting and arbitrage — [Track360 operator playbook 2026](https://track360.io/blog/matched-betting-arbitrage-bonus-abuse-detection-operator-playbook-2026); [iGaming Academy](https://igacademy.com/?p=29238) (via search summary).
- **Limits data (Massachusetts):**
  - 0.64% of bettors were limited (Dec 2024 snapshot, averaged over seven online books). 57.6% of those were cut to 1–24% of the default maximum bet, and 12.7% to under 1%.
  - Bettors who consistently won were more likely to be limited.
  
  Sources: [Covers](https://www.covers.com/industry/massachusetts-limiting-sports-betting-prediction-markets-exchanges-sharps-box-september-2025); [SBC Americas](https://sbcamericas.com/2025/09/30/mgc-data-limiting-bettors-ma/); [Birches Health](https://bircheshealth.com/resources/limiting-bettors) (via search summary).
- I found no dated, credible data on how quickly US books promo-restrict pure promo hunters, meaning books that stop sending boosts and bonuses rather than cutting stake limits.

### Inferences
- **Worked bonus-bet conversion (my arithmetic).** Take a $200 stake-not-returned bonus bet at +300 at the book.
  - **Hedge on Kalshi:** buy NO at 75¢ plus a 0.07 × 0.75 × 0.25 ≈ 1.31¢ fee. You need 600 contracts costing $457.88, which locks $142.12 either way (71% conversion). If the true probability is 23% (NO at 77¢), it locks about $131 (65%). Shopping the bonus bet to +330 at the same fair price lifts it to about $144 (72%).
  - **Hedge at another book at −360:** you need $469.56 on the other side, which locks $130.44 (65%).
  - Kalshi is worth about 5–6 points of conversion on longshots. Capital tied up until settlement is about $460–$520 per $200 of bonus bets.
- **Worked first-bet insurance (up to $1,500 back in bonus bets if the first bet loses), valuing bonus bets at 70%:**
  - **Even-money qualifier:** a $1,500 qualifier at −110 hedged on Kalshi at 51.75¢ locks about $425. A hedge at another book at −110 locks about $414.
  - **+300 qualifier:** hedged on Kalshi, it locks about $651 but ties up about $5.3k ($1,500 at the book plus $3,849 on Kalshi). Converting the $1,500 of bonus bets later needs about $3.4k more.
  - These offers fit the $1k–$25k bankroll and dominate sign-up value.
- **Profit boosts** (Caesars-style, 20 × 100%): at a $25 maximum stake on a roughly fair +100 line, each locks about $11 when hedged on Kalshi, so about $220 for 20. The per-boost maximum stake is unverified.
- **Arizona sign-up sweep estimate:**

| Offer | Estimated value |
|---|---|
| bet365 | ~$130–150 |
| FanDuel | ~$160–185 |
| DraftKings | ~$95–110 |
| BetMGM | ~$400–650 |
| Fanatics (structure uncertain) | ~$250–450 |
| Caesars | ~$150–220 |
| Five smaller books, ~$50–200 each | ~$250–800 |
| **Total, pre-tax, one-time** | **~$1.5k–$3k** |

  This rests on mid-2026 offer terms, so verify each.
- **Reloads** (weekly boosts, no-sweat parlays, insurance) could plausibly add a few hundred dollars a month across about 12 books at first, decaying as promo restrictions arrive. I found no credible US data to pin this down.
- **Speed of limits for promo-only accounts:** cross-venue hedging is invisible to the book, but the betting pattern is not: only boosted or promo lines, maximum stakes, no organic action. Expect promo restriction rather than stake limits, often within weeks to months. This is an inference; the Massachusetts data measures stake limits, not promo eligibility.
- **Automation within ToS:**
  - Fully automated bet placement at a sportsbook breaks ToS (bans on bots and "sniping" software) and the geolocation rules.
  - Scraping sportsbook odds may itself breach ToS, so use licensed odds APIs instead.
  - What can be automated: the scanner, choosing the best bonus target and hedge line, sizing, a checklist alert to a human, and placing the Kalshi hedge leg by API once the human confirms the sportsbook leg is accepted. That order avoids getting hedged on a bet the book rejected or repriced.
- **Settlement-rule mismatch** between a sportsbook leg and a Kalshi leg can turn a "lock" into a loss: overtime inclusion, postponements, voids, ties. Map each market's rules before hedging (inference; the companion note flags the same issue).

### Gaps
- Current (November 2026) Arizona promo terms: maximum stakes per boost, bonus-bet token splits, minimum odds and expiry. All are unverified.
- I found no US-specific, dated study of matched-betting income or time-to-promo-restriction.
- I found no ADG rule specifically addressing bonus hedging; it is governed by each operator's terms.

## Q4. Cross-venue arbitrage and middling between Arizona sportsbooks and Kalshi: frequency, size after fees, how long gaps last, and account-limit risk

### Takeaway
True arbitrage among US sportsbooks is rare, small and fleeting. In NBA live betting (FanDuel vs. BetMGM), arbs existed about 4.5% of game time and typically lasted about 13 seconds. Pre-game arbs exist, but taking them is the classic trigger for limits. Arbs against Kalshi in liquid games essentially never clear fees, and in-game gaps last about 6 seconds.

Under the 2026 rule that only 90% of gambling losses are deductible, a two-way arb below roughly 1.6–1.8% margin loses money after tax for an itemizer at a ~25% marginal rate, and nearly any arb loses for a non-itemizer (Q7). Middles at NFL key numbers (a 3-point margin in about 15% of games) can be clearly +EV when lines differ by a full point across 3, but such splits are rare and flag accounts.

### Cited Findings
- **NBA live arbitrage** (FanDuel vs. BetMGM, Princeton senior thesis): arbs were present in 4.52% of scraped game time and typically lasted about 13 seconds under favorable conditions. Practical limits included betslip reloads, site restrictions and account risk — [Princeton thesis](https://theses-dissertations.princeton.edu/entities/publication/437f7731-67ad-4af7-a1e6-648c1d003d46) (thesis; via search summary).
- **Market structure and arb duration:**
  - A cross-country study found monopolistic or tightly regulated markets (Finland, less robustly Switzerland) had longer-lasting arbs than liberalized markets. In Norway, arbs had a mean duration of 0 minutes and none exceeded 15 minutes — [UZH BA thesis](https://www.oec.uzh.ch/dam/jcr:190863d3-d0c0-4db6-9f19-59f20dfda7e0/BA%20Thesis%20Cambria.pdf) (thesis).
  - A University of Amsterdam master's thesis, built on a hand-collected database, found more competition was linked to longer-lasting arbs — [thesis PDF hosted by the Dutch gambling authority](https://kansspelautoriteit.nl/publish/pages/5547/scriptie_len_van_der_sluijs.pdf) (thesis; I inferred that this URL is the UvA thesis the search summary described).
  - Using sportsbook APIs, a Union College project found arbs at "fairly regular frequency", with ROI from a fraction of a percent up to about 20% — [Union College](https://steinmetz.union.edu/node/1441032168) (student work). My note: the upper figure likely reflects stale lines or data errors.
- **Bookmaker practice blocks arbs (peer-reviewed):** Grant et al. (2018, *European Journal of Finance*) found that competing bookmakers' prices do offer arbitrage, but bookmakers' management practices prevent informed bettors from exploiting it. They distinguish "position-takers" from "book-balancers" — [Nottingham eprints](https://eprints.nottingham.ac.uk/49935) (via search summary).
- **Arbs against prediction markets:** no liquid-game arb against Kalshi or Polymarket cleared fees. Gaps between Vegas lines and prediction markets were 1–4 points in inconsistent directions, mostly within the vig, and a fuzzy team-name matcher produced 18 false "arbs" (companion note; [VV1Git/sportstrades](https://github.com/VV1Git/sportstrades)).
- **Who gets limited and why:**
  - Pros name DraftKings, BetMGM and PointsBet as the harshest limiters and describe FanDuel as less harsh.
  - Common triggers are hitting stale lines before they adjust, and winning on player props.
  - FanDuel says exploiting "pricing inefficiencies" or market timing is not acceptable, and BetMGM says low-volume or unusual markets can lead to being backed off.
  - Once limited, most limited Massachusetts bettors were cut to 1–24% of the default maximum.
  
  Sources: [IBJ/AP](https://www.ibj.com/articles/sportsbooks-say-you-can-win-big-then-they-try-to-limit-winners); [Action Network – limits](https://www.actionnetwork.com/education/what-are-limits-sports-betting); [AlienWP summary](https://alienwp.com/massachusetts-sportsbook-limit-rule-what-bettors-need-to-know/) (weak source); [SBC Americas](https://sbcamericas.com/2025/09/30/mgc-data-limiting-bettors-ma/) (via search summary).
- **Operator limit rates:** BetMGM said it limits about 1% of Massachusetts patrons. FanDuel said 0.043% of bets were subject to maximum limits; that is a share of bets, not accounts — [WSN](https://www.wsn.com/betting/massachusetts-sportsbooks-limit-small-percentage-customers/); [Legal Sports Report](https://www.legalsportsreport.com/?p=201137) (via search summary).
- **Regulation of limits:** Massachusetts regulators voted to advance a rule requiring more transparency on limiting (Dec 2025); I could not confirm it was finalized. Arizona has no comparable rule that I found — [SBC Americas](https://sbcamericas.com/2025/12/18/massachusetts-sportsbooks-limiting/).
- **NFL key numbers:** a final margin of exactly 3 occurred in about 15.1% of games (1999–2025, 7,276 games) and exactly 7 in about 9.0%. Seven-point margins slid to about 7.7% in recent eras. Pushes at exactly 3 and 7 are reported at about 9.0% and 6.5% of spreads in one dataset — [DeucesCracked NFL margin data](https://www.deucescracked.com/blog/nfl-margin-of-victory-data-1999-2025); [DocSports 2026 study](https://www.docsports.com/2026/study-of-nfl-games-reveals-shifting-key-betting-numbers.html); [Covers key numbers](https://www.covers.com/nfl/key-numbers) (betting-education sources; approximate).

### Inferences
- **Arb arithmetic with a 2026 tax overlay** (my derivation from the cited 90% rule; see Q7):
  - Take a two-way arb staking S in total at roughly even odds, with margin r. The winning leg's profit is about rS + S/2 and the losing stake about S/2.
  - Taxable income for an itemizer is about (r + 0.05)·S, so after-tax profit ≈ S·[r(1−t) − 0.05t].
  - Break-even margin: r* ≈ 0.05t/(1−t). At t = 24.5% (22% federal + 2.5% Arizona) r* ≈ 1.6%; at t = 26.5%, about 1.8%; at t = 34.5%, about 2.6%.
  - Most real arbs are below 2%, so pure arbitrage is likely after-tax negative in 2026 unless the 90% rule is repealed retroactively (Q7) or the losses are otherwise deductible.
- **Speed:** at seconds-level latency with a human tapping, live arbs lasting about 13 seconds are mostly unreachable. In-play bet acceptance delays at books make this worse; I did not source their length. Pre-game arbs on stale soft lines last longer but are exactly the pattern books flag.
- **Arbs against Kalshi:** Kalshi tends to sit near the sharp price, so a "Kalshi arb" is really a sharp-vs-soft-book +EV bet with a hedge. It pays the hedge cost (taker fee plus spread) to remove variance, which is economically worse than the unhedged +EV bet (Q5) except when bankroll variance is binding.
- **Middle EV example (arithmetic):** take a favorite −2.5 at −110 at one book and the dog +3.5 at −110 at another. If the margin lands exactly on 3 (≈15%), both legs win (+2 units); otherwise one wins and one loses (−0.1 units). EV ≈ 0.15 × 2 − 0.85 × 0.1 = +0.215 units on 2.2 staked, about +9.8%.
  - Splits that wide across 3 at standard juice are rare and short-lived.
  - Half-point middles across non-key numbers are usually −EV after vig.
  - Kalshi lists spreads and totals at its own numbers, which may create more middle windows with a book. Unmeasured.
- **Account-limit risk:** arbing and middling are the fastest routes to limits because they systematically take off-market prices. Expect a limited lifetime per book (weeks to months; see Q5) and treat each account as a consumable.

### Gaps
- I found no US pre-game study of arb frequency and duration across Arizona-available books, and no study of Kalshi-vs-sportsbook middle frequency.
- I did not source in-play bet acceptance delays at US books.
- Arizona-specific evidence on limiting: none found. Massachusetts data is the best proxy.

## Q5. Positive-EV betting against sharp lines (beating the closing line, with sharp books as the reference): does it work for small players, and how quickly do books limit them?

### Takeaway
This has the best evidence of any small-player method. The logic: treat de-vigged sharp or consensus prices as fair, and bet soft-book prices that beat them.
- Kaunitz, Zhong & Kreiner made money with exactly this rule: +5.5% in live paper trading, then real money, until bookmakers restricted them within weeks to months.
- Closing-line value (CLV) against a de-vigged sharp close is the accepted fast test of skill.

In the US it is a wasting asset:
- Winners get limited, fastest on props and stale-line steam.
- Once limited, stakes shrink to a few percent of the normal maximum.
- Pinnacle closed its public API in July 2025, so a sharp reference now costs money.
- The 2026 90% loss rule takes roughly 1.2–1.3 points of after-tax yield on even-money bets at about a 25% marginal rate (Q7).

Expect a positive but small and front-loaded result: plausibly low thousands to about $10k in total across Arizona books before limits, pre-tax. That figure is speculative.

### Cited Findings
- **Kaunitz, Zhong & Kreiner (2017):**
  - They tested a consensus-anchored strategy on 479,440 soccer games (2005–2015) with closing odds, ran a 6-month simulation on minute-by-minute odds, then staked real money for 5 months.
  - Live paper trading returned 5.5%: $1,128.50 on 407 bets of $50.
  - Bookmakers then limited stakes or required "manual inspection". Coverage disagrees on timing, a few weeks versus a few months.
  - The authors conclude bookmakers don't accept consistent winners.
  
  Sources: [arXiv 1710.02824](https://arxiv.org/abs/1710.02824); [MIT Technology Review](https://www.technologyreview.com/2017/10/19/67760/the-secret-betting-strategy-that-beats-online-bookmakers/) (via search summary; older but foundational).
- **CLV predicts profit:** Buchdahl reportedly showed, across about 10,000 matches, that a bet's price relative to Pinnacle's closing price was a very reliable indicator of profitability (companion note; [Pinnacle Odds Dropper](https://www.pinnacleoddsdropper.com/blog/closing-line-value--clv-demystified-by-expert-joseph-buchdahl); via search summary).
- **Sharp closing prices are well calibrated:** an analysis of football-data.co.uk data (193,803 matches) found Pinnacle closing odds well calibrated, and closing odds fold in traders' information (companion note; [football-data.co.uk](https://football-data.co.uk/blog/pinnacle_efficiency.php); [arXiv 2010.12508](https://arxiv.org/pdf/2010.12508)).
- **Data access:**
  - Pinnacle closed its API to the general public on July 23, 2025.
  - Third-party feeds exist: The Odds API offers a free tier, then $30–$249/month by credits, with featured-market updates about every 60 seconds pre-match and 40 seconds in-play.
  - Pinnacle itself is offshore and not available to US persons for betting.
  
  Companion note; [pinnacleapi-documentation](https://github.com/pinnacleapi/pinnacleapi-documentation); [The Odds API](https://the-odds-api.com/).
- **Limits data and triggers:** see Q4. Massachusetts: 0.64% of accounts limited, and consistent winners more likely. Triggers include stale lines and props. FanDuel says exploiting "pricing inefficiencies" is not acceptable.
- **Speed of limiting:** I found no source giving a time-to-limit in weeks for DraftKings or FanDuel. Reporting says savvy bettors are being restricted faster than before — [Defector](https://defector.com/the-government-is-letting-sports-books-screw-you); [Bleacher Nation](https://www.bleachernation.com/?p=2219780) (weak) (via search summary).
- **Circa Sports** is licensed in Arizona, with an early-2027 launch target (Q1).

### Inferences
- **Soundness:** the method is sound because it does not require out-predicting the market. It exploits soft books lagging the sharp consensus. The edge per bet is the gap between the soft price and the de-vigged sharp price, which a CLV log validates within a few hundred bets rather than thousands.
- **Expected yield and capacity (speculative):**
  - Typical claimed edges are 1–4% of turnover.
  - Before limiting, a book might take roughly $5k–$30k of turnover from an account like ours, which is $100–$1,200 of EV per book. Across about 12 Arizona books that is about $1k–$14k total, front-loaded, with props limited fastest.
  - After limiting, stakes fall to about 1–24% of the maximum (Massachusetts data), and the account mainly serves promos, if those survive.
- **After-tax yield** (Q7 formula): an even-money edge e becomes about e(1−t) − 0.05t. At t = 24.5%, a 3% edge leaves about 1.0% after tax and a 2% edge about 0.3%. Edges below about 1.6% go negative even for itemizers.
- **Reference choice:** with Pinnacle's API closed, use a commercial multi-book consensus that includes sharper books. Kalshi or Polymarket mid prices can also serve as a sharp-ish reference for main markets, since they sit within about 0.6–0.75 pp of Pinnacle per the vendor data in Q2. Circa's Arizona launch (about 2027) would add a sharp-ish US reference, and possibly higher limits; that is unverified.
- **Fit for us:** good as semi-automation. The bot computes de-vigged fair prices, flags soft-book prices beyond a threshold, sizes bets (fractional Kelly), logs CLV, and a human places the bet. Paper-test by logging hypothetical bets against the close for 2–4 weeks before staking; CLV is measurable without money.

### Gaps
- I found no US-specific, dated study of time-to-limit for +EV bettors, and no US replication of Kaunitz on American books and sports.
- Whether Circa will offer high limits to winning Arizona bettors when it launches: unverified.
- Commercial +EV tool pricing and feed latency beyond The Odds API (OddsJam, OpticOdds, Unabated and others): not sourced here.

## Q6. Statistical/model edges with credible evidence of after-vig profitability, and survivorship bias in public tipster claims

### Takeaway
The peer-reviewed evidence is discouraging for "predict the game better" models in major markets. Moskowitz (*Journal of Finance*, 2021) finds momentum and value patterns in betting prices about one-fifth the size of those in financial markets, too small to beat transaction costs. Sharp closing prices are well calibrated.

The credible after-cost edges on record are structural, not predictive:
- soft books lagging consensus (Kaunitz), which is limited quickly;
- favorite–longshot bias on Kalshi, earned mainly by makers.

Public tipster records suffer from heavy survivorship and selection bias. One comparative soccer study found tipster forecasts worse than betting odds and prediction markets. I found no rigorous public audit showing that a meaningful share of tipsters beat the closing line over time.

### Cited Findings
- Moskowitz, "Asset Pricing and Sports Betting", *Journal of Finance* 76(6), 2021, pp. 3153–3209: returns from return-predictability factors in betting markets "are a fraction of those in financial markets and fail to overcome transactions costs, preventing arbitrage from eliminating them". A summary puts predictability at about one-fifth of financial markets — [RePEc](https://econpapers.repec.org/RePEc:bla:jfinan:v:76:y:2021:i:6:p:3153-3209); [Chicago BFI](https://bfi.uchicago.edu/insights/asset-pricing-and-sports-betting/); [Alpha Architect](https://alphaarchitect.com/value-momentum-sports-betting/) (via search summary).
- An early Booth write-up of the same research says the roughly 10% vig "cuts deeply into" statistically possible profits (presentation-stage; verify) — [Chicago BFI news](https://bfi.uchicago.edu/news/what-losing-50-on-a-football-game-can-teach-us-about-financial-markets/).
- Blindly backing everything at Pinnacle's close lost about 4.92% in one replication (31,550 matches). Results sat about 1% from fair implied probabilities (companion note; [Football Trading Academy](https://footballtradinga.com/pinnacle-odds/); promotional, thin method).
- On Kalshi, a favorite–longshot bias is documented: sub-10¢ contracts lose more than 60%, and a difference-in-differences test found no detectable change in the bias from the fee change. The maker side captures the transfer (companion note; [UCD WP2025_19](https://www.ucd.ie/economics/t4media/WP2025_19.pdf); [Vladosyna replication](https://github.com/Vladosyna/kalshi-makers-takers-persistence)).
- One vendor claims a study of over 600M MLB player-prop line movements found Kalshi posting the sharpest prices. If true, Kalshi may lead rather than lag on props (companion note; [SmartStake](https://www.smartstake.app/learn/kalshi-vs-sportsbook); vendor, method unread).
- A soccer forecasting study found tipster forecasts inferior to those from bookmakers and prediction markets. This is probably Spann & Skiera, but authorship was not confirmed, and I could not tell which of two core.ac.uk results carries the finding — [core.ac.uk PDF 1](https://core.ac.uk/download/42149577.pdf); [core.ac.uk PDF 2](https://core.ac.uk/download/156785178.pdf) (via search summary).
- A tipster-platform analysis notes survivorship: tipsters with poor records are less likely to still be posting after 1,000 tips. It is a single company's dataset with no percentage — [Stockomendation](https://stockomendation.com/blog/august-10-2018) (weak).
- Pyckio says it selects "PRO" tipsters with an algorithm designed by two economics PhDs. I found no published hit rates from that algorithm — [El Referente](https://elreferente.es/?p=15907); [Merca2](https://www.merca2.es/2018/05/18/tipster-corredor-bolsa-millennials-63597/) (via search summary; older; I could not tell which of the two pages carries the quote).

### Inferences
- Survivorship mechanics: thousands of tipsters post, and the ones visible after a year or two are, by construction, the lucky tail. Advertised yields are usually measured against the tipster's own posted odds, not the closing line, and on unverified stake sizes. Any third-party claim should be re-graded on CLV against a de-vigged sharp close with every pick timestamped before the move; otherwise treat it as noise.
- Where model edges plausibly exist for us: soft or niche markets (props, small leagues, WNBA, small-college) at sportsbooks, where sharp references are weak and books price off feeds. These are also the markets books limit fastest. Main-market sides and totals are where academic evidence says models do not beat costs.
- Our own model is unlikely to beat the de-vigged sharp close in major markets. Its best use is as a fair-value tool in thin markets, or as a filter on the +EV scanner, not as a stand-alone edge.

### Gaps
- I could not locate Buchdahl's tipster analyses (e.g. in *Squares & Sharps*) or a quantitative public audit of what share of tipsters beat the close.
- I found no peer-reviewed US-market (NFL/NBA/MLB) study from 2023–2026 showing a model-based strategy profitable after vig out of sample.

## Q7. Arizona-specific rules: age, location verification, tax treatment, automation bans

### Takeaway
- **Eligibility:** you must be 21 or older, physically in Arizona at the time of each bet (geofenced under A.A.C. R19-4-117), and pass account checks for self-exclusion, child-support arrears and state debts.
- **State tax:** Arizona taxes gambling winnings at its flat 2.5% income-tax rate (withholding is also 2.5%).
- **Federal tax:** for 2026, the One Big Beautiful Bill Act (OBBBA) caps the gambling-loss deduction at 90% of losses (and still at winnings). Losses help only if you itemize. A repeal cleared House Ways & Means 38–5 on Sept 16, 2026 but is not law.
- **Event contracts:** the tax treatment of Kalshi sports contracts is unresolved (gambling vs. capital gains vs. Section 1256).
- **Automation:** I found no Arizona regulation specific to bots, but operator ToS ban automation, and geolocation makes server-side betting impossible anyway.

The tax rules are the hidden killer of high-turnover, thin-margin strategies (arbitrage, matched betting, low-edge +EV), especially for someone who does not itemize.

### Cited Findings
- Operators must confirm a patron is at least 21, not self-excluded and not otherwise barred (citing A.R.S. § 5-1311(B), A.A.C. R19-4-133). They also check for outstanding child support, state tax debt and debts to the Arizona Department of Economic Security (citing A.R.S. §§ 5-1302(G)(7), 5-1320(F)) — [ADG letter to CFTC, June 2, 2025](https://www.ingame.com/wp-content/uploads/2025/06/Arizona-Dept-Gaming-Letter-CFTC-June-2-2025.pdf) (via search summary).
- Operators must geolocate so that only people located in Arizona wager, and a patron located outside the state is blocked (A.R.S. § 5-1302(G)(2); A.A.C. R19-4-117). A 2022 bill summary describes a check before each wager plus recurring checks during a session — [Cornell LII – R19-4-117 Geofencing](https://www.law.cornell.edu/regulations/arizona/Ariz-Admin-Code-SS-R19-4-117); [ADG letter to CFTC](https://www.ingame.com/wp-content/uploads/2025/06/Arizona-Dept-Gaming-Letter-CFTC-June-2-2025.pdf); [AZ Legislature summary](https://azleg.gov/legtext/55leg/2R/summary/S.1442COM.DOCX.htm) (via search summary).
- ADG rules define a "player account" as an account a patron opens with a responsible party to place event wagers — [Cornell LII – R19-4-101](https://www.law.cornell.edu/regulations/arizona/Ariz-Admin-Code-SS-R19-4-101).
- Arizona taxes gambling winnings as ordinary income at the flat 2.5% rate, which replaced earlier progressive rates. Arizona gambling withholding was lowered to 2.5% — [DeucesCracked – AZ taxes](https://www.deucescracked.com/sports-betting/us/arizona/taxes); [Sovos](https://sovos.com/regulatory-updates/trr/arizona-lowers-gambling-withholding-rate-to-2-5/) (via search summary).
- **Federal 90% rule:** from 2026 returns, OBBBA limits the gambling-loss deduction to 90% of losses, still capped at winnings. The disallowed 10% does not carry forward — [Porte Brown](https://www.portebrown.com/newsblog-archive/new-law-reduces-tax-odds-for-gamblers); [Clarity Tax Counsel](https://claritytaxcounsel.com/guides/90-percent-gambling-loss-rule); [AZFamily, July 2025](https://www.azfamily.com/2025/07/08/new-tax-law-caps-gambling-loss-deductions-under-trump-budget/) (via search summary).
- Gambling losses are deductible only if you itemize, and only up to winnings — [AZFamily](https://www.azfamily.com/2025/07/08/new-tax-law-caps-gambling-loss-deductions-under-trump-budget/); [DeucesCracked – AZ taxes](https://www.deucescracked.com/sports-betting/us/arizona/taxes) (via search summary).
- **Repeal status:**
  - On Sept 16, 2026, House Ways & Means voted 38–5 to restore the full deduction, folded into H.R. 10357 (Digital Asset Tax Certainty Act). If enacted, it would apply to tax years beginning after Dec 31, 2025; JCT scores it at about $2B over 2027–2036.
  - A separate attempt to attach the FAIR BET Act to the NDAA was declined by the House Rules Committee.
  - No floor vote was expected before the November midterms, and the Senate would still need to act.
  
  Sources: [Covers](https://www.covers.com/industry/house-committee-advances-repeal-of-90-percent-gambling-loss-deduction-limit-sept-16-2026); [Las Vegas Sun](https://lasvegassun.com/news/2026/sep/17/house-ways-and-means-committee-advances-bill-to-re/); [GamblingTaxHelp](https://www.gamblingtaxhelp.com/repeal-efforts/) (via search summary).
- **Prediction-market tax treatment is unresolved:**
  - Sources variously describe Kalshi gains as gambling income, ordinary income or short-term capital gains, or possibly Section 1256 contracts (60/40).
  - They conflict on whether Kalshi issues 1099-MISC or 1099-B.
  - Whether Kalshi sports contracts count as "wagering" under the 90% rule awaits IRS guidance, which had not been issued as of May 2026.
  
  Sources: [Keeper Tax](https://www.keepertax.com/posts/how-to-file-taxes-on-kalshi-and-polymarket); [CoinLedger](https://coinledger.io/blog/prediction-markets-tax); [Oddschecker, Oct 31 2026](https://www.oddschecker.com/us/insight/specials/politics/20261031-do-you-pay-tax-on-prediction-market-winnings); [Robinhood – event contract taxes](https://robinhood.com/us/en/support/articles/event-contracts-taxes-statements/) (mostly tax blogs; via search summary).
- I found no Arizona rule on bots or automated wagering. Operator ToS ban automation (Q1), and some other states (Michigan) require operators to ban bots — [Cornell LII – Mich. R 432.752](https://www.law.cornell.edu/regulations/michigan/Mich-Admin-Code-R-432-752).

### Inferences
These are not tax advice. They assume per-wager accounting (each winning bet's profit counts as winnings and each losing stake as a loss), which I believe is the IRS default for sports wagering; there is no formal session method for sports.

- **The 90% rule taxes turnover, not just profit.** For an itemizer, taxable income from a betting program ≈ profit + 10% × (total losing stakes). On even-money bets, losing stakes are about half of turnover, so phantom taxable income is about 5% of turnover. After-tax yield on turnover ≈ e(1−t) − 0.05t, giving a break-even edge of about 1.6% at t = 24.5% (22% federal + 2.5% Arizona) and 1.8% at t = 26.5%. This applies to +EV betting, arbitrage and the hedge legs of matched betting.
- **The standard-deduction trap is worse.** Someone who would otherwise take the standard deduction (about $16k for a single filer in 2026; not verified this session) gets little or no benefit from gambling losses until itemized deductions exceed it. Gross winnings are then taxed almost in full.
  - Example: a promo sweep with $15k gross winnings, $12k losses and $3k economic profit, for a single filer with about $4k of other itemized deductions. They still take the standard deduction, so taxable income rises by the full $15k: about $3.7k of federal plus Arizona tax, a net loss of about $700.
  - Unless the repeal passes retroactively, promo conversion and arbitrage at scale only make after-tax sense for someone who itemizes heavily, or who can use professional-gambler (Schedule C) treatment. Schedule C keeps the standard deduction but adds self-employment tax and still has the 90% cap. I did not source the professional-status test.
- **Mixed-venue hedges are asymmetric.** If Kalshi legs are capital (or Section 1256) while sportsbook legs are gambling, the two legs of a hedge land in different tax baskets. Worst case: the sportsbook leg wins (gambling income, fully taxable) and the Kalshi leg loses (a capital loss, usable only against capital gains plus $3k a year). This needs a CPA before any scaled hedged program.
- Whether Arizona follows the federal 90% rule and itemized-loss treatment is unknown. Arizona starts from federal AGI, which already includes gross winnings.
- **Location compliance:** every sportsbook bet must come from a device physically in Arizona and pass the operator's geolocation. For Kalshi, if Arizona sports trading is later geofenced, a cloud server elsewhere must not be used to keep trading; that is circumvention, which is excluded.

### Gaps
- Arizona Department of Revenue treatment of gambling losses and conformity to OBBBA's 90% rule: not found.
- Whether OBBBA raised the W-2G reporting threshold (I recall $2,000 but did not confirm it this session).
- IRS position on Kalshi sports contracts: no IRS guidance found.
- No Arizona-specific rule on automated wagering found. I could not read DraftKings' Arizona terms or FanDuel's sportsbook (non-DFS) terms in full.

## Q8 (Objective). Strategy-by-strategy inventory: does each net money after the venue's cut for us?

### Takeaway
For an Arizona resident in November 2026, the only strategies with a better-than-even chance of netting money after the venue's cut are:
1. One-time sign-up promo conversion: about $1.5k–$3k pre-tax; 85% confidence.
2. Soft-book +EV betting against de-vigged sharp prices: small and front-loaded until limits; about 55% confidence.
3. Reload promos: about 55% confidence.

All three are semi-automated: the bot computes, a human places sportsbook bets. Kalshi-based automated strategies (sharp-anchored market making, the longshot fade) are the only fully automatable ones. They are modest-confidence (about 20–25% after the Arizona legal haircut) and could be shut off for Arizona at any time by the pending Ninth Circuit appeal. Pure arbitrage, middling, in-play sniping, own models in major markets, and tipsters are poor bets. P2P exchange strategies have no legal Arizona venue.

Separately from fees, the 2026 tax rules can make thin-margin, high-turnover strategies after-tax negative. Get a tax plan before scaling anything.

### Cited Findings
- **Sportsbook strategies:** Q3–Q5 evidence. Promo conversion runs about 65–75%; Kaunitz's consensus edge was +5.5% in paper trading, with restriction within weeks to months; Massachusetts limit data; arbs last about 13 seconds in NBA live betting.
- **Kalshi strategies:** Q2 evidence. Taker fee about 1.75¢ at 50¢; main markets within about 0.75 pp of Pinnacle; makers +1.12% gross; favorite–longshot bias.
- **Moskowitz:** factor predictability in betting does not beat costs (Q6).
- **Regulatory status of each venue:** Q1. **Tax rules:** Q7.
- The companion Kalshi-only note gives these confidences for a durable after-fee edge for a US trader: longshot fade 28%, sharp-anchored making 25%, thin-market anchoring 18%, main-market taker anchoring 10%, combo making 10%, steam sniping 7%, in-game 4%, cross-venue arbitrage 4% (companion note).

### Inferences
Each confidence is my estimate that the strategy nets positive after the venue's cut over about 12 months for our setup, before income tax unless noted. After-tax notes refer to Q7.

#### S1. Sign-up promo conversion ("matched betting") across Arizona sportsbooks
- **Logic, sound:** welcome offers have positive cash value. Hedging the qualifier and the bonus bets on another venue locks most of it in.
- **Evidence, credible:** an academic model (Whelan) plus consistent practitioner conversion benchmarks of about 65–75%. Offer terms are from mid-2026 roundups.
- **Fees and capacity:** the cost is book vig on qualifiers and hedges (about 4.5% on −110 markets) or the Kalshi taker fee (about 1.3–1.75¢ per contract). Capacity is one-time: roughly $1.5k–$3k across about 12–13 Arizona books.
- **Infrastructure and capital:** a calculator or scanner plus an odds feed (free–$59/month), with manual placement and an optional Kalshi API hedge. Peak capital is about $3–6k for the large insurance offers.
- **Risks:**
  - Promo-term breaches if both sides are bet on one account, which also risks bonus voiding.
  - Promo restriction.
  - Settlement-rule mismatch on cross-venue hedges.
  - Kalshi regulatory risk if it is the hedge venue (fall back to a book hedge at about 5 points lower conversion).
  - The standard-deduction tax trap.
- **Fit:** high. It is simple and the bankroll fits.
- **Confidence of netting positive:** 85% pre-tax. After tax it depends on itemizing (Q7); it can be negative for a non-itemizer.

#### S2. Ongoing reload promos (profit and odds boosts, no-sweat bets and parlays, insurance, loyalty bonuses)
- **Logic, sound:** boosts are +EV when the boosted price beats fair, and they can often be hedged.
- **Evidence, weak:** practitioner claims only; no credible US data on income or decay.
- **Fees and capacity:** small maximum stakes ($10–$50 typical; unverified). Plausibly $100–$500/month early on, decaying.
- **Infrastructure:** a boost scanner (boosts appear in apps, and scraping breaches ToS) plus manual entry. Low capital.
- **Risks:** promo restriction, effort per dollar, and ToS.
- **Fit:** moderate. It is human-time-intensive.
- **Confidence:** 55%.

#### S3. Soft-book +EV betting against de-vigged sharp or consensus prices (pre-game; main markets plus props)
- **Logic, sound:** soft books lag the sharp consensus.
- **Evidence, the best available:** Kaunitz et al. paper and real money, plus the CLV literature. No US replication.
- **Fees and capacity:** vig is built into the price. The edge is the gap to fair, typically 1–4%. Capacity is limited per account by stake limits (most limited bettors are cut to 1–24% of the maximum): perhaps $1k–$14k total EV across Arizona books, front-loaded (speculative).
- **Infrastructure and capital:** a multi-book odds feed including sharp books ($30–$250+/month; Pinnacle's API is closed), a de-vig engine, CLV logging, and manual placement. $2k–$10k spread across books.
- **Risks:** fast limiting (props and steam fastest), data cost, and the after-tax yield haircut of about 1.2–1.3 points at even money.
- **Fit:** good as semi-automation. Paper-test cheaply by logging CLV before staking.
- **Confidence:** 55% pre-tax; about 45% after tax for an itemizer.

#### S4. Pure arbitrage among Arizona sportsbooks (pre-game and live)
- **Logic:** sound in theory, but bookmakers manage it away (Grant et al.).
- **Evidence:** arbs are rare and fleeting (about 13 seconds and about 4.5% of game time in NBA live betting).
- **Fees and capacity:** margins are mostly under 2%, and stake limits on the soft leg cap capacity.
- **Infrastructure:** a scanner plus fast manual placement on two apps at once.
- **Risks:** one leg rejected or repriced (a naked position), limits, voided "palpable error" bets, and the 2026 tax break-even of about 1.6–1.8% margin.
- **Fit:** poor at seconds-level latency with a human tapping.
- **Confidence:** 15% pre-tax; about 5% after tax.

#### S5. Sportsbook-vs-Kalshi price arbitrage (no promo)
- **Logic:** Kalshi tends to be the sharp side, so this is really S3 with a costly hedge.
- **Evidence:** the open-source scanner found no liquid-game arbs after fees; in-game gaps last about 6 seconds.
- **Fees:** taker fee plus spread on Kalshi, plus vig on the book.
- **Infrastructure:** Kalshi API plus a manual book leg.
- **Risks:** Kalshi Arizona legal risk, rule mismatch and limits.
- **Fit:** poor.
- **Confidence:** 10%.

#### S6. Middling (NFL key numbers 3 and 7; NBA and college totals; Kalshi alternate lines against books)
- **Logic, sound** when the split crosses a key number at near-standard juice (about +10% EV for a full point across 3 at −110 both sides).
- **Evidence:** the key-number frequencies are solid; how often such splits occur in Arizona is unmeasured.
- **Capacity:** rare, and the triggering line move is the stale-line pattern books limit.
- **Infrastructure:** a line-history scanner and manual placement.
- **Risks:** limits; Kalshi legal risk if Kalshi lines are used.
- **Fit:** opportunistic add-on to S3.
- **Confidence:** 25% pre-tax.

#### S7. Kalshi taker sharp-line anchoring (main pre-game markets)
- **Logic:** good for valuation, weak as an edge, because the median gap is below the fee.
- **Evidence:** vendor and open-source measurements (companion note).
- **Fit:** full automation is possible but loses the latency race to professional makers.
- **Confidence:** 10%; the companion note also gives 10%.

#### S8. Kalshi passive market making anchored to sharp prices (plus LIP credits) in less-trafficked sports series
- **Logic, sound:** it sits on the side of the documented maker–taker transfer.
- **Evidence:** Becker and Vladosyna replications, gross of fees; no small-maker sports P&L.
- **Fees:** maker fee about 0.44¢ at 50¢ in maker-fee series.
- **Capacity:** small; tens to low hundreds of dollars a month at our size (speculative).
- **Infrastructure:** Kalshi WebSocket plus write tier, and a fast sharp feed for cancels.
- **Risks:**
  - Adverse selection on news.
  - Queue competition from SIG-class firms.
  - A forced Arizona exit if the injunction is dissolved.
  - Unresolved tax treatment.
- **Paper test:** unreliable for queue position, so test live at tiny size.
- **Confidence:** 20%. The companion note gives 25% nationally; I cut it for Arizona legal risk.

#### S9. Kalshi favorite–longshot fade (buy NO at 90¢+ on longshot futures or props priced above sharp futures)
- **Logic, sound:** the bias is documented on Kalshi across categories.
- **Fees:** small at high prices (about 0.6¢ or less per contract).
- **Capacity:** capital-heavy, with tail risk per position.
- **Arizona-specific risk:** long-dated futures could be stranded or force-closed if Arizona is geofenced, so prefer short-dated props.
- **Confidence:** 20%. The companion note gives 28% nationally; I cut it for Arizona and capital lock-up.

#### S10. Own predictive models in major markets (NFL/NBA/MLB sides and totals)
- **Logic:** weak against efficient closing lines.
- **Evidence:** Moskowitz finds factor edges do not beat costs; sharp closes are well calibrated.
- **Confidence:** 10%.

#### S11. Models or sharp-anchoring in niche and soft markets at sportsbooks (player props, small leagues, WNBA, small-college)
- **Logic, plausible:** books price these off feeds, and sharp references are weak.
- **Evidence:** anecdotal. Props are the leading trigger for limits.
- **Capacity:** low stake limits.
- **Confidence:** 30% pre-tax, short-lived.

#### S12. In-play stale-line sniping at sportsbooks
- Banned by ToS ("sniping software"), blocked in practice by bet acceptance delays, and requires automation we cannot legally run. Human speed is not enough.
- **Confidence:** 5%. Not recommended.

#### S13. Correlated same-game-parlay mispricing at sportsbooks
- **Logic:** books sometimes misprice correlation. They also restrict correlated parlays, void "related contingencies" and limit winners.
- **Evidence:** none sourced here. Combo takers on Kalshi lost more than $1B (companion note; unverified), which suggests combos are a sink for retail money, not a source.
- **Confidence:** 15%.

#### S14. Following tipsters or paid picks
- Survivorship bias, no CLV audits, and subscription cost.
- **Confidence:** 5%.

#### S15. Licensed P2P exchange trading or market making (Betfair-style back/lay)
- No licensed Arizona venue (Q1), so this is infeasible. Watch for Sporttrade, ProphetX or Novig relaunching as CFTC venues; any such relaunch would face the same Arizona-versus-CFTC dispute as Kalshi.

#### S16. Sweepstakes and unlicensed P2P sports venues (Novig, ProphetX sweepstakes, BetOpenly, offshore books)
- Excluded: they are unavailable in Arizona or under ADG cease-and-desist, and using them would require evading geolocation or Arizona law.

#### S17. Prediction-market cross-venue arbitrage (Kalshi vs. Polymarket US vs. Robinhood)
- Prices sit within about 1¢. Polymarket US sports availability in Arizona is contested, and Robinhood has no API.
- **Confidence:** 5%.

#### Summary ranking (confidence of netting positive after the venue's cut, pre-income-tax, for an Arizona-based small bot)

| Rank | Strategy | Automation | Confidence | Main limiter |
|---|---|---|---|---|
| 1 | S1 Sign-up promo conversion | Semi (human places bets) | 85% | One-time; promo terms; tax trap |
| 2 | S3 Soft-book +EV vs sharp prices | Semi | 55% | Limits in weeks to months; data cost; 90% rule |
| 3 | S2 Reload promos | Semi | 55% | Promo restriction; small size |
| 4 | S11 Niche/prop edges at books | Semi | 30% | Fastest limits |
| 5 | S6 Middling | Semi | 25% | Rare; flags accounts |
| 6 | S8 Kalshi sharp-anchored making | Full (API) | 20% | Adverse selection; Arizona legal risk |
| 6 | S9 Kalshi longshot fade | Full (API) | 20% | Tail risk; Arizona legal risk |
| 8 | S4 Sportsbook arbitrage | Semi | 15% | Rare and fleeting; tax break-even about 1.7% |
| 8 | S13 Correlated SGP pricing | Semi | 15% | Book controls; limits |
| 10 | S5 Sportsbook vs. Kalshi arbitrage | Semi + API | 10% | Fees; Kalshi sits at the sharp price |
| 10 | S7 Kalshi taker anchoring | Full | 10% | Fee exceeds the typical gap |
| 10 | S10 Own models, major markets | Any | 10% | Efficient closes |
| 13 | S12 In-play sniping | Not allowed | 5% | ToS; bet delays |
| 13 | S14 Tipsters | – | 5% | Survivorship |
| 13 | S17 Prediction-market cross-venue arbitrage | Partial | 5% | Prices within 1¢; Arizona access |
| – | S15 / S16 P2P exchanges and sweepstakes | – | n/a (no legal venue or excluded) | – |

- **Practical sequencing for "us":**
  1. Build the de-vig and CLV logger and the promo calculator first. They feed S1, S3 and S6, and the bot can run them in Arizona without breaching any ToS.
  2. Do the S1 sign-up sweep manually, with hedges on Kalshi while it remains available, and at books otherwise.
  3. Run S3 on paper (log CLV) for 2–4 weeks before staking.
  4. Run Kalshi S8 and S9 only at tiny live size, given queue realism and the pending Ninth Circuit ruling.
  5. Before any of it, settle the tax plan: itemize, professional-gambler status, and how to treat Kalshi legs.

### Gaps
- No credible, dated US source quantifies ongoing promo income, time-to-limit for +EV bettors, or Arizona sportsbook stake limits by market.
- Kalshi's Arizona availability could change at any time (Ninth Circuit motion pending; Supreme Court petition in the NJ case). No ruling was found after late September 2026.
- Tax: IRS treatment of Kalshi sports contracts and Arizona conformity are unresolved, as is whether the 90% repeal will pass retroactively for 2026. Each could swing the after-tax ranking of S1–S6.
- Every profit, capacity and conversion figure in these inferences is my own arithmetic or estimate from the cited inputs, not a measured track record.
