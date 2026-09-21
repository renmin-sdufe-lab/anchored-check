"""Analysis of a b2 output directory: tables, the gate-2 table and the figures.

Every number in ``summary.md`` and in every figure comes from ``runs.csv``.  The
PROTOCOL.md criteria G2-a, G2-b and G2-c are evaluated **literally**, on the
primary metric of DESIGN 6 (attack-attributable success per targeted slot) at
the pre-registered settings, with paired 95 % Student-t intervals over the ten
seeds.  The null-corrected reading demanded by DESIGN 6 is printed beside every
literal one, so a reader can see both.

Usage:
    uv run python analyze.py outputs/<YYYYmmdd_HHMMSS>_pilot_b2
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from figstyle import apply_style
from figures import figure_a, figure_b
from stats import GATE, NULL, PRIMARY, cell, net_paired, paired, ratio
from tables import (
    apparatus_table,
    below_null_note,
    check_decomposition_table,
    cost_table,
    delta_table,
    difference_table,
    false_positive_table,
    headline_table,
    identical_notes,
    mode_table,
    null_table,
    paired_qos_table,
    qos_table,
    ramp_table,
    runtime_note,
    secondary_table,
    sigma_rho_table,
    threshold_table,
)

logger = logging.getLogger("wes.analyze")

#: The σ_map values G2-a must hold at (PROTOCOL.md).
SIGMA_MAPS: tuple[float, ...] = (2.0, 4.0, 6.0)

#: Harm clauses of G2-c: metric, absolute budget, relative budget (DESIGN 6.2).
HARM_CLAUSES: tuple[tuple[str, float | None, float | None], ...] = (
    ("rsrp_deficit", 0.5, None),
    ("outage_share", None, 0.10),
)


@dataclass(frozen=True)
class Gate:
    """One gate criterion with its evidence."""

    key: str
    criterion: str
    evidence: str
    passed: bool

    def row(self) -> str:
        """Markdown row of the gate table."""
        verdict = "**PASS**" if self.passed else "**FAIL**"
        return f"| **{self.key}** | {self.criterion} | {self.evidence} | {verdict} |"


def gate_a(frame: pd.DataFrame) -> Gate:
    """G2-a: at ρ = 1, Δ = 10, every σ_map, arm 3 ≥ 0.5 × arm 1."""
    clauses: list[str] = []
    verdicts: list[bool] = []
    for sigma in SIGMA_MAPS:
        setting = {**GATE, "sigma_map": sigma}
        single = cell(frame, "single", PRIMARY, **setting)
        vote = cell(frame, "obs_dhr", PRIMARY, **setting)
        boundary = paired(frame, "obs_dhr", "single", PRIMARY, scale=0.5, **setting)
        net_boundary = net_paired(frame, "obs_dhr", "single", PRIMARY, scale=0.5, **setting)
        holds = bool(vote.mean >= 0.5 * single.mean)
        verdicts.append(holds)
        clauses.append(
            f"σ_map = {sigma:g}: arm 1 = {single}, arm 3 = {vote} "
            f"({ratio(vote, single):.3f} × arm 1, {'≥' if holds else '<'} 0.5×); "
            f"paired arm3 − 0.5·arm1 = {boundary}; null-corrected {net_boundary}"
        )
    return Gate(
        "G2-a",
        "ρ = 1, Δ = 10, every σ_map: arm 3 ≥ 0.5 × arm 1 on the primary metric",
        "; ".join(clauses),
        all(verdicts),
    )


def gate_b(frame: pd.DataFrame) -> Gate:
    """G2-b: at σ_map = 2, arm 4 ≤ 0.2 × arm 3 with the CI excluding the boundary."""
    setting = {**GATE, "sigma_map": 2.0}
    vote = cell(frame, "obs_dhr", PRIMARY, **setting)
    physics = cell(frame, "obs_dhr_phys", PRIMARY, **setting)
    boundary = paired(frame, "obs_dhr_phys", "obs_dhr", PRIMARY, scale=0.2, **setting)
    net_boundary = net_paired(frame, "obs_dhr_phys", "obs_dhr", PRIMARY, scale=0.2, **setting)
    false_exclusion = cell(frame, "obs_dhr_phys", "false_exclusion_rate", **setting)
    below = bool(physics.mean <= 0.2 * vote.mean and boundary.hi < 0.0)
    reported: list[str] = []
    for sigma in (4.0, 6.0):
        local = {**GATE, "sigma_map": sigma}
        other_vote = cell(frame, "obs_dhr", PRIMARY, **local)
        other_phys = cell(frame, "obs_dhr_phys", PRIMARY, **local)
        reported.append(
            f"σ_map = {sigma:g} (reported): arm 3 = {other_vote}, arm 4 = {other_phys} "
            f"({ratio(other_phys, other_vote):.3f} × arm 3)"
        )
    return Gate(
        "G2-b",
        "ρ = 1, Δ = 10, σ_map = 2, step: arm 4 ≤ 0.2 × arm 3 with the CI excluding "
        "the boundary **and** false exclusion ≤ 0.05",
        f"arm 3 = {vote}; arm 4 = {physics} ({ratio(physics, vote):.4f} × arm 3); "
        f"paired arm4 − 0.2·arm3 = {boundary} (CI wholly below 0: "
        f"{'yes' if boundary.hi < 0.0 else 'no'}); null-corrected {net_boundary}; "
        f"false exclusion = {false_exclusion} "
        f"(≤ 0.05: {'yes' if false_exclusion.mean <= 0.05 else 'no'}). "
        + "; ".join(reported),
        bool(below and false_exclusion.mean <= 0.05),
    )


def _harm_clause(frame: pd.DataFrame, arm: str, metric: str, absolute: float | None,
                 relative: float | None) -> tuple[str, bool]:
    """One G2-c harm clause of one arm against arm 1 at the Δ = 0 null."""
    base = cell(frame, "single", metric, **NULL)
    value = cell(frame, arm, metric, **NULL)
    diff = paired(frame, arm, "single", metric, **NULL)
    if absolute is not None:
        ok = bool(diff.mean <= absolute)
        budget = f"≤ +{absolute:g} dB"
    else:
        ok = bool(value.mean <= (1.0 + (relative or 0.0)) * base.mean)
        budget = f"≤ +{100 * (relative or 0.0):g} % relative"
    return (
        f"{metric} arm1 = {base}, {arm} = {value}, paired {diff} ({budget}: "
        f"{'yes' if ok else 'no'})",
        ok,
    )


def gate_c(frame: pd.DataFrame) -> Gate:
    """G2-c: at Δ = 0, arms 4 and 5c pay no more than the DESIGN 6.2 harm budget."""
    clauses: list[str] = []
    verdicts: list[bool] = []
    for arm in ("obs_dhr_phys", "cheap_phys"):
        for metric, absolute, relative in HARM_CLAUSES:
            clause, ok = _harm_clause(frame, arm, metric, absolute, relative)
            clauses.append(clause)
            verdicts.append(ok)
        missed = cell(frame, arm, "missed_handover_per_ue_slot", **NULL)
        attacked = cell(frame, arm, "missed_handover_per_ue_slot", **GATE)
        clauses.append(
            f"missed handovers / UE-slot {arm} = {missed} at Δ = 0 and {attacked} under "
            f"attack (reported, PROTOCOL.md sets no threshold)"
        )
    return Gate(
        "G2-c",
        "at Δ = 0, arms 4 and 5c against arm 1: `rsrp_deficit` not worse by more than "
        "0.5 dB and `outage_share` not worse by more than 10 % relative",
        "; ".join(clauses),
        all(verdicts),
    )


def gate_table(frame: pd.DataFrame) -> tuple[str, dict[str, bool]]:
    """Evaluate G2-a … G2-c literally and render the gate table."""
    gates = [gate_a(frame), gate_b(frame), gate_c(frame)]
    lines = ["\n### Gate-2 table (PROTOCOL.md, evaluated literally on the "
             "attack-attributable rate per targeted slot)\n"]
    lines.append("| gate | criterion | numbers | verdict |")
    lines.append("|---|---|---|---|")
    lines.extend(gate.row() for gate in gates)
    return "\n".join(lines) + "\n", {gate.key: gate.passed for gate in gates}


def reading(verdicts: dict[str, bool]) -> str:
    """The PROTOCOL.md reading that applies, in the specification's own words."""
    if not verdicts["G2-a"]:
        return (
            "**G2-a fails** → in the specification's own words: *\"G2-a fails → apparatus "
            "defect, found before anything is written.\"*"
        )
    if verdicts["G2-b"]:
        return (
            "**G2-a and G2-b pass** → in the specification's own words: *\"G2-a and G2-b "
            "pass → the paper is 'what anchors the check', with σ_map the design parameter "
            "and the ramp the boundary.\"*"
        )
    return (
        "**G2-a passes and G2-b fails** → in the specification's own words: *\"G2-a passes "
        "and G2-b fails at every σ_map → the paper is the observation-diversity boundary "
        "paper and physical consistency is a discussion item.\"*"
    )


def build_summary(frame: pd.DataFrame) -> tuple[str, dict[str, bool]]:
    """Assemble the whole ``summary.md`` body and the gate verdicts."""
    table, verdicts = gate_table(frame)
    parts = [
        "# WES majority-reach run b2: analysis summary\n",
        f"Runs: {runtime_note(frame)}\n",
        f"Gate setting: {GATE}\n",
        table,
        f"\n{reading(verdicts)}\n",
        null_table(frame),
        headline_table(frame),
        sigma_rho_table(frame),
        delta_table(frame),
        secondary_table(frame),
        qos_table(frame),
        paired_qos_table(frame),
        apparatus_table(frame),
        false_positive_table(frame),
        mode_table(frame),
        ramp_table(frame),
        cost_table(frame),
        difference_table(frame),
        check_decomposition_table(frame),
        threshold_table(frame),
    ]
    for heading, notes in (("Arms below their own null", below_null_note(frame)),
                           ("Arms that behave identically", identical_notes(frame))):
        if notes:
            parts.append(f"\n### {heading}\n")
            parts.extend(f"- {note}\n" for note in notes)
    return "\n".join(parts), verdicts


def main(argv: list[str] | None = None) -> Path:
    """Analyse one output directory and write ``summary.md`` plus the figures."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Analyse a WES b2 output directory.")
    parser.add_argument("outdir", type=Path, help="output directory containing runs.csv")
    args = parser.parse_args(argv)
    frame = pd.read_csv(args.outdir / "runs.csv")
    body, verdicts = build_summary(frame)
    (args.outdir / "summary.md").write_text(body)
    apply_style()
    figure_a(frame, args.outdir)
    figure_b(frame, args.outdir)
    logger.info("gate verdicts: %s", verdicts)
    logger.info("wrote %s", args.outdir / "summary.md")
    return args.outdir


if __name__ == "__main__":
    main()
