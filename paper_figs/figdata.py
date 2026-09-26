"""Read-only access to the frozen run tables behind Fig. 3, Fig. 4 and Table I.

Every number the figures and the table show is derived here from ``runs.csv``.
Nothing is typed in and nothing is read out of a report.

The b2 sweep carries five blocks (main grid, ping-pong mode, sticky ramp, check
decomposition, no-persistence variant) in one table.  :data:`BASELINE` is the
cut the article reports from: the pre-registered trap attacker, no ramp, the
arm's own default check set, the 3-consecutive persistence rule and p = 0.2.
Every selection in this package goes through :func:`select`, so no figure can
silently read a diagnostic block.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

#: Package-relative anchors.  ``figdata.py`` lives in ``paper_figs``.
PAPER_FIGS_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = PAPER_FIGS_DIR.parent / "data"

#: Name of the frozen run directory the article reports from.
RUN_TAG: Final[str] = "b2"
#: The pre-registered diagnostic that adds the parameter-diversity arm
#: (PROTOCOL.md, row diag).
DIAG_TAG: Final[str] = "diag_param"
DIAG_ARM: Final[str] = "model_dhr_param"
#: The re-measured map-veto arm (PROTOCOL.md, row diag-veto): its rows replace
#: the ones the b2 sweep produced for that arm.
VETO_TAG: Final[str] = "diag_veto"
VETO_ARM: Final[str] = "cheap_phys"

#: The pre-registered cut of the sweep.  Applied to every selection.
BASELINE: Final[dict[str, object]] = {
    "mode": "trap",
    "ramp_slots": 1,
    "check_set": "default",
    "persistence_slots": 3,
    "p": 0.2,
}

#: Seeds per design cell; every cell of the main grid has exactly this many.
SEEDS_PER_CELL: Final[int] = 10

#: Two-sided 95 % Student-t quantile for df = 9 (10 seeds), as in ``stats.py``.
T95_DF9: Final[float] = 2.262

#: Metric columns used by the figures and the table.
SUCCESS: Final[str] = "attack_success_attr"
WRONG_HO: Final[str] = "wrong_handover_per_ho"
MISSED_HO: Final[str] = "missed_handover_rate"
FALSE_EXCLUSION: Final[str] = "false_exclusion_rate"
OTA_BYTES: Final[str] = "bytes_ota_per_ue_s"
RSRP_DEFICIT: Final[str] = "rsrp_deficit"
N_VOTERS: Final[str] = "n_voting_channels"
COMPUTE: Final[str] = "compute_per_decision"
MAP_THRESHOLD: Final[str] = "thr_map"
MAJORITY_REACHABLE: Final[str] = "majority_reachable"

#: The design points the two figures are cut at.
SIGMA_PANELS: Final[tuple[float, float]] = (2.0, 4.0)
#: The boundary panel: every map error level against every falsification.
SIGMA_GRID: Final[tuple[float, float, float]] = (2.0, 4.0, 6.0)
DELTA_GRID: Final[tuple[float, float, float]] = (6.0, 10.0, 15.0)
#: The two arms whose null-corrected ratio the boundary panel plots.
CHECKED_ARM: Final[str] = "obs_dhr_phys"
VOTE_ARM: Final[str] = "obs_dhr"
SIGMA_REF: Final[float] = 2.0
RHO_GRID: Final[tuple[float, float, float]] = (0.0, 0.5, 1.0)
DELTA_ATTACK: Final[float] = 10.0
DELTA_NULL: Final[float] = 0.0
RHO_ATTACK: Final[float] = 1.0
#: With no falsification the attacker is inert, so every metric at Delta = 0 is
#: bit-identical across rho (checked in :mod:`figcheck`).  rho = 0 is the cell
#: the null is read from, so the choice is stated once rather than per figure.
RHO_NULL: Final[float] = 0.0

#: The arm every cost is expressed relative to.
COST_REFERENCE_ARM: Final[str] = "single"


@dataclass(frozen=True)
class Interval:
    """A sample mean with the half-width of its 95 % t-interval."""

    mean: float
    half: float
    n: int

    @property
    def lo(self) -> float:
        """Lower confidence bound."""
        return self.mean - self.half

    @property
    def hi(self) -> float:
        """Upper confidence bound."""
        return self.mean + self.half

    def __str__(self) -> str:
        """Render as ``mean ± half``."""
        return f"{self.mean:+.5f} ± {self.half:.5f}"


@dataclass(frozen=True)
class RunTable:
    """The b2 run table, the diagnostic rows appended, and their directories."""

    frame: pd.DataFrame
    run_dir: Path
    diag_dir: Path
    veto_dir: Path

    def dir_for(self, arm: str) -> Path:
        """The output directory an arm's rows were read from."""
        if arm == DIAG_ARM:
            return self.diag_dir
        if arm == VETO_ARM:
            return self.veto_dir
        return self.run_dir


def t95(df: int) -> float:
    """Two-sided 95 % Student-t quantile for ``df`` degrees of freedom.

    Uses SciPy when it is installed so the constant is checked rather than
    trusted; falls back to the pre-registered df = 9 value otherwise.

    Args:
        df: Degrees of freedom.

    Returns:
        The quantile.

    Raises:
        ValueError: If ``df`` is not positive, or if SciPy contradicts the
            pre-registered df = 9 value.
    """
    if df <= 0:
        raise ValueError(f"degrees of freedom must be positive, got {df}")
    try:
        from scipy import stats

        exact = float(stats.t.ppf(0.975, df))
    except ImportError:
        if df != 9:
            raise
        logger.warning("SciPy absent; using the tabulated t = %.3f for df = 9", T95_DF9)
        return T95_DF9
    if df != 9:
        return exact
    if abs(exact - T95_DF9) > 5e-4:
        raise ValueError(f"t(0.975, 9) = {exact:.5f} contradicts the tabulated {T95_DF9}")
    # The pre-registered analysis rounds to three decimals; keep that so every
    # interval in the article is reproducible without SciPy.
    return T95_DF9


def mean_interval(values: np.ndarray) -> Interval:
    """Mean and 95 % t-interval half-width of one sample.

    Args:
        values: Finite sample values; NaNs are dropped.

    Returns:
        The interval.

    Raises:
        ValueError: If fewer than two values survive.
    """
    clean = np.asarray(values, dtype=float)
    clean = clean[~np.isnan(clean)]
    if clean.size < 2:
        raise ValueError(f"need at least two observations, got {clean.size}")
    sd = float(clean.std(ddof=1))
    n = int(clean.size)
    return Interval(float(clean.mean()), t95(n - 1) * sd / math.sqrt(n), n)


def frozen_run_dir(tag: str = RUN_TAG, data: Path = DATA_DIR) -> Path:
    """The frozen run directory named ``tag`` under ``data/``.

    Args:
        tag: Directory name under ``data/``: ``b2`` for the run the article
            reports, ``diag_param`` and ``diag_veto`` for the diagnostics.
        data: The shipped data directory.

    Returns:
        The directory holding ``runs.csv``.

    Raises:
        FileNotFoundError: If the directory or its run table is missing.
    """
    chosen = data / tag
    if not (chosen / "runs.csv").is_file():
        raise FileNotFoundError(f"no runs.csv under {chosen}")
    logger.info("%s -> %s", tag, chosen)
    return chosen


def load() -> RunTable:
    """Load the frozen b2 run table plus the two diagnostics' rows.

    Only the diagnostic arm is taken from the parameter-diversity run; its
    single-channel rows duplicate b2's bit for bit and would double every seed.
    Only the map-veto arm is taken from ``diag_veto``.

    Raises:
        ValueError: If any :data:`BASELINE` key is missing from a table.
    """
    run_dir = frozen_run_dir()
    frame = pd.read_csv(run_dir / "runs.csv")
    diag_dir = frozen_run_dir(DIAG_TAG)
    diag = pd.read_csv(diag_dir / "runs.csv")
    diag = diag[diag["arm"] == DIAG_ARM]
    veto_dir = frozen_run_dir(VETO_TAG)
    veto = pd.read_csv(veto_dir / "runs.csv")
    veto = veto[veto["arm"] == VETO_ARM]
    # The b2 rows of the veto arm ran a check the arm is not billed for
    # (DESIGN 4.4); the re-measured rows replace them.
    frame = frame[frame["arm"] != VETO_ARM]
    for path, table in ((run_dir, frame), (diag_dir, diag), (veto_dir, veto)):
        missing = [key for key in BASELINE if key not in table.columns]
        if missing:
            raise ValueError(f"{path/'runs.csv'} lacks the baseline columns {missing}")
    logger.info("%s: %d rows, %d columns", run_dir.name, len(frame), frame.shape[1])
    logger.info("%s: %d rows of %s", diag_dir.name, len(diag), DIAG_ARM)
    logger.info("%s: %d rows of %s", veto_dir.name, len(veto), VETO_ARM)
    frame = pd.concat([frame, diag, veto], ignore_index=True)
    return RunTable(frame=frame, run_dir=run_dir, diag_dir=diag_dir, veto_dir=veto_dir)


def baseline(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows of the pre-registered cut named by :data:`BASELINE`."""
    mask = pd.Series(True, index=frame.index)
    for key, value in BASELINE.items():
        mask &= frame[key] == value
    return frame[mask]


def select(
    frame: pd.DataFrame,
    arm: str,
    sigma_map: float | None = None,
    delta: float | None = None,
    rho: float | None = None,
) -> pd.DataFrame:
    """One cell of the pre-registered design, indexed by seed and sorted.

    Args:
        frame: The b2 run table.
        arm: Arm key, e.g. ``obs_dhr_phys``.
        sigma_map: Radio-map error standard deviation in dB, or ``None`` for all.
        delta: Falsification magnitude in dB, or ``None`` for all.
        rho: Attacker reach into the neighbour columns, or ``None`` for all.

    Returns:
        The matching rows, indexed by seed.

    Raises:
        ValueError: If the selection is empty.
    """
    sub = baseline(frame)
    sub = sub[sub["arm"] == arm]
    if sigma_map is not None:
        sub = sub[sub["sigma_map"] == sigma_map]
    if delta is not None:
        sub = sub[sub["delta"] == delta]
    if rho is not None:
        sub = sub[sub["rho"] == rho]
    if sub.empty:
        raise ValueError(
            f"empty selection: arm={arm} sigma_map={sigma_map} delta={delta} rho={rho}"
        )
    if len(sub) != SEEDS_PER_CELL and rho is not None and delta is not None:
        logger.warning(
            "arm=%s sigma_map=%s delta=%s rho=%s has %d rows, expected %d",
            arm,
            sigma_map,
            delta,
            rho,
            len(sub),
            SEEDS_PER_CELL,
        )
    return sub.set_index("seed").sort_index()


def cell_interval(
    frame: pd.DataFrame, arm: str, metric: str, sigma_map: float, delta: float, rho: float
) -> Interval:
    """Mean and 95 % t-interval of one metric in one design cell."""
    cell = select(frame, arm, sigma_map=sigma_map, delta=delta, rho=rho)
    return mean_interval(cell[metric].to_numpy(dtype=float))


def paired_interval(
    treatment: pd.DataFrame, baseline_cell: pd.DataFrame, metric: str, sign: float = 1.0
) -> Interval:
    """Per-seed paired difference ``sign * (treatment - baseline)`` of one metric.

    Args:
        treatment: Seed-indexed rows for the treated cell.
        baseline_cell: Seed-indexed rows for the reference cell.
        metric: Column to difference.
        sign: ``-1`` flips the metric.

    Returns:
        The paired interval over the shared seeds.

    Raises:
        ValueError: If the two cells share fewer than two seeds.
    """
    seeds = treatment.index.intersection(baseline_cell.index)
    if len(seeds) < 2:
        raise ValueError(f"only {len(seeds)} shared seeds for metric {metric}")
    treated = treatment.loc[seeds, metric].to_numpy(dtype=float)
    control = baseline_cell.loc[seeds, metric].to_numpy(dtype=float)
    return mean_interval(sign * (treated - control))


def constant(frame: pd.DataFrame, arm: str, column: str) -> float:
    """The single value ``column`` takes for ``arm`` over the whole baseline cut.

    Cost and wiring columns are properties of the arm, not of the run, so they
    must not vary with seed or design point.  This raises rather than averaging
    if they do.

    Raises:
        ValueError: If the column is not constant for the arm.
    """
    values = pd.unique(baseline(frame).loc[baseline(frame)["arm"] == arm, column])
    if len(values) != 1:
        raise ValueError(f"{column} is not constant for arm {arm}: {sorted(values.tolist())}")
    return float(values[0])


def flag(frame: pd.DataFrame, arm: str, column: str, rho: float) -> bool:
    """The single boolean ``column`` takes for ``arm`` at attacker reach ``rho``.

    Raises:
        ValueError: If the column is not constant in that slice.
    """
    sub = select(frame, arm, rho=rho)
    values = pd.unique(sub[column])
    if len(values) != 1:
        raise ValueError(f"{column} is not constant for arm {arm} at rho={rho}: {values}")
    return bool(values[0])


def majority_reachable(frame: pd.DataFrame, arm: str) -> bool:
    """Whether the attacker can hold a voting majority, read at the arm's largest reach.

    The flag is a design fact of the arm at a given reach.  Arms that only read
    the UE report carry it at every reach, so the diagnostic arm, run at
    rho = 0 only, is read there; every other arm is read at full reach.
    """
    rows = baseline(frame)
    rows = rows[rows["arm"] == arm]
    if rows.empty:
        raise ValueError(f"no baseline rows for arm {arm}")
    return flag(frame, arm, MAJORITY_REACHABLE, float(rows["rho"].max()))


def ota_ratio(frame: pd.DataFrame, arm: str) -> float:
    """Signalling bytes per UE per second, relative to the single-channel arm."""
    reference = constant(frame, COST_REFERENCE_ARM, OTA_BYTES)
    if reference <= 0.0:
        raise ValueError(f"non-positive reference cost {reference}")
    return constant(frame, arm, OTA_BYTES) / reference


def xn_bytes(frame: pd.DataFrame, arm: str) -> float:
    """Bytes per UE per second carried over Xn: the arm's signalling less the UE report.

    ``bytes_ota_per_ue_s`` sums every channel but the serving gNB's own
    measurement, so it holds the UE report (over the air) plus the neighbour
    reports (over Xn).  The single-channel arm carries the UE report alone.
    """
    return constant(frame, arm, OTA_BYTES) - constant(frame, COST_REFERENCE_ARM, OTA_BYTES)


def corrected_mean(frame: pd.DataFrame, arm: str, sigma_map: float, delta: float,
                   rho: float) -> float:
    """Mean attack-attributable rate less the arm's own Delta = 0 null (DESIGN 6.1)."""
    attacked = cell_interval(frame, arm, SUCCESS, sigma_map, delta, rho).mean
    null = cell_interval(frame, arm, SUCCESS, sigma_map, DELTA_NULL, RHO_NULL).mean
    return attacked - null


def corrected_ratio(frame: pd.DataFrame, sigma_map: float, delta: float, rho: float) -> float:
    """Null-corrected rate of the checked arm over that of the vote-only arm."""
    numerator = corrected_mean(frame, CHECKED_ARM, sigma_map, delta, rho)
    denominator = corrected_mean(frame, VOTE_ARM, sigma_map, delta, rho)
    if denominator <= 0.0:
        raise ValueError(
            f"vote-only arm at or below its null: sigma_map={sigma_map} delta={delta}"
        )
    return numerator / denominator


def map_bound(frame: pd.DataFrame, sigma_map: float) -> float:
    """Mean calibrated map-check threshold of the checked arm at one map error level."""
    cell = select(frame, CHECKED_ARM, sigma_map=sigma_map, delta=DELTA_ATTACK, rho=RHO_ATTACK)
    return float(cell[MAP_THRESHOLD].mean())


__all__ = [
    "BASELINE",
    "COST_REFERENCE_ARM",
    "DELTA_ATTACK",
    "DELTA_NULL",
    "FALSE_EXCLUSION",
    "MAJORITY_REACHABLE",
    "MISSED_HO",
    "N_VOTERS",
    "CHECKED_ARM",
    "COMPUTE",
    "DELTA_GRID",
    "DIAG_ARM",
    "DIAG_TAG",
    "VETO_ARM",
    "VETO_TAG",
    "MAP_THRESHOLD",
    "SIGMA_GRID",
    "VOTE_ARM",
    "OTA_BYTES",
    "DATA_DIR",
    "RHO_ATTACK",
    "RHO_GRID",
    "RHO_NULL",
    "RSRP_DEFICIT",
    "RUN_TAG",
    "SEEDS_PER_CELL",
    "SIGMA_PANELS",
    "SIGMA_REF",
    "SUCCESS",
    "T95_DF9",
    "WRONG_HO",
    "Interval",
    "RunTable",
    "baseline",
    "cell_interval",
    "constant",
    "flag",
    "load",
    "mean_interval",
    "frozen_run_dir",
    "ota_ratio",
    "corrected_mean",
    "corrected_ratio",
    "majority_reachable",
    "map_bound",
    "xn_bytes",
    "paired_interval",
    "select",
    "t95",
]
