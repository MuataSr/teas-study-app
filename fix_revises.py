#!/usr/bin/env python3
"""Fix mechanical issues on 79 revise items flagged by QC Pass 2.
Handles: explanation answer leak, format inconsistency, generic distractors.
Does NOT need LLM — uses string/template fixes."""

import json
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "kb" / "teas_unified.db"
REPORT_PATH = Path(__file__).parent / "qc_reports" / "qc_pass2_report.json"
FIX_LOG = Path(__file__).parent / "qc_reports" / "fix_revises_log.json"

# Load report to get revise items with their fix_suggestions
with open(REPORT_PATH) as f:
    report = json.load(f)

revises = [r for r in report["results"] if r["verdict"] == "revise"]
print(f"Total revise items: {len(revises)}")

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

fixes_applied = []

for r in revises:
    qid = r["id"]
    issues = r.get("issues", "")
    fix_sug = r.get("fix_suggestion", "")

    c.execute("SELECT id, subject, question_text, correct_answer, wrong_answers, explanation FROM questions WHERE id = ?", (qid,))
    row = c.fetchone()
    if not row:
        continue

    q = {
        "id": row[0], "subject": row[1], "question_text": row[2],
        "correct_answer": row[3], "wrong_answers": row[4], "explanation": row[5]
    }

    fix_detail = {"id": qid, "subject": q["subject"], "original_issues": issues[:200], "fixes": []}

    # 1. Fix "None of the above" generic distractors
    try:
        wa = json.loads(q["wrong_answers"])
        if any("none of the above" in str(w).lower() for w in wa):
            # Extract the topic from question to generate a better distractor
            # Use the existing wrong answers as templates for style
            clean_wa = [w for w in wa if "none of the above" not in w.lower()]
            if len(clean_wa) < 3:
                # Need to replace the generic one
                # Extract correct answer text from question
                ca_letter = q["correct_answer"]
                ca_text = None
                for sep in [")", "."]:
                    pattern = rf"{ca_letter}{re.escape(sep)}\s*(.+?)(?:\n[A-D][\)\.]|\Z)"
                    match = re.search(pattern, q["question_text"], re.DOTALL)
                    if match:
                        ca_text = match.group(1).strip()
                        break
                
                if ca_text:
                    # Create a plausible wrong answer by modifying the correct one
                    # Swap numbers, negate, or use a similar-looking value
                    import random
                    # Extract numbers from correct answer
                    nums = re.findall(r'\d+\.?\d*', ca_text)
                    if nums:
                        # Slightly modify the first number
                        n = float(nums[0])
                        fake_n = n + random.choice([1, 2, 3, 5, 10, -1, -2])
                        fake_answer = ca_text.replace(nums[0], str(int(fake_n) if fake_n == int(fake_n) else fake_n))
                        new_wa = [w for w in wa if "none of the above" not in w.lower()]
                        new_wa.append(fake_answer)
                        # Keep only 3
                        new_wa = new_wa[:3]
                        c.execute("UPDATE questions SET wrong_answers = ? WHERE id = ?", (json.dumps(new_wa), qid))
                        fix_detail["fixes"].append(f"Replaced 'None of the above' with '{fake_answer}'")
                    else:
                        # Non-numeric: use a negation or opposite
                        negations = {"increase": "decrease", "decrease": "increase", "gain": "loss", 
                                    "positive": "negative", "higher": "lower", "lower": "higher",
                                    "more": "less", "less": "more", "always": "never", "never": "always",
                                    "is": "is not", "are": "are not"}
                        fake_answer = ca_text
                        for orig, neg in negations.items():
                            if orig in ca_text.lower():
                                idx = ca_text.lower().index(orig)
                                fake_answer = ca_text[:idx] + neg + ca_text[idx+len(orig):]
                                break
                        new_wa = [w for w in wa if "none of the above" not in w.lower()]
                        new_wa.append(fake_answer)
                        new_wa = new_wa[:3]
                        c.execute("UPDATE questions SET wrong_answers = ? WHERE id = ?", (json.dumps(new_wa), qid))
                        fix_detail["fixes"].append(f"Replaced 'None of the above' with negation: '{fake_answer}'")
    except (json.JSONDecodeError, Exception) as e:
        pass

    # 2. Fix explanation answer leak ("The correct answer is X" or "Option A is correct")
    if q["explanation"]:
        exp = q["explanation"]
        # Check for direct answer revelation patterns
        leak_patterns = [
            r"The correct answer is [A-D]\b",
            r"Option [A-D] is (the )?correct",
            r"The answer is [A-D]\b",
            r"\bAnswer: [A-D]\b",
            r"Choice [A-D] (is|represents) the correct",
        ]
        has_leak = any(re.search(p, exp) for p in leak_patterns)
        if has_leak:
            # Remove the leak sentence
            new_exp = exp
            for p in leak_patterns:
                new_exp = re.sub(r'(?m)^.*?' + p + r'.*?\.\s*$', '', new_exp)
            # If we stripped too much, append a generic teaching prompt
            if len(new_exp.strip()) < 50:
                ca_letter = q["correct_answer"]
                new_exp = f"Think about which option best fits the question. Consider each choice carefully and eliminate the ones that don't make sense.\n\n{new_exp.strip()}"
            c.execute("UPDATE questions SET explanation = ? WHERE id = ?", (new_exp.strip(), qid))
            fix_detail["fixes"].append("Removed answer-revealing sentence from explanation")

    # 3. Fix format inconsistency (correct answer is equation vs distractors are numbers)
    if "format inconsistent" in issues.lower() or "formatting" in issues.lower():
        # Try to normalize all options to same type
        try:
            wa = json.loads(q["wrong_answers"])
            # Check if correct answer has '=' sign but distractors don't
            ca_text = None
            for sep in [")", "."]:
                pattern = rf"{q['correct_answer']}{re.escape(sep)}\s*(.+?)(?:\n[A-D][\)\.]|\Z)"
                match = re.search(pattern, q["question_text"], re.DOTALL)
                if match:
                    ca_text = match.group(1).strip()
                    break
            
            if ca_text and "=" in ca_text:
                # Extract just the value from the equation
                val = ca_text.split("=")[-1].strip()
                # Replace correct answer text in question with just the value
                new_qt = q["question_text"].replace(ca_text, val)
                c.execute("UPDATE questions SET question_text = ? WHERE id = ?", (new_qt, qid))
                fix_detail["fixes"].append(f"Normalized format: '{ca_text}' → '{val}'")
        except Exception as e:
            pass

    if fix_detail["fixes"]:
        fixes_applied.append(fix_detail)
        print(f"  ✅ ID {qid} [{q['subject']}] — {len(fix_detail['fixes'])} fixes")
    else:
        fix_detail["fixes"].append("NO_AUTO_FIX — needs LLM review")
        fixes_applied.append(fix_detail)
        print(f"  ⏭️  ID {qid} [{q['subject']}] — no mechanical fix, needs LLM")

conn.commit()
conn.close()

# Save fix log
with open(FIX_LOG, "w") as f:
    json.dump(fixes_applied, f, indent=2)

auto_fixed = sum(1 for fd in fixes_applied if "NO_AUTO_FIX" not in str(fd["fixes"]))
needs_llm = sum(1 for fd in fixes_applied if "NO_AUTO_FIX" in str(fd["fixes"]))
print(f"\n✅ Auto-fixed: {auto_fixed}")
print(f"⏭️  Needs LLM: {needs_llm}")
print(f"Fix log saved to: {FIX_LOG}")
