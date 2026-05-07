#!/usr/bin/env python3
"""Fix last 8 questions — targeted patches."""
import sqlite3, json

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'

FIXES = {
    # Q31, Q32: explanations truncated at EXPLANATION_COMPLETE — append the missing final sentence
    31: {
        "explanation_fix": "append",
        "append_text": " This gives us the correct answer of \\(\\frac{9}{10}\\), confirming that option A is the right choice."
    },
    32: {
        "explanation_fix": "append",
        "append_text": " Therefore, the sum is \\(\\frac{14}{15}\\), making option A the correct answer."
    },
    # Q33: question text is GARBLED — contains wrong problem. Rewrite completely
    33: {
        "question_text": "Add \\(\\frac{3}{4}\\)+\\(\\frac{1}{2}\\)=?\n\nA) \\(\\frac{5}{8}\\)\nB) \\(\\frac{4}{4}\\)\nC) \\(\\frac{6}{4}\\)\nD) \\(\\frac{5}{4}\\)",
        "correct_answer": "D",
        "wrong_answers": json.dumps(["\\(\\frac{5}{8}\\)", "\\(\\frac{4}{4}\\)", "\\(\\frac{6}{4}\\)"]),
        "explanation": "To add \\(\\frac{3}{4}\\) and \\(\\frac{1}{2}\\), first find a common denominator. The least common denominator of 4 and 2 is 4. Convert \\(\\frac{1}{2}\\) to an equivalent fraction with denominator 4: \\(\\frac{1}{2}=\\frac{2}{4}\\). Now add the fractions: \\(\\frac{3}{4}+\\frac{2}{4}=\\frac{5}{4}\\). Option A (\\(\\frac{5}{8}\\)) is a common mistake from adding numerators and denominators separately. Option B (\\(\\frac{4}{4}=1\\)) ignores the \\(\\frac{3}{4}\\) term entirely. Option C (\\(\\frac{6}{4}\\)) results from incorrectly converting \\(\\frac{1}{2}\\) to \\(\\frac{3}{4}\\). The correct answer is D, \\(\\frac{5}{4}\\)."
    },
    # Q193: wrong_answers are just letters ["B","C","D"] — need actual answer text
    193: {
        "question_text": "Briana and Susan both have the same total number of candies. Briana has 1 box, 2 tubes, and 7 loose candies. Susan has 1 box, 1 tube, and 20 loose candies. Each tube contains the same number of candies, and each box contains the same number of candies. How many candies are in each tube?\n\nA) 13\nB) 16\nC) 18\nD) 15",
        "correct_answer": "A",
        "wrong_answers": json.dumps(["16", "18", "15"]),
    },
    # Q197: answer text in options looks wrong
    197: {
        "question_text": "For the following expressions, answer: What do the equal signs tell us? Which is more, one third or four twelfths?\n\n\\(\\frac{1}{3}\\) = \\(\\frac{2}{6}\\) = \\(\\frac{4}{12}\\)\n\nA) One third is greater because it has a smaller denominator\nB) Four twelfths is greater because it has a larger numerator\nC) They are equal because equivalent fractions represent the same value\nD) It cannot be determined without more information",
        "correct_answer": "C",
        "wrong_answers": json.dumps(["One third is greater because it has a smaller denominator", "Four twelfths is greater because it has a larger numerator", "It cannot be determined without more information"]),
        "explanation": "Equivalent fractions represent the same value even though they look different. Starting with \\(\\frac{1}{3}\\), multiplying both numerator and denominator by 2 gives \\(\\frac{2}{6}\\), and multiplying by 4 gives \\(\\frac{4}{12}\\). All three fractions — \\(\\frac{1}{3}\\), \\(\\frac{2}{6}\\), and \\(\\frac{4}{12}\\) — are equal to approximately 0.333. The equal signs tell us these expressions have identical values. Option A is incorrect because a smaller denominator alone does not make a fraction larger — it depends on the numerator too. Option B is incorrect for the same reason in reverse. Option D is incorrect because we have enough information to determine equivalence. The correct answer is C: they are equal."
    },
    # Q200: wrong_answers contain full worked solutions instead of just answer text
    200: {
        "question_text": "Solve for t: t - 24 = 23t\n\nA) t = -1\nB) t = -\\(\\frac{12}{11}\\)\nC) t = 12\nD) t = 0",
        "correct_answer": "B",
        "wrong_answers": json.dumps(["t = -1", "t = 12", "t = 0"]),
        "explanation": "To solve t - 24 = 23t, first isolate the variable. Subtract t from both sides: -24 = 22t. Then divide both sides by 22: t = \\(-\\frac{24}{22}\\). Simplifying by dividing numerator and denominator by 2 gives t = \\(-\\frac{12}{11}\\). Option A (t = -1) results from incorrectly subtracting 23t from both sides to get -24 = -22t instead of -24 = 22t. Option C (t = 12) comes from dropping the negative sign entirely. Option D (t = 0) is not a solution since plugging it in gives -24 = 0, which is false. The correct answer is B, t = \\(-\\frac{12}{11}\\)."
    },
    # Q756: wrong_answers are just letters, need full text
    756: {
        "question_text": "Read the following three sentences:\n1. The patient arrived at the clinic with a fever.\n2. The nurse took the patient's temperature.\n3. The reading was 102 degrees.\n\nWhich option best combines these sentences into one?\n\nA) The patient arrived at the clinic with a fever, and the nurse took the temperature, it was 102 degrees.\nB) The patient arrived at the clinic with a fever; the nurse took the patient's temperature, which read 102 degrees.\nC) The patient arrived, the nurse took the temperature, and it was 102 degrees.\nD) Arriving with a fever, the nurse took the patient's temperature and the reading was 102 degrees.",
        "correct_answer": "B",
        "wrong_answers": json.dumps(["The patient arrived at the clinic with a fever, and the nurse took the temperature, it was 102 degrees.", "The patient arrived, the nurse took the temperature, and it was 102 degrees.", "Arriving with a fever, the nurse took the patient's temperature and the reading was 102 degrees."]),
    },
    # Q2053: explanation says "Option A is right" but correct answer is D (arithmetic sequence)
    2053: {
        "explanation": "The temperatures — 98.6°F, 99.0°F, 99.4°F, 99.8°F — increase by exactly 0.4°F each hour (99.0 - 98.6 = 0.4, 99.4 - 99.0 = 0.4, 99.8 - 99.4 = 0.4). A constant difference between consecutive terms defines an arithmetic sequence. Option A is incorrect because a quadratic function involves a squared term and produces varying (non-constant) differences between consecutive values. Option B is incorrect because a constant sequence has no change between terms (difference of 0). Option C is incorrect because an exponential sequence has a constant ratio between terms, not a constant difference. The correct answer is D, an arithmetic sequence."
    }
}


def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    for qid, fix in FIXES.items():
        if fix.get("explanation_fix") == "append":
            # Truncated explanation — append missing text
            c.execute('UPDATE questions SET explanation = explanation || ? WHERE id=?',
                      (fix["append_text"], qid))
            print(f'Q{qid}: appended to explanation')
        else:
            # Full question rewrite
            sets = []
            params = []
            if "question_text" in fix:
                sets.append("question_text=?")
                params.append(fix["question_text"])
            if "correct_answer" in fix:
                sets.append("correct_answer=?")
                params.append(fix["correct_answer"])
            if "wrong_answers" in fix:
                sets.append("wrong_answers=?")
                params.append(fix["wrong_answers"])
            if "explanation" in fix:
                sets.append("explanation=?")
                params.append(fix["explanation"])
            params.append(qid)
            c.execute(f'UPDATE questions SET {", ".join(sets)} WHERE id=?', params)
            print(f'Q{qid}: updated {", ".join(sets)}')

    conn.commit()

    # Verify
    for qid in FIXES:
        q = c.execute('SELECT question_text, correct_answer, wrong_answers, explanation FROM questions WHERE id=?', (qid,)).fetchone()
        print(f'  Q{qid} check: {len(str(q[0]))}q {len(str(q[3]))}e')

    conn.close()
    print('Done.')


if __name__ == '__main__':
    main()
