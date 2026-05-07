#!/usr/bin/env bash
# TEAS Pipeline Supervisor — restarts on crash, reports progress, retries failures
# Usage: bash run_pipeline.sh [--port 8082] [--subject math]
#
# Designed for 9B model on Vulkan after 4B soldier finishes math.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
DB_PATH="$APP_DIR/data/kb/teas_unified.db"
LOG_DIR="$APP_DIR/data/kb"
SUPERVISOR_LOG="$LOG_DIR/supervisor.log"
MAX_RESTARTS=10
RESTART_DELAY=15
HEALTH_WAIT=30

# Defaults
PORT=8082
SUBJECT=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port) PORT="$2"; shift 2 ;;
        --subject) SUBJECT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SUPERVISOR_LOG"
}

# Health check — wait for model to be responsive
health_check() {
    python3 -c "
import urllib.request, json, sys
try:
    req = urllib.request.Request('http://0.0.0.0:$PORT/v1/models')
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f'OK — {len(data.get(\"data\", []))} model(s)')
        sys.exit(0)
except Exception as e:
    print(f'UNREACHABLE: {e}')
    sys.exit(1)
"
}

# Count remaining work
count_remaining() {
    local subj="${1:-}"
    python3 -c "
import sqlite3, sys
conn = sqlite3.connect('$DB_PATH')
c = conn.cursor()
if '$subj':
    c.execute('SELECT COUNT(*) FROM questions WHERE subject=? AND LENGTH(explanation) < 250', ('$subj',))
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM questions WHERE subject=? AND LENGTH(explanation) >= 250', ('$subj',))
    done = c.fetchone()[0]
    print(f'$subj: {done} explained, {total} remaining')
else:
    for s in ['reading','math','science','english']:
        c.execute('SELECT COUNT(*) FROM questions WHERE subject=? AND LENGTH(explanation) < 250', (s,))
        rem = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM questions WHERE subject=? AND LENGTH(explanation) >= 250', (s,))
        done = c.fetchone()[0]
        print(f'{s}: {done} explained, {rem} remaining')
    c.execute('SELECT COUNT(*) FROM questions WHERE subject=\"english\"', ())
    eng_total = c.fetchone()[0]
    eng_need = 500 - eng_total
    if eng_need > 0:
        print(f'english: {eng_total}/500 questions, {eng_need} still need generation')
conn.close()
"
}

# Main supervisor loop
run_subject() {
    local subj="$1"
    local script_type="$2"  # "rewrite" or "generate"
    local restarts=0

    while [ $restarts -lt $MAX_RESTARTS ]; do
        remaining=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
c = conn.cursor()
if '$subj' == 'english' and '$script_type' == 'generate':
    c.execute('SELECT 500 - COUNT(*) FROM questions WHERE subject=\"english\"')
else:
    c.execute('SELECT COUNT(*) FROM questions WHERE subject=\"'\"$subj\"'\" AND LENGTH(explanation) < 250')
print(c.fetchone()[0])
conn.close()
")

        if [ "$remaining" -eq 0 ] 2>/dev/null; then
            log "$subj ($script_type): COMPLETE — no remaining work"
            return 0
        fi

        log "$subj ($script_type): $remaining remaining, launch attempt $((restarts + 1))/$MAX_RESTARTS"

        # Health gate
        for i in $(seq 1 3); do
            if health_check > /dev/null 2>&1; then
                break
            fi
            log "  Health check failed ($i/3), waiting ${HEALTH_WAIT}s..."
            sleep $HEALTH_WAIT
        done

        if ! health_check > /dev/null 2>&1; then
            log "  FATAL: Model unreachable after 3 attempts"
            return 1
        fi

        # Run the script
        if [ "$script_type" = "rewrite" ]; then
            python3 "$SCRIPT_DIR/rewrite_explanations.py" --port "$PORT" --subject "$subj" 2>&1 | tee -a "$SUPERVISOR_LOG"
        else
            python3 "$SCRIPT_DIR/generate_questions.py" --port "$PORT" --subject "$subj" 2>&1 | tee -a "$SUPERVISOR_LOG"
        fi

        exit_code=${PIPESTATUS[0]}
        remaining_after=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
c = conn.cursor()
if '$subj' == 'english' and '$script_type' == 'generate':
    c.execute('SELECT 500 - COUNT(*) FROM questions WHERE subject=\"english\"')
else:
    c.execute('SELECT COUNT(*) FROM questions WHERE subject=\"'\"$subj\"'\" AND LENGTH(explanation) < 250')
print(c.fetchone()[0])
conn.close()
" 2>/dev/null || echo "999")

        if [ "${remaining_after:-999}" -eq 0 ] 2>/dev/null; then
            log "$subj ($script_type): COMPLETE"
            return 0
        fi

        if [ $exit_code -eq 0 ]; then
            log "$subj ($script_type): Script exited cleanly but $remaining_after remaining — relaunching"
        else
            log "$subj ($script_type): Script crashed (exit $exit_code), $remaining_after remaining — restarting in ${RESTART_DELAY}s"
            sleep $RESTART_DELAY
        fi

        restarts=$((restarts + 1))
    done

    log "$subj ($script_type): EXHAUSTED $MAX_RESTARTS restarts"
    return 1
}

# Execution plan
log "========================================="
log "TEAS Pipeline Supervisor starting"
log "Port: $PORT | Subject: ${SUBJECT:-all}"
log "========================================="

count_remaining "$SUBJECT"

if [ -n "$SUBJECT" ]; then
    case "$SUBJECT" in
        math|science|reading)
            run_subject "$SUBJECT" "rewrite"
            ;;
        english)
            # English needs generation first, then rewrite
            run_subject "$SUBJECT" "generate"
            run_subject "$SUBJECT" "rewrite"
            ;;
    esac
else
    # Full pipeline order: math rewrite → science rewrite → english gen → english rewrite
    run_subject "math" "rewrite"
    run_subject "science" "rewrite"
    run_subject "english" "generate"
    run_subject "english" "rewrite"
fi

log "========================================="
log "Pipeline complete"
count_remaining "$SUBJECT"
log "========================================="
