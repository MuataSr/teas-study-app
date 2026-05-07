#!/usr/bin/env python3
"""Fix short/generic distractors in math questions.
Replaces weak distractors like '0', '1', 'It cannot be determined' with plausible alternatives.
Usage: python3 fix_short_distractors.py --start_id N --count N
"""
import sqlite3, json, sys, urllib.request, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
PORT = 8082

def call_model(prompt):
    url = f'http://127.0.0.1:{PORT}/v1/chat/completions'
    body = json.dumps({
        'model': 'local',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 512,
        'temperature': 0.7,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    start = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        result = json.loads(resp.read())
    elapsed = time.time() - start
    content = result['choices'][0]['message']['content']
    if '</think' in content:
        content = content.split('</think')[-1].strip()
    return content, elapsed

def fix_question(db, qid, question_text, correct_answer, wrong_answers):
    """Generate better distractors for a question with weak ones."""
    wrong_str = ', '.join(wrong_answers)
    
    prompt = f"""You are a TEAS 7 math test question writer. This question has weak distractors that are too short or generic.

Question: {question_text}
Correct answer: {correct_answer}
Current wrong answers: {wrong_str}

Generate 3 new, plausible wrong answers that:
- Are similar in format to the correct answer (same units, same type of number)
- Represent common student mistakes
- Are NOT generic phrases like "None of the above" or "It cannot be determined"
- Are NOT single-digit numbers unless the correct answer is also a small number

Return ONLY a JSON array of 3 strings, nothing else. Example: ["15", "25", "35"]"""

    content, elapsed = call_model(prompt)
    
    # Try to parse JSON from output
    try:
        # Find JSON array in the response
        start = content.index('[')
        end = content.index(']') + 1
        new_wrong = json.loads(content[start:end])
        if len(new_wrong) != 3:
            return False, f'Got {len(new_wrong)} items, need 3'
        if any(len(str(w).strip()) < 2 for w in new_wrong):
            return False, f'Still has short distractors: {new_wrong}'
    except (ValueError, json.JSONDecodeError) as e:
        return False, f'Parse error: {e}'
    
    db.execute('UPDATE questions SET wrong_answers=? WHERE id=?',
               (json.dumps(new_wrong), qid))
    db.commit()
    return True, f'{wrong_str} -> {new_wrong} ({elapsed:.1f}s)'

def main():
    args = sys.argv[1:]
    start_id = int(args[args.index('--start_id')+1]) if '--start_id' in args else 1
    count = int(args[args.index('--count')+1]) if '--count' in args else 3
    
    db = sqlite3.connect(DB)
    
    # Find short-distractor questions
    rows = db.execute('''
        SELECT id, question_text, correct_answer, wrong_answers 
        FROM questions WHERE subject='math' ORDER BY id
    ''').fetchall()
    
    targets = []
    for row in rows:
        qid, qt, ca, wa = row
        if qid < start_id:
            continue
        try:
            w = json.loads(wa)
            if len(w) == 3 and any(len(x.strip()) < 3 for x in w):
                targets.append((qid, qt, ca, w))
        except:
            continue  # skip letter-ref (handled separately)
        if len(targets) >= count:
            break
    
    if not targets:
        print('No more short-distractor questions to fix!')
        return
    
    print(f'Fixing {len(targets)} short-distractor questions starting at ID {targets[0][0]}...')
    ok = 0
    fail = 0
    for qid, qt, ca, wa in targets:
        success, msg = fix_question(db, qid, qt, ca, wa)
        if success:
            ok += 1
            print(f'  ID {qid}: {msg}')
        else:
            fail += 1
            print(f'  ID {qid}: FAIL - {msg}')
    
    print(f'\nBatch done: {ok} fixed, {fail} failed')

if __name__ == '__main__':
    main()
