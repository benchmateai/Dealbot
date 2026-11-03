# The Dealbot paper-desk team

One week of paper trading on live Kalshi 15-minute crypto contracts (ETH and BTC), judged by Jev, to
show whether the desk is worth taking live. Paper money only. House rules, from the owner: never
place a live order; ask the owner before adding any API key (trading-only, withdrawals disabled);
keep secrets out of code and logs; show the owner every change as a diff.

The measured week runs from 2026-11-03T08:25:00Z to 2026-11-10T08:25:00Z; the final report and
verdict follow at 08:55Z. It started at 06:20:24Z, but from 06:42 to 08:23Z every restart of the
desk left the previous desk running (the chunk script killed a wrapper shell, not the desk), so two
to four desks traded side by side and wrote every decision twice into one log. That stretch stays
in the run branch's record and is left out of the results (fixed in 1f1a3f4; reports/health.py now
raises an ALERT if a decision is ever logged twice).

## Who does what

| Role | Model | Cadence | Does | Never |
|---|---|---|---|---|
| Coordinator | Opus 5.5, session `session_01C4NeDS3CKGZfUNrC7ArPuL` | on escalation; supervisor check every 6 h; morning report 06:31 Arizona (13:31Z) | the only writer of code (`claude/desk-skeleton`) and the only voice to the owner; fixes what teammates find; replaces a teammate that stops | live trading; keys without the owner |
| Runner | Sonnet 5.5, session `session_01JrtRuFoJFvVT79cmMzPuAC` | 110-minute chunks back to back | `ops/paper_chunk.sh` (`ops/runner_prompt.md`): the chunk script pushes logs to `paper-run` every 30 min; the runner republishes the pipeline dashboard after each chunk | edits, commits or pushes by hand |
| Watchdog | Haiku 5.5, session `session_01JrtRuCP3RKtfhHmsiC3UYw` | hourly at :17 | `ops/watchdog.sh` (`ops/watchdog_prompt.md`): health line, then refreshes the money dashboard | edits code, deletes anything |
| Analyst | Sonnet 5.5, session `session_01JrtRuFFYYmFkU2WSWi25VR` | daily 12:41Z | `ops/analyst_prompt.md`: reconciles settlements, studies P&L, Jev's calibration and the filter funnel; one note a day on `paper-notes` | edits the desk's code or the run |
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
  `ops/`, `tests/`, `reports/` or `dashboard/` does not (the run picks it up at its next restart).
- `paper-run`: the run's logs, state, trials, reports and summaries; only the chunk script commits here.
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
- Watchdog: when the health line is ALERT (stale pushes, a desk fault, no Jev calls for two hours,
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

## During the paper week

BUG fixes (wrong behaviour) go in as soon as they are found. TUNING (thresholds, sizes, filter
settings) waits until the week ends, so the test measures one configuration, unless the owner says
otherwise; the analyst's notes collect those proposals for the post-week review.
