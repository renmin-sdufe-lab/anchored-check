"""Executors, checks and adjudication (DESIGN 3.3, 4)."""

from __future__ import annotations

import numpy as np
import pytest

from wes.adjudicate import (
    ADJUDICATOR_REGISTRY,
    ARM_WIRING,
    DITHERED_ARMS,
    TRUSTED_CHANNEL,
    PhysicsExclusion,
    SlotView,
    build_thresholds,
    make_adjudicator,
    weighted_vote,
)
from wes.calibration import calibrate
from wes.channels import C1, C3, C4, N_CHANNELS, N, build_channels, network_view
from wes.checks import (
    ARM_CHECKS,
    CHECK_EXCLUDES,
    CHECK_NAMES,
    CHECK_TESTS,
    analytic_floor,
    arm_checks,
    dither_z,
    peer_reference,
)
from wes.config import load_config
from wes.decisions import ARM_ORDER, KEEP
from wes.executors import ARM_VOTERS, EXECUTOR_REGISTRY, ExecutorBank, arm_specs, n_voters
from wes.radio import rsrp_true
from wes.world import build_world, cell_positions, make_streams


@pytest.fixture(scope="module")
def cfg():
    """Base configuration."""
    return load_config()


@pytest.fixture(scope="module")
def world_channels(cfg):
    """One seed of world, true RSRP, clean channels and their calibration."""
    streams = make_streams(0)
    world = build_world(cfg, streams)
    rsrp = rsrp_true(cfg, world.positions, world.cells, world.shadow)
    channels = build_channels(cfg, rsrp, streams["noise"], world.map_error)
    return world, rsrp, channels, calibrate(cfg, channels)


def _thresholds(cfg, world_channels):
    """Threshold table of the shared fixture."""
    return build_thresholds(cfg, world_channels[3])


def test_registries_cover_every_arm(cfg):
    """Every arm resolves to a registered adjudicator with the DESIGN 3.3 voters."""
    assert set(ARM_WIRING) == set(ARM_ORDER)
    assert len(ARM_ORDER) == 7
    assert set(EXECUTOR_REGISTRY) == {"a3", "load_aware", "trend"}
    for arm in ARM_ORDER:
        assert ARM_WIRING[arm] in ADJUDICATOR_REGISTRY
        assert len(arm_specs(cfg, arm)) == n_voters(arm)
    assert ARM_VOTERS["obs_dhr"] == (C1, N, C4)
    assert ARM_VOTERS["obs_dhr_phys"] == (C1, N, C4)
    assert ARM_VOTERS["cheap_phys"] == (C1, C4)
    assert ARM_VOTERS["single"] == (C1,)
    assert DITHERED_ARMS == ("obs_dhr_phys_dither",)
    assert TRUSTED_CHANNEL == C4


def test_arm_two_prime_runs_three_decision_families_on_c1(cfg):
    """DESIGN 3.2: three families, one channel, so a common cause reaches all three."""
    specs = arm_specs(cfg, "model_dhr3")
    assert [s.rule for s in specs] == ["a3", "load_aware", "trend"]
    assert {s.channel for s in specs} == {C1}


def test_parameter_diversity_arm_carries_the_three_variants(cfg):
    """DESIGN 3.2: three A3 variants on C1 with the variant hysteresis and TTT."""
    specs = arm_specs(cfg, "model_dhr_param")
    assert [s.rule for s in specs] == ["a3", "a3", "a3"]
    assert {s.channel for s in specs} == {C1}
    assert [(s.hysteresis, s.ttt) for s in specs] == [(2.0, 4), (3.0, 5), (4.0, 6)]


def test_a3_rule_needs_hysteresis_and_time_to_trigger(cfg):
    """A target must beat the serving cell by the hysteresis for TTT slots."""
    bank = ExecutorBank(cfg, arm_specs(cfg, "single"), n_ue=1, n_cells=7)
    serving = np.zeros(1, dtype=int)
    load = np.ones(7)
    readings = np.full((N_CHANNELS, 1, 7), -140.0)
    readings[C1, 0, 0] = -90.0
    readings[C1, 0, 3] = -90.0 + 2.0
    for _ in range(10):
        assert bank.step(readings, serving, load)[0, 0] == KEEP
    readings[C1, 0, 3] = -90.0 + 4.0
    for slot in range(1, 8):
        decision = bank.step(readings, serving, load)[0, 0]
        assert decision == (KEEP if slot < cfg.rule.ttt else 3)


def test_load_aware_rule_refuses_a_busier_target(cfg):
    """DESIGN 3.2: the load-aware family keeps serving when the target is busier."""
    specs = arm_specs(cfg, "model_dhr3")
    bank = ExecutorBank(cfg, specs, n_ue=1, n_cells=7)
    serving = np.zeros(1, dtype=int)
    readings = np.full((N_CHANNELS, 1, 7), -140.0)
    readings[C1, 0, 0] = -90.0
    readings[C1, 0, 3] = -84.0
    busy = np.ones(7)
    busy[3] = 5.0
    for _ in range(10):
        decisions = bank.step(readings, serving, busy)
    assert decisions[0, 0] == 3
    assert decisions[1, 0] == KEEP
    light = np.ones(7)
    light[0] = 5.0
    for _ in range(10):
        decisions = bank.step(readings, serving, light)
    assert decisions[1, 0] == 3


def test_trend_rule_needs_a_strictly_rising_difference(cfg):
    """DESIGN 3.2: the trend family fires on a rise, not on a constant offset."""
    specs = arm_specs(cfg, "model_dhr3")
    bank = ExecutorBank(cfg, specs, n_ue=1, n_cells=7)
    serving = np.zeros(1, dtype=int)
    load = np.ones(7)
    readings = np.full((N_CHANNELS, 1, 7), -140.0)
    readings[C1, 0, 0] = -90.0
    readings[C1, 0, 3] = -84.0
    for _ in range(10):
        flat = bank.step(readings, serving, load)
    assert flat[2, 0] == KEEP
    for step in range(10):
        readings[C1, 0, 3] = -90.0 + 1.0 * (step + 1)
        rising = bank.step(readings, serving, load)
    assert rising[2, 0] == 3


def test_weighted_vote_needs_a_strict_majority(cfg):
    """Three voters need two agreeing; a three-way split keeps the serving cell."""
    decisions = np.array([[0, 2, 2], [1, 2, 3], [2, 5, 4]])
    weights = np.ones_like(decisions, dtype=float)
    assert weighted_vote(decisions, weights, 7).tolist() == [KEEP, 2, KEEP]


def test_thresholds_are_z_times_the_calibrated_sigma(cfg, world_channels):
    """DESIGN 4: every threshold is z times a warm-up standard deviation."""
    calibration = world_channels[3]
    thresholds = _thresholds(cfg, world_channels)
    for name in CHECK_NAMES:
        assert thresholds.nominal(name) == pytest.approx(
            cfg.checks.z * calibration.sigma(name)
        )
    louder = build_thresholds(load_config(("checks.z=6.0",)), calibration)
    for name in CHECK_NAMES:
        assert louder.nominal(name) == pytest.approx(2.0 * thresholds.nominal(name))
    assert set(thresholds.row()) == {f"thr_{name}" for name in CHECK_NAMES}


def _checker(cfg, thresholds, n_ue, enabled, **overrides):
    """A checker with one named check enabled."""
    dotlist = (f"checks.enabled=[{enabled}]",) + tuple(
        f"{k}={v}" for k, v in overrides.items()
    )
    return PhysicsExclusion(load_config(dotlist), thresholds, n_ue, cfg.world.n_cells)


def test_neighbour_reciprocity_is_symmetric_when_channels_differ(cfg, world_channels):
    """Symmetric exclusion: C1 and N name different cells, and both are excluded.

    The counterexample: truth is -85 dBm at the serving cell 0 and -84 dBm at
    cell 5, and C1 is inflated by +18 dB at cell 4.  C1's strongest other cell
    is then 4 and N's is 5, so a check that only looked at the channel's own
    argmax would compare cell 4 against an honest N and exclude C1 alone.
    """
    thresholds = _thresholds(cfg, world_channels)
    n_ue = 3
    truth = np.full((n_ue, cfg.world.n_cells), -100.0)
    truth[:, 0] = -85.0
    truth[:, 5] = -84.0
    readings = np.repeat(truth[None, :, :], N_CHANNELS, axis=0)
    readings[C1, :, 4] += 18.0
    serving = np.zeros(n_ue, dtype=int)
    readings = network_view(readings, serving)
    available = np.ones((N_CHANNELS, n_ue), dtype=bool)
    checker = _checker(cfg, thresholds, n_ue, "neighbour_reciprocity", **{
        "checks.persistence_slots": 1
    })
    cols = checker.relevant_cells(readings, serving)
    assert cols[0, 1] == 4 and cols[0, 2] == 5
    excluded, fired = checker.evaluate(readings, available, serving)
    assert excluded[C1].all()
    assert excluded[N].all()
    assert fired[CHECK_NAMES.index("neighbour_reciprocity")].all()
    assert CHECK_EXCLUDES["neighbour_reciprocity"] == (C1, N)


def test_neighbour_reciprocity_is_blind_when_both_are_falsified(cfg, world_channels):
    """At rho = 1 the peer report moves with C1, so the check sees nothing."""
    thresholds = _thresholds(cfg, world_channels)
    n_ue = 2
    truth = np.full((n_ue, cfg.world.n_cells), -100.0)
    truth[:, 0] = -85.0
    readings = np.repeat(truth[None, :, :], N_CHANNELS, axis=0)
    readings[C1, :, 4] += 18.0
    readings[C3, :, 4] += 18.0
    serving = np.zeros(n_ue, dtype=int)
    readings = network_view(readings, serving)
    available = np.ones((N_CHANNELS, n_ue), dtype=bool)
    checker = _checker(cfg, thresholds, n_ue, "neighbour_reciprocity", **{
        "checks.persistence_slots": 1
    })
    excluded, _ = checker.evaluate(readings, available, serving)
    assert not excluded[C1].any()
    assert not excluded[N].any()


def test_serving_reciprocity_excludes_c1_alone(cfg, world_channels):
    """DESIGN 4: C2 is unreachable, so a serving-cell mismatch is C1's fault."""
    thresholds = _thresholds(cfg, world_channels)
    n_ue = 2
    truth = np.full((n_ue, cfg.world.n_cells), -100.0)
    truth[:, 0] = -85.0
    readings = np.repeat(truth[None, :, :], N_CHANNELS, axis=0)
    readings[C1, :, 0] -= 15.0
    serving = np.zeros(n_ue, dtype=int)
    readings = network_view(readings, serving)
    available = np.ones((N_CHANNELS, n_ue), dtype=bool)
    checker = _checker(cfg, thresholds, n_ue, "serving_reciprocity", **{
        "checks.persistence_slots": 1
    })
    excluded, _ = checker.evaluate(readings, available, serving)
    assert excluded[C1].all()
    assert not excluded[N].any()


def _sustained_firings(cfg, thresholds, name, offsets):
    """Run one check alone over a sequence of C1 offsets and report its exclusions."""
    checker = _checker(cfg, thresholds, 1, name)
    base = np.full((N_CHANNELS, 1, cfg.world.n_cells), -100.0)
    base[:, 0, 0] = -85.0
    serving = np.zeros(1, dtype=int)
    available = np.ones((N_CHANNELS, 1), dtype=bool)
    cell = 0 if name == "serving_reciprocity" else 4
    for _ in range(3):
        checker.evaluate(network_view(base.copy(), serving), available, serving)
    fired = []
    for offset in offsets:
        readings = base.copy()
        readings[C1, 0, cell] += offset
        readings = network_view(readings, serving)
        fired.append(bool(checker.evaluate(readings, available, serving)[0][C1, 0]))
    return fired


@pytest.mark.parametrize("name", ["serving_reciprocity", "neighbour_reciprocity", "map"])
def test_every_check_carries_the_persistence_rule(cfg, world_channels, name):
    """Persistence: three consecutive violations exclude, one does not."""
    thresholds = _thresholds(cfg, world_channels)
    assert _sustained_firings(cfg, thresholds, name, [20.0] * 3) == [False, False, True]


def test_the_rate_check_needs_three_consecutive_rises(cfg, world_channels):
    """The rate check compares consecutive slots, so a *step* is a one-slot event.

    Under DESIGN 4's uniform persistence rule a single sustained step therefore
    never reaches a streak of three, while an offset that keeps growing past the
    bound does.  This is measured rather than assumed; the no-persistence
    variant of arm 4 reports what the rule costs.
    """
    thresholds = _thresholds(cfg, world_channels)
    step = _sustained_firings(cfg, thresholds, "rate", [20.0] * 6)
    assert not any(step)
    growing = _sustained_firings(cfg, thresholds, "rate", [20.0 * (i + 1) for i in range(4)])
    assert growing == [False, False, True, True]


def test_analytic_floor_matches_the_three_sigma_arithmetic():
    """DESIGN 4: the printed floor is the Gaussian z-test rate, persisted."""
    single = analytic_floor(3.0, 1, 1)
    assert single == pytest.approx(0.0026998, rel=1e-3)
    assert analytic_floor(3.0, 1, 3) == pytest.approx(single**3, rel=1e-9)
    assert analytic_floor(3.0, 2, 1) == pytest.approx(1.0 - (1.0 - single) ** 2, rel=1e-9)
    assert set(CHECK_TESTS) == set(CHECK_NAMES)


def test_dither_draws_z_from_the_c2_noise(cfg):
    """DESIGN 3.3 arm 4d: z is channel-derived, in range, and varies with the reading."""
    values = dither_z(cfg, np.linspace(-110.0, -70.0, 500))
    assert values.min() >= cfg.checks.dither_low
    assert values.max() <= cfg.checks.dither_high
    assert values.std() > 0.4
    repeat = dither_z(cfg, np.linspace(-110.0, -70.0, 500))
    assert np.array_equal(values, repeat)


def test_confidence_downweighting_is_multiplicative(cfg):
    """A disagreeing executor loses weight by the decay factor, floored."""
    cells = cell_positions(cfg)
    adjudicator = make_adjudicator("weighted_majority", cfg, cells, 3, 1)
    decisions = np.array([[2], [2], [5]])
    channels = np.array([C1, C1, C1])
    readings = np.zeros((N_CHANNELS, 1, cfg.world.n_cells))
    available = np.ones((N_CHANNELS, 1), dtype=bool)
    serving = np.zeros(1, dtype=int)
    before = adjudicator.weights.copy()
    for _ in range(3):
        view = SlotView(0, decisions, channels, readings, available, serving)
        assert adjudicator.decide(view).decision[0] == 2
    assert adjudicator.weights[2, 0] == pytest.approx(before[2, 0] * cfg.dhr.decay**3)
    assert adjudicator.weights[0, 0] == pytest.approx(cfg.dhr.weight_cap)
    for _ in range(60):
        adjudicator.decide(SlotView(0, decisions, channels, readings, available, serving))
    assert adjudicator.weights[2, 0] == pytest.approx(cfg.dhr.weight_floor)


def _physics_view(cfg, decisions, available, serving, readings=None):
    """A SlotView for the three-channel physics arms."""
    if readings is None:
        readings = np.full((N_CHANNELS, 1, cfg.world.n_cells), -100.0)
        readings = network_view(readings, serving)
    return SlotView(0, decisions, np.array([C1, N, C4]), readings, available, serving)


def test_trusted_channel_fallback_forwards_the_map(cfg, world_channels):
    """DESIGN 3.4: with fewer than two survivors the unreachable channel decides."""
    cells = cell_positions(cfg)
    thresholds = _thresholds(cfg, world_channels)
    local = load_config(("checks.enabled=[serving_reciprocity]",))
    adjudicator = make_adjudicator("physics_majority", local, cells, 3, 1, thresholds)
    available = np.zeros((N_CHANNELS, 1), dtype=bool)
    available[C4] = True
    serving = np.zeros(1, dtype=int)
    view = _physics_view(cfg, np.array([[4], [4], [6]]), available, serving)
    result = adjudicator.decide(view)
    assert result.voters[0] == 1
    assert result.fallback[0]
    assert result.decision[0] == 6


def test_fallback_keeps_serving_when_nothing_survives(cfg, world_channels):
    """With no surviving channel the fallback keeps the serving cell."""
    cells = cell_positions(cfg)
    thresholds = _thresholds(cfg, world_channels)
    local = load_config(("checks.enabled=[serving_reciprocity]",))
    adjudicator = make_adjudicator("physics_majority", local, cells, 3, 1, thresholds)
    available = np.zeros((N_CHANNELS, 1), dtype=bool)
    serving = np.zeros(1, dtype=int)
    result = adjudicator.decide(
        _physics_view(cfg, np.array([[3], [3], [3]]), available, serving)
    )
    assert result.voters[0] == 0
    assert result.decision[0] == KEEP


def test_cheap_arm_needs_unanimity(cfg, world_channels):
    """DESIGN 3.3 arm 5c: hand over only when C1 and C4 name the same target."""
    cells = cell_positions(cfg)
    thresholds = _thresholds(cfg, world_channels)
    local = load_config(("checks.enabled=[serving_reciprocity]",))
    adjudicator = make_adjudicator("unanimity_physics", local, cells, 2, 1, thresholds)
    serving = np.zeros(1, dtype=int)
    readings = network_view(np.full((N_CHANNELS, 1, cfg.world.n_cells), -100.0), serving)
    available = np.ones((N_CHANNELS, 1), dtype=bool)
    channels = np.array([C1, C4])
    agree = SlotView(0, np.array([[4], [4]]), channels, readings, available, serving)
    assert adjudicator.decide(agree).decision[0] == 4
    disagree = SlotView(0, np.array([[4], [5]]), channels, readings, available, serving)
    assert adjudicator.decide(disagree).decision[0] == KEEP


def test_the_veto_arm_runs_only_the_checks_it_pays_for(cfg, world_channels):
    """DESIGN 4.4: arm 5c drops the check whose reference travels over Xn.

    Neighbour reciprocity compares C1 against N, whose neighbour columns are C3
    reports delivered over Xn; `measured_channels` bills arm 5c for C1, C2 and
    C4 only, so the arm may not run that check.  Arms 4 and 4d keep all four.
    """
    thresholds = _thresholds(cfg, world_channels)
    cells = cell_positions(cfg)
    veto = make_adjudicator("unanimity_physics", cfg, cells, 2, cfg.world.n_ue,
                            thresholds, False, "cheap_phys")
    assert veto.checks.enabled == ("serving_reciprocity", "map", "rate")
    assert "neighbour_reciprocity" not in veto.checks.enabled
    assert ARM_CHECKS["cheap_phys"] == ("serving_reciprocity", "map", "rate")
    assert veto.checks.check_units == pytest.approx(3.0 * cfg.cost.compute_check)
    assert veto.checks.peer == C4
    for arm in ("obs_dhr_phys", "obs_dhr_phys_dither"):
        full = make_adjudicator("physics_majority", cfg, cells, 3, cfg.world.n_ue,
                                thresholds, arm in DITHERED_ARMS, arm)
        assert full.checks.enabled == CHECK_NAMES
        assert full.checks.check_units == pytest.approx(4.0 * cfg.cost.compute_check)
        assert full.checks.peer == N
    assert arm_checks(cfg, None) == CHECK_NAMES
    assert peer_reference(None) == N


def test_an_explicit_check_override_beats_the_arm_check_set(cfg, world_channels):
    """DESIGN 4.4: the decomposition variants still address any single check."""
    thresholds = _thresholds(cfg, world_channels)
    cells = cell_positions(cfg)
    for name in CHECK_NAMES:
        local = load_config((f"checks.enabled=[{name}]",))
        assert arm_checks(local, "cheap_phys") == (name,)
        veto = make_adjudicator("unanimity_physics", local, cells, 2, cfg.world.n_ue,
                                thresholds, False, "cheap_phys")
        assert veto.checks.enabled == (name,)
    pair = load_config(("checks.enabled=[neighbour_reciprocity,map]",))
    assert arm_checks(pair, "cheap_phys") == ("neighbour_reciprocity", "map")


def test_a_disabled_check_forms_no_difference_at_all(cfg, world_channels):
    """DESIGN 4.4: only the enabled checks are computed, so N is never touched."""
    thresholds = _thresholds(cfg, world_channels)
    serving = np.zeros(1, dtype=int)
    readings = network_view(np.full((N_CHANNELS, 1, cfg.world.n_cells), -100.0), serving)
    bounds = {name: np.full(1, thresholds.nominal(name)) for name in CHECK_NAMES}
    for arm, expected in (("cheap_phys", ARM_CHECKS["cheap_phys"]),
                          ("obs_dhr_phys", CHECK_NAMES)):
        checker = PhysicsExclusion(cfg, thresholds, 1, cfg.world.n_cells, arm=arm)
        cols = checker.relevant_cells(readings, serving)
        assert tuple(checker._violations(readings, cols, bounds)) == expected
    single = PhysicsExclusion(load_config(("checks.enabled=[map]",)), thresholds, 1,
                              cfg.world.n_cells, arm="obs_dhr_phys")
    cols = single.relevant_cells(readings, serving)
    assert tuple(single._violations(readings, cols, bounds)) == ("map",)


def test_the_veto_arm_never_reads_the_peer_channel(cfg, world_channels):
    """DESIGN 4.4: arm 5c's checks are invariant to every value of N.

    N's neighbour columns are C3 reports delivered over Xn and the arm is billed
    for C1, C2 and C4 only, so neither a value nor an index may come from N: the
    second non-serving test cell is C4's argmax and no difference against N is
    formed.  Arm 4, which votes N, must still react to the same tampering, or
    the test would pass for the wrong reason.
    """
    _, rsrp, channels, calibration = world_channels
    thresholds = build_thresholds(cfg, calibration)
    rng = np.random.default_rng(7)
    pairs = {arm: (PhysicsExclusion(cfg, thresholds, cfg.world.n_ue, cfg.world.n_cells,
                                    arm=arm),
                   PhysicsExclusion(cfg, thresholds, cfg.world.n_ue, cfg.world.n_cells,
                                    arm=arm))
             for arm in ("cheap_phys", "obs_dhr_phys")}
    moved = False
    for t in range(cfg.sim.warmup, cfg.sim.warmup + 40):
        serving = np.argmax(rsrp[t], axis=1)
        clean = network_view(channels.slot(t), serving)
        tampered = clean.copy()
        tampered[N] = rng.normal(-100.0, 40.0, size=tampered[N].shape)
        available = channels.available[:, t]
        for arm, (honest, probed) in pairs.items():
            got = honest.evaluate(clean.copy(), available, serving)
            other = probed.evaluate(tampered.copy(), available, serving)
            same = (np.array_equal(got[0], other[0]) and np.array_equal(got[1], other[1])
                    and np.array_equal(honest.relevant_cells(clean, serving),
                                       probed.relevant_cells(tampered, serving)))
            if arm == "cheap_phys":
                assert same, f"the veto arm reacted to N at slot {t}"
            elif not same:
                moved = True
    assert moved, "arm 4 must react to N, or the veto arm's invariance proves nothing"


def test_clean_false_exclusion_is_inside_the_gate_budget(cfg, world_channels):
    """DESIGN 4's calibrated 3-sigma thresholds keep clean exclusion under 0.05."""
    _, rsrp, channels, calibration = world_channels
    thresholds = build_thresholds(cfg, calibration)
    checker = PhysicsExclusion(cfg, thresholds, cfg.world.n_ue, cfg.world.n_cells)
    hits, total = 0, 0
    for t in range(cfg.sim.warmup, cfg.sim.warmup + 600):
        serving = np.argmax(rsrp[t], axis=1)
        readings = network_view(channels.slot(t), serving)
        excluded, _ = checker.evaluate(readings, channels.available[:, t], serving)
        hits += int(excluded.any(axis=0).sum())
        total += cfg.world.n_ue
    assert hits / total < 0.05
