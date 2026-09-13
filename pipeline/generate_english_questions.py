#!/usr/bin/env python3
"""Generate TEAS-aligned English/Language Usage questions from english.db KB content."""

import sqlite3
import json
import urllib.request
import urllib.error
import time
import sys
import os

def _env_key(name):
    """Read a credential from the environment, falling back to a repo-root .env.
    Credentials are never committed - see .env.example."""
    v = os.environ.get(name, "")
    if not v and os.path.exists(".env"):
        for _line in open(".env"):
            if _line.strip().startswith(name + "="):
                v = _line.split("=", 1)[1].strip().strip("\"'")
                break
    if not v:
        raise SystemExit(
            f"{name} is not set. Copy .env.example to .env and fill it in, "
            f"or export {name}."
        )
    return v

# ── Config ──
API_KEY = _env_key("ZAI_API_KEY")
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-5-turbo"
KB_PATH = "data/kb/english.db"
UNIFIED_PATH = "data/kb/teas_unified.db"
BATCH_SIZE = 10  # questions per API call

# ── TEAS English Categories ──
CATEGORIES = {
    "conventions_grammar": {
        "table": "rules",
        "filter": "category IN ('sentence_errors', 'verbs', 'pronouns', 'modifiers', 'agreement', 'parallel_structure', 'active_passive')",
        "count": 50,
        "prompt_focus": "Conventions of Standard English — grammar, sentence structure, subject-verb agreement, verb tenses, pronoun usage, parallel structure, active vs passive voice, dangling/misplaced modifiers, sentence fragments, comma splices, run-on sentences",
    },
    "conventions_punctuation": {
        "table": "punctuation_rules",
        "filter": "1=1",
        "count": 35,
        "prompt_focus": "Conventions of Standard English — punctuation rules including commas, semicolons, colons, apostrophes, quotation marks, dashes, parentheses, hyphens, and end punctuation",
    },
    "knowledge_vocabulary": {
        "table": "confusing_words",
        "filter": "1=1",
        "count": 35,
        "prompt_focus": "Knowledge of Language — commonly confused words (affect/effect, their/there/they're, its/it's, who/whom, etc.), word meaning in context, vocabulary, parts of speech identification",
    },
    "writing_conventions": {
        "table": "rules",
        "filter": "category IN ('paragraphs', 'transitions', 'writing_process', 'audience', 'tone', 'style')",
        "count": 30,
        "prompt_focus": "Using Language and Vocabulary to Express Ideas in Writing — paragraph structure, topic sentences, supporting evidence, transitions between ideas, audience awareness, tone, thesis statements, cohesive writing",
    },
}


def call_api(prompt, max_retries=3):
    """Call Z.AI API with retry logic."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert TEAS 7 test question writer. The TEAS (Test of Essential Academic Skills) "
                    "English & Language Usage section has 37 questions covering:\n"
                    "1. Conventions of Standard English (grammar, spelling, punctuation, sentence structure)\n"
                    "2. Knowledge of Language (vocabulary, word meaning in context)\n"
                    "3. Using Language and Vocabulary in Writing (paragraphs, transitions, audience, tone)\n\n"
                    "Generate questions in EXACTLY this JSON format (array of objects):\n"
                    '[{"topic":"topic name","question_text":"question with 4 choices labeled A/B/C/D","correct_answer":"letter of correct answer","wrong_answers":["list of 3 wrong answer letters"],"explanation":"why correct is right","difficulty":"easy|medium|hard"}]\n\n'
                    "IMPORTANT RULES:\n"
                    "- Each question must have exactly 4 answer choices (A, B, C, D)\n"
                    "- Only ONE correct answer\n"
                    "- Questions must be TEAS-style: practical, nursing-context where natural, testing real skills\n"
                    "- Include the answer choices IN the question_text field\n"
                    "- correct_answer is the LETTER (A, B, C, or D)\n"
                    "- wrong_answers is a list of the 3 wrong LETTERS\n"
                    "- Mix of easy, medium, hard difficulty\n"
                    "- Vary question formats: identify the error, fill-in-the-blank, choose the correct version, which word fits, etc.\n"
                    "- DO NOT include citation/MLA/APA questions — TEAS does not test these\n"
                    "- Return ONLY valid JSON array, no markdown fences, no commentary"
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 4096,
    }).encode()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                BASE_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  API error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None


def extract_json(text):
    """Extract JSON array from LLM response, handling markdown fences."""
    text = text.strip()
    # Remove markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    # Find JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start:end+1])
    return None


def load_kb_content(table, filter_clause):
    """Load KB content from english.db."""
    conn = sqlite3.connect(KB_PATH)
    rows = conn.execute(f"SELECT * FROM [{table}] WHERE {filter_clause}").fetchall()
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info([{table}])").fetchall()]
    result = [dict(zip(cols, r)) for r in rows]
    conn.close()
    return result


def generate_questions(category, kb_content, count):
    """Generate questions for a category in batches."""
    all_questions = []
    remaining = count

    while remaining > 0:
        batch_size = min(BATCH_SIZE, remaining)
        print(f"  Generating {batch_size} questions ({remaining} remaining)...")

        # Build context from KB content (truncate if too long)
        context_str = json.dumps(kb_content, indent=2, default=str)
        if len(context_str) > 6000:
            context_str = context_str[:6000] + "\n... (truncated)"

        prompt = (
            f"Generate {batch_size} TEAS 7 English & Language Usage questions.\n\n"
            f"Category focus: {category['prompt_focus']}\n\n"
            f"Reference material from our knowledge base:\n{context_str}\n\n"
            f"Generate {batch_size} questions. Return ONLY a JSON array."
        )

        response = call_api(prompt)
        if not response:
            print(f"  FAILED - skipping batch")
            remaining -= batch_size
            continue

        questions = extract_json(response)
        if not questions:
            print(f"  Could not parse JSON from response")
            print(f"  Response preview: {response[:200]}")
            remaining -= batch_size
            continue

        # Validate and add subject
        valid = 0
        for q in questions:
            if all(k in q for k in ["topic", "question_text", "correct_answer", "wrong_answers", "explanation", "difficulty"]):
                q["subject"] = "english"
                all_questions.append(q)
                valid += 1

        print(f"  Got {valid} valid questions")
        remaining -= batch_size
        time.sleep(1)  # Rate limiting

    return all_questions


def insert_questions(questions):
    """Insert questions into the unified DB."""
    conn = sqlite3.connect(UNIFIED_PATH)

    # Get current max ID
    max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM questions").fetchone()[0]

    inserted = 0
    for i, q in enumerate(questions):
        try:
            conn.execute(
                """INSERT INTO questions (id, subject, topic, question_text, correct_answer, wrong_answers, explanation, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    max_id + i + 1,
                    q["subject"],
                    q["topic"],
                    q["question_text"],
                    q["correct_answer"],
                    json.dumps(q["wrong_answers"]),
                    q["explanation"],
                    q.get("difficulty", "medium"),
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"  Insert error for question {i}: {e}")

    conn.commit()
    conn.close()
    return inserted


def main():
    print("=" * 60)
    print("TEAS English Question Generator")
    print("=" * 60)

    total_generated = 0
    total_inserted = 0

    for cat_name, cat_info in CATEGORIES.items():
        print(f"\n--- {cat_name} (target: {cat_info['count']}) ---")

        kb_content = load_kb_content(cat_info["table"], cat_info["filter"])
        print(f"  Loaded {len(kb_content)} KB entries")

        if not kb_content:
            print(f"  No KB content found, skipping")
            continue

        questions = generate_questions(cat_info, kb_content, cat_info["count"])
        total_generated += len(questions)

        if questions:
            inserted = insert_questions(questions)
            total_inserted += inserted
            print(f"  Inserted {inserted} questions")

    print(f"\n{'=' * 60}")
    print(f"Done! Generated {total_generated}, inserted {total_inserted}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
