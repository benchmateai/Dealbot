# Dealbot desk

A 24/7 AI trading desk skeleton. **Paper trading only.** There is no live broker in this repository
and no code path that can place a live order. Jev (TypeSafe's System One decision model) is the
judge; code owns every decision.

```
feed/       raw ticks (synthetic random walk, or JSONL replay)            -> never decides anything
state/      deterministic snapshot, < 400 tokens, point-in-time safe      -> what Jev sees
questions/  one battery per bot (gambler, house, spy), one judgment each  -> what Jev is asked
judge/      the only process holding the Jev key; returns raw answers     -> never decides anything
policy/     thresholds (one per action, from costs) and weights in code   -> raw answers -> one pick
risk/       hard vetoes before every order; no model can override them    -> approve or veto
broker/     paper broker, same interface a live one would use             -> fills, fees, gas
filter/     the funnel: free cut, one-call, hard facts, Jev, final pick   -> every rejection logged
book/       one open position at a time, plus the bench                   -> no scan while open
logs/       JSONL: every snapshot, question, answer (with probabilities), decision, veto, outcome
outcomes/   grades every judgment after its horizon from the realized path -> calibration data
reports/    calibration (buckets, Brier, reliability chart), daily summary, trial report
trials/     registry of every configuration ever run, deflated Sharpe haircut
desk/       config, block clock, modes (shadow | paper), the loop, the CLI
```

## Run it

Keyless dry run (stub judge, synthetic feed, no network):

```bash
uv venv && uv pip install -e '.[dev]'          # desk needs only the standard library
python -m desk.run --mode shadow --fast --blocks 200
python -m reports.daily --date $(date -u +%F)
python -m reports.calibration
pytest
```

With the real judge, two processes with two environments:

```bash
# judge host: the ONLY place TYPESAFE_API_KEY exists
cp .env.judge.example .env.judge   # fill DESK_SECRET, JEV_MODEL; export TYPESAFE_API_KEY yourself
uv pip install -e '.[judge]'
python -m judge.service --env-file .env.judge

# desk host: never sees the key (the desk refuses to start if TYPESAFE_API_KEY is in its environment)
cp .env.desk.example .env.desk     # same DESK_SECRET and JEV_MODEL, JUDGE_URL=http://judge-host:8787
python -m desk.run --env-file .env.desk --mode shadow     # 24/7, real block clock
python -m desk.run --env-file .env.desk --mode paper
```

`DESK_SECRET`: `python -c "import secrets; print(secrets.token_hex(32))"`. `JEV_MODEL`: an exact
pinned name from `GET /v1/models` (the judge verifies it on start). `jev-latest` is refused by both
processes.

## How a block works

1. The feed delivers every tick with `ts < block.ts`. The paper broker fills resting orders.
2. Equity is marked; outcomes whose horizon has passed are graded and logged.
3. If a position is open (or an entry order is resting): **manage** that one position. Otherwise **scan**.
4. Scan runs the funnel over every symbol, cheapest check first:
   `free_cut` (bench, staleness, sanity, spread, vol band; only the snapshot in hand) ->
   `one_call` (feed lag, resting orders, equity) ->
   `hard_facts` (best-case edge vs fees+gas, risk pre-check with a full-size order) ->
   `jev` (one call per surviving candidate, bounded by `MAX_JEV_CANDIDATES`, deadline = next block minus margin) ->
   `final_pick` (policy scores every action; one candidate survives).
   Every rejection is logged with its stage and check, and benches the symbol for a reason-specific time.
5. The one surviving pick becomes one order. The risk gate runs **all** vetoes: max position, daily loss,
   leverage, range guard, fees+gas, model version, stale data. Every veto is logged.
6. shadow: the approved order is logged as `would_execute`. paper: it goes to the paper broker.

If Jev has not answered before the deadline, the desk holds. A rate limit starts exponential backoff
(honoring retry-after). A malformed-question error is never retried: it is a bug in the battery, so the
desk logs it and holds every block until the process is restarted with a fixed battery.

## Jev, the official SDK, and the official skill

- Adapter: `judge/jev.py`, the only module that imports `typesafe_sdk` (0.7.x). The desk never imports it.
- The battery is sent as one `system_one` call per decision: the full set of questions over the same state.
- The judge pins the model (`TypeSafeClient(model=JEV_MODEL)`), verifies it against `/v1/models` on start,
  and returns `response.model` verbatim; the risk gate vetoes any decision whose model string differs.
- Retries: `RetryPolicy(http_statuses={429, 500, 502, 503, 504}, respect_retry_after=True)` inside a fixed
  budget. 400/422 map to `malformed_question` and are never retried.
- The official skill (`typesafe-ai/skills` on GitHub; in Claude Code: `claude plugin marketplace add typesafe-ai/skills`
  then `claude plugin install typesafe@typesafe-ai`) shaped the question design: one narrow judgment per
  question, named JSON state with backticked paths (`mkt.spr_bps`, `desk.cost_bps`), descriptions in criteria,
  an explicit no-match option on every Choice, independent questions asked together, policy kept in code.

State sent with every battery:

```json
{"mkt": {"sym": "ETH-USD", "as_of": 1700000000000, "blk": 41, "mid": 2501.3, "spr_bps": 2.0, "imb": 0.11,
         "rv_bps": 9.8, "ret_bps": {"w1": 1.2, "w5": -4.0, "w20": 18.3}, "n": 360, "inv": 0.0, "inv_usd": 0.0,
         "dd_bps": -12.5, "dd_day_bps": 0.0},
 "pos": null,
 "desk": {"bot": "gambler", "phase": "entry", "cost_bps": 24.0, "fee_bps": 10, "gas_usd": 0.5}}
```

## Policy numbers live in code

- `policy/thresholds.py`: `threshold = wrong_bps / (wrong_bps + missed_bps)` per action, per bot. Change a
  cost and the threshold follows.
- `policy/weights.py`: each action is a weighted average of probabilities pulled from named answers; weights
  sum to 1; a term whose `when` condition fails contributes 0.
- `policy/thresholds.py` `EDGE`: target and stop in bps give `expected_edge_bps`, which the fees+gas veto
  compares with round-trip cost. Market orders (gambler, spy) pay `FEE_BPS`; resting limit orders (house)
  pay `MAKER_FEE_BPS`; `GAS_USD` is charged per transaction either way.

## Trial registry and the deflated Sharpe haircut

Every configuration the desk starts with is a trial: bot, battery version, thresholds, weights, edge model,
risk limits, clip size, symbols, feed, cadence and the pinned Jev version (see `trials/fingerprint.py`; mode and
deployment details are excluded, so a shadow run and a paper run of one configuration are one trial). The desk
registers each run in `logs/data/trials.json`, logs a `trial` record, and stamps decisions and heartbeats with
the trial id. Nothing is ever removed from the registry: its size is the N that deflates every survivor.

`python -m reports.trials` builds each trial's return series from its heartbeat equity, computes the per-period
Sharpe with skew and kurtosis, and deflates it (Bailey and López de Prado, 2014): the best-noise Sharpe is the
expected maximum of N noise trials, the haircut Sharpe is the observed Sharpe minus that, and the DSR is the
probability the survivor beats the best noise trial. The report also prints the minimum backtest length for N
trials. Treat a configuration as a candidate only when its DSR is at least 0.95 on a sample longer than that
minimum. Use `--effective-trials` to lower N for highly correlated trials or raise it for trials run elsewhere.

## Logs and reports

`logs/data/events-YYYY-MM-DD.jsonl`, one record per line with `ts` and `kind`. Every value passes through
the redactor (configured secrets, bearer tokens, key-shaped strings, secret-looking keys). Outcome records
carry the predicted probabilities and the realized label, so calibration needs no joins.

- `python -m reports.calibration [--date D]` -> `reports/out/calibration-*.md` + `reliability-*.svg`
  (predicted vs observed per bucket, Brier overall and per question).
- `python -m reports.daily --date D` -> decisions, trades, PnL after fees and gas, every veto, rejections by check.
- `python -m reports.trials` -> `reports/out/trials.md`, every trial with its deflated Sharpe.

## Rules this repository follows

- Never a live order: `broker/` has only `PaperBroker`; `make_broker("live")` raises.
- No keys in code or logs. `.env*` is gitignored except the two examples. The desk refuses to run if it can
  see `TYPESAFE_API_KEY`. Any future exchange key must be trading-only with withdrawals disabled.
- Hard vetoes cannot be bypassed in code: the broker only accepts an order with a single-use approval issued
  by the risk gate for that exact order.
- Every snapshot field uses only data from before the decision (`ts < as_of`), checked by tests.

## Known gaps (skeleton)

- Fixed clip size (`ORDER_QTY`); no sizing model.
- Shadow mode never opens a virtual position, so exit decisions are only labeled in paper mode.
- The HTTP client timeout is per socket operation, not a hard total; the judge also receives the deadline.
- The calibration chart is a static SVG (light and dark via `prefers-color-scheme`).
