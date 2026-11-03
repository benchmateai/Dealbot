#!/usr/bin/env bash
# One unattended chunk of the paper desk: pull the run branch, resume from its checkpoint, run the
# judge and the desk for CHUNK_BLOCKS blocks, then commit the logs and the checkpoint and push.
# Paper only. The TypeSafe key is read from the environment by the judge (JUDGE_AUTH=env) or injected
# by the environment's proxy (JUDGE_AUTH=proxy); it is removed from the desk's environment either way.
# Nothing secret is written to the branch. The judge gets its own .venv with the SDK when needed.
#
#   RUN_BRANCH=paper-run FEED=coinbase DESK_SYMBOLS=ETH-USD CHUNK_BLOCKS=570 bash ops/paper_chunk.sh
set -euo pipefail
cd "$(dirname "$0")/.."

RUN_BRANCH=${RUN_BRANCH:-paper-run}
BASE_BRANCH=${BASE_BRANCH:-claude/desk-skeleton}   # the first chunk branches the run off this
JUDGE_AUTH=${JUDGE_AUTH:-env}                    # env: TYPESAFE_API_KEY | proxy: the environment proxy injects the key
CHUNK_BLOCKS=${CHUNK_BLOCKS:-570}            # 570 blocks of 12 s = 114 minutes
JUDGE_PORT=${JUDGE_PORT:-8787}
JUDGE_BACKEND=${JUDGE_BACKEND:-typesafe}      # typesafe | stub | demo (demo and stub need no key)
export DESK_MODE=${DESK_MODE:-paper}
export DESK_BOT=${DESK_BOT:-gambler}
export FEED=${FEED:-coinbase}
export LOG_DIR=logs/data

if git fetch -q origin "$RUN_BRANCH" 2>/dev/null; then
  git checkout -q "$RUN_BRANCH" && git pull -q --ff-only origin "$RUN_BRANCH"
else
  git fetch -q origin "$BASE_BRANCH" && git checkout -q -B "$RUN_BRANCH" "origin/$BASE_BRANCH"
fi
mkdir -p "$LOG_DIR"

export DESK_SECRET
DESK_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

PY=python3
NEED=""
[ "$JUDGE_BACKEND" = "typesafe" ] && ! python3 -c "import typesafe_sdk" 2>/dev/null && NEED="$NEED typesafe-sdk>=0.7.5,<0.8"
[ "$FEED" = "kalshi" ] && ! python3 -c "import cryptography" 2>/dev/null && NEED="$NEED cryptography>=42"
if [ -n "$NEED" ]; then
  if [ ! -x .venv/bin/python ]; then
    if command -v uv >/dev/null 2>&1; then uv venv -q .venv; else python3 -m venv .venv; fi
  fi
  # shellcheck disable=SC2086
  if command -v uv >/dev/null 2>&1; then uv pip install -q --python .venv/bin/python $NEED; else .venv/bin/pip install -q $NEED; fi
  PY=.venv/bin/python
fi
if [ "$JUDGE_BACKEND" = "typesafe" ]; then
  if [ "$JUDGE_AUTH" = "env" ] && [ -z "${TYPESAFE_API_KEY:-}" ]; then echo "paper_chunk: TYPESAFE_API_KEY is not set (or set JUDGE_AUTH=proxy)" >&2; exit 2; fi
  export JUDGE_AUTH
  if [ ! -s "$LOG_DIR/pinned_model.txt" ]; then "$PY" -m judge.pin_model > "$LOG_DIR/pinned_model.txt"; fi
  export JEV_MODEL; JEV_MODEL=$(cat "$LOG_DIR/pinned_model.txt")
  export JUDGE_URL="http://127.0.0.1:$JUDGE_PORT"
  JUDGE_BACKEND=typesafe JUDGE_PORT=$JUDGE_PORT "$PY" -m judge.service > "$LOG_DIR/judge.log" 2>&1 &
  JUDGE_PID=$!
  for _ in $(seq 1 30); do curl -sf --noproxy '*' "http://127.0.0.1:$JUDGE_PORT/healthz" >/dev/null 2>&1 && break; sleep 1; done
  trap 'kill $JUDGE_PID 2>/dev/null || true' EXIT
elif [ "$JUDGE_BACKEND" = "demo" ]; then
  export JUDGE_URL="stub://demo"
else
  export JUDGE_URL="stub://local"
fi

echo "paper_chunk: branch=$RUN_BRANCH mode=$DESK_MODE bot=$DESK_BOT feed=$FEED judge=$JUDGE_URL model=${JEV_MODEL:-stub} blocks=$CHUNK_BLOCKS"
env -u TYPESAFE_API_KEY "$PY" -m desk.run --blocks "$CHUNK_BLOCKS" --state-file "$LOG_DIR/state.json" ${DESK_FAST:+--fast} ${DESK_START_MS:+--start-ms "$DESK_START_MS"}

python3 -m reports.daily --log-dir "$LOG_DIR" --date "$(date -u +%F)" --out "$LOG_DIR/reports" >/dev/null 2>&1 || true
git add -f "$LOG_DIR"/events-*.jsonl "$LOG_DIR/state.json" "$LOG_DIR/trials.json" 2>/dev/null || true
[ -s "$LOG_DIR/pinned_model.txt" ] && git add -f "$LOG_DIR/pinned_model.txt"
git add -f "$LOG_DIR/reports" 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -q -m "paper run: chunk ending $(date -u +%FT%TZ) (${DESK_BOT}, ${FEED}, ${DESK_MODE})"
  for delay in 0 2 4 8 16; do [ "$delay" -gt 0 ] && sleep "$delay"; git push -q -u origin "$RUN_BRANCH" && break; done
fi
echo "paper_chunk: done"
