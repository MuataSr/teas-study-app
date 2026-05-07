"""
kb.py — Knowledge Base query layer for TEAS Study Buddy.

Each subject has its own SQLite DB in data/kb/. This module provides
functions to pull topics, lessons, practice questions, and quiz questions
from the KBs instead of using hardcoded mock data.

Usage:
    from kb import get_english_topics, get_english_lesson, get_english_quiz_questions
"""

import sqlite3
import os

# ---------------------------------------------------------------------------
# DB paths — relative to this file so PyInstaller can find them
# ---------------------------------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_KB_DIR = os.path.join(_BASE_DIR, "data", "kb")

DB_PATHS = {
    "english": os.path.join(_KB_DIR, "english.db"),
    "math": os.path.join(_KB_DIR, "math.db"),
    "science": os.path.join(_KB_DIR, "teas_unified.db"),
    "reading": os.path.join(_KB_DIR, "teas_unified.db"),
    "unified": os.path.join(_KB_DIR, "teas_unified.db"),
}


def _slugify(text):
    """Convert text to URL-safe slug."""
    return text.lower().strip().replace("&", "and").replace(" ", "-").replace(",", "").replace("'", "").replace("/", "-")


def _connect(subject):
    """Open a read-only connection to a subject KB."""
    path = DB_PATHS.get(subject)
    if not path or not os.path.exists(path):
        return None
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ===========================================================================
# ENGLISH — writing_guide.db schema
# ===========================================================================
#
# Tables:
#   rules            (id, category, rule_text, correct_example, incorrect_example, explanation)
#   confusing_words  (id, word_1, word_2, definition_1, definition_2, example_1, example_2)
#   punctuation_rules(id, mark, rule_text, correct_example, incorrect_example, explanation)
#   misconceptions   (id, category, misconception, wrong_pattern, correct_pattern, example, explanation)
#   citation_rules   (id, style, category, rule_text, correct_example, incorrect_example, explanation)
#   citation_errors  (id, error_type, wrong, correct, explanation)
#
# TEAS English topics map:
#   Grammar & Usage   → rules where category in grammar-related categories
#   Sentence Structure→ rules where category in structure-related categories
#   Punctuation       → punctuation_rules
#   Vocabulary        → confusing_words

_ENGLISH_GRAMMAR_CATS = (
    "subject_verb_agreement", "pronoun_usage", "capitalization",
    "comma_splice", "wordiness", "voice", "academic_tone",
    "professional_tone", "general",
)

_ENGLISH_STRUCTURE_CATS = (
    "sentence_errors", "sentence_structure", "sentence_types",
    "paragraph_structure", "conclusion_writing",
)

_ENGLISH_TOPIC_MAP = {
    "grammar": {
        "name": "Grammar & Usage",
        "slug": "grammar",
        "categories": _ENGLISH_GRAMMAR_CATS,
    },
    "sentence-structure": {
        "name": "Sentence Structure",
        "slug": "sentence-structure",
        "categories": _ENGLISH_STRUCTURE_CATS,
    },
    "punctuation": {
        "name": "Punctuation",
        "slug": "punctuation",
    },
    "vocabulary": {
        "name": "Vocabulary",
        "slug": "vocabulary",
    },
}


def get_english_topics():
    """Return the 4 English topics with question counts from the KB."""
    conn = _connect("english")
    if not conn:
        return _ENGLISH_TOPIC_MAP  # fallback

    topics = []
    for slug, meta in _ENGLISH_TOPIC_MAP.items():
        count = 0
        if slug == "punctuation":
            count = conn.execute("SELECT COUNT(*) FROM punctuation_rules").fetchone()[0]
        elif slug == "vocabulary":
            count = conn.execute("SELECT COUNT(*) FROM confusing_words").fetchone()[0]
        else:
            placeholders = ",".join("?" * len(meta["categories"]))
            count = conn.execute(
                f"SELECT COUNT(*) FROM rules WHERE category IN ({placeholders})",
                meta["categories"],
            ).fetchone()[0]

        topics.append({
            "name": meta["name"],
            "slug": slug,
            "question_count": count,
            # readiness_pct starts at 0 — user_progress.db will track this later
            "readiness_pct": 0,
        })

    conn.close()
    return topics


def get_english_lesson(topic_slug):
    """Build a lesson dict from KB content for a given topic."""
    conn = _connect("english")
    if not conn:
        return {"content": "", "key_concept": "", "common_mistake": ""}

    content_parts = []
    key_concepts = []
    mistakes = []

    if topic_slug == "punctuation":
        rows = conn.execute(
            "SELECT mark, rule_text, correct_example, incorrect_example FROM punctuation_rules"
        ).fetchall()
        for r in rows:
            content_parts.append(f"**{r['mark']}:** {r['rule_text']}")
            if r["correct_example"]:
                content_parts.append(f"  ✓ {r['correct_example']}")
            if r["incorrect_example"]:
                content_parts.append(f"  ✗ {r['incorrect_example']}")
            key_concepts.append(f"Use {r['mark']} correctly: {r['rule_text'][:60]}")
        mistakes.append(
            "Relying on 'sounds right' instead of knowing the actual rule. "
            "Many punctuation errors feel natural because they mirror speech patterns."
        )

    elif topic_slug == "vocabulary":
        rows = conn.execute(
            "SELECT word_1, word_2, definition_1, definition_2, example_1, example_2 "
            "FROM confusing_words"
        ).fetchall()
        for r in rows:
            content_parts.append(f"**{r['word_1']}** = {r['definition_1']}")
            if r["example_1"]:
                content_parts.append(f"  Example: {r['example_1']}")
            content_parts.append(f"**{r['word_2']}** = {r['definition_2']}")
            if r["example_2"]:
                content_parts.append(f"  Example: {r['example_2']}")
            content_parts.append("")
            key_concepts.append(
                f"Know the difference: {r['word_1']} vs {r['word_2']}"
            )
        mistakes.append(
            "Assuming similar-sounding or similar-spelled words have the same meaning. "
            "On the TEAS, these pairs are tested specifically to catch this error."
        )

    else:
        # Grammar or Sentence Structure — from rules table
        meta = _ENGLISH_TOPIC_MAP.get(topic_slug)
        if meta and "categories" in meta:
            placeholders = ",".join("?" * len(meta["categories"]))
            rows = conn.execute(
                f"SELECT category, rule_text, correct_example, incorrect_example, explanation "
                f"FROM rules WHERE category IN ({placeholders})",
                meta["categories"],
            ).fetchall()
            for r in rows:
                content_parts.append(f"[{r['category'].replace('_', ' ').title()}] {r['rule_text']}")
                if r["correct_example"]:
                    content_parts.append(f"  ✓ {r['correct_example'][:120]}")
                if r["incorrect_example"]:
                    content_parts.append(f"  ✗ {r['incorrect_example'][:120]}")
                if r["explanation"]:
                    key_concepts.append(r["explanation"][:100])
                mistakes.append(r["rule_text"][:100])

    conn.close()

    return {
        "content": "\n".join(content_parts) if content_parts else "Lesson content coming soon.",
        "key_concept": key_concepts[0] if key_concepts else "Master the rules in this topic.",
        "common_mistake": mistakes[0] if mistakes else "Rushing through without checking each rule.",
    }


def get_english_practice(topic_slug):
    """Return a single practice question for the topic from the KB."""
    conn = _connect("english")
    if not conn:
        return None

    question = None

    if topic_slug == "punctuation":
        row = conn.execute(
            "SELECT mark, rule_text, correct_example, incorrect_example "
            "FROM punctuation_rules ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if row:
            question = {
                "question_text": f"Which sentence uses the {row['mark']} correctly?",
                "options": _shuffle_options(
                    row["correct_example"],
                    row["incorrect_example"],
                ),
                "correct_index": 0,  # _shuffle_options puts correct first
                "hint": f"The rule: {row['rule_text']}",
            }

    elif topic_slug == "vocabulary":
        row = conn.execute(
            "SELECT word_1, word_2, definition_1, definition_2, example_1, example_2 "
            "FROM confusing_words ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if row:
            # Build a fill-in-the-blank style question
            blank = f"___"
            q_text = (
                f'Choose the correct word: "{row["example_1"] or row["example_2"]}" '
                f"(if {row['word_1']} is correct) or "
                f'"{row["example_2"] or row["example_1"]}" '
                f"(if {row['word_2']} is correct)."
            )
            # Simpler: definition matching
            question = {
                "question_text": (
                    f"Which word means: \"{row['definition_1']}\"?"
                ),
                "options": _shuffle_options(
                    row["word_1"],
                    row["word_2"],
                    f"{row['word_1']} (but spelled differently)",
                    f"{row['word_2']} (with a different meaning)",
                ),
                "correct_index": 0,
                "hint": f"Think about what {row['word_2']} means: {row['definition_2']}",
            }

    else:
        # Grammar or Sentence Structure
        meta = _ENGLISH_TOPIC_MAP.get(topic_slug)
        if meta and "categories" in meta:
            placeholders = ",".join("?" * len(meta["categories"]))
            row = conn.execute(
                f"SELECT rule_text, correct_example, incorrect_example, explanation "
                f"FROM rules WHERE category IN ({placeholders}) "
                f"AND incorrect_example IS NOT NULL AND incorrect_example != '' "
                f"ORDER BY RANDOM() LIMIT 1",
                meta["categories"],
            ).fetchone()
            if row:
                question = {
                    "question_text": f"Which sentence is correct?",
                    "options": _shuffle_options(
                        row["correct_example"],
                        row["incorrect_example"],
                    ),
                    "correct_index": 0,
                    "hint": f"The rule: {row['rule_text']}",
                }

    conn.close()
    return question


def get_english_quiz_questions(topic_slug=None, count=5):
    """Return a list of quiz questions for the topic from the KB."""
    conn = _connect("english")
    if not conn:
        return []

    questions = []

    if topic_slug is None:
        # No topic specified — pull from all topics
        topic_slug = "grammar"  # default

    if topic_slug == "punctuation":
        # Punctuation rules don't have incorrect_example, so generate questions differently
        # Pull rules and create wrong versions by removing punctuation
        rows = conn.execute(
            "SELECT mark, rule_text, correct_example "
            "FROM punctuation_rules "
            "ORDER BY RANDOM() LIMIT ?",
            (max(count * 2, 6),),
        ).fetchall()
        # Gather all correct examples as distractor pool
        all_examples = [r["correct_example"] for r in rows if r["correct_example"]]
        import re
        for r in rows:
            correct = r["correct_example"]
            # Create wrong version: replace the punctuation mark with nothing
            wrong = re.sub(r'[,;:]', '', correct)
            if wrong == correct:
                continue
            # Pick 2 extra distractors from other punctuation examples
            extras = [e for e in all_examples if e != correct and e != wrong]
            extra_a = extras[0] if len(extras) >= 1 else None
            extra_b = extras[1] if len(extras) >= 2 else None
            opts = _shuffle_options(correct, wrong, extra_a, extra_b)
            questions.append({
                "question_text": f"Which sentence uses the {r['mark']} correctly?",
                "options": opts,
                "correct_index": 0,
                "explanation": f"The rule for {r['mark']}: {r['rule_text']}",
                "topic": "Punctuation",
            })
            if len(questions) >= count:
                break

    elif topic_slug == "vocabulary":
        rows = conn.execute(
            "SELECT word_1, word_2, definition_1, definition_2, example_1, example_2 "
            "FROM confusing_words ORDER BY RANDOM() LIMIT ?",
            (count,),
        ).fetchall()
        for r in rows:
            questions.append({
                "question_text": f"Which word means: \"{r['definition_1']}\"?",
                "options": _shuffle_options(
                    r["word_1"],
                    r["word_2"],
                    "Neither word fits this definition",
                    "Both words mean the same thing",
                ),
                "correct_index": 0,
                "explanation": (
                    f"{r['word_1']} means {r['definition_1']}. "
                    f"{r['word_2']} means {r['definition_2']}."
                ),
                "topic": "Vocabulary",
            })

    else:
        # Grammar or Sentence Structure — gather extra wrong examples as distractors
            meta = _ENGLISH_TOPIC_MAP.get(topic_slug)
            if meta and "categories" in meta:
                placeholders = ",".join("?" * len(meta["categories"]))
                rows = conn.execute(
                    f"SELECT category, rule_text, correct_example, incorrect_example, explanation "
                    f"FROM rules WHERE category IN ({placeholders}) "
                    f"AND incorrect_example IS NOT NULL AND incorrect_example != '' "
                    f"ORDER BY RANDOM() LIMIT ?",
                    (*meta["categories"], max(count * 3, 10)),
                ).fetchall()

                # Collect extra incorrect examples from OTHER rules as distractors
                all_wrong = [r["incorrect_example"] for r in rows if r["incorrect_example"]]

                for r in rows[:count]:
                    correct = r["correct_example"]
                    wrong = r["incorrect_example"]
                    # Pick 2 extra distractors from other rules (not the same as correct/wrong)
                    extras = [w for w in all_wrong if w != correct and w != wrong]
                    extra_a = extras[0] if len(extras) >= 1 else None
                    extra_b = extras[1] if len(extras) >= 2 else None
                    opts = _shuffle_options(correct, wrong, extra_a, extra_b)
                    questions.append({
                        "question_text": "Which sentence is grammatically correct?",
                        "options": opts,
                        "correct_index": 0,
                        "explanation": r["explanation"] or r["rule_text"],
                        "topic": r["category"].replace("_", " ").title(),
                    })

    conn.close()
    return questions


def get_english_misconceptions(category=None, limit=5):
    """Return misconception entries — useful for wrong-answer explanations."""
    conn = _connect("english")
    if not conn:
        return []

    if category:
        rows = conn.execute(
            "SELECT misconception, wrong_pattern, correct_pattern, example, explanation "
            "FROM misconceptions WHERE category = ? ORDER BY RANDOM() LIMIT ?",
            (category, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT misconception, wrong_pattern, correct_pattern, example, explanation "
            "FROM misconceptions ORDER BY RANDOM() LIMIT ?",
            (limit,),
        ).fetchall()

    results = [dict(r) for r in rows]
    conn.close()
    return results


# ===========================================================================
# Math Knowledge Base
# ===========================================================================

def get_math_topics():
    """Return list of math topics with question counts.

    Each topic dict has: name, slug, question_count, readiness_pct.
    """
    conn = _connect("unified")
    rows = conn.execute(
        "SELECT topic, COUNT(*) as cnt FROM questions "
        "WHERE subject = 'math' GROUP BY topic ORDER BY topic"
    ).fetchall()
    conn.close()
    return [
        {
            "name": r["topic"],
            "slug": _slugify(r["topic"]),
            "question_count": r["cnt"],
            "readiness_pct": 0,
        }
        for r in rows
    ]


def get_math_lesson(topic):
    """Return a lesson dict for a math *topic* (slug or display name).

    Returns {content, key_concept, common_mistake}.
    """
    conn = _connect("unified")
    rows = conn.execute(
        "SELECT question_text, correct_answer, explanation, difficulty "
        "FROM questions WHERE subject = 'math' AND topic = ? "
        "ORDER BY RANDOM() LIMIT 3",
        (topic,),
    ).fetchall()
    conn.close()

    if not rows:
        # Try slug match
        all_topics = get_math_topics()
        match = next((t["name"] for t in all_topics if t["slug"] == topic), None)
        if match:
            return get_math_lesson(match)
        return {"content": "", "key_concept": "", "common_mistake": ""}

    sample = rows[0]
    key_concept = f"Sample question: {sample['question_text']}\nCorrect answer: {sample['correct_answer']}"
    common_mistake = sample["explanation"] or ""
    content_parts = []
    for r in rows:
        content_parts.append(
            f"Q: {r['question_text']}\nA: {r['correct_answer']} ({r['difficulty']})"
        )
        if r["explanation"]:
            content_parts.append(f"  Explanation: {r['explanation']}")

    return {
        "content": "\n\n".join(content_parts),
        "key_concept": key_concept,
        "common_mistake": common_mistake,
    }


def get_math_quiz_questions(topic=None, count=5):
    """Return quiz questions for math.

    Each dict: question_text, options (list of 4), correct_index (always 0),
    explanation, topic, difficulty.
    """
    import random, json

    conn = _connect("unified")
    if topic:
        rows = conn.execute(
            "SELECT question_text, correct_answer, wrong_answers, explanation, topic, difficulty "
            "FROM questions WHERE subject = 'math' AND topic = ? AND wrong_answers LIKE '[%' "
            "ORDER BY RANDOM() LIMIT ?",
            (topic, count),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT question_text, correct_answer, wrong_answers, explanation, topic, difficulty "
            "FROM questions WHERE subject = 'math' AND wrong_answers LIKE '[%' "
            "ORDER BY RANDOM() LIMIT ?",
            (count,),
        ).fetchall()
    conn.close()

    results = []
    for r in rows:
        stem, inline_opts = _parse_mcq_options(r["question_text"])
        correct_text = inline_opts.get(r["correct_answer"], r["correct_answer"])
        # Use the other 3 parsed options as distractors
        distractors = [v for k, v in inline_opts.items() if k != r["correct_answer"]]
        while len(distractors) < 3:
            distractors.append("None of the above")
        options = _shuffle_options(correct_text, distractors[0], distractors[1], distractors[2])
        results.append({
            "question_text": stem,
            "options": options,
            "correct_index": 0,
            "explanation": r["explanation"] or "",
            "topic": r["topic"],
            "difficulty": r["difficulty"] or "medium",
        })
    return results


# ===========================================================================
# Science Knowledge Base
# ===========================================================================

def get_science_topics():
    """Return list of science topics from the unified KB.

    Each topic dict: name, slug, question_count, readiness_pct.
    """
    conn = _connect("science")
    rows = conn.execute(
        "SELECT topic, COUNT(*) as cnt FROM questions "
        "WHERE subject = 'science' "
        "GROUP BY topic ORDER BY topic"
    ).fetchall()
    conn.close()
    return [
        {
            "name": r["topic"],
            "slug": _slugify(r["topic"]),
            "question_count": r["cnt"],
            "readiness_pct": 0,
        }
        for r in rows
    ]


def get_science_lesson(topic):
    """Return a lesson dict for a science topic (slug or display name).

    Returns {content, key_concept, common_mistake}.
    """
    conn = _connect("science")
    rows = conn.execute(
        "SELECT question_text, correct_answer, explanation "
        "FROM questions WHERE subject = 'science' AND topic = ? "
        "ORDER BY RANDOM() LIMIT 3",
        (topic,),
    ).fetchall()
    conn.close()

    if not rows:
        all_topics = get_science_topics()
        match = next((t["name"] for t in all_topics if t["slug"] == topic), None)
        if match:
            return get_science_lesson(match)
        return {"content": "", "key_concept": "", "common_mistake": ""}

    key_concept = f"Sample: {rows[0]['question_text']}\nAnswer: {rows[0]['correct_answer']}"
    common_mistake = rows[0]["explanation"] or ""
    content_parts = []
    for r in rows:
        content_parts.append(f"Q: {r['question_text']}\nA: {r['correct_answer']}")
        if r["explanation"]:
            content_parts.append(f"  Explanation: {r['explanation']}")

    return {
        "content": "\n\n".join(content_parts),
        "key_concept": key_concept,
        "common_mistake": common_mistake,
    }


def _get_science_distractors(correct_answer, topic=None, count=3):
    """Pull random correct_answers from same-topic questions as distractors.
    Falls back to any science question if topic pool is too small.
    """
    conn = _connect("science")
    distractors = []

    # Try same-topic distractors first
    if topic:
        rows = conn.execute(
            "SELECT correct_answer FROM questions "
            "WHERE subject = 'science' AND correct_answer != ? AND topic = ? "
            "ORDER BY RANDOM() LIMIT ?",
            (correct_answer, topic, count),
        ).fetchall()
        distractors = [r["correct_answer"] for r in rows]

    # Fall back to any science question if same-topic pool is small
    if len(distractors) < count:
        remaining = count - len(distractors)
        rows = conn.execute(
            "SELECT correct_answer FROM questions "
            "WHERE subject = 'science' AND correct_answer != ? "
            "ORDER BY RANDOM() LIMIT ?",
            (correct_answer, remaining),
        ).fetchall()
        distractors.extend(r["correct_answer"] for r in rows)

    conn.close()
    return distractors[:count]


def _get_science_text_distractors(question_id, topic=None, count=3):
    """Pull random option TEXT from other science questions as distractors.
    Parses question_text to extract actual option text, not letters.
    """
    conn = _connect("science")
    distractors = []
    seen = set()

    # Try same-topic first, then any science question
    for where_clause in (
        f"subject = 'science' AND id != {question_id}" + (f" AND topic = '{topic}'" if topic else ""),
        f"subject = 'science' AND id != {question_id}",
    ):
        if len(distractors) >= count:
            break
        rows = conn.execute(
            f"SELECT question_text, correct_answer FROM questions "
            f"WHERE {where_clause} ORDER BY RANDOM() LIMIT 20"
        ).fetchall()
        for r in rows:
            _, opts = _parse_mcq_options(r["question_text"])
            # Add all parsed options except the one matching this question's correct
            for letter, text in opts.items():
                if text and text not in seen:
                    seen.add(text)
                    distractors.append(text)
            if len(distractors) >= count * 2:
                break

    conn.close()
    import random
    random.shuffle(distractors)
    return distractors[:count]


def get_science_quiz_questions(topic=None, count=5):
    """Return quiz questions for science.

    Uses correct_answers from other questions as plausible distractors.
    Each dict: question_text, options (4), correct_index (0), explanation, topic, difficulty.
    """
    conn = _connect("science")
    if topic:
        rows = conn.execute(
            "SELECT id, question_text, correct_answer, explanation, topic, difficulty "
            "FROM questions WHERE subject = 'science' AND topic = ? "
            "ORDER BY RANDOM() LIMIT ?",
            (topic, count),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, question_text, correct_answer, explanation, topic, difficulty "
            "FROM questions WHERE subject = 'science' "
            "ORDER BY RANDOM() LIMIT ?",
            (count,),
        ).fetchall()
    conn.close()

    results = []
    for r in rows:
        stem, inline_opts = _parse_mcq_options(r["question_text"])
        correct_text = inline_opts.get(r["correct_answer"], r["correct_answer"])
        # Use the other 3 parsed options as distractors
        distractors = [v for k, v in inline_opts.items() if k != r["correct_answer"]]
        while len(distractors) < 3:
            distractors.append("None of the above")
        options = _shuffle_options(correct_text, distractors[0], distractors[1], distractors[2])
        results.append({
            "question_text": stem,
            "options": options,
            "correct_index": 0,
            "explanation": r["explanation"] or "",
            "topic": r["topic"],
            "difficulty": r["difficulty"] or "medium",
        })
    return results


# ===========================================================================
# Reading Knowledge Base
# ===========================================================================

def get_reading_topics():
    """Return list of reading topics from the unified KB.

    Each topic dict: name, slug, question_count, readiness_pct.
    """
    conn = _connect("reading")
    rows = conn.execute(
        "SELECT topic, COUNT(*) as cnt FROM questions "
        "WHERE subject = 'reading' "
        "GROUP BY topic ORDER BY topic"
    ).fetchall()
    conn.close()
    return [
        {
            "name": r["topic"],
            "slug": _slugify(r["topic"]),
            "question_count": r["cnt"],
            "readiness_pct": 0,
        }
        for r in rows
    ]


def get_reading_lesson(topic):
    """Return a lesson dict for a reading topic (slug or display name).

    Returns {content, key_concept, common_mistake}.
    """
    conn = _connect("reading")
    rows = conn.execute(
        "SELECT question_text, correct_answer, explanation "
        "FROM questions WHERE subject = 'reading' AND topic = ? "
        "ORDER BY RANDOM() LIMIT 3",
        (topic,),
    ).fetchall()
    conn.close()

    if not rows:
        all_topics = get_reading_topics()
        match = next((t["name"] for t in all_topics if t["slug"] == topic), None)
        if match:
            return get_reading_lesson(match)
        return {"content": "", "key_concept": "", "common_mistake": ""}

    key_concept = f"Sample: {rows[0]['question_text']}\nAnswer: {rows[0]['correct_answer']}"
    common_mistake = rows[0]["explanation"] or ""
    content_parts = []
    for r in rows:
        content_parts.append(f"Q: {r['question_text']}\nA: {r['correct_answer']}")
        if r["explanation"]:
            content_parts.append(f"  Explanation: {r['explanation']}")

    return {
        "content": "\n\n".join(content_parts),
        "key_concept": key_concept,
        "common_mistake": common_mistake,
    }


def _get_reading_distractors(correct_answer, topic=None, count=3):
    """Pull random correct_answers from other reading questions as distractors."""
    conn = _connect("reading")
    distractors = []
    if topic:
        rows = conn.execute(
            "SELECT correct_answer FROM questions "
            "WHERE subject = 'reading' AND correct_answer != ? AND topic = ? "
            "ORDER BY RANDOM() LIMIT ?",
            (correct_answer, topic, count),
        ).fetchall()
        distractors = [r["correct_answer"] for r in rows]
    if len(distractors) < count:
        remaining = count - len(distractors)
        rows = conn.execute(
            "SELECT correct_answer FROM questions "
            "WHERE subject = 'reading' AND correct_answer != ? "
            "ORDER BY RANDOM() LIMIT ?",
            (correct_answer, remaining),
        ).fetchall()
        distractors.extend(r["correct_answer"] for r in rows)
    conn.close()
    return distractors[:count]


def _get_reading_text_distractors(question_id, topic=None, count=3):
    """Pull random option TEXT from other reading questions as distractors.
    Parses question_text to extract actual option text, not letters.
    """
    conn = _connect("reading")
    distractors = []
    seen = set()

    for where_clause in (
        f"subject = 'reading' AND id != {question_id}" + (f" AND topic = '{topic}'" if topic else ""),
        f"subject = 'reading' AND id != {question_id}",
    ):
        if len(distractors) >= count:
            break
        rows = conn.execute(
            f"SELECT question_text, correct_answer FROM questions "
            f"WHERE {where_clause} ORDER BY RANDOM() LIMIT 20"
        ).fetchall()
        for r in rows:
            _, opts = _parse_mcq_options(r["question_text"])
            for letter, text in opts.items():
                if text and text not in seen:
                    seen.add(text)
                    distractors.append(text)
            if len(distractors) >= count * 2:
                break

    conn.close()
    import random
    random.shuffle(distractors)
    return distractors[:count]


def get_reading_quiz_questions(topic=None, count=5):
    """Return quiz questions for reading.

    Uses correct_answers from other questions as plausible distractors.
    Each dict: question_text, options (4), correct_index (0), explanation, topic, difficulty.
    """
    conn = _connect("reading")
    if topic:
        rows = conn.execute(
            "SELECT id, question_text, correct_answer, explanation, topic, difficulty "
            "FROM questions WHERE subject = 'reading' AND topic = ? "
            "ORDER BY RANDOM() LIMIT ?",
            (topic, count),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, question_text, correct_answer, explanation, topic, difficulty "
            "FROM questions WHERE subject = 'reading' "
            "ORDER BY RANDOM() LIMIT ?",
            (count,),
        ).fetchall()
    conn.close()

    results = []
    for r in rows:
        stem, inline_opts = _parse_mcq_options(r["question_text"])
        correct_text = inline_opts.get(r["correct_answer"], r["correct_answer"])
        # Use the other 3 parsed options as distractors
        distractors = [v for k, v in inline_opts.items() if k != r["correct_answer"]]
        while len(distractors) < 3:
            distractors.append("None of the above")
        options = _shuffle_options(correct_text, distractors[0], distractors[1], distractors[2])
        results.append({
            "question_text": stem,
            "options": options,
            "correct_index": 0,
            "explanation": r["explanation"] or "",
            "topic": r["topic"],
            "difficulty": r["difficulty"] or "medium",
        })
    return results



# ===========================================================================
# Helpers
# ===========================================================================

def _sanitize_latex(text):
    """Strip LaTeX escape characters and convert to readable plain text.

    Handles: backslash-dollar -> dollar, backslash-parens removed,
    backslash-frac{a}{b} -> a/b, backslash-times -> x,
    backslash-div -> division sign, backslash-sqrt{x} -> sqrt(x),
    backslash-log -> log, x^{n} -> x^n, and stray backslashes.
    """
    if not text:
        return text
    import re
    # Remove inline math delimiters
    text = text.replace('\\(', '').replace('\\)', '')
    # \frac{a}{b} -> a/b
    text = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', r'\1/\2', text)
    # \sqrt{x} -> √x
    text = re.sub(r'\\sqrt\{([^}]*)\}', r'√\1', text)
    # \times -> × (multiplication)
    text = text.replace('\\times', '×')
    # \div -> ÷
    text = text.replace('\\div', '÷')
    # \log -> log
    text = text.replace('\\log', 'log')
    # x^{n} -> x^n  (superscripts in braces)
    text = re.sub(r'\^\{([^}]*)\}', r'^\1', text)
    # \$ -> $ (literal dollar/currency sign)
    text = text.replace('\\$', '$')
    # Remove any remaining stray backslashes (keep \n for newlines)
    text = re.sub(r'\\(?![nrt])', '', text)
    return text.strip()


def _parse_mcq_options(question_text):
    """Parse A) B) C) D) options from question_text.

    Returns (stem, {A: text, B: text, ...}) where stem is the question
    without the inline options. Handles 'A)', '(A)', 'A.' formats,
    options on separate lines, and all 4 options on one line
    (double-space, single-space, or comma separated).
    Strips LaTeX escaping from both stem and option text.
    """
    import re
    lines = question_text.split("\n")
    stem_lines = []
    options = {}
    for line in lines:
        stripped = line.strip()
        # Match at start of line: "A) text", "(A) text", "A. text"
        m = re.match(r"^\(?([A-D])\)?[.)]\s*(.*)", stripped)
        if m:
            letter = m.group(1)
            rest = m.group(2)
            # Check if rest contains more options:
            # "Monday  B) Tuesday" or "3 cups B) 4 cups" or "5 + (3 × 2), B) (5 + 3)"
            if re.search(r"[,;\s]\s*[A-D]\)", rest):
                parts = re.split(r"(?:[,;]?\s+)([A-D]\))", rest)
                options[letter] = parts[0].strip()
                # parts alternates: text, "B)", text, "C)", text, ...
                for k in range(1, len(parts) - 1, 2):
                    opt_letter = parts[k][0]  # "B)" -> "B"
                    opt_text = parts[k + 1].strip() if k + 1 < len(parts) else ""
                    options[opt_letter] = opt_text
            else:
                options[letter] = rest.strip()
        else:
            stem_lines.append(line)
    stem = _sanitize_latex("\n".join(stem_lines).strip())
    # Sanitize option text too
    options = {k: _sanitize_latex(v) for k, v in options.items()}
    return stem, options


def _shuffle_options(correct, wrong, extra_a=None, extra_b=None):
    """Return a 4-option list with correct always at index 0.
    Extra options are filler for when we only have 2 real ones."""
    import random
    options = [correct, wrong]
    if extra_a:
        options.append(extra_a)
    if extra_b:
        options.append(extra_b)
    # Pad to 4 if needed
    while len(options) < 4:
        options.append("None of the above")
    # Shuffle indices 1-3, keep correct at 0
    rest = options[1:]
    random.shuffle(rest)
    return [options[0]] + rest
