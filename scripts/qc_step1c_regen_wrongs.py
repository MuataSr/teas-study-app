#!/usr/bin/env python3
"""QC Step 1c: Regenerate [REPLACE_NEEDED] wrong answers via 9B model."""
import sqlite3, json, urllib.request, sys, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://localhost:8082/v1/chat/completions'

def call_llm(prompt):
    """Call local 9B model, return response text."""
    body = json.dumps({
        "model": "Qwen3.5-9B-Instruct-Q4_K_M.gguf",
        "messages": [
            {"role": "system", "content": "You generate plausible wrong answer options for multiple-choice questions. Output ONLY valid JSON arrays. No explanation."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.8
    }).encode()
    req = urllib.request.Request(LLM_URL, data=body, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read())
    return data['choices'][0]['message']['content']

def build_prompt(questions):
    """Build a prompt for a batch of questions needing wrong answers."""
    lines = []
    for i, q in enumerate(questions):
        qid, subject, topic, qtext, correct, wrongs_json = q
        wrongs = json.loads(wrongs_json)
        need_count = sum(1 for w in wrongs if w == "[REPLACE_NEEDED]")
        good_wrongs = [w for w in wrongs if w != "[REPLACE_NEEDED]"]
        
        lines.append(f"Question {i+1} (id={qid}, {subject}/{topic}):")
        lines.append(f"  Question: {qtext}")
        lines.append(f"  Correct answer: {correct}")
        lines.append(f"  Existing good wrong answers: {good_wrongs}")
        lines.append(f"  Need {need_count} new wrong answer(s)")
        lines.append("")

    lines.append("For each question, provide the replacement wrong answers as a JSON object.")
    lines.append('Format: {"Q1": ["wrong1", "wrong2"], "Q2": ["wrong1"], ...}')
    lines.append("Each wrong answer must be:")
    lines.append("- Plausible (a student might pick it)")
    lines.append("- Factually incorrect")
    lines.append("- Different from the correct answer and other wrong answers")
    lines.append("- Same format/length as the correct answer when possible")
    lines.append("- Do NOT include the correct answer or [REPLACE_NEEDED]")
    
    return "\n".join(lines)

def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Find all questions with [REPLACE_NEEDED]
    cur.execute("""
        SELECT id, subject, topic, question_text, correct_answer, wrong_answers
        FROM questions WHERE wrong_answers LIKE '%REPLACE_NEEDED%'
        ORDER BY subject, id
    """)
    questions = cur.fetchall()
    print(f"Found {len(questions)} questions with [REPLACE_NEEDED]")

    # Group into batches of 3
    batches = []
    for i in range(0, len(questions), 3):
        batches.append(questions[i:i+3])
    print(f"Processing {len(batches)} batches of 3...")

    total_fixed = 0
    errors = 0

    for batch_idx, batch in enumerate(batches):
        print(f"\n--- Batch {batch_idx+1}/{len(batches)} ---")
        for q in batch:
            print(f"  id={q['id']} ({q['subject']}/{q['topic']})")

        prompt = build_prompt(batch)
        
        try:
            raw = call_llm(prompt)
            # Strip think tags if present
            if '</think' in raw:
                raw = raw.split('</think')[-1].strip()
            # Extract JSON
            # Try to find JSON object in response
            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start == -1 or end == 0:
                print(f"  ERROR: No JSON found in response")
                print(f"  Raw: {raw[:200]}")
                errors += 1
                continue
            
            replacements = json.loads(raw[start:end])
            
            # Apply replacements
            for i, q in enumerate(batch):
                key = f"Q{i+1}"
                if key not in replacements:
                    print(f"  id={q['id']}: Missing key {key} in response")
                    errors += 1
                    continue
                
                new_wrongs = replacements[key]
                wrongs = json.loads(q['wrong_answers'])
                
                # Replace [REPLACE_NEEDED] entries in order
                replace_idx = 0
                for j, w in enumerate(wrongs):
                    if w == "[REPLACE_NEEDED]" and replace_idx < len(new_wrongs):
                        wrongs[j] = new_wrongs[replace_idx]
                        replace_idx += 1
                
                if replace_idx > 0:
                    cur.execute("UPDATE questions SET wrong_answers = ? WHERE id = ?",
                               (json.dumps(wrongs), q['id']))
                    total_fixed += replace_idx
                    print(f"  id={q['id']}: replaced {replace_idx} wrong answer(s) ✅")
                else:
                    print(f"  id={q['id']}: no replacements applied")

            db.commit()

        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
            print(f"  Raw: {raw[:300]}")
            errors += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1

        time.sleep(1)  # rate limit

    db.close()
    print(f"\n=== DONE ===")
    print(f"Total wrong answers replaced: {total_fixed}")
    print(f"Errors: {errors}")

if __name__ == '__main__':
    main()
