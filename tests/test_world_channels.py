"""Path loss, shadowing, the DESIGN 2 channels and the calibration."""

from __future__ import annotations

import numpy as np
import pytest

from wes.calibration import WarmupCollector, offline_channel_diagnostic
from wes.channels import C1, C2, C3, C4, N, build_channels, network_view
from wes.config import ConfigError, load_config
from wes.radio import path_loss_db, rsrp_true
from wes.world import build_world, cell_positions, make_streams, map_error_field, shadow_field


@pytest.fixture(scope="module")
def cfg():
    """Base configuration used by every test in this module."""
    return load_config()


def test_config_rejects_missing_key(cfg):
    """An unknown section value raises ConfigError rather than being ignored."""
    with pytest.raises(ConfigError):
        from wes.config import SimConfig, _build

        _build(SimConfig, {"sim": {}})


def test_path_loss_at_100m_and_1km(cfg):
    """PL(100 m) = 90.5 dB and PL(1 km) = 128.1 dB (DESIGN 1)."""
    assert path_loss_db(100.0, cfg) == pytest.approx(128.1 - 37.6, abs=1e-9)
    assert path_loss_db(1000.0, cfg) == pytest.approx(128.1, abs=1e-9)


def test_cell_layout_is_a_7_cell_cluster(cfg):
    """Six ring cells sit one inter-site distance from the centre cell."""
    cells = cell_positions(cfg)
    assert cells.shape == (7, 2)
    assert np.allclose(cells[0], 0.0)
    assert np.allclose(np.linalg.norm(cells[1:], axis=-1), cfg.world.isd)


def test_shadowing_correlation_decays_with_distance(cfg):
    """The shadowing autocorrelation follows exp(-d / 50 m) along a straight path."""
    rng = np.random.default_rng(7)
    horizon, n_ue, step = 4000, 40, 5.0
    positions = np.zeros((horizon, n_ue, 2))
    positions[:, :, 0] = (np.arange(horizon) * step)[:, None]
    field = shadow_field(cfg, positions, rng)
    series = field[:, :, 0]
    series = series - series.mean()
    variance = float(np.mean(series**2))
    empirical = []
    for lag in (1, 2, 5, 10, 20):
        empirical.append(float(np.mean(series[lag:] * series[:-lag])) / variance)
    expected = [np.exp(-lag * step / cfg.radio.shadow_decorr) for lag in (1, 2, 5, 10, 20)]
    assert np.all(np.diff(empirical) < 0.0)
    assert np.allclose(empirical, expected, atol=0.05)
    assert float(np.std(field)) == pytest.approx(cfg.radio.shadow_sigma, rel=0.1)


def test_channel_noise_standard_deviations(cfg):
    """C1-C3 report noise matches DESIGN 2 within 10 % over 20 000 samples."""
    rng = np.random.default_rng(11)
    rsrp = np.zeros((1000, 20, 7))
    channels = build_channels(cfg, rsrp, rng)
    for index, sigma in zip((C1, C2, C3), cfg.channels.sigmas, strict=True):
        sample = channels.values[index].ravel()[:20000]
        assert float(sample.std()) == pytest.approx(sigma, rel=0.1)


@pytest.mark.parametrize("sigma_map", [2.0, 4.0, 6.0])
def test_c4_map_error_has_the_configured_sigma_and_correlation(sigma_map):
    """DESIGN 2: eps_map carries sigma_map and the shadowing's spatial correlation."""
    local = load_config((f"channels.sigma_map={sigma_map}",))
    streams = make_streams(4)
    world = build_world(local, streams)
    rsrp = rsrp_true(local, world.positions, world.cells, world.shadow)
    channels = build_channels(local, rsrp, streams["noise"], world.map_error)
    error = channels.values[C4][: local.sim.warmup] - rsrp[: local.sim.warmup]
    assert float(np.std(error)) == pytest.approx(sigma_map, rel=0.1)
    series = world.map_error[:, :, 0]
    lag1 = float(np.mean(series[1:] * series[:-1]) / np.mean(series**2))
    lag50 = float(np.mean(series[50:] * series[:-50]) / np.mean(series**2))
    assert lag1 > lag50 > 0.0


def test_sigma_map_sweep_keeps_the_world_and_scales_the_field(cfg):
    """The sigma_map sweep is a common random number: the field only scales."""
    base = build_world(cfg, make_streams(2))
    wider = build_world(load_config(("channels.sigma_map=6.0",)), make_streams(2))
    assert np.array_equal(base.positions, wider.positions)
    assert np.array_equal(base.shadow, wider.shadow)
    assert np.allclose(wider.map_error, 3.0 * base.map_error)


def test_map_error_is_independent_of_the_report_noise(cfg):
    """DESIGN 2: eps_map is drawn from the world stream, not from the noise stream."""
    streams = make_streams(5)
    world = build_world(cfg, streams)
    rsrp = rsrp_true(cfg, world.positions, world.cells, world.shadow)
    channels = build_channels(cfg, rsrp, streams["noise"], world.map_error)
    warmup = cfg.sim.warmup
    noise = (channels.values[C1] - rsrp)[:warmup].ravel()
    error = world.map_error[:warmup].ravel()
    assert abs(float(np.corrcoef(noise, error)[0, 1])) < 0.05
    direct = map_error_field(cfg, world.positions, make_streams(5)["world"])
    assert not np.allclose(direct, world.map_error)


def test_c2_carries_only_the_serving_column(cfg):
    """DESIGN 2: the serving gNB measures its own link and nothing else."""
    rng = np.random.default_rng(3)
    rsrp = rng.normal(-95.0, 7.0, size=(1, 6, cfg.world.n_cells))
    channels = build_channels(cfg, rsrp, rng)
    serving = np.array([0, 1, 2, 3, 4, 5])
    readings = network_view(channels.slot(0), serving)
    rows = np.arange(serving.size)
    assert np.isfinite(readings[C2][rows, serving]).all()
    assert np.isnan(readings[C2]).sum() == serving.size * (cfg.world.n_cells - 1)
    assert np.array_equal(readings[N][rows, serving], readings[C2][rows, serving])
    others = np.ones_like(readings[N], dtype=bool)
    others[rows, serving] = False
    assert np.array_equal(readings[N][others], channels.values[C3][0][others])


def _seed_channels(cfg, seed):
    """True RSRP and clean channels of one seed."""
    streams = make_streams(seed)
    world = build_world(cfg, streams)
    rsrp = rsrp_true(cfg, world.positions, world.cells, world.shadow)
    return rsrp, build_channels(cfg, rsrp, streams["noise"], world.map_error)


def _online(cfg, rsrp, channels):
    """Warm-up collector fed the masked view with every UE on its strongest cell."""
    collector = WarmupCollector()
    for t in range(cfg.sim.warmup):
        serving = np.argmax(rsrp[t], axis=1)
        collector.observe(network_view(channels.slot(t), serving), serving)
    return collector


def test_offline_diagnostic_recovers_every_channel_sigma(cfg):
    """The offline diagnostic recovers DESIGN 2's generating noise constants."""
    _, channels = _seed_channels(cfg, 1)
    diagnostic = offline_channel_diagnostic(cfg, channels)
    assert diagnostic.sigma_c1 == pytest.approx(cfg.channels.sigma_c1, rel=0.05)
    assert diagnostic.sigma_c2 == pytest.approx(cfg.channels.sigma_c2, rel=0.05)
    assert diagnostic.sigma_c3 == pytest.approx(cfg.channels.sigma_c3, rel=0.05)
    assert diagnostic.sigma_map == pytest.approx(cfg.channels.sigma_map, rel=0.05)
    assert set(diagnostic.row()) == {"sigma_c1_hat", "sigma_map_hat"}


def test_online_calibration_reads_only_what_the_serving_gnb_has(cfg):
    """DESIGN 4.2: every check sigma comes from the masked warm-up view.

    Serving reciprocity has one sample per UE-slot at the serving column,
    neighbour reciprocity one per UE, neighbour cell and slot, and each sigma is
    the standard deviation of exactly those samples.
    """
    rsrp, channels = _seed_channels(cfg, 1)
    collector = _online(cfg, rsrp, channels)
    calibration = collector.calibration(cfg)
    warmup, n_ue, n_cells = cfg.sim.warmup, cfg.world.n_ue, cfg.world.n_cells
    assert calibration.samples == {
        "serving_reciprocity": warmup * n_ue,
        "neighbour_reciprocity": warmup * n_ue * (n_cells - 1),
        "map": warmup * n_ue * n_cells,
        "rate": (warmup - 1) * n_ue * n_cells,
    }
    rows = np.arange(n_ue)
    serving, neighbour = [], []
    for t in range(warmup):
        cell = np.argmax(rsrp[t], axis=1)
        values = channels.values[:, t]
        serving.append(values[C1][rows, cell] - values[C2][rows, cell])
        others = np.ones((n_ue, n_cells), dtype=bool)
        others[rows, cell] = False
        neighbour.append((values[C1] - values[C3])[others])
    c1 = channels.values[C1][:warmup]
    for check, expected in (
        ("serving_reciprocity", np.concatenate(serving)),
        ("neighbour_reciprocity", np.concatenate(neighbour)),
        ("map", c1 - channels.values[C4][:warmup]),
        ("rate", np.diff(c1, axis=0)),
    ):
        assert calibration.sigma(check) == pytest.approx(float(np.std(expected)), rel=1e-9)
    assert calibration.serving_reciprocity == pytest.approx(
        float(np.hypot(cfg.channels.sigma_c1, cfg.channels.sigma_c2)), rel=0.1
    )
    with pytest.raises(KeyError):
        calibration.sigma("geometry")


def test_online_calibration_needs_two_warm_up_slots(cfg):
    """A warm-up too short to form a rate difference cannot calibrate."""
    rsrp, channels = _seed_channels(cfg, 1)
    collector = WarmupCollector()
    serving = np.argmax(rsrp[0], axis=1)
    collector.observe(network_view(channels.slot(0), serving), serving)
    with pytest.raises(ValueError, match="rate"):
        collector.calibration(cfg)


def test_calibration_tracks_a_wider_map(cfg):
    """A wider radio map widens the map threshold and nothing else materially."""
    wide = load_config(("channels.sigma_map=6.0",))
    rsrp, channels = _seed_channels(wide, 1)
    assert offline_channel_diagnostic(wide, channels).sigma_map == pytest.approx(
        6.0, rel=0.05
    )
    calibration = _online(wide, rsrp, channels).calibration(wide)
    assert calibration.map_consistency > 5.0
    assert calibration.serving_reciprocity < 3.0


def test_world_is_reproducible_and_bounded(cfg):
    """Two runs of the same seed give identical worlds inside the toroidal square."""
    first = build_world(cfg, make_streams(0))
    second = build_world(cfg, make_streams(0))
    assert np.array_equal(first.positions, second.positions)
    assert np.array_equal(first.shadow, second.shadow)
    assert np.array_equal(first.map_error, second.map_error)
    assert np.all(np.abs(first.positions) <= cfg.world.area_half + 1e-9)
    rsrp = rsrp_true(cfg, first.positions, first.cells, first.shadow)
    assert rsrp.shape == (cfg.sim.horizon, cfg.world.n_ue, cfg.world.n_cells)
    assert np.isfinite(rsrp).all()


def test_shadow_cell_correlation_is_configurable(cfg):
    """The inter-cell correlation is explicit; 0.0 keeps DESIGN 1's independence."""
    rng_a, rng_b = np.random.default_rng(2), np.random.default_rng(2)
    positions = np.zeros((500, 20, 2))
    positions[:, :, 0] = (np.arange(500) * 4.0)[:, None]
    independent = shadow_field(cfg, positions, rng_a)
    correlated = shadow_field(
        load_config(("radio.shadow_cell_corr=0.8",)), positions, rng_b
    )

    def mean_cross_correlation(field: np.ndarray) -> float:
        flat = field.reshape(-1, field.shape[-1])
        matrix = np.corrcoef(flat, rowvar=False)
        off = matrix[~np.eye(field.shape[-1], dtype=bool)]
        return float(off.mean())

    assert abs(mean_cross_correlation(independent)) < 0.05
    assert mean_cross_correlation(correlated) > 0.6
    assert float(np.std(correlated)) == pytest.approx(cfg.radio.shadow_sigma, rel=0.1)
