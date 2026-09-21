"""Warm-up calibration of every standard deviation a check uses (DESIGN 4.2).

Revision B1 handed the defender the generating noise constants and estimated
only ``sigma_C4``, which is not a measurement the defender could make.  B2'
fixes every threshold to ``z`` times the standard deviation of the compared
difference, **measured on the clean warm-up window**, so no check reads a
constant out of ``conf/base.yaml``.

Four differences are measured directly, because they are exactly what the four
checks of DESIGN 4 compare:

======================  =========================================
check                   calibrated difference
======================  =========================================
serving reciprocity     ``C1 - C2``
neighbour reciprocity   ``C1 - C3``
map consistency         ``C1 - C4``
rate consistency        ``C1(t) - C1(t-1)``
======================  =========================================

The per-channel standard deviations are recovered for the report from the three
pairwise variances, ``sigma_C1^2 = (V12 + V13 - V23) / 2`` and so on, and
``sigma_map^2 = Var(C1 - C4) - sigma_C1^2``.  Nothing here sees a falsified
sample: the calibration runs on the precomputed clean array before any slot is
poisoned, and the warm-up is assumed clean, which the report states.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from .channels import C1, C2, C3, C4, Channels
from .config import SimConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Calibration:
    """Standard deviations measured on the clean warm-up window (DESIGN 4)."""

    serving_reciprocity: float
    neighbour_reciprocity: float
    map_consistency: float
    rate: float
    sigma_c1: float
    sigma_c2: float
    sigma_c3: float
    sigma_map: float
    n_samples: int

    def sigma(self, check: str) -> float:
        """Standard deviation of the difference one named check compares.

        Raises:
            KeyError: If the check name is unknown.
        """
        table = {
            "serving_reciprocity": self.serving_reciprocity,
            "neighbour_reciprocity": self.neighbour_reciprocity,
            "map": self.map_consistency,
            "rate": self.rate,
        }
        if check not in table:
            raise KeyError(f"unknown check {check!r}; known: {sorted(table)}")
        return table[check]

    def row(self) -> dict[str, float]:
        """Calibrated quantities recorded in ``runs.csv``."""
        return {
            "sigma_serving_recip_hat": self.serving_reciprocity,
            "sigma_neighbour_recip_hat": self.neighbour_reciprocity,
            "sigma_map_diff_hat": self.map_consistency,
            "sigma_rate_hat": self.rate,
            "sigma_c1_hat": self.sigma_c1,
            "sigma_map_hat": self.sigma_map,
        }


def _std(values: np.ndarray, floor: float) -> float:
    """Standard deviation of a clean warm-up sample, floored for safety."""
    return float(max(np.std(values), floor))


def _sqrt_floor(variance: float, floor: float) -> float:
    """Square root of a variance that a difference of estimates may drive negative."""
    return float(np.sqrt(max(variance, floor**2)))


def calibrate(cfg: SimConfig, channels: Channels) -> Calibration:
    """Measure every check's ``sigma_diff`` on the clean warm-up (DESIGN 4).

    Args:
        cfg: Configuration tree.
        channels: Clean precomputed channels of the run.

    Returns:
        The calibration every threshold of :mod:`wes.checks` is derived from.
    """
    warmup = cfg.sim.warmup
    floor = cfg.checks.sigma_floor
    c1 = channels.values[C1][:warmup]
    c2 = channels.values[C2][:warmup]
    c3 = channels.values[C3][:warmup]
    c4 = channels.values[C4][:warmup]
    v12, v13, v23 = float(np.var(c1 - c2)), float(np.var(c1 - c3)), float(np.var(c2 - c3))
    var_c1 = 0.5 * (v12 + v13 - v23)
    sigma_c1 = _sqrt_floor(var_c1, floor)
    calibration = Calibration(
        serving_reciprocity=_std(c1 - c2, floor),
        neighbour_reciprocity=_std(c1 - c3, floor),
        map_consistency=_std(c1 - c4, floor),
        rate=_std(np.diff(c1, axis=0), floor),
        sigma_c1=sigma_c1,
        sigma_c2=_sqrt_floor(0.5 * (v12 + v23 - v13), floor),
        sigma_c3=_sqrt_floor(0.5 * (v13 + v23 - v12), floor),
        sigma_map=_sqrt_floor(float(np.var(c1 - c4)) - var_c1, floor),
        n_samples=int(c1.size),
    )
    logger.debug("calibrated on %d warm-up samples: %s", calibration.n_samples, calibration)
    return calibration
