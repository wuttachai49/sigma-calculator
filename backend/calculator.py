"""Sigma metric calculation and QC rule recommendation engine."""

from __future__ import annotations
from dataclasses import dataclass


# ── QGI ───────────────────────────────────────────────────────────────────────

def calculate_qgi(bias_pct: float, cv_pct: float, tea: float) -> dict:
    """
    Quality Goal Index = (Bias / 1.65) / (CV / TEa × 0.5)

    Numerator   : Bias% / 1.65          — inaccuracy relative to the 1.65 z-score factor
    Denominator : (CV% / TEa%) × 0.5   — imprecision relative to allowable imprecision (0.5 × TEa)

    Simplified  : QGI = (Bias% × TEa%) / (1.65 × 0.5 × CV%)
                       = (Bias% × TEa%) / (0.825 × CV%)

    Interpretation:
      < 0.8  → Precision-limited  (focus: reduce CV)
      0.8–1.2 → Mixed             (both bias & CV contribute equally)
      > 1.2  → Accuracy-limited   (focus: reduce Bias)
    """
    if cv_pct <= 0:
        raise ValueError("CV% must be > 0")
    if tea <= 0:
        raise ValueError("TEa must be > 0")
    denominator = (cv_pct / tea) * 0.5
    if denominator == 0:
        raise ValueError("QGI denominator is zero (CV% / TEa × 0.5 = 0)")
    qgi = (abs(bias_pct) / 1.65) / denominator
    qgi = round(qgi, 3)

    if qgi < 0.8:
        label   = "Precision-limited"
        color   = "#6366f1"
        action  = "CV dominates total error. Investigate instrument precision, reagent lot consistency, and pipetting reproducibility."
    elif qgi <= 1.2:
        label   = "Mixed"
        color   = "#f59e0b"
        action  = "Bias and imprecision contribute roughly equally. Review both calibration accuracy and precision sources."
    else:
        label   = "Accuracy-limited"
        color   = "#ef4444"
        action  = "Bias dominates total error. Investigate calibration, reagent bias, matrix effects, and EQA performance."

    return {
        "qgi":    qgi,
        "label":  label,
        "color":  color,
        "action": action,
    }


@dataclass
class SigmaResult:
    analyte: str
    department: str
    tea: float
    bias_pct: float
    cv_pct: float
    sigma: float
    grade: str
    grade_color: str
    qc_rules: list[dict]
    interpretation: str
    tea_source: str = ""
    qgi: float = 0.0
    qgi_label: str = ""
    qgi_color: str = ""
    qgi_action: str = ""


# Each rule carries both a Unicode display form and a plain-ASCII form for PDF/Excel.
_QC_RULES: dict[str, dict] = {
    "world_class": {
        "label": "World Class (σ ≥ 6)",
        "rules": [
            {"rule": "1₃ₛ",    "plain": "1:3s"},
        ],
        "n_controls": 2,
        "runs": 1,
        "description": "Simple 1:3s rule is sufficient. Minimum QC burden.",
    },
    "excellent": {
        "label": "Excellent (5 ≤ σ < 6)",
        "rules": [
            {"rule": "1₃ₛ",  "plain": "1:3s"},
            {"rule": "2₂ₛ",  "plain": "2:2s"},
            {"rule": "R₄ₛ",  "plain": "R:4s"},
        ],
        "n_controls": 2,
        "runs": 1,
        "description": "Multirule 1:3s/2:2s/R:4s with N=2. Low QC burden.",
    },
    "good": {
        "label": "Good (4 ≤ σ < 5)",
        "rules": [
            {"rule": "1₂.₅ₛ", "plain": "1:2.5s"},
            {"rule": "2₂ₛ",   "plain": "2:2s"},
            {"rule": "R₄ₛ",   "plain": "R:4s"},
            {"rule": "4₁ₛ",   "plain": "4:1s"},
            {"rule": "10ₓ",   "plain": "10x"},
        ],
        "n_controls": 4,
        "runs": 2,
        "description": "Westgard multirule with N=4. Moderate QC burden.",
    },
    "marginal": {
        "label": "Marginal (3 ≤ σ < 4)",
        "rules": [
            {"rule": "1₂ₛ",  "plain": "1:2s"},
            {"rule": "2₂ₛ",  "plain": "2:2s"},
            {"rule": "R₄ₛ",  "plain": "R:4s"},
            {"rule": "4₁ₛ",  "plain": "4:1s"},
            {"rule": "8ₓ",   "plain": "8x"},
            {"rule": "10ₓ",  "plain": "10x"},
        ],
        "n_controls": 6,
        "runs": 2,
        "description": "Tight multirule with N=6. High QC burden. Consider method improvement.",
    },
    "unacceptable": {
        "label": "Unacceptable (σ < 3)",
        "rules": [
            {"rule": "Method requires improvement", "plain": "Method requires improvement"},
        ],
        "n_controls": None,
        "runs": None,
        "description": "QC cannot compensate for poor method performance. Investigate and improve TEa, Bias, or CV.",
    },
}

_GRADE_BANDS = [
    (6.0, "World Class", "#10b981", "world_class"),
    (5.0, "Excellent",   "#3b82f6", "excellent"),
    (4.0, "Good",        "#f59e0b", "good"),
    (3.0, "Marginal",    "#f97316", "marginal"),
    (0.0, "Unacceptable","#ef4444", "unacceptable"),
]


def _classify(sigma: float) -> tuple[str, str, str]:
    for threshold, grade, color, band_key in _GRADE_BANDS:
        if sigma >= threshold:
            return grade, color, band_key
    return "Unacceptable", "#ef4444", "unacceptable"


def calculate_sigma(
    analyte: str,
    department: str,
    tea: float,
    bias_pct: float,
    cv_pct: float,
    tea_source: str = "",
) -> SigmaResult:
    if cv_pct <= 0:
        raise ValueError("CV% must be > 0")
    if tea <= 0:
        raise ValueError("TEa must be > 0")

    sigma = (tea - abs(bias_pct)) / cv_pct
    sigma = round(sigma, 2)

    grade, color, band_key = _classify(sigma)
    qc_data = _QC_RULES[band_key]

    rules_display = list(qc_data["rules"])  # already {"rule": ..., "plain": ...}

    interp_lines = [qc_data["description"]]
    if sigma >= 3:
        plain_names = ", ".join(r["plain"] for r in qc_data["rules"])
        interp_lines.append(
            f"Recommended: {plain_names}  |  "
            f"N controls = {qc_data['n_controls']}, "
            f"Runs/day = {qc_data['runs']}"
        )

    qgi_data = calculate_qgi(bias_pct, cv_pct, tea)

    return SigmaResult(
        analyte=analyte,
        department=department,
        tea=tea,
        bias_pct=bias_pct,
        cv_pct=cv_pct,
        sigma=sigma,
        grade=grade,
        grade_color=color,
        qc_rules=rules_display,
        interpretation=" ".join(interp_lines),
        tea_source=tea_source,
        qgi=qgi_data["qgi"],
        qgi_label=qgi_data["label"],
        qgi_color=qgi_data["color"],
        qgi_action=qgi_data["action"],
    )


def opspecs_chart_data(tea: float, cv_range: tuple[float, float] = (0.5, 15.0)) -> dict:
    """
    Returns OPSpecs (Operating Specifications) chart data.
    Lines represent Bias = TEa - σ×CV for σ = 2,3,4,5,6.
    X-axis: CV%, Y-axis: Bias%.
    """
    import numpy as np

    cv_vals = list(np.linspace(cv_range[0], cv_range[1], 200))
    sigma_levels = [6, 5, 4, 3, 2]
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"]
    lines = []
    for sigma, color in zip(sigma_levels, colors):
        bias_vals = [max(0.0, tea - sigma * cv) for cv in cv_vals]
        # Clip where bias would be >= tea (invalid region)
        points = [(round(cv, 3), round(b, 3)) for cv, b in zip(cv_vals, bias_vals) if b >= 0]
        lines.append({
            "sigma": sigma,
            "color": color,
            "cv": [p[0] for p in points],
            "bias": [p[1] for p in points],
            "label": f"σ = {sigma}",
        })
    return {"tea": tea, "lines": lines}
