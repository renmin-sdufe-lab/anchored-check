"""Physical-consistency checks and their calibrated thresholds (DESIGN 4).

Four checks run on the three voting channels of DESIGN 3.3:

* **serving reciprocity** ``|C1[s] - C2[s]|`` at the serving cell.  C2 is the
  serving gNB's own uplink estimate, which a transport-path attacker cannot
  reach, so a violation excludes C1 alone;
* **neighbour reciprocity** ``|C1[c] - N[c]|`` at the two decision-relevant
  neighbour cells (the strongest other cell C1 names and the one the peer
  channel names).  With no trusted anchor there, a violation excludes **both**
  channels;
* **map consistency** ``|C1[c] - C4[c]|`` against the operator's radio map;
* **rate consistency** ``|C1[c](t) - C1[c](t-1)|`` against the calibrated
  per-slot RSRP change, which catches a step at any attacker reach and is evaded
  by a ramp below the bound: the pre-registered boundary of PROTOCOL.md.

Every threshold is ``z`` times a standard deviation measured online on the
attack-free warm-up (:mod:`wes.calibration`); until that calibration is
installed the checks run on :func:`placeholder_thresholds` and cannot fire.
Every check carries the same 3-consecutive-violation persistence rule, and arm
4d draws ``z`` per UE and per slot from the serving gNB's own C2 noise instead of holding it at 3.

Which checks an arm runs is :data:`ARM_CHECKS` (DESIGN 4.4): every arm runs all
four by default except the cheap arm 5c, which has no Xn and therefore may not
run the one check whose reference travels over it.  An explicit
``checks.enabled`` override always wins, so the decomposition diagnostics keep
addressing single checks on any arm.

DESIGN 4.4 also closes the two ways an arm without Xn could still touch N: the
second non-serving cell the map and rate checks test comes from
:func:`peer_reference`, which is N only for an arm that votes N and the radio
map C4 otherwise, and a disabled check's difference is never formed at all.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import numpy as np

from .calibration import Calibration
from .channels import C1, C2, C4, N_CHANNELS, N
from .config import SimConfig
from .executors import ARM_VOTERS

logger = logging.getLogger(__name__)

#: Checks of DESIGN 4, in the order they are reported.
CHECK_NAMES: tuple[str, ...] = (
    "serving_reciprocity",
    "neighbour_reciprocity",
    "map",
    "rate",
)

#: Two-sided tests each check runs per UE-slot, for the analytic floor.  The
#: three decision-relevant cells are the serving cell and the strongest other
#: cell each of C1 and N names; when those coincide the count is an upper bound.
CHECK_TESTS: dict[str, int] = {
    "serving_reciprocity": 1,
    "neighbour_reciprocity": 2,
    "map": 3,
    "rate": 3,
}

#: Channels a violation of each check excludes (DESIGN 4).  Neighbour
#: reciprocity is symmetric because neither side is anchored on a measurement
#: the attacker cannot reach.
CHECK_EXCLUDES: dict[str, tuple[int, ...]] = {
    "serving_reciprocity": (C1,),
    "neighbour_reciprocity": (C1, N),
    "map": (C1,),
    "rate": (C1,),
}

#: Checks an arm runs when a job leaves ``checks.enabled`` at its default set
#: (DESIGN 4.4).  Arm 5c ``cheap_phys`` votes C1 and C4 and is billed by
#: :func:`wes.engine.measured_channels` for C1, C2 and C4 only, so it must not
#: run neighbour reciprocity: that check's reference N carries the C3 reports
#: delivered over Xn, an interface this arm does not have.  Both checks it keeps
#: beside serving reciprocity are anchored on measurements it already pays for.
ARM_CHECKS: dict[str, tuple[str, ...]] = {
    "cheap_phys": ("serving_reciprocity", "map", "rate"),
}


def peer_reference(arm: str | None = None) -> int:
    """Channel whose argmax names the second non-serving test cell (DESIGN 4.4).

    The map and rate checks test the serving cell and the strongest other cell
    each of two channels names.  For an arm that votes the composite channel N
    the second of those is N, as DESIGN 4.1 writes it; for an arm that has no Xn
    (arm 5c) reading N even as an index would be reading a channel it is not
    billed for, so the column comes from the radio map C4 the arm already pays
    for.

    Args:
        arm: Arm key, or ``None`` when the caller has no arm in hand, in which
            case the DESIGN 4.1 default N applies.

    Returns:
        The channel index :data:`wes.channels.N` or :data:`wes.channels.C4`.
    """
    if arm is None:
        return N
    return N if N in ARM_VOTERS.get(arm, (N,)) else C4


def arm_checks(cfg: SimConfig, arm: str | None = None) -> tuple[str, ...]:
    """Checks one arm runs, ordered as :data:`CHECK_NAMES` (DESIGN 4.1, 4.4).

    An explicit ``checks.enabled`` override always wins, so the check-set
    decomposition diagnostics of ``run.py`` still address every arm; the
    per-arm restriction of :data:`ARM_CHECKS` applies to the default set alone.

    Args:
        cfg: Configuration tree.
        arm: Arm key, or ``None`` when the caller has no arm in hand.

    Returns:
        The enabled check names in report order.
    """
    enabled: tuple[str, ...] = tuple(cfg.checks.enabled)
    if arm in ARM_CHECKS and set(enabled) == set(CHECK_NAMES):
        enabled = ARM_CHECKS[arm]
    return tuple(name for name in CHECK_NAMES if name in enabled)


@dataclass(frozen=True)
class Thresholds:
    """Nominal ``z * sigma_diff`` exclusion thresholds in dB (DESIGN 4)."""

    z: float
    sigma: dict[str, float]

    def nominal(self, check: str) -> float:
        """Threshold of one check at the nominal ``z``."""
        return self.z * self.sigma[check]

    def row(self) -> dict[str, float]:
        """Flat mapping of the thresholds recorded in ``runs.csv``."""
        return {f"thr_{name}": self.nominal(name) for name in CHECK_NAMES}


def build_thresholds(cfg: SimConfig, calibration: Calibration) -> Thresholds:
    """Derive every exclusion threshold from the warm-up calibration (DESIGN 4).

    Args:
        cfg: Configuration tree.
        calibration: Online warm-up calibration of this run.

    Returns:
        The threshold table; nothing here is fitted to attacked data and no
        generating constant is read.
    """
    return Thresholds(
        z=float(cfg.checks.z),
        sigma={name: calibration.sigma(name) for name in CHECK_NAMES},
    )


def placeholder_thresholds(cfg: SimConfig) -> Thresholds:
    """Threshold table in force before the warm-up calibration exists (DESIGN 4.2).

    Every ``sigma_diff`` is infinite, so no difference can exceed its bound, no
    streak builds and nothing is excluded while the checks are idle during the
    attack-free warm-up; a dithered ``z`` keeps the bound infinite.

    Args:
        cfg: Configuration tree.

    Returns:
        The idle threshold table the engine replaces at the end of the warm-up.
    """
    return Thresholds(z=float(cfg.checks.z),
                      sigma=dict.fromkeys(CHECK_NAMES, math.inf))


def analytic_floor(z: float, tests: int, persistence: int) -> float:
    """Per-UE-slot false-positive floor of a ``z``-test check (DESIGN 4).

    Under Gaussian differences a two-sided ``z``-test fires with probability
    ``erfc(z / sqrt(2))``; the check runs ``tests`` of them, and the persistence
    rule needs the violation to repeat, which the independent approximation
    raises to the power of the streak length.
    """
    per_test = math.erfc(z / math.sqrt(2.0))
    per_slot = 1.0 - (1.0 - per_test) ** tests
    return float(per_slot**persistence)


def dither_z(cfg: SimConfig, serving_c2: np.ndarray) -> np.ndarray:
    """Draw ``z ~ U[low, high]`` from the serving gNB's own C2 noise (DESIGN 3.3).

    The low-order bits of the serving-link measurement are its measurement
    noise: randomness the serving gNB observes and a transport-path attacker
    cannot.  An xor-shift mix decorrelates them from the RSRP magnitude.

    Args:
        cfg: Configuration tree.
        serving_c2: ``(n_ue,)`` C2 reading at each UE's serving cell.

    Returns:
        Array of shape ``(n_ue,)`` with one multiplier per UE.
    """
    bits = np.abs(np.nan_to_num(serving_c2) * 1e6).astype(np.uint64)
    bits ^= bits >> np.uint64(33)
    bits *= np.uint64(0xFF51AFD7ED558CCD)
    bits ^= bits >> np.uint64(29)
    unit = (bits >> np.uint64(11)).astype(float) / float(1 << 53)
    low, high = cfg.checks.dither_low, cfg.checks.dither_high
    return low + (high - low) * unit


class PhysicsExclusion:
    """The physical-consistency checks of DESIGN 4."""

    def __init__(self, cfg: SimConfig, thresholds: Thresholds, n_ue: int,
                 n_cells: int, dither: bool = False, arm: str | None = None) -> None:
        """Allocate the streak counters and the previous-slot buffer.

        Raises:
            KeyError: If ``cfg.checks.enabled`` names an unknown check.
        """
        unknown = set(cfg.checks.enabled) - set(CHECK_NAMES)
        if unknown:
            raise KeyError(f"unknown physical-consistency checks {sorted(unknown)}")
        self.cfg = cfg
        self.thresholds = thresholds
        self.n_ue = n_ue
        self.n_cells = n_cells
        self.dither = bool(dither)
        self.arm = arm
        self.peer = peer_reference(arm)
        self._rows = np.arange(n_ue)
        self._streak = np.zeros((len(CHECK_NAMES), n_ue), dtype=int)
        self.enabled = arm_checks(cfg, arm)
        self._previous = np.full((n_ue, n_cells), np.nan, dtype=float)

    @property
    def check_units(self) -> float:
        """Compute units charged per UE-slot: one per enabled check (DESIGN 6.4)."""
        return float(len(self.enabled)) * self.cfg.cost.compute_check

    def floors(self) -> dict[str, float]:
        """Analytic false-positive floor of every enabled check (DESIGN 4)."""
        return {
            name: analytic_floor(self.thresholds.z, CHECK_TESTS[name],
                                 self.cfg.checks.persistence_slots)
            for name in self.enabled
        }

    def relevant_cells(self, readings: np.ndarray, serving: np.ndarray) -> np.ndarray:
        """Serving cell plus the strongest other cell C1 and the peer each name.

        The peer is N for an arm that votes it and C4 for an arm without Xn
        (:func:`peer_reference`, DESIGN 4.4); the symmetry argument behind the
        second column is the same either way, since both are channels the
        adjudicator already reads.
        """
        cols = np.empty((self.n_ue, 3), dtype=int)
        cols[:, 0] = serving
        for index, channel in enumerate((C1, self.peer), start=1):
            masked = np.where(np.isnan(readings[channel]), -np.inf, readings[channel])
            masked[self._rows, serving] = -np.inf
            cols[:, index] = np.argmax(masked, axis=1)
        return cols

    def _violation(self, name: str, readings: np.ndarray, cols: np.ndarray,
                   bound: np.ndarray) -> np.ndarray:
        """Raw violation mask of one check, before the persistence rule."""
        c1 = readings[C1]
        if name == "serving_reciprocity":
            serving = cols[:, 0]
            gap = np.abs(c1[self._rows, serving] - readings[C2][self._rows, serving])
            return gap > bound
        if name == "neighbour_reciprocity":
            gap = np.abs(np.take_along_axis(c1 - readings[N], cols[:, 1:], axis=1))
        elif name == "map":
            gap = np.abs(np.take_along_axis(c1 - readings[C4], cols, axis=1))
        else:
            gap = np.abs(np.take_along_axis(c1 - self._previous, cols, axis=1))
        return (gap > bound[:, None]).any(axis=1)

    def _violations(self, readings: np.ndarray, cols: np.ndarray,
                    threshold: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """Violation masks of the **enabled** checks only (DESIGN 4.4).

        A disabled check's difference is never formed, so an arm that does not
        run neighbour reciprocity never touches N here; its streak counter was
        never read, so skipping it changes no enabled check's verdict.
        """
        return {
            name: self._violation(name, readings, cols, threshold[name])
            for name in self.enabled
        }

    def _thresholds_of_slot(self, readings: np.ndarray,
                            serving: np.ndarray) -> dict[str, np.ndarray]:
        """Per-UE threshold of every check, dithered for arm 4d (DESIGN 3.3)."""
        if self.dither:
            z = dither_z(self.cfg, readings[C2][self._rows, serving])
        else:
            z = np.full(self.n_ue, self.thresholds.z, dtype=float)
        return {name: z * self.thresholds.sigma[name] for name in self.enabled}

    def evaluate(self, readings: np.ndarray, available: np.ndarray,
                 serving: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Run every enabled check and turn its streaks into exclusions.

        Args:
            readings: ``(n_channels, n_ue, n_cells)`` readings of the slot, with
                C2 masked and N composed by :func:`wes.channels.network_view`.
            available: ``(n_channels, n_ue)`` availability mask.
            serving: ``(n_ue,)`` serving-cell index per UE.

        Returns:
            The ``(n_channels, n_ue)`` exclusion mask and the
            ``(n_checks, n_ue)`` per-check firing mask.
        """
        cols = self.relevant_cells(readings, serving)
        threshold = self._thresholds_of_slot(readings, serving)
        violated = self._violations(readings, cols, threshold)
        excluded = np.zeros((N_CHANNELS, self.n_ue), dtype=bool)
        fired = np.zeros((len(CHECK_NAMES), self.n_ue), dtype=bool)
        ready = np.isfinite(self._previous).all(axis=1)
        for index, name in enumerate(CHECK_NAMES):
            if name not in self.enabled:
                continue
            active = violated[name] & ready if name == "rate" else violated[name]
            self._streak[index] = np.where(active, self._streak[index] + 1, 0)
            fired[index] = self._streak[index] >= self.cfg.checks.persistence_slots
            for channel in CHECK_EXCLUDES[name]:
                excluded[channel] |= fired[index] & available[channel]
        self._previous = readings[C1].copy()
        return excluded, fired
