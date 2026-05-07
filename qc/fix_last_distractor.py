#!/usr/bin/env python3
"""Fix the last remaining 'None of the above' distractor (ID 217)."""
import sqlite3, json, urllib.request

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'

prompt = '''Question: Which of the following correctly describes the mechanism of action of antidiuretic hormone (ADH)?
Correct answer: It increases water reabsorption in the collecting duct of the nephron.
Current wrong answers (keep these): ["ADH is released by the posterior pituitary in response to high blood osmolarity", "It makes the collecting ducts more permeable to water, allowing water to be reabsorbed back into the blood, thus concentrating the urine and decreasing blood osmolarity"]
Generate ONE specific, plausible, factually incorrect science answer to replace "None of the above". Output ONLY the replacement text, nothing else.'''

payload = json.dumps({
    "model": "openai/qwen3.5-9b",
    "messages": [
        {"role": "system", "content": "Output ONLY the replacement text. No JSON, no explanation."},
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 200,
    "temperature": 0.3
}).encode()

req = urllib.request.Request(LLM_URL, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=120) as resp:
    raw = json.loads(resp.read().decode())
    content = raw["choices"][0]["message"]["content"].strip()
    print(f"Replacement: {content}")

wrongs = [
    "ADH is released by the posterior pituitary in response to high blood osmolarity",
    "It makes the collecting ducts more permeable to water, allowing water to be reabsorbed back into the blood, thus concentrating the urine and decreasing blood osmolarity",
    content
]

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("UPDATE questions SET wrong_answers=? WHERE id=217", (json.dumps(wrongs),))
conn.commit()
c.execute("SELECT COUNT(*) FROM questions WHERE subject='science' AND wrong_answers LIKE '%None of the above%'")
remaining = c.fetchone()[0]
print(f"Remaining 'None of the above': {remaining}")
conn.close()
