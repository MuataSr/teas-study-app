#!/usr/bin/env python3
"""
Generate TEAS Science questions using Z.AI cloud API.
Produces ~8 questions per topic across all 24 TEAS science topics.
Outputs JSON file for insertion into science.db high_yield_qa table.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, ".env")

# Load .env
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

ZAI_API_KEY = os.environ.get("ZAI_API_KEY", "")
ZAI_BASE_URL = os.environ.get("ZAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4").rstrip("/")
ZAI_MODEL = os.environ.get("ZAI_MODEL", "glm-5-turbo")

# 24 TEAS Science topics organized by category
TOPICS = {
    "Anatomy & Physiology": [
        "Cardiovascular system",
        "Nervous system",
        "Endocrine system",
        "Muscular system",
        "Urinary system",
        "Blood typing and compatibility",
        "Tissue types",
        "Immune system - types of immunity",
    ],
    "Life Science": [
        "Cell theory and cell types",
        "Cell division",
        "DNA structure and replication",
        "Photosynthesis and cellular respiration",
        "Ecology",
        "Macromolecules",
    ],
    "Physical Science": [
        "Chemical bonds",
        "Acids, bases, and pH",
        "Periodic table trends",
        "States of matter and phase changes",
        "Metric system and conversions",
    ],
    "Scientific Reasoning": [
        "Experimental design",
        "Identifying variables",
        "Interpreting data",
        "Drawing conclusions",
        "Endocrine system - blood glucose regulation",
    ],
}

QUESTIONS_PER_TOPIC = 8

SYSTEM_PROMPT = """You are a TEAS (Test of Essential Academic Skills) Science question writer. Generate multiple-choice questions in EXACT JSON format.

RULES:
- Each question must have exactly 4 answer options (A, B, C, D)
- One option must be clearly correct
- Three options must be plausible but incorrect distractors (common student mistakes)
- Questions must be appropriate for nursing program entrance exam level
- Use proper medical/scientific terminology
- Explanations should be concise (1-2 sentences) and educational

OUTPUT FORMAT: Return ONLY a JSON array, no markdown fences, no extra text."""

def call_zai(prompt, max_retries=3):
    """Call Z.AI chat completions API."""
    url = f"{ZAI_BASE_URL}/chat/completions"
    payload = json.dumps({
        "model": ZAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 4096,
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {ZAI_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"].strip()
                # Strip markdown fences if present
                if content.startswith("```"):
                    content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                if content.startswith("```"):
                    content = content[3:]
                content = content.strip()
                return content
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} (attempt {attempt+1})")
            if e.code == 429:
                time.sleep(10)
            elif e.code >= 500:
                time.sleep(5)
            else:
                raise
        except Exception as e:
            print(f"  Error: {e} (attempt {attempt+1})")
            time.sleep(3)
    return None


def generate_questions_for_topic(category, topic, count=QUESTIONS_PER_TOPIC):
    """Generate questions for a specific topic."""
    prompt = f"""Generate {count} TEAS Science multiple-choice questions about: {topic}

Category: {category}

For each question provide:
- "question": the question text
- "correct_answer": the correct answer text
- "wrong_answers": array of 3 plausible incorrect answers
- "explanation": brief explanation of why the correct answer is right

Return a JSON array of {count} objects."""

    content = call_zai(prompt)
    if not content:
        return []

    try:
        questions = json.loads(content)
        if not isinstance(questions, list):
            return []
        # Validate and tag each question
        tagged = []
        for q in questions:
            if not all(k in q for k in ["question", "correct_answer", "explanation"]):
                continue
            wrong = q.get("wrong_answers", [])
            if not isinstance(wrong, list) or len(wrong) < 3:
                wrong = ["None of the above", "Both A and C", "Not enough information"]
            tagged.append({
                "question": q["question"],
                "correct_answer": q["correct_answer"],
                "wrong_answers": wrong[:3],
                "explanation": q["explanation"],
                "body_system": topic,
                "category": category,
                "difficulty": "medium",
            })
        return tagged
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return []


def main():
    if not ZAI_API_KEY:
        print("ERROR: ZAI_API_KEY not set in pipeline/.env")
        sys.exit(1)

    all_questions = []
    total_topics = sum(len(v) for v in TOPICS.values())

    print(f"Generating questions for {total_topics} topics...")
    print(f"Model: {ZAI_MODEL}")
    print(f"Target: ~{total_topics * QUESTIONS_PER_TOPIC} questions")
    print()

    done = 0
    for category, topics in TOPICS.items():
        for topic in topics:
            done += 1
            print(f"[{done}/{total_topics}] {topic} ({category})...", end=" ", flush=True)
            qs = generate_questions_for_topic(category, topic)
            print(f"{len(qs)} questions")
            all_questions.extend(qs)
            time.sleep(1)  # Rate limit

    print(f"\nTotal generated: {len(all_questions)} questions")

    # Save output
    out_path = os.path.join(SCRIPT_DIR, "runs", "science", "generated_questions.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_questions, f, indent=2)
    print(f"Saved to {out_path}")

    # Stats
    from collections import Counter
    topic_counts = Counter(q["body_system"] for q in all_questions)
    print(f"\nQuestions per topic:")
    for topic, count in sorted(topic_counts.items()):
        print(f"  {topic}: {count}")


if __name__ == "__main__":
    main()
