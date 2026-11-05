#!/usr/bin/env bash
# One chunk of the shadow lab: record Kalshi market data for CHUNK_MINUTES and publish each finished hour to
# the shadow-run branch. Read-only: the lab has no order code (lab/__init__.py). It runs in its own worktree
# (LAB_DIR), apart from the paper desk's run, and paces its Kalshi requests (LAB_RATE a second, backing off
# on any rate limit) because it shares the network address, and Kalshi's per-address limit, with the desk.
#
# LAB_FEEDS picks the recorders. "rest" (the default) is the public REST recorder, for strategies A and D.
# "ws" is the live feed, for B, C, E and F: it needs the market-data key in KALSHI_PROD_API_KEY_ID /
# KALSHI_PROD_PRIVATE_KEY and runs from a virtualenv (WS_VENV) with the websockets package, made on first
# use. "rest,ws" runs both. Each recorder writes its own hour files, so one lab runner per feed can publish
# to the same branch: each merges the other's commits before it pushes.
#
# A recorder that exits early is restarted (after 30 s, up to its *_RESTARTS times a chunk); both run to the
# chunk's end time, and every stop is bounded (TERM, then KILL after STOP_GRACE seconds).
#
#   LAB_FEEDS=rest bash ops/lab_chunk.sh   exit 0 done; 2 setup (for the live feed: no key, or no virtualenv);
#                                          5 the REST recorder kept failing; 6 the live feed kept failing
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
LAB_BRANCH=${LAB_BRANCH:-shadow-run}
BASE_BRANCH=${BASE_BRANCH:-claude/desk-skeleton}
LAB_DIR=${LAB_DIR:-$HOME/dealbot-lab}
LAB_FEEDS=${LAB_FEEDS:-rest}
CHUNK_MINUTES=${CHUNK_MINUTES:-110}
LAB_RATE=${LAB_RATE:-0.25}
PUBLISH_SECONDS=${PUBLISH_SECONDS:-1800}
PY=${PY:-python3}
WS_VENV=${WS_VENV:-$HOME/dealbot-lab-venv}
WS_RATE=${WS_RATE:-0.1}
WS_RESTARTS=${WS_RESTARTS:-3}
REST_RESTARTS=${REST_RESTARTS:-3}
STOP_GRACE=${STOP_GRACE:-60}
# no recorder sees a credential it does not use: the REST one uses none, the live feed only the market-data key
LAB_ENV=(env -u TYPESAFE_API_KEY -u KALSHI_API_KEY_ID -u KALSHI_PRIVATE_KEY -u KALSHI_PROD_API_KEY_ID -u KALSHI_PROD_PRIVATE_KEY)
WS_ENV=(env -u TYPESAFE_API_KEY -u KALSHI_API_KEY_ID -u KALSHI_PRIVATE_KEY)

say() { echo "lab_chunk: $*"; }

WANT_REST=""; WANT_WS=""
case ",$LAB_FEEDS," in *,rest,*) WANT_REST=1 ;; esac
case ",$LAB_FEEDS," in *,ws,*) WANT_WS=1 ;; esac
if [ -z "$WANT_REST$WANT_WS" ]; then say "LAB_FEEDS=$LAB_FEEDS names no feed (rest, ws)" >&2; exit 2; fi
if [ -n "$WANT_WS" ] && { [ -z "${KALSHI_PROD_API_KEY_ID:-}" ] || [ -z "${KALSHI_PROD_PRIVATE_KEY:-}" ]; }; then
  say "the live feed needs KALSHI_PROD_API_KEY_ID and KALSHI_PROD_PRIVATE_KEY in this session's environment" >&2
  exit 2
fi

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

# true while this worktree has commits the remote branch lacks (or the branch does not exist yet)
ahead() { ! git rev-parse -q --verify "origin/$LAB_BRANCH" >/dev/null || [ -n "$(git rev-list -n 1 "origin/$LAB_BRANCH..HEAD")" ]; }
publish() {
  git add -f lab/data/*/*.jsonl.gz 2>/dev/null || true
  git diff --cached --quiet || git commit -q -m "shadow lab ($LAB_FEEDS): data through $(date -u +%FT%TZ) on base $BASE_SHA"
  local delay
  for delay in 0 2 4 8 16; do
    [ "$delay" -gt 0 ] && sleep "$delay"
    ahead || return 0
    # the other lab runner publishes its own files here too: take its commits first (they never touch ours)
    if git fetch -q origin "$LAB_BRANCH" 2>/dev/null && ! git merge -q --no-edit "origin/$LAB_BRANCH" >/dev/null 2>&1; then
      git merge --abort 2>/dev/null || true
      say "could not merge origin/$LAB_BRANCH; the data stays local until the next publish" >&2
      return 0
    fi
    git push -q -u origin "$LAB_BRANCH" 2>/dev/null && return 0
  done
  say "push failed; the commit stays local until the next publish" >&2
}

ws_python() {
  local py="$WS_VENV/bin/python"
  if [ -x "$py" ] && "$py" -c "import websockets, cryptography" 2>/dev/null; then echo "$py"; return 0; fi
  if command -v uv >/dev/null 2>&1; then
    uv venv -q --system-site-packages --python "$(command -v "$PY")" "$WS_VENV" >&2 && uv pip install -q --python "$py" "websockets>=14" "cryptography>=42" >&2
  else
    "$PY" -m venv --system-site-packages "$WS_VENV" >&2 && "$py" -m pip install -q "websockets>=14" "cryptography>=42" >&2
  fi
  "$py" -c "import websockets, cryptography" 2>/dev/null && echo "$py"
}

stop_pid() {
  if [ -z "$1" ] || ! kill -0 "$1" 2>/dev/null; then return 0; fi
  kill -TERM "$1" 2>/dev/null || true
  local waited=0
  while kill -0 "$1" 2>/dev/null && [ "$waited" -lt "$STOP_GRACE" ]; do sleep 1; waited=$(( waited + 1 )); done
  if kill -0 "$1" 2>/dev/null; then say "pid $1 ignored TERM for $STOP_GRACE s; killing it" >&2; kill -KILL "$1" 2>/dev/null || true; fi
  wait "$1" 2>/dev/null || true
}
LAB_PID=""
WS_PID=""
FINAL=""
# however the chunk ends (a signal included), stop the recorders and publish what they wrote
finish() { stop_pid "$WS_PID"; stop_pid "$LAB_PID"; WS_PID=""; LAB_PID=""; [ -n "$FINAL" ] || publish || true; }
trap finish EXIT
trap 'exit 143' TERM
trap 'exit 130' INT

WS_PY=""
if [ -n "$WANT_WS" ]; then
  WS_PY=$(ws_python) || WS_PY=""
  if [ -z "$WS_PY" ]; then say "could not set up $WS_VENV with websockets and cryptography" >&2; exit 2; fi
fi
END=$(( $(date +%s) + CHUNK_MINUTES * 60 ))
left() { echo $(( END - $(date +%s) )); }
start_rest() {
  [ "$(left)" -ge 60 ] || return 1
  "${LAB_ENV[@]}" "$PY" -m lab.recorder --until "$END" --data lab/data --rate "$LAB_RATE" &
  LAB_PID=$!
  say "REST recorder on base $BASE_SHA until $(date -u -d "@$END" +%H:%M:%SZ) at $LAB_RATE requests a second (pid $LAB_PID)"
}
start_ws() {
  [ "$(left)" -ge 120 ] || return 1
  "${WS_ENV[@]}" "$WS_PY" -m lab.ws_recorder --until "$END" --data lab/data --rate "$WS_RATE" &
  WS_PID=$!
  say "live feed on base $BASE_SHA until $(date -u -d "@$END" +%H:%M:%SZ) (pid $WS_PID)"
}
if [ -n "$WANT_REST" ]; then start_rest || true; fi
if [ -n "$WANT_WS" ]; then start_ws || true; fi

REST_FAILS=0
WS_FAILS=0
WS_LAST_RC=0
NEXT=$(( $(date +%s) + PUBLISH_SECONDS ))
while [ -n "$LAB_PID$WS_PID" ]; do
  sleep 5
  if [ -n "$LAB_PID" ] && ! kill -0 "$LAB_PID" 2>/dev/null; then
    RRC=0; wait "$LAB_PID" || RRC=$?; LAB_PID=""
    if [ "$RRC" -ne 0 ]; then
      REST_FAILS=$(( REST_FAILS + 1 )); say "the REST recorder exited with code $RRC (failure $REST_FAILS of $REST_RESTARTS)" >&2
      if [ "$REST_FAILS" -lt "$REST_RESTARTS" ]; then sleep 30; start_rest || true; fi
    fi
  fi
  if [ -n "$WS_PID" ] && ! kill -0 "$WS_PID" 2>/dev/null; then
    WRC=0; wait "$WS_PID" || WRC=$?; WS_PID=""; WS_LAST_RC=$WRC
    if [ "$WRC" -ne 0 ]; then
      WS_FAILS=$(( WS_FAILS + 1 )); say "the live feed exited with code $WRC (failure $WS_FAILS of $WS_RESTARTS)" >&2
      if [ "$WS_FAILS" -lt "$WS_RESTARTS" ]; then sleep 30; start_ws || true; fi
    fi
  fi
  if [ "$(left)" -lt -120 ]; then  # a recorder still running two minutes past the end
    say "stopping recorders still running after the chunk's end" >&2
    stop_pid "$WS_PID"; stop_pid "$LAB_PID"; WS_PID=""; LAB_PID=""
  fi
  if [ "$(date +%s)" -ge "$NEXT" ]; then NEXT=$(( $(date +%s) + PUBLISH_SECONDS )); publish; fi
done
FINAL=1
publish
if [ "$REST_FAILS" -ge "$REST_RESTARTS" ]; then say "the REST recorder failed $REST_FAILS times this chunk" >&2; exit 5; fi
if [ -n "$WANT_WS" ] && [ "$WS_FAILS" -ge "$WS_RESTARTS" ]; then say "the live feed failed $WS_FAILS times this chunk" >&2; exit 6; fi
# a feed that ended the chunk never having connected (3) or gone quiet (4) has failed, whatever the count
if [ -n "$WANT_WS" ] && { [ "$WS_LAST_RC" -eq 3 ] || [ "$WS_LAST_RC" -eq 4 ]; }; then say "the live feed ended the chunk with exit $WS_LAST_RC" >&2; exit 6; fi
say "done ($LAB_FEEDS) $(git log -1 --format='%h %s')"
