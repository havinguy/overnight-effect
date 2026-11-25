#!/bin/bash
# Weekly track-forward refresh wrapper (launchd job com.harry.overnight-refresh). Added 2026-11-25.
# Runs EXACTLY: <PY> src/track_forward.py --refresh, from the repo root. It never restores, deletes or edits data;
# the only data writes are those track_forward.py --refresh itself makes (pre-refresh backup + vendor append).
# Usage: weekly_refresh.sh            real run
#        weekly_refresh.sh --dry      print command / PATH / python + import check + test notification; no refresh
set -u
REPO="/Users/harrynguyen/overnight-effect"
PY="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"   # the python3 the logger has always run on (vnstock 4.0.4, pandas 2.3.3)
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOME="${HOME:-/Users/harrynguyen}"
export LANG="en_US.UTF-8" LC_ALL="en_US.UTF-8" PYTHONIOENCODING="utf-8"
unset OVERNIGHT_LIVE   # live mode must come from the entry point (src/track_forward.py), not an env override

cd "$REPO" || exit 90
mkdir -p logs
LOG="logs/refresh_$(date -u +%Y-%m).log"
STATUS="results/refresh_status.txt"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
notify() { /usr/bin/osascript -e "display notification \"$1\" with title \"overnight-effect\"" >/dev/null 2>&1 || true; }

if [ "${1:-}" = "--dry" ]; then
  {
    echo "=== $(ts) DRY RUN (no refresh) ==="
    echo "cwd: $(pwd)"
    echo "user: $(id -un) uid $(id -u)"
    echo "PATH: $PATH"
    echo "HOME: $HOME"
    echo "command that the real run executes: $PY src/track_forward.py --refresh"
    echo "python: $("$PY" -c 'import sys; print(sys.executable, sys.version.split()[0])' 2>&1)"
    echo "import check: $("$PY" -c 'import importlib.metadata as m, vnstock, pandas; print("vnstock", m.version("vnstock"), "pandas", pandas.__version__)' 2>&1 | tail -1)"
    echo "logs/ writable: $( (touch logs/.write_test && rm -f logs/.write_test && echo yes) 2>&1)"
  } >> "$LOG" 2>&1
  notify "DRY RUN ok: launchd can run the refresh wrapper (no data touched)"
  tail -9 "$LOG"
  exit 0
fi

START="$(ts)"
TMP="$(mktemp -t overnight_refresh)"
echo "=== $START start: $PY src/track_forward.py --refresh ===" >> "$LOG"
"$PY" src/track_forward.py --refresh > "$TMP" 2>&1
RC=$?
cat "$TMP" >> "$LOG"
echo "=== $(ts) end: exit $RC ===" >> "$LOG"
{
  echo "utc_start: $START"
  echo "utc_end: $(ts)"
  echo "exit_code: $RC"
  echo "command: $PY src/track_forward.py --refresh"
  grep -E '^\[(data|check|backup)\]' "$TMP" | sed "s#$REPO/##g"
  grep -E '^Frozen boundary' "$TMP"
  echo "full log: $LOG"
} > "$STATUS"
GUARD=0; grep -qE '^\[check\] (DATA REWRITE|FAIL)' "$TMP" && GUARD=1
rm -f "$TMP"

if [ "$RC" -eq 2 ] && [ "$GUARD" -eq 1 ]; then
  notify "track_forward refresh FAILED, exit 2: old-row guard tripped. Compare with data/snapshots/pre_refresh_* before restoring anything. See logs/"
elif [ "$RC" -ne 0 ]; then
  notify "track_forward refresh FAILED, exit $RC, see logs/"
fi
exit "$RC"
