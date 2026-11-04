# Copying profitable Solana whales loses money at every speed a bot can reach

**In plain words**

- **Copying lost money at every delay.** A $100 copy of these traders' buys lost about **19–23% on average**, whether the bot was 0.2 seconds late or 30 seconds late. Only about 1 copy in 6 made money.
- **Bigger copies lost more.** $1,000 copies lost **36–40% on average**, because a buy that size moves the price of a small coin by about 20%.
- **About 1 coin in 10 went to zero** (lost 90% or more within a day). For coins that had already left pump.fun's launch stage, it was 1 in 3.
- **The traders themselves still made money**, about +1,083 SOL as a group in the test week. They did it with a few big winners and by getting in first. Their median trade lost money too.
- **Speed does not fix it.** Even a bot that got the trader's exact price would only break even (+0.8% on average), and that is impossible without jumping ahead of them, which we rule out. Most of the loss comes on the way out: the trader sells first, and the copier sells into the price drop the trader caused.
- **Confidence: high** that a cloud copy bot does not make money on these wallets. The result held for 19 of the 20 traders and for every delay and size tested. It covers one week of data, so treat the exact percentages as rough.

## The test kept the choice of traders separate from the test of copying them

I picked the 20 traders using only one week of data (Oct 21–28, 2026). I then tested copying them on the following week (Oct 28–Nov 4), so knowing how a trader later did could not influence who was chosen. Everything came from public Solana transactions read through Helius. No wallet was created and no transaction was signed or sent. The full method, file list and credit count are in [notes](../research_notes/Copy%20trading%20whale%20wallets/notes.md).

1. **Trader list.** The starting pool was 474 publicly listed "KOL" wallets: the KOLScan leaderboard as scraped into the public GitHub project [ryds052-dot/kol-quest](https://github.com/ryds052-dot/kol-quest) (472 wallets), plus three addresses from web search ([KOL Explorer](https://kolexplorer.com/kol/cented), [solana-trading.com](https://solana-trading.com/blog/memecoin-trader-wallets-top10-2026)). From these I kept the 150 most active in the selection week. For those 150 I pulled all 642,154 selection-week transactions and computed each wallet's realized profit in SOL. The 20 most profitable with at least 10 trades formed the copy list; together they made **+2,475 SOL** that week.
2. **Copies.** The 20 made 9,403 buys in the test week. I kept those made by Nov 3 00:00 UTC, so that each has a full day of follow-up. I also dropped buys that cannot be priced from a single SOL or USDC pool. Most of these went through coins quoted in another token, and about 286 were the trader launching its own coin. That left 4,788 eligible buys, of which I sampled **2,000** at random. 71% bought on the pump.fun launch curve, 23% on PumpSwap, and the rest on Raydium, Meteora and Orca.
3. **Price a copier would pay.** For each buy, I read every real swap in the same pool after the trader's buy. A copier landing at a given delay trades at the pool price set by the first real swap at or after that moment. On top of that come the copier's own price impact for $100 or $1,000, under the pool's constant-product pricing rule, and the venue fee. Venue fees use the low end of each published schedule: 1.25% on the pump.fun curve, 0.30% on PumpSwap and 0.25% on the AMMs. Each copier transaction also pays a 0.0005 SOL priority fee and tip. The price model predicted 218,000 real swap fills with a median error of 0.3% on pump.fun and 0.7% on PumpSwap.
4. **Exits.** When the trader sold part of its holding, the copier sold the same share after the same delay. Anything still held 24 hours after the trader's buy was valued at what it would fetch if sold then.
5. **Delays.** Solana produced a slot (block) every 0.21 seconds in this period, so "next slot" means about 0.2 s. I also tested 0.4 s, 1 s, 5 s and 30 s, plus an impossible zero-delay case as a ceiling.

The design called for scraping KOL leaderboards directly. Those sites could not be reached from the study's environment, so the trader list comes from the GitHub scrape instead. The scrape was committed on Oct 29, inside the test week, so I ranked by selection-week activity and profit only, never by KOLScan's own profit numbers.

## Results: every achievable delay loses money

| Delay | Size | Copies | Win rate | Median return | Mean return | Total P&L | Went to zero | Whale median / mean on the same trades |
|---|---|---|---|---|---|---|---|---|
| 0 (the whale's own price; impossible) | $100 | 1,996 | 35% | −11.0% | **+0.8%** | +$1,634 | 10% | −20.8% / −10.2% |
| 0 (impossible) | $1,000 | 1,996 | 15% | −34.8% | −23.5% | −$469,081 | 11% | −20.8% / −10.2% |
| next slot (~0.2 s) | $100 | 1,996 | 16% | −31.2% | **−18.8%** | −$37,535 | 10% | −20.8% / −10.3% |
| next slot | $1,000 | 1,996 | 10% | −47.7% | −36.3% | −$725,269 | 12% | −20.8% / −10.3% |
| 0.4 s | $100 | 1,995 | 16% | −31.7% | −19.4% | −$38,697 | 10% | −20.8% / −10.3% |
| 0.4 s | $1,000 | 1,995 | 10% | −47.8% | −36.7% | −$732,414 | 12% | −20.8% / −10.3% |
| 1 s | $100 | 1,994 | 15% | −32.2% | **−20.5%** | −$40,788 | 11% | −20.8% / −10.3% |
| 1 s | $1,000 | 1,994 | 10% | −48.5% | −37.5% | −$747,335 | 12% | −20.8% / −10.3% |
| 5 s | $100 | 1,993 | 16% | −32.7% | **−22.9%** | −$45,694 | 11% | −20.8% / −10.4% |
| 5 s | $1,000 | 1,993 | 9% | −49.4% | −39.5% | −$786,319 | 12% | −20.8% / −10.4% |
| 30 s | $100 | 1,971 | 15% | −22.7% | **−22.0%** | −$43,383 | 11% | −21.0% / −10.8% |
| 30 s | $1,000 | 1,971 | 8% | −42.7% | −40.4% | −$795,363 | 13% | −21.0% / −10.8% |

Total P&L is the sum over all 2,000 sampled copies, about one copy for every two eligible buys. Copying every eligible buy would roughly double it. A few copies at each delay could not be priced; `summary.json` gives the counts.

**The decay is front-loaded.** The first fifth of a second costs about 20 points: the mean falls from +0.8% at zero delay to −18.8% at the next slot. After that, waiting longer costs only about 1 point per step, out to 5 seconds. Faster than the next slot is not possible for a bot that reacts to the trader's transaction rather than predicting it. Getting the trader's own price would mean trading in the same block ahead of them, which is front-running and outside this study. Even that ceiling only breaks even at $100.

**Size makes it worse.** The traders' median buy was 0.70 SOL, about $70. A $1,000 copy is about ten SOL going into a launch curve that typically holds about 51 SOL, so the copier pays about 20% more than the quoted price on the way in and loses about as much on the way out.

**Coins went to zero less often on the launch curve, but those copies still lost.** On the pump.fun curve a coin cannot fall below its launch price, so only 3% of those coins lost 90%. Most of them still fell 30–60%. Coins that had graduated to PumpSwap went to zero a third of the time.

## The copier's main loss comes on the way out

These traders flip fast. The median time from buy to first sell is **52 seconds**: 37% of buys are sold within 30 seconds and 76% within 5 minutes. When the trader sells, its sale knocks the price down. A copier one slot behind sells into that drop.

| Delay ($100) | Median entry premium over the whale's fill | Mean return | Mean return if the exit were at the whale's own sell price | Cost of the late exit |
|---|---|---|---|---|
| 0 (impossible) | +1.4% | +0.8% | +0.8% | 0 |
| next slot | +4.4% | −18.8% | −8.2% | −10.6 points |
| 0.4 s | +5.0% | −19.4% | −9.0% | −10.4 points |
| 1 s | +6.0% | −20.5% | −9.6% | −10.9 points |
| 5 s | +6.2% | −22.9% | −9.7% | −13.2 points |
| 30 s | +2.6% | −22.0% | −1.5% | −20.5 points |

The entry hurts too. Other bots pile in within a second, so a copier one slot late already pays about 4% more than the trader did. On top of that come fees and price impact of about 5–7% for a round trip at $100 on the launch curve. At 30 seconds the early pile-in has faded, so the entry is cheaper, but by then the trader has often already sold. Skipping trades the trader has already exited does not help: on the remaining 1,237 copies, the 30-second mean worsens to −29%.

## The traders profit through size and timing that copies cannot reproduce

As a group, the 20 stayed profitable in the test week (+1,083 SOL realized across all their trades). Their typical trade still lost money, after the tips (about 0.013 SOL per buy) and 1% trading-terminal fees they pay: their median return on the copied buys was −21%. Weighted by how much they put into each trade, their return was **+6%**. They win by betting big on the few trades they get early. A fixed-size copier gets the losers in full and reaches the winners late. Weighting the copier's $100 copies by the trader's own size would have returned +16% at zero delay but −18.5% one slot late.

| Wallet | Selection week (SOL) | Test week (SOL) | Copies | Whale mean | Copier mean ($100, 1 s) |
|---|---|---|---|---|---|
| zeropnl `4xY9T1…` | +713.6 | +484.1 | 32 | −5.0% | −13.0% |
| milito `EeXvxk…` | +169.1 | −13.8 | 138 | −19.2% | −26.1% |
| Mitch `4Be9Cv…` | +156.5 | −2.0 | 6 | +79.3% | +65.3% |
| Pikalosi `9cdZg6…` | +155.0 | +67.2 | 212 | −11.1% | −18.9% |
| Orange `2X4H5Y…` | +154.3 | −50.6 | 21 | −18.6% | −27.2% |
| Frost `4nwfXw…` | +126.3 | −6.6 | 31 | −6.2% | −24.6% |
| cap `CAPn1y…` | +121.2 | +213.2 | 215 | −29.3% | −24.9% |
| Casino `8rvAsD…` | +102.8 | +208.5 | 94 | −15.7% | −28.1% |
| Giann `GNrmKZ…` | +88.1 | −14.8 | 26 | +11.9% | −3.1% |
| el charto `CCUcje…` | +86.5 | −19.1 | 20 | −28.4% | −31.9% |
| Flames `6aXFYX…` | +86.1 | −17.8 | 395 | −13.5% | −24.5% |
| evening `E7gozE…` | +84.2 | −9.4 | 17 | −15.6% | −24.6% |
| Sheep `78N177…` | +78.1 | +19.6 | 48 | −20.7% | −33.9% |
| Latuche `GJA1HE…` | +60.7 | +60.7 | 45 | +11.5% | −1.4% |
| k4ye `5fHJsz…` | +60.1 | +26.1 | 200 | +4.4% | −10.1% |
| King Solomon `DEdEW3…` | +52.3 | −0.9 | 48 | +2.6% | −33.5% |
| LUKEY `DjM7Tu…` | +52.0 | +70.6 | 2 | −14.7% | −35.0% |
| dov 7 `8nqtxp…` | +47.5 | +17.9 | 11 | −35.1% | −31.5% |
| Gasp `xyzfhx…` | +42.2 | +56.7 | 382 | −4.1% | −16.2% |
| blixze `5vg7he…` | +38.8 | −6.1 | 51 | −5.5% | −21.3% |

Half the traders (10 of 20) lost money in the test week after topping the selection week, so last week's profit is a weak guide to next week's. Copying was profitable for only one trader, Mitch, and that rests on just 6 trades. Full addresses and how each wallet was found are in [wallets_seed_150.csv](../research_notes/Copy%20trading%20whale%20wallets/wallets_seed_150.csv).

## Being fast enough would take more than speed

A profitable copier would need two things this design cannot give. It would have to buy at or before the trader's own price, in the same slot. It would also have to exit before the trader's sale lands. Both mean predicting or jumping ahead of the trader's transactions, which is front-running and ruled out here. The best a cloud bot can do is land in the next slot, about 0.2 seconds later, and the next slot already costs about 19% per trade. Co-located servers, private transaction relays and bigger tips only shave the gap between 0.2 s and 1 s, which is worth about 2 points.

## Limits

- **One week of test data and 20 traders.** Memecoin markets swing from week to week. The sign of the result is robust: every delay and size lost money, and so did 19 of 20 traders. The exact percentages are not.
- **2,000 of 4,788 eligible buys were sampled**, at random with a fixed seed. 3,087 buys routed through coins quoted in other tokens, or launched by the trader itself, were left out, and those may behave differently.
- **Price model.** A copier landing in a slot is assumed to trade against the state just before the first real swap in that slot. Within a slot, ordering could go either way. The constant-product model fits the pump.fun curve and the AMMs closely. It only approximates the few concentrated-liquidity pools in the sample (10 copies).
- **Fees favour the copier.** Venue fees use the low end of each schedule, and the priority fee is far below the traders' own tips. Raising the priority fee and tip to 0.005 SOL lowers the $100 means by about 1 point.
- **The 24-hour mark** uses the first trade after the mark or, if none, the last trade before it. A coin with no trades for hours is marked at a stale price.
- **The trader list** comes from a third-party scrape of KOLScan, not from KOLScan itself. Its profit figures were never used.
- **Credits:** about 187,000 Helius credits were used, of the 800,000 allowed. The count may be off by a few thousand; see the notes.

## Sources

- KOLScan leaderboard scrape: [github.com/ryds052-dot/kol-quest](https://github.com/ryds052-dot/kol-quest), `output/kolscan-leaderboard.json`, commit 93c87f6.
- Wallet addresses for Cented, Cupsey and Jijo: [KOL Explorer: Cented](https://kolexplorer.com/kol/cented), [KOL Explorer: Cupsey](https://kolexplorer.com/kol/cupsey), [uwuu.ai](https://uwuu.ai/blog/cupsey-solana-trader), [solana-trading.com](https://solana-trading.com/blog/memecoin-trader-wallets-top10-2026).
- Helius `getTransactionsForAddress` method and pricing: [Helius docs](https://www.helius.dev/docs/rpc/gettransactionsforaddress).
- pump.fun and PumpSwap fee schedules: [Coinpaprika launchpad fees guide](https://coinpaprika.com/education/launchpad-fees/), [KuCoin on PumpSwap's 0.25% fee](https://www.kucoin.com/it/news/articles/pump-fun-debuts-pumpswap-dex-with-0-25-fee-structure-and-zero-sol-migration-fee-to-reclaim-solana-s-memecoin-market).
- On-chain data: Solana mainnet through Helius RPC, Oct 21–Nov 4, 2026. SOL/USD from the Orca SOL–USDC pool `Czfq3xZZ…`.
- Code, wallet lists and per-copy results: [research_notes/Copy trading whale wallets/](../research_notes/Copy%20trading%20whale%20wallets/).
