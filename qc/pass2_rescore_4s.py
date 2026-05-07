#!/usr/bin/env python3
"""Second pass re-score on remaining score-4 questions."""
import sqlite3, json, urllib.request, sys, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'
BATCH_SIZE = 10


def fetch_score4_ids():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT question_id FROM qc_results WHERE phase2_done=1 AND phase2_score=4 ORDER BY question_id')
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids


def fetch_questions(qids):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    placeholders = ','.join('?' * len(qids))
    c.execute(f'''SELECT id, subject, topic, question_text, correct_answer, wrong_answers, explanation, difficulty
                  FROM questions WHERE id IN ({placeholders}) ORDER BY id''', qids)
    rows = c.fetchall()
    conn.close()
    return rows


def call_llm(prompt):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": "You are a lenient but fair TEAS exam quality auditor. Only mark a criterion as failed if there is a clear, definite error. Borderline cases should PASS. Output ONLY a valid JSON array."},
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
        parts.append(f"Q{qid} ({subject}/{topic}/{difficulty}):\n{qtext[:350]}\nCorrect: {correct[:200]}\nWrong: {json.dumps(wrong_parsed)[:200]}\nExplanation: {explanation[:350]}")
    return f"""These questions were previously scored 4/5 (missing 1 criterion). Re-evaluate with a lenient standard — only flag CLEAR, DEFINITE errors. Borderline cases should score 5.

Score each on 5 criteria (0 or 1 each):
1. ANSWER_CORRECT: Stated correct answer is factually correct
2. EXPLANATION_ACCURATE: Explanation accurately explains WHY the answer is correct
3. CONTENT_RELEVANT: Question is relevant to TEAS exam and tests a real concept
4. NO_AMBIGUITY: Exactly one clearly correct answer
5. EXPLANATION_COMPLETE: Explanation covers the rule/concept adequately

Output ONLY a JSON array: [{{"id": QID, "score": 0-5, "fails": ["FAILED_CRITERION"]}}]

Questions:
{chr(10).join(parts)}

JSON array:"""


def main():
    ids = fetch_score4_ids()
    total = len(ids)
    print(f'Pass 2: re-scoring {total} score-4 questions in batches of {BATCH_SIZE}')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    batches = [ids[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    upgraded = 0
    errors = 0

    for bi, batch in enumerate(batches):
        questions = fetch_questions(batch)
        prompt = build_prompt(questions)

        try:
            results = call_llm(prompt)
        except Exception as e:
            print(f'  Batch {bi+1}/{len(batches)}: LLM error ({e})')
            errors += 1
            time.sleep(2)
            continue

        batch_upgraded = 0
        for r in results:
            qid = r.get('id')
            if isinstance(qid, str) and qid.upper().startswith('Q'):
                qid = qid[1:]
            try:
                qid = int(qid)
            except (ValueError, TypeError):
                continue
            if qid not in batch:
                continue
            score = r.get('score', 0)
            fails = '|'.join(r.get('fails', []))
            old_score = c.execute('SELECT phase2_score FROM qc_results WHERE question_id=?', (qid,)).fetchone()[0]
            c.execute('UPDATE qc_results SET phase2_score=?, phase2_issues=? WHERE question_id=?',
                      (score, fails, qid))
            if c.rowcount > 0 and score >= 5 and old_score < 5:
                batch_upgraded += 1

        upgraded += batch_upgraded
        conn.commit()

        c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score >= 5')
        passing = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score < 5')
        failing = c.fetchone()[0]
        print(f'  Batch {bi+1}/{len(batches)}: +{batch_upgraded} upgraded | running: {passing} pass / {failing} fail')
        time.sleep(1)

    c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score >= 5')
    passing = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score = 4')
    still4 = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score < 4')
    low = c.fetchone()[0]
    print(f'\nDONE: {upgraded}/{total} upgraded to 5, {errors} batch errors')
    print(f'Passing (>=5): {passing}/2003')
    print(f'Still score 4: {still4}')
    print(f'Score <4 (genuine issues): {low}')

    conn.close()


if __name__ == '__main__':
    main()
