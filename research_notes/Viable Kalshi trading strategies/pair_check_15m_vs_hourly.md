# Pair check: top-of-hour 15-minute crypto contracts vs the hourly "above K" ladder

Checked 2026-11-03 (data to 20:00Z that day). Series: KXBTC15M vs KXBTCD, and KXETH15M vs KXETHD.

**Question.** Does the 15-minute contract that closes on the hour settle on exactly the same number, at exactly the same time, as that hour's ladder? If so, a 15-minute YES bid above the YES ask of an hourly "above K" strike with K below the 15-minute strike is a locked trade.

**Method.**
- Data: public, unauthenticated GET requests only, one at a time. Spacing started at 1.2 s and was widened to 10 s once 429s appeared, with backoff after every 429.
- Sources: Kalshi's contract-terms PDFs (S3 copies), series, event and market objects, and 1-minute batch candlesticks.
- No orders were placed and no credentials were used.
- Request log and raw cache: `/tmp/claude-0/-home-user-Dealbot/15fe6aa2-ee2f-5d67-b9f6-68ae8122149a/scratchpad/pair_check/` (`requests.log`, `cache/`, `scripts/`).

## 0. The trade being tested

Let X be the settlement number (the "expiration_value") and S the 15-minute strike (`floor_strike`).
- The 15-minute market pays YES if X ≥ S.
- The hourly "above K" market pays YES if X > K.

**Direct trade (K < S).** Every X that pays the 15-minute YES also pays the hourly YES. Buy the hourly YES at its ask a_H, and buy the 15-minute NO at 1 − b_15, where b_15 is the 15-minute YES bid.

| Outcome | Hourly YES | 15m NO | Total |
|---|---|---|---|
| X ≥ S | 1 | 0 | $1 |
| K < X < S | 1 | 1 | $2 |
| X ≤ K | 0 | 1 | $1 |

The minimum payout is $1. The locked gross profit is b_15 − a_H, plus a $1 bonus if X lands between K and S.

**Mirror trade (K > S).** Buy the 15-minute YES at its ask a_15, and buy the hourly NO at 1 − b_H, where b_H is the hourly YES bid. The minimum payout is again $1, and the locked gross profit is b_H − a_15.

**Requirements.** The inequality must be strict. If K = S, then X = S pays the 15-minute YES and the hourly NO, and the direct trade pays $0. The whole argument also needs the same X on both legs.

## 1. Rules

### 1a. Series records (`GET /trade-api/v2/series/{ticker}`)

| | KXBTC15M / KXETH15M | KXBTCD / KXETHD |
|---|---|---|
| `frequency` | `fifteen_min` | `hourly` |
| title | "BTC 15 min" / "ETH 15 min" | "Bitcoin price Above/below" / "Ethereum price Above/below" |
| `contract_terms_url` | `https://assets.kalshi.com/contract_terms/CRYPTO.pdf` | `.../contract_terms/BTC.pdf` and `.../ETH.pdf` |
| settlement source | CF Benchmarks | CF Benchmarks (`.../indices/BRTI`, `.../indices/ETHUSD_RTI`) |
| fees | `quadratic`, multiplier 1 | `quadratic`, multiplier 1 |

The `important_info` text is the same on all four series: "The price used to determine this market is based on CF Benchmarks' corresponding Real Time Index (RTI). At the last minute before expiration, 60 RTI prices are collected. The official and final value is the average of these prices."

- `assets.kalshi.com` is blocked by this session's egress policy (403 on CONNECT), including the regulatory product certifications. I read the copies in Kalshi's public bucket `kalshi-public-docs.s3.amazonaws.com/contract_terms/` instead.
- CRYPTO.pdf (which the 15-minute series points to) and CRYPTO15M.pdf have the same text, except for the minimum tick: CRYPTO.pdf says $0.001, CRYPTO15M.pdf says $0.01.

### 1b. 15-minute contract (CRYPTO.pdf / CRYPTO15M.pdf, plus market rule text)

**Underlying:** "the spot price of one <cryptocurrency> in U.S. dollars at <time>, according to a simple average of the CF <cryptocurrency> <index> for the 60 seconds prior to <time>, after Issuance and before <date>. Revisions to the Underlying made after Expiration will not be accounted for in determining the Expiration Value."

**Comparators:** "“Above X” means strictly greater than X, while “below X” means strictly less than X. … “at least X” means X or greater."

**Missing data:** "If no data is available or incomplete on the Expiration Date at the Expiration Time, then affected strikes resolve to No."

**Contingencies:** "Before Settlement, Kalshi may, at its sole discretion, initiate the Market Outcome Review Process pursuant to Rule 6.3(d) of the Rulebook. If an Expiration Value cannot be determined on the Expiration Date, Kalshi has the right to determine payouts pursuant to Rule 6.3(b) in the Rulebook."

**Template expiration:** "Expiration Time: … 10:00 AM ET" and "The latest Expiration Date … shall be one week after <date>." This is generic template text. The market objects carry the real times (below).

**Market rule text** (`KXBTC15M-26NOV031500-00`, closing 20:00Z):
- `rules_primary`: "If the simple average of the sixty seconds of CF Benchmarks' BRTI before 3:00 PM EST on Nov 3, 2026 is at least the simple average of the sixty seconds of CF Benchmarks' BRTI before 2:45 PM EST on November 3, 2026, then the market resolves to Yes."
- `rules_secondary`: "… the price used to determine this market is based on CF Benchmarks' corresponding Real Time Index (RTI). At the last minute before expiration, 60 RTI prices are collected. The official and final value is the average of these prices, rounded to the nearest 2 decimal places."
- ETH uses the same wording with "ETHUSDRTI".
- 7 of 1,902 markets in the window state the strike as a number instead: "… ETHUSD_RTI before 8:00 PM EDT on Oct 24, 2026 is at least 2354.78 …". Three of them are top-of-hour ETH pairs, and all three matched (part 2).

**Fields** (the same on all 472 top-of-hour markets checked):

| Field | Value |
|---|---|
| `strike_type` | `greater_or_equal` |
| `floor_strike` | the opening 60-second average |
| `custom_strike` | `{"round_digits": "2"}` |
| `open_time` | close − 15 min |
| `expected_expiration_time` | close + 5 min |
| `latest_expiration_time` | close + 7 days |
| `can_close_early` | true |
| `settlement_timer_seconds` | 1 |
| `price_level_structure` | `tapered_deci_cent` |

**How the strike is set:** `floor_strike` equals the previous 15-minute window's `expiration_value`. This held in 949 of 949 BTC and 949 of 949 ETH consecutive windows.

### 1c. Hourly/daily ladder (BTC.pdf / ETH.pdf, plus market rule text)

**Underlying:** "the spot price of one Bitcoin in U.S. dollars at <time>, according to a simple average of the CF Bitcoin Real-Time Index (“BRTI”) for the minute (60 seconds) prior to <time>. Revisions to the Underlying made after Expiration will not be accounted for in determining the Expiration Value." ETH.pdf reads the same with "CF Ethereum Real-Time Index (“ERTI”)".

**Payout and missing data:** "…the index is <above/below/between> <price> on <date> at <time>. … If no data is available on the Expiration Date at the Expiration Time, then the market resolves to No."

**Expiration:** "The Expiration Date of the Contract shall be the sooner of the first minute after <time> on <date> that data is available or one week after <date>." And: "The Expiration time of the Contract shall be the first minute after <time> that data is available."

**Contingencies:** "Before Settlement, Kalshi may, at its sole discretion, initiate the Market Outcome Review Process pursuant to Rule 6.3(c) of the Rulebook."

BTC.pdf does not define "above". The market's `strike_type` = `greater` and CRYPTO.pdf's definition both mean strictly greater.

**Market rule text** (`KXBTCD-26NOV0315-T86799.99`):
- `rules_primary`: "If the simple average of the sixty seconds of CF Benchmarks' Bitcoin Real-Time Index (BRTI) before 3 PM EST is above 86799.99 at 3 PM EST on Nov 3, 2026, then the market resolves to Yes."
- `rules_secondary` ends: "At the last minute before expiration, 60 RTI prices are collected. The official and final value is the average of these prices." It does not say "rounded to the nearest 2 decimal places".
- ETH: "… CF Benchmarks' Ethereum Real-Time Index (ERTI) before 3 PM EST is above 2994.99 …".
- Only these two templates appear across all 2,085 distinct hourly market objects fetched.

**Fields** (the same on all 2,085 distinct objects):

| Field | Value |
|---|---|
| `strike_type` | `greater` |
| `cap_strike` | null |
| `custom_strike` | `{"round_digits": "2"}` |
| `expected_expiration_time` | close + 5 min |
| `latest_expiration_time` | close + 7 days |
| `can_close_early` | true |
| `settlement_timer_seconds` | 60 |
| `price_level_structure` | `linear_cent` |

**Strike grid:** strikes sit at xx99.99 (BTC) or x4.99 / x9.99 (ETH), so "above 77499.99" is in effect "≥ 77,500.00" on two-decimal values.

| Events | BTC grid | ETH grid |
|---|---|---|
| Regular hourly (188 BTC / 300 ETH strikes) | $100 | $5 |
| 5 PM ET daily | $250 (one event $100, one $500) | $40 |

**Help centre:** "For most crypto price markets, the expiration value is based on a simple average of the CF Benchmarks index over the 60 seconds before the time named in the market's rules. … a 15-minute market compares the average from the minute before it closes with the average from the minute before it opened … the market's rules and contract terms control."

**Docs, settlement feed:** the quarter-hour final-minute average accumulates over "(quarter_close_ts_ms - 60000, quarter_close_ts_ms]. The start-boundary tick is excluded and the close tick is included". Every hourly close (:00) is also a quarter-hour close.

### 1d. Is KXBTCD hourly or daily? Which closes coincide?

**Hourly, around the clock.** The series `frequency` is `hourly`.
- There is one event per hour: 236 per asset between 2026-10-24 21:00Z and 2026-11-03 20:00Z.
- The only gap: no hourly events closing 2026-10-29 06:00–09:00Z (a Thursday, 2–5 AM EDT). The 15-minute series also had no markets closing 07:15–09:00Z that morning. This looks like a scheduled exchange maintenance window (not verified).
- A regular event opens 1 hour before its close.
- The "daily" contract is the 5 PM ET event of the same series, for example `KXBTCD-26OCT2417`. It is listed about 23–26 hours ahead (one was listed 7 days ahead), on the coarser grid shown above.
- The DST repeat hour got its own event, `KXBTCD-26NOV0101EST` (06:00Z), alongside `KXBTCD-26NOV0101` (05:00Z).
- Every top-of-hour 15-minute market (ticker suffix `-00`) has a KXBTCD / KXETHD event with an identical `close_time`, except the two closes inside that gap (Oct 29 06:00Z and 07:00Z).

### 1e. Side by side

| | 15-minute (top of hour) | Hourly "above K" |
|---|---|---|
| Index | CF BRTI / ETH RTI (named "ETHUSDRTI") | CF BRTI / ETH RTI (named "ERTI") |
| Window | 60 s before the close | 60 s before the close (same timestamp) |
| Comparator | at least S (≥) | above K (>) |
| Strike | previous window's settlement, two decimals | listed xx99.99 grid |
| Rounding | "rounded to the nearest 2 decimal places" | not stated in rule text; `round_digits` 2 |
| Missing data | "no data … or incomplete … affected strikes resolve to No"; Kalshi may set payouts under Rule 6.3(b) | "no data … resolves to No"; expiration is "the first minute after <time> that data is available" |
| Review | Market Outcome Review, Rule 6.3(d) | Market Outcome Review, Rule 6.3(c) |
| Settlement timer | 1 s; settled 1.8–11.5 s after close (median 3.6 s) | 60 s; settled 94–769 s after close (median 158 s) |
| Ticks | 0.1¢ in the tails | 1¢ |

### 1f. What could break the lock

The index, averaging window, timestamp and revision policy match. The ETH index is named differently ("ETHUSDRTI" vs "ERTI"), but the settled values were identical. The tie rule is the only systematic difference.

1. **Ties.** "At least" against "above" means K must be strictly below S (or strictly above S for the mirror).
   - Never trade the strike where K = S.
   - No such case occurred in the window, but S can land on xx99.99.
2. **Rounding.** The hourly text does not say the value is rounded.
   - This cannot break the lock while K ≠ S. A sub-cent difference between a rounded and an unrounded average cannot reverse a strict inequality: the grids differ by at least $0.01.
   - Both markets also carry `round_digits` 2 and published identical two-decimal values (part 2).
3. **Missing or incomplete index data. This is the real tail risk.**
   - For "incomplete" data, the 15-minute terms resolve the affected strikes to No.
   - The hourly terms resolve to No only if "no data is available". They also move the expiration to "the first minute after <time> that data is available", which could be a later minute's average.
   - In a partial outage the two legs could be resolved on different facts:
     - Mirror trade: the 15-minute leg goes No (YES pays 0), while the hourly settles on a later value above K (NO pays 0). The pair pays $0.
     - Direct trade: the hourly goes No or settles on a later value at or below K (YES pays 0), while the 15-minute settles normally at or above S (NO pays 0). The pair pays $0.
   - Both terms also leave payouts to Kalshi's discretion (Rule 6.3(b)/(c)/(d); 7.1 in other filings).
4. **Disputes.** A result can be `disputed` and then `amended` during the settlement timer (1 s vs 60 s), separately per market.
5. **Not a rules risk, but an operational one.**
   - The hourly leg pays out minutes after the 15-minute leg.
   - Both markets are `can_close_early`.
   - The position accountability level is $25,000 per strike per member in both.

## 2. Empirical check: do the settlement numbers match?

**Sample.** Every top-of-hour KXBTC15M and KXETH15M market closing 2026-10-24 21:00Z to 2026-11-03 20:00Z: 238 per asset, of which 236 have an hourly event. Each was paired with the KXBTCD / KXETHD event of the same `close_time`.

The hourly side was checked on:
- for regular hours, the nearest strike on each side of S, fetched by ticker;
- for the 5 PM events, the full ladder.

That is 2,085 hourly market objects across 472 events.

**Results.**
- **472 of 472 pairs matched** (236 BTC, 236 ETH): `expiration_value` was the identical string, for example "77534.38" in both `KXBTC15M-26NOV031500-00` and `KXBTCD-26NOV0315-*`.
- **Mismatches: none.**
- Every hourly market object in an event carried the same value.
- `close_time` was identical in every pair.
- Every `result` agreed with its rule:
  - hourly: yes ⇔ value > `floor_strike`, 2,085 of 2,085;
  - 15-minute: yes ⇔ value ≥ `floor_strike`, 472 of 472.
- **Values were not published at the same moment.** The 15-minute leg settles about 2–12 s after close (median 3.6 s). The hourly leg settles about 1.5–13 min after close.
- One 15-minute market, `KXBTC15M-26OCT290300-00` (and its ETH twin), took 2.1 h. It sits in that Oct 29 gap and had no hourly counterpart.

## 3. Opportunity scan (1-minute candles, final 15 minutes before each top-of-hour close)

### 3a. Data and test

**Window: 7 days.** The 168 top-of-hour pairs per asset closing 2026-10-27 17:00Z to 2026-11-03 20:00Z.
- 336 pairs had candles. 335 were scanned: the 5 PM event `KXBTCD-26OCT2817B` returned no candles.
- I stopped at 7 days instead of 10 because the shared address was drawing 429s on about 40% of requests (see request log).

**Legs per pair:** the 15-minute market, plus the nearest hourly strike strictly below S (direct trade) and strictly above S (mirror trade).
- Within a ladder, a lower strike's YES is worth at least as much as a higher one's.
- So the nearest strike below S is the cheapest hourly YES that still dominates the 15-minute YES, and the nearest strike above S has the highest bid among dominated strikes.
- Farther strikes can only win if the ladder is internally inverted.

**Endpoint:** `GET /trade-api/v2/markets/candlesticks?market_tickers=…&start_ts=…&end_ts=…&period_interval=1`.
- Batch form: up to 100 tickers. The server rejects a request when tickers × window minutes exceeds 10,000 (its 400 said "requested candlesticks across all markets: 34800, max candlesticks: 10000").
- The single-market path `GET /trade-api/v2/series/{series_ticker}/markets/{ticker}/candlesticks` returns the same fields.
- Fields used: `end_period_ts` (inclusive end of the minute), `yes_bid.{open,low,high,close}_dollars`, `yes_ask.{…}_dollars`.

**Minutes and test.**
- Minutes scanned: the 15 one-minute candles ending at close−14 min … close. The last one is the averaging minute itself.
- Test: each leg's minute-close quote, i.e. the standing quote at the same minute boundary.
- Direct gap = 15-minute YES bid − hourly YES ask (K < S).
- Mirror gap = hourly YES bid − 15-minute YES ask (K > S).
- Size: 10,003 pair-minutes (BTC direct 2,505, BTC mirror 2,505, ETH direct 2,485, ETH mirror 2,508). Some thin ETH strikes are missing minutes.

### 3b. How the market prices the dominance

- The gap is normally well negative, meaning no lock.
  - Medians: −18¢ (direct) and −14¢ (mirror).
  - In uncertain minutes (15-minute mid between 10¢ and 90¢): medians −19¢ to −28¢, 90th percentile −4¢ to −9¢.
- When S sits within $10 (BTC) or $0.50 (ETH) of a strike, the two contracts are almost the same bet. There the median gap is −2¢ to −4¢, about one bid-ask spread.
- So the books do price the dominance. Crossings are the exception.

### 3c. Crossings found (minute-close quotes)

**Count:** 68 crossed minute-snapshots, 0.68% of pair-minutes, in 45 episodes across 28 of 335 pairs (8.4%). There were also 57 exact touches (gap 0), which lock in no profit before fees.

**By trade:**

| | BTC | ETH |
|---|---|---|
| Direct | 7 | 9 |
| Mirror | 21 | 8 |

**Size** (largest gap per episode):
- 27 episodes at 1¢ and 10 at 2¢.
- 6 under 1¢. These come from the 15-minute market's 0.1¢ tail ticks against cent-only hourly quotes.
- One at 3¢ and one at 6¢.

**Duration** (consecutive minute-snapshots):

| Minutes | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Episodes | 34 | 5 | 1 | 4 | 1 |

**Where:** 43 of 45 episodes had S within $20 (BTC) or $0.40 (ETH) of the strike. These are essentially the same contract quoted twice by different books.

**When:** 3 to 14 minutes before the close. None in the final 2 minutes.

**Fees.** Taker fee per leg = ceil(0.07 × C × P × (1−P)) dollars, with P the price paid on that leg.

Breakeven gap:
- **1 contract:** more than 2¢ if prices are under about 17¢ or over about 83¢, otherwise more than 4¢. Each leg rounds up to 1¢ or 2¢.
- **100 contracts, per contract:**

| Price | 10/90¢ | 20/80¢ | 30/70¢ | 50¢ |
|---|---|---|---|---|
| Breakeven | 1.26¢ | 2.24¢ | 2.94¢ | 3.50¢ |

Survivors:
- **At 1 contract:** 1 episode (#7, +2¢).
- **At 100 contracts:** 2 episodes (#7, +$2.55; #26, +$0.01).
- **Upper bound:** summing every fee-positive episode at 100 contracts gives **≈ $2.56 for the week**. That assumes 100 contracts were available on both legs at the displayed price, which candles cannot show.

**The one crossing that looks real (#7).** `KXBTC15M-26OCT272200-00` against `KXBTCD-26OCT2722-T80799.99` (K $19.35 below S), Oct 28, 01:54–01:55Z.
- BTC was moving up fast. The 15-minute YES went 30¢ → 47¢ → 68¢ over three minutes, while the hourly strike went 27/28¢ → 40/41¢ → 81/83¢.
- At the 01:55 close the 15-minute bid was 47¢ against an hourly ask of 41¢.
- It settled at 80833.05, above both S and K, so the pair would have paid exactly $1.
- This looks like the thinner hourly book lagging during a fast move. One-minute data cannot show whether both quotes stood at the same instant, or for how many contracts.

### 3d. Caveats

- **Timing.** A candle's close is the last quote before the minute boundary, and the two markets' closes can be up to about a second apart. A "1-minute" episode may have existed for milliseconds or not at all simultaneously.
- **Size.** Candles carry no size.
- **High/low comparison is meaningless here.** Comparing the 15-minute bid's high with the hourly ask's low inside the same minute shows a "crossing" in 2,646 of 10,003 pair-minutes, by up to 94¢. That only reflects price moving within the minute. It is not evidence of an opportunity.
- **Execution.** There is no atomic two-market order, so the legs must be lifted one after the other and the second can move first.
- **Not tested:** fills, order-book depth, and maker (passive) execution of either leg. A maker leg may cut the fee but brings back legging risk.

### 3e. Episode list

| # | Trade | Pair (15m / hourly leg) | Minute(s) UTC, mins to close | S | K (distance to S) | 15m bid/ask | Hourly bid/ask | Gap | Taker fees, 1 lot (net) | Taker fees, 100 lots (net) | Survives fees? | Lasted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26OCT271800-00` / `KXETHD-26OCT2718-T2349.99` | 2026-10-27 21:48 (12 left at best) | 2349.81 | 2349.99 (0.18) | 0.690/0.700 | 0.71/0.73 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.47+$1.45 (-1.92) | no | 1 min |
| 2 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26OCT271800-00` / `KXETHD-26OCT2718-T2349.99` | 2026-10-27 21:53 (7 left at best) | 2349.81 | 2349.99 (0.18) | 0.660/0.670 | 0.70/0.71 | 3.0¢ | 2¢+2¢ (-1.0¢) | $1.55+$1.47 (-0.02) | no | 1 min |
| 3 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT272100-00` / `KXETHD-26OCT2721-T2344.99` | 2026-10-28 00:46, 00:47 (14 left at best) | 2345.04 | 2344.99 (0.05) | 0.250/0.260 | 0.20/0.24 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.28+$1.32 (-1.60) | no | 2 min |
| 4 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT272100-00` / `KXETHD-26OCT2721-T2344.99` | 2026-10-28 00:49 (11 left at best) | 2345.04 | 2344.99 (0.05) | 0.210/0.220 | 0.17/0.19 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.08+$1.17 (-0.25) | no | 1 min |
| 5 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT272100-00` / `KXETHD-26OCT2721-T2344.99` | 2026-10-28 00:53 (7 left at best) | 2345.04 | 2344.99 (0.05) | 0.290/0.300 | 0.26/0.28 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.42+$1.45 (-1.87) | no | 1 min |
| 6 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT272100-00` / `KXETHD-26OCT2721-T2344.99` | 2026-10-28 00:56 (4 left at best) | 2345.04 | 2344.99 (0.05) | 0.089/0.090 | 0.07/0.08 | 0.9¢ | 1¢+1¢ (-1.1¢) | $0.52+$0.57 (-0.19) | no | 1 min |
| 7 | BTC direct (buy hourly YES + 15m NO) | `KXBTC15M-26OCT272200-00` / `KXBTCD-26OCT2722-T80799.99` | 2026-10-28 01:54, 01:55 (5 left at best) | 80819.34 | 80799.99 (19.35) | 0.470/0.480 | 0.40/0.41 | 6.0¢ | 2¢+2¢ (+2.0¢) | $1.70+$1.75 (+2.55) | yes, both sizes | 2 min |
| 8 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26OCT280200-00` / `KXETHD-26OCT2802-T2349.99` | 2026-10-28 05:49, 05:50 (11 left at best) | 2349.95 | 2349.99 (0.04) | 0.690/0.700 | 0.71/0.72 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.47+$1.45 (-1.92) | no | 2 min |
| 9 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26OCT280200-00` / `KXETHD-26OCT2802-T2349.99` | 2026-10-28 05:54 (6 left at best) | 2349.95 | 2349.99 (0.04) | 0.390/0.400 | 0.42/0.43 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.68+$1.71 (-1.39) | no | 1 min |
| 10 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT281200-00` / `KXBTCD-26OCT2812-T80499.99` | 2026-10-28 15:48 (12 left at best) | 80497.83 | 80499.99 (2.16) | 0.330/0.340 | 0.36/0.37 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.58+$1.62 (-1.20) | no | 1 min |
| 11 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT281500-00` / `KXBTCD-26OCT2815-T81199.99` | 2026-10-28 18:56 (4 left at best) | 81153.52 | 81199.99 (46.47) | 0.008/0.009 | 0.01/0.02 | 0.1¢ | 1¢+1¢ (-1.9¢) | $0.07+$0.07 (-0.04) | no | 1 min |
| 12 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT290800-00` / `KXBTCD-26OCT2908-T80099.99` | 2026-10-29 11:52 (8 left at best) | 80095.29 | 80099.99 (4.70) | 0.850/0.860 | 0.87/0.88 | 1.0¢ | 1¢+1¢ (-1.0¢) | $0.85+$0.80 (-0.65) | no | 1 min |
| 13 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26OCT291000-00` / `KXETHD-26OCT2910-T2314.99` | 2026-10-29 13:50 (10 left at best) | 2314.68 | 2314.99 (0.31) | 0.660/0.670 | 0.68/0.71 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.55+$1.53 (-2.08) | no | 1 min |
| 14 | BTC direct (buy hourly YES + 15m NO) | `KXBTC15M-26OCT291200-00` / `KXBTCD-26OCT2912-T81599.99` | 2026-10-29 15:48 (12 left at best) | 81603.54 | 81599.99 (3.55) | 0.730/0.740 | 0.71/0.72 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.42+$1.38 (-1.80) | no | 1 min |
| 15 | BTC direct (buy hourly YES + 15m NO) | `KXBTC15M-26OCT291200-00` / `KXBTCD-26OCT2912-T81599.99` | 2026-10-29 15:51 (9 left at best) | 81603.54 | 81599.99 (3.55) | 0.560/0.570 | 0.54/0.55 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.74+$1.73 (-2.47) | no | 1 min |
| 16 | BTC direct (buy hourly YES + 15m NO) | `KXBTC15M-26OCT291200-00` / `KXBTCD-26OCT2912-T81599.99` | 2026-10-29 15:55 (5 left at best) | 81603.54 | 81599.99 (3.55) | 0.510/0.520 | 0.49/0.50 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.75+$1.75 (-2.50) | no | 1 min |
| 17 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT291500-00` / `KXBTCD-26OCT2915-T80599.99` | 2026-10-29 18:56 (4 left at best) | 80591.58 | 80599.99 (8.41) | 0.988/0.989 | 0.99/1.00 | 0.1¢ | 1¢+1¢ (-1.9¢) | $0.08+$0.07 (-0.05) | no | 1 min |
| 18 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT291700-00` / `KXBTCD-26OCT2917-T78999.99` | 2026-10-29 20:46 (14 left at best) | 78928.65 | 78999.99 (71.34) | 0.360/0.370 | 0.39/0.41 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.64+$1.67 (-1.31) | no | 1 min |
| 19 | BTC direct (buy hourly YES + 15m NO) | `KXBTC15M-26OCT300600-00` / `KXBTCD-26OCT3006-T77599.99` | 2026-10-30 09:48 (12 left at best) | 77611.28 | 77599.99 (11.29) | 0.240/0.250 | 0.22/0.23 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.24+$1.28 (-1.52) | no | 1 min |
| 20 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT301300-00` / `KXETHD-26OCT3013-T2229.99` | 2026-10-30 16:50 (10 left at best) | 2230.36 | 2229.99 (0.37) | 0.120/0.130 | 0.10/0.11 | 1.0¢ | 1¢+1¢ (-1.0¢) | $0.69+$0.74 (-0.43) | no | 1 min |
| 21 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT301400-00` / `KXETHD-26OCT3014-T2239.99` | 2026-10-30 17:47 (13 left at best) | 2240.00 | 2239.99 (0.01) | 0.530/0.540 | 0.50/0.52 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.75+$1.75 (-2.50) | no | 1 min |
| 22 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT301400-00` / `KXETHD-26OCT3014-T2239.99` | 2026-10-30 17:55 (5 left at best) | 2240.00 | 2239.99 (0.01) | 0.230/0.240 | 0.21/0.22 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.21+$1.24 (-1.45) | no | 1 min |
| 23 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26OCT301600-00` / `KXETHD-26OCT3016-T2229.99` | 2026-10-30 19:47 (13 left at best) | 2229.94 | 2229.99 (0.05) | 0.720/0.730 | 0.74/0.75 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.38+$1.35 (-1.73) | no | 1 min |
| 24 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26OCT301600-00` / `KXETHD-26OCT3016-T2229.99` | 2026-10-30 19:49 (11 left at best) | 2229.94 | 2229.99 (0.05) | 0.820/0.830 | 0.84/0.85 | 1.0¢ | 1¢+1¢ (-1.0¢) | $0.99+$0.95 (-0.94) | no | 1 min |
| 25 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT301600-00` / `KXBTCD-26OCT3016-T76499.99` | 2026-10-30 19:52 (8 left at best) | 76485.59 | 76499.99 (14.40) | 0.943/0.944 | 0.95/0.96 | 0.6¢ | 1¢+1¢ (-1.4¢) | $0.38+$0.34 (-0.12) | no | 1 min |
| 26 | BTC direct (buy hourly YES + 15m NO) | `KXBTC15M-26OCT302200-00` / `KXBTCD-26OCT3022-T77299.99` | 2026-10-31 01:52, 01:53, 01:54 (7 left at best) | 77301.42 | 77299.99 (1.43) | 0.180/0.190 | 0.15/0.16 | 2.0¢ | 1¢+2¢ (-1.0¢) | $0.95+$1.04 (+0.01) | 100 lots only | 3 min |
| 27 | BTC direct (buy hourly YES + 15m NO) | `KXBTC15M-26OCT302200-00` / `KXBTCD-26OCT3022-T77299.99` | 2026-10-31 01:57 (3 left at best) | 77301.42 | 77299.99 (1.43) | 0.200/0.210 | 0.18/0.19 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.08+$1.12 (-1.20) | no | 1 min |
| 28 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT310600-00` / `KXBTCD-26OCT3106-T77299.99` | 2026-10-31 09:47, 09:48 (13 left at best) | 77299.94 | 77299.99 (0.05) | 0.390/0.400 | 0.41/0.42 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.68+$1.70 (-2.38) | no | 2 min |
| 29 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT310600-00` / `KXBTCD-26OCT3106-T77299.99` | 2026-10-31 09:50 (10 left at best) | 77299.94 | 77299.99 (0.05) | 0.520/0.530 | 0.54/0.55 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.75+$1.74 (-2.49) | no | 1 min |
| 30 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT310600-00` / `KXBTCD-26OCT3106-T77299.99` | 2026-10-31 09:53, 09:54, 09:55, 09:56, 09:57 (6 left at best) | 77299.94 | 77299.99 (0.05) | 0.390/0.400 | 0.42/0.43 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.68+$1.71 (-1.39) | no | 5 min |
| 31 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT310900-00` / `KXETHD-26OCT3109-T2249.99` | 2026-10-31 12:46, 12:47 (13 left at best) | 2250.09 | 2249.99 (0.10) | 0.310/0.320 | 0.28/0.29 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.45+$1.50 (-0.95) | no | 2 min |
| 32 | ETH direct (buy hourly YES + 15m NO) | `KXETH15M-26OCT310900-00` / `KXETHD-26OCT3109-T2249.99` | 2026-10-31 12:49 (11 left at best) | 2250.09 | 2249.99 (0.10) | 0.250/0.260 | 0.23/0.24 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.28+$1.32 (-1.60) | no | 1 min |
| 33 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT311000-00` / `KXBTCD-26OCT3110-T77399.99` | 2026-10-31 13:49, 13:50, 13:51, 13:52 (11 left at best) | 77398.48 | 77399.99 (1.51) | 0.830/0.840 | 0.85/0.86 | 1.0¢ | 1¢+1¢ (-1.0¢) | $0.95+$0.90 (-0.85) | no | 4 min |
| 34 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT311400-00` / `KXBTCD-26OCT3114-T77499.99` | 2026-10-31 17:47, 17:48, 17:49, 17:50 (12 left at best) | 77482.79 | 77499.99 (17.20) | 0.760/0.770 | 0.79/0.80 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.24+$1.17 (-0.41) | no | 4 min |
| 35 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT311800-00` / `KXBTCD-26OCT3118-T77399.99` | 2026-10-31 21:48 (12 left at best) | 77393.41 | 77399.99 (6.58) | 0.620/0.630 | 0.64/0.65 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.64+$1.62 (-2.26) | no | 1 min |
| 36 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT311800-00` / `KXBTCD-26OCT3118-T77399.99` | 2026-10-31 21:50 (10 left at best) | 77393.41 | 77399.99 (6.58) | 0.800/0.810 | 0.82/0.83 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.08+$1.04 (-1.12) | no | 1 min |
| 37 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT311800-00` / `KXBTCD-26OCT3118-T77399.99` | 2026-10-31 21:52, 21:53, 21:54, 21:55 (8 left at best) | 77393.41 | 77399.99 (6.58) | 0.904/0.905 | 0.91/0.92 | 0.5¢ | 1¢+1¢ (-1.5¢) | $0.61+$0.58 (-0.69) | no | 4 min |
| 38 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26OCT312000-00` / `KXBTCD-26OCT3120-T77399.99` | 2026-10-31 23:56 (4 left at best) | 77385.45 | 77399.99 (14.54) | 0.910/0.911 | 0.92/0.93 | 0.9¢ | 1¢+1¢ (-1.1¢) | $0.57+$0.52 (-0.19) | no | 1 min |
| 39 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26NOV010000-00` / `KXBTCD-26NOV0100-T77699.99` | 2026-11-01 03:56 (4 left at best) | 77697.82 | 77699.99 (2.17) | 0.170/0.180 | 0.19/0.20 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.04+$1.08 (-1.12) | no | 1 min |
| 40 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26NOV011800-00` / `KXBTCD-26NOV0118-T77699.99` | 2026-11-01 22:54 (6 left at best) | 77699.01 | 77699.99 (0.98) | 0.800/0.810 | 0.82/0.84 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.08+$1.04 (-1.12) | no | 1 min |
| 41 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26NOV021400-00` / `KXBTCD-26NOV0214-T76799.99` | 2026-11-02 18:48, 18:49, 18:50, 18:51 (11 left at best) | 76799.20 | 76799.99 (0.79) | 0.690/0.700 | 0.72/0.73 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.47+$1.42 (-0.89) | no | 4 min |
| 42 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26NOV021400-00` / `KXBTCD-26NOV0214-T76799.99` | 2026-11-02 18:53 (7 left at best) | 76799.20 | 76799.99 (0.79) | 0.650/0.660 | 0.68/0.69 | 2.0¢ | 2¢+2¢ (-2.0¢) | $1.58+$1.53 (-1.11) | no | 1 min |
| 43 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26NOV021800-00` / `KXBTCD-26NOV0218-T76699.99` | 2026-11-02 22:48 (12 left at best) | 76684.65 | 76699.99 (15.34) | 0.780/0.790 | 0.80/0.81 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.17+$1.12 (-1.29) | no | 1 min |
| 44 | BTC mirror (buy 15m YES + hourly NO) | `KXBTC15M-26NOV021800-00` / `KXBTCD-26NOV0218-T76699.99` | 2026-11-02 22:50 (10 left at best) | 76684.65 | 76699.99 (15.34) | 0.870/0.880 | 0.89/0.90 | 1.0¢ | 1¢+1¢ (-1.0¢) | $0.74+$0.69 (-0.43) | no | 1 min |
| 45 | ETH mirror (buy 15m YES + hourly NO) | `KXETH15M-26NOV031400-00` / `KXETHD-26NOV0314-T2294.99` | 2026-11-03 18:49 (11 left at best) | 2294.71 | 2294.99 (0.28) | 0.200/0.210 | 0.22/0.23 | 1.0¢ | 2¢+2¢ (-3.0¢) | $1.17+$1.21 (-1.38) | no | 1 min |

## Sources

- Kalshi API series records: [KXBTC15M](https://api.elections.kalshi.com/trade-api/v2/series/KXBTC15M), [KXBTCD](https://api.elections.kalshi.com/trade-api/v2/series/KXBTCD), [KXETH15M](https://api.elections.kalshi.com/trade-api/v2/series/KXETH15M), [KXETHD](https://api.elections.kalshi.com/trade-api/v2/series/KXETHD)
- Contract terms (S3 copies): [CRYPTO.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/CRYPTO.pdf), [CRYPTO15M.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/CRYPTO15M.pdf), [BTC.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/BTC.pdf), [ETH.pdf](https://kalshi-public-docs.s3.amazonaws.com/contract_terms/ETH.pdf)
- Market objects: [settled KXBTC15M](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTC15M&status=settled&limit=5), [settled KXBTCD](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXBTCD&status=settled&limit=5), [event KXBTCD-26NOV0315](https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=KXBTCD-26NOV0315&limit=1000), [event KXETHD-26NOV0315](https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=KXETHD-26NOV0315&limit=1000), [events KXBTCD](https://api.elections.kalshi.com/trade-api/v2/events?series_ticker=KXBTCD)
- Candles: [batch candlesticks endpoint](https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks) (`GET /trade-api/v2/markets/candlesticks`, up to 100 tickers, and tickers × window minutes ≤ 10,000)
- Kalshi docs: [market lifecycle](https://docs.kalshi.com/getting_started/market_lifecycle) (determined / disputed / amended, `settlement_timer_seconds`), [CF Benchmarks value feed](https://docs.kalshi.com/websockets/cfbenchmarks-value) (averaging semantics)
- Kalshi help centre: [Crypto Markets](https://help.kalshi.com/en/articles/13823838-crypto-markets)
- Request log for this check:
  - 101 calls to `api.elections.kalshi.com`: 57 OK, 43 throttled (HTTP 429, Kalshi `too_many_requests`, no Retry-After header), 1 rejected (400, oversized candle batch).
  - Also 4 S3 PDFs, 1 help-centre page, and 5 attempts refused by the proxy for `assets.kalshi.com`.
  - Window: 20:22–21:15Z.
  - Spacing: 1.2 s at first, raised to 2.5, 8 and then 10 s; backoff of 15–120 s after each 429.

## 4. Verdict

**A near-lock with named risks, not a true lock, and too rare and too small to matter.** On settlement mechanics the pair behaves as a lock. Both legs use the same CF Benchmarks 60-second average (BRTI, or the ETH RTI) ending at the same top-of-hour timestamp. Over 10 days all 472 top-of-hour pairs (236 BTC, 236 ETH) settled on the identical expiration value, and every result agreed with its strike. Neither the "at least S" vs "above K" wording nor the rounding wording can break it, as long as K ≠ S. It falls short of a contractual lock for three reasons. First, the two contract terms handle missing or incomplete index data differently: the 15-minute terms resolve affected strikes No when data is "incomplete", while the hourly terms move expiration to "the first minute after <time> that data is available". Second, Kalshi can review, amend after a dispute, or determine payouts market by market. Third, the two legs cannot be bought in one atomic order, and legging risk is real in the fast final minutes. As a trade it rarely appears and almost never pays. Over 7 days (335 pairs, 10,003 pair-minutes), the minute-close quotes crossed in 68 minutes, forming 45 episodes in 28 pairs. Nearly all were 1–2¢ for a single minute, where S sat within cents of an hourly strike. Only one episode survived taker fees: a 6¢ crossing for about two minutes during a fast BTC move on Oct 28, worth +2¢ on 1 contract or +$2.55 on 100. The week's fee-positive total was about $2.56 at 100 contracts, even assuming that size was available. Treat this as a settlement-consistency fact and a possible latency signal, not as a strategy.
