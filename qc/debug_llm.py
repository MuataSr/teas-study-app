#!/usr/bin/env python3
"""Debug: check what IDs LLM returns for a test batch."""
import sqlite3, json, urllib.request

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''SELECT id, subject, topic, question_text, correct_answer, wrong_answers, explanation, difficulty
             FROM questions WHERE id BETWEEN 506 AND 510''')
rows = c.fetchall()

parts = []
for q in rows:
    qid, subject, topic, qtext, correct, wrong, explanation, difficulty = q
    try:
        wp = json.loads(wrong)
    except:
        wp = []
    parts.append(f'Q{qid} ({subject}/{topic}/{difficulty}):\n{qtext[:300]}\nCorrect: {correct[:150]}\nWrong: {json.dumps(wp)[:150]}\nExplanation: {explanation[:300]}')

prompt = 'Score each (0-5). JSON array: [{"id": QID, "score": 0-5, "fails": []}]\n\n' + '\n\n---\n\n'.join(parts)

payload = json.dumps({
    'model': 'openai/qwen3.5-9b',
    'messages': [{'role': 'system', 'content': 'Output ONLY JSON array.'}, {'role': 'user', 'content': prompt}],
    'max_tokens': 2048, 'temperature': 0.1
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
    print('Raw LLM response:')
    print(content[:1500])
    print()
    # Try to parse
    try:
        parsed = json.loads(content)
        print('\nParsed IDs:', [r.get('id') for r in parsed])
    except:
        print('Failed to parse as JSON')
conn.close()
