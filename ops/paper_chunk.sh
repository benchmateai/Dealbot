#!/usr/bin/env bash
# One unattended chunk of the paper desk. Paper only: there is no live broker in this repository.
#
#   FEED=kalshi DESK_BOT=kalshi DESK_SYMBOLS=KXETH15M,KXBTC15M bash ops/paper_chunk.sh
#
# The run branch lives in its own git worktree outside this checkout (RUN_DIR), so the session's
# checkout stays clean on the base branch and no stop hook asks anyone to commit run logs. A chunk:
#   1. syncs the run worktree: the run branch from origin, then the base branch merged in
#   2. pins the Jev model once per run and starts the judge, which alone holds the TypeSafe key
#   3. runs the pre-flight (python -m desk.preflight); a failure stops the chunk with exit 4
#   4. runs the desk until the chunk deadline, checking the base branch every WATCH_SECONDS: when a
#      fix lands, the desk stops after its current block, the run merges the fix, passes the
#      pre-flight again and carries on (so a pushed fix reaches the run within minutes). A base
#      change that only touches docs, ops scripts, tests, reports or dashboards does not stop the
#      desk; the run picks it up at the next restart or chunk
#   5. after every desk segment, and every PUBLISH_SECONDS while the desk runs (first after 15
#      minutes): a summary (reports.chunk_summary) and a commit of logs, checkpoint, trials, reports
#      and summaries to the run branch, pushed, so health checks and the dashboard never wait long
#   6. at the end: the daily report and the dashboard snapshot in DASHBOARD_OUT
# The desk process never sees TYPESAFE_API_KEY or any Kalshi credential.
#
# Exit codes: 0 done, 2 setup (key missing, judge down, pin failed), 4 pre-flight failed, 5 desk crashed.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)

RUN_BRANCH=${RUN_BRANCH:-paper-run}
BASE_BRANCH=${BASE_BRANCH:-claude/desk-skeleton}
RUN_DIR=${RUN_DIR:-$HOME/dealbot-run}
VENV=${VENV:-$HOME/dealbot-venv}
JUDGE_AUTH=${JUDGE_AUTH:-env}                 # env: TYPESAFE_API_KEY | proxy: the environment proxy injects the key
JUDGE_PORT=${JUDGE_PORT:-8787}
JUDGE_BACKEND=${JUDGE_BACKEND:-typesafe}      # typesafe | stub | demo (demo and stub need no key)
BLOCK_SECONDS=${BLOCK_SECONDS:-12}
if [ -n "${CHUNK_BLOCKS:-}" ]; then CHUNK_SECONDS=$(( CHUNK_BLOCKS * BLOCK_SECONDS )); else CHUNK_SECONDS=$(( ${CHUNK_MINUTES:-110} * 60 )); fi
WATCH_SECONDS=${WATCH_SECONDS:-180}
PUBLISH_SECONDS=${PUBLISH_SECONDS:-1800}
FIRST_PUBLISH_SECONDS=${FIRST_PUBLISH_SECONDS:-900}
DASHBOARD_OUT=${DASHBOARD_OUT:-/tmp/dealbot-dashboard/data.json}
export DESK_MODE=${DESK_MODE:-paper}
export DESK_BOT=${DESK_BOT:-gambler}
export FEED=${FEED:-coinbase}
export BLOCK_SECONDS
export LOG_DIR=logs/data

say() { echo "paper_chunk: $*"; }
DESK_ENV=(env -u TYPESAFE_API_KEY -u KALSHI_API_KEY_ID -u KALSHI_PRIVATE_KEY -u KALSHI_PROD_API_KEY_ID -u KALSHI_PROD_PRIVATE_KEY)
desk_env() { "${DESK_ENV[@]}" "$@"; }
retry_push() { for delay in 0 2 4 8 16; do [ "$delay" -gt 0 ] && sleep "$delay"; git push -q -u origin "$RUN_BRANCH" && return 0; done; return 1; }

# ---- 1. the run worktree ---------------------------------------------------------------------
git -C "$REPO" worktree prune
git -C "$REPO" fetch -q origin "$BASE_BRANCH"
if [ "$(git -C "$REPO" branch --show-current)" = "$RUN_BRANCH" ]; then
  git -C "$REPO" checkout -q "$BASE_BRANCH"   # an older session left the checkout on the run branch
fi
if [ ! -e "$RUN_DIR/.git" ]; then
  if git -C "$REPO" fetch -q origin "$RUN_BRANCH" 2>/dev/null; then
    git -C "$REPO" worktree add -q -B "$RUN_BRANCH" "$RUN_DIR" "origin/$RUN_BRANCH"
  else
    git -C "$REPO" worktree add -q -B "$RUN_BRANCH" "$RUN_DIR" "origin/$BASE_BRANCH"
  fi
fi
cd "$RUN_DIR"

sync_run() {
  git fetch -q origin "$BASE_BRANCH"
  if git fetch -q origin "$RUN_BRANCH" 2>/dev/null; then
    git merge -q --no-edit "origin/$RUN_BRANCH"
  fi
  git merge -q --no-edit "origin/$BASE_BRANCH"
  BASE_SHA=$(git rev-parse "origin/$BASE_BRANCH")
  SEEN_SHA=$BASE_SHA
  mkdir -p "$LOG_DIR"
}
sync_run

# True when the change from the merged base ($1) to a newer base ($2) can alter what the running desk
# does: anything but docs, ops scripts, tests, reports, dashboards and the shadow lab (those run fresh at
# every publish or chunk; no desk module imports them). An unreadable diff counts as a change.
desk_code_changed() {
  local files
  files=$(git diff --name-only "$1" "$2" 2>/dev/null) || return 0
  [ -n "$files" ] || return 1
  printf '%s\n' "$files" | grep -qvE '^(ops/|tests/|dashboard/|reports/|docs/|lab/|research_notes/)|\.md$'
}

# ---- 2. python and the judge -----------------------------------------------------------------
NEED="cryptography>=42"
IMPORTS="cryptography"
if [ "$JUDGE_BACKEND" = "typesafe" ]; then NEED="$NEED typesafe-sdk>=0.7.5,<0.8"; IMPORTS="$IMPORTS, typesafe_sdk"; fi
# shellcheck disable=SC2086
if ! "$VENV/bin/python" -c "import $IMPORTS" 2>/dev/null; then
  if command -v uv >/dev/null 2>&1; then
    [ -x "$VENV/bin/python" ] || uv venv -q "$VENV"
    uv pip install -q --python "$VENV/bin/python" $NEED
  else
    [ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q $NEED
  fi
fi
PY="$VENV/bin/python"

export DESK_SECRET
DESK_SECRET=$("$PY" -c 'import secrets; print(secrets.token_hex(32))')
JUDGE_PID=""
stop_judge() { if [ -n "$JUDGE_PID" ]; then kill "$JUDGE_PID" 2>/dev/null || true; wait "$JUDGE_PID" 2>/dev/null || true; JUDGE_PID=""; fi; }
DESK_PID=""
stop_desk() { if [ -n "$DESK_PID" ] && kill -0 "$DESK_PID" 2>/dev/null; then kill -TERM "$DESK_PID" 2>/dev/null || true; wait "$DESK_PID" 2>/dev/null || true; fi; DESK_PID=""; }
trap 'stop_desk; stop_judge' EXIT

# One desk per container. Until 2026-11-03 the desk was started through a shell function, so the PID
# this script killed on a restart was a wrapper shell and the desk itself kept trading next to its
# replacement, writing every decision twice into the same log. Any desk still running here is stopped
# (gracefully, then for good after a minute) before a new one starts.
stop_strays() {
  local pattern='^[^ ]*python[0-9.]* -m desk[.]run --blocks' pids  # the desk itself, never a shell that names it
  pids=$(pgrep -f "$pattern" || true)
  [ -n "$pids" ] || return 0
  say "stopping stray desk process(es): $(echo $pids)"
  kill -TERM $pids 2>/dev/null || true
  for _ in $(seq 1 60); do pgrep -f "$pattern" >/dev/null || return 0; sleep 1; done
  kill -KILL $pids 2>/dev/null || true
}

start_judge() {
  if [ "$JUDGE_BACKEND" = "demo" ]; then export JUDGE_URL="stub://demo"; return; fi
  if [ "$JUDGE_BACKEND" != "typesafe" ]; then export JUDGE_URL="stub://local"; return; fi
  if [ "$JUDGE_AUTH" = "env" ] && [ -z "${TYPESAFE_API_KEY:-}" ]; then say "TYPESAFE_API_KEY is not set (or set JUDGE_AUTH=proxy)" >&2; exit 2; fi
  export JUDGE_AUTH
  if [ ! -s "$LOG_DIR/pinned_model.txt" ]; then
    if ! "$PY" -m judge.pin_model > "$LOG_DIR/pinned_model.txt.new"; then rm -f "$LOG_DIR/pinned_model.txt.new"; say "could not pin a model" >&2; exit 2; fi
    mv "$LOG_DIR/pinned_model.txt.new" "$LOG_DIR/pinned_model.txt"
  fi
  export JEV_MODEL; JEV_MODEL=$(cat "$LOG_DIR/pinned_model.txt")
  export JUDGE_URL="http://127.0.0.1:$JUDGE_PORT"
  JUDGE_BACKEND=typesafe JUDGE_PORT=$JUDGE_PORT "$PY" -m judge.service >> "$LOG_DIR/judge.log" 2>&1 &
  JUDGE_PID=$!
  for _ in $(seq 1 30); do curl -sf --noproxy '*' "$JUDGE_URL/healthz" >/dev/null 2>&1 && return 0; sleep 1; done
  say "the judge did not come up; last lines of $LOG_DIR/judge.log:" >&2
  tail -n 20 "$LOG_DIR/judge.log" >&2
  exit 2
}

preflight() {
  if desk_env "$PY" -m desk.preflight > "$LOG_DIR/preflight.log" 2>&1; then
    say "preflight passed: $(grep -m1 '^scenario' "$LOG_DIR/preflight.log")"
  else
    say "PREFLIGHT FAILED; the desk was not started. Report:" >&2
    cat "$LOG_DIR/preflight.log" >&2
    exit 4
  fi
}

# ---- 5. publish a segment --------------------------------------------------------------------
publish() {
  local since_ms=$1
  "$PY" -m reports.chunk_summary --log-dir "$LOG_DIR" --since-ms "$since_ms" | sed 's/^/paper_chunk: /' || true
  "$PY" -m reports.daily --log-dir "$LOG_DIR" --date "$(date -u +%F)" --out "$LOG_DIR/reports" >/dev/null 2>&1 || true
  git add -f "$LOG_DIR"/events-*.jsonl "$LOG_DIR/state.json" "$LOG_DIR/trials.json" 2>/dev/null || true
  [ -s "$LOG_DIR/pinned_model.txt" ] && git add -f "$LOG_DIR/pinned_model.txt"
  git add -f "$LOG_DIR/reports" "$LOG_DIR/summaries" 2>/dev/null || true
  if ! git diff --cached --quiet; then
    git commit -q -m "paper run: ${DESK_BOT}/${FEED}/${DESK_MODE} through $(date -u +%FT%TZ) on base ${BASE_SHA:0:7}"
    retry_push || say "push failed; the commit stays local until the next segment" >&2
  fi
}

# ---- 3, 4. run until the deadline, restarting on base changes --------------------------------
START_MS=$(( $(date +%s) * 1000 ))
DEADLINE=$(( $(date +%s) + CHUNK_SECONDS ))
stop_strays
start_judge
preflight
say "branch=$RUN_BRANCH base=${BASE_SHA:0:7} mode=$DESK_MODE bot=$DESK_BOT feed=$FEED judge=$JUDGE_URL model=${JEV_MODEL:-stub} until=$(date -u -d "@$DEADLINE" +%H:%M:%SZ)"
while :; do
  LEFT=$(( DEADLINE - $(date +%s) ))
  [ "$LEFT" -ge 60 ] || break
  SEGMENT_MS=$(( $(date +%s) * 1000 ))
  stop_strays
  # a plain command, not desk_env: env execs python, so $! is the desk itself and the TERM below reaches it
  "${DESK_ENV[@]}" "$PY" -m desk.run --blocks $(( LEFT / BLOCK_SECONDS )) --state-file "$LOG_DIR/state.json" &
  DESK_PID=$!
  RESTART=""
  LAST_WATCH=$(date +%s)
  NEXT_PUBLISH=$(( $(date +%s) + FIRST_PUBLISH_SECONDS ))
  while kill -0 "$DESK_PID" 2>/dev/null; do
    sleep 5
    if [ "$(date +%s)" -ge "$NEXT_PUBLISH" ] && [ -z "$RESTART" ]; then
      NEXT_PUBLISH=$(( $(date +%s) + PUBLISH_SECONDS ))
      publish "$SEGMENT_MS"   # the desk keeps running; a line it is writing completes in the next commit
    fi
    if [ $(( $(date +%s) - LAST_WATCH )) -ge "$WATCH_SECONDS" ]; then
      LAST_WATCH=$(date +%s)
      REMOTE=$(git ls-remote origin "refs/heads/$BASE_BRANCH" 2>/dev/null | cut -f1)
      if [ -n "$REMOTE" ] && [ "$REMOTE" != "$SEEN_SHA" ] && [ -z "$RESTART" ]; then
        SEEN_SHA=$REMOTE
        if git fetch -q origin "$BASE_BRANCH" 2>/dev/null && ! desk_code_changed "$BASE_SHA" "$REMOTE"; then
          say "base moved to ${REMOTE:0:7} (docs, ops, tests, reports or dashboards only); the desk keeps running"
        else
          say "base moved to ${REMOTE:0:7}; stopping the desk after its current block to pick it up"
          RESTART=1
          kill -TERM "$DESK_PID" 2>/dev/null || true
        fi
      fi
    fi
  done
  DESK_RC=0
  wait "$DESK_PID" || DESK_RC=$?
  DESK_PID=""
  publish "$SEGMENT_MS"
  if [ -n "$RESTART" ]; then
    stop_judge
    sync_run
    start_judge
    preflight
    say "restarted on base ${BASE_SHA:0:7}"
    continue
  fi
  if [ "$DESK_RC" -ne 0 ]; then say "the desk exited with code $DESK_RC" >&2; exit 5; fi
  break
done

# ---- 6. the chunk's summary and the dashboard snapshot -----------------------------------------
"$PY" -m reports.chunk_summary --log-dir "$LOG_DIR" --since-ms "$START_MS" --out-dir "$LOG_DIR/summaries/chunks" | sed 's/^/paper_chunk: chunk /' || true
git add -f "$LOG_DIR/summaries" 2>/dev/null || true
if ! git diff --cached --quiet; then git commit -q -m "paper run: chunk summary $(date -u +%FT%TZ)"; retry_push || true; fi
mkdir -p "$(dirname "$DASHBOARD_OUT")"
"$PY" -m dashboard.export --log-dir "$LOG_DIR" --out "$DASHBOARD_OUT" | sed 's/^/paper_chunk: /' || say "dashboard export failed" >&2
say "done $(git log -1 --format='%h %s')"
