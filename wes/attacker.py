"""Transport-path telemetry-poisoning attacker (DESIGN 5).

The attacker sits on the reporting path of a fixed fraction ``p`` of UEs: a
relay or false base station on the UE's path, or a compromised transport link.
It falsifies their C1 measurement report by ``delta`` dB, either to pull them
into a *trap* cell (``trap``) or to push them off their serving cell
(``pingpong``).  With probability ``rho`` it also owns the neighbour reports
that feed the composite network channel N.  The serving gNB's own uplink
measurement C2 and the operator's radio map C4 are out of its reach, and the
RAN controller and the serving gNB are attested and out of scope.

Revision B2' fixes three things the rebuilt observation model required:

* the trap cell is drawn from the cells a **+15 dB** falsification could trigger,
  independently of ``delta``, and is **sticky**: kept while it stays feasible,
  so the attacker no longer abandons its own ramp every few slots;
* the ramp is keyed on the **UE** and restarts only when the trap cell changes,
  and feasibility and opportunity are computed from the **applied** magnitude;
* an opportunity is a targeted UE-slot in which the falsified report would
  trigger the intended handover under the base rule **including** the
  time-to-trigger; the instantaneous count is kept beside it.

All draws come from the ``attacker`` RNG stream and are precomputed over the
horizon, so the attacker realisation is a common random number across arms.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .channels import C1, C3, N_CHANNELS, N
from .config import SimConfig
from .decisions import KEEP

logger = logging.getLogger(__name__)

ATTACKER_REGISTRY: dict[str, type[Attacker]] = {}

#: Channels a transport-path attacker can write to (DESIGN 5).  ``C3`` carries
#: the neighbour columns of the composite channel ``N``, so writing to C3 is
#: writing to N; C2's serving column and the radio map C4 are unreachable.
REACHABLE: tuple[int, ...] = (C1, C3)


def register_attacker(name: str) -> Callable[[type[Attacker]], type[Attacker]]:
    """Class decorator registering an attacker mode under ``name``."""

    def decorator(cls: type[Attacker]) -> type[Attacker]:
        ATTACKER_REGISTRY[name] = cls
        return cls

    return decorator


def n_targets(cfg: SimConfig) -> int:
    """Number of targeted UEs, ``round(p * n_ue)`` (DESIGN 5)."""
    return int(round(cfg.attacker.p * cfg.world.n_ue))


@dataclass(frozen=True)
class PoisonResult:
    """Outcome of poisoning one slot."""

    readings: np.ndarray
    intent: np.ndarray
    opportunity: np.ndarray
    opportunity_instant: np.ndarray
    offset: np.ndarray
    falsified: np.ndarray


class Attacker:
    """Base telemetry-poisoning attacker; subclasses fix the falsification mode."""

    def __init__(self, cfg: SimConfig, rng: np.random.Generator) -> None:
        """Draw the targeted UE set, the reach decisions and the ramp state."""
        self.cfg = cfg
        self.n_ue = cfg.world.n_ue
        self.n_cells = cfg.world.n_cells
        self.delta = float(cfg.attacker.delta)
        self.reference_delta = float(cfg.attacker.trap_reference_delta)
        self.rho = float(cfg.attacker.rho)
        self.hysteresis = float(cfg.rule.hysteresis)
        self.ttt = int(cfg.rule.ttt)
        self.ramp_slots = max(1, int(cfg.attacker.ramp_slots))
        self.targets = np.zeros(self.n_ue, dtype=bool)
        chosen = rng.choice(self.n_ue, size=n_targets(cfg), replace=False)
        self.targets[chosen] = True
        self._peer_draw = rng.random((cfg.sim.horizon, self.n_ue))
        self._rows = np.arange(self.n_ue)
        self._ramp_age = np.zeros(self.n_ue, dtype=int)
        self._victim = np.full(self.n_ue, -1, dtype=int)
        self._counter = np.zeros((self.n_ue, self.n_cells), dtype=int)
        self._last_serving = np.full(self.n_ue, -1, dtype=int)
        #: Channels this attacker writes to, recorded for the report.
        self.poisoned_channels: tuple[int, ...] = REACHABLE

    # ---------------------------------------------------------------- mode API

    def feasible(self, serving: np.ndarray, rsrp: np.ndarray,
                 magnitude: np.ndarray) -> np.ndarray:
        """Cells a falsification of ``magnitude`` dB can push over the A3 threshold."""
        raise NotImplementedError

    def victim_cells(self, serving: np.ndarray, load: np.ndarray,
                     rsrp: np.ndarray) -> np.ndarray:
        """Cell whose reading is falsified for each UE (-1 when none is feasible)."""
        raise NotImplementedError

    def sign(self) -> float:
        """Sign of the dB offset the attacker adds to the victim cell's reading."""
        raise NotImplementedError

    def intended_decision(self, victim: np.ndarray) -> np.ndarray:
        """Decision the attacker wants the adjudicator to take."""
        return np.where(self.targets, victim, KEEP)

    def wants_specific_cell(self) -> bool:
        """Whether success requires a handover to one particular cell."""
        raise NotImplementedError

    def opportunity_cells(self, serving: np.ndarray, victim: np.ndarray,
                          fired: np.ndarray) -> np.ndarray:
        """Whether the matured A3 condition realises the attacker's intent."""
        raise NotImplementedError

    # ------------------------------------------------------------------ acting

    def peer_compromised(self, t: int) -> np.ndarray:
        """Mask of targeted UEs whose neighbour reports are falsified in slot ``t``."""
        return self.targets & (self._peer_draw[t] < self.rho)

    def majority_reachable(self, voting_channels: tuple[int, ...]) -> bool:
        """Whether the channels this attacker reaches can carry a voting majority.

        ``N`` counts as reachable whenever ``rho`` is positive: the attacker owns
        the neighbour reports behind it in that share of slots.
        """
        reach = {C1} | ({N} if self.rho > 0.0 else set())
        shared = [c for c in voting_channels if c in reach]
        return len(shared) * 2 > len(voting_channels)

    def _reference_feasible(self, serving: np.ndarray, rsrp: np.ndarray) -> np.ndarray:
        """DESIGN 5.2 trap set: what a +15 dB falsification could trigger, for every Δ."""
        return self.feasible(serving, rsrp,
                             np.full(self.n_ue, self.reference_delta, dtype=float))

    def _sticky_victim(self, serving: np.ndarray, load: np.ndarray,
                       rsrp: np.ndarray) -> np.ndarray:
        """Keep the previous victim cell while it stays feasible (DESIGN 5)."""
        allowed = self._reference_feasible(serving, rsrp)
        fresh = self.victim_cells(serving, load, rsrp)
        held = self._victim.copy()
        keeps = (held >= 0) & allowed[self._rows, np.maximum(held, 0)]
        victim = np.where(keeps, held, fresh)
        held_on = (victim == self._victim) & (victim >= 0)
        self._ramp_age = np.where(held_on, self._ramp_age + 1, 0)
        self._victim = victim
        return victim

    def _magnitude(self) -> np.ndarray:
        """Applied falsification magnitude after the DESIGN 5 ramp."""
        fraction = np.minimum(1.0, (self._ramp_age + 1) / self.ramp_slots)
        return self.delta * fraction

    def _matured(self, serving: np.ndarray, rsrp: np.ndarray,
                 offset: np.ndarray, victim: np.ndarray) -> np.ndarray:
        """A3 condition on the falsified truth, held for ``ttt`` slots."""
        changed = serving != self._last_serving
        if changed.any():
            self._counter[changed] = 0
        self._last_serving = np.asarray(serving).copy()
        falsified = rsrp.copy()
        active = victim >= 0
        falsified[self._rows[active], victim[active]] += offset[active]
        margin = falsified - falsified[self._rows, serving][:, None]
        condition = margin > self.hysteresis
        condition[self._rows, serving] = False
        self._counter = np.where(condition, self._counter + 1, 0)
        return self._counter >= self.ttt

    def poison(self, t: int, readings: np.ndarray, serving: np.ndarray,
               load: np.ndarray, rsrp: np.ndarray) -> PoisonResult:
        """Falsify one slot of channel readings.

        Args:
            t: Slot index.
            readings: ``(n_channels, n_ue, n_cells)`` clean readings; not mutated.
            serving: ``(n_ue,)`` serving-cell index per UE.
            load: ``(n_cells,)`` number of UEs served by each cell.
            rsrp: ``(n_ue, n_cells)`` true RSRP of the slot.

        Returns:
            The poisoned readings, the attacker's intended decision per UE, the
            opportunity masks with and without the time-to-trigger, the applied
            dB offset and the mask of channels actually falsified per UE.
        """
        out = readings.copy()
        victim = self._sticky_victim(serving, load, rsrp)
        magnitude = self._magnitude()
        active = self.targets & (victim >= 0)
        offset = np.where(active, self.sign() * magnitude, 0.0)
        rows, cells = self._rows[active], victim[active]
        out[C1, rows, cells] += offset[active]
        peer = self.peer_compromised(t) & active
        out[C3, self._rows[peer], victim[peer]] += offset[peer]
        matured = self._matured(serving, rsrp, offset, victim)
        instant = self._instant(serving, rsrp, offset, victim)
        falsified = np.zeros((N_CHANNELS, self.n_ue), dtype=bool)
        falsified[C1] = active
        falsified[N] = peer & (victim != serving)
        return PoisonResult(
            readings=out,
            intent=self.intended_decision(np.where(active, victim, KEEP)),
            opportunity=active & self.opportunity_cells(serving, victim, matured),
            opportunity_instant=active & instant,
            offset=offset,
            falsified=falsified,
        )

    def _instant(self, serving: np.ndarray, rsrp: np.ndarray, offset: np.ndarray,
                 victim: np.ndarray) -> np.ndarray:
        """Instantaneous opportunity: the A3 inequality without the TTT."""
        magnitude = np.abs(offset)
        allowed = self.feasible(serving, rsrp, magnitude)
        return self.opportunity_cells(serving, victim, allowed)

    def success(self, decision: np.ndarray, intent: np.ndarray) -> np.ndarray:
        """Targeted UE-slots in which the verdict matches the attacker's intent."""
        if self.wants_specific_cell():
            return self.targets & (intent != KEEP) & (decision == intent)
        return self.targets & (intent != KEEP) & (decision != KEEP)

    def attributable(self, decision: np.ndarray, intent: np.ndarray,
                     oracle: np.ndarray) -> np.ndarray:
        """Successes the falsification actually caused (DESIGN 6.1).

        A targeted UE-slot counts only when the verdict matches the attacker's
        intent *and* the base rule on the true channels would not have taken the
        same decision.
        """
        return self.success(decision, intent) & (oracle != decision)


@register_attacker("trap")
class TrapAttacker(Attacker):
    """Adds +delta dB to a feasible busy neighbour to pull the UE into congestion."""

    def feasible(self, serving: np.ndarray, rsrp: np.ndarray,
                 magnitude: np.ndarray) -> np.ndarray:
        """Cells whose true RSRP is within ``magnitude - hysteresis`` of the serving cell."""
        margin = rsrp - rsrp[self._rows, serving][:, None]
        allowed = margin + magnitude[:, None] > self.hysteresis
        allowed[self._rows, serving] = False
        return allowed

    def victim_cells(self, serving: np.ndarray, load: np.ndarray,
                     rsrp: np.ndarray) -> np.ndarray:
        """Busiest cell of the Δ-independent trap set; ``-1`` when none is feasible."""
        allowed = self._reference_feasible(serving, rsrp)
        scored = np.where(allowed, np.broadcast_to(load, (self.n_ue, self.n_cells)), -np.inf)
        victim = np.argmax(scored, axis=1)
        return np.where(allowed.any(axis=1), victim, -1)

    def sign(self) -> float:
        """The trap attacker inflates the trap cell."""
        return 1.0

    def wants_specific_cell(self) -> bool:
        """Success means handing over to the trap cell specifically."""
        return True

    def opportunity_cells(self, serving: np.ndarray, victim: np.ndarray,
                          fired: np.ndarray) -> np.ndarray:
        """The intended handover is the one to the trap cell."""
        safe = np.maximum(victim, 0)
        return (victim >= 0) & fired[self._rows, safe]


@register_attacker("pingpong")
class PingPongAttacker(Attacker):
    """Subtracts delta dB from the serving cell to push the UE off it."""

    def feasible(self, serving: np.ndarray, rsrp: np.ndarray,
                 magnitude: np.ndarray) -> np.ndarray:
        """Cells that clear A3 once the serving reading is deflated by ``magnitude``."""
        margin = rsrp - (rsrp[self._rows, serving][:, None] - magnitude[:, None])
        allowed = margin > self.hysteresis
        allowed[self._rows, serving] = False
        return allowed

    def victim_cells(self, serving: np.ndarray, load: np.ndarray,
                     rsrp: np.ndarray) -> np.ndarray:
        """The UE's own serving cell, when some other cell could then win."""
        return np.where(self._reference_feasible(serving, rsrp).any(axis=1), serving, -1)

    def sign(self) -> float:
        """The ping-pong attacker deflates the serving cell."""
        return -1.0

    def wants_specific_cell(self) -> bool:
        """Success means any handover away from the serving cell."""
        return False

    def opportunity_cells(self, serving: np.ndarray, victim: np.ndarray,
                          fired: np.ndarray) -> np.ndarray:
        """Any cell that matures under the deflated serving reading will do."""
        return (victim >= 0) & fired.any(axis=1)


def make_attacker(cfg: SimConfig, rng: np.random.Generator) -> Attacker:
    """Instantiate the attacker mode named by ``cfg.attacker.mode``.

    Raises:
        KeyError: If the mode is not registered.
    """
    mode = cfg.attacker.mode
    if mode not in ATTACKER_REGISTRY:
        raise KeyError(f"unknown attacker mode {mode!r}; known: {sorted(ATTACKER_REGISTRY)}")
    return ATTACKER_REGISTRY[mode](cfg, rng)
