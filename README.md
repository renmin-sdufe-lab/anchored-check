# Wireless Endogenous Security for 6G Control Agents: Observation Diversity and Anchored Consistency Checks

Simulation code, pre-registered protocol and frozen run tables behind the
article of that title.

A discrete-slot simulator of handover decisions in a seven-cell RAN under
**telemetry poisoning**. An adversary on the reporting path inflates a
neighbour cell in a UE's measurement report to pull the UE into a congested
*trap* cell, or deflates its serving cell to make it bounce. Because every
executor reads that same report, the falsification is a *common cause*: running
several handover rules on it changes nothing.

The simulator compares that rule diversity against **observation diversity**,
the same rule on several channels, adjudicated, and against adjudication that
first excludes a channel failing a **physical-consistency check**. The model is
built at three voting channels of which the attacker can reach two, so the vote
is genuinely lost at full reach and the question becomes what the adjudicator
can still do. The answer turns on what each check is *anchored* on: a check
whose reference the attacker can reach decays to nothing as its reach grows, and
a check anchored on a measurement out of reach does not.

`DESIGN.md` is the model specification: world, radio, mobility, the four
observation channels and their noise, the handover rule, the executors and
adjudicators, the checks and their calibration, the attacker, the metrics, the
costs and the random-number discipline. Source comments cite its section
numbers. `PROTOCOL.md` records the hypothesis, the gates and the predictions
fixed before each run, with the outcomes and the refutations.

## The seven arms

| arm | key | voters | adjudication |
|---|---|---|---|
| 1 | `single` | `C1` | none |
| 2′ | `model_dhr3` | three decision families (A3, load-aware, trend) on `C1` | weighted majority with confidence down-weighting |
| 3 | `obs_dhr` | `C1`, `N`, `C4` | strict majority |
| 4 | `obs_dhr_phys` | `C1`, `N`, `C4` | exclude by the checks, then a majority of the survivors |
| 4d | `obs_dhr_phys_dither` | `C1`, `N`, `C4` | as arm 4, with the thresholds dithered per UE-slot |
| 5c | `cheap_phys` | `C1`, `C4` (no Xn) | after its own three checks, hand over only on unanimity |
| 2p | `model_dhr_param` | three A3 executors on `C1` at (2 dB, 4 slots), (3 dB, 5) and (4 dB, 6) | as arm 2′ |

`C1` is the UE measurement report over all cells; `N` is the network's own
assembly, the serving gNB's uplink measurement of the serving link plus each
neighbour's uplink measurement of its own link over Xn; `C4` is the operator's
radio map, whose error standard deviation `σ_map` is the design parameter of the
sweep. Only `C1` and `N`'s neighbour columns can be written from the reporting
path, so arms 3, 4 and 4d lose their majority at full attacker reach and arm 5c
never does.

Arm 5c is the one arm with no Xn, and it is held to that literally. It votes
`C1` and `C4` and is billed for those plus the serving gNB's own `C2`, so it
runs only the three checks whose references it pays for: serving reciprocity,
map consistency and rate consistency. It hands
over only when both channels survive their checks and name the same target, and
otherwise keeps the serving cell; when `C1` is excluded it is left with one
voter, which is below `checks.min_channels`, so the fallback decides and the arm
follows the radio map alone. It never reads the composite channel `N`, neither
as a value nor as an index, and a test asserts that its exclusions are invariant
under arbitrary tampering with `N` while arm 4's are not.

Arm 2p is a diagnostic rather than a member of the main sweep: it puts three
*parameter settings* of the one rule where arm 2′ puts three *decision
families*, on the same single report, and it is run on its own design point
(`conf/sweeps/diag_param.yaml`).

## The four checks

Each compares `C1` against a reference and excludes after three consecutive
violations of a `3σ̂` bound, where every `σ̂` is measured on that run's warm-up
rather than read out of the configuration. The first `sim.warmup = 300` slots
are attack-free: the attacker is silent and the checks are idle. At the end of
the warm-up every threshold is calibrated from the readings the serving gNB had
during it (`C2` on the serving link only, the `C3` reports on the neighbour
links), and scoring starts at slot 300. The `sigma_c1_hat` and `sigma_map_hat`
columns of `runs.csv` are an offline diagnostic over the full clean array that
no check uses.

| check | reference | anchored on something the attacker can reach? |
|---|---|---|
| serving reciprocity | the serving gNB's own uplink measurement | no |
| neighbour reciprocity | the neighbours' uplink measurements in `N` | yes, at `ρ > 0`, and the exclusion is symmetric |
| map consistency | the operator's radio map | no |
| rate consistency | `C1`'s own previous slot | no, but a slow ramp stays under the bound |

Beside each check's measured false-exclusion rate the analysis prints its
analytic Gaussian floor, so a check firing far above its floor (the map check
does, because its error field is spatially correlated) is visible rather than
assumed away.

**Per-arm check sets.** An arm may only run a check whose reference it already
pays for. Arms 4 and 4d run all four. Arm 5c is billed for `C1`, `C2` and `C4`,
and the neighbour columns of `N` are the `C3` reports carried over Xn, so it
runs `{serving reciprocity, map, rate}` and charges five compute units per
decision instead of six. The restriction lives in `wes.checks.ARM_CHECKS` and
applies only to a job that leaves `checks.enabled` at its default, so an
explicit check set still addresses a single check on any arm and the per-check
decomposition diagnostics are unaffected.

**The peer reference.** The map and rate checks test the serving cell and the
strongest other cell each of two channels names. The second of those is the
*peer*: `N` for an arm that votes `N`, and the radio map `C4` for an arm that
does not, which `wes.checks.peer_reference` decides. Together with forming a
check's difference only when that check is enabled, this is what keeps an arm
without Xn from touching `N` even as an index. The effect is measurable: after
both changes every metric of arm 5c is identical whether the attacker owns none
of the peer reports or all of them, and the run table says so cell by cell.

## The attacker

A transport-path adversary (a relay or false base station on the UE's path, or a
compromised transport link) owns the `C1` reports of a fixed 20 % of UEs, and
with probability `ρ` also the neighbour reports behind `N` for those UEs. It
never touches the serving gNB's own measurement or the radio map. The trap cell
is the most loaded cell a `+15 dB` falsification could reach (the same set at
every falsification size, so the `Δ = 0` null controls the same population), and
it is **sticky**, kept while it stays feasible. The applied offset can rise over
a **ramp** of 10 or 20 slots instead of stepping, which is how the rate check is
evaded. In `pingpong` mode the sign is reversed and any handover away from the
serving cell counts as a success.

Success is counted as **attack-attributable**: a targeted UE-slot scores only
when the adjudicated decision matches the attacker's intent *and* the base rule
on the true channels would not have taken it anyway.

## Install

Requires Python >= 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Dependencies: numpy, pandas, matplotlib, omegaconf (plus pytest and ruff for
development). No GPU.

## Layout

```
wes/            simulation package (world, radio, channels, checks, executors,
                adjudicators, attacker, engine, metrics)
conf/           base configuration and the six sweep definitions
run.py          command-line runner: expands a sweep, writes outputs/<stamp>_<tag>/
analyze.py      summary.md, the gate table and the figures from one runs.csv
stats.py        paired intervals, the gate setting and the shared column names
tables.py       the report tables
figures.py      the simulator's own figures
figstyle.py     shared figure style
DESIGN.md       the model specification
PROTOCOL.md     hypotheses, gates and readings fixed before each run
tests/          test suite, with the arm baselines it replays in tests/data/
data/           the frozen run tables backing the article, plus SHA256SUMS
paper_figs/     the article's figures, table and recompute script, from data/
```

## Running one configuration

Every command writes `outputs/<YYYYmmdd_HHMMSS>_<tag>/` with the resolved
`config.yaml`, an `env.json` record of the environment, and `runs.csv`.

```bash
# Two arms at the gate setting, two seeds: full attacker reach, Δ = 10 dB,
# σ_map = 2 dB, trap mode. Four runs, about a second.
uv run python run.py --arms single,obs_dhr_phys --seeds 0-1 \
    --delta 10 --rho 1 --sigma-map 2 --mode trap --tag demo
```

Those four rows are bit-identical to the corresponding rows of `data/b2/runs.csv`.

`--arms all` runs the seven arms of the table above. `--delta`, `--rho`,
`--sigma-map`, `--mode`, `--ramp`, `--checks`, `--persist` and `--z` all take
comma-separated lists and are expanded into the cross product; `--workers` sets
the process count (default: all cores).

## Running the full sweep

```bash
uv run python run.py --sweep conf/sweeps/pilot_b2.yaml --tag pilot_b2
uv run python analyze.py outputs/<YYYYmmdd_HHMMSS>_pilot_b2
```

The sweep is 3 400 runs: six arms (every arm but the 2p diagnostic) ×
`σ_map ∈ {2, 4, 6}` × `Δ ∈ {0, 6, 10, 15}` × `ρ ∈ {0, 0.5, 1}` in trap mode,
plus ping-pong mode, the sticky ramp, the per-check decomposition and a
no-persistence variant, at ten seeds each. One run takes about 1.1 s on one
core, so the sweep is roughly one CPU-hour: **7 minutes on ten cores**.
`analyze.py` then writes `summary.md`, holding the gate table evaluated
literally, the null control, the `σ_map × ρ` grid, the harm and cost tables, the
per-check decomposition and the thresholds actually used, and the simulator's
own two figures, from `runs.csv` alone.

The earlier revisions are `conf/sweeps/pilot_b0.yaml` (920 runs) and
`conf/sweeps/pilot_b1.yaml` (2 640 runs, about 11 minutes on ten cores). They
were run against earlier versions of the model; `PROTOCOL.md` says what each one
tested and what it settled.

Three diagnostics are their own design points and take seconds to minutes:

```bash
uv run python run.py --sweep conf/sweeps/diag_param.yaml --tag diag_param
uv run python run.py --sweep conf/sweeps/diag_veto.yaml --tag diag_veto
uv run python run.py --sweep conf/sweeps/diag_pingpong.yaml --tag diag_pingpong
```

`diag_param` is 40 runs: arms `single` and `model_dhr_param` × `Δ ∈ {0, 10}` at
`ρ = 0`, `σ_map = 2 dB`, trap mode, on the same ten seeds. Its `single` rows are
bit-identical to the corresponding rows of `data/b2/runs.csv`, which is how the
run doubles as a check that the seventh arm was added without disturbing the
other six.

`diag_veto` is 520 runs of arm 5c alone over its whole grid, re-measured after
the arm was restricted to the checks it pays for and its peer reference moved
off `N`. Every arm-5c number the article quotes comes from this run.

`diag_pingpong` is 200 runs: the per-check decomposition of arm 4 in the
ping-pong attacker mode at both reaches, which the `b2` sweep did not run. Its
default rows at `ρ = 0` are bit-identical to the corresponding `b2` rows.

## Frozen data

Each directory holds the same four files: `runs.csv`, the `summary.md`
produced from it, the resolved `config.yaml` and the `env.json` of the machine
that produced it.

| directory | rows | what it is |
|---|---|---|
| `data/b2/` | 3 400 | the run the article reports |
| `data/diag_param/` | 40 | the parameter-diversity diagnostic, arm 2p against the single-channel arm |
| `data/diag_veto/` | 520 | arm 5c re-measured after it was restricted to the checks it pays for; these rows supersede the arm's rows in `data/b2/`, which were measured while it still ran a check whose reference travels over Xn |
| `data/diag_pingpong/` | 200 | the per-check decomposition of arm 4 in the ping-pong attacker mode, at both reaches |
| `data/b1/` | 2 640 | the earlier confirmatory run, kept because `PROTOCOL.md` reports its gate table; it was run against an earlier observation model and the article quotes no number from it |

Verify all five with:

```bash
cd data && shasum -a 256 -c SHA256SUMS      # or: sha256sum -c SHA256SUMS
```

`uv run python analyze.py data/b2` and the same command on `data/diag_param`,
`data/diag_veto` and `data/diag_pingpong` rebuild each `summary.md` from its
`runs.csv` and write the simulator's own two figures beside it. The three
diagnostic summaries are reproduced byte for byte. The `b2` summary is
reproduced byte for byte except that every arm-indexed table gains an empty row
for arm 2p, which the `b2` sweep did not run: the shipped file is the one that
run produced, before the seventh arm existed. `data/b1` predates the `σ_map`
and persistence columns, so the current `analyze.py` cannot read it; its
`summary.md` is kept as the run produced it.

A caveat on the two single-arm summaries. Their gate table reads `n/a`
throughout and prints `FAIL`, because every gate compares arms 1, 3 and 4 and
those sweeps carry one arm each. No gate is evaluated from them; their per-arm
tables are what they are for.

## Article figures and numbers

```bash
uv run python paper_figs/make_figs.py
uv run python paper_figs/paper_numbers.py
```

The first reads `data/b2/runs.csv`, the `model_dhr_param` rows of
`data/diag_param/runs.csv` for the parameter-diversity row of the table and the
`cheap_phys` rows of `data/diag_veto/runs.csv` for the map-veto arm, and writes
`paper_figs/fig4.pdf`, `fig4.png`, `fig5.pdf`, `fig5.png` and `table1.tex`. The file names are those the manuscript source includes: `fig4` is Fig. 3 of the article and `fig5` is Fig. 4.

**Fig. 3** is three panels across the double column. (a) and (b) plot
attack-attributable success per targeted slot against attacker reach at
`Δ = 10 dB`, cut at `σ_map = 2` and `4 dB`, with each arm's `Δ = 0` null drawn
as a thin dotted rule in its own colour and a leader line tying the null label
to the band it names. (c) is the boundary of the anchored check: the
null-corrected ratio of the checked arm to the vote-only arm at full reach,
against the falsification magnitude, one curve per map error level, with each
level's calibrated map-check threshold marked on the axis, so where a curve
climbs to 1 can be read against the bound that explains it.

**Fig. 4** is two panels at single-column width. (a) is wrong handovers per
handover at `σ_map = 2 dB`, clean and under attack. (b) is missed handovers per
oracle handover with no attacker, drawn at all three map error levels, left to
right with growing marker size, so what refusing to act costs can be read
against the map error that drives it. Together: what the defence buys, beside
what it costs.

**Table I** is a seven-row LaTeX fragment, one row per arm, giving the voters,
the adjudication, whether the attacker can hold a voting majority at `ρ = 1`,
the Xn bytes per UE and second, the executors and checks per decision and the
false exclusion rate with no attacker. Every number in it is read from the run
tables; only the voter and adjudication wording is written by hand, and the
voter *count* behind each wording is checked against the run table's
`n_voting_channels`.

The script then reads every plotted value back out of the drawn artists, and
every data-derived table cell back out of the generated LaTeX, and prints it
beside an independent recomputation straight from the CSVs, so a mismatch
between what was computed and what was drawn shows up as a non-zero
discrepancy. It also confirms that the `Δ = 0` null does not vary with attacker
reach, which is the assumption behind reading each arm's null at `ρ = 0`, and
checks each figure's in-figure word count against its budget. It exits non-zero
if any of the three fails. Nothing in the figures is typed in by hand.

The second prints every number the article's case study quotes, each with the
design cell it came from, recomputed from `data/b2/runs.csv`,
`data/diag_param/runs.csv`, `data/diag_veto/runs.csv` and
`data/diag_pingpong/runs.csv` with the standard library alone.

## What backs what

| article item | source |
|---|---|
| Table I, rows for arms 1, 2′, 2p, 3, 4 and 4d (voters, adjudication, majority reachable, Xn bytes, executors and checks, false exclusion) | `data/b2/runs.csv`, plus `data/diag_param/runs.csv` for the parameter-diversity row; every number read from the run tables, not typed |
| Table I, the map-veto row (arm 5c) | `data/diag_veto/runs.csv` |
| Fig. 3(a)(b) (attack-attributable success against attacker reach, one panel per `σ_map`, with each arm's `Δ = 0` null) | `data/b2/runs.csv` at `Δ = 10`, `σ_map ∈ {2, 4}`, except the map-veto curve, which is `data/diag_veto/runs.csv` |
| Fig. 3(c) (checked over vote-only, null-corrected, against `Δ`, with each map-check threshold marked) | `data/b2/runs.csv` at `ρ = 1`, `Δ ∈ {6, 10, 15}`, `σ_map ∈ {2, 4, 6}`; the thresholds from `thr_map` |
| Fig. 4 (wrong handovers clean and under attack at `σ_map = 2`, missed handovers with no attacker at all three `σ_map`) | `data/b2/runs.csv`, except the map-veto markers, which are `data/diag_veto/runs.csv` |
| The gate table and the reading it triggers | `data/b2/summary.md`, reproducible with `analyze.py` |
| The parameter-diversity ratio on a shared input | `data/diag_param/runs.csv`, `attack_success_attr` at `p = 0.2`, `Δ = 10`, `ρ = 0`, less each arm's `Δ = 0` null |
| Every quoted number for the map-veto arm: its attack-attributable success and null, its null-corrected ratio, its fallback, harm, cost and false exclusion, and its ramp rows | `data/diag_veto/runs.csv`; the arm's rows in `data/b2/runs.csv` are retired and are not quoted anywhere |
| The ping-pong decomposition: which check detects the serving-cell deflation, at either reach | `data/diag_pingpong/runs.csv`, `detect_rate_actionable` at `Δ = 10`, `σ_map = 2`, per check set |
| Every other quoted number in the case study | `paper_figs/paper_numbers.py`, from `data/b2/runs.csv` |

## Seeds and determinism

Ten seeds, `seed ∈ {0..9}`, in every cell of every experiment. Five independent
generators are spawned per seed: `world` (shadowing and the radio-map error
field), `mobility`, `noise`, `attacker` and `policy`. The first four are
consumed entirely by precomputation, so for a given seed the trajectories, the
shadowing, the map error, the report noise and the attacker's target and reach
draws are identical across arms. Paired differences are therefore exact per
seed, and every interval is a paired 95 % Student-t interval over the ten seeds.

Two properties follow and are used rather than assumed. Because the standard
deviation of a correlated field only scales its innovations, the sweep over
`σ_map` leaves the underlying realisation unchanged. And because an attacker
with `Δ = 0` is inert, every metric at the null is bit-identical across `ρ`,
which `paper_figs/make_figs.py` measures on every run.

`run.py` pins `PYTHONHASHSEED=0` and single-threaded BLAS before NumPy is
imported and starts its workers with the `spawn` method, so the workers inherit
both. The model has no wall-clock dependence, so a re-run of any command
reproduces the frozen tables in `data/` exactly. `DESIGN.md` §7 has the details.

## Tests

```bash
uv run pytest -q
uv run ruff check .
```

107 tests. They cover the path-loss and shadowing model, the spatial
correlation of the map error, the channel noise levels and the masking that
keeps the serving gNB to its own link, the warm-up calibration and the rule that
no threshold may read a generating constant, each check including the symmetric
neighbour exclusion and the persistence rule, the per-arm check sets and the
peer reference, the dithered thresholds, the three decision families and the
three parameter variants, every adjudicator and the fallback, the attacker's
sticky trap cell, its ramp and its time-to-trigger-aware opportunity counter,
the attack-attributable metric against a brute-force counterfactual, the byte
and compute accounting, the missed-handover tracker, the paired statistics and
the gate table, and one full run pinned bit-exactly as a regression fixture.

Two of them are bit-identity tests. `tests/data/` holds a short run of all seven
arms captured before each of the two changes to arm 5c, and the tests replay
both: every other arm must reproduce its row exactly, and arm 5c may move only
in the way the design fixed in advance. A third runs the arm's checks over
forty real slots against an `N` slice replaced by noise and asserts that nothing
it computes moves, while arm 4's does.

## Licence

MIT. See `LICENSE`.
