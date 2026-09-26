# WES majority-reach run b2: analysis summary

Runs: 200 runs; mean 1.50 s, max 1.96 s per run (DESIGN 8 budget 20 s); 299 s CPU in total

Gate setting: {'p': 0.2, 'delta': 10.0, 'rho': 1.0, 'sigma_map': 2.0, 'mode': 'trap', 'check_set': 'default', 'z': 3.0, 'ramp_slots': 1, 'persistence_slots': 3}


### Gate-2 table (PROTOCOL.md, evaluated literally on the attack-attributable rate per targeted slot)

| gate | criterion | numbers | verdict |
|---|---|---|---|
| **G2-a** | ρ = 1, Δ = 10, every σ_map: arm 3 ≥ 0.5 × arm 1 on the primary metric | σ_map = 2: arm 1 = n/a, arm 3 = n/a (nan × arm 1, < 0.5×); paired arm3 − 0.5·arm1 = n/a; null-corrected n/a; σ_map = 4: arm 1 = n/a, arm 3 = n/a (nan × arm 1, < 0.5×); paired arm3 − 0.5·arm1 = n/a; null-corrected n/a; σ_map = 6: arm 1 = n/a, arm 3 = n/a (nan × arm 1, < 0.5×); paired arm3 − 0.5·arm1 = n/a; null-corrected n/a | **FAIL** |
| **G2-b** | ρ = 1, Δ = 10, σ_map = 2, step: arm 4 ≤ 0.2 × arm 3 with the CI excluding the boundary **and** false exclusion ≤ 0.05 | arm 3 = n/a; arm 4 = n/a (nan × arm 3); paired arm4 − 0.2·arm3 = n/a (CI wholly below 0: no); null-corrected n/a; false exclusion = n/a (≤ 0.05: no). σ_map = 4 (reported): arm 3 = n/a, arm 4 = n/a (nan × arm 3); σ_map = 6 (reported): arm 3 = n/a, arm 4 = n/a (nan × arm 3) | **FAIL** |
| **G2-c** | at Δ = 0, arms 4 and 5c against arm 1: `rsrp_deficit` not worse by more than 0.5 dB and `outage_share` not worse by more than 10 % relative | rsrp_deficit arm1 = n/a, obs_dhr_phys = n/a, paired n/a (≤ +0.5 dB: no); outage_share arm1 = n/a, obs_dhr_phys = n/a, paired n/a (≤ +10 % relative: no); missed handovers / UE-slot obs_dhr_phys = n/a at Δ = 0 and n/a under attack (reported, PROTOCOL.md sets no threshold); rsrp_deficit arm1 = n/a, cheap_phys = n/a, paired n/a (≤ +0.5 dB: no); outage_share arm1 = n/a, cheap_phys = n/a, paired n/a (≤ +10 % relative: no); missed handovers / UE-slot cheap_phys = n/a at Δ = 0 and n/a under attack (reported, PROTOCOL.md sets no threshold) | **FAIL** |


**G2-a fails** → in the specification's own words: *"G2-a fails → apparatus defect, found before anything is written."*


### Δ = 0 null control (attacker present, falsification zero; σ_map = 2)

| arm | attack-attributable success / targeted slot | attack-attributable success / opportunity | actionable share (with TTT) | false exclusion (clean UE-slots) | RSRP deficit (dB) | outage share | throughput proxy |
|---|---|---|---|---|---|---|---|
| 1 single (C1) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 2' model DHR (3 families on C1) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4 obs DHR + physics | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4d obs DHR + dithered physics | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |


### Headline metrics at the gate setting (p = 0.2, Δ = 10 dB, ρ = 1, σ_map = 2 dB, trap; mean ± 95 % CI)

| arm | attack-attributable success / targeted slot | attack-attributable success / opportunity | raw success / targeted slot | actionable share (with TTT) | false exclusion (clean UE-slots) | throughput proxy |
|---|---|---|---|---|---|---|
| 1 single (C1) | n/a | n/a | n/a | n/a | n/a | n/a |
| 2' model DHR (3 families on C1) | n/a | n/a | n/a | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | n/a | n/a | n/a | n/a | n/a | n/a |
| 4 obs DHR + physics | n/a | n/a | n/a | n/a | n/a | n/a |
| 4d obs DHR + dithered physics | n/a | n/a | n/a | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | n/a | n/a | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a | n/a | n/a | n/a |


### attack-attributable success / targeted slot over σ_map × ρ (Δ = 10 dB, trap)

| arm | σ_map | Δ = 0 null |
|---|---|---|


### attack-attributable success / targeted slot against Δ (ρ = 1, trap)

| arm | σ_map |
|---|---|


### Primary and secondary attack metrics (σ_map = 2, Δ = 10, trap)

| arm | ρ | attack-attributable success / targeted slot | attack-attributable success / opportunity | attack-attributable success / instant opportunity |
|---|---|---|---|---|


### Harm and quality of service: Δ = 0 (cost of the defence) and Δ = 10, ρ = 1 (its value); σ_map = 2

| arm | Δ | RSRP deficit (dB) | outage share | wrong-cell share | wrong handovers / handover | ping-pongs / handover | missed handovers / UE-slot | missed handovers / oracle handover | handovers / UE-slot | trusted-channel fallback rate | throughput proxy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 single (C1) | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 1 single (C1) | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 2' model DHR (3 families on C1) | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 2' model DHR (3 families on C1) | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4 obs DHR + physics | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4 obs DHR + physics | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4d obs DHR + dithered physics | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4d obs DHR + dithered physics | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |


### Paired harm differences against arm 1 (`*` marks a CI excluding zero)

| arm | Δ | RSRP deficit (dB) | outage share | missed handovers / UE-slot |
|---|---|---|---|---|
| 2' model DHR (3 families on C1) | 0 (null) | n/a | n/a | n/a |
| 2' model DHR (3 families on C1) | 10 | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | 0 (null) | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | 10 | n/a | n/a | n/a |
| 4 obs DHR + physics | 0 (null) | n/a | n/a | n/a |
| 4 obs DHR + physics | 10 | n/a | n/a | n/a |
| 4d obs DHR + dithered physics | 0 (null) | n/a | n/a | n/a |
| 4d obs DHR + dithered physics | 10 | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | 0 (null) | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | 10 | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 0 (null) | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 10 | n/a | n/a | n/a |


### Apparatus diagnostics at the gate setting

| arm | majority reachable | actionable share (with TTT) | actionable share (instantaneous) | falsified-channel exclusion on actionable slots | false exclusion (clean UE-slots) | voting channels |
|---|---|---|---|---|---|---|
| 1 single (C1) | n/a | n/a | n/a | n/a | n/a | n/a |
| 2' model DHR (3 families on C1) | n/a | n/a | n/a | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | n/a | n/a | n/a | n/a | n/a | n/a |
| 4 obs DHR + physics | n/a | n/a | n/a | n/a | n/a | n/a |
| 4d obs DHR + dithered physics | n/a | n/a | n/a | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | n/a | n/a | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a | n/a | n/a | n/a |



### Both attacker modes with the Δ = 0 null (σ_map = 2, ρ = 0; ping-pong is only run at ρ = 0)

| arm | attack-attributable success / targeted slot (pingpong) | Δ = 0 null (pingpong) | wrong HO / handover (pingpong) |
|---|---|---|---|
| 1 single (C1) | n/a | n/a | n/a |
| 2' model DHR (3 families on C1) | n/a | n/a | n/a |
| 3 obs DHR (C1, N, C4) | n/a | n/a | n/a |
| 4 obs DHR + physics | 0.0006 ± 0.0001 | 0.0005 ± 0.0001 | 0.0388 ± 0.0086 |
| 4d obs DHR + dithered physics | n/a | n/a | n/a |
| 5c cheap physics (C1, C4) | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a |



### Cost per arm at the gate setting (DESIGN 6: reported, not gated)

| arm | measurement bytes (B/UE/s) | over-the-air bytes (B/UE/s) | compute units/decision | OTA bytes / arm 1 | compute / arm 1 |
|---|---|---|---|---|---|
| 1 single (C1) | nan | nan | nan | nanx | nanx |
| 2' model DHR (3 families on C1) | nan | nan | nan | nanx | nanx |
| 3 obs DHR (C1, N, C4) | nan | nan | nan | nanx | nanx |
| 4 obs DHR + physics | nan | nan | nan | nanx | nanx |
| 4d obs DHR + dithered physics | nan | nan | nan | nanx | nanx |
| 5c cheap physics (C1, C4) | nan | nan | nan | nanx | nanx |
| 2p param DHR (3 A3 variants on C1) | nan | nan | nan | nanx | nanx |


### Paired differences on the null-corrected primary metric (Δ = 10; `*` marks a 95 % CI excluding zero)

| pair | σ_map | ρ | paired difference |
|---|---|---|---|
| model_dhr3 − single | 2 | 0 | n/a |
| obs_dhr − single | 2 | 0 | n/a |
| obs_dhr_phys − obs_dhr | 2 | 0 | n/a |
| obs_dhr_phys_dither − obs_dhr_phys | 2 | 0 | n/a |
| cheap_phys − obs_dhr_phys | 2 | 0 | n/a |
| model_dhr3 − single | 2 | 1 | n/a |
| obs_dhr − single | 2 | 1 | n/a |
| obs_dhr_phys − obs_dhr | 2 | 1 | n/a |
| obs_dhr_phys_dither − obs_dhr_phys | 2 | 1 | n/a |
| cheap_phys − obs_dhr_phys | 2 | 1 | n/a |
| model_dhr3 − single | 4 | 0 | n/a |
| obs_dhr − single | 4 | 0 | n/a |
| obs_dhr_phys − obs_dhr | 4 | 0 | n/a |
| obs_dhr_phys_dither − obs_dhr_phys | 4 | 0 | n/a |
| cheap_phys − obs_dhr_phys | 4 | 0 | n/a |
| model_dhr3 − single | 4 | 1 | n/a |
| obs_dhr − single | 4 | 1 | n/a |
| obs_dhr_phys − obs_dhr | 4 | 1 | n/a |
| obs_dhr_phys_dither − obs_dhr_phys | 4 | 1 | n/a |
| cheap_phys − obs_dhr_phys | 4 | 1 | n/a |
| model_dhr3 − single | 6 | 0 | n/a |
| obs_dhr − single | 6 | 0 | n/a |
| obs_dhr_phys − obs_dhr | 6 | 0 | n/a |
| obs_dhr_phys_dither − obs_dhr_phys | 6 | 0 | n/a |
| cheap_phys − obs_dhr_phys | 6 | 0 | n/a |
| model_dhr3 − single | 6 | 1 | n/a |
| obs_dhr − single | 6 | 1 | n/a |
| obs_dhr_phys − obs_dhr | 6 | 1 | n/a |
| obs_dhr_phys_dither − obs_dhr_phys | 6 | 1 | n/a |
| cheap_phys − obs_dhr_phys | 6 | 1 | n/a |


### Check decomposition, arm 4 (diagnostic; **not** a gate result)

| check set | persistence | σ_map | ρ | Δ = 0 null | Δ = 10 | false exclusion | detection on actionable slots |
|---|---|---|---|---|---|---|---|


### Thresholds actually used (z = 3 × a standard deviation calibrated on the clean warm-up), with their spread across the 10 seeds

| σ_map | check | mean (dB) | min (dB) | max (dB) | sd (dB) |
|---|---|---|---|---|---|
