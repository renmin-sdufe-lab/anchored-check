"""Observation-channel diversity for handover security in a 7-cell RAN.

The package implements DESIGN.md: a 7-cell handover world (:mod:`wes.world`,
:mod:`wes.radio`), four observation channels (:mod:`wes.channels`), a telemetry
poisoning attacker (:mod:`wes.attacker`), A3 handover executors
(:mod:`wes.executors`), adjudicators (:mod:`wes.adjudicate`), schedulers
(:mod:`wes.scheduler`) and the slot-stepped engine (:mod:`wes.engine`).
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
