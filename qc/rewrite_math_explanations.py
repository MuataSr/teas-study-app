#!/usr/bin/env python3
"""Rewrite math cluster explanations (Q194-Q202). Answer choices are fine, just fix explanations."""
import sqlite3, json, urllib.request, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'

MATH_IDS = [194, 195, 196, 197, 198, 199, 200, 201, 202]

SYSTEM = """You are a TEAS math tutor. You will receive a math question with its correct answer and wrong answers.
Your ONLY job is to write a clear, accurate explanation (250+ chars) for WHY the correct answer is right.
Include step-by-step reasoning. Do NOT mention "a common mistake is" — just explain the correct solution clearly.
Output ONLY a JSON object: {"explanation": "..."}"""


def fetch_question(qid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''SELECT id, question_text, correct_answer, wrong_answers
                  FROM questions WHERE id=?''', (qid,))
    row = c.fetchone()
    conn.close()
    return row


def build_prompt(q):
    qid, qtext, correct, wrong = q
    try:
        wrong_parsed = json.loads(wrong)
    except:
        wrong_parsed = []
    return f"""Write a clear explanation for this TEAS math question.

Question: {qtext}
Correct Answer: {correct}
Wrong Answers: {json.dumps(wrong_parsed)}

Output: {{"explanation": "..."}}"""


def call_llm(prompt):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.3
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


def save_explanation(qid, explanation):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE questions SET explanation=? WHERE id=?', (explanation, qid))
    conn.commit()
    conn.close()


def main():
    print(f'Rewriting explanations for {len(MATH_IDS)} math questions...')

    for qid in MATH_IDS:
        q = fetch_question(qid)
        prompt = build_prompt(q)
        try:
            result = call_llm(prompt)
            exp = result['explanation']
            if len(exp) < 100:
                print(f'  Q{qid}: explanation too short ({len(exp)} chars), skipping')
                continue
            save_explanation(qid, exp)
            print(f'  Q{qid}: rewritten ({len(exp)} chars)')
        except Exception as e:
            print(f'  Q{qid}: FAILED ({e})')
        time.sleep(1)

    print('Done.')


if __name__ == '__main__':
    main()
