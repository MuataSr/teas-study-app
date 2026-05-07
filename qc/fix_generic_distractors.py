#!/usr/bin/env python3
"""Fix generic 'None of the above' distractors in science questions.
Sends batches to local 9B for specific plausible replacements."""
import sqlite3, json, urllib.request, sys

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'
BATCH = 25


def get_generic_distractors():
    """Find science questions with 'None of the above' in wrong_answers."""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""SELECT id, question_text, correct_answer, wrong_answers
                 FROM questions 
                 WHERE subject='science' AND wrong_answers LIKE '%None of the above%'
                 ORDER BY id""")
    rows = c.fetchall()
    conn.close()
    return rows


def call_llm(prompt):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": "Output ONLY a valid JSON array. No markdown, no explanation."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.3
    }).encode()
    req = urllib.request.Request(LLM_URL, data=payload,
                                headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode()
            # Parse OpenAI envelope, extract assistant content
            envelope = json.loads(raw)
            content = envelope['choices'][0]['message']['content']
            # Strip think tags
            if '<think' in content:
                content = content.split('</think')[-1].strip()
            while '```' in content:
                content = content.replace('```json', '').replace('```', '')
            return json.loads(content.strip())
    except Exception as e:
        print(f'  LLM error: {e}')
        return None


def build_prompt(questions):
    parts = []
    for qid, qtext, correct, wrongs_json in questions:
        try:
            wrongs = json.loads(wrongs_json)
        except:
            wrongs = []
        other_wrongs = [w for w in wrongs if w != "None of the above"]
        parts.append(f"""Q{qid}:
Question: {qtext[:300]}
Correct answer: {correct[:200]}
Current wrong answers (keep these): {json.dumps(other_wrongs)}
Generate ONE specific, plausible, factually incorrect science answer to replace "None of the above".""")

    qs_text = '\n\n---\n\n'.join(parts)
    return f"""You are a TEAS 7 science exam question writer. Each question below has "None of the above" as a wrong answer — this is a lazy distractor that makes questions too easy.

For each question, generate ONE specific, plausible, factually incorrect answer that:
- Is a real science term or concept (not generic)
- Is similar in length/style to the correct answer
- Would be tempting to a student who doesn't know the material
- Is NOT "None of the above", "All of the above", or similar

Output a JSON array: [{{"id": QUESTION_ID, "replacement": "specific wrong answer"}}]

Questions:
{qs_text}

JSON array:"""


def apply_fixes(results):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    fixed = 0
    for r in results:
        if not isinstance(r, dict):
            continue
        qid = r.get('id')
        if isinstance(qid, str):
            qid = qid.lstrip('Qq')
            try:
                qid = int(qid)
            except ValueError:
                continue
        elif not isinstance(qid, int):
            continue
        replacement = r.get('replacement', '').strip()
        if not replacement:
            continue

        # Get current wrong answers
        c.execute("SELECT wrong_answers FROM questions WHERE id=?", (qid,))
        row = c.fetchone()
        if not row:
            continue
        try:
            wrongs = json.loads(row[0])
        except:
            continue

        # Replace "None of the above" with the new distractor
        new_wrongs = [replacement if w == "None of the above" else w for w in wrongs]
        c.execute("UPDATE questions SET wrong_answers=? WHERE id=?",
                  (json.dumps(new_wrongs), qid))
        fixed += 1

    conn.commit()
    conn.close()
    return fixed


def main():
    all_rows = get_generic_distractors()
    total = len(all_rows)
    print(f'Found {total} science questions with "None of the above" distractors')

    if not total:
        print('Nothing to fix.')
        return

    # Process in batches
    total_fixed = 0
    for i in range(0, total, BATCH):
        batch = all_rows[i:i+BATCH]
        batch_end = min(i + BATCH, total)
        print(f'\nBatch {i//BATCH + 1}: Q{batch[0][0]}-Q{batch[-1][0]} ({len(batch)} questions, {i}-{batch_end}/{total})')

        prompt = build_prompt(batch)
        results = call_llm(prompt)

        if not results:
            print(f'  LLM call failed, skipping batch')
            continue

        fixed = apply_fixes(results)
        total_fixed += fixed
        print(f'  Fixed {fixed}/{len(batch)} in this batch')
        print(f'  Total progress: {total_fixed}/{total} ({total_fixed*100//total}%)')

    print(f'\nDone! Fixed {total_fixed}/{total} generic distractors.')

    # Verify
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM questions WHERE subject='science' AND wrong_answers LIKE '%None of the above%'")
    remaining = c.fetchone()[0]
    conn.close()
    print(f'Remaining "None of the above": {remaining}')


if __name__ == '__main__':
    main()
