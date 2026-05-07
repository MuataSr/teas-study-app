#!/usr/bin/env python3
"""Generate 99 more English questions to reach 500 total."""

import sqlite3
import json
import urllib.request
import time
import sys
import os

# ── Config ──
API_KEY = "REMOVED-ROTATED-KEY"
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-5-turbo"
UNIFIED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "kb", "teas_unified.db")
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "kb", "generate_batch3.log")

SYSTEM_PROMPT = (
    "You are an expert TEAS 7 test question writer. The TEAS English & Language Usage section covers:\n"
    "1. Conventions of Standard English (grammar, spelling, punctuation, sentence structure)\n"
    "2. Knowledge of Language (vocabulary, word meaning in context)\n"
    "3. Using Language and Vocabulary in Writing (paragraphs, transitions, audience, tone)\n\n"
    "Generate questions in EXACTLY this JSON format (array of objects):\n"
    '[{"topic":"topic name","question_text":"question with 4 choices labeled A/B/C/D",'
    '"correct_answer":"letter of correct answer","wrong_answers":["list of 3 wrong answer letters"],'
    '"explanation":"detailed explanation of why the correct answer is right and why others are wrong",'
    '"difficulty":"easy|medium|hard"}]\n\n'
    "RULES:\n"
    "- Exactly 4 answer choices (A, B, C, D), only ONE correct\n"
    "- TEAS-style: practical, nursing-context where natural\n"
    "- Include answer choices IN question_text\n"
    "- correct_answer = LETTER (A/B/C/D), wrong_answers = list of 3 wrong LETTERS\n"
    "- Mix easy/medium/hard difficulty\n"
    "- Vary formats: identify error, fill-in-the-blank, choose correct version, which word fits\n"
    "- NO citation/MLA/APA questions\n"
    "- Return ONLY valid JSON array, no markdown fences"
)

# Topics to generate (distributed to fill gaps to ~27 each)
ALLOCATION = {
    "Apostrophe Usage": 14,
    "Comma Usage": 9,
    "Formal vs Informal Language": 9,
    "Paragraph Organization": 9,
    "Sentence Revision": 9,
    "Supporting Evidence": 9,
    "Topic Sentences and Thesis": 9,
    "Semicolon and Colon Usage": 8,
    "Active vs Passive Voice": 7,
    "Parts of Speech": 7,
    "Transition Words": 7,
    "Modifiers": 2,
}

# Topic-specific guidance for better variety
TOPIC_GUIDANCE = {
    "Apostrophe Usage": "possessive vs plural, contractions, possessives with singular/plural nouns, joint possession, apostrophes with abbreviations and numbers",
    "Comma Usage": "serial comma, introductory clauses, coordinate adjectives, nonrestrictive clauses, direct address, dates/addresses, compound sentences",
    "Formal vs Informal Language": "register shifts, audience-appropriate language, academic vs casual tone, professional communication, avoiding slang in formal writing",
    "Paragraph Organization": "logical order of ideas, chronological vs emphatic order, transitional paragraphs, introductory and concluding paragraphs, coherence strategies",
    "Sentence Revision": "conciseness, clarity, redundancy elimination, sentence combining, rephrasing for clarity, fixing awkward constructions",
    "Supporting Evidence": "relevant vs irrelevant evidence, types of evidence (facts, statistics, examples, expert opinion), integrating evidence into paragraphs, evaluating source credibility",
    "Topic Sentences and Thesis": "identifying topic sentences, writing effective topic sentences, thesis statement clarity, scope of thesis statements, positioning within paragraphs",
    "Semicolon and Colon Usage": "joining independent clauses, semicolons with transitions, colons before lists/quotes/explanations, common misuse cases",
    "Active vs Passive Voice": "identifying active/passive, when passive is appropriate, converting between voices, clarity and directness in writing",
    "Parts of Speech": "noun/verb/adjective/adverb identification, gerunds vs participles, prepositions, conjunctions, interjections in context",
    "Transition Words": "additive, contrastive, causal, sequential transitions, choosing appropriate transitions, transition placement within sentences",
    "Modifiers": "dangling modifiers, misplaced modifiers, squinting modifiers, limiting modifiers, comparative/superlative forms",
}


def call_api(prompt, max_retries=5):
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
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
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 30 * (attempt + 1)  # 30s, 60s, 90s, 120s, 150s
                log(f"  429 rate limited, waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                log(f"  HTTP error {e.code} (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(10)
        except Exception as e:
            log(f"  API error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
    return None


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start:end+1])
    return None


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def main():
    log("=" * 50)
    log("English Batch 3 — generating 99 questions")
    log("=" * 50)

    conn = sqlite3.connect(UNIFIED_PATH)
    max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM questions").fetchone()[0]
    log(f"Starting from ID {max_id + 1}")

    # Load existing question texts for dedup
    existing = set()
    for row in conn.execute("SELECT question_text FROM questions WHERE subject='english'").fetchall():
        existing.add(row[0].strip()[:80])

    total_inserted = 0

    for topic, count in ALLOCATION.items():
        log(f"\n--- {topic}: generating {count} ---")
        guidance = TOPIC_GUIDANCE.get(topic, "")
        remaining = count

        while remaining > 0:
            batch_size = min(5, remaining)
            prompt = (
                f"Generate {batch_size} TEAS 7 English questions on: {topic}\n\n"
                f"Focus areas: {guidance}\n\n"
                f"IMPORTANT: Each question's 'topic' field must be exactly '{topic}'.\n"
                f"Generate {batch_size} questions. Return ONLY a JSON array."
            )

            response = call_api(prompt)
            if not response:
                log(f"  API failed, retrying same batch ({remaining} remaining)")
                time.sleep(30)
                continue

            questions = extract_json(response)
            if not questions:
                log(f"  JSON parse failed: {response[:150]}")
                time.sleep(10)
                continue

            valid = 0
            for q in questions:
                qt = q.get("question_text", "").strip()[:80]
                if qt in existing:
                    continue  # dedup
                if all(k in q for k in ["topic", "question_text", "correct_answer", "wrong_answers", "explanation", "difficulty"]):
                    try:
                        max_id += 1
                        conn.execute(
                            """INSERT INTO questions (id, subject, topic, question_text, correct_answer, wrong_answers, explanation, difficulty)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (max_id, "english", topic, q["question_text"], q["correct_answer"],
                             json.dumps(q["wrong_answers"]), q["explanation"], q.get("difficulty", "medium")),
                        )
                        existing.add(qt)
                        valid += 1
                    except Exception as e:
                        log(f"  Insert error: {e}")

            if valid > 0:
                conn.commit()
                remaining -= valid
                log(f"  +{valid} valid, {remaining} still needed")
            else:
                log(f"  0 valid from batch, retrying ({remaining} remaining)")
                time.sleep(15)
            time.sleep(2)
            time.sleep(1)

        total_inserted += count - remaining
        log(f"  {topic} done: {count - remaining}/{count} inserted")

    conn.close()
    log(f"\n{'=' * 50}")
    log(f"Complete! Total inserted: {total_inserted}")
    log(f"{'=' * 50}")


if __name__ == "__main__":
    main()
