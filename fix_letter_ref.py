#!/usr/bin/env python3
"""Fix letter-reference wrong_answers (e.g. 'B,C,D') in math questions.
Calls llama-server on port 8082 to generate proper answer choices.
Usage: python3 fix_letter_ref.py --start_id N --count N
"""
import sqlite3, json, sys, urllib.request, time

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
PORT = 8082

def call_model(prompt):
    """Call local llama-server chat completions."""
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
    # Strip thinking tags if present
    if '</think' in content:
        content = content.split('</think')[-1].strip()
    return content, elapsed

def parse_choices(text):
    """Extract A/B/C/D choices from model output."""
    choices = {}
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        for letter in ['A', 'B', 'C', 'D']:
            if line.startswith(f'{letter})') or line.startswith(f'{letter}.') or line.startswith(f'{letter} '):
                answer = line[2:].strip()
                if answer:
                    choices[letter] = answer
    return choices

def fix_question(db, qid, question_text, correct_letter, wrong_letters):
    """Generate proper choices for a letter-reference question."""
    wrong_set = set(wrong_letters)
    prompt = f"""You are a TEAS 7 math test question writer. Given this math question, generate exactly 4 answer choices (A, B, C, D).

The correct answer is option {correct_letter}. Generate one correct answer and three plausible wrong answers.

Format exactly like this:
A) <answer>
B) <answer>
C) <answer>
D) <answer>

Question: {question_text}

Generate the 4 choices now:"""

    content, elapsed = call_model(prompt)
    choices = parse_choices(content)
    
    if len(choices) < 4:
        return False, f'Only got {len(choices)} choices: {choices}'
    
    correct_text = choices[correct_letter]
    wrong_texts = [choices[l] for l in wrong_letters if l in choices]
    
    if len(wrong_texts) < 3:
        return False, f'Missing wrong texts for {wrong_letters}: {choices}'
    
    # Build new question text with embedded choices
    choices_block = '  '.join(f'{l}) {choices[l]}' for l in ['A','B','C','D'])
    new_question = f"{question_text}\n\n{choices_block}"
    
    # Update DB
    db.execute('UPDATE questions SET question_text=?, correct_answer=?, wrong_answers=? WHERE id=?',
               (new_question, correct_text, json.dumps(wrong_texts), qid))
    db.commit()
    return True, f'OK ({elapsed:.1f}s)'

def main():
    args = sys.argv[1:]
    start_id = int(args[args.index('--start_id')+1]) if '--start_id' in args else 411
    count = int(args[args.index('--count')+1]) if '--count' in args else 3
    
    db = sqlite3.connect(DB)
    
    # Find letter-reference questions starting from start_id
    rows = db.execute('''
        SELECT id, question_text, correct_answer, wrong_answers 
        FROM questions WHERE subject='math' ORDER BY id
    ''').fetchall()
    
    targets = []
    for row in rows:
        qid, qt, ca, wa = row
        if qid < start_id:
            continue
        if len(wa) <= 7 and all(c in 'ABCD,' for c in wa) and len(ca) <= 2:
            wrong_letters = [l.strip() for l in wa.split(',')]
            if len(wrong_letters) == 3:
                targets.append((qid, qt, ca, wrong_letters))
        if len(targets) >= count:
            break
    
    if not targets:
        print('No more letter-reference questions to fix!')
        return
    
    print(f'Fixing {len(targets)} letter-reference questions starting at ID {targets[0][0]}...')
    ok = 0
    fail = 0
    for qid, qt, ca, wl in targets:
        success, msg = fix_question(db, qid, qt, ca, wl)
        if success:
            ok += 1
            print(f'  ID {qid}: {msg}')
        else:
            fail += 1
            print(f'  ID {qid}: FAIL - {msg}')
    
    print(f'\nBatch done: {ok} fixed, {fail} failed')

if __name__ == '__main__':
    main()
