# OpenCode Prompt — Screen 1: Base Layout + Dashboard

Copy everything below this line and paste into OpenCode.

---

## Context

You are building **TEAS Study Buddy** — a Flask + Jinja2 + Tailwind CSS web app for nursing students preparing for the ATI TEAS 7 exam. This is Screen 1 of 7. You are building the **base layout template** and the **Dashboard (home screen)**.

## Tech Stack
- Flask (Python 3.12+)
- Jinja2 templates
- Tailwind CSS via CDN (no build step, no npm)
- No JavaScript frameworks — vanilla JS only
- Google Fonts CDN for Libre Baskerville (headings) and Source Sans 3 (body)

## File Structure
```
teas-study-app/
├── app.py                 # Flask app with routes
├── templates/
│   ├── base.html          # ← BUILD THIS (layout shell)
│   ├── dashboard.html     # ← BUILD THIS (home screen)
│   └── partials/
│       └── subject_card.html  # ← BUILD THIS (reusable card component)
├── static/
│   ├── css/
│   │   └── custom.css     # ← BUILD THIS (design system overrides)
│   └── js/
│       └── theme.js       # ← BUILD THIS (dark mode toggle)
```

## Design System — FOLLOW EXACTLY

### Colors
**Light mode:**
- Background: `#FAFAF7`
- Surface (cards): `#FFFFFF`
- Primary: `#1B4332` (deep forest green)
- Primary light: `#2D6A4F`
- Accent: `#40916C` (green for correct, progress bars)
- Error: `#D00000`
- Warning: `#E85D04`
- Text primary: `#1A1A2E`
- Text secondary: `#6B7280`
- Border: `#E5E7EB`

**Dark mode:**
- Background: `#1A1A2E`
- Surface: `#16213E`
- Primary: `#52B788`
- Primary light: `#74C69D`
- Accent: `#40916C`
- Error: `#EF4444`
- Warning: `#F59E0B`
- Text primary: `#E5E7EB`
- Text secondary: `#9CA3AF`
- Border: `#2A3A5C`

### Typography
- Headings: `font-family: 'Libre Baskerville', serif` (Google Fonts)
- Body: `font-family: 'Source Sans 3', sans-serif` (Google Fonts)
- Base size: 16px

### Component Rules — NON-NEGOTIABLE
- No glassmorphism (no backdrop-blur, no semi-transparent backgrounds)
- No gradients (flat solid colors only)
- No rounded pill buttons (use 6px border-radius, rectangular buttons)
- No emoji in UI text (use plain text or icon library)
- Cards: 1px border, 8px border-radius, subtle shadow `0 1px 3px rgba(0,0,0,0.08)`
- Buttons: primary = filled with primary color, secondary = outlined with 1px border
- Max content width: 720px centered
- Card padding: 24px
- Section gaps: 32px

### Philosophy
"Study app that feels like a quiet library, not a casino."
No gamification. No confetti. No streaks. No points. Clean, calm, academic. Think editorial/print design, not tech startup landing page.

## What to Build

### 1. base.html
The layout shell that all screens extend. Must include:
- HTML5 doctype with `lang="en"`
- Google Fonts link for Libre Baskerville and Source Sans 3
- Tailwind CSS CDN
- Custom CSS file link (`static/css/custom.css`)
- Dark mode: add class `dark` to `<html>` element. Use `data-theme="dark"` attribute on `<html>`. CSS custom properties switch based on `[data-theme="dark"]`.
- Top nav bar with:
  - Left: app name "TEAS Study Buddy" in Libre Baskerville, primary color
  - Right: dark mode toggle button (sun/moon icon, plain text "Light" / "Dark")
- Main content area: `{% block content %}{% endblock %}`
- Include theme.js at bottom of body
- Mobile responsive (single column below 640px)
- All text in Source Sans 3 except headings in Libre Baskerville

### 2. custom.css
CSS custom properties for the full color system (light + dark via `[data-theme="dark"]` selector). Override any Tailwind defaults that conflict with the design system. Set body background and font family. Style progress bars (green fill, rounded ends, 8px height). Ensure dark mode transitions feel smooth (no flash of wrong theme on load).

### 3. theme.js
Toggle `data-theme` attribute on `<html>` between "light" and "dark". Save preference to localStorage. On page load, check localStorage and apply saved theme immediately (before render, to prevent flash). Wire up the toggle button in the nav.

### 4. dashboard.html
Extends base.html. This is the home screen the student sees every time they open the app.

**Layout (top to bottom):**

1. **Header section:**
   - "Your TEAS Readiness" heading (Libre Baskerville)
   - Large overall readiness percentage (big number, e.g. "68%")
   - Full-width progress bar underneath (green fill, light gray track)

2. **Subject cards grid** (2×2 grid on desktop, single column on mobile):
   - 4 cards: Mathematics, Science, Reading, English & Language
   - Each card shows:
     - Subject name (heading, left-aligned)
     - Readiness percentage (large, right-aligned)
     - Small progress bar
     - Number of weak areas text (e.g. "3 topics need review")
     - Color indicator: green border-left if >80%, orange if 60-80%, red if <60%
   - Cards are clickable (will navigate to subject detail later, use `href="#"` for now)

3. **Study Recommendations section:**
   - Heading: "Recommended for You"
   - 2-3 recommendation items, each as a simple row:
     - Subject icon/label (plain text, no emoji)
     - Topic name
     - "Needs work" label in warning color
   - These link to study mode (href="#" for now)

4. **Action buttons section** (2 buttons side by side):
   - "Quick Quiz" (primary button, filled) — "10 minutes"
   - "Study Mode" (secondary button, outlined) — "25 minutes"

**Mock data:** Use hardcoded mock data for the dashboard. Do NOT connect to any database yet. The values should look realistic:
- Overall: 68%
- Math: 86% (3 weak areas)
- Science: 91% (1 weak area)
- Reading: 45% (8 weak areas) — this is the weakest, highlight it
- English: 72% (5 weak areas)
- Recommendations: "Reading: Key Ideas & Details", "English: Subject-Verb Agreement"

### 5. partials/subject_card.html
A Jinja2 partial that dashboard.html includes via `{% include %}`. Accepts variables: `subject_name`, `readiness_pct`, `weak_count`, `status` (where status is "strong", "fair", or "weak"). The card HTML should use these variables. Dashboard renders 4 of these.

### 6. app.py (minimal)
Just enough Flask to serve the templates:
- Route `/` renders dashboard.html with mock data
- Route `/static/<path:file>` for CSS/JS (Flask default)
- Run on `localhost:5432`, debug=True

## Output Requirements
- Produce complete, working files — not snippets or pseudocode
- Every file should be ready to run with `python app.py` and see the dashboard in a browser
- Use Tailwind utility classes for layout (flex, grid, padding, margin) but CSS custom properties for colors (so dark mode works cleanly)
- The result should look like a calm, professional study tool — not a tech startup, not a game, not a generic Bootstrap template

## Anti-Patterns to Avoid
- Do NOT use default Tailwind blue (#3B82F6) anywhere
- Do NOT use Inter, Roboto, or system-ui as fonts
- Do NOT add illustrations, decorations, or background patterns
- Do NOT use emoji in any UI text
- Do NOT make it look like every other SaaS landing page
- Do NOT add any JavaScript frameworks (React, Vue, Alpine, HTMX) — vanilla JS only
- Do NOT use any icon library for this screen — plain text only
