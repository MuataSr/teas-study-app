#!/usr/bin/env python3
"""Re-score the 19 rewritten questions."""
import sqlite3, json, urllib.request, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'


def fetch_low_ids():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT question_id FROM qc_results WHERE phase2_done=1 AND phase2_score < 5 ORDER BY question_id')
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids


def fetch_questions(qids):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    ph = ','.join('?' * len(qids))
    c.execute(f'''SELECT id, subject, topic, question_text, correct_answer, wrong_answers, explanation, difficulty
                  FROM questions WHERE id IN ({ph}) ORDER BY id''', qids)
    rows = c.fetchall()
    conn.close()
    return rows


def call_llm(prompt):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": "You are a fair TEAS exam quality auditor. Score each question on 5 criteria (0 or 1 each): ANSWER_CORRECT, EXPLANATION_ACCURATE, CONTENT_RELEVANT, NO_AMBIGUITY, EXPLANATION_COMPLETE. Only flag CLEAR errors. Output ONLY a valid JSON array."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.1
    }).encode()
    req = urllib.request.Request(LLM_URL, data=payload,
                                headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read())
        content = result['choices'][0]['message']['content'].strip()
        if '<think' in content:
            content = content.split('</think')[-1].strip()
        while '```' in content:
            content = content.replace('```json', '').replace('```', '')
        return json.loads(content.strip())


def build_prompt(questions):
    parts = []
    for q in questions:
        qid, subject, topic, qtext, correct, wrong, explanation, difficulty = q
        try:
            wrong_parsed = json.loads(wrong)
        except:
            wrong_parsed = []
        parts.append(f"Q{qid} ({subject}/{topic}/{difficulty}):\n{qtext[:400]}\nCorrect: {correct[:200]}\nWrong: {json.dumps(wrong_parsed)[:200]}\nExplanation: {explanation[:400]}")
    return f"""Score these TEAS questions (0-5 each). Only flag CLEAR, DEFINITE errors.

Output JSON array: [{{"id": QID, "score": 0-5, "fails": ["FAILED_CRITERION"]}}]

Questions:
{chr(10).join(parts)}

JSON array:"""


def main():
    ids = fetch_low_ids()
    total = len(ids)
    print(f'Re-scoring {total} rewritten questions')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Do in 2 batches of ~10
    batches = [ids[:10], ids[10:]]
    upgraded = 0

    for bi, batch in enumerate(batches):
        if not batch:
            continue
        questions = fetch_questions(batch)
        prompt = build_prompt(questions)
        try:
            results = call_llm(prompt)
        except Exception as e:
            print(f'  Batch {bi+1}: error ({e})')
            continue

        for r in results:
            qid = r.get('id')
            if isinstance(qid, str) and qid.upper().startswith('Q'):
                qid = qid[1:]
            try:
                qid = int(qid)
            except:
                continue
            score = r.get('score', 0)
            fails = '|'.join(r.get('fails', []))
            c.execute('UPDATE qc_results SET phase2_score=?, phase2_issues=? WHERE question_id=?', (score, fails, qid))
            if score >= 5:
                upgraded += 1

        conn.commit()
        passing = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score >= 5').fetchone()[0]
        low = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score < 5').fetchone()[0]
        print(f'  Batch {bi+1}: {passing} pass / {low} fail')
        time.sleep(1)

    passing = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score >= 5').fetchone()[0]
    low = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score < 5').fetchone()[0]
    print(f'\nFINAL: {passing}/2003 passing ({100*passing/2003:.1f}%)')
    print(f'Remaining issues: {low}')

    if low > 0:
        print('\nStill failing:')
        c.execute('''SELECT qr.question_id, q.subject, q.question_text, qr.phase2_score, qr.phase2_issues
                     FROM qc_results qr JOIN questions q ON qr.question_id = q.id
                     WHERE qr.phase2_done=1 AND qr.phase2_score < 5''')
        for r in c.fetchall():
            print(f'  Q{r[0]} score={r[3]} [{r[4]}]: {r[2][:100]}')

    conn.close()


if __name__ == '__main__':
    main()
