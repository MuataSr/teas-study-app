#!/usr/bin/env python3
import sqlite3
c = sqlite3.connect('/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db')
cur = c.cursor()

print("=== qc_results schema ===")
for col in cur.execute('PRAGMA table_info(qc_results)').fetchall():
    print(col)

print("\n=== phase2_done distribution ===")
for r in cur.execute('SELECT phase2_done, COUNT(*) FROM qc_results GROUP BY phase2_done').fetchall():
    print(r)

print("\n=== qc_progress ===")
for r in cur.execute('SELECT * FROM qc_progress').fetchall():
    print(r)

print("\n=== sample phase2_done rows ===")
for r in cur.execute('SELECT question_id, phase2_done, phase2_score FROM qc_results WHERE phase2_done=1 LIMIT 5').fetchall():
    print(r)
if not cur.execute('SELECT question_id FROM qc_results WHERE phase2_done=1 LIMIT 1').fetchone():
    print("No phase2_done=1 rows found")

c.close()
