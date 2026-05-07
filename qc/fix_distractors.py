#!/usr/bin/env python3
"""Fix math question distractors using Gemma 4 via Google AI Studio."""
import sqlite3, json, urllib.request, sys, os

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://localhost:8082/v1/chat/completions'

def call_llm(prompt):
    payload = json.dumps({
        'model': 'local',
        'messages': [{'role': 'system', 'content': 'You are a TEAS math question expert. Always respond with valid JSON only, no markdown.'},
                     {'role': 'user', 'content': prompt}],
        'temperature': 0.7,
        'max_tokens': 512
    }).encode()
    req = urllib.request.Request(LLM_URL, data=payload,
                                 headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read())
    text = data['choices'][0]['message']['content']
    # Strip think tags if present
    if '</think' in text:
        text = text.split('</think')[-1].strip()
    return text

def fix_distractors(question_text, correct_answer, topic, difficulty):
    prompt = f"""You are a TEAS math question expert. Given this question, generate 4 plausible wrong answers.

Rules:
- Wrong answers must be mathematically related (common mistakes, miscalculations)
- All answers must be plain numbers or simple expressions — NO images, NO diagrams, NO fraction boxes
- Include common wrong answers from calculation errors
- Match the format of the correct answer (decimal if correct is decimal, fraction if fraction, etc.)

Question: {question_text}
Correct Answer: {correct_answer}
Topic: {topic}
Difficulty: {difficulty}

Respond with JSON: {{"wrong_answers": ["ans1", "ans2", "ans3", "ans4"]}}"""

    result = call_llm(prompt)
    # Extract JSON from response
    result = result.strip()
    if result.startswith('```'):
        result = result.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    return json.loads(result)['wrong_answers']

def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Get IDs needing distractor fix
    c.execute("""SELECT r.question_id FROM qc_results r 
                 JOIN questions q ON r.question_id=q.id 
                 WHERE r.subject='math' AND r.phase2_done=1 AND r.phase2_score < 4
                 ORDER BY r.phase2_score ASC""")

    ids = [row[0] for row in c.fetchall()]
    # Get already-fixed IDs
    c.execute("SELECT value FROM fix_progress WHERE key='fixed_ids'")
    row = c.fetchone()
    fixed = set(json.loads(row[0])) if row and row[0] else set()

    todo = [qid for qid in ids if qid not in fixed]
    print(f"Total: {len(ids)}, Already fixed: {len(fixed)}, Remaining: {len(todo)}")

    if not todo:
        print("All done!")
        conn.close()
        return

    # Process batch
    batch_size = 3
    batch = todo[:batch_size]
    new_fixed = []

    for qid in batch:
        c.execute("SELECT question_text, correct_answer, wrong_answers, topic, difficulty FROM questions WHERE id=?", (qid,))
        q_text, correct, wrong, topic, diff = c.fetchone()

        try:
            new_wrong = fix_distractors(q_text, correct, topic, diff)
            # Validate: all plain text
            for w in new_wrong:
                if any(bad in str(w) for bad in ['[Image]', '----', '\\n\\n', '\\n +']):
                    print(f"  Q{qid}: bad distractor detected, skipping")
                    raise ValueError("Bad distractor content")

            c.execute("UPDATE questions SET wrong_answers=? WHERE id=?", (json.dumps(new_wrong), qid))
            new_fixed.append(qid)
            print(f"  Q{qid}: fixed ({topic})")

        except Exception as e:
            print(f"  Q{qid}: FAILED - {e}")

    # Update progress
    if new_fixed:
        all_fixed = fixed | set(new_fixed)
        c.execute("INSERT OR REPLACE INTO fix_progress VALUES ('fixed_ids', ?)", (json.dumps(list(all_fixed)),))
        d_count = len([i for i in ids if i in all_fixed])
        c.execute("INSERT OR REPLACE INTO fix_progress VALUES ('distractors_fixed', ?)", (str(d_count),))
        conn.commit()

    print(f"Fixed this batch: {len(new_fixed)}. Total fixed: {len(fixed) + len(new_fixed)}/{len(ids)}")
    conn.close()

if __name__ == '__main__':
    main()
