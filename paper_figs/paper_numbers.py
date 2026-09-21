"""Recompute every number the article quotes in its case study from ``runs.csv``.

Run from the package root: ``uv run python paper_figs/paper_numbers.py``.
Reads the ``runs.csv`` of the main run and of the three diagnostics under
``data/`` only; nothing is taken from a report, so a mismatch between this
script and the article is a finding, not a formatting difference.  Intervals
are paired 95 % Student-t intervals over the ten common-random-number seeds
(df = 9).

Arm 5c is quoted from ``data/diag_veto`` alone: its ``b2`` rows ran a check
whose reference travels over an interface the arm does not pay for (DESIGN 4.4)
and are retired.
"""
from __future__ import annotations

import contextlib
import csv
import math
import statistics
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
RUNS = DATA / "b2" / "runs.csv"
DIAG = DATA / "diag_param" / "runs.csv"
VETO = DATA / "diag_veto" / "runs.csv"
PINGPONG = DATA / "diag_pingpong" / "runs.csv"
T9 = 2.262


def emit(*parts: object) -> None:
    """Write one output line, joining the parts with spaces."""
    sys.stdout.write(" ".join(str(part) for part in parts) + "\n")


def load(path: Path = RUNS) -> list[dict[str, object]]:
    """Load a runs.csv with numeric columns parsed."""
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key, value in list(row.items()):
            if key in ("arm", "mode", "check_set", "checks"):
                continue
            with contextlib.suppress(TypeError, ValueError):
                row[key] = float(value)
    return rows


def sel(rows: list[dict[str, object]], **where: object) -> list[dict[str, object]]:
    """Rows matching every keyword condition exactly."""
    out = []
    for row in rows:
        keep = True
        for key, want in where.items():
            have = row[key]
            keep = (have == want if isinstance(want, str)
                    else abs(float(have) - float(want)) < 1e-9)
            if not keep:
                break
        if keep:
            out.append(row)
    return out


def cell(rows: list[dict[str, object]], arm: str, delta: float, rho: float,
         sigma_map: float, col: str = "attack_success_attr", mode: str = "trap",
         ramp: float = 1, check_set: str = "default",
         persistence: float = 3) -> dict[int, float]:
    """Per-seed values of one column in one grid cell (exactly ten seeds)."""
    picked = sel(rows, arm=arm, delta=delta, rho=rho, sigma_map=sigma_map,
                 mode=mode, ramp_slots=ramp, check_set=check_set,
                 persistence_slots=persistence, p=0.2)
    out: dict[int, float] = {}
    for row in picked:
        seed = int(row["seed"])
        if seed in out:
            raise ValueError(f"duplicate seed {seed} in {arm} {delta} {rho} {sigma_map}")
        out[seed] = float(row[col])
    if len(out) != 10:
        raise ValueError(f"{arm} d={delta} rho={rho} s={sigma_map} {col}: {len(out)} seeds")
    return out


def mean_ci(values: list[float]) -> str:
    """Mean and half-width of the 95 % t-interval."""
    mean = statistics.mean(values)
    half = T9 * statistics.stdev(values) / math.sqrt(len(values))
    return f"{mean:.4f} ± {half:.4f}"


def mean(values: dict[int, float]) -> float:
    """Plain mean over seeds."""
    return statistics.mean(values.values())


def paired(a: dict[int, float], b: dict[int, float]) -> str:
    """Paired difference a − b with its t-interval."""
    return mean_ci([a[s] - b[s] for s in sorted(a)])


def corrected(rows: list[dict[str, object]], arm: str, delta: float, rho: float,
              sigma_map: float, **kw: object) -> float:
    """Mean attack-attributable rate less the arm's own Δ = 0 null (DESIGN 6.1)."""
    return mean(cell(rows, arm, delta, rho, sigma_map, **kw)) - mean(
        cell(rows, arm, 0, rho, sigma_map, **kw))


def veto_block(rows: list[dict[str, object]], veto: list[dict[str, object]]) -> None:
    """The map-veto arm 5c as re-measured by diag_veto (DESIGN 4.4)."""
    emit("\n== The map-veto arm, quoted from diag_veto (DESIGN 4.4) ==")
    emit(f"source: {VETO.parent.relative_to(DATA.parent)}")
    emit("(every arm-5c row printed above from b2 is retired, PROTOCOL.md row diag-veto)")
    for s in (2, 4, 6):
        for rho in (0, 0.5, 1):
            v = cell(veto, "cheap_phys", 10, rho, s)
            n = cell(veto, "cheap_phys", 0, rho, s)
            emit(f"5c Δ10 σ{s} ρ{rho}: {mean_ci(list(v.values()))}  null "
                 f"{mean_ci(list(n.values()))}")
    base = corrected(rows, "single", 10, 1, 2)
    emit(f"5c / single null-corrected at ρ1 σ2 Δ10: "
         f"{corrected(veto, 'cheap_phys', 10, 1, 2) / base:.3f}")
    for s in (2, 4, 6):
        m = cell(veto, "cheap_phys", 0, 0, s, col="missed_handover_rate")
        d = cell(veto, "cheap_phys", 0, 0, s, col="rsrp_deficit")
        emit(f"Δ0 5c σ{s}: missed/oracle {mean_ci(list(m.values()))}  rsrp_deficit "
             f"{mean_ci(list(d.values()))}")
    m5 = cell(veto, "cheap_phys", 10, 1, 2, col="missed_handover_rate")
    m1 = cell(rows, "single", 10, 1, 2, col="missed_handover_rate")
    emit(f"under attack (Δ10 ρ1 σ2) missed/oracle: 5c {mean_ci(list(m5.values()))}"
         f"  single {mean_ci(list(m1.values()))}")
    fb = cell(veto, "cheap_phys", 10, 1, 2, col="fallback_rate")
    fb0 = cell(veto, "cheap_phys", 0, 1, 2, col="fallback_rate")
    emit(f"5c fallback under attack {mean_ci(list(fb.values()))}  at Δ0 "
         f"{mean_ci(list(fb0.values()))}  under attack / p=0.2 {mean(fb) / 0.2:.3f}")
    comp = cell(veto, "cheap_phys", 10, 1, 2, col="compute_per_decision")
    ota = cell(veto, "cheap_phys", 10, 1, 2, col="bytes_ota_per_ue_s")
    emit(f"5c compute/decision {mean(comp):.2f}  OTA bytes/UE/s {mean(ota):.0f}")
    for s in (2, 4, 6):
        fe = cell(veto, "cheap_phys", 0, 0, s, col="false_exclusion_rate")
        emit(f"5c false exclusion at Δ0 σ{s}: {mean_ci(list(fe.values()))}")
    w = cell(veto, "cheap_phys", 10, 1, 2, col="wrong_handover_per_ho")
    w0 = cell(veto, "cheap_phys", 0, 1, 2, col="wrong_handover_per_ho")
    emit(f"5c wrong HO/HO under attack {mean_ci(list(w.values()))}  at Δ0 "
         f"{mean_ci(list(w0.values()))}")
    for s in (2, 4):
        for ramp in (1, 10, 20):
            v = cell(veto, "cheap_phys", 10, 1, s, ramp=ramp)
            det = cell(veto, "cheap_phys", 10, 1, s, ramp=ramp,
                       col="detect_rate_actionable")
            fbr = cell(veto, "cheap_phys", 10, 1, s, ramp=ramp, col="fallback_rate")
            emit(f"ramp {ramp} σ{s} ρ1 Δ10 5c: {mean_ci(list(v.values()))}"
                 f"  detection {mean(det):.3f}  fallback {mean(fbr):.4f}")


def pingpong_block(rows: list[dict[str, object]],
                   pingpong: list[dict[str, object]]) -> None:
    """The arm-4 check decomposition in the ping-pong mode (DESIGN 5.4)."""
    emit("\n== Ping-pong decomposition of arm 4 at both reaches (PROTOCOL.md) ==")
    emit(f"source: {PINGPONG.parent.relative_to(DATA.parent)}")
    for cs in ("default", "serving", "neighbour", "map", "rate"):
        for rho in (0, 1):
            det = cell(pingpong, "obs_dhr_phys", 10, rho, 2, col="detect_rate_actionable",
                       mode="pingpong", check_set=cs)
            emit(f"ping-pong detection, check_set={cs}, ρ{rho} σ2 Δ10: "
                 f"{mean_ci(list(det.values()))}")
    for rho in (0, 1):
        a = cell(pingpong, "obs_dhr_phys", 10, rho, 2, mode="pingpong")
        n = cell(pingpong, "obs_dhr_phys", 0, rho, 2, mode="pingpong")
        emit(f"ping-pong arm4 default ρ{rho}: {mean_ci(list(a.values()))}  null "
             f"{mean_ci(list(n.values()))}  corrected {mean(a) - mean(n):+.4f}")
    share = cell(rows, "obs_dhr_phys", 10, 1, 2, col="actionable_share")
    opp = cell(rows, "obs_dhr", 10, 1, 2, col="attack_success_opp")
    emit(f"b2 arm4 actionable_share ρ1 σ2 Δ10: {mean_ci(list(share.values()))}")
    emit(f"b2 arm3 attack_success_opp ρ1 σ2 Δ10: {mean_ci(list(opp.values()))}")
    for arm in ("single", "obs_dhr", "obs_dhr_phys"):
        m = cell(rows, arm, 10, 1, 2, col="missed_handover_rate")
        emit(f"b2 missed/oracle under attack (Δ10 ρ1 σ2) {arm}: "
             f"{mean_ci(list(m.values()))}")


def main() -> None:
    """Print every quoted number with its provenance."""
    rows = load()
    emit("== Lesson 1: rule diversity on a shared input ==")
    a1 = cell(rows, "single", 10, 0, 2)
    a1n = cell(rows, "single", 0, 0, 2)
    a2 = cell(rows, "model_dhr3", 10, 0, 2)
    a2n = cell(rows, "model_dhr3", 0, 0, 2)
    emit("arm1 Δ10:", mean_ci(list(a1.values())), "null", mean_ci(list(a1n.values())))
    emit("arm2' Δ10:", mean_ci(list(a2.values())), "null", mean_ci(list(a2n.values())))
    raw = mean(a2) / mean(a1)
    corr = (mean(a2) - mean(a2n)) / (mean(a1) - mean(a1n))
    emit(f"arm2'/arm1 raw {raw:.3f}  null-corrected {corr:.3f}")
    for arm in ("single", "model_dhr3", "obs_dhr_phys", "cheap_phys"):
        m = cell(rows, arm, 0, 0, 2, col="missed_handover_rate")
        mu = cell(rows, arm, 0, 0, 2, col="missed_handover_per_ue_slot")
        d = cell(rows, arm, 0, 0, 2, col="rsrp_deficit")
        emit(f"Δ0 {arm}: missed/oracle {mean_ci(list(m.values()))}  missed/UE-slot "
              f"{mean_ci(list(mu.values()))}  rsrp_deficit {mean_ci(list(d.values()))}")

    emit("\n== Lesson 2: the vote at ρ = 0 and ρ = 1 ==")
    for s in (2, 4, 6):
        for rho in (0, 0.5, 1):
            a3 = cell(rows, "obs_dhr", 10, rho, s)
            emit(f"arm3 σ{s} ρ{rho}: {mean_ci(list(a3.values()))}  /arm1 {mean(a3)/mean(a1):.3f}")
    emit(f"arm1/arm3 at σ2 ρ0: {mean(a1) / mean(cell(rows, 'obs_dhr', 10, 0, 2)):.1f}")
    for arm in ("single", "obs_dhr", "obs_dhr_phys", "cheap_phys"):
        w = cell(rows, arm, 10, 1, 2, col="wrong_handover_per_ho")
        emit(f"wrong HO/HO under attack (Δ10 ρ1 σ2) {arm}: {mean_ci(list(w.values()))}")

    emit("\n== Lesson 3: the anchored check ==")
    for s in (2, 4, 6):
        a3 = cell(rows, "obs_dhr", 10, 1, s)
        a4 = cell(rows, "obs_dhr_phys", 10, 1, s)
        fe = cell(rows, "obs_dhr_phys", 10, 1, s, col="false_exclusion_rate")
        thr = cell(rows, "obs_dhr_phys", 10, 1, s, col="thr_map")
        emit(f"σ{s} ρ1 Δ10: arm4 {mean_ci(list(a4.values()))}  arm4/arm3 {mean(a4)/mean(a3):.3f}"
              f"  paired arm4−arm3 {paired(a4, a3)}  FE {mean_ci(list(fe.values()))}"
              f"  thr_map {mean(thr):.1f} dB")
    for rho in (0, 1):
        for cs in ("map", "neighbour", "rate", "serving", "default"):
            det = cell(rows, "obs_dhr_phys", 10, rho, 2, col="detect_rate_actionable",
                       check_set=cs)
            emit(f"detection actionable, check_set={cs}, ρ{rho} σ2 Δ10: "
                  f"{mean_ci(list(det.values()))}")
    for delta in (6, 15):
        a3 = cell(rows, "obs_dhr", delta, 1, 2)
        a4 = cell(rows, "obs_dhr_phys", delta, 1, 2)
        det = cell(rows, "obs_dhr_phys", delta, 1, 2, col="detect_rate_actionable")
        emit(f"Δ{delta} ρ1 σ2: arm3 {mean_ci(list(a3.values()))}  arm4 {mean_ci(list(a4.values()))}"
              f"  arm4/arm3 {mean(a4)/mean(a3):.3f}  removed share {1-mean(a4)/mean(a3):.3f}"
              f"  detection {mean_ci(list(det.values()))}")
    for s in (2, 4):
        for ramp in (1, 10, 20):
            a4 = cell(rows, "obs_dhr_phys", 10, 1, s, ramp=ramp)
            det = cell(rows, "obs_dhr_phys", 10, 1, s, ramp=ramp, col="detect_rate_actionable")
            emit(f"ramp {ramp} σ{s} ρ1 Δ10 arm4: {mean_ci(list(a4.values()))}"
                  f"  detection {mean(det):.3f}")
    a4d = cell(rows, "obs_dhr_phys_dither", 10, 1, 2)
    a4 = cell(rows, "obs_dhr_phys", 10, 1, 2)
    emit("dither ρ1 σ2 Δ10:", mean_ci(list(a4d.values())), " arm4:",
          mean_ci(list(a4.values())), " paired", paired(a4d, a4))

    emit("\n== Lesson 4: the cheap arm ==")
    vals = []
    for s in (2, 4, 6):
        for rho in (0, 0.5, 1):
            vals.append(mean(cell(rows, "cheap_phys", 10, rho, s)))
    emit(f"5c Δ10 over ρ×σ: min {min(vals):.4f} max {max(vals):.4f}")
    fb = cell(rows, "cheap_phys", 10, 1, 2, col="fallback_rate")
    fb0 = cell(rows, "cheap_phys", 0, 1, 2, col="fallback_rate")
    emit("5c fallback under attack (Δ10 ρ1 σ2):", mean_ci(list(fb.values())),
          " at Δ0:", mean_ci(list(fb0.values())))
    for arm in ("single", "model_dhr3", "obs_dhr", "obs_dhr_phys",
                "obs_dhr_phys_dither", "cheap_phys"):
        b = cell(rows, arm, 10, 1, 2, col="bytes_ota_per_ue_s")
        c = cell(rows, arm, 10, 1, 2, col="compute_per_decision")
        emit(f"{arm}: OTA bytes/UE/s {mean(b):.0f}  compute/decision {mean(c):.2f}")
    d1 = cell(rows, "single", 0, 0, 2, col="rsrp_deficit")
    d4 = cell(rows, "obs_dhr_phys", 0, 0, 2, col="rsrp_deficit")
    d5 = cell(rows, "cheap_phys", 0, 0, 2, col="rsrp_deficit")
    emit("Δ0 rsrp_deficit paired arm4−arm1:", paired(d4, d1), " 5c−arm1:", paired(d5, d1))

    emit("\n== Null-corrected ratios quoted in the article (DESIGN 6.1) ==")
    base = corrected(rows, "single", 10, 0, 2)
    for arm, rho, s in [("model_dhr3", 0, 2), ("obs_dhr", 0, 2), ("obs_dhr", 0, 6),
                        ("obs_dhr", 1, 2), ("obs_dhr", 1, 4), ("obs_dhr", 1, 6),
                        ("cheap_phys", 1, 2)]:
        emit(f"{arm} ρ{rho} σ{s} Δ10 / single: {corrected(rows, arm, 10, rho, s) / base:.3f}")
    emit(f"single / obs_dhr at ρ0 σ2: {base / corrected(rows, 'obs_dhr', 10, 0, 2):.1f}")
    for s in (2, 4, 6):
        r = corrected(rows, "obs_dhr_phys", 10, 1, s) / corrected(rows, "obs_dhr", 10, 1, s)
        emit(f"arm4 / arm3 σ{s} ρ1 Δ10: {r:.3f}")
    for delta in (6, 15):
        r = corrected(rows, "obs_dhr_phys", delta, 1, 2) / corrected(rows, "obs_dhr", delta, 1, 2)
        emit(f"arm4 / arm3 Δ{delta} ρ1 σ2: {r:.3f}  removed {1 - r:.3f}")
    r = corrected(rows, "obs_dhr_phys_dither", 10, 1, 2) / corrected(rows, "obs_dhr_phys", 10, 1, 2)
    emit(f"dither / arm4 ρ1 σ2 Δ10: {r:.3f}")
    for delta in (6, 10):
        det = cell(rows, "obs_dhr_phys", delta, 0, 2, col="detect_rate_actionable", mode="pingpong")
        emit(f"ping-pong mode, arm4 detection, Δ{delta} ρ0 σ2: {mean_ci(list(det.values()))}")

    emit("\n== Parameter-diversity diagnostic (PROTOCOL.md, data/diag_param) ==")
    diag = load(DIAG)
    single = corrected(diag, "single", 10, 0, 2)
    param = corrected(diag, "model_dhr_param", 10, 0, 2)
    s10, s0 = cell(diag, "single", 10, 0, 2), cell(diag, "single", 0, 0, 2)
    p10, p0 = cell(diag, "model_dhr_param", 10, 0, 2), cell(diag, "model_dhr_param", 0, 0, 2)
    diffs = [(p10[k] - p0[k]) - (s10[k] - s0[k]) for k in sorted(s10)]
    emit(f"param Δ10 {mean_ci(list(p10.values()))}  single Δ10 {mean_ci(list(s10.values()))}"
         f"  null-corrected ratio {param / single:.3f}  paired corrected diff {mean_ci(diffs)}")
    for col in ("missed_handover_rate", "rsrp_deficit"):
        a = cell(diag, "single", 0, 0, 2, col=col)
        c = cell(diag, "model_dhr_param", 0, 0, 2, col=col)
        emit(f"Δ0 {col}: single {mean(a):.4f}  param {mean(c):.4f}")

    veto_block(rows, load(VETO))
    pingpong_block(rows, load(PINGPONG))


if __name__ == "__main__":
    main()
