#!/usr/bin/env bash
# The watchdog's deterministic half: fetch the run branch, judge its health, write the phone
# dashboard's rows. Read-only: commits and pushes nothing, starts and stops nothing, needs no key.
#
#   bash ops/watchdog.sh
#
# Prints the money line (dashboard.money) and the health line (reports.health) and exits 3 when the
# health line is an ALERT, 0 otherwise. MONEY_OUT (default /tmp/dealbot-dashboard/money.json) gets
# the rows the money dashboard reads; LOG_COPY, when set, keeps the copy of the run's logs there.
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
"$PY" -m reports.health --log-dir "$COPY/logs/data" --commit-ms "$COMMIT_MS"
