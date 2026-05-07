# TEAS Study App — Build Blueprint

> Version 2.0 — May 1, 2026
> AI Tutor: Gemma 4 E4B (router) + Gemma 4 26B A4B (teacher)
> Inference: Google AI Studio
> Delivery: Hosted web app / PWA on Digital Ocean
> Framework: Flask + Jinja2 + Tailwind CSS CDN

---

## 1. Product Vision

**TEAS Study Buddy** — a hosted web app for nursing students preparing for the ATI TEAS 7 exam. Access from any device with a browser. Every wrong answer gets an AI explanation grounded in real OpenStax content — not a generic hint, not a textbook page number, a real Socratic conversation powered by a dual-model AI tutor.

**Core promise:** "Learn *why*, not just *what*."

### Differentiation vs Competitors

| Feature | PocketPrep/Mometrix | UWorld | **TEAS Study Buddy** |
|---------|--------------------|--------|---------------------|
| Price | $30-60 subscription | $59/month | Affordable one-time or low monthly |
| Internet required | Always | Always | Always (AI tutor is the core) |
| Explains wrong answers | Generic feedback | Generic feedback | AI tutor explains *why* (Socratic) |
| Learn mode (lessons) | No — quiz only | Minimal | Yes — short lessons before quizzes |
| Spaced repetition | Basic | No | Yes — targets weak areas |
| Device needed | Phone/browser | Browser | Any browser (phone, tablet, laptop) |
| Progress tracking | Basic | Detailed | Detailed + predicted score |
| Content source | Proprietary | Proprietary | OpenStax (transparent) |
| AI architecture | None | None | Dual-model (router + teacher) |

### Monetization: Reverse Free Trial

**The Play:** Give away the quiz bank for free. Let students grind questions for 2-3 weeks while the app silently builds a learning profile. Then auto-activate the AI tutor — it walks in already knowing exactly what the student needs.

**Flow:**
1. Student signs up → free access to 2,000+ questions (no credit card, no trial timer)
2. 2-3 weeks of quizzing → app tracks: weak areas, missed concepts, struggle patterns, time-per-question, misconceptions
3. AI tutor auto-activates → first message: *"Hey, I noticed you've been struggling with polynomials — let's work through that"*
4. Student experiences the "wow moment" — the tutor already knows them

**Why this beats a traditional free trial:**
- Zero cold-start problem — the AI tutor has real student data on day one
- Student is already invested and frustrated with their weak spots when AI turns on
- No bait-and-switch feel — they got real value (full question bank) for free before upsell
- The tutor proves its worth immediately instead of needing 5 sessions to learn the student
- Students don't realize they need AI tutoring until they've hit a wall with hard problems — then it feels like magic

**The psychological hook:** Give away the commodity (questions — everyone has those), charge for the thing nobody else has (Socratic AI that already knows you).

**Free tier (permanent):** Full question bank + Smart Daily Plan + Confidence Slider + Mistake Bank + Quickfire Mode + Streak System + Celebration Animations + Per-Question Review + Topic-Level Mastery Tracking + Progress Heatmap + Readiness Scores
**Paid tier:** AI Socratic tutor + misconception diagnosis + personalized study plans + predicted scores + Full Exam Mode

**Full Exam Mode (paid tier):**
- Timed full-length practice exams (all 4 subjects, real TEAS time limits: Math 57 min, Science 60 min, Reading 55 min, English+Language 37 min)
- Composite score + per-subject breakdown with percentile ranking
- "Not ready yet" gate — if mastery data suggests the student will score poorly, the exam locks with a message: *"You're making great progress, but we think a few more study sessions will set you up for success"* — protects brand reputation
- Post-exam AI tutor debrief — walks through weakest areas with Socratic follow-up
- Unlimited retakes (subscription model means no per-exam gouging)
- Authentic difficulty curve — questions selected by mastery data to simulate real TEAS feel

**Why this is a killer paid feature:** ATI charges $50-60 for a single practice exam. We bundle unlimited full exams into a $12.99/mo subscription. That's the David Tran philosophy in action — rich man's product at a poor man's price. The single mom studying at night after her shift gets the same exam prep as someone who can afford ATI's premium package.

**Free tier design goal:** "Why are you paying for ATI when TEAS Study App is way better and FREE?" — the free tier must CRUSH ATI on UX alone. The AI tutor and exam mode are the upsell, not the only differentiator.

### Pricing Tiers

| Plan | Price | Per Month | Billing |
|------|-------|-----------|---------|
| Monthly | $12.99/mo | $12.99 | Auto-renew |
| Quarterly | $29.99/qtr | $10.00 | Auto-renew |
| Yearly | $79.99/yr | $6.67 | Auto-renew |

Competitive context: PocketPrep $30-60, UWorld $59/mo. We undercut everyone while offering something nobody has (Socratic AI).

### Financial Model

**Per-interaction AI cost (1 wrong answer explained):**
- Router (Gemma 4 E4B): $0.00 — free on Google AI Studio
- Teacher (Gemma 4 26B A4B): $0.00 — free on Google AI Studio (no paid tier exists)
- Contingency (if Google ever charges): ~$0.0003 per interaction at Gemini Flash rates

**Infrastructure scaling (Digital Ocean Droplet + Google AI Studio):**

| Phase | Students | DO Droplet | Google AI Studio | Total/Mo |
|-------|----------|-----------|-----------------|----------|
| 1 — Launch | 0-50 | Free tier ($0) | Free ($0) | **$0** |
| 2 — Growing | 50-200 | 1 vCPU, 1GB ($6) | Free ($0) | **$6** |
| 3 — Scaled | 200-500 | 1 vCPU, 2GB ($12) | Free ($0) | **$12** |
| 4 — Heavy | 500+ | 2 vCPU, 4GB ($24) | ~$4 pay-as-you-go | **~$28** |

**Per-student COGS at each phase:**

| Phase | Infra/Mo | Students | COGS/Student |
|-------|----------|----------|-------------|
| Launch (50) | $0 | 50 | $0.00 |
| Growing (100) | $6 | 100 | $0.06 |
| Scaled (250) | $12 | 250 | $0.05 |
| Heavy (500) | $28 | 500 | $0.06 |

**Revenue projections:**

| Students | Monthly Plan | Yearly Plan | Mix (realistic) |
|----------|-------------|-------------|-----------------|
| 50 | $643/mo | $327/mo | ~$450/mo |
| 100 | $1,286/mo | $654/mo | ~$900/mo |
| 250 | $3,215/mo | $1,635/mo | ~$2,250/mo |
| 500 | $6,430/mo | $3,270/mo | ~$4,500/mo |

**Key assumptions:**
- Gemma 4 is free on Google AI Studio — no paid tier, confirmed on Google's pricing page
- Even if Google flips to pay-as-you-go at Gemini Flash rates, COGS stays under $0.10/student/month
- DO droplet doesn't need GPU — it serves the web app and proxies API calls to Google
- The droplet handles HTTPS, public IP, and uptime (things a home mini-PC on residential WiFi cannot)

**Dev vs Production split:**
- **M7-Ultra (local):** dev, testing, question generation, eval runs
- **Digital Ocean (production):** web app frontend + backend, public-facing
- **Google AI Studio (inference):** Gemma 4 E4B router + Gemma 4 26B A4B teacher

### Revenue Expansion: Beyond the App

#### Public TEAS NotebookLM
- **What:** Free public NotebookLM built from OpenStax TEAS content (Math, Science, Reading, English)
- **Why:** Zero cost to Mu2 (Google's infrastructure), students self-serve quiz and flashcard generation
- **Strategic value:** Extends Mu2 brand into Google's ecosystem without writing code. App = structured practice, NotebookLM = open exploration
- **Message to students:** "Why pay ATI for flashcards when Mu2 gives you the raw material to make your own?"
- **NotebookLM sources:** OpenStax College Algebra, Concepts of Biology, Reading/Writing guides — all OER, all free

#### TEAS Workbook (PDF + Print-on-Demand)
- **What:** Comprehensive TEAS study workbook covering all 4 subjects, aligned with the app's question bank
- **Formats:** Free PDF download from teas.mu2.solutions + Print-on-Demand (Amazon KDP or similar, zero inventory risk)
- **Content:** Concept review, worked examples, practice problems, tear-out formula sheets, study schedules
- **Pricing target:** PDF free, POD paperback at $12-15 (undercutting ATI's $30-50 study guides)
- **Strategic value:** Physical study aids still dominate — Amazon "TEAS study guide" = pages of $20-40 books. Students who buy the workbook enter our funnel → app download → free tier engagement → paid tier conversion
- **Production:** python-docx for manuscript, KDP for print (no inventory, no warehouse, no risk)

### Competitive Target: ATI

ATI is the 800-lb gorilla. Their product is stale — expensive, quiz-only, no AI, no personalization, coasting on brand name. Mu2 is not competing with ATI. Mu2 is making ATI irrelevant.

**Full-spectrum assault (none of which ATI offers):**
1. Free app with best-in-class UX
2. Free NotebookLM for open exploration
3. Affordable workbook for the "I need a real book" crowd
4. $12.99/mo paid tier with AI tutor + full exam mode

ATI charges $50-60 for a single practice exam. We give away the question bank, the NotebookLM, and the PDF workbook — then charge less than a quarter of ATI's price for the full premium experience.

### What the UX research says

- Students study in **5-10 minute bursts** between classes, during breaks, on the bus
- **Anxiety is the enemy** — calm, clean interface reduces test stress
- Biggest competitor weakness: **quiz-only, no teaching** — students memorize answers but don't understand concepts
- **Dark mode is expected**, not a premium feature
- **Mobile-first design** — most students will use phones
- **Progress visibility drives motivation** — "I'm 68% ready for Math" is more motivating than "you got 12/15 correct"

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                Digital Ocean Droplet                  │
│  ┌────────────────────────────────────────────────┐  │
│  │        Flask + Jinja2 + Tailwind CSS           │  │
│  │  ┌──────────┐  ┌──────┐  ┌──────────────────┐ │  │
│  │  │  Flask   │  │SQLite│  │  Static Assets   │ │  │
│  │  │  App     │  │  DB  │  │  (CSS/JS/PWA)    │ │  │
│  │  └────┬─────┘  └──────┘  └──────────────────┘ │  │
│  └───────┼─────────────────────────────────────────┘  │
│          │                                            │
│          │  HTTPS (public IP, managed SSL)            │
│          │                                            │
└──────────┼────────────────────────────────────────────┘
           │
    ┌──────┴──────┐
    │   Student   │
    │  (Browser)  │
    └─────────────┘

           │
           │  AI Tutor Calls (OpenAI-compatible API)
           ▼
 ┌─────────────────────┐
 │   Google AI Studio   │
 │  (FREE — no paid     │
 │   tier exists)       │
 │                     │
 │  ┌───────────────┐  │
 │  │ Gemma 4 E4B  │  │  ← Router: classifies question,
 │  │  (Router)     │  │     selects KB context, routes
 │  └──────┬────────┘  │
 │         │           │
 │         ▼           │
 │  ┌───────────────┐  │
 │  │ Gemma 4 26B  │  │  ← Teacher: Socratic explanation,
 │  │  A4B (Teacher)│  │     guiding questions, never gives
 │  └───────────────┘  │     answer directly
 │                     │
 │  Free tier: ~250    │
 │  RPD (requestable)  │
 └─────────────────────┘

 ┌─────────────────────┐
 │   M7-Ultra (Local)  │
 │  Dev / Testing /    │
 │  Question Gen /     │
 │  Eval Runs          │
 └─────────────────────┘
```

### How it works

1. **Student opens app** in any browser (phone, tablet, laptop)
2. **Sign up / login** — email + password (progress persists across devices)
3. Dashboard shows readiness scores, weak areas, study recommendations
4. Quizzes load from unified KB (SQLite on server)
5. **Wrong answers trigger the dual-model AI tutor:**
   - **Router (Gemma 4 E4B):** Classifies the question, pulls relevant KB context (misconception, topic, difficulty), builds the teacher prompt
   - **Teacher (Gemma 4 26B A4B):** Generates a Socratic explanation — why the student's answer is wrong, what concept they're missing, a guiding question to lead them to the right answer
6. All progress saves to server-side SQLite (per-user)
7. PWA support — installable on phones/tablets for app-like experience

### Dual-Model AI Tutor — Why Two Models?

The router/teacher split is the core differentiator. No competitor does this.

**Router (Gemma 4 E4B — fast, cheap):**
- Classifies question type and difficulty
- Queries KB for relevant misconception data
- Selects appropriate teaching strategy
- Builds the context-rich prompt for the teacher
- Cost: ~$0.04/million tokens (essentially free on Google AI Studio free tier)

**Teacher (Gemma 4 26B A4B — smart, still cheap):**
- Receives a rich prompt from the router (question + wrong answer + KB context + student history + teaching strategy)
- Generates Socratic explanation in 2-3 sentences
- Asks one guiding question (never gives the answer directly)
- Cost: ~$0.08/million tokens (free tier covers 1500 req/day)

**Why not one model?** A single model doing both classification and teaching burns tokens on routing logic that doesn't need a large model. The E4B router handles the "thinking about what to teach" in milliseconds, then hands a perfectly crafted prompt to the 26B teacher. Result: better teaching at lower cost.

### AI Tutor Flow

```
Student answers wrong
         │
         ▼
┌───────────────────┐
│ Router (E4B)      │
│ 1. Classify Q     │
│ 2. Query KB       │
│ 3. Build prompt   │
└───────┬───────────┘
        │
        ▼
┌───────────────────────────────────┐
│ Teacher (26B A4B) prompt:         │
│ - Student's wrong answer          │
│ - Correct answer                  │
│ - KB misconception context        │
│ - Student's history (weak areas)  │
│ - Socratic teaching instruction   │
│ - Teaching strategy from router   │
└───────┬───────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ Teacher response:                 │
│ - Why the student's answer is    │
│   a common misconception         │
│ - What concept they're missing   │
│ - Guiding question to lead them  │
│   to the right answer themselves │
└───────────────────────────────────┘
```

**Google AI Studio config:**
- Router model: `gemma-4-e4b` via Gemini API
- Teacher model: `gemma-4-26b-a4b` via Gemini API
- `max_tokens`: 1024 (explanations, not essays)
- Temperature: 0.7 (slight warmth, not creative writing)
- Response format: plain text
- Free tier: 1,500 requests/day (sufficient for launch; paid tier scales cheaply)

**Router prompt pattern:**
```
You are a TEAS 7 question classifier. Given this question, the student's wrong answer, and the correct answer, determine:
1. Subject and topic
2. Difficulty level (easy/medium/hard)
3. The most likely misconception from this wrong answer
4. Teaching strategy: "direct_explanation", "analogy", "step_by_step", or "counter_example"

Respond in JSON: {"subject": "...", "topic": "...", "difficulty": "...", "misconception_id": ..., "strategy": "..."}
```

**Teacher prompt pattern:**
```
You are a TEAS 7 exam tutor. A nursing student answered a question incorrectly.

Question: {question}
Student's answer: {student_answer}
Correct answer: {correct_answer}
Relevant misconception: {kb_misconception}
Common wrong answer pattern: {kb_wrong_pattern}
Teaching strategy: {router_strategy}
Student's weak areas: {weak_areas}

Explain WHY their answer is wrong in 2-3 sentences. Then ask ONE guiding
question that helps them discover the correct answer themselves.
Do NOT give the correct answer directly. Use simple language.
Strategy hint: {apply_router_strategy}
```

---

## 3. Design System

### Philosophy
"Study app that feels like a quiet library, not a casino."

No gamification gimmicks. No confetti. No streak counters. No points. Just clear progress and good teaching. Nursing students are adults preparing for a career — treat them that way.

### Color Palette

**Light mode:**
- Background: `#FAFAF7` (warm off-white, easy on eyes)
- Surface: `#FFFFFF` (cards, panels)
- Primary: `#1B4332` (deep forest green — medical/academic)
- Primary light: `#2D6A4F`
- Accent: `#40916C` (green for correct, progress)
- Error: `#D00000` (red for wrong answers — clear, not alarming)
- Warning: `#E85D04` (orange for "needs review")
- Text primary: `#1A1A2E` (near-black, high contrast)
- Text secondary: `#6B7280` (gray for hints, metadata)
- Border: `#E5E7EB`

**Dark mode:**
- Background: `#1A1A2E`
- Surface: `#16213E`
- Primary: `#52B788` (lighter green for visibility)
- Primary light: `#74C69D`
- Accent: `#40916C`
- Error: `#EF4444`
- Warning: `#F59E0B`
- Text primary: `#E5E7EB`
- Text secondary: `#9CA3AF`
- Border: `#2A3A5C`

### Typography
- **Headings:** Libre Baskerville (serif, academic feel) — Google Fonts CDN
- **Body:** Source Sans 3 (clean, readable) — Google Fonts CDN
- **Code/Math:** JetBrains Mono (for formulas, line numbers)

Scale: 16px base, modular scale 1.25 (16 → 20 → 25 → 31 → 39)

### Spacing & Layout
- Max content width: 720px (reading comfort, not full-width)
- Card padding: 24px
- Card border-radius: 8px (subtle, not pill-shaped)
- Card shadow: `0 1px 3px rgba(0,0,0,0.08)` (barely there)
- Section gaps: 32px
- Mobile breakpoint: 640px (single column below)

### Component Rules
- **No glassmorphism** — solid backgrounds only
- **No gradients** — flat colors
- **No rounded pill buttons** — 6px border-radius, rectangular
- **No emoji in UI** — use icons from a minimal icon set (Lucide or similar)
- **Cards have 1px borders**, not shadow-heavy
- **Buttons:** primary = filled green, secondary = outlined, danger = outlined red
- **Inputs:** 1px border, 8px radius, 12px padding, no floating labels

---

## 4. Screen Specifications

### Screen 0: Sign Up / Login

**Purpose:** Account creation and authentication

```
┌─────────────────────────────────────┐
│                                     │
│         TEAS Study Buddy            │
│                                     │
│  "Learn why, not just what."        │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Email                       │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ Password                    │    │
│  └─────────────────────────────┘    │
│                                     │
│  [  Sign Up  ]  [  Log In  ]       │
│                                     │
│  Content: OpenStax (CC BY 4.0)      │
│  AI Tutor: Gemma 4 (Google AI)      │
└─────────────────────────────────────┘
```

**Behavior:**
- Email + password (no social login for MVP)
- Server-side session (Flask session with secure cookie)
- On signup: create user row in DB, redirect to welcome
- On login: load progress, redirect to dashboard
- Password hashing: werkzeug security (Flask built-in)

### Screen 1: Dashboard (Home)

**Purpose:** "What should I study right now?"

```
┌─────────────────────────────────────┐
│  TEAS Study Buddy        [🌙 Dark] │
├─────────────────────────────────────┤
│                                     │
│  Your TEAS Readiness                │
│  ████████░░░░░░░  68% overall       │
│                                     │
│  ┌──────────┐  ┌──────────┐        │
│  │  Math    │  │ English  │        │
│  │  86% ✓   │  │  72%     │        │
│  │  3 weak  │  │  5 weak  │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐        │
│  │ Science  │  │ Reading  │        │
│  │  91% ✓   │  │  45% ⚠   │        │
│  │  1 weak  │  │  8 weak  │        │
│  └──────────┘  └──────────┘        │
│                                     │
│  Study Recommendations              │
│  → Reading: Key Ideas & Details    │
│  → English: Subject-Verb Agreement │
│                                     │
│  ┌──────────┐  ┌──────────┐        │
│  │ Quick    │  │ Study    │        │
│  │ Quiz     │  │ Mode     │        │
│  │ 10 min   │  │ 25 min   │        │
│  └──────────┘  └──────────┘        │
└─────────────────────────────────────┘
```

**Behavior:**
- Overall readiness = weighted average of 4 subjects (TEAS weights: Reading 28%, Math 26%, Science 32%, English 14%)
- Subject cards show: readiness %, number of weak areas, color indicator (green >80%, orange 60-80%, red <60%)
- "Study Recommendations" lists the 2 weakest topics across all subjects
- "Quick Quiz" = 5 random questions from weak areas, estimated 10 min
- "Study Mode" = lesson + quiz on recommended topic, estimated 25 min
- Dark mode toggle persists in user settings (server-side)

### Screen 2: Subject Overview

**Purpose:** Deep dive into one subject

```
┌─────────────────────────────────────┐
│  ← Back    Mathematics    86%       │
├─────────────────────────────────────┤
│                                     │
│  ██████████████████░░░░  86%        │
│  127 questions answered             │
│                                     │
│  Topics:                            │
│  ┌─────────────────────────────┐    │
│  │ Numbers & Operations   92% │ ✓  │
│  │ ████████████████████░░░░░  │    │
│  │ 45 questions · 3 weak     │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ Algebra                78% │ ⚠  │
│  │ ██████████████░░░░░░░░░░░  │    │
│  │ 38 questions · 6 weak     │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ Data Interpretation     85% │ ✓  │
│  │ ██████████████████░░░░░░░  │    │
│  │ 44 questions · 2 weak     │    │
│  └─────────────────────────────┘    │
│                                     │
│  [Study Weakest]  [Quiz All]        │
└─────────────────────────────────────┘
```

**Behavior:**
- Topic readiness = weighted average of question accuracy in that topic
- Topics with <60% readiness get orange highlight
- "Study Weakest" opens Study Mode on the lowest-scoring topic
- "Quiz All" starts a quiz mixing all topics at proportional weights

### Screen 3: Study Mode (Learn + Quiz)

**Purpose:** The core differentiator — teach before testing

```
┌─────────────────────────────────────┐
│  ← Back    Algebra    Step 1 of 3   │
├─────────────────────────────────────┤
│                                     │
│  LEARN                              │
│  ─────────────────────────          │
│  Solving Linear Equations           │
│                                     │
│  To solve 3x + 7 = 22:             │
│  1. Isolate the variable term       │
│     3x = 22 - 7                     │
│     3x = 15                         │
│  2. Divide both sides by the coeff  │
│     x = 15 / 3                      │
│     x = 5                           │
│                                     │
│  Common mistake: subtracting 3      │
│  instead of dividing. Remember:     │
│  the coefficient multiplies x,      │
│  so you divide to undo it.          │
│                                     │
│  ─────────────────────────          │
│  Got it? Try these:                 │
│                                     │
│  2x + 5 = 17                        │
│  x = ?                              │
│  [ 4 ]  [ 6 ]  [ 11 ]  [ 12 ]       │
│                                     │
└─────────────────────────────────────┘
```

**Behavior:**
- Study Mode has 3 steps: LEARN → PRACTICE → QUIZ
- **LEARN:** Short lesson (3-5 sentences) with one worked example and one common mistake callout. Sourced from KB misconception data.
- **PRACTICE:** 2-3 guided questions with immediate feedback. Wrong answers trigger the AI tutor.
- **QUIZ:** 5-10 questions, scored, no hints. Results feed into progress tracking.
- Estimated time per Study Mode session: 15-25 minutes

### Screen 4: Quiz Mode (Quick Quiz)

**Purpose:** "I only have 10 minutes"

```
┌─────────────────────────────────────┐
│  Quick Quiz    Q 3 of 5    ⏱ 7:42  │
├─────────────────────────────────────┤
│                                     │
│  Mathematics · Algebra              │
│                                     │
│  Which equation represents          │
│  "seven less than twice a number    │
│  is fifteen"?                       │
│                                     │
│  ○  7 - 2n = 15                    │
│  ○  2n - 7 = 15                    │
│  ○  2(n - 7) = 15                  │
│  ○  15 - 2n = 7                    │
│                                     │
│           [Skip →]                  │
└─────────────────────────────────────┘
```

**After answering:**

```
┌─────────────────────────────────────┐
│  Quick Quiz    Q 3 of 5             │
├─────────────────────────────────────┤
│                                     │
│  ✗ Incorrect                       │
│  You answered: 7 - 2n = 15         │
│  Correct: 2n - 7 = 15              │
│                                     │
│  ── AI Tutor ────────────────────── │
│                                     │
│  The phrase "seven less than twice  │
│  a number" means you take "twice    │
│  a number" FIRST, then subtract 7.  │
│                                     │
│  Think of it this way: if n = 11,   │
│  twice n is 22. Seven less than     │
│  that is 15. So: 2(11) - 7 = 15.   │
│                                     │
│  Quick question: what would "five   │
│  more than three times a number"    │
│  look like?                         │
│                                     │
│  [3n + 5]  [5(n + 3)]  [3n - 5]    │
│                                     │
│           [Continue →]              │
└─────────────────────────────────────┘
```

**Behavior:**
- 4 answer choices (multiple choice), radio buttons
- Timer counts UP (not down — no added anxiety)
- Skip button available (question marked for review)
- After answering: show correct/wrong, then AI tutor explanation (dual-model: router classifies → teacher explains)
- If AI tutor asked a follow-up question, student can answer it
- "Continue" moves to next question
- At end: score summary with topic breakdown

### Screen 5: Results & Progress

```
┌─────────────────────────────────────┐
│  Quiz Complete                      │
├─────────────────────────────────────┤
│                                     │
│       Quick Quiz Results            │
│                                     │
│       4 of 5 correct (80%)          │
│                                     │
│  Mathematics · Algebra        3/3  │
│  Mathematics · Numbers & Op  1/2   │
│                                     │
│  ── Questions to Review ──          │
│                                     │
│  Q2: Which equation represents...   │
│      Your answer: 7 - 2n = 15      │
│      [Review with AI Tutor]         │
│                                     │
│  ── Overall Progress ──             │
│                                     │
│  Total questions: 342               │
│  Accuracy: 76%                      │
│  Since last week: +4%               │
│                                     │
│  [Study Weak Areas]  [Dashboard]    │
└─────────────────────────────────────┘
```

**Behavior:**
- Questions answered incorrectly go into a review queue
- Review queue feeds spaced repetition (questions resurface after 1 day, 3 days, 7 days)
- "Review with AI Tutor" opens a 1-on-1 chat about that specific question
- Progress stats are cumulative across all sessions (server-side, per user)

### Screen 6: AI Tutor Chat (1-on-1)

```
┌─────────────────────────────────────┐
│  ← Back    AI Tutor                 │
├─────────────────────────────────────┤
│                                     │
│  Context: Q2 from Quick Quiz        │
│  "Which equation represents         │
│   seven less than twice a           │
│   number is fifteen?"               │
│                                     │
│  ┌───────────────────────────┐     │
│  │ Let's break this down.    │     │
│  │                           │     │
│  │ "Twice a number" = 2n     │     │
│  │ "Seven less than" means   │     │
│  │ subtract 7 FROM that.     │     │
│  │                           │     │
│  │ So the order matters:     │     │
│  │ 2n first, then - 7.       │     │
│  │                           │     │
│  │ Try writing it as:        │     │
│  │ "something minus 7 = 15"  │     │
│  │ What is that "something"? │     │
│  └───────────────────────────┘     │
│                                     │
│  ┌───────────────────────────┐     │
│  │ I think it's 2n           │     │
│  └───────────────────────────┘     │
│                                     │
│  ┌───────────────────────────┐     │
│  │ Exactly! 2n - 7 = 15.    │     │
│  │ Now solve for n. What     │     │
│  │ do you get?               │     │
│  └───────────────────────────┘     │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Type your answer...    [Send]│   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Behavior:**
- Chat interface with context: the question that launched it
- AI tutor uses dual-model pipeline (router classifies follow-up → teacher responds)
- Socratic method: never gives the answer directly, always guides
- Student can ask follow-up questions freely
- Max 10 message exchanges per chat session (prevents infinite loops, saves API costs)
- No online/offline indicator — app requires internet for AI tutor

### Screen 7: Settings

```
┌─────────────────────────────────────┐
│  ← Back    Settings                 │
├─────────────────────────────────────┤
│                                     │
│  Appearance                         │
│  [  Light  ]  [  Dark  ]           │
│                                     │
│  Study Preferences                  │
│  Questions per quiz: [5 ▾]          │
│  Default mode: [Study ▾]            │
│  Show timer: [  On  ]              │
│                                     │
│  Account                            │
│  Email: student@example.com         │
│  [Change Password] [Log Out]        │
│                                     │
│  About                              │
│  TEAS Study Buddy v1.0              │
│  Content: OpenStax (CC BY 4.0)      │
│  AI Tutor: Gemma 4 (Google AI)      │
│  Hosted on Digital Ocean            │
└─────────────────────────────────────┘
```

---

## 5. User Flows

### Flow 1: First Visit
1. Student opens URL in browser
2. Sign up screen: email + password
3. Brief welcome (3 bullet points, no scrolling): what it does, how long to prepare, tip about dark mode
4. "Let's start" → Dashboard

### Flow 2: Daily Study (10 minutes)
1. Dashboard → "Quick Quiz" button
2. App selects 5 questions from weakest areas
3. Student answers 5 questions with AI tutor feedback on wrong answers
4. Results screen → "Study Weak Areas" or back to Dashboard

### Flow 3: Focused Study (25 minutes)
1. Dashboard → "Study Mode" or click a subject card
2. Subject Overview → click weakest topic or "Study Weakest"
3. Study Mode: LEARN (2 min lesson) → PRACTICE (3 questions) → QUIZ (5-10 questions)
4. Results screen with topic breakdown

### Flow 4: Deep Dive (confused about a concept)
1. From any quiz result → "Review with AI Tutor"
2. AI Tutor Chat opens with question context
3. Student asks questions, AI guides them through understanding
4. Student closes chat → question marked as "reviewed" (won't repeat immediately)

### Flow 5: Return Visit (different device)
1. Student opens URL on phone/tablet/laptop
2. Logs in with email + password
3. All progress, readiness scores, and review queue load from server
4. Picks up exactly where they left off

---

## 6. Data Model

### Server-side SQLite (per-user progress)

```sql
-- Users (replaces USB-as-identity)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT
);

-- Track every question attempt (per user)
CREATE TABLE question_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question_id TEXT NOT NULL,
    subject TEXT NOT NULL,          -- math, english, science, reading
    topic TEXT NOT NULL,
    correct INTEGER NOT NULL,       -- 1 or 0
    student_answer TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    quiz_type TEXT,                 -- 'quick', 'study_practice', 'study_quiz', 'tutor_chat'
    ai_tutor_used INTEGER DEFAULT 0 -- 1 if AI tutor explained this
);

-- Spaced repetition queue (per user)
CREATE TABLE review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    topic TEXT NOT NULL,
    next_review TEXT NOT NULL,      -- ISO date when to show again
    interval_days INTEGER DEFAULT 1, -- 1 → 3 → 7 → 14 → 30
    times_reviewed INTEGER DEFAULT 0,
    last_correct INTEGER            -- NULL if not yet reviewed
);

-- Subject/topic readiness (per user, denormalized for fast dashboard)
CREATE TABLE readiness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    subject TEXT NOT NULL,
    topic TEXT,
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    readiness_pct REAL DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, subject, topic)
);

-- User settings (per user)
CREATE TABLE settings (
    user_id INTEGER NOT NULL REFERENCES users(id),
    key TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (user_id, key)
);
-- Default rows per user: ('dark_mode', 'false'), ('questions_per_quiz', '5'), ('default_mode', 'quick')

-- AI tutor chat history (per user, for context within a session)
CREATE TABLE tutor_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question_id TEXT,
    role TEXT NOT NULL,             -- 'student', 'router', 'teacher'
    message TEXT NOT NULL,
    timestamp TEXT DEFAULT (datetime('now'))
);
```

### Knowledge Base (teas_unified.db — static, read-only)

```sql
-- All 4 subjects in one table (2,003 questions total)
CREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    subject TEXT,           -- math, english, science, reading
    topic TEXT,             -- specific topic within subject
    question_text TEXT,
    correct_answer TEXT,
    wrong_answers TEXT,     -- JSON array of 3 wrong options
    explanation TEXT,       -- 250+ chars
    difficulty TEXT,        -- easy, medium, hard
    misconception_id INTEGER REFERENCES misconceptions(id)
);

CREATE TABLE misconceptions (
    id INTEGER PRIMARY KEY,
    subject TEXT,
    topic TEXT,
    misconception TEXT,     -- the wrong belief
    correct_explanation TEXT,
    common_wrong_answer TEXT,
    why_students_err TEXT,
    teas_relevance TEXT,
    source TEXT
);
```

---

## 7. KB Integration

The unified KB (`data/kb/teas_unified.db`) already contains all 4 subjects with 500+ questions each. This is the read-only question bank the app queries.

**For quizzes:** App queries `questions` table by subject/topic/difficulty, shuffles options server-side, serves to student.

**For AI tutor context:** When a student answers wrong, the app looks up the question's `misconception_id`, fetches the misconception data, and passes it to the router model as context.

**For Study Mode lessons:** App queries `misconceptions` table by subject/topic, uses `misconception` + `correct_explanation` + `why_students_err` fields to build mini-lessons.

---

## 8. Phase Breakdown

### Phase 0: Auth + User System (2 days)
- [ ] User signup (email + password, werkzeug hashing)
- [ ] User login (server-side sessions, secure cookies)
- [ ] Password change flow
- [ ] Per-user DB schema (all tables have user_id)
- [ ] Migrate existing Flask app from USB-first to user-aware

### Phase 1: App Shell + Dashboard (3 days)
- [ ] Flask app with Jinja2 templates + Tailwind CDN
- [ ] Design system implemented (colors, typography, spacing)
- [ ] Dark mode toggle (server-side setting)
- [ ] Dashboard screen with 4 subject cards
- [ ] Readiness calculation from question_attempts
- [ ] Study recommendations (weakest topics first)
- [ ] Responsive layout (mobile-first)

### Phase 2: Quiz Engine (3 days)
- [ ] Question loading from unified KB
- [ ] Multiple choice UI with 4 options
- [ ] Answer validation + immediate feedback
- [ ] Quick Quiz mode (5 questions from weak areas)
- [ ] Timer (count-up, toggleable)
- [ ] Results screen with topic breakdown
- [ ] Progress saving to server DB

### Phase 3: Study Mode (3 days)
- [ ] LEARN step: misconception-based mini-lessons
- [ ] PRACTICE step: guided questions with hints
- [ ] QUIZ step: scored questions feeding progress
- [ ] Subject Overview with topic breakdowns
- [ ] Topic navigation from Subject Overview → Study Mode

### Phase 4: Dual-Model AI Tutor (3 days)
- [ ] Google AI Studio API client (Gemini API, urllib.request)
- [ ] Router integration (Gemma 4 E4B — classify + build prompt)
- [ ] Teacher integration (Gemma 4 26B A4B — Socratic response)
- [ ] AI Tutor Chat screen (context: specific question)
- [ ] Socratic method prompting (never give direct answers)
- [ ] Rate limiting (max 10 exchanges per chat)
- [ ] API key management via environment variables
- [ ] Error handling (API timeout, rate limit, free tier exhaustion)

### Phase 5: Spaced Repetition + Progress (2 days)
- [ ] Review queue population on wrong answers
- [ ] Interval scaling (1 → 3 → 7 → 14 → 30 days)
- [ ] Review questions surface in Quick Quiz
- [ ] "Study Weak Areas" prioritizes review queue
- [ ] Progress trends (comparison to last week)
- [ ] Settings screen

### Phase 6: PWA + Deploy (3 days)
- [ ] PWA manifest (installable on phones/tablets)
- [ ] Service worker (cache static assets for performance)
- [ ] Digital Ocean deployment (App Platform or Droplet)
- [ ] Domain setup + SSL (Let's Encrypt)
- [ ] Environment variable configuration on DO
- [ ] End-to-end testing on live URL
- [ ] Mobile testing (Chrome mobile, Safari)

**Estimated total: 19 working days**

---

## 9. Technical Constraints & Decisions

### Must-haves
- **Python 3.12+** — matching M7-Ultra's installed version
- **Flask** — no Django, no FastAPI, no SQLAlchemy. Raw sqlite3.
- **Tailwind CSS via CDN** — no build step, no npm
- **urllib.request** for API calls — no requests library
- **Single-page-app feel** — use HTMX or fetch() for partial updates, no full page reloads between quiz questions

### Nice-to-haves (Phase 7+)
- Export progress as PDF study report
- Keyboard shortcuts for quiz answers (1/2/3/4 keys)
- Sound effects (correct/wrong) — toggleable
- Print-friendly study guides from KB content
- Email digest of weekly progress

### Non-negotiable
- **Internet required** — AI tutor is the core value, no offline mode
- **User accounts required** — progress persists across devices
- **No subscription model** — affordable pricing (TBD: one-time or low monthly)
- **Works on any modern browser** — phone, tablet, laptop
- **Respects student privacy** — no data sharing, minimal PII (email + progress only)

### What NOT to build
- No social features (leaderboards, study groups)
- No video content (bandwidth cost)
- No adaptive testing algorithm (keep it simple — spaced repetition is enough)
- No native mobile app (PWA covers install-on-phone use case)
- No gamification (streaks, badges, levels — nursing students are adults)
- No offline mode (AI tutor requires internet; don't build a degraded half-product)

---

## 10. File Structure (App Code)

```
teas-study-app/
├── app.py                    # Flask app, all routes, auth
├── db.py                     # SQLite access (user progress, per-user)
├── kb.py                     # KB query layer (unified KB, read-only)
├── router.py                 # Gemma 4 E4B client (classify + build prompt)
├── teacher.py                # Gemma 4 26B A4B client (Socratic response)
├── ai_tutor.py               # Orchestrates router → teacher pipeline
├── progress.py               # Readiness calculations, spaced repetition
├── config.py                 # Settings, env vars, Google AI Studio key
├── requirements.txt          # flask, gunicorn
├── templates/
│   ├── base.html             # Layout shell, nav, dark mode toggle
│   ├── auth.html             # Login / signup
│   ├── dashboard.html
│   ├── subject.html
│   ├── study.html            # Study Mode (learn + practice + quiz)
│   ├── quiz.html             # Quick Quiz
│   ├── results.html
│   ├── tutor_chat.html       # AI Tutor 1-on-1
│   └── settings.html
├── static/
│   ├── css/
│   │   └── custom.css        # Design system overrides beyond Tailwind
│   ├── js/
│   │   ├── quiz.js           # Quiz interaction (answer selection, timer)
│   │   ├── tutor.js          # AI tutor chat (fetch API)
│   │   └── theme.js          # Dark mode toggle
│   ├── manifest.json         # PWA manifest
│   └── sw.js                 # Service worker (static asset caching)
├── data/
│   └── kb/
│       └── teas_unified.db   # All 4 subjects (2,003 questions)
├── .env.example              # GOOGLE_AI_KEY=, FLASK_SECRET=, etc.
├── Dockerfile                # For Digital Ocean deployment
└── Procfile                  # gunicorn app:app
```

### Deployment (Digital Ocean Droplet)

```
Digital Ocean Droplet (not App Platform — simpler, cheaper)
├── Droplet Tier (scales with students)
│   ├── Phase 1: Free tier (512MB RAM, 4GB transfer)
│   ├── Phase 2: Basic 1 vCPU, 1GB RAM ($6/mo)
│   ├── Phase 3: Basic 1 vCPU, 2GB RAM ($12/mo)
│   └── Phase 4: Basic 2 vCPU, 4GB RAM ($24/mo)
├── App: gunicorn app:app (Flask)
├── Database: SQLite on local filesystem
├── Env vars: GOOGLE_AI_KEY, FLASK_SECRET
├── Domain: custom domain + Let's Encrypt SSL
└── Reverse proxy: nginx (or Caddy for auto-SSL)
```

**Why Droplet over App Platform:**
- Droplet free tier = $0 to start, App Platform minimum is $5/mo
- Droplet = full control (nginx, cron jobs, logs), App Platform = opinionated
- No GPU needed on droplet — all inference happens at Google AI Studio
- Droplet only serves the web app and proxies API calls

---

*This blueprint is the design spec for building the TEAS Study App. Every screen layout, color, spacing rule, and interaction pattern is documented above. Build from this — don't invent new patterns.*

*Version 2.0 replaces Version 1.0 (USB delivery + GLM-5.1). The product pivoted to hosted web app + dual Gemma 4 models on Google AI Studio, deployed on Digital Ocean Droplet. Infrastructure cost scales from $0 to ~$28/month as the user base grows. Old v1.0 backed up as BUILD_BLUEPRINT.v1.md.bak.*
