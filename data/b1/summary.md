# WES confirmatory run b1: analysis summary

Runs: 2640 runs; mean 2.17 s, max 5.22 s per run (DESIGN 8 budget 20 s); 5730 s CPU in total

Thresholds actually used (z = 3, derived, never fitted): thr_recip_serving_c1 = 5.408 dB; thr_recip_neighbour_c1 = 6.708 dB; thr_recip_serving_c3 = 7.500 dB; thr_temporal_c1 = 6.312 dB; thr_self_c1 = 5.881 dB; sigma_c4_hat = 1.851 dB

Gate setting: {'p': 0.2, 'delta': 10.0, 'rho': 0.0, 'mode': 'trap', 'check_set': 'default', 'z': 3.0, 'ramp_slots': 1}


### Gate-1 table (PROTOCOL.md, row b1, evaluated literally on the attack-attributable rate per opportunity)

| gate | criterion | numbers | verdict |
|---|---|---|---|
| **G1-a** | arm 2 attack-attributable success per opportunity ≥ 0.8 × arm 1 | arm 1 = 0.1215 ± 0.0012; arm 2 = 0.1218 ± 0.0012; ratio = 1.003; paired arm2 − arm1 = 0.0003 ± 0.0004 | **PASS** |
| **G1-b** | arm 4 ≤ 0.2 × arm 1 with the paired CI excluding the boundary **and** false exclusion ≤ 0.05 | arm 1 = 0.1215 ± 0.0012; arm 4 = 0.0005 ± 0.0002 (0.0043 × arm 1); paired arm4 − 0.2·arm1 = -0.0238 ± 0.0003 (CI wholly below 0: yes); false exclusion = 0.0108 ± 0.0003 (≤ 0.05: yes); per channel-slot = 0.0066 ± 0.0002 | **PASS** |
| **G1-c** | arm 4 ≤ arm 3 ≤ arm 2 **and** paired arm3 − arm4 CI excludes 0 | arm 2 = 0.1218 ± 0.0012; arm 3 = 0.0008 ± 0.0002; arm 4 = 0.0005 ± 0.0002; ordered: yes; paired arm3 − arm4 = 0.0003 ± 0.0002 (excludes 0: yes) | **PASS** |
| **G1-d** | QoS gate (PROTOCOL.md, row b1) | throughput arm4 − 0.98·arm1 = 0.0268 ± 0.0042 (CI wholly above 0: yes); wrong handovers arm4/arm1 = 0.005 (≤ 1.1: yes; arm4 = 0.0000 ± 0.0000, arm1 = 0.0095 ± 0.0008); ping-pongs arm4/arm1 = 0.010 (≤ 1.1: yes; arm4 = 0.0001 ± 0.0000, arm1 = 0.0110 ± 0.0010); fallback share = 0.0000 ± 0.0000 (≤ 0.05: yes); missed handovers arm4 = 0.1682 ± 0.0106 vs arm1 = 0.1842 ± 0.0255 (reported, the protocol sets no threshold) | **PASS** |
| **G1-e** | at ρ = 1: arm 4 ≤ 0.5 × arm 3 **and** arm 4 ≤ arm 2 (Δ = 6 difference reported, not gated) | ρ = 1: arm 2 = 0.1218 ± 0.0012, arm 3 = 0.0046 ± 0.0006, arm 4 = 0.0037 ± 0.0006; arm4 ≤ 0.5·arm3: no (paired arm4 − 0.5·arm3 = 0.0014 ± 0.0003); arm4 ≤ arm2: yes. Δ = 6 boundary: arm 3 = 0.0018 ± 0.0004, arm 4 = 0.0016 ± 0.0004, paired arm4 − arm3 = -0.0001 ± 0.0002 | **FAIL** |


### Δ = 0 null control (DESIGN 6.1; attacker present, falsification zero)

| arm | attributable / opportunity | raw / targeted slot | actionable share | false exclusion | throughput |
|---|---|---|---|---|---|
| single | 0.0162 ± 0.0051 | 0.0029 ± 0.0003 | 0.0327 ± 0.0035 | 0.0000 ± 0.0000 | 1.3584 ± 0.0404 |
| model_dhr | 0.0160 ± 0.0048 | 0.0029 ± 0.0003 | 0.0327 ± 0.0036 | 0.0000 ± 0.0000 | 1.3584 ± 0.0405 |
| obs_dhr | 0.0022 ± 0.0019 | 0.0025 ± 0.0003 | 0.0406 ± 0.0042 | 0.0000 ± 0.0000 | 1.3531 ± 0.0410 |
| obs_dhr_phys | 0.0024 ± 0.0020 | 0.0025 ± 0.0003 | 0.0405 ± 0.0043 | 0.0108 ± 0.0003 | 1.3524 ± 0.0406 |


### Headline metrics at the gate setting (p = 0.2, Δ = 10 dB, ρ = 0, trap; mean ± 95 % CI over seeds)

| arm | attack-attributable success / opportunity | attack-attributable success / targeted slot | raw success / targeted slot | actionable share of targeted slots | false exclusion (clean UE-slots) | throughput proxy |
|---|---|---|---|---|---|---|
| 1 single (C1) | 0.1215 ± 0.0012 | 0.0531 ± 0.0046 | 0.0609 ± 0.0053 | 0.4368 ± 0.0370 | 0.0000 ± 0.0000 | 1.3521 ± 0.0437 |
| 2 model DHR (C1 x3) | 0.1218 ± 0.0012 | 0.0532 ± 0.0045 | 0.0610 ± 0.0052 | 0.4368 ± 0.0371 | 0.0000 ± 0.0000 | 1.3521 ± 0.0437 |
| 3 observation DHR (C1-C4) | 0.0008 ± 0.0002 | 0.0003 ± 0.0001 | 0.0018 ± 0.0002 | 0.4276 ± 0.0367 | 0.0000 ± 0.0000 | 1.3532 ± 0.0410 |
| 4 obs DHR + physics | 0.0005 ± 0.0002 | 0.0002 ± 0.0001 | 0.0016 ± 0.0003 | 0.4280 ± 0.0370 | 0.0108 ± 0.0003 | 1.3519 ± 0.0406 |


### attack-attributable success / opportunity against Δ (p = 0.2, ρ = 0, trap)

| arm | Δ = 0 (null) | Δ = 6 dB | Δ = 10 dB | Δ = 15 dB |
|---|---|---|---|---|
| 1 single (C1) | 0.0162 ± 0.0051 | 0.1086 ± 0.0037 | 0.1215 ± 0.0012 | 0.1116 ± 0.0027 |
| 2 model DHR (C1 x3) | 0.0160 ± 0.0048 | 0.1085 ± 0.0038 | 0.1218 ± 0.0012 | 0.1117 ± 0.0028 |
| 3 observation DHR (C1-C4) | 0.0022 ± 0.0019 | 0.0018 ± 0.0004 | 0.0008 ± 0.0002 | 0.0003 ± 0.0001 |
| 4 obs DHR + physics | 0.0024 ± 0.0020 | 0.0016 ± 0.0004 | 0.0005 ± 0.0002 | 0.0002 ± 0.0001 |


### attack-attributable success / opportunity against ρ (p = 0.2, Δ = 10, trap)

| arm | Δ = 0 null | ρ = 0 | ρ = 0.5 | ρ = 1 |
|---|---|---|---|---|
| 1 single (C1) | 0.0162 ± 0.0051 | 0.1215 ± 0.0012 | 0.1215 ± 0.0012 | 0.1215 ± 0.0012 |
| 2 model DHR (C1 x3) | 0.0160 ± 0.0048 | 0.1218 ± 0.0012 | 0.1218 ± 0.0012 | 0.1218 ± 0.0012 |
| 3 observation DHR (C1-C4) | 0.0022 ± 0.0019 | 0.0008 ± 0.0002 | 0.0020 ± 0.0004 | 0.0046 ± 0.0006 |
| 4 obs DHR + physics | 0.0024 ± 0.0020 | 0.0005 ± 0.0002 | 0.0015 ± 0.0003 | 0.0037 ± 0.0006 |


### Quality of service (DESIGN 6.2) at the gate setting; Δ = 0 null in parentheses

| arm | throughput proxy | wrong handovers / UE-slot | ping-pongs / UE-slot | wrong handovers / handover | ping-pongs / handover | handovers / UE-slot | missed handovers / oracle handover | trusted-channel fallback rate |
|---|---|---|---|---|---|---|---|---|
| 1 single (C1) | 1.3521 ± 0.0437 (1.3584) | 0.0095 ± 0.0008 (0.0001) | 0.0110 ± 0.0010 (0.0002) | 0.5863 ± 0.0138 (0.0345) | 0.6789 ± 0.0188 (0.0445) | 0.0162 ± 0.0010 (0.0037) | 0.1842 ± 0.0255 (0.0732) | 0.0000 ± 0.0000 (0.0000) |
| 2 model DHR (C1 x3) | 1.3521 ± 0.0437 (1.3584) | 0.0095 ± 0.0008 (0.0001) | 0.0110 ± 0.0010 (0.0002) | 0.5869 ± 0.0133 (0.0344) | 0.6780 ± 0.0195 (0.0448) | 0.0162 ± 0.0010 (0.0037) | 0.1921 ± 0.0225 (0.0766) | 0.0000 ± 0.0000 (0.0000) |
| 3 observation DHR (C1-C4) | 1.3532 ± 0.0410 (1.3531) | 0.0000 ± 0.0000 (0.0000) | 0.0001 ± 0.0000 (0.0001) | 0.0119 ± 0.0061 (0.0087) | 0.0309 ± 0.0044 (0.0306) | 0.0032 ± 0.0002 (0.0032) | 0.1738 ± 0.0104 (0.1740) | 0.0000 ± 0.0000 (0.0000) |
| 4 obs DHR + physics | 1.3519 ± 0.0406 (1.3524) | 0.0000 ± 0.0000 (0.0000) | 0.0001 ± 0.0000 (0.0001) | 0.0146 ± 0.0049 (0.0086) | 0.0326 ± 0.0034 (0.0309) | 0.0032 ± 0.0002 (0.0032) | 0.1682 ± 0.0106 (0.1715) | 0.0000 ± 0.0000 (0.0000) |


### Apparatus diagnostics at the gate setting

| arm | actionable share of targeted slots | C1 exclusion on actionable slots | false exclusion (clean UE-slots) | false exclusion, reciprocity | false exclusion, temporal | false exclusion, self-history | voting channels |
|---|---|---|---|---|---|---|---|
| 1 single (C1) | 0.4368 ± 0.0370 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| 2 model DHR (C1 x3) | 0.4368 ± 0.0371 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 3.0000 ± 0.0000 |
| 3 observation DHR (C1-C4) | 0.4276 ± 0.0367 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 4.0000 ± 0.0000 |
| 4 obs DHR + physics | 0.4280 ± 0.0370 | 0.9754 ± 0.0034 | 0.0108 ± 0.0003 | 0.0057 ± 0.0001 | 0.0007 ± 0.0002 | 0.0007 ± 0.0002 | 3.8438 ± 0.0126 |


### attack-attributable success / opportunity over the p x Δ grid (ρ = 0, trap)

| arm | p=0.05, Δ=0 | p=0.05, Δ=6 | p=0.05, Δ=10 | p=0.05, Δ=15 | p=0.2, Δ=0 | p=0.2, Δ=6 | p=0.2, Δ=10 | p=0.2, Δ=15 | p=0.5, Δ=0 | p=0.5, Δ=6 | p=0.5, Δ=10 | p=0.5, Δ=15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 single (C1) | 0.0194 ± 0.0045 | 0.1098 ± 0.0081 | 0.1131 ± 0.0067 | 0.1086 ± 0.0031 | 0.0162 ± 0.0051 | 0.1086 ± 0.0037 | 0.1215 ± 0.0012 | 0.1116 ± 0.0027 | 0.0212 ± 0.0029 | 0.1087 ± 0.0017 | 0.1182 ± 0.0016 | 0.1066 ± 0.0013 |
| 2 model DHR (C1 x3) | 0.0194 ± 0.0045 | 0.1097 ± 0.0081 | 0.1132 ± 0.0067 | 0.1088 ± 0.0031 | 0.0160 ± 0.0048 | 0.1085 ± 0.0038 | 0.1218 ± 0.0012 | 0.1117 ± 0.0028 | 0.0207 ± 0.0023 | 0.1086 ± 0.0016 | 0.1182 ± 0.0016 | 0.1068 ± 0.0015 |
| 3 observation DHR (C1-C4) | 0.0023 ± 0.0017 | 0.0020 ± 0.0010 | 0.0009 ± 0.0004 | 0.0004 ± 0.0002 | 0.0022 ± 0.0019 | 0.0018 ± 0.0004 | 0.0008 ± 0.0002 | 0.0003 ± 0.0001 | 0.0025 ± 0.0013 | 0.0020 ± 0.0003 | 0.0008 ± 0.0002 | 0.0003 ± 0.0001 |
| 4 obs DHR + physics | 0.0023 ± 0.0017 | 0.0020 ± 0.0010 | 0.0009 ± 0.0004 | 0.0004 ± 0.0002 | 0.0024 ± 0.0020 | 0.0016 ± 0.0004 | 0.0005 ± 0.0002 | 0.0002 ± 0.0001 | 0.0026 ± 0.0012 | 0.0019 ± 0.0003 | 0.0006 ± 0.0001 | 0.0002 ± 0.0001 |


### Both attacker modes (p = 0.2, Δ = 10, ρ = 0)

| arm | attack-attributable success / opportunity (pingpong) | wrong handovers / handover (pingpong) | ping-pongs / handover (pingpong) | attack-attributable success / opportunity (trap) | wrong handovers / handover (trap) | ping-pongs / handover (trap) |
|---|---|---|---|---|---|---|
| 1 single (C1) | 0.1434 ± 0.0021 | 0.6186 ± 0.0167 | 0.7299 ± 0.0176 | 0.1215 ± 0.0012 | 0.5863 ± 0.0138 | 0.6789 ± 0.0188 |
| 2 model DHR (C1 x3) | 0.1428 ± 0.0023 | 0.6194 ± 0.0172 | 0.7306 ± 0.0178 | 0.1218 ± 0.0012 | 0.5869 ± 0.0133 | 0.6780 ± 0.0195 |
| 3 observation DHR (C1-C4) | 0.0013 ± 0.0002 | 0.0163 ± 0.0049 | 0.0322 ± 0.0046 | 0.0008 ± 0.0002 | 0.0119 ± 0.0061 | 0.0309 ± 0.0044 |
| 4 obs DHR + physics | 0.0014 ± 0.0003 | 0.0161 ± 0.0046 | 0.0324 ± 0.0044 | 0.0005 ± 0.0002 | 0.0146 ± 0.0049 | 0.0326 ± 0.0034 |


### Slow-ramp attacker (DESIGN 5.3; reported, not gated)

| arm | ρ | ramp = 1 slot(s) | ramp = 10 slot(s) | ramp = 20 slot(s) | C1 exclusion, step | C1 exclusion, slowest ramp |
|---|---|---|---|---|---|---|
| 1 single (C1) | 0 | 0.1215 ± 0.0012 | 0.0599 ± 0.0021 | 0.0355 ± 0.0013 | 0.000 | 0.000 |
| 1 single (C1) | 0.5 | 0.1215 ± 0.0012 | n/a | n/a | 0.000 | nan |
| 1 single (C1) | 1 | 0.1215 ± 0.0012 | 0.0599 ± 0.0021 | 0.0355 ± 0.0013 | 0.000 | 0.000 |
| 2 model DHR (C1 x3) | 0 | 0.1218 ± 0.0012 | 0.0601 ± 0.0020 | 0.0355 ± 0.0013 | 0.000 | 0.000 |
| 2 model DHR (C1 x3) | 0.5 | 0.1218 ± 0.0012 | n/a | n/a | 0.000 | nan |
| 2 model DHR (C1 x3) | 1 | 0.1218 ± 0.0012 | 0.0601 ± 0.0020 | 0.0355 ± 0.0013 | 0.000 | 0.000 |
| 3 observation DHR (C1-C4) | 0 | 0.0008 ± 0.0002 | 0.0008 ± 0.0002 | 0.0008 ± 0.0002 | 0.000 | 0.000 |
| 3 observation DHR (C1-C4) | 0.5 | 0.0020 ± 0.0004 | n/a | n/a | 0.000 | nan |
| 3 observation DHR (C1-C4) | 1 | 0.0046 ± 0.0006 | 0.0041 ± 0.0007 | 0.0037 ± 0.0006 | 0.000 | 0.000 |
| 4 obs DHR + physics | 0 | 0.0005 ± 0.0002 | 0.0005 ± 0.0002 | 0.0005 ± 0.0002 | 0.975 | 0.491 |
| 4 obs DHR + physics | 0.5 | 0.0015 ± 0.0003 | n/a | n/a | 0.906 | nan |
| 4 obs DHR + physics | 1 | 0.0037 ± 0.0006 | 0.0035 ± 0.0005 | 0.0033 ± 0.0005 | 0.838 | 0.376 |


### Knowing adaptive attacker (DESIGN 5; reported, not gated)

| arm | reachable channels are a voting majority | blind, ρ = 0 | blind, ρ = 0.5 | blind, ρ = 1 | knowing, ρ = 0 | knowing, ρ = 0.5 | knowing, ρ = 1 |
|---|---|---|---|---|---|---|---|
| 1 single (C1) | yes | 0.1215 ± 0.0012 | 0.1215 ± 0.0012 | 0.1215 ± 0.0012 | 0.1215 ± 0.0012 | 0.1215 ± 0.0012 | 0.1215 ± 0.0012 |
| 2 model DHR (C1 x3) | yes | 0.1218 ± 0.0012 | 0.1218 ± 0.0012 | 0.1218 ± 0.0012 | 0.1218 ± 0.0012 | 0.1218 ± 0.0012 | 0.1218 ± 0.0012 |
| 3 observation DHR (C1-C4) | no | 0.0008 ± 0.0002 | 0.0020 ± 0.0004 | 0.0046 ± 0.0006 | 0.0008 ± 0.0002 | 0.0020 ± 0.0004 | 0.0046 ± 0.0006 |
| 4 obs DHR + physics | no | 0.0005 ± 0.0002 | 0.0015 ± 0.0003 | 0.0037 ± 0.0006 | 0.0005 ± 0.0002 | 0.0015 ± 0.0003 | 0.0037 ± 0.0006 |


### Cost per arm at the gate setting (DESIGN 6.4: reported, not gated)

| arm | measurement bytes (B/UE/s) | over-the-air bytes (B/UE/s) | compute units/decision | bytes / arm 1 | compute / arm 1 |
|---|---|---|---|---|---|
| 1 single (C1) | 400.0 | 400.0 | 1.0 | 1.00x | 1.00x |
| 2 model DHR (C1 x3) | 400.0 | 400.0 | 4.0 | 1.00x | 4.00x |
| 3 observation DHR (C1-C4) | 4200.0 | 4000.0 | 5.0 | 10.50x | 5.00x |
| 4 obs DHR + physics | 4200.0 | 4000.0 | 11.0 | 10.50x | 11.00x |


### Paired differences (per seed)

| pair | setting | attack-attributable success / opportunity | false exclusion | throughput |
|---|---|---|---|---|
| model_dhr − single | Δ = 0 null | -0.0002 ± 0.0007 | 0.0000 ± 0.0000 | 0.0000 ± 0.0002 |
| obs_dhr − model_dhr | Δ = 0 null | -0.0138 ± 0.0042 * | 0.0000 ± 0.0000 | -0.0052 ± 0.0024 * |
| obs_dhr − obs_dhr_phys | Δ = 0 null | -0.0002 ± 0.0004 | -0.0108 ± 0.0003 * | 0.0008 ± 0.0014 |
| obs_dhr_phys − single | Δ = 0 null | -0.0138 ± 0.0047 * | 0.0108 ± 0.0003 * | -0.0060 ± 0.0014 * |
| model_dhr − single | Δ = 10, ρ = 0 | 0.0003 ± 0.0004 | 0.0000 ± 0.0000 | -0.0000 ± 0.0003 |
| obs_dhr − model_dhr | Δ = 10, ρ = 0 | -0.1210 ± 0.0012 * | 0.0000 ± 0.0000 | 0.0011 ± 0.0052 |
| obs_dhr − obs_dhr_phys | Δ = 10, ρ = 0 | 0.0003 ± 0.0002 * | -0.0108 ± 0.0003 * | 0.0013 ± 0.0014 |
| obs_dhr_phys − single | Δ = 10, ρ = 0 | -0.1209 ± 0.0012 * | 0.0108 ± 0.0003 * | -0.0002 ± 0.0047 |
| model_dhr − single | Δ = 10, ρ = 0.5 | 0.0003 ± 0.0004 | 0.0000 ± 0.0000 | -0.0000 ± 0.0003 |
| obs_dhr − model_dhr | Δ = 10, ρ = 0.5 | -0.1198 ± 0.0013 * | 0.0000 ± 0.0000 | 0.0020 ± 0.0052 |
| obs_dhr − obs_dhr_phys | Δ = 10, ρ = 0.5 | 0.0005 ± 0.0002 * | -0.0108 ± 0.0003 * | 0.0010 ± 0.0015 |
| obs_dhr_phys − single | Δ = 10, ρ = 0.5 | -0.1199 ± 0.0013 * | 0.0108 ± 0.0003 * | 0.0010 ± 0.0047 |
| model_dhr − single | Δ = 10, ρ = 1 | 0.0003 ± 0.0004 | 0.0000 ± 0.0000 | -0.0000 ± 0.0003 |
| obs_dhr − model_dhr | Δ = 10, ρ = 1 | -0.1172 ± 0.0014 * | 0.0000 ± 0.0000 | 0.0029 ± 0.0045 |
| obs_dhr − obs_dhr_phys | Δ = 10, ρ = 1 | 0.0008 ± 0.0002 * | -0.0108 ± 0.0003 * | 0.0009 ± 0.0022 |
| obs_dhr_phys − single | Δ = 10, ρ = 1 | -0.1177 ± 0.0013 * | 0.0108 ± 0.0003 * | 0.0020 ± 0.0043 |
| model_dhr − single | Δ = 6, ρ = 0 | -0.0000 ± 0.0001 | 0.0000 ± 0.0000 | -0.0000 ± 0.0002 |
| obs_dhr − model_dhr | Δ = 6, ρ = 0 | -0.1068 ± 0.0037 * | 0.0000 ± 0.0000 | -0.0083 ± 0.0032 * |
| obs_dhr − obs_dhr_phys | Δ = 6, ρ = 0 | 0.0001 ± 0.0002 | -0.0108 ± 0.0003 * | 0.0008 ± 0.0015 |
| obs_dhr_phys − single | Δ = 6, ρ = 0 | -0.1070 ± 0.0038 * | 0.0108 ± 0.0003 * | -0.0091 ± 0.0021 * |

`*` marks a paired 95 % CI that excludes zero.


### Check decomposition, arm 4 (diagnostic; **not** a gate result)

| check set | ρ | Δ = 0 null | Δ = 10 | false exclusion | C1 exclusion on actionable slots |
|---|---|---|---|---|---|
| default | 0 | 0.0024 ± 0.0020 | 0.0005 ± 0.0002 | 0.0108 ± 0.0003 | 0.9754 ± 0.0034 |
| default | 1 | 0.0024 ± 0.0020 | 0.0037 ± 0.0006 | 0.0108 ± 0.0003 | 0.8385 ± 0.0162 |
| no_self | 0 | 0.0024 ± 0.0020 | 0.0005 ± 0.0002 | 0.0106 ± 0.0003 | 0.9747 ± 0.0035 |
| no_self | 1 | 0.0024 ± 0.0020 | 0.0037 ± 0.0006 | 0.0106 ± 0.0003 | 0.8307 ± 0.0167 |
| recip | 0 | 0.0024 ± 0.0020 | 0.0005 ± 0.0002 | 0.0096 ± 0.0002 | 0.9179 ± 0.0037 |
| recip | 1 | 0.0024 ± 0.0020 | 0.0045 ± 0.0006 | 0.0096 ± 0.0002 | 0.0056 ± 0.0004 |
| self | 0 | 0.0022 ± 0.0019 | 0.0008 ± 0.0002 | 0.0011 ± 0.0003 | 0.0251 ± 0.0036 |
| self | 1 | 0.0022 ± 0.0019 | 0.0045 ± 0.0006 | 0.0011 ± 0.0003 | 0.0265 ± 0.0040 |
| temporal | 0 | 0.0022 ± 0.0019 | 0.0008 ± 0.0002 | 0.0010 ± 0.0002 | 0.8298 ± 0.0170 |
| temporal | 1 | 0.0022 ± 0.0019 | 0.0037 ± 0.0006 | 0.0010 ± 0.0002 | 0.8298 ± 0.0168 |
