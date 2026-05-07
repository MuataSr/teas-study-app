# V2 Build Plan — TEAS Study App

**Goal:** Transform V1 (single-user Flask quiz app) into V2 (multi-user, hosted, mobile-first, free-to-crush-ATI study app with AI tutor upsell).

**Current V1 state:**
- 3 files: app.py (561 lines, 17 routes), db.py (277 lines, 14 functions), kb.py (787 lines, 19 functions)
- 7 templates: base, dashboard, quiz, results, stats, resources, settings
- 2 static assets: teas.css, theme.js
- DB: 2,003 questions, 119 misconceptions, 53 study topics
- Features: quiz flow, per-question timer, topic breakdown, streak counter, recent sessions, dark mode toggle, reset progress
- **Missing:** auth, confidence slider, spaced repetition, study mode, AI tutor, quickfire, celebrations, PWA, onboarding

---

## Contradiction Resolutions

| Conflict | BUILD_BLUEPRINT | UX Vision | Resolution |
|----------|----------------|-----------|------------|
| Gamification | "No confetti, no streaks, no points" | Streaks, confetti, Quickfire, celebrations | **UX Vision wins.** Crush ATI, not play it safe. |
| Study vs Practice | Study mode (learn → practice → quiz) | Confidence slider replaces study/exam toggle | **Merge.** Confidence slider IS the study/practice/quiz continuum. Low confidence = teach mode. High = quiz mode. No separate "study mode" screen. |
| Auth | Full signup/login with per-user DB | Not mentioned | **BUILD_BLUEPRINT wins.** Required for multi-user hosting. Keep it minimal. |

---

## Build Phases

### Phase 0: Foundation (Auth + User Schema) ⏱ ~2 days

**Why first:** Everything else depends on per-user data.

**Database changes (db.py):**
- `users` table: id, email, password_hash, display_name, exam_date, target_score, created_at
- `sessions` table: id, user_id, quiz_id, subject, started_at, completed_at (rename current in-memory sessions)
- `answers` table: id, user_id, session_id, question_id, selected_answer, correct, confidence, time_elapsed, answered_at
- `review_queue` table: id, user_id, question_id, next_review, interval, ease_factor (spaced repetition)
- All existing queries wrapped with `WHERE user_id = ?`

**App changes (app.py):**
- `/signup` + `/login` + `/logout` routes (Jinja templates, session cookies via Flask `session`)
- `/onboarding` — first-time wizard: name, exam date, target score
- Middleware: `@login_required` decorator for all routes except signup/login
- Anonymous fallback: localStorage UUID for users who skip signup (data persists on device only)

**Files:** signup.html, login.html, onboarding.html (minimal templates)

**Deliverable:** New user can sign up, set exam date, and see a personalized dashboard greeting.

---

### Phase 1: Confidence Slider + Adaptive Engine ⏱ ~3 days

**Core UX innovation.** Replaces study/exam toggle. Single input on every question.

**UI (quiz.html):**
- 3-point slider below answer choices: "Not sure" / "Maybe" / "Got this"
- Must select answer AND confidence before submitting
- Slider color: red (not sure) → yellow (maybe) → green (got this)
- On submit: "Not sure" → show explanation immediately (teach mode). "Got this" → move on (quiz mode). "Maybe" → show short hint, then explanation after 5s.

**Engine (db.py + app.py):**
- Confidence stored per answer in `answers` table
- Confidence drives spaced repetition intervals:
  - "Got this" correct → interval × 2 (max 30 days)
  - "Got this" wrong → reset to 1 day
  - "Not sure" correct → interval × 1.2
  - "Not sure" wrong → interval = 1 day (prioritize)
  - "Maybe" → interval × 1.5
- Review queue populates from confidence-weighted intervals
- Dashboard "Focus Areas" now powered by confidence data, not just accuracy

**KB integration (kb.py):**
- Low confidence + wrong answer → pull misconception from KB if topic matches
- "Not sure" responses surface related study_topics for review

**Deliverable:** Confidence slider works end-to-end. Wrong + "not sure" questions resurface faster. Misconceptions appear contextually.

---

### Phase 2: Quickfire Mode + Celebrations ⏱ ~2 days

**Quickfire** — the addictive 60-second rapid-fire mode from UX Vision.

**New route:** `/quickfire` or `/quickfire/<subject>`
- 60-second timer, questions stream one at a time
- No explanations between questions (speed is the game)
- Correct = +10 points, Wrong = -5 points (can't go below 0)
- Ends when timer hits 0 or 5 wrong answers
- Shows final score + accuracy + questions/minute

**Celebrations (JS/CSS):**
- Per-quiz celebrations on results page based on score:
  - 90%+ → confetti burst (CSS animation, no library)
  - 100% → special "Perfect!" animation
  - 70-89% → subtle pulse + "Nice work!"
  - Below 70% → encouraging message, no animation
- Quickfire has its own celebrations: high score badge, new record toast
- All animations: CSS keyframes only (zero JS libraries, ~50 lines CSS)

**New files:** quickfire.html, confetti.css (or inline in teas.css)

**Deliverable:** Quickfire playable. Celebrations fire on results page. No external dependencies.

---

### Phase 3: Spaced Repetition + Mistake Bank ⏱ ~2 days

**Spaced repetition engine** (BUILD_BLUEPRINT `review_queue` table, created in Phase 0).

**New route:** `/review` — "Due for Review" card
- Shows count of questions due today (from review_queue)
- Mixed subject review of only due items
- Completing review marks items as reviewed, updates next_review date

**Mistake Bank:**
- New route: `/mistakes` — all wrong answers, sorted by recency
- Filter by subject, topic, confidence level
- "Redo" button for any mistake (re-quiz just those questions)
- Mistakes marked "mastered" after 2 consecutive correct answers at "Got this" confidence
- Mistake count badge on dashboard

**Dashboard integration:**
- "Due for Review" count in stats row
- Mistake Bank link in Focus Areas section
- TEAS-weighted readiness: Reading 28%, Math 26%, Science 32%, English 14%

**Deliverable:** Review queue works. Mistake bank browsable. Readiness score weighted by TEAS proportions.

---

### Phase 4: Study Topics + Misconception Surfacing ⏱ ~2 days

**Study content** — the "teach before testing" differentiator.

**New route:** `/topics` → `/topics/<subject>` → `/topics/<subject>/<topic>`
- Browse all 53 study topics grouped by subject
- Each topic page: brief lesson summary + related misconception cards + "Practice this topic" quiz
- Misconception cards: what students get wrong, why, and the correct explanation (from KB misconceptions table)
- Topic completion tracking: mark topics as "studied" after practicing

**Dashboard integration:**
- Subject rows show topic completion count (e.g., "8/24 topics studied")
- "Focus Areas" pulls from misconception matches on wrong answers

**KB work (kb.py):**
- `get_lesson(subject, topic)` — returns study topic + related misconceptions
- `get_misconceptions(subject, topic)` — filtered misconception cards
- Study topics currently have 53 entries — may need enrichment for topics with only 1-2 items

**Deliverable:** Browseable topic library. Misconception cards visible. Topic practice quizzes work.

---

### Phase 5: AI Tutor (Paid Upsell) ⏱ ~3 days

**The revenue feature.** Dual-model architecture: Gemma 4 E4B (router) + Gemma 4 26B A4B (teacher) via Google AI Studio.

**New route:** `/tutor` — full chat interface
- Chat UI: message bubbles, typing indicator, message history
- Context: sees student's recent answers, mistakes, confidence patterns, and current question
- Can explain concepts, give hints, create practice problems, Socratic dialogue
- Rate limit: free users get 5 messages/day. Paid: unlimited.
- "Ask Ann-E about this question" button on quiz results page

**Architecture (new files):**
- `tutor.py` — Gemini API client, context builder, rate limiter
- `tutor.html` — chat UI template
- API key stored in `.env`, NOT in code
- Free tier: 5 messages/day tracked in `users` table
- Paid tier: Stripe checkout integration (Phase 7, not here)

**Context window for tutor:**
- Last 10 answers (question + answer + confidence)
- Current misconception if wrong answer
- Study topics the student has struggled with
- Exam date proximity (more urgent = more encouraging)

**Deliverable:** AI tutor responds to messages with context-aware help. Free tier limit enforced. Chat history persists.

---

### Phase 6: Dashboard Redesign + Dark Mode Polish ⏱ ~2 days

**Visual overhaul** to match UX Vision's premium feel.

**Dashboard redesign:**
- TEAS readiness gauge (circular progress, TEAS-weighted)
- Subject cards with mini sparkline trend (last 7 sessions)
- Streak counter with fire icon + current streak length
- "Due for Review" prominent card
- Quickfire high score card
- Daily plan: "Do 10 questions in Science" type suggestion based on weakest areas
- Onboarding state: show welcome back / exam countdown if exam date set

**Dark mode:**
- Full dark theme (already has toggle in base.html)
- System preference detection via `prefers-color-scheme`
- Smooth transition between modes

**Stats page redesign:**
- Per-subject accuracy trend (simple CSS bar chart, no library)
- Calendar heatmap (GitHub-style contribution graph for study activity)
- Topic mastery grid
- Time spent per subject

**Deliverable:** Dashboard looks premium. Dark mode complete. Stats page shows trends.

---

### Phase 7: PWA + Deployment ⏱ ~2 days

**PWA:**
- `manifest.json` — app name, icons (SVG inline, no image files needed), theme color, display: standalone
- `service-worker.js` — cache static assets, offline quiz mode (cache questions in IndexedDB)
- Install prompt on mobile
- Push notification: daily study reminder (optional, browser notification API)

**Deployment:**
- Digital Ocean Droplet setup (1 vCPU, 1GB to start — free tier)
- Nginx reverse proxy → Flask (gunicorn)
- SQLite on droplet (sufficient for 0-500 users)
- Environment variables for Gemini API key
- SSL via Let's Encrypt (certbot)
- Domain: teas.mu2.solutions (or similar)

**Error states to handle:**
- Gemini API down → graceful fallback ("AI tutor is taking a break, try again soon")
- DB locked → retry with backoff
- Free tier exhausted → upsell message
- Network offline → cached questions still work (PWA)

**Deliverable:** App installable on phones. Deployed to droplet. HTTPS working. Error states handled.

---

### Phase 8: Payment + Polish ⏱ ~2 days

**Stripe integration:**
- Checkout page: monthly subscription (TBD price)
- Free vs paid feature comparison
- Webhook handler for subscription status
- DB field: `subscription_status` on users table

**Final polish:**
- Onboarding flow complete (welcome → exam date → first quiz)
- Accessibility pass: ARIA labels, keyboard navigation, color contrast check
- Session persistence: auto-save quiz progress to localStorage, resume on reload
- Question difficulty filter on quiz start (easy/medium/hard/all)
- Timed exam simulation: 100 questions, 209 minutes (real TEAS conditions)
- Mobile testing: verify all screens on 375px viewport

**Deliverable:** Paid tier works. App is production-ready. Accessible.

---

## Scope Summary

| Phase | Feature | Est. Days | Dependencies |
|-------|---------|-----------|-------------|
| 0 | Auth + User Schema | 2 | None |
| 1 | Confidence Slider + Adaptive | 3 | Phase 0 |
| 2 | Quickfire + Celebrations | 2 | Phase 0 |
| 3 | Spaced Repetition + Mistake Bank | 2 | Phase 0 + 1 |
| 4 | Study Topics + Misconceptions | 2 | Phase 0 |
| 5 | AI Tutor | 3 | Phase 0 + 1 |
| 6 | Dashboard + Dark Mode | 2 | Phase 0-4 |
| 7 | PWA + Deploy | 2 | All above |
| 8 | Payment + Polish | 2 | Phase 7 |
| **Total** | | **~20 days** | |

**Parallel opportunity:** Phases 2 and 4 can run in parallel after Phase 0. Phase 3 can start alongside Phase 1.

**New files to create:**
- Templates: signup.html, login.html, onboarding.html, quickfire.html, tutor.html, topics.html, topic_detail.html, mistakes.html, review.html, pricing.html
- Python: tutor.py
- Static: confetti.css (or inline), manifest.json, service-worker.js
- Config: .env (Gemini API key)

**New DB tables:**
- users, answers, review_queue (+ rename sessions table to be user-scoped)

**KB enrichment needed:**
- Study topics with < 3 items need more content (some have only 1-2)

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Gemini free tier exhaustion | Track usage, show clear limits, cache tutor responses for common questions |
| SQLite concurrency on multi-user | WAL mode, connection pooling, upgrade to Postgres at 500+ users |
| PWA IndexedDB quota | Limit cached questions to 200, evict old sessions |
| Mobile performance | No JS frameworks, minimal CSS, lazy-load stats charts |
| Scope creep | This plan IS the scope. Anything new goes to V3. |
