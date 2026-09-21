"""Markdown tables of the b2 analysis, all computed from ``runs.csv``."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from figstyle import ARM_LABELS
from stats import (
    GATE,
    METRIC_LABELS,
    METRICS,
    NULL,
    PRIMARY,
    SECONDARY,
    cell,
    identical_arms,
    net,
    net_paired,
    paired,
    select,
)
from wes.checks import CHECK_NAMES, CHECK_TESTS, analytic_floor
from wes.decisions import ARM_ORDER

logger = logging.getLogger(__name__)

#: Arms of the DESIGN 7 sigma_map x rho table.
SWEEP_ARMS: tuple[str, ...] = ("single", "obs_dhr", "obs_dhr_phys", "cheap_phys")

COST_METRICS: tuple[str, ...] = (
    "bytes_per_ue_s",
    "bytes_ota_per_ue_s",
    "compute_per_decision",
)

HARM_METRICS: tuple[str, ...] = (
    "rsrp_deficit",
    "outage_share",
    "wrong_cell_share",
    "wrong_handover_per_ho",
    "pingpong_per_ho",
    "missed_handover_per_ue_slot",
    "missed_handover_rate",
    "handover_rate",
    "fallback_rate",
    "throughput",
)

APPARATUS_METRICS: tuple[str, ...] = (
    "actionable_share",
    "actionable_share_inst",
    "detect_rate_actionable",
    "false_exclusion_rate",
    "mean_voters",
)

THRESHOLD_COLUMNS: tuple[str, ...] = tuple(f"thr_{name}" for name in CHECK_NAMES)


def _header(columns: list[str]) -> list[str]:
    """Markdown table header for the given column names."""
    return ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]


def _values(frame: pd.DataFrame, arm: str, metrics: tuple[str, ...],
            setting: dict[str, Any]) -> list[str]:
    """Rendered interval per metric for one arm in one setting."""
    return [str(cell(frame, arm, metric, **setting)) for metric in metrics]


def headline_table(frame: pd.DataFrame) -> str:
    """Mean +- 95 % CI of every headline metric at the gate setting."""
    lines = ["\n### Headline metrics at the gate setting "
             "(p = 0.2, Δ = 10 dB, ρ = 1, σ_map = 2 dB, trap; mean ± 95 % CI)\n"]
    lines += _header(["arm"] + [METRIC_LABELS[m] for m in METRICS])
    for arm in ARM_ORDER:
        lines.append(f"| {ARM_LABELS[arm]} | " + " | ".join(_values(frame, arm, METRICS, GATE))
                     + " |")
    return "\n".join(lines) + "\n"


def null_table(frame: pd.DataFrame) -> str:
    """The Δ = 0 null control every ratio of DESIGN 6 is taken against."""
    metrics = (PRIMARY, SECONDARY, "actionable_share", "false_exclusion_rate",
               "rsrp_deficit", "outage_share", "throughput")
    lines = ["\n### Δ = 0 null control (attacker present, falsification zero; σ_map = 2)\n"]
    lines += _header(["arm"] + [METRIC_LABELS[m] for m in metrics])
    for arm in ARM_ORDER:
        lines.append(f"| {ARM_LABELS[arm]} | "
                     + " | ".join(_values(frame, arm, metrics, NULL)) + " |")
    return "\n".join(lines) + "\n"


def sigma_rho_table(frame: pd.DataFrame, metric: str = PRIMARY,
                    arms: tuple[str, ...] = SWEEP_ARMS) -> str:
    """DESIGN 7's σ_map × ρ grid with each arm's own Δ = 0 null."""
    setting = {k: v for k, v in GATE.items() if k not in ("rho", "sigma_map")}
    rows = select(frame, **setting)
    sigmas, rhos = sorted(rows.sigma_map.unique()), sorted(rows.rho.unique())
    lines = [f"\n### {METRIC_LABELS[metric]} over σ_map × ρ (Δ = 10 dB, trap)\n"]
    lines += _header(["arm", "σ_map"] + [f"ρ = {r:g}" for r in rhos] + ["Δ = 0 null"])
    for arm in arms:
        for sigma in sigmas:
            local = {**setting, "sigma_map": float(sigma)}
            cells = [str(cell(frame, arm, metric, **{**local, "rho": float(r)}))
                     for r in rhos]
            null = str(cell(frame, arm, metric, **{**local, "rho": 1.0, "delta": 0.0}))
            lines.append(f"| {ARM_LABELS[arm]} | {sigma:g} | "
                         + " | ".join([*cells, null]) + " |")
    return "\n".join(lines) + "\n"


def delta_table(frame: pd.DataFrame, metric: str = PRIMARY) -> str:
    """The Δ boundary per σ_map, with the Δ = 0 null in the first column."""
    setting = {k: v for k, v in GATE.items() if k not in ("delta", "sigma_map")}
    rows = select(frame, **setting)
    deltas, sigmas = sorted(rows.delta.unique()), sorted(rows.sigma_map.unique())
    lines = [f"\n### {METRIC_LABELS[metric]} against Δ (ρ = 1, trap)\n"]
    lines += _header(["arm", "σ_map"]
                     + [("Δ = 0 (null)" if d == 0 else f"Δ = {d:g} dB") for d in deltas])
    for arm in ARM_ORDER:
        for sigma in sigmas:
            local = {**setting, "sigma_map": float(sigma)}
            cells = [str(cell(frame, arm, metric, **{**local, "delta": float(d)}))
                     for d in deltas]
            lines.append(f"| {ARM_LABELS[arm]} | {sigma:g} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def mode_table(frame: pd.DataFrame) -> str:
    """Both attacker modes with their nulls (DESIGN 6.1)."""
    setting = {k: v for k, v in GATE.items() if k not in ("mode", "rho")}
    modes = [m for m in ("trap", "pingpong") if m in set(frame["mode"])]
    lines = ["\n### Both attacker modes with the Δ = 0 null "
             "(σ_map = 2, ρ = 0; ping-pong is only run at ρ = 0)\n"]
    lines += _header(["arm"] + [f"{label} ({mode})" for mode in modes
                                for label in (METRIC_LABELS[PRIMARY], "Δ = 0 null",
                                              "wrong HO / handover")])
    for arm in ARM_ORDER:
        cells: list[str] = []
        for mode in modes:
            local = {**setting, "mode": mode, "rho": 0.0}
            cells.append(str(cell(frame, arm, PRIMARY, **local)))
            cells.append(str(cell(frame, arm, PRIMARY, **{**local, "delta": 0.0})))
            cells.append(str(cell(frame, arm, "wrong_handover_per_ho", **local)))
        lines.append(f"| {ARM_LABELS[arm]} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def ramp_table(frame: pd.DataFrame) -> str:
    """DESIGN 5's sticky ramp at Δ = 10, ρ = 1 (reported, not gated)."""
    setting = {k: v for k, v in GATE.items() if k not in ("ramp_slots", "sigma_map")}
    rows = select(frame, **setting)
    ramps, sigmas = sorted(rows.ramp_slots.unique()), sorted(rows.sigma_map.unique())
    if len(ramps) < 2:
        return ""
    lines = ["\n### Sticky ramp attacker (DESIGN 5; reported, not gated)\n"]
    lines += _header(["arm", "σ_map"] + [f"ramp = {int(r)} slot(s)" for r in ramps]
                     + [f"detection, ramp = {int(r)}" for r in ramps]
                     + [f"actionable share, ramp = {int(r)}" for r in ramps])
    for arm in ("single", "obs_dhr", "obs_dhr_phys"):
        for sigma in sigmas:
            local = {**setting, "sigma_map": float(sigma)}
            if any(cell(frame, arm, PRIMARY, **{**local, "ramp_slots": int(r)}).n == 0
                   for r in ramps):
                continue
            cells = [str(cell(frame, arm, PRIMARY, **{**local, "ramp_slots": int(r)}))
                     for r in ramps]
            for metric in ("detect_rate_actionable", "actionable_share"):
                cells += [
                    f"{cell(frame, arm, metric, **{**local, 'ramp_slots': int(r)}).mean:.3f}"
                    for r in ramps
                ]
            lines.append(f"| {ARM_LABELS[arm]} | {sigma:g} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def qos_table(frame: pd.DataFrame) -> str:
    """DESIGN 6.2 harm metrics at Δ = 0 and under attack."""
    lines = ["\n### Harm and quality of service: Δ = 0 (cost of the defence) and "
             "Δ = 10, ρ = 1 (its value); σ_map = 2\n"]
    lines += _header(["arm", "Δ"] + [METRIC_LABELS[m] for m in HARM_METRICS])
    for arm in ARM_ORDER:
        for label, setting in (("0 (null)", NULL), ("10", GATE)):
            lines.append(f"| {ARM_LABELS[arm]} | {label} | "
                         + " | ".join(_values(frame, arm, HARM_METRICS, setting)) + " |")
    return "\n".join(lines) + "\n"


def cost_table(frame: pd.DataFrame) -> str:
    """Measurement bytes and compute units per arm, with the ratio to arm 1."""
    lines = ["\n### Cost per arm at the gate setting (DESIGN 6: reported, not gated)\n"]
    lines += _header(
        ["arm"] + [METRIC_LABELS[m] for m in COST_METRICS]
        + ["OTA bytes / arm 1", "compute / arm 1"]
    )
    base_ota = cell(frame, "single", "bytes_ota_per_ue_s", **GATE).mean
    base_compute = cell(frame, "single", "compute_per_decision", **GATE).mean
    for arm in ARM_ORDER:
        values = [cell(frame, arm, metric, **GATE).mean for metric in COST_METRICS]
        rendered = [f"{v:.1f}" for v in values]
        rendered.append(f"{values[1] / base_ota:.2f}x" if base_ota else "n/a")
        rendered.append(f"{values[2] / base_compute:.2f}x" if base_compute else "n/a")
        lines.append(f"| {ARM_LABELS[arm]} | " + " | ".join(rendered) + " |")
    return "\n".join(lines) + "\n"


def apparatus_table(frame: pd.DataFrame) -> str:
    """Detection, false exclusion and the actionable share at the gate setting."""
    lines = ["\n### Apparatus diagnostics at the gate setting\n"]
    lines += _header(["arm", "majority reachable"]
                     + [METRIC_LABELS[m] for m in APPARATUS_METRICS])
    for arm in ARM_ORDER:
        rows = select(frame, arm=arm, **GATE)
        flag = "n/a" if rows.empty else ("yes" if bool(rows.majority_reachable.iloc[0])
                                         else "no")
        lines.append(f"| {ARM_LABELS[arm]} | {flag} | "
                     + " | ".join(_values(frame, arm, APPARATUS_METRICS, GATE)) + " |")
    return "\n".join(lines) + "\n"


def false_positive_table(frame: pd.DataFrame) -> str:
    """Measured false exclusion per check beside its analytic 3σ floor (DESIGN 4)."""
    rows = select(frame, arm="obs_dhr_phys", **NULL)
    if rows.empty:
        return ""
    z = float(rows["z"].iloc[0])
    persistence = int(rows["persistence_slots"].iloc[0])
    lines = ["\n### False exclusion per check against its analytic floor "
             "(arm 4, Δ = 0, clean UE-slots)\n"]
    lines += _header(["check", "tests / UE-slot", "measured", "analytic floor"])
    for name in CHECK_NAMES:
        measured = cell(frame, "obs_dhr_phys", f"fe_{name}", **NULL)
        floor = analytic_floor(z, CHECK_TESTS[name], persistence)
        lines.append(f"| {name} | {CHECK_TESTS[name]} | {measured} | {floor:.2e} |")
    union = cell(frame, "obs_dhr_phys", "false_exclusion_rate", **NULL)
    lines.append(f"| any check (union) | n/a | {union} | n/a |")
    return "\n".join(lines) + "\n"


def check_decomposition_table(frame: pd.DataFrame) -> str:
    """Each check alone, and the no-persistence variant (diagnostic, not a gate)."""
    setting = {k: v for k, v in GATE.items()
               if k not in ("check_set", "rho", "sigma_map", "persistence_slots")}
    rows = select(frame, arm="obs_dhr_phys", **setting)
    variants = [("default", 3)]
    variants += [(c, 3) for c in sorted(rows.check_set.unique()) if c != "default"]
    if 1 in set(rows.persistence_slots):
        variants.append(("default", 1))
    lines = ["\n### Check decomposition, arm 4 (diagnostic; **not** a gate result)\n"]
    lines += _header(["check set", "persistence", "σ_map", "ρ", "Δ = 0 null", "Δ = 10",
                      "false exclusion", "detection on actionable slots"])
    for check, persistence in variants:
        for sigma in sorted(rows.sigma_map.unique()):
            for rho in sorted(rows.rho.unique()):
                local = {**setting, "check_set": check, "rho": float(rho),
                         "sigma_map": float(sigma), "persistence_slots": persistence}
                null = cell(frame, "obs_dhr_phys", PRIMARY, **{**local, "delta": 0.0})
                hit = cell(frame, "obs_dhr_phys", PRIMARY, **local)
                if not hit.n or not null.n:
                    continue
                fe = cell(frame, "obs_dhr_phys", "false_exclusion_rate", **local)
                det = cell(frame, "obs_dhr_phys", "detect_rate_actionable", **local)
                lines.append(f"| {check} | {persistence} | {sigma:g} | {rho:g} | "
                             f"{null} | {hit} | {fe} | {det} |")
    return "\n".join(lines) + "\n"


def difference_table(frame: pd.DataFrame) -> str:
    """Paired per-seed differences, on the null-corrected metric (DESIGN 6)."""
    pairs = (
        ("model_dhr3", "single"),
        ("obs_dhr", "single"),
        ("obs_dhr_phys", "obs_dhr"),
        ("obs_dhr_phys_dither", "obs_dhr_phys"),
        ("cheap_phys", "obs_dhr_phys"),
    )
    setting = {k: v for k, v in GATE.items() if k not in ("rho", "sigma_map")}
    lines = ["\n### Paired differences on the null-corrected primary metric "
             "(Δ = 10; `*` marks a 95 % CI excluding zero)\n"]
    lines += _header(["pair", "σ_map", "ρ", "paired difference"])
    for sigma in (2.0, 4.0, 6.0):
        for rho in (0.0, 1.0):
            local = {**setting, "sigma_map": sigma, "rho": rho}
            for left, right in pairs:
                iv = net_paired(frame, left, right, PRIMARY, **local)
                mark = " *" if iv.excludes_zero() else ""
                lines.append(f"| {left} − {right} | {sigma:g} | {rho:g} | {iv}{mark} |")
    return "\n".join(lines) + "\n"


def below_null_note(frame: pd.DataFrame) -> list[str]:
    """Arms whose attacked value sits at or below their own null (DESIGN 6.1)."""
    notes: list[str] = []
    setting = {k: v for k, v in GATE.items() if k not in ("rho", "sigma_map")}
    for sigma in sorted(select(frame, **setting).sigma_map.unique()):
        for rho in sorted(select(frame, **setting).rho.unique()):
            local = {**setting, "sigma_map": float(sigma), "rho": float(rho)}
            for arm in ARM_ORDER:
                iv = net(frame, arm, PRIMARY, **local)
                if iv.n and iv.hi <= 0.0:
                    notes.append(
                        f"σ_map = {sigma:g}, ρ = {rho:g}: `{arm}` is **below resolution**: "
                        f"its Δ = 10 value minus its own Δ = 0 null is {iv}"
                    )
    return notes


def identical_notes(frame: pd.DataFrame) -> list[str]:
    """Report arm pairs that behave bit-identically in any reported setting."""
    notes: list[str] = []
    setting = {k: v for k, v in GATE.items() if k != "rho"}
    for rho in sorted(select(frame, **setting).rho.unique()):
        for metric in (PRIMARY, "throughput"):
            for left, right in identical_arms(frame, metric, ARM_ORDER,
                                              **{**setting, "rho": float(rho)}):
                notes.append(
                    f"ρ = {rho:g}: arms `{left}` and `{right}` have bit-identical per-seed "
                    f"{METRIC_LABELS[metric]}"
                )
    return notes


def runtime_note(frame: pd.DataFrame) -> str:
    """One-line runtime summary of the whole sweep."""
    seconds = frame["runtime_seconds"].to_numpy(dtype=float)
    return (f"{len(frame)} runs; mean {np.mean(seconds):.2f} s, max {np.max(seconds):.2f} s "
            f"per run (DESIGN 8 budget 20 s); {np.sum(seconds):.0f} s CPU in total")


def threshold_table(frame: pd.DataFrame) -> str:
    """Thresholds actually used, with their spread across seeds."""
    setting = {k: v for k, v in GATE.items() if k != "sigma_map"}
    lines = ["\n### Thresholds actually used (z = 3 × a standard deviation calibrated "
             "on the clean warm-up), with their spread across the 10 seeds\n"]
    lines += _header(["σ_map", "check", "mean (dB)", "min (dB)", "max (dB)", "sd (dB)"])
    for sigma in sorted(select(frame, **setting).sigma_map.unique()):
        rows = select(frame, arm="obs_dhr_phys", **{**setting, "sigma_map": float(sigma)})
        if rows.empty:
            continue
        for column in THRESHOLD_COLUMNS:
            values = rows[column].to_numpy(dtype=float)
            lines.append(f"| {sigma:g} | {column.removeprefix('thr_')} | "
                         f"{values.mean():.3f} | {values.min():.3f} | {values.max():.3f} | "
                         f"{values.std(ddof=1):.4f} |")
        for column in ("sigma_c1_hat", "sigma_map_hat"):
            values = rows[column].to_numpy(dtype=float)
            lines.append(f"| {sigma:g} | {METRIC_LABELS[column]} | {values.mean():.3f} | "
                         f"{values.min():.3f} | {values.max():.3f} | "
                         f"{values.std(ddof=1):.4f} |")
    return "\n".join(lines) + "\n"


def secondary_table(frame: pd.DataFrame) -> str:
    """The per-opportunity metric beside the primary one (DESIGN 6)."""
    setting = {k: v for k, v in GATE.items() if k != "rho"}
    rhos = sorted(select(frame, **setting).rho.unique())
    metrics = (PRIMARY, SECONDARY, "attack_success_opp_inst")
    lines = ["\n### Primary and secondary attack metrics (σ_map = 2, Δ = 10, trap)\n"]
    lines += _header(["arm", "ρ"] + [METRIC_LABELS[m] for m in metrics])
    for arm in ARM_ORDER:
        for rho in rhos:
            local = {**setting, "rho": float(rho)}
            lines.append(f"| {ARM_LABELS[arm]} | {rho:g} | "
                         + " | ".join(_values(frame, arm, metrics, local)) + " |")
    return "\n".join(lines) + "\n"


def paired_qos_table(frame: pd.DataFrame) -> str:
    """Paired harm differences of every defended arm against arm 1 (PROTOCOL.md G2-c)."""
    metrics = ("rsrp_deficit", "outage_share", "missed_handover_per_ue_slot")
    lines = ["\n### Paired harm differences against arm 1 (`*` marks a CI excluding zero)\n"]
    lines += _header(["arm", "Δ"] + [METRIC_LABELS[m] for m in metrics])
    for arm in ARM_ORDER[1:]:
        for label, setting in (("0 (null)", NULL), ("10", GATE)):
            cells = []
            for metric in metrics:
                iv = paired(frame, arm, "single", metric, **setting)
                cells.append(f"{iv}{' *' if iv.excludes_zero() else ''}")
            lines.append(f"| {ARM_LABELS[arm]} | {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
