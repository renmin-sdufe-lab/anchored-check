# WES: observation diversity for handover security, simulation design

A radio-access network hands a UE from one cell to another on the strength of a
measurement it did not make itself. The **UE measurement report** is the
cheapest and the most exposed of those inputs: an adversary on the reporting
path can inflate a neighbour cell by a few decibels and steer the UE wherever it
likes. This simulator asks what a decision layer can do about it when the
falsification is a *common cause*: every executor reads the same poisoned
number.

Two answers are compared. **Rule diversity** runs several handover rules on the
one report; **observation diversity** runs the same rule on several channels and
adjudicates. Because the second only helps while the attacker cannot reach a
voting majority, the model is deliberately built at `k = 3` voters of which the
attacker can reach two, and the question becomes what the adjudicator can still
do once the vote is lost. The answer turns on what each consistency check is
*anchored* on: a check whose reference the attacker can reach decays to nothing
as its reach grows; a check anchored on a measurement out of reach does not.

The document specifies the world, the radio model, the observation channels, the
handover rule, the executors and adjudicators, the physical-consistency checks
and their calibration, the attacker, the metrics, the sweep and the
reproducibility rules. Section numbers are referenced from the source comments.
`PROTOCOL.md` records the hypotheses, gates and predictions fixed before each
run.

---

## 1. Simulation model

### 1.1 Time and horizon

Discrete slots, one slot = 100 ms. Horizon `T = 3000` slots (5 minutes).
Metrics are collected for `t >= 300`; the first 300 slots are the warm-up. They
are excluded from every reported quantity and are the window on which the checks
of §4 are calibrated.

### 1.2 Cells, UEs and mobility

Seven omnidirectional cells at 3.5 GHz, all at the same transmit power
`P_tx = 46 dBm`. Cell 0 sits at the origin and cells 1–6 on a ring of radius
equal to the inter-site distance `isd = 500 m`, at 60° spacing.

Thirty UEs move by random direction on a square torus of half-side 750 m: each
UE draws a heading, a speed in `[1, 15] m/s` and a leg length in `[50, 300] m`,
walks the leg, then redraws all three; positions wrap at the cluster edge. The
whole trajectory set is drawn before the run starts.

Each UE is attached to exactly one cell. A cell's **load** is the number of UEs
it serves; every UE starts on its strongest cell.

### 1.3 Radio model

For every (UE, cell) pair and every slot:

**Path loss.** `PL(d) = 128.1 + 37.6 log10(d_km)`, with `d` floored at 10 m so
the logarithm stays finite.

**Shadowing.** A log-normal field of standard deviation `σ = 6 dB` with
exponential spatial correlation, generated along each trajectory as
`s(t) = a s(t-1) + sqrt(1 - a²) σ ε` with `a = exp(-dd / d_corr)`, `dd` the
distance the UE moved in the slot and `d_corr = 50 m`. Cells share a fraction
`radio.shadow_cell_corr` of the innovation; the configured default is `0.0`,
which is independence across cells. Because `σ` only scales the innovations,
two fields drawn from the same generator state at different `σ` are exact
multiples of one another, which is what keeps the sweep over the map error of
§2 a common random number.

**True RSRP.** `RSRP_true(u, c, t) = P_tx − PL − shadowing`, in dBm. Fast
fading is averaged out at the report level and appears as the per-report noise
of §2.

**Throughput proxy.** A neighbour cell interferes in proportion to its activity
factor `load_c / n_ue`; with thermal noise at `−95 dBm` the served rate is
`log2(1 + SINR)` divided by the serving cell's load. It is reported, never
gated: §6.2 states why.

**Outage.** A UE-slot is in outage when its true serving RSRP falls below
`radio.outage_rsrp_dbm = −110 dBm`.

---

## 2. Observation channels

Four channels are drawn, and the decision layer sees three of them. Every one
is a measurement some real node can make; none is a network-wide oracle.

| channel | what it is | noise | reachable |
|---|---|---|---|
| `C1` | the UE's own measurement report, covering **all** cells | `N(0, 1 dB)` | **yes** |
| `C2` | the serving gNB's uplink (SRS) estimate of the **serving link only**; every other column is missing | `N(0, 1.5 dB)` | no |
| `C3` | each neighbour gNB's uplink estimate of **its own link**, delivered over Xn | `N(0, 2 dB)` | with probability `ρ` |
| `C4` | the operator's radio map, evaluated at the position the serving gNB estimates by uplink positioning | `ε_map`, see below | no |

**The composite network channel `N`.** No single node holds a network-wide
view, but the network can assemble one: C2's serving column plus C3's neighbour
columns. `N` is that assembly, composed per slot after the attacker has acted,
and it is the second voter of §3.3. Its serving column is out of the attacker's
reach; its neighbour columns are not.

**The radio map `C4`.** `RSRP_true + ε_map`, where `ε_map` is a Gaussian field
carrying the shadowing's spatial correlation with standard deviation
`channels.sigma_map ∈ {2, 4, 6} dB`, independent of every measurement noise and
available from slot 0. Position error is absorbed into `σ_map`, which is the
design parameter the sweep of §7 moves: it sets how tight a bound the map can
put on a falsification, and therefore how large a falsification the map check of
§4 can see.

**Reachability.** A transport-path adversary (§5) writes to `C1` always and to
`N`'s neighbour columns with probability `ρ`. `C2`'s serving column and the
radio map are never falsified; that assumption is stated, not proven. The clean
channels are precomputed over the whole horizon, so they are common random
numbers across arms; poisoning is applied on top, per slot.

---

## 3. The handover decision

### 3.1 The A3 rule

One decision per UE per slot: keep the serving cell, or hand over to a target.
The base rule is 3GPP event A3: a target whose reading exceeds the serving
cell's by `rule.hysteresis = 3 dB` for `rule.ttt = 5` consecutive slots
triggers a handover to the strongest such cell. The time-to-trigger counters
are reset when the serving cell changes.

### 3.2 Decision families

An **executor** is one rule evaluated on one channel. Three rule families are
registered:

- `a3`, the base rule above;
- `load_aware`, A3 **and** the target's load below the serving cell's, else
  keep serving;
- `trend`, the channel's target-minus-serving difference has risen strictly
  over the last `ttt` slots and exceeds the hysteresis at the last one.

All three read `C1` in the rule-diversity arm, so a common cause reaches every
one of them. That is the point of that arm, not an oversight.

### 3.3 Arms: voters and adjudicators

Voting channels are `C1`, `N` and `C4` (`k = 3`). `C2` alone cannot evaluate A3,
since it sees one cell, so it does not vote; it anchors the serving-cell
reciprocity check, the warm-up calibration and the positioning behind `C4`.

| arm | key | voters | adjudication |
|---|---|---|---|
| 1 | `single` | `C1` | none: the lone executor's decision stands |
| 2′ | `model_dhr3` | three decision families on `C1` | weighted majority with confidence down-weighting |
| 3 | `obs_dhr` | `C1`, `N`, `C4` | strict majority (more than half the participating weight) |
| 4 | `obs_dhr_phys` | `C1`, `N`, `C4` | exclusion by the §4 checks, then a majority of the survivors |
| 4d | `obs_dhr_phys_dither` | `C1`, `N`, `C4` | as arm 4, thresholds dithered per UE-slot (§4.3) |
| 5c | `cheap_phys` | `C1`, `C4` (no Xn) | after its own three checks (§4.4), hand over only when both name the same target |
| 2p | `model_dhr_param` | three A3 executors on `C1` at `(hysteresis, ttt)` = (2 dB, 4), (3 dB, 5) and (4 dB, 6) | as arm 2′ |

A candidate wins a vote only with strictly more than half of the participating
weight; otherwise the verdict is *keep serving*. The confidence down-weighting
of arm 2′ multiplies a disagreeing executor's weight by `dhr.decay = 0.9` and
lets an agreeing one recover by `dhr.recover = 1.02`, clipped to
`[dhr.weight_floor, dhr.weight_cap] = [0.25, 1.0]`.

Each run records `majority_reachable`: whether the channels the attacker can
reach could carry a voting majority for that arm at that `ρ`. At `ρ > 0` the
reachable pair `{C1, N}` is two voters of three, so a plain vote can be lost;
arm 5c, whose second voter is unreachable, is never in that position.

Arm 2p is a diagnostic rather than a member of the main sweep. It answers, on
this apparatus and this metric, what three *parameter settings* of one rule buy
against a shared input, where arm 2′ answers the same question for three
*decision families*. Its three settings come from `rule.variant_hysteresis` and
`rule.variant_ttt`; it reads `C1` alone, so it costs one report and three
executor runs, exactly as arm 2′ does. It is run on its own design point
(`conf/sweeps/diag_param.yaml`, `PROTOCOL.md` row `diag`) and appears in no
other experiment; no other arm's code path changes when it is added, which the
diagnostic verifies by reproducing the single-channel rows of `data/b2` bit for
bit.

### 3.4 Fallback, and refusing to act

When exclusions leave fewer than `checks.min_channels = 2` voters, the decision
follows the surviving channel anchored on a measurement out of the attacker's
reach, the radio map `C4`, if it survives; otherwise the surviving channel;
otherwise keep serving. The share of UE-slots decided this way is reported as
`fallback_rate`.

Arm 5c sits on top of that rule with a stricter one of its own. It votes two
channels, so it hands over only when **both survive and name the same target**,
and keeps the serving cell whenever they disagree or either has been excluded
from the vote. Losing one voter also puts it below `min_channels`, so the
fallback above then decides: with `C1` excluded and `C4` surviving, the arm
follows the radio map alone. That pair of rules is where its defence comes from
and what it costs: under attack a large share of targeted UE-slots ends in a
refusal to act, counted in `fallback_rate` and paid for in missed handovers.

Refusing to act is not free, and it is made visible. An **oracle** executor runs
the base A3 rule on the *true* RSRP against the arm's own serving assignment. It
never votes and is never billed. It supplies the counterfactual that §6.1
subtracts, the reference the harm metrics of §6.2 compare against, and the
recommendation whose non-execution counts as a **missed handover**. Because the
oracle keeps recommending the same handover for as long as the condition holds,
each recommendation is opened once and closed once: by a matching handover
within `ttt` slots, by the oracle changing its mind, or by the deadline passing.

---

## 4. Physical-consistency checks

### 4.1 The four checks

Arms 4, 4d and 5c exclude a channel from the vote when it fails a consistency
check. Each check compares `C1` against a reference and excludes on the
threshold of §4.2. Arms 4 and 4d run all four; arm 5c runs the three whose
references it pays for, which §4.4 sets out.

| check | comparison | cells tested | excludes |
|---|---|---|---|
| serving reciprocity | `abs(C1[s] − C2[s])` | the serving cell | `C1` |
| neighbour reciprocity | `abs(C1[c] − N[c])` | the strongest other cell `C1` names and the one the peer channel names | **both** `C1` and `N` |
| map consistency | `abs(C1[c] − C4[c])` | serving cell and both of the above | `C1` |
| rate consistency | `abs(C1[c](t) − C1[c](t−1))` | serving cell and both of the above | `C1` |

Serving reciprocity is anchored on `C2`, which the attacker cannot reach, so a
mismatch there is `C1`'s fault and `C1` alone is excluded. Neighbour
reciprocity has no trusted side: at `ρ = 1` the neighbour columns of `N` are
falsified together with `C1`, and a violation says only that the two disagree,
so the exclusion is symmetric. Map consistency is anchored on the radio map,
which is also out of reach, and its power is set by `σ_map`: the threshold is
about `3 sqrt(σ_C1² + σ_map²)`, so a falsification below that bound is invisible
to it. Rate consistency catches a *step* at any reach, and is evaded by a ramp
that stays below the bound, the boundary this study states rather than hides.

The three decision-relevant cells are the serving cell and the strongest other
cell each of `C1` and the peer channel names; when those coincide the count is
an upper bound. The peer channel is `N` for an arm that votes `N` and `C4` for
an arm that does not, which §4.4 explains.

### 4.2 Calibration on the warm-up

Every threshold is `z · σ̂_diff` with `z = checks.z = 3`, and every `σ̂_diff` is
the standard deviation of the compared difference **measured on the clean
warm-up window** of that run. No check reads a generating constant out of
`conf/base.yaml`; a test asserts it. Four differences are measured directly,
because they are exactly what the four checks compare:

| check | calibrated difference |
|---|---|
| serving reciprocity | `C1 − C2` |
| neighbour reciprocity | `C1 − C3` |
| map consistency | `C1 − C4` |
| rate consistency | `C1(t) − C1(t−1)` |

The per-channel standard deviations are recovered for the report from the three
pairwise variances (`σ_C1² = (V12 + V13 − V23) / 2` and so on, with
`σ_map² = Var(C1 − C4) − σ_C1²`), and every calibrated quantity is written to
`runs.csv`. The warm-up is assumed clean; the report says so. A numerical floor
`checks.sigma_floor = 0.05 dB` keeps a calibrated standard deviation positive.

### 4.3 Persistence, dithering and the analytic floor

**Persistence.** Every check carries the same rule: a violation excludes only
after `checks.persistence_slots = 3` consecutive slots. The variant with no
persistence is run and reported for arm 4.

**Dithering (arm 4d).** Instead of holding `z` at 3, arm 4d draws
`z ~ U[checks.dither_low, checks.dither_high] = U[2, 4]` per UE and per slot
from the low-order bits of the serving gNB's own `C2` reading, randomness the
serving gNB observes and a transport-path attacker does not. An xor-shift mix
decorrelates the draw from the RSRP magnitude. The intent is to reach
falsifications that sit just inside a fixed 3σ bound.

**Analytic floor.** Beside each check's *measured* false-exclusion rate the
analysis prints its analytic floor: under Gaussian differences a two-sided
`z`-test fires with probability `erfc(z/√2)`, a check running `tests` of them
fires with `1 − (1 − p)^tests` per slot, and the persistence rule raises that to
the power of the streak length. A measured rate far above its floor means the
compared difference is not the Gaussian the floor assumes, which is the case for
the map check, whose error field is spatially correlated.

### 4.4 Per-arm check sets and the peer reference

An arm may only run a check whose reference it already pays for. Arm 5c has no
Xn: `wes.engine.measured_channels` bills it for `C1`, `C2` and `C4`, and the
neighbour columns of `N` are the `C3` reports that travel over Xn. So arm 5c
runs `{serving reciprocity, map, rate}` and arms 4 and 4d run all four. The
restriction is in `wes.checks.ARM_CHECKS` and applies only to a job that leaves
`checks.enabled` at its default; an explicit check-set override always wins, so
the per-check decomposition diagnostics still address a single check on any arm.
Compute units follow the enabled checks, so arm 5c charges two executor runs
plus three checks, five units per decision rather than six. Its bytes are
unchanged.

Two subtler paths could still let an arm without Xn touch `N`, and both are
closed.

- **The peer reference.** The second non-serving cell the map and rate checks
  test is the strongest other cell a *peer* channel names.
  `wes.checks.peer_reference` returns `N` for an arm that votes `N` (arms 3, 4
  and 4d, unchanged) and the radio map `C4` for an arm that does not (arm 5c),
  so the veto arm chooses where to look with a channel it already pays for.
- **Disabled checks.** A check's difference is formed only when that check is
  enabled, so no difference against `N` is computed for the veto arm at all.
  A disabled check's streak counter was never read, so this changes no enabled
  check's verdict on any other arm or in any decomposition variant.

The result is an arm whose every metric is identical whether the attacker owns
none of the peer reports or all of them, which is what an arm with no Xn ought
to be. Choosing the second test cell from the map rather than from `N` is not
free: at `σ_map = 6 dB` the arm false-excludes a little more and declines a few
more legitimate handovers. The `σ_map` axis is reported beside every number, so
that cost is visible.

---

## 5. The attacker

### 5.1 Reach and targets

A transport-path adversary (a relay or false base station on the UE's path, or
a compromised transport link) falsifies the `C1` report of a fixed fraction
`attacker.p = 0.2` of UEs, drawn once per seed, and with probability
`attacker.rho` also owns the neighbour reports behind `N` for those UEs. It
never touches `C2`'s serving column or the radio map. The RAN controller and
the serving gNB are attested and out of scope. Because the mechanism is per UE,
`p` is not a free parameter and is not swept.

All draws come from the `attacker` stream and are precomputed over the horizon,
so the attacker realisation is a common random number across arms.

### 5.2 Trap cell: Δ-independent and sticky

In `trap` mode the attacker adds `+Δ` dB to a neighbour cell's reading to pull
the UE into congestion. The trap cell is the **most loaded** cell among those a
`+15 dB` falsification could trigger (`attacker.trap_reference_delta = 15`),
used for every `Δ` including `Δ = 0`, so the targeted population does not depend
on the falsification size and the null of §6.1 is a control for the same
population. The trap cell is **sticky**: it is kept while it stays feasible, so
the attacker does not abandon its own ramp every few slots.

The **actionable share**, the share of targeted slots in which the actual `Δ`
suffices, is reported beside every rate.

### 5.3 Ramp

The applied offset rises linearly from 0 to `Δ` over `attacker.ramp_slots`
slots (`1` is a step). The ramp is keyed on the UE and restarts only when the
trap cell changes, and both feasibility and opportunity are computed from the
**applied** magnitude, so a half-delivered ramp cannot claim a full-Δ
opportunity.

### 5.4 Modes

| mode | falsification | success |
|---|---|---|
| `trap` | `+Δ` on the trap cell | a handover to that specific cell |
| `pingpong` | `−Δ` on the serving cell | any handover away from the serving cell |

The two modes are not interchangeable, and §4's checks see them differently.
In `trap` mode the attacker inflates a neighbour and leaves the serving cell
alone, so serving reciprocity has nothing to compare and the defence rests on
the map check. In `pingpong` mode the attacker deflates the *serving* cell, and
serving reciprocity, whose reference `C2` is the serving gNB's own uplink
measurement and is unreachable at every `ρ`, is the check that fires. Both
modes are run with their own `Δ = 0` null and every detection figure names the
mode it was measured in; `conf/sweeps/diag_pingpong.yaml` decomposes the
`pingpong` mode check by check at both reaches, which the `b2` sweep did not do.

### 5.5 Attack opportunity

An **opportunity** is a targeted UE-slot in which the falsified report would
trigger the attacker's intended handover under the base rule *including* the
time-to-trigger. The instantaneous count, the A3 inequality without the TTT,
is kept beside it as a second column.

---

## 6. Metrics

One row per (arm, seed, `p`, `Δ`, `ρ`, `σ_map`, mode, ramp, check set,
persistence) in `runs.csv`, with means and paired 95 % Student-t intervals over
the seeds computed in the analysis.

### 6.1 Attack-attributable success and its null

The primary security metric is **attack-attributable success per targeted
slot**, `attack_success_attr`. A targeted UE-slot counts only when

1. the adjudicated decision matches the attacker's intent, **and**
2. the base rule on the *true* channels would not have taken the same decision.

Without clause 2 the metric scores handovers the network would have made anyway;
with it, the metric is monotone in `Δ`. The per-opportunity rate,
`attack_success_opp`, is reported beside it with both denominators of §5.5, and
the raw (non-attributable) rate is kept as `attack_success`.

**The null.** Every block of the sweep carries a `Δ = 0` control on the same
code path, same seeds and same targeted population: the attacker is present and
falsifies nothing. Ratios against the single-channel arm are taken on
`value − the arm's own null`, with a paired interval, and any arm whose attacked
value sits at or below its null is reported as such rather than given a ratio.

### 6.2 Harm

Security numbers alone do not say whether a defence is worth deploying, so the
user-visible cost is reported at `Δ = 0` (what the defence costs when nobody is
attacking) and under attack (what it buys).

| metric | definition |
|---|---|
| `wrong_handover_per_ho`, `pingpong_per_ho` | handovers into a cell that is not better by the hysteresis, and returns within `metrics.pingpong_window = 20` slots, per executed handover (primary) |
| `wrong_handover_rate`, `pingpong_rate`, `handover_rate` | the same counts per UE-slot |
| `missed_handover_rate`, `missed_handover_per_ue_slot` | oracle recommendations the arm does not execute, per oracle event and per UE-slot |
| `rsrp_deficit` | mean true RSRP of the oracle's serving choice minus that of the arm's, in dB |
| `outage_share` | share of scored UE-slots below `radio.outage_rsrp_dbm` |
| `wrong_cell_share` | share of scored UE-slots served by a cell other than the oracle's choice |
| `throughput` | the §1.3 proxy |

The throughput proxy is reported and is never cited as evidence that a defence
has no cost: it moves by well under a percent under an attack that corrupts most
handovers, because it is a function of geometry and load rather than of handover
quality.

### 6.3 Detection and false exclusion

`detect_rate` is the share of targeted UE-slots in which **any** falsified
channel was excluded; `detect_rate_actionable` restricts it to opportunities.
`false_exclusion_rate` is the share of *clean* UE-slots with any reachable
channel excluded (primary), and `false_exclusion_rate_ch` the same per
channel-slot. `fe_serving_reciprocity` … `fe_rate` give the per-check
contribution on clean UEs, printed beside the analytic floors of §4.3. The
thresholds actually used and the calibrated standard deviations behind them are
written to every row.

### 6.4 Costs

Measurement signalling is charged per UE-slot for every channel the arm has to
measure: an executor voting on `N` measures `C2` and `C3`; a checking
adjudicator measures `C2` and `C4` whether or not an executor votes on them.

| channel | bytes per UE-slot |
|---|---|
| `C1` | 40 (one report, all cells) |
| `C2` | 20, internal to the serving gNB |
| `C3` | 60 **per neighbour report** actually used to build `N` |
| `C4` | 0, the radio map costs no signalling |

`bytes_per_ue_s` is the total; `bytes_ota_per_ue_s` excludes `C2` and is the
over-the-air figure the article compares arms on. Compute is
`cost.compute_executor = 1` unit per executor run plus `cost.compute_check = 1`
unit per enabled check, reported as `compute_per_decision`. Costs are reported,
never gated.

---

## 7. Design, seeds and common random numbers

The sweep is `conf/sweeps/pilot_b2.yaml`: six arms × `σ_map ∈ {2, 4, 6}` ×
`Δ ∈ {0, 6, 10, 15}` × `ρ ∈ {0, 0.5, 1}` in trap mode (2 160 runs); ping-pong
mode at `ρ = 0` for every arm and `σ_map` (720); the sticky ramp at
`ramp ∈ {10, 20}`, `Δ = 10`, `ρ = 1`, `σ_map ∈ {2, 4}` for arms 1, 3 and 4
(120); the per-check decomposition for arm 4 (320); and the no-persistence
variant of arm 4 (80). 3 400 runs, ten seeds each.

Three diagnostics are separate design points rather than blocks of that sweep.
Each runs on the same ten seeds and the same common random numbers.

- `conf/sweeps/diag_param.yaml`, the parameter-diversity diagnostic of §3.3:
  arms `single` and `model_dhr_param` × `Δ ∈ {0, 10}` at `ρ = 0`,
  `σ_map = 2 dB` in trap mode. 40 runs, about three seconds.
- `conf/sweeps/diag_veto.yaml`, arm 5c over its whole grid after it was given
  its own check set and its own peer reference (§4.4): `Δ ∈ {0, 6, 10, 15}` ×
  `ρ ∈ {0, 0.5, 1}` × `σ_map ∈ {2, 4, 6}` in trap mode (360), the ping-pong
  block at `ρ = 0` (120) and the sticky ramp at `Δ = 10`, `ρ = 1` (40).
  520 runs. Every arm-5c number the article quotes comes from this run; the
  arm's rows in the `b2` sweep ran a check it is not billed for and are retired.
- `conf/sweeps/diag_pingpong.yaml`, the per-check decomposition of arm 4 in the
  ping-pong mode (§5.4), which the `b2` sweep ran in the trap mode only:
  `Δ ∈ {0, 10}` × `ρ ∈ {0, 1}` at `σ_map = 2 dB` over the five check sets.
  200 runs, of which the default rows at `ρ = 0` reproduce the corresponding
  `b2` rows bit for bit.

Five independent generators are spawned from each seed: `world` (shadowing and
the map error field), `mobility`, `noise` (report noise), `attacker` (targets
and reach draws) and `policy`. The first four are consumed entirely by
precomputation, so for a given seed the trajectories, the shadowing, the map
error, the report noise and the attacker's draws are **identical across arms**;
`policy` is spawned and reserved. Paired differences are therefore computed per
seed and the pairing is exact.

Two consequences are used throughout. Because `σ` only scales the innovations
of a correlated field (§1.3), the sweep over `σ_map` keeps the same underlying
realisation. And because an attacker with `Δ = 0` is inert, every metric at the
null is bit-identical across `ρ`; the figures read the null at `ρ = 0` and the
figure cross-check measures that invariance rather than assuming it.

---

## 8. Outputs and reproducibility

Every run writes `outputs/<YYYYmmdd_HHMMSS>_<tag>/` containing:

- `config.yaml`, the fully resolved configuration plus the expanded sweep;
- `env.json`, the interpreter version, platform, package versions, commit hash,
  `PYTHONHASHSEED`, the command line, the job count and the wall time;
- `runs.csv`, one row per design point and seed, with every metric of §6;
- `summary.md` and the figures, produced by `analyze.py` from `runs.csv` alone.

Reproducibility rules: seeds are fixed as in §7; `run.py` pins
`PYTHONHASHSEED=0` and single-threaded BLAS before NumPy is imported, and the
worker pool uses the `spawn` start method so the workers inherit both; the model
contains no wall-clock dependence; and no number in any table or figure is
entered by hand, since everything is derived from `runs.csv`. One run of 3 000 slots
over 7 cells and 30 UEs takes about one second on one core.

---

## 9. Implementation requirements

- Python >= 3.11, a `uv` project; dependencies numpy, pandas, matplotlib,
  omegaconf; pytest and ruff for development. No GPU.
- Module layout: `wes/config.py` (frozen dataclasses, OmegaConf loader),
  `wes/world.py` (streams, layout, mobility, correlated fields), `wes/radio.py`,
  `wes/channels.py`, `wes/calibration.py`, `wes/checks.py`, `wes/executors.py`,
  `wes/adjudicate.py`, `wes/attacker.py`, `wes/decisions.py`, `wes/metrics.py`,
  `wes/engine.py`, then `run.py`, `analyze.py`, `stats.py`, `tables.py`,
  `figures.py`, `figstyle.py`.
- Executors, adjudicators and attackers are registered by name, so an arm is
  nothing but the objects handed to the one engine loop; no arm has its own
  code path.
- Style: type hints throughout, a module-level `logger`, no `print` in library
  code, no mutable defaults, no global mutable state, specific exceptions,
  docstrings on public functions, files of 200–400 lines, `ruff check` clean.
- Performance: one run finishes well inside 20 s on a laptop CPU, which a test
  asserts; `run.py` parallelises over jobs with `multiprocessing`.
