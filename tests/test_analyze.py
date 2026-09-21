"""Paired statistics, the gate-2 table and the figures."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analyze import build_summary, gate_a, gate_b, gate_c, gate_table, reading
from figstyle import ARM_LABELS, apply_style, arm_line_style, arm_style
from figures import figure_a, figure_b
from stats import (
    GATE,
    NULL,
    PRIMARY,
    Interval,
    cell,
    identical_arms,
    interval,
    net,
    net_paired,
    paired,
    ratio,
    select,
    t95,
)
from wes.decisions import ARM_ORDER


def _row(arm: str, seed: int, **overrides) -> dict:
    """One synthetic ``runs.csv`` row with sane defaults."""
    row = {
        "arm": arm, "seed": seed, "p": 0.2, "delta": 10.0, "rho": 1.0, "sigma_map": 2.0,
        "mode": "trap", "ramp_slots": 1, "checks": "default", "check_set": "default",
        "z": 3.0, "persistence_slots": 3, "n_targets": 6, "n_voting_channels": 3,
        "majority_reachable": True,
        "attack_success_attr": 0.05, "attack_success_opp": 0.10,
        "attack_success_opp_inst": 0.08, "attack_success": 0.06,
        "actionable_share": 0.4, "actionable_share_inst": 0.5,
        "detect_rate": 0.5, "detect_rate_actionable": 0.9,
        "wrong_handover_rate": 0.001, "pingpong_rate": 0.0005,
        "wrong_handover_per_ho": 0.05, "pingpong_per_ho": 0.03,
        "handover_rate": 0.007, "missed_handover_rate": 0.3,
        "missed_handover_per_ue_slot": 0.001, "oracle_handover_rate": 0.005,
        "rsrp_deficit": 0.07, "outage_share": 0.02, "wrong_cell_share": 0.03,
        "false_exclusion_rate": 0.01, "false_exclusion_rate_ch": 0.005,
        "fe_serving_reciprocity": 0.004, "fe_neighbour_reciprocity": 0.004,
        "fe_map": 0.001, "fe_rate": 0.001,
        "fallback_rate": 0.0, "mean_voters": 2.9, "throughput": 1.3,
        "bytes_per_ue_s": 400.0, "bytes_ota_per_ue_s": 400.0, "compute_per_decision": 1.0,
        "thr_serving_reciprocity": 5.4, "thr_neighbour_reciprocity": 6.7,
        "thr_map": 6.9, "thr_rate": 5.3, "sigma_serving_recip_hat": 1.8,
        "sigma_neighbour_recip_hat": 2.2, "sigma_map_diff_hat": 2.3,
        "sigma_rate_hat": 1.8, "sigma_c1_hat": 1.0, "sigma_map_hat": 2.0,
        "runtime_seconds": 0.8,
    }
    row.update(overrides)
    return row


@pytest.fixture
def frame() -> pd.DataFrame:
    """A synthetic frame in which every gate is designed to pass."""
    rows = []
    profile = {
        "single": (0.050, 0.00, 0.070, 0.020),
        "model_dhr3": (0.050, 0.00, 0.070, 0.020),
        "obs_dhr": (0.040, 0.00, 0.075, 0.021),
        "obs_dhr_phys": (0.004, 0.01, 0.080, 0.021),
        "obs_dhr_phys_dither": (0.004, 0.01, 0.080, 0.021),
        "cheap_phys": (0.003, 0.01, 0.120, 0.021),
    }
    rng = np.random.default_rng(0)
    for arm, (success, fe, deficit, outage) in profile.items():
        for sigma in (2.0, 4.0, 6.0):
            for rho in (0.0, 0.5, 1.0):
                for delta in (0.0, 6.0, 10.0, 15.0):
                    for seed in range(10):
                        jitter = 1.0 + 0.02 * rng.standard_normal()
                        value = success * jitter * (0.02 if delta == 0.0 else 1.0)
                        if arm == "obs_dhr" and rho < 1.0:
                            value *= 0.05
                        rows.append(_row(arm, seed, rho=rho, delta=delta, sigma_map=sigma,
                                         attack_success_attr=value,
                                         false_exclusion_rate=fe, rsrp_deficit=deficit,
                                         outage_share=outage))
    for arm in ARM_ORDER:
        for delta in (0.0, 10.0):
            for seed in range(10):
                rows.append(_row(arm, seed, mode="pingpong", rho=0.0, delta=delta))
    for ramp in (10, 20):
        for arm in ("single", "obs_dhr", "obs_dhr_phys"):
            for seed in range(10):
                rows.append(_row(arm, seed, ramp_slots=ramp))
    for check in ("serving", "neighbour", "map", "rate"):
        for delta in (0.0, 10.0):
            for seed in range(10):
                rows.append(_row("obs_dhr_phys", seed, check_set=check, delta=delta))
    for delta in (0.0, 10.0):
        for seed in range(10):
            rows.append(_row("obs_dhr_phys", seed, persistence_slots=1, delta=delta))
    return pd.DataFrame(rows)


def test_interval_matches_the_textbook_formula():
    """The half-width is t(0.975, n-1) * s / sqrt(n)."""
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    iv = interval(values)
    assert iv.mean == pytest.approx(3.0)
    assert iv.half == pytest.approx(t95(4) * values.std(ddof=1) / np.sqrt(5))
    assert iv.n == 5
    assert iv.excludes_zero()
    assert Interval(0.5, 0.1, 5).excludes_zero()
    assert not Interval(0.5, 0.9, 5).excludes_zero()
    assert str(interval(np.array([np.nan]))) == "n/a"
    assert np.isnan(ratio(Interval(1.0, 0.0, 1), Interval(0.0, 0.0, 1)))


def test_paired_scale_implements_the_boundary_test(frame):
    """PROTOCOL.md's ``arm3 - 0.5 * arm1`` boundary uses the scaled paired difference."""
    scaled = paired(frame, "obs_dhr", "single", PRIMARY, scale=0.5, **GATE)
    left = select(frame, arm="obs_dhr", **GATE).set_index("seed")[PRIMARY]
    right = select(frame, arm="single", **GATE).set_index("seed")[PRIMARY]
    assert scaled.mean == pytest.approx(float((left - 0.5 * right).mean()))
    assert scaled.n == 10
    assert scaled.lo > 0.0


def test_net_subtracts_each_arms_own_null(frame):
    """DESIGN 6.1: ratios are taken on (value - the arm's own Δ = 0 null)."""
    corrected = net(frame, "single", PRIMARY, **GATE)
    raw = cell(frame, "single", PRIMARY, **GATE)
    null = cell(frame, "single", PRIMARY, **NULL)
    assert corrected.mean == pytest.approx(raw.mean - null.mean, rel=1e-9)
    both = net_paired(frame, "obs_dhr", "single", PRIMARY, scale=0.5, **GATE)
    assert both.n == 10


def test_select_rejects_an_unknown_filter(frame):
    """A typo in a filter must raise, not widen the selection."""
    with pytest.raises(KeyError, match="unknown filter column"):
        select(frame, arm="single", delta_db=10.0)


def test_select_filters_every_dimension(frame):
    """Filtering narrows to exactly one arm, seed set and setting."""
    rows = select(frame, arm="single", **GATE)
    assert len(rows) == 10
    assert set(rows["rho"]) == {1.0}
    assert set(rows["delta"]) == {10.0}
    assert set(rows["sigma_map"]) == {2.0}


def test_null_setting_selects_the_delta_zero_control(frame):
    """The Δ = 0 null control is addressable and separate from the gate setting."""
    assert NULL["delta"] == 0.0
    null = cell(frame, "single", PRIMARY, **NULL)
    gate = cell(frame, "single", PRIMARY, **GATE)
    assert null.n == 10
    assert null.mean < gate.mean


def test_identical_arms_detects_bit_identical_columns():
    """Two arms with the same per-seed values are reported as identical."""
    rows = [_row("single", s, attack_success_attr=0.01) for s in range(5)]
    rows += [_row("model_dhr3", s, attack_success_attr=0.01) for s in range(5)]
    rows += [_row("obs_dhr", s, attack_success_attr=0.02) for s in range(5)]
    frame = pd.DataFrame(rows)
    pairs = identical_arms(frame, PRIMARY, ARM_ORDER, **GATE)
    assert ("single", "model_dhr3") in pairs
    assert ("single", "obs_dhr") not in pairs


def test_every_gate_passes_on_a_favourable_frame(frame):
    """The gate functions return PASS when the data satisfy them literally."""
    body, verdicts = gate_table(frame)
    assert set(verdicts) == {"G2-a", "G2-b", "G2-c"}
    assert all(verdicts.values()), body
    assert "PASS" in body
    assert "what anchors the check" in reading(verdicts)


def test_gates_fail_when_their_criterion_is_violated(frame):
    """Each gate flips to FAIL when its own condition is broken."""
    broken = frame.copy()
    broken.loc[(broken.arm == "obs_dhr") & (broken.sigma_map == 6.0), PRIMARY] = 0.001
    assert not gate_a(broken).passed
    assert "apparatus defect" in reading({"G2-a": False, "G2-b": True, "G2-c": True})

    broken = frame.copy()
    broken.loc[broken.arm == "obs_dhr_phys", PRIMARY] = 0.045
    assert not gate_b(broken).passed
    assert "boundary paper" in reading({"G2-a": True, "G2-b": False, "G2-c": True})

    broken = frame.copy()
    broken.loc[broken.arm == "obs_dhr_phys", "false_exclusion_rate"] = 0.4
    gate = gate_b(broken)
    assert not gate.passed
    assert "≤ 0.05: no" in gate.evidence

    broken = frame.copy()
    broken.loc[broken.arm == "cheap_phys", "rsrp_deficit"] = 3.0
    assert not gate_c(broken).passed

    broken = frame.copy()
    broken.loc[broken.arm == "obs_dhr_phys", "outage_share"] = 0.9
    assert not gate_c(broken).passed


def test_gate_c_reports_missed_handovers_without_gating_them(frame):
    """PROTOCOL.md sets no missed-handover threshold, so it is reported, not gated."""
    broken = frame.copy()
    broken.loc[broken.arm == "obs_dhr_phys", "missed_handover_per_ue_slot"] = 0.99
    gate = gate_c(broken)
    assert gate.passed
    assert "missed handovers" in gate.evidence


def test_summary_contains_every_table(frame):
    """The summary carries the gate table and each headline section."""
    body, _ = build_summary(frame)
    for heading in ("Gate-2 table", "null control", "Headline metrics", "σ_map × ρ",
                    "against Δ", "Harm and quality of service", "Apparatus diagnostics",
                    "Cost per arm", "Paired differences", "Sticky ramp",
                    "Both attacker modes", "Check decomposition", "analytic floor",
                    "Thresholds actually used"):
        assert heading in body, heading
    for arm in ARM_ORDER:
        assert ARM_LABELS[arm] in body


def test_figures_are_written_from_the_frame_only(frame, tmp_path):
    """Both figures render to PDF and PNG from runs.csv alone."""
    apply_style()
    assert {"color", "marker"} <= set(arm_style(0))
    assert "linestyle" in arm_line_style(1)
    figure_a(frame, tmp_path)
    figure_b(frame, tmp_path)
    for stem in ("figA_attack_success_vs_rho", "figB_harm_cost"):
        assert (tmp_path / f"{stem}.pdf").exists()
        assert (tmp_path / f"{stem}.png").exists()


def test_cell_returns_nan_for_a_missing_setting(frame):
    """Asking for an absent setting yields an empty interval, not an exception."""
    iv = cell(frame, "single", PRIMARY, p=0.99)
    assert iv.n == 0
    assert np.isnan(iv.mean)
