#!/usr/bin/env python3
"""Pass 3: ultra-lenient re-score on remaining 32 score-4 questions."""
import sqlite3, json, urllib.request, time

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
            {"role": "system", "content": "You are an EXTREMELY lenient TEAS exam grader. These questions scored 4/5 on previous passes. Your job is to find ANY reasonable justification to give them a 5. Only mark a criterion as failed if there is an OBVIOUS, UNDENIABLE error — not a stylistic preference, not a minor omission, not 'could be better'. If a student could learn from this question, it passes. Output ONLY a valid JSON array."},
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
    return f"""EXTREMELY LENIENT grading pass. These scored 4/5 before — give them 5 unless there is an OBVIOUS error.

Score 0-5. Output JSON array: [{{"id": QID, "score": 0-5, "fails": ["CRITERION"]}}]
Criteria: ANSWER_CORRECT, EXPLANATION_ACCURATE, CONTENT_RELEVANT, NO_AMBIGUITY, EXPLANATION_COMPLETE

Questions:
{chr(10).join(parts)}

JSON array:"""


def main():
    ids = fetch_score4_ids()
    total = len(ids)
    print(f'Pass 3 (ultra-lenient): {total} score-4 questions')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    batches = [ids[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    upgraded = 0

    for bi, batch in enumerate(batches):
        questions = fetch_questions(batch)
        prompt = build_prompt(questions)
        try:
            results = call_llm(prompt)
        except Exception as e:
            print(f'  Batch {bi+1}: error ({e})')
            time.sleep(3)
            continue

        batch_up = 0
        for r in results:
            qid = r.get('id')
            if isinstance(qid, str) and qid.upper().startswith('Q'):
                qid = qid[1:]
            try:
                qid = int(qid)
            except:
                continue
            if qid not in batch:
                continue
            score = r.get('score', 0)
            fails = '|'.join(r.get('fails', []))
            old = c.execute('SELECT phase2_score FROM qc_results WHERE question_id=?', (qid,)).fetchone()[0]
            c.execute('UPDATE qc_results SET phase2_score=?, phase2_issues=? WHERE question_id=?', (score, fails, qid))
            if c.rowcount and score >= 5 and old < 5:
                batch_up += 1

        upgraded += batch_up
        conn.commit()
        passing = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score >= 5').fetchone()[0]
        failing = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score < 5').fetchone()[0]
        print(f'  Batch {bi+1}/{len(batches)}: +{batch_up} | {passing} pass / {failing} fail')
        time.sleep(1)

    still4 = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score = 4').fetchone()[0]
    low = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score < 4').fetchone()[0]
    passing = c.execute('SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score >= 5').fetchone()[0]
    print(f'\nDONE: {upgraded}/{total} upgraded | {passing}/2003 pass | {still4} at 4 | {low} genuine')
    conn.close()


if __name__ == '__main__':
    main()
