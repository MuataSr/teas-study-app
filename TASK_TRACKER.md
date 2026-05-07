# Phase 0 Task Tracker — Auth + User Schema

## Tasks

### DB Schema (db.py)
- [x] 1. Add `users` table (id, email, password_hash, display_name, exam_date, target_score, created_at)
- [x] 2. Add `user_id` column to `quiz_sessions` and `answers`
- [x] 3. Add `review_queue` table (id, user_id, question_id, next_review, interval, ease_factor)
- [x] 4. Add `confidence` column to `answers` table
- [x] 5. Wrap existing queries with user_id filtering (get_recent_sessions, get_mistakes, get_readiness, etc.)
- [x] 6. Add user CRUD functions (create_user, get_user_by_email, get_user, update_user)
- [x] 7. Add anonymous UUID user auto-creation

### Auth System (app.py)
- [x] 8. Add `@login_required` decorator
- [x] 9. Add `/signup` route + template
- [x] 10. Add `/login` route + template
- [x] 11. Add `/logout` route
- [x] 12. Add `/onboarding` route + template (name, exam_date, target_score)
- [x] 13. Wire `@login_required` to all existing routes
- [x] 14. Anonymous fallback: auto-create UUID user in session

### Templates
- [x] 15. Create `signup.html`
- [x] 16. Create `login.html`
- [x] 17. Create `onboarding.html`
- [x] 18. Update `base.html` with auth-aware nav (login/signup or logout)
- [x] 19. Update `dashboard.html` with personalized greeting (display_name + exam countdown)

### Testing
- [x] 20. Register + login flow verified
- [x] 21. Onboarding wizard flow verified
- [x] 22. Anonymous UUID fallback verified

---

# Phase 1 Task Tracker — Confidence + Spaced Repetition

## Tasks

### DB Layer (db.py)
- [x] 1. Add SM-2 spaced repetition functions (update_review_queue, get_due_reviews)
- [x] 2. Add topic mastery tracking (update_topic_mastery, get_weak_topics)

### Confidence Slider UI
- [x] 3. 3-tap confidence selector (Not sure / Kinda sure / Got this)
- [x] 4. Dynamic hint text per confidence level
- [x] 5. Confidence data sent with form submission
- [x] 6. Confidence stored in answers table

### Confidence-Driven Feedback
- [x] 7. Post-submit feedback replaces redirect-to-next (render, not redirect)
- [x] 8. Confidence 1 (Not sure): full explanation + related lesson always shown
- [x] 9. Confidence 2 (Kinda sure): hint mode, explanation on wrong; reveal link on correct
- [x] 10. Confidence 3 (Got this): minimal — correct/wrong only, optional "Show explanation" reveal
- [x] 11. Choices locked (no pointer, correct/wrong highlights) after submit
- [x] 12. Related lesson pulled from KB for wrong answers (key concept + common mistake)
- [x] 13. "Next Question →" button for mid-quiz, "See Results →" for last question

### CSS Styling
- [x] 14. Feedback banner (correct/wrong variants + dark mode)
- [x] 15. Explanation box styling
- [x] 16. Related lesson + common mistake card
- [x] 17. Reveal link (dashed underline toggle)
- [x] 18. Choice correct/wrong state highlights

### Testing
- [x] 20. Verify signup → login → dashboard flow works
- [x] 21. Verify anonymous mode works (no signup, quiz still works)
- [x] 22. Verify reset progress only clears current user's data
