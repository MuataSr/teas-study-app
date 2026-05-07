#!/usr/bin/env python3
"""
Batch explanation rewriter for TEAS study app.
Calls local llama-server to generate detailed, evidence-based explanations.
Fully resumable — safe to re-run at any time.
"""

import sqlite3
import json
import urllib.request
import urllib.error
import time
import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'kb', 'teas_unified.db')
LOG_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'kb', 'rewrite_log.jsonl')
DEFAULT_LLM_PORT = 8082
MIN_EXPLANATION_LENGTH = 250
DELAY_BETWEEN = 0.5

PROMPT_TEMPLATE = """You are a TEAS (Test of Essential Academic Skills) exam tutor. Write a detailed explanation for this multiple-choice question.

STRICT RULES:
- Explain why the correct answer is right, citing specific evidence from the passage or question
- Explain why EACH wrong answer is wrong, citing specific evidence
- Be specific — name the option letters and briefly what they say
- Do NOT use bullet points or numbered lists
- Write in clear, concise paragraphs (3-5 sentences total)
- Target 400-600 characters
- Do NOT repeat the full question text — reference it briefly
- Do NOT use phrases like "the correct answer is correct"

Question (ID {qid}, {subject}):
{question}

Correct Answer: {correct}

Wrong Answers: {wrong}

Write the explanation now:"""


def load_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_questions(conn, subject=None):
    query = """
        SELECT id, subject, question_text, correct_answer, wrong_answers, explanation
        FROM questions
        WHERE LENGTH(explanation) < ?
    """
    params = [MIN_EXPLANATION_LENGTH]
    if subject:
        query += " AND subject = ?"
        params.append(subject)
    query += " ORDER BY subject, id"
    return conn.execute(query, params).fetchall()


def call_llm(prompt, max_retries=3):
    payload = json.dumps({
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        "temperature": 0.3,
        "top_p": 0.9,
    }).encode()

    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(LLM_URL, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read().decode()
                if not body.strip():
                    if attempt < max_retries - 1:
                        wait = (attempt + 1) * 5
                        print(f"  Retry {attempt+1}/{max_retries} in {wait}s: empty response")
                        time.sleep(wait)
                        continue
                    return None
                result = json.loads(body)
                content = result["choices"][0]["message"]["content"].strip()
                if "</think" in content:
                    content = content.split("</think")[-1].strip()
                if "<think" in content:
                    content = content.split("<think")[0].strip()
                return content
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                print(f"  Retry {attempt+1}/{max_retries} in {wait}s: {e.reason}")
                time.sleep(wait)
            else:
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                print(f"  Retry {attempt+1}/{max_retries} in {wait}s: {e}")
                time.sleep(wait)
            else:
                return None
    return None


def log_entry(qid, subject, old_len, new_len, status, note=""):
    entry = {
        "qid": qid,
        "subject": subject,
        "old_len": old_len,
        "new_len": new_len,
        "status": status,
        "note": note,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def spot_check(conn, subject, count=3):
    rows = conn.execute(
        "SELECT id, question_text, correct_answer, explanation FROM questions WHERE subject = ? AND LENGTH(explanation) >= ? ORDER BY RANDOM() LIMIT ?",
        (subject, MIN_EXPLANATION_LENGTH, count)
    ).fetchall()
    print(f"\n{'='*60}")
    print(f"SPOT CHECK: {count} random {subject} explanations")
    print(f"{'='*60}")
    for r in rows:
        q_short = r["question_text"][:80] + "..." if len(r["question_text"]) > 80 else r["question_text"]
        print(f"\n  ID {r['id']}: {q_short}")
        print(f"  Answer: {r['correct_answer']}")
        print(f"  Explanation ({len(r['explanation'])} chars): {r['explanation'][:200]}...")
    print()


def main():
    parser = argparse.ArgumentParser(description="Batch rewrite TEAS question explanations")
    parser.add_argument("--subject", choices=["reading", "english", "math", "science"], help="Only process one subject")
    parser.add_argument("--limit", type=int, default=0, help="Max questions to process (0 = all)")
    parser.add_argument("--check", action="store_true", help="Spot-check recent explanations, don't rewrite")
    parser.add_argument("--start", type=int, default=0, help="Skip first N questions (for resuming)")
    parser.add_argument("--port", type=int, default=DEFAULT_LLM_PORT, help="llama-server port (default: 8082)")
    args = parser.parse_args()

    global LLM_URL
    LLM_URL = f"http://0.0.0.0:{args.port}/v1/chat/completions"

    # Check server is alive
    try:
        req = urllib.request.Request(f"http://0.0.0.0:{args.port}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            models = json.loads(resp.read().decode())
            print(f"Server OK — {len(models.get('data', []))} model(s) available")
    except Exception as e:
        print(f"ERROR: Cannot reach llama-server: {e}")
        sys.exit(1)

    conn = load_db()

    if args.check:
        subjects = [args.subject] if args.subject else ["reading", "english", "math", "science"]
        for s in subjects:
            spot_check(conn, s)
        conn.close()
        return

    questions = list(get_questions(conn, args.subject))
    print(f"Found {len(questions)} questions with explanations < {MIN_EXPLANATION_LENGTH} chars")

    if args.subject:
        print(f"Subject filter: {args.subject}")
    if args.limit > 0:
        questions = questions[:args.limit]
        print(f"Limited to: {args.limit} questions")
    if args.start > 0:
        questions = questions[args.start:]
        print(f"Starting from offset: {args.start}")

    print(f"Processing: {len(questions)} questions\n")

    stats = {"total": len(questions), "success": 0, "failed": 0, "skipped": 0}
    start_time = time.time()

    for i, q in enumerate(questions):
        qid = q["id"]
        subject = q["subject"]
        old_len = len(q["explanation"]) if q["explanation"] else 0

        # Double-check still needs rewriting (resumable)
        current = conn.execute("SELECT LENGTH(explanation) FROM questions WHERE id=?", (qid,)).fetchone()[0]
        if current >= MIN_EXPLANATION_LENGTH:
            stats["skipped"] += 1
            continue

        try:
            wrong_text = ", ".join(json.loads(q["wrong_answers"])) if q["wrong_answers"] and q["wrong_answers"].startswith("[") else (q["wrong_answers"] or "None provided")
        except (json.JSONDecodeError, TypeError):
            wrong_text = q["wrong_answers"] or "None provided"
        prompt = PROMPT_TEMPLATE.format(
            qid=qid,
            subject=subject,
            question=q["question_text"],
            correct=q["correct_answer"],
            wrong=wrong_text,
        )

        explanation = call_llm(prompt)

        if explanation and len(explanation) >= 100:
            explanation = explanation.strip('"').strip("'").strip()
            conn.execute("UPDATE questions SET explanation = ? WHERE id = ?", (explanation, qid))
            conn.commit()
            new_len = len(explanation)
            log_entry(qid, subject, old_len, new_len, "success")
            stats["success"] += 1
            print(f"  [{i+1}/{len(questions)}] ID {qid} ({subject}): {old_len}→{new_len} chars")
        else:
            log_entry(qid, subject, old_len, 0, "failed", explanation[:100] if explanation else "no response")
            stats["failed"] += 1
            print(f"  [{i+1}/{len(questions)}] ID {qid} ({subject}): FAILED")

        if (i + 1) % 25 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (len(questions) - i - 1) / rate if rate > 0 else 0
            print(f"\n  --- Progress: {i+1}/{len(questions)} | "
                  f"OK:{stats['success']} FAIL:{stats['failed']} SKIP:{stats['skipped']} | "
                  f"{rate:.1f} q/min | ~{remaining/60:.0f} min left ---\n")

        time.sleep(DELAY_BETWEEN)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"DONE in {elapsed/60:.1f} minutes")
    print(f"  Success: {stats['success']}")
    print(f"  Failed:  {stats['failed']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Total:   {stats['total']}")
    print(f"{'='*60}")

    subjects_done = [args.subject] if args.subject else ["reading", "english", "math", "science"]
    for s in subjects_done:
        spot_check(conn, s, count=3)

    conn.close()


if __name__ == "__main__":
    main()
