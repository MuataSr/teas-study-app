"""
Mu2 Creative Toolkit — Diagram Generator

Generates Mermaid diagram definitions and HTML wrappers for flowcharts,
concept maps, process diagrams, and sequence diagrams.

Usage:
    from mu2_creative_toolkit.diagrams import DiagramGenerator

    gen = DiagramGenerator()
    html = gen.render("flowchart", nodes=[...], edges=[...])
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Literal, Optional


# ── Data structures ──────────────────────────────────────────────────────────

DiagramType = Literal["flowchart", "concept_map", "process", "sequence"]


@dataclass
class DiagramNode:
    """A node in a diagram."""
    id: str
    label: str
    shape: str = "rect"    # rect, rounded, diamond, circle, stadium
    style: str = ""         # optional Mermaid style overrides


@dataclass
class DiagramEdge:
    """A directed edge between two nodes."""
    source: str
    target: str
    label: str = ""


@dataclass
class DiagramDef:
    """Complete diagram definition ready for Mermaid rendering."""
    mermaid: str
    diagram_type: DiagramType
    title: str = ""
    css_classes: str = ""   # optional extra CSS

    def to_html(self) -> str:
        """Render as a Mermaid-ready HTML block for frontend rendering."""
        escaped_title = html.escape(self.title) if self.title else ""

        lines = [
            f'<div class="diagram-block" data-type="{self.diagram_type}">',
        ]
        if escaped_title:
            lines.append(f'  <div class="diagram-title">{escaped_title}</div>')
        lines.append('  <pre class="mermaid">')
        for line in self.mermaid.strip().splitlines():
            lines.append(f'    {line}')
        lines.append('  </pre>')
        lines.append('</div>')
        return "\n".join(lines)


# ── Shape mapping ─────────────────────────────────────────────────────────────

SHAPE_MAP: dict[str, str] = {
    "rect":     "",                    # A[Label]    — rectangle
    "rounded":  "(",                   # A(Label)    — rounded rectangle
    "stadium":  "([",                  # A([Label])  — stadium
    "diamond":  "{",                   # A{Label}    — diamond (decision)
    "circle":   "((",                  # A((Label))  — circle
    "hexagon":  "{{",                  # A{{Label}}  — hexagon (subroutine)
    "cylinder": "[(",                  # A[(Label)]  — cylinder (database)
    "parallelogram": "[/",             # A[/Label/]  — parallelogram
    "trapezoid": "[\\",               # A[\Label/]  — trapezoid
}

SHAPE_CLOSE: dict[str, str] = {
    "rect":           "]",
    "rounded":        ")",
    "stadium":        "])",
    "diamond":        "}",
    "circle":         "))",
    "hexagon":        "}}",
    "cylinder":       ")]",
    "parallelogram":  "/]",
    "trapezoid":      "/]",
}


def _format_node(node: DiagramNode) -> str:
    """Format a node as a Mermaid node declaration."""
    label = html.escape(node.label)
    open_shape = SHAPE_MAP.get(node.shape, "")
    close_shape = SHAPE_CLOSE.get(node.shape, "]")

    if node.style:
        return f'{node.id}["{label}"]:::{node.style}'
    elif open_shape:
        return f'{node.id}{open_shape}"{label}"{close_shape}'
    else:
        return f'{node.id}["{label}"]'


def _format_edge(edge: DiagramEdge) -> str:
    """Format an edge as a Mermaid edge declaration."""
    if edge.label:
        escaped = html.escape(edge.label)
        return f'{edge.source} -->|{escaped}| {edge.target}'
    return f'{edge.source} --> {edge.target}'


# ── Diagram templates ────────────────────────────────────────────────────────

def _build_flowchart_mermaid(
    direction: str = "TD",
    nodes: list[DiagramNode] | None = None,
    edges: list[DiagramEdge] | None = None,
    subgraphs: list[dict] | None = None,
    node_styles: dict[str, str] | None = None,
) -> str:
    """Build a Mermaid flowchart definition string."""
    lines = [f"flowchart {direction}"]

    # Subgraphs (grouped sections)
    if subgraphs:
        for sg in subgraphs:
            sg_id = sg.get("id", "")
            sg_label = sg.get("label", "")
            sg_nodes = sg.get("nodes", [])
            lines.append(f'  subgraph {sg_id} ["{sg_label}"]')
            for node in sg_nodes:
                if isinstance(node, DiagramNode):
                    lines.append(f'    {_format_node(node)}')
            lines.append('  end')

    # Nodes (outside subgraphs)
    if nodes:
        for node in nodes:
            lines.append(f'  {_format_node(node)}')

    # Edges
    if edges:
        for edge in edges:
            lines.append(f'  {_format_edge(edge)}')

    # Style definitions
    if node_styles:
        for style_name, style_def in node_styles.items():
            lines.append(f'  style {style_name} {style_def}')

    return "\n".join(lines)


def _build_concept_map_mermaid(
    nodes: list[DiagramNode],
    edges: list[DiagramEdge],
) -> str:
    """Build a concept map (LR-directed graph with labeled edges)."""
    lines = ["flowchart LR"]

    for node in nodes:
        lines.append(f'  {_format_node(node)}')

    for edge in edges:
        label = edge.label or "relates to"
        escaped = html.escape(label)
        lines.append(f'  {edge.source} --- |"{escaped}"| {edge.target}')

    return "\n".join(lines)


def _build_sequence_mermaid(
    participants: list[str],
    steps: list[dict],
    title: str = "",
) -> str:
    """Build a sequence diagram.

    Steps are dicts with keys: actor, action, arrow ("→", "←", "→>").
    """
    lines = ["sequenceDiagram"]
    if title:
        lines.append(f'  title {html.escape(title)}')

    for p in participants:
        lines.append(f'  participant {p}')

    for step in steps:
        actor = step.get("actor", "")
        target = step.get("target", "")
        action = step.get("action", "")
        arrow = step.get("arrow", "->>")
        escaped_action = html.escape(action)
        lines.append(f'  {actor}{arrow}{target}: {escaped_action}')

    return "\n".join(lines)


# ── Generator ────────────────────────────────────────────────────────────────

class DiagramGenerator:
    """Generates Mermaid diagram definitions and HTML wrappers."""

    def render(
        self,
        diagram_type: DiagramType,
        *,
        title: str = "",
        direction: str = "TD",
        nodes: list[dict] | None = None,
        edges: list[dict] | None = None,
        subgraphs: list[dict] | None = None,
        node_styles: dict[str, str] | None = None,
        participants: list[str] | None = None,
        steps: list[dict] | None = None,
        raw_mermaid: str | None = None,
    ) -> str:
        """Generate a diagram and return its HTML.

        For flowchart/concept_map/process: provide nodes + edges (dicts or DiagramNodes).
        For sequence: provide participants + steps.
        For raw: provide raw_mermaid string (bypasses all other params).

        Args:
            diagram_type: "flowchart", "concept_map", "process", "sequence"
            title: Optional display title.
            direction: "TD" (top-down), "LR" (left-right), "BT", "RL"
            nodes: List of {"id", "label", "shape"} dicts.
            edges: List of {"source", "target", "label"} dicts.
            subgraphs: List of {"id", "label", "nodes"} dicts.
            node_styles: Dict of {nodeId: "css_style_string"}.
            participants: List of participant names (sequence diagrams only).
            steps: List of step dicts (sequence diagrams only).
            raw_mermaid: Raw Mermaid definition string (overrides all other params).

        Returns:
            HTML string with <pre class="mermaid"> block.
        """
        if raw_mermaid:
            mermaid_str = raw_mermaid
        elif diagram_type == "sequence":
            if not participants or not steps:
                raise ValueError("Sequence diagrams require participants and steps")
            mermaid_str = _build_sequence_mermaid(
                participants=participants,
                steps=steps,
                title=title,
            )
        else:
            if not nodes:
                raise ValueError(f"{diagram_type} diagrams require nodes")

            parsed_nodes = [
                DiagramNode(
                    id=n.get("id", ""),
                    label=n.get("label", ""),
                    shape=n.get("shape", "rect"),
                    style=n.get("style", ""),
                )
                for n in nodes
            ]
            parsed_edges = [
                DiagramEdge(
                    source=e.get("source", ""),
                    target=e.get("target", ""),
                    label=e.get("label", ""),
                )
                for e in (edges or [])
            ]

            if diagram_type == "concept_map":
                mermaid_str = _build_concept_map_mermaid(parsed_nodes, parsed_edges)
            else:
                mermaid_str = _build_flowchart_mermaid(
                    direction=direction,
                    nodes=parsed_nodes,
                    edges=parsed_edges,
                    subgraphs=subgraphs,
                    node_styles=node_styles,
                )

        diagram_def = DiagramDef(
            mermaid=mermaid_str,
            diagram_type=diagram_type,
            title=title,
        )
        return diagram_def.to_html()

    def render_raw(self, mermaid: str, title: str = "", diagram_type: DiagramType = "flowchart") -> str:
        """Render raw Mermaid string — simplest interface for LLM-generated diagrams.

        The model writes the Mermaid definition directly. This wraps it in HTML.
        """
        return self.render(
            diagram_type=diagram_type,
            title=title,
            raw_mermaid=mermaid,
        )


# ── Diagram CSS snippet (for frontend) ───────────────────────────────────────

DIAGRAM_CSS_CLASSES = """
/* Diagram block styles — theme-driven */
.diagram-block {
    background: var(--surface, #fafaf7);
    border: 1px solid var(--border, #e0e0e0);
    border-radius: 6px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    overflow-x: auto;
}

.diagram-title {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-secondary, #555);
    margin-bottom: 0.75rem;
}

.diagram-block pre.mermaid {
    background: transparent;
    padding: 0;
    margin: 0;
    font-family: inherit;
    text-align: center;
}
"""
