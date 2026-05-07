# TEAS Study App — Project Status

**Last updated:** 2026-05-03
**Current phase:** Phase 0 complete — data ready, moving to Flask testing
**Phase 0 tracker:** `PHASE0_TASKS.md` (22/22 tasks complete)

## Hard Targets
- **500 questions per subject** — no exceptions

## Question Counts (verified from DB)
| Subject | Target | Current | Explanations (250+) | Status |
|---------|--------|---------|---------------------|--------|
| Math    | 500    | 500     | 500                 | ✅ DONE |
| Science | 500    | 501     | 501                 | ✅ DONE |
| Reading | 500    | 501     | 501                 | ✅ DONE |
| English | 500    | 501     | 501                 | ✅ DONE |
| **TOTAL** | **2000** | **2003** | **2003** | ✅ DONE |

## Difficulty Distribution (30/45/25 per subject — verified)
| Subject | Easy | Medium | Hard |
|---------|------|--------|------|
| Math    | 150  | 225    | 125  |
| Science | 150  | 226    | 125  |
| Reading | 150  | 226    | 125  |
| English | 150  | 226    | 125  |

## Data Quality (verified from DB)
- **Null fields:** 0
- **Duplicate questions:** 0
- **Non-MCQ correct_answer values:** 0 (all A/B/C/D)
- **Single-line option formatting:** 0 (all fixed 2026-05-01)
- **All 2,003 questions are multiple-choice with A/B/C/D options**
- **All 2,003 explanations are 250+ characters**

## Distractor Format
- All 2,003 questions now use **text-format wrong_answers** (actual option text, not letter labels)
- 404 English questions converted from letter labels → parsed inline options from question text (2026-05-03)
- Q1795 manually rewritten (malformed inline options with duplicates)

## Distractor Quality
- **Generic distractors remaining: 0** ✅
- **Letter-format distractors remaining: 0** ✅
- Fixes applied:
  - Math: 2 lazy "0" distractors → plausible wrong answers (Q123, Q189)
  - English: 404 letter-label distractors → text-format (regex parse from inline options)
  - English Q1795: malformed duplicate options → rewritten with 4 distinct choices

## App Testing
- ✅ 12/12 pages render (dashboard, 4 subjects, stats, resources, settings, quickfire, signup, login, onboarding)
- ✅ All 4 subjects serve real MCQ questions
- ✅ Quickfire mode: start, correct answer, wrong answer all working
- ✅ KaTeX math rendering active
- ✅ Dark mode supported
- ✅ APIs functional (stats, quickfire, highscores)
- Not yet deployed

## Architecture
- **Delivery:** Hosted web app / PWA
- **Hosting:** Digital Ocean (App Platform or Droplet)
- **Model:** Gemma 4 E4B (router) + Gemma 4 26B A4B (teacher)
- **Inference:** Google AI Studio (free tier: 1500 req/day)
- **DB:** `data/kb/teas_unified.db` (SQLite)

## What's Left
1. ~~Fix 149 science "None of the above" distractors~~ ✅
2. ~~Fix 6 math generic distractors~~ ✅
3. ~~Convert 404 English letter-format distractors~~ ✅
4. ~~Test Flask app end-to-end~~ ✅
5. Deploy

## Key Files
- `scripts/generate_questions.py` — generates new questions
- `scripts/rewrite_explanations.py` — expands explanations
- `app.py` — Flask web app
- `db.py` — database layer
- `kb.py` — knowledge base layer

## Telegram
- Project updates → chat ID `-1003972068284`
