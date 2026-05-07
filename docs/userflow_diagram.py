"""Generate TEAS Study Buddy User Flow PDF."""
import fitz  # PyMuPDF

doc = fitz.open(width=612, height=792)  # US Letter

# ── Colors ──
NAVY = (0.106, 0.227, 0.361)
TEAL = (0.0, 0.435, 0.627)
DARK = (0.15, 0.15, 0.15)
GRAY = (0.45, 0.45, 0.45)
LIGHT_BG = (0.95, 0.97, 1.0)
WHITE = (1, 1, 1)
GREEN = (0.18, 0.55, 0.34)
RED = (0.75, 0.22, 0.17)
AMBER = (0.85, 0.55, 0.1)
BLUE_ACCENT = (0.2, 0.5, 0.75)
PURPLE_ACCENT = (0.4, 0.25, 0.65)
ORANGE_ACCENT = (0.8, 0.45, 0.15)

M = 40  # left margin
W = 612 - 80  # usable width
R = M + W  # right edge


def draw_box(page, x, y, w, h, fill=None, border=None, radius=4):
    shape = page.new_shape()
    r = fitz.Rect(x, y, x + w, y + h)
    if fill:
        shape.draw_rect(r)
        shape.finish(color=fill, fill=fill)
    if border:
        shape.draw_rect(r)
        shape.finish(color=border, width=0.8)
    shape.commit()


def draw_text(page, x, y, text, size=9, color=DARK, font="helv", bold=False):
    fname = "helv"  # PyMuPDF 1.27 — helvB not available as fontname
    page.insert_text((x, y), text, fontname=fname, fontsize=size, color=color)


def draw_arrow_down(page, x, y1, y2, color=GRAY):
    """Draw vertical arrow from y1 to y2 at x."""
    page.insert_text((x, y2), "▼", fontname="helv", fontsize=8, color=color)


def draw_arrow_right(page, x1, y, x2, color=GRAY):
    page.insert_text((x2 - 6, y + 3), "→", fontname="helv", fontsize=8, color=color)


def section_header(page, y, title, color=TEAL):
    draw_text(page, M, y, title, size=13, color=color, bold=True)
    # underline
    shape = page.new_shape()
    shape.draw_line(fitz.Point(M, y - 3), fitz.Point(R, y - 3))
    shape.finish(color=color, width=1.2)
    shape.commit()
    return y - 16


# ═══════════════════════════════════════════
# PAGE 1 — Entry + Dashboard + Quiz Flow
# ═══════════════════════════════════════════
page = doc.new_page()
y = 50

# Title
draw_text(page, M, y, "TEAS Study Buddy — User Flow", size=20, color=NAVY, bold=True)
draw_text(page, M, y + 18, "Complete Application Flow Diagram", size=10, color=GRAY)
y += 40

# ── SECTION 1: Entry Points ──
y = section_header(page, y, "1  ENTRY POINTS")
box_y = y
draw_box(page, M, box_y, W, 28, fill=LIGHT_BG, border=TEAL)
draw_text(page, M + 10, box_y + 18, "Landing Page  /", size=11, color=NAVY, bold=True)

# Four branches from landing
branch_y = box_y + 28
branches = [
    ("New User", "Onboarding → set name,\nexam date, target score", PURPLE_ACCENT),
    ("Returning", "Dashboard\n(pick up where you left off)", GREEN),
    ("Login", "Email + password\n→ Dashboard", BLUE_ACCENT),
    ("Signup", "Create account →\nOnboarding → Dashboard", ORANGE_ACCENT),
]
bw = (W - 30) / 4
for i, (label, desc, color) in enumerate(branches):
    bx = M + i * (bw + 10)
    draw_box(page, bx, branch_y, bw, 52, fill=WHITE, border=color)
    draw_text(page, bx + 6, branch_y + 14, label, size=9, color=color, bold=True)
    for j, line in enumerate(desc.split("\n")):
        draw_text(page, bx + 6, branch_y + 26 + j * 10, line, size=7.5, color=GRAY)
    # arrow down from landing to each
    cx = bx + bw / 2
    page.insert_text((cx, branch_y + 4), "▼", fontname="helv", fontsize=7, color=color)

y = branch_y + 64

# ── SECTION 2: Dashboard ──
y = section_header(page, y, "2  DASHBOARD  /")
draw_box(page, M, y, W, 105, fill=LIGHT_BG, border=TEAL)

# Subject cards
cards = [
    ("Math", "76%", GREEN),
    ("Science", "62%", AMBER),
    ("Reading", "85%", GREEN),
    ("English", "44%", RED),
]
cw = (W - 50) / 4
for i, (subj, pct, clr) in enumerate(cards):
    cx = M + 10 + i * (cw + 10)
    draw_box(page, cx, y + 8, cw, 40, fill=WHITE, border=clr)
    draw_text(page, cx + 8, y + 24, subj, size=9, color=DARK, bold=True)
    draw_text(page, cx + 8, y + 38, pct, size=12, color=clr, bold=True)

# Dashboard features
features = [
    "• Smart recommendations based on weak topics",
    "• Recent quiz sessions with scores",
    "• Exam countdown (if date set)",
    "• Quickfire high scores",
    "• Study streak tracking",
]
fy = y + 58
for feat in features:
    draw_text(page, M + 14, fy, feat, size=8, color=DARK)
    fy += 11

# Arrow down from dashboard
arrow_x = M + W / 2
draw_arrow_down(page, arrow_x, y + 105, y + 112, TEAL)
y += 118

# ── SECTION 3: Quiz Flow ──
y = section_header(page, y, "3  QUIZ FLOW  /quiz/{subject}")

# Step 3a: Start
draw_box(page, M, y, W, 22, fill=WHITE, border=TEAL)
draw_text(page, M + 10, y + 15, "Step A:  Pick question count (5–20)  →  questions shuffled from KB", size=9, color=DARK)
y += 30

# Step 3b: Question display
draw_arrow_down(page, arrow_x, y - 8, y - 2, TEAL)
draw_box(page, M, y, W, 78, fill=WHITE, border=BLUE_ACCENT)
draw_text(page, M + 10, y + 14, "Step B:  Show Question", size=10, color=BLUE_ACCENT, bold=True)

# Mini question mockup
qx = M + 20
draw_text(page, qx, y + 30, "What is 15% of 200?", size=8.5, color=DARK, bold=True)
opts = ["A) 25", "B) 30", "C) 35", "D) 40"]
for j, opt in enumerate(opts):
    draw_text(page, qx + 10, y + 42 + j * 9, f"○  {opt}", size=8, color=GRAY)

# Confidence slider
draw_text(page, qx, y + 78, "Confidence:", size=7.5, color=DARK, bold=True)
slider_labels = ["Not sure (1)", "Kinda sure (2)", "Got this (3)"]
slider_colors = [RED, AMBER, GREEN]
sx = qx + 75
for j, (sl, sc) in enumerate(zip(slider_labels, slider_colors)):
    draw_text(page, sx + j * 90, y + 78, sl, size=7, color=sc)

y += 86
draw_arrow_down(page, arrow_x, y - 8, y - 2, TEAL)

# Step 3c: Feedback
draw_box(page, M, y, W, 92, fill=WHITE, border=PURPLE_ACCENT)
draw_text(page, M + 10, y + 14, "Step C:  Feedback (3 modes based on confidence)", size=10, color=PURPLE_ACCENT, bold=True)

# Result banner
draw_text(page, M + 20, y + 30, "✓ Correct   or   ✗ Wrong  — correct answer always shown", size=8.5, color=DARK)

# Three feedback modes
modes = [
    ("Confidence 1: Not sure", "Full explanation always\n+ related lesson concept\n+ 'watch out' common mistake", RED),
    ("Confidence 2: Kinda sure", "Wrong → full explanation\nRight → 'Nice!' + reveal button", AMBER),
    ("Confidence 3: Got this", "Correct → nothing (fast)\nWrong → 'Show explanation'", GREEN),
]
mw = (W - 40) / 3
for i, (title, desc, clr) in enumerate(modes):
    mx = M + 14 + i * (mw + 6)
    draw_box(page, mx, y + 38, mw, 48, fill=LIGHT_BG, border=clr)
    draw_text(page, mx + 6, y + 50, title, size=7.5, color=clr, bold=True)
    for j, line in enumerate(desc.split("\n")):
        draw_text(page, mx + 6, y + 61 + j * 9, line, size=7, color=GRAY)

# Next button
draw_text(page, M + 20, y + 86, "[ Next Question → ]", size=8, color=TEAL, bold=True)

y += 100
draw_arrow_down(page, arrow_x, y - 8, y - 2, TEAL)

# Loop arrow note
draw_text(page, R - 160, y - 4, "More questions? Loop back to Step B", size=7, color=GRAY)

# Step 3d: Results
draw_box(page, M, y, W, 95, fill=WHITE, border=GREEN)
draw_text(page, M + 10, y + 14, "Step D:  Results  /results/{subject}/{quiz_id}", size=10, color=GREEN, bold=True)

# Score summary
rx = M + 20
draw_text(page, rx, y + 32, "Score: 82%", size=14, color=GREEN, bold=True)
draw_text(page, rx, y + 46, "Correct: 4   Wrong: 1   Time: 2:15   Streak: 3", size=8, color=DARK)

# Topic breakdown
draw_text(page, rx, y + 62, "Topic Breakdown:", size=8, color=DARK, bold=True)
draw_text(page, rx + 10, y + 73, "Fractions  2/2     Percentages  1/2     Algebra  1/1", size=7.5, color=GRAY)

# Mistakes
draw_text(page, rx, y + 84, "Review Mistakes: question + your answer + correct + explanation", size=7.5, color=GRAY)

# Action buttons
draw_text(page, rx, y + 92, "[ Try Again ]    [ ⚡ Quickfire Mode ]    [ Back to Study ]", size=8, color=TEAL)


# ═══════════════════════════════════════════
# PAGE 2 — Quickfire + Pages + Data Flow
# ═══════════════════════════════════════════
page = doc.new_page()
y = 50

draw_text(page, M, y, "TEAS Study Buddy — User Flow (continued)", size=20, color=NAVY, bold=True)
y += 35

# ── SECTION 4: Quickfire ──
y = section_header(page, y, "4  QUICKFIRE MODE  /quickfire")
draw_box(page, M, y, W, 68, fill=LIGHT_BG, border=ORANGE_ACCENT)
draw_text(page, M + 10, y + 14, "Gamified speed mode — pick a subject, answer 50 questions in 60 seconds", size=9, color=DARK, bold=True)

qf_rules = [
    ("+10 points", "per correct answer", GREEN),
    ("-5 points", "per wrong answer (floor: 0)", RED),
    ("End triggers:", "5 wrong answers  OR  time runs out  OR  all 50 answered", AMBER),
    ("Tracking:", "High scores per subject, questions per minute stat", BLUE_ACCENT),
]
ry = y + 30
for label, desc, clr in qf_rules:
    draw_text(page, M + 20, ry, label, size=8.5, color=clr, bold=True)
    draw_text(page, M + 110, ry, desc, size=8, color=DARK)
    ry += 12

y += 76

# ── SECTION 5: Other Pages ──
y = section_header(page, y, "5  OTHER PAGES")

pages_data = [
    ("/stats", "Performance & Analytics",
     ["Per-subject readiness percentage", "Topic-level mastery breakdown",
      "Current study streak", "Weekly activity chart", "Recent quiz history (10 sessions)"]),
    ("/resources", "Curated Free Study Links",
     ["Nurse Cheung — study guides", "Union Test Prep — practice tests",
      "Khan Academy — foundational lessons", "Mometrix Academy — 170Q practice test"]),
    ("/settings", "Profile & Preferences",
     ["Display name & email", "Exam date & target score",
      "Reset all progress", "App version info"]),
    ("/scratchpad", "Freehand Canvas",
     ["Draw / sketch / work through problems", "Touch + mouse support"]),
]

py = y
for route, title, bullets in pages_data:
    bh = 18 + len(bullets) * 10
    draw_box(page, M, py, W, bh, fill=WHITE, border=TEAL)
    draw_text(page, M + 10, py + 14, f"{route}", size=9, color=TEAL, bold=True)
    draw_text(page, M + 100, py + 14, title, size=9, color=DARK, bold=True)
    for j, b in enumerate(bullets):
        draw_text(page, M + 20, py + 26 + j * 10, f"•  {b}", size=7.5, color=GRAY)
    py += bh + 6

y = py + 8

# ── SECTION 6: Data Flow ──
y = section_header(page, y, "6  DATA FLOW  (behind the scenes)")

# Question fetch
draw_box(page, M, y, W, 20, fill=LIGHT_BG, border=TEAL)
draw_text(page, M + 10, y + 14, "Question Shown  →  kb.py  →  teas_unified.db  (2,003 MCQs across 4 subjects)", size=8.5, color=DARK)
y += 28

# Answer submit
draw_box(page, M, y, W, 44, fill=LIGHT_BG, border=PURPLE_ACCENT)
draw_text(page, M + 10, y + 14, "Answer Submitted  →  db.py  →  user_progress.db", size=8.5, color=DARK, bold=True)
db_ops = [
    ("record_answer()", "saves question, selection, time, confidence"),
    ("update_topic_mastery()", "adjusts per-topic accuracy tracking"),
    ("update_review_queue()", "spaced repetition scheduling"),
]
for j, (fn, desc) in enumerate(db_ops):
    draw_text(page, M + 20, y + 26 + j * 10, f"•  {fn}", size=7.5, color=PURPLE_ACCENT, bold=True)
    draw_text(page, M + 150, y + 26 + j * 10, desc, size=7.5, color=GRAY)
y += 52

# Feedback render
draw_box(page, M, y, W, 28, fill=LIGHT_BG, border=GREEN)
draw_text(page, M + 10, y + 14, "Feedback Rendered:", size=8.5, color=DARK, bold=True)
draw_text(page, M + 120, y + 14, "Static explanation (250+ chars)  +  Related lesson (concept + common mistake)", size=8, color=GRAY)
y += 20
draw_text(page, M + 120, y, "[FUTURE]  AI Tutor  →  Gemma E4B router  →  Gemma 26B teacher", size=8, color=BLUE_ACCENT)
y += 28

# ── SECTION 7: Key Design Principles ──
y = section_header(page, y, "7  KEY DESIGN DECISIONS")

principles = [
    ("Confidence slider = tutor gate", "3 distinct feedback modes, zero extra UI complexity"),
    ("Wrong answers always teach", "Explanation surfaces automatically (auto or via reveal button)"),
    ("Right answers respect the slider", "'Got this' = zero lecture, 'Not sure' = full treatment"),
    ("Results feed the loop", "Topic breakdown + mistakes → dashboard recommendations → next quiz"),
    ("Quickfire is separate", "Gamified speed mode, independent scoring from regular quizzes"),
    ("AI tutor slots in cleanly", "Same explanation box, richer content when available — no UI rework needed"),
]

for i, (principle, desc) in enumerate(principles):
    draw_box(page, M, y, W, 18, fill=WHITE, border=TEAL)
    draw_text(page, M + 10, y + 13, f"{i+1}.  {principle}", size=8.5, color=NAVY, bold=True)
    draw_text(page, M + 220, y + 13, desc, size=8, color=GRAY)
    y += 22

# Footer
y += 10
draw_text(page, M, y, "TEAS Study Buddy  •  Mu2 Solutions  •  Open Source  •  teas-study-app", size=7, color=GRAY)
draw_text(page, R - 80, y, "v0.1.0 MVP", size=7, color=GRAY)

# Save
out = "/home/muatasr/.nanobot/workspace/teas-study-app/docs/TEAS_Study_Buddy_User_Flow.pdf"
doc.save(out)
doc.close()
print(f"Saved: {out}")
