"""Declarative content of Fig. 4, Fig. 5 and Table I.

Which arm, which design cell, which metric and which colour each curve, marker
and table cell is made of.  Keeping this apart from the drawing code lets the
cross-check in :mod:`figcheck` rebuild every plotted number from ``runs.csv``
without importing the plotting module.

The only strings here that are not read from the run table are the legend
labels fixed by the figure specification, the axis labels, and Table I's
``voters`` and ``adjudication`` cells, which describe the wiring of SPEC S6.2
and S7.  The voter *count* behind each ``voters`` cell is checked against the
run table's ``n_voting_channels`` in :mod:`figcheck`, so the description cannot
drift from the runs it labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import figdata
import figstyle

#: Arms compared in both figures, in the order the paper introduces them.
ARM_ORDER: Final[tuple[str, ...]] = ("single", "obs_dhr", "obs_dhr_phys", "cheap_phys")


@dataclass(frozen=True)
class Series:
    """One curve of Fig. 4(a)(b): an arm swept over attacker reach at one sigma_map."""

    key: str
    label: str
    arm: str
    colour: str
    marker: str
    linestyle: object


@dataclass(frozen=True)
class BoundarySeries:
    """One curve of Fig. 4(c): the checked-over-vote ratio at one sigma_map over Delta."""

    key: str
    label: str
    sigma_map: float
    colour: str
    marker: str
    linestyle: object


@dataclass(frozen=True)
class Panel:
    """One panel of Fig. 5: a metric column, the cell it is read at, an axis label."""

    key: str
    column: str
    label: str
    #: ``True`` when the panel draws a clean and an attacked marker per arm;
    #: ``False`` when it draws the clean level only.
    attacked_too: bool = False
    #: ``True`` when the clean level is drawn at every map error level, left to
    #: right, with growing marker size.
    sigma_levels: bool = False


@dataclass(frozen=True)
class TableRow:
    """One row of Table I."""

    key: str
    arm: str
    policy: str
    voters: str
    adjudication: str


SERIES: Final[tuple[Series, ...]] = tuple(
    Series(
        key=arm,
        label=figstyle.ARM_LABELS[arm],
        arm=arm,
        colour=figstyle.ARM_COLOURS[arm],
        marker=figstyle.ARM_MARKERS[arm],
        linestyle=figstyle.ARM_LINESTYLES[arm],
    )
    for arm in ARM_ORDER
)

BOUNDARY_SERIES: Final[tuple[BoundarySeries, ...]] = tuple(
    BoundarySeries(
        key=f"sigma{sigma_map:.0f}",
        label=f"{sigma_map:.0f} dB",
        sigma_map=sigma_map,
        colour=figstyle.SIGMA_COLOURS[sigma_map],
        marker=figstyle.SIGMA_MARKERS[sigma_map],
        linestyle=figstyle.SIGMA_LINESTYLES[sigma_map],
    )
    for sigma_map in figdata.SIGMA_GRID
)

PANELS: Final[tuple[Panel, ...]] = (
    Panel(
        key="wrong_ho",
        column=figdata.WRONG_HO,
        label="Wrong handovers / handover",
        attacked_too=True,
    ),
    Panel(
        key="missed_ho",
        column=figdata.MISSED_HO,
        label="Missed handovers / oracle handover",
        sigma_levels=True,
    ),
)

#: Table I, in the order the paper introduces the arms.  ``voters`` names the
#: channels of ``ARM_VOTERS``: C1 the UE report, N the assembled network view,
#: C4 the operator radio map.
TABLE_ROWS: Final[tuple[TableRow, ...]] = (
    TableRow("single", "single", "Single channel", "C1", "None"),
    # Three copies of the A3 rule at different hysteresis and time-to-trigger
    # settings read the same UE report (SPEC S7).
    TableRow(
        "model_dhr_param",
        "model_dhr_param",
        "Parameter diversity",
        "C1 (three settings)",
        "Weighted majority",
    ),
    # Three decision families -- A3, load-aware and trend (SPEC S5.1) -- read
    # the same UE report, so the diversity is in the rule, not in its parameters.
    TableRow(
        "model_dhr3",
        "model_dhr3",
        "Rule diversity",
        "C1 (three rules)",
        "Weighted majority",
    ),
    TableRow("obs_dhr", "obs_dhr", "Observation vote", "C1, N, C4", "Majority"),
    TableRow(
        "obs_dhr_phys", "obs_dhr_phys", "Vote with checks", "C1, N, C4", "Exclude, then vote"
    ),
    TableRow(
        "obs_dhr_phys_dither",
        "obs_dhr_phys_dither",
        "Dithered thresholds",
        "C1, N, C4",
        "Dithered exclusion",
    ),
    TableRow(
        "cheap_phys",
        "cheap_phys",
        "Map veto",
        "C1, C4",
        "Unanimity, map if C1 excluded",
    ),
)

#: Number of channels each ``voters`` cell names, checked against the run table.
VOTER_COUNTS: Final[dict[str, int]] = {
    "single": 1,
    "model_dhr_param": 3,
    "model_dhr3": 3,
    "obs_dhr": 3,
    "obs_dhr_phys": 3,
    "obs_dhr_phys_dither": 3,
    "cheap_phys": 2,
}

#: Fig. 4 axis labels and in-figure notes.
FIG4_X_LABEL: Final[str] = r"Attacker reach $\rho$"
FIG4_Y_LABEL: Final[str] = "Attack-attributable success per slot"
FIG4_NULL_LABEL: Final[str] = r"$\Delta = 0$ null"
FIG4_SIGMA_TITLE: Final[str] = r"$\sigma_{\mathrm{map}}$"
FIG4_BOUNDARY_X_LABEL: Final[str] = r"Falsification $\Delta$ (dB)"
FIG4_BOUNDARY_Y_LABEL: Final[str] = "Checked over vote-only, null-corrected"

#: Fig. 5 in-figure notes and the key of its two-marker panel.
FIG5_CLEAN_LABEL: Final[str] = "Clean"
FIG5_ATTACKED_LABEL: Final[str] = "Attacked"
FIG5_NOTE: Final[str] = ""
#: Axis label under Fig. 5 panel (b), whose groups hold the three map-error levels.
FIG5_SIGMA_LABEL: Final[str] = r"$\sigma_{\mathrm{map}}$ (dB)"

PANEL_LABELS: Final[tuple[str, ...]] = ("(a)", "(b)", "(c)", "(d)")


def sigma_panel_label(index: int, sigma_map: float) -> str:
    """Panel label of Fig. 4(a)(b): the letter and the radio-map error it is cut at."""
    return rf"{PANEL_LABELS[index]} $\sigma_{{\mathrm{{map}}}} = {sigma_map:.0f}$ dB"


SERIES_BY_KEY: Final[dict[str, Series]] = {s.key: s for s in SERIES}
BOUNDARY_BY_KEY: Final[dict[str, BoundarySeries]] = {s.key: s for s in BOUNDARY_SERIES}
PANEL_BY_KEY: Final[dict[str, Panel]] = {p.key: p for p in PANELS}
TABLE_ROW_BY_KEY: Final[dict[str, TableRow]] = {r.key: r for r in TABLE_ROWS}

__all__ = [
    "ARM_ORDER",
    "BOUNDARY_BY_KEY",
    "BOUNDARY_SERIES",
    "FIG4_BOUNDARY_X_LABEL",
    "FIG4_BOUNDARY_Y_LABEL",
    "FIG4_SIGMA_TITLE",
    "FIG4_NULL_LABEL",
    "FIG4_X_LABEL",
    "FIG4_Y_LABEL",
    "FIG5_ATTACKED_LABEL",
    "FIG5_CLEAN_LABEL",
    "FIG5_NOTE",
    "FIG5_SIGMA_LABEL",
    "PANELS",
    "PANEL_BY_KEY",
    "PANEL_LABELS",
    "SERIES",
    "SERIES_BY_KEY",
    "TABLE_ROWS",
    "TABLE_ROW_BY_KEY",
    "VOTER_COUNTS",
    "BoundarySeries",
    "Panel",
    "Series",
    "TableRow",
    "sigma_panel_label",
]
