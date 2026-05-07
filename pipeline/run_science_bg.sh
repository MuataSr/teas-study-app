#!/bin/bash
# Self-daemonizing wrapper — double-forks to detach from terminal
cd /home/muatasr/.nanobot/workspace/teas-study-app/pipeline

# Clean previous run outputs if --force-all passed
if [ "$1" = "--force-all" ]; then
    rm -rf runs/science/01_* runs/science/02_* runs/science/03_* runs/science/04_* runs/science/05_* runs/science/06_* runs/science/data/science.db
    shift
fi

( python3 -u kb_pipeline.py science "$@" </dev/null >/tmp/kb-pipeline-science.log 2>&1 & )
echo "launched"
