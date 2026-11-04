# Copy-trading whale wallets: working notes

Paper-only study on public Solana data, run 2026-11-04. No wallet or key was created or used, and nothing was signed or sent. Every Helius call was a read (`getTransactionsForAddress`, `getTransaction`, `getSlot`, `getBlockTime`).

## Files

| File | What it holds |
|---|---|
| `wallets_kolscan_all_474_screened.csv` | Every KOLScan wallet in the public scrape (472), plus two addresses found by web search (Cented, Jijo; Cupsey was already in the scrape), with selection-week transaction counts |
| `wallets_seed_150.csv` | The 150-wallet seed list with selection-week buys, sells and realized P&L, ranked; `selected_top20=True` marks the 20 copied in the test week |
| `per_copy_results.csv` | One row per copy × delay × size (2,000 copies × 6 delays × 2 sizes); column notes below |
| `summary.json` | Aggregates per delay and size, plus counts of copies that could not be priced |
| `tables.md` | Generated tables used in the report |
| `code/` | The pipeline (standard-library Python only); see `code/README.md` |

## Where the wallets came from

The design asked for KOL and smart-money wallets from public leaderboards and articles. In this container, WebFetch could not resolve any of the leaderboard or article hosts (kolscan.io, madeonsol.com, dev.to, medium.com and others). Two sources still worked:

1. **KOLScan leaderboard scrape on GitHub.** `github.com/ryds052-dot/kol-quest`, file `output/kolscan-leaderboard.json`, commit `93c87f6` dated 2026-10-29. It lists 472 unique KOL wallets with KOLScan names and X handles, across the 1-, 7- and 30-day boards.
2. **Web-search snippets.** These gave Cupsey `2fg5QD1e…` (kolexplorer.com, uwuu.ai; already in the scrape), Cented `CyaE1Vxv…` (kolexplorer.com) and Jijo `4BdKaxN8…` (solana-trading.com).

**Choosing the 150-wallet seed.** I did not rank wallets by KOLScan's own profit figures. The scrape was committed on Oct 29, inside the test week, so those figures could contain test-week results. Instead I counted each wallet's successful transactions in the selection week (signatures only, 10 credits per wallet) and kept the 150 most active. All 474 addresses had some activity, and the 150th had 831 transactions. Choosing by activity tilts the seed toward high-frequency traders. That is also the group whose trades a copy bot would follow most often.

**Choosing the top 20.** Realized selection-week P&L in SOL uses the average-cost method on each wallet's own swaps. A sell of tokens bought before Oct 21 has no known cost and is left out. Each wallet needed at least 10 swaps. 22 of the 150 seed wallets reached the 15,000-transaction fetch cap, so their P&L covers only part of the week; none of the top 20 hit the cap. The top 20 earned **+2,475 SOL** together in the selection week and **+1,083 SOL** in the test week, so as a group they stayed profitable.

## Method details and changes to the design

- **Slot time.** I measured 0.2126 s per slot over the selection week (slot 459,421,613 to 462,265,395 against block times). The "next slot" delay is therefore about 0.2 s. I added 0.4 s as 2 slots; 1 s, 5 s and 30 s are 5, 24 and 141 slots.
- **Which buys were copied.** The top 20 made 9,403 buys in the test week. I kept buys made before 2026-11-03 00:00 UTC so that each has a full 24 hours of follow-up; the data ends at about 07:00 UTC on Nov 4, so the 1,528 later buys were dropped. I also dropped 3,087 buys whose price cannot be read from a single SOL- or USDC-quoted pool:
  - About 2,800 were routed through pools quoted in another token. pump.fun now launches coins quoted in xStocks, PEPE and similar tokens, so the whale paid SOL, swapped it into the quote token, and then bought the coin.
  - About 286 were the wallet creating the coin itself and making the first buy.

  That left 4,788 eligible buys, from which I drew a seeded random sample of 2,000 (seed 7) to stay inside the time and credit budget. Of the sample, 1,416 bought on the pump.fun bonding curve, 457 on PumpSwap and 127 on Raydium, Meteora or Orca. One was quoted in USDC.
- **Prices.** For every swap on the pool, I take the pool's own balance changes, which give the fill price and the quote reserve after the trade. For the pump.fun bonding curve, the reserve is the curve's lamports plus the 30 SOL virtual reserve. A copier landing in slot T trades against the state just before the first real swap at or after T. With the constant-product rule, the copier's own $100 or $1,000 then moves the price. I checked this model on 218,000 consecutive pairs of swaps by predicting each fill from the previous pool state:
  - pump.fun: median error 0.32%, 90th percentile 1.5%
  - PumpSwap: median error 0.70%, 90th percentile 2.4%
  - Raydium CPMM: median error 0.08%
  - concentrated-liquidity pools (Meteora DLMM, Orca Whirlpool, Raydium CLMM): median error 0.2–0.5%, but these pools are only 10 of the 2,000 copies

  Results are in `model_validation.json` in the scratch data and reproducible with `code/s6_validate.py`.
- **Fees.** Venue fees are charged on each side at the low end of each published schedule, which favours the copier:
  - pump.fun bonding curve 1.25%
  - PumpSwap 0.30%, the bottom of its market-cap tiers; small coins pay up to 1.25%
  - Raydium, Meteora and Orca AMMs 0.25%
  - LaunchLab and Meteora DBC 1%

  I added a priority fee plus tip of 0.0005 SOL per copier transaction, and a rerun at 0.005 SOL changed mean returns by about 1 point at $100. In comparison, the whales tipped about 0.013 SOL per buy and often paid a 1% trading-terminal fee. Those costs sit inside their own fills, so the whale benchmark is net of them.
- **Exits.** When the whale sells a fraction f of its holding of the token, the copier sells the same fraction of its own position, after the same delay, against the pool the whale sold on. Whatever is left 24 hours after the whale's buy is valued at what it would fetch if sold then, including the copier's own price impact and the fee. That 24-hour value comes from the first swap of the token in the two hours after the mark (790 copies) or, failing that, the last swap before it (1,208 copies). Two copies had no price at all.
- **"Went to zero".** The 24-hour price was at or below 10% of the copier's entry price.
- **SOL/USD.** I took the median of swaps in the Orca SOL–USDC pool: $106.40 on Oct 21, $101.23 on Oct 28 and $92.76 on Nov 3, and interpolated between them. A $100 copy is about 1 SOL. Returns are measured in SOL, and the dollar P&L is the return times the copy size.
- **Zero-delay benchmark.** As an impossible upper bound, the copier also trades at the exact pool state the whale saw.

## Facts worth keeping

- The whales' median buy was 0.70 SOL (about $70) and the mean 1.74 SOL. A $1,000 copy is about 14 times the median whale's size.
- The median pump.fun curve held about 51 SOL of virtual reserve when a copy entered, so a 1 SOL buy moves the price about 2% and a 10 SOL buy about 20%.
- The whales flip fast. The median time to the first sell is 52 seconds:
  - 7% of buys are first sold within 5 s
  - 37% within 30 s
  - 51% within 60 s
  - 76% within 5 minutes
  - only 4% are not sold within 24 hours
- On the copied trades, the whale's own median return was −21%, its mean −10% and its win rate 25%. Weighted by the whale's own size, the return was **+6%**. Its profit comes from a few large winners.
- With zero delay, $100 copies weighted by the whale's size would have returned +16%; one slot late, that falls to −18.5%.
- A 30 s copier who skips buys the whale has already sold does worse, not better: a mean of −29% on 1,237 copies against −22% on all of them.
- The pump.fun bonding curve has a price floor, the launch price. Coins still on the curve can lose 30–60% but rarely 90%: only 3% went to zero. Coins that had graduated to PumpSwap went to zero 33% of the time.

## Credits

The ledger recorded **186,552 credits**:

- 10,830 for the activity screen (signatures)
- about 65,000 for selection-week history (642,154 transactions; some pages were fetched twice by overlapping workers)
- about 5,500 for test-week history
- about 97,700 for price paths
- 12 single `getTransaction` calls for debugging

During the selection-week fetch, a concurrent write once reset the ledger file. I restored it from the last reading I had taken (24,175, rounded up to 25,200), so the true total may differ by a few thousand. Either way it is far below the 800,000 cap.

## per_copy_results.csv columns

| Column | Meaning |
|---|---|
| `id`, `buy_sig`, `buy_slot`, `buy_time` | The whale's buy |
| `whale`, `mint`, `venue`, `via_jupiter`, `quote` | Who bought, which coin, where, and in what quote currency |
| `whale_buy_quote` | SOL the whale spent, all-in |
| `whale_fill_price` | The whale's all-in price |
| `whale_pool_price` | The pool-side price of the whale's swap |
| `delay`, `size_usd` | The scenario |
| `status` | `ok`, `no_entry_price` or `no_24h_price` |
| `entry_price` | The copier's average fill |
| `entry_vs_whale_pool_price` | The copier's premium over the whale's fill |
| `entry_lag_slots` | Slots between the target slot and the first real swap |
| `held_to_24h_frac` | Share of the copier's position still held at 24 h |
| `missing_exit_windows` | Whale sells whose price window was missing (0 for almost all) |
| `p24_vs_entry`, `went_to_zero` | 24-hour price relative to the copier's entry, and whether it lost 90% or more |
| `return`, `pnl_usd` | The copy's result after all costs |
| `return_if_exit_at_whale_sell_price` | The same copy with the delay applied to the entry only |
| `whale_return` | The whale's own return on that buy, with the same proportional exits and 24 h mark |
