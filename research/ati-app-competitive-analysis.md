# ATI TEAS App — Competitive Analysis

**Date:** May 1, 2026
**Source:** Direct screenshots from ATI mobile app (user "Unize")
**Analyst:** Ann-E

---

## App Overview

ATI's official TEAS prep mobile app — the incumbent competitor. Subscription-based, ~2,300 question pool, TEAS-aligned subcategories, quiz-focused with static explanations.

---

## Screenshots Analyzed

**Batch 1 (12 screenshots):** Home dashboard, per-subject results (Math, Reading, Science, English), New Quiz config, Quick Start settings, Previous Quizzes, Flagged Questions, quiz question with Select All That Apply + rationales, and welcome screen.

**Batch 2 (10 screenshots):** Full quiz flow — quiz creation (2-step topic selection + config), in-quiz experience (timer, flag button, passage-based reading, vocabulary MCQs, math geometry), and post-answer feedback (green check/red X, "My Answer" tags, per-choice explanations).

---

## Feature Inventory

### Navigation & Structure
- 3-tab bottom nav: **Home → Results → Settings**
- Card-based layout with circular progress indicators
- Personalized welcome ("Welcome, Unize")

### Home Dashboard
- Overall progress ring (48% completion shown)
- Quick stats: Total Correct (349), Total Answered (509)
- Unique question tracking: "507 Used | 1,793 Remain"
- 4 subject links with percentage scores: Reading 69%, Math 60%, Science 73%, English 69%

### New Quiz Options (3 modes)
- **Custom Quiz** — user configures topics, count, etc.
- **Random Quiz** — system generates
- **Quick Start Quiz** — one-tap into a subcategory

### Quick Start Quiz Configuration
- Auto-generated quiz name (e.g., "Math May 01, 2026 8:00 PM")
- **Question count slider:** 5 to 100 (default: 10)
- **Two quiz modes:**
  - **Study Mode** — shows explanations after each answer
  - **Exam Mode** — presumably timed, no explanations until end

### Per-Subject Results Pages
Each subject breaks into TEAS-aligned subcategories:

| Subject | Subcategories |
|---------|--------------|
| **Math** | Numbers and Algebra (67%), Measurement and Data (57%) |
| **Reading** | Key Ideas and Details (57%), Craft and Structure (74%), Integration of Knowledge and Ideas (86%) |
| **Science** | Human Anatomy & Physiology (80%), Biology (57%), Chemistry (65%), Scientific Reasoning (77%) |
| **English** | Conventions of Standard English (54%), Knowledge of Language (70%), Using Language and Vocabulary to Express (85%) |

### Post-Answer Feedback
- Shows **CORRECT/INCORRECT** label per answer choice
- Provides a **rationale for EVERY option** — explains why correct is correct AND why each wrong answer is wrong
- Detailed paragraph-style explanations (3-5 sentences per choice)
- Evidence: monocot/dicot science question showed full rationale for all 5 options
- **Visual feedback:** Green checkmark on correct, Red X on incorrect
- **"My Answer" tag** on the student's incorrect selection
- Correct answer highlighted with its explanation
- Written explanations for *why* wrong answers are wrong (not just "incorrect")

### In-Quiz Experience
- **Timer:** "Time Elapsed" counter visible during quiz
- **Flag button:** Bookmark questions for review later (feeds into Flagged Questions system)
- **Navigation:** Submit + Next button flow
- **Question formats observed:**
  - Passage-based reading comprehension (long passages, e.g., "Chickens: Environmental Warriors!")
  - Vocabulary MCQs (e.g., lackadaisical)
  - Math geometry (composite volume — cylinder + cone)
  - Data table questions (seed/cotyledon)
  - Select All That Apply (checkboxes, multi-select)

### Quiz Creation Flow (2-step)
- **Step 1:** Topic selection with checkboxes (Science, Anatomy, Biology, Chemistry, Scientific Reasoning, English subtopics)
- **Step 2:** Quiz name (auto-filled with date/time), question count slider (5–100), Study Mode vs Exam Mode toggle

### Review & Progress Features
- **Flagged Questions:** 57 flagged, filterable by subject (Math 21, Science 30, English 6, Reading 0), "Start Review" button
- **Previous Quizzes:** 42 completed, 16 incomplete (resumable), shows date started + completion date
- **Question of the Day:** daily engagement hook with START button

### Question Formats Observed
- Multiple choice (A/B/C/D)
- **Select All That Apply** (checkboxes, multi-select)
- Data table questions (seed/cotyledon table)
- Standard MCQ with passage-based questions (implied by Reading subcategories)

---

## Question Pool Estimates

| Subject | Used | Remaining | Est. Total |
|---------|------|-----------|------------|
| Overall | 507 | 1,793 | ~2,300 |
| Math | 274 | 229 | ~503 |
| Reading | 164 | 501 | ~665 |
| English | 131 | 368 | ~499 |
| Science | Not shown | Not shown | TBD |

Note: Per-subject totals don't sum to overall 2,300 — suggests some questions may be tagged across subjects or the counter logic differs.

---

## Competitive Comparison

| Feature | ATI TEAS App | TEAS Study App (Mu2) |
|---------|-------------|---------------------|
| Question pool | ~2,300 | 2,003 (competitive) |
| Explanations | Static per-choice rationale | Socratic AI tutor (adaptive) |
| Quiz modes | Study + Exam | TBD |
| Question count config | 5-100 slider | TBD |
| Flagged questions | ✅ (57 flagged) | Not yet |
| Previous quiz history | ✅ (42 completed, 16 resumable) | Not yet |
| Question of the Day | ✅ | Not yet |
| Custom quiz builder | ✅ | Not yet |
| AI tutoring | ❌ None | **Core feature** |
| Adaptive difficulty | ❌ No | Planned (Gemma 4) |
| Subcategory tracking | ✅ TEAS-aligned | ✅ Same structure |
| Select All That Apply | ✅ | ✅ In DB |
| Price | Paid subscription | Free/affordable |
| Platform | Mobile app | Web/PWA |
| Explanation quality | Static textbook paragraphs | Conversational, targeted, misconception-aware |

---

## Key Strategic Insights

### What ATI Does Well
1. **Clean, simple UX** — low friction, quiz-first design
2. **Study vs Exam mode** — lets students choose how they want to practice
3. **Per-choice rationales** — explains every option, not just the correct one
4. **Flagged questions** — students can bookmark hard questions for review
5. **Quiz history + resume** — incomplete quizzes are resumable
6. **Question of the Day** — simple daily engagement hook
7. **Question count flexibility** — 5-100 lets students do quick drills or full sessions

### Where ATI Falls Short (Our Opportunities)
1. **Zero AI** — no adaptive learning, no conversation, no misconception detection
2. **Static explanations** — same text every time, regardless of student's actual confusion
3. **No Socratic method** — just quiz → answer → read → next. No teaching.
4. **No follow-up questions** — if a student picks wrong, they read why, but never get guided to understanding
5. **No difficulty adaptation** — same question pool, same order, no personalization
6. **Paid subscription** — barrier for CNA students, single parents, rural learners (our target market)
7. **Mobile-only** — no web/PWA, no desktop access

### Our Unfair Advantages
1. **Socratic AI tutor** — doesn't just explain, *guides* the student to understanding
2. **Misconception detection** — identifies *why* the student got it wrong, not just *that* they did
3. **Adaptive follow-ups** — each session is unique based on the student's responses
4. **Free/affordable** — David Tran philosophy: rich man's sauce at poor man's price
5. **Open source** — community trust, no lock-in
6. **Web/PWA** — works on any device, no app store required

---

## Feature Priorities for TEAS Study App

### Must Match (Table Stakes)
- [ ] Study Mode vs Exam Mode toggle
- [ ] Question count selector (5-100 range)
- [ ] Flagged/bookmark questions system
- [ ] Previous quiz history with resume
- [ ] Question of the Day
- [ ] Per-choice explanations (at minimum, match ATI's depth)

### Must Beat (Differentiators)
- [x] AI Socratic tutoring (core architecture)
- [ ] Misconception-aware explanations
- [ ] Adaptive difficulty progression
- [ ] Conversational follow-up questions

### Nice to Have
- [ ] Custom quiz builder (topic + count + difficulty)
- [ ] Streak tracking / gamification
- [ ] Study reminders
- [ ] Weak area identification dashboard

---

## Notes
- The "Unize" user account appears to be a test/demo account (all quizzes show "Date Started: 05/01/2026" regardless of listed completion date)
- ATI's explanation quality is solid but generic — textbook-style paragraphs, not personalized
- The Select All That Apply format with full per-option rationales is their strongest content feature
