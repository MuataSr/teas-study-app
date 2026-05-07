#!/usr/bin/env python3
"""Manually rewrite 4 remaining broken questions with known issues."""
import sqlite3, json, urllib.request, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'

SYSTEM = """You are a TEAS exam question writer. Output ONLY a valid JSON object with:
- "question_text": the full question with 4 labeled choices (A/B/C/D)
- "correct_answer": the letter of the correct answer (e.g. "A")
- "wrong_answers": array of 3 strings, each being a wrong answer letter
- "explanation": detailed explanation 250+ chars explaining why correct is right and each wrong is wrong
Use LaTeX for math: \\(\\frac{1}{2}\\)"""

QUESTIONS = {
    666: {
        "prompt": """Write a TEAS English question about verb tenses in a healthcare context.
The question should present 4 sentences and ask which one uses verb tenses correctly.
Include one sentence with incorrect tense sequencing (e.g., mixing past perfect with simple past incorrectly).
Make all 4 options grammatically plausible — only one should have correct tense usage.
Difficulty: medium.""",
        "subject": "english", "topic": "Verb Tenses"
    },
    756: {
        "prompt": """Write a TEAS English question about sentence revision/combining in a healthcare context.
Present 3 separate sentences about a patient and 4 options (A/B/C/D) for how to combine them.
Only ONE option should be the best combination. The other 3 should have issues (run-on, comma splice, missing info, awkward phrasing).
Difficulty: medium.""",
        "subject": "english", "topic": "Sentence Revision"
    },
    1860: {
        "prompt": """Write a TEAS Science question about pH and IV fluids for nursing.
Question: "A nurse is administering intravenous fluids. Which solution has a pH significantly less than 7.0, making it acidic?"
IMPORTANT FACTS:
- Normal saline (0.9% NaCl) pH ≈ 5.5 (acidic, NOT neutral)
- Lactated Ringer's pH ≈ 6.5 (slightly acidic)
- Dextrose 5% in Water (D5W) pH ≈ 4.0-5.0 (acidic)
- 0.45% NaCl (half-saline) pH ≈ 5.0-5.5 (acidic)
Make D5W the correct answer since it has the lowest pH. Other options should be plausible IV solutions.
Difficulty: medium.""",
        "subject": "science", "topic": "Chemistry"
    },
    193: {
        "prompt": """Write a TEAS math word problem about solving a system of equations with candy/boxes/tubes.
Context: Two students (Briana and Susan) have the same total candies.
Briana: 1 box + 2 tubes + 7 loose candies
Susan: 1 box + 1 tube + 20 loose candies
Each tube has the same number of candies. Each box has the same number of candies.
Question should ask: How many candies are in each tube?
The answer choices should be integers (A=13, B=16, C=18, D=15) — A is correct.
Show the work: subtract boxes (same), so 2T+7 = T+20, T=13.
Difficulty: medium.""",
        "subject": "math", "topic": "Equations and inequalities"
    }
}


def call_llm(prompt):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.5
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


def save(qid, data, subject, topic):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''UPDATE questions SET question_text=?, correct_answer=?, wrong_answers=?, explanation=?
                  WHERE id=?''',
              (data['question_text'], data['correct_answer'],
               json.dumps(data['wrong_answers']), data['explanation'], qid))
    conn.commit()
    conn.close()


def main():
    for qid, info in QUESTIONS.items():
        print(f'Rewriting Q{qid} ({info["subject"]}/{info["topic"]})...')
        try:
            result = call_llm(info['prompt'])
            # Validate structure
            qt = result.get('question_text', '')
            ca = result.get('correct_answer', '')
            wa = result.get('wrong_answers', [])
            exp = result.get('explanation', '')
            assert len(qt) > 50, f"question too short: {len(qt)}"
            assert len(ca) <= 3, f"answer should be a letter: {ca}"
            assert len(wa) == 3, f"need 3 wrong answers, got {len(wa)}"
            assert len(exp) > 100, f"explanation too short: {len(exp)}"

            save(qid, result, info['subject'], info['topic'])
            print(f'  ✓ Saved ({len(exp)} chars)')
        except Exception as e:
            print(f'  ✗ FAILED: {e}')
        time.sleep(1)
    print('Done.')


if __name__ == '__main__':
    main()
