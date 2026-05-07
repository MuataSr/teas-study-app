"""
Mu2 Creative Toolkit
====================

Shared visual generation module for Mu2 tutor harnesses.
Any Mu2 tutor imports it and gets formula, diagram, and table generation.

Zero external Python dependencies. KaTeX + Mermaid render client-side via CDN.

Quick start:
    from mu2_creative_toolkit import generate_visual, get_css_bundle

    # Generate a formula
    html = generate_visual("formula", {
        "key": "quadratic_formula"
    })

    # Generate a diagram from raw Mermaid
    html = generate_visual("diagram", {
        "title": "Cell Respiration",
        "mermaid": "graph TD\\n  A[Glucose] --> B[Glycolysis]\\n  B --> C[ATP]"
    })

    # Generate a table
    html = generate_visual("table", {
        "title": "Muscle Types",
        "headers": ["Type", "Control", "Function"],
        "rows": [
            ["Skeletal", "Voluntary", "Movement"],
            ["Smooth", "Involuntary", "Organ function"],
            ["Cardiac", "Involuntary", "Pumping blood"]
        ]
    })

    # Get all CSS for frontend
    css = get_css_bundle()
"""

from .toolkit import (
    generate_visual,
    get_css_bundle,
    get_formula_generator,
    get_diagram_generator,
    get_table_generator,
    VISUAL_TOOL_DEFINITION,
)

__all__ = [
    "generate_visual",
    "get_css_bundle",
    "get_formula_generator",
    "get_diagram_generator",
    "get_table_generator",
    "VISUAL_TOOL_DEFINITION",
]
