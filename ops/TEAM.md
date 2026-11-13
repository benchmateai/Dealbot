# The Dealbot paper-desk team

One week of paper trading on live Kalshi 15-minute crypto contracts (ETH and BTC), to show whether the
desk is worth taking live. The first desk was judged by Jev; since 2026-11-05 desk v2 trades a
market-anchored forecast instead (see "Desk v2"). Paper money only. House rules, from the owner: never
place a live order; ask the owner before adding any API key (trading-only, withdrawals disabled);
keep secrets out of code and logs; show the owner every change as a diff.

The first desk's measured week ran from 2026-11-03T08:25:00Z until desk v2 took over at
2026-11-05T04:19:48Z; v2's week runs to 2026-11-12T04:20Z, and the final report and verdict follow at
04:50Z. The first week started at 06:20:24Z, but from 06:42 to 08:23Z every restart of the
desk left the previous desk running (the chunk script killed a wrapper shell, not the desk), so two
to four desks traded side by side and wrote every decision twice into one log. That stretch stays
in the run branch's record and is left out of the results (fixed in 1f1a3f4; reports/health.py now
raises an ALERT if a decision is ever logged twice).

On 2026-11-05 the owner switched the desk to v2 as soon as it passed its tests. The first desk's week
closed at the switch with its result kept for the record (-60.42 USD after fees on 250 closed bets, its
last open bet then settling a winner under v2). v2's measured week runs seven days from its first block,
2026-11-05T04:19:48Z (`reports/runs.py` finds it in the log), and the stop and final-report tasks are
re-timed to it.

## Who does what

| Role | Model | Cadence | Does | Never |
|---|---|---|---|---|
| Coordinator | Opus 5.5, session `session_01C4NeDS3CKGZfUNrC7ArPuL` | on escalation; supervisor check every 6 h; morning report 06:31 Arizona (13:31Z) | the only writer of code (`claude/desk-skeleton`) and the only voice to the owner; fixes what teammates find; replaces a teammate that stops | live trading; keys without the owner |
| Runner | Sonnet 5.5, session `session_01JrtRuFoJFvVT79cmMzPuAC` | 110-minute chunks back to back | `ops/paper_chunk.sh` (`ops/runner_prompt.md`): the chunk script pushes logs to `paper-run` every 30 min; the runner republishes the pipeline dashboard after each chunk | edits, commits or pushes by hand |
| Watchdog | Haiku 5.5, session `session_01JrtRuCP3RKtfhHmsiC3UYw` | hourly at :17 | `ops/watchdog.sh` (`ops/watchdog_prompt.md`): health line, then refreshes the money dashboard | edits code, deletes anything |
| Lab runner (REST) | Haiku 5.5, session `session_01JrtRuC2MxTqb4BE8GVXSXP` | 110-minute chunks back to back | `LAB_FEEDS=rest ops/lab_chunk.sh` (`ops/lab_runner_prompt.md`): records Kalshi's public market data (settlement values for A; D was dropped 2026-11-05) and pushes each finished hour to `shadow-run` | orders of any kind; edits, commits or pushes by hand |
| Lab runner (live feed) | Haiku 5.5, session `session_01JrtRuF1RVSJHGR8478xKpm` (since 2026-11-04 03:20Z) | 110-minute chunks back to back | `LAB_FEEDS=ws ops/lab_chunk.sh` (`ops/lab_feed_runner_prompt.md`): records the authenticated WebSocket feed for E and F (B and C were dropped 2026-11-05; the recorder is unchanged) into the same branch | orders of any kind; reading or printing the key; edits, commits or pushes by hand |
| Lab runner (gaps) | Haiku 5.5, session `session_01JrtRuEaTaCAT56DVc9hkc3` (since 2026-11-08 22:01Z, in the Dealbot environment) | 110-minute chunks back to back | `LAB_FEEDS=gap ops/lab_chunk.sh` (`ops/gap_runner_prompt.md`): records Kalshi and Polymarket US public quotes on the pairs in `lab/gap_pairs.json` into the same branch | orders of any kind; keys; edits, commits or pushes by hand |
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
| Paper run: stop after one week | `trig_01GZynojVUiE1qCcTVikWBML` | 2026-11-12T04:20Z (v2's week) | the coordinator |
| Paper run: final weekly report and verdict | `trig_0185uWBZUeyYdDopGG326NDd` | 2026-11-12T04:50Z | the coordinator |

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
  virtualenv for the live feed; exit 6: the live feed kept failing; exit 7: the gap recorder kept failing).
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

## Running cost and budgets (from 2026-11-10)

The owner asked to see what the team costs to run beside what it makes. get_session reports each session's
cumulative usage cost (`usage.cost_usd`), and only the coordinator reads it. Each morning report writes the
seven costs to a snapshot, `<coordinator scratchpad>/costs/today.json`:
`{"at": ISO, "sessions": {role: {"id", "cost_usd", "created_at"}}}`, with the roles of `ops/budgets.json`
(coordinator, runner, watchdog, analyst, lab_rest, lab_ws, lab_gap); a teammate replaced since the last
snapshot has its old session read too (each of them, if it was replaced more than once) and added under `"retired": {old id: {"role", "cost_usd"}}`, so what
it spent before the switch is counted. It then runs `python3 -m reports.costs
--snapshot <that file> --ledger <coordinator scratchpad>/costs/ledger.jsonl --record --paper-24h <the
round's paper change over the last 24 hours>`: each teammate's spend since the last morning against its
daily budget, the team's total, and the desk's paper result beside it. The supervisor checks run it the same
way on their own snapshot (`costs/now.json`) without `--record`. Both then put it on the money dashboard
(from 2026-11-11): `python3 -m dashboard.costs --snapshot <that file> --history <coordinator
scratchpad>/costs/history.jsonl --append --out <coordinator scratchpad>/costs/costs.json` (each teammate's
spend since the history's snapshot nearest 24 hours back, against its budget, and its total, and the team's
cost by Arizona day for the calendar's Team cost tab; the days before the first snapshot, 2026-11-10T21:30Z, come
from `costs/before.json` beside the history, estimated once: the coordinator's from its own logs priced at list
prices, the other teammates' spread evenly over their sessions), uploaded as
an asset and set as the file of the dashboard's `costs` dataset, as for `datasets/paper`; the page shows it
beside the desks' paper result over the same hours. A teammate that has spent a whole day's
budget since the morning is a runaway: the coordinator reads its last replies, stops or fixes the loop as
the escalation section says, and tells the owner in two lines. The budgets in `ops/budgets.json` change only
with the owner, and nothing is stopped automatically for being over one.

## Review before push (from 2026-11-10)

A commit that touches money code (`ops/money_paths.txt`: what places, sizes, fills, prices, fees, settles or
reports money) goes to `claude/desk-skeleton` only after a fresh reviewer has read it. The coordinator
starts a subagent (the Agent tool, general-purpose) with the brief in `ops/review_prompt.md` and the commit
range, and gives it the code, not the coordinator's own view of the change. Every finding is fixed or
answered before the push, and the commit's message then carries a `Reviewed-by:` trailer naming the
reviewer and what came of its findings; the diff sent to the owner says the same. `ops/review_gate.py`
refuses a push of such a commit without the trailer: the coordinator's clone runs it as git's pre-push hook
(`git config core.hooksPath ops/hooks`). The runners push only data through their chunk scripts and are not
affected.

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

### Cross-venue gaps (from 2026-11-08)

The owner asked to measure the Kalshi to Polymarket US price gaps the cross-venue report ranked low
(`reports/Viable trading strategies across venues.md`: a median real gap of 0.78 cents against about 3.5
cents of fees). The gap recorder (`lab/gap_recorder.py`) reads both venues' public prices, with no key and
no orders, for the pairs in `lab/gap_pairs.json`: markets that settle the same way on both venues, each
with a note saying why (175 on 2026-11-08: the 2027 NFL, NBA, NHL and MLB champions, the 2028 Democratic
and Republican nominees, October's CPI and core CPI month-on-month, the December Fed decision and a 2026
cut; on 2026-11-10 the owner added 44 Bitcoin pairs, 219 in all: the 28 year-end 2026 price ranges, how
high and how low it goes this year, $100,000 by Dec 1 and by Jan 1, and $150,000, $200,000 and $250,000
this year, all settled on CF Benchmarks' BRTI on both venues; Kalshi charges no fee on its year-end
ranges and quotes them in tenths of a cent where Polymarket US quotes whole cents, so the cheapest ranges'
books cross by a fraction of a cent most of the time and the money a lock ties up until Jan 1 decides
whether it pays). Every 60 seconds it reads Kalshi's best prices in batches and each Polymarket US book right after
(seconds apart), and writes a `gap_quote` record when either changes. `python3 -m lab.gap_report --lab
<shadow-run lab/data>` gives the gaps: the mid gap, the share of the time either venue's bid crossed the
other's ask, and whether that paid after both taker fees (Kalshi 0.07 times the series' multiplier;
Polymarket US the market's own coefficient, 0.095 for an account below $10,000 a month; makers pay
nothing there and earn no rebate below $10 million) and after 4% a year on the money a lock ties up until
settlement. On a first live look (two passes) the median mid gap was 0.35 cents, the books crossed 13.5%
of the time, 4.5% paid after fees and none after the cost of the money. Pairs end as their markets settle
(the CPI ones on Nov 10); new ones go into `lab/gap_pairs.json` with a rules note and are picked up at
the next chunk. Polymarket US and Deribit are reachable only from the Dealbot cloud environment (it allows
gateway.polymarket.us and www.deribit.com; the Default one does not), so the gap recorder has its own runner there; a
replacement is created the same way (`create_session` in that environment, source
https://github.com/benchmateai/Dealbot at `claude/desk-skeleton`, model Haiku 5.5, tags
`dealbot-paper-run`, `dealbot-lab`, prompt `ops/gap_runner_prompt.md`).

### The Bitcoin options test (from 2026-11-10)

The owner asked to test pricing the Bitcoin markets off Bitcoin's options. The gap recorder also reads
Deribit's public API (no key, no orders): the BTC index every pass (`opt_index`) and every 5 minutes the
option surface (`opt_surface`: each expiry 2 to 200 days away, its forward and its out-of-the-money options'
mark volatilities). Each Bitcoin pair in `lab/gap_pairs.json` carries a `model`, what it pays on: a year-end
range, the price above or below a level on Jan 1, or a touch of a price before Dec 1 or Jan 1.
`lab/btc_options.py` prices them: the ranges at what the options imply (the call price's slope in the strike,
from the smile at Jan 1 between the Dec 25 and Jan 29 expiries), the touch markets at a model's price (a
geometric Brownian motion with the barrier strike's volatility). `python3 -m lab.strategies.btc_options --lab
<shadow-run lab/data>` replays the recorded quotes against those prices from 2026-11-10 20:00Z: how far each
venue's mid sits from the options' price (ranges and touches apart), how often an edge of a cent or more was
there after fees and the cost of the money, and three paper variants fixed before any result (hurdles of 1, 2
and 3 cents beyond the taker fee and 4% a year on the money until settlement; taker buys at the displayed
price and size, at most $100 per market, side and venue and $3,000 in all, held to settlement), marked at the
options' price and at the venues' bids, with whether the venues drift toward the options' price 1, 6 and 24
hours after an entry. Settlement comes on Dec 1 for one pair and Jan 1 for the rest, sooner for a touch that
happens; Kalshi's quotes now carry its `result` so the test can settle them. `python3 -m lab.btc_options`
gives one live look at every pair beside its price.

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

On 2026-11-05, after v2's first 44 bets (long shots +20.83 USD, favourites +4.95; the late stop saved
5.13 on 22 long shots and cost 6.27 on the one favourite it sold, which then won), the owner chose two
paper rules on v2's own bets, fixed in `reports/shadow_v2.py` and counted only on bets opened from
2026-11-05T22:00Z: `late_stop_underdogs` (the late stop only on bets bought under 50 cents; favourites held
to the close) and `skip_favourites` (skip bets bought above 70 cents). On 2026-11-06 they added a third,
`skip_late_entries` (skip bets opened under 3 minutes before the close: lab A's forecast lost to Kalshi's
price 3 minutes and 1 minute out), and `next_round` (rules 1 and 3 together, favourites kept), both counted
only on bets opened from 2026-11-06T07:00Z and reported beside v2 on exactly the same bets. v2 itself
trades on unchanged; `python3 -m reports.shadow_v2 --log-dir <logs/data>` prints them all beside v2, and
the dashboard shows them.

The next round (the owner's decisions of 2026-11-06 and 2026-11-07): v2 stays as it is until its week ends
on 2026-11-12, so the test measures one configuration. On 2026-11-06 the owner picked desk v3 for the next
round (v2's forecast with entries only 3 to 10 minutes out and the late stop on long shots only; built on
the branch `claude/next-round`, now parked). By 2026-11-07 the forecast's edge had faded (its fitted
weight fell from 0.55 to 0.15, lab A fell to about zero, and Kalshi's price scored as well or better at
every horizon), so the owner chose the E desk instead: a paper desk for strategy E, resting two-sided
orders where Kalshi pays liquidity rewards.

On 2026-11-12 the owner skipped the E desk and stood the team down after v2's final report: v2 failed its
paper test (its forecast scored no better than Kalshi's price at any horizon, and its deflated Sharpe was
0.05 against the 0.95 needed). The desk runner, the watchdog, the analyst and the three lab runners are
stopped, their scheduled tasks and the morning report are disabled, and `ops/round.txt` stays `v2`;
nothing was deleted or archived. Only the long-shot backtest (`lab/longshot.py`) runs, in the
coordinator's session, restarted every two hours until its download finishes. The E desk below was never
started.

Later on 2026-11-12: the long-shot backtest failed its main test, and the owner asked for one more test
and for a fresh look at everything tried. The weather settlement backtest (`lab/weather.py`, Kalshi's
temperature markets against The Weather Company's settlement figure) runs in the coordinator's session.
An audit of the earlier tests found that the Kalshi to Polymarket US gaps on the Bitcoin year-end ranges
paid after both fees and the cost of the money 15% of the time on the final recording, which the final
summary had misreported. On the owner's word (about 19:40Z) the gap-recorder runner was restarted, which
also feeds the Bitcoin options test, and the coordinator builds a backtest of quoting Kalshi's combos
from public trade data; the combos stay on paper, as their legs are sports contracts and Arizona's case
on those is still open. The desk runner, the watchdog, the analyst and the other two lab runners stay
stopped.

The E desk (`lab/strategies/e_desk.py`) quotes as lab E does and adds risk rules that stop it adding
risk but never stop it pairing off what it holds: $250 per market, $5,000 of orders and holdings in all,
nothing added in a market's last 3 hours, and no new risk in a market after a $40 loss there. Five
variants, registered before its start, run beside it on the same recording and are never retuned
mid-week: `news_pause` (pause 15 minutes after a 5-cent move), `calendar_blackout` (no new risk in
economic and crypto markets an hour either side of the dated releases in CATALYSTS: inside the week only
the Fed minutes, Nov 18 at 19:00Z), `headline_filter` (no new risk in Kalshi's Elections markets or in
approval, impeachment and departure series), `no_close_rule` (the main desk without the 3-hour close
rule) and `cheap_side` (on a side priced 10 cents or less, quote up to $250 by dollars instead of a
tenth of the Target Size: Kalshi splits each side's pool by contracts, not dollars). Its report splits its money by kind of market (Kalshi's category for the series: sports,
political, economic, crypto, other), and the page shows that split. Its week runs from
2026-11-12T05:00Z (START_MS) to 2026-11-19T05:00Z. It sends nothing to Kalshi: each run replays its rules
over the lab's live-feed recording on `shadow-run`, so the live-feed lab runner must keep recording. The
hourly watchdog merges its rows into money.json (`dashboard/edesk.py`), and the page's E desk section
shows them. `ops/round.txt` names the round: `v2` until the switch, then `edesk`, when the watchdog's
health line judges the recording the E desk runs on instead of desk v2's pushes.

On E's first 81 hours (in sample, 2026-11-03 to 11-07) lab E, marked correctly, made about -$12 (payments
$71.67, fills marked -$83.74; most of the loss one presidential-approval market that went to 98 cents
against it), and the E desk's rules about -$2.

The close rule needs each market's close time on its books. Until 2026-11-07 the live-feed recorder kept
none for E's markets (the program list does not carry them) and recorded no E results, so the rule never
acted in sample. Since then the recorder looks up each market E picks (close time, series, event) and
each new series (a `series_meta` record with Kalshi's category), unwatches an E market at its close and
fetches its result, also for a market that leaves E before it closes. With Kalshi's close times and
results filled in afterwards, E's first 90 hours come to about -$4 for the main desk, +$8 without the
close rule, and +$16 for the headline filter (which kept out 29 election and approval markets and earned
$4.80 in payments); the calendar blackout had nothing to act on.

Two corrections of 2026-11-08. The $5,000 cap counted a YES and a NO held in one market as money tied
up (Kalshi nets the pair into $1 at once) and kept counting a market's holding after its result was
recorded (paid out). On the same 113.6 hours, the old accounting held the desk at its cap in 28
markets and made -$3.05; the fixed one caps 4 markets and makes +$25.47 (payments $86.26, fills marked
-$60.79). And Kalshi's rule that it scores the orders that "help reach the Target Size" leaves open
whether orders already resting at a price come first: the desk scores as lab E does (they do, so an
order behind a queue that already fills the Target Size earns nothing), and every report also gives the
payments if every order at a level counts. The main desk's payments are $86.26 one way and $172.60 the
other; only Kalshi's own payouts can settle it. On the same hours cheap_side made +$71.40, but on less
in payments ($39.59, near its cap all along): its lead is one Senate-seat long shot bought cheap and
marked up $77, unsettled, and the approval bracket that cost the main desk $79, which it never held.

Switching to the E desk (planned for after the final report; not done, as the owner skipped the E desk):
1. On `claude/desk-skeleton`, set `ops/round.txt` to `edesk` and push (ops/ never restarts the desk).
2. The desk runner stays stopped after v2's week. Never stop the lab runners: the E desk runs on the live
   feed, and lab E stays its control.
3. Re-enable the supervisor, watchdog, analyst and morning report scheduled tasks (update_trigger
   enabled true), with the morning report's prompt rewritten for the E desk (`python3 -m
   lab.strategies.e_desk --lab <lab copy> --variants` for its line, its split by kind of market and the
   five variants' lines, replayed side by side in about two minutes by the week's end, each with its net
   if Kalshi credits whole price levels; lab E beside it; and keep the `lab.gap_report` line on the
   Kalshi to Polymarket US gaps, the `lab.strategies.btc_options` line on the Bitcoin options test, and the
   team's running cost with its dashboard step, as "Running cost and budgets" says).
4. Schedule the E desk's final report for 2026-11-19T05:30Z: its result at the week's end (the replay
   stops there by itself) against lab E and the five variants, by market, program and kind of market,
   with the money it tied up.
5. Refresh the money dashboard (the watchdog does it hourly) and tell the owner the E desk has started
   and when its week ends.

`KALSHI_FORECAST=blend` runs the first desk again. The pre-flight runs v2 with a confident forecast in
place of the confident judge.

## During the paper week

BUG fixes (wrong behaviour) go in as soon as they are found. TUNING (thresholds, sizes, filter
settings) waits until the week ends, so the test measures one configuration, unless the owner says
otherwise; the analyst's notes collect those proposals for the post-week review.
