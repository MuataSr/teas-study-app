# TEAS Study App — UX Design Vision

**Date:** May 2, 2026
**Author:** Ann-E
**Status:** Design Doc — Pre-Flask Build
**Principle:** "ATI asks the student to do the work of deciding what to study. Our app does that thinking for them."

---

## Core Design Philosophy

ATI built a test engine. We're building a study *experience*.

The difference: a tool tells you what you got wrong. A tutor guides you to stop getting it wrong. Every UX decision should feel like a smart study buddy, not a cold quiz machine.

### Anti-Patterns (What We're NOT Building)
- No boring menus asking "what do you want to study?"
- No stale percentage-only results pages
- No flat lists of flagged questions
- No decision fatigue
- No "homework chore" feeling

### Design Principles
1. **Zero decision fatigue** — app opens with a plan, not a menu
2. **Celebrate progress** — animations, streaks, milestones
3. **Teach metacognition** — confidence tracking builds self-awareness
4. **Smart, not static** — spaced repetition and weak-area targeting
5. **One more round** — gamification that makes you want to stay, not escape

---

## Feature Specifications

### 1. Smart Daily Plan (replaces "New Quiz" as default landing)

**ATI's approach:** Menu with 3 options (Custom Quiz, Random Quiz, Quick Start)
**Our approach:** App opens directly to a personalized study plan

**What it shows:**
- Greeting: *"Good evening! Here's your 5-minute plan for today"*
- Pre-selected questions based on:
  - Spaced repetition (surfaces questions due for review)
  - Weak areas (topics below 70% mastery)
  - Time since last session (topics not touched recently)
- Single "Start" button — tap and go
- "Customize" link for power users who want to pick subjects/topics/count

**Why this wins:** Removes the "what should I study?" barrier. Students open the app and immediately start learning. ATI makes you navigate a menu before seeing a single question.

**Tech notes:**
- Algorithm: weighted random from topics where `mastery < 80` or `days_since_last_review > 2`
- Default count: 10 questions
- "Customize" expands to show subject/topic checkboxes + count slider

---

### 2. Confidence Slider (replaces Study/Exam mode toggle + flag button)

**ATI's approach:** Binary Study Mode (show answer) vs Exam Mode (hide answer) + separate flag button
**Our approach:** After every answer, a 1-5 confidence slider appears

**Scale:**
1. "Lucky guess" 🎲
2. "Not really sure" 🤔
3. "Somewhat confident" 🤷
4. "Pretty sure" 💪
5. "Nailed it" 🔥

**Logic:**
- Low confidence (1-2) + correct → flagged for review (you don't actually know it)
- High confidence (4-5) + wrong → **priority flagged** (you thought you knew it — dangerous misconception)
- Mid confidence (3) → neutral, shows in normal rotation
- This replaces both the flag button AND the study/exam mode toggle
- Questions with low confidence always show the explanation; high confidence correct answers skip explanation (saves time)

**Why this wins:** Teaches metacognition. Students learn to calibrate their own understanding. ATI's flag button is thoughtless — tap and forget. Our confidence slider makes the student *reflect* on every answer.

**Tech notes:**
- Store confidence score alongside answer in DB
- `db.record_answer()` gains `confidence` column (int, 1-5)
- Mistake Bank query weights by: confidence mismatch (high conf + wrong = top priority), days since last attempt, topic weakness

---

### 3. Mistake Bank (replaces flat flagged questions list)

**ATI's approach:** 57 flagged questions in a flat list, filterable by subject, "Start Review" button
**Our approach:** Living, prioritized collection with forgetting curves

**What it shows:**
- Total mistakes count with visual urgency (low = green, high = amber, very high = red)
- Prioritized queue based on:
  1. Confidence mismatches (thought you knew it → wrong) — highest priority
  2. Repeated mistakes (same question/topic missed multiple times)
  3. Time decay (haven't seen it in a while — forgetting curve)
  4. Topic weakness (struggling area overall)
- *"You got this wrong 3 days ago — try again?"* style prompts
- Quick review option: "Review 5 weak spots" (one-tap)

**Why this wins:** ATI's flagged list is a graveyard — 57 questions, no prioritization, no intelligence. Our Mistake Bank actively surfaces what matters *right now* based on learning science.

**Tech notes:**
- New DB table: `mistake_bank` with columns: question_id, subject, topic, last_wrong_at, wrong_count, last_confidence, priority_score
- Priority score computed: `confidence_mismatch * 10 + wrong_count * 3 + days_since_review * 1 + (100 - topic_mastery) * 0.5`
- Cron-like recalculation on each quiz completion

---

### 4. Quickfire Mode (complements standard quiz)

**ATI's approach:** Standard quiz with configurable count (5-100), timer shown but optional
**Our approach:** 60-second rapid-fire gamified mode

**How it works:**
- Student selects subject (or mixed)
- 60-second countdown starts
- Questions appear one at a time, tap answer → instant next question
- No explanations during Quickfire (speed is the game)
- End screen: score, questions per minute, personal best tracking
- *"You answered 12 questions in 60 seconds — new personal best!"*

**Why this wins:** Gamification. The "one more round" feeling. ATI's quiz feels like homework. Quickfire feels like a game you want to beat your score at. Perfect for short study sessions (bus stop, waiting room, between classes).

**Tech notes:**
- Separate route: `/quickfire/<subject_slug>`
- Timer runs client-side (JS countdown)
- Server endpoint receives rapid-fire answers via AJAX (not page redirects)
- Personal best stored in DB: `quickfire_bests` (subject, questions_answered, correct, date)

---

### 5. Visual Streak System (upgrades existing streak tracking)

**ATI's approach:** No streak system at all
**Our approach:** Duolingo-style visible streak with loss aversion

**What it shows:**
- Fire/streak icon on dashboard with day count
- *"3-day streak! Don't break the chain"*
- Streak freeze: miss one day = streak preserved (1 per week)
- Weekly streak goal with reward (e.g., "5-day week = 🎯")
- Streak history chart (not just current — show longest streak too)

**Why this wins:** We already track streaks in the DB — this is pure frontend. Massive engagement boost for minimal code. ATI has nothing like this.

**Tech notes:**
- `db.get_current_streak()` already exists
- Add: `db.get_longest_streak()`, `db.get_streak_freezes_remaining()`
- Client-side: CSS animation on streak counter, local storage for last-seen date

---

### 6. Celebration Moments (upgrades results/review experience)

**ATI's approach:** Static percentages, green check / red X, paragraph explanations
**Our approach:** Animated, narrative, rewarding

**In-quiz feedback:**
- Correct answer: green ✅ slides in with satisfying animation, subtle haptic feel
- Wrong answer: red ❌ with gentle shake, correct answer highlights gold
- Confidence slider appears with smooth slide-up animation
- "My Answer" tag on wrong picks (like ATI does — this part is good)

**Post-quiz results:**
- Score reveal: number counts up from 0 to final score (CSS animation)
- Personal best: confetti burst 🎉
- Narrative summary: *"You improved 12% in Science this week!"* not just "73%"
- Topic breakdown: animated progress bars fill to their values
- Mistakes section: each mistake shows question, what you picked, correct answer, and explanation

**Post-quiz per-question review:**
- ATI doesn't have this — we should
- Scroll through every question (not just mistakes)
- See what you picked vs correct, with explanations
- Confidence score shown next to each answer

**Why this wins:** ATI's results feel like a spreadsheet. Ours feel like progress. The animations and narrative framing make students *feel* the improvement, not just read a number.

**Tech notes:**
- CSS-only animations (no JS animation libraries)
- Confetti: lightweight CSS confetti (50 lines of CSS, zero dependencies)
- Progress bar fill: CSS transition `width` over 0.8s
- Score counter: JS `requestAnimationFrame` counting from 0 to N

---

### 7. Profile/Progress Page (upgrades settings + stats)

**ATI's approach:** Basic results page with percentages + settings
**Our approach:** Visual journey map

**What it shows:**
- Overall readiness ring (animated, color-coded)
- Subject cards with mastery progress bars and topic counts
- *"You've mastered 8 of 15 topics — 7 to go!"*
- Weekly activity heatmap (like GitHub contributions)
- Study time this week vs last week
- Topics unlocked (visual badges for topics at 80%+ mastery)
- Settings accessible from here (not a separate boring page)

**Why this wins:** Progress tells a story. Students see how far they've come and how far to go. ATI shows "69%" and calls it a day. We show a journey.

**Tech notes:**
- Merge `/stats` and `/settings` into single `/progress` page
- Heatmap: CSS grid with color intensity based on questions answered per day
- Badge system: `db.get_mastered_topics()` returns topics with mastery >= 80
- Settings as a slide-out panel or collapsible section, not a dedicated page

---

### 8. Question Count Flexibility (raise cap from 20 to 100)

**ATI's approach:** 5-100 slider
**Our approach:** 5-100 slider, but with smart defaults

- Quick study: 5 questions (default for Daily Plan)
- Standard session: 10 questions
- Deep dive: 25 questions
- Full practice: 50 questions
- Exam simulation: 100 questions
- Slider with preset buttons for common counts

**Tech notes:**
- Change `min(count, 20)` to `min(count, 100)` in `quiz_start()`
- Add preset buttons in quiz config UI

---

### 9. Topic-Level Quiz Creation

**ATI's approach:** 2-step: pick topics via checkboxes → configure count/mode
**Our approach:** Same, but integrated into Daily Plan customization

- When customizing a study session, show expandable subject cards
- Each subject shows its subtopics with mastery percentages
- Checkboxes to select specific topics
- Count slider and confidence toggle at bottom

**Tech notes:**
- `kb.py` already has `get_<subject>_topics()` returning topic lists
- Need `get_<subject>_quiz_questions(topic=...)` filter parameter
- DB already tracks per-topic mastery via `db.update_topic_mastery()`

---

### 10. Question of the Day

**ATI's approach:** "Question of the Day" with START button
**Our approach:** Same concept, but smarter

- Shows on dashboard as a featured card
- Picks from a different subject each day (rotation: Math → Science → Reading → English)
- After answering, shows explanation + confidence slider
- Tracks QOTD streak separately ("You've answered 7 days in a row!")
- If already answered today, shows yesterday's question + how the community answered (future: user community data)

**Tech notes:**
- Deterministic daily question: `hash(date.today() + subject_rotation)` → pick from pool
- DB table: `qotd_log` (date, question_id, selected, correct, confidence)
- Show different state: not yet answered / already answered / missed yesterday

---

## Design Language

### Color Palette
- Editorial/print style (Mu2 brand — NOT AI slop)
- Dark navy, off-white, warm accent colors
- Progress colors: green (#22c55e) for strong, amber (#f59e0b) for fair, red (#ef4444) for weak
- No purple-pink gradients, no glassmorphism, no Inter font

### Typography
- Headings: Libre Baskerville (serif, editorial feel)
- Body: Source Sans 3 (clean, readable)
- Numbers/scores: monospace or tabular figures for alignment

### Animations
- Subtle, purposeful, not flashy
- Progress bars fill on page load (0.8s ease-out)
- Score numbers count up (not instant)
- Correct/wrong feedback: 0.3s slide-in
- Confetti: only on personal bests and milestones
- No page transitions — keep it instant (single-page feel with minimal reloads)

### Layout
- Mobile-first (60%+ of students on phones)
- Card-based with generous whitespace
- Bottom nav: Home, Study, Mistakes, Progress
- Max content width: 640px (centered on desktop)

---

## The Free Tier Must CRUSH ATI

**Design mandate:** The free tier (no AI tutor) must be so good that students genuinely ask *"Why are you paying for ATI when TEAS Study App is way better and FREE?"*

**What ATI gives you for $50-100+:**
- Quiz engine with configurable count
- Study mode (show answer) / Exam mode (hide answer)
- Flag button for bookmarking
- Basic percentage scores
- Generic per-choice rationales
- Flat flagged questions list
- Results page with green check / red X

**What WE give away for FREE (all non-AI features):**
- Smart Daily Plan — opens with a plan, not a menu
- Confidence Slider — teaches metacognition, replaces study/exam toggle AND flag button
- Mistake Bank — prioritized by forgetting curves, not a flat graveyard
- Quickfire 60-second mode — gamification ATI doesn't have
- Visual Streak System — Duolingo-style engagement
- Celebration Animations — progress bars, score counters, narrative results
- Per-Question Review — scroll through every question post-quiz (ATI doesn't have this)
- Topic-Level Mastery — see which specific topics you've mastered
- Progress Heatmap — weekly activity visualization
- 2,003 questions with 250+ char explanations (ATI comparable)
- Mobile-first responsive design (ATI's app is janky on mobile)

**The AI tutor (paid) is the cherry on top, not the only reason to use our app.** By the time a student hits the AI paywall, they're already invested, already seeing progress, already telling classmates about us.

---

## Implementation Priority

### Phase 1 — MVP+ (features that make free tier better than ATI)
- [ ] Smart Daily Plan (default landing)
- [ ] Confidence Slider (replaces study/exam + flag)
- [ ] Raise question cap to 100
- [ ] In-quiz visual feedback (green ✅ / red ❌ + "My Answer" tag)
- [ ] Post-quiz per-question review (all questions, not just mistakes)
- [ ] Celebration animations (progress bars, score counter)

### Phase 2 — Differentiation
- [ ] Mistake Bank with prioritization algorithm
- [ ] Quickfire Mode (60-second rapid fire)
- [ ] Visual Streak System (upgrade existing)
- [ ] Topic-level quiz creation
- [ ] Question of the Day

### Phase 3 — Polish
- [ ] Profile/Progress page (merge stats + settings)
- [ ] Weekly activity heatmap
- [ ] Badge system for mastered topics
- [ ] Confetti on personal bests
- [ ] Narrative progress summaries ("You improved 12% this week!")

---

## Competitive Edge Summary

| Feature | ATI ($50-100+) | Us (FREE) |
|---------|----------------|-----------|
| Default experience | Menu navigation | Smart Daily Plan |
| Post-answer feedback | Flag button + static explanation | Confidence Slider + metacognition |
| Mistake review | Flat list, no prioritization | Mistake Bank with forgetting curves |
| Quick practice | Standard quiz only | Quickfire 60-second mode |
| Streak/motivation | None | Visual streak + celebrations |
| Results page | Percentages only | Animated narrative + per-question review |
| Progress tracking | Basic stats | Journey map with badges + heatmap |
| Mobile UX | Clunky | Mobile-first responsive |
| AI tutoring | None | Socratic Gemma 4 tutor (paid upsell) |
