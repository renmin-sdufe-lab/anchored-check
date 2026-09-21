"""Frozen configuration tree for the WES pilot (DESIGN sections 1-6).

Every constant lives in ``conf/base.yaml``.  :func:`load_config` merges the base
file with dotlist overrides and materialises the result as nested frozen
dataclasses, so no downstream module can mutate configuration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar, get_args, get_origin, get_type_hints

from omegaconf import OmegaConf

logger = logging.getLogger(__name__)

CONF_DIR = Path(__file__).resolve().parent.parent / "conf"

T = TypeVar("T")


class ConfigError(ValueError):
    """Raised when the merged configuration cannot be turned into a SimConfig."""


@dataclass(frozen=True)
class SimSection:
    """Horizon, warm-up and slot duration (DESIGN 1)."""

    horizon: int
    warmup: int
    slot_seconds: float

    @property
    def metric_slots(self) -> int:
        """Number of slots contributing to the metrics."""
        return self.horizon - self.warmup

    @property
    def metric_seconds(self) -> float:
        """Wall-clock seconds of the metric window."""
        return self.metric_slots * self.slot_seconds


@dataclass(frozen=True)
class WorldSection:
    """Cell layout, UE population and mobility bounds (DESIGN 1)."""

    n_cells: int
    isd: float
    n_ue: int
    speed_min: float
    speed_max: float
    leg_min: float
    leg_max: float
    area_half: float


@dataclass(frozen=True)
class RadioSection:
    """Path loss, shadowing and noise (DESIGN 1)."""

    tx_power_dbm: float
    pl_a: float
    pl_b: float
    min_distance: float
    shadow_sigma: float
    shadow_decorr: float
    shadow_cell_corr: float
    noise_dbm: float
    outage_rsrp_dbm: float


@dataclass(frozen=True)
class ChannelSection:
    """Report noise of C1-C3 and the radio-map error of C4 (DESIGN 2)."""

    sigma_c1: float
    sigma_c2: float
    sigma_c3: float
    sigma_map: float

    @property
    def sigmas(self) -> tuple[float, float, float]:
        """Report-noise standard deviations of C1, C2 and C3 in dB."""
        return (self.sigma_c1, self.sigma_c2, self.sigma_c3)


@dataclass(frozen=True)
class RuleSection:
    """A3 rule parameters and the three model-diversity variants (DESIGN 3)."""

    hysteresis: float
    ttt: int
    variant_hysteresis: tuple[float, ...]
    variant_ttt: tuple[int, ...]


@dataclass(frozen=True)
class CheckSection:
    """Physical-consistency checks of the adjudicator (DESIGN 3.3, 4).

    Revision B1 replaced the hand-picked dB thresholds of DESIGN 3 with
    ``z * sigma_diff``; Revision B2' calibrates every ``sigma_diff`` on the clean
    warm-up, applies the persistence rule to every check and lets arm 4d draw
    ``z`` per slot from ``[dither_low, dither_high]``.
    """

    z: float
    persistence_slots: int
    min_channels: int
    sigma_floor: float
    dither_low: float
    dither_high: float
    enabled: tuple[str, ...]

    @property
    def key(self) -> str:
        """Identifier of the enabled check set, used in ``runs.csv``."""
        return "+".join(self.enabled) or "none"


@dataclass(frozen=True)
class DhrSection:
    """Confidence down-weighting of the model-diversity adjudicator (DESIGN 3.3, arm 2)."""

    decay: float
    recover: float
    weight_floor: float
    weight_cap: float


@dataclass(frozen=True)
class AttackerSection:
    """Telemetry-poisoning attacker (DESIGN 5)."""

    p: float
    delta: float
    rho: float
    mode: str
    ramp_slots: int
    trap_reference_delta: float


@dataclass(frozen=True)
class CostSection:
    """Measurement bytes and compute units (DESIGN 3)."""

    bytes_c1: float
    bytes_c2: float
    bytes_c3: float
    bytes_c4: float
    compute_executor: float
    compute_check: float

    @property
    def channel_bytes(self) -> tuple[float, float, float, float]:
        """Per-report byte cost of C1, C2, C3 and C4."""
        return (self.bytes_c1, self.bytes_c2, self.bytes_c3, self.bytes_c4)


@dataclass(frozen=True)
class MetricSection:
    """Metric window parameters (DESIGN 6)."""

    pingpong_window: int


@dataclass(frozen=True)
class SimConfig:
    """The whole configuration tree."""

    sim: SimSection
    world: WorldSection
    radio: RadioSection
    channels: ChannelSection
    rule: RuleSection
    checks: CheckSection
    dhr: DhrSection
    attacker: AttackerSection
    cost: CostSection
    metrics: MetricSection


def _coerce(value: Any, annotation: Any) -> Any:
    """Convert one YAML value to the type its dataclass field declares."""
    if is_dataclass(annotation):
        return _build(annotation, value)
    origin = get_origin(annotation)
    if origin is tuple:
        (inner,) = {a for a in get_args(annotation) if a is not Ellipsis}
        return tuple(_coerce(v, inner) for v in value)
    if annotation is bool:
        return bool(value)
    if annotation is int:
        return int(value)
    if annotation is float:
        return float(value)
    if annotation is str:
        return str(value)
    return value


def _build(cls: type[T], mapping: Any) -> T:
    """Build one frozen dataclass from a plain mapping.

    Raises:
        ConfigError: If a field is missing from the mapping.
    """
    if not isinstance(mapping, dict):
        raise ConfigError(f"expected a mapping for {cls.__name__}, got {type(mapping).__name__}")
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for field in fields(cls):  # type: ignore[arg-type]
        if field.name not in mapping:
            raise ConfigError(f"missing configuration key {cls.__name__}.{field.name}")
        kwargs[field.name] = _coerce(mapping[field.name], hints[field.name])
    return cls(**kwargs)


def load_config(overrides: tuple[str, ...] = ()) -> SimConfig:
    """Load ``conf/base.yaml`` and apply dotlist overrides.

    Args:
        overrides: Dotlist strings such as ``"attacker.delta=15"``.

    Returns:
        The frozen configuration tree.

    Raises:
        ConfigError: If the merged tree does not match :class:`SimConfig`.
    """
    base = OmegaConf.load(CONF_DIR / "base.yaml")
    merged = OmegaConf.merge(base, OmegaConf.from_dotlist(list(overrides)))
    raw = OmegaConf.to_container(merged, resolve=True)
    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")
    cfg = _build(SimConfig, raw)
    logger.debug("loaded configuration with overrides %s", overrides)
    return cfg


def config_to_yaml(cfg: SimConfig) -> str:
    """Render a configuration tree back to YAML for the run output directory."""
    return OmegaConf.to_yaml(OmegaConf.create(_asdict(cfg)))


def _asdict(obj: Any) -> Any:
    """Recursively convert frozen dataclasses to plain containers."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _asdict(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, tuple):
        return [_asdict(v) for v in obj]
    return obj
