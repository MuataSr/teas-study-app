#!/usr/bin/env python3
"""Launch generate_questions.py in background with proper logging."""
import subprocess
import sys
import os

PYTHON = "/usr/bin/python3"
LOG = "/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/generate_all.log"
SCRIPT = "/home/muatasr/.nanobot/workspace/teas-study-app/scripts/generate_questions.py"
CWD = "/home/muatasr/.nanobot/workspace/teas-study-app"
PIDFILE = "/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/generate.pid"

log_fd = os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

proc = subprocess.Popen(
    [PYTHON, "-u", SCRIPT, "--all"],
    stdout=log_fd,
    stderr=log_fd,
    stdin=subprocess.DEVNULL,
    cwd=CWD,
    env={**os.environ, "PYTHONUNBUFFERED": "1"},
)

os.close(log_fd)

with open(PIDFILE, "w") as f:
    f.write(str(proc.pid))

print(f"PID: {proc.pid}")
