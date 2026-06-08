"""
OPSpecs chart generator (server-side, matplotlib).

Generates a Normalized OPSpecs chart so all analytes — regardless of
their individual TEa — can be plotted on the same axes:

  Normalized CV   (x) = CV%   / TEa × 100   [% of TEa used by imprecision]
  Normalized Bias (y) = Bias% / TEa × 100   [% of TEa used by inaccuracy]

Sigma lines in normalized space:  y = 100 − σ × x
The "acceptable" region is below the σ = 3 line.
"""

from __future__ import annotations
import io
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


_SIGMA_PALETTE = {
    6: ("#10b981", "σ = 6  (World Class)"),
    5: ("#3b82f6", "σ = 5  (Excellent)"),
    4: ("#f59e0b", "σ = 4  (Good)"),
    3: ("#f97316", "σ = 3  (Marginal)"),
    2: ("#ef4444", "σ = 2  (Unacceptable)"),
}

_GRADE_COLORS = {
    "World Class":   "#10b981",
    "Excellent":     "#3b82f6",
    "Good":          "#f59e0b",
    "Marginal":      "#f97316",
    "Unacceptable":  "#ef4444",
}


def _sigma_color(grade: str) -> str:
    return _GRADE_COLORS.get(grade, "#888888")


def generate_opspecs_chart(
    results: list[dict[str, Any]],
    meta: dict[str, str] | None = None,
    dpi: int = 150,
    width_in: float = 10.0,
    height_in: float = 6.5,
) -> bytes:
    """
    Return a PNG of a Normalized OPSpecs chart with all analyte points plotted.
    Each point is colored by its Sigma grade.
    """
    meta = meta or {}

    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#f8f9fc")

    # ── Sigma lines ──────────────────────────────────────────────────────────
    x = np.linspace(0, 70, 500)
    for sigma in [6, 5, 4, 3, 2]:
        color, label = _SIGMA_PALETTE[sigma]
        y = 100 - sigma * x
        # Only draw where y >= 0
        mask = y >= 0
        ax.plot(x[mask], y[mask], color=color, linewidth=2.0,
                label=label, zorder=3)

    # Fill region below σ=6 line (world-class zone)
    y6 = np.clip(100 - 6 * x, 0, None)
    ax.fill_between(x, 0, y6, alpha=0.06, color="#10b981", zorder=1)

    # ── Analyte points ───────────────────────────────────────────────────────
    labeled_points: list[tuple[float, float, str, str]] = []
    for r in results:
        tea  = r.get("tea", 0)
        bias = abs(r.get("bias_pct", 0))
        cv   = r.get("cv_pct", 0)
        if not tea or not cv:
            continue
        nx = cv   / tea * 100
        ny = bias / tea * 100
        color = _sigma_color(r.get("grade", ""))
        sigma = r.get("sigma", 0)
        ax.scatter(nx, ny, color=color, s=90, zorder=5,
                   edgecolors="white", linewidths=1.2)
        labeled_points.append((nx, ny, r.get("analyte", ""), color))

    # ── Analyte labels (with simple overlap avoidance) ───────────────────────
    for nx, ny, name, color in labeled_points:
        ax.annotate(
            name,
            xy=(nx, ny),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=7,
            color=color,
            fontweight="bold",
            clip_on=True,
        )

    # ── Reference lines at 33% of TEa ────────────────────────────────────────
    ax.axvline(33.33, color="#cccccc", linewidth=0.8, linestyle="--", zorder=2)
    ax.axhline(33.33, color="#cccccc", linewidth=0.8, linestyle="--", zorder=2)
    ax.text(33.5, ax.get_ylim()[1] * 0.97 if ax.get_ylim()[1] > 0 else 95,
            "33% TEa", fontsize=6.5, color="#aaaaaa", va="top")

    # ── Axes ─────────────────────────────────────────────────────────────────
    ax.set_xlim(0, 70)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Normalized Imprecision — CV% / TEa × 100  (%)", fontsize=10)
    ax.set_ylabel("Normalized Inaccuracy — Bias% / TEa × 100  (%)", fontsize=10)

    lab = meta.get("lab", "")
    analyzer = meta.get("analyzer", "")
    period   = meta.get("period", "")
    subtitle_parts = [p for p in [lab, analyzer, period] if p]
    subtitle = "  |  ".join(subtitle_parts)

    title = "Normalized OPSpecs Chart — All Analytes"
    ax.set_title(title + (f"\n{subtitle}" if subtitle else ""),
                 fontsize=12, fontweight="bold", pad=10)

    ax.grid(color="#e0e4ef", linewidth=0.6, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#cccccc")

    # ── Legend ───────────────────────────────────────────────────────────────
    sigma_handles = [
        mpatches.Patch(color=c, label=lbl)
        for sigma, (c, lbl) in _SIGMA_PALETTE.items()
    ]
    legend = ax.legend(
        handles=sigma_handles,
        loc="upper right",
        fontsize=8,
        framealpha=0.9,
        edgecolor="#dddddd",
        fancybox=True,
    )

    # ── Footer note ──────────────────────────────────────────────────────────
    fig.text(
        0.5, 0.01,
        "Formula: σ = (TEa − |Bias%|) / CV%   |   "
        "Normalized axes: each axis expressed as % of TEa   |   "
        "Source: Westgard QC (westgard.com)",
        ha="center", va="bottom", fontsize=7, color="#888888",
    )

    plt.tight_layout(rect=[0, 0.03, 1, 1])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()
