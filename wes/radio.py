"""Path loss, true RSRP and the load-based SINR/throughput proxy (DESIGN 1)."""

from __future__ import annotations

import logging

import numpy as np

from .config import SimConfig

logger = logging.getLogger(__name__)


def path_loss_db(distance_m: np.ndarray | float, cfg: SimConfig) -> np.ndarray:
    """Path loss ``pl_a + pl_b log10(d_km)`` with a minimum-distance guard (DESIGN 1)."""
    d = np.maximum(np.asarray(distance_m, dtype=float), cfg.radio.min_distance)
    return cfg.radio.pl_a + cfg.radio.pl_b * np.log10(d / 1000.0)


def distances(positions: np.ndarray, cells: np.ndarray) -> np.ndarray:
    """Euclidean UE-to-cell distances.

    Args:
        positions: ``(..., 2)`` UE positions.
        cells: ``(n_cells, 2)`` cell centres.

    Returns:
        Array of shape ``(..., n_cells)`` in metres.
    """
    return np.linalg.norm(positions[..., None, :] - cells, axis=-1)


def rsrp_true(cfg: SimConfig, positions: np.ndarray, cells: np.ndarray,
              shadow: np.ndarray) -> np.ndarray:
    """True RSRP ``P_tx - PL - shadowing`` for every (slot, UE, cell) (DESIGN 1).

    Args:
        cfg: Configuration tree.
        positions: ``(horizon, n_ue, 2)`` UE positions.
        cells: ``(n_cells, 2)`` cell centres.
        shadow: ``(horizon, n_ue, n_cells)`` shadowing in dB.

    Returns:
        Array of shape ``(horizon, n_ue, n_cells)`` in dBm.
    """
    d = np.linalg.norm(positions[:, :, None, :] - cells[None, None, :, :], axis=-1)
    return cfg.radio.tx_power_dbm - path_loss_db(d, cfg) - shadow


def dbm_to_linear(dbm: np.ndarray) -> np.ndarray:
    """Convert dBm to milliwatts."""
    return np.power(10.0, np.asarray(dbm, dtype=float) / 10.0)


def throughput_proxy(cfg: SimConfig, rsrp_row: np.ndarray, serving: np.ndarray,
                     load: np.ndarray) -> np.ndarray:
    """Load-based SINR proxy and per-UE throughput proxy (DESIGN 1).

    A neighbour cell interferes in proportion to its activity factor
    ``load_c / n_ue``; the served rate is ``log2(1 + SINR)`` shared by the
    serving cell's load.

    Args:
        cfg: Configuration tree.
        rsrp_row: ``(n_ue, n_cells)`` true RSRP in dBm for one slot.
        serving: ``(n_ue,)`` serving-cell index per UE.
        load: ``(n_cells,)`` number of UEs served by each cell.

    Returns:
        Array of shape ``(n_ue,)`` with the throughput proxy.
    """
    power = dbm_to_linear(rsrp_row)
    activity = load / max(1, int(rsrp_row.shape[0]))
    ue_index = np.arange(rsrp_row.shape[0])
    signal = power[ue_index, serving]
    total = power @ activity
    interference = total - activity[serving] * signal
    noise = dbm_to_linear(np.asarray(cfg.radio.noise_dbm))
    sinr = signal / (interference + noise)
    serving_load = np.maximum(load[serving], 1.0)
    return np.log2(1.0 + sinr) / serving_load
