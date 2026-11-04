### Main results

| Delay | Size | Copies | Win rate | Median return | Mean return | Total P&L | Went to zero | Whale median / mean on same trades |
|---|---|---|---|---|---|---|---|---|
| 0 (whale's own price, impossible) | $100 | 1996 | 35% | -11.0% | +0.8% | $1,634 | 10% | -20.8% / -10.2% |
| 0 (whale's own price, impossible) | $1,000 | 1996 | 15% | -34.8% | -23.5% | $-469,081 | 11% | -20.8% / -10.2% |
| next slot (~0.2 s) | $100 | 1996 | 16% | -31.2% | -18.8% | $-37,535 | 10% | -20.8% / -10.3% |
| next slot (~0.2 s) | $1,000 | 1996 | 10% | -47.7% | -36.3% | $-725,269 | 12% | -20.8% / -10.3% |
| 0.4 s | $100 | 1995 | 16% | -31.7% | -19.4% | $-38,697 | 10% | -20.8% / -10.3% |
| 0.4 s | $1,000 | 1995 | 10% | -47.8% | -36.7% | $-732,414 | 12% | -20.8% / -10.3% |
| 1 s | $100 | 1994 | 15% | -32.2% | -20.5% | $-40,788 | 11% | -20.8% / -10.3% |
| 1 s | $1,000 | 1994 | 10% | -48.5% | -37.5% | $-747,335 | 12% | -20.8% / -10.3% |
| 5 s | $100 | 1993 | 16% | -32.7% | -22.9% | $-45,694 | 11% | -20.8% / -10.4% |
| 5 s | $1,000 | 1993 | 9% | -49.4% | -39.5% | $-786,319 | 12% | -20.8% / -10.4% |
| 30 s | $100 | 1971 | 15% | -22.7% | -22.0% | $-43,383 | 11% | -21.0% / -10.8% |
| 30 s | $1,000 | 1971 | 8% | -42.7% | -40.4% | $-795,363 | 13% | -21.0% / -10.8% |

### Where the loss comes from ($100 copies)

| Delay | Median entry price vs whale's fill | Mean return | Mean return if the exit were at the whale's own sell price | Cost of being late on the exit |
|---|---|---|---|---|
| 0 (whale's own price, impossible) | +1.4% | +0.8% | +0.8% | +0.0% |
| next slot (~0.2 s) | +4.4% | -18.8% | -8.2% | -10.6% |
| 0.4 s | +5.0% | -19.4% | -9.0% | -10.4% |
| 1 s | +6.0% | -20.5% | -9.6% | -10.9% |
| 5 s | +6.2% | -22.9% | -9.7% | -13.2% |
| 30 s | +2.6% | -22.0% | -1.5% | -20.5% |

### By venue ($100, 1 s delay)

| Venue of whale buy | Copies | Win rate | Median | Mean | Went to zero | Whale mean |
|---|---|---|---|---|---|---|
| pumpfun | 1416 | 13% | -33.1% | -21.7% | 3% | -9.8% |
| pumpswap | 457 | 19% | -32.0% | -18.4% | 33% | -13.5% |
| raydium_launchlab | 38 | 18% | -8.8% | -13.0% | 8% | -2.2% |
| raydium_cpmm | 35 | 37% | -14.5% | -8.7% | 20% | -1.2% |
| meteora_damm_v2 | 25 | 20% | -15.7% | -20.5% | 24% | -20.2% |
| meteora_dbc | 8 | 0% | -49.1% | -50.9% | 12% | -49.0% |
| meteora_dlmm | 6 | 67% | +8.6% | -2.2% | 0% | -8.5% |
| raydium_v4 | 5 | 40% | -4.3% | +12.8% | 0% | +23.0% |
| orca_whirlpool | 3 | 100% | +0.3% | +0.4% | 0% | +108.3% |
| raydium_clmm | 1 | 0% | -2.0% | -2.0% | 0% | -3.6% |

### Each whale: selection week vs test week, and what copying it returned ($100, 1 s)

| Wallet (KOLScan name) | Selection-week realized P&L (SOL) | Test-week realized P&L (SOL) | Test-week buys | Copies sampled | Whale's mean return on sampled buys | Copier mean return | Copier win rate |
|---|---|---|---|---|---|---|---|
| zeropnl `4xY9T1…` | +713.6 | +484.1 | 316 | 32 | -5.0% | -13.0% | 28% |
| milito `EeXvxk…` | +169.1 | -13.8 | 634 | 138 | -19.2% | -26.1% | 16% |
| Mitch `4Be9Cv…` | +156.5 | -2.0 | 18 | 6 | +79.3% | +65.3% | 67% |
| Pikalosi `9cdZg6…` | +155.0 | +67.2 | 635 | 212 | -11.1% | -18.9% | 20% |
| Orange `2X4H5Y…` | +154.3 | -50.6 | 112 | 21 | -18.6% | -27.2% | 14% |
| Frost `4nwfXw…` | +126.3 | -6.6 | 133 | 31 | -6.2% | -24.6% | 13% |
| cap `CAPn1y…` | +121.2 | +213.2 | 1161 | 215 | -29.3% | -24.9% | 14% |
| Casino `8rvAsD…` | +102.8 | +208.5 | 596 | 94 | -15.7% | -28.1% | 15% |
| Giann `GNrmKZ…` | +88.1 | -14.8 | 139 | 26 | +11.9% | -3.1% | 27% |
| el charto `CCUcje…` | +86.5 | -19.1 | 73 | 20 | -28.4% | -31.9% | 5% |
| Flames `6aXFYX…` | +86.1 | -17.8 | 1697 | 395 | -13.5% | -24.5% | 11% |
| evening `E7gozE…` | +84.2 | -9.4 | 69 | 17 | -15.6% | -24.6% | 24% |
| Sheep `78N177…` | +78.1 | +19.6 | 236 | 48 | -20.7% | -33.9% | 10% |
| Latuche `GJA1HE…` | +60.7 | +60.7 | 192 | 45 | +11.5% | -1.4% | 31% |
| k4ye `5fHJsz…` | +60.1 | +26.1 | 927 | 200 | +4.4% | -10.1% | 19% |
| King Solomon `DEdEW3…` | +52.3 | -0.9 | 157 | 48 | +2.6% | -33.5% | 10% |
| LUKEY ✣ `DjM7Tu…` | +52.0 | +70.6 | 36 | 2 | -14.7% | -35.0% | 50% |
| dov 7 `8nqtxp…` | +47.5 | +17.9 | 135 | 11 | -35.1% | -31.5% | 0% |
| Gasp `xyzfhx…` | +42.2 | +56.7 | 1903 | 382 | -4.1% | -16.2% | 13% |
| blixze ♱ `5vg7he…` | +38.8 | -6.1 | 216 | 51 | -5.5% | -21.3% | 16% |
| **All 20** | **+2475.3** | **+1083.4** | | | | | |

```
{
 "events": 2000,
 "median_whale_buy_sol": 0.7022200135,
 "mean_whale_buy_sol": 1.7430204518610002,
 "median_seconds_to_first_sell": 52,
 "share_first_sell_within_30s": 0.37,
 "share_first_sell_within_60s": 0.5085,
 "share_first_sell_within_5min": 0.7635,
 "share_no_sell_24h": 0.0405,
 "sampled_whale_total_pnl_sol": 206.56170764824,
 "sampled_whale_total_cost_sol": 3463.705103,
 "sel_total_top20_sol": 2475.2984,
 "test_total_top20_sol": 1083.4254559197682
}
```