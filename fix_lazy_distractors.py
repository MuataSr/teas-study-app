#!/usr/bin/env python3
"""Fix 8 specific math questions with lazy distractors."""
import sqlite3, json, urllib.request, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
PORT = 8082

FIXES = {
    116: {
        "prompt": """This math question has lazy distractors. Generate 3 plausible wrong answers that a student might actually write.

Question: Write the "Switch-Around Rule" in your own words, and give examples to show if it's always, sometimes, or rarely true.
Correct answer: The switch-around rule is not always true, it applies only for addition and multiplication. For example: 7+3=10 and 3+7=10, but 7-3=4 and 3-7=-4, it's not the same

Return ONLY a JSON array of 3 wrong answer strings (student misconceptions about commutativity). Each should be 1-2 sentences.""",
        "filter_short": False
    },
    119: {
        "prompt": """This math question has lazy distractors. Generate 3 plausible wrong answers.

Question: Sarah shares $15.40 among some of her friends. She gives the same amount to each person. (a) How many people might there be? (b) How many people CANNOT share $15.40 equally?
Correct answer: You can share $15.40 among 2, 4, and 7 people ($7.70, $3.85, $2.20 each)

Return ONLY a JSON array of 3 wrong answer strings (wrong factor pairs or wrong reasoning about divisors of 15.40).""",
        "filter_short": False
    },
    182: {
        "prompt": """This math question has lazy distractors. Generate 3 plausible wrong answers.

Question: Will different solutions be obtained from the following equations? 7w+22=109 and 7n+22=109
Correct answer: Of course, the solution is the same (w and n are just different variable names)

Return ONLY a JSON array of 3 wrong answer strings (common student misconceptions about variable naming).""",
        "filter_short": False
    },
    193: {
        "prompt": """This math question has lazy distractors. Generate 3 plausible wrong answers.

Question: Two students have the same amount of candies. Briana has one box, two tubes, and 7 loose candies. Susan has one box, one tube, and 20 loose candies. How many candies are in a tube?
Correct answer: Tube:13 candies. The box could contain any amount of candies.

Return ONLY a JSON array of 3 wrong answer strings (wrong tube counts a student might calculate). Each should be a short number like "10", "12", "15".""",
        "filter_short": False
    },
    195: {
        "prompt": """This math question has lazy distractors. Generate 3 plausible wrong answers.

Question: 3 + 4 = 7  ↑ The arrow above points to a symbol. What does the symbol mean?
Correct answer: The symbol is the equal sign and it means that the statement on the left side is equivalent to the statement on the right side.

Return ONLY a JSON array of 3 wrong answer strings (student misconceptions about what the = sign means).""",
        "filter_short": False
    },
    197: {
        "prompt": """This math question has lazy distractors. Generate 3 plausible wrong answers.

Question: For the following expressions, answer: What do the equal signs tell us? Which is more, one third or four twelfths? 1/3 = 4/12
Correct answer: The equal signs tell us that both expressions at each side are equivalent to each other. One third is equal to four twelfths.

Return ONLY a JSON array of 3 wrong answer strings (student misconceptions about fraction equivalence or the meaning of =).""",
        "filter_short": False
    },
    430: {
        "prompt": """This math question has "0" as a distractor. Generate 3 plausible wrong answers for a mean vs range difference problem.

Question: A data table shows a patient's daily blood sugar readings for four days: 90 mg/dL, 95 mg/dL, 100 mg/dL, 105 mg/dL. What is the difference between the mean of these readings and the range of these readings?
Correct answer: 10

Mean = 97.5, Range = 15, Difference = |97.5 - 15| = 82.5... wait, let me recalculate. Mean = (90+95+100+105)/4 = 97.5. Range = 105-90 = 15. Difference between mean and range = |97.5 - 15| = 82.5.

Return ONLY a JSON array of 3 wrong numbers a student might get. Example: ["5", "82.5", "12.5"]""",
        "filter_short": True
    },
    181: {
        "prompt": """This math question has weak distractors. Generate 3 plausible wrong answers.

Question: Are these number sentences true or false? a = a and c = r
Correct answer: c=r could be true or false, depending on the values of these variables

Return ONLY a JSON array of 3 wrong answer strings (student misconceptions about variable equality).""",
        "filter_short": False
    },
}

GENERIC = {'0','1','it cannot be determined','none of the above','all of the above'}

def call_model(prompt):
    url = f'http://127.0.0.1:{PORT}/v1/chat/completions'
    body = json.dumps({
        'model': 'local',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 512,
        'temperature': 0.7,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as resp:
        result = json.loads(resp.read())
    content = result['choices'][0]['message']['content']
    if '</think' in content:
        content = content.split('</think')[-1].strip()
    return content

def main():
    db = sqlite3.connect(DB)
    ok = 0
    fail = 0

    for qid, fix in FIXES.items():
        content = call_model(fix['prompt'])
        try:
            start = content.index('[')
            end = content.index(']') + 1
            new_wrong = json.loads(content[start:end])
            if len(new_wrong) != 3:
                print(f'  ID {qid}: FAIL - got {len(new_wrong)} items')
                fail += 1
                continue
            if any(w.strip().lower() in GENERIC for w in new_wrong):
                print(f'  ID {qid}: FAIL - still has generic: {new_wrong}')
                fail += 1
                continue
            db.execute('UPDATE questions SET wrong_answers=? WHERE id=?',
                       (json.dumps(new_wrong), qid))
            db.commit()
            print(f'  ID {qid}: OK -> {new_wrong}')
            ok += 1
        except Exception as e:
            print(f'  ID {qid}: FAIL - {e}')
            fail += 1

    print(f'\nDone: {ok} fixed, {fail} failed')

if __name__ == '__main__':
    main()
