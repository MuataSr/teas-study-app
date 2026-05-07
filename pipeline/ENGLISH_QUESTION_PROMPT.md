# TEAS 7 English & Language Usage — Question Generation Prompt

## Instructions

You are generating practice questions for the TEAS 7 (Test of Essential Academic Skills) English & Language Usage section. Generate exactly **50 questions** following the specifications below.

## Output Format

Return **ONLY** a valid JSON array of 50 objects. No markdown, no explanation, no wrapping — just the JSON array. Each object must have exactly these fields:

```json
{
  "topic": "string — see Topic List below",
  "question_text": "string — the full question with A/B/C/D choices embedded",
  "correct_answer": "string — single uppercase letter: A, B, or D",
  "wrong_answers": "string — JSON array of the 3 wrong letters, e.g. '[\"A\",\"C\",\"D\"]'",
  "explanation": "string — clear explanation of why the correct answer is right",
  "difficulty": "string — one of: easy, medium, hard"
}
```

### Field Rules
- `topic`: Must exactly match one of the topics from the Topic List below
- `question_text`: Must include the full question stem AND four answer choices labeled A, B, C, D — each on its own line
- `correct_answer`: Single letter only: `"A"`, `"B"`, `"C"`, or `"D"`
- `wrong_answers`: Must be a **JSON string** (not a raw array) of exactly 3 letters — the three incorrect choices. Example: `'["A","C","D"]'`
- `explanation`: 1–2 sentences explaining the grammatical rule or reasoning
- `difficulty`: Distribute roughly — 15 easy, 25 medium, 10 hard

## Target DB Schema

These questions will be inserted into a SQLite table with this schema:

```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,         -- always 'english'
    topic TEXT NOT NULL,           -- from the topic list
    question_text TEXT NOT NULL,   -- full question with choices
    correct_answer TEXT NOT NULL,  -- single letter
    wrong_answers TEXT NOT NULL,   -- JSON array string of 3 wrong letters
    explanation TEXT,
    difficulty TEXT DEFAULT 'medium'
);
```

## TEAS 7 English Section — What's Actually Tested

The TEAS 7 English section has 33 scored + 4 unscored = 37 questions, 37 minutes. It covers three broad areas:

### 1. Conventions of Standard English (~15 questions)
- Subject-verb agreement (including collective nouns, compound subjects, indefinite pronouns)
- Verb tenses (simple, perfect, progressive; consistency within a sentence)
- Pronoun case (subjective vs objective) and antecedent agreement
- Active vs passive voice identification
- Misplaced and dangling modifiers
- Parallel structure in lists and comparisons
- Sentence fragments, comma splices, run-on sentences
- Correct comma usage (series, introductory clauses, coordinating conjunctions, non-restrictive clauses)
- Semicolon and colon usage
- Apostrophe usage (possessives vs plurals, its vs it's)

### 2. Knowledge of Language (~11 questions)
- Commonly confused word pairs: affect/effect, their/there/they're, its/it's, who/whom, whose/who's, then/than, your/you're, to/too/two, accept/except, principal/principle, complement/compliment, stationary/stationery, desert/dessert, loose/lose, chose/choose, breath/breathe, cite/site/sight, bare/bear, course/coarse, assent/ascent, council/counsel, decent/descent/dissent, forth/fourth, hear/here, idle/idol, peak/peek/pique, plain/plane, role/roll, weather/whether
- Word meaning in context (pick the right definition based on how it's used in a sentence)
- Formal vs informal language register
- Audience-appropriate language
- Parts of speech identification

### 3. Using Language and Vocabulary in Writing (~11 questions)
- Topic sentences and thesis statements
- Supporting evidence and irrelevant details
- Paragraph organization and logical order
- Transition words (however, therefore, furthermore, meanwhile, consequently, etc.)
- Revising sentences for clarity and conciseness
- Combining sentences effectively

## Topic List (use these exact strings)

**Grammar Conventions:**
- `Subject-Verb Agreement`
- `Verb Tenses`
- `Pronoun Usage`
- `Active vs Passive Voice`
- `Modifiers`
- `Parallel Structure`
- `Sentence Structure`
- `Comma Usage`
- `Semicolon and Colon Usage`
- `Apostrophe Usage`

**Knowledge of Language:**
- `Commonly Confused Words`
- `Word Meaning in Context`
- `Formal vs Informal Language`
- `Parts of Speech`

**Writing Conventions:**
- `Topic Sentences and Thesis`
- `Supporting Evidence`
- `Paragraph Organization`
- `Transition Words`
- `Sentence Revision`

## Distribution Target (out of 50)

| Category | Count |
|----------|-------|
| Grammar Conventions | ~18 |
| Knowledge of Language | ~17 |
| Writing Conventions | ~15 |

## Question Format Examples

### Example 1 — Grammar (easy)
```
Choose the sentence with correct subject-verb agreement.

A. The list of supplies are on the desk.
B. The list of supplies is on the desk.
C. The list of supplies be on the desk.
D. The list of supplies were on the desk.
```
```json
{
  "topic": "Subject-Verb Agreement",
  "question_text": "Choose the sentence with correct subject-verb agreement.\n\nA. The list of supplies are on the desk.\nB. The list of supplies is on the desk.\nC. The list of supplies be on the desk.\nD. The list of supplies were on the desk.",
  "correct_answer": "B",
  "wrong_answers": "[\"A\",\"C\",\"D\"]",
  "explanation": "'List' is the subject and is singular, so it takes the singular verb 'is.' The prepositional phrase 'of supplies' does not affect subject-verb agreement.",
  "difficulty": "easy"
}
```

### Example 2 — Confused Words (medium)
```
The nurse must ensure that the correct medication is administered to _____ patient.

A. there
B. their
C. they're
D. thier
```
```json
{
  "topic": "Commonly Confused Words",
  "question_text": "The nurse must ensure that the correct medication is administered to _____ patient.\n\nA. there\nB. their\nC. they're\nD. thier",
  "correct_answer": "B",
  "wrong_answers": "[\"A\",\"C\",\"D\"]",
  "explanation": "'Their' is the possessive pronoun indicating ownership. 'There' refers to a place, 'they're' is a contraction of 'they are,' and 'thier' is not a word.",
  "difficulty": "medium"
}
```

### Example 3 — Writing Conventions (medium)
```
Which transition word best fills the blank in the following paragraph?

The patient's blood pressure was elevated. _____, the physician ordered additional monitoring.

A. However
B. Therefore
C. Meanwhile
D. Although
```
```json
{
  "topic": "Transition Words",
  "question_text": "Which transition word best fills the blank in the following paragraph?\n\nThe patient's blood pressure was elevated. _____, the physician ordered additional monitoring.\n\nA. However\nB. Therefore\nC. Meanwhile\nD. Although",
  "correct_answer": "B",
  "wrong_answers": "[\"A\",\"C\",\"D\"]",
  "explanation": "'Therefore' indicates cause and effect — the elevated blood pressure caused the physician to order monitoring. 'However' and 'Although' show contrast; 'Meanwhile' shows simultaneous events.",
  "difficulty": "medium"
}
```

### Example 4 — Modifiers (hard)
```
Which sentence contains a dangling modifier?

A. Walking to the clinic, the rain started to fall.
B. The nurse walking to the clinic saw the rain starting to fall.
C. Walking to the clinic, she noticed the rain starting to fall.
D. She noticed the rain starting to fall while walking to the clinic.
```
```json
{
  "topic": "Modifiers",
  "question_text": "Which sentence contains a dangling modifier?\n\nA. Walking to the clinic, the rain started to fall.\nB. The nurse walking to the clinic saw the rain starting to fall.\nC. Walking to the clinic, she noticed the rain starting to fall.\nD. She noticed the rain starting to fall while walking to the clinic.",
  "correct_answer": "A",
  "wrong_answers": "[\"B\",\"C\",\"D\"]",
  "explanation": "In choice A, the modifying phrase 'Walking to the clinic' grammatically modifies 'the rain,' but rain doesn't walk — the modifier is dangling because no human subject is present for it to modify.",
  "difficulty": "hard"
}
```

## Rules

1. **Every question must have exactly 4 choices** (A, B, C, D) — never fewer, never more
2. **Only one correct answer** — the other 3 must be clearly wrong
3. **Wrong choices should be plausible** — use common student mistakes as distractors
4. **Use nursing/healthcare context** where natural (TEAS is for nursing school admission)
5. **Vary question formats**: "Choose the correct sentence," "Fill in the blank," "Identify the error," "Which word best completes," "Select the best transition," etc.
6. **No MLA/APA/citation questions** — those are not on the TEAS English section
7. **No spelling-only questions** — focus on grammar, meaning, and writing conventions
8. **Difficulty calibration**: Easy = obvious rule application. Medium = requires knowing the rule. Hard = subtle errors, tricky cases, or multiple rules interacting
9. **Return ONLY the JSON array** — no commentary, no markdown fences, no preamble
10. **Ensure valid JSON** — all strings properly escaped, especially newlines in question_text (use `\n`)

## IMPORTANT: JSON Escaping

- Use `\n` for newlines inside `question_text` strings
- Escape quotes inside strings with `\"`
- `wrong_answers` must be a JSON **string** containing an array, not a raw array

Example of correct `wrong_answers`:
```
"wrong_answers": "[\"A\",\"C\",\"D\"]"
```

NOT:
```
"wrong_answers": ["A","C","D"]
```
