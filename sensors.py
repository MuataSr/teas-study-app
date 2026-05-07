#!/usr/bin/env python3
"""
TEAS Study App — DB Sensor Suite
Run before deploy or after any batch generation/rewrite.
Zero dependencies — pure Python stdlib.
Usage: python3 sensors.py [db_path]
"""

import sqlite3, json, sys, os

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(__file__), "data", "kb", "teas_unified.db"
)

# ── helpers ──────────────────────────────────────────────────
RED = "\033[91m"; GRN = "\033[92m"; YLW = "\033[93m"; RST = "\033[0m"

def ok(msg):   print(f"  {GRN}✓{RST} {msg}")
def fail(msg):  print(f"  {RED}✗{RST} {msg}")
def warn(msg):  print(f"  {YLW}!{RST} {msg}")

def count(c, sql, params=()):
    return c.execute(sql, params).fetchone()[0]

# ── sensor groups ────────────────────────────────────────────

def pre_commit(c):
    """Gate: block any question that fails these."""
    print("\n── PRE-COMMIT GUARD ──")
    total = count(c, "SELECT COUNT(*) FROM questions")
    print(f"  {total} questions loaded")

    # JSON validity
    bad = count(c, "SELECT COUNT(*) FROM questions WHERE json_valid(wrong_answers)=0")
    (ok(f"All wrong_answers valid JSON") if bad == 0
     else fail(f"{bad} questions with invalid JSON in wrong_answers"))

    # Exactly 3 distractors
    bad = count(c, "SELECT COUNT(*) FROM questions WHERE json_array_length(json(wrong_answers)) != 3")
    (ok("All wrong_answers have exactly 3 items") if bad == 0
     else fail(f"{bad} questions don't have 3 distractors"))

    # correct_answer in A/B/C/D
    bad = count(c, "SELECT COUNT(*) FROM questions WHERE correct_answer NOT IN ('A','B','C','D')")
    (ok("All correct_answer values are A/B/C/D") if bad == 0
     else fail(f"{bad} questions with invalid correct_answer"))

    # Explanation length
    bad = count(c, "SELECT COUNT(*) FROM questions WHERE LENGTH(explanation) < 250")
    (ok("All explanations ≥ 250 chars") if bad == 0
     else fail(f"{bad} explanations under 250 chars"))

    # No null/empty required fields
    nulls = 0
    for col in ("question_text", "correct_answer", "wrong_answers", "explanation", "subject", "topic"):
        n = count(c, f"SELECT COUNT(*) FROM questions WHERE {col} IS NULL OR TRIM({col})=''")
        if n: nulls += n
    (ok("No null/empty required fields") if nulls == 0
     else fail(f"{nulls} null/empty fields found"))

    # Difficulty values
    bad = count(c, "SELECT COUNT(*) FROM questions WHERE difficulty NOT IN ('easy','medium','hard')")
    (ok("All difficulty values valid") if bad == 0
     else fail(f"{bad} invalid difficulty values"))

    return bad == 0 and nulls == 0


def content_integrity(c):
    """Catch content quality issues."""
    print("\n── CONTENT INTEGRITY ──")

    # Duplicate question texts
    dupes = count(c, "SELECT COUNT(*) - COUNT(DISTINCT question_text) FROM questions")
    (ok("No duplicate question texts") if dupes == 0
     else warn(f"{dupes} duplicate question texts"))

    # Distractors matching correct answer
    # (hard to check semantically with pure SQL, but flag exact text matches)
    bad = count(c, """
        SELECT COUNT(*) FROM questions q
        WHERE EXISTS (
            SELECT 1 FROM json_each(q.wrong_answers) wa
            WHERE wa.value = q.correct_answer
        )
    """)
    (ok("No distractors match correct_answer letter") if bad == 0
     else warn(f"{bad} distractors match correct_answer letter"))

    # Single-char generic distractors
    bad = count(c, """
        SELECT COUNT(*) FROM questions q
        WHERE EXISTS (
            SELECT 1 FROM json_each(q.wrong_answers) wa
            WHERE LENGTH(wa.value) <= 1
        )
    """)
    (ok("No single-char generic distractors") if bad == 0
     else warn(f"{bad} single-char distractors (e.g. '0', '1')"))

    # "None of the above"
    bad = count(c, "SELECT COUNT(*) FROM questions WHERE wrong_answers LIKE '%None of the above%'")
    (ok('No "None of the above" distractors') if bad == 0
     else warn(f'{bad} "None of the above" distractors'))

    # Unescaped < > in question text (math symbols that could break HTML)
    bad = count(c, """
        SELECT COUNT(*) FROM questions 
        WHERE (question_text LIKE '%>%' OR question_text LIKE '%<%')
        AND question_text NOT LIKE '%&gt;%' AND question_text NOT LIKE '%&lt;%'
    """)
    (ok("No unescaped < > in question text") if bad == 0
     else warn(f"{bad} questions with < or > (may need HTML escaping)"))

    # English wrong_answers still using letter labels instead of text
    bad = count(c, """
        SELECT COUNT(*) FROM questions 
        WHERE subject='english'
        AND (
            wrong_answers LIKE '%"A"%' OR wrong_answers LIKE '%"B"%' 
            OR wrong_answers LIKE '%"C"%' OR wrong_answers LIKE '%"D"%'
            OR wrong_answers LIKE '%A. %' OR wrong_answers LIKE '%B. %'
            OR wrong_answers LIKE '%C. %' OR wrong_answers LIKE '%D. %'
        )
        AND LENGTH(wrong_answers) < 20
    """)
    (ok("English wrong_answers use option text, not letters") if bad == 0
     else warn(f"{bad} English questions may use letter labels in wrong_answers"))

    return True  # content checks are warnings, not gates


def distribution(c):
    """Verify target distribution per subject."""
    print("\n── DISTRIBUTION CHECK ──")

    subjects = c.execute("""
        SELECT subject, COUNT(*),
               SUM(CASE WHEN difficulty='easy' THEN 1 ELSE 0 END),
               SUM(CASE WHEN difficulty='medium' THEN 1 ELSE 0 END),
               SUM(CASE WHEN difficulty='hard' THEN 1 ELSE 0 END),
               COUNT(DISTINCT topic)
        FROM questions GROUP BY subject
    """).fetchall()

    all_ok = True
    for sub, total, easy, med, hard, topics in subjects:
        # Count check (500 ± 2)
        count_ok = 498 <= total <= 502
        if count_ok:
            ok(f"{sub}: {total} questions")
        else:
            fail(f"{sub}: {total} questions (target 500)")
            all_ok = False

        # Difficulty ratio (30/45/25 ± 5%)
        if total > 0:
            e_pct, m_pct, h_pct = easy/total*100, med/total*100, hard/total*100
            diff_ok = (25 <= e_pct <= 35) and (40 <= m_pct <= 50) and (20 <= h_pct <= 30)
            if diff_ok:
                ok(f"  difficulty: {e_pct:.0f}%/{m_pct:.0f}%/{h_pct:.0f}% (E/M/H)")
            else:
                warn(f"  difficulty: {e_pct:.0f}%/{m_pct:.0f}%/{h_pct:.0f}% (target 30/45/25)")

        # Topic coverage
        if topics >= 4:
            ok(f"  {topics} topics covered")
        else:
            warn(f"  only {topics} topics — consider broadening")

    return all_ok


def db_health(c):
    """Basic database structural health."""
    print("\n── DB HEALTH ──")

    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    expected = {"questions", "misconceptions", "study_topics", "english_rules"}
    missing = expected - set(table_names)
    (ok(f"All expected tables present") if not missing
     else fail(f"Missing tables: {missing}"))

    # Index check
    idxs = c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchall()
    (ok(f"{len(idxs)} custom indexes") if idxs else warn("No custom indexes — queries may be slow on large sets"))

    return not missing


# ── main ─────────────────────────────────────────────────────

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        sys.exit(2)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print(f"╔══ TEAS Sensor Suite ══╗")
    print(f"  DB: {DB_PATH}")

    results = {
        "pre_commit":      pre_commit(c),
        "content":         content_integrity(c),
        "distribution":    distribution(c),
        "db_health":       db_health(c),
    }

    conn.close()

    # Summary
    gates = [k for k, v in results.items() if k in ("pre_commit", "db_health", "distribution")]
    passed = sum(1 for k in gates if results[k])
    total = len(gates)

    print(f"\n{'═'*30}")
    if passed == total:
        print(f"  {GRN}ALL GATES PASSED ({passed}/{total}){RST}")
        print(f"  Safe to deploy ✅")
        sys.exit(0)
    else:
        print(f"  {RED}{total - passed} GATE(S) FAILED ({passed}/{total}){RST}")
        print(f"  Fix before deploying ❌")
        sys.exit(1)


if __name__ == "__main__":
    main()
