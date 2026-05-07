#!/usr/bin/env python3
"""
Fix 76 score-2 math questions by cleaning up correct_answer format.

Categories:
- 59 questions have correct_answer with steps/sentences (need LLM to extract clean answer)
- 17 questions have clean short correct_answer (skip — QC false positives)

Also fixes:
- 3 score-1 math (wrong math, correct in wrong_answers)
- 3 score-2 math with duplicate wrong answers
- Q1363 reading explanation (about rickets, wrong topic)
- Q1885 english answer (consequently → however)
"""
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
        # Strip thinking tags
        if '<think' in content:
            content = content.split('</think')[-1].strip()
        while '```' in content:
            content = content.replace('```json', '').replace('```', '')
        return content


def extract_clean_answer(question, current_ca, wrong_answers):
    """Use LLM to extract just the answer from a multi-step correct_answer field."""
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


def fix_math_fully(question, wrong_answers):
    """Re-solve a math question completely. Returns (answer, explanation)."""
    prompt = f"""Solve this TEAS 7 math problem. Show your work.

Question: {question}
Wrong answers (these are INCORRECT): {wrong_answers}

Output as JSON: {{"answer": "the correct answer (short, final value only)", "explanation": "2-3 sentence explanation"}}"""

    result = call_llm(prompt, max_tokens=512, temperature=0.1)
    try:
        return json.loads(result)
    except:
        return None


def fix_dup_wrong_answers(conn, qid):
    """Fix duplicate wrong answers by removing dupes and generating replacements."""
    c = conn.cursor()
    c.execute("SELECT correct_answer, wrong_answers FROM questions WHERE id=?", (qid,))
    row = c.fetchone()
    correct = str(row[0]).strip()
    wrongs = json.loads(row[1])

    # Remove exact duplicates
    seen = set()
    deduped = []
    for w in wrongs:
        ws = str(w).strip()
        if ws not in seen:
            seen.add(ws)
            deduped.append(ws)

    removed = len(wrongs) - len(deduped)
    if removed == 0:
        return False

    # Generate replacement distractors
    while len(deduped) < 4:
        try:
            prompt = f"""Math question: the answer is {correct}
Current wrong answers: {json.dumps(deduped)}
Generate ONE new plausible wrong answer a student might choose. Output ONLY the answer."""
            new_w = call_llm(prompt, max_tokens=80, temperature=0.3)
            if new_w and str(new_w).strip() not in seen and str(new_w).strip() != correct:
                deduped.append(str(new_w).strip())
                seen.add(str(new_w).strip())
        except:
            break

    c.execute("UPDATE questions SET wrong_answers=? WHERE id=?", (json.dumps(deduped), qid))
    conn.commit()
    return True


def fix_explanation(subject, question, correct, wrongs):
    """Regenerate explanation for a question."""
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

    fixed = {"answer_cleaned": 0, "math_resolved": 0, "dupes_fixed": 0,
             "explanations_fixed": 0, "skipped": 0, "errors": 0}

    # ================================================================
    # PHASE 1: Score-1 math — re-solve completely (3 questions)
    # ================================================================
    print("=" * 60)
    print("PHASE 1: Score-1 math (full re-solve)")
    print("=" * 60)

    for qid in [40, 46, 49]:
        c.execute("SELECT question_text, correct_answer, wrong_answers FROM questions WHERE id=?", (qid,))
        row = c.fetchone()
        print(f"\n  Q{qid}: '{row[1][:60]}' → ", end="", flush=True)

        result = fix_math_fully(row[0], row[2])
        if result:
            c.execute("UPDATE questions SET correct_answer=?, explanation=? WHERE id=?",
                      (result["answer"], result.get("explanation", ""), qid))
            conn.commit()
            print(f"✓ {result['answer']}")
            fixed["math_resolved"] += 1
        else:
            print(f"✗ FAILED")
            fixed["errors"] += 1

    # ================================================================
    # PHASE 2: Score-2 math with duplicate wrong answers (3 questions)
    # ================================================================
    print("\n" + "=" * 60)
    print("PHASE 2: Score-2 math with duplicate wrongs")
    print("=" * 60)

    c.execute("""
        SELECT q.id FROM qc_results qr
        JOIN questions q ON q.id = qr.question_id
        WHERE qr.phase2_score = 2 AND qr.subject = 'math'
    """)
    math_ids = [r[0] for r in c.fetchall()]

    for qid in math_ids:
        c.execute("SELECT wrong_answers FROM questions WHERE id=?", (qid,))
        wa = json.loads(c.fetchone()[0])
        if len(wa) != len(set(wa)):
            print(f"  Q{qid}: fixing dupes... ", end="", flush=True)
            if fix_dup_wrong_answers(conn, qid):
                print("✓")
                fixed["dupes_fixed"] += 1
            else:
                print("skipped")

    # ================================================================
    # PHASE 3: Score-2 math with messy correct_answer (59 questions)
    # ================================================================
    print("\n" + "=" * 60)
    print("PHASE 3: Score-2 math — clean up correct_answer format")
    print("=" * 60)

    c.execute("""
        SELECT q.id, q.question_text, q.correct_answer, q.wrong_answers
        FROM qc_results qr
        JOIN questions q ON q.id = qr.question_id
        WHERE qr.phase2_score = 2 AND qr.subject = 'math'
    """)

    batch = 0
    for row in c.fetchall():
        qid, question, ca, wa_json = row
        ca = str(ca).strip()

        # Skip already-clean answers (short, no steps)
        if len(ca) <= 25 and '=' not in ca and '\n' not in ca:
            fixed["skipped"] += 1
            continue

        batch += 1
        print(f"\n  [{batch}/59] Q{qid}: ", end="", flush=True)
        print(f"'{ca[:50]}...' → ", end="", flush=True)

        try:
            clean = extract_clean_answer(question, ca, wa_json)
            if clean and len(clean) <= 80:
                c.execute("UPDATE questions SET correct_answer=? WHERE id=?", (clean.strip(), qid))
                conn.commit()
                print(f"'{clean.strip()}'")
                fixed["answer_cleaned"] += 1
            else:
                print(f"⚠ unusable: '{clean[:50]}'")
                fixed["errors"] += 1
        except Exception as e:
            print(f"✗ {e}")
            fixed["errors"] += 1

        # Rate limit
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
        fixed["errors"] += 1

    # Q1885: english, score 0 — 'consequently' is wrong answer
    print("  Q1885 (english): fixing answer...", end=" ", flush=True)
    c.execute("SELECT question_text, correct_answer, wrong_answers, explanation FROM questions WHERE id=1885")
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
        fixed["math_resolved"] += 1
    except Exception as e:
        print(f"✗ {e}")
        fixed["errors"] += 1

    # Q1369, Q1374, Q1379: reading score 0 — content looks correct, re-generate explanations
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
            fixed["errors"] += 1

    # ================================================================
    # SUMMARY
    # ================================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Answers cleaned (extracted from steps): {fixed['answer_cleaned']}")
    print(f"  Math fully re-solved: {fixed['math_resolved']}")
    print(f"  Duplicate wrongs fixed: {fixed['dupes_fixed']}")
    print(f"  Explanations regenerated: {fixed['explanations_fixed']}")
    print(f"  Skipped (already clean, QC false positives): {fixed['skipped']}")
    print(f"  Errors: {fixed['errors']}")

    conn.close()
    print("\nDone. Re-run phase2 QC to update scores.")


if __name__ == '__main__':
    main()
