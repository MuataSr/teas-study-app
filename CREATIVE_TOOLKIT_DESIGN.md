# Mu2 AI Tutor Creative Toolkit — Design Doc

> Shared module: any Mu2 tutor harness imports it, gets visual generation capabilities.

## Vision

The tutor doesn't just *tell* — it *shows*. When a student is stuck, the tutor decides what visual would help and generates it mid-conversation. Diagrams, charts, formulas, formatted reference sheets — all on the fly, all downloadable.

**Core principle:** Model stays the same, tools compound. The LLM doesn't need a visual framework — it needs tool calls that say "generate this" and a harness that renders the output.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Tutor Harness                  │
│  (any Mu2 tutor: TEAS, OpenStax, etc.)     │
│                                             │
│  LLM decides: "this student needs a visual" │
│        │                                    │
│        ▼                                    │
│  Tool Call: generate_visual(                │
│    type: "flowchart" | "chart" | "formula"  │
│          | "table" | "study_sheet",        │
│    data: { ... }                            │
│  )                                          │
│        │                                    │
│        ▼                                    │
│  ┌─────────────────────────────┐            │
│  │   creative_toolkit.py       │            │
│  │   (shared Mu2 module)       │            │
│  │                             │            │
│  │  • render_diagram()         │            │
│  │  • render_chart()           │            │
│  │  • render_formula()         │            │
│  │  • render_table()           │            │
│  │  • render_study_sheet()     │            │
│  │  • export_pptx()            │            │
│  └──────────┬──────────────────┘            │
│             │                               │
│             ▼                               │
│  Output: HTML/SVG string or file path       │
│  Frontend renders inline in chat            │
└─────────────────────────────────────────────┘
```

### Module Structure

```
mu2-creative-toolkit/
├── __init__.py              # Public API
├── toolkit.py               # Main dispatcher: generate_visual(type, data)
├── diagrams.py              # Mermaid → SVG/HTML
├── charts.py                # matplotlib → PNG/SVG
├── formulas.py              # LaTeX string generator + KaTeX renderer
├── tables.py                # Structured data → formatted HTML tables
├── study_sheets.py          # Multi-section reference sheets
├── export.py                # python-pptx export
└── templates/               # Reusable Mermaid/chart templates
    ├── flowchart.mmd
    ├── concept_map.mmd
    ├── process.mmd
    └── chart_styles.json
```

---

## Visual Types

### 1. Diagrams (Mermaid)
**When to use:** Processes, relationships, concept maps, step sequences.

The model generates a Mermaid definition string. The toolkit renders it to SVG via the `mermaid` CLI or a headless render.

```python
generate_visual(
    type="flowchart",
    data={
        "title": "Cellular Respiration",
        "definition": """
            graph TD
                A[Glucose] --> B[Glycolysis]
                B --> C[Pyruvate]
                C --> D[Citric Acid Cycle]
                D --> E[Electron Transport Chain]
                E --> F[ATP: 36-38]
        """,
        "style": "rounded"  # optional
    }
)
```

**Supported diagram types:**
- Flowchart (processes, decision trees)
- Concept map (relationships between ideas)
- Sequence diagram (ordered steps)
- Pie/XY chart (simple data viz via Mermaid)

### 2. Charts (matplotlib)
**When to use:** Data visualization, comparisons, trends, distributions.

```python
generate_visual(
    type="chart",
    data={
        "chart_type": "bar",  # bar, line, pie, scatter
        "title": "TEAS Math Topic Frequency",
        "x_label": "Topic",
        "y_label": "Questions",
        "series": [
            {"label": "Algebra", "values": [45]},
            {"label": "Geometry", "values": [32]},
            {"label": "Data", "values": [28]}
        ]
    }
)
```

Output: PNG or SVG. Styled with a clean, non-AI-looking palette (Mu2 brand colors).

### 3. Formulas (KaTeX)
**When to use:** Math equations, chemical formulas, physics notation.

The model generates a LaTeX string. The toolkit wraps it for KaTeX rendering in the frontend.

```python
generate_visual(
    type="formula",
    data={
        "latex": r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
        "label": "Quadratic Formula",
        "explanation": "Used to find roots of ax² + bx + c = 0"
    }
)
```

**Frontend rendering:** KaTeX JS library (loaded via CDN or bundled). Python side only generates the LaTeX string and metadata.

**Inline vs block:** Support both inline formulas (within chat text) and block formulas (standalone display).

### 4. Tables
**When to use:** Comparisons, summaries, reference data.

```python
generate_visual(
    type="table",
    data={
        "title": "Muscle Tissue Types",
        "headers": ["Type", "Location", "Control", "Function"],
        "rows": [
            ["Skeletal", "Attached to bones", "Voluntary", "Movement"],
            ["Smooth", "Walls of organs", "Involuntary", "Movement of substances"],
            ["Cardiac", "Heart", "Involuntary", "Pumping blood"]
        ]
    }
)
```

Output: Styled HTML table. Clean borders, alternating row shading.

### 5. Study Sheets
**When to use:** End-of-topic summaries, exam prep references, "cheat sheets."

Combines multiple visual types into a single downloadable reference document.

```python
generate_visual(
    type="study_sheet",
    data={
        "title": "TEAS Science: Cell Biology Quick Reference",
        "sections": [
            {
                "heading": "Key Formulas",
                "type": "formula",
                "items": [...]
            },
            {
                "heading": "Process Overview",
                "type": "flowchart",
                "definition": "..."
            },
            {
                "heading": "Comparison",
                "type": "table",
                "headers": [...],
                "rows": [...]
            },
            {
                "heading": "Key Terms",
                "type": "list",
                "items": ["Mitosis: ...", "Meiosis: ..."]
            }
        ]
    }
)
```

---

## Frontend Integration (TEAS Web App)

### Chat Inline Rendering
Visuals render below the tutor's text response in the chat stream. Each visual is a self-contained HTML block:

```html
<div class="visual-container">
    <div class="visual-header">
        <span class="visual-type-badge">📊 Chart</span>
        <span class="visual-title">TEAS Math Topic Frequency</span>
    </div>
    <div class="visual-body">
        <!-- SVG, PNG, or KaTeX-rendered content -->
    </div>
    <div class="visual-actions">
        <button>📥 Download</button>
        <button>📋 Copy</button>
    </div>
</div>
```

### KaTeX Setup
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
```

Inline math wrapped in `$...$`, block math in `$$...$$`. Auto-render scans chat messages on load.

### Mermaid Setup
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
```

Mermaid definitions render to SVG inside a `<pre class="mermaid">` block.

---

## Export

### PPTX (python-pptx)
Study sheets and individual visuals export to editable PowerPoint. Already in our toolchain.

### HTML
Any visual can be saved as a standalone HTML file (self-contained with inline CSS).

### PDF
Future phase — LibreOffice headless conversion (already on M7-Ultra).

---

## Model Tool Interface

The toolkit exposes a simple function-call interface to the LLM:

```python
tools = [
    {
        "name": "generate_visual",
        "description": "Generate a visual aid (diagram, chart, formula, table, or study sheet) to help the student understand a concept.",
        "parameters": {
            "type": "object",
            "properties": {
                "visual_type": {
                    "type": "string",
                    "enum": ["flowchart", "concept_map", "chart", "formula", "table", "study_sheet"]
                },
                "title": {"type": "string"},
                "content": {"type": "object", "description": "Visual-specific data (see types above)"}
            },
            "required": ["visual_type", "title", "content"]
        }
    }
]
```

The tutor decides *when* to use it based on the conversation context. No explicit student trigger needed — the model uses its judgment.

---

## Design Principles

1. **No new framework.** Python backend, lightweight JS in frontend. Mermaid + KaTeX via CDN.
2. **Build once, use everywhere.** Module is harness-agnostic. TEAS tutor, OpenStax tutor, ORDER coach — all import the same module.
3. **Non-AI aesthetic.** Clean editorial style. No purple gradients, no glassmorphism. Think textbook, not startup landing page.
4. **Downloadable by default.** Every visual has a download button. Students build a personal study library.
5. **Model decides, not the student.** The tutor generates visuals proactively when it judges they'd help — no extra UI controls needed.

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] `toolkit.py` dispatcher + `formulas.py` (KaTeX LaTeX generation)
- [ ] `tables.py` (HTML table generation)
- [ ] Frontend: KaTeX rendering in chat stream
- [ ] Inline math support (`$...$`) in all tutor responses
- [ ] Wire tool call into TEAS study app harness

### Phase 2: Diagrams & Charts (Week 3-4)
- [ ] `diagrams.py` (Mermaid → SVG)
- [ ] `charts.py` (matplotlib → PNG/SVG)
- [ ] Frontend: Mermaid rendering in chat stream
- [ ] Diagram/chart templates for common TEAS patterns
- [ ] Download buttons (PNG, SVG)

### Phase 3: Study Sheets & Export (Week 5-6)
- [ ] `study_sheets.py` (multi-section composite documents)
- [ ] `export.py` (python-pptx)
- [ ] Study sheet templates per subject (math, science, reading, English)
- [ ] PPTX export with styled layouts
- [ ] Student study library (saved visuals across sessions)

### Phase 4: Smart Generation (Week 7-8)
- [ ] Model learns *when* to generate visuals (few-shot examples in system prompt)
- [ ] Adaptive visual selection based on student performance data
- [ ] Visual difficulty matching (simple diagrams for beginners, detailed for advanced)
- [ ] A/B testing visual vs. text-only explanations

---

## Resolved Decisions (May 5, 2026)

1. **Mermaid rendering: Client-side JS (CDN).** Lighter on the droplet, no puppeteer/playwright dependency, Mermaid JS is battle-tested. Server-side mermaid-py requires a headless browser — overkill for our $6/mo infra. The Python backend only generates the Mermaid definition string; the frontend renders it to SVG.
2. **Chart style: Theme-driven.** Colors, fonts, and styling controlled by the app theme, not hardcoded. Makes it easy to rebrand per client or per subject without touching the toolkit code.
3. **Session persistence: Visuals persist across sessions.** Students build a personal study library over time. Requires user accounts (already planned for the study app). Visuals are stored server-side and surfaced in a "My Study Library" section.
