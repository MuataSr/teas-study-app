"""Create the TEAS A&P Knowledge Base schema."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ap.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")

conn.executescript("""
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
""")

conn.commit()
count = conn.execute("SELECT COUNT(*) FROM misconceptions").fetchone()[0]
print(f"Schema created. DB: {DB_PATH}")
print(f"Misconceptions: {count}, Tables: misconceptions, high_yield_qa")
conn.close()
