#!/usr/bin/env python3
"""Phase 1: Automated format/structural checks. No LLM needed. Resumable.
Only flags truly broken questions. Format variations go to Phase 2 LLM."""
import sqlite3, json, sys

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'

def check(qid, row):
    topic, qtext, correct, wrong, explanation, difficulty = row
    issues = []

    # 1. Missing or empty critical fields
    if not topic or not topic.strip():
        issues.append('missing_topic')
    if not qtext or len(qtext.strip()) < 5:
        issues.append(f'short_question({len(qtext) if qtext else 0})')
    if not correct or not correct.strip():
        issues.append('missing_correct')
    if not wrong or not wrong.strip():
        issues.append('missing_wrong')
    if not explanation or len(explanation.strip()) < 80:
        issues.append(f'short_explanation({len(explanation) if explanation else 0})')
    if difficulty not in ('easy', 'medium', 'hard'):
        issues.append(f'bad_difficulty({str(difficulty)[:20]})')

    passed = 1 if len(issues) == 0 else 0
    return passed, '|'.join(issues)


def run_phase1():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Reset
    c.execute('UPDATE qc_results SET phase1_passed=0, phase1_issues=""')
    conn.commit()

    c.execute('''SELECT q.id, q.subject, q.topic, q.question_text, 
                        q.correct_answer, q.wrong_answers, q.explanation, q.difficulty
                 FROM questions q ORDER BY q.id''')
    rows = c.fetchall()
    total = len(rows)
    passed = failed = 0

    c.execute("UPDATE qc_progress SET value='1' WHERE key='phase1_started'")
    c.execute("UPDATE qc_progress SET value='phase1' WHERE key='status'")
    conn.commit()

    for i, row in enumerate(rows):
        qid, subject = row[0], row[1]
        p, issues = check(qid, row[2:])
        c.execute('UPDATE qc_results SET subject=?, phase1_passed=?, phase1_issues=? WHERE question_id=?',
                  (subject, p, issues, qid))
        if p: passed += 1
        else: failed += 1
        if (i + 1) % 500 == 0 or i + 1 == total:
            conn.commit()
            print(f'  {i+1}/{total} ({passed} pass, {failed} fail)')

    c.execute("UPDATE qc_progress SET value=? WHERE key='phase1_total'", (str(total),))
    c.execute("UPDATE qc_progress SET value=? WHERE key='phase1_done'", (str(total),))
    c.execute("UPDATE qc_progress SET value='phase1_done' WHERE key='status'")
    conn.commit()

    c.execute("SELECT subject, COUNT(*) FROM qc_results WHERE phase1_passed=0 GROUP BY subject")
    print(f'\nPhase 1 done: {passed} pass, {failed} fail')
    for r in c.fetchall():
        print(f'  {r[0]}: {r[1]} failures')
    conn.close()


if __name__ == '__main__':
    run_phase1()
