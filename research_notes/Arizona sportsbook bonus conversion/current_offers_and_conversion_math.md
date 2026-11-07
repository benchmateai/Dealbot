# Arizona sportsbook sign-up and reload promotions (as of 2026-11-07): per-book inventory, conversion math, realistic net, bankroll and pitfalls

Method note. Direct page fetches failed in this session: www.covers.com, www.sportsbookreview.com and www.si.com would not resolve (blocked by the session's network allowlist). Every fact below therefore comes from search-engine summaries of the cited pages ("via search summary"); I read none of the pages in full. Where I say an offer is "confirmed on the book's own page", I mean the search engine summarized a page on the operator's own domain (fanduel.com, az.betmgm.com, caesars.com, bet365.com, hardrock.bet, help.betdesertdiamond.com, ballybet.com, thescorebethelp.zendesk.com). Before staking money, re-read each offer in the app while geolocated in Arizona.

All dollar values, conversion rates, hedge sizes and totals under "Inferences" are my own arithmetic. I ran them in a short script, and they rest on the cited terms and illustrative odds. They are not measured track records.

This note does not repeat the venue landscape, the Kalshi legal status or the 2026 tax rules. Those are in `research_notes/Viable trading strategies across venues/arizona_sports_betting.md` (dated 2026-11-04), cited below as "the earlier note".

Notation used throughout:
- **American and decimal odds.** +300 means decimal 4.00; −360 means decimal 1.278.
- **c** is the bonus-bet conversion rate: the share of a bonus bet's face value that ends up as withdrawable cash.
- **Stake not returned (SNR).** A winning bonus bet pays only the profit, never the bonus stake.

## Q1. What is each Arizona-licensed sportsbook's current new-user offer, and what are its exact terms?

### Takeaway
About eleven books have a live Arizona welcome offer as of 2026-11-07. Three types dominate:
- **Bet-and-get bonus bets:** FanDuel, DraftKings, bet365, Hard Rock, Bally, Fanatics FanCash, theScore's $100 offer.
- **First-bet "safety net" or second-chance refunds paid in bonus bets:** BetMGM up to $1,500, theScore up to $1,000, BetRivers.
- **Profit boosts:** Caesars, ten 100% boosts capped at $25 each.

Desert Diamond runs a deposit match paid in bonus bets with a 1x deposit playthrough.

I confirmed eight offers on the operator's own pages, all via search summary: FanDuel, BetMGM, Caesars, bet365, Hard Rock, Desert Diamond, Bally, and theScore's help-center terms. One caveat: BetMGM's own Arizona terms list a promotion period that ended 11/1/2026, although affiliates still advertised the offer on Nov 5. I could not confirm DraftKings' Arizona reward, Fanatics' Arizona terms, BetRivers' Arizona amount, or any offer at BetCris or Golden Nugget on the books' own pages.

Three deadlines fall this month: FanDuel's offer ends Nov 22, bet365's closes Nov 23, and DraftKings' national offer runs to Nov 29.

### Cited Findings

**Roster context**
- Arizona had 14 event-wagering licensees as of about May 2026 — [G3 Newswire](https://g3newswire.com/arizona-to-launch-tender-for-more-betting-licences/) (via search summary).
- In September 2026 ADG allocated nine *limited* event-wagering licenses to local businesses partnered with Caesars (American Wagering) and Turf Paradise (Skyfall 7). These are retail venues, not new apps — [Focus Gaming News](https://focusgn.com/arizona-regulator-allocates-nine-limited-event-wagering-licences) (via search summary).
- Circa Sports' license took effect July 27, 2026; Circa is not live yet — [G3 Newswire](https://g3newswire.com/circa-sports-lands-arizona-sports-betting-license/) (via search summary).
- BetCris launched in Arizona in January 2025 through Plannatech, under the San Carlos Apache license — [SBC Americas](https://sbcamericas.com/2025/01/27/betcris-arizona-sportsbook-announcement/). A page last verified July 17, 2026 still described it as live, with no bonus code launched yet — [VegasInsider](https://www.vegasinsider.com/sportsbooks/betcris-promo-code/) (via search summary).
- A March 2026 Arizona directory lists Golden Nugget, which is DraftKings-powered in Arizona, among 13 active books. It reports that TwinSpires, Unibet, Betway, Fubo and Betfred have left Arizona — [arizonasportsbetting.us.com](https://arizonasportsbetting.us.com/) (weak directory source); [Legal Sports Report – Golden Nugget AZ launch](https://www.legalsportsreport.com/64985/golden-nugget-sportsbook-launch-az/). SaharaBets left in July 2024 — [SBC Americas](https://sbcamericas.com/2024/07/10/saharabets-deserts-arizona/) (via search summary).
- theScore Bet replaced ESPN BET on Dec 1, 2025 in PENN's markets, including Arizona, and ESPN BET accounts were migrated automatically — [Rotogrinders](https://rotogrinders.com/sports-betting/thescorebet); [Bleacher Nation](https://www.bleachernation.com/?p=2670049) (via search summary).
- November 2026 roundups headline Arizona welcome offers at about $6,300–$6,450 in face value (Covers, SI, Sportsbook Review); Rotowire said $5,600 in October 2026 — [Covers AZ, Nov 2026](https://www.covers.com/betting/bonuses/arizona-best-bonuses-promo-codes); [SI AZ](https://www.si.com/betting/usa/arizona/sportsbook-promos); [SBR AZ, Nov 2026](https://www.sportsbookreview.com/bonuses-arizona/); [Rotowire AZ, Oct 2026](https://www.rotowire.com/betting/promos/arizona) (via search summary; affiliate sites paid per sign-up).

**FanDuel.** Confirmed on FanDuel's own page via search summary. Window: Nov 2–22, 2026.
- **Offer:** "$200 guaranteed" over four days. A $5+ cash wager on each of four consecutive days earns $50 in bonus bets per day, capped at $200.
- **Timing:** eligible wagers must be placed between 3 AM and 11:59 PM ET.
- **Exclusions:** bets funded with bonus money, site credit, bonus bets or profit boost tokens do not count, and cashed-out wagers are excluded.
- **Bonus bets:** non-withdrawable; they expire 7 days after receipt. 21+ in Arizona.
- **Conflict:** the page title reads "Get $150 in Bonus Bets", while its URL and the summarized body describe $200.
- Source: [FanDuel Research – new customer promo](https://www.fanduel.com/research/fanduel-new-customer-promo-get-usd200-in-bonus-bets-guaranteed) (via search summary).
- Affiliate roundups give FanDuel's Arizona offer as $150–$200, and "several sites" say it runs through Nov 22, 2026. The summary did not say which of the Covers, SI, SBR and Fantasy Alarm pages carry which figure — [Covers AZ](https://www.covers.com/betting/bonuses/arizona-best-bonuses-promo-codes); [SBR AZ](https://www.sportsbookreview.com/bonuses-arizona/); [SI AZ](https://www.si.com/betting/usa/arizona/sportsbook-promos) (via search summary).
- **Ended offers:** a $350 seven-day promo ran through Sept 20, 2026, and a one-game "Bet $1, Get $100" was tied to Cardinals–Cowboys on Nov 1 — [FanDuel Research](https://www.fanduel.com/research/fanduel-nfl-promo-new-customers-bet-usd1-get-usd100-cardinals-vs-cowboys-on-november-1) (via search summary).
- **Bonus bet rules:**
  - They expire in 7 days unless stated otherwise. A bonus bet placed before expiry may be on an event that settles after it — [FanDuel support](https://support.fanduel.com/s/article/When-will-a-Free-Bet-expire).
  - The stake is not returned. In FanDuel's example, a $25 bonus bet that wins returns only $22.73. Part of a bonus bet can be used and the rest kept until expiry — [FanDuel support – Bonus Bets](https://support.fanduel.com/s/article/Bonus-Bets).
  - Cash-out value excludes the bonus stake — [FanDuel support – Cash Out](https://support.fanduel.com/s/article/What-is-the-Cash-Out-Feature) (via search summary).
- **Not found:** the minimum odds for the qualifying wagers.

**DraftKings.** Not confirmed on DraftKings' own page for Arizona.
- **National offer:** "Bet $5, Get $200 in bonus bets", window Oct 12 – Nov 29, 2026 — [WSN, Oct 26, 2026](https://www.wsn.com/promos/draftkings-promo-code-nfl-cowboys-vs-eagles-10-26-2026/); [WSN, Oct 13, 2026](https://www.wsn.com/promos/draftkings-promo-code-nba-knicks-vs-raptors-10-13-2026/) (via search summary).
- **Arizona listings:**
  - Fantasy Alarm: $200 in bonus bets plus three months of NBA League Pass, with the first $50 credited immediately and the rest unlocking over three weeks — [Fantasy Alarm AZ](https://www.fantasyalarm.com/arizona-promo-codes).
  - A Sportsbook Review page says "last verified Nov. 1, 2026" and no code needed. Its URL slug is from 2023, so attribution is uncertain — [SBR](https://www.sportsbookreview.com/picks/promos/draftkings-promo-code-navy-notre-dame-aug-26-2023/) (via search summary).
- **DraftKings' own pages:**
  - "OSB5" terms list AZ as eligible (new customers, 21+, one offer per customer), but the reward amount was not visible — [DraftKings OSB terms](https://www.draftkings.com/osb5).
  - A $200 sportsbook variant pays eight $25 bonus bets valid for 7 days (168 hours). Some versions require the qualifier at −500 or longer. One JP200 version ran Aug 25 – Sept 7, 2025 for CO, DC, MA, ME, NJ, NY and WV only — [DraftKings JP200](https://www.draftkings.com/200jp); [DraftKings JP200+5](https://www.draftkings.com/2005jp) (via search summary).
  - DraftKings' Arizona landing page advertised a deposit bonus of up to $1,000 in site credit; this is probably stale — [DraftKings AZ](https://sportsbook.draftkings.com/az-sports-betting).
  - DraftKings' "Official promo codes for November 2026" page exists, but no details surfaced — [DraftKings promo codes](https://www.draftkings.com/promo-code).
  - A separate DraftKings *Predictions* offer pays $200 in "Predictions Dollars" for a $5 first trade, as four $50 allotments over 21 days; no states were listed — [DraftKings Predictions](https://predictions.draftkings.com/en/predictions?nis=5&ch=1) (via search summary).
- **Bonus bet rules:** the stake is excluded from winnings, winnings go to cash, and the bonus bet must be played through once — [DraftKings support](https://support.draftkings.com/dk/en-us/what-is-a-bonus-bet?id=kb_article_view&sysparm_article=KB0010380); [DraftKings VIP promo terms](https://sportsbook.draftkings.com/vippromoterms) (via search summary).

**BetMGM.** Structure confirmed on BetMGM's Arizona page via search summary, but the listed period ended 11/1/2026.
- **Offer:** First Bet Offer, up to $1,500 back in bonus bets if the first bet loses.
- **Eligibility:** new customers, 21+; $10 minimum deposit.
- **Refund format:** a losing bet over $50 returns **five bonus bets, each 20% of the stake** (up to $1,500 total). A bet of $50 or less returns one bonus bet equal to the stake.
- **Expiry:** tokens and bonus bets expire 7 days after issue.
- **Restrictions:** bonus bets are never redeemable for cash and not usable on casino or poker. Limit five per person, account, household (IP address) or computer.
- **Period:** 8/28/2025 12:00 AM EST to 11/1/2026 11:59 PM EST.
- Source: [BetMGM AZ First Bet Offer](https://www.az.betmgm.com/en/engage/lan/sports/first-bet-offer) (via search summary).
- BetMGM's own Arizona blog (October 2026) gives the code BETMGMBONUS — [BetMGM AZ promos](https://sports.betmgm.com/en/blog/betmgm-state-promos/arizona-sportsbook/) (via search summary).
- **Affiliates still list up to $1,500 in November:** code PLAYLSR on Nov 5, 2026 — [Legal Sports Report](https://www.legalsportsreport.com/sports-betting/betmgm-promo-code/); code COVERS, "checked November 2026" — [Covers](https://www.covers.com/betting/bonuses/betmgm-bonus-codes) (via search summary).
- **Not found:** the qualifying-bet minimum odds.

**Caesars.** Confirmed on Caesars' Arizona support and welcome pages via search summary; no promotion period stated.
- **Offer:** ten 100% Profit Boosts for opening an account and placing a qualifying wager of $1 or more; promo code CZRDYW; AZ listed; 21+.
- **Per-token limits:** $25 maximum wager; $2,500 maximum extra winnings; minimum odds −10000.
- **Expiry:** boosts must be used within 14 calendar days.
- **Payout:** extra winnings are paid **as cash**.
- **Disqualifiers:** a qualifier that is cashed out, placed with a boost token, placed on a Super Boost market or placed with a bonus bet does not count. Boosts cannot be combined with bonus bets. Disputes can go to ADG.
- Source: [Caesars AZ promotions terms](https://www.caesars.com/sportsbook-and-casino/az/support/promotions/) (multistate page that lists AZ).
- The Arizona welcome page reads: "Place your first bet of $1 or more to receive 10 100% Profit Boosts, Up to $25 Max Bet per Boost. Profit Boosts must be used within 14 days" — [Caesars AZ welcome](https://www.caesars.com/sportsbook-and-casino/az/welcome) (via search summary).
- An October 2026 affiliate variant (code LSRDYW) gave 10 boost tokens after a $10 deposit and first bet, and expired Oct 31, 2026. URL attribution is uncertain — [Legal Sports Report](https://www.legalsportsreport.com/78739/caesars-promo-code-for-thursday-night-football-chiefs-chargers/) (via search summary).

**bet365.** Confirmed on bet365's Arizona hub via search summary. Closes 08:59 AM, Nov 23, 2026.
- **Offer:** "Bet $10 Get $200 in Bonus Bets".
- **Claiming:** claim within 30 days of registering; deposit at least $10 in the 7 days before claiming; claims are made in the bet365 app (iOS and Android only).
- **Release requirement:** $10 of qualifying bets that settle within 30 days of claiming. At least one selection must be at −500 or longer.
- **Exclusions:** cash-outs, bets placed with bonus bets, and pushes do not count.
- **Bonus bets:** expire 7 days after being added; non-withdrawable; the bonus stake is excluded from returns.
- **Eligibility:** 21+; for customers who have never claimed a bet365 New Customer Promo.
- Sources: [bet365 Arizona hub](https://www.bet365.com/hub/en-us/states/arizona); [bet365 offer page](https://www.bet365.com/promos/en-us/home/open-account-global-offer) (via search summary).
- Older bet365 pages list $150 variants.
- An affiliate page last verified Oct 10, 2026 listed "bet $10, get $365" and a "$1,000 safety net" option. URL attribution is uncertain, and the safety net is unconfirmed for Arizona in November — [Sharp Football Analysis](https://www.sharpfootballanalysis.com/?p=93621) (via search summary).

**Fanatics.** Not confirmed on Fanatics' own Arizona terms.
- **Offer A, "Bet $20, Get $350 in FanCash":**
  - Paid as $50 a day for 7 days.
  - The first wager of $20+ must be placed within 7 days of opening the account, at −500 or longer.
  - Arizona is listed among eligible states (IN, IA, AZ, MA, WY).
  - Sources: [SI, spring 2026](https://www.si.com/betting-promo/fanatics-sportsbook-promo-bet-20-get-up-to-350-in-select-states-for-mlb-nhl-nba-playoffs-01kqwqb7wkkm); [SI review](https://www.si.com/betting/reviews/fanatics-sportsbook) (via search summary). November 2026 Arizona roundups list the same offer, under codes including SIBONUS350, COVERS350, FOX2026 and SBREVIEW — [Covers AZ](https://www.covers.com/betting/bonuses/arizona-best-bonuses-promo-codes); [SI AZ](https://www.si.com/betting/usa/arizona/sportsbook-promos) (via search summary; site-by-site attribution approximate).
  - In search results, a Fanatics-domain page is titled "Fanatics Sports & Casino — Bet $20 Get $350 in FanCash" (no state given) — [Fanatics Sportsbook](https://sportsbook.fanatics.com/).
- **Offer B, up to $1,000 in FanCash over 10 consecutive days:**
  - A daily "bet match": FanCash equals the qualifying wager, capped at $100 FanCash a day. FanCash from this promotion expires 7 days after issue.
  - Nov 2026 roundups say Arizona bettors can choose this option (code SIBONUS350) — [SI AZ](https://www.si.com/betting/usa/arizona/sportsbook-promos) (via search summary).
  - Earlier descriptions: [Rotogrinders AZ, Mar 2026](https://rotogrinders.com/sports-betting/arizona); [Legal Sports Report, Aug 2026, code BONUSLSR](https://www.legalsportsreport.com/sportsbook-promos/fanatics/) (via search summary).
  - **Minimum odds conflict:** one review says the bet match is a daily $1+ bet at −200 or longer; a June SI page said −500.
  - **Expiry conflict:** sources give either 7 days or 24 hours per daily FanCash grant (via search summary).
- **FanCash rules:**
  - FanCash converts to bonus bets 1:1, but to casino credit at only $0.50 per $1.
  - Earned FanCash expires 365 days after the last earning activity.
  - Source: [Fanatics FanCash program terms (Tennessee version)](https://sportsbook.fanatics.com/legal/tn/fancash-program-terms/) (via search summary).
- **Exclusions in Fanatics acquisition terms:** bets placed with bonus bets, cashed-out bets, voided bets, odds-boosted bets, and bets settled after the promotion period — [Fanatics promo terms ALL_1406 (2024)](https://sportsbook.fanatics.com/promo-terms/2024/Acquisition/ALL_1406.pdf) (via search summary).

**BetRivers.** Not confirmed, and the Arizona amount conflicts across sources.
- **$100 second-chance bet** (code SPORTS; bonus usable at −200 or longer), in a page last updated April 2024 — [Rotowire BetRivers AZ](https://www.rotowire.com/betting/betrivers/arizona) (via search summary).
- The same $100 for Arizona under code PLAYMAX, "tested & verified 05/07/2026" — [Football Whispers](https://footballwhispers.com/us/blog/betrivers-bonus-code-playmax/). A different Arizona code, USARIV, "last updated July 18, 2026" — [PlayUSA](https://www.playusa.com/bet-rivers/) (via search summary).
- Another affiliate lists Arizona among states with up to $500 — [TopEndSports](https://www.topendsports.com/en-us/sports-betting/promo-codes/betrivers-promo-code/) (via search summary).
- BetRivers' own Arizona site advertises a "$250 sportsbook BONUS" and a "1X playthrough on bonus money", without visible terms — [BetRivers AZ](https://az.betrivers.com/) (via search summary).
- Affiliates mention a $10 minimum deposit and bonus bets that must be used within 30 days — [Rotowire BetRivers](https://www.rotowire.com/betting/betrivers) (via search summary).

**Hard Rock Bet.** Confirmed on Hard Rock's own pages via search summary. Window: Aug 24 – Dec 31, 2026.
- **Offer:** Bet $5, Get $100 in bonus bets; no promo code; Arizona listed.
- **Qualifier:** a $5+ cash wager on any market at −500 or longer. Round robins are excluded; using Early Cash Out makes the bet ineligible; bets placed with bonus bets are excluded.
- **Payout schedule:** **$20 in bonus bets each week for five weeks**.
- **Eligibility conflict:** one official page says "Available to all new AND existing players", which contradicts affiliates' "new users only".
- Sources: [Hard Rock Bet promo page](https://www.hardrock.bet/sportsbook/big-game-rollout); [Hard Rock Bet promo page](https://www.hardrock.bet/ac_vip_offer) (via search summary; which page carries which term is unclear).
- Affiliates (June–July 2026) advertised $150, a 7-day bonus expiry and a $10 minimum deposit — [Rotowire, July 2026](https://www.rotowire.com/news/hard-rock-bet-promo-code-150-in-bonus-bets-july-2026-125155) (via search summary).

**Desert Diamond (Bet Desert Diamond).** $250 match confirmed on its help center via search summary. Window: Jan 1 – Dec 31, 2026.
- **Offer:** $250 Welcome Match. A first deposit over $100 earns a 100% match up to $250 **in bonus bets**, credited within 48 hours as **five bonus bets** (each one-fifth of the match).
- **Bonus bets:** expire 7 days after issue; usable only at −200 or longer (parlay legs included; boosted odds excluded); no cash value.
- **Playthrough:** **you must wager the initial deposit at least once before withdrawing bonus-bet winnings.**
- **Eligibility:** 21+, physically in Arizona and **not on Indian Lands**; one use per new player. Players who register through an affiliate site must deposit at least $100.01.
- Source: [Bet Desert Diamond help – $250 Welcome Match](https://help.betdesertdiamond.com/hc/en-us/articles/39783613225755--250-Welcome-Match-offer) (via search summary).
- **Alternative listed by affiliates:** Bet $20, Get $100 in bonus bets, no code, bonus bets expiring after 14 days — [Action Network, July 2026](https://www.actionnetwork.com/online-sports-betting/reviews/desert-diamond); [Rotowire](https://www.rotowire.com/news/bet-desert-diamond-promo-code-get-100-instantly-for-phoenix-suns-vs-detroit-pistons-102794); [Rotogrinders, Apr 2026](https://rotogrinders.com/sports-betting/desert-diamond-promo-code) (via search summary).
- WSN lists "$250 Match Bonus + $25 Free Bet" — [WSN](https://www.wsn.com/sportsbooks/desert-diamond/) (via search summary).

**theScore Bet.** Help-center terms found; the current Arizona-specific offer is not confirmed.
- **"$1,000 Bet Reset":**
  - If the eligible wager loses, you get 100% back, up to $1,000, as **five bonus bets**.
  - Only for players who have **never registered and deposited on a PENN Sports Interactive product**; the terms reference a March 16, 2026 cutoff.
  - Source: [theScore Bet help – $1,000 Bet Reset](https://thescorebethelp.zendesk.com/hc/en-us/articles/43010570595085--1-000-Bet-Reset) (via search summary).
- **"Bet $10, Get $100":**
  - Five $20 bonus bets after a first cash wager of $10+, to be used within 7 days.
  - No state is named, and the page is about 442 days old — [theScore Bet help – Bet $10, Get $100](https://thescorebethelp.zendesk.com/hc/en-us/articles/38994581269389-Bet-10-Get-100) (via search summary).
- **Affiliate listings:**
  - "Up to $1,000 back", October 2026 — [Rotowire](https://www.rotowire.com/news/thescore-bet-promo-code-roto-up-to-1000-back-for-october-2026-138695).
  - "Bet $10, Get $100 in Bonus Bets If You Win" plus a bet reset of up to $1,000, verified Aug 3, 2026. The URL in the results is Rotogrinders' Canada page — [Rotogrinders](https://rotogrinders.com/sports-betting/canada/thescore-bet) (via search summary).
- **Bonus bet rules:** a winning bonus bet returns only the winnings, in withdrawable cash — [theScore Bet help – Bonus Bets](https://thescorebethelp.zendesk.com/hc/en-us/articles/14848235692045-Bonus-Bets) (via search summary).

**Bally Bet.** Confirmed on Bally Bet's Arizona page via search summary. Window: Jan 1 – Dec 31, 2026.
- **Offer:** Bet $10, Get $50.
- **Qualifier:** a first-time deposit plus a first sports wager of $10+ at minimum odds of −250, settling within 28 days of registration. Only the first wager counts, and several smaller wagers adding up to $10 do not qualify.
- **Payout:** bonus-bet tokens load within 48 hours of the qualifier grading, **win or lose**. They expire 7 days after issue.
- Sources: [Bally Bet AZ](https://www.ballybet.com/az); [Bally Bet promotions](https://www.ballybet.com/promotions). An older help article describes the reward as two $25 tokens — [Bally Bet help](https://help.co.ballybet.com/hc/en-us/articles/24118703224978-I-have-a-question-about-the-Welcome-Offer) (via search summary).

### Inferences
- **Inventory summary.** "Own page" means confirmed on the operator's domain via search summary.

| Book | Current Arizona new-user offer (checked 2026-11-07) | Type | Key mechanics | Window / date | Own-page status |
|---|---|---|---|---|---|
| FanDuel | $50 in bonus bets/day × 4 days for $5+ cash bets | Bet-and-get | 4 consecutive days; bonus bets expire 7 days; SNR; min odds not found | Nov 2–22, 2026 | Confirmed (title says $150, body says $200) |
| DraftKings | Bet $5, get $200 in bonus bets (+ NBA League Pass) | Bet-and-get | Possibly $50 now + rest over 3 weeks, or 8 × $25; 7-day bonus life (per other DraftKings terms) | National window Oct 12 – Nov 29, 2026 (affiliate) | **Not confirmed** for AZ |
| BetMGM | Up to $1,500 back in bonus bets if first bet loses | Second chance | 5 × 20% tokens; 7-day expiry; $10 min deposit; qualifier min odds not found | Official terms end 11/1/2026; affiliates still list it Nov 5 | Structure confirmed; **current period unconfirmed** |
| Caesars | 10 × 100% profit boosts after a $1+ bet | Profit boosts | $25 max per boost; 14 days; extra winnings paid in cash | Period not stated | Confirmed |
| bet365 | Bet $10, get $200 in bonus bets | Bet-and-get | −500 or longer; 7-day expiry; claim in app within 30 days | Closes 08:59 AM Nov 23, 2026 | Confirmed |
| Fanatics | A: $20 bet → $350 FanCash ($50/day × 7); or B: up to $1,000 FanCash (≤ $100/day × 10) | Bet-and-get (FanCash) | −500 (A); B −200 or −500 (conflict); FanCash → bonus bets 1:1; 7-day or 24-hour expiry (conflict) | Nov 2026 roundups | **Not confirmed** for AZ |
| BetRivers | 2nd-chance bet, $100 / $250 / $500 (conflict) | Second chance | −200 or longer; 30-day bonus life; 1x playthrough on bonus money | Sources Apr 2024 – Jul 2026 | **Not confirmed** |
| Hard Rock Bet | Bet $5, get $100 in bonus bets | Bet-and-get | $20/week × 5 weeks; −500 or longer | Aug 24 – Dec 31, 2026 | Confirmed |
| Desert Diamond | 100% deposit match to $250 in bonus bets (deposit > $100); affiliates also list Bet $20 → $100 | Deposit match | 5 bonus bets; −200 or longer; deposit wagered 1x before withdrawing | Jan 1 – Dec 31, 2026 | $250 match confirmed |
| theScore Bet | $1,000 bet reset, or Bet $10 → $100 | Second chance / bet-and-get | 5 bonus bets; excludes anyone with a prior PENN account (e.g. ESPN BET, auto-migrated) | Reset terms reference Mar 16, 2026 | Terms found; **AZ offer not confirmed** |
| Bally Bet | Bet $10, get $50 (2 × $25) | Bet-and-get | −250; first wager only; 7-day expiry | Jan 1 – Dec 31, 2026 | Confirmed |
| BetCris | No welcome offer found | – | – | Live since Jan 2025 | No offer found |
| Golden Nugget | Unknown | – | DraftKings-powered | Listed active Mar 2026 | Not checked |
| Circa | Not live | – | – | Early-2027 target (earlier note) | – |

- **Time zones.** Arizona is on MST (UTC−7) with no daylight saving. In November, Eastern time is EST (UTC−5), so "11:59 PM ET" deadlines fall at 9:59 PM Arizona time. That covers FanDuel's daily wager window and BetMGM's period end. FanDuel's "3 AM ET" daily start is 1 AM in Arizona.
- **Deadlines.** FanDuel (Nov 22), bet365 (Nov 23) and DraftKings' national window (Nov 29) all close this month. Registering before those dates matters more than the order of everything else.
- **BetMGM.** Its own terms list a period that ended 11/1/2026, yet BetMGM's own October blog and November affiliate pages still advertise the offer. Most likely it was renewed under new terms, but that is unverified. Check the in-app terms for the new period, the minimum odds and whether the 5 × 20% token split still applies.

### Gaps
- DraftKings' Arizona reward, token split and minimum odds for November 2026: not visible on DraftKings' own pages.
- Fanatics' Arizona-specific terms: which option is live, the minimum odds, the FanCash expiry, and whether Offer B pays win-or-lose or only on losses.
- BetRivers' Arizona amount ($100 vs $250 vs $500) and terms.
- BetMGM's terms after 11/1/2026, and its qualifying minimum odds.
- theScore Bet's current Arizona offer.
- Golden Nugget's status and offer.
- Any BetCris welcome offer.
- ADG's official roster (not readable here; the earlier note had the same gap).
- FanDuel's qualifying minimum odds.
- Promotion period for Caesars' CZRDYW.

## Q2. How is each offer type converted to withdrawable cash (qualifying bet, hedge, bonus conversion), with worked examples, typical conversion rates and expected net?

### Takeaway
Hedged at another book, a stake-not-returned bonus bet converts to cash at about **c = (o_b − 1)(o_h − 1)/o_h**, where o_b is the bonus bet's decimal odds and o_h is the hedge's. In practice that comes to about **55–60% at +150 to +200** and about **65–73% at +300 to +500** at typical 2–4% holds. About 75–80% needs unusually good line shopping or a near-arbitrage pair. Practitioner guides call 70% "good".

Expected net by offer type, hedged (my arithmetic):
- **Bet-and-get:** about 65–75% of the bonus's face value, minus a trivial qualifier cost.
- **Second-chance / safety-net offers:** about **25–30% of the maximum stake** for an even-money qualifier, rising to about **38–46%** for a +300 qualifier, at roughly double the capital.
- **100% profit boosts on $25:** about **$8.50–$13** each, locked.
- **Deposit matches paid in bonus bets:** about 60–70% of the match, minus the cost of the deposit playthrough.

### Cited Findings
- **Benchmarks:**
  - "A good bonus bet conversion rate is 70% or higher" — [Action Network – bonus bet conversion](https://www.actionnetwork.com/education/bonus-bet-conversion) (via search summary).
  - A widely shared practitioner spreadsheet treats 70% as conservative, 80% as good and over 90% as fantastic — [Google Sheets model](https://docs.google.com/spreadsheets/d/1kycH-o8VIIFgAK9lSvq_hYwBEM8Mhl2B/edit) (via search summary).
- **Conversion rises with odds:**
  - One calculator guide's table gives about 70–75% at decimal 4.00 (+300) and 75–80% at 5.00 (+400).
  - Tables disagree on +200: about 62% in one, about 70% in another.
  - Conversion also depends on the hedge price found at the other book.
  - A worked example: a $100 bonus bet at 4.00, with the opposite side at 1.36 elsewhere.
  - Sources: [TopEndSports bonus bet calculator](https://www.topendsports.com/sport/betting-tools/bonus-bet-calculator.htm); [OddsShopper – how to convert a free bet](https://www.oddsshopper.com/articles/betting-101/how-to-convert-a-free-bet) (via search summary; the summary did not say which page carries which table).
- **Academic model:** the hedged profit from a free bet is the free bet's expected risky profit (1 − m − p) multiplied by a margin discount factor. The optimal free-bet win probability is "low but not very low" — [Whelan, "The Economics of Free Bets"](https://www.karlwhelan.com/Papers/FreeBets.pdf) (via search summary).
- **No-sweat / second-chance offers:**
  - The refund comes as bonus credit, so a $1,000 refund converted at 70% yields $700, and a lost no-sweat bet nets −$300 — [OddCompare – no-sweat bets](https://oddcompare.pages.dev/learn/bonus-betting/no-sweat-bets) (via search summary).
  - One author says a maximized no-sweat bet can be worth "as much as 60% of your bet size", but most bettors botch it and get closer to $100 of EV — [JuiceReel](https://juicereel.beehiiv.com/p/how-to-maximize-the-no-sweat-bet) (via search summary).
  - Betting heavy favorites can make the offer negative-EV, and hedging gives up some EV to the hedge vig in exchange for certainty — [OddCompare](https://oddcompare.pages.dev/learn/bonus-betting/no-sweat-bets); [JuiceReel](https://juicereel.beehiiv.com/p/how-to-maximize-the-no-sweat-bet) (via search summary).
- **Stake not returned at the major books:**
  - FanDuel: a $25 bonus bet that wins returns only $22.73 — [FanDuel support](https://support.fanduel.com/s/article/Bonus-Bets).
  - DraftKings excludes the stake from winnings — [DraftKings support](https://support.draftkings.com/dk/en-us/what-is-a-bonus-bet?id=kb_article_view&sysparm_article=KB0010380).
  - bet365 excludes the bonus stake from returns — [bet365 AZ hub](https://www.bet365.com/hub/en-us/states/arizona).
  - theScore returns winnings only — [theScore help](https://thescorebethelp.zendesk.com/hc/en-us/articles/14848235692045-Bonus-Bets).
  - Caesars pays boost winnings as cash — [Caesars AZ terms](https://www.caesars.com/sportsbook-and-casino/az/support/promotions/) (all via search summary).

### Inferences
All figures below are my arithmetic from the formulas shown. The odds pairs are illustrative of typical two-book markets; holds are in brackets.

**Type 1: Bet-and-get bonus bets (stake not returned).** Applies to FanDuel, DraftKings, bet365, Hard Rock, Bally, theScore's $100 offer, Fanatics FanCash once converted to bonus bets, and Desert Diamond's $100 variant.
1. **Qualifier.** Place the minimum cash bet ($5–$20), respecting the minimum odds (−500 or longer at bet365, Hard Rock and Fanatics; −250 at Bally). Hedging is optional. Unhedged, a $10 bet at −110 costs about $0.45 of EV; hedged at −110 at another book, it locks −$0.91. Never cash out a qualifier, since that voids the offer at Caesars, Hard Rock, FanDuel and bet365.
2. **Bonus bet.** Once the bonus bets arrive, put each on a longshot, roughly +300 to +500, at the promo book.
3. **Hedge.** At another book, bet the opposite outcome with cash stake **h = B(o_b − 1)/o_h**. The locked profit is **B·c**, where c is the conversion formula in the takeaway.
4. **Settle.** One leg wins, either way, and leaves about the same cash. Withdraw after any playthrough is met.

Worked conversion rates:

| Bonus odds / hedge odds [hold] | Conversion c | $200 bonus: hedge stake | Locked cash |
|---|---|---|---|
| +150 / −170 [3.0%] | 55.6% | $189 | $111 |
| +200 / −240 [3.9%] | 58.8% | $282 | $118 |
| +300 / −360 [3.3%] | 65.2% | $470 | $130 |
| +300 / −400 [5.0%] | 60.0% | $480 | $120 |
| +400 / −500 [3.3%] | 66.7% | $667 | $133 |
| +400 / −450 [1.8%, a shopped price] | 72.7% | $655 | $145 |
| +500 / −650 [3.3%] | 66.7% | $867 | $133 |
| +1000 / −1400 [2.4%] | 66.7% | $1,867 | $133 |

- The guide example of 4.00 against 1.36 works out to c = 3 × 0.36 / 1.36 = **79.4%**. That pair has a slightly negative hold, which is how "80%" figures arise: only from favorable price mismatches.
- **Realistic planning range: c ≈ 65–72%**, with a 65–75% band used in the totals. Above about +500 the gain from longer odds is eaten by wider holds and much larger hedge stakes, so +300 to +500 is the practical zone. This is consistent with Whelan's "low but not very low" optimum.
- **Expected net, bet-and-get:** a $200 bonus nets about $130–$150; $100 nets about $65–$75; $50 nets about $32–$37.

**Type 2: Second chance / first-bet safety net / bet reset** (refund of a losing first bet as bonus bets). Applies to BetMGM (up to $1,500), theScore (up to $1,000) and BetRivers.
1. **Qualifier.** Place stake Q, up to the cap, at decimal odds o_q at the promo book.
2. **Hedge now.** At another book, bet the other side with cash **h = Q(o_q − c)/o_h**, where c is the rate you expect to get when converting the refund. The lock is **Q(o_q − 1) − h**.
3. **If the qualifier loses,** you receive Q in bonus bets (BetMGM pays five 20% tokens). Convert each as in Type 1 within the 7-day expiry.

Locked profit by qualifier size and odds (c = 0.65 / 0.70 / 0.75):

| Qualifier (hedge) | Q = $1,500 (BetMGM) | Q = $1,000 (theScore) | Q = $250 | Q = $100 |
|---|---|---|---|---|
| −110 (−110) | $374 / $414 / $453; hedge ~$950; ~$2,450 at risk | $250 / $276 / $302; ~$1,633 at risk | $62–$75 | $25–$30 |
| +200 (−240) | $512 / $565 / $618; ~$3,935 at risk | $341 / $376 / $412; ~$2,624 at risk | $85–$103 | $34–$41 |
| +300 (−360) | $567 / $626 / $685; ~$5,374 at risk | $378 / $417 / $457; ~$3,583 at risk | $95–$114 | $38–$46 |

- **Unhedged EV** of the same offer at c = 0.70 is about 31% of Q at −110, 44% at +200, 50% at +300 and 61% at +1000. That matches JuiceReel's "up to 60%" claim. Hedging gives up about 3 points of EV at −110, about 6 at +200, about 8 at +300 and about 23 at +1000 (a +1000/−1400 hedge locks about 39% of Q but puts about 10.6 × Q at risk). The trade is certainty for EV, and it needs more capital.
- **Recommendation for a small bankroll:** hedge the qualifier at around even money. BetMGM's full $1,500 then locks about **$414** and needs about $2.45k in play. Go to +200 or +300 only if you have $4–5.5k available plus capital to convert $1,500 of bonus bets (Q4).
- **"Bet $10, get $100 *if your bet wins*"** (one theScore listing) is a different shape. Hedging it is awkward, so take the EV: put the $10 qualifier at the shortest odds allowed. At −500 the EV is about $55 (win probability about 0.79 × $100 × 0.70), versus about $35 at −110.

**Type 3: Profit boosts** (Caesars: ten 100% boosts, $25 maximum stake each).
1. Pick a market and apply the token: a $25 cash bet whose profit is doubled, so decimal odds o become 1 + 2(o − 1).
2. Hedge at another book with **h = S × boosted decimal / o_h**. The lock is **S × boosted decimal − S − h**.

Locked per $25 token:

| Base odds (hedge) | 100% boost | 50% boost | 25% boost |
|---|---|---|---|
| −110 (−110) | $8.55 | $3.14 | $0.43 |
| +200 (−240) | $11.76 | $4.41 | $0.74 |
| +300 (−360) | $13.04 | $4.89 | $0.82 |
| +500 (−650) | $11.67 | $3.33 | −$0.83 |

- Caesars' ten tokens therefore lock about **$85–$130**.
- Unhedged, the EV per $25 token is about $10 at −110 and $15–$19 at +200 to +500. Ten tokens give $100–$190 in EV, but with real variance.
- Because Caesars pays boost winnings in cash, no further conversion step is needed.

**Type 4: Deposit match paid in bonus bets with a playthrough** (Desert Diamond: deposit more than $100, get a 100% match up to $250 as five bonus bets; wager the deposit 1x before withdrawing bonus-bet winnings).
1. Deposit $250 and receive five $50 bonus bets within 48 hours. Convert each as in Type 1 at −200 or longer (longshots qualify), within 7 days.
2. Turn over the $250 deposit once: one −110 bet costs about $11 of EV, or about $23 locked if hedged.
3. Net is about **$140–$176**. theScore's invite-only $50 and $100 deposit matches have the same shape: 1x playthrough on the deposit, paid as one bonus bet (Q3).

**FanCash (Fanatics).** Convert FanCash to bonus bets 1:1, never to casino credit at 0.5:1, then treat it as Type 1.
- **Offer A:** $350 FanCash nets about $227–$262.
- **Offer B:** $1,000 FanCash, if paid win or lose, nets about $560–$705 after ten $100 qualifiers (about $45 of EV unhedged, $91 hedged).
- **Offer B if it pays only on losses:** it behaves like ten $100 second-chance bets, worth about $25–$46 a day, or $250–$460 in total.

**Exchange hedge.** Hedging on Kalshi instead of a second book adds about 5–6 points of conversion on longshots, per the earlier note's arithmetic. It carries the Arizona legal and settlement-rule risk described there, so book-to-book hedging is assumed here.

### Gaps
- I found no measured, US-specific distribution of achieved conversion rates. The 65–80% range rests on practitioner rules of thumb and on the arithmetic above.
- I could not confirm whether BetMGM, Desert Diamond or theScore tokens can be split (FanDuel and DraftKings allow partial use). Indivisible tokens slightly constrain hedge sizing.
- The hedge-side holds in the tables are illustrative. I did not pull live November 2026 odds.

## Q3. What is a realistic total for one person claiming every Arizona sign-up offer, over what time, and which reload promotions are worth converting (value per month)?

### Takeaway
A full Arizona sweep in November 2026 is worth about **$1.6k–$2.3k pre-tax**, central about $1.9k, at 65–75% conversion. It rises to **$1.9k–$2.8k** if Fanatics' $1,000 FanCash match pays win-or-lose and if BetMGM's $1,500 offer is still live. If BetMGM's and DraftKings' offers have lapsed, it falls to about $1.1k–$1.5k.

Calendar time is about **5 weeks**, because Hard Rock drips $20 a week for five weeks. About 80–90% of the value can be locked in the first two weeks. Hands-on time is roughly 12–20 hours.

Ongoing reloads are thin. 100% boosts, no-sweat tokens, deposit-match invites and referral bonuses are worth converting; 25–33% boosts and parlay/SGP boosts mostly are not. Expect roughly **$50–$300 a month**, decaying as accounts get promo-restricted. This is an estimate, because US income data is weak.

After tax, a non-itemizer may keep only a few hundred dollars of the sweep (earlier note, Q7).

### Cited Findings
- **Deadlines and drip schedules (Q1 sources):**
  - FanDuel requires bets on 4 consecutive days, window ending Nov 22, 2026 — [FanDuel Research](https://www.fanduel.com/research/fanduel-new-customer-promo-get-usd200-in-bonus-bets-guaranteed).
  - bet365 closes Nov 23, 2026 and requires a claim within 30 days of registering — [bet365 AZ hub](https://www.bet365.com/hub/en-us/states/arizona).
  - Hard Rock pays $20 a week for 5 weeks, through Dec 31, 2026 — [Hard Rock Bet](https://www.hardrock.bet/sportsbook/big-game-rollout).
  - Caesars boosts last 14 days — [Caesars AZ welcome](https://www.caesars.com/sportsbook-and-casino/az/welcome).
  - Fanatics pays FanCash daily over 7 or 10 days — [SI](https://www.si.com/betting-promo/fanatics-sportsbook-promo-bet-20-get-up-to-350-in-select-states-for-mlb-nhl-nba-playoffs-01kqwqb7wkkm); [Rotogrinders AZ](https://rotogrinders.com/sports-betting/arizona).
  - DraftKings may unlock over 3 weeks — [Fantasy Alarm](https://www.fantasyalarm.com/arizona-promo-codes).
  - Most bonus bets expire 7 days after issue: FanDuel, BetMGM, bet365, Bally, Desert Diamond, theScore (Q1) (all via search summary).
- **Current reload types (dates mostly unconfirmed for November 2026):**
  - FanDuel advertises a daily 30% profit boost token for same-game or 3+ leg parlays (undated page) — [Fox Sports – FanDuel](https://www.foxsports.com/stories/betting/fanduel-promo-code).
  - FanDuel's "Dinger Tuesdays" offer a 50% profit boost or a bet reset token on home-run props (June–July 2026) — [Rotowire](https://www.rotowire.com/news/fanduel-promo-code-no-sweat-first-bet-for-november-67457).
  - FanDuel referrals pay $50 in bonus bets — [SI – FanDuel existing users](https://www.si.com/betting/sportsbook-promos/fanduel-promo-code/existing-user).
  - FanDuel's offers vary by state and day — [FantasyLabs](https://www.fantasylabs.com/?p=202047) (via search summary).
  - DraftKings has run a 25% MLB parlay boost (+300 minimum, $20 maximum bet), a 33% MLB profit boost token, a "Stepped Up" parlay boost of up to 105%, and No Sweat SGP tokens (January–July 2026) — [Fox Sports – DraftKings](https://www.foxsports.com/stories/betting/draftkings-promo); [Football Whispers](https://footballwhispers.com/us/blog/draftkings-sportsbook-code/); [Yardbarker](https://www.yardbarker.com/sports_betting/articles/draftkings_promo_code/s1_17347_41226688) (via search summary).
  - theScore offers invite-only $50 and $100 deposit matches (100% match, paid as one bonus bet, 1x playthrough on the deposit) — [theScore – $50 Deposit Match](https://thescorebethelp.zendesk.com/hc/en-us/articles/49370046905613--50-Deposit-Match); [theScore – $100 Deposit Match](https://thescorebethelp.zendesk.com/hc/en-us/articles/49370008258061--100-Deposit-Match).
  - theScore's refer-a-friend ($50 bonus bet each; Arizona listed) ended Apr 30, 2026 — [theScore – Refer A Friend](https://thescorebethelp.zendesk.com/hc/en-us/articles/41542867321485-Refer-A-Friend) (via search summary).
- **Reload income benchmarks (weak):**
  - UK guides put reload offers at about £2–£20 each, and about £3,000–£6,000 a year for an operation with 20+ accounts and a daily routine — [OddCompare – reload offers](https://oddcompare.pages.dev/learn/matched-betting/reload-offers); [OddCompare – long-term system](https://oddcompare.pages.dev/learn/matched-betting/long-term-system).
  - A US-oriented promotional guide claims "up to $2,000 per month", with no method given — [MyTopSportsbooks guide](https://mytopsportsbooks.pages.dev/mytopsportsbooks/www.mytopsportsbooks.com/guide/advanced-betting/no-risk-matched-betting-usa).
  - Monthly reload income varies with the sports calendar — [OddsMonkey help](https://oddsmonkey2.zendesk.com/hc/en-gb/articles/33011802773393-How-Can-I-Make-More-Money-From-Reload-Offers) (via search summary).
- **Older US benchmark:** about $500 an hour over up to 17 hours of new-user promos across twelve states, from 2022's much richer launch-era offers — [EA Forum guide (2022)](https://forum.nunosempere.com/posts/29EZBsbLovTgu6C3B/ea-fundraising-through-advantage-sports-betting-a-guide) (cited in the earlier note).

### Inferences
- **Per-offer value (from Q2 math, c = 65–75%):**

| Book | Assumed version | Pre-tax value | Calendar time to finish |
|---|---|---|---|
| FanDuel | 4 × $50 | $129–$149 | ~1.5 weeks |
| DraftKings | $200 (unconfirmed) | $130–$150 | 1–4 weeks, depending on drip |
| bet365 | $200 | $130–$150 | ~1 week |
| BetMGM | $1,500 safety net (if renewed), −110 to +300 qualifier | $374–$685 | ~1–1.5 weeks |
| Caesars | 10 × 100% boosts | $85–$130 locked (EV up to ~$190) | ≤ 2 weeks |
| Fanatics | A: $350 FanCash / B: $1,000 match (win or lose) | A: $227–$262 / B: $560–$705 | 1.5–2.5 weeks |
| BetRivers | $100 2nd chance (Arizona-specific reports) | $25–$46 ($62–$228 if $250–$500) | ≤ 30 days |
| Hard Rock | $100 (5 × $20 weekly) | $65–$75 | 5 weeks (long pole) |
| Desert Diamond | $250 match | $140–$176 | ~1.5 weeks |
| theScore | $1,000 bet reset (if eligible) | $250–$457 ($65–$75 if only Bet $10 → $100) | ~1.5 weeks |
| Bally | $50 | $32–$37 | ~1.5 weeks |
| **Total (Fanatics A)** | | **~$1,590–$2,320** | |
| **Total (Fanatics B)** | | **~$1,920–$2,760** | |
| Total if BetMGM and DraftKings have lapsed (Fanatics A) | | ~$1,080–$1,480 | |

- **Realistic central case:** about **$1.9k pre-tax**, so the earlier note's $1.5k–$3k range still holds. Mistakes (a voided qualifier, an expired token) typically cost tens of dollars each. Missing one large offer (BetMGM or theScore eligibility) costs $250–$700.
- **Hours:**
  - About 11 sign-ups with KYC at 10–20 minutes each is 2–4 hours.
  - About 45–60 conversion events (FanDuel 4, DraftKings 4–8, bet365 1+, BetMGM 5 tokens, Caesars 10, Fanatics 7–10, Hard Rock 5, Desert Diamond 5, theScore 5, Bally 2, BetRivers 1) at 5–15 minutes each is 5–12 hours.
  - Deposits, withdrawals and bookkeeping add 2–4 hours.
  - Total about **12–20 hours**, or roughly $100–$200 an hour pre-tax. That is well below the 2022 benchmark.
- **Tax overlay** (rules in the earlier note, Q7; not tax advice):
  - Hedged promo play generates gross winnings several times the net. Per $200 bonus converted at +300/−360, expected gross winnings are about $244 against $130 net (about 1.9×). Second-chance offers and boosts run about 5× (for BetMGM at −110: about $2.0k gross for about $0.4k net).
  - A ~$1.9k sweep therefore implies roughly $5.5k–$6.5k of gross winnings.
  - For a **non-itemizer** at a ~24.5% combined federal-plus-Arizona marginal rate, tax on gross winnings of about $1.3k–$1.6k leaves roughly **$300–$600 after tax**.
  - For someone **already itemizing**, taxable income is about the net plus 10% of losses (2026's 90% rule), or about $2.3k. That costs about $560 in tax and leaves about **$1.3k after tax**.
- **Reloads worth converting, ranked by my Q2 math:**
  1. **100% profit boosts**, about $8.50–$13 locked per $25 maximum.
  2. **No-sweat or bet-reset tokens** paid back as bonus bets: about 25–42% of the token stake locked, so about $7–$10 on a $25 token.
  3. **Deposit-match invites** with 1x playthrough: about 60–70% of the match, so about $30 on $50 or $60 on $100.
  4. **Referral bonuses**: about $35 per $50 bonus bet, but they require a genuine referral.
  5. **50% boosts** are marginal (about $3–$5 locked per $25). Take them only if hedging is quick.
- **Reloads to skip as hedges:**
  - **25–33% boosts** lock under $1–$2 on $20–$25 maximum stakes. They are only worth placing as small unhedged +EV bets.
  - **Parlay and SGP boosts** are hard to hedge, because correlated legs have no clean opposite at another book. Their high built-in hold often leaves them near zero even after the boost. This is an inference; I did not source SGP hold figures.
- **Monthly reload value:** across about 10 Arizona accounts, a plausible range is **$50–$300 a month** for one person. The top of that range needs active daily checks and accounts still receiving targeted offers. Value decays as books promo-restrict hedge-only accounts (Q5). This is a speculative estimate; the only figures I found are UK benchmarks and a promotional US claim.

### Gaps
- I found no US-specific, dated data on reload-promo income per month or per account, and none for Arizona.
- I could not confirm which reloads are running in Arizona this month. Promotions rotate daily and are shown in-app, and most sources are undated or from mid-2026.
- Tax figures depend on the earlier note's assumptions (per-wager accounting; Arizona following federal treatment), which are themselves unresolved.

## Q4. What bankroll is needed to work through the offers, and how long is money tied up?

### Takeaway
Plan on about **$2.5k–$3k of working capital** for a sequenced sweep that includes BetMGM's $1,500 safety net hedged at even money, converting its five $300 tokens one or two at a time. Plan on **$5k–$9k** to run everything in parallel or to take the higher-value +200/+300 qualifiers.

Without the two big second-chance offers (BetMGM, theScore), about $1k is enough. Each single conversion ties money up for hours to a few days, chosen by event start time. Across the sweep, money is spread over about 11 books for about 5 weeks. Withdrawal processing times are not sourced here.

### Cited Findings
- **Minimum deposits and the playthrough:**
  - BetMGM requires a $10 minimum deposit — [BetMGM AZ](https://www.az.betmgm.com/en/engage/lan/sports/first-bet-offer).
  - bet365 requires $10 within the 7 days before claiming — [bet365 AZ hub](https://www.bet365.com/hub/en-us/states/arizona).
  - Desert Diamond requires a deposit over $100 (at least $100.01 via affiliates), and the deposit must be wagered 1x before bonus winnings can be withdrawn — [Bet Desert Diamond help](https://help.betdesertdiamond.com/hc/en-us/articles/39783613225755--250-Welcome-Match-offer).
  - Bally requires a first-time deposit — [Bally Bet AZ](https://www.ballybet.com/az) (all via search summary).
- **Bonus credit timing:**
  - Desert Diamond credits bonus bets within 48 hours of the deposit — [Bet Desert Diamond help](https://help.betdesertdiamond.com/hc/en-us/articles/39783613225755--250-Welcome-Match-offer).
  - Bally loads tokens within 48 hours of the qualifier grading — [Bally Bet AZ](https://www.ballybet.com/az).
  - bet365 qualifying bets must settle within 30 days of claiming — [bet365 AZ hub](https://www.bet365.com/hub/en-us/states/arizona).
  - Bally's qualifier must settle within 28 days of registration — [Bally Bet AZ](https://www.ballybet.com/az) (via search summary).
- FanDuel lets you place a bonus bet before it expires on an event that settles later — [FanDuel support](https://support.fanduel.com/s/article/When-will-a-Free-Bet-expire).

### Inferences
- **Hedge capital per bonus, at +300/−360 (my arithmetic):**

| Bonus | Hedge stake | Locked cash |
|---|---|---|
| $20 | $47 | $13 |
| $50 | $117 | $33 |
| $100 | $235 | $65 |
| $200 | $470 | $130 |
| $300 (one BetMGM token) | $704 | $196 |
| $1,000 | $2,348 | $652 |
| $1,500 | $3,522 | $978 |

  At +200/−240 the hedge is about 60% of these, at slightly lower conversion.
- **Second-chance qualifiers (cash at risk = qualifier plus hedge):**
  - BetMGM $1,500: about $2.45k at −110, $3.9k at +200, $5.4k at +300.
  - theScore $1,000: about $1.6k, $2.6k and $3.6k at the same odds.
- **Sequenced minimum (about $2.5k–$3k):**
  1. Do BetMGM first at −110: $1,500 plus a $950 hedge.
  2. On a qualifier loss, the hedge pays back about $1.81k at the hedge book. Convert the five $300 tokens over the 7-day window, about $704 of hedge each, recycling capital as each settles. Same-day events keep the cycle at one day.
  3. Run theScore's reset next with the same capital.
  4. Do the small bet-and-gets alongside. They need only $5–$20 qualifiers and $47–$470 hedges.
- **Parallel or high-value path (about $5k–$9k):** BetMGM and theScore qualifiers at +200/+300 at the same time, several $200 conversions open together (about $470 each), and Desert Diamond's $250 deposit plus playthrough.
- **Where the money sits:** cash ends up scattered across the hedge books. Keep 2–3 "hedge" accounts funded with the best longshot-opposite prices; these will be books whose welcome offers are already used. Withdraw only after each book's playthrough is met and its offers are finished.
- **Duration:** each conversion ties up capital only until its event settles, so choose events starting within 24–48 hours. A bonus bet placed just before expiry on a later event (allowed at FanDuel) extends the lock-up, so avoid futures. Overall, expect the bankroll to be committed for about 5 weeks (Hard Rock's drip), with most of it free after about 2 weeks.

### Gaps
- Withdrawal processing times and methods for each Arizona book: not sourced. Desert Diamond has a withdrawal help page, but no times were surfaced.
- Whether any Arizona book requires playthrough of deposited cash before withdrawal beyond Desert Diamond and theScore's 1x deposit matches. BetRivers advertises "1X playthrough on bonus money" without detail.

## Q5. What practical pitfalls do guides, terms and communities report (terms changes, voided bets, settlement delays, minimum-odds traps)?

### Takeaway
Most losses come from fine print, not from the math. Six categories recur:
- Offers ending or changing between the affiliate page and sign-up.
- Minimum-odds and qualifier disqualifiers: −500 or −250 qualifier floors, −200 bonus floors, no cash-out, pushes, round robins, Super Boost markets.
- Short expiries: 7 days for most bonus bets.
- Eligibility traps: theScore excludes anyone with a prior PENN account; Desert Diamond excludes being on tribal land; BetMGM limits one per household or IP.
- Settlement-rule mismatches and voids that unbalance a hedge.
- Promo restriction or voided winnings for hedge-only betting patterns.

### Cited Findings
- **Terms change or lapse:**
  - BetMGM's Arizona terms show an 11/1/2026 end while it is still advertised — [BetMGM AZ](https://www.az.betmgm.com/en/engage/lan/sports/first-bet-offer).
  - Affiliate codes and amounts conflict across pages, for example BetRivers' Arizona $100 vs $250 vs $500 — [Rotowire](https://www.rotowire.com/betting/betrivers/arizona); [TopEndSports](https://www.topendsports.com/en-us/sports-betting/promo-codes/betrivers-promo-code/); [BetRivers AZ](https://az.betrivers.com/).
  - FanDuel's page title says $150 while the body says $200 — [FanDuel Research](https://www.fanduel.com/research/fanduel-new-customer-promo-get-usd200-in-bonus-bets-guaranteed) (via search summary).
- **Minimum odds and qualifier disqualifiers:**
  - bet365: −500 or longer; cash-outs, pushes and bonus-funded bets excluded — [bet365 AZ hub](https://www.bet365.com/hub/en-us/states/arizona).
  - Hard Rock: −500 or longer; round robins excluded; Early Cash Out voids eligibility — [Hard Rock Bet](https://www.hardrock.bet/sportsbook/big-game-rollout).
  - Bally: −250 minimum, first wager only, split wagers don't count — [Bally Bet AZ](https://www.ballybet.com/az).
  - Caesars: cash-out, boost-token, Super Boost and bonus-funded qualifiers are disqualified — [Caesars AZ terms](https://www.caesars.com/sportsbook-and-casino/az/support/promotions/).
  - Desert Diamond: bonus bets at −200 or longer, parlay legs included; boosted odds excluded — [Bet Desert Diamond help](https://help.betdesertdiamond.com/hc/en-us/articles/39783613225755--250-Welcome-Match-offer).
  - Fanatics excludes bonus-funded, cashed-out, voided, odds-boosted and late-settling bets — [Fanatics ALL_1406](https://sportsbook.fanatics.com/promo-terms/2024/Acquisition/ALL_1406.pdf).
  - A theScore promotion required a same-game parlay at +400 or longer — [theScore – Capitals Bet Reset](https://thescorebethelp.zendesk.com/hc/en-us/articles/42133572774541-Capitals-Bet-Reset) (via search summary).
- **Eligibility traps:**
  - theScore's $1,000 reset excludes anyone who previously registered and deposited on a PENN product — [theScore help](https://thescorebethelp.zendesk.com/hc/en-us/articles/43010570595085--1-000-Bet-Reset). ESPN BET accounts were migrated to theScore Bet automatically — [Rotogrinders](https://rotogrinders.com/sports-betting/thescorebet).
  - Desert Diamond requires being "physically present in the state of Arizona and not on Indian Lands" — [Bet Desert Diamond help](https://help.betdesertdiamond.com/hc/en-us/articles/39783613225755--250-Welcome-Match-offer).
  - BetMGM limits the offer to five per person, household (IP address) or computer — [BetMGM AZ](https://www.az.betmgm.com/en/engage/lan/sports/first-bet-offer).
  - bet365 requires a claim in the iOS or Android app within 30 days, for customers who never claimed before — [bet365 AZ hub](https://www.bet365.com/hub/en-us/states/arizona) (via search summary).
- **Settlement deadlines:** bet365 qualifiers must settle within 30 days of claiming, and Bally's within 28 days of registration, so futures can miss them — [bet365 AZ hub](https://www.bet365.com/hub/en-us/states/arizona); [Bally Bet AZ](https://www.ballybet.com/az).
- **Voids, palpable errors and settlement differences:**
  - A voided market returns the stake, which can leave a hedge unbalanced if the other leg settles — [Stoiximan help (example operator)](https://stoiximancy.zendesk.com/hc/en-us/articles/6224311502365-Why-haven-t-I-received-the-full-amount-of-my-betslip-s-potential-winnings-Dead-Heat-Obvious-Error-Void).
  - Operators reserve the right to reverse settlements made in error. In Massachusetts, BetMGM may not void for "obvious error" without Commission approval — [BetMGM MA House Rules](https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-3.28.25.pdf).
  - US regulators are split on palpable-error voids; New Jersey's policy is not to void automatically — [SBC Americas](https://sbcamericas.com/2023/12/01/draftkings-palp-error-payout-regulation/).
  - Example: Barstool voided 257 past-posted NFL bets in Massachusetts — [SBC Americas](https://sbcamericas.com/2023/09/21/barstool-nfl-vetoed-wagers/).
  - Books treat player injury and retirement differently: a bet may be void at one book and a loss at another — [NT Racing Commission decision (Australia)](https://dth.nt.gov.au/__data/assets/pdf_file/0005/479723/O-v-Ladbrokes.pdf) (via search summary; which decision carries the quote is uncertain).
- **Account restriction and voided winnings:**
  - The New York Attorney General warned that books restrict accounts for "irregular playing patterns", citing hedging, and that at least one platform blocked withdrawals as a penalty (2022) — [NY Senate / AG consumer alert](https://www.nysenate.gov/newsroom/articles/2022/kevin-thomas/consumer-alert-ag-warns-new-yorkers-deceptive-online-sports).
  - A limits guide says betting only boosts and free bets and maxing every promo without organic bets signals bonus abuse — [Gambling911](https://www.gambling911.com/gambling/how-to-avoid-getting-limited-by-sportsbooks-tips-to-keep-account-safe-110525).
  - One review rated Caesars' terms worst, because its bonus-abuse definitions are broad and allow promotional winnings to be voided retroactively — [terms.law ToS Watchdog](https://terms.law/ToS-Watchdog/sports-betting/caesars/).
  - Community anecdotes, unverified and via a Reddit mirror: an r/sportsbook user reported winnings voided days later with a negative balance billed — [r/sportsbook mirror](https://reddit.sudovanilla.org/r/sportsbook). An r/bet365 user reported being restricted to about £2 bets — [r/bet365 mirror](https://reddit.sudovanilla.org/r/bet365) (via search summary).

### Inferences
- **Checklist per offer:**
  1. Read the in-app terms at sign-up; affiliate pages lag.
  2. Screenshot the terms.
  3. Place the qualifier on a main-market moneyline or spread that settles within days, inside the odds band.
  4. Never cash out, never use a boost or bonus on a qualifier, and avoid pushes. At bet365 a push does not count, so prefer moneylines or half-point lines.
  5. Convert bonus bets well before the 7-day expiry. Put the bonus at the promo book and the hedge on the identical market and settlement rules elsewhere.
  6. Wait until the promo-book bet is accepted at the expected price before placing the hedge.
- **Choosing hedgeable markets:**
  - Prefer two-way markets whose rules match across books, such as moneylines including overtime in the NFL and NBA.
  - Avoid player props (did-not-play and void rules differ), tennis (retirement rules), three-way soccer markets, and anything with a draw or push unless both books settle it the same way.
  - A void on one leg turns a lock into a naked position.
- **Restriction risk is real but delayed.** Welcome-offer hedges are invisible to the promo book, because the hedge sits at a competitor. A run of only maximum-size promo plays with no organic action is the pattern books flag, so expect reload offers to dry up first.
- **Self-inflicted pitfalls:**
  - Geolocation: every bet must be placed physically in Arizona, and at Desert Diamond off tribal land.
  - A prior ESPN BET account disqualifies you from theScore's reset.
  - Missing FanDuel's consecutive-day requirement.
  - Letting Fanatics FanCash expire, possibly after only 24 hours.
  - Converting FanCash to casino credit at 0.5:1 instead of bonus bets at 1:1.

### Gaps
- I could not access matched-betting subreddit threads directly; the only community evidence was two mirrored, unverified anecdotes. No Arizona-specific community reports found.
- I found no ADG rule or decision on palpable-error voids or bonus-abuse voiding in Arizona. Patrons can escalate disputes to ADG, per the Caesars Arizona terms, but I found no outcomes.
- Settlement delays (for example, stat corrections or delayed prop grading) at Arizona books: not quantified.
