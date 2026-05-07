#!/bin/bash
cd /home/muatasr/.nanobot/workspace/teas-study-app/pipeline
python3 kb_pipeline.py reading --force editor > /tmp/kb-pipeline-reading.log 2>&1 &
