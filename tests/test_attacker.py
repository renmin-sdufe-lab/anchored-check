"""The transport-path telemetry-poisoning attacker (DESIGN 5)."""

from __future__ import annotations

import numpy as np
import pytest

from wes.attacker import ATTACKER_REGISTRY, REACHABLE, make_attacker, n_targets
from wes.channels import C1, C2, C3, C4, N_CHANNELS, POISONABLE, N
from wes.config import load_config
from wes.decisions import KEEP
from wes.world import make_streams


def _setup(**overrides):
    """Build a configuration, an attacker, a clean slot and a true RSRP field."""
    dotlist = tuple(f"{k}={v}" for k, v in overrides.items())
    cfg = load_config(dotlist)
    attacker = make_attacker(cfg, make_streams(0)["attacker"])
    rng = np.random.default_rng(5)
    n_ue, n_cells = cfg.world.n_ue, cfg.world.n_cells
    rsrp = rng.normal(-90.0, 8.0, size=(n_ue, n_cells))
    readings = np.repeat(rsrp[None, :, :], N_CHANNELS, axis=0)
    readings += rng.normal(0.0, 0.5, size=readings.shape)
    serving = np.argmax(rsrp, axis=1)
    load = np.array([2.0, 9.0, 1.0, 4.0, 3.0, 6.0, 5.0])
    return cfg, attacker, readings, serving, load, rsrp


def test_all_modes_are_registered():
    """The registry exposes the DESIGN 5 modes and the reachable-channel sets agree."""
    assert set(ATTACKER_REGISTRY) == {"trap", "pingpong"}
    assert REACHABLE == (C1, C3)
    assert POISONABLE == (C1, N)


@pytest.mark.parametrize("p", [0.05, 0.2, 0.5])
def test_exact_target_count_per_seed(p):
    """Exactly round(p * N) UEs are targeted, in every seed."""
    cfg = load_config((f"attacker.p={p}",))
    expected = n_targets(cfg)
    assert expected == round(p * cfg.world.n_ue)
    for seed in range(5):
        attacker = make_attacker(cfg, make_streams(seed)["attacker"])
        assert int(attacker.targets.sum()) == expected


def test_target_set_differs_across_seeds():
    """The targeted UE set is redrawn per seed."""
    cfg = load_config()
    sets = {tuple(np.flatnonzero(make_attacker(cfg, make_streams(s)["attacker"]).targets))
            for s in range(6)}
    assert len(sets) > 1


@pytest.mark.parametrize("mode", ["trap", "pingpong"])
@pytest.mark.parametrize("rho", [0.0, 0.5, 1.0])
def test_c2_and_c4_are_never_falsified(mode, rho):
    """DESIGN 5: the serving link and the radio map are out of reach."""
    _, attacker, readings, serving, load, rsrp = _setup(
        **{"attacker.mode": mode, "attacker.rho": rho}
    )
    for t in range(20):
        out = attacker.poison(t, readings, serving, load, rsrp).readings
        assert np.array_equal(out[C2], readings[C2])
        assert np.array_equal(out[C4], readings[C4])


def test_rho_zero_never_touches_the_peer_reports_and_rho_one_always_does():
    """rho = 0 leaves C3 clean; rho = 1 falsifies it exactly where C1 is falsified."""
    _, clean, readings, serving, load, rsrp = _setup(**{"attacker.rho": 0.0})
    _, adaptive, _, _, _, _ = _setup(**{"attacker.rho": 1.0})
    for t in range(30):
        clean_out = clean.poison(t, readings, serving, load, rsrp)
        assert np.array_equal(clean_out.readings[C3], readings[C3])
        assert not clean_out.falsified[N].any()
        adaptive_out = adaptive.poison(t, readings, serving, load, rsrp)
        assert np.allclose(
            adaptive_out.readings[C1] - readings[C1],
            adaptive_out.readings[C3] - readings[C3],
        )


def test_rho_half_compromises_about_half_the_reports():
    """rho = 0.5 falsifies the peer reports on roughly half the targeted UE-slots."""
    _, attacker, _, _, _, _ = _setup(**{"attacker.rho": 0.5})
    hits = sum(int(attacker.peer_compromised(t).sum()) for t in range(1000))
    assert hits == pytest.approx(0.5 * 1000 * attacker.targets.sum(), rel=0.1)


@pytest.mark.parametrize("delta", [0.0, 6.0, 10.0, 15.0])
def test_the_trap_set_does_not_depend_on_delta(delta):
    """DESIGN 5.2: the trap cell comes from the +15 dB feasible set, for every Δ."""
    cfg, attacker, readings, serving, load, rsrp = _setup(**{"attacker.delta": delta})
    result = attacker.poison(0, readings, serving, load, rsrp)
    reference = attacker.feasible(
        serving, rsrp, np.full(cfg.world.n_ue, cfg.attacker.trap_reference_delta)
    )
    for ue in np.flatnonzero(attacker.targets):
        if not reference[ue].any():
            assert result.intent[ue] == KEEP
            continue
        trap = int(result.intent[ue])
        assert reference[ue, trap]
        candidates = np.flatnonzero(reference[ue])
        assert load[trap] == load[candidates].max()


def test_the_trap_cell_is_sticky_while_it_stays_feasible():
    """DESIGN 5.2: the attacker does not abandon its own ramp."""
    cfg, attacker, readings, serving, load, rsrp = _setup(**{"attacker.ramp_slots": 20})
    victims, ages = [], []
    for t in range(30):
        attacker.poison(t, readings, serving, load, rsrp)
        victims.append(attacker._victim.copy())
        ages.append(attacker._ramp_age.copy())
    targeted = np.flatnonzero(attacker.targets & (victims[0] >= 0))
    assert targeted.size
    for ue in targeted:
        assert len({int(v[ue]) for v in victims}) == 1
        assert ages[-1][ue] == 29
    del cfg


def test_the_ramp_delivers_delta_at_the_end_of_the_ramp():
    """DESIGN 5: the applied offset rises to Δ over ``ramp`` slots and stays there."""
    cfg, attacker, readings, serving, load, rsrp = _setup(
        **{"attacker.ramp_slots": 10, "attacker.delta": 10.0}
    )
    magnitudes = []
    for t in range(14):
        result = attacker.poison(t, readings, serving, load, rsrp)
        active = attacker.targets & (result.intent >= 0)
        magnitudes.append(float(np.abs(result.offset[active]).max()))
    assert magnitudes[0] == pytest.approx(cfg.attacker.delta / 10)
    assert magnitudes[4] == pytest.approx(cfg.attacker.delta / 2)
    assert magnitudes[9] == pytest.approx(cfg.attacker.delta)
    assert magnitudes[13] == pytest.approx(cfg.attacker.delta)
    assert np.all(np.diff(magnitudes[:10]) > 0)


def test_feasibility_follows_the_applied_magnitude():
    """DESIGN 5.3: a half-delivered ramp cannot claim a full-Δ opportunity."""
    _, ramped, readings, serving, load, rsrp = _setup(
        **{"attacker.ramp_slots": 20, "attacker.delta": 15.0}
    )
    _, step, _, _, _, _ = _setup(**{"attacker.ramp_slots": 1, "attacker.delta": 15.0})
    early = ramped.poison(0, readings, serving, load, rsrp)
    full = step.poison(0, readings, serving, load, rsrp)
    assert int(early.opportunity_instant.sum()) < int(full.opportunity_instant.sum())
    magnitude = np.abs(early.offset)
    allowed = ramped.feasible(serving, rsrp, magnitude)
    for ue in np.flatnonzero(early.opportunity_instant):
        assert allowed[ue, int(early.intent[ue])]


def test_opportunity_respects_the_time_to_trigger():
    """An opportunity needs the A3 condition held for TTT slots."""
    cfg, attacker, readings, serving, load, rsrp = _setup()
    first = attacker.poison(0, readings, serving, load, rsrp)
    assert not first.opportunity.any()
    assert first.opportunity_instant.any()
    for t in range(1, cfg.rule.ttt - 1):
        result = attacker.poison(t, readings, serving, load, rsrp)
        assert not result.opportunity.any()
    matured = attacker.poison(cfg.rule.ttt - 1, readings, serving, load, rsrp)
    assert matured.opportunity.any()
    assert np.array_equal(matured.opportunity, matured.opportunity_instant)


def test_delta_zero_is_a_null_control():
    """With delta = 0 no reading changes and opportunities are genuine A3 events."""
    _, attacker, readings, serving, load, rsrp = _setup(**{"attacker.delta": 0.0})
    result = attacker.poison(0, readings, serving, load, rsrp)
    assert np.array_equal(result.readings, readings)
    assert not result.offset.any()


def test_pingpong_applies_minus_delta_to_the_serving_cell_only():
    """Only the serving cell of a targeted UE is deflated, by -delta."""
    cfg, attacker, readings, serving, load, rsrp = _setup(**{"attacker.mode": "pingpong"})
    result = attacker.poison(0, readings, serving, load, rsrp)
    diff = result.readings[C1] - readings[C1]
    for ue in range(cfg.world.n_ue):
        cells = np.flatnonzero(np.abs(diff[ue]) > 1e-9)
        if not attacker.targets[ue] or result.intent[ue] == KEEP:
            assert cells.size == 0
            continue
        assert cells.tolist() == [int(serving[ue])]
        assert diff[ue, serving[ue]] == pytest.approx(-cfg.attacker.delta)


def test_attributable_success_subtracts_the_counterfactual():
    """DESIGN 6.1: a handover the oracle would also have made is not an attack success."""
    _, attacker, readings, serving, load, rsrp = _setup()
    result = attacker.poison(0, readings, serving, load, rsrp)
    decision = np.where(attacker.targets, result.intent, KEEP)
    assert np.array_equal(
        attacker.success(decision, result.intent),
        attacker.targets & (result.intent != KEEP),
    )
    assert not attacker.attributable(decision, result.intent, decision.copy()).any()
    other = np.full_like(decision, KEEP)
    assert np.array_equal(
        attacker.attributable(decision, result.intent, other),
        attacker.success(decision, result.intent),
    )


def test_majority_reachable_depends_on_rho():
    """With three voters the reachable pair is a majority at rho > 0."""
    voters = (C1, N, C4)
    blind = make_attacker(load_config(("attacker.rho=0.0",)), make_streams(0)["attacker"])
    adaptive = make_attacker(load_config(("attacker.rho=1.0",)), make_streams(0)["attacker"])
    assert not blind.majority_reachable(voters)
    assert adaptive.majority_reachable(voters)
    assert adaptive.majority_reachable((C1, N))
    assert not adaptive.majority_reachable((C1, C4))


def test_attacker_draws_are_common_random_numbers_across_arms():
    """Two attackers built from the same seed poison identically."""
    cfg = load_config()
    first = make_attacker(cfg, make_streams(3)["attacker"])
    second = make_attacker(cfg, make_streams(3)["attacker"])
    assert np.array_equal(first.targets, second.targets)
    for t in (0, 17, 512):
        assert np.array_equal(first.peer_compromised(t), second.peer_compromised(t))
