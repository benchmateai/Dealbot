#!/usr/bin/env bash
# One chunk of the shadow lab: record Kalshi market data for CHUNK_MINUTES and publish each finished hour to
# the shadow-run branch. Read-only: the lab has no order code (lab/__init__.py). It runs in its own worktree
# (LAB_DIR), apart from the paper desk's run, and paces its Kalshi requests (LAB_RATE a second, backing off
# on any rate limit) because it shares the network address, and Kalshi's per-address limit, with the desk.
#
#   bash ops/lab_chunk.sh            exit 0 done, 2 setup, 5 the recorder crashed
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
LAB_BRANCH=${LAB_BRANCH:-shadow-run}
BASE_BRANCH=${BASE_BRANCH:-claude/desk-skeleton}
LAB_DIR=${LAB_DIR:-$HOME/dealbot-lab}
CHUNK_MINUTES=${CHUNK_MINUTES:-110}
LAB_RATE=${LAB_RATE:-0.25}
PUBLISH_SECONDS=${PUBLISH_SECONDS:-1800}
PY=${PY:-python3}

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

LAB_PID=""
stop_lab() { if [ -n "$LAB_PID" ] && kill -0 "$LAB_PID" 2>/dev/null; then kill -TERM "$LAB_PID" 2>/dev/null || true; wait "$LAB_PID" 2>/dev/null || true; fi; LAB_PID=""; }
trap stop_lab EXIT
# the recorder never sees a key it does not need: the paper desk's credentials are removed
env -u TYPESAFE_API_KEY "$PY" -m lab.recorder --minutes "$CHUNK_MINUTES" --data lab/data --rate "$LAB_RATE" &
LAB_PID=$!
say "recording on base $BASE_SHA for $CHUNK_MINUTES minutes at $LAB_RATE requests a second"
NEXT=$(( $(date +%s) + PUBLISH_SECONDS ))
while kill -0 "$LAB_PID" 2>/dev/null; do
  sleep 5
  if [ "$(date +%s)" -ge "$NEXT" ]; then NEXT=$(( $(date +%s) + PUBLISH_SECONDS )); publish; fi
done
RC=0
wait "$LAB_PID" || RC=$?
LAB_PID=""
publish
if [ "$RC" -ne 0 ]; then say "the recorder exited with code $RC" >&2; exit 5; fi
say "done $(git log -1 --format='%h %s')"
