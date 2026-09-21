"""Slot-stepped simulation engine (DESIGN 1-6).

The engine owns the precomputed world, the clean observation channels, the
attacker, an oracle A3 rule on the true RSRP and the per-arm executor bank and
adjudicator.  An arm is nothing but the policy objects handed to this same loop,
so the world, the mobility, the report noise and the attacker draws are common
random numbers across arms for a given seed.

Each slot the attacker writes to C1 and, with probability ``rho``, to the
neighbour reports behind the composite channel N; the engine then applies
:func:`wes.channels.network_view`, which masks C2 to the serving link and
assembles N, so no executor and no check can read a measurement its node could
not make (DESIGN 2).

The oracle is the Revision B1 counterfactual: it never votes and is never
billed, but its decision says whether a handover would have happened without the
falsification (attack-attributable success, DESIGN 6.1), which handovers an arm declines
to make (missed handovers) and which cell the UE should be on (the DESIGN 6.2
harm metrics).
"""

from __future__ import annotations

import logging
import time

import numpy as np

from .adjudicate import (
    ARM_WIRING,
    DITHERED_ARMS,
    SlotView,
    arm_checks,
    build_thresholds,
    make_adjudicator,
)
from .attacker import make_attacker
from .calibration import calibrate
from .channels import C1, C2, C3, C4, N, build_channels, network_view
from .config import SimConfig
from .decisions import KEEP
from .executors import ExecutorBank, arm_specs, n_voters, oracle_executor
from .metrics import ByteLedger, MetricsCollector, MissedHandoverTracker, RunResult
from .radio import rsrp_true, throughput_proxy
from .world import build_world, make_streams

logger = logging.getLogger(__name__)

#: Channels the physical-consistency checks must measure even when no executor
#: votes on them: C2 anchors serving reciprocity, C4 the map check.
CHECK_REFERENCES: tuple[int, ...] = (C2, C4)

#: Reports a channel costs per UE-slot (DESIGN 6.4).  C1 is one UE report
#: covering every cell; C2 is the serving gNB's own link; C3 is one report per
#: neighbour actually used to build N; C4 is read from the operator's map.
CHANNEL_REPORTS: dict[int, str] = {C1: "one", C2: "one", C3: "neighbours", C4: "one"}


def measured_channels(arm: str, bank: ExecutorBank) -> tuple[int, ...]:
    """Channels an arm has to measure, hence pay signalling bytes for (DESIGN 3).

    A voting executor on the composite channel N measures C2 and C3; a checking
    adjudicator measures C2 and C4 whether or not an executor votes on them.

    The bill and the check set have to agree: an arm with no Xn in this tuple
    must not run a check whose reference reaches over Xn, which is why arm 5c
    runs :data:`wes.checks.ARM_CHECKS`'s three-check set (DESIGN 4.4).
    """
    used: set[int] = set()
    for channel in bank.channels:
        used |= {C2, C3} if int(channel) == N else {int(channel)}
    if ARM_WIRING[arm] in ("physics_majority", "unanimity_physics"):
        used |= set(CHECK_REFERENCES)
    return tuple(sorted(used))


class Engine:
    """One simulation run: a configuration, an arm and a seed."""

    def __init__(self, cfg: SimConfig, arm: str, seed: int) -> None:
        """Precompute the world and the channels, then wire the arm's policies.

        Raises:
            KeyError: If the arm key is unknown.
        """
        if arm not in ARM_WIRING:
            raise KeyError(f"unknown arm {arm!r}; known: {sorted(ARM_WIRING)}")
        self.cfg = cfg
        self.arm = arm
        self.seed = seed
        self.streams = make_streams(seed)
        self.world = build_world(cfg, self.streams)
        self.rsrp = rsrp_true(cfg, self.world.positions, self.world.cells, self.world.shadow)
        self.channels = build_channels(cfg, self.rsrp, self.streams["noise"],
                                       self.world.map_error)
        self.calibration = calibrate(cfg, self.channels)
        self.thresholds = build_thresholds(cfg, self.calibration)
        self.attacker = make_attacker(cfg, self.streams["attacker"])
        n_ue, n_cells = cfg.world.n_ue, cfg.world.n_cells
        self.specs = arm_specs(cfg, arm)
        self.bank = ExecutorBank(cfg, self.specs, n_ue, n_cells)
        self.oracle = oracle_executor(cfg, n_ue, n_cells)
        self.n_vote = n_voters(arm)
        self.adjudicator = make_adjudicator(
            ARM_WIRING[arm], cfg, self.world.cells, len(self.specs), n_ue,
            self.thresholds, arm in DITHERED_ARMS, arm,
        )
        self.measured = measured_channels(arm, self.bank)
        #: Checks this arm actually runs (DESIGN 4.4); recorded in ``runs.csv``
        #: so the check-set column names what ran, not what was configured.
        self.enabled_checks = arm_checks(cfg, arm)
        self.voting_channels = tuple(int(c) for c in self.bank.channels)
        self.ledger = ByteLedger()
        self.metrics = MetricsCollector(cfg.sim.warmup, cfg.sim.slot_seconds, n_ue)
        self.missed = MissedHandoverTracker(n_ue, cfg.rule.ttt)
        self._min_channels = (
            cfg.checks.min_channels if self.adjudicator.enforces_min_channels else 0
        )

    def _initial_state(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Attach every UE to its strongest cell and build the load and history."""
        serving = np.argmax(self.rsrp[0], axis=1).astype(int)
        load = np.bincount(serving, minlength=self.cfg.world.n_cells).astype(float)
        last_left = np.full(
            (self.cfg.world.n_ue, self.cfg.world.n_cells), -(10**9), dtype=int
        )
        return serving, load, last_left

    def _charge_slot(self) -> None:
        """Charge one slot of measurement bytes for every UE (DESIGN 6.4)."""
        costs = self.cfg.cost.channel_bytes
        neighbours = self.cfg.world.n_cells - 1
        for channel in self.measured:
            reports = neighbours if CHANNEL_REPORTS[channel] == "neighbours" else 1
            self.ledger.charge(channel, costs[channel] * reports, self.cfg.world.n_ue)

    @property
    def majority_reachable(self) -> bool:
        """Whether the attacker's reachable channels could form a voting majority."""
        return self.attacker.majority_reachable(self.voting_channels)

    def _harm(self, truth: np.ndarray, serving: np.ndarray,
              oracle_decision: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """DESIGN 6.2 harm terms of one slot against the oracle's serving choice."""
        rows = np.arange(serving.size)
        choice = np.where(oracle_decision == KEEP, serving, oracle_decision)
        deficit = truth[rows, choice] - truth[rows, serving]
        outage = truth[rows, serving] < self.cfg.radio.outage_rsrp_dbm
        return deficit, outage, choice != serving

    def run(self) -> RunResult:
        """Execute the whole horizon and return the run's metric row."""
        start = time.perf_counter()
        cfg = self.cfg
        serving, load, last_left = self._initial_state()
        window = cfg.metrics.pingpong_window
        hysteresis = cfg.rule.hysteresis
        scored_slots = 0
        for t in range(cfg.sim.horizon):
            truth = self.rsrp[t]
            poisoned = self.attacker.poison(t, self.channels.slot(t), serving, load, truth)
            readings = network_view(poisoned.readings, serving)
            decisions = self.bank.step(readings, serving, load)
            oracle_decision = self.oracle.step(truth, serving, load)
            view = SlotView(
                t=t,
                decisions=decisions,
                spec_channels=self.bank.channels,
                readings=readings,
                available=self.channels.available[:, t],
                serving=serving,
            )
            verdict = self.adjudicator.decide(view)
            decision = verdict.decision
            scoring = t >= cfg.sim.warmup
            self.missed.observe(t, oracle_decision, scoring)
            if scoring:
                scored_slots += 1
                self._charge_slot()
                deficit, outage, wrong_cell = self._harm(truth, serving, oracle_decision)
                self.metrics.observe(
                    targets=self.attacker.targets,
                    success=self.attacker.success(decision, poisoned.intent),
                    attributable=self.attacker.attributable(
                        decision, poisoned.intent, oracle_decision
                    ),
                    opportunity=poisoned.opportunity,
                    opportunity_instant=poisoned.opportunity_instant,
                    detected=(poisoned.falsified & verdict.excluded).any(axis=0),
                    excluded=verdict.excluded,
                    fired=verdict.fired,
                    voters=verdict.voters,
                    fallback=verdict.fallback if self._min_channels else np.zeros_like(
                        verdict.fallback
                    ),
                    throughput=throughput_proxy(cfg, truth, serving, load),
                    deficit=deficit,
                    outage=outage,
                    wrong_cell=wrong_cell,
                    check_units=verdict.check_units,
                )
            moving = np.flatnonzero(decision != KEEP)
            if moving.size:
                target = decision[moving]
                previous = serving[moving]
                self.missed.resolve(moving, target, scoring)
                if scoring:
                    self.metrics.observe_handovers(
                        wrong=truth[moving, target] < truth[moving, previous] + hysteresis,
                        pingpong=(t - last_left[moving, target]) <= window,
                    )
                last_left[moving, previous] = t
                serving = serving.copy()
                serving[moving] = target
                load = np.bincount(serving, minlength=cfg.world.n_cells).astype(float)
        return self._result(time.perf_counter() - start, scored_slots)

    def _result(self, runtime: float, scored_slots: int) -> RunResult:
        """Assemble the run row from the collector and the cost ledgers."""
        cfg = self.cfg
        rates = self.metrics.rates(self.missed)
        ue_seconds = cfg.world.n_ue * cfg.sim.metric_seconds
        executors = len(self.bank) * cfg.cost.compute_executor
        return RunResult(
            arm=self.arm,
            seed=self.seed,
            p=cfg.attacker.p,
            delta=cfg.attacker.delta,
            rho=cfg.attacker.rho,
            sigma_map=cfg.channels.sigma_map,
            mode=cfg.attacker.mode,
            ramp_slots=cfg.attacker.ramp_slots,
            checks="+".join(self.enabled_checks) or "none",
            z=cfg.checks.z,
            persistence_slots=cfg.checks.persistence_slots,
            n_targets=int(self.attacker.targets.sum()),
            n_voting_channels=len(self.voting_channels),
            majority_reachable=self.majority_reachable,
            bytes_per_ue_s=self.ledger.total / ue_seconds,
            bytes_ota_per_ue_s=self.ledger.total_excluding((C2,)) / ue_seconds,
            compute_per_decision=executors + self.metrics.mean_check_units(scored_slots),
            runtime_seconds=runtime,
            **self.thresholds.row(),
            **self.calibration.row(),
            **rates,
        )
