#!/bin/bash
cd /home/muatasr/.nanobot/workspace/teas-study-app
echo "=== QC START: $(date) ===" > data/kb/qc_remaining.log
python3 scripts/qc_pass.py --subject reading --delay 2.5 >> data/kb/qc_remaining.log 2>&1
echo "=== Reading DONE: $(date) ===" >> data/kb/qc_remaining.log
python3 scripts/qc_pass.py --subject science --delay 2.5 >> data/kb/qc_remaining.log 2>&1
echo "=== Science DONE: $(date) ===" >> data/kb/qc_remaining.log
python3 scripts/qc_pass.py --status >> data/kb/qc_remaining.log 2>&1
echo "=== ALL COMPLETE: $(date) ===" >> data/kb/qc_remaining.log
