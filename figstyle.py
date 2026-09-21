"""Figure style for the WES pilot (DESIGN 8): Times, >= 8 pt, colour-blind safe, vector output."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from wes.decisions import ARM_LABELS  # noqa: E402

logger = logging.getLogger(__name__)

#: Okabe-Ito qualitative palette (colour-blind safe), one entry per arm.
PALETTE: tuple[str, ...] = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#000000")
MARKERS: tuple[str, ...] = ("o", "s", "^", "D", "v")
LINESTYLES: tuple[str, ...] = ("-", "--", "-", "--", ":")


def apply_style() -> None:
    """Install the publication rcParams used by every figure in this project."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.5,
            "lines.linewidth": 1.2,
            "lines.markersize": 4,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
        }
    )


def arm_style(index: int) -> dict[str, object]:
    """Colour and hollow marker for one arm index.

    Markers are drawn unfilled so that arms whose values coincide exactly stay
    visible on top of one another.
    """
    return {
        "color": PALETTE[index % len(PALETTE)],
        "marker": MARKERS[index % len(MARKERS)],
        "markerfacecolor": "none",
        "markeredgewidth": 1.0,
    }


def arm_line_style(index: int) -> dict[str, object]:
    """Colour, hollow marker and a distinct dash pattern for one arm index."""
    return {**arm_style(index), "linestyle": LINESTYLES[index % len(LINESTYLES)]}


def save(fig, stem: Path) -> tuple[Path, Path]:
    """Write the figure as a vector PDF plus a PNG preview and close it."""
    pdf, png = stem.with_suffix(".pdf"), stem.with_suffix(".png")
    fig.savefig(pdf)
    fig.savefig(png)
    plt.close(fig)
    logger.info("wrote %s and %s", pdf.name, png.name)
    return pdf, png


__all__ = [
    "ARM_LABELS",
    "LINESTYLES",
    "MARKERS",
    "PALETTE",
    "apply_style",
    "arm_line_style",
    "arm_style",
    "save",
]
