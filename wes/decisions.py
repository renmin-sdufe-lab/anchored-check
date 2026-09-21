"""Encoding of a handover decision and the arm roster (DESIGN 3.3).

A decision for one UE in one slot is an integer: :data:`KEEP` means "keep the
serving cell", any non-negative value is the index of the target cell.  The
encoding lives in its own module because the attacker (DESIGN 5), the executors
and the adjudicators (DESIGN 3.3) all speak it and none of them may depend on the
others.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

#: Decision value meaning "keep the serving cell".
KEEP: int = -1

#: Arm keys in DESIGN 3.3 order.
ARM_ORDER: tuple[str, ...] = (
    "single",
    "model_dhr3",
    "obs_dhr",
    "obs_dhr_phys",
    "obs_dhr_phys_dither",
    "cheap_phys",
    "model_dhr_param",
)

#: Human-readable arm labels used in tables and figures.
ARM_LABELS: dict[str, str] = {
    "single": "1 single (C1)",
    "model_dhr3": "2' model DHR (3 families on C1)",
    "obs_dhr": "3 obs DHR (C1, N, C4)",
    "obs_dhr_phys": "4 obs DHR + physics",
    "obs_dhr_phys_dither": "4d obs DHR + dithered physics",
    "cheap_phys": "5c cheap physics (C1, C4)",
    "model_dhr_param": "2p param DHR (3 A3 variants on C1)",
}


def is_handover(decision: np.ndarray) -> np.ndarray:
    """Boolean mask of decisions that move a UE to another cell."""
    return np.asarray(decision) != KEEP
