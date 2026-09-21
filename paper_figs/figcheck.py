"""Cross-check for the article figures and Table I.

Reads every number back out of the drawn matplotlib artists -- and every
data-derived cell back out of the generated LaTeX fragment -- then compares it
with a second, independent recomputation that re-reads ``runs.csv`` from disk
with plain pandas and numpy.  The two paths share no code beyond the column
names and the baseline filter, so a silent mismatch between what was computed
and what was drawn shows up as a non-zero discrepancy in the printed table.

``print`` is the deliverable here, not debugging output: the table is what a
reader checking the figures reads.  Progress and warnings still go through
``logging``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from matplotlib.container import BarContainer, ErrorbarContainer
from matplotlib.lines import Line2D

import figdata
import figspecs

logger = logging.getLogger(__name__)

_SEEDS_PER_CELL = figdata.SEEDS_PER_CELL


@dataclass(frozen=True)
class Plotted:
    """One value read back out of a drawn artist or a generated table cell."""

    figure: str
    series: str
    point: str
    quantity: str
    value: float
    half: float


def errorbar_values(
    container: ErrorbarContainer, along: Literal["x", "y"]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read drawn coordinates and interval half-widths back out of an artist.

    Args:
        container: The container returned by ``Axes.errorbar``.
        along: The axis the error bars run along.

    Returns:
        Positions on the other axis, values along ``along``, and half-widths.
    """
    line: Line2D = container.lines[0]
    x = np.asarray(line.get_xdata(), dtype=float)
    y = np.asarray(line.get_ydata(), dtype=float)
    segments = container.lines[2][0].get_segments()
    axis = 0 if along == "x" else 1
    halves = np.array([(seg[1][axis] - seg[0][axis]) / 2.0 for seg in segments], dtype=float)
    return (y, x, halves) if along == "x" else (x, y, halves)


def bar_heights(container: BarContainer) -> np.ndarray:
    """Read drawn bar heights back out of a ``Axes.bar`` container."""
    return np.array([patch.get_height() for patch in container.patches], dtype=float)


def _cell(runs_dir: Path, query: dict[str, object]) -> pd.DataFrame:
    """Re-read one design cell straight from a ``runs.csv`` on disk."""
    frame = pd.read_csv(runs_dir / "runs.csv")
    for key, value in (figdata.BASELINE | query).items():
        frame = frame[frame[key] == value]
    return frame.sort_values("seed")


def _interval_of(sample: np.ndarray) -> tuple[float, float]:
    """Mean and 95 % t half-width of a sample, recomputed from scratch."""
    n = int(sample.size)
    if n != _SEEDS_PER_CELL:
        logger.warning("expected %d seeds, found %d", _SEEDS_PER_CELL, n)
    half = figdata.T95_DF9 * float(np.std(sample, ddof=1)) / float(np.sqrt(n))
    return float(np.mean(sample)), half


def _corrected_mean(runs: figdata.RunTable, arm: str, sigma_map: float, delta: float,
                    rho: float) -> float:
    """Mean success less the arm's own Delta = 0 null, from the file on disk."""
    runs_dir = runs.dir_for(arm)
    attacked = _cell(runs_dir, {"arm": arm, "sigma_map": sigma_map, "delta": delta, "rho": rho})
    null = _cell(
        runs_dir,
        {"arm": arm, "sigma_map": sigma_map, "delta": figdata.DELTA_NULL, "rho": figdata.RHO_NULL},
    )
    return float(attacked[figdata.SUCCESS].mean() - null[figdata.SUCCESS].mean())


def _fig4_reference(item: Plotted, runs: figdata.RunTable) -> tuple[float, float]:
    """Independently recompute one Fig. 4 point."""
    if item.quantity in ("ratio", "bound"):
        boundary = figspecs.BOUNDARY_BY_KEY[item.series]
        if item.quantity == "bound":
            cell = _cell(
                runs.dir_for(figdata.CHECKED_ARM),
                {
                    "arm": figdata.CHECKED_ARM,
                    "sigma_map": boundary.sigma_map,
                    "delta": figdata.DELTA_ATTACK,
                    "rho": figdata.RHO_ATTACK,
                },
            )
            return float(cell[figdata.MAP_THRESHOLD].mean()), 0.0
        delta = float(item.point)
        checked = _corrected_mean(
            runs, figdata.CHECKED_ARM, boundary.sigma_map, delta, figdata.RHO_ATTACK
        )
        vote = _corrected_mean(
            runs, figdata.VOTE_ARM, boundary.sigma_map, delta, figdata.RHO_ATTACK
        )
        return checked / vote, 0.0
    series = figspecs.SERIES_BY_KEY[item.series]
    sigma_map = float(item.point.split("|")[0])
    if item.quantity == "null":
        query = {
            "arm": series.arm,
            "sigma_map": sigma_map,
            "delta": figdata.DELTA_NULL,
            "rho": figdata.RHO_NULL,
        }
    else:
        query = {
            "arm": series.arm,
            "sigma_map": sigma_map,
            "delta": figdata.DELTA_ATTACK,
            "rho": float(item.point.split("|")[1]),
        }
    sample = _cell(runs.dir_for(series.arm), query)[figdata.SUCCESS].to_numpy(dtype=float)
    mean, half = _interval_of(sample)
    return (mean, 0.0) if item.quantity == "null" else (mean, half)


def _fig5_reference(item: Plotted, runs: figdata.RunTable) -> tuple[float, float]:
    """Independently recompute one Fig. 5 marker."""
    panel = figspecs.PANEL_BY_KEY[item.point]
    arm = figspecs.SERIES_BY_KEY[item.series].arm
    attacked = item.quantity == "attacked"
    sigma_map = figdata.SIGMA_REF
    if "|" in item.quantity:
        sigma_map = float(item.quantity.split("|")[1])
    query = {
        "arm": arm,
        "sigma_map": sigma_map,
        "delta": figdata.DELTA_ATTACK if attacked else figdata.DELTA_NULL,
        "rho": figdata.RHO_ATTACK if attacked else figdata.RHO_NULL,
    }
    return _interval_of(_cell(runs.dir_for(arm), query)[panel.column].to_numpy(dtype=float))


def _table_reference(item: Plotted, runs: figdata.RunTable) -> tuple[float, float]:
    """Independently recompute one data-derived Table I cell."""
    arm = figspecs.TABLE_ROW_BY_KEY[item.series].arm
    runs_dir = runs.dir_for(arm)
    if item.quantity == "voters":
        values = np.unique(_cell(runs_dir, {"arm": arm})[figdata.N_VOTERS].to_numpy(dtype=float))
    elif item.quantity == "reachable":
        rows = _cell(runs_dir, {"arm": arm})
        rows = rows[rows["rho"] == rows["rho"].max()]
        values = np.unique(rows[figdata.MAJORITY_REACHABLE].to_numpy()).astype(float)
    elif item.quantity == "compute":
        values = np.unique(_cell(runs_dir, {"arm": arm})[figdata.COMPUTE].to_numpy(dtype=float))
    elif item.quantity == "false_excl":
        query = {
            "arm": arm,
            "sigma_map": figdata.SIGMA_REF,
            "delta": figdata.DELTA_NULL,
            "rho": figdata.RHO_NULL,
        }
        sample = _cell(runs_dir, query)[figdata.FALSE_EXCLUSION].to_numpy(dtype=float)
        return float(np.mean(sample)), 0.0
    else:
        own = np.unique(_cell(runs_dir, {"arm": arm})[figdata.OTA_BYTES].to_numpy(dtype=float))
        reference = np.unique(
            _cell(runs.run_dir, {"arm": figdata.COST_REFERENCE_ARM})[figdata.OTA_BYTES].to_numpy(
                dtype=float
            )
        )
        if own.size != 1 or reference.size != 1:
            raise ValueError(f"signalling bytes are not constant for {arm}")
        return float(own[0] - reference[0]), 0.0
    if values.size != 1:
        raise ValueError(f"{item.quantity} is not constant for {arm}: {values}")
    return float(values[0]), 0.0


def check_null_is_invariant_in_reach(runs_dir: Path) -> float:
    """Confirm that every plotted metric at Delta = 0 does not depend on rho.

    The figures read each arm's null at rho = 0.  That is only legitimate if the
    inert attacker leaves the run bit-identical across the reach sweep, so the
    claim is measured here rather than assumed.

    Returns:
        The largest absolute spread found across rho at Delta = 0.
    """
    columns = (figdata.SUCCESS, figdata.WRONG_HO, figdata.MISSED_HO, figdata.FALSE_EXCLUSION)
    worst = 0.0
    for arm in figspecs.ARM_ORDER:
        for sigma_map in figdata.SIGMA_PANELS:
            query = {"arm": arm, "sigma_map": sigma_map, "delta": figdata.DELTA_NULL}
            cell = _cell(runs_dir, query)
            table = cell.pivot_table(index="seed", columns="rho", values=list(columns))
            for column in columns:
                block = table[column].to_numpy(dtype=float)
                worst = max(worst, float(np.nanmax(np.abs(block - block[:, [0]]))))
    print(f"\nDelta = 0 spread across rho (must be 0): {worst:.3e}")  # noqa: T201
    if worst > 0.0:
        logger.error("the Delta = 0 null depends on rho; the figures read it at rho = 0 only")
    return worst


def cross_check(runs: figdata.RunTable, drawn: list[Plotted]) -> float:
    """Print every plotted number beside its independent recomputation.

    Args:
        runs: The loaded tables, for the source directories.
        drawn: Values read back out of the drawn artists and the table fragment.

    Returns:
        The largest absolute discrepancy found.
    """
    head = (
        f"{'figure':6} {'series':20} {'point':12} {'quantity':10} {'plotted':>11} "
        f"{'recomputed':>11} {'plot +-':>9} {'recomp +-':>9} {'|diff|':>9}"
    )
    print("\n" + head)  # noqa: T201
    print("-" * len(head))  # noqa: T201
    worst = 0.0
    for item in drawn:
        if item.figure == "fig4":
            ref, half_ref = _fig4_reference(item, runs)
        elif item.figure == "fig5":
            ref, half_ref = _fig5_reference(item, runs)
        else:
            ref, half_ref = _table_reference(item, runs)
        delta = max(abs(item.value - ref), abs(item.half - half_ref))
        worst = max(worst, delta)
        print(  # noqa: T201
            f"{item.figure:6} {item.series:20} {item.point:12} {item.quantity:10} "
            f"{item.value:11.5f} {ref:11.5f} {item.half:9.5f} {half_ref:9.5f} {delta:9.2e}"
        )
    print("-" * len(head))  # noqa: T201
    print(f"largest plotted-vs-recomputed discrepancy: {worst:.3e}")  # noqa: T201
    return worst


def report_paired_contrasts(runs: figdata.RunTable) -> None:
    """Print the paired per-seed contrasts the captions may quote.

    No panel of either figure plots a difference -- every one plots a level, so
    every interval drawn is a plain mean with its own 95 % t-interval.  The
    contrasts a caption states are differences, though, and a difference between
    two arms that share common random numbers must be taken per seed rather than
    read off two means.  They are printed here rather than drawn.
    """
    frame = runs.frame
    reference = figdata.COST_REFERENCE_ARM
    print("\npaired per-seed contrasts against the single-channel arm (not plotted)")  # noqa: T201
    print(f"  {'arm':14} {'quantity':28} {'paired difference':>22}")  # noqa: T201
    for series in figspecs.SERIES:
        if series.arm == reference:
            continue
        for metric, label, delta, rho in (
            (figdata.SUCCESS, "success, attacked", figdata.DELTA_ATTACK, figdata.RHO_ATTACK),
            (figdata.WRONG_HO, "wrong handovers, attacked", figdata.DELTA_ATTACK,
             figdata.RHO_ATTACK),
            (figdata.MISSED_HO, "missed handovers, clean", figdata.DELTA_NULL, figdata.RHO_NULL),
        ):
            treated = figdata.select(
                frame, series.arm, sigma_map=figdata.SIGMA_REF, delta=delta, rho=rho
            )
            control = figdata.select(
                frame, reference, sigma_map=figdata.SIGMA_REF, delta=delta, rho=rho
            )
            effect = figdata.paired_interval(treated, control, metric)
            print(f"  {series.arm:14} {label:28} {str(effect):>22}")  # noqa: T201


def report_text_budget(name: str, texts: list[str], limit: int) -> int:
    """Print the in-figure word count against its budget and return the count.

    Words are whitespace-separated tokens containing at least one letter, so
    tick labels and bare numerals do not count.  Mathtext markup is stripped
    first, so ``$\\Delta = 10$ dB`` counts the two words a reader sees.

    Args:
        name: Figure name for the printed line.
        texts: Every string placed inside the figure.
        limit: The word budget from the figure specification.

    Returns:
        The number of words counted.
    """
    rendered = [_strip_mathtext(text) for text in texts]
    words = [
        token
        for text in rendered
        for token in text.replace("\n", " ").split()
        if any(char.isalpha() for char in token)
    ]
    print(f"\n{name} in-figure text: {len(words)} words (limit {limit})")  # noqa: T201
    print("  " + " | ".join(text.replace("\n", " ") for text in rendered))  # noqa: T201
    if len(words) > limit:
        logger.error("%s exceeds its %d-word budget with %d words", name, limit, len(words))
    return len(words)


#: Mathtext commands replaced by the single symbol a reader sees, so the word
#: count is the reader's count and not LaTeX's.
_SYMBOLS: dict[str, str] = {
    r"\sigma": "σ",
    r"\Delta": "Δ",
    r"\rho": "ρ",
    r"\times": "×",
    r"\mathrm": "",
}


def _strip_mathtext(text: str) -> str:
    """Render a mathtext string the way a reader counting words would read it."""
    out = text
    for command, symbol in _SYMBOLS.items():
        out = out.replace(command, symbol)
    for character in "${}":
        out = out.replace(character, "")
    return " ".join(out.split())


__all__ = [
    "Plotted",
    "bar_heights",
    "check_null_is_invariant_in_reach",
    "cross_check",
    "errorbar_values",
    "report_paired_contrasts",
    "report_text_budget",
]
