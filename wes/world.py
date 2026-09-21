"""RNG streams, cell layout, UE mobility and the correlated shadowing field (DESIGN 1).

The world is precomputed for the whole horizon before any arm runs, so every
physical realisation (positions, shadowing, report noise, attacker draws) is a
common random number across arms for a given seed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from .config import SimConfig

logger = logging.getLogger(__name__)

#: DESIGN 8: five independent streams spawned from one integer seed.
STREAM_NAMES: tuple[str, ...] = ("world", "mobility", "noise", "attacker", "policy")


def make_streams(seed: int) -> dict[str, np.random.Generator]:
    """Spawn the five named RNG streams for one run.

    Args:
        seed: Integer seed of the run.

    Returns:
        Mapping from stream name to an independent NumPy generator.
    """
    children = np.random.SeedSequence(seed).spawn(len(STREAM_NAMES))
    return {
        name: np.random.default_rng(child)
        for name, child in zip(STREAM_NAMES, children, strict=True)
    }


def cell_positions(cfg: SimConfig) -> np.ndarray:
    """Centres of the 7-cell hexagonal cluster.

    Cell 0 sits at the origin; cells 1-6 sit on a ring of radius equal to the
    inter-site distance at 60-degree spacing (DESIGN 1).

    Returns:
        Array of shape ``(n_cells, 2)`` in metres.
    """
    n_ring = cfg.world.n_cells - 1
    angles = np.arange(n_ring) * (2.0 * np.pi / n_ring)
    ring = cfg.world.isd * np.stack([np.cos(angles), np.sin(angles)], axis=-1)
    return np.vstack([np.zeros((1, 2)), ring])


def _wrap(pos: np.ndarray, half: float) -> np.ndarray:
    """Fold positions back into the square torus of half-side ``half``."""
    return ((pos + half) % (2.0 * half)) - half


def simulate_mobility(cfg: SimConfig, rng: np.random.Generator) -> np.ndarray:
    """Random-direction mobility with toroidal wrap-around (DESIGN 1).

    Each UE draws a heading, a speed in ``[speed_min, speed_max]`` and a leg
    length; on completing a leg it redraws all three.  Positions wrap at the
    cluster edge, which is the specification's wrap-around.

    Returns:
        Array of shape ``(horizon, n_ue, 2)`` in metres.
    """
    world, n_ue, horizon = cfg.world, cfg.world.n_ue, cfg.sim.horizon
    half, step_seconds = world.area_half, cfg.sim.slot_seconds
    positions = np.empty((horizon, n_ue, 2), dtype=float)
    pos = rng.uniform(-half, half, size=(n_ue, 2))
    heading = rng.uniform(0.0, 2.0 * np.pi, size=n_ue)
    speed = rng.uniform(world.speed_min, world.speed_max, size=n_ue)
    remaining = rng.uniform(world.leg_min, world.leg_max, size=n_ue)
    for t in range(horizon):
        positions[t] = pos
        step = speed * step_seconds
        direction = np.stack([np.cos(heading), np.sin(heading)], axis=-1)
        pos = _wrap(pos + step[:, None] * direction, half)
        remaining = remaining - step
        done = remaining <= 0.0
        n_done = int(done.sum())
        if n_done:
            heading[done] = rng.uniform(0.0, 2.0 * np.pi, size=n_done)
            speed[done] = rng.uniform(world.speed_min, world.speed_max, size=n_done)
            remaining[done] = rng.uniform(world.leg_min, world.leg_max, size=n_done)
    logger.debug("simulated mobility for %d UEs over %d slots", n_ue, horizon)
    return positions


def correlated_field(cfg: SimConfig, positions: np.ndarray, rng: np.random.Generator,
                     sigma: float, cell_corr: float) -> np.ndarray:
    """Gudmundson field of standard deviation ``sigma`` along the trajectories.

    The field of one (UE, cell) pair follows
    ``s(t) = a s(t-1) + sqrt(1 - a^2) sigma eps`` with ``a = exp(-dd / d_corr)``
    and ``dd`` the distance the UE moved in the slot, so the spatial
    autocorrelation is ``exp(-d / d_corr)`` along the trajectory.  Because
    ``sigma`` only scales the innovations, two fields drawn from the same
    generator state with different ``sigma`` are exact multiples of each other,
    which keeps the DESIGN 7 sweep over ``sigma_map`` a common random number.

    Args:
        cfg: Configuration tree.
        positions: ``(horizon, n_ue, 2)`` UE positions.
        rng: Generator to draw the innovations from.
        sigma: Standard deviation of the field in dB.
        cell_corr: Fraction of the innovation shared across cells.

    Returns:
        Array of shape ``(horizon, n_ue, n_cells)`` in dB.
    """
    horizon, n_ue = positions.shape[0], positions.shape[1]
    n_cells = cfg.world.n_cells
    decorr = cfg.radio.shadow_decorr
    field = np.empty((horizon, n_ue, n_cells), dtype=float)
    state = _innovation(rng, n_ue, n_cells, cell_corr) * sigma
    field[0] = state
    steps = np.linalg.norm(np.diff(positions, axis=0), axis=-1)
    for t in range(1, horizon):
        alpha = np.exp(-steps[t - 1] / decorr)[:, None]
        eps = _innovation(rng, n_ue, n_cells, cell_corr)
        state = alpha * state + np.sqrt(np.maximum(1.0 - alpha**2, 0.0)) * sigma * eps
        field[t] = state
    return field


def shadow_field(
    cfg: SimConfig, positions: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """Gudmundson log-normal shadowing with exponential spatial correlation (DESIGN 1).

    The shadowing of one (UE, cell) pair follows
    ``s(t) = a s(t-1) + sqrt(1 - a^2) sigma eps`` with ``a = exp(-dd / d_corr)``
    and ``dd`` the distance the UE moved in the slot, so the spatial
    autocorrelation is ``exp(-d / d_corr)`` along the trajectory.  Cells share a
    fraction ``shadow_cell_corr`` of the innovation; the
    configured default 0.0 keeps DESIGN 1's stated independence across cells and
    reproduces the b0 world bit-for-bit.

    Args:
        cfg: Configuration tree.
        positions: ``(horizon, n_ue, 2)`` UE positions.
        rng: Generator of the ``world`` stream.

    Returns:
        Array of shape ``(horizon, n_ue, n_cells)`` in dB.
    """
    return correlated_field(cfg, positions, rng, cfg.radio.shadow_sigma,
                            float(cfg.radio.shadow_cell_corr))


def map_error_field(
    cfg: SimConfig, positions: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    """DESIGN 2's ``eps_map``: the radio map's error field.

    The operator's map predicts every cell's RSRP at the position the serving
    gNB estimates by uplink positioning.  Its error is modelled as a Gaussian
    field with the shadowing's spatial correlation and standard deviation
    ``channels.sigma_map``; position error is absorbed in that standard
    deviation.  It is drawn after the shadowing from the same ``world`` stream,
    so the shadowing realisation is unchanged by the sweep over ``sigma_map``.
    """
    return correlated_field(cfg, positions, rng, cfg.channels.sigma_map,
                            float(cfg.radio.shadow_cell_corr))


def _innovation(rng: np.random.Generator, n_ue: int, n_cells: int,
                cell_corr: float) -> np.ndarray:
    """Unit-variance shadowing innovation with inter-cell correlation ``cell_corr``."""
    per_cell = rng.normal(0.0, 1.0, size=(n_ue, n_cells))
    if cell_corr <= 0.0:
        return per_cell
    common = rng.normal(0.0, 1.0, size=(n_ue, 1))
    return np.sqrt(cell_corr) * common + np.sqrt(1.0 - cell_corr) * per_cell


@dataclass(frozen=True)
class World:
    """Precomputed physical realisation of one seed (identical across arms)."""

    cells: np.ndarray
    positions: np.ndarray
    shadow: np.ndarray
    map_error: np.ndarray

    @property
    def horizon(self) -> int:
        """Number of simulated slots."""
        return int(self.positions.shape[0])

    @property
    def n_ue(self) -> int:
        """Number of UEs."""
        return int(self.positions.shape[1])

    @property
    def n_cells(self) -> int:
        """Number of cells."""
        return int(self.cells.shape[0])


def build_world(cfg: SimConfig, streams: dict[str, np.random.Generator]) -> World:
    """Build the cell layout, the UE trajectories and the shadowing field."""
    cells = cell_positions(cfg)
    positions = simulate_mobility(cfg, streams["mobility"])
    shadow = shadow_field(cfg, positions, streams["world"])
    map_error = map_error_field(cfg, positions, streams["world"])
    logger.debug("built world: %d cells, %d UEs", cells.shape[0], positions.shape[1])
    return World(cells=cells, positions=positions, shadow=shadow, map_error=map_error)
