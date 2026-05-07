#!/usr/bin/env python3
"""
Batch question generator for TEAS study app.
Calls local llama-server (4B model) to generate new questions per subject/topic.
Fully resumable — safe to re-run at any time.

Usage:
  python3 generate_questions.py --subject math
  python3 generate_questions.py --subject science --topic "Cell theory"
  python3 generate_questions.py --subject english --limit 20
  python3 generate_questions.py --status
"""

import sqlite3
import json
import urllib.request
import urllib.error
import time
import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'kb', 'teas_unified.db')
LOG_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'kb', 'generate_log.jsonl')
DEFAULT_LLM_PORT = 8082
TARGET_PER_SUBJECT = 500
DELAY_BETWEEN = 1.0

# TEAS topic definitions with weight guidance for distribution
TOPIC_GUIDANCE = {
    "math": {
        "Number sense": "fractions, decimals, percentages, place value, number lines",
        "Number Operations": "addition, subtraction, multiplication, division of whole numbers, fractions, decimals",
        "Measurement": "conversions (metric/imperial), perimeter, area, volume, temperature",
        "Data Interpretation": "reading charts, graphs, tables, mean/median/mode, probability",
        "Algebraic representations": "translating words to expressions, algebraic expressions",
        "Equations and inequalities": "solving linear equations, inequalities, multi-step",
        "Patterns, relationships, and functions": "sequences, function tables, coordinate plane",
        "Ratios and proportional reasoning": "ratios, proportions, unit rates, scale",
        "Variables, expressions, and operations": "evaluating expressions, order of operations, like terms",
        "Properties of number and operations": "commutative, associative, distributive, identity properties",
    },
    "science": {
        "Anatomy & Physiology": "major body systems: cardiovascular, respiratory, digestive, nervous, muscular, skeletal, endocrine, immune, urinary, reproductive",
        "Life Science / Biology": "cell structure, genetics, evolution, ecology, classification",
        "Chemistry": "atomic structure, periodic table, chemical bonds, reactions, solutions, acids/bases",
        "Scientific Reasoning": "experimental design, variables, drawing conclusions, interpreting data",
        "Biology": "cell theory, DNA, genetics, natural selection, photosynthesis",
        "Cell theory and cell types": "prokaryotic vs eukaryotic, organelles, cell membrane",
        "Macromolecules": "carbohydrates, lipids, proteins, nucleic acids",
        "Acids, bases, and pH": "pH scale, neutralization, indicators, buffers",
        "Chemical bonds": "ionic, covalent, hydrogen bonding",
        "Metric system and conversions": "SI units, prefixes, dimensional analysis",
        "Periodic table trends": "atomic radius, electronegativity, ionization energy",
        "States of matter and phase changes": "solid, liquid, gas, plasma, melting, boiling, sublimation",
        "Blood typing and compatibility": "ABO, Rh factor, universal donor/recipient",
        "Cell division": "mitosis, meiosis, cell cycle",
        "DNA structure and replication": "double helix, base pairing, replication fork",
        "Photosynthesis and cellular respiration": "light reactions, Calvin cycle, ATP, glycolysis",
        "Cardiovascular system": "heart structure, blood vessels, blood flow, cardiac cycle",
        "Endocrine system": "hormones, glands, feedback loops",
        "Muscular system": "muscle types, contraction, sliding filament",
        "Nervous system": "neurons, synapses, CNS vs PNS, reflexes",
        "Immune system - types of immunity": "innate vs adaptive, antibodies, vaccines",
        "Tissue types": "epithelial, connective, muscle, nervous",
        "Urinary system": "kidneys, nephron, filtration, reabsorption",
        "Ecology": "food chains, biomes, populations, ecosystems",
        "Experimental design": "hypothesis, control group, independent/dependent variables",
        "Identifying variables": "independent, dependent, controlled variables in experiments",
        "Drawing conclusions": "analyzing results, correlation vs causation",
        "Interpreting data": "reading tables, graphs, identifying trends",
    },
    "english": {
        "Commonly Confused Words": "affect/effect, their/there/they're, its/it's, your/you're, then/than, accept/except",
        "Subject-Verb Agreement": "singular/plural subjects, compound subjects, intervening phrases",
        "Verb Tenses": "past, present, future, perfect tenses, progressive, irregular verbs",
        "Pronoun Usage": "subject/object pronouns, pronoun-antecedent agreement, who/whom",
        "Word Meaning in Context": "context clues, denotation vs connotation, figurative language",
        "Sentence Structure": "simple, compound, complex, compound-complex, fragments, run-ons",
        "Parallel Structure": "parallel items in lists, comparisons, conjunctions",
        "Modifiers": "misplaced, dangling, squinting modifiers",
        "Parts of Speech": "nouns, verbs, adjectives, adverbs, prepositions, conjunctions, interjections",
        "Comma Usage": "serial comma, introductory clauses, appositives, coordinating conjunctions",
        "Sentence Revision": "clarity, conciseness, redundancy, combining sentences",
        "Transition Words": "however, therefore, furthermore, meanwhile, consequently",
        "Active vs Passive Voice": "identifying and converting active/passive constructions",
        "Topic Sentences and Thesis": "identifying main idea, topic sentences, thesis statements",
        "Supporting Evidence": "relevant details, examples, facts vs opinions in paragraphs",
        "Paragraph Organization": "logical order, chronological, spatial, order of importance",
        "Formal vs Informal Language": "register, tone, audience awareness, slang",
        "Apostrophe Usage": "possessives, contractions, plurals",
        "Semicolon and Colon Usage": "joining independent clauses, lists, introductions",
    },
}

# Difficulty distribution target: ~30% easy, ~40% medium, ~30% hard
DIFFICULTY_POOL = ["easy"] * 3 + ["medium"] * 4 + ["hard"] * 3


def load_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_gap_counts(conn, subject):
    """Return current count and gap per topic for a subject."""
    current = conn.execute(
        "SELECT topic, COUNT(*) as cnt FROM questions WHERE subject=? GROUP BY topic",
        (subject,)
    ).fetchall()
    total = sum(r["cnt"] for r in current)
    gap = TARGET_PER_SUBJECT - total
    return total, gap, {r["topic"]: r["cnt"] for r in current}


def build_generation_queue(conn, subject, max_per_topic=None):
    """Build a prioritized queue of (topic, count_needed, difficulty) tuples."""
    total, gap, topic_counts = get_gap_counts(conn, subject)
    
    if gap <= 0:
        return []
    
    topics = TOPIC_GUIDANCE.get(subject, {})
    queue = []
    
    # Spread questions across topics — prioritize underrepresented ones
    # Each topic gets at least 1 question, remainder distributed proportionally
    active_topics = [t for t in topics if t in topic_counts or gap > 0]
    
    # Give each topic at least 1 if gap allows
    base = min(len(active_topics), gap)
    remainder = gap - base
    
    # Distribute remainder to topics with fewer questions (fill thin ones first)
    topic_list = sorted(active_topics, key=lambda t: topic_counts.get(t, 0))
    
    counts = {}
    for i, t in enumerate(topic_list):
        counts[t] = 1
        if i < remainder:
            counts[t] += 1
    
    for topic, count in counts.items():
        guidance = topics.get(topic, "")
        for j in range(count):
            diff = DIFFICULTY_POOL[j % len(DIFFICULTY_POOL)]
            if max_per_topic and sum(1 for qt, _, _ in queue if qt == topic) >= max_per_topic:
                continue
            queue.append((topic, diff, guidance))
    
    return queue


def call_llm(prompt, max_retries=3):
    payload = json.dumps({
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
    }).encode()
    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(LLM_URL, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as resp:
                body = resp.read().decode()
                if not body.strip():
                    if attempt < max_retries - 1:
                        wait = (attempt + 1) * 5
                        print(f"  Retry {attempt+1}/{max_retries} in {wait}s: empty response")
                        time.sleep(wait)
                        continue
                    return None
                result = json.loads(body)
                content = result["choices"][0]["message"]["content"].strip()
                # Strip thinking tags if present
                if "</think" in content:
                    content = content.split("</think")[-1].strip()
                if "<think" in content:
                    content = content.split("<think")[0].strip()
                return content
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                print(f"  Retry {attempt+1}/{max_retries} in {wait}s: {e.reason}")
                time.sleep(wait)
            else:
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                print(f"  Retry {attempt+1}/{max_retries} in {wait}s: {e}")
                time.sleep(wait)
            else:
                return None
    return None


def parse_generation_response(content, topic):
    """Parse LLM JSON output into question dict. Returns None on failure."""
    # Try to extract JSON from the response
    try:
        # Find JSON block — might be wrapped in markdown code fences
        json_str = content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        q = json.loads(json_str)
        
        # Validate required fields
        required = ["question", "correct_answer", "wrong_answers", "explanation"]
        for field in required:
            if field not in q or not q[field]:
                return None
        
        if not isinstance(q["wrong_answers"], list) or len(q["wrong_answers"]) < 3:
            return None
        
        return {
            "question_text": q["question"].strip(),
            "correct_answer": q["correct_answer"].strip(),
            "wrong_answers": json.dumps(q["wrong_answers"]),
            "explanation": q["explanation"].strip(),
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def log_entry(action, subject, topic, difficulty, status, qid=None, note=""):
    entry = {
        "action": action,
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "status": status,
        "qid": qid,
        "note": note[:200] if note else "",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def generate_prompt(subject, topic, difficulty, guidance):
    return f"""You are a TEAS (Test of Essential Academic Skills) exam question writer. Generate ONE new multiple-choice question.

SUBJECT: {subject.upper()}
TOPIC: {topic}
DIFFICULTY: {difficulty}
CONTENT AREAS: {guidance}

RULES:
- Write a clear, unambiguous question with exactly 4 answer choices (A, B, C, D)
- The correct answer must be definitively correct — no ambiguity
- Wrong answers must be plausible but clearly wrong (common misconceptions or mistakes)
- Include a brief explanation (2-3 sentences) explaining why the correct answer is right
- Question should be appropriate for nursing program entrance exam level
- Use realistic scenarios, not trivia

Return ONLY valid JSON in this exact format, no other text:
{{
  "question": "Your question text here?",
  "correct_answer": "The correct answer text",
  "wrong_answers": ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"],
  "explanation": "Brief explanation of why the correct answer is right."
}}

Generate the question now:"""


def check_server(port=DEFAULT_LLM_PORT):
    try:
        req = urllib.request.Request(f"http://0.0.0.0:{port}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            models = json.loads(resp.read().decode())
            return True, len(models.get('data', []))
    except Exception as e:
        return False, str(e)


def show_status(conn):
    print(f"\n{'='*60}")
    print(f"TEAS QUESTION STATUS (target: {TARGET_PER_SUBJECT} per subject)")
    print(f"{'='*60}")
    for subject in ["reading", "math", "science", "english"]:
        total, gap, topics = get_gap_counts(conn, subject)
        bar_full = min(total // 10, 50)
        bar_empty = 50 - bar_full
        bar = "█" * bar_full + "░" * bar_empty
        status = "✅ DONE" if gap <= 0 else f"need {gap}"
        print(f"\n  {subject.upper():10s} [{bar}] {total:3d}/500  {status}")
        # Show top 3 thinnest topics
        sorted_topics = sorted(topics.items(), key=lambda x: x[1])
        for t, c in sorted_topics[:3]:
            print(f"    ↳ {t}: {c}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Generate TEAS questions using local 4B model")
    parser.add_argument("--subject", choices=["reading", "math", "science", "english"], help="Subject to generate for")
    parser.add_argument("--topic", type=str, help="Specific topic (within subject)")
    parser.add_argument("--limit", type=int, default=0, help="Max questions to generate (0 = fill to 500)")
    parser.add_argument("--status", action="store_true", help="Show current status only")
    parser.add_argument("--max-per-topic", type=int, default=0, help="Max questions per topic (0 = unlimited)")
    parser.add_argument("--all", action="store_true", help="Generate for all subjects needing questions")
    parser.add_argument("--port", type=int, default=DEFAULT_LLM_PORT, help="llama-server port (default: 8082)")
    args = parser.parse_args()

    global LLM_URL
    LLM_URL = f"http://0.0.0.0:{args.port}/v1/chat/completions"

    conn = load_db()

    if args.status:
        show_status(conn)
        conn.close()
        return

    # Check server
    ok, info = check_server(args.port)
    if not ok:
        print(f"ERROR: Cannot reach llama-server on port {args.port}: {info}")
        sys.exit(1)
    print(f"Server OK — {info} model(s) available\n")

    # Determine which subjects to process
    if args.all:
        subjects = []
        for s in ["math", "science", "english"]:
            total, gap, _ = get_gap_counts(conn, s)
            if gap > 0:
                subjects.append(s)
    elif args.subject:
        subjects = [args.subject]
    else:
        print("ERROR: Specify --subject, --all, or --status")
        sys.exit(1)

    for subject in subjects:
        total, gap, _ = get_gap_counts(conn, subject)
        print(f"\n{'='*60}")
        print(f"GENERATING: {subject.upper()} ({total}/{TARGET_PER_SUBJECT}, need {gap})")
        print(f"{'='*60}")

        if args.topic:
            # Generate for a single topic
            queue = [(args.topic, DIFFICULTY_POOL[i % len(DIFFICULTY_POOL)],
                       TOPIC_GUIDANCE.get(subject, {}).get(args.topic, ""))
                      for i in range(args.limit if args.limit > 0 else 10)]
        else:
            queue = build_generation_queue(conn, subject, args.max_per_topic or None)

        if not queue:
            print("  Nothing to generate — already at target!")
            continue

        if args.limit > 0:
            queue = queue[:args.limit]
            print(f"  Limited to: {args.limit} questions")

        print(f"  Queue: {len(queue)} questions across {len(set(t for t,_,_ in queue))} topics\n")

        stats = {"total": len(queue), "success": 0, "failed": 0}
        start_time = time.time()

        for i, (topic, difficulty, guidance) in enumerate(queue):
            # Re-check gap — might have been filled by previous runs
            current_total = conn.execute("SELECT COUNT(*) FROM questions WHERE subject=?", (subject,)).fetchone()[0]
            if current_total >= TARGET_PER_SUBJECT:
                print(f"  Subject {subject} reached {TARGET_PER_SUBJECT} — stopping!")
                break

            prompt = generate_prompt(subject, topic, difficulty, guidance)
            response = call_llm(prompt)

            if response:
                parsed = parse_generation_response(response, topic)
                if parsed:
                    conn.execute(
                        "INSERT INTO questions (subject, topic, question_text, correct_answer, wrong_answers, explanation, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (subject, topic, parsed["question_text"], parsed["correct_answer"],
                         parsed["wrong_answers"], parsed["explanation"], difficulty)
                    )
                    conn.commit()
                    qid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    log_entry("generate", subject, topic, difficulty, "success", qid)
                    stats["success"] += 1
                    q_short = parsed["question_text"][:60] + "..." if len(parsed["question_text"]) > 60 else parsed["question_text"]
                    print(f"  [{i+1}/{len(queue)}] ID {qid} ({topic}, {difficulty}): {q_short}")
                else:
                    log_entry("generate", subject, topic, difficulty, "failed", note="parse_error: " + response[:100])
                    stats["failed"] += 1
                    print(f"  [{i+1}/{len(queue)}] FAILED (parse error) — {topic}")
            else:
                log_entry("generate", subject, topic, difficulty, "failed", note="no_response")
                stats["failed"] += 1
                print(f"  [{i+1}/{len(queue)}] FAILED (no response) — {topic}")

            if (i + 1) % 25 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                remaining = (len(queue) - i - 1) / rate if rate > 0 else 0
                new_total = conn.execute("SELECT COUNT(*) FROM questions WHERE subject=?", (subject,)).fetchone()[0]
                print(f"\n  --- Progress: {i+1}/{len(queue)} | "
                      f"OK:{stats['success']} FAIL:{stats['failed']} | "
                      f"{subject} now: {new_total}/500 | "
                      f"{rate:.1f} q/min | ~{remaining/60:.0f} min left ---\n")

            time.sleep(DELAY_BETWEEN)

        elapsed = time.time() - start_time
        new_total = conn.execute("SELECT COUNT(*) FROM questions WHERE subject=?", (subject,)).fetchone()[0]
        print(f"\n  DONE in {elapsed/60:.1f} min — {subject}: {total}→{new_total} "
              f"(+{new_total-total}, {stats['failed']} failed)")

    # Final status
    show_status(conn)
    conn.close()


if __name__ == "__main__":
    main()
