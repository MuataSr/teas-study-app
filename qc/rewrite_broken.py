#!/usr/bin/env python3
"""Rewrite broken questions (score <4). Batch 1: 6 clearly broken questions."""
import sqlite3, json, urllib.request, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'

# The 6 clearly broken questions
BROKEN_IDS = [666, 1229, 2069, 756, 193, 1860]

SYSTEM = """You are a TEAS exam question writer. You will receive a broken question and must rewrite it completely.
Rules:
- Output a JSON object with keys: question_text, correct_answer, wrong_answers (array of 3 strings), explanation (250+ chars)
- Question must test a real TEAS concept
- 4 answer choices (A/B/C/D format), exactly one correct
- Explanation must explain WHY the correct answer is right AND why each wrong answer is wrong
- All wrong_answers must be plausible distractors
- Use LaTeX for math: \\(\\frac{1}{2}\\) not 1/2"""


def fetch_question(qid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''SELECT id, subject, topic, question_text, correct_answer, wrong_answers, explanation, difficulty
                  FROM questions WHERE id=?''', (qid,))
    row = c.fetchone()
    conn.close()
    return row


def build_rewrite_prompt(q):
    qid, subject, topic, qtext, correct, wrong, explanation, difficulty = q
    try:
        wrong_parsed = json.loads(wrong)
    except:
        wrong_parsed = []
    return f"""BROKEN QUESTION — rewrite from scratch keeping same subject/topic/difficulty.

Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}

ORIGINAL (broken):
Question: {qtext}
Correct: {correct}
Wrong: {json.dumps(wrong_parsed)}
Explanation: {explanation}

REWRITE as a proper JSON object:
{{"question_text": "...", "correct_answer": "...", "wrong_answers": ["...", "...", "..."], "explanation": "..."}}"""


def call_llm(prompt):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.7
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


def save_rewrite(qid, data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''UPDATE questions SET question_text=?, correct_answer=?, wrong_answers=?, explanation=?
                  WHERE id=?''',
              (data['question_text'], data['correct_answer'],
               json.dumps(data['wrong_answers']), data['explanation'], qid))
    conn.commit()
    conn.close()


def main():
    print(f'Rewriting {len(BROKEN_IDS)} broken questions...')

    for qid in BROKEN_IDS:
        q = fetch_question(qid)
        prompt = build_rewrite_prompt(q)
        try:
            result = call_llm(prompt)
            # Validate
            assert 'question_text' in result and len(result['question_text']) > 20
            assert 'correct_answer' in result and len(result['correct_answer']) > 1
            assert 'wrong_answers' in result and len(result['wrong_answers']) == 3
            assert 'explanation' in result and len(result['explanation']) > 100
            save_rewrite(qid, result)
            print(f'  Q{qid}: rewritten ({len(result["explanation"])} chars explanation)')
        except Exception as e:
            print(f'  Q{qid}: FAILED ({e})')
        time.sleep(1)

    print('Done.')


if __name__ == '__main__':
    main()
