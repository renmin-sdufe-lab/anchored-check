"""Handover executors and the per-arm executor banks (DESIGN 3.2, 3.3).

An executor is a handover rule evaluated on one observation channel.  Three
decision families are registered:

* ``a3``, the 3GPP event-A3 rule: the target beats the serving cell by the
  hysteresis for time-to-trigger consecutive slots;
* ``load_aware``, A3 **and** the target's load is below the serving cell's,
  else keep serving (DESIGN 3.2);
* ``trend``, the channel's serving-to-target difference has risen strictly over
  the last ``ttt`` slots and exceeds the hysteresis at the last one (DESIGN 3.2).

Arm 2' runs all three on C1, so a common cause still reaches every executor;
arms 3, 4, 4d and 5c run the A3 rule on different channels (DESIGN 3.3).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .channels import C1, C4, N
from .config import SimConfig
from .decisions import KEEP

logger = logging.getLogger(__name__)

EXECUTOR_REGISTRY: dict[str, type[Executor]] = {}


def register_executor(name: str) -> Callable[[type[Executor]], type[Executor]]:
    """Class decorator registering an executor rule under ``name``."""

    def decorator(cls: type[Executor]) -> type[Executor]:
        EXECUTOR_REGISTRY[name] = cls
        return cls

    return decorator


@dataclass(frozen=True)
class ExecutorSpec:
    """One executor: a rule family, its parameters and the channel it reads."""

    rule: str
    channel: int
    hysteresis: float
    ttt: int
    label: str


class Executor:
    """Interface every handover rule implements."""

    def __init__(self, spec: ExecutorSpec, n_ue: int, n_cells: int) -> None:
        """Store the spec and allocate per-UE rule state."""
        self.spec = spec
        self.n_ue = n_ue
        self.n_cells = n_cells
        self._rows = np.arange(n_ue)
        self._last_serving = np.full(n_ue, -1, dtype=int)

    def step(self, values: np.ndarray, serving: np.ndarray,
             load: np.ndarray) -> np.ndarray:
        """Return one decision per UE from this slot's channel readings."""
        raise NotImplementedError

    def _margin(self, values: np.ndarray, serving: np.ndarray) -> np.ndarray:
        """Per-cell excess over the serving cell, ``-inf`` where unreadable."""
        finite = np.where(np.isnan(values), -np.inf, values)
        reference = finite[self._rows, serving][:, None]
        margin = finite - reference
        margin[self._rows, serving] = -np.inf
        return margin

    def _reset_on_handover(self, serving: np.ndarray) -> np.ndarray:
        """Mask of UEs whose serving cell changed since the last slot."""
        changed = serving != self._last_serving
        self._last_serving = np.asarray(serving).copy()
        return changed

    @staticmethod
    def _pick(fired: np.ndarray, values: np.ndarray) -> np.ndarray:
        """Strongest cell among those the rule fired on, else :data:`KEEP`."""
        masked = np.where(fired, np.where(np.isnan(values), -np.inf, values), -np.inf)
        best = np.argmax(masked, axis=1)
        return np.where(fired.any(axis=1), best, KEEP)


@register_executor("a3")
class A3Executor(Executor):
    """Event-A3 rule with hysteresis and time-to-trigger (DESIGN 3)."""

    def __init__(self, spec: ExecutorSpec, n_ue: int, n_cells: int) -> None:
        """Allocate the per-(UE, cell) time-to-trigger counters."""
        super().__init__(spec, n_ue, n_cells)
        self._counter = np.zeros((n_ue, n_cells), dtype=int)

    def _fired(self, values: np.ndarray, serving: np.ndarray) -> np.ndarray:
        """Advance the TTT counters and report which cells have matured."""
        changed = self._reset_on_handover(serving)
        if changed.any():
            self._counter[changed] = 0
        condition = self._margin(values, serving) > self.spec.hysteresis
        self._counter = np.where(condition, self._counter + 1, 0)
        return self._counter >= self.spec.ttt

    def step(self, values: np.ndarray, serving: np.ndarray,
             load: np.ndarray) -> np.ndarray:
        """Emit a decision per UE.

        Args:
            values: ``(n_ue, n_cells)`` RSRP readings of this executor's channel.
            serving: ``(n_ue,)`` serving-cell index per UE.
            load: ``(n_cells,)`` number of UEs served by each cell.

        Returns:
            Array of shape ``(n_ue,)``; :data:`KEEP` or a target-cell index.
        """
        return self._pick(self._fired(values, serving), values)


@register_executor("load_aware")
class LoadAwareExecutor(A3Executor):
    """DESIGN 3.2: A3 and ``load[target] < load[serving]``, else keep serving."""

    def step(self, values: np.ndarray, serving: np.ndarray,
             load: np.ndarray) -> np.ndarray:
        """Fire only on cells less loaded than the serving cell."""
        fired = self._fired(values, serving)
        lighter = load[None, :] < load[serving][:, None]
        return self._pick(fired & lighter, values)


@register_executor("trend")
class TrendExecutor(Executor):
    """DESIGN 3.2: the difference rises strictly over the last ``ttt`` slots.

    A window of ``ttt`` samples is strictly increasing when the difference has
    risen in each of its ``ttt - 1`` transitions, so the run counter fires at
    ``ttt - 1``.  The rule also requires the difference to exceed the hysteresis
    at the last slot, which is what makes it a handover rule rather than a
    trend detector.
    """

    def __init__(self, spec: ExecutorSpec, n_ue: int, n_cells: int) -> None:
        """Allocate the rise counters and the previous-difference buffer."""
        super().__init__(spec, n_ue, n_cells)
        self._runs = np.zeros((n_ue, n_cells), dtype=int)
        self._previous = np.full((n_ue, n_cells), np.nan, dtype=float)

    def step(self, values: np.ndarray, serving: np.ndarray,
             load: np.ndarray) -> np.ndarray:
        """Advance the strictly-increasing run counters and emit a decision."""
        changed = self._reset_on_handover(serving)
        margin = self._margin(values, serving)
        if changed.any():
            self._runs[changed] = 0
            self._previous[changed] = np.nan
        rising = np.isfinite(self._previous) & np.isfinite(margin) & (margin > self._previous)
        self._runs = np.where(rising, self._runs + 1, 0)
        fired = (self._runs >= max(1, self.spec.ttt - 1)) & (margin > self.spec.hysteresis)
        self._previous = margin.copy()
        return self._pick(fired, values)


def make_executor(spec: ExecutorSpec, n_ue: int, n_cells: int) -> Executor:
    """Instantiate the rule named by ``spec.rule``.

    Raises:
        KeyError: If the rule is not registered.
    """
    if spec.rule not in EXECUTOR_REGISTRY:
        raise KeyError(f"unknown executor rule {spec.rule!r}; known: {sorted(EXECUTOR_REGISTRY)}")
    return EXECUTOR_REGISTRY[spec.rule](spec, n_ue, n_cells)


def base_spec(cfg: SimConfig, channel: int, name: str, rule: str = "a3") -> ExecutorSpec:
    """One rule family at the base A3 parameters on one channel."""
    return ExecutorSpec(
        rule=rule,
        channel=channel,
        hysteresis=cfg.rule.hysteresis,
        ttt=cfg.rule.ttt,
        label=name,
    )


#: Voting channels of every arm (DESIGN 3.3).  Arm 2' votes three decision
#: families on C1; the others vote the A3 rule on their channels.
ARM_VOTERS: dict[str, tuple[int, ...]] = {
    "single": (C1,),
    "model_dhr3": (C1, C1, C1),
    "obs_dhr": (C1, N, C4),
    "obs_dhr_phys": (C1, N, C4),
    "obs_dhr_phys_dither": (C1, N, C4),
    "cheap_phys": (C1, C4),
    "model_dhr_param": (C1, C1, C1),
}

#: Decision families of arm 2' (DESIGN 3.2), in voting order.
MODEL_FAMILIES: tuple[str, ...] = ("a3", "load_aware", "trend")

#: Channel names used to label executors in the report.
CHANNEL_LABELS: dict[int, str] = {C1: "C1", N: "N", C4: "C4"}


def arm_specs(cfg: SimConfig, arm: str) -> tuple[ExecutorSpec, ...]:
    """Executor bank of one arm (DESIGN 3.3).

    Raises:
        KeyError: If the arm key is unknown.
    """
    if arm not in ARM_VOTERS:
        raise KeyError(f"unknown arm {arm!r}; known: {sorted(ARM_VOTERS)}")
    if arm == "model_dhr3":
        return tuple(
            base_spec(cfg, C1, f"C1 {rule}", rule=rule) for rule in MODEL_FAMILIES
        )
    if arm == "model_dhr_param":
        pairs = zip(cfg.rule.variant_hysteresis, cfg.rule.variant_ttt, strict=True)
        return tuple(
            ExecutorSpec(rule="a3", channel=C1, hysteresis=hyst, ttt=ttt,
                         label=f"C1 a3 {hyst:g}/{ttt}")
            for hyst, ttt in pairs
        )
    return tuple(
        base_spec(cfg, channel, CHANNEL_LABELS[channel]) for channel in ARM_VOTERS[arm]
    )


def n_voters(arm: str) -> int:
    """Number of executors that vote in a slot for one arm (DESIGN 3.3)."""
    return len(ARM_VOTERS[arm])


def oracle_executor(cfg: SimConfig, n_ue: int, n_cells: int) -> Executor:
    """Base A3 rule on the *true* RSRP (DESIGN 6.1 counterfactual and missed handovers).

    The oracle never votes and is never billed; it answers "would the base rule
    on the true channels have taken this decision?", which is the counterfactual
    the attack-attributable metric subtracts and the reference the harm metrics
    compare against.
    """
    spec = ExecutorSpec(
        rule="a3",
        channel=-1,
        hysteresis=cfg.rule.hysteresis,
        ttt=cfg.rule.ttt,
        label="oracle(true)",
    )
    return make_executor(spec, n_ue, n_cells)


class ExecutorBank:
    """The executors of one arm, stepped together each slot."""

    def __init__(self, cfg: SimConfig, specs: tuple[ExecutorSpec, ...], n_ue: int,
                 n_cells: int) -> None:
        """Instantiate one executor per spec."""
        self.cfg = cfg
        self.specs = specs
        self.units = tuple(make_executor(spec, n_ue, n_cells) for spec in specs)
        self.channels = np.array([spec.channel for spec in specs], dtype=int)
        self._out = np.empty((len(specs), n_ue), dtype=int)

    def step(self, readings: np.ndarray, serving: np.ndarray,
             load: np.ndarray) -> np.ndarray:
        """Run every executor on its channel.

        Args:
            readings: ``(n_channels, n_ue, n_cells)`` readings of the slot.
            serving: ``(n_ue,)`` serving-cell index per UE.
            load: ``(n_cells,)`` number of UEs served by each cell.

        Returns:
            Array of shape ``(n_specs, n_ue)`` of decisions.
        """
        for index, unit in enumerate(self.units):
            self._out[index] = unit.step(readings[unit.spec.channel], serving, load)
        return self._out

    def __len__(self) -> int:
        """Number of executors in the bank."""
        return len(self.units)
