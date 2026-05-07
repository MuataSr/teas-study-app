#!/usr/bin/env python3
"""Resume Phase 3 (from Q161 onward) + Phase 4 of fix_score2_math.py"""
import sqlite3, json, urllib.request, time, sys

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
LLM_URL = 'http://127.0.0.1:8082/v1/chat/completions'


def call_llm(prompt, max_tokens=512, temperature=0.3):
    payload = json.dumps({
        "model": "openai/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": "Output ONLY the requested content. No markdown, no extra text."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }).encode()
    req = urllib.request.Request(LLM_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = json.loads(resp.read().decode())
        content = raw["choices"][0]["message"]["content"].strip()
        if '<think' in content:
            content = content.split('</think')[-1].strip()
        while '```' in content:
            content = content.replace('```json', '').replace('```', '')
        return content


def extract_clean_answer(question, current_ca, wrong_answers):
    prompt = f"""A math question has its correct answer stored with extra work/steps mixed in. Extract ONLY the final numeric answer.

Question: {question}
Current (messy) correct_answer field: {current_ca}
Wrong answers: {wrong_answers}

Rules:
- Extract ONLY the final numeric answer (e.g., "$5.90" not "5 gallons cost $5.90")
- Keep any units, dollar signs, or symbols that are part of the answer
- Do NOT include calculation steps
- Output ONLY the clean answer, nothing else

Clean answer:"""
    return call_llm(prompt, max_tokens=100, temperature=0.1)


def fix_explanation(subject, question, correct, wrongs):
    prompt = f"""You are a TEAS 7 {subject} tutor. Write a clear, accurate explanation.

Question: {question}
Correct answer: {correct}
Wrong answers: {json.dumps(wrongs)}

Write a 2-4 sentence explanation that:
- States why the correct answer is right
- Briefly explains why key wrong answers are wrong
- Is factually accurate and relevant to THIS specific question

Output ONLY the explanation text:"""
    return call_llm(prompt, max_tokens=300, temperature=0.3)


def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    fixed = {"answer_cleaned": 0, "skipped": 0, "errors": 0, "explanations_fixed": 0}

    # ================================================================
    # PHASE 3 RESUME: Score-2 math — skip first 23 already processed
    # ================================================================
    print("=" * 60)
    print("PHASE 3 RESUME: Score-2 math (items 24+)")
    print("=" * 60)

    c.execute("""
        SELECT q.id, q.question_text, q.correct_answer, q.wrong_answers
        FROM qc_results qr
        JOIN questions q ON q.id = qr.question_id
        WHERE qr.phase2_score = 2 AND qr.subject = 'math'
    """)

    all_rows = c.fetchall()
    batch = 0
    for row in all_rows:
        qid, question, ca, wa_json = row
        ca = str(ca).strip()

        # Skip already-clean answers (short, no steps)
        if len(ca) <= 25 and '=' not in ca and '\n' not in ca:
            fixed["skipped"] += 1
            continue

        # Skip first 23 already processed (Q137-Q161 range done)
        if qid <= 161:
            print(f"  Q{qid}: already processed, skipping")
            fixed["skipped"] += 1
            continue

        batch += 1
        print(f"\n  [{batch}] Q{qid}: '{ca[:50]}...' → ", end="", flush=True)

        try:
            clean = extract_clean_answer(question, ca, wa_json)
            if clean and len(clean) <= 80 and clean not in ("Clean answer:", ""):
                c.execute("UPDATE questions SET correct_answer=? WHERE id=?", (clean.strip(), qid))
                conn.commit()
                print(f"'{clean.strip()}'")
                fixed["answer_cleaned"] += 1
            else:
                print(f"⚠ unusable: '{str(clean)[:50]}'")
                fixed["errors"] += 1
        except Exception as e:
            print(f"✗ {e}")
            fixed["errors"] += 1

        time.sleep(0.5)

    # ================================================================
    # PHASE 4: Fix non-math low-scores
    # ================================================================
    print("\n" + "=" * 60)
    print("PHASE 4: Non-math fixes")
    print("=" * 60)

    # Q1363: reading, score 2 — explanation about rickets (wrong topic)
    print("\n  Q1363 (reading): fixing explanation...", end=" ", flush=True)
    c.execute("SELECT question_text, correct_answer, wrong_answers FROM questions WHERE id=1363")
    row = c.fetchone()
    try:
        new_exp = fix_explanation("reading", row[0], row[1], json.loads(row[2]))
        c.execute("UPDATE questions SET explanation=? WHERE id=1363", (new_exp,))
        conn.commit()
        print("✓")
        fixed["explanations_fixed"] += 1
    except Exception as e:
        print(f"✗ {e}")

    # Q1885: english, score 0 — 'consequently' is wrong answer
    print("  Q1885 (english): fixing answer...", end=" ", flush=True)
    c.execute("SELECT question_text, correct_answer, wrong_answers FROM questions WHERE id=1885")
    row = c.fetchone()
    try:
        prompt = f"""Fix this TEAS 7 English question. The current correct answer '{row[1]}' is WRONG.

Question: {row[0]}
Current wrong answers: {row[2]}

The question describes a patient who had a reaction YESTERDAY but is stable NOW.
This is a CONTRAST (not a consequence). Choose the correct transition word.

Output as JSON: {{"answer": "the correct answer", "explanation": "why this answer is correct"}}"""
        result = call_llm(prompt, max_tokens=300, temperature=0.1)
        parsed = json.loads(result)
        c.execute("UPDATE questions SET correct_answer=?, explanation=? WHERE id=1885",
                  (parsed["answer"], parsed.get("explanation", "")))
        conn.commit()
        print(f"✓ → {parsed['answer']}")
    except Exception as e:
        print(f"✗ {e}")

    # Q1369, Q1374, Q1379: reading score 0 — re-generate explanations
    for qid in [1369, 1374, 1379]:
        print(f"  Q{qid} (reading): regenerating explanation...", end=" ", flush=True)
        c.execute("SELECT question_text, correct_answer, wrong_answers FROM questions WHERE id=?", (qid,))
        row = c.fetchone()
        try:
            new_exp = fix_explanation("reading", row[0], row[1], json.loads(row[2]))
            c.execute("UPDATE questions SET explanation=? WHERE id=?", (new_exp, qid))
            conn.commit()
            print("✓")
            fixed["explanations_fixed"] += 1
        except Exception as e:
            print(f"✗ {e}")

    # ================================================================
    # SUMMARY
    # ================================================================
    print("\n" + "=" * 60)
    print("RESUME SUMMARY")
    print("=" * 60)
    print(f"  Answers cleaned: {fixed['answer_cleaned']}")
    print(f"  Skipped (already done/clean): {fixed['skipped']}")
    print(f"  Explanations regenerated: {fixed['explanations_fixed']}")
    print(f"  Errors/unusable: {fixed['errors']}")
    conn.close()
    print("\nDone. Re-run phase2 QC to update scores.")


if __name__ == '__main__':
    main()
