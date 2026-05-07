#!/usr/bin/env python3
"""Fork-and-launch: daemonizes the question generation script properly."""
import os
import sys
import time

# Fork to background
pid = os.fork()
if pid > 0:
    # Parent — wait briefly for child to start, then exit
    time.sleep(0.5)
    print(f"Launched generator PID {pid}")
    sys.exit(0)

# Child — detach from terminal
os.setsid()
os.close(0)  # stdin
os.close(1)  # stdout
os.close(2)  # stderr

log_fd = os.open("/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/generate_all.log",
                  os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
os.dup2(log_fd, 1)
os.dup2(log_fd, 2)
if log_fd > 2:
    os.close(log_fd)

os.chdir("/home/muatasr/.nanobot/workspace/teas-study-app")
os.execvp(sys.executable, [sys.executable, "scripts/generate_questions.py", "--all"])
