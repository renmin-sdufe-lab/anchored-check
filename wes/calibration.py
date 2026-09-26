"""Online warm-up calibration of every standard deviation a check uses (DESIGN 4.2).

Revision B1 handed the defender the generating noise constants and estimated
only ``sigma_C4``, which is not a measurement the defender could make.  B2'
fixes every threshold to ``z`` times the standard deviation of the compared
difference, **measured on the attack-free warm-up**, so no check reads a
constant out of ``conf/base.yaml``.

The first ``cfg.sim.warmup`` slots of every run are attack-free: the attacker is
silent and the checks are idle.  During them the engine hands each slot's
readings, exactly as :func:`wes.channels.network_view` delivers them to the
checks, to a :class:`WarmupCollector`.  The samples are therefore only what the
serving gNB has: C2 on the serving link alone and the C3 reports of the
neighbour links, which are N's non-serving columns.  At the start of slot
``warmup`` :meth:`WarmupCollector.calibration` turns them into the
:class:`Calibration` every threshold is derived from, and scoring starts in that
same slot.

======================  ==================================================
check                   calibrated difference (warm-up samples)
======================  ==================================================
serving reciprocity     ``C1 - C2`` at the serving cell, one per UE-slot
neighbour reciprocity   ``C1 - N`` at every non-serving cell (C3 reports)
map consistency         ``C1 - C4`` at every cell
rate consistency        ``C1(t) - C1(t-1)`` at every cell, consecutive slots
======================  ==================================================

:func:`offline_channel_diagnostic` is a separate, offline diagnostic: it reads
the whole precomputed clean array, including C2 and C3 on the same link, which
no node can observe, and recovers the per-channel standard deviations reported
as ``sigma_c1_hat`` and ``sigma_map_hat``.  No check uses it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from .channels import C1, C2, C3, C4, Channels, N
from .config import SimConfig

logger = logging.getLogger(__name__)

#: Checks calibrated online, in the order :mod:`wes.checks` reports them.
CALIBRATED_CHECKS: tuple[str, ...] = (
    "serving_reciprocity",
    "neighbour_reciprocity",
    "map",
    "rate",
)


@dataclass(frozen=True)
class Calibration:
    """Check standard deviations measured online on the attack-free warm-up."""

    serving_reciprocity: float
    neighbour_reciprocity: float
    map_consistency: float
    rate: float
    samples: dict[str, int] = field(default_factory=dict)

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
        """Online check sigmas recorded in ``runs.csv``."""
        return {
            "sigma_serving_recip_hat": self.serving_reciprocity,
            "sigma_neighbour_recip_hat": self.neighbour_reciprocity,
            "sigma_map_diff_hat": self.map_consistency,
            "sigma_rate_hat": self.rate,
        }


@dataclass(frozen=True)
class ChannelDiagnostic:
    """Per-channel standard deviations of the offline diagnostic (not used by checks)."""

    sigma_c1: float
    sigma_c2: float
    sigma_c3: float
    sigma_map: float
    n_samples: int

    def row(self) -> dict[str, float]:
        """Diagnostic quantities recorded in ``runs.csv``."""
        return {"sigma_c1_hat": self.sigma_c1, "sigma_map_hat": self.sigma_map}


def _std(values: np.ndarray, floor: float) -> float:
    """Standard deviation of a clean warm-up sample, floored for safety."""
    return float(max(np.std(values), floor))


def _sqrt_floor(variance: float, floor: float) -> float:
    """Square root of a variance that a difference of estimates may drive negative."""
    return float(np.sqrt(max(variance, floor**2)))


def _finite(values: np.ndarray) -> np.ndarray:
    """Flattened finite entries of a difference array."""
    flat = np.asarray(values, dtype=float).ravel()
    return flat[np.isfinite(flat)]


class WarmupCollector:
    """Accumulates the warm-up differences each check compares (DESIGN 4.2).

    Feed it one slot at a time with the readings the checks would read, i.e.
    the output of :func:`wes.channels.network_view`; nothing else is sampled.
    """

    def __init__(self) -> None:
        """Start with no samples and no previous slot."""
        self._samples: dict[str, list[np.ndarray]] = {name: [] for name in CALIBRATED_CHECKS}
        self._previous: np.ndarray | None = None
        self.slots = 0

    def observe(self, readings: np.ndarray, serving: np.ndarray) -> None:
        """Record one warm-up slot of differences.

        Args:
            readings: ``(n_channels, n_ue, n_cells)`` readings of the slot, with
                C2 masked and N composed by :func:`wes.channels.network_view`;
                not mutated.
            serving: ``(n_ue,)`` serving-cell index per UE.
        """
        c1 = readings[C1]
        rows = np.arange(c1.shape[0])
        neighbours = np.ones(c1.shape, dtype=bool)
        neighbours[rows, serving] = False
        self._samples["serving_reciprocity"].append(
            _finite(c1[rows, serving] - readings[C2][rows, serving])
        )
        self._samples["neighbour_reciprocity"].append(
            _finite((c1 - readings[N])[neighbours])
        )
        self._samples["map"].append(_finite(c1 - readings[C4]))
        if self._previous is not None:
            self._samples["rate"].append(_finite(c1 - self._previous))
        self._previous = c1.copy()
        self.slots += 1

    def samples(self, check: str) -> np.ndarray:
        """All samples collected so far for one check.

        Raises:
            KeyError: If the check name is unknown.
        """
        if check not in self._samples:
            raise KeyError(f"unknown check {check!r}; known: {sorted(self._samples)}")
        parts = self._samples[check]
        return np.concatenate(parts) if parts else np.empty(0, dtype=float)

    def calibration(self, cfg: SimConfig) -> Calibration:
        """Turn the collected samples into every check's ``sigma_diff``.

        Args:
            cfg: Configuration tree, for ``checks.sigma_floor``.

        Returns:
            The calibration every threshold of :mod:`wes.checks` is derived from.

        Raises:
            ValueError: If some check has no sample, i.e. the warm-up was shorter
                than two slots.
        """
        floor = cfg.checks.sigma_floor
        pooled = {name: self.samples(name) for name in CALIBRATED_CHECKS}
        empty = sorted(name for name, values in pooled.items() if values.size == 0)
        if empty:
            raise ValueError(
                f"warm-up of {self.slots} slots gave no calibration sample for {empty}"
            )
        calibration = Calibration(
            serving_reciprocity=_std(pooled["serving_reciprocity"], floor),
            neighbour_reciprocity=_std(pooled["neighbour_reciprocity"], floor),
            map_consistency=_std(pooled["map"], floor),
            rate=_std(pooled["rate"], floor),
            samples={name: int(values.size) for name, values in pooled.items()},
        )
        logger.debug("calibrated online on %d warm-up slots: %s", self.slots, calibration)
        return calibration


def offline_channel_diagnostic(cfg: SimConfig, channels: Channels) -> ChannelDiagnostic:
    """Offline per-channel noise diagnostic; no check uses it.

    It reads every column of the precomputed clean C1, C2, C3 and C4 over the
    warm-up, including C2 and C3 on the same link, which no node observes
    online, and recovers ``sigma_C1^2 = (V12 + V13 - V23) / 2`` (and likewise
    for C2 and C3) and ``sigma_map^2 = Var(C1 - C4) - sigma_C1^2``.  The result
    is reported beside the online calibration only to show the channel model
    is what DESIGN 2 says it is.

    Args:
        cfg: Configuration tree.
        channels: Clean precomputed channels of the run.

    Returns:
        The diagnostic recorded as ``sigma_c1_hat`` and ``sigma_map_hat``.
    """
    warmup = cfg.sim.warmup
    floor = cfg.checks.sigma_floor
    c1 = channels.values[C1][:warmup]
    c2 = channels.values[C2][:warmup]
    c3 = channels.values[C3][:warmup]
    c4 = channels.values[C4][:warmup]
    v12, v13, v23 = float(np.var(c1 - c2)), float(np.var(c1 - c3)), float(np.var(c2 - c3))
    var_c1 = 0.5 * (v12 + v13 - v23)
    diagnostic = ChannelDiagnostic(
        sigma_c1=_sqrt_floor(var_c1, floor),
        sigma_c2=_sqrt_floor(0.5 * (v12 + v23 - v13), floor),
        sigma_c3=_sqrt_floor(0.5 * (v13 + v23 - v12), floor),
        sigma_map=_sqrt_floor(float(np.var(c1 - c4)) - var_c1, floor),
        n_samples=int(c1.size),
    )
    logger.debug("offline diagnostic on %d samples: %s", diagnostic.n_samples, diagnostic)
    return diagnostic
