#!/usr/bin/env python3
"""Fix math question explanations using local LLM."""
import sqlite3, json, urllib.request, sys, os

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://localhost:8082/v1/chat/completions'

def call_llm(prompt):
    payload = json.dumps({
        'model': 'local',
        'messages': [{'role': 'system', 'content': 'You are a TEAS math tutor. Provide clear, step-by-step explanations. Respond with JSON only, no markdown.'},
                     {'role': 'user', 'content': prompt}],
        'temperature': 0.7,
        'max_tokens': 512
    }).encode()
    req = urllib.request.Request(LLM_URL, data=payload,
                                 headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read())
    text = data['choices'][0]['message']['content']
    if '</think' in text:
        text = text.split('</think')[-1].strip()
    return text

def fix_explanation(question_text, correct_answer, wrong_answers, topic, old_explanation):
    prompt = f"""Rewrite this TEAS math explanation to be detailed (250+ chars) with step-by-step reasoning.

Rules:
- Explain WHY the correct answer is right, not just state it
- Show the calculation steps clearly
- Briefly explain why common wrong answers are wrong
- Keep it educational and clear for nursing students

Question: {question_text}
Correct Answer: {correct_answer}
Wrong Answers: {wrong_answers}
Topic: {topic}
Current explanation: {old_explanation}

Respond with JSON: {{"explanation": "your detailed explanation"}}"""

    result = call_llm(prompt)
    result = result.strip()
    if result.startswith('```'):
        result = result.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    return json.loads(result)['explanation']

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Get IDs needing explanation fix (phase2_issues mentions EXPLANATION)
    c.execute("""SELECT r.question_id FROM qc_results r 
                 JOIN questions q ON r.question_id=q.id 
                 WHERE r.subject='math' AND r.phase2_done=1 AND r.phase2_score < 4
                 AND r.phase2_issues LIKE '%EXPLANATION%'
                 ORDER BY r.phase2_score ASC""")

    ids = [row[0] for row in c.fetchall()]

    c.execute("SELECT value FROM fix_progress WHERE key='exp_fixed_ids'")
    row = c.fetchone()
    fixed = set(json.loads(row[0])) if row and row[0] else set()

    todo = [qid for qid in ids if qid not in fixed]
    print(f"Total needing explanation fix: {len(ids)}, Already fixed: {len(fixed)}, Remaining: {len(todo)}")

    if not todo:
        print("All explanations done!")
        conn.close()
        return

    batch = todo[:3]
    new_fixed = []

    for qid in batch:
        c.execute("SELECT question_text, correct_answer, wrong_answers, topic, explanation FROM questions WHERE id=?", (qid,))
        q_text, correct, wrong, topic, old_exp = c.fetchone()

        try:
            new_exp = fix_explanation(q_text, correct, wrong, topic, old_exp)
            if len(new_exp) < 150:
                print(f"  Q{qid}: explanation too short ({len(new_exp)} chars), skipping")
                continue
            c.execute("UPDATE questions SET explanation=? WHERE id=?", (new_exp, qid))
            new_fixed.append(qid)
            print(f"  Q{qid}: fixed ({topic}, {len(old_exp)}→{len(new_exp)} chars)")

        except Exception as e:
            print(f"  Q{qid}: FAILED - {e}")

    if new_fixed:
        all_fixed = fixed | set(new_fixed)
        c.execute("INSERT OR REPLACE INTO fix_progress VALUES ('exp_fixed_ids', ?)", (json.dumps(list(all_fixed)),))
        e_count = len([i for i in ids if i in all_fixed])
        c.execute("INSERT OR REPLACE INTO fix_progress VALUES ('explanations_fixed', ?)", (str(e_count),))
        conn.commit()

    print(f"Fixed this batch: {len(new_fixed)}. Total: {len(fixed) + len(new_fixed)}/{len(ids)}")
    conn.close()

if __name__ == '__main__':
    main()
