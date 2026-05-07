"""
User progress tracking for TEAS Study App.

SQLite-backed storage for users, quiz sessions, answers, and readiness scores.
Uses only stdlib sqlite3 — no ORM, no external dependencies.
Supports multi-user via user_id foreign keys on all data tables.
"""

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "user_progress.db")


def _get_conn():
    """Return a connection with Row factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist. Safe to call multiple times."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email           TEXT UNIQUE,
                password_hash   TEXT,
                display_name    TEXT NOT NULL DEFAULT 'Student',
                exam_date       TEXT,
                target_score    INTEGER DEFAULT 80,
                is_anonymous    INTEGER NOT NULL DEFAULT 0,
                onboarding_done INTEGER NOT NULL DEFAULT 0,
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL DEFAULT 1,
                subject         TEXT NOT NULL,
                num_questions   INTEGER NOT NULL,
                score           INTEGER NOT NULL DEFAULT 0,
                total           INTEGER NOT NULL DEFAULT 0,
                pct             REAL NOT NULL DEFAULT 0.0,
                started_at      TEXT NOT NULL,
                finished_at     TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS answers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL DEFAULT 1,
                session_id      INTEGER NOT NULL,
                question_id     INTEGER NOT NULL,
                question_text   TEXT NOT NULL,
                selected_answer TEXT NOT NULL,
                correct_answer  TEXT NOT NULL,
                is_correct      INTEGER NOT NULL DEFAULT 0,
                confidence      INTEGER DEFAULT NULL,
                time_elapsed    INTEGER NOT NULL DEFAULT 0,
                answered_at     TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (session_id) REFERENCES quiz_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS topic_mastery (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL DEFAULT 1,
                subject         TEXT NOT NULL,
                topic           TEXT NOT NULL,
                total_attempted INTEGER NOT NULL DEFAULT 0,
                total_correct   INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, subject, topic),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS review_queue (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL DEFAULT 1,
                question_id     INTEGER NOT NULL,
                subject         TEXT NOT NULL,
                topic           TEXT NOT NULL,
                next_review     TEXT NOT NULL,
                interval_days   REAL NOT NULL DEFAULT 1.0,
                ease_factor     REAL NOT NULL DEFAULT 2.5,
                times_correct   INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, question_id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS quickfire_high_scores (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL DEFAULT 1,
                subject         TEXT NOT NULL,
                score           INTEGER NOT NULL,
                correct         INTEGER NOT NULL,
                total           INTEGER NOT NULL,
                qpm             REAL NOT NULL DEFAULT 0.0,
                played_at       TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        # Migrate: add user_id column to existing tables if missing
        _migrate_add_column(conn, "quiz_sessions", "user_id", "INTEGER NOT NULL DEFAULT 1")
        _migrate_add_column(conn, "answers", "user_id", "INTEGER NOT NULL DEFAULT 1")
        _migrate_add_column(conn, "answers", "confidence", "INTEGER DEFAULT NULL")
        _migrate_add_column(conn, "topic_mastery", "user_id", "INTEGER NOT NULL DEFAULT 1")
        # Note: topic_mastery.id added via table recreation if old schema exists

        # Ensure anonymous default user exists
        row = conn.execute("SELECT id FROM users WHERE id=1").fetchone()
        if not row:
            now = datetime.utcnow().isoformat()
            conn.execute(
                "INSERT INTO users (id, email, display_name, is_anonymous, created_at) VALUES (1, NULL, 'Student', 1, ?)",
                (now,),
            )

        conn.commit()


def _migrate_add_column(conn, table, column, col_type):
    """Add a column to a table if it doesn't exist."""
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def create_session(user_id, subject, num_questions):
    """Start a new quiz session. Returns the new session_id."""
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO quiz_sessions (user_id, subject, num_questions, started_at) VALUES (?, ?, ?, ?)",
            (user_id, subject, num_questions, now),
        )
        conn.commit()
        return cur.lastrowid


def record_answer(user_id, session_id, question_id, question_text, selected, correct, is_correct, time_elapsed, confidence=None):
    """Record a single answer. Returns the answer id."""
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO answers
               (user_id, session_id, question_id, question_text, selected_answer, correct_answer, is_correct, confidence, time_elapsed, answered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, session_id, question_id, question_text, selected, correct, int(is_correct), confidence, time_elapsed, now),
        )
        conn.commit()
        return cur.lastrowid


def finish_session(session_id, score, total, pct):
    """Mark a quiz session as finished with final score."""
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "UPDATE quiz_sessions SET score=?, total=?, pct=?, finished_at=? WHERE id=?",
            (score, total, pct, now, session_id),
        )
        conn.commit()


def get_readiness(user_id, subject):
    """Overall readiness percentage for a subject (correct / attempted across all time)."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT SUM(total_correct) AS c, SUM(total_attempted) AS a FROM topic_mastery WHERE user_id=? AND subject=?",
            (user_id, subject),
        ).fetchone()
        if row["a"] and row["a"] > 0:
            return round(row["c"] / row["a"] * 100, 1)
        # Fallback: compute from answers if no mastery rows yet
        row2 = conn.execute(
            """SELECT COUNT(*) AS a,
                      SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS c
               FROM answers a2
               JOIN quiz_sessions s ON a2.session_id = s.id
               WHERE a2.user_id=? AND s.subject = ?""",
            (user_id, subject),
        ).fetchone()
        if row2["a"] and row2["a"] > 0:
            return round(row2["c"] / row2["a"] * 100, 1)
        return 0.0


def get_topic_readiness(user_id, subject, topic):
    """Readiness percentage for a specific subject + topic."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT total_correct, total_attempted FROM topic_mastery WHERE user_id=? AND subject=? AND topic=?",
            (user_id, subject, topic),
        ).fetchone()
        if row and row["total_attempted"] > 0:
            return round(row["total_correct"] / row["total_attempted"] * 100, 1)
        return 0.0


def get_recent_sessions(user_id, limit=5):
    """Return the most recent finished sessions as a list of dicts."""
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT id, subject, num_questions, score, total, pct, started_at, finished_at
               FROM quiz_sessions
               WHERE user_id=? AND finished_at IS NOT NULL
               ORDER BY id DESC
               LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_mistakes(user_id, session_id):
    """Return all wrong answers for a session as a list of dicts."""
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT question_id, question_text, selected_answer, correct_answer, time_elapsed, answered_at
               FROM answers
               WHERE user_id=? AND session_id=? AND is_correct=0""",
            (user_id, session_id),
        ).fetchall()
        return [dict(r) for r in rows]


def get_subject_stats(user_id, subject):
    """Comprehensive stats for a subject including per-topic breakdown."""
    with _get_conn() as conn:
        # Overall totals from topic_mastery
        overall = conn.execute(
            "SELECT SUM(total_attempted) AS a, SUM(total_correct) AS c FROM topic_mastery WHERE user_id=? AND subject=?",
            (user_id, subject),
        ).fetchone()

        total_attempted = overall["a"] or 0
        total_correct = overall["c"] or 0
        readiness_pct = round(total_correct / total_attempted * 100, 1) if total_attempted > 0 else 0.0

        # Per-topic breakdown
        topic_rows = conn.execute(
            "SELECT topic, total_attempted, total_correct FROM topic_mastery WHERE user_id=? AND subject=? ORDER BY topic",
            (user_id, subject),
        ).fetchall()
        topics = []
        for tr in topic_rows:
            ta = tr["total_attempted"] or 0
            tc = tr["total_correct"] or 0
            topics.append({
                "topic": tr["topic"],
                "total": ta,
                "correct": tc,
                "pct": round(tc / ta * 100, 1) if ta > 0 else 0.0,
            })

        return {
            "total_attempted": total_attempted,
            "total_correct": total_correct,
            "readiness_pct": readiness_pct,
            "topics": topics,
        }


def get_overall_stats(user_id):
    """High-level stats across all subjects."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT subject, SUM(total_attempted) AS a, SUM(total_correct) AS c FROM topic_mastery WHERE user_id=? GROUP BY subject ORDER BY subject",
            (user_id,),
        ).fetchall()

        subjects = []
        grand_attempted = 0
        grand_correct = 0
        for r in rows:
            a = r["a"] or 0
            c = r["c"] or 0
            grand_attempted += a
            grand_correct += c
            subjects.append({
                "name": r["subject"],
                "slug": r["subject"].lower().replace(" ", "-"),
                "readiness_pct": round(c / a * 100, 1) if a > 0 else 0.0,
            })

        overall_readiness = round(grand_correct / grand_attempted * 100, 1) if grand_attempted > 0 else 0.0

        return {
            "overall_readiness": overall_readiness,
            "subjects": subjects,
        }


def get_weekly_activity(user_id):
    """Return quiz session counts for the last 7 days as [{day, count}, ...]."""
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT DATE(started_at) AS day, COUNT(*) AS count
               FROM quiz_sessions
               WHERE user_id=? AND started_at >= DATE('now', '-7 days')
               GROUP BY DATE(started_at)
               ORDER BY day""",
            (user_id,),
        ).fetchall()
        result = [dict(r) for r in rows]

    # Fill in missing days so the chart always has 7 entries
    today = datetime.utcnow().date()
    filled = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        found = next((r for r in result if r["day"] == d), None)
        filled.append({"day": d, "count": found["count"] if found else 0})
    return filled


def update_topic_mastery(user_id, subject, topic, is_correct):
    """Upsert topic mastery counters."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT total_attempted, total_correct FROM topic_mastery WHERE user_id=? AND subject=? AND topic=?",
            (user_id, subject, topic),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE topic_mastery SET total_attempted=?, total_correct=? WHERE user_id=? AND subject=? AND topic=?",
                (row["total_attempted"] + 1, row["total_correct"] + int(is_correct), user_id, subject, topic),
            )
        else:
            conn.execute(
                "INSERT INTO topic_mastery (user_id, subject, topic, total_attempted, total_correct) VALUES (?, ?, ?, 1, ?)",
                (user_id, subject, topic, int(is_correct)),
            )
        conn.commit()


def reset_all_progress(user_id):
    """Delete all progress data for a specific user."""
    with _get_conn() as conn:
        # Get session IDs for this user
        session_ids = [r[0] for r in conn.execute("SELECT id FROM quiz_sessions WHERE user_id=?", (user_id,)).fetchall()]
        if session_ids:
            placeholders = ",".join("?" * len(session_ids))
            conn.execute(f"DELETE FROM answers WHERE user_id=? AND session_id IN ({placeholders})", [user_id] + session_ids)
        conn.execute("DELETE FROM review_queue WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM topic_mastery WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM quiz_sessions WHERE user_id=?", (user_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------

def _hash_password(password):
    """Hash password with salt. Returns salt:hash string."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password, stored):
    """Verify password against salt:hash stored string."""
    if not stored or ":" not in stored:
        return False
    salt, hashed = stored.split(":", 1)
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed


def create_user(email=None, password=None, display_name="Student"):
    """Create a new user. Returns user dict with id. Raises ValueError if email taken."""
    now = datetime.utcnow().isoformat()
    password_hash = _hash_password(password) if password else None

    with _get_conn() as conn:
        if email:
            existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if existing:
                raise ValueError("Email already registered")

        cur = conn.execute(
            "INSERT INTO users (email, password_hash, display_name, is_anonymous, created_at) VALUES (?, ?, ?, 0, ?)",
            (email, password_hash, display_name, now),
        )
        conn.commit()
        user_id = cur.lastrowid

    return get_user(user_id)


def create_anonymous_user():
    """Create an anonymous user with a UUID display name. Returns user dict."""
    now = datetime.utcnow().isoformat()
    anon_id = secrets.token_hex(8)[:12].upper()

    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (display_name, is_anonymous, created_at) VALUES (?, 1, ?)",
            (f"Student-{anon_id}", now),
        )
        conn.commit()
        return get_user(cur.lastrowid)


def get_user(user_id):
    """Get user by ID. Returns dict or None."""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email):
    """Get user by email. Returns dict or None."""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None


def verify_login(email, password):
    """Verify credentials. Returns user dict if valid, None otherwise."""
    user = get_user_by_email(email)
    if not user or not user.get("password_hash"):
        return None
    if _verify_password(password, user["password_hash"]):
        return user
    return None


def update_user(user_id, **fields):
    """Update user fields (display_name, exam_date, target_score, onboarding_done)."""
    allowed = {"display_name", "exam_date", "target_score", "onboarding_done"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_user(user_id)

    sets = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [user_id]

    with _get_conn() as conn:
        conn.execute(f"UPDATE users SET {sets} WHERE id=?", values)
        conn.commit()

    return get_user(user_id)


def get_total_answered(user_id):
    """Total questions answered by a user."""
    with _get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM answers WHERE user_id=?", (user_id,)).fetchone()
        return row["c"] or 0


# ── Spaced Repetition (SM-2 variant) ──

def update_review_queue(user_id, question_id, subject, topic, is_correct, confidence):
    """Update the review queue based on answer correctness and confidence.

    SM-2 variant with confidence modifier:
    - confidence 1 (not sure) + wrong  → interval 0.5 days (review soon)
    - confidence 1 + right            → interval 1 day
    - confidence 2 (kinda sure) + wrong → interval 1 day
    - confidence 2 + right            → interval = previous * ease
    - confidence 3 (got this) + wrong → interval 1 day
    - confidence 3 + right            → interval = previous * ease * 1.3 (bonus)
    """
    now = datetime.utcnow()
    now_iso = now.isoformat()

    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, interval_days, ease_factor, times_correct FROM review_queue WHERE user_id=? AND question_id=?",
            (user_id, question_id),
        ).fetchone()

        if row:
            # Existing entry — SM-2 update
            qid = row["id"]
            interval = row["interval_days"]
            ease = row["ease_factor"]
            correct_count = row["times_correct"]

            if is_correct:
                correct_count += 1
                if confidence == 3:
                    interval = interval * ease * 1.3
                elif confidence == 2:
                    interval = interval * ease
                else:
                    interval = max(interval, 1.0)
                # Ease boost after 3 consecutive correct
                if correct_count >= 3:
                    ease = min(ease + 0.1, 3.0)
            else:
                # Wrong answer — reset interval based on confidence
                correct_count = 0
                ease = max(ease - 0.3, 1.3)
                interval = 0.5 if confidence == 1 else 1.0

            next_review = (now + timedelta(days=interval)).isoformat()
            conn.execute(
                "UPDATE review_queue SET next_review=?, interval_days=?, ease_factor=?, times_correct=?, subject=?, topic=? WHERE id=?",
                (next_review, interval, ease, correct_count, subject, topic, qid),
            )
        else:
            # New entry
            if is_correct and confidence >= 2:
                interval = 2.0 if confidence == 3 else 1.0
                ease = 2.5
            else:
                interval = 0.5 if confidence == 1 else 1.0
                ease = 2.0

            next_review = (now + timedelta(days=interval)).isoformat()
            conn.execute(
                "INSERT INTO review_queue (user_id, question_id, subject, topic, next_review, interval_days, ease_factor, times_correct) VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                (user_id, question_id, subject, topic, next_review, interval, ease),
            )

        conn.commit()


def get_due_review_items(user_id, subject=None, limit=20):
    """Get questions due for review (next_review <= now), optionally filtered by subject."""
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        if subject:
            rows = conn.execute(
                "SELECT * FROM review_queue WHERE user_id=? AND subject=? AND next_review <= ? ORDER BY next_review ASC LIMIT ?",
                (user_id, subject, now, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM review_queue WHERE user_id=? AND next_review <= ? ORDER BY next_review ASC LIMIT ?",
                (user_id, now, limit),
            ).fetchall()
        return [dict(r) for r in rows]


def get_confidence_distribution(user_id, subject=None):
    """Get confidence breakdown for analytics: {1: count, 2: count, 3: count, null: count}."""
    with _get_conn() as conn:
        if subject:
            rows = conn.execute(
                "SELECT confidence, COUNT(*) AS c FROM answers WHERE user_id=? AND confidence IS NOT NULL GROUP BY confidence",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT confidence, COUNT(*) AS c FROM answers WHERE user_id=? AND confidence IS NOT NULL GROUP BY confidence",
                (user_id,),
            ).fetchall()
        dist = {1: 0, 2: 0, 3: 0}
        for r in rows:
            if r["confidence"] in dist:
                dist[r["confidence"]] = r["c"]
        return dist


def get_accuracy_by_confidence(user_id):
    """Get accuracy rates grouped by confidence level for analytics."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT confidence, SUM(is_correct) AS correct, COUNT(*) AS total FROM answers WHERE user_id=? AND confidence IS NOT NULL GROUP BY confidence",
            (user_id,),
        ).fetchall()
        result = {}
        for r in rows:
            conf = r["confidence"]
            total = r["total"]
            correct = r["correct"]
            result[conf] = {"correct": correct, "total": total, "pct": round(correct / total * 100, 1) if total > 0 else 0}
        return result


# ── Quickfire Mode ──

def save_quickfire_score(user_id, subject, score, correct, total, qpm):
    """Save a quickfire high score. Only saves if it's a new best for this user+subject."""
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        # Check if this beats the existing high score
        existing = conn.execute(
            "SELECT score FROM quickfire_high_scores WHERE user_id=? AND subject=? ORDER BY score DESC LIMIT 1",
            (user_id, subject),
        ).fetchone()
        if existing and score <= existing["score"]:
            return False  # Not a new high score
        conn.execute(
            "INSERT INTO quickfire_high_scores (user_id, subject, score, correct, total, qpm, played_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, subject, score, correct, total, qpm, now),
        )
        conn.commit()
        return True  # New high score


def get_quickfire_high_score(user_id, subject):
    """Get the best quickfire score for a user+subject combo."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT score, correct, total, qpm, played_at FROM quickfire_high_scores WHERE user_id=? AND subject=? ORDER BY score DESC LIMIT 1",
            (user_id, subject),
        ).fetchone()
        return dict(row) if row else None


def get_quickfire_high_scores(user_id):
    """Get all quickfire high scores for a user, one per subject."""
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT subject, MAX(score) AS score FROM quickfire_high_scores
               WHERE user_id=? GROUP BY subject ORDER BY subject""",
            (user_id,),
        ).fetchall()
        return {r["subject"]: r["score"] for r in rows}
