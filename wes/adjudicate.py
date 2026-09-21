"""Adjudication of executor decisions (DESIGN 3.3).

Five adjudicators are registered:

* ``single`` (arm 1) forwards the only executor's decision;
* ``weighted_majority`` (arm 2') is a majority vote over three decision families
  with DHR-style multiplicative confidence down-weighting of executors that
  disagree with the verdict;
* ``majority`` (arm 3) is a strict majority vote over C1, N and C4;
* ``physics_majority`` (arms 4 and 4d) first excludes channels that fail a
  physical-consistency check of DESIGN 4, then votes over what is left;
* ``unanimity_physics`` (arm 5c) hands over only when the two surviving cheap
  channels name the same target, and keeps serving otherwise.

When exclusions leave fewer than ``checks.min_channels`` voters, DESIGN 3.4's
trusted-channel fallback follows the surviving channel anchored on a measurement
the attacker cannot reach (the radio map C4), otherwise the surviving channel,
otherwise keep serving.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .channels import C4, N_CHANNELS
from .checks import (
    ARM_CHECKS,
    CHECK_NAMES,
    PhysicsExclusion,
    Thresholds,
    arm_checks,
    build_thresholds,
)
from .config import SimConfig
from .decisions import KEEP

logger = logging.getLogger(__name__)

__all__ = [
    "ADJUDICATOR_REGISTRY",
    "ARM_CHECKS",
    "ARM_WIRING",
    "CHECK_NAMES",
    "TRUSTED_CHANNEL",
    "Adjudication",
    "Adjudicator",
    "PhysicsExclusion",
    "SlotView",
    "Thresholds",
    "arm_checks",
    "build_thresholds",
    "make_adjudicator",
    "register_adjudicator",
    "weighted_vote",
]

ADJUDICATOR_REGISTRY: dict[str, type[Adjudicator]] = {}

#: The voting channel anchored on measurements the attacker cannot reach; the
#: DESIGN 3.4 fallback prefers it when the vote runs short of voters.
TRUSTED_CHANNEL: int = C4

#: Adjudicator used by each arm (DESIGN 3.3).
ARM_WIRING: dict[str, str] = {
    "single": "single",
    "model_dhr3": "weighted_majority",
    "obs_dhr": "majority",
    "obs_dhr_phys": "physics_majority",
    "obs_dhr_phys_dither": "physics_majority",
    "cheap_phys": "unanimity_physics",
    "model_dhr_param": "weighted_majority",
}

#: Arms whose adjudicator dithers the check thresholds per slot (DESIGN 3.3).
DITHERED_ARMS: tuple[str, ...] = ("obs_dhr_phys_dither",)


def register_adjudicator(name: str) -> Callable[[type[Adjudicator]], type[Adjudicator]]:
    """Class decorator registering an adjudicator under ``name``."""

    def decorator(cls: type[Adjudicator]) -> type[Adjudicator]:
        ADJUDICATOR_REGISTRY[name] = cls
        return cls

    return decorator


@dataclass(frozen=True)
class SlotView:
    """Everything an adjudicator sees in one slot."""

    t: int
    decisions: np.ndarray
    spec_channels: np.ndarray
    readings: np.ndarray
    available: np.ndarray
    serving: np.ndarray


@dataclass(frozen=True)
class Adjudication:
    """Verdict of one slot plus the bookkeeping the metrics need."""

    decision: np.ndarray
    excluded: np.ndarray
    fired: np.ndarray
    voters: np.ndarray
    check_units: float
    fallback: np.ndarray


def weighted_vote(decisions: np.ndarray, weights: np.ndarray, n_cells: int) -> np.ndarray:
    """Majority vote with per-voter weights.

    A candidate wins only with strictly more than half of the participating
    weight; otherwise the verdict is :data:`KEEP` (no majority).

    Args:
        decisions: ``(n_vote, n_ue)`` decisions.
        weights: ``(n_vote, n_ue)`` non-negative voter weights.
        n_cells: Number of cells, sizing the tally.

    Returns:
        Array of shape ``(n_ue,)`` with the adjudicated decision.
    """
    n_ue = decisions.shape[1]
    rows = np.arange(n_ue)
    tally = np.zeros((n_ue, n_cells + 1), dtype=float)
    for index in range(decisions.shape[0]):
        np.add.at(tally, (rows, decisions[index] + 1), weights[index])
    total = tally.sum(axis=1)
    best = np.argmax(tally, axis=1)
    win = tally[rows, best] > 0.5 * total
    return np.where(win & (total > 0.0), best - 1, KEEP)


class Adjudicator:
    """Interface every adjudication rule implements."""

    #: Whether this rule applies the DESIGN 3.4 fewer-than-two-channels fallback.
    enforces_min_channels: bool = False

    def __init__(self, cfg: SimConfig, cells: np.ndarray, n_specs: int, n_ue: int,
                 thresholds: Thresholds | None = None, dither: bool = False,
                 arm: str | None = None) -> None:
        """Store the configuration, the bank geometry and the arm key."""
        self.cfg = cfg
        self.cells = cells
        self.n_specs = n_specs
        self.n_ue = n_ue
        self.thresholds = thresholds
        self.dither = dither
        self.arm = arm
        self.n_cells = int(cells.shape[0])
        self._rows = np.arange(n_ue)

    def _available(self, view: SlotView) -> np.ndarray:
        """Availability of each voting executor's channel, per UE."""
        return view.available[view.spec_channels[:, None], self._rows[None, :]]

    def decide(self, view: SlotView) -> Adjudication:
        """Adjudicate one slot."""
        raise NotImplementedError

    def _empty(self) -> tuple[np.ndarray, np.ndarray]:
        """Zero exclusion and firing masks, for adjudicators without checks."""
        return (
            np.zeros((N_CHANNELS, self.n_ue), dtype=bool),
            np.zeros((len(CHECK_NAMES), self.n_ue), dtype=bool),
        )

    def _no_fallback(self) -> np.ndarray:
        """All-false fallback mask."""
        return np.zeros(self.n_ue, dtype=bool)


@register_adjudicator("single")
class SingleAdjudicator(Adjudicator):
    """Arm 1: the lone executor's decision is the verdict."""

    def decide(self, view: SlotView) -> Adjudication:
        """Forward the single executor's decision (KEEP if its channel is missing)."""
        available = self._available(view)
        excluded, fired = self._empty()
        decision = np.where(available[0], view.decisions[0], KEEP)
        return Adjudication(decision, excluded, fired, available[0].astype(int), 0.0,
                            self._no_fallback())


@register_adjudicator("majority")
class MajorityAdjudicator(Adjudicator):
    """Arm 3: strict majority vote over the available voting channels."""

    def decide(self, view: SlotView) -> Adjudication:
        """Vote with unit weights on every available channel."""
        available = self._available(view)
        excluded, fired = self._empty()
        decision = weighted_vote(view.decisions, available.astype(float), self.n_cells)
        return Adjudication(decision, excluded, fired, available.sum(axis=0), 0.0,
                            self._no_fallback())


@register_adjudicator("weighted_majority")
class WeightedMajorityAdjudicator(Adjudicator):
    """Arm 2': majority vote with multiplicative confidence down-weighting."""

    def __init__(self, cfg: SimConfig, cells: np.ndarray, n_specs: int, n_ue: int,
                 thresholds: Thresholds | None = None, dither: bool = False,
                 arm: str | None = None) -> None:
        """Start every executor at full confidence."""
        super().__init__(cfg, cells, n_specs, n_ue, thresholds, dither, arm)
        self.weights = np.ones((n_specs, n_ue), dtype=float)

    def decide(self, view: SlotView) -> Adjudication:
        """Vote with the current confidences, then update them on (dis)agreement."""
        available = self._available(view)
        excluded, fired = self._empty()
        decision = weighted_vote(view.decisions, available.astype(float) * self.weights,
                                 self.n_cells)
        self._update(view.decisions, decision)
        return Adjudication(decision, excluded, fired, available.sum(axis=0), 0.0,
                            self._no_fallback())

    def _update(self, decisions: np.ndarray, verdict: np.ndarray) -> None:
        """Shrink a disagreeing executor's weight, let an agreeing one recover."""
        dhr = self.cfg.dhr
        agree = decisions == verdict[None, :]
        grown = np.minimum(self.weights * dhr.recover, dhr.weight_cap)
        shrunk = np.maximum(self.weights * dhr.decay, dhr.weight_floor)
        self.weights = np.where(agree, grown, shrunk)


class CheckingAdjudicator(Adjudicator):
    """Common machinery of the arms that exclude before they vote (DESIGN 4)."""

    enforces_min_channels: bool = True

    def __init__(self, cfg: SimConfig, cells: np.ndarray, n_specs: int, n_ue: int,
                 thresholds: Thresholds | None = None, dither: bool = False,
                 arm: str | None = None) -> None:
        """Build the physical-consistency checker over this arm's check set.

        Raises:
            ValueError: If no threshold table was supplied.
        """
        super().__init__(cfg, cells, n_specs, n_ue, thresholds, dither, arm)
        if thresholds is None:
            raise ValueError("a checking adjudicator needs a calibrated Thresholds table")
        self.checks = PhysicsExclusion(cfg, thresholds, n_ue, int(cells.shape[0]),
                                       dither=dither, arm=arm)

    def _survivors(self, view: SlotView) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Exclusion mask, per-check firings and the surviving voter mask."""
        excluded, fired = self.checks.evaluate(view.readings, view.available, view.serving)
        reachable = excluded[view.spec_channels[:, None], self._rows[None, :]]
        kept = self._available(view) & ~reachable
        return excluded, fired, kept

    def _fallback(self, view: SlotView, kept: np.ndarray,
                  voters: np.ndarray) -> np.ndarray:
        """DESIGN 3.4 trusted-channel fallback when too few channels survive.

        The decision follows the surviving channel anchored on measurements the
        attacker cannot reach (the radio map C4) if it survives, otherwise the
        surviving channel, otherwise keep serving.
        """
        decisions = view.decisions
        trusted = kept & (view.spec_channels == TRUSTED_CHANNEL)[:, None]
        has_trusted = trusted.any(axis=0)
        survivor = np.where(voters >= 1, decisions[np.argmax(kept, axis=0), self._rows],
                            KEEP)
        return np.where(has_trusted, decisions[np.argmax(trusted, axis=0), self._rows],
                        survivor)


@register_adjudicator("physics_majority")
class PhysicsMajorityAdjudicator(CheckingAdjudicator):
    """Arms 4 and 4d: physical-consistency exclusion, then a majority of survivors."""

    def decide(self, view: SlotView) -> Adjudication:
        """Exclude inconsistent channels and vote over the survivors."""
        excluded, fired, kept = self._survivors(view)
        decision = weighted_vote(view.decisions, kept.astype(float), self.n_cells)
        voters = kept.sum(axis=0)
        short = voters < self.cfg.checks.min_channels
        decision = np.where(short, self._fallback(view, kept, voters), decision)
        return Adjudication(decision, excluded, fired, voters, self.checks.check_units,
                            short)


@register_adjudicator("unanimity_physics")
class UnanimityPhysicsAdjudicator(CheckingAdjudicator):
    """Arm 5c: hand over only when both cheap channels name the same target."""

    def decide(self, view: SlotView) -> Adjudication:
        """Require unanimity among the survivors, else keep the serving cell."""
        excluded, fired, kept = self._survivors(view)
        voters = kept.sum(axis=0)
        candidate = view.decisions[0]
        agree = np.ones(self.n_ue, dtype=bool)
        for index in range(1, view.decisions.shape[0]):
            agree &= view.decisions[index] == candidate
        full = voters >= view.decisions.shape[0]
        decision = np.where(full & agree, candidate, KEEP)
        short = voters < self.cfg.checks.min_channels
        decision = np.where(short, self._fallback(view, kept, voters), decision)
        return Adjudication(decision, excluded, fired, voters, self.checks.check_units,
                            short)


def make_adjudicator(name: str, cfg: SimConfig, cells: np.ndarray, n_specs: int,
                     n_ue: int, thresholds: Thresholds | None = None,
                     dither: bool = False, arm: str | None = None) -> Adjudicator:
    """Instantiate a registered adjudicator.

    Args:
        name: Registered adjudicator key (:data:`ARM_WIRING` maps arms to it).
        cfg: Configuration tree.
        cells: ``(n_cells, 2)`` cell positions.
        n_specs: Number of executors in the arm's bank.
        n_ue: Number of UEs.
        thresholds: Calibrated threshold table; required by the checking rules.
        dither: Whether to draw ``z`` per slot (arm 4d).
        arm: Arm key, which selects the arm's check set (DESIGN 4.4).

    Raises:
        KeyError: If the adjudicator name is unknown.
    """
    if name not in ADJUDICATOR_REGISTRY:
        raise KeyError(f"unknown adjudicator {name!r}; known: {sorted(ADJUDICATOR_REGISTRY)}")
    return ADJUDICATOR_REGISTRY[name](cfg, cells, n_specs, n_ue, thresholds, dither, arm)
