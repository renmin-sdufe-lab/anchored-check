"""Shared constants and paired statistics for the pilot analysis (DESIGN section 6)."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

#: The pre-registered gate setting of PROTOCOL.md (p = 0.2, delta = 10, rho = 1,
#: sigma_map = 2 dB, step attacker, all checks, uniform persistence).
GATE: dict[str, Any] = {
    "p": 0.2,
    "delta": 10.0,
    "rho": 1.0,
    "sigma_map": 2.0,
    "mode": "trap",
    "check_set": "default",
    "z": 3.0,
    "ramp_slots": 1,
    "persistence_slots": 3,
}

#: The null control that accompanies every setting (DESIGN 6.1).
NULL: dict[str, Any] = {**GATE, "delta": 0.0}

#: DESIGN 6's primary security metric: attack-attributable success per targeted
#: slot, which is monotone in the falsification magnitude.
PRIMARY = "attack_success_attr"

#: The secondary metric reported beside it (DESIGN 6).
SECONDARY = "attack_success_opp"

METRICS: tuple[str, ...] = (
    "attack_success_attr",
    "attack_success_opp",
    "attack_success",
    "actionable_share",
    "false_exclusion_rate",
    "throughput",
)

METRIC_LABELS: dict[str, str] = {
    "attack_success_attr": "attack-attributable success / targeted slot",
    "attack_success_opp": "attack-attributable success / opportunity",
    "attack_success_opp_inst": "attack-attributable success / instant opportunity",
    "attack_success": "raw success / targeted slot",
    "actionable_share": "actionable share (with TTT)",
    "actionable_share_inst": "actionable share (instantaneous)",
    "detect_rate": "falsified-channel exclusion on targeted UEs",
    "detect_rate_actionable": "falsified-channel exclusion on actionable slots",
    "false_exclusion_rate": "false exclusion (clean UE-slots)",
    "false_exclusion_rate_ch": "false exclusion (clean channel-slots)",
    "fe_serving_reciprocity": "false exclusion, serving reciprocity",
    "fe_neighbour_reciprocity": "false exclusion, neighbour reciprocity",
    "fe_map": "false exclusion, map",
    "fe_rate": "false exclusion, rate",
    "wrong_handover_rate": "wrong handovers / UE-slot",
    "pingpong_rate": "ping-pongs / UE-slot",
    "wrong_handover_per_ho": "wrong handovers / handover",
    "pingpong_per_ho": "ping-pongs / handover",
    "handover_rate": "handovers / UE-slot",
    "missed_handover_rate": "missed handovers / oracle handover",
    "missed_handover_per_ue_slot": "missed handovers / UE-slot",
    "oracle_handover_rate": "oracle handovers / UE-slot",
    "rsrp_deficit": "RSRP deficit (dB)",
    "outage_share": "outage share",
    "wrong_cell_share": "wrong-cell share",
    "throughput": "throughput proxy",
    "bytes_per_ue_s": "measurement bytes (B/UE/s)",
    "bytes_ota_per_ue_s": "over-the-air bytes (B/UE/s)",
    "compute_per_decision": "compute units/decision",
    "fallback_rate": "trusted-channel fallback rate",
    "mean_voters": "voting channels",
    "thr_serving_reciprocity": "threshold, serving reciprocity (dB)",
    "thr_neighbour_reciprocity": "threshold, neighbour reciprocity (dB)",
    "thr_map": "threshold, map (dB)",
    "thr_rate": "threshold, rate (dB)",
    "sigma_map_hat": "calibrated sigma_map (dB)",
    "sigma_c1_hat": "calibrated sigma_C1 (dB)",
}

# Two-sided 95 % Student-t quantiles for df = 1..30; 1.96 beyond.
_T95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
    9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074,
    23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045,
    30: 2.042,
}


def t95(df: int) -> float:
    """Two-sided 95 % Student-t quantile for ``df`` degrees of freedom."""
    if df <= 0:
        return float("nan")
    return _T95.get(df, 1.96)


@dataclass(frozen=True)
class Interval:
    """A mean with the half-width of its 95 % t-interval."""

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

    def excludes_zero(self) -> bool:
        """Whether the interval lies wholly above or wholly below zero."""
        return bool((self.lo > 0.0) or (self.hi < 0.0))

    def __str__(self) -> str:
        """Render as ``mean ± half``."""
        if math.isnan(self.mean):
            return "n/a"
        return f"{self.mean:.4f} ± {self.half:.4f}"


def interval(values: np.ndarray) -> Interval:
    """Mean and 95 % t-interval half-width of a sample, ignoring ``nan``."""
    raw = np.asarray(values, dtype=float)
    clean = np.asarray([v for v in raw if not math.isnan(v)])
    n = clean.size
    if n < raw.size:  # never shrink n silently
        logger.warning("dropped %d nan of %d samples before the interval", raw.size - n,
                       raw.size)
    if n == 0:
        return Interval(float("nan"), float("nan"), 0)
    if n == 1:
        return Interval(float(clean[0]), 0.0, 1)
    sd = float(clean.std(ddof=1))
    return Interval(float(clean.mean()), t95(n - 1) * sd / math.sqrt(n), n)


def select(frame: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    """Rows matching every column/value pair, with float columns compared loosely.

    Raises:
        KeyError: If a filter names a column the frame does not have.  A
            silently ignored typo would widen the selection instead of failing,
            and every gate goes through this function.
    """
    missing = [c for c in filters if c not in frame.columns]
    if missing:
        raise KeyError(f"unknown filter column(s) {sorted(missing)}")
    mask = pd.Series(True, index=frame.index)
    for column, value in filters.items():
        if isinstance(value, float):
            mask &= np.isclose(frame[column].astype(float), value)
        else:
            mask &= frame[column] == value
    return frame[mask]


def cell(frame: pd.DataFrame, arm: str, metric: str, **filters: Any) -> Interval:
    """Mean and 95 % interval of one metric for one arm in one setting."""
    rows = select(frame, arm=arm, **filters)
    return interval(rows[metric].to_numpy(dtype=float))


def paired(frame: pd.DataFrame, arm_a: str, arm_b: str, metric: str,
           scale: float = 1.0, **filters: Any) -> Interval:
    """Paired 95 % interval of ``arm_a - scale * arm_b`` over the shared seeds.

    Args:
        frame: The ``runs.csv`` frame.
        arm_a: Left arm of the comparison.
        arm_b: Right arm of the comparison.
        metric: Column to compare.
        scale: Factor applied to ``arm_b``; ``0.2`` turns the difference into
            PROTOCOL.md's "arm 4 minus 0.2 x arm 1" boundary test.
        **filters: Setting columns to hold fixed.

    Returns:
        The paired interval; ``n = 0`` when the arms share no seed.
    """
    left = select(frame, arm=arm_a, **filters).set_index("seed")[metric]
    right = select(frame, arm=arm_b, **filters).set_index("seed")[metric]
    common = sorted(set(left.index) & set(right.index))
    if not common:
        return Interval(float("nan"), float("nan"), 0)
    return interval((left.loc[common] - scale * right.loc[common]).to_numpy(dtype=float))


def identical_arms(frame: pd.DataFrame, metric: str, arms: tuple[str, ...],
                   **filters: Any) -> list[tuple[str, str]]:
    """Arm pairs whose per-seed values of a metric coincide exactly."""
    table = select(frame, **filters).pivot_table(index="seed", columns="arm", values=metric)
    pairs: list[tuple[str, str]] = []
    present = [a for a in arms if a in table.columns]
    for i, first in enumerate(present):
        for second in present[i + 1:]:
            left = table[first].to_numpy(dtype=float)
            right = table[second].to_numpy(dtype=float)
            if np.allclose(left, right, atol=1e-12, equal_nan=True):
                pairs.append((first, second))
    return pairs


def _series(frame: pd.DataFrame, arm: str, metric: str, **filters: Any) -> pd.Series:
    """Per-seed values of one metric for one arm in one setting."""
    return select(frame, arm=arm, **filters).set_index("seed")[metric]


def net_series(frame: pd.DataFrame, arm: str, metric: str, **filters: Any) -> pd.Series:
    """Per-seed ``value - the arm's own Delta = 0 null`` (DESIGN 6.1).

    An arm whose attacked value sits at or below its no-attack floor carries no
    measurable attack signal, so every ratio against another arm is taken on the
    null-corrected quantity and the sign of this series says which arms those
    are.
    """
    attacked = _series(frame, arm, metric, **filters)
    null = _series(frame, arm, metric, **{**filters, "delta": 0.0})
    common = sorted(set(attacked.index) & set(null.index))
    return attacked.loc[common] - null.loc[common]


def net(frame: pd.DataFrame, arm: str, metric: str, **filters: Any) -> Interval:
    """Interval of the null-corrected metric of one arm (DESIGN 6)."""
    return interval(net_series(frame, arm, metric, **filters).to_numpy(dtype=float))


def net_paired(frame: pd.DataFrame, arm_a: str, arm_b: str, metric: str,
               scale: float = 1.0, **filters: Any) -> Interval:
    """Paired interval of ``net(arm_a) - scale * net(arm_b)`` (DESIGN 6)."""
    left = net_series(frame, arm_a, metric, **filters)
    right = net_series(frame, arm_b, metric, **filters)
    common = sorted(set(left.index) & set(right.index))
    if not common:
        return Interval(float("nan"), float("nan"), 0)
    return interval((left.loc[common] - scale * right.loc[common]).to_numpy(dtype=float))


def ratio(numerator: Interval, denominator: Interval) -> float:
    """Ratio of two means; ``nan`` when the denominator vanishes."""
    if not denominator.mean:
        return float("nan")
    return float(numerator.mean / denominator.mean)
