# Copy-trade study pipeline

Standard-library Python 3. Read-only: every network call is a Helius read method (`getTransactionsForAddress`,
`getTransaction`, `getSlot`, `getBlockTime`). The API key is read from `HELIUS_API_KEY` and never printed.
Set `CT_DATA` to a scratch directory for raw caches and the credit ledger.

| Step | Script | Does |
|---|---|---|
| 1 | `s1_screen.py seed_all.json` | Selection-week signature counts per seed wallet (10 credits each) |
| 2 | `s2_fetch_swaps.py wallets.json START END outdir [max_pages]` | Full transactions in a window, kept only as the wallet's own swaps (`swaps.parse`) |
| 3 | `s3_select.py` | Realized selection-week P&L, top 20 with at least 10 trades |
| 4a | `s4_events.py test_swaps out.json [cap]` | Test-week buys and the whale's sells within 24 h |
| 4b | `s4_paths.py events.json` | Pool swaps after each buy and each sell, and at +24 h (cached) |
| 5 | `s5_sim.py events.json outdir` | Copy simulation at each delay and size, writing `per_copy_results.csv` and `summary.json` |
| 6 | `s6_validate.py` | Checks the constant-product price model against real fills |
| 7 | `s7_tables.py` | Report tables |

Windows used: selection 1792540800–1793145600 (Oct 21–28, 2026), test 1793145600–1793750400 (Oct 28–Nov 4).
Environment knobs: `SLOT_SECONDS` (0.2126), `PRIO_SOL` (0.0005), `THREADS`, `CREDIT_CAP`.
