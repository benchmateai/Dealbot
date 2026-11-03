#!/usr/bin/env bash
# One chunk of the shadow lab: record Kalshi market data for CHUNK_MINUTES and publish each finished hour to
# the shadow-run branch. Read-only: the lab has no order code (lab/__init__.py). It runs in its own worktree
# (LAB_DIR), apart from the paper desk's run, and paces its Kalshi requests (LAB_RATE a second, backing off
# on any rate limit) because it shares the network address, and Kalshi's per-address limit, with the desk.
#
# Two recorders: the public REST one (strategies A and D) always, and the live-feed one (B, C, E, F) when the
# session has the market-data key in KALSHI_PROD_API_KEY_ID / KALSHI_PROD_PRIVATE_KEY. The live feed runs from
# a virtualenv (WS_VENV) with the websockets package, made on first use; each recorder writes its own files.
#
#   bash ops/lab_chunk.sh            exit 0 done, 2 setup, 5 the REST recorder crashed, 6 the live feed kept failing
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
LAB_BRANCH=${LAB_BRANCH:-shadow-run}
BASE_BRANCH=${BASE_BRANCH:-claude/desk-skeleton}
LAB_DIR=${LAB_DIR:-$HOME/dealbot-lab}
CHUNK_MINUTES=${CHUNK_MINUTES:-110}
LAB_RATE=${LAB_RATE:-0.25}
PUBLISH_SECONDS=${PUBLISH_SECONDS:-1800}
PY=${PY:-python3}
WS_VENV=${WS_VENV:-$HOME/dealbot-lab-venv}
WS_RATE=${WS_RATE:-0.1}
WS_RESTARTS=${WS_RESTARTS:-3}
# no recorder sees a credential it does not use: the REST one uses none, the live feed only the market-data key
LAB_ENV=(env -u TYPESAFE_API_KEY -u KALSHI_API_KEY_ID -u KALSHI_PRIVATE_KEY -u KALSHI_PROD_API_KEY_ID -u KALSHI_PROD_PRIVATE_KEY)
WS_ENV=(env -u TYPESAFE_API_KEY -u KALSHI_API_KEY_ID -u KALSHI_PRIVATE_KEY)

say() { echo "lab_chunk: $*"; }
retry_push() { for delay in 0 2 4 8 16; do [ "$delay" -gt 0 ] && sleep "$delay"; git push -q -u origin "$LAB_BRANCH" && return 0; done; return 1; }

git -C "$REPO" worktree prune
git -C "$REPO" fetch -q origin "$BASE_BRANCH"
if [ ! -e "$LAB_DIR/.git" ]; then
  if git -C "$REPO" fetch -q origin "$LAB_BRANCH" 2>/dev/null; then
    git -C "$REPO" worktree add -q -B "$LAB_BRANCH" "$LAB_DIR" "origin/$LAB_BRANCH"
  else
    git -C "$REPO" worktree add -q -B "$LAB_BRANCH" "$LAB_DIR" "origin/$BASE_BRANCH"
  fi
fi
cd "$LAB_DIR"
git fetch -q origin "$BASE_BRANCH"
if git fetch -q origin "$LAB_BRANCH" 2>/dev/null; then git merge -q --no-edit "origin/$LAB_BRANCH"; fi
git merge -q --no-edit "origin/$BASE_BRANCH"
BASE_SHA=$(git rev-parse --short "origin/$BASE_BRANCH")

publish() {
  git add -f lab/data/*/*.jsonl.gz 2>/dev/null || true
  if ! git diff --cached --quiet; then
    git commit -q -m "shadow lab: data through $(date -u +%FT%TZ) on base $BASE_SHA"
    retry_push || say "push failed; the commit stays local until the next publish" >&2
  fi
}

ws_python() {
  local py="$WS_VENV/bin/python"
  if [ -x "$py" ] && "$py" -c "import websockets, cryptography" 2>/dev/null; then echo "$py"; return 0; fi
  if command -v uv >/dev/null 2>&1; then
    uv venv -q --system-site-packages --python "$(command -v "$PY")" "$WS_VENV" >&2 && uv pip install -q --python "$py" "websockets>=13" "cryptography>=42" >&2
  else
    "$PY" -m venv --system-site-packages "$WS_VENV" >&2 && "$py" -m pip install -q "websockets>=13" "cryptography>=42" >&2
  fi
  "$py" -c "import websockets, cryptography" 2>/dev/null && echo "$py"
}

stop_pid() { if [ -n "$1" ] && kill -0 "$1" 2>/dev/null; then kill -TERM "$1" 2>/dev/null || true; wait "$1" 2>/dev/null || true; fi; }
LAB_PID=""
WS_PID=""
trap 'stop_pid "$WS_PID"; stop_pid "$LAB_PID"' EXIT
END=$(( $(date +%s) + CHUNK_MINUTES * 60 ))
"${LAB_ENV[@]}" "$PY" -m lab.recorder --minutes "$CHUNK_MINUTES" --data lab/data --rate "$LAB_RATE" &
LAB_PID=$!
say "recording on base $BASE_SHA for $CHUNK_MINUTES minutes at $LAB_RATE requests a second"

WS_PY=""
WS_FAILS=0
if [ -n "${KALSHI_PROD_API_KEY_ID:-}" ] && [ -n "${KALSHI_PROD_PRIVATE_KEY:-}" ]; then
  WS_PY=$(ws_python) || WS_PY=""
  if [ -z "$WS_PY" ]; then say "could not set up $WS_VENV with websockets; the live feed (B, C, E, F) is off this chunk" >&2; WS_FAILS=$WS_RESTARTS; fi
else
  say "no market-data key in this session's environment; the live feed (B, C, E, F) is off"
fi
start_ws() {
  local minutes=$(( (END - $(date +%s)) / 60 ))
  [ "$minutes" -ge 5 ] || return 1
  "${WS_ENV[@]}" "$WS_PY" -m lab.ws_recorder --minutes "$minutes" --data lab/data --rate "$WS_RATE" &
  WS_PID=$!
  say "live feed recording for $minutes minutes (pid $WS_PID)"
}
if [ -n "$WS_PY" ]; then start_ws || true; fi

NEXT=$(( $(date +%s) + PUBLISH_SECONDS ))
while kill -0 "$LAB_PID" 2>/dev/null; do
  sleep 5
  if [ -n "$WS_PID" ] && ! kill -0 "$WS_PID" 2>/dev/null; then
    WRC=0; wait "$WS_PID" || WRC=$?; WS_PID=""
    if [ "$WRC" -ne 0 ]; then
      WS_FAILS=$(( WS_FAILS + 1 )); say "the live feed exited with code $WRC (failure $WS_FAILS of $WS_RESTARTS)" >&2
      if [ "$WS_FAILS" -lt "$WS_RESTARTS" ]; then sleep 30; start_ws || true; fi
    fi
  fi
  if [ "$(date +%s)" -ge "$NEXT" ]; then NEXT=$(( $(date +%s) + PUBLISH_SECONDS )); publish; fi
done
RC=0
wait "$LAB_PID" || RC=$?
LAB_PID=""
if [ -n "$WS_PID" ]; then
  for _ in $(seq 1 60); do kill -0 "$WS_PID" 2>/dev/null || break; sleep 1; done  # it ends on its own a moment later
  stop_pid "$WS_PID"; WS_PID=""
fi
publish
if [ "$RC" -ne 0 ]; then say "the REST recorder exited with code $RC" >&2; exit 5; fi
if [ "$WS_FAILS" -ge "$WS_RESTARTS" ] && [ -n "${KALSHI_PROD_API_KEY_ID:-}" ]; then say "the live feed failed $WS_FAILS times this chunk" >&2; exit 6; fi
say "done $(git log -1 --format='%h %s')"
