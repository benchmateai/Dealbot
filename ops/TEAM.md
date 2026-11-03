# The Dealbot paper-desk team

One week of paper trading on live Kalshi 15-minute crypto contracts (ETH and BTC), judged by Jev, to
show whether the desk is worth taking live. Paper money only. House rules, from the owner: never
place a live order; ask the owner before adding any API key (trading-only, withdrawals disabled);
keep secrets out of code and logs; show the owner every change as a diff.

The week runs from the first judged decision, 2026-11-03T06:20:24Z, to 2026-11-10T06:20:30Z; the
final report and verdict follow at 06:50Z.

## Who does what

| Role | Model | Cadence | Does | Never |
|---|---|---|---|---|
| Coordinator | Opus 5.5, session `session_01C4NeDS3CKGZfUNrC7ArPuL` | on escalation; supervisor check every 6 h; morning report 06:31 Arizona (13:31Z) | the only writer of code (`claude/desk-skeleton`) and the only voice to the owner; fixes what teammates find; replaces a teammate that stops | live trading; keys without the owner |
| Runner | Sonnet 5.5, session `session_01JrtRuFoJFvVT79cmMzPuAC` | 110-minute chunks back to back | `ops/paper_chunk.sh` (`ops/runner_prompt.md`): the chunk script pushes logs to `paper-run` every 30 min; the runner republishes the pipeline dashboard after each chunk | edits, commits or pushes by hand |
| Watchdog | Haiku 5.5, see the scheduled task "Dealbot watchdog (hourly)" | hourly at :17 | `ops/watchdog.sh` (`ops/watchdog_prompt.md`): health line, then refreshes the money dashboard | edits code, deletes anything |
| Analyst | Sonnet 5.5, see the scheduled task "Dealbot analyst (daily)" | daily 12:41Z | `ops/analyst_prompt.md`: reconciles settlements, studies P&L, Jev's calibration and the filter funnel; one note a day on `paper-notes` | edits the desk's code or the run |
| Fresh eyes | a review subagent the coordinator starts | before any change to `risk/`, `policy/`, `broker/` or fills | reads the diff cold, without the coordinator's reasoning | |

Each teammate does one job on a schedule and hands everything else up. The deterministic parts
(health rules, money rows, reconciliation) are code with tests (`reports/health.py`,
`dashboard/money.py`, `reports/reconcile.py`), so the models only run them and act on the result.

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

Any teammate escalates with `fire_trigger` on `trig_011Fb7LfMudmP3ipB3cb1Uq5` and the text
`"<role>: <what is wrong>"`; that wakes the coordinator, who verifies before acting.

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
