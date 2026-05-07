"""
Mu2 Creative Toolkit — Main Dispatcher

Single entry point: generate_visual(type, data)
Routes to the appropriate generator (formula, diagram, table, chart, study_sheet).

Usage:
    from mu2_creative_toolkit import generate_visual

    html = generate_visual("formula", {
        "latex": r"\\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}",
        "label": "Quadratic Formula"
    })
"""

from __future__ import annotations

from typing import Any

from .formulas import FormulaGenerator
from .diagrams import DiagramGenerator
from .tables import TableGenerator


# ── Singleton generators ─────────────────────────────────────────────────────

_formula_gen = FormulaGenerator()
_diagram_gen = DiagramGenerator()
_table_gen = TableGenerator()


# ── Public API ───────────────────────────────────────────────────────────────

def generate_visual(visual_type: str, data: dict[str, Any]) -> str:
    """Generate a visual and return its HTML.

    This is the main entry point that the tutor harness calls.
    The LLM generates the tool call with type + data, this renders it.

    Args:
        visual_type: One of "formula", "diagram", "table", "chart", "study_sheet".
        data: Visual-specific data dict (varies by type).

    Returns:
        HTML string ready for rendering in the chat stream.

    Raises:
        ValueError: If visual_type is unknown or required data is missing.
    """
    if visual_type == "formula":
        return _render_formula(data)
    elif visual_type == "diagram":
        return _render_diagram(data)
    elif visual_type == "table":
        return _render_table(data)
    elif visual_type == "chart":
        return _render_chart(data)
    elif visual_type == "study_sheet":
        return _render_study_sheet(data)
    else:
        raise ValueError(
            f"Unknown visual_type: {visual_type!r}. "
            f"Expected: formula, diagram, table, chart, study_sheet"
        )


# ── Type renderers ───────────────────────────────────────────────────────────

def _render_formula(data: dict[str, Any]) -> str:
    """Render a formula.

    Two modes:
      1. Library formula: data["key"] = "quadratic_formula"
      2. Custom formula: data["latex"] = raw LaTeX string
    """
    # Library formula
    if "key" in data:
        return _formula_gen.render(
            data["key"],
            display_mode=data.get("display_mode", True),
        )

    # Custom formula
    latex = data.get("latex", "")
    if not latex:
        raise ValueError("Formula requires 'key' or 'latex'")

    return _formula_gen.render_custom(
        latex=latex,
        label=data.get("label", ""),
        category=data.get("category", "math"),
        explanation=data.get("explanation", ""),
        variables=data.get("variables"),
        display_mode=data.get("display_mode", True),
    )


def _render_diagram(data: dict[str, Any]) -> str:
    """Render a diagram.

    Two modes:
      1. Raw Mermaid: data["mermaid"] = raw string (simplest for LLM)
      2. Structured: data["nodes"] + data["edges"]
    """
    # Raw Mermaid (preferred for LLM-generated diagrams)
    if "mermaid" in data:
        return _diagram_gen.render_raw(
            mermaid=data["mermaid"],
            title=data.get("title", ""),
            diagram_type=data.get("diagram_type", "flowchart"),
        )

    # Structured diagram
    return _diagram_gen.render(
        diagram_type=data.get("diagram_type", "flowchart"),
        title=data.get("title", ""),
        direction=data.get("direction", "TD"),
        nodes=data.get("nodes"),
        edges=data.get("edges"),
        subgraphs=data.get("subgraphs"),
        node_styles=data.get("node_styles"),
        participants=data.get("participants"),
        steps=data.get("steps"),
    )


def _render_table(data: dict[str, Any]) -> str:
    """Render a table.

    Two modes:
      1. Headers + rows: data["headers"] + data["rows"]
      2. Comparison: data["items"] (list of dicts)
    """
    gen = _table_gen

    if "items" in data:
        return gen.render_comparison(
            items=data["items"],
            title=data.get("title", "Comparison"),
            style=data.get("style", "striped"),
        )

    headers = data.get("headers", [])
    rows = data.get("rows", [])
    if not headers or not rows:
        raise ValueError("Table requires 'headers' and 'rows' (or 'items')")

    return gen.render(
        headers=headers,
        rows=rows,
        title=data.get("title", ""),
        caption=data.get("caption", ""),
        style=data.get("style", "default"),
        footer=data.get("footer", ""),
    )


def _render_chart(data: dict[str, Any]) -> str:
    """Render a chart placeholder.

    Charts require matplotlib (optional dep). If not available,
    returns a styled placeholder message.

    TODO: Implement in Phase 2 with matplotlib.
    """
    chart_type = data.get("chart_type", "bar")
    title = data.get("title", "Chart")
    escaped_title = html_escape(title)

    return (
        f'<div class="chart-placeholder">'
        f'  <div class="chart-title">{escaped_title}</div>'
        f'  <div class="chart-body">'
        f'    <p>📊 {html_escape(chart_type).capitalize()} chart coming in Phase 2.</p>'
        f'    <p>Charts require matplotlib — rendering on the server.</p>'
        f'  </div>'
        f'</div>'
    )


def _render_study_sheet(data: dict[str, Any]) -> str:
    """Render a multi-section study sheet.

    Combines formulas, diagrams, and tables into one composite document.

    TODO: Implement in Phase 3.
    """
    title = data.get("title", "Study Sheet")
    escaped_title = html_escape(title)

    return (
        f'<div class="study-sheet">'
        f'  <h3 class="study-sheet-title">{escaped_title}</h3>'
        f'  <p>Study sheets coming in Phase 3.</p>'
        f'</div>'
    )


def _html_escape(text: str) -> str:
    """Simple HTML escaping (avoids importing html for chart placeholder)."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ── Convenience accessors ────────────────────────────────────────────────────

def get_formula_generator() -> FormulaGenerator:
    """Access the formula generator directly (for advanced use)."""
    return _formula_gen


def get_diagram_generator() -> DiagramGenerator:
    """Access the diagram generator directly (for advanced use)."""
    return _diagram_gen


def get_table_generator() -> TableGenerator:
    """Access the table generator directly (for advanced use)."""
    return _table_gen


# ── Tool definition for LLM ──────────────────────────────────────────────────

VISUAL_TOOL_DEFINITION = {
    "name": "generate_visual",
    "description": (
        "Generate a visual aid to help the student understand a concept. "
        "Choose the visual type based on what would best help: "
        "formulas for equations, diagrams for processes/relationships, "
        "tables for comparisons/summaries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "visual_type": {
                "type": "string",
                "enum": ["formula", "diagram", "table", "chart", "study_sheet"],
                "description": "The type of visual to generate.",
            },
            "title": {
                "type": "string",
                "description": "Display title for the visual.",
            },
            "data": {
                "type": "object",
                "description": (
                    "Visual-specific data. "
                    "For formulas: {'key': 'quadratic_formula'} or {'latex': '...', 'label': '...'}. "
                    "For diagrams: {'mermaid': 'graph TD\\n  A-->B'} or {'nodes': [...], 'edges': [...]}. "
                    "For tables: {'headers': [...], 'rows': [[...], ...]} or {'items': [{...}, ...]}."
                ),
            },
        },
        "required": ["visual_type", "data"],
    },
}


# ── CSS bundle ───────────────────────────────────────────────────────────────

def get_css_bundle() -> str:
    """Return combined CSS for all visual types (for frontend <style> tag)."""
    from .formulas import KATEX_CSS_CLASSES
    from .diagrams import DIAGRAM_CSS_CLASSES
    from .tables import TABLE_CSS_CLASSES

    return f"""
/* Mu2 Creative Toolkit Styles */
{KATEX_CSS_CLASSES}
{DIAGRAM_CSS_CLASSES}
{TABLE_CSS_CLASSES}
"""
