#!/usr/bin/env python3
"""Debug: trace exactly what phase2_llm.py does for one batch."""
import sqlite3, json, urllib.request

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'

# Step 1: get_next_batch
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''SELECT q.id, q.subject, q.topic, q.question_text, 
                    q.correct_answer, q.wrong_answers, q.explanation, q.difficulty
             FROM questions q
             JOIN qc_results qc ON q.id = qc.question_id
             WHERE qc.phase1_passed = 1 AND qc.phase2_done = 0
             ORDER BY q.subject, q.id
             LIMIT 3''')
rows = c.fetchall()
print(f'Got {len(rows)} rows')
print(f'Row IDs: {[r[0] for r in rows]}')

# Step 2: build prompt (truncated)
parts = []
for q in rows:
    qid, subject, topic, qtext, correct, wrong, explanation, difficulty = q
    try:
        wrong_parsed = json.loads(wrong)
    except:
        wrong_parsed = []
    parts.append(f'Q{qid} ({subject}/{topic}/{difficulty}):\n{qtext[:300]}\nCorrect: {correct[:150]}\nWrong: {json.dumps(wrong_parsed)[:150]}\nExplanation: {explanation[:300]}')

prompt = 'Score (0-5). JSON: [{"id": QID, "score": 0-5, "fails": []}]\n\n' + '\n\n---\n\n'.join(parts)

# Step 3: call LLM
payload = json.dumps({
    'model': 'openai/qwen3.5-9b',
    'messages': [
        {'role': 'system', 'content': 'Output ONLY a valid JSON array. No markdown fences, no explanation.'},
        {'role': 'user', 'content': prompt}
    ],
    'max_tokens': 2048,
    'temperature': 0.1
}).encode()

req = urllib.request.Request(
    'http://127.0.0.1:8082/v1/chat/completions',
    data=payload, headers={'Content-Type': 'application/json'}, method='POST'
)
with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read())
    content = result['choices'][0]['message']['content'].strip()
    if '<think' in content:
        content = content.split('</think')[-1].strip()
    while '```' in content:
        content = content.replace('```json', '').replace('```', '')
    content = content.strip()
    print(f'\nLLM response: {content[:500]}')

results = json.loads(content)
print(f'\nParsed results: {results}')
print(f'LLM IDs: {[r.get("id") for r in results]}')
print(f'LLM ID types: {[type(r.get("id")).__name__ for r in results]}')

# Step 4: update
saved = 0
for r in results:
    qid = r.get('id')
    score = r.get('score', 0)
    fails = '|'.join(r.get('fails', []))
    if qid:
        c.execute('UPDATE qc_results SET phase2_score=?, phase2_issues=?, phase2_done=1 WHERE question_id=?', (score, fails, qid))
        saved += 1
        print(f'  Updated Q{qid}: rowcount={c.rowcount}')

conn.commit()

# Step 5: verify
batch_ids = [r[0] for r in rows]
c.execute(f'SELECT question_id, phase2_done, phase2_score FROM qc_results WHERE question_id IN ({",".join(str(i) for i in batch_ids)})')
for r in c.fetchall():
    print(f'  Verify Q{r[0]}: done={r[1]} score={r[2]}')

conn.close()
