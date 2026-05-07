# TEAS Study App — KB Pipeline Design

## Overview

Automated 6-stage pipeline that builds scored knowledge bases (filing cabinets) for each TEAS 7 subject. One subject at a time, end-to-end. Cloud API (Z.AI) for all generation stages.

## Architecture

```
kb_pipeline.py
├── Reads subject config from this file
├── Reads/creates run directory
├── Chains stages sequentially
├── Each stage: prepare input → call API → validate → save output
└── Writes stage reports + final score
```

## TEAS 7 Subject Breakdown

| Subject | Questions (scored) | Topics | Textbook |
|---------|-------------------|--------|----------|
| Reading | 39 | Key Ideas (15), Craft & Structure (9), Integration (15) | — (no textbook needed) |
| Math | 34 | Numbers & Algebra (18), Measurement & Data (16) | Elementary-Algebra-2e.pdf, Prealgebra-2e.pdf |
| Science | 44 | A&P (18), Biology (9), Chemistry (8), Scientific Reasoning (9) | Anatomy-and-Physiology-2e.pdf, Concepts-of-Biology.pdf, Chemistry-2e.pdf |
| English | 33 | Conventions (12), Knowledge of Language (11), Vocabulary (10) | Writing-Guide-with-Handbook.pdf |

## The 6 Stages

### Stage 1: Scout
**Purpose:** Research and document all misconceptions, high-yield topics, and TEAS traps for a subject.

**Script prepares (the table-setting):**
- `01_scout_input.md` — Contains:
  - Subject name, TEAS weight, question count
  - Official topic list with subtopics
  - Specific research questions per topic (not "research math" but "What are the 5 most common fraction misconceptions among nursing students?")
  - Curated source URLs (ATI blog, Khan Academy, peer-reviewed education research)
  - Relevant textbook PDF path (if applicable)
  - Exact output format template with example entries
  - Minimum count targets (e.g., "at least 4 misconceptions per topic")

**API call:**
- System prompt: Education researcher role, specific subject expertise
- User prompt: The `01_scout_input.md` content + any textbook excerpts
- Max tokens: 16384

**Output:** `01_scout_brief.md`
- Structured markdown with misconceptions per topic
- Each misconception has: ID, statement, correct explanation, why students err, TEAS relevance, source
- High-yield Q&A pairs
- Cross-topic traps
- Sources cited

**Validation:** Must contain misconception entries, must cover all topics, minimum count met.

---

### Stage 2: KB Builder
**Purpose:** Convert scout brief into a structured SQLite database.

**Script prepares:**
- `02_builder_input.md` — Contains:
  - Full scout brief content
  - Exact SQL schema (CREATE TABLE statements)
  - Example rows from A&P KB (3-5 sample rows showing format)
  - Insert instructions: one INSERT per misconception, all fields required
  - Target counts: misconceptions table + high_yield_qa table

**API call:**
- System prompt: Database builder role, precise SQL generation
- User prompt: The `02_builder_input.md` content
- Max tokens: 16384

**Output:** `{subject}.db` (SQLite file)
- `misconceptions` table populated
- `high_yield_qa` table populated
- Schema matches A&P template exactly

**Validation:** Script runs the SQL itself (not trusting API output blindly):
- Parse the SQL from API response
- Execute against fresh DB
- Verify row counts, non-empty fields, valid JSON if applicable
- Roll back on any error

---

### Stage 3: Skeptic
**Purpose:** Fact-check every misconception and identify weaknesses.

**Script prepares:**
- `03_skeptic_input.md` — Contains:
  - Full KB exported as formatted text (all misconceptions + QA pairs)
  - Scout brief for cross-reference
  - Specific fact-check questions:
    1. Is each correct explanation scientifically accurate?
    2. Is each "common wrong answer" actually plausible?
    3. Are there any misconceptions missing from high-yield TEAS topics?
    4. Are sources credible and real?
    5. Any contradictions between entries?
  - Output format: numbered issue list with severity (critical/warning/info) + fix suggestion

**API call:**
- System prompt: Adversarial reviewer, science education fact-checker
- User prompt: The `03_skeptic_input.md` content
- Max tokens: 16384

**Output:** `03_skeptic_report.md`
- List of issues found (ID, severity, description, suggested fix)
- Missing misconception suggestions (with topic)
- Overall quality assessment (1-10)
- Pass/fail recommendation (quality ≥ 7 = pass)

**Validation:** Report must exist and contain issues list. Quality < 7 triggers full re-scout.

---

### Stage 4: Crash Test Dummy (CTD)
**Purpose:** Simulate student queries against the KB to test coverage and helpfulness.

**Script prepares:**
- `04_ctd_input.md` — Contains:
  - Full KB exported as formatted text
  - Scout brief with topic list
  - 20-30 simulated student questions (generated from topic list + common misconceptions)
  - For each question, ask: "Can the KB answer this? How well? Quote the relevant entry."
  - Scoring rubric:
    - 3 pts: Direct hit (KB has exact misconception match)
    - 2 pts: Adjacent (KB covers related concept)
    - 1 pt: Partial (KB has general info but not specific enough)
    - 0 pts: Gap (KB has nothing relevant)

**API call:**
- System prompt: Test evaluator, simulates confused student
- User prompt: The `04_ctd_input.md` content
- Max tokens: 16384

**Output:** `04_ctd_results.md`
- Per-question score with justification
- Coverage percentage per topic
- Gap list (topics/questions the KB can't address)
- Overall health score (percentage)

**Validation:** Health score ≥ 85% = pass. < 85% = flag gaps for Editor stage.

---

### Stage 5: Editor
**Purpose:** Merge Skeptic + CTD feedback, fix issues, fill gaps.

**Script prepares:**
- `05_editor_input.md` — Contains:
  - Current KB content (exported)
  - Skeptic report (issues + fixes)
  - CTD results (gaps + scores)
  - Specific instructions:
    - Apply all critical and warning fixes from Skeptic
    - Create new misconception entries for CTD gaps
    - Do NOT delete existing entries — only fix or add
    - Output complete updated SQL INSERT statements
  - Updated row count targets

**API call:**
- System prompt: Knowledge base editor, precise and careful
- User prompt: The `05_editor_input.md` content
- Max tokens: 16384

**Output:** Updated `{subject}.db` + `05_editor_report.md` (change log)
- What was fixed, what was added, what was left as-is and why

**Validation:** Script applies edits to DB, verifies row counts increased or stayed same (never decreased).

---

### Stage 6: Eval
**Purpose:** Score the final KB on standardized metrics.

**Script prepares:**
- Runs entirely in Python, no API call needed
- Reads final DB
- Scores on:
  - Coverage: % of TEAS topics with ≥ 3 misconceptions
  - Depth: average quality of explanations (checked by API spot-check on 5 random entries)
  - Accuracy: skeptic issues resolved (critical: 100%, warning: ≥ 80%)
  - Completeness: all required fields non-empty
  - CTD Health: from stage 4 (or re-run on updated KB)

**Output:** `06_eval_report.md` + summary to stdout
- Per-metric score (0-100)
- Overall score (weighted average)
- Grade: A (≥ 90), B (≥ 80), C (≥ 70), F (< 70)
- Recommendations for improvement

**Validation:** Overall ≥ 80% (B grade) = KB ships. < 80% = flag for manual review.

---

## Run Directory Structure

```
pipeline/runs/{subject_slug}/
├── 01_scout_input.md          (prepared by script)
├── 01_scout_brief.md          (API output)
├── 02_builder_input.md        (prepared by script)
├── data/{subject}.db          (built by script from API SQL)
├── 03_skeptic_input.md        (prepared by script)
├── 03_skeptic_report.md       (API output)
├── 04_ctd_input.md            (prepared by script)
├── 04_ctd_results.md          (API output)
├── 05_editor_input.md         (prepared by script)
├── 05_editor_report.md        (API output)
├── 06_eval_report.md          (script output)
└── pipeline.log               (full run log with timestamps)
```

## Resume Logic

Each stage checks for its output file before running:
- If `01_scout_brief.md` exists → skip scout, use existing
- If `{subject}.db` exists → skip KB build, use existing
- etc.

`--force` flag re-runs from specified stage regardless.

## Failure Handling

- API call fails → retry up to 3 times with exponential backoff
- Validation fails → log error, halt pipeline, print diagnostic
- Quality gate fails (skeptic < 7, CTD < 85%, eval < 80%) → halt with clear message

## Subject Configs

Embedded in the script. Each subject has:
- `slug`: directory name
- `name`: display name
- `teas_weight`: question count and percentage
- `topics`: list of topic names with subtopics
- `textbook`: path to PDF (or None for Reading/English)
- `sources`: list of research URLs
- `min_misconceptions`: target minimum entries
- `research_questions`: 3-5 specific questions per topic to guide the Scout
