#!/usr/bin/env python3
"""Clean the math question bank: delete duplicates, fix wrong_answers, set difficulty."""

import sqlite3
import json
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'kb', 'math.db')
DIRTY_ROWS_PATH = '/tmp/math_dirty_rows.json'

TOPIC_DIFFICULTY = {
    'Number sense': 'easy',
    'Number Operations': 'easy',
    'Ratios and proportional reasoning': 'medium',
    'Properties of number and operations': 'medium',
    'Variables, expressions, and operations': 'medium',
    'Equations and inequalities': 'medium',
    'Patterns, relationships, and functions': 'hard',
    'Algebraic representations': 'hard',
}

DUPLICATE_IDS = [14, 48, 107, 209, 147, 5, 6]


def extract_numeric_value(text: str) -> float | None:
    """Extract the final numeric answer from a correct_answer string."""
    text = text.strip()
    # Try last line first
    lines = text.split('\n')
    last_line = lines[-1].strip()

    # Pattern: "N unit" at start of last line (e.g. "15 giants", "54 ml", "44 items")
    m = re.match(r'^(-?[\d.]+)\s', last_line)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Pattern: "N%" 
    m = re.match(r'^([\d.]+)%$', last_line)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Pattern: just a number like "65", "20", "116"
    m = re.match(r'^(-?[\d.]+)$', last_line)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Pattern: expression ending with "=N unit" (e.g. "=16 cm", "=300")
    m = re.search(r'=\s*(-?[\d.]+)\s*(\w*)$', last_line)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Pattern: "x=N" (e.g. "x=-2")
    m = re.match(r'^x\s*=\s*(-?[\d.]+)$', last_line)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass

    # Look for last number in entire text that looks like a final answer
    # Find all numbers in the last line
    nums = re.findall(r'(?<![a-zA-Z/])(-?\d+\.?\d*)(?![a-zA-Z/])', last_line)
    if nums:
        try:
            return float(nums[-1])
        except ValueError:
            pass

    return None


def has_unit(correct_answer: str) -> str:
    """Check if correct_answer ends with a unit suffix."""
    lines = correct_answer.strip().split('\n')
    last = lines[-1].strip()
    m = re.match(r'^-?[\d.]+\s+(\S+)', last)
    if m:
        unit = m.group(1)
        # Don't treat common math symbols as units
        if unit in ('x', 'y', 'n', 'f(x)', '+', '-'):
            return ''
        return unit
    return ''


def has_percent(correct_answer: str) -> bool:
    """Check if correct_answer is a percentage."""
    return '%' in correct_answer.strip()


def generate_wrong_answers(correct_answer: str) -> list[str]:
    """Generate 3 short wrong answers for a given correct_answer."""
    ca = correct_answer.strip()

    # --- Long explanation/description (>100 chars) ---
    if len(ca) > 100:
        # Check if it's about shapes/graphs
        shape_keywords = ['quadrilateral', 'parallelogram', 'triangle', 'circle',
                          'graph', 'line', 'plot', 'scatter', 'linear', 'exponential',
                          'curved', 'straight']
        is_shape = any(kw in ca.lower() for kw in shape_keywords)
        if is_shape:
            return ["A triangle", "A circle", "A straight line"]
        else:
            return ["0", "It cannot be determined", "None of the above"]

    # --- Try to extract a numeric value ---
    unit = has_unit(ca)
    is_pct = has_percent(ca)
    val = extract_numeric_value(ca)

    if val is not None:
        wrongs = []

        # ±1 or ±10% off
        if val == int(val) and val > 0:
            # Off by 1
            wrongs.append(str(int(val) + 1))
            # Common arithmetic error (e.g. half, double)
            if val % 2 == 0:
                wrongs.append(str(int(val) // 2))
            else:
                wrongs.append(str(int(val) * 2))
            # Different number
            wrongs.append(str(int(val) + 5))
        elif val > 0:
            # Decimal values
            offset = round(val * 0.1, 2) if val * 0.1 >= 0.01 else 1
            wrongs.append(str(round(val + offset, 2)))
            wrongs.append(str(round(val * 2, 2)))
            wrongs.append(str(round(val - offset, 2) if val - offset > 0 else round(val + 5, 2)))
        else:
            # Negative or zero
            wrongs.append(str(int(val) - 1))
            wrongs.append(str(abs(int(val))))
            wrongs.append("0")

        # Deduplicate and ensure none match correct
        seen = set()
        result = []
        for w in wrongs:
            if w not in seen:
                seen.add(w)
                result.append(w)

        # Append unit/percent if needed
        if unit:
            result = [f"{w} {unit}" for w in result]
        elif is_pct:
            result = [f"{w}%" for w in result]

        # Ensure none equal the displayed correct answer
        result = [w for w in result if w.strip() != ca.strip() and w.strip() != ca.split('\n')[-1].strip()]
        while len(result) < 3:
            result.append(str(int(val or 0) + len(result) * 3 + 7))

        return result[:3]

    # --- Non-numeric short answers (expressions like "24x-18", "h+10", "Sometimes true") ---
    # These are conceptual answers - generate plausible alternatives
    ca_lower = ca.lower()

    # Variable expressions
    if re.match(r'^[a-z]\s*[+\-]=?\d', ca_lower) or re.match(r'^\d[a-z]', ca_lower):
        # Extract the expression
        expr = ca.strip()
        # Generate variants
        variants = []
        if 'x' in expr:
            variants = ["x+1", "x-1", "2x"]
        elif 'h' in expr:
            variants = ["h-10", "h+5", "h"]
        elif 'y' in expr:
            variants = ["y=2x+1", "y=x", "y=-x"]
        if variants:
            return variants[:3]

    # Boolean/conditional answers
    if any(phrase in ca_lower for phrase in ['sometimes', 'always', 'never', 'true', 'false']):
        return ["Always true", "Never true", "False"]

    # Slope/steepness answers
    if 'slope' in ca_lower or 'steepness' in ca_lower:
        return ["The steepness is -1", "The steepness is 0", "The steepness is 2"]

    # Equation answers
    if '=' in ca and len(ca) < 30:
        return ["x=0", "x=1", "No solution"]

    # Generic fallback for short non-numeric
    return ["0", "1", "It cannot be determined"]


def main():
    db_path = os.path.normpath(DB_PATH)
    print(f"DB path: {db_path}")
    print(f"DB exists: {os.path.exists(db_path)}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ====== Step 1: Delete 7 duplicate rows ======
    print("\n=== Step 1: Delete duplicates ===")
    placeholders = ','.join('?' * len(DUPLICATE_IDS))
    c.execute(f"SELECT id, question_text FROM questions WHERE id IN ({placeholders})", DUPLICATE_IDS)
    found = c.fetchall()
    print(f"Found {len(found)} rows to delete: {[r['id'] for r in found]}")
    c.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", DUPLICATE_IDS)
    conn.commit()
    print(f"Deleted. Remaining: {c.execute('SELECT COUNT(*) FROM questions').fetchone()[0]}")

    # ====== Step 2: Fix 57 rows with long wrong_answers ======
    print("\n=== Step 2: Fix wrong_answers ===")
    with open(DIRTY_ROWS_PATH) as f:
        dirty_rows = json.load(f)
    print(f"Loaded {len(dirty_rows)} dirty rows")

    updated = 0
    for row in dirty_rows:
        qid = row['id']
        ca = row['correct_answer']
        wrongs = generate_wrong_answers(ca)

        # Validate
        assert len(wrongs) == 3, f"ID {qid}: got {len(wrongs)} wrongs"
        for w in wrongs:
            assert len(w) <= 60, f"ID {qid}: wrong answer too long: {w[:80]}"
            assert w != ca, f"ID {qid}: wrong matches correct"

        wrongs_json = json.dumps(wrongs)
        c.execute("UPDATE questions SET wrong_answers = ? WHERE id = ?", (wrongs_json, qid))
        updated += 1

    conn.commit()
    print(f"Updated {updated} rows from JSON")

    # --- Sweep: fix any remaining rows with long wrong answers ---
    all_rows = c.execute("SELECT id, correct_answer, wrong_answers FROM questions").fetchall()
    sweep_fixed = 0
    for rid, ca, wa_json in all_rows:
        wrongs = json.loads(wa_json)
        needs_fix = any(len(w) > 60 for w in wrongs)
        if needs_fix:
            new_wrongs = generate_wrong_answers(ca)
            assert len(new_wrongs) == 3
            for w in new_wrongs:
                assert len(w) <= 60, f"ID {rid}: still too long: {w[:80]}"
            c.execute("UPDATE questions SET wrong_answers = ? WHERE id = ?",
                      (json.dumps(new_wrongs), rid))
            sweep_fixed += 1
    conn.commit()
    print(f"Sweep fixed {sweep_fixed} additional rows with long wrongs")

    # ====== Step 3: Set difficulty per topic ======
    print("\n=== Step 3: Set difficulty ===")
    for topic, difficulty in TOPIC_DIFFICULTY.items():
        c.execute("UPDATE questions SET difficulty = ? WHERE topic = ?", (difficulty, topic))
        count = c.rowcount
        if count > 0:
            print(f"  {topic} -> {difficulty} ({count} rows)")
    conn.commit()

    # ====== Step 4: Verify ======
    print("\n=== Step 4: Verification ===")

    # 1. Total count
    total = c.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"1. Total questions: {total} (expected 213) {'✅' if total == 213 else '❌'}")

    # 2. Duplicate check
    dupes = c.execute(
        "SELECT question_text, COUNT(*) FROM questions GROUP BY question_text HAVING COUNT(*) > 1"
    ).fetchall()
    print(f"2. Duplicate question_texts: {len(dupes)} {'✅' if len(dupes) == 0 else '❌'}")
    if dupes:
        for d in dupes[:5]:
            print(f"   - \"{d[0][:60]}...\" x{d[1]}")

    # 3. Wrong answer length check
    long_wrongs = 0
    rows = c.execute("SELECT id, wrong_answers FROM questions").fetchall()
    for r in rows:
        wrongs = json.loads(r['wrong_answers'])
        for w in wrongs:
            if len(w) > 60:
                long_wrongs += 1
                print(f"   ID {r['id']}: too long = \"{w[:80]}\"")
    print(f"3. Wrong answers > 60 chars: {long_wrongs} {'✅' if long_wrongs == 0 else '❌'}")

    # 4. Correct answer in wrongs check
    ca_in_wrongs = 0
    for r in rows:
        wrongs = json.loads(r['wrong_answers'])
        ca = r['wrong_answers']  # We need correct_answer
    # Re-fetch with correct_answer
    rows2 = c.execute("SELECT id, correct_answer, wrong_answers FROM questions").fetchall()
    for r in rows2:
        wrongs = json.loads(r['wrong_answers'])
        ca = r['correct_answer'].strip()
        # Check last line of ca against wrongs (since ca can be multi-line)
        ca_last = ca.split('\n')[-1].strip()
        for w in wrongs:
            if w.strip() == ca or w.strip() == ca_last:
                ca_in_wrongs += 1
                print(f"   ID {r['id']}: correct \"{ca_last}\" in wrongs")
    print(f"4. Correct answer in wrongs: {ca_in_wrongs} {'✅' if ca_in_wrongs == 0 else '❌'}")

    # 5. Difficulty distribution
    print("5. Difficulty distribution:")
    for r in c.execute("SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty").fetchall():
        print(f"   {r[0]}: {r[1]}")

    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    main()
