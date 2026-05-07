"""
Mu2 Creative Toolkit — Tables Module

Generates clean, themed HTML tables for comparisons, summaries,
and reference data. Zero external dependencies.

Usage:
    from mu2_creative_toolkit.tables import TableGenerator

    gen = TableGenerator()
    html = gen.render(headers=["Type", "Function"], rows=[["Skeletal", "Movement"], ...])
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Literal, Optional


# ── Data structures ──────────────────────────────────────────────────────────

TableStyle = Literal["default", "striped", "bordered", "compact"]


@dataclass
class TableDef:
    """Complete table definition with metadata."""
    headers: list[str]
    rows: list[list[str]]
    title: str = ""
    caption: str = ""
    style: TableStyle = "default"
    footer: str = ""

    def to_html(self) -> str:
        """Render as a styled HTML table."""
        escaped_title = html.escape(self.title) if self.title else ""
        escaped_caption = html.escape(self.caption) if self.caption else ""

        lines = [
            f'<div class="table-block" data-style="{self.style}">',
        ]

        if escaped_title:
            lines.append(f'  <div class="table-title">{escaped_title}</div>')

        lines.append('  <table>')

        # Header row
        lines.append('    <thead>')
        lines.append('      <tr>')
        for h in self.headers:
            lines.append(f'        <th>{html.escape(h)}</th>')
        lines.append('      </tr>')
        lines.append('    </thead>')

        # Body rows
        lines.append('    <tbody>')
        for row in self.rows:
            lines.append('      <tr>')
            for cell in row:
                lines.append(f'        <td>{html.escape(cell)}</td>')
            lines.append('      </tr>')
        lines.append('    </tbody>')

        # Footer row (spans all columns)
        if self.footer:
            colspan = len(self.headers)
            escaped_footer = html.escape(self.footer)
            lines.append('    <tfoot>')
            lines.append(f'      <tr><td colspan="{colspan}">{escaped_footer}</td></tr>')
            lines.append('    </tfoot>')

        lines.append('  </table>')

        if escaped_caption:
            lines.append(f'  <div class="table-caption">{escaped_caption}</div>')

        lines.append('</div>')
        return "\n".join(lines)


# ── Generator ────────────────────────────────────────────────────────────────

class TableGenerator:
    """Generates styled HTML tables."""

    def render(
        self,
        headers: list[str],
        rows: list[list[str]],
        *,
        title: str = "",
        caption: str = "",
        style: TableStyle = "default",
        footer: str = "",
    ) -> str:
        """Generate an HTML table.

        Args:
            headers: Column headers.
            rows: List of row data (each row is a list of strings).
            title: Optional display title above the table.
            caption: Optional caption below the table.
            style: "default", "striped", "bordered", or "compact".
            footer: Optional footer row text.

        Returns:
            HTML string for the table.
        """
        table_def = TableDef(
            headers=headers,
            rows=rows,
            title=title,
            caption=caption,
            style=style,
            footer=footer,
        )
        return table_def.to_html()

    def render_comparison(
        self,
        items: list[dict],
        *,
        title: str = "Comparison",
        style: TableStyle = "striped",
    ) -> str:
        """Render a list of dicts as a comparison table.

        Each dict's keys become headers, values become cells.
        First dict determines column order.

        Args:
            items: List of dicts with consistent keys.
            title: Display title.
            style: Table style.

        Returns:
            HTML string for the comparison table.
        """
        if not items:
            return ""

        # Use keys from first item as headers
        headers = list(items[0].keys())
        rows = [
            [str(item.get(h, "")) for h in headers]
            for item in items
        ]

        return self.render(
            headers=headers,
            rows=rows,
            title=title,
            style=style,
        )


# ── Table CSS snippet (for frontend) ─────────────────────────────────────────

TABLE_CSS_CLASSES = """
/* Table block styles — theme-driven */
.table-block {
    margin: 0.75rem 0;
    overflow-x: auto;
}

.table-title {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-secondary, #555);
    margin-bottom: 0.5rem;
}

.table-block table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.table-block th,
.table-block td {
    padding: 0.6rem 0.8rem;
    text-align: left;
    border-bottom: 1px solid var(--border, #e0e0e0);
}

.table-block th {
    font-weight: 600;
    color: var(--text-primary, #1B3A5C);
    border-bottom: 2px solid var(--border, #ccc);
}

.table-block tfoot td {
    font-style: italic;
    color: var(--text-secondary, #666);
    font-size: 0.8rem;
}

.table-caption {
    font-size: 0.8rem;
    color: var(--text-secondary, #666);
    margin-top: 0.4rem;
    font-style: italic;
}

/* Striped variant */
.table-block[data-style="striped"] tbody tr:nth-child(even) {
    background: var(--surface-alt, #f5f5f2);
}

/* Bordered variant */
.table-block[data-style="bordered"] table {
    border: 1px solid var(--border, #ddd);
}

.table-block[data-style="bordered"] th,
.table-block[data-style="bordered"] td {
    border: 1px solid var(--border, #ddd);
}

/* Compact variant */
.table-block[data-style="compact"] th,
.table-block[data-style="compact"] td {
    padding: 0.35rem 0.5rem;
    font-size: 0.85rem;
}
"""
