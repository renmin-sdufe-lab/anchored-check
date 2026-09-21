"""Per-run metric collection and the row written to ``runs.csv`` (DESIGN 6).

Revision B2' makes attack-attributable success **per targeted slot** the primary
security metric, because it is monotone in the falsification magnitude,
and keeps the per-opportunity rate beside it with both the time-to-trigger and
the instantaneous denominator.  Harm is reported as wrong handovers and
ping-pongs per executed handover, missed handovers per UE-slot and per oracle
event, and the three user-visible quantities of DESIGN 6.2: the RSRP
deficit against the oracle's serving choice, the outage share and the
wrong-cell share.  Detection counts the exclusion of any channel the attacker
actually falsified.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from .channels import CHANNEL_NAMES, POISONABLE
from .checks import CHECK_NAMES

logger = logging.getLogger(__name__)


class ByteLedger:
    """Measurement-signalling bytes charged per channel (DESIGN 6.4)."""

    def __init__(self) -> None:
        """Start every channel counter at zero."""
        self.totals: dict[str, float] = dict.fromkeys(CHANNEL_NAMES, 0.0)

    def charge(self, channel: int, nbytes: float, count: int) -> float:
        """Charge ``nbytes * count`` to one channel and return the amount.

        Raises:
            IndexError: If ``channel`` is not a valid channel index.
        """
        amount = float(nbytes) * int(count)
        self.totals[CHANNEL_NAMES[channel]] += amount
        return amount

    @property
    def total(self) -> float:
        """All measurement bytes charged in the metric window."""
        return float(sum(self.totals.values()))

    def total_excluding(self, channels: tuple[int, ...]) -> float:
        """Bytes charged outside the given channels (the over-the-air split)."""
        skip = {CHANNEL_NAMES[c] for c in channels}
        return float(sum(v for k, v in self.totals.items() if k not in skip))


@dataclass(frozen=True)
class RunResult:
    """Every DESIGN 6 metric of one run, flattened into a ``runs.csv`` row."""

    arm: str
    seed: int
    p: float
    delta: float
    rho: float
    sigma_map: float
    mode: str
    ramp_slots: int
    checks: str
    z: float
    persistence_slots: int
    n_targets: int
    n_voting_channels: int
    majority_reachable: bool
    attack_success_attr: float
    attack_success_opp: float
    attack_success_opp_inst: float
    attack_success: float
    actionable_share: float
    actionable_share_inst: float
    detect_rate: float
    detect_rate_actionable: float
    wrong_handover_rate: float
    pingpong_rate: float
    wrong_handover_per_ho: float
    pingpong_per_ho: float
    handover_rate: float
    missed_handover_rate: float
    missed_handover_per_ue_slot: float
    oracle_handover_rate: float
    rsrp_deficit: float
    outage_share: float
    wrong_cell_share: float
    false_exclusion_rate: float
    false_exclusion_rate_ch: float
    fe_serving_reciprocity: float
    fe_neighbour_reciprocity: float
    fe_map: float
    fe_rate: float
    fallback_rate: float
    mean_voters: float
    throughput: float
    bytes_per_ue_s: float
    bytes_ota_per_ue_s: float
    compute_per_decision: float
    thr_serving_reciprocity: float
    thr_neighbour_reciprocity: float
    thr_map: float
    thr_rate: float
    sigma_serving_recip_hat: float
    sigma_neighbour_recip_hat: float
    sigma_map_diff_hat: float
    sigma_rate_hat: float
    sigma_c1_hat: float
    sigma_map_hat: float
    runtime_seconds: float

    def to_row(self) -> dict[str, Any]:
        """Flat mapping for the pandas frame behind ``runs.csv``."""
        return asdict(self)


class MissedHandoverTracker:
    """Counts oracle handover *events* an arm does not execute (DESIGN 6.2).

    The oracle runs on the true RSRP against the arm's own serving assignment,
    so it keeps recommending the same handover for as long as the condition
    holds.  Counting slots would therefore score one declined handover many
    times; this tracker counts each recommendation once and marks it matched if
    the arm executes the same handover within ``ttt`` slots.
    """

    def __init__(self, n_ue: int, ttt: int) -> None:
        """Start with no outstanding recommendation."""
        self.ttt = int(ttt)
        self.pending = np.full(n_ue, -1, dtype=int)
        self.deadline = np.zeros(n_ue, dtype=int)
        self.open = np.zeros(n_ue, dtype=bool)
        self.events = 0
        self.missed = 0

    def observe(self, t: int, oracle: np.ndarray, scoring: bool) -> None:
        """Register this slot's oracle recommendation and expire stale ones.

        A recommendation is opened when the oracle names a target it was not
        already recommending, and is closed exactly once, by a matching
        handover (:meth:`resolve`), by the oracle changing its mind, or by the
        ``ttt``-slot deadline passing.  A recommendation the oracle withdraws is
        not a miss.

        Args:
            t: Slot index.
            oracle: ``(n_ue,)`` oracle decision of the slot.
            scoring: Whether the slot is inside the metric window.
        """
        expired = self.open & (t > self.deadline)
        fresh = (oracle >= 0) & (oracle != self.pending)
        superseded = fresh & self.open & ~expired
        withdrawn = (oracle < 0) & self.open & ~expired
        if scoring:
            self.missed += int((expired | superseded).sum())
            self.events += int(fresh.sum())
        self.open = np.where(expired | superseded | withdrawn, False, self.open)
        self.pending = np.where(oracle < 0, -1, self.pending)
        self.open = np.where(fresh, True, self.open)
        self.pending = np.where(fresh, oracle, self.pending)
        self.deadline = np.where(fresh, t + self.ttt, self.deadline)

    def resolve(self, moving: np.ndarray, target: np.ndarray, scoring: bool) -> None:
        """Close outstanding recommendations against the handovers just executed."""
        if moving.size == 0:
            return
        pending, is_open = self.pending[moving], self.open[moving]
        if scoring:
            self.missed += int((is_open & (pending != target)).sum())
        self.pending[moving] = -1
        self.open[moving] = False


@dataclass
class MetricsCollector:
    """Accumulates the DESIGN 6 quantities over the metric window of one run."""

    warmup: int
    slot_seconds: float
    n_ue: int
    ue_slots: int = 0
    targeted_slots: int = 0
    opportunity_slots: int = 0
    opportunity_slots_inst: int = 0
    success_slots: int = 0
    attributable_slots: int = 0
    attributable_opportunity: int = 0
    attributable_opportunity_inst: int = 0
    detected_slots: int = 0
    detected_actionable: int = 0
    clean_slots: int = 0
    clean_excluded_slots: int = 0
    clean_excluded_channel_slots: int = 0
    clean_fired: np.ndarray = field(
        default_factory=lambda: np.zeros(len(CHECK_NAMES), dtype=float)
    )
    handovers: int = 0
    wrong_handovers: int = 0
    pingpongs: int = 0
    fallbacks: int = 0
    voters_sum: float = 0.0
    throughput_sum: float = 0.0
    deficit_sum: float = 0.0
    outage_slots: int = 0
    wrong_cell_slots: int = 0
    check_units_sum: float = 0.0

    def observe(self, targets: np.ndarray, success: np.ndarray, attributable: np.ndarray,
                opportunity: np.ndarray, opportunity_instant: np.ndarray,
                detected: np.ndarray, excluded: np.ndarray, fired: np.ndarray,
                voters: np.ndarray, fallback: np.ndarray, throughput: np.ndarray,
                deficit: np.ndarray, outage: np.ndarray, wrong_cell: np.ndarray,
                check_units: float) -> None:
        """Accumulate one post-warm-up slot.

        Args:
            targets: ``(n_ue,)`` attacker-targeted mask.
            success: ``(n_ue,)`` verdicts matching the attacker's intent.
            attributable: ``(n_ue,)`` successes the falsification actually caused.
            opportunity: ``(n_ue,)`` targeted slots where the falsified report
                would trigger the intended handover under the base rule with TTT.
            opportunity_instant: ``(n_ue,)`` the same without the TTT.
            detected: ``(n_ue,)`` targeted slots in which a falsified channel was
                excluded.
            excluded: ``(n_channels, n_ue)`` exclusion mask.
            fired: ``(n_checks, n_ue)`` per-check firing mask.
            voters: ``(n_ue,)`` number of channels that voted.
            fallback: ``(n_ue,)`` mask of UEs decided by the DESIGN 3.4 fallback.
            throughput: ``(n_ue,)`` throughput proxy.
            deficit: ``(n_ue,)`` RSRP deficit against the oracle's serving choice.
            outage: ``(n_ue,)`` mask of UEs below the outage threshold.
            wrong_cell: ``(n_ue,)`` mask of UEs not on the oracle's choice.
            check_units: Adjudication compute units charged this slot per decision.
        """
        clean = ~targets
        poisonable = list(POISONABLE)
        self.ue_slots += self.n_ue
        self.targeted_slots += int(targets.sum())
        self.opportunity_slots += int(opportunity.sum())
        self.opportunity_slots_inst += int(opportunity_instant.sum())
        self.success_slots += int(success.sum())
        self.attributable_slots += int(attributable.sum())
        self.attributable_opportunity += int((attributable & opportunity).sum())
        self.attributable_opportunity_inst += int((attributable & opportunity_instant).sum())
        self.detected_slots += int((targets & detected).sum())
        self.detected_actionable += int((opportunity & detected).sum())
        self.clean_slots += int(clean.sum())
        self.clean_excluded_slots += int((clean & excluded[poisonable].any(axis=0)).sum())
        self.clean_excluded_channel_slots += int(excluded[poisonable][:, clean].sum())
        self.clean_fired += fired[:, clean].sum(axis=1)
        self.fallbacks += int(fallback.sum())
        self.voters_sum += float(voters.sum())
        self.throughput_sum += float(throughput.sum())
        self.deficit_sum += float(deficit.sum())
        self.outage_slots += int(outage.sum())
        self.wrong_cell_slots += int(wrong_cell.sum())
        self.check_units_sum += float(check_units)

    def observe_handovers(self, wrong: np.ndarray, pingpong: np.ndarray) -> None:
        """Accumulate the handovers executed in one post-warm-up slot."""
        self.handovers += int(wrong.size)
        self.wrong_handovers += int(wrong.sum())
        self.pingpongs += int(pingpong.sum())

    @staticmethod
    def _ratio(numerator: float, denominator: float) -> float:
        """Safe ratio; ``nan`` when the denominator is zero."""
        return float(numerator) / float(denominator) if denominator else float("nan")

    def mean_check_units(self, scored_slots: int) -> float:
        """Adjudication units per decision, averaged over scored slots."""
        return self._ratio(self.check_units_sum, scored_slots)

    def rates(self, missed: MissedHandoverTracker) -> dict[str, float]:
        """Every rate DESIGN 6 asks for, as a flat mapping."""
        clean_slots = self.clean_slots
        fired = {
            f"fe_{name}": self._ratio(self.clean_fired[i], clean_slots)
            for i, name in enumerate(CHECK_NAMES)
        }
        return {
            "attack_success_attr": self._ratio(self.attributable_slots, self.targeted_slots),
            "attack_success_opp": self._ratio(
                self.attributable_opportunity, self.opportunity_slots
            ),
            "attack_success_opp_inst": self._ratio(
                self.attributable_opportunity_inst, self.opportunity_slots_inst
            ),
            "attack_success": self._ratio(self.success_slots, self.targeted_slots),
            "actionable_share": self._ratio(self.opportunity_slots, self.targeted_slots),
            "actionable_share_inst": self._ratio(
                self.opportunity_slots_inst, self.targeted_slots
            ),
            "detect_rate": self._ratio(self.detected_slots, self.targeted_slots),
            "detect_rate_actionable": self._ratio(
                self.detected_actionable, self.opportunity_slots
            ),
            "wrong_handover_rate": self._ratio(self.wrong_handovers, self.ue_slots),
            "pingpong_rate": self._ratio(self.pingpongs, self.ue_slots),
            "wrong_handover_per_ho": self._ratio(self.wrong_handovers, self.handovers),
            "pingpong_per_ho": self._ratio(self.pingpongs, self.handovers),
            "handover_rate": self._ratio(self.handovers, self.ue_slots),
            "missed_handover_rate": self._ratio(missed.missed, missed.events),
            "missed_handover_per_ue_slot": self._ratio(missed.missed, self.ue_slots),
            "oracle_handover_rate": self._ratio(missed.events, self.ue_slots),
            "rsrp_deficit": self._ratio(self.deficit_sum, self.ue_slots),
            "outage_share": self._ratio(self.outage_slots, self.ue_slots),
            "wrong_cell_share": self._ratio(self.wrong_cell_slots, self.ue_slots),
            "false_exclusion_rate": self._ratio(self.clean_excluded_slots, clean_slots),
            "false_exclusion_rate_ch": self._ratio(
                self.clean_excluded_channel_slots, clean_slots * len(POISONABLE)
            ),
            "fallback_rate": self._ratio(self.fallbacks, self.ue_slots),
            "mean_voters": self._ratio(self.voters_sum, self.ue_slots),
            "throughput": self._ratio(self.throughput_sum, self.ue_slots),
            **fired,
        }
