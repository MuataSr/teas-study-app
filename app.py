"""
app.py — TEAS Study Buddy Flask application.

All data comes from kb.py (knowledge base) and db.py (user progress).
No hardcoded mock data — everything is live from SQLite.
Supports multi-user auth with anonymous fallback.
"""

import os
import json
import uuid
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, jsonify, session, flash
from flask_wtf.csrf import CSRFProtect
from kb import (
    get_math_topics, get_math_lesson, get_math_quiz_questions,
    get_science_topics, get_science_lesson, get_science_quiz_questions,
    get_reading_topics, get_reading_lesson, get_reading_quiz_questions,
    get_english_topics, get_english_lesson, get_english_quiz_questions,
)
import db

# ---------------------------------------------------------------------------
# App & Config
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", os.urandom(24).hex())
csrf = CSRFProtect(app)




# ---------------------------------------------------------------------------
# Auth Helpers
# ---------------------------------------------------------------------------

def _get_current_user_id():
    """Return current user_id from session, ensuring a user exists."""
    user_id = session.get("user_id")
    if not user_id:
        # Auto-create anonymous user
        user = db.create_anonymous_user()
        session["user_id"] = user["id"]
        session.permanent = True
        return user["id"]
    return user_id


def _get_current_user():
    """Return current user dict or None."""
    user_id = session.get("user_id")
    if user_id:
        return db.get_user(user_id)
    return None


@app.context_processor
def inject_user():
    user = _get_current_user()
    review_due = 0
    if user and not user.get("is_anonymous", 1):
        review_due = len(db.get_due_review_items(user["id"]))
    return {"current_user": user, "review_due_count": review_due}


def login_required(f):
    """Decorator: routes work for all users (anonymous or registered).
    Ensures user_id exists in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        _get_current_user_id()
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Subject Registry
# ---------------------------------------------------------------------------

_SUBJECT_GETTERS = {
    "math": {
        "topics": get_math_topics,
        "lesson": get_math_lesson,
        "quiz": get_math_quiz_questions,
        "name": "Math",
    },
    "science": {
        "topics": get_science_topics,
        "lesson": get_science_lesson,
        "quiz": get_science_quiz_questions,
        "name": "Science",
    },
    "english": {
        "topics": get_english_topics,
        "lesson": get_english_lesson,
        "quiz": get_english_quiz_questions,
        "name": "English",
    },
    "reading": {
        "topics": get_reading_topics,
        "lesson": get_reading_lesson,
        "quiz": get_reading_quiz_questions,
        "name": "Reading",
    },
}


def _get_subject_info(slug):
    """Return subject config dict or None."""
    return _SUBJECT_GETTERS.get(slug)


def _all_subjects(user_id):
    """Build the SUBJECTS list with live readiness scores."""
    subjects = []
    for slug in ("math", "science", "reading", "english"):
        info = _SUBJECT_GETTERS[slug]
        readiness = db.get_readiness(user_id, slug) or 0
        subjects.append({
            "subject_name": info["name"],
            "slug": slug,
            "readiness_pct": readiness,
        })
    return subjects


def _greeting():
    """Time-based greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def _exam_countdown(exam_date_str):
    """Days until exam. Returns None if no date set."""
    if not exam_date_str:
        return None
    try:
        exam = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        diff = (exam - today).days
        return max(0, diff)
    except (ValueError, TypeError):
        return None


def _build_recommendations(user_id):
    """Suggest weak topics across all subjects."""
    recs = []
    for slug, info in _SUBJECT_GETTERS.items():
        readiness = db.get_readiness(user_id, slug) or 0
        if readiness < 60:
            topics = info["topics"]()
            if topics:
                t = random.choice(topics)
                recs.append({
                    "subject": info["name"],
                    "topic": t["name"],
                    "level": "Building" if readiness < 40 else ("Fair" if readiness < 70 else "Strong"),
                })
    return recs[:5]


def _build_recent_sessions(user_id):
    """Recent quiz sessions for dashboard."""
    sessions = db.get_recent_sessions(user_id, 5)
    result = []
    for s in sessions:
        pct = s.get("pct", 0) or 0
        if pct >= 80:
            status = "Strong"
        elif pct >= 60:
            status = "Fair"
        else:
            status = "Building"
        result.append({
            "topic": s.get("subject", "Unknown"),
            "subject": f"{s.get('num_questions', 0)} questions",
            "score": int(pct),
            "date": s.get("finished_at", "")[:10] if s.get("finished_at") else "—",
            "status": status,
        })
    return result


def _format_time(seconds):
    """Format seconds as M:SS or just seconds."""
    if seconds is None:
        return "0:00"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/mathjax-test")
def mathjax_test():
    return render_template("mathjax_test.html")

@app.route("/")
@login_required
def dashboard():
    user_id = session.get("user_id", 1)
    user = _get_current_user()
    stats = db.get_overall_stats(user_id)
    overall_pct = stats.get("overall_readiness", 0) or 0

    subjects = _all_subjects(user_id)

    # Add weak_count to each subject for dashboard cards
    for subj in subjects:
        subj_stats = db.get_subject_stats(user_id, subj["slug"])
        weak = 0
        for t in subj_stats.get("topics", []):
            if (t.get("pct") or 0) < 60:
                weak += 1
        subj["weak_count"] = weak

    # Add review due count
    for subj in subjects:
        due_items = db.get_due_review_items(user_id, subject=subj["slug"])
        subj["review_due"] = len(due_items)

    recommendations = _build_recommendations(user_id)
    recent_sessions = _build_recent_sessions(user_id)

    display_name = user["display_name"] if user else "Student"
    exam_days = _exam_countdown(user.get("exam_date") if user else None)
    exam_date_str = user.get("exam_date", "") if user else ""

    # Quickfire high scores for dashboard card
    quickfire_scores = db.get_quickfire_high_scores(user_id) if not user.get("is_anonymous", 1) else {}

    return render_template("dashboard.html",
        greeting=_greeting(),
        display_name=display_name,
        overall_pct=int(overall_pct),
        subjects=subjects,
        recommendations=recommendations,
        recent_sessions=recent_sessions,
        exam_days=exam_days,
        exam_date=exam_date_str,
        is_anonymous=user.get("is_anonymous", 1) if user else 1,
        quickfire_scores=quickfire_scores,
        active_nav="home",
    )


@app.route("/review")
@login_required
def review():
    user_id = session.get("user_id", 1)
    subject_slugs = ["math", "science", "reading", "english"]
    review_data = []
    total_due = 0
    for slug in subject_slugs:
        due_items = db.get_due_review_items(user_id, subject=slug)
        subject_name = _SUBJECT_GETTERS.get(slug, {}).get("name", slug.title())
        due_count = len(due_items)
        total_due += due_count
        review_data.append({
            "slug": slug,
            "name": subject_name,
            "due_count": due_count,
        })
    return render_template("review.html",
        review_data=review_data,
        total_due=total_due,
        active_nav="review",
    )


@app.route("/review/start", methods=["POST"])
@login_required
def review_start():
    user_id = session.get("user_id", 1)
    subject = request.form.get("subject", "")

    if subject:
        due_items = db.get_due_review_items(user_id, subject=subject)
    else:
        due_items = db.get_due_review_items(user_id)

    if not due_items:
        return redirect("/review")

    questions = []
    seen_topics = set()

    for item in due_items:
        subj = item["subject"]
        topic = item["topic"]
        key = (subj, topic)
        if key in seen_topics:
            continue
        seen_topics.add(key)

        info = _SUBJECT_GETTERS.get(subj)
        if not info:
            continue

        qs = info["quiz"](topic=topic, count=1)
        if qs:
            questions.extend(qs)

    if not questions:
        return redirect("/review")

    random.shuffle(questions)
    questions = questions[:20]

    quiz_id = uuid.uuid4().hex[:12]
    db.save_quiz(
        quiz_id=quiz_id,
        user_id=user_id,
        subject=subject or "review",
        questions=questions,
        answers=[],
        current_index=0,
        session_id=None,
        started_at=datetime.now().isoformat(),
        is_review=True,
    )

    return redirect(f"/quiz/review/{quiz_id}/0")


@app.route("/api/stats")
@login_required
def api_stats():
    """Lightweight JSON endpoint for dashboard counters."""
    user_id = session.get("user_id", 1)
    overall = db.get_overall_stats(user_id)
    answered = db.get_total_answered(user_id)

    # Streak
    weekly = db.get_weekly_activity(user_id)
    streak = 0
    today = datetime.utcnow().date()
    check = today
    activity_days = {w["day"] for w in weekly}
    while True:
        if check.isoformat() in activity_days:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    return jsonify(answered=answered, streak=streak)


@app.route("/quiz/<subject_slug>")
@login_required
def quiz_start(subject_slug):
    """Start a new quiz. Creates session and redirects to first question."""
    user_id = session.get("user_id", 1)
    if subject_slug == "mixed":
        return quiz_start_mixed()

    info = _get_subject_info(subject_slug)
    if not info:
        return redirect("/")

    count = request.args.get("count", db.get_quiz_count(user_id, default=5), type=int)
    count = min(count, 20)

    questions = info["quiz"](count=count)
    if not questions:
        return redirect("/")

    quiz_id = uuid.uuid4().hex[:12]
    db.save_quiz(
        quiz_id=quiz_id,
        user_id=user_id,
        subject=subject_slug,
        questions=questions,
        answers=[],
        current_index=0,
        session_id=None,
        started_at=datetime.now().isoformat(),
        is_review=False,
    )

    return redirect(f"/quiz/{subject_slug}/{quiz_id}/0")


def quiz_start_mixed():
    """Start a mixed-subject quiz."""
    user_id = session.get("user_id", 1)
    count = request.args.get("count", db.get_quiz_count(user_id, default=5), type=int)
    count = min(count, 20)

    all_questions = []
    per_subject = max(1, count // 4)
    for slug, info in _SUBJECT_GETTERS.items():
        qs = info["quiz"](count=per_subject)
        for q in qs:
            q["_subject"] = info["name"]
            q["_subject_slug"] = slug
        all_questions.extend(qs)

    random.shuffle(all_questions)
    all_questions = all_questions[:count]

    if not all_questions:
        return redirect("/")

    quiz_id = uuid.uuid4().hex[:12]
    db.save_quiz(
        quiz_id=quiz_id,
        user_id=user_id,
        subject="mixed",
        questions=all_questions,
        answers=[],
        current_index=0,
        session_id=None,
        started_at=datetime.now().isoformat(),
        is_review=False,
    )

    return redirect(f"/quiz/mixed/{quiz_id}/0")


@app.route("/quiz/<subject_slug>/<quiz_id>/<int:q_index>")
@login_required
def quiz_question(subject_slug, quiz_id, q_index):
    """Show a specific question in the quiz."""
    quiz = db.load_quiz(quiz_id)
    if not quiz:
        return redirect("/")

    questions = quiz["questions"]
    if q_index < 0 or q_index >= len(questions):
        return redirect("/")

    question = questions[q_index]

    subject_name = _SUBJECT_GETTERS.get(subject_slug, {}).get("name", "Mixed Review")
    if subject_slug == "mixed":
        subject_name = "Mixed Review"
    elif subject_slug == "review":
        subject_name = "Spaced Review"

    return render_template("quiz.html",
        question=question,
        current_q=q_index + 1,
        total_q=len(questions),
        subject_name=subject_name,
        subject_slug=subject_slug,
        quiz_id=quiz_id,
    )


@app.route("/quiz/<subject_slug>/<quiz_id>/<int:q_index>/answer", methods=["POST"])
@login_required
def quiz_answer(subject_slug, quiz_id, q_index):
    """Process an answer and redirect to next question or results."""
    quiz = db.load_quiz(quiz_id)
    if not quiz:
        return redirect("/")

    user_id = quiz.get("user_id", session.get("user_id", 1))
    questions = quiz["questions"]
    if q_index < 0 or q_index >= len(questions):
        return redirect("/")

    question = questions[q_index]
    selected = request.form.get("selected", "")
    time_elapsed = request.form.get("time_elapsed", 0, type=float)
    confidence = request.form.get("confidence", None, type=int)

    correct_answer = question.get("correct_answer", "")
    correct_index = question.get("correct_index")

    if isinstance(correct_index, int) and "options" in question and 0 <= correct_index < len(question["options"]):
        correct_answer = question["options"][correct_index]

    is_correct = False
    if isinstance(correct_index, int) and "options" in question and selected:
        try:
            selected_idx = question["options"].index(selected)
            is_correct = (selected_idx == correct_index)
        except (ValueError, TypeError):
            pass

    if not is_correct:
        is_correct = (selected == correct_answer) or (str(selected).strip().lower() == str(correct_answer).strip().lower())

    answer = {
        "question_id": question.get("id", q_index),
        "question_text": question.get("question_text", ""),
        "selected": selected,
        "correct": correct_answer,
        "is_correct": is_correct,
        "time_elapsed": time_elapsed,
        "confidence": confidence,
        "topic": question.get("topic", ""),
    }
    quiz["answers"].append(answer)

    if quiz["session_id"] is None:
        quiz["session_id"] = db.create_session(
            user_id=user_id,
            subject=quiz["subject"],
            num_questions=len(questions),
        )

    db.record_answer(
        user_id=user_id,
        session_id=quiz["session_id"],
        question_id=question.get("id", q_index),
        question_text=question.get("question_text", ""),
        selected=selected,
        correct=correct_answer,
        is_correct=is_correct,
        time_elapsed=int(time_elapsed),
        confidence=confidence,
    )

    # Update topic mastery
    topic = question.get("topic", "")
    if topic:
        db.update_topic_mastery(user_id, quiz["subject"], topic, is_correct)

    # Update spaced repetition review queue
    if confidence is not None:
        db.update_review_queue(
            user_id=user_id,
            question_id=question.get("id", q_index),
            subject=quiz["subject"],
            topic=topic,
            is_correct=is_correct,
            confidence=confidence,
        )

    db.save_quiz(
        quiz_id=quiz_id,
        user_id=quiz["user_id"],
        subject=quiz["subject"],
        questions=quiz["questions"],
        answers=quiz["answers"],
        current_index=q_index + 1,
        session_id=quiz["session_id"],
        started_at=quiz["started_at"],
        is_review=quiz.get("is_review", False),
    )

    next_index = q_index + 1

    # Build feedback based on confidence level
    explanation = question.get("explanation", "")
    feedback_mode = "quiz"  # default: minimal feedback
    if confidence == 1:
        feedback_mode = "teach"  # show full explanation
    elif confidence == 2:
        feedback_mode = "hint"  # hint first, reveal after 5s

    # Get related lesson/concept for wrong answers
    related_lesson = None
    if not is_correct and topic:
        lesson_fn = _SUBJECT_GETTERS.get(subject_slug, {}).get("lesson")
        if lesson_fn:
            try:
                related_lesson = lesson_fn(topic)
            except Exception:
                pass

    if next_index < len(questions):
        return render_template("quiz.html",
            question=question,
            current_q=q_index + 1,
            total_q=len(questions),
            subject_name=_SUBJECT_GETTERS.get(subject_slug, {}).get("name", subject_slug),
            subject_slug=subject_slug,
            quiz_id=quiz_id,
            # Feedback context
            feedback=True,
            is_correct=is_correct,
            selected=selected,
            correct_answer=correct_answer,
            explanation=explanation,
            feedback_mode=feedback_mode,
            related_lesson=related_lesson,
            next_url=f"/quiz/{subject_slug}/{quiz_id}/{next_index}",
        )
    else:
        correct_count = sum(1 for a in quiz["answers"] if a["is_correct"])
        total = len(quiz["answers"])
        pct = int((correct_count / total * 100) if total else 0)
        elapsed = sum(a.get("time_elapsed", 0) for a in quiz["answers"])

        db.finish_session(quiz["session_id"], correct_count, total, pct)

        # Review quizzes redirect back to /review instead of results page
        review_next_url = "/review" if quiz.get("is_review") else f"/results/{subject_slug}/{quiz_id}"

        return render_template("quiz.html",
            question=question,
            current_q=q_index + 1,
            total_q=len(questions),
            subject_name=_SUBJECT_GETTERS.get(subject_slug, {}).get("name", subject_slug),
            subject_slug=subject_slug,
            quiz_id=quiz_id,
            # Feedback context (last question)
            feedback=True,
            is_correct=is_correct,
            selected=selected,
            correct_answer=correct_answer,
            explanation=explanation,
            feedback_mode=feedback_mode,
            related_lesson=related_lesson,
            next_url=review_next_url,
        )


@app.route("/results/<subject_slug>/<quiz_id>")
@login_required
def quiz_results(subject_slug, quiz_id):
    """Show quiz results."""
    quiz = db.load_quiz(quiz_id)
    if not quiz:
        return redirect("/")

    answers = quiz["answers"]
    questions = quiz["questions"]

    correct_count = sum(1 for a in answers if a["is_correct"])
    total = len(answers)
    pct = int((correct_count / total * 100) if total else 0)
    elapsed = sum(a.get("time_elapsed", 0) for a in answers)

    best_streak = 0
    current_streak = 0
    for a in answers:
        if a["is_correct"]:
            current_streak += 1
            best_streak = max(best_streak, current_streak)
        else:
            current_streak = 0

    topic_map = {}
    for a in answers:
        topic = a.get("topic", "General")
        if topic not in topic_map:
            topic_map[topic] = {"correct": 0, "total": 0}
        topic_map[topic]["total"] += 1
        if a["is_correct"]:
            topic_map[topic]["correct"] += 1

    topic_breakdown = [
        {"topic": t, "correct": v["correct"], "total": v["total"],
         "pct": int((v["correct"] / v["total"] * 100) if v["total"] else 0)}
        for t, v in topic_map.items()
    ]

    mistakes = [
        {
            "question": a["question_text"],
            "user_answer": a["selected"],
            "correct_answer": a["correct"],
            "explanation": next(
                (q.get("explanation", "") for q in questions if q.get("question_text") == a["question_text"]),
                "",
            ),
        }
        for a in answers if not a["is_correct"]
    ]

    subject_name = _SUBJECT_GETTERS.get(subject_slug, {}).get("name", "Mixed Review")
    if subject_slug == "mixed":
        subject_name = "Mixed Review"

    db.delete_quiz(quiz_id)

    return render_template("results.html",
        score=correct_count,
        total=total,
        pct=pct,
        elapsed_time=_format_time(elapsed),
        accuracy=pct,
        best_streak=best_streak,
        topic_breakdown=topic_breakdown,
        mistakes=mistakes,
        subject_slug=subject_slug,
        subject_name=subject_name,
    )


@app.route("/stats")
@login_required
def stats():
    user_id = session.get("user_id", 1)
    overall_stats = db.get_overall_stats(user_id)
    overall_readiness = int(overall_stats.get("overall_readiness", 0) or 0)

    subjects = []
    for slug in ("math", "science", "reading", "english"):
        info = _SUBJECT_GETTERS[slug]
        subj_stats = db.get_subject_stats(user_id, slug)
        topics = info["topics"]()

        db_topics = {t["topic"]: t for t in subj_stats.get("topics", [])}
        strong = 0
        for t in topics:
            db_t = db_topics.get(t["name"]) or db_topics.get(t.get("slug", ""))
            if db_t and (db_t.get("pct") or 0) >= 80:
                strong += 1

        subjects.append({
            "name": info["name"],
            "slug": slug,
            "readiness_pct": int(subj_stats.get("readiness_pct", 0) or 0),
            "strong_topics": strong,
            "total_topics": len(topics),
        })

    recent = db.get_recent_sessions(user_id, 10)
    recent_quizzes = []
    for s in recent:
        recent_quizzes.append({
            "date": s.get("finished_at", "")[:10] if s.get("finished_at") else "—",
            "subject_name": s.get("subject", "Unknown").title(),
            "subject_slug": s.get("subject", ""),
            "score": int(s.get("pct", 0) or 0),
            "total_questions": s.get("num_questions", 0),
        })

    weekly = db.get_weekly_activity(user_id)

    current_streak = 0
    today = datetime.utcnow().date()
    check_date = today
    activity_days = set()
    for w in weekly:
        activity_days.add(w.get("day", ""))

    while True:
        day_str = check_date.strftime("%Y-%m-%d")
        if day_str in activity_days:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Compute insights
    insights = []
    subject_readiness = {s["slug"]: s["readiness_pct"] for s in subjects}

    # Weakest subject
    if subject_readiness:
        weakest_slug = min(subject_readiness, key=subject_readiness.get)
        weakest_name = _SUBJECT_GETTERS.get(weakest_slug, {}).get("name", weakest_slug.title())
        weakest_pct = subject_readiness[weakest_slug]
        if weakest_pct < 100:
            insights.append({
                "type": "warning",
                "icon": "🎯",
                "text": f"Weakest area: {weakest_name} ({weakest_pct}% readiness)",
                "action_text": "Practice " + weakest_name,
                "action_url": f"/quiz/{weakest_slug}",
            })

    # Strongest subject
    strongest_slug = max(subject_readiness, key=subject_readiness.get)
    strongest_name = _SUBJECT_GETTERS.get(strongest_slug, {}).get("name", strongest_slug.title())
    strongest_pct = subject_readiness[strongest_slug]
    if strongest_pct > 0:
        insights.append({
            "type": "success",
            "icon": "🏆",
            "text": f"Strongest area: {strongest_name} ({strongest_pct}% readiness)",
        })

    # Study streak insight
    if current_streak > 0:
        insights.append({
            "type": "info",
            "icon": "🔥",
            "text": f"{current_streak} day study streak — keep it going!",
        })

    return render_template("stats.html",
        overall_readiness=overall_readiness,
        subjects=subjects,
        recent_quizzes=recent_quizzes,
        weekly_activity=weekly,
        current_streak=current_streak,
        has_data=overall_readiness > 0 or bool(recent_quizzes),
        active_nav="stats",
    )


@app.route("/resources")
@login_required
def resources():
    """Curated free TEAS study resources."""
    resources = [
        {
            "name": "Nurse Cheung",
            "url": "https://nursecheung.com/ati-teas-version-7-comprehensive-study-guide/",
            "description": "Free study guides covering every TEAS subtopic — Reading, Math, Science, and English — written by a critical care nurse educator.",
            "badge": "study guides",
            "category": "Study Guides",
            "tags": ["math", "science", "reading", "english"],
        },
        {
            "name": "Union Test Prep",
            "url": "https://uniontestprep.com/teas/test",
            "description": "100% free study guides and practice tests with no paywall or email gate. Covers all four TEAS subjects.",
            "badge": "practice tests",
            "category": "Practice Tests",
            "tags": ["math", "science", "reading", "english"],
        },
        {
            "name": "Nurse.org TEAS Guide",
            "url": "https://nurse.org/education/teas-test-study-guide",
            "description": "Free 170-question practice test plus an 8-week study schedule to keep you on track.",
            "badge": "study plan",
            "category": "Tips & Strategies",
            "tags": ["math", "science", "reading", "english"],
        },
        {
            "name": "Mometrix Academy",
            "url": "https://www.mometrix.com/academy/teas-practice-test",
            "description": "Free 170-question practice test with detailed answer explanations from a trusted test-prep company.",
            "badge": "practice tests",
            "category": "Practice Tests",
            "tags": ["math", "science", "reading", "english"],
        },
        {
            "name": "Khan Academy",
            "url": "https://www.khanacademy.org",
            "description": "Free foundational lessons in math, science, and grammar. Not TEAS-specific, but perfect for reviewing weak areas from scratch.",
            "badge": "foundations",
            "category": "Video Courses",
            "tags": ["math", "science", "english"],
        },
    ]
    return render_template("resources.html", resources=resources, active_nav="home")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = _get_current_user()
    user_id = session.get("user_id", 1)

    if request.method == "POST":
        count = request.form.get("question_count", 5, type=int)
        count = max(1, min(count, 20))
        db.set_quiz_count(user_id, count)
        return redirect("/settings")

    quiz_count = db.get_quiz_count(user_id, default=5)
    return render_template("settings.html",
        settings={
            "dark_mode": False,
            "font_size": "medium",
            "question_count": quiz_count,
            "timer_direction": "countdown",
        },
        user=_get_current_user(),
        version="0.1.0 MVP",
        active_nav="settings",
    )


@app.route("/settings/reset", methods=["POST"])
@login_required
def settings_reset():
    """Reset all user progress."""
    user_id = session.get("user_id", 1)
    db.reset_all_progress(user_id)
    return redirect("/settings")


@app.route("/settings/profile", methods=["POST"])
@login_required
def settings_profile():
    user_id = session.get("user_id", 1)
    display_name = request.form.get("display_name", "")
    exam_date = request.form.get("exam_date", "")
    if display_name:
        db.update_user(user_id, display_name=display_name)
    if exam_date:
        db.update_user(user_id, exam_date=exam_date)
    return redirect("/settings")


@app.route("/api/export")
@login_required
def api_export():
    user_id = session.get("user_id", 1)
    user = db.get_user(user_id)
    sessions = db.get_user_sessions(user_id)
    data = {
        "user": {k: v for k, v in user.items() if k != "password_hash"} if user else {},
        "sessions": sessions or [],
    }
    return jsonify(data), 200, {"Content-Disposition": "attachment; filename=teas-study-data.json"}


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Register a new account."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", "").strip() or "Student"

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("signup.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("signup.html")

        try:
            user = db.create_user(email=email, password=password, display_name=display_name)
            session["user_id"] = user["id"]
            session.permanent = True
            flash("Account created! Welcome to TEAS Study Buddy.", "success")
            return redirect("/onboarding")
        except ValueError as e:
            flash(str(e), "error")
            return render_template("signup.html")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in to an existing account."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("login.html")

        user = db.verify_login(email, password)
        if not user:
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session.permanent = True
        flash(f"Welcome back, {user['display_name']}!", "success")
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log out and start fresh anonymous session."""
    session.clear()
    flash("Logged out. See you next time!", "success")
    return redirect("/")


@app.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    """First-time setup wizard: name, exam date, feature tour."""
    user_id = session.get("user_id", 1)
    user = _get_current_user()

    if user and user.get("onboarding_done"):
        return redirect("/")

    today = datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        step = request.form.get("step", "")

        if step == "1":
            display_name = request.form.get("display_name", "").strip() or "Student"
            db.update_user(user_id, display_name=display_name)
            return redirect("/onboarding?step=2")

        elif step == "2":
            exam_date = request.form.get("exam_date", "").strip() or None
            db.update_user(user_id, exam_date=exam_date)
            return redirect("/onboarding?step=3")

        else:
            # Legacy / final submit
            display_name = request.form.get("display_name", "").strip() or "Student"
            exam_date = request.form.get("exam_date", "").strip() or None
            target_score = request.form.get("target_score", 80, type=int)
            target_score = max(0, min(100, target_score))
            db.update_user(user_id,
                display_name=display_name,
                exam_date=exam_date,
                target_score=target_score,
                onboarding_done=1,
            )
            flash("Profile saved! Let's start studying.", "success")
            return redirect("/")

    return render_template("onboarding.html", user=user, today=today)


# ---------------------------------------------------------------------------
# Quickfire Mode (Phase 2)
# ---------------------------------------------------------------------------

def _quickfire_pick_questions(subject, count=50):
    """Pick random questions for quickfire mode, shuffled."""
    info = _get_subject_info(subject)
    if not info:
        return []
    questions = info["quiz"]()
    random.shuffle(questions)
    return questions[:count]


@app.route("/api/quickfire/highscores")
@login_required
def quickfire_highscores():
    return jsonify(db.get_quickfire_high_scores(session["user_id"]))


@app.route("/quickfire")
@login_required
def quickfire():
    return render_template("quickfire.html", active_nav="quickfire", subjects=_SUBJECT_GETTERS)


@app.route("/api/quickfire/start", methods=["POST"])
@login_required
def quickfire_start():
    subject = request.json.get("subject")
    if subject not in _SUBJECT_GETTERS:
        return jsonify(error="Invalid subject"), 400
    questions = _quickfire_pick_questions(subject)
    if not questions:
        return jsonify(error="No questions available"), 404
    session_id = os.urandom(8).hex()
    _quickfire_sessions[session_id] = {
        "user_id": session["user_id"],
        "subject": subject,
        "questions": questions,
        "index": 0,
        "score": 0,
        "correct": 0,
        "wrong": 0,
        "answered": [],
    }
    q = questions[0]
    return jsonify(session_id=session_id, question=_format_q(q), remaining=len(questions) - 1)


@app.route("/api/quickfire/answer", methods=["POST"])
@login_required
def quickfire_answer():
    data = request.json
    session_id = data.get("session_id")
    answer = data.get("answer")
    time_left = data.get("time_left", 0)

    qs = _quickfire_sessions.get(session_id)
    if not qs:
        return jsonify(error="Session expired"), 404

    idx = qs["index"]
    questions = qs["questions"]
    q = questions[idx]
    # kb.py uses correct_index (0-based) not correct_answer letter
    correct_index = q.get("correct_index", 0)
    answer_idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(answer.strip().upper(), -1)
    is_correct = answer_idx == correct_index

    qs["answered"].append({"question_id": q.get("id"), "correct": is_correct})
    qs["index"] += 1

    if is_correct:
        qs["correct"] += 1
        qs["score"] += 10
    else:
        qs["wrong"] += 1
        qs["score"] = max(0, qs["score"] - 5)

    ended = False
    end_reason = None
    if qs["wrong"] >= 5:
        ended = True
        end_reason = "5 wrong"
    elif time_left <= 0:
        ended = True
        end_reason = "time"
    elif qs["index"] >= len(questions):
        ended = True
        end_reason = "complete"

    if ended:
        total = qs["correct"] + qs["wrong"]
        accuracy = round(qs["correct"] / total * 100) if total else 0
        time_spent = max(1, 60 - time_left)
        qpm = round(total / (time_spent / 60), 1)
        is_new_high = db.save_quickfire_score(
            qs["user_id"], qs["subject"], qs["score"], qs["correct"], total, qpm
        )
        high = db.get_quickfire_high_score(qs["user_id"], qs["subject"])
        del _quickfire_sessions[session_id]
        return jsonify(
            ended=True,
            reason=end_reason,
            score=qs["score"],
            correct=qs["correct"],
            wrong=qs["wrong"],
            total=total,
            accuracy=accuracy,
            qpm=qpm,
            is_new_high=is_new_high,
            high_score=high["score"] if high else 0,
        )

    next_q = questions[qs["index"]]
    return jsonify(
        ended=False,
        correct=is_correct,
        score=qs["score"],
        wrong=qs["wrong"],
        question=_format_q(next_q),
        remaining=len(questions) - qs["index"],
    )


def _format_q(q):
    """Format a question dict for JSON response.

    kb.py quiz functions return: question_text, options (list of 4), correct_index (0),
    explanation, topic, difficulty. No option_a/b/c/d or correct_answer fields.
    """
    options = q.get("options", [])
    labels = ["A", "B", "C", "D"]
    return {
        "id": q.get("id"),
        "text": q.get("question_text", ""),
        "options": options[:4],
        "labels": labels,
        "correct_index": q.get("correct_index", 0),
    }


# In-memory quickfire sessions (no persistence needed — games are short)
_quickfire_sessions: dict = {}


# ---------------------------------------------------------------------------
# Creative Toolkit — Visual Library & API
# ---------------------------------------------------------------------------

from mu2_creative_toolkit import generate_visual


# Pre-built visual library per subject
_VISUAL_LIBRARY = {
    "math": [
        {"type": "formula", "params": {"key": "quadratic_formula"}},
        {"type": "formula", "params": {"key": "pythagorean_theorem"}},
        {"type": "formula", "params": {"key": "slope"}},
        {"type": "formula", "params": {"key": "circle_area"}},
        {"type": "formula", "params": {"key": "distance_formula"}},
        {"type": "formula", "params": {"key": "combinations"}},
        {"type": "formula", "params": {"key": "percent_change"}},
        {"type": "table", "params": {"headers": ["Prefix", "Symbol", "Factor"], "rows": [
            ["Tera", "T", "10¹²"], ["Giga", "G", "10⁹"], ["Mega", "M", "10⁶"],
            ["Kilo", "k", "10³"], ["Hecto", "h", "10²"], ["Deka", "da", "10¹"],
            ["Base", "—", "1"], ["Deci", "d", "10⁻¹"], ["Centi", "c", "10⁻²"],
            ["Milli", "m", "10⁻³"], ["Micro", "μ", "10⁻⁶"], ["Nano", "n", "10⁻⁹"],
        ], "title": "Metric Prefixes", "style": "striped"}},
        {"type": "table", "params": {"headers": ["From", "To", "Multiply By"], "rows": [
            ["Inches", "Centimeters", "2.54"], ["Pounds", "Kilograms", "0.454"],
            ["Gallons", "Liters", "3.785"], ["Miles", "Kilometers", "1.609"],
            ["Fahrenheit", "Celsius", "(°F − 32) × 5/9"], ["Ounces", "Grams", "28.35"],
        ], "title": "Common Conversions", "style": "bordered"}},
        {"type": "diagram", "name": None, "params": {
            "title": "Order of Operations",
            "diagram_type": "flowchart",
            "direction": "TB",
            "nodes": [
                {"id": "P", "label": "Parentheses", "shape": "rounded"},
                {"id": "E", "label": "Exponents", "shape": "rounded"},
                {"id": "M", "label": "Multiply / Divide", "shape": "rect"},
                {"id": "A", "label": "Add / Subtract", "shape": "rect"},
            ],
            "edges": [
                {"source": "P", "target": "E"},
                {"source": "E", "target": "M"},
                {"source": "M", "target": "A"},
            ]
        }},
    ],
    "science": [
        {"type": "formula", "params": {"key": "density"}},
        {"type": "formula", "params": {"key": "speed"}},
        {"type": "formula", "params": {"key": "newtons_second"}},
        {"type": "formula", "params": {"key": "kinetic_energy"}},
        {"type": "formula", "params": {"key": "ideal_gas_law"}},
        {"type": "formula", "params": {"key": "ohms_law"}},
        {"type": "table", "params": {"headers": ["Quantity", "Unit", "Symbol"], "rows": [
            ["Length", "meter", "m"], ["Mass", "kilogram", "kg"], ["Time", "second", "s"],
            ["Temperature", "Kelvin", "K"], ["Amount", "mole", "mol"],
            ["Electric Current", "Ampere", "A"], ["Luminosity", "Candela", "cd"],
        ], "title": "SI Base Units", "style": "striped"}},
        {"type": "table", "params": {"headers": ["Element", "Symbol", "Atomic #"], "rows": [
            ["Hydrogen", "H", "1"], ["Carbon", "C", "6"], ["Nitrogen", "N", "7"],
            ["Oxygen", "O", "8"], ["Sodium", "Na", "11"], ["Iron", "Fe", "26"],
            ["Calcium", "Ca", "20"], ["Potassium", "K", "19"],
        ], "title": "Common Element Symbols", "style": "bordered"}},
        {"type": "diagram", "name": None, "params": {
            "title": "Scientific Method",
            "diagram_type": "flowchart",
            "direction": "LR",
            "nodes": [
                {"id": "O", "label": "Observe", "shape": "rounded"},
                {"id": "Q", "label": "Question", "shape": "rounded"},
                {"id": "H", "label": "Hypothesis", "shape": "diamond"},
                {"id": "E", "label": "Experiment", "shape": "rect"},
                {"id": "A", "label": "Analyze Data", "shape": "rect"},
                {"id": "C", "label": "Conclusion", "shape": "rounded"},
            ],
            "edges": [
                {"source": "O", "target": "Q"},
                {"source": "Q", "target": "H"},
                {"source": "H", "target": "E", "label": "tests"},
                {"source": "E", "target": "A"},
                {"source": "A", "target": "C"},
            ]
        }},
    ],
    "reading": [
        {"type": "table", "params": {"headers": ["Structure", "Signal Words", "Purpose"], "rows": [
            ["Cause & Effect", "because, therefore, as a result", "Why things happen"],
            ["Compare & Contrast", "similarly, however, on the other hand", "How things are alike/different"],
            ["Chronological", "first, then, finally, after", "Order of events"],
            ["Problem & Solution", "issue, resolved, therefore", "Presenting a problem and fix"],
            ["Description", "for example, such as, characteristics", "Details about a topic"],
        ], "title": "Text Structures", "style": "striped"}},
        {"type": "table", "params": {"headers": ["Device", "Definition", "Example"], "rows": [
            ["Metaphor", "Direct comparison without like/as", "Time is money"],
            ["Simile", "Comparison using like/as", "Brave as a lion"],
            ["Personification", "Giving human traits to non-human", "The wind whispered"],
            ["Alliteration", "Repeating initial consonant sounds", "Peter Piper picked"],
            ["Hyperbole", "Extreme exaggeration", "I've told you a million times"],
        ], "title": "Rhetorical Devices", "style": "bordered"}},
        {"type": "diagram", "name": None, "params": {
            "title": "Reading Comprehension Strategy",
            "diagram_type": "flowchart",
            "direction": "TB",
            "nodes": [
                {"id": "P", "label": "Preview", "shape": "rounded"},
                {"id": "Q", "label": "Question", "shape": "diamond"},
                {"id": "R", "label": "Read Actively", "shape": "rect"},
                {"id": "S", "label": "Summarize", "shape": "rounded"},
                {"id": "V", "label": "Verify", "shape": "rect"},
            ],
            "edges": [
                {"source": "P", "target": "Q"},
                {"source": "Q", "target": "R"},
                {"source": "R", "target": "S"},
                {"source": "S", "target": "V"},
            ]
        }},
    ],
    "english": [
        {"type": "table", "params": {"headers": ["Part of Speech", "Function", "Example"], "rows": [
            ["Noun", "Person, place, thing, idea", "dog, freedom, Maria"],
            ["Verb", "Action or state of being", "run, is, think"],
            ["Adjective", "Modifies a noun", "red, tall, ancient"],
            ["Adverb", "Modifies verb/adj/other adverb", "quickly, very, well"],
            ["Pronoun", "Replaces a noun", "he, they, it"],
            ["Preposition", "Shows relationship", "in, on, at, between"],
            ["Conjunction", "Joins words/clauses", "and, but, or, because"],
            ["Interjection", "Expresses emotion", "wow, oh, hey"],
        ], "title": "Parts of Speech", "style": "striped"}},
        {"type": "table", "params": {"headers": ["Mark", "Use", "Example"], "rows": [
            ["Period (.)", "End of statement", "Hello world."],
            ["Comma (,)", "Pause, list, clause", "red, blue, and green"],
            ["Semicolon (;)", "Join related independent clauses", "It was late; we left."],
            ["Colon (:)", "Introduce list/explanation", "Three things: a, b, c."],
            ["Apostrophe (')", "Possession, contraction", "John's, don't"],
            ["Quotation (\")", "Direct speech, titles", 'She said, "hi."'],
        ], "title": "Punctuation Rules", "style": "bordered"}},
        {"type": "table", "params": {"headers": ["Word", "Meaning", "Word", "Meaning"], "rows": [
            ["affect", "to influence", "effect", "a result"],
            ["their", "possessive", "there", "a place", ],
            ["your", "possessive", "you're", "you are"],
            ["its", "possessive", "it's", "it is"],
            ["who", "subject", "whom", "object"],
            ["less", "uncountable", "fewer", "countable"],
        ], "title": "Commonly Confused Words", "style": "striped"}},
        {"type": "table", "params": {"headers": ["Type", "Structure", "Example"], "rows": [
            ["Simple", "One independent clause", "The cat slept."],
            ["Compound", "Two independent clauses (FANBOYS)", "The cat slept, and the dog barked."],
            ["Complex", "Independent + dependent clause", "After it rained, the cat slept."],
            ["Compound-Complex", "Two independent + one dependent", "After it rained, the cat slept, and the dog barked."],
        ], "title": "Sentence Types", "style": "bordered"}},
        {"type": "diagram", "name": None, "params": {
            "title": "Sentence Structure Types",
            "diagram_type": "flowchart",
            "direction": "LR",
            "nodes": [
                {"id": "S", "label": "Simple", "shape": "rounded"},
                {"id": "C", "label": "Compound", "shape": "rounded"},
                {"id": "X", "label": "Complex", "shape": "rounded"},
                {"id": "CX", "label": "Compound-Complex", "shape": "rounded"},
            ],
            "edges": [
                {"source": "S", "target": "C", "label": "+ FANBOYS"},
                {"source": "S", "target": "X", "label": "+ sub clause"},
                {"source": "C", "target": "CX", "label": "+ sub clause"},
            ]
        }},
    ],
}


@app.route("/scratchpad")
@login_required
def scratchpad():
    """Scratchpad — hand-drawn math sketching canvas."""
    return render_template("scratchpad.html", active_nav="visuals")


@app.route("/canvas-demo")
@login_required
def canvas_demo():
    """Tutor Canvas — demo page for AI-driven illustrations."""
    return render_template("canvas_demo.html")


@app.route("/visuals")
@app.route("/visuals/<subject>")
@login_required
def visuals(subject=None):
    """Visual Library — browse pre-built formulas, diagrams, and tables."""
    subjects = ["math", "science", "reading", "english"]
    if subject and subject not in subjects:
        return redirect(url_for("visuals"))

    cards = []
    subjects_to_show = [subject] if subject else subjects
    for sub in subjects_to_show:
        for item in _VISUAL_LIBRARY.get(sub, []):
            try:
                html = generate_visual(item["type"], item["params"])
                cards.append({
                    "subject": sub,
                    "type": item["type"],
                    "html": html,
                })
            except Exception as e:
                cards.append({
                    "subject": sub,
                    "type": item["type"],
                    "html": f'<p style="color:red;">Error: {e}</p>',
                })

    return render_template("visuals.html",
        active_nav="visuals",
        cards=cards,
        subjects=subjects,
        current_subject=subject,
    )


@app.route("/api/visual", methods=["POST"])
@login_required
def api_visual():
    """Generate a visual on the fly — used by future tutor/chat features."""
    data = request.get_json(silent=True) or {}
    visual_type = data.get("type", "")
    params = data.get("params", {})

    if not visual_type:
        return jsonify({"error": "Missing 'type' field"}), 400

    try:
        html = generate_visual(visual_type, params)
        return jsonify({"html": html, "type": visual_type})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    db.init_db()
    db.cleanup_stale_quizzes()
    app.run(host="0.0.0.0", port=5001, debug=False)
