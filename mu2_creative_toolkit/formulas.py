"""
Mu2 Creative Toolkit — LaTeX Formula Generator

Generates LaTeX strings and KaTeX-ready HTML wrappers for math, chemistry,
and physics notation. Zero external Python dependencies.

Usage:
    from mu2_creative_toolkit.formulas import FormulaGenerator

    gen = FormulaGenerator()
    html = gen.render("quadratic_formula")
    # or
    html = gen.render_custom(r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}", "Quadratic Formula")
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class FormulaBlock:
    """A single formula with metadata for rendering."""
    latex: str
    label: str
    category: str = "math"          # math | chemistry | physics
    display_mode: bool = True       # True = block, False = inline
    explanation: str = ""
    variables: list[FormulaVar] = field(default_factory=list)

    def to_katex_html(self) -> str:
        """Render as KaTeX-ready HTML block."""
        escaped_label = html.escape(self.label)
        escaped_explanation = html.escape(self.explanation) if self.explanation else ""

        # KaTeX delimiters: $$...$$ for block, $...$ for inline
        delim = "$$" if self.display_mode else "$"

        parts = [
            f'<div class="formula-block" data-category="{self.category}">',
        ]

        if self.label:
            parts.append(f'  <div class="formula-label">{escaped_label}</div>')

        parts.append(f'  <div class="formula-math">{delim}{self.latex}{delim}</div>')

        if escaped_explanation:
            parts.append(f'  <div class="formula-explanation">{escaped_explanation}</div>')

        if self.variables:
            parts.append('  <div class="formula-variables"><strong>Variables:</strong><ul>')
            for v in self.variables:
                escaped_sym = html.escape(v.symbol)
                escaped_desc = html.escape(v.description)
                parts.append(f'    <li>{escaped_sym} = {escaped_desc}</li>')
            parts.append('  </ul></div>')

        parts.append('</div>')
        return "\n".join(parts)

    def to_inline_html(self) -> str:
        """Render as inline KaTeX (for embedding in chat text)."""
        return f'<span class="formula-inline" data-category="{self.category}">${self.latex}$</span>'


@dataclass
class FormulaVar:
    """A variable in a formula with its meaning."""
    symbol: str
    description: str


# ── Template Library ─────────────────────────────────────────────────────────

# Pre-built formulas organized by subject. The model can reference these by key
# or generate custom LaTeX strings.

FORMULA_LIBRARY: dict[str, FormulaBlock] = {

    # ── Math ──────────────────────────────────────────────────────────────

    "quadratic_formula": FormulaBlock(
        latex=r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
        label="Quadratic Formula",
        category="math",
        explanation="Solves any quadratic equation of the form ax² + bx + c = 0",
        variables=[
            FormulaVar("a", "coefficient of x² (leading coefficient)"),
            FormulaVar("b", "coefficient of x"),
            FormulaVar("c", "constant term"),
        ],
    ),

    "pythagorean_theorem": FormulaBlock(
        latex=r"a^2 + b^2 = c^2",
        label="Pythagorean Theorem",
        category="math",
        explanation="In a right triangle, the sum of the squares of the legs equals the square of the hypotenuse",
        variables=[
            FormulaVar("a, b", "lengths of the legs (shorter sides)"),
            FormulaVar("c", "length of the hypotenuse (longest side)"),
        ],
    ),

    "slope": FormulaBlock(
        latex=r"m = \frac{y_2 - y_1}{x_2 - x_1}",
        label="Slope Formula",
        category="math",
        explanation="Calculates the steepness of a line between two points",
        variables=[
            FormulaVar("m", "slope of the line"),
            FormulaVar("(x₁, y₁)", "first point coordinates"),
            FormulaVar("(x₂, y₂)", "second point coordinates"),
        ],
    ),

    "distance_formula": FormulaBlock(
        latex=r"d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}",
        label="Distance Formula",
        category="math",
        explanation="Calculates the straight-line distance between two points in a coordinate plane",
        variables=[
            FormulaVar("d", "distance between the points"),
            FormulaVar("(x₁, y₁)", "first point coordinates"),
            FormulaVar("(x₂, y₂)", "second point coordinates"),
        ],
    ),

    "midpoint_formula": FormulaBlock(
        latex=r"M = \left( \frac{x_1 + x_2}{2}, \frac{y_1 + y_2}{2} \right)",
        label="Midpoint Formula",
        category="math",
        explanation="Finds the exact midpoint of a line segment between two points",
    ),

    "point_slope": FormulaBlock(
        latex=r"y - y_1 = m(x - x_1)",
        label="Point-Slope Form",
        category="math",
        explanation="Equation of a line using a known point and the slope",
        variables=[
            FormulaVar("m", "slope of the line"),
            FormulaVar("(x₁, y₁)", "a point the line passes through"),
        ],
    ),

    "circle_area": FormulaBlock(
        latex=r"A = \pi r^2",
        label="Area of a Circle",
        category="math",
        explanation="Calculates the area enclosed by a circle",
        variables=[
            FormulaVar("A", "area"),
            FormulaVar("r", "radius of the circle"),
        ],
    ),

    "circle_circumference": FormulaBlock(
        latex=r"C = 2\pi r",
        label="Circumference of a Circle",
        category="math",
        explanation="Calculates the distance around a circle",
        variables=[
            FormulaVar("C", "circumference"),
            FormulaVar("r", "radius"),
        ],
    ),

    "area_rectangle": FormulaBlock(
        latex=r"A = l \times w",
        label="Area of a Rectangle",
        category="math",
        explanation="Calculates the area of a rectangle",
        variables=[
            FormulaVar("l", "length"),
            FormulaVar("w", "width"),
        ],
    ),

    "area_triangle": FormulaBlock(
        latex=r"A = \frac{1}{2}bh",
        label="Area of a Triangle",
        category="math",
        explanation="Calculates the area of a triangle",
        variables=[
            FormulaVar("b", "base length"),
            FormulaVar("h", "height (perpendicular to base)"),
        ],
    ),

    "area_trapezoid": FormulaBlock(
        latex=r"A = \frac{1}{2}(b_1 + b_2)h",
        label="Area of a Trapezoid",
        category="math",
        explanation="Calculates the area of a trapezoid",
        variables=[
            FormulaVar("b₁, b₂", "lengths of the two parallel sides (bases)"),
            FormulaVar("h", "height"),
        ],
    ),

    "volume_cylinder": FormulaBlock(
        latex=r"V = \pi r^2 h",
        label="Volume of a Cylinder",
        category="math",
        explanation="Calculates the volume of a right circular cylinder",
        variables=[
            FormulaVar("V", "volume"),
            FormulaVar("r", "radius of the base"),
            FormulaVar("h", "height"),
        ],
    ),

    "volume_sphere": FormulaBlock(
        latex=r"V = \frac{4}{3}\pi r^3",
        label="Volume of a Sphere",
        category="math",
        explanation="Calculates the volume of a sphere",
        variables=[
            FormulaVar("V", "volume"),
            FormulaVar("r", "radius"),
        ],
    ),

    "volume_cone": FormulaBlock(
        latex=r"V = \frac{1}{3}\pi r^2 h",
        label="Volume of a Cone",
        category="math",
        explanation="Calculates the volume of a right circular cone",
        variables=[
            FormulaVar("V", "volume"),
            FormulaVar("r", "radius of the base"),
            FormulaVar("h", "height"),
        ],
    ),

    "percent_change": FormulaBlock(
        latex=r"\text{Percent Change} = \frac{\text{New} - \text{Old}}{\text{Old}} \times 100",
        label="Percent Change",
        category="math",
        explanation="Calculates the percentage increase or decrease between two values",
    ),

    "mean": FormulaBlock(
        latex=r"\bar{x} = \frac{\sum x_i}{n}",
        label="Mean (Average)",
        category="math",
        explanation="The sum of all values divided by the number of values",
        variables=[
            FormulaVar(r"\bar{x}", "the mean"),
            FormulaVar("n", "number of values"),
        ],
    ),

    "simple_interest": FormulaBlock(
        latex=r"I = Prt",
        label="Simple Interest",
        category="math",
        explanation="Calculates interest earned or owed on a principal amount",
        variables=[
            FormulaVar("I", "interest"),
            FormulaVar("P", "principal (starting amount)"),
            FormulaVar("r", "annual interest rate (as a decimal)"),
            FormulaVar("t", "time in years"),
        ],
    ),

    "probability": FormulaBlock(
        latex=r"P(E) = \frac{\text{favorable outcomes}}{\text{total outcomes}}",
        label="Basic Probability",
        category="math",
        explanation="The likelihood of an event occurring",
    ),

    "combinations": FormulaBlock(
        latex=r"_nC_r = \frac{n!}{r!(n-r)!}",
        label="Combinations",
        category="math",
        explanation="Number of ways to choose r items from n items when order doesn't matter",
        variables=[
            FormulaVar("n", "total number of items"),
            FormulaVar("r", "number of items being chosen"),
        ],
    ),

    "permutations": FormulaBlock(
        latex=r"_nP_r = \frac{n!}{(n-r)!}",
        label="Permutations",
        category="math",
        explanation="Number of ways to arrange r items from n items when order matters",
    ),

    # ── Chemistry ──────────────────────────────────────────────────────────

    "ideal_gas_law": FormulaBlock(
        latex=r"PV = nRT",
        label="Ideal Gas Law",
        category="chemistry",
        explanation="Relates pressure, volume, temperature, and moles of a gas",
        variables=[
            FormulaVar("P", "pressure (atm)"),
            FormulaVar("V", "volume (L)"),
            FormulaVar("n", "moles of gas"),
            FormulaVar("R", "ideal gas constant (0.0821 L·atm/mol·K)"),
            FormulaVar("T", "temperature (K)"),
        ],
    ),

    "density": FormulaBlock(
        latex=r"\rho = \frac{m}{V}",
        label="Density",
        category="chemistry",
        explanation="Mass per unit volume of a substance",
        variables=[
            FormulaVar(r"\rho", "density (g/cm³ or g/mL)"),
            FormulaVar("m", "mass (g)"),
            FormulaVar("V", "volume (cm³ or mL)"),
        ],
    ),

    "molarity": FormulaBlock(
        latex=r"M = \frac{\text{moles of solute}}{\text{liters of solution}}",
        label="Molarity",
        category="chemistry",
        explanation="Concentration of a solution expressed as moles per liter",
    ),

    "dilution": FormulaBlock(
        latex=r"M_1V_1 = M_2V_2",
        label="Dilution Formula",
        category="chemistry",
        explanation="Relates the concentration and volume before and after dilution",
        variables=[
            FormulaVar("M₁", "initial concentration (molarity)"),
            FormulaVar("V₁", "initial volume"),
            FormulaVar("M₂", "final concentration"),
            FormulaVar("V₂", "final volume"),
        ],
    ),

    "ph": FormulaBlock(
        latex=r"\text{pH} = -\log[\text{H}^+]",
        label="pH Formula",
        category="chemistry",
        explanation="Measures acidity or basicity of a solution on a scale of 0–14",
    ),

    "avogadro": FormulaBlock(
        latex=r"n = \frac{N}{N_A}",
        label="Avogadro's Number",
        category="chemistry",
        explanation="Converts between number of particles and moles",
        variables=[
            FormulaVar("n", "number of moles"),
            FormulaVar("N", "number of particles"),
            FormulaVar("N_A", "Avogadro's number (6.022 × 10²³)"),
        ],
    ),

    # ── Physics ───────────────────────────────────────────────────────────

    "newtons_second": FormulaBlock(
        latex=r"F = ma",
        label="Newton's Second Law",
        category="physics",
        explanation="Force equals mass times acceleration — the fundamental equation of motion",
        variables=[
            FormulaVar("F", "force (Newtons)"),
            FormulaVar("m", "mass (kg)"),
            FormulaVar("a", "acceleration (m/s²)"),
        ],
    ),

    "kinetic_energy": FormulaBlock(
        latex=r"KE = \frac{1}{2}mv^2",
        label="Kinetic Energy",
        category="physics",
        explanation="Energy of an object in motion",
        variables=[
            FormulaVar("KE", "kinetic energy (Joules)"),
            FormulaVar("m", "mass (kg)"),
            FormulaVar("v", "velocity (m/s)"),
        ],
    ),

    "gravitational_pe": FormulaBlock(
        latex=r"PE = mgh",
        label="Gravitational Potential Energy",
        category="physics",
        explanation="Energy stored due to an object's height above a reference point",
        variables=[
            FormulaVar("PE", "potential energy (Joules)"),
            FormulaVar("m", "mass (kg)"),
            FormulaVar("g", "acceleration due to gravity (9.8 m/s²)"),
            FormulaVar("h", "height (m)"),
        ],
    ),

    "ohms_law": FormulaBlock(
        latex=r"V = IR",
        label="Ohm's Law",
        category="physics",
        explanation="Voltage equals current times resistance — fundamental to electrical circuits",
        variables=[
            FormulaVar("V", "voltage (Volts)"),
            FormulaVar("I", "current (Amperes)"),
            FormulaVar("R", "resistance (Ohms)"),
        ],
    ),

    "speed": FormulaBlock(
        latex=r"v = \frac{d}{t}",
        label="Speed Formula",
        category="physics",
        explanation="Speed equals distance divided by time",
        variables=[
            FormulaVar("v", "speed (m/s)"),
            FormulaVar("d", "distance (m)"),
            FormulaVar("t", "time (s)"),
        ],
    ),

    "work": FormulaBlock(
        latex=r"W = Fd\cos\theta",
        label="Work Formula",
        category="physics",
        explanation="Work done when a force moves an object over a distance",
        variables=[
            FormulaVar("W", "work (Joules)"),
            FormulaVar("F", "force (Newtons)"),
            FormulaVar("d", "displacement (m)"),
            FormulaVar(r"\theta", "angle between force and displacement"),
        ],
    ),

    "wavelength_energy": FormulaBlock(
        latex=r"E = hf = \frac{hc}{\lambda}",
        label="Photon Energy",
        category="physics",
        explanation="Energy of a photon related to its frequency or wavelength",
        variables=[
            FormulaVar("E", "energy (Joules)"),
            FormulaVar("h", "Planck's constant (6.626 × 10⁻³⁴ J·s)"),
            FormulaVar("f", "frequency (Hz)"),
            FormulaVar("c", "speed of light (3 × 10⁸ m/s)"),
            FormulaVar(r"\lambda", "wavelength (m)"),
        ],
    ),
}


# ── Generator ────────────────────────────────────────────────────────────────

class FormulaGenerator:
    """Generates LaTeX formulas and KaTeX-ready HTML."""

    def __init__(self) -> None:
        self._library = dict(FORMULA_LIBRARY)

    def render(self, key: str, display_mode: bool = True) -> str:
        """Render a named formula from the library.

        Args:
            key: Formula key from FORMULA_LIBRARY (e.g. "quadratic_formula").
            display_mode: True for block display, False for inline.

        Returns:
            KaTeX-ready HTML string.

        Raises:
            KeyError: If the formula key doesn't exist.
        """
        block = self._library[key]
        block.display_mode = display_mode
        return block.to_katex_html() if display_mode else block.to_inline_html()

    def render_custom(
        self,
        latex: str,
        label: str = "",
        category: str = "math",
        explanation: str = "",
        variables: list[dict[str, str]] | None = None,
        display_mode: bool = True,
    ) -> str:
        """Render a custom LaTeX formula not in the library.

        Args:
            latex: Raw LaTeX string.
            label: Optional display label.
            category: "math", "chemistry", or "physics".
            explanation: Optional plain-text explanation.
            variables: Optional list of {"symbol": ..., "description": ...} dicts.
            display_mode: True for block display, False for inline.

        Returns:
            KaTeX-ready HTML string.
        """
        vars_list = [
            FormulaVar(v["symbol"], v["description"])
            for v in (variables or [])
        ]
        block = FormulaBlock(
            latex=latex,
            label=label,
            category=category,
            display_mode=display_mode,
            explanation=explanation,
            variables=vars_list,
        )
        return block.to_katex_html() if display_mode else block.to_inline_html()

    def render_inline(self, latex: str, category: str = "math") -> str:
        """Render a quick inline formula (for embedding in chat text)."""
        block = FormulaBlock(latex=latex, category=category, display_mode=False)
        return block.to_inline_html()

    def list_formulas(self, category: str | None = None) -> list[dict]:
        """List available formulas, optionally filtered by category.

        Returns:
            List of {"key": ..., "label": ..., "category": ...} dicts.
        """
        results = []
        for key, block in self._library.items():
            if category and block.category != category:
                continue
            results.append({
                "key": key,
                "label": block.label,
                "category": block.category,
            })
        return results

    def register(self, key: str, block: FormulaBlock) -> None:
        """Add a custom formula to the library for reuse."""
        self._library[key] = block

    def search(self, query: str) -> list[dict]:
        """Search formulas by label or category (case-insensitive substring)."""
        q = query.lower()
        results = []
        for key, block in self._library.items():
            if q in block.label.lower() or q in block.category.lower():
                results.append({
                    "key": key,
                    "label": block.label,
                    "category": block.category,
                })
        return results


# ── KaTeX CSS snippet (for frontend) ─────────────────────────────────────────

KATEX_CSS_CLASSES = """
/* Formula block styles — theme-driven, no hardcoded colors */
.formula-block {
    background: var(--surface, #fafaf7);
    border: 1px solid var(--border, #e0e0e0);
    border-radius: 6px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    font-family: inherit;
}

.formula-label {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-secondary, #555);
    margin-bottom: 0.5rem;
}

.formula-math {
    font-size: 1.2rem;
    overflow-x: auto;
    padding: 0.5rem 0;
}

.formula-explanation {
    font-size: 0.85rem;
    color: var(--text-secondary, #666);
    margin-top: 0.5rem;
    line-height: 1.5;
}

.formula-variables {
    font-size: 0.8rem;
    color: var(--text-secondary, #666);
    margin-top: 0.5rem;
}

.formula-variables ul {
    list-style: none;
    padding-left: 0;
    margin: 0.25rem 0 0 0;
}

.formula-variables li {
    padding: 0.1rem 0;
}

.formula-variables li::before {
    content: "→ ";
    color: var(--accent, #1B3A5C);
}

.formula-inline {
    display: inline;
}
"""
