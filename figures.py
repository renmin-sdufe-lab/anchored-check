"""The two figures of the b2 analysis, built from ``runs.csv`` alone."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from figstyle import ARM_LABELS, arm_line_style, arm_style, save
from stats import GATE, NULL, PRIMARY, cell, select
from tables import SWEEP_ARMS

logger = logging.getLogger(__name__)

LINTHRESH = 1e-4

#: σ_map panels of figure A (DESIGN 7).
SIGMA_MAPS: tuple[float, ...] = (2.0, 4.0, 6.0)

#: Harm panels of figure B (DESIGN 6.2).
HARM_PANELS: tuple[tuple[str, str], ...] = (
    ("rsrp_deficit", "RSRP deficit (dB)"),
    ("missed_handover_per_ue_slot", "missed handovers / UE-slot"),
    ("bytes_ota_per_ue_s", "over-the-air bytes (B/UE/s)"),
)


def _symlog(ax) -> None:
    """Symmetric-log y axis from zero; attack success spans three decades."""
    ax.set_yscale("symlog", linthresh=LINTHRESH)
    ax.set_ylim(bottom=0.0)
    ax.set_ylabel("attack-attributable success / targeted slot")


def figure_a(frame: pd.DataFrame, outdir: Path) -> None:
    """Attack success against ρ, one panel per σ_map, with each arm's Δ = 0 null."""
    setting = {k: v for k, v in GATE.items() if k not in ("rho", "sigma_map")}
    values = sorted(select(frame, **setting).rho.unique())
    fig, axes = plt.subplots(1, len(SIGMA_MAPS), figsize=(7.2, 2.6), sharey=True)
    for position, (ax, sigma) in enumerate(zip(axes, SIGMA_MAPS, strict=True)):
        local = {**setting, "sigma_map": sigma}
        for index, arm in enumerate(SWEEP_ARMS):
            means, errors = [], []
            for rho in values:
                iv = cell(frame, arm, PRIMARY, **{**local, "rho": float(rho)})
                means.append(iv.mean)
                errors.append(iv.half)
            ax.errorbar(values, means, yerr=errors, capsize=2, elinewidth=0.7,
                        label=ARM_LABELS[arm] if position == 1 else None,
                        **arm_line_style(index))
            null = cell(frame, arm, PRIMARY, **{**local, "rho": 1.0, "delta": 0.0})
            ax.axhline(null.mean, color=arm_style(index)["color"], linewidth=0.5,
                       linestyle=(0, (1, 3)), alpha=0.6)
        ax.set_xlabel(r"attacker reach $\rho$ on $N$")
        ax.set_title(rf"$\sigma_{{\mathrm{{map}}}} = {sigma:g}$ dB")
        _symlog(ax)
        if position:
            ax.set_ylabel("")
    axes[1].legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.18), ncol=2,
                   handletextpad=0.4, columnspacing=1.0, borderaxespad=0.0)
    save(fig, outdir / "figA_attack_success_vs_rho")


def figure_b(frame: pd.DataFrame, outdir: Path) -> None:
    """Harm and cost of every arm at Δ = 0 and under attack (DESIGN 6)."""
    fig, axes = plt.subplots(1, len(HARM_PANELS), figsize=(7.2, 2.6), sharey=True)
    for position, (ax, (column, label)) in enumerate(zip(axes, HARM_PANELS, strict=True)):
        for index, arm in enumerate(SWEEP_ARMS):
            for setting, marker in ((NULL, "none"), (GATE, "full")):
                rows = select(frame, arm=arm, **setting)
                if rows.empty:
                    continue
                style = arm_style(index)
                if marker == "full":
                    style = {**style, "markerfacecolor": style["color"]}
                label_text = ARM_LABELS[arm] if position == 1 and marker == "none" else None
                ax.errorbar([float(rows[column].mean())],
                            [float(rows["wrong_cell_share"].mean())],
                            capsize=2, elinewidth=0.7, linestyle="none",
                            label=label_text, **style)
        ax.set_xlabel(label)
        ax.set_ylabel("wrong-cell share" if position == 0 else "")
    axes[0].annotate("hollow: no attack · filled: under attack", (0.03, 0.94),
                     xycoords="axes fraction", fontsize=6, color="0.35")
    axes[1].legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2,
                   handletextpad=0.4, columnspacing=1.0, borderaxespad=0.0)
    save(fig, outdir / "figB_harm_cost")
