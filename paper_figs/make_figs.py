"""Build Fig. 4 (``fig:reach``), Fig. 5 (``fig:cost``) and Table I of the article.

Fig. 4 plots attack-attributable success per targeted slot against attacker
reach at Delta = 10 dB, one panel per radio-map error level (sigma_map = 2 and
4 dB), with each arm's Delta = 0 null drawn as a thin dotted rule in its own
colour, and a third panel with the boundary of the anchored check: the
null-corrected ratio of the checked arm to the vote-only arm at full reach over
the falsification magnitude, one curve per map error level, with each level's
calibrated map-check threshold marked on the axis.  Fig. 5 puts the harm of the
defence in one column at sigma_map = 2 dB: wrong handovers per handover clean
and under attack, and missed handovers per oracle handover with no attacker.
Table I is written as a LaTeX fragment whose data-derived cells come from the
same run tables.

Every plotted value is derived from ``data/b2/runs.csv`` and, for the
parameter-diversity and map-veto rows, ``data/diag_param/runs.csv`` and
``data/diag_veto/runs.csv``; nothing is typed in.  After drawing,
:mod:`figcheck` reads the numbers back out of the artists and prints them beside
an independent recomputation, so a mismatch between what was computed and what
was drawn shows up as a non-zero discrepancy.

Usage:
    uv run python paper_figs/make_figs.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Final

import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, MaxNLocator

import figcheck
import figdata
import figspecs
import figstyle

logger = logging.getLogger("wes.figs")

OUT_DIR: Final[Path] = Path(__file__).resolve().parent

#: Fig. 4 geometry.  Double column: two reach panels and the boundary panel.
FIG4_SIZE: Final[tuple[float, float]] = (figstyle.COL_DOUBLE, 2.75)
#: Fig. 5 geometry.  Single column, two harm panels side by side.
FIG5_SIZE: Final[tuple[float, float]] = (figstyle.COL_SINGLE, 2.70)

#: Horizontal offset of the clean and attacked markers of Fig. 5 panel (a).
PAIR_OFFSET: Final[float] = 0.16
#: Horizontal offset of the three map-error levels in Fig. 5 panel (b).
SIGMA_OFFSET: Final[float] = 0.24

#: In-figure word budgets fixed by the figure specification.
FIG4_WORD_BUDGET: Final[int] = 45
FIG5_WORD_BUDGET: Final[int] = 30

TABLE1_PATH: Final[Path] = OUT_DIR / "table1.tex"


# --------------------------------------------------------------------------- #
# Fig. 4
# --------------------------------------------------------------------------- #
def _draw_reach_curve(
    ax: Axes, frame, series: figspecs.Series, sigma_map: float
) -> tuple[list[figcheck.Plotted], list[float]]:
    """Draw one arm's reach sweep and its null, returning values and extent."""
    means: list[float] = []
    halves: list[float] = []
    for rho in figdata.RHO_GRID:
        interval = figdata.cell_interval(
            frame, series.arm, figdata.SUCCESS, sigma_map, figdata.DELTA_ATTACK, rho
        )
        means.append(interval.mean)
        halves.append(interval.half)
    container = ax.errorbar(
        list(figdata.RHO_GRID),
        means,
        yerr=halves,
        label=series.label,
        color=series.colour,
        ecolor=to_rgba(series.colour, 0.55),
        marker=series.marker,
        linestyle=series.linestyle,
        markerfacecolor="none",
        markeredgewidth=0.9,
        capsize=1.4,
        elinewidth=0.6,
    )
    _, drawn_y, drawn_half = figcheck.errorbar_values(container, along="y")

    null = figdata.cell_interval(
        frame, series.arm, figdata.SUCCESS, sigma_map, figdata.DELTA_NULL, figdata.RHO_NULL
    )
    line = ax.axhline(
        null.mean,
        color=series.colour,
        linestyle=figstyle.NULL_LINESTYLE,
        linewidth=figstyle.NULL_LINEWIDTH,
        zorder=1,
    )

    values: list[figcheck.Plotted] = [
        figcheck.Plotted(
            "fig4",
            series.key,
            f"{sigma_map:.0f}|{rho:.1f}",
            "success",
            float(y_val),
            float(half),
        )
        for rho, y_val, half in zip(figdata.RHO_GRID, drawn_y, drawn_half, strict=True)
    ]
    values.append(
        figcheck.Plotted(
            "fig4",
            series.key,
            f"{sigma_map:.0f}|null",
            "null",
            float(line.get_ydata()[0]),
            0.0,
        )
    )
    extent = [
        float(np.min(drawn_y - drawn_half)),
        float(np.max(drawn_y + drawn_half)),
        float(null.mean),
    ]
    return values, extent


def _draw_boundary_panel(ax: Axes, frame) -> tuple[list[figcheck.Plotted], list[str]]:
    """Draw Fig. 4(c): checked over vote-only, null-corrected, against Delta."""
    drawn: list[figcheck.Plotted] = []
    bounds: list[float] = []
    for series in figspecs.BOUNDARY_SERIES:
        ratios = [
            figdata.corrected_ratio(frame, series.sigma_map, delta, figdata.RHO_ATTACK)
            for delta in figdata.DELTA_GRID
        ]
        (line,) = ax.plot(
            list(figdata.DELTA_GRID),
            ratios,
            label=series.label,
            color=series.colour,
            marker=series.marker,
            linestyle=series.linestyle,
            markerfacecolor="none",
            markeredgewidth=0.9,
        )
        drawn.extend(
            figcheck.Plotted("fig4", series.key, f"{delta:.0f}", "ratio", float(y_val), 0.0)
            for delta, y_val in zip(figdata.DELTA_GRID, line.get_ydata(), strict=True)
        )
        bound = figdata.map_bound(frame, series.sigma_map)
        (tick,) = ax.plot(
            [bound],
            [0.0],
            marker="|",
            markersize=9,
            markeredgewidth=1.3,
            color=series.colour,
            linestyle="none",
            clip_on=False,
            zorder=4,
        )
        drawn.append(
            figcheck.Plotted("fig4", series.key, "-", "bound", float(tick.get_xdata()[0]), 0.0)
        )
        bounds.append(bound)

    # Room to the right of the last falsification for the legend and the 6 dB bound.
    ax.set_xlim(4.5, 21.5)
    ax.set_ylim(0.0, 1.05)
    ax.xaxis.set_major_locator(FixedLocator(list(figdata.DELTA_GRID)))
    ax.yaxis.set_major_locator(FixedLocator([0.0, 0.5, 1.0]))
    ax.set_xlabel(figspecs.FIG4_BOUNDARY_X_LABEL, fontsize=9, labelpad=2.0)
    ax.set_ylabel(figspecs.FIG4_BOUNDARY_Y_LABEL, fontsize=9, labelpad=2.5)
    label = figspecs.PANEL_LABELS[2]
    # Lower left: the top left corner holds the 6 dB curve's first marker.
    ax.text(0.04, 0.05, label, transform=ax.transAxes, fontsize=9, va="bottom", ha="left")
    legend = ax.legend(
        loc="center right",
        title=figspecs.FIG4_SIGMA_TITLE,
        fontsize=8,
        title_fontsize=8,
        handlelength=2.2,
        borderaxespad=0.3,
        labelspacing=0.25,
    )
    legend.get_title().set_color(figstyle.NOTE_COLOUR)
    _ = bounds
    texts = [
        label,
        figspecs.FIG4_BOUNDARY_X_LABEL,
        figspecs.FIG4_BOUNDARY_Y_LABEL,
        figspecs.FIG4_SIGMA_TITLE,
        *[series.label for series in figspecs.BOUNDARY_SERIES],
    ]
    return drawn, texts


def build_fig4(runs: figdata.RunTable) -> tuple[Figure, list[figcheck.Plotted], list[str]]:
    """Draw Fig. 4 and return it with the values drawn and the text placed."""
    fig = Figure(figsize=FIG4_SIZE)
    grid = fig.add_gridspec(
        1,
        3,
        wspace=0.32,
        left=0.062,
        right=0.995,
        top=0.965,
        bottom=0.300,
        width_ratios=[1.0, 1.0, 0.95],
    )
    axes = [fig.add_subplot(grid[0, col]) for col in range(3)]

    drawn: list[figcheck.Plotted] = []
    extent: list[float] = []
    nulls: dict[float, list[float]] = {}
    lowest_curve: dict[float, float] = {}
    for ax, sigma_map in zip(axes[:2], figdata.SIGMA_PANELS, strict=True):
        for series in figspecs.SERIES:
            values, bounds = _draw_reach_curve(ax, runs.frame, series, sigma_map)
            drawn.extend(values)
            extent.extend(bounds)
            nulls.setdefault(sigma_map, []).append(
                next(v.value for v in values if v.quantity == "null")
            )
            lowest_curve[sigma_map] = min(
                lowest_curve.get(sigma_map, float("inf")),
                min(v.value for v in values if v.quantity == "success"),
            )

    low, high = min(extent), max(extent)
    texts: list[str] = []
    for col, (ax, sigma_map) in enumerate(zip(axes[:2], figdata.SIGMA_PANELS, strict=True)):
        ax.set_yscale("log")
        ax.set_ylim(low / 1.25, high * 2.0)
        ax.set_xlim(-0.08, 1.08)
        ax.xaxis.set_major_locator(FixedLocator(list(figdata.RHO_GRID)))
        ax.tick_params(axis="y", which="minor", length=1.4, width=0.5)
        label = figspecs.sigma_panel_label(col, sigma_map)
        ax.text(0.018, 0.965, label, transform=ax.transAxes, fontsize=9, va="top", ha="left")
        texts.append(label)
        if col == 1:
            ax.tick_params(labelleft=False)
        ax.set_xlabel(figspecs.FIG4_X_LABEL, fontsize=9, labelpad=2.0)
    texts.append(figspecs.FIG4_X_LABEL)

    # The null label sits in the gap above the dotted band and a leader line
    # ties it to the band, so it cannot be read as naming the nearest curve.
    sigma_a = figdata.SIGMA_PANELS[0]
    top_null = max(nulls[sigma_a])
    midpoint = float(np.sqrt(top_null * lowest_curve[sigma_a]))
    axes[0].annotate(
        figspecs.FIG4_NULL_LABEL,
        xy=(0.78, top_null),
        xytext=(0.52, midpoint),
        fontsize=8,
        color=figstyle.NOTE_COLOUR,
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "-", "color": figstyle.NOTE_COLOUR, "linewidth": 0.6,
                    "shrinkA": 0.0, "shrinkB": 1.0},
    )
    texts.append(figspecs.FIG4_NULL_LABEL)
    axes[0].set_ylabel(figspecs.FIG4_Y_LABEL, fontsize=9, labelpad=2.5)
    texts.append(figspecs.FIG4_Y_LABEL)

    boundary_drawn, boundary_texts = _draw_boundary_panel(axes[2], runs.frame)
    drawn.extend(boundary_drawn)
    texts.extend(boundary_texts)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.365, 0.128),
        handlelength=2.9,
        columnspacing=1.2,
        frameon=False,
    )
    texts.extend(labels)

    return fig, drawn, texts


# --------------------------------------------------------------------------- #
# Fig. 5
# --------------------------------------------------------------------------- #
def _draw_level_panel(ax: Axes, frame, panel: figspecs.Panel) -> list[figcheck.Plotted]:
    """Draw one arm-indexed panel of levels, clean and optionally under attack."""
    drawn: list[figcheck.Plotted] = []
    settings = [("clean", figdata.DELTA_NULL, figdata.RHO_NULL, False, figdata.SIGMA_REF, 0.0, 4.4)]
    if panel.attacked_too:
        settings = [
            ("clean", figdata.DELTA_NULL, figdata.RHO_NULL, False, figdata.SIGMA_REF,
             -PAIR_OFFSET, 4.4),
            ("attacked", figdata.DELTA_ATTACK, figdata.RHO_ATTACK, True, figdata.SIGMA_REF,
             PAIR_OFFSET, 4.4),
        ]
    if panel.sigma_levels:
        settings = [
            (f"clean|{sigma_map:.0f}", figdata.DELTA_NULL, figdata.RHO_NULL, False, sigma_map,
             offset, size)
            for sigma_map, offset, size in zip(
                figdata.SIGMA_GRID, (-SIGMA_OFFSET, 0.0, SIGMA_OFFSET), (3.2, 4.4, 5.6),
                strict=True,
            )
        ]
    for position, series in enumerate(figspecs.SERIES):
        for quantity, delta, rho, filled, sigma_map, offset, size in settings:
            interval = figdata.cell_interval(frame, series.arm, panel.column, sigma_map, delta, rho)
            container = ax.errorbar(
                [position + offset],
                [interval.mean],
                yerr=[interval.half],
                color=series.colour,
                ecolor=to_rgba(series.colour, 0.6),
                marker=series.marker,
                markerfacecolor=series.colour if filled else "none",
                markeredgewidth=0.9,
                markersize=size,
                linestyle="none",
                capsize=1.6,
                elinewidth=0.7,
            )
            _, values, halves = figcheck.errorbar_values(container, along="y")
            drawn.append(
                figcheck.Plotted(
                    "fig5", series.key, panel.key, quantity, float(values[0]), float(halves[0])
                )
            )
    return drawn


def build_fig5(runs: figdata.RunTable) -> tuple[Figure, list[figcheck.Plotted], list[str]]:
    """Draw Fig. 5 and return it with the values drawn and the text placed."""
    fig = Figure(figsize=FIG5_SIZE)
    grid = fig.add_gridspec(
        1, 2, wspace=0.55, left=0.135, right=0.985, top=0.910, bottom=0.335
    )
    axes = [fig.add_subplot(grid[0, col]) for col in range(2)]

    drawn: list[figcheck.Plotted] = []
    texts: list[str] = []
    for col, (ax, panel) in enumerate(zip(axes, figspecs.PANELS, strict=True)):
        drawn.extend(_draw_level_panel(ax, runs.frame, panel))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10]))
        ax.set_ylim(bottom=0.0)
        if panel.key == "wrong_ho":
            ax.set_ylim(0.0, 0.78)
        ax.set_xlim(-0.62, len(figspecs.SERIES) - 0.38)
        ax.set_xticks(list(range(len(figspecs.SERIES))))
        ax.set_xticklabels([])
        ax.tick_params(bottom=False)
        if panel.sigma_levels:
            offsets = (-SIGMA_OFFSET, 0.0, SIGMA_OFFSET)
            positions = range(len(figspecs.SERIES))
            ax.set_xticks(
                [position + offset for position in positions for offset in offsets],
                minor=True,
            )
            ax.set_xticklabels(
                [f"{sigma_map:.0f}" for _ in figspecs.SERIES for sigma_map in figdata.SIGMA_GRID],
                minor=True,
                fontsize=8,
            )
            ax.tick_params(axis="x", which="minor", bottom=True, length=1.5, pad=1.5)
            ax.set_xlabel(figspecs.FIG5_SIGMA_LABEL, fontsize=9, labelpad=1.5)
            texts.append(figspecs.FIG5_SIGMA_LABEL)
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", alpha=0.25)
        ax.set_ylabel(panel.label, fontsize=9, labelpad=2.5)
        label = figspecs.PANEL_LABELS[col]
        ax.text(0.03, 0.965, label, transform=ax.transAxes, fontsize=9, va="top", ha="left")
        texts.append(label)
        texts.append(panel.label)

    key_handles = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            color="0.30",
            markerfacecolor="none" if hollow else "0.30",
            markeredgewidth=0.9,
            markersize=4.4,
        )
        for hollow in (True, False)
    ]
    key_labels = [figspecs.FIG5_CLEAN_LABEL, figspecs.FIG5_ATTACKED_LABEL]
    axes[0].legend(key_handles, key_labels, loc="upper right", fontsize=8, borderaxespad=0.2)
    texts.extend(key_labels)

    handles = [
        Line2D(
            [],
            [],
            marker=series.marker,
            linestyle="none",
            color=series.colour,
            markerfacecolor="none",
            markeredgewidth=0.9,
            markersize=4.4,
        )
        for series in figspecs.SERIES
    ]
    labels = [series.label for series in figspecs.SERIES]
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.56, 0.175),
        columnspacing=1.0,
        frameon=False,
    )
    texts.extend(labels)

    if figspecs.FIG5_NOTE:
        fig.text(
            0.985,
            0.012,
            figspecs.FIG5_NOTE,
            fontsize=8,
            color=figstyle.NOTE_COLOUR,
            ha="right",
            va="bottom",
        )
        texts.append(figspecs.FIG5_NOTE)
    return fig, drawn, texts


# --------------------------------------------------------------------------- #
# Table I
# --------------------------------------------------------------------------- #
def _false_exclusion_cell(frame, arm: str) -> float:
    """False exclusion on clean UEs with no attacker at the reference map error."""
    return figdata.cell_interval(
        frame, arm, figdata.FALSE_EXCLUSION, figdata.SIGMA_REF, figdata.DELTA_NULL, figdata.RHO_NULL
    ).mean


def build_table1(runs: figdata.RunTable, path: Path = TABLE1_PATH) -> list[figcheck.Plotted]:
    """Write Table I as a LaTeX fragment and return its data-derived cells.

    Raises:
        ValueError: If a row's declared voter list disagrees with the run table.
    """
    frame = runs.frame
    lines = [
        "% Table I -- arms compared in the case study.",
        f"% Generated by paper_figs/make_figs.py from data/{runs.run_dir.name}/runs.csv,",
        f"% data/{runs.diag_dir.name}/runs.csv (the parameter-diversity row) and",
        f"% data/{runs.veto_dir.name}/runs.csv (the map-veto row).",
        "% Voter counts, majority reachability, Xn bytes, rule evaluations and false",
        "% exclusion are read from the run tables; the voter and adjudication wording",
        "% follows DESIGN 3.3.",
        "\\begin{table*}[!t]",
        "  \\caption{Arms compared in the case study.}",
        "  \\label{tab:arms}",
        "  \\centering",
        "  \\scriptsize",
        "  \\setlength{\\tabcolsep}{5pt}",
        "  \\begin{tabular}{@{}lllcrrr@{}}",
        "    \\hline",
        "    Policy & Voters & Adjudication",
        "      & \\shortstack[c]{Majority reachable\\\\at $\\rho = 1$}",
        "      & \\shortstack[r]{Xn bytes\\\\per UE per s}",
        "      & \\shortstack[r]{Executors and checks\\\\per decision}",
        "      & \\shortstack[r]{False exclusion,\\\\no attacker} \\\\",
        "    \\hline",
    ]
    drawn: list[figcheck.Plotted] = []
    for row in figspecs.TABLE_ROWS:
        voters = figdata.constant(frame, row.arm, figdata.N_VOTERS)
        declared = figspecs.VOTER_COUNTS[row.key]
        if int(voters) != declared:
            raise ValueError(
                f"{row.key}: the table names {declared} voters, the run table records {voters:.0f}"
            )
        reachable = figdata.majority_reachable(frame, row.arm)
        xn = figdata.xn_bytes(frame, row.arm)
        compute = figdata.constant(frame, row.arm, figdata.COMPUTE)
        false_exclusion = _false_exclusion_cell(frame, row.arm)
        fe_text = "0" if false_exclusion == 0.0 else f"{false_exclusion:.4f}"
        lines.append(
            f"    {row.policy} & {row.voters} & {row.adjudication} & "
            f"{'Yes' if reachable else 'No'} & {xn:.0f} & {compute:.0f} & {fe_text} \\\\"
        )
        drawn.extend(
            [
                figcheck.Plotted("tab1", row.key, "-", "voters", float(voters), 0.0),
                figcheck.Plotted("tab1", row.key, "-", "reachable", float(reachable), 0.0),
                figcheck.Plotted("tab1", row.key, "-", "xn_bytes", float(xn), 0.0),
                figcheck.Plotted("tab1", row.key, "-", "compute", float(compute), 0.0),
                figcheck.Plotted("tab1", row.key, "-", "false_excl", float(false_exclusion), 0.0),
            ]
        )
    lines.extend(["    \\hline", "  \\end{tabular}", "\\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("wrote %s (%d rows)", path.name, len(figspecs.TABLE_ROWS))
    return drawn


def main() -> int:
    """Build both figures and Table I, then print the cross-check and word counts."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    figstyle.apply_style()
    figstyle.check_font_available()
    runs = figdata.load()
    logger.info("t(0.975, df = 9) = %.4f", figdata.t95(9))

    fig4, drawn4, texts4 = build_fig4(runs)
    figstyle.save(fig4, OUT_DIR / "fig4")
    fig5, drawn5, texts5 = build_fig5(runs)
    figstyle.save(fig5, OUT_DIR / "fig5")
    drawn_table = build_table1(runs)

    figcheck.report_paired_contrasts(runs)
    spread = figcheck.check_null_is_invariant_in_reach(runs.run_dir)
    worst = figcheck.cross_check(runs, drawn4 + drawn5 + drawn_table)
    count4 = figcheck.report_text_budget("Fig. 4", texts4, FIG4_WORD_BUDGET)
    count5 = figcheck.report_text_budget("Fig. 5", texts5, FIG5_WORD_BUDGET)
    logger.info("source: %s + %s + %s", runs.run_dir.name, runs.diag_dir.name, runs.veto_dir.name)
    over_budget = count4 > FIG4_WORD_BUDGET or count5 > FIG5_WORD_BUDGET
    return 0 if worst < 1e-9 and spread == 0.0 and not over_budget else 1


if __name__ == "__main__":
    sys.exit(main())
