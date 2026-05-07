#!/bin/bash
cd /home/muatasr/.nanobot/workspace/teas-study-app/pipeline
exec python3 -u kb_pipeline.py science >> /tmp/kb-pipeline-science.log 2>&1
