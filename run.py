"""Command-line runner for the WES pilot simulation (DESIGN 8).

Examples:
    uv run python run.py --arms all --seeds 0-9 --delta 10 --rho 0 --tag pilot_b2
    uv run python run.py --sweep conf/sweeps/pilot_b2.yaml --tag pilot_b2
"""

from __future__ import annotations

import os

# Pin BLAS threading and the hash seed *before* numpy is
# imported anywhere in this process, not inside main() after pandas has already
# loaded its BLAS.
for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                  "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_variable, "1")
os.environ.setdefault("PYTHONHASHSEED", "0")

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import multiprocessing as mp  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import datetime  # noqa: E402
from importlib import metadata  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import pandas as pd  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402

from wes.config import config_to_yaml, load_config  # noqa: E402
from wes.decisions import ARM_ORDER  # noqa: E402
from wes.engine import Engine  # noqa: E402

logger = logging.getLogger("wes.run")

ROOT = Path(__file__).resolve().parent
PACKAGES = ("numpy", "pandas", "matplotlib", "omegaconf", "pytest")

#: Named check sets (DESIGN 4 plus the decomposition diagnostics).
CHECK_SETS: dict[str, tuple[str, ...]] = {
    "default": ("serving_reciprocity", "neighbour_reciprocity", "map", "rate"),
    "serving": ("serving_reciprocity",),
    "neighbour": ("neighbour_reciprocity",),
    "map": ("map",),
    "rate": ("rate",),
}


@dataclass(frozen=True)
class Job:
    """One simulation run: an arm, a seed and an attacker/check setting."""

    arm: str
    seed: int
    p: float
    delta: float
    rho: float
    sigma_map: float
    mode: str
    checks: str
    z: float
    ramp: int
    persist: int

    def overrides(self) -> tuple[str, ...]:
        """Configuration dotlist that materialises this job."""
        names = ",".join(CHECK_SETS[self.checks])
        return (
            f"attacker.p={self.p}",
            f"attacker.delta={self.delta}",
            f"attacker.rho={self.rho}",
            f"attacker.mode={self.mode}",
            f"attacker.ramp_slots={self.ramp}",
            f"channels.sigma_map={self.sigma_map}",
            f"checks.enabled=[{names}]",
            f"checks.z={self.z}",
            f"checks.persistence_slots={self.persist}",
        )


def run_job(job: Job) -> dict[str, Any]:
    """Execute one run and return its metrics row."""
    cfg = load_config(job.overrides())
    row = Engine(cfg, job.arm, job.seed).run().to_row()
    row["check_set"] = job.checks
    return row


def parse_int_list(text: str) -> list[int]:
    """Parse ``"0-9"``, ``"0,3,5"`` or ``"7"`` into a list of integers."""
    values: list[int] = []
    for part in str(text).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            low, high = part.split("-", 1)
            values.extend(range(int(low), int(high) + 1))
        else:
            values.append(int(part))
    return values


def parse_float_list(text: str) -> list[float]:
    """Parse a comma-separated list of floats."""
    return [float(p) for p in str(text).split(",") if str(p).strip()]


def parse_str_list(text: str) -> list[str]:
    """Parse a comma-separated list of names."""
    return [p.strip() for p in str(text).split(",") if p.strip()]


def resolve_arms(text: str | list[str]) -> list[str]:
    """Expand ``all`` or a comma-separated arm list into arm keys.

    Raises:
        ValueError: If an arm key is unknown.
    """
    arms = text if isinstance(text, list) else parse_str_list(text)
    if arms == ["all"]:
        return list(ARM_ORDER)
    unknown = [a for a in arms if a not in ARM_ORDER]
    if unknown:
        raise ValueError(f"unknown arms {unknown}; known: {list(ARM_ORDER)}")
    return arms


def build_jobs(blocks: list[dict[str, Any]]) -> list[Job]:
    """Expand sweep blocks into a deduplicated, ordered list of jobs.

    Raises:
        ValueError: If a block names an unknown check set.
    """
    seen: set[Job] = set()
    jobs: list[Job] = []
    for block in blocks:
        for check in block["checks"]:
            if check not in CHECK_SETS:
                raise ValueError(f"unknown check set {check!r}; known: {sorted(CHECK_SETS)}")
        product = (
            (arm, seed, p, delta, rho, sigma_map, mode, check, z, ramp, persist)
            for arm in block["arms"]
            for seed in block["seeds"]
            for p in block["p"]
            for delta in block["delta"]
            for rho in block["rho"]
            for sigma_map in block["sigma_map"]
            for mode in block["mode"]
            for check in block["checks"]
            for z in block["z"]
            for ramp in block["ramp"]
            for persist in block["persist"]
        )
        for values in product:
            arm, seed, p, delta, rho, sigma_map, mode, check, z, ramp, persist = values
            job = Job(arm, int(seed), float(p), float(delta), float(rho), float(sigma_map),
                      str(mode), str(check), float(z), int(ramp), int(persist))
            if job in seen:
                continue
            seen.add(job)
            jobs.append(job)
    return jobs


def normalise_block(raw: dict[str, Any]) -> dict[str, Any]:
    """Fill a sweep block with defaults and coerce every field to a list."""
    return {
        "arms": resolve_arms(raw.get("arms", "all")),
        "seeds": parse_int_list(raw.get("seeds", "0-9")),
        "p": [float(v) for v in raw.get("p", [0.2])],
        "delta": [float(v) for v in raw.get("delta", [10.0])],
        "rho": [float(v) for v in raw.get("rho", [0.0])],
        "sigma_map": [float(v) for v in raw.get("sigma_map", [2.0])],
        "mode": [str(v) for v in raw.get("mode", ["trap"])],
        "checks": [str(v) for v in raw.get("checks", ["default"])],
        "z": [float(v) for v in raw.get("z", [3.0])],
        "ramp": [int(v) for v in raw.get("ramp", [1])],
        "persist": [int(v) for v in raw.get("persist", [3])],
    }


def load_sweep(path: Path) -> tuple[str, list[dict[str, Any]]]:
    """Read a sweep YAML into a tag and a list of normalised blocks.

    Raises:
        ValueError: If the file does not contain a mapping.
    """
    raw = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
    if not isinstance(raw, dict):
        raise ValueError(f"sweep file {path} must contain a mapping")
    blocks = [normalise_block(block) for block in raw.get("jobs", [])]
    return str(raw.get("tag", "sweep")), blocks


def environment_info(n_jobs: int) -> dict[str, Any]:
    """Record interpreter, platform, package versions and the git commit."""
    versions: dict[str, str] = {}
    for package in PACKAGES:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:  # pragma: no cover - optional package
            versions[package] = "not installed"
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
            check=True, timeout=15,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):  # pragma: no cover - no git
        commit = "unknown"
    return {
        "timestamp": datetime.now().astimezone().isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", "unset"),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", "unset"),
        "packages": versions,
        "git_commit": commit,
        "command": " ".join(sys.argv),
        "n_jobs": n_jobs,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Run the WES pilot simulation.")
    parser.add_argument("--sweep", type=Path, default=None, help="sweep YAML to expand")
    parser.add_argument("--arms", default="all", help="'all' or comma-separated arm keys")
    parser.add_argument("--seeds", default="0-9", help="seed list such as '0-9'")
    parser.add_argument("--p", default="0.2", help="targeted UE fractions")
    parser.add_argument("--delta", default="10", help="falsification magnitudes in dB")
    parser.add_argument("--rho", default="0", help="attacker reach on N's neighbour columns")
    parser.add_argument("--sigma-map", default="2", help="radio-map error std in dB")
    parser.add_argument("--mode", default="trap", help="attacker modes")
    parser.add_argument("--checks", default="default", help="check sets")
    parser.add_argument("--z", default="3", help="threshold multipliers z (DESIGN 4)")
    parser.add_argument("--ramp", default="1", help="attacker ramp lengths in slots")
    parser.add_argument("--persist", default="3", help="consecutive violations to exclude")
    parser.add_argument("--tag", default="run", help="output directory suffix")
    parser.add_argument("--workers", type=int, default=0, help="processes (0 = cpu_count)")
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs")
    return parser.parse_args(argv)


def blocks_from_args(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Build a single sweep block from the command-line flags."""
    return [
        normalise_block(
            {
                "arms": resolve_arms(args.arms),
                "seeds": args.seeds,
                "p": parse_float_list(args.p),
                "delta": parse_float_list(args.delta),
                "rho": parse_float_list(args.rho),
                "sigma_map": parse_float_list(args.sigma_map),
                "mode": parse_str_list(args.mode),
                "checks": parse_str_list(args.checks),
                "z": parse_float_list(args.z),
                "ramp": parse_int_list(args.ramp),
                "persist": parse_int_list(args.persist),
            }
        )
    ]


def main(argv: list[str] | None = None) -> Path:
    """Run every job, write the output directory and return its path."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    if args.sweep is not None:
        tag, blocks = load_sweep(args.sweep)
        tag = args.tag if args.tag != "run" else tag
    else:
        tag, blocks = args.tag, blocks_from_args(args)
    jobs = build_jobs(blocks)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = Path(args.outdir) / f"{stamp}_{tag}"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "config.yaml").write_text(
        config_to_yaml(load_config())
        + "\n"
        + OmegaConf.to_yaml(OmegaConf.create({"sweep": {"tag": tag, "blocks": blocks}}))
    )
    (outdir / "env.json").write_text(json.dumps(environment_info(len(jobs)), indent=2))

    workers = args.workers or (os.cpu_count() or 1)
    logger.info("running %d jobs on %d workers -> %s", len(jobs), workers, outdir)
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    context = mp.get_context("spawn")
    with context.Pool(processes=workers) as pool:
        for done, row in enumerate(pool.imap_unordered(run_job, jobs, chunksize=1), 1):
            rows.append(row)
            if done % 200 == 0 or done == len(jobs):
                logger.info("%d/%d done (%.1f s)", done, len(jobs), time.perf_counter() - start)
    frame = pd.DataFrame(rows).sort_values(
        ["mode", "check_set", "persistence_slots", "z", "ramp_slots", "sigma_map", "p",
         "delta", "rho", "arm", "seed"]
    )
    frame.to_csv(outdir / "runs.csv", index=False)
    elapsed = time.perf_counter() - start
    logger.info("finished %d runs in %.1f s -> %s", len(rows), elapsed, outdir / "runs.csv")
    (outdir / "env.json").write_text(
        json.dumps({**environment_info(len(jobs)), "wall_seconds": elapsed}, indent=2)
    )
    return outdir


if __name__ == "__main__":
    main()
