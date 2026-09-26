"""Engine, metrics, CRN pairing and the run CLI (DESIGN 5-7)."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from run import CHECK_SETS, Job, build_jobs, normalise_block, parse_int_list, resolve_arms
from wes.channels import C1, C2, C3, C4, N, network_view
from wes.config import load_config
from wes.decisions import ARM_ORDER, KEEP
from wes.engine import Engine, measured_channels
from wes.metrics import ByteLedger, MetricsCollector, MissedHandoverTracker
from wes.world import make_streams

#: Short runs of every arm captured before arm 5c was given its own check set
#: and before its peer reference moved off N (DESIGN 4.4); the bit-identity
#: tests below replay both.  Both fixtures were regenerated on 2026-09-26 after
#: the attack-free warm-up and online calibration correction, with arm 5c's
#: entry produced by the pre-edit wiring (four checks and peer N, respectively
#: three checks and peer N) on the corrected engine.
TEST_DATA = Path(__file__).resolve().parent / "data"
BASELINE_PRE_CHECK_SET = TEST_DATA / "arm_baseline_pre_check_set.json"
BASELINE_PRE_PEER = TEST_DATA / "arm_baseline_pre_peer.json"

#: Columns the peer-reference change may move on the veto arm: the second
#: non-serving cell the map and rate checks test moves from N's argmax to C4's,
#: which can change an exclusion and therefore a voter count and a fallback.
PEER_MOVED: frozenset[str] = frozenset(
    {"detect_rate", "detect_rate_actionable", "fallback_rate", "mean_voters"}
)

#: One run of the observation model, pinned bit-exactly for future revisions.
#: Arm 4 at the gate setting, seed 3.  Re-pinned on 2026-09-26 after the
#: attack-free warm-up and online calibration correction.
PINNED_RUN: dict[str, float] = {
    "attack_success_attr": 0.0049382716049382715,
    "attack_success_opp": 0.017455213596692696,
    "actionable_share": 0.2687654320987654,
    "false_exclusion_rate": 0.0005555555555555556,
    "detect_rate_actionable": 0.9529168580615526,
    "rsrp_deficit": 0.08731889049625037,
    "throughput": 1.354195322241807,
    "thr_map": 6.914122030312857,
    "thr_rate": 5.340468799925379,
}


@pytest.fixture(scope="module")
def cfg():
    """Base configuration."""
    return load_config()


@pytest.fixture(scope="module")
def engines(cfg):
    """One completed run per arm at seed 0, shared by several tests."""
    out = {}
    for arm in ARM_ORDER:
        engine = Engine(cfg, arm, 0)
        out[arm] = (engine, engine.run())
    return out


def test_common_random_numbers_across_arms(cfg, engines):
    """World, channels and attacker draws are identical across arms for one seed.

    The online calibration is not: it reads C2 at each arm's own serving cell
    during the warm-up, so only its sample counts are common across arms.
    """
    reference = engines[ARM_ORDER[0]][0]
    for arm in ARM_ORDER[1:]:
        other = engines[arm][0]
        assert np.array_equal(reference.world.positions, other.world.positions)
        assert np.array_equal(reference.world.shadow, other.world.shadow)
        assert np.array_equal(reference.world.map_error, other.world.map_error)
        assert np.array_equal(reference.rsrp, other.rsrp)
        assert np.array_equal(
            reference.channels.values, other.channels.values, equal_nan=True
        )
        assert np.array_equal(reference.attacker.targets, other.attacker.targets)
        assert reference.diagnostic == other.diagnostic
        assert reference.calibration.samples == other.calibration.samples
        for t in (0, 500, 2999):
            assert np.array_equal(
                reference.attacker.peer_compromised(t), other.attacker.peer_compromised(t)
            )


def test_paired_seeds_differ_but_repeat(cfg):
    """Different seeds give different worlds; the same seed reproduces bit-exactly."""
    first = Engine(cfg, "obs_dhr", 1)
    again = Engine(cfg, "obs_dhr", 1)
    other = Engine(cfg, "obs_dhr", 2)
    assert np.array_equal(first.rsrp, again.rsrp)
    assert not np.array_equal(first.rsrp, other.rsrp)
    assert first.run().attack_success_attr == again.run().attack_success_attr


def test_one_run_of_the_new_model_is_pinned_bit_exactly():
    """A fixed row of the Revision B2' apparatus, pinned for future revisions."""
    cfg = load_config(("attacker.rho=1.0", "attacker.delta=10.0", "channels.sigma_map=2.0"))
    result = Engine(cfg, "obs_dhr_phys", 3).run()
    for column, expected in PINNED_RUN.items():
        assert getattr(result, column) == pytest.approx(expected, abs=1e-12), column


def test_only_the_veto_arm_changed_when_it_lost_a_check():
    """DESIGN 4.4: every arm but 5c is bit-identical across the check-set change.

    ``tests/data/arm_baseline_pre_check_set.json`` is a short run of every arm
    captured before the edit.  The fixture was regenerated on 2026-09-26 after
    the attack-free warm-up and online calibration correction, with arm 5c on
    its pre-edit four-check wiring.  Six arms must replay it exactly; arm 5c must
    differ in the one way the design fixed in advance, three checks instead of
    four and five compute units instead of six, and in nothing that is not
    downstream of the exclusions it no longer makes.
    """
    saved = json.loads(BASELINE_PRE_CHECK_SET.read_text())
    overrides = tuple(saved["overrides"])
    seed = int(saved["seed"])
    for arm, before in saved["arms"].items():
        engine = Engine(load_config(overrides), arm, seed)
        after = asdict(engine.run())
        after.pop("runtime_seconds", None)
        checks = getattr(engine.adjudicator, "checks", None)
        enabled = list(getattr(checks, "enabled", ()))
        if arm == "cheap_phys":
            assert before["_enabled_checks"] == list(CHECK_SETS["default"])
            assert enabled == ["serving_reciprocity", "map", "rate"]
            assert before["compute_per_decision"] == pytest.approx(6.0)
            assert after["compute_per_decision"] == pytest.approx(5.0)
            assert after["bytes_ota_per_ue_s"] == pytest.approx(
                before["bytes_ota_per_ue_s"]
            )
            continue
        assert enabled == before["_enabled_checks"], arm
        for column, value in before.items():
            if column == "_enabled_checks":
                continue
            assert after[column] == value, f"{arm}.{column}"


def test_only_the_veto_arm_changed_when_it_stopped_reading_the_peer():
    """DESIGN 4.4: the peer-reference and skip-disabled changes touch arm 5c alone.

    ``tests/data/arm_baseline_pre_peer.json`` is a short run of every arm
    captured before the edit.  The fixture was regenerated on 2026-09-26 after
    the attack-free warm-up and online calibration correction, with arm 5c on
    its pre-edit peer reference N.  The six other arms must replay it exactly, which
    also pins that skipping a disabled check's difference changes no verdict,
    since the decomposition arms never read a streak they did not enable.  Arm
    5c may move only in the columns an exclusion can move, and only a little.
    """
    saved = json.loads(BASELINE_PRE_PEER.read_text())
    overrides = tuple(saved["overrides"])
    for arm, before in saved["arms"].items():
        after = asdict(Engine(load_config(overrides), arm, int(saved["seed"])).run())
        after.pop("runtime_seconds", None)
        moved = {c for c in after if c != "_enabled_checks" and after[c] != before[c]}
        if arm != "cheap_phys":
            assert moved == set(), arm
            continue
        assert moved <= PEER_MOVED, sorted(moved)
        assert moved, "the veto arm must actually stop reading N"
        assert after["attack_success_attr"] == before["attack_success_attr"]
        assert after["compute_per_decision"] == pytest.approx(5.0)
        assert after["detect_rate_actionable"] == pytest.approx(
            before["detect_rate_actionable"], abs=0.005
        )


def _short_config():
    """Short run at the gate setting, for the warm-up tests."""
    return load_config(("sim.horizon=500", "attacker.delta=10.0", "attacker.rho=1.0",
                        "channels.sigma_map=2.0"))


def test_the_attacker_is_silent_during_the_warm_up(monkeypatch):
    """DESIGN 1: no slot before ``warmup`` is poisoned or reaches the attacker."""
    cfg = _short_config()
    engine = Engine(cfg, "obs_dhr_phys", 0)
    calls: list[int] = []
    poison = engine.attacker.poison

    def spy(t, readings, serving, load, rsrp):
        calls.append(t)
        return poison(t, readings, serving, load, rsrp)

    monkeypatch.setattr(engine.attacker, "poison", spy)
    seen: list[tuple[int, np.ndarray, np.ndarray]] = []
    observe = engine.collector.observe

    def record(readings, serving):
        seen.append((engine.collector.slots, readings.copy(), serving.copy()))
        observe(readings, serving)

    monkeypatch.setattr(engine.collector, "observe", record)
    engine.run()
    warmup = cfg.sim.warmup
    assert calls == list(range(warmup, cfg.sim.horizon))
    assert [t for t, _, _ in seen] == list(range(warmup))
    for t, readings, serving in seen:
        clean = network_view(engine.channels.slot(t), serving)
        assert np.array_equal(readings, clean, equal_nan=True), t


def test_online_calibration_uses_the_serving_column_of_the_warm_up():
    """The serving sigma is the std of exactly ``warmup * n_ue`` serving samples."""
    cfg = _short_config()
    engine = Engine(cfg, "obs_dhr_phys", 0)
    result = engine.run()
    calibration = engine.calibration
    samples = engine.collector.samples("serving_reciprocity")
    assert calibration.samples["serving_reciprocity"] == cfg.sim.warmup * cfg.world.n_ue
    assert samples.size == cfg.sim.warmup * cfg.world.n_ue
    assert calibration.serving_reciprocity == float(np.std(samples))
    assert result.sigma_serving_recip_hat == calibration.serving_reciprocity
    assert result.sigma_c1_hat == engine.diagnostic.sigma_c1


def test_the_checks_are_idle_during_the_warm_up(monkeypatch):
    """No check fires and nothing is excluded before the thresholds exist."""
    cfg = _short_config()
    for arm in ("obs_dhr_phys", "obs_dhr_phys_dither", "cheap_phys"):
        engine = Engine(cfg, arm, 0)
        decide = engine.adjudicator.decide
        verdicts: list[tuple[int, object]] = []

        def spy(view, decide=decide, verdicts=verdicts):
            verdict = decide(view)
            verdicts.append((view.t, verdict))
            return verdict

        monkeypatch.setattr(engine.adjudicator, "decide", spy)
        engine.run()
        early = [v for t, v in verdicts if t < cfg.sim.warmup]
        assert len(early) == cfg.sim.warmup
        for verdict in early:
            assert not verdict.fired.any(), arm
            assert not verdict.excluded.any(), arm
            assert not verdict.fallback.any(), arm
        assert any(v.fired.any() for t, v in verdicts if t >= cfg.sim.warmup), arm


def test_recorded_thresholds_are_z_times_the_online_sigmas():
    """``runs.csv`` records the thresholds the running checks actually used."""
    cfg = _short_config()
    engine = Engine(cfg, "obs_dhr_phys", 0)
    result = engine.run()
    for name in ("serving_reciprocity", "neighbour_reciprocity", "map", "rate"):
        expected = cfg.checks.z * engine.calibration.sigma(name)
        assert getattr(result, f"thr_{name}") == pytest.approx(expected, rel=1e-12)
        assert engine.adjudicator.checks.thresholds.nominal(name) == pytest.approx(
            expected, rel=1e-12
        )
    assert engine.adjudicator.checks.thresholds is engine.thresholds


def test_one_run_is_well_under_twenty_seconds(cfg):
    """DESIGN 8 budget: a single run must finish inside 20 s."""
    start = time.perf_counter()
    Engine(cfg, "obs_dhr_phys", 3).run()
    assert time.perf_counter() - start < 20.0


def test_the_primary_metric_is_monotone_in_delta(cfg):
    """The per-targeted-slot rate rises with the attack size."""
    values = {
        arm: [
            Engine(load_config((f"attacker.delta={delta}", "attacker.rho=1.0")), arm, 0)
            .run()
            .attack_success_attr
            for delta in (0.0, 6.0, 10.0, 15.0)
        ]
        for arm in ("single", "obs_dhr")
    }
    for arm, series in values.items():
        assert np.all(np.diff(series) > 0.0), arm
    defended = Engine(
        load_config(("attacker.delta=10.0", "attacker.rho=0.0")), "obs_dhr_phys", 0
    ).run()
    baseline = Engine(
        load_config(("attacker.delta=10.0", "attacker.rho=0.0")), "single", 0
    ).run()
    assert defended.attack_success_attr < 0.1 * baseline.attack_success_attr


def test_the_vote_breaks_when_the_attacker_reaches_a_majority(cfg):
    """DESIGN 3.3: at rho = 1 the reachable pair {C1, N} is two voters of three."""
    blind = Engine(load_config(("attacker.rho=0.0",)), "obs_dhr", 0).run()
    reached = Engine(load_config(("attacker.rho=1.0",)), "obs_dhr", 0).run()
    single = Engine(load_config(("attacker.rho=1.0",)), "single", 0).run()
    assert not blind.majority_reachable
    assert reached.majority_reachable
    assert reached.attack_success_attr > 5.0 * blind.attack_success_attr
    assert reached.attack_success_attr >= 0.5 * single.attack_success_attr


def test_attributable_metric_removes_the_null(cfg):
    """DESIGN 6.1: the attributable rate is below the raw rate, and near zero at Δ = 0."""
    for arm in ARM_ORDER:
        null = Engine(load_config(("attacker.delta=0",)), arm, 0).run()
        assert null.attack_success_attr <= null.attack_success
        assert null.attack_success_attr < 0.01


def test_opportunity_denominator_uses_the_true_channels(cfg):
    """DESIGN 5: the actionable share grows with Δ and stays below the instant one."""
    shares, instant = [], []
    for delta in (0.0, 6.0, 10.0, 15.0):
        result = Engine(load_config((f"attacker.delta={delta}",)), "single", 0).run()
        shares.append(result.actionable_share)
        instant.append(result.actionable_share_inst)
    assert all(np.diff(shares) > 0)
    assert shares[0] < 0.1
    assert all(s < i for s, i in zip(shares, instant, strict=True))


def test_attack_success_is_measured_only_over_targeted_ue_slots(cfg):
    """With p = 0 there is no targeted UE-slot and attack success is undefined."""
    result = Engine(load_config(("attacker.p=0.0",)), "single", 0).run()
    assert result.n_targets == 0
    assert np.isnan(result.attack_success)
    assert result.false_exclusion_rate == 0.0


def test_false_exclusion_is_measured_only_over_clean_ues(cfg):
    """Every UE targeted means no clean UE remains and false exclusion is undefined."""
    result = Engine(load_config(("attacker.p=1.0",)), "obs_dhr_phys", 0).run()
    assert result.n_targets == cfg.world.n_ue
    assert np.isnan(result.false_exclusion_rate)


def test_metric_denominators(cfg):
    """The collector divides by the denominators DESIGN 6 names."""
    collector = MetricsCollector(warmup=0, slot_seconds=0.1, n_ue=4)
    tracker = MissedHandoverTracker(4, 5)
    targets = np.array([True, True, False, False])
    excluded = np.zeros((5, 4), dtype=bool)
    excluded[C1, 2] = True
    fired = np.zeros((4, 4), dtype=bool)
    fired[0, 2] = True
    collector.observe(
        targets=targets,
        success=np.array([True, True, False, False]),
        attributable=np.array([True, False, False, False]),
        opportunity=np.array([True, True, False, False]),
        opportunity_instant=np.array([True, True, False, False]),
        detected=np.array([True, False, False, False]),
        excluded=excluded,
        fired=fired,
        voters=np.full(4, 3),
        fallback=np.zeros(4, dtype=bool),
        throughput=np.ones(4),
        deficit=np.array([0.0, 2.0, 0.0, 0.0]),
        outage=np.array([False, True, False, False]),
        wrong_cell=np.array([False, True, False, False]),
        check_units=4.0,
    )
    rates = collector.rates(tracker)
    assert rates["attack_success"] == pytest.approx(1.0)
    assert rates["attack_success_attr"] == pytest.approx(0.5)
    assert rates["attack_success_opp"] == pytest.approx(0.5)
    assert rates["actionable_share"] == pytest.approx(1.0)
    assert rates["detect_rate"] == pytest.approx(0.5)
    assert rates["false_exclusion_rate"] == pytest.approx(0.5)
    assert rates["false_exclusion_rate_ch"] == pytest.approx(0.25)
    assert rates["fe_serving_reciprocity"] == pytest.approx(0.5)
    assert rates["rsrp_deficit"] == pytest.approx(0.5)
    assert rates["outage_share"] == pytest.approx(0.25)
    assert rates["wrong_cell_share"] == pytest.approx(0.25)
    assert collector.mean_check_units(1) == pytest.approx(4.0)


def test_missed_handover_tracker_counts_events_not_slots():
    """One declined recommendation is one miss, not one per slot."""
    tracker = MissedHandoverTracker(1, ttt=5)
    for t in range(12):
        tracker.observe(t, np.array([3]), scoring=True)
    assert tracker.events == 1
    assert tracker.missed == 1

    withdrawn = MissedHandoverTracker(1, ttt=5)
    withdrawn.observe(0, np.array([3]), scoring=True)
    withdrawn.observe(1, np.array([KEEP]), scoring=True)
    withdrawn.observe(2, np.array([KEEP]), scoring=True)
    assert withdrawn.events == 1
    assert withdrawn.missed == 0

    matched = MissedHandoverTracker(1, ttt=5)
    for t in range(3):
        matched.observe(t, np.array([3]), scoring=True)
    matched.resolve(np.array([0]), np.array([3]), scoring=True)
    assert matched.events == 1
    assert matched.missed == 0


def test_harm_metrics_are_reported_for_every_arm(engines):
    """DESIGN 6.2: refusing to act and serving the wrong cell are both visible."""
    for _, result in engines.values():
        assert 0.0 < result.missed_handover_rate < 1.0
        assert result.missed_handover_per_ue_slot > 0.0
        assert result.oracle_handover_rate > 0.0
        assert result.rsrp_deficit >= 0.0
        assert 0.0 <= result.outage_share <= 1.0
        assert 0.0 <= result.wrong_cell_share <= 1.0


def test_byte_ledger_and_measured_channels(cfg, engines):
    """DESIGN 6.4: C3 is billed per neighbour report actually used."""
    ledger = ByteLedger()
    ledger.charge(C1, 40.0, 3)
    assert ledger.total == pytest.approx(120.0)
    assert ledger.total_excluding((C1,)) == pytest.approx(0.0)
    expected = {
        "single": (C1,),
        "model_dhr3": (C1,),
        "obs_dhr": (C1, C2, C3, C4),
        "obs_dhr_phys": (C1, C2, C3, C4),
        "obs_dhr_phys_dither": (C1, C2, C3, C4),
        "cheap_phys": (C1, C2, C4),
        "model_dhr_param": (C1,),
    }
    neighbours = cfg.world.n_cells - 1
    for arm, (engine, result) in engines.items():
        assert measured_channels(arm, engine.bank) == expected[arm]
        per_slot = sum(
            cfg.cost.channel_bytes[c] * (neighbours if c == C3 else 1) for c in expected[arm]
        )
        assert result.bytes_per_ue_s == pytest.approx(per_slot / cfg.sim.slot_seconds)
    assert engines["cheap_phys"][1].bytes_ota_per_ue_s == pytest.approx(
        engines["single"][1].bytes_ota_per_ue_s
    )
    assert engines["obs_dhr_phys"][1].bytes_ota_per_ue_s == pytest.approx(4000.0)


def test_compute_units_per_decision(cfg, engines):
    """DESIGN 6.4: executor runs plus one unit per enabled check, nothing else."""
    expected = {"single": 1.0, "model_dhr3": 3.0, "obs_dhr": 3.0, "obs_dhr_phys": 7.0,
                "obs_dhr_phys_dither": 7.0, "cheap_phys": 5.0, "model_dhr_param": 3.0}
    for arm, (_, result) in engines.items():
        assert result.compute_per_decision == pytest.approx(expected[arm])


def test_voting_channels_and_majority_reach(engines):
    """DESIGN 3.3: three voters for the observation arms, two for the cheap one."""
    counts = {"single": 1, "model_dhr3": 3, "obs_dhr": 3, "obs_dhr_phys": 3,
              "obs_dhr_phys_dither": 3, "cheap_phys": 2, "model_dhr_param": 3}
    for arm, (engine, result) in engines.items():
        assert result.n_voting_channels == counts[arm]
        assert engine.voting_channels[0] == C1
        assert not result.majority_reachable or arm in ("single", "model_dhr3",
                                                          "model_dhr_param")
    assert set(engines["obs_dhr"][0].voting_channels) == {C1, N, C4}


def test_serving_cell_only_changes_on_a_handover_decision(cfg):
    """Handover counts equal the number of non-KEEP verdicts after the warm-up."""
    engine = Engine(cfg, "single", 0)
    result = engine.run()
    assert 0.0 < result.handover_rate < 1.0
    assert engine.metrics.handovers == int(
        round(result.handover_rate * engine.metrics.ue_slots)
    )
    assert result.wrong_handover_rate <= result.handover_rate
    assert KEEP == -1


def test_run_cli_job_expansion():
    """Sweep blocks expand into the deduplicated job list the CLI executes."""
    block = normalise_block({"arms": "all", "seeds": "0-1", "delta": [0, 10],
                             "rho": [0.0, 1.0], "sigma_map": [2.0, 6.0]})
    jobs = build_jobs([block, block])
    assert len(jobs) == len(ARM_ORDER) * 2 * 2 * 2 * 2
    assert len(set(jobs)) == len(jobs)
    assert parse_int_list("0-2,5") == [0, 1, 2, 5]
    assert resolve_arms("all") == list(ARM_ORDER)
    with pytest.raises(ValueError, match="unknown arms"):
        resolve_arms("nope")
    job = Job("obs_dhr_phys", 0, 0.2, 10.0, 1.0, 4.0, "trap", "map", 3.0, 10, 1)
    assert "checks.enabled=[map]" in job.overrides()
    assert "attacker.ramp_slots=10" in job.overrides()
    assert "channels.sigma_map=4.0" in job.overrides()
    assert "checks.persistence_slots=1" in job.overrides()
    assert set(CHECK_SETS["default"]) == {"serving_reciprocity", "neighbour_reciprocity",
                                          "map", "rate"}


def test_streams_are_named_as_the_design_requires():
    """DESIGN 8 names five RNG streams; all five are spawned."""
    streams = make_streams(0)
    assert set(streams) == {"world", "mobility", "noise", "attacker", "policy"}
