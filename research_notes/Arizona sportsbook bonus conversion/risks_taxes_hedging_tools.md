# Arizona sportsbook bonus conversion: terms and limit risk, 2026 taxes, Kalshi as the hedge venue, tools, and what a bot may do (status as of 2026-11-07)

Method note. Research was run on 2026-11-07.
- **How facts were gathered.** Direct page fetches failed for sportsbook.draftkings.com, irs.gov and ingame.com because those hosts are not on this session's network allowlist. Every fact below therefore comes from search-engine summaries of the cited pages ("via search summary"). Quoted operator and IRS wording is as the summary reported it; no page was read in full.
- **Dates.** Each finding carries the page or event date where one was visible. "Undated" means no date surfaced (seen 2026-11-07).
- **Bias.** Vendor and affiliate sources sell tools or earn referral fees, and are flagged as such.
- **Scope.** This note does not repeat the earlier landscape note (`research_notes/Viable trading strategies across venues/arizona_sports_betting.md`, dated 2026-11-04). That note covers the licensed-book roster, Kalshi's Arizona litigation through late September 2026, the basic 90% loss rule, Arizona's 2.5% rate, geofencing citations, and promo EV and conversion benchmarks. Facts taken from it are tagged "(earlier note)".

## Q1. What do Arizona sportsbooks' terms say about bonus abuse, hedging, matched or arbitrage betting, multiple accounts and automated tools, and what happens in practice?

### Takeaway
The Arizona and US terms I could see (DraftKings Arizona, FanDuel, bet365 US) all ban multiple accounts, "bonus abuse" and automated tools. bet365's US terms also list arbitrage as prohibited conduct. None that I found bans hedging a bonus at a *different* book. All of them, however, reserve discretion to restrict promotions, void bonuses or winnings tied to abuse, and close accounts.

For a hunter with one account per book, the realistic sanction is losing promo eligibility ("promo-banned"), not confiscation. I found no dated data on how fast that happens. Arizona, unlike Massachusetts, has no rule requiring books to explain restrictions. Disputes go to the operator first, then to the Arizona Department of Gaming (ADG).

### Cited Findings

#### Operator terms (Arizona or US versions)
- **DraftKings, Arizona Terms of Use.** The search index showed the page as about 1,255 days old (roughly mid-2023), so the live version may differ.
  - "You may establish only one (1) Account per person". If DraftKings finds more than one, it "reserves the right to suspend or terminate any or all of your Accounts" and may withhold winnings — [DraftKings AZ Terms of Use](https://sportsbook.draftkings.com/legal/az-terms-of-use).
  - Prohibited conduct includes "automated means (including without limitation harvesting bots, robots, parser, spiders, or screen scrapers)" and "any type of bonus abuse, abuse of the refer-a-friend program, or abuse of any other offers or promotions" — same page.
- **DraftKings promotion terms (undated).** DraftKings may withhold bonus rewards from customers who violate or attempt to violate the terms, "including by sharing account credentials with other individuals, placing wagers on behalf of other individuals, circumventing DraftKings age and location verification procedures" — [DraftKings P6 terms](https://www.draftkings.com/p65terms); [DraftKings JP30 terms](https://www.draftkings.com/jp25). The pages that surfaced were casino and jackpot promos; I assume, without confirmation, that sportsbook promo terms use the same wording.
- **DraftKings support (undated)** describes a strict "One Player, One Account" policy: violations "will lock or restrict your account, and may result in accounts being banned" — [DraftKings support: "Can someone make bets for me?"](https://support.draftkings.com/dk/en-us/can-someone-make-bets-for-me?id=kb_article_view&sysparm_article=KB0010374).
- **FanDuel, general Terms of Use (undated).** This is FanDuel's umbrella/DFS document, not its Arizona sportsbook terms — [FanDuel Terms of Use](https://www.fanduel.com/terms).
  - If you open, use or control more than one account, FanDuel may "suspend or terminate any or all of your accounts and terminate, withhold or revoke the awarding of any prizes".
  - "In the event of abuse of the bonus system by any user, FanDuel reserves the right to retract your user bonuses".
  - A deposit bonus is retracted if the user withdraws immediately after the deposit.
- **FanDuel sportsbook state terms (undated).** The NJ, MI, MD, NY and NC versions surfaced; the Arizona version did not — [FanDuel NJ terms](https://account.nj.casino.fanduel.com/terms); [MI](https://account.mi.casino.fanduel.com/terms); [MD](https://account.md.sportsbook.fanduel.com/terms); [NY](https://account.ny.sportsbook.fanduel.com/terms); [NC](https://account.nc.sportsbook.fanduel.com/terms).
  - The "Master Promotions" section lets the operator exclude anyone it believes entered a promotion with more than one username or account.
  - Promotions are limited to one per person, matched on identifiers such as shared household address, IP address, email, phone number and payment account.
  - Bets placed "in an attempt to defraud" the sportsbook can be voided.
  - FanDuel may refuse or restrict promotion eligibility in its sole discretion, including on the basis of wagering patterns or failure to take a promotion in good faith.
  - It may restrict, modify or withdraw any promotion at any time.
  - The Michigan version adds that bonus payments can be withheld from cancelled accounts.
- FanDuel's own glossary defines hedging neutrally, as "betting the opposing side of your original bet, to either ensure some profit or minimize potential loss" (undated) — [FanDuel support glossary](https://support.fanduel.com/s/article/Sports-Betting-Terms).
- FanDuel's terms also restrict robots, scrapers and "sniping" software. A tracker shows that clause updated May 5, 2026 (earlier note).
- Some promo terms make two-sided wagers on the same promo disqualifying (earlier note: theScore Bet; Spokesman-Review, Dec 2022).
- **bet365 US terms.** The North Carolina version is effective Sept 28, 2026; no Arizona version surfaced — [bet365 NC Help Center T&Cs](https://help.nc.bet365.com/s/en-us/terms-and-conditions); [bet365 en-us Help Centre T&Cs](https://help.bet365.com/s/en-us/terms-and-conditions).
  - Arbitrage is listed as prohibited conduct, alongside non-genuine play and unfair use. The clause applies when bet365 "discovers or has reason to believe" it occurred.
  - bet365 reserves the right to suspend markets, void transactions and return bets.
  - It may close an account without notice where it suspects prohibited activity.
- **Other Arizona books.** I could not surface the Arizona terms of BetMGM, Caesars, Fanatics, BetRivers, Hard Rock Bet, Desert Diamond, theScore Bet or Bally Bet (see Gaps).

#### Arizona rules that shape account terms
- ADG rules require each operator to "prohibit a patron from having more than one player account and username" (2022 code supplement) — [19 A.A.C. 4, Supp. 22-2](https://apps.azsos.gov/public_services/Title_19/19-04.pdf); [Cornell LII R19-4-133](https://www.law.cornell.edu/regulations/arizona/Ariz-Admin-Code-SS-R19-4-133). The rule applies per operator, so one account at each licensed book is consistent with it.
- R19-4-134 makes two patron obligations mandatory terms of every player-account agreement: rules on "allowing any other person to access or use his or her player account" and on "being physically present in the State to place a wager" (current text; date not shown) — [Cornell LII R19-4-134](https://www.law.cornell.edu/regulations/arizona/Ariz-Admin-Code-SS-R19-4-134).
- An event wager "shall not be accepted from a person who is placing the event wager for the benefit of another for compensation" (2022 supplement; excerpt truncated) — [19 A.A.C. 4](https://apps.azsos.gov/public_services/Title_19/19-04.pdf).
- R19-4-128 lists "promotional or bonus credit" among the accepted ways to fund a wager (2022 supplement) — same source.
- I found no ADG rule on hedging, matched betting or arbitrage. These are left to operator terms, which matches the earlier note.

#### What happens in practice
- **Legal status.** No US federal or state law criminalizes arbitrage betting; the consequences are contractual (limits, closure) — [AVO (vendor, undated)](https://www.avo.bet/articles/is-arbitrage-betting-legal); [Bleacher Nation, Dec 27, 2024](https://www.bleachernation.com/betting/2024/12/27/arbitrage-betting/).
- **Hedging at another book.** Matched-betting sites say the terms they reviewed do not prohibit hedging at other sportsbooks. What gets accounts banned is multi-accounting and identity fraud. Hedging a cash bet against a bonus bet at the *same* book does breach terms — [Ungambled (advocacy, undated)](https://www.ungambled.com/blog/matched-betting-bonus-hunting/bonus-abuse-vs-bonus-hunting/); [ProfitDuel (vendor, undated)](https://www.profitduel.com/blog/avoid-sportsbook-account-limited).
- **Two tiers of sanction.** A "promo banned" account stays open for normal bets but gets no promos; a "complete ban" closes the account. Using only bonus bets and promotions is itself a recognizable matched-betting pattern — [ProfitDuel (vendor, undated)](https://www.profitduel.com/blog/avoid-sportsbook-account-limited).
- **Voids are the exception.** In regulated markets, operators generally cannot simply void an arbitrager's winnings; voids are mostly used for bets at obviously wrong ("palpable error") lines. Typical responses are lower stake limits, removal of promo eligibility, suspension or closure, and voids only where the terms allow — [AVO (vendor)](https://www.avo.bet/articles/is-arbitrage-betting-legal); [AVO, avoiding limits (vendor)](https://www.avo.bet/articles/how-to-avoid-sportsbook-limits).
- **Permanence.** bet365 stake limits and offer restrictions "usually stay in place permanently" (anecdotal, UK-focused, undated) — [Racing Post](https://www.racingpost.com/online-casino/articles/bet365-account-restricted/); [AceOdds](https://www.aceodds.com/articles/bet365-account-restrictions.html).
- **Speed of promo restriction.** I found no dated, credible US data on how fast promo-only accounts lose promo eligibility. The earlier note found none either.
- **Withdrawal speed** (Nov 2026 affiliate reviews; they conflict):
  - Online bank transfer is instant at DraftKings, FanDuel and Fanatics, and takes 24–48 business hours at some other books — [CBS Sports, Nov 2026](https://www.cbssports.com/betting/news/fast-withdrawal-betting-sites/).
  - BetMGM 2–3 hours, FanDuel 4–5 hours, DraftKings 4–6 hours — [SI](https://www.si.com/betting/usa/fastest-payout).
  - FanDuel can take up to 48 hours to process, and DraftKings is slightly slower — [Covers, 2026](https://www.covers.com/betting/fanduel-vs-draftkings).
  - BetMGM internal processing can take up to 5 business days, especially for first-time or large withdrawals. The summary did not say which guide made this claim: [SportsBettingDime](https://www.sportsbettingdime.com/sportsbooks/banking/fastest-payouts/) or [GamingToday](https://www.gamingtoday.com/sports-betting/fastest-payout-sportsbooks/).
- **Arizona dispute route** (FAQ undated; rules 2022) — [ADG Complaints FAQ](https://gaming.az.gov/faq-sub-categories/complaints); [19 A.A.C. 4](https://apps.azsos.gov/public_services/Title_19/19-04.pdf):
  - A patron with an unresolved dispute "MUST FIRST FILE A COMPLAINT WITH THE RELEVANT OPERATOR".
  - The operator's response must tell the patron of the right to escalate.
  - The patron may then file with ADG under R19-4-148.A. ADG may investigate and order corrective action.
  - The rule sets a deadline for the operator's written response; the excerpt reads "within 10…" (unconfirmed).
- **Massachusetts contrast.** A Massachusetts Gaming Commission rule reportedly requires books to notify a bettor within 48 hours of restricting an account, with a specific explanation, effective June 1, 2026. This is from secondary sources; I did not read the rule text — [BettingSite.net](https://www.bettingsite.net/blog/sportsbook-limiting-winning-bettors/); [BetHero](https://betherosports.com/blog/can-sportsbooks-ban-you-for-winning). The earlier note found no comparable Arizona rule.

### Inferences
- **The real sanction is discretionary.** Cross-book hedges are invisible to each book. The betting pattern is visible: promo-only action, maximum stakes, plus-money targets. FanDuel's "wagering patterns" and "good faith" language is broad enough to restrict promos for that pattern without any ToS breach.
- **Five actions break an explicit clause.** These turn a promo restriction into a confiscation risk:
  1. A second account at the same book, including using a household member's account.
  2. Letting anyone, or any software, use your credentials.
  3. Betting both sides of a promo at the same book.
  4. Any location spoofing.
  5. Withdrawing a deposit bonus immediately (FanDuel).
- **Household overlap.** FanDuel matches on household address, IP address and payment account, so two adults in one home may be held to one promotion. Separate devices, payment methods and accounts help, but expect the book may still treat the home as one household.
- **bet365 arbitrage clause.** bet365's US terms name arbitrage, so a two-book arb leg there risks a void, not just a limit. A bonus-bet hedge taken at fair prices is not arbitrage in the usual sense, but a book could label it as such.
- **Practical defenses.**
  - Clear identity checks and make a small test withdrawal at each book early, before large promo balances build up.
  - Screenshot promo terms when you opt in, since books can modify promotions at any time.

### Gaps
- I did not see the Arizona terms of BetMGM, Caesars, Fanatics, BetRivers, Hard Rock Bet, Desert Diamond, theScore Bet or Bally Bet, nor FanDuel's Arizona sportsbook terms. The DraftKings Arizona text may be stale (about 2023).
- No dated US or Arizona data on time to promo restriction, how often bonuses are clawed back, or how ADG resolves bonus disputes.
- The exact R19-4-148 response deadline and the post-2022 text of R19-4-128, -133 and -134 are unconfirmed.

## Q2. Taxes for 2026: how are sportsbook winnings and converted bonus bets taxed federally and in Arizona, how should results be tracked, and does matched betting create "phantom" taxable income?

### Takeaway
For tax year 2026:
- Every winning wager's profit is gross income.
- Losses are deductible only on Schedule A, only at 90%, and only up to winnings.
- The W-2G threshold rose to $2,000, but a form is still required only when winnings are at least 300× the wager. Promo conversion therefore almost never produces a form, even though all of it is reportable.
- Arizona (flat 2.5%) conformed to the Internal Revenue Code as of Jan 1, 2026 in a June 2026 omnibus bill, so the 90% cap probably carries into Arizona itemized deductions (unconfirmed).

Matched betting does create phantom income whenever a bonus bet wins while its hedge loses at another venue. In my arithmetic:
- A non-itemizer is taxed on about 1.9× the economic profit of a $200 bonus-bet conversion.
- A non-itemizer can end up after-tax negative on a large first-bet-insurance offer.
- An itemizer keeps about 65–75% of pre-tax value.

### Cited Findings

#### Federal rules for 2026
- **90% cap.** OBBBA §70114 amended IRC §165(d). For tax years beginning after Dec 31, 2025, only 90% of wagering losses are deductible, still limited to wagering gains and only as an itemized deduction — [National Tax Tools, 2026](https://nationaltaxtools.com/guides/gambling-loss-deduction/); [Keeper, 2025–26](https://www.keepertax.com/posts/are-gambling-losses-tax-deductible).
- The IRS's January 2026 W-2G instructions state you "can deduct 90% of your gambling losses as an itemized deduction, but the amount you deduct cannot be more than the amount of your winnings" — [IRS Instructions for Forms W-2G and 5754 (Rev. Jan 2026)](https://www.irs.gov/instructions/iw2g).
- **W-2G threshold** (Rev. Jan 2026) — [IRS W-2G instructions](https://www.irs.gov/instructions/iw2g); [iw2g PDF](https://www.irs.gov/pub/irs-pdf/iw2g.pdf); [Form W-2G (Rev. Jan 2026)](https://www.irs.gov/pub/irs-pdf/fw2g.pdf); [IRS Pub 1099 (2026 edition per summary)](https://www.irs.gov/pub/irs-pdf/p1099.pdf):
  - "The minimum threshold amount for payments made in calendar year 2026 is $2,000." It is adjusted for inflation in later years.
  - For sports wagering, a W-2G is filed only if winnings meet the threshold and are "at least 300 times the amount of the wager".
  - A proposed regulation (REG-113229-25) also applies $2,000 to bingo, keno and slots — [IRB 2026-19](https://www.irs.gov/irb/2026-19_IRB).
- **Withholding** (Rev. Jan 2026) — [IRS W-2G instructions](https://www.irs.gov/instructions/iw2g):
  - Regular withholding of 24% applies when winnings minus the wager exceed $5,000 and are at least 300× the wager.
  - Backup withholding of 24% applies if the winner gives no taxpayer ID (TIN) on reportable winnings up to $5,000.
- **Reporting duty and records** (current IRS page, undated) — [IRS Topic 419](https://www.irs.gov/taxtopics/tc419):
  - Gambling winnings are "fully taxable" and must be reported whether or not a form arrives.
  - To deduct losses you "must keep an accurate diary or similar record" and be able to provide "receipts, tickets, statements, or other records that show the amount of both your winnings and losses".
  - Losses count only if you itemize on Schedule A.
- **Diary contents.** Publication 529 (Rev. Dec 2020, older) lists the date and type of each wager, where it was placed, who was present, and the amounts won or lost. You cannot net losses against winnings and report the difference — [IRS Pub 529 (12/2020)](https://www.irs.gov/publications/p529).
- **Bonus bets.** I found no IRS guidance specific to bonus bets, and tax-prep pages conflict.
  - They agree that profit won with a bonus bet is taxable.
  - One says the bonus credit itself is not income until it produces winnings.
  - Another says the IRS "generally views Bonus Bets, Site Credits, and promotional prizes as taxable income at their fair market value".
  - The summary did not attribute each view to a specific page: [Tax Defense Network](https://www.taxdefensenetwork.com/blog/do-i-have-to-pay-taxes-on-sports-betting/); [Jackson Hewitt](https://www.jacksonhewitt.com/tax-help/tax-tips-topics/filing-your-taxes/gambling-winnings/); [MyTaxFella](https://mytaxfella.com/blog/do-you-have-to-pay-taxes-on-sports-betting); [Claimyr Q&A, Apr 2025 (anecdotal)](https://claimyr.com/government-services/irs/How-should-I-report-gambling-winnings-from-bonus-money-for-taxes/2025-04-11).
- **Repeal status** — [Legal Sports Report, Sept 2026](https://www.legalsportsreport.com/277757/gambling-loss-deduction-fix-clears-key-hurdle/); [Las Vegas Sun, Sept 17, 2026](https://lasvegassun.com/news/2026/sep/17/house-ways-and-means-committee-advances-bill-to-re/); [BettingNews, Sept 2026](https://www.bettingnews.com/articles/industry/h-r-10357-advances-gambling-loss-tax-deduction-fix/); [GamblingTaxHelp (undated)](https://www.gamblingtaxhelp.com/repeal-efforts/):
  - On Sept 16, 2026, House Ways & Means approved repealing the 90% cap inside H.R. 10357 (Digital Asset Tax Certainty Act), effective for tax years beginning after Dec 31, 2025.
  - The language that moved came from the FULL HOUSE Act, not Rep. Titus's FAIR BET Act (H.R. 4304). The Rules Committee had declined to attach the FAIR BET Act to the NDAA.
  - Searches on 2026-11-07 found no House floor vote and no Senate action. Titus is pressing for a House vote before Jan 1, 2027.
  - As enacted, the 90% rule applies to tax year 2026.

#### Kalshi hedge legs
- No Revenue Ruling, private letter ruling or IRS FAQ classified event contracts as of July 16, 2026 — [PredictionMarketLaws](https://predictionmarketlaws.com/guides/prediction-market-taxes).
- Kalshi reportedly issues 1099-INT for interest, 1099-MISC for credits and rewards, and 1099-B or 1099-DA for crypto transfers, but no 1099-B for event-contract trades. One source conflicts — [Awaken Tax, 2026](https://awaken.tax/media/article/kalshi-taxes); [CoinLedger, 2026](https://coinledger.io/blog/prediction-markets-tax).
- Practitioners variously treat event contracts as Section 1256 contracts, capital gains, wagering or ordinary income. Sports-outcome contracts are seen as the most likely to count as gambling income. Whether the 90% cap applies to them is open — [CoinLedger](https://coinledger.io/blog/prediction-markets-tax); [Camuso CPA](https://camusocpa.com/kalshi-tax-reporting/); [Monaco CPA](https://www.monacocpa.cpa/prediction-market-tax) (2026 tax-firm blogs).

#### Arizona
- Arizona taxes gambling winnings at its flat 2.5% rate, with 2.5% withholding (earlier note).
- **2026 conformity.** HB 4168 / SB 1861 ("taxation; omnibus; 2026-2027") was enacted, with legislative action completed June 13, 2026. Its Senate fact sheet says it conforms Arizona statutes to the IRC "as of January 1, 2026" and modifies individual income tax deductions; the snippets do not say which ones — [SB 1861 fact sheet, as enacted](https://www.azleg.gov/legtext/57leg/2R/summary/S.1861-4168ATT_ASENACTED.DOCX.htm); [HB 4168 fact sheet, as enacted](https://www.azleg.gov/legtext/57leg/2R/summary/S.4168-1861ATT_ASENACTED.DOCX.htm).
- **Earlier attempts.**
  - An earlier conformity bill, HB 2785, was vetoed in Feb 2026 — [HB 2785 summary](https://www.azleg.gov/legtext/57leg/2R/summary/H.HB2785_021326_VETOEDBYTHEGOVERNOR.DOCX.htm).
  - SB 1106 (prefiled Jan 8, 2026) would have conformed while excluding the $6,000 senior deduction, the $40,000 SALT cap and the car-loan interest deduction. It listed no gambling exclusion — [JLBC fiscal note, SB 1106](https://www.azleg.gov/legtext/57leg/2R/fiscal/SB1106.PDF).
- Arizona's Schedule A instructions (about 2023) allow wagering losses "only to the extent of your wagering gains" — [ADOR Form 140 Schedule A instructions](https://azdor.gov/sites/default/files/2023-03/Forms-Individual-2001-140SchedA-i.pdf).

### Inferences
Not tax advice. These assume per-wager accounting, as in the earlier note.
- **Where phantom income comes from.** Each bet stands alone. A winning bet's profit is income; a losing cash stake is an itemized loss allowed at 90%. A losing bonus bet produces no deductible loss, because no money was wagered, unless the bonus counted as income on receipt (unresolved).
- **Example 1: a $200 bonus bet at +300, hedged at another book at −360.** The hedge stake is $469.57 and locks $130.43. Take the chance the bonus wins as about 25%.
  - **Bonus wins:** $600 of gambling income and a $469.57 loss. Taxable income is $600 for a non-itemizer, or $600 − 0.9 × $469.57 = $177.39 for an itemizer.
  - **Bonus loses:** $130.43 of income and no deductible loss.
  - **Expected taxable income:** $247.83 for a non-itemizer (1.9× the profit) and $142.18 for an itemizer (1.09×).
  - **After tax at 24.5%** (22% federal + 2.5% Arizona): about $70 for a non-itemizer (53% of pre-tax) and about $96 for an itemizer (73%).
  - **Kalshi hedge instead:** if Kalshi losses count as capital losses, usable against other capital gains or up to $3,000 a year of ordinary income, the phantom income largely disappears and about $107 remains after tax. If Kalshi losses count as wagering losses, the result matches the book hedge.
- **Example 2: first-bet insurance, $1,500 qualifier at −110.** Hedge $950 at −110 at another book, value the bonus at 70% for sizing, convert the $1,500 of bonus bets at 65%, and take the qualifier as a coin flip.
  - **Expected economic value:** about $378.
  - **Non-itemizer:** expected taxable income is about $2,040, so tax at 24.5% is about $500 and the offer is worth about −$120 after tax. At a 14.5% combined rate (12% federal bracket) it is worth about +$80.
  - **Itemizer:** expected taxable income is about $545, tax is about $134, leaving about +$245 after tax (65% of pre-tax).
  - Large insurance offers are where the 2026 rules bite hardest.
- **Decide on itemizing first.** Whether a full Arizona sweep pays depends mostly on whether you itemize, or would once 90% of gambling losses is added to SALT, mortgage interest and charity. A sweep plausibly generates five figures each of gross winnings and losses (my estimate).
  - Non-itemizers should favor small "bet $X, get bonus bets" offers over large insurance qualifiers, and keep cash qualifiers small.
  - The tax-optimal bonus-bet odds shift slightly shorter. Even so, in my arithmetic +300 still beats +100 for a non-itemizer: about 35¢ versus 28¢ after tax per $1 of bonus.
- **No third-party reporting.** W-2Gs will almost never be issued for this activity: a +300 payout is 3× the stake, far below the 300× test. The IRS gets no third-party report, but the income is still reportable. Leaving it off a return would be evasion, and the ledger is the defense.
- **How to track.** Keep one ledger row per wager:
  - date and time, venue (book or Kalshi), market and its settlement rules
  - odds, cash or bonus stake, payout, result
  - an offer ID linking qualifier, bonus and hedge legs
  - the Kalshi order or fill ID, and fees

  Reconcile each year to every book's account-activity export, Kalshi statements and bank transfers. Keep bet-slip screenshots and the promo terms. Gross winnings go on the return in full; losses go on Schedule A at 90%.
- **Arizona.** Arizona conformed to the IRC as of Jan 1, 2026, which includes §70114, so its itemized gambling-loss deduction is most likely also capped at 90% (inference). At 2.5%, Arizona adds only about 2.5¢ of tax per $1 of phantom income.

### Gaps
- Whether HB 4168 / SB 1861 decoupled from §70114: not seen.
- Whether Arizona still lets taxpayers itemize on the state return while taking the federal standard deduction. I recall that it has since about 2019, but did not verify this session.
- No IRS authority found on (a) whether bonus credits are income on receipt, or (b) any session or netting method for sports wagers. The 2026 federal standard deduction (about $16k single) was not verified this session.
- Kalshi sports-contract classification and tax forms remain unresolved (no guidance as of July 2026).
- Whether Arizona books provide annual win/loss statements: not checked.

## Q3. Can Kalshi sports contracts serve as the hedge leg (coverage, liquidity, fees, settlement timing, rule mismatches), and what is Kalshi's legal status for Arizona residents as of November 2026?

### Takeaway
Kalshi works as a hedge leg for bonus bets in main game markets.
- **Liquidity:** major-league game-winner, spread and total markets are deep; a record $4.86B traded over NFL Week 1 of 2026.
- **Fees:** at typical hedge prices (70–80¢) the taker fee is about 1.1–1.5¢ per contract. Against a +300 bonus that equals roughly −320 for the opposite side, versus −360 or worse at a book.
- **Timing:** most markets settle within a few hours, and ACH withdrawals take 1–3 business days.

Hedge only where the rules match:
- Kalshi counts overtime.
- It pays $0.50 per contract on a tie when the market has no Tie strike.
- It settles games not started within 48 hours, and player props for players who never play, at its own "fair price" rather than voiding.
- Props and live markets are thin.

Legally, Arizona access still rests on the May 5, 2026 federal injunction; I found no ruling on Arizona's motion to dissolve it as of Nov 7. A Nov 4, 2026 injunction blocking Kalshi sports contracts on two California tribes' lands, enforced with GeoComply location blocks, is a model Arizona tribes could follow (inference).

### Cited Findings

#### Fees
- **Taker fee.** Multiplier × 0.07 × contracts × price × (1 − price), rounded up; Kalshi's own example is 100 contracts at 60¢ for $1.68. Maker fees apply only on listed markets and only when a resting order fills. Tennis (ATP/WTA) match markets and World Cup game markets carry a multiplier of 1 — [Kalshi Fee Schedule, July 2026 ("7.7.26 Update")](https://kalshi.com/docs/kalshi-fee-schedule.pdf); [Kalshi Help, Fees (undated)](https://help.kalshi.com/en/articles/13823805-fees).
- **Combo maker fee.** An August 2026 changelog entry sets a 0.5 multiplier for combos, versus the standard 0.25. Combos created after 11:59 PM ET on Aug 19, 2026 that consist entirely of independent NFL legs carry no maker fee — [Kalshi API changelog](https://docs.kalshi.com/changelog).

#### Settlement and cash timing
- **Typical settlement.** Most markets settle "within a few hours after the outcome is known", often about three hours, and longer when Kalshi is waiting on official data. A market still showing open does not mean the payout criteria are unmet — [Kalshi Help, Market FAQs (undated)](https://help.kalshi.com/en/articles/13823821-market-faqs); [Kalshi News, market life cycle (about Aug 2025)](https://news.kalshi.com/p/what-is-the-market-life-cycle).
- **Dispute window.** Once a market is determined, a settlement timer (`settlement_timer_seconds`) runs, during which the result may be disputed — [Kalshi API, Market Lifecycle](https://docs.kalshi.com/getting_started/market_lifecycle).
- **Combos.** These settle 1–12 hours after the last leg resolves, or immediately at $0 if any leg settles at $0 — [Kalshi Help, Combos](https://help.kalshi.com/en/articles/13823820-combos).
- **Withdrawals** (third-party 2026 guides; they conflict) — [CaliforniaPredictionMarkets](https://californiapredictionmarkets.com/guides/how-to-withdraw-from-kalshi); [KalshiView](https://kalshiview.com/blog/kalshi-withdrawal-guide-how-long-does-it-actually-take/); [Prediction.com](https://prediction.com/blog/kalshi-fees-complete-guide-2026):
  - ACH: free, 1–3 business days.
  - Debit card: hours; the fee is reported as up to $2 by one guide and none by another.
  - Wire: $5–$30.

#### Rule mismatches with sportsbooks
- **NFL game contract** (undated; the PDF text came through fragmented, so verify the wording) — [Kalshi NFLGAME contract terms](https://assets.kalshi.com/contract_terms/NFLGAME.pdf); [SportsIndex settlement guide](https://sportsindex.io/guides/prediction-market-settlement-rules); [OddsShopper, postponed games (2026)](https://www.oddsshopper.com/articles/prediction-markets/kalshi-postponed-game-rules):
  - All overtime periods count toward the winner.
  - **Ties:** if the market lists a "Tie" strike, it resolves Yes and both team strikes resolve No. With no Tie strike, each team's contracts pay $0.50.
  - **Postponements:** a game that begins within 48 hours of its scheduled time settles on its result. Otherwise the market resolves to "the last fair market price as determined by Kalshi", which is not a refund.
- **Other sports and props** (secondary 2026 guides) — [DarkHorse Odds](https://about.darkhorseodds.com/guides/kalshi-polymarket-market-rules); [AgentBets](https://agentbets.ai/news/player-injury-rules-sportsbooks-prediction-markets/); [OddsShopper](https://www.oddsshopper.com/articles/prediction-markets/kalshi-postponed-game-rules):
  - Sportsbooks typically void postponed games and return the stake.
  - Kalshi settles a shortened MLB game on its result if an official final is declared.
  - Kalshi soccer contracts define several result scopes, and cup matches count extra time.
  - Sportsbooks void props for a player who never plays. Kalshi may settle them at the last fair price, which has caught out traders expecting sportsbook rules.
  - Kalshi's NFL, soccer and NHL props use the price before game start.
- **NFL player markets** — [Kalshi Help, Protected NFL Player Markets](https://help.kalshi.com/en/articles/17515177-protected-nfl-player-markets); [Kalshi FOOTBALLENTITYSTAT terms](https://assets.kalshi.com/contract_terms/FOOTBALLENTITYSTAT.pdf):
  - A standard market carries no injury protection. An active player who never takes a snap settles at the fair price before game start.
  - A "protected" market settles at the pre-kickoff fair price if the player plays in the first half but not the second half or overtime and has not reached the target. Protection is chosen in the combo builder and cannot be added after trading.
  - The contract template says an inactive or non-playing player resolves at "the last fair price as determined by the Exchange in its sole discretion".
- **Ladder and escalator yardage markets.** A player who does not play settles at a fair price Kalshi sets at its discretion, possibly based on trading before the absence was known; this is not a refund — [Kalshi Help, Ladder and Escalator Markets](https://help.kalshi.com/en/articles/17516391-ladder-and-escalator-markets).

#### Coverage, liquidity and size
- **Coverage.** Kalshi lists NFL spreads, totals, quarter markets and player props (2026) — [OddsShopper, Kalshi NFL props](https://www.oddsshopper.com/articles/prediction-markets/kalshi-nfl-props); [OddsShopper, player props](https://www.oddsshopper.com/articles/prediction-markets/kalshi-player-props).
- **Volume.** $4.859B traded over NFL Week 1, a record (Sept 2026) — [PredictionNews](https://predictionnews.com/story/kalshi-posts-record-4-9-billion-football-weekend-volume).
- **Depth** (reviews and vendors; Nov 2026 for Sharp Football Analysis, others 2026) — [Sharp Football Analysis Kalshi review](https://www.sharpfootballanalysis.com/prediction-markets/kalshi/); [Alphascope, order book](https://www.alphascope.app/blog/kalshi-order-book-explained); [Legal Sports Report Kalshi review](https://www.legalsportsreport.com/prediction-markets/kalshi-review/); [SI](https://www.si.com/prediction-markets/reviews/kalshi-vs-polymarket):
  - The deepest books are marquee events such as prime-time NFL games.
  - Live markets and props are "not nearly as deep" as at sportsbooks.
  - In one worked example, a 200-contract market order on a prop swept four price levels: it filled at about 17¢ on a market that displayed 14¢.
  - Legal Sports Report rates liquidity 3.5/5 and says the book can thin quickly; SI calls it deeper across established markets.
- **Position accountability.** Kalshi's Jan 22, 2025 CFTC filing for "Will <team> win?" title contracts sets a position accountability level of $25,000 per strike per member. That is a soft threshold, not a hard cap. Levels for game markets were not confirmed — [Kalshi CFTC filing, Jan 22, 2025](https://www.cftc.gov/sites/default/files/filings/ptc/25/01/ptc01222514045.pdf); [OddsShopper, position limits](https://www.oddsshopper.com/articles/prediction-markets/kalshi-position-limits).

#### Legal status for Arizona residents (updates since the earlier note)
- **Nevada.** On Aug 28, 2026 a three-judge Ninth Circuit panel ruled unanimously against Kalshi in *KalshiEX v. Assad* (No. 25-7516) — [Ninth Circuit opinion](https://cdn.ca9.uscourts.gov/datastore/opinions/2026/08/28/25-7516.pdf).
  - Kalshi said it "will be seeking further review" — [OddsShopper, 2026](https://www.oddsshopper.com/articles/prediction-markets/where-is-kalshi-legal) (the summary did not clearly attribute the quote).
  - An InGame headline refers to Kalshi's request for a Ninth Circuit rehearing; the page could not be read — [InGame](https://www.ingame.com/ninth-circuit-states-plan-predictions-stopped/).
- **Arizona.** In September 2026, AG Mayes asked the Ninth Circuit to dissolve or summarily vacate Judge Liburdi's injunction — [AZ Mirror, Sept 25, 2026](https://azmirror.com/2026/09/25/after-9th-circuit-ruling-mayes-pushes-to-revive-her-gambling-case-against-kalshi/); [GamblingNews](https://www.gamblingnews.com/news/arizona-attempts-to-restart-legal-fight-against-kalshi/); [Law360 (headline only)](https://www.law360.com/articles/2476284/kalshi-to-take-arizona-injunction-bid-to-9th-circ-); context: [Yogonet, Sept 2, 2026](https://www.yogonet.com/international/news/2026/09/02/126190-arizona-ninth-circuit-ruling-backs-state-authority-over-kalshi-sports-contracts-but-election-dispute-remains).
  - Searches on 2026-11-07 found no ruling on that motion.
  - Sources still conflict on whether the May 5 order is preliminary or permanent — [DeFi Rate](https://defirate.com/news/federal-judge-permanently-blocks-arizona-criminal-case-vs-kalshi/); [Courthouse News](https://www.courthousenews.com/judge-shields-kalshi-election-wagering-in-arizona/).
- **Tribal lands (California)** — [iGaming Express](https://igamingexpress.com/kalshi-tribal-lands-sports-contracts-injunction/); [SportsBettingDime](https://www.sportsbettingdime.com/news/industry/judge-bans-kalshi-sports-contracts-on-two-california-tribes-land/); [World Casino Directory](https://news.worldcasinodirectory.com/california-tribes-win-injunction-against-kalshi-sports-markets-125007); [Law360 (headline only)](https://www.law360.com/articles/2546990/tribes-win-injunction-against-kalshi-after-9th-circ-reversal-):
  - On Sept 16, 2026 the Ninth Circuit ruled for the tribes under the Indian Gaming Regulatory Act (IGRA) in *Blue Lake Rancheria v. Kalshi* (No. 25-7504) — [Ninth Circuit opinion](https://cdn.ca9.uscourts.gov/datastore/opinions/2026/09/16/25-7504.pdf).
  - On Nov 4, 2026 a federal judge in the Northern District of California barred Kalshi from offering sports contracts on the lands of the Blue Lake Rancheria and the Chicken Ranch Rancheria. One summary gave the date as Nov 5 and said three tribes; most reports say two.
  - Kalshi said it had worked with GeoComply on location blocks. The tribes reported a trade placed from tribal land after the blocks were announced.
  - The tribes must provide boundary maps by Nov 13, 2026.

### Inferences
- **Fee and equivalent odds** (my arithmetic from the fee formula; taker fee per contract, before any spread):

| Hedge price | Fee | Fee as % of cost | Effective American odds |
|---|---|---|---|
| 90¢ | 0.63¢ | 0.7% | −967 |
| 80¢ | 1.12¢ | 1.4% | −430 |
| 75¢ | 1.31¢ | 1.75% | −322 |
| 67¢ | 1.56¢ | 2.3% | −215 |
| 60¢ | 1.68¢ | 2.8% | −161 |
| 50¢ | 1.75¢ | 3.5% | −107 |

  Paying a 1¢ spread on top (buying at 76¢ when 75¢ is fair) moves −322 to about −340.
- **Sizing formula for a bot.** To hedge a stake-not-returned bonus bet of B at decimal odds D, buy N = B × (D − 1) contracts on the opposite outcome at an all-in cost c = ask price + fee.
  - Locked profit = N × (1 − c), so conversion = (D − 1) × (1 − c).
  - A sportsbook hedge at decimal odds H converts at (D − 1) × (H − 1) / H.
  - At +300: c = 76.3¢ gives 71%; a 77.3¢ all-in cost (76¢ ask) gives 68%; a −360 book hedge gives 65%.
- **Order handling.** Fees are rounded up, which penalizes many small orders. Place each hedge as one order, ideally a limit order at the computed price.
- **Best fits:**
  - NFL, NBA and NHL game-winner markets, where both venues count overtime.
  - NFL and college-football spreads and totals at the same number as the book line.
  - Hedge close to game time, and only after the sportsbook leg is confirmed.
- **Avoid as hedges:**
  - Soccer three-way markets against Kalshi's scopes.
  - Props: thin, and a non-playing player settles at a fair price instead of voiding.
  - Live markets and combos.
  - MLB "listed pitcher" bets, which a book voids on a pitcher change and Kalshi does not.
- **Tie and postponement outcomes:**
  - An NFL tie pays $0.50 per hedge contract. If the book grades the bonus bet a push and returns the token (common practice, unverified for Arizona books), the hedger ends roughly neutral.
  - A postponement beyond 48 hours voids the book leg while Kalshi settles near the mid. The loss is about the fee plus spread plus any drift.
- **Size is not the constraint.** Promo hedges of $500–$5,000 are far below a $25k accountability level, so depth at the ask is what binds on main markets.
- **Legal risk is mainly a forced exit.** Whether a user faces legal exposure is unresearched (see the earlier note's gap).
  - Keep hedges same-day so nothing is stranded if Kalshi geofences Arizona after a Ninth Circuit ruling.
  - Kalshi's use of GeoComply shows device location now matters.
  - An Arizona IGRA suit modeled on *Blue Lake* could block Kalshi sports on reservation land. This is speculative; I found no Arizona tribal suit.
  - Never route around a block with an out-of-state server or VPN.

### Gaps
- No ruling found on Arizona's motion to dissolve as of 2026-11-07. The status of Kalshi's rehearing petition in the Nevada case is unknown, because InGame was unreadable.
- Arizona books' own tie, postponement and non-participant rules were not read. Kalshi's tennis-retirement, MLB pitcher-change and soccer-scope texts were not read in full.
- No measured order-book depth at typical hedge sizes ($500–$5,000) per sport, and no position limits for game markets.

## Q4. What tools exist (odds screens, matched-betting calculators, odds APIs), what do they cost, which free options are adequate, and how much time does it take?

### Takeaway
For a one-time Arizona sign-up sweep, free tools are enough:
- a free odds screen (Unabated's free tier, or Betwatch in beta)
- Kalshi's own order book and free API
- a simple calculator, easy to code or available free
- a spreadsheet ledger

Paid suites mostly pay off for reloads, positive-expected-value (+EV) betting and arbitrage:
- OddsJam: about $200–$500 a month (reports conflict), with a promo converter
- Unabated Premium: $199 a month
- Outlier: $20–$80 a month

For a bot, The Odds API's free 500 credits a month cover a few on-demand lookups a day, and its $30 tier supports a modest scanner. Vendors claim 15–20 minutes per offer after about an hour of learning. I estimate 10–20 hours in total for a full Arizona sweep.

### Cited Findings

#### Odds screens and betting suites (2026 affiliate or competitor reviews; prices conflict)
- **Betwatch:** free during beta; shows about 40 odds sources side by side with the best price flagged — [Betwatch (vendor)](https://betwatch.io/best/odds-screens).
- **Unabated** — [XCLSV Unabated review 2026](https://xclsvmedia.com/unabated-review-2026-premium-sharp-bettor-tool-worth-it/); [SmartStake (competitor)](https://www.smartstake.app/learn/oddsjam-vs-unabated):
  - Free sign-up tier. Its screen covers dozens of books, exchanges and prediction markets beside the "Unabated Line".
  - Premium costs $199 a month or $1,584 a year.
  - One review says it has no promo converter and only partial arbitrage.
- **OddsJam** — [The Sport Stack](https://thesportstack.io/learn/oddsjam-alternatives); [BetResearcher](https://betresearcher.com/tools/compare/best-oddsjam-alternatives/); [Oddible](https://oddible.ai/blog/best-sports-betting-analytics-apps-in-2026-ranked-and-compared):
  - 7-day free trial. Covers +EV, arbitrage, middles, line shopping, a promo converter and a bet tracker.
  - Reported prices conflict: Gold about $199.99 and Platinum about $499 (Sept 2026); a top tier near $498 a month; or tiers of $99, $199 and $299. There is no plain public price list.
- **Outlier:** $19.99, $29.99 (early-bird) or $79.99 a month, with a 7-day trial. Prop-focused +EV, arbitrage and middles; no promo converter found — [XCLSV comparison 2026](https://xclsvmedia.com/oddsjam-vs-avo-vs-outlier-best-ev-betting-software-compared-2026/).
- **Promo-math and tracking tools** (all vendors; pricing not found):
  - [PromoMath](https://promomath.com/), billed as "Sportsbook promo math, hedging, and tracking"
  - [SmartStake matched-betting docs](https://www.smartstake.app/docs/matched-betting)
  - [ProfitDuel](https://www.profitduel.com/matched-betting), a paid US matched-betting service
  - [DarkHorse Odds guides](https://about.darkhorseodds.com/guides/what-is-matched-betting)
  
  The earlier note cites free calculators (TopEndSports, Action Network).

#### Odds APIs
- **The Odds API** — [SportsAPIs.dev review](https://sportsapis.dev/apis/the-odds-api); [OddsPapi, free-tier limits (competitor)](https://oddspapi.io/blog/the-odds-api-free-tier-limits/); [OddsPapi pricing comparison (competitor)](https://oddspapi.io/blog/odds-api-pricing-2026-comparison/):
  - The free Starter plan gives 500 credits a month and is "permanently free", per one review. Paid plans start at $30 a month for 20,000 credits.
  - Each call costs (number of markets) × (number of regions) credits. 500 credits is therefore about 83 multi-market calls, or about 16 requests a day. Historical odds cost 10× more.
  - Odds update about every 60 seconds pre-match and 40 seconds in-play (earlier note).
- **OddsPapi** claims a free tier of 250 requests a month covering 300+ bookmakers, including sharp books (vendor's own claim) — [OddsPapi](https://oddspapi.io/blog/odds-api-pricing-2026-comparison/).
- **SportsGameOdds** reportedly offers a free tier with 80+ books including Pinnacle, plus a 7-day trial. This comes from competitor OddsPapi and is unverified — [OddsPapi](https://oddspapi.io/blog/odds-api-pricing-2026-comparison/).
- **Kalshi's** official API is free, with tiered rate limits (earlier note).

#### Time required (vendor claims, undated or 2026; vendors have an incentive to make it sound easy)
- **Per offer:** about an hour to learn, then "around 15 to 20 minutes" per offer.
- **Per week:** typical users spend 5–10 hours a week when starting. Vendors' tiers are 1–2 hours a week for $300–$500 a month, 3–5 hours for $500–$1,000, and 6–10 hours for $1,000–$2,000+.
- **Value:**
  - Sign-ups are worth $1,000–$3,000+ depending on the state, then reloads $300–$1,000+ a month for active users.
  - ProfitDuel says most members make $200–$500 a month from sportsbook promos.
- **Attribution.** The summary did not tie each figure to one page among [BetSuite](https://betsuite.ai/blog/matched-betting-usa-guide), [ProfitDuel, how much you can make](https://www.profitduel.com/blog/how-much-can-you-make-matched-betting), [OddsMatched](https://www.oddsmatched.com/matched-betting-guide/how-much-money-can-you-make-with-matched-betting) and [DarkHorse Odds](https://about.darkhorseodds.com/guides/what-is-matched-betting).

### Inferences
- **Free stack for the sweep:**
  - Unabated's free screen or Betwatch, to find the best plus-money bonus target and the best book hedge.
  - Kalshi's web or API order book, for the Kalshi hedge.
  - A 20-line calculator using the Q3 formulas.
  - The Q2 ledger.

  Paying only makes sense if you continue with reloads. Even then, a month's free trial would test it, but trials require signing up, which is the user's decision.
- **Bot data budget on The Odds API's $30 tier:**
  - 20,000 credits a month is about 667 a day.
  - At 3 credits a call (3 markets × 1 region), that is about 220 calls a day.
  - That supports one league scanned every 6–7 minutes around the clock, or every 1–2 minutes during a 4–6 hour game window.
  - The free tier covers on-demand pricing of a few bonus targets a day.
- **Promo discovery stays manual.** Boosts and promos are not in odds APIs, and scraping the books' apps breaches their terms (Q5). Discovery is therefore manual (apps, emails) or via affiliate promo pages.
- **Time estimate** (my inference):
  - About 20–30 minutes per book for sign-up, identity checks and deposit, then 15–20 minutes per qualifier or bonus conversion.
  - Offers paid out in installments add steps (FanDuel $50 a day for five days; DraftKings over 14 days; earlier note).
  - Across about 12 books that comes to roughly 10–20 hours over 2–4 weeks, including reconciliation, plus tax-preparation time.

### Gaps
- No vendor pricing page was read directly (OddsJam, Unabated, Outlier, The Odds API). All figures come from third-party summaries, and they conflict.
- No independent data on how much time US matched betting takes.
- Whether PromoMath's and DarkHorse's promo tools are free: unknown.

## Q5. What can a bot legally do (compute, scan, alert, track), what must a human do (placing bets, identity and geolocation), and what would a bot violate if it placed bets?

### Takeaway
Software may do everything except operate the sportsbook accounts:
- compute hedges and stake sizes
- pull odds from licensed APIs (never by scraping the books)
- scan published promos
- alert a human with a checklist
- track and reconcile results
- optionally place the Kalshi hedge through Kalshi's API after the human confirms the book bet was accepted

A human must:
- open and verify each account (21+, identity checks)
- place every sportsbook bet personally, on their own device, while physically in Arizona and passing geolocation
- keep their credentials to themselves, including from sync tools

A bot that placed sportsbook bets would breach DraftKings' and FanDuel's automation bans, their promo terms, and the third-party account-access terms that ADG rule R19-4-134 makes mandatory. Run from a server, it would also breach the in-state presence and geolocation rules. The result: voided bets, withheld winnings and account closure.

### Cited Findings
- DraftKings' Arizona terms ban "automated means (including without limitation harvesting bots, robots, parser, spiders, or screen scrapers)" (page about 2023) — [DraftKings AZ Terms](https://sportsbook.draftkings.com/legal/az-terms-of-use).
- DraftKings' promo terms let it withhold bonus rewards for "sharing account credentials with other individuals, placing wagers on behalf of other individuals, circumventing DraftKings age and location verification procedures" (undated) — [DraftKings P6 terms](https://www.draftkings.com/p65terms).
- A 2024 DraftKings sweepstakes stated "automated and/or third-party entries are prohibited" (Feb 7, 2024; these are sweepstakes rules, not sportsbook terms) — [DraftKings sweepstakes rules](https://dknetwork.draftkings.com/2024/02/07/2024-draftkings-super-bonus-bet-bonanza-sweepstakes-official-rules/).
- FanDuel's terms restrict robots, scrapers and "sniping" software, and bar prizes obtained through unauthorized scripts or automation. A tracker shows the clause updated May 5, 2026 (earlier note).
- ADG R19-4-134 requires every player-account agreement to state the patron's obligations about letting anyone else access or use the account, and about being physically present in Arizona — [Cornell LII R19-4-134](https://www.law.cornell.edu/regulations/arizona/Ariz-Admin-Code-SS-R19-4-134).
- ADG bars accepting a wager from a person placing it for someone else's benefit for compensation (2022) — [19 A.A.C. 4](https://apps.azsos.gov/public_services/Title_19/19-04.pdf).
- Geofencing and a location check before each wager are required under A.R.S. § 5-1302(G)(2) and A.A.C. R19-4-117 (earlier note) — [Cornell LII R19-4-117](https://www.law.cornell.edu/regulations/arizona/Ariz-Admin-Code-SS-R19-4-117).
- Account creation requires age 21+ and identity checks — [Cornell LII R19-4-133](https://www.law.cornell.edu/regulations/arizona/Ariz-Admin-Code-SS-R19-4-133) (the earlier note has the statutory citations).
- Kalshi offers an official trading API (earlier note). It applies GeoComply location blocks where a court requires them (Nov 2026) — [iGaming Express](https://igamingexpress.com/kalshi-tribal-lands-sports-contracts-injunction/).
- I found no Arizona statute or ADG rule that bans bots outright. The bans are contractual, matching the earlier note.

### Inferences
- **What software may do:**

| Task | Software allowed? | Why |
|---|---|---|
| Pull odds from a licensed odds API, and Kalshi market data | Yes | No sportsbook account is touched; the API vendor's terms govern |
| Scrape sportsbook sites or apps for odds, boosts or bet history | No | DraftKings bans "parser, spiders, or screen scrapers"; FanDuel bans robots and scrapers |
| Compute conversion %, hedge size, EV and tax impact; rank offers | Yes | Pure computation |
| Alert a human (push, SMS, email) with book, market, line, stake and hedge | Yes | A human still acts |
| Pre-fill or submit bet slips (browser automation, macros, autofill extensions, "sniping") | No | Breaches the "automated means" and sniping clauses, and the R19-4-134 account-access terms |
| Log into a sportsbook with your credentials (e.g. bet-sync trackers) | Avoid | Likely counts as "sharing account credentials" (DraftKings) and third-party account access (R19-4-134); use manual exports instead |
| Track results from manual entry or exported statements, and reconcile | Yes | Offline |
| Place the Kalshi hedge by API after a human confirms the book bet was accepted at the expected price | Yes | This is the API's intended use. Stop if an Arizona or tribal-land block applies; never route around one |
| Create or verify accounts, pass identity checks, accept terms, deposit | Human only | Identity and age checks under R19-4-133 |
| Pass geolocation | Human only, on their own device in Arizona | R19-4-117; DraftKings bars circumventing location checks; a cloud server or VPN cannot legitimately pass |

- **If a bot placed sportsbook bets, three things would follow:**
  1. It would breach the contract, triggering voids, withheld bonuses or winnings, and closure under the Q1 clauses.
  2. It would breach the account-access terms that ADG makes mandatory.
  3. If run from a server, it would amount to geolocation circumvention. This is the line between a terms-of-service problem and a regulatory one.
- **Recommended flow:**
  1. The bot sends an alert.
  2. A human places the book leg.
  3. The human confirms acceptance and price, for example by tapping "placed at +300 for $200".
  4. The bot places a Kalshi limit order sized by the Q3 formula, with a cap on slippage.
  5. The bot logs both legs under one offer ID.

### Gaps
- Kalshi's member agreement on automated trading, multiple accounts and location was not read this session.
- Whether Arizona's computer-crime statute could apply to automation that breaches terms of service: not researched.
- FanDuel's Arizona sportsbook terms were not read.

## Q6. Responsible-gambling and practical risks (voids, settlement mismatches, money tied up), and what Arizona requires

### Takeaway
Arizona requires bettors to be 21 or older, physically in the state for every wager (verified by geolocation), and screened at sign-up (earlier note). ADG runs statewide self-exclusion, covering tribal casinos, event wagering and fantasy sports, or all of them. It also runs an operator-first dispute process. I found no enacted ADG rule requiring operators to offer deposit limits.

The practical risks are:
- **Deadlines:** qualifying bets within 7–30 days; bonus bets that expire in 7–14 days.
- **Capital tied up:** Kalshi settles in hours, but book withdrawals take hours to days, and longer the first time.
- **One-leg failures:** a rejected or repriced bet, or a void for a palpable error.
- **Settlement mismatches:** ties, postponements, props.
- **The tax trap** (Q2).
- **Behavioral drift** from hedged promos into unhedged betting.

### Cited Findings
- ADG's guidance tells players to "make a plan and set limits on your time and money". Self-exclusion lets a person "self ban from all Tribal Gaming Facilities or Event Wagering and Fantasy Sports (EWFS) Contests, or both within the State of Arizona" (undated) — [ADG Responsible Gaming](https://gaming.az.gov/resources/ResponsibleGaming).
- Self-exclusion falls under R19-4-150. Patrons can confirm their status with ADG's Constituent Services Unit at (602) 771-4263 (undated) — [ADG](https://gaming.az.gov/node?page=1/); [ADG Complaints FAQ](https://gaming.az.gov/faq-sub-categories/complaints).
- A public comment on ADG's draft rules describes deposit limits as a feature, not a requirement. I found no enacted Arizona rule requiring them — [ADG public comments](https://gaming.az.gov/sites/default/files/Event%20Wagering%20and%20Fantasy%20Sports%20Public%20Comment%201%20-%20Online%20Written%20Comments.pdf).
- **Promo deadlines and restrictions** (Nov 2026 promo roundups; affiliates) — [next.io](https://next.io/betting-sites-us/bonus/); [Goal](https://www.goal.com/en-us/betting/sportsbook-promos-us/blt4eaf874e36455b5f); [LSR](https://www.legalsportsreport.com/sportsbook-promos/). The summary did not attribute each claim to one page.
  - Qualifying wagers are usually due within 7–30 days of registration; bet365 allows 30.
  - Bonus bets often expire in 7–14 days; BetMGM's first-bet offer allows 7. Unused bonuses lapse.
  - Restrictions include minimum and maximum odds, stake caps, exclusion of live bets, and straight-bet-only requirements.
- FanDuel and BetMGM bonus bets need one playthrough (1×) before winnings can be withdrawn (undated) — [CBS Sports promos](https://www.cbssports.com/betting/news/sportsbook-promos).
- Sportsbook house rules reserve the right to void bets, including on markets posted at wrong odds. The example found is a Wisconsin tribal book, not an Arizona one — [Potawatomi house rules](https://www.potawatomi.com/casino/sportsbook). Palpable-error voids are the main way regulated books void winning bets — [AVO (vendor)](https://www.avo.bet/articles/is-arbitrage-betting-legal).
- Settlement mismatches and Kalshi timing are covered in Q3; book withdrawal times in Q1.

### Inferences
- **Risk register for promo conversion:**

| Risk | What goes wrong | Mitigation |
|---|---|---|
| One leg rejected or repriced | You are left holding an unhedged bet | Place the book leg first and the hedge second; use limit orders |
| Palpable-error void after hedging | The hedge is left unhedged | Avoid prices far off consensus; outlier lines are the usual void targets |
| Settlement mismatch | A locked profit becomes a loss | Use main markets with the same overtime rules; never hedge soccer 3-way, props, live bets or combos; check tie rules |
| Bonus expiry | Value lapses | Put every token on a calendar; FanDuel and DraftKings pay tokens out over several days |
| Capital lock-up | Several thousand dollars tied up | Peak exposure is about $3k–$6k on large insurance offers (earlier note); keep a float on Kalshi; test withdrawals early |
| Verification holds | Withdrawals delayed | Finish identity checks at sign-up; use one funding method per book |
| Kalshi forced exit | The hedge venue disappears mid-program | Hedge same-day only; fall back to book hedges, at about 5 points lower conversion |
| Phantom tax income | An after-tax loss (Q2) | Settle the itemizing question first; size insurance offers to match |
| Behavioral drift | Unhedged "fun" bets, chasing losses | Fix the offer list and an end date in advance; use operator deposit limits where offered; ADG self-exclusion if needed |

- **Arizona compliance checklist for each session:**
  - Be 21 or older and use only your own account at each book.
  - Be physically in Arizona. Avoid reservation land if a Kalshi tribal-land block is ever ordered (speculative).
  - Pass each book's geolocation on your own device, with no VPN.
  - Never place a bet for anyone else.

### Gaps
- Not verified this session:
  - self-exclusion durations
  - the ADG problem-gambling helpline number (I recall 1-800-NEXT-STEP)
  - any Arizona rule requiring operators to offer responsible-gaming tools
- Each Arizona book's rules on ties, postponements and palpable-error voids were not read.
