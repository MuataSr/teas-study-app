#!/bin/bash
cd /home/muatasr/.nanobot/workspace/teas-study-app
python3 -u scripts/generate_questions.py --all >> data/kb/generate_all.log 2>&1
