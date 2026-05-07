#!/usr/bin/env python3
"""Phase 2: LLM-based QC. Resumable. Processes one batch per run.
Increased batch to 50 for throughput (~3min per batch)."""
import sqlite3, json, subprocess, sys, time, urllib.request

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
BATCH_SIZE = 25

def get_next_batch():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''SELECT q.id, q.subject, q.topic, q.question_text, 
                        q.correct_answer, q.wrong_answers, q.explanation, q.difficulty
                 FROM questions q
                 JOIN qc_results qc ON q.id = qc.question_id
                 WHERE qc.phase1_passed = 1 AND qc.phase2_done = 0
                 ORDER BY q.subject, q.id
                 LIMIT ?''', (BATCH_SIZE,))
    rows = c.fetchall()

    c.execute("SELECT COUNT(*) FROM qc_results WHERE phase1_passed=1 AND phase2_done=0")
    remaining = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM qc_results WHERE phase1_passed=1 AND phase2_done=1")
    done = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM qc_results WHERE phase1_passed=0")
    p1fail = c.fetchone()[0]

    conn.close()
    return rows, remaining, done, p1fail


def build_prompt(questions):
    parts = []
    for q in questions:
        qid, subject, topic, qtext, correct, wrong, explanation, difficulty = q
        try:
            wrong_parsed = json.loads(wrong)
        except:
            wrong_parsed = []
        parts.append(f"""Q{qid} ({subject}/{topic}/{difficulty}):
{qtext[:400]}
Correct: {correct[:200]}
Wrong: {json.dumps(wrong_parsed)[:200]}
Explanation: {explanation[:400]}""")

    questions_text = '\n\n---\n\n'.join(parts)

    return f"""You are a TEAS exam quality auditor. Score each question on 5 criteria (0 or 1 each):

1. ANSWER_CORRECT: The stated correct answer is actually factually correct
2. EXPLANATION_ACCURATE: The explanation accurately explains WHY the answer is correct
3. CONTENT_RELEVANT: Question is relevant to TEAS exam and tests a real concept
4. NO_AMBIGUITY: Question has exactly one clearly correct answer
5. EXPLANATION_COMPLETE: Explanation covers the rule/concept, not just "X is correct"

Output ONLY a JSON array. Each element: {{"id": QUESTION_ID, "score": 0-5, "fails": ["criteria_that_failed"]}}

Questions:
{questions_text}

JSON array:"""


def call_llm(prompt):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": "Output ONLY a valid JSON array. No markdown fences, no explanation."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8192,
        "temperature": 0.1
    }).encode()

    req = urllib.request.Request(
        'http://127.0.0.1:8082/v1/chat/completions',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            result = json.loads(resp.read())
            content = result['choices'][0]['message']['content'].strip()
            # Strip think tags
            if '<think' in content:
                content = content.split('</think')[-1].strip()
            # Strip markdown fences - handle ```json and ``` variants
            while '```' in content:
                content = content.replace('```json', '').replace('```', '')
            content = content.strip()
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f'  JSON parse error: {e}')
        return None
    except Exception as e:
        print(f'  LLM error: {e}')
        return None


def score_batch():
    rows, remaining, done, p1fail = get_next_batch()

    if not rows:
        return 'complete', 0, 0, 0, 0

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE qc_progress SET value='1' WHERE key='phase2_started'")
    c.execute("UPDATE qc_progress SET value='phase2' WHERE key='status'")
    c.execute("UPDATE qc_progress SET value=? WHERE key='current_batch'", 
              (f'Q{rows[0][0]}-Q{rows[-1][0]}',))
    c.execute("UPDATE qc_progress SET value=? WHERE key='phase2_total'", (str(done + remaining),))
    c.execute("UPDATE qc_progress SET value=? WHERE key='phase2_done'", (str(done),))
    conn.commit()
    conn.close()

    print(f'Batch Q{rows[0][0]}-Q{rows[-1][0]}: {len(rows)} questions ({remaining} remaining)')

    prompt = build_prompt(rows)
    results = call_llm(prompt)

    if not results:
        print('  LLM call failed, will retry next run')
        return 'error', len(rows), remaining, done, p1fail

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    saved = 0
    for r in results:
        qid = r.get('id')
        # Normalize: strip "Q" prefix and convert to int
        if isinstance(qid, str) and qid.upper().startswith('Q'):
            qid = qid[1:]
        try:
            qid = int(qid)
        except (ValueError, TypeError):
            continue
        score = r.get('score', 0)
        fails = '|'.join(r.get('fails', []))
        c.execute('''UPDATE qc_results SET phase2_score=?, phase2_issues=?, phase2_done=1
                     WHERE question_id=?''', (score, fails, qid))
        if c.rowcount > 0:
            saved += 1
    conn.commit()

    # Check if any in batch were missed
    batch_ids = set(row[0] for row in rows)
    saved_ids = set()
    for r in results:
        qid = r.get('id')
        if isinstance(qid, str) and qid.upper().startswith('Q'):
            qid = qid[1:]
        try:
            saved_ids.add(int(qid))
        except (ValueError, TypeError):
            pass
    missed = batch_ids - saved_ids
    if missed:
        print(f'  Missed {len(missed)} IDs, will retry')

    conn.close()
    print(f'  Scored {saved}/{len(rows)}')
    return 'ok', len(rows), remaining, done, p1fail


if __name__ == '__main__':
    status, batch_size, remaining, done, p1fail = score_batch()
    print(f'Status: {status} | Batch: {batch_size} | Remaining: {remaining} | Done: {done}')
