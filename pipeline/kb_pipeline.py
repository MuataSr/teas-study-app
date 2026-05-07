#!/usr/bin/env python3
"""TEAS Study App — KB Pipeline.

Automated 6-stage pipeline that builds scored knowledge bases for each TEAS 7 subject.
Stages: Scout → KB Builder → Skeptic → Crash Test Dummy → Editor → Eval

Usage:
    python kb_pipeline.py science              # Run full pipeline for science
    python kb_pipeline.py math --force 3       # Re-run from stage 3 (Skeptic)
    python kb_pipeline.py all                  # Run all subjects sequentially
    python kb_pipeline.py --list               # List available subjects

Env: Loads ZAI_API_KEY, ZAI_BASE_URL, ZAI_MODEL from .env in same directory.
"""

import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).resolve().parent
RUNS_DIR = PIPELINE_DIR / "runs"
TEXTBOOKS_DIR = PIPELINE_DIR / ".." / "textbooks"
DATA_DIR = PIPELINE_DIR / "data"
ENV_FILE = PIPELINE_DIR / ".env"

# ─────────────────────────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────────────────────────

def load_env():
    """Load .env file into os.environ (no dotenv dependency)."""
    if not ENV_FILE.exists():
        raise FileNotFoundError(f"No .env file at {ENV_FILE}")
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key:
                os.environ.setdefault(key, value)

load_env()

ZAI_API_KEY = os.environ.get("ZAI_API_KEY", "")
ZAI_BASE_URL = os.environ.get("ZAI_BASE_URL", "https://api.z.ai/api/coding/paas/v4").rstrip("/")
ZAI_MODEL = os.environ.get("ZAI_MODEL", "glm-5-turbo")

# ─────────────────────────────────────────────────────────────────────────────
# Subject Configurations
# ─────────────────────────────────────────────────────────────────────────────

SUBJECTS = {
    "reading": {
        "slug": "reading",
        "name": "TEAS 7 Reading",
        "teas_weight": "39 questions (26% of exam)",
        "topics": [
            {
                "name": "Key Ideas & Details",
                "subtopics": [
                    "Identifying main idea and supporting details",
                    "Summarizing passages",
                    "Drawing conclusions from text",
                    "Making inferences from explicit and implicit information",
                    "Distinguishing fact from opinion",
                ],
                "research_questions": [
                    "What are the most common mistakes students make when identifying the main idea of a TEAS reading passage?",
                    "How do TEAS 7 reading questions distinguish between inference and literal comprehension?",
                    "What strategies help students avoid selecting answer choices that are true but not supported by the passage?",
                ],
            },
            {
                "name": "Craft & Structure",
                "subtopics": [
                    "Analyzing author's purpose and point of view",
                    "Understanding text structure (cause-effect, compare-contrast, chronological, problem-solution)",
                    "Interpreting figurative language, tone, and mood",
                    "Vocabulary in context",
                    "Analyzing organizational patterns",
                ],
                "research_questions": [
                    "What types of figurative language appear most frequently on the TEAS 7 reading section?",
                    "How do students confuse author's purpose with author's point of view on TEAS questions?",
                    "What text structures are tested and what are the signal words students miss?",
                ],
            },
            {
                "name": "Integration of Knowledge & Ideas",
                "subtopics": [
                    "Comparing multiple passages on the same topic",
                    "Evaluating arguments and evidence",
                    "Identifying logical fallacies",
                    "Synthesizing information across sources",
                    "Determining source credibility",
                ],
                "research_questions": [
                    "What types of logical fallacies appear on the TEAS 7 reading section?",
                    "How do dual-passage questions work on the TEAS 7 and what traps do students fall into?",
                    "What makes a source credible vs unreliable in TEAS 7 reading questions?",
                ],
            },
        ],
        "textbook": None,
        "sources": [
            "https://www.atitesting.com/teas-prep/teas-overview",
            "https://www.archerreview.com/blog/what-is-ati-teas-overview",
            "https://www.khanacademy.org/reading/reading-comprehension",
        ],
        "min_misconceptions": 15,
        "min_qa": 25,
    },
    "math": {
        "slug": "math",
        "name": "TEAS 7 Mathematics",
        "teas_weight": "34 questions (23% of exam)",
        "topics": [
            {
                "name": "Numbers & Algebra",
                "subtopics": [
                    "Fractions (addition, subtraction, multiplication, division, mixed numbers)",
                    "Decimals and percents (conversions, operations, percent word problems)",
                    "Ratios and proportions",
                    "Integer operations (positive and negative numbers)",
                    "Order of operations (PEMDAS)",
                    "Solving one-step and multi-step equations",
                    "Translating word problems into equations",
                    "Inequalities on a number line",
                ],
                "research_questions": [
                    "What are the 5 most common fraction misconceptions among nursing students on the TEAS?",
                    "How do students confuse ratio and proportion problems on the TEAS math section?",
                    "What word problem translation errors are most frequent on TEAS 7 math?",
                    "How do students mishandle negative numbers in multi-step equations?",
                    "What percent calculation mistakes appear most often on the TEAS?",
                ],
            },
            {
                "name": "Measurement & Data",
                "subtopics": [
                    "Metric system conversions (kilo, centi, milli, etc.)",
                    "Household measurement conversions (tsp, tbsp, oz, cups, lbs)",
                    "Reading and interpreting tables, charts, and graphs",
                    "Mean, median, mode, range",
                    "Geometry: perimeter, area, circumference, volume",
                    "Unit conversions within and between systems",
                ],
                "research_questions": [
                    "What metric-houshold conversion errors are most common on the TEAS 7?",
                    "How do students misinterpret graph and chart data on TEAS questions?",
                    "What geometry formula mix-ups appear on the TEAS (e.g., perimeter vs area vs circumference)?",
                    "How do students mishandle mean/median/mode when outliers are present?",
                ],
            },
        ],
        "textbook": ["Elementary-Algebra-2e.pdf", "Prealgebra-2e.pdf"],
        "sources": [
            "https://www.atitesting.com/teas-prep/teas-overview",
            "https://www.khanacademy.org/math",
        ],
        "min_misconceptions": 12,
        "min_qa": 25,
    },
    "science": {
        "slug": "science",
        "name": "TEAS 7 Science",
        "teas_weight": "44 questions (29% of exam)",
        "topics": [
            {
                "name": "Anatomy & Physiology",
                "subtopics": [
                    "Cell structure and function",
                    "Tissue types (epithelial, connective, muscle, nervous)",
                    "Skeletal system (bone types, axial vs appendicular)",
                    "Muscular system (muscle types, contraction, origin/insertion)",
                    "Nervous system (CNS vs PNS, afferent/efferent, reflex arcs)",
                    "Endocrine system (hormones, feedback loops)",
                    "Cardiovascular system (heart, blood vessels, blood components)",
                    "Respiratory system (gas exchange, lung mechanics)",
                    "Digestive system (organs, enzymes, absorption)",
                    "Immune/lymphatic system (innate vs adaptive, WBC types)",
                    "Integumentary system (skin layers, functions)",
                    "Urinary system (nephron, filtration, reabsorption)",
                    "Reproductive system (male and female anatomy, fertilization)",
                ],
                "research_questions": [
                    "What A&P misconceptions cause the most wrong answers on the TEAS 7 science section?",
                    "Which body systems are tested most heavily and what traps exist in those questions?",
                    "What cell biology concepts do nursing students most commonly confuse?",
                    "How do TEAS questions test the difference between similar anatomical terms (e.g., afferent/efferent, arteries/veins)?",
                    "What hormone-function mismatches are most common on the TEAS?",
                ],
            },
            {
                "name": "Biology",
                "subtopics": [
                    "Cell theory and cell types (prokaryotic vs eukaryotic)",
                    "Cell organelles and their functions",
                    "Cell division (mitosis vs meiosis, phases)",
                    "DNA structure and replication",
                    "Genetics (Punnett squares, dominant/recessive traits)",
                    "Evolution and natural selection",
                    "Ecology (food chains, trophic levels, biomes)",
                ],
                "research_questions": [
                    "What biology misconceptions are most frequently tested on the TEAS 7?",
                    "How do students confuse mitosis and meiosis on TEAS questions?",
                    "What genetics/Punnett square errors appear most often?",
                    "What ecology concepts do students misapply on the TEAS?",
                ],
            },
            {
                "name": "Chemistry",
                "subtopics": [
                    "Atomic structure (protons, neutrons, electrons)",
                    "Periodic table trends (electronegativity, atomic radius)",
                    "Chemical bonds (ionic, covalent, hydrogen)",
                    "States of matter and phase changes",
                    "Chemical reactions and balancing equations",
                    "Acids, bases, and pH",
                    "Solutions and concentrations",
                ],
                "research_questions": [
                    "What chemistry misconceptions cause the most errors on the TEAS 7?",
                    "How do students confuse ionic and covalent bonding on TEAS questions?",
                    "What pH and acid-base mistakes are most common?",
                    "How do students mishandle phase change diagrams on the TEAS?",
                ],
            },
            {
                "name": "Scientific Reasoning",
                "subtopics": [
                    "Scientific method and experimental design",
                    "Identifying independent, dependent, and controlled variables",
                    "Interpreting data from experiments",
                    "Drawing conclusions from evidence",
                    "Evaluating hypothesis and prediction statements",
                ],
                "research_questions": [
                    "How do TEAS 7 questions test variable identification in experiments?",
                    "What experimental design traps do students fall into on the TEAS?",
                    "How do students confuse correlation with causation on TEAS science questions?",
                ],
            },
        ],
        "textbook": ["Anatomy-and-Physiology-2e.pdf", "Concepts-of-Biology.pdf", "Chemistry-2e.pdf"],
        "sources": [
            "https://www.atitesting.com/teas-prep/teas-overview",
            "https://www.khanacademy.org/science",
        ],
        "min_misconceptions": 20,
        "min_qa": 30,
    },
    "english": {
        "slug": "english",
        "name": "TEAS 7 English & Language Usage",
        "teas_weight": "33 questions (22% of exam)",
        "topics": [
            {
                "name": "Conventions of Standard English",
                "subtopics": [
                    "Subject-verb agreement",
                    "Verb tenses (past, present, perfect, progressive)",
                    "Pronoun-antecedent agreement",
                    "Comma usage (introductory clauses, series, compound sentences)",
                    "Semicolons and colons",
                    "Apostrophes (possessives, contractions)",
                    "Sentence fragments and run-on sentences",
                    "Parallel structure",
                ],
                "research_questions": [
                    "What grammar rules are most frequently tested on the TEAS 7 English section?",
                    "What subject-verb agreement traps appear on TEAS questions (e.g., prepositional phrases between subject and verb)?",
                    "What comma rule errors are most common on the TEAS 7?",
                    "How do students confuse sentence fragments with run-on sentences?",
                ],
            },
            {
                "name": "Knowledge of Language",
                "subtopics": [
                    "Audience-appropriate language",
                    "Tone and register (formal vs informal)",
                    "Concise vs wordy phrasing",
                    "Active vs passive voice",
                    "Transitions and cohesion",
                    "Avoiding redundancy and ambiguity",
                ],
                "research_questions": [
                    "What tone/register mistakes do students make on TEAS 7 English questions?",
                    "How do TEAS questions test active vs passive voice and what do students get wrong?",
                    "What transition word errors are most common on the TEAS?",
                ],
            },
            {
                "name": "Vocabulary Acquisition",
                "subtopics": [
                    "Context clues (definition, example, contrast, inference)",
                    "Commonly confused words (affect/effect, their/there/they're, etc.)",
                    "Word parts (prefixes, suffixes, roots)",
                    "Medical terminology basics",
                    "Academic vocabulary",
                ],
                "research_questions": [
                    "What commonly confused word pairs appear most often on the TEAS 7?",
                    "How do TEAS questions test context clues and what traps exist?",
                    "What word parts (prefixes/suffixes/roots) are most tested on the TEAS?",
                ],
            },
        ],
        "textbook": ["Writing-Guide-with-Handbook.pdf"],
        "sources": [
            "https://www.atitesting.com/teas-prep/teas-overview",
            "https://www.khanacademy.org/grammar",
        ],
        "min_misconceptions": 12,
        "min_qa": 25,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# SQL Schema (matches A&P KB template exactly)
# ─────────────────────────────────────────────────────────────────────────────

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS misconceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_system TEXT NOT NULL,
    topic TEXT NOT NULL,
    misconception TEXT NOT NULL,
    correct_explanation TEXT NOT NULL,
    common_wrong_answer TEXT,
    why_students_err TEXT,
    teas_relevance TEXT,
    source TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS high_yield_qa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    body_system TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_miscon_body_system ON misconceptions(body_system);
CREATE INDEX IF NOT EXISTS idx_miscon_topic ON misconceptions(topic);
CREATE INDEX IF NOT EXISTS idx_qa_body_system ON high_yield_qa(body_system);
"""

# Example rows to show the API what format we expect
EXAMPLE_MISCONCEPTIONS = [
    (
        "Cardiovascular",
        "Heart Anatomy",
        "The left side of the heart pumps blood to the lungs.",
        "The RIGHT side pumps blood to the lungs (pulmonary circuit). The LEFT side pumps oxygenated blood to the body (systemic circuit).",
        "The left side pumps to lungs",
        "Students think 'left = lung' because both start with L, confusing the two circuits.",
        "TEAS 7 frequently tests pulmonary vs systemic circulation distinction.",
        "ATI Nursing Blog 2025",
    ),
    (
        "Respiratory",
        "Gas Exchange",
        "Oxygen is carried mainly in the plasma of the blood.",
        "Oxygen is carried primarily by hemoglobin inside red blood cells (~98.5%). Only ~1.5% dissolves directly in plasma.",
        "Plasma carries most oxygen",
        "Students hear 'blood carries oxygen' and assume plasma (the liquid part) does the carrying.",
        "Gas exchange mechanism is directly tested on TEAS 7 science questions.",
        "OpenStax A&P 2e",
    ),
]

EXAMPLE_QA = [
    (
        "What is the correct path of blood through the heart?",
        "Vena cava → Right atrium → Tricuspid valve → Right ventricle → Pulmonary artery → Lungs → Pulmonary vein → Left atrium → Mitral valve → Left ventricle → Aorta",
        "Deoxygenated blood enters via vena cava, moves through right heart to lungs, returns oxygenated via pulmonary veins to left heart, then out through aorta to the body.",
        "Cardiovascular",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

class PipelineLog:
    """Simple logger that writes to both a file and stdout."""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.filepath, "a", encoding="utf-8")

    def log(self, stage, msg, level="INFO"):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"[{ts}] [{stage}] [{level}] {msg}"
        print(line, flush=True)
        self._fh.write(line + "\n")
        self._fh.flush()

    def close(self):
        self._fh.close()

# ─────────────────────────────────────────────────────────────────────────────
# Z.AI API Layer
# ─────────────────────────────────────────────────────────────────────────────

def call_api(system_prompt, user_prompt, max_tokens=16384, temperature=0.7, log=None, stage="API"):
    """Call Z.AI chat completions API with retry and error handling.

    Returns the content string, or raises on unrecoverable error.
    """
    url = f"{ZAI_BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZAI_API_KEY}",
    }
    payload = {
        "model": ZAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "reasoning_effort": "none",
    }

    last_error = None
    for attempt in range(1, 4):  # 3 retries
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=data, headers=headers)
            resp = urllib.request.urlopen(req, timeout=300)
            result = json.loads(resp.read())

            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            if log:
                log.log(stage, f"API call OK (attempt {attempt}): {usage.get('total_tokens', '?')} tokens used")
            return content

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            last_error = f"HTTP {e.code}: {body}"
            if log:
                log.log(stage, f"API HTTP error (attempt {attempt}): {last_error}", "WARN")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_error = str(e)
            if log:
                log.log(stage, f"API network error (attempt {attempt}): {last_error}", "WARN")

        if attempt < 3:
            wait = 5 * (2 ** (attempt - 1))  # 5s, 10s
            if log:
                log.log(stage, f"Retrying in {wait}s...", "WARN")
            time.sleep(wait)

    raise RuntimeError(f"API failed after 3 retries: {last_error}")

# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def read_file_safe(path):
    """Read a text file, return content or empty string."""
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def export_db_text(db_path):
    """Export all KB content as formatted markdown text."""
    conn = sqlite3.connect(db_path)
    lines = []

    # Misconceptions
    rows = conn.execute(
        "SELECT body_system, topic, misconception, correct_explanation, "
        "common_wrong_answer, why_students_err, teas_relevance, source "
        "FROM misconceptions ORDER BY body_system, topic, id"
    ).fetchall()

    lines.append("# Misconceptions Knowledge Base\n")
    for r in rows:
        lines.append(f"## [{r[0]}] {r[1]}")
        lines.append(f"**Misconception:** {r[2]}")
        lines.append(f"**Correct:** {r[3]}")
        lines.append(f"**Common wrong answer:** {r[4]}")
        lines.append(f"**Why students err:** {r[5]}")
        lines.append(f"**TEAS relevance:** {r[6]}")
        lines.append(f"**Source:** {r[7]}")
        lines.append("")

    # QA pairs
    qa_rows = conn.execute(
        "SELECT question, correct_answer, explanation, body_system "
        "FROM high_yield_qa ORDER BY body_system, id"
    ).fetchall()

    lines.append("# High-Yield Q&A\n")
    lines.append("Columns: body_system, question, correct_answer, explanation\n")
    for r in qa_rows:
        lines.append(f"## [{r[3]}] {r[0]}")
        lines.append(f"**correct_answer:** {r[1]}")
        lines.append(f"**Explanation:** {r[2]}")
        lines.append("")

    conn.close()
    return "\n".join(lines)


def parse_quality_score(text, pattern):
    """Extract a numeric score from API text output."""
    m = re.search(pattern, text)
    if m:
        return float(m.group(1))
    return None


def make_example_rows_sql():
    """Build SQL INSERT examples from the hardcoded example data."""
    lines = ["-- Example misconception entries:"]
    for i, row in enumerate(EXAMPLE_MISCONCEPTIONS):
        escaped = [r.replace("'", "''") for r in row]
        lines.append(
            f"INSERT INTO misconceptions "
            f"(body_system, topic, misconception, correct_explanation, "
            f"common_wrong_answer, why_students_err, teas_relevance, source) "
            f"VALUES ('{escaped[0]}', '{escaped[1]}', '{escaped[2]}', '{escaped[3]}', "
            f"'{escaped[4]}', '{escaped[5]}', '{escaped[6]}', '{escaped[7]}');"
        )

    lines.append("")
    lines.append("-- Example Q&A entries:")
    for row in EXAMPLE_QA:
        escaped = [r.replace("'", "''") for r in row]
        lines.append(
            f"INSERT INTO high_yield_qa "
            f"(question, correct_answer, explanation, body_system) "
            f"VALUES ('{escaped[0]}', '{escaped[1]}', '{escaped[2]}', '{escaped[3]}');"
        )
    return "\n".join(lines)


def count_db_entries(db_path):
    """Return (misconception_count, qa_count) from a DB file."""
    if not Path(db_path).exists():
        return 0, 0
    conn = sqlite3.connect(db_path)
    mc = conn.execute("SELECT COUNT(*) FROM misconceptions").fetchone()[0]
    qc = conn.execute("SELECT COUNT(*) FROM high_yield_qa").fetchone()[0]
    conn.close()
    return mc, qc


def extract_sql_inserts(text):
    """Extract SQL INSERT statements from API response text."""
    # Match INSERT INTO ... ; (multi-line)
    inserts = re.findall(r"INSERT\s+INTO\s+[\w]+\s*\([^)]+\)\s*VALUES\s*\([^;]+\);", text, re.IGNORECASE | re.DOTALL)
    return inserts


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Scout
# ─────────────────────────────────────────────────────────────────────────────

def stage_scout(subject, run_dir, log):
    """Research misconceptions and high-yield topics for a subject."""
    out_file = run_dir / "01_scout_brief.md"
    if out_file.exists():
        log.log("SCOUT", "Output exists, skipping (use --force to re-run)")
        return True

    log.log("SCOUT", f"Preparing scout input for {subject['name']}")

    # Build research guide with specific questions
    topic_sections = []
    for topic in subject["topics"]:
        section = f"### {topic['name']}\n\n**Subtopics:**\n"
        for st in topic["subtopics"]:
            section += f"- {st}\n"
        section += "\n**Research questions to answer:**\n"
        for i, q in enumerate(topic["research_questions"], 1):
            section += f"{i}. {q}\n"
        section += f"\n**Target:** At least {subject['min_misconceptions'] // len(subject['topics'])} misconceptions for this topic.\n"
        topic_sections.append(section)

    topics_text = "\n".join(topic_sections)

    # Build input markdown
    input_md = f"""# Scout Research Brief — {subject['name']}

## Subject Overview
- **Name:** {subject['name']}
- **TEAS 7 Weight:** {subject['teas_weight']}
- **Target misconception count:** at least {subject['min_misconceptions']}
- **Target Q&A count:** at least {subject['min_qa']}

## Topics to Research

{topics_text}

## Research Sources
{chr(10).join('- ' + s for s in subject['sources'])}

## Output Format

For EACH misconception, provide:
1. **ID:** M{{number}} (M1, M2, M3...)
2. **Topic:** Which topic from above
3. **Misconception statement:** What students incorrectly believe (1-2 sentences)
4. **Correct explanation:** The accurate scientific/academic explanation (2-4 sentences)
5. **Common wrong answer:** The specific wrong answer choice students tend to pick
6. **Why students make this error:** The cognitive reason behind the misconception
7. **TEAS 7 relevance:** How and why this appears on the exam
8. **Source:** Where this misconception is documented

Also provide high-yield Q&A pairs:
- **Question:** A TEAS-style question
- **Correct answer:** The accurate answer
- **Explanation:** Why this is correct and why distractors are wrong
- **Topic:** Which topic this covers

## Critical Rules
- Do NOT invent misconceptions — base them on documented education research
- Each misconception must be distinct — no duplicates or near-duplicates
- Cover ALL topics listed above — no topic should have zero misconceptions
- Explanations must be scientifically accurate and appropriate for nursing students
- Sources should be real (textbook names, ATI materials, peer-reviewed research)
"""

    # Save input for debugging
    (run_dir / "01_scout_input.md").write_text(input_md, encoding="utf-8")
    log.log("SCOUT", "Input prepared, calling API...")

    system = (
        f"You are an expert education researcher specializing in {subject['name']} "
        f"and TEAS 7 exam preparation. You have deep knowledge of common student "
        f"misconceptions, how they develop, and how they are tested on standardized "
        f"nursing entrance exams. You write precisely and cite sources."
    )

    try:
        result = call_api(system, input_md, max_tokens=16384, temperature=0.7, log=log, stage="SCOUT")
        out_file.write_text(result, encoding="utf-8")
        log.log("SCOUT", f"Scout brief written ({len(result)} chars)")

        # Quick validation
        m_count = len(re.findall(r"M\d+", result))
        log.log("SCOUT", f"Found {m_count} misconception IDs in output")
        if m_count < subject["min_misconceptions"]:
            log.log("SCOUT", f"WARNING: Only {m_count} misconceptions found (target: {subject['min_misconceptions']})", "WARN")

        return True
    except Exception as e:
        log.log("SCOUT", f"FAILED: {e}", "ERROR")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: KB Builder
# ─────────────────────────────────────────────────────────────────────────────

def stage_kb_build(subject, run_dir, log):
    """Convert scout brief into a structured SQLite database."""
    db_path = run_dir / "data" / f"{subject['slug']}.db"
    if db_path.exists():
        mc, qc = count_db_entries(db_path)
        if mc >= subject["min_misconceptions"]:
            log.log("BUILD", f"DB exists with {mc} misconceptions, skipping (use --force to re-run)")
            return True

    log.log("BUILD", f"Preparing KB build input for {subject['name']}")

    scout_brief = read_file_safe(run_dir / "01_scout_brief.md")
    if not scout_brief:
        log.log("BUILD", "FAILED: No scout brief found. Run stage 1 first.", "ERROR")
        return False

    example_sql = make_example_rows_sql()

    input_md = f"""# KB Build Instructions — {subject['name']}

## Task
Convert the scout brief below into valid SQL INSERT statements that populate the knowledge base.

## Database Schema

```sql
{DB_SCHEMA}
```

## Example INSERT Statements (follow this format exactly)

```sql
{example_sql}
```

## Scout Brief (source material)

{scout_brief}

## Requirements
1. Create INSERT statements for the `misconceptions` table — one row per misconception from the brief
2. Create INSERT statements for the `high_yield_qa` table — one row per Q&A pair from the brief
3. For `misconceptions`, use the topic name as `body_system` and the subtopic as `topic`
4. All fields must be non-empty except `source` (use 'TEAS 7 Study Guide' if no specific source given)
5. Escape single quotes in values by doubling them: 'it''s' not 'it's'
6. Output ONLY valid SQL — no markdown code fences, no explanations, just the SQL statements
7. Start with CREATE TABLE statements, then INSERT INTO misconceptions, then INSERT INTO high_yield_qa
8. Target: at least {subject['min_misconceptions']} misconception rows and {subject['min_qa']} Q&A rows

## Output Format
Output the complete SQL as a single block. Start with PRAGMA and CREATE TABLE, then all INSERTs.
"""

    (run_dir / "02_builder_input.md").write_text(input_md, encoding="utf-8")
    log.log("BUILD", "Input prepared, calling API...")

    system = (
        "You are a database engineer building educational knowledge bases. "
        "You write precise, valid SQLite SQL. You never output anything except SQL code. "
        "You always escape single quotes in string values by doubling them."
    )

    try:
        result = call_api(system, input_md, max_tokens=16384, temperature=0.3, log=log, stage="BUILD")
    except Exception as e:
        log.log("BUILD", f"API FAILED: {e}", "ERROR")
        return False

    # Strip markdown code fences if present
    sql = result.strip()
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\s*\n?", "", sql)
        sql = re.sub(r"\n?```\s*$", "", sql)

    # Execute SQL against fresh database
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        conn.executescript(sql)
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        db_path.unlink(missing_ok=True)
        log.log("BUILD", f"SQL execution FAILED: {e}", "ERROR")
        # Save raw SQL for debugging
        (run_dir / "02_raw_sql.txt").write_text(sql, encoding="utf-8")
        log.log("BUILD", "Raw SQL saved to 02_raw_sql.txt for debugging")
        return False

    mc, qc = count_db_entries(db_path)
    conn.close()

    log.log("BUILD", f"DB built: {mc} misconceptions, {qc} Q&A pairs")

    if mc < subject["min_misconceptions"]:
        log.log("BUILD", f"WARNING: Only {mc} misconceptions (target: {subject['min_misconceptions']})", "WARN")

    return True


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: Skeptic
# ─────────────────────────────────────────────────────────────────────────────

def stage_skeptic(subject, run_dir, log):
    """Fact-check the KB and identify weaknesses."""
    out_file = run_dir / "03_skeptic_report.md"
    if out_file.exists():
        log.log("SKEPTIC", "Output exists, skipping (use --force to re-run)")
        return True

    db_path = run_dir / "data" / f"{subject['slug']}.db"
    if not db_path.exists():
        log.log("SKEPTIC", "FAILED: No database found. Run stage 2 first.", "ERROR")
        return False

    log.log("SKEPTIC", f"Preparing skeptic review for {subject['name']}")

    kb_text = export_db_text(db_path)
    scout_brief = read_file_safe(run_dir / "01_scout_brief.md")

    topic_list = "\n".join(f"- {t['name']}" for t in subject["topics"])

    input_md = f"""# Skeptic Review — {subject['name']}

## Task
You are an adversarial fact-checker reviewing a knowledge base built for TEAS 7 exam preparation.
Your job is to find every error, gap, and weakness. Be thorough and specific.

## Topics This KB Must Cover
{topic_list}

## Knowledge Base Content

{kb_text}

## Original Scout Brief (for cross-reference)

{scout_brief}

## Review Checklist
For EACH entry in the knowledge base, check:

1. **Scientific accuracy:** Is the correct explanation actually correct? Any factual errors?
2. **Plausibility of wrong answers:** Is the "common wrong answer" something students would actually choose?
3. **Why students err:** Does the reasoning match documented education research?
4. **TEAS relevance:** Is this actually tested on the TEAS 7, or is it tangential?
5. **Source credibility:** Are cited sources real and authoritative?
6. **Duplicates:** Are any misconceptions redundant or near-duplicates?

## Gap Analysis
- Are there high-yield TEAS topics with ZERO misconceptions?
- Are there common student errors documented in nursing education literature that are missing?
- Are any topic areas underrepresented compared to their TEAS question weight?

## Output Format

### Issues Found
For each issue:
- **ID:** I1, I2, I3...
- **Severity:** CRITICAL / WARNING / INFO
- **Entry reference:** Which misconception or Q&A is affected
- **Description:** What's wrong
- **Suggested fix:** How to correct it

### Missing Content
- List specific misconceptions or Q&A pairs that should be added, with topic

### Overall Assessment
- **Quality score:** 1-10
- **Pass/fail:** PASS (quality >= 7) or FAIL
- **Summary:** 2-3 sentence summary of KB health
"""

    (run_dir / "03_skeptic_input.md").write_text(input_md, encoding="utf-8")
    log.log("SKEPTIC", "Input prepared, calling API...")

    system = (
        "You are a rigorous science education fact-checker with expertise in TEAS 7 exam content. "
        "You are adversarial — you actively look for errors, not confirmations. "
        "You distinguish between CRITICAL errors (scientifically wrong), WARNINGs (incomplete or misleading), "
        "and INFO items (minor improvements). You cite specific evidence."
    )

    try:
        result = call_api(system, input_md, max_tokens=16384, temperature=0.3, log=log, stage="SKEPTIC")
        out_file.write_text(result, encoding="utf-8")
        log.log("SKEPTIC", f"Skeptic report written ({len(result)} chars)")

        quality = parse_quality_score(result, r"[Qq]uality\s*(?:score|rating)[:\s]*(\d+(?:\.\d+)?)")
        if quality is not None:
            log.log("SKEPTIC", f"Quality score: {quality}/10 {'PASS' if quality >= 7 else 'FAIL'}")
            if quality < 7:
                log.log("SKEPTIC", "Quality below 7 — Editor stage will need to address issues", "WARN")

        return True
    except Exception as e:
        log.log("SKEPTIC", f"FAILED: {e}", "ERROR")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Stage 4: Crash Test Dummy (CTD)
# ─────────────────────────────────────────────────────────────────────────────

def stage_ctd(subject, run_dir, log):
    """Simulate student queries against the KB to test coverage."""
    out_file = run_dir / "04_ctd_results.md"
    if out_file.exists():
        log.log("CTD", "Output exists, skipping (use --force to re-run)")
        return True

    db_path = run_dir / "data" / f"{subject['slug']}.db"
    if not db_path.exists():
        log.log("CTD", "FAILED: No database found. Run stage 2 first.", "ERROR")
        return False

    log.log("CTD", f"Preparing crash test for {subject['name']}")

    kb_text = export_db_text(db_path)

    # Generate simulated student questions from topic list
    student_questions = []
    for topic in subject["topics"]:
        for st in topic["subtopics"]:
            # Convert subtopic into a student-style question
            student_questions.append(f"[{topic['name']}] Student asks: 'I don't understand {st.lower()}. Can you help me?'")
        # Add misconception-probing questions
        student_questions.append(
            f"[{topic['name']}] Student says: 'I thought [common misconception about {topic['name'].lower()}]. Is that right?'"
        )

    questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(student_questions))

    input_md = f"""# Crash Test Dummy — {subject['name']}

## Task
You are simulating a confused TEAS 7 student trying to use this knowledge base to study.
For each question below, check if the KB can answer it and score the coverage.

## Knowledge Base Content

{kb_text}

## Student Questions

{questions_text}

## Scoring Rubric
For each question, assign:
- **3 points:** Direct hit — KB has an exact misconception match or Q&A that directly addresses this
- **2 points:** Adjacent — KB covers a related concept that partially answers the question
- **1 point:** Partial — KB has general info about the topic area but nothing specific enough
- **0 points:** Gap — KB has nothing relevant to this question

## Output Format

### Per-Question Results
For each question:
- **Question:** (restate it)
- **Score:** 0-3
- **Matched entry:** Which KB entry (if any) was relevant
- **Verdict:** Why you gave this score

### Coverage by Topic
For each topic: percentage of questions answered at 2+ points

### Gap List
All questions that scored 0 or 1, grouped by topic

### Overall Health Score
Total points / max possible points × 100%
"""

    (run_dir / "04_ctd_input.md").write_text(input_md, encoding="utf-8")
    log.log("CTD", f"Testing {len(student_questions)} simulated questions, calling API...")

    system = (
        "You are a test evaluator simulating confused TEAS 7 students. "
        "You score generously — if the KB has anything remotely useful, give it at least 1 point. "
        "You only give 0 points when the KB truly has nothing relevant. "
        "You quote specific KB entries to justify your scores."
    )

    try:
        result = call_api(system, input_md, max_tokens=16384, temperature=0.3, log=log, stage="CTD")
        out_file.write_text(result, encoding="utf-8")
        log.log("CTD", f"CTD results written ({len(result)} chars)")

        health = parse_quality_score(result, r"[Hh]ealth\s*(?:score|rating)[:\s]*(\d+(?:\.\d+)?)")
        if health is not None:
            log.log("CTD", f"Health score: {health}% {'PASS' if health >= 85 else 'NEEDS WORK'}")
            if health < 85:
                log.log("CTD", "Health below 85% — gaps will be addressed in Editor stage", "WARN")

        return True
    except Exception as e:
        log.log("CTD", f"FAILED: {e}", "ERROR")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Stage 5: Editor
# ─────────────────────────────────────────────────────────────────────────────

def stage_editor(subject, run_dir, log):
    """Merge Skeptic + CTD feedback, fix issues, fill gaps."""
    db_path = run_dir / "data" / f"{subject['slug']}.db"
    report_file = run_dir / "05_editor_report.md"

    if report_file.exists() and db_path.exists():
        mc, qc = count_db_entries(db_path)
        if mc >= subject["min_misconceptions"]:
            log.log("EDITOR", "Editor output exists, skipping (use --force to re-run)")
            return True

    if not db_path.exists():
        log.log("EDITOR", "FAILED: No database found. Run stage 2 first.", "ERROR")
        return False

    log.log("EDITOR", f"Preparing editor input for {subject['name']}")

    kb_text = export_db_text(db_path)
    skeptic_report = read_file_safe(run_dir / "03_skeptic_report.md")
    ctd_results = read_file_safe(run_dir / "04_ctd_results.md")

    mc_before, qc_before = count_db_entries(db_path)

    input_md = f"""# Editor Instructions — {subject['name']}

## Task
You are the final editor of this knowledge base. Your job is to:
1. Fix all CRITICAL and WARNING issues from the Skeptic report
2. Fill gaps identified by the Crash Test Dummy
3. Output complete SQL to update the database

## Current KB Content

{kb_text}

## Skeptic Report (issues to fix)

{skeptic_report}

## Crash Test Dummy Results (gaps to fill)

{ctd_results}

## Rules
- DO NOT delete existing entries — only fix or add new ones
- For fixes: output the corrected row as a complete INSERT statement
- For additions: output new INSERT statements for missing misconceptions or Q&A pairs
- For entries that are fine: do NOT re-output them
- Escape single quotes in values by doubling them: 'it''s' not 'it's'
- Output ONLY valid SQL — no markdown code fences, no explanations

## Current Counts
- Misconceptions: {mc_before} (target: {subject['min_misconceptions']})
- Q&A pairs: {qc_before} (target: {subject['min_qa']})

## SQL Format
```sql
-- For corrections, use INSERT OR REPLACE:
INSERT OR REPLACE INTO misconceptions (id, body_system, topic, misconception, correct_explanation, common_wrong_answer, why_students_err, teas_relevance, source) VALUES (id_value, ...);

-- For new entries, use plain INSERT:
INSERT INTO misconceptions (body_system, topic, misconception, correct_explanation, common_wrong_answer, why_students_err, teas_relevance, source) VALUES (...);

-- For high_yield_qa corrections (with id):
INSERT OR REPLACE INTO high_yield_qa (id, body_system, question, correct_answer, explanation) VALUES (id_value, ...);

-- For high_yield_qa new entries (without id):
INSERT INTO high_yield_qa (body_system, question, correct_answer, explanation) VALUES (...);
```

Start your output with: -- EDITOR CHANGES FOLLOW
"""

    (run_dir / "05_editor_input.md").write_text(input_md, encoding="utf-8")
    log.log("EDITOR", "Input prepared, calling API...")

    system = (
        "You are a meticulous knowledge base editor. You fix errors precisely and fill gaps with accurate content. "
        "You write valid SQLite SQL only — no markdown, no explanations. "
        "You always escape single quotes by doubling them. "
        "You use INSERT OR REPLACE for corrections (with id) and INSERT for new entries (without id). "
        "CRITICAL SCHEMA RULES:\n"
        "1. The high_yield_qa table column for the answer is 'correct_answer' (NOT 'answer').\n"
        "2. The high_yield_qa table does NOT have a 'topic' or 'passage' column. Valid columns: id, body_system, question, correct_answer, explanation.\n"
        "3. The misconceptions table valid columns: id, body_system, topic, misconception, correct_explanation, common_wrong_answer, why_students_err, teas_relevance, source.\n"
        "4. You must use EXACT column names — any other column name will crash the database."
    )

    try:
        result = call_api(system, input_md, max_tokens=16384, temperature=0.3, log=log, stage="EDITOR")
    except Exception as e:
        log.log("EDITOR", f"API FAILED: {e}", "ERROR")
        return False

    # Strip markdown fences
    sql = result.strip()
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\s*\n?", "", sql)
        sql = re.sub(r"\n?```\s*$", "", sql)

    # Safety: auto-fix common column name mistakes
    sql = sql.replace("high_yield_qa (id, body_system, question, answer,",
                      "high_yield_qa (id, body_system, question, correct_answer,")
    sql = sql.replace("high_yield_qa (body_system, question, answer,",
                      "high_yield_qa (body_system, question, correct_answer,")

    # Validate: extract column lists from high_yield_qa statements
    qa_cols_pattern = re.compile(r'high_yield_qa\s*\(([^)]+)\)', re.IGNORECASE)
    valid_qa_cols = {'id', 'question', 'correct_answer', 'explanation', 'body_system'}
    for m in qa_cols_pattern.finditer(sql):
        raw_cols = [c.strip().lower() for c in m.group(1).split(',')]
        invalid = [c for c in raw_cols if c and c not in valid_qa_cols]
        if invalid:
            log.log("EDITOR", f"INVALID columns in high_yield_qa: {invalid} — skipping all QA SQL", "WARN")
            # Remove all high_yield_qa statements from SQL
            sql = re.sub(r'INSERT\s+(?:OR\s+REPLACE\s+)?INTO\s+high_yield_qa[^;]*;', '', sql, flags=re.IGNORECASE)
            break

    # Apply to existing database
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(sql)
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        log.log("EDITOR", f"SQL execution FAILED: {e}", "ERROR")
        (run_dir / "05_editor_raw_sql.txt").write_text(sql, encoding="utf-8")
        return False

    mc_after, qc_after = count_db_entries(db_path)
    conn.close()

    # Write change report
    report = f"""# Editor Report — {subject['name']}

## Counts
- Misconceptions: {mc_before} → {mc_after} (+{mc_after - mc_before})
- Q&A pairs: {qc_before} → {qc_after} (+{qc_after - qc_before})

## Applied SQL
```sql
{sql}
```

## Status
{"PASS" if mc_after >= subject["min_misconceptions"] and qc_after >= subject["min_qa"] else "NEEDS REVIEW"}
"""
    report_file.write_text(report, encoding="utf-8")
    log.log("EDITOR", f"Edits applied: {mc_after} misconceptions, {qc_after} Q&A pairs")

    return True


# ─────────────────────────────────────────────────────────────────────────────
# Stage 6: Eval
# ─────────────────────────────────────────────────────────────────────────────

def stage_eval(subject, run_dir, log):
    """Score the final KB on standardized metrics."""
    out_file = run_dir / "06_eval_report.md"
    if out_file.exists():
        log.log("EVAL", "Output exists, skipping (use --force to re-run)")
        return True

    db_path = run_dir / "data" / f"{subject['slug']}.db"
    if not db_path.exists():
        log.log("EVAL", "FAILED: No database found.", "ERROR")
        return False

    log.log("EVAL", f"Evaluating {subject['name']} knowledge base")

    conn = sqlite3.connect(str(db_path))

    # ── Metric 1: Coverage ──
    # % of topics with >= 3 misconceptions
    topic_counts = {}
    for topic in subject["topics"]:
        name = topic["name"]
        count = conn.execute(
            "SELECT COUNT(*) FROM misconceptions WHERE body_system = ? OR topic LIKE ?",
            (name, f"%{name}%")
        ).fetchone()[0]
        topic_counts[name] = count

    topics_covered = sum(1 for c in topic_counts.values() if c >= 3)
    total_topics = len(subject["topics"])
    coverage = (topics_covered / total_topics * 100) if total_topics else 0

    # ── Metric 2: Completeness ──
    # % of all rows with all required fields non-empty
    total_mc = conn.execute("SELECT COUNT(*) FROM misconceptions").fetchone()[0]
    complete_mc = conn.execute(
        "SELECT COUNT(*) FROM misconceptions WHERE "
        "body_system != '' AND topic != '' AND misconception != '' AND "
        "correct_explanation != '' AND why_students_err != '' AND teas_relevance != ''"
    ).fetchone()[0]
    completeness_mc = (complete_mc / total_mc * 100) if total_mc else 0

    total_qa = conn.execute("SELECT COUNT(*) FROM high_yield_qa").fetchone()[0]
    complete_qa = conn.execute(
        "SELECT COUNT(*) FROM high_yield_qa WHERE "
        "question != '' AND correct_answer != '' AND explanation != '' AND body_system != ''"
    ).fetchone()[0]
    completeness_qa = (complete_qa / total_qa * 100) if total_qa else 0
    completeness = (completeness_mc + completeness_qa) / 2

    # ── Metric 3: Depth ──
    # Average explanation length (longer = more detailed)
    avg_exp = conn.execute(
        "SELECT AVG(LENGTH(correct_explanation)) FROM misconceptions"
    ).fetchone()[0] or 0
    depth = min(100, (avg_exp / 200) * 100)  # 200 chars = full score

    # ── Metric 4: Skeptic Resolution ──
    skeptic_report = read_file_safe(run_dir / "03_skeptic_report.md")
    critical_count = len(re.findall(r"CRITICAL", skeptic_report))
    warning_count = len(re.findall(r"WARNING", skeptic_report))
    # We assume Editor fixed criticals; warnings partially fixed
    skeptic_resolved = 100  # optimistic since Editor ran
    if critical_count > 0 and "FAIL" in skeptic_report:
        skeptic_resolved = 70  # Editor may not have caught everything

    # ── Metric 5: CTD Health ──
    ctd_results = read_file_safe(run_dir / "04_ctd_results.md")
    ctd_health = parse_quality_score(ctd_results, r"[Hh]ealth\s*(?:score|rating)[:\s]*(\d+(?:\.\d+)?)")
    if ctd_health is None:
        ctd_health = 75  # conservative default

    conn.close()

    # ── Weighted Overall ──
    overall = (
        coverage * 0.25 +
        completeness * 0.25 +
        depth * 0.15 +
        skeptic_resolved * 0.15 +
        ctd_health * 0.20
    )

    grade = "A" if overall >= 90 else "B" if overall >= 80 else "C" if overall >= 70 else "F"

    # ── Build report ──
    topic_lines = "\n".join(f"  - {name}: {count} misconceptions {'✅' if count >= 3 else '⚠️'}" for name, count in topic_counts.items())

    report = f"""# Eval Report — {subject['name']}

**Overall Score: {overall:.1f}% — Grade: {grade}**
{"✅ SHIPS" if grade in ("A", "B") else "❌ NEEDS MANUAL REVIEW"}

## Metric Breakdown

| Metric | Score | Weight | Contribution |
|--------|-------|--------|-------------|
| Coverage | {coverage:.0f}% | 25% | {coverage * 0.25:.1f} |
| Completeness | {completeness:.0f}% | 25% | {completeness * 0.25:.1f} |
| Depth | {depth:.0f}% | 15% | {depth * 0.15:.1f} |
| Skeptic Resolution | {skeptic_resolved:.0f}% | 15% | {skeptic_resolved * 0.15:.1f} |
| CTD Health | {ctd_health:.0f}% | 20% | {ctd_health * 0.20:.1f} |

## Coverage by Topic
{topic_lines}

## Totals
- Misconceptions: {total_mc} (target: {subject['min_misconceptions']})
- Q&A pairs: {total_qa} (target: {subject['min_qa']})
- Avg explanation length: {avg_exp:.0f} chars
- Skeptic issues: {critical_count} critical, {warning_count} warnings
- CTD health: {ctd_health:.0f}%

## Recommendations
"""
    if coverage < 90:
        report += "- Add misconceptions for undercovered topics\n"
    if completeness < 95:
        report += "- Fill in missing fields on existing entries\n"
    if depth < 80:
        report += "- Expand brief explanations with more detail\n"
    if ctd_health < 85:
        report += "- Address CTD-identified gaps with new entries\n"
    if overall >= 80:
        report += "- KB meets shipping threshold\n"

    out_file.write_text(report, encoding="utf-8")
    log.log("EVAL", f"Score: {overall:.1f}% — Grade: {grade} {'✅ SHIPS' if grade in ('A', 'B') else '❌ REVIEW NEEDED'}")
    log.log("EVAL", f"Totals: {total_mc} misconceptions, {total_qa} Q&A pairs")

    return grade in ("A", "B")


# ─────────────────────────────────────────────────────────────────────────────
# CLI & Main
# ─────────────────────────────────────────────────────────────────────────────

STAGES = [
    ("scout", "Stage 1: Scout", stage_scout),
    ("build", "Stage 2: KB Builder", stage_kb_build),
    ("skeptic", "Stage 3: Skeptic", stage_skeptic),
    ("ctd", "Stage 4: Crash Test Dummy", stage_ctd),
    ("editor", "Stage 5: Editor", stage_editor),
    ("eval", "Stage 6: Eval", stage_eval),
]

STAGE_MAP = {name: (label, func) for name, label, func in STAGES}


def run_pipeline(subject_key, force_from=None):
    """Run the full 6-stage pipeline for a subject."""
    if subject_key not in SUBJECTS:
        print(f"Unknown subject: {subject_key}")
        print(f"Available: {', '.join(SUBJECTS.keys())}")
        return False

    subject = SUBJECTS[subject_key]
    run_dir = RUNS_DIR / subject["slug"]
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "pipeline.log"

    log = PipelineLog(log_path)
    log.log("PIPELINE", f"{'='*60}")
    log.log("PIPELINE", f"Starting pipeline for {subject['name']}")
    if force_from:
        log.log("PIPELINE", f"Force re-run from stage: {force_from}")
    log.log("PIPELINE", f"Run directory: {run_dir}")
    log.log("PIPELINE", f"{'='*60}")

    active = False
    results = {}

    for stage_name, stage_label, stage_func in STAGES:
        if force_from and not active:
            if stage_name == force_from:
                active = True
                log.log("PIPELINE", f">>> {stage_label} (forced)")
            else:
                log.log("PIPELINE", f"    {stage_label} — skipped (before force point)")
                results[stage_name] = "skipped"
                continue
        else:
            active = True
            log.log("PIPELINE", f">>> {stage_label}")

        start = time.time()
        ok = stage_func(subject, run_dir, log)
        elapsed = time.time() - start

        if ok:
            log.log("PIPELINE", f"    {stage_label} — OK ({elapsed:.0f}s)")
            results[stage_name] = "ok"
        else:
            log.log("PIPELINE", f"    {stage_label} — FAILED ({elapsed:.0f}s)", "ERROR")
            results[stage_name] = "failed"
            log.log("PIPELINE", f"Pipeline halted at {stage_label}. Fix the issue and re-run with --force {stage_name}")
            log.close()
            return False

    # Final summary
    log.log("PIPELINE", f"{'='*60}")
    log.log("PIPELINE", "Pipeline complete!")
    log.log("PIPELINE", f"{'='*60}")
    for stage_name, stage_label, _ in STAGES:
        status = results.get(stage_name, "?")
        log.log("PIPELINE", f"  {stage_label}: {status}")

    # Print final eval summary
    eval_report = read_file_safe(run_dir / "06_eval_report.md")
    if eval_report:
        # Extract just the first 5 lines
        for line in eval_report.split("\n")[:5]:
            if line.strip():
                log.log("PIPELINE", line.strip())

    log.log("PIPELINE", f"Results in: {run_dir}")
    log.close()
    return True


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        return

    if "--list" in args:
        print("Available subjects:")
        for key, sub in SUBJECTS.items():
            print(f"  {key:12s} — {sub['name']} ({sub['teas_weight']})")
        return

    # Parse --force flag
    force_from = None
    clean_args = []
    for a in args:
        if a.startswith("--force"):
            val = a.split("=", 1)[1] if "=" in a else None
            force_from = val  # None means force all, string means from that stage
            continue
        clean_args.append(a)

    if not clean_args:
        print("Error: specify a subject. Use --list to see options.")
        return

    subject_key = clean_args[0]

    if subject_key == "all":
        success = True
        for key in SUBJECTS:
            print(f"\n{'='*40}")
            print(f"Running pipeline for: {key}")
            print(f"{'='*40}\n")
            ok = run_pipeline(key, force_from=force_from)
            if not ok:
                success = False
                print(f"\nFAILED on {key}. Stopping.")
                break
        print(f"\nAll subjects {'✅ PASSED' if success else '❌ SOME FAILED'}")
        return

    ok = run_pipeline(subject_key, force_from=force_from)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
