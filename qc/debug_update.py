#!/usr/bin/env python3
"""Debug: test the actual update that phase2_llm.py does."""
import sqlite3, json, urllib.request

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'

conn = sqlite3.connect(DB)
c = conn.cursor()

# Get one question
c.execute('''SELECT id, question_text FROM questions WHERE id=506''')
q = c.fetchone()
print(f'DB question_id: {q[0]} (type: {type(q[0]).__name__})')

# Simulate LLM returning id=506
llm_id = 506
print(f'LLM returned id: {llm_id} (type: {type(llm_id).__name__})')

# Test the update
c.execute('UPDATE qc_results SET phase2_score=5, phase2_issues="", phase2_done=1 WHERE question_id=?', (llm_id,))
print(f'Rows updated: {c.rowcount}')

conn.commit()

# Verify
c.execute('SELECT question_id, phase2_done, phase2_score FROM qc_results WHERE question_id=506')
r = c.fetchone()
print(f'After update: {r}')

conn.close()
