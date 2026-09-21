"""The observation channels of DESIGN 2 and the composite network channel N.

Revision B2' replaces DESIGN 2's four network-wide measurements with channels a
real node can make:

* ``C1`` UE measurement report over all cells, ``RSRP_true + N(0, 1 dB)``;
* ``C2`` the serving gNB's own uplink (SRS) estimate of the **serving link only**
  (every other column is missing);
* ``C3`` each neighbour gNB's uplink estimate of **its own link**, delivered over
  Xn, ``RSRP_true + N(0, 2 dB)``;
* ``C4`` the operator's radio map evaluated at the position the serving gNB
  estimates, ``RSRP_true + eps_map`` with ``eps_map`` a Gaussian field carrying
  the shadowing's spatial correlation and standard deviation ``sigma_map``,
  independent of every measurement noise and available from slot 0.

The composite channel ``N`` is what the network can actually assemble: C2's
serving column plus C3's neighbour columns.  It is the second voter of
DESIGN 3.3 and the only one whose neighbour entries a transport-path attacker can
reach.  ``N`` depends on the serving cell, so it is composed per slot by
:func:`network_view` after the attacker has acted.

The clean channels are precomputed for the whole horizon, so they are common
random numbers across arms.  Poisoning (DESIGN 5) is applied on top, per slot.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from .config import SimConfig

logger = logging.getLogger(__name__)

#: Channel index order used everywhere in the package.  ``N`` is composed per
#: slot from C2 and C3 and is not drawn independently.
CHANNEL_NAMES: tuple[str, ...] = ("C1", "C2", "C3", "C4", "N")
C1, C2, C3, C4, N = 0, 1, 2, 3, 4
N_CHANNELS = len(CHANNEL_NAMES)

#: Channels a transport-path attacker can write to (DESIGN 5): the UE report and
#: the neighbour columns of the composite network channel.  C2's serving column
#: and the radio map C4 are unreachable.
POISONABLE: tuple[int, ...] = (C1, N)

#: Channels drawn directly from the physical truth; N is composed from C2 and C3.
DRAWN: tuple[int, ...] = (C1, C2, C3)


@dataclass(frozen=True)
class Channels:
    """Clean observation channels for one seed, precomputed over the horizon."""

    values: np.ndarray
    available: np.ndarray

    @property
    def horizon(self) -> int:
        """Number of simulated slots."""
        return int(self.values.shape[1])

    def slot(self, t: int) -> np.ndarray:
        """Copy of the ``(n_channels, n_ue, n_cells)`` readings of one slot."""
        return self.values[:, t].copy()


def build_channels(cfg: SimConfig, rsrp: np.ndarray, rng: np.random.Generator,
                   map_error: np.ndarray | None = None) -> Channels:
    """Draw the clean C1-C4 realisations for one seed (DESIGN 2).

    Args:
        cfg: Configuration tree.
        rsrp: ``(horizon, n_ue, n_cells)`` true RSRP in dBm.
        rng: Generator of the ``noise`` stream.
        map_error: ``(horizon, n_ue, n_cells)`` radio-map error field; zeros when
            omitted, which is only useful in unit tests.

    Returns:
        The precomputed :class:`Channels` bundle.  The ``N`` slice is filled with
        ``nan``: it is composed per slot by :func:`network_view`.
    """
    horizon, n_ue, n_cells = rsrp.shape
    values = np.full((N_CHANNELS, horizon, n_ue, n_cells), np.nan, dtype=float)
    for index, sigma in enumerate(cfg.channels.sigmas):
        values[index] = rsrp + rng.normal(0.0, sigma, size=rsrp.shape)
    error = np.zeros_like(rsrp) if map_error is None else map_error
    values[C4] = rsrp + error
    available = np.ones((N_CHANNELS, horizon, n_ue), dtype=bool)
    logger.debug("built %d channels over %d slots for %d UEs", N_CHANNELS, horizon, n_ue)
    return Channels(values=values, available=available)


def network_view(readings: np.ndarray, serving: np.ndarray) -> np.ndarray:
    """Mask C2 to the serving link and compose the network channel N (DESIGN 2).

    The serving gNB measures its own link and nothing else, so every other C2
    column is set to ``nan`` and can never be read by an executor or a check.
    ``N`` is the view the network can assemble from its own nodes: C2 at the
    serving cell, each neighbour's own C3 report elsewhere.

    Args:
        readings: ``(n_channels, n_ue, n_cells)`` readings of the slot; modified
            in place, so the caller must pass a copy it owns.
        serving: ``(n_ue,)`` serving-cell index per UE.

    Returns:
        The same array, with C2 masked and N composed.
    """
    rows = np.arange(readings.shape[1])
    serving_c2 = readings[C2, rows, serving].copy()
    readings[C2] = np.nan
    readings[C2, rows, serving] = serving_c2
    readings[N] = readings[C3]
    readings[N, rows, serving] = serving_c2
    return readings
