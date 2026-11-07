#!/usr/bin/env bash
# The watchdog's deterministic half: fetch the run branch, judge its health, write the phone
# dashboard's rows. Read-only: commits and pushes nothing, starts and stops nothing, needs no key.
#
#   bash ops/watchdog.sh
#
# Prints the money line (dashboard.money), the E desk line (dashboard.edesk, on the lab's live-feed
# recording from shadow-run) and the health line, and exits 3 when the health line is an ALERT, 0
# otherwise. The health line judges the round named in ops/round.txt: desk v2's run (reports.health)
# or, once the E desk is the round, the recording it runs on. MONEY_OUT (default
# /tmp/dealbot-dashboard/money.json) gets the rows the money dashboard reads; LOG_COPY, when set,
# keeps the copy of the run's logs there.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
RUN_BRANCH=${RUN_BRANCH:-paper-run}
MONEY_OUT=${MONEY_OUT:-/tmp/dealbot-dashboard/money.json}
PY=${PY:-python3}
cd "$REPO"

fetched=""
for delay in 0 2 4 8; do
  [ "$delay" -gt 0 ] && sleep "$delay"
  if git fetch -q origin "$RUN_BRANCH" 2>/dev/null; then fetched=1; break; fi
done
if [ -z "$fetched" ]; then echo "health: ALERT · could not fetch origin/$RUN_BRANCH"; exit 3; fi

COPY=${LOG_COPY:-$(mktemp -d)}
[ -n "${LOG_COPY:-}" ] || trap 'rm -rf "$COPY"' EXIT
rm -rf "$COPY/logs"
mkdir -p "$COPY"
git archive "origin/$RUN_BRANCH" logs/data | tar -x -C "$COPY"
COMMIT_MS=$(( $(git log -1 --format=%ct "origin/$RUN_BRANCH") * 1000 ))

mkdir -p "$(dirname "$MONEY_OUT")"
"$PY" -m dashboard.money --log-dir "$COPY/logs/data" --out "$MONEY_OUT" | sed 's/^/money: /' || echo "money: FAILED to build the dashboard rows"

ROUND=$(tr -d '[:space:]' < "$REPO/ops/round.txt" 2>/dev/null || echo v2)
LAB=$(mktemp -d)
lab_ok=""
if git fetch -q origin shadow-run 2>/dev/null && git archive origin/shadow-run lab/data | tar -x -C "$LAB"; then
  lab_ok=1
  "$PY" -m dashboard.edesk --lab "$LAB/lab/data" --merge-into "$MONEY_OUT" | sed 's/^/edesk: /' || echo "edesk: FAILED to build the E desk rows"
else
  echo "edesk: FAILED to fetch the lab recording (origin/shadow-run)"
fi
status=0
if [ "$ROUND" = "edesk" ]; then
  if [ -n "$lab_ok" ]; then
    "$PY" -m dashboard.edesk --lab "$LAB/lab/data" --health || status=$?
  else
    echo "health: ALERT · could not fetch origin/shadow-run, the recording the E desk runs on"; status=3
  fi
else
  "$PY" -m reports.health --log-dir "$COPY/logs/data" --commit-ms "$COMMIT_MS" || status=$?
fi
rm -rf "$LAB"
exit "$status"
