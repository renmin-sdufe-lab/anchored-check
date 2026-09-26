"""Publication style for the article figures.

Follows the same rules as the simulator's own ``figstyle.py`` (DESIGN 8: Times,
>= 8 pt, no in-figure titles, colour-blind safe, vector output) with two
adjustments made for the magazine page:

1. The four compared policies take four well-separated entries of the Okabe-Ito
   qualitative palette, and each also carries its own marker shape and dash
   pattern, so two arms whose values coincide -- ``obs_dhr_phys`` and
   ``cheap_phys`` sit within 1.3e-5 of one another at rho = 0 -- stay legible
   under any colour-vision deficiency and in greyscale print.  Markers are drawn
   hollow in Fig. 3 for the same reason.
2. ``savefig.bbox`` is ``None`` rather than ``"tight"``, so a figure declared at
   3.45 in or 7.1 in is written at exactly that width.  Margins are set by hand
   in :mod:`make_figs` instead.

The simulation package is read-only for this module; nothing here imports from
it and nothing here writes into it.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

#: IEEE single- and double-column text widths in inches.
COL_SINGLE: Final[float] = 3.45
COL_DOUBLE: Final[float] = 7.1

#: Smallest point size any text in these figures is allowed to take.
MIN_PT: Final[float] = 8.0

#: Okabe-Ito entries for the four arms the figures compare.  Blue, vermillion,
#: bluish green and reddish purple are the four best-separated members of the
#: palette; the two whose luminance is closest (vermillion and bluish green)
#: are additionally separated by marker shape and dash pattern.
ARM_COLOURS: Final[dict[str, str]] = {
    "single": "#0072B2",  # blue
    "obs_dhr": "#D55E00",  # vermillion
    "obs_dhr_phys": "#009E73",  # bluish green
    "cheap_phys": "#CC79A7",  # reddish purple
}
ARM_MARKERS: Final[dict[str, str]] = {
    "single": "o",
    "obs_dhr": "s",
    "obs_dhr_phys": "^",
    "cheap_phys": "D",
}
ARM_LINESTYLES: Final[dict[str, tuple[float, tuple[float, ...]] | str] ] = {
    "single": "-",
    "obs_dhr": (0, (5.0, 1.8)),
    "obs_dhr_phys": (0, (1.2, 1.2, 4.0, 1.2)),
    "cheap_phys": (0, (2.2, 1.4)),
}

#: Greys, markers and dashes for the three radio-map error levels of the
#: boundary panel of Fig. 3, which plots one ratio rather than several arms.
SIGMA_COLOURS: Final[dict[float, str]] = {2.0: "0.10", 4.0: "0.42", 6.0: "0.68"}
SIGMA_MARKERS: Final[dict[float, str]] = {2.0: "o", 4.0: "s", 6.0: "^"}
SIGMA_LINESTYLES: Final[dict[float, object]] = {
    2.0: "-",
    4.0: (0, (5.0, 1.8)),
    6.0: (0, (1.2, 1.2, 4.0, 1.2)),
}

#: Short legend labels fixed by the figure specification.
ARM_LABELS: Final[dict[str, str]] = {
    "single": "Single channel",
    "obs_dhr": "Observation vote",
    "obs_dhr_phys": "Vote with checks",
    "cheap_phys": "Map veto",
}

#: The Delta = 0 null is a property of the arm, not a series of its own, so it
#: is drawn in the arm's colour as a thin dotted rule rather than a fifth curve.
NULL_LINESTYLE: Final[tuple[float, tuple[float, ...]]] = (0, (1.0, 1.6))
NULL_LINEWIDTH: Final[float] = 0.7

#: Grey used for every explanatory note placed inside a figure.
NOTE_COLOUR: Final[str] = "0.35"


def apply_style() -> None:
    """Install the publication rcParams used by every article figure."""
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
            "axes.linewidth": 0.6,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.5,
            "lines.linewidth": 1.1,
            "lines.markersize": 3.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "legend.frameon": False,
            "legend.handlelength": 2.0,
            "legend.handletextpad": 0.5,
            "legend.columnspacing": 1.1,
            "legend.labelspacing": 0.35,
            "figure.dpi": 150,
            "savefig.dpi": 600,
            "savefig.bbox": None,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def check_font_available() -> str:
    """Return the file matplotlib will actually use for the serif family.

    Raises:
        RuntimeError: If the resolved face is a fallback rather than a Times cut.
    """
    from matplotlib import font_manager

    path = font_manager.findfont(font_manager.FontProperties(family="serif"))
    if "times" not in Path(path).name.lower():
        raise RuntimeError(f"Times not resolved for the serif family; got {path}")
    logger.info("serif family resolves to %s", path)
    return path


def save(fig: Figure, stem: Path) -> tuple[Path, Path]:
    """Write the figure as a vector PDF plus a PNG preview and close it."""
    pdf, png = stem.with_suffix(".pdf"), stem.with_suffix(".png")
    fig.savefig(pdf)
    fig.savefig(png)
    plt.close(fig)
    logger.info("wrote %s and %s", pdf.name, png.name)
    return pdf, png


__all__ = [
    "ARM_COLOURS",
    "ARM_LABELS",
    "ARM_LINESTYLES",
    "ARM_MARKERS",
    "COL_DOUBLE",
    "COL_SINGLE",
    "MIN_PT",
    "NOTE_COLOUR",
    "NULL_LINESTYLE",
    "NULL_LINEWIDTH",
    "apply_style",
    "check_font_available",
    "save",
]
