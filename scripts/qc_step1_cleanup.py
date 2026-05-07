#!/usr/bin/env python3
"""QC Step 1: Structural cleanup — no LLM needed."""
import sqlite3, json, re, shutil
from datetime import datetime

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
BACKUP = DB.replace('.db', '_pre_qc.db')

def main():
    # Backup first
    shutil.copy2(DB, BACKUP)
    print(f"Backed up to {BACKUP}")

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # ── 1. Remove duplicate questions ──
    print("\n=== 1. DUPLICATE REMOVAL ===")
    cur.execute("""
        SELECT question_text, COUNT(*) as c, MIN(id) as keep_id, GROUP_CONCAT(id) as all_ids
        FROM questions GROUP BY question_text HAVING c > 1
    """)
    dupes = cur.fetchall()
    removed = 0
    for d in dupes:
        ids = d['all_ids'].split(',')
        keep = ids[0]
        for drop_id in ids[1:]:
            cur.execute("DELETE FROM questions WHERE id = ?", (int(drop_id),))
            removed += 1
            print(f"  Dropped id={drop_id} (dup of {keep})")
    print(f"  Removed {removed} duplicates")

    # ── 2. Strip check/verification from correct_answer ──
    print("\n=== 2. CORRECT ANSWER CLEANUP ===")
    cur.execute("SELECT id, correct_answer FROM questions")
    rows = cur.fetchall()
    cleaned = 0
    for row in rows:
        ans = row['correct_answer']
        cleaned_ans = strip_check_steps(ans)
        if cleaned_ans != ans:
            cur.execute("UPDATE questions SET correct_answer = ? WHERE id = ?", (cleaned_ans, row['id']))
            cleaned += 1
            if cleaned <= 10:
                print(f"  id={row['id']}: \"{ans[:60]}...\" → \"{cleaned_ans[:60]}...\"")
    print(f"  Cleaned {cleaned} answers")

    # ── 3. Flag short explanations ──
    print("\n=== 3. SHORT EXPLANATION FLAGS ===")
    cur.execute("SELECT id, subject, LENGTH(explanation) as elen FROM questions WHERE LENGTH(explanation) < 200 ORDER BY elen ASC")
    short_rows = cur.fetchall()
    print(f"  Found {len(short_rows)} explanations <200 chars")
    for r in short_rows[:10]:
        print(f"  id={r['id']} ({r['subject']}): {r['elen']} chars")
    if len(short_rows) > 10:
        print(f"  ... and {len(short_rows)-10} more")

    # ── 4. Wrong answers contain correct answer ──
    print("\n=== 4. WRONG ANSWER VALIDATION ===")
    cur.execute("SELECT id, subject, correct_answer, wrong_answers FROM questions")
    rows = cur.fetchall()
    leakers = 0
    for row in rows:
        correct = row['correct_answer'].strip().lower()
        try:
            wrongs = json.loads(row['wrong_answers'])
        except:
            leakers += 1
            print(f"  id={row['id']}: MALFORMED JSON")
            continue
        for w in wrongs:
            w_clean = str(w).strip().lower()
            if correct in w_clean or w_clean in correct:
                if len(correct) > 3:  # skip single-char matches
                    leakers += 1
                    print(f"  id={row['id']} ({row['subject']}): correct \"{correct[:40]}\" in wrong \"{w[:40]}\"")
                    break
    if leakers == 0:
        print("  All clean — no leaks found")

    db.commit()

    # ── Final counts ──
    print("\n=== FINAL COUNTS ===")
    cur.execute("SELECT subject, COUNT(*) FROM questions GROUP BY subject ORDER BY subject")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    db.close()
    print(f"\n=== Done: {datetime.now().strftime('%c')} ===")

def strip_check_steps(ans):
    """Remove 'Check:', 'Checking:', verification lines from answer."""
    if '\n' in ans:
        # Split on newline, take first line as the actual answer
        lines = ans.split('\n')
        # First line is the answer; rest are verification
        first = lines[0].strip()
        if first:
            return first
    # Also strip common patterns like "Check:" inline
    cleaned = re.split(r'\n\s*(?:Check|Checking|Verify|Verification)\s*:', ans, flags=re.IGNORECASE)[0]
    cleaned = cleaned.strip()
    return cleaned if cleaned else ans

if __name__ == '__main__':
    main()
