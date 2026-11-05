# The Dealbot paper-desk team

One week of paper trading on live Kalshi 15-minute crypto contracts (ETH and BTC), to show whether the
desk is worth taking live. The first desk was judged by Jev; since 2026-11-05 desk v2 trades a
market-anchored forecast instead (see "Desk v2"). Paper money only. House rules, from the owner: never
place a live order; ask the owner before adding any API key (trading-only, withdrawals disabled);
keep secrets out of code and logs; show the owner every change as a diff.

The measured week runs from 2026-11-03T08:25:00Z to 2026-11-10T08:25:00Z; the final report and
verdict follow at 08:55Z. It started at 06:20:24Z, but from 06:42 to 08:23Z every restart of the
desk left the previous desk running (the chunk script killed a wrapper shell, not the desk), so two
to four desks traded side by side and wrote every decision twice into one log. That stretch stays
in the run branch's record and is left out of the results (fixed in 1f1a3f4; reports/health.py now
raises an ALERT if a decision is ever logged twice).

On 2026-11-05 the owner switched the desk to v2 as soon as it passed its tests. The first desk's week
closed at the switch with its result kept for the record; v2's measured week runs seven days from its
first block (`reports/runs.py` finds it in the log), and the stop and final-report tasks are re-timed to
it.

## Who does what

| Role | Model | Cadence | Does | Never |
|---|---|---|---|---|
| Coordinator | Opus 5.5, session `session_01C4NeDS3CKGZfUNrC7ArPuL` | on escalation; supervisor check every 6 h; morning report 06:31 Arizona (13:31Z) | the only writer of code (`claude/desk-skeleton`) and the only voice to the owner; fixes what teammates find; replaces a teammate that stops | live trading; keys without the owner |
| Runner | Sonnet 5.5, session `session_01JrtRuFoJFvVT79cmMzPuAC` | 110-minute chunks back to back | `ops/paper_chunk.sh` (`ops/runner_prompt.md`): the chunk script pushes logs to `paper-run` every 30 min; the runner republishes the pipeline dashboard after each chunk | edits, commits or pushes by hand |
| Watchdog | Haiku 5.5, session `session_01JrtRuCP3RKtfhHmsiC3UYw` | hourly at :17 | `ops/watchdog.sh` (`ops/watchdog_prompt.md`): health line, then refreshes the money dashboard | edits code, deletes anything |
| Lab runner (REST) | Haiku 5.5, session `session_01JrtRuC2MxTqb4BE8GVXSXP` | 110-minute chunks back to back | `LAB_FEEDS=rest ops/lab_chunk.sh` (`ops/lab_runner_prompt.md`): records Kalshi's public market data (settlement values for A; D was dropped 2026-11-05) and pushes each finished hour to `shadow-run` | orders of any kind; edits, commits or pushes by hand |
| Lab runner (live feed) | Haiku 5.5, session `session_01JrtRuF1RVSJHGR8478xKpm` (since 2026-11-04 03:20Z) | 110-minute chunks back to back | `LAB_FEEDS=ws ops/lab_chunk.sh` (`ops/lab_feed_runner_prompt.md`): records the authenticated WebSocket feed for E and F (B and C were dropped 2026-11-05; the recorder is unchanged) into the same branch | orders of any kind; reading or printing the key; edits, commits or pushes by hand |
| Analyst | Sonnet 5.5, session `session_01JrtRuFFYYmFkU2WSWi25VR` | daily 12:41Z | `ops/analyst_prompt.md`: reconciles settlements, studies P&L, the forecast's calibration and the filter funnel; one note a day on `paper-notes` | edits the desk's code or the run |
| Fresh eyes | a review subagent the coordinator starts | before any change to `risk/`, `policy/`, `broker/` or fills | reads the diff cold, without the coordinator's reasoning | |

Each teammate does one job on a schedule and hands everything else up. The deterministic parts
(health rules, money rows, reconciliation) are code with tests (`reports/health.py`,
`dashboard/money.py`, `reports/reconcile.py`), so the models only run them and act on the result.

## Scheduled tasks

| Task | Id | When | Into |
|---|---|---|---|
| Dealbot watchdog (hourly) | `trig_01KrRSXV2TttnkfeWBk9dPej` | :17 every hour | the watchdog |
| Dealbot analyst (daily) | `trig_012LJKTfeFq9HcsRRwTToX1c` | 12:41Z | the analyst |
| Dealbot morning report | `trig_01BCqah4duYaj4kiukYhoD6J` | 06:31 Arizona (13:31Z) | the coordinator |
| Dealbot supervisor check | `trig_01WRrVejPmbJuufYScvmqRsF` | 01:06, 07:06, 19:06Z | the coordinator |
| Paper run: stop after one week | `trig_01GZynojVUiE1qCcTVikWBML` | 2026-11-10T08:25Z | the coordinator |
| Paper run: final weekly report and verdict | `trig_0185uWBZUeyYdDopGG326NDd` | 2026-11-10T08:55Z | the coordinator |

## Where things live

- `claude/desk-skeleton`: the code (PR #1). A push that touches the desk's code restarts the running
  desk within about 3 minutes, after the pre-flight passes again; a push that touches only docs,
  `ops/`, `tests/`, `reports/`, `dashboard/`, `lab/` or `research_notes/` does not (the run picks it up
  at its next restart).
- `paper-run`: the run's logs, state, trials, reports and summaries; only the chunk script commits here.
- `shadow-run`: the shadow lab's recorded market data, `lab/data/<date>/<HH>.jsonl.gz` from the REST
  recorder and `<HH>.ws.jsonl.gz` from the live feed; only the lab chunk script commits here.
- `paper-notes`: the analyst's daily notes, `notes/<date>.md`.
- Money dashboard (the owner's phone): https://claude.ai/artifact/PAbprFb46SYGp9T2RZa66o, page
  `dashboard/money_page/index.html`, dataset `paper` = the rows from `python -m dashboard.money`.
  The watchdog uploads fresh rows hourly; the coordinator does it again before the morning report.
- Pipeline dashboard (engine room): https://claude.ai/artifact/8HskYG3shsTzFoV3WmFtQS, republished
  by the runner after every chunk.

## Escalation

Any teammate escalates with `send_message` to the coordinator's session,
`session_01C4NeDS3CKGZfUNrC7ArPuL` (it created theirs), starting the message with
`Escalation from the Dealbot <role>`; it arrives at once, and the coordinator verifies before acting.
Never `fire_trigger`: a manual fire starts a fresh session with no repository (on 2026-11-03 one of
those pushed a needless notification to the owner's phone), so the old poke-only task
`trig_011Fb7LfMudmP3ipB3cb1Uq5` is disabled.

- Runner: after two failed cycles in a row (pre-flight exit 4 twice, or any other failure twice).
- Lab runners: after two failed cycles in a row (exit 5: the REST recorder crashed; exit 2: no key or
  virtualenv for the live feed; exit 6: the live feed kept failing).
- Watchdog: when the health line is ALERT (stale pushes, a desk fault, no forecasts (v2) or Jev calls for two hours,
  Jev failing, a stuck position, the daily loss limit), once per problem, again only after 3 hours.
- Analyst: a position settled the wrong way (reconcile exit 3), a BUG finding, or an ALERT.

The coordinator then:
1. A defect in the desk's code: fix it on `claude/desk-skeleton` with the whole suite passing
   (`TYPESAFE_API_KEY` unset) and the fresh-eyes review for risk, policy, broker or fill changes;
   push; check the next health line.
2. A stopped runner: read its last messages; send it a message to resume once the cause is fixed. If
   it does not answer, or its context is above 600,000 tokens between chunks, create a replacement
   (`create_session`, source https://github.com/benchmateai/Dealbot at `claude/desk-skeleton`,
   model Sonnet 5.5, tags `dealbot-paper-run`, `dealbot-runner`, prompt `ops/runner_prompt.md`),
   tell the old one to stop after its current chunk, and update the runner id here and in the
   scheduled tasks' prompts.
3. Tell the owner in two or three lines only what was wrong and what changed, or what is theirs to
   decide.

## Shadow strategies

On 2026-11-03 the owner chose to keep the live test unchanged and judge the analyst's proposal beside
it. `reports/shadow.py` replays the desk's own log under two rules registered at 15:15Z that day:
`capped` (skip entries more than 10 points from the market's mid) and `capped_exit` (capped, and sell
3 minutes before the close). Their results before 15:15Z were known when they were chosen; only trades
opened after it test them. The rules are not retuned during the week.

On 2026-11-04 the owner asked for a stop-loss. Replayed on the week's first 130 bets, fixed stops at
75, 50, 33 and 25% of the entry price all lost more than the desk (these contracts often halve and
recover), so the owner chose to test the one rule that helped on paper instead: `late_stop`, selling a
bet still losing 60 seconds before the close. It counts only bets opened from 09:15Z on 2026-11-04,
and `reports/shadow.py` prints the desk's result on the same bets beside it.

These comparisons are frozen at desk v2's start: v2 trades its own forecast with the late stop built
in, so the rules judge the first desk's bets only. `capped` and `capped_exit` were dropped (both behind
the desk on the test window); the late stop moved into the desk.

## Shadow lab

The owner then asked for six next-round strategies to run beside the live test, read-only and on paper
(`lab/`; the research behind them is `reports/Viable Kalshi trading strategies.md`). Each counts only
data recorded after its registration time, and none is retuned during the week.

| | Strategy | Registered (Nov 3) | Data |
|---|---|---|---|
| A | repaired model control (taker): settlement-aware model, pooled with the market | 21:00Z | the desk's price tape, REST |
| B | late-window harvest (taker): buy the side the settlement average has all but decided | 22:00Z | live feed |
| C | ETH 15-minute market making (maker) | 22:00Z | live feed |
| D | consistency scanner, with the 15-minute against hourly-ladder pair | 21:00Z | REST |
| E | liquidity-incentive capture (maker) | 22:00Z | live feed |
| F | maker long-shot fade (maker) | 22:00Z | live feed |

`python3 -m lab.report --tape <paper-run logs/data> --lab <shadow-run lab/data>` prints one line each.
On 2026-11-05 B (-79.52 USD on 22 entries), C (-959 USD even as an upper bound) and D (one gap in about
30 hours that lasted past a snapshot) were dropped; the report names them and scores A, E and F. A is the
lab's replay of exactly what desk v2 trades (`policy/anchored.py`), with every position held to
settlement and BTC and ETH at once, so it stays the reference for the desk.
Maker results (C, E, F) are upper bounds: fills are pessimistic, but paper cannot know queue position.
B, C, E and F say they are waiting until the live feed has run. The live feed needs the market-data
key the owner adds to the cloud environment (`KALSHI_PROD_API_KEY_ID`, `KALSHI_PROD_PRIVATE_KEY`; it
signs WebSocket subscriptions and nothing else). A session sees only the environment variables set
before it was created, so the live-feed lab runner was created once the key was in (2026-11-04
03:20Z; `create_session`, source https://github.com/benchmateai/Dealbot at `claude/desk-skeleton`,
model Haiku 5.5, tags `dealbot-paper-run`, `dealbot-lab`, prompt `ops/lab_feed_runner_prompt.md`); a
replacement is created the same way. The REST runner carries on unchanged. Each recorder writes its own files and each runner
merges the other's commits before it pushes. The paper desk and the REST recorder run with the key
removed from their environment.

## Desk v2 (from 2026-11-05)

Why: over the first desk's 243 bets, the side it bought won 21.8% of the time against an average price
of 23.3 cents, while its own forecast said 30.8%. Kalshi's price was the better forecast at every time
left before the close (log loss 0.312 against 0.359 for the desk's 50/50 blend and 0.402 for Jev, on
7,571 settled forecasts), and Jev's answers sat far too close to 50/50 (a 1% shot read as 16%). So the
desk bought fairly priced underdogs, sold every winner early and rode every loser to zero; fees were
half the loss. The analysis is in the owner's report "Why the desk is losing".

What v2 trades (`policy/anchored.py`, `KALSHI_FORECAST=anchored`, the Kalshi default):
- the forecast q is Kalshi's own mid moved toward a model of the settlement rule (the 60-second index
  average) by a weight fitted on settled contracts; at weight 0 q is the market and nothing trades;
- entries 60 to 600 seconds before the close when q clears the price by 1.5 x (the taker fee + half the
  spread), then hold to settlement, except the owner's late stop: sell a bet still losing 60 seconds
  before the close;
- no Jev call (the judge service still starts; its answers no longer decide anything). The funnel's
  ForecastStage logs a `forecast` record beside each decision, and each desk start logs a `forecaster`
  record after replaying the run's log, so a restarted desk forecasts as if it had run throughout;
- the risk gate pins the forecaster's version (`anchored-1`), and its fee check now measures a NO bet on
  the NO price (on the YES price it overstated cheap NO edges up to 30-fold and never blocked them);
- one position at a time, as before; lab strategy A holds BTC and ETH at once, so it trades more.

`KALSHI_FORECAST=blend` runs the first desk again. The pre-flight runs v2 with a confident forecast in
place of the confident judge.

## During the paper week

BUG fixes (wrong behaviour) go in as soon as they are found. TUNING (thresholds, sizes, filter
settings) waits until the week ends, so the test measures one configuration, unless the owner says
otherwise; the analyst's notes collect those proposals for the post-week review.
