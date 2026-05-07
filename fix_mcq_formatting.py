#!/usr/bin/env python3
"""Fix MCQ formatting issues in all subjects.

Handles:
  1. Space-separated options → split into individual lines (math: 80, reading: 37)
  2. Duplicate options in reading questions (459) → deduplicate, keep first occurrence
  3. Duplicate options in math/science/english → deduplicate
  4. Missing correct option (reading: 40, math: ~70) → extract from explanation

Usage:
  python3 fix_mcq_formatting.py          # dry run
  python3 fix_mcq_formatting.py --apply  # update database
"""

import sqlite3
import json
import re
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "kb", "teas_unified.db")


def parse_all_options(question_text):
    """Parse options from question text, handling all formats."""
    lines = question_text.strip().split("\n")
    options = []

    for line in lines:
        stripped = line.strip()

        # Line-separated: each option on its own line
        if re.match(r'^[A-D][\).]', stripped):
            options.append(stripped)
        elif re.search(r'[A-D]\)', stripped):
            # Space-separated on one line: "A) text  B) text  C) text  D) text"
            parts = re.split(r'(?=\s+[A-D]\))', stripped)
            for part in parts:
                part = part.strip()
                if re.match(r'^[A-D]\)', part):
                    options.append(part)

    return options


def deduplicate_options(options, correct_answer):
    """Remove duplicate options, keeping the best version of each letter."""
    by_letter = {}
    for opt in options:
        m = re.match(r'^([A-D])[\).]\s*(.*)', opt.strip())
        if m:
            letter = m.group(1)
            text = m.group(2).strip()
            if letter in by_letter:
                # Keep the longer version (more likely to be the real option)
                existing_text = by_letter[letter]
                if len(text) > len(existing_text):
                    by_letter[letter] = text
                # But if one is an explanation (starts with lowercase or "wrong"/"because"),
                # prefer the non-explanation version
                if re.match(r'^[a-z]|^wrong|^because', existing_text, re.IGNORECASE) and not re.match(r'^[a-z]|^wrong|^because', text, re.IGNORECASE):
                    by_letter[letter] = text
                elif re.match(r'^[a-z]|^wrong|^because', text, re.IGNORECASE) and not re.match(r'^[a-z]|^wrong|^because', existing_text, re.IGNORECASE):
                    pass  # keep existing
            else:
                by_letter[letter] = text

    return by_letter


def extract_correct_option_from_explanation(explanation, correct_letter):
    """Try to extract the correct option text from the explanation."""
    if not explanation:
        return None

    first_sentence = re.split(r'[.!?]', explanation)[0].strip()

    # Pattern: "...because [correct option text]..."
    m = re.search(r'\bbecause\s+(.+)', first_sentence, re.IGNORECASE)
    if m:
        text = m.group(1).strip()
        # Clean trailing clauses
        text = re.sub(r',\s+(?:unlike|whereas|while|although|however|compared|ensuring|minimizing|unlike).*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text)
        if 15 < len(text) < 120:
            return text

    # Pattern: "[Subject] is [adjective] because..." → use the subject + because clause
    m = re.match(r'^(.+?)\s+is\s+\w+\s+because\s+(.+)', first_sentence, re.IGNORECASE)
    if m:
        subject = m.group(1).strip()
        reason = m.group(2).strip()
        text = f"{subject} because {reason}"
        text = re.sub(r',\s+(?:unlike|whereas|while|although|however|compared|ensuring|minimizing).*$', '', text, flags=re.IGNORECASE)
        if 15 < len(text) < 120:
            return text

    return None


def fix_question(r):
    """Fix a question's MCQ formatting. Returns (fixed_question_text, fixed_correct_answer) or None if OK."""
    options = parse_all_options(r["question_text"])
    correct = r["correct_answer"]

    by_letter = deduplicate_options(options, correct)

    # Check if correct answer letter has an option
    if correct in ["A", "B", "C", "D"] and correct not in by_letter:
        # Try to extract from explanation
        explanation = r["explanation"] if "explanation" in r.keys() else ""
        extracted = extract_correct_option_from_explanation(explanation, correct)
        if extracted:
            by_letter[correct] = extracted

    # Check we have at least 3 options
    if len(by_letter) < 3:
        return None  # Can't fix

    # Check if correct answer is still valid
    if correct in ["A", "B", "C", "D"] and correct not in by_letter:
        return None  # Can't fix - missing correct option

    # Rebuild question text: keep non-option lines, append clean options
    lines = r["question_text"].strip().split("\n")
    non_option_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^[A-D][\).]', stripped):
            break  # Stop at first option line
        elif re.search(r'[A-D]\)', stripped) and len(re.findall(r'[A-D]\)', stripped)) >= 2:
            break  # Stop at space-separated options line
        non_option_lines.append(line)

    # Build new options section
    new_options = []
    for letter in ["A", "B", "C", "D"]:
        if letter in by_letter:
            new_options.append(f"{letter}) {by_letter[letter]}")

    new_q = "\n".join(non_option_lines).rstrip() + "\n" + "\n".join(new_options)
    return new_q, correct


def main():
    apply = "--apply" in sys.argv

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    rows = db.execute("SELECT * FROM questions").fetchall()

    fixed = 0
    cant_fix = 0
    already_ok = 0
    errors = []

    for r in rows:
        options = parse_all_options(r["question_text"])
        by_letter = deduplicate_options(options, r["correct_answer"])
        correct = r["correct_answer"]

        # Determine if this question needs fixing
        needs_fix = False

        # Check for space-separated options on single line
        for line in r["question_text"].strip().split("\n"):
            if re.match(r'^[A-D]\)', line.strip()) and len(re.findall(r'[A-D]\)', line.strip())) >= 2:
                needs_fix = True
                break

        # Check for duplicate option texts
        option_texts = list(by_letter.values())
        if len(option_texts) != len(set(option_texts)):
            needs_fix = True

        # Check for missing correct option
        if correct in ["A", "B", "C", "D"] and correct not in by_letter:
            needs_fix = True

        if not needs_fix:
            already_ok += 1
            continue

        result = fix_question(r)
        if result is None:
            cant_fix += 1
            errors.append(r["id"])
        else:
            fixed += 1
            if apply:
                new_q, new_correct = result
                db.execute("""
                    UPDATE questions
                    SET question_text = ?, correct_answer = ?
                    WHERE id = ?
                """, (new_q, new_correct, r["id"]))

    print(f"Already OK: {already_ok}")
    print(f"Fixed: {fixed}")
    print(f"Can't fix: {cant_fix}")

    if errors:
        print(f"\nCan't fix IDs (first 20): {errors[:20]}")

    if apply:
        db.commit()
        print("\nChanges applied!")

    # Final count
    rows2 = db.execute("SELECT * FROM questions").fetchall()
    final_ok = 0
    final_issues = {}
    for r in rows2:
        options = parse_all_options(r["question_text"])
        by_letter = deduplicate_options(options, r["correct_answer"])
        correct = r["correct_answer"]

        issue = None
        if len(by_letter) < 4:
            issue = f"only {len(by_letter)} options"
        elif correct in ["A", "B", "C", "D"] and correct not in by_letter:
            issue = f"correct {correct} missing"

        if issue:
            final_issues[issue] = final_issues.get(issue, 0) + 1
        else:
            final_ok += 1

    print(f"\nFinal: {final_ok}/{len(rows2)} questions have valid MCQ format")
    if final_issues:
        for issue, count in sorted(final_issues.items(), key=lambda x: -x[1]):
            print(f"  {issue}: {count}")

    db.close()


if __name__ == "__main__":
    main()
