# WES majority-reach run b2: analysis summary

Runs: 3400 runs; mean 1.08 s, max 1.63 s per run (DESIGN 8 budget 20 s); 3674 s CPU in total

Gate setting: {'p': 0.2, 'delta': 10.0, 'rho': 1.0, 'sigma_map': 2.0, 'mode': 'trap', 'check_set': 'default', 'z': 3.0, 'ramp_slots': 1, 'persistence_slots': 3}


### Gate-2 table (PROTOCOL.md, evaluated literally on the attack-attributable rate per targeted slot)

| gate | criterion | numbers | verdict |
|---|---|---|---|
| **G2-a** | ρ = 1, Δ = 10, every σ_map: arm 3 ≥ 0.5 × arm 1 on the primary metric | σ_map = 2: arm 1 = 0.0414 ± 0.0037, arm 3 = 0.0328 ± 0.0027 (0.791 × arm 1, ≥ 0.5×); paired arm3 − 0.5·arm1 = 0.0121 ± 0.0010; null-corrected 0.0120 ± 0.0010; σ_map = 4: arm 1 = 0.0414 ± 0.0037, arm 3 = 0.0334 ± 0.0028 (0.805 × arm 1, ≥ 0.5×); paired arm3 − 0.5·arm1 = 0.0127 ± 0.0011; null-corrected 0.0125 ± 0.0011; σ_map = 6: arm 1 = 0.0414 ± 0.0037, arm 3 = 0.0340 ± 0.0030 (0.821 × arm 1, ≥ 0.5×); paired arm3 − 0.5·arm1 = 0.0133 ± 0.0013; null-corrected 0.0132 ± 0.0013 | **PASS** |
| **G2-b** | ρ = 1, Δ = 10, σ_map = 2, step: arm 4 ≤ 0.2 × arm 3 with the CI excluding the boundary **and** false exclusion ≤ 0.05 | arm 3 = 0.0328 ± 0.0027; arm 4 = 0.0037 ± 0.0005 (0.1130 × arm 3); paired arm4 − 0.2·arm3 = -0.0029 ± 0.0005 (CI wholly below 0: yes); null-corrected -0.0032 ± 0.0006; false exclusion = 0.0008 ± 0.0002 (≤ 0.05: yes). σ_map = 4 (reported): arm 3 = 0.0334 ± 0.0028, arm 4 = 0.0242 ± 0.0026 (0.726 × arm 3); σ_map = 6 (reported): arm 3 = 0.0340 ± 0.0030, arm 4 = 0.0312 ± 0.0028 (0.917 × arm 3) | **PASS** |
| **G2-c** | at Δ = 0, arms 4 and 5c against arm 1: `rsrp_deficit` not worse by more than 0.5 dB and `outage_share` not worse by more than 10 % relative | rsrp_deficit arm1 = 0.0499 ± 0.0039, obs_dhr_phys = 0.0642 ± 0.0043, paired 0.0143 ± 0.0032 (≤ +0.5 dB: yes); outage_share arm1 = 0.0000 ± 0.0000, obs_dhr_phys = 0.0000 ± 0.0000, paired 0.0000 ± 0.0000 (≤ +10 % relative: yes); missed handovers / UE-slot obs_dhr_phys = 0.0005 ± 0.0001 at Δ = 0 and 0.0008 ± 0.0001 under attack (reported, PROTOCOL.md sets no threshold); rsrp_deficit arm1 = 0.0499 ± 0.0039, cheap_phys = 0.1126 ± 0.0118, paired 0.0627 ± 0.0123 (≤ +0.5 dB: yes); outage_share arm1 = 0.0000 ± 0.0000, cheap_phys = 0.0000 ± 0.0000, paired 0.0000 ± 0.0000 (≤ +10 % relative: yes); missed handovers / UE-slot cheap_phys = 0.0010 ± 0.0001 at Δ = 0 and 0.0010 ± 0.0002 under attack (reported, PROTOCOL.md sets no threshold) | **PASS** |


**G2-a and G2-b pass** → in the specification's own words: *"G2-a and G2-b pass → the paper is 'what anchors the check', with σ_map the design parameter and the ramp the boundary."*


### Δ = 0 null control (attacker present, falsification zero; σ_map = 2)

| arm | attack-attributable success / targeted slot | attack-attributable success / opportunity | actionable share (with TTT) | false exclusion (clean UE-slots) | RSRP deficit (dB) | outage share | throughput proxy |
|---|---|---|---|---|---|---|---|
| 1 single (C1) | 0.0006 ± 0.0002 | 0.0020 ± 0.0031 | 0.0056 ± 0.0010 | 0.0000 ± 0.0000 | 0.0499 ± 0.0039 | 0.0000 ± 0.0000 | 1.3584 ± 0.0404 |
| 2' model DHR (3 families on C1) | 0.0003 ± 0.0001 | 0.0009 ± 0.0007 | 0.0412 ± 0.0106 | 0.0000 ± 0.0000 | 0.4826 ± 0.0421 | 0.0000 ± 0.0000 | 1.2933 ± 0.0373 |
| 3 obs DHR (C1, N, C4) | 0.0004 ± 0.0001 | 0.0028 ± 0.0033 | 0.0073 ± 0.0013 | 0.0000 ± 0.0000 | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4 obs DHR + physics | 0.0004 ± 0.0001 | 0.0028 ± 0.0033 | 0.0073 ± 0.0013 | 0.0008 ± 0.0002 | 0.0642 ± 0.0043 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4d obs DHR + dithered physics | 0.0004 ± 0.0001 | 0.0028 ± 0.0033 | 0.0073 ± 0.0013 | 0.0011 ± 0.0002 | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 5c cheap physics (C1, C4) | 0.0002 ± 0.0001 | 0.0016 ± 0.0019 | 0.0122 ± 0.0030 | 0.0008 ± 0.0002 | 0.1126 ± 0.0118 | 0.0000 ± 0.0000 | 1.3515 ± 0.0415 |


### Headline metrics at the gate setting (p = 0.2, Δ = 10 dB, ρ = 1, σ_map = 2 dB, trap; mean ± 95 % CI)

| arm | attack-attributable success / targeted slot | attack-attributable success / opportunity | raw success / targeted slot | actionable share (with TTT) | false exclusion (clean UE-slots) | throughput proxy |
|---|---|---|---|---|---|---|
| 1 single (C1) | 0.0414 ± 0.0037 | 0.5336 ± 0.0177 | 0.0472 ± 0.0043 | 0.0729 ± 0.0068 | 0.0000 ± 0.0000 | 1.3536 ± 0.0436 |
| 2' model DHR (3 families on C1) | 0.0132 ± 0.0017 | 0.0437 ± 0.0067 | 0.0154 ± 0.0020 | 0.2823 ± 0.0286 | 0.0000 ± 0.0000 | 1.2813 ± 0.0396 |
| 3 obs DHR (C1, N, C4) | 0.0328 ± 0.0027 | 0.2964 ± 0.0150 | 0.0360 ± 0.0031 | 0.1092 ± 0.0112 | 0.0000 ± 0.0000 | 1.3540 ± 0.0443 |
| 4 obs DHR + physics | 0.0037 ± 0.0005 | 0.0125 ± 0.0017 | 0.0056 ± 0.0007 | 0.2941 ± 0.0270 | 0.0008 ± 0.0002 | 1.3516 ± 0.0417 |
| 4d obs DHR + dithered physics | 0.0064 ± 0.0012 | 0.0235 ± 0.0046 | 0.0085 ± 0.0014 | 0.2708 ± 0.0248 | 0.0011 ± 0.0002 | 1.3517 ± 0.0433 |
| 5c cheap physics (C1, C4) | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0028 ± 0.0003 | 0.3080 ± 0.0282 | 0.0008 ± 0.0002 | 1.3494 ± 0.0410 |


### attack-attributable success / targeted slot over σ_map × ρ (Δ = 10 dB, trap)

| arm | σ_map | ρ = 0 | ρ = 0.5 | ρ = 1 | Δ = 0 null |
|---|---|---|---|---|---|
| 1 single (C1) | 2 | 0.0414 ± 0.0037 | 0.0414 ± 0.0037 | 0.0414 ± 0.0037 | 0.0006 ± 0.0002 |
| 1 single (C1) | 4 | 0.0414 ± 0.0037 | 0.0414 ± 0.0037 | 0.0414 ± 0.0037 | 0.0006 ± 0.0002 |
| 1 single (C1) | 6 | 0.0414 ± 0.0037 | 0.0414 ± 0.0037 | 0.0414 ± 0.0037 | 0.0006 ± 0.0002 |
| 3 obs DHR (C1, N, C4) | 2 | 0.0019 ± 0.0003 | 0.0068 ± 0.0007 | 0.0328 ± 0.0027 | 0.0004 ± 0.0001 |
| 3 obs DHR (C1, N, C4) | 4 | 0.0031 ± 0.0006 | 0.0083 ± 0.0008 | 0.0334 ± 0.0028 | 0.0004 ± 0.0001 |
| 3 obs DHR (C1, N, C4) | 6 | 0.0040 ± 0.0007 | 0.0097 ± 0.0010 | 0.0340 ± 0.0030 | 0.0004 ± 0.0001 |
| 4 obs DHR + physics | 2 | 0.0013 ± 0.0002 | 0.0014 ± 0.0002 | 0.0037 ± 0.0005 | 0.0004 ± 0.0001 |
| 4 obs DHR + physics | 4 | 0.0026 ± 0.0005 | 0.0063 ± 0.0008 | 0.0242 ± 0.0026 | 0.0004 ± 0.0001 |
| 4 obs DHR + physics | 6 | 0.0042 ± 0.0007 | 0.0096 ± 0.0008 | 0.0312 ± 0.0028 | 0.0004 ± 0.0001 |
| 5c cheap physics (C1, C4) | 2 | 0.0013 ± 0.0002 | 0.0013 ± 0.0002 | 0.0013 ± 0.0002 | 0.0002 ± 0.0001 |
| 5c cheap physics (C1, C4) | 4 | 0.0019 ± 0.0003 | 0.0020 ± 0.0003 | 0.0020 ± 0.0003 | 0.0002 ± 0.0001 |
| 5c cheap physics (C1, C4) | 6 | 0.0020 ± 0.0003 | 0.0021 ± 0.0003 | 0.0021 ± 0.0002 | 0.0002 ± 0.0001 |


### attack-attributable success / targeted slot against Δ (ρ = 1, trap)

| arm | σ_map | Δ = 0 (null) | Δ = 6 dB | Δ = 10 dB | Δ = 15 dB |
|---|---|---|---|---|---|
| 1 single (C1) | 2 | 0.0006 ± 0.0002 | 0.0151 ± 0.0011 | 0.0414 ± 0.0037 | 0.0847 ± 0.0055 |
| 1 single (C1) | 4 | 0.0006 ± 0.0002 | 0.0151 ± 0.0011 | 0.0414 ± 0.0037 | 0.0847 ± 0.0055 |
| 1 single (C1) | 6 | 0.0006 ± 0.0002 | 0.0151 ± 0.0011 | 0.0414 ± 0.0037 | 0.0847 ± 0.0055 |
| 2' model DHR (3 families on C1) | 2 | 0.0003 ± 0.0001 | 0.0058 ± 0.0006 | 0.0132 ± 0.0017 | 0.0188 ± 0.0019 |
| 2' model DHR (3 families on C1) | 4 | 0.0003 ± 0.0001 | 0.0058 ± 0.0006 | 0.0132 ± 0.0017 | 0.0188 ± 0.0019 |
| 2' model DHR (3 families on C1) | 6 | 0.0003 ± 0.0001 | 0.0058 ± 0.0006 | 0.0132 ± 0.0017 | 0.0188 ± 0.0019 |
| 3 obs DHR (C1, N, C4) | 2 | 0.0004 ± 0.0001 | 0.0095 ± 0.0005 | 0.0328 ± 0.0027 | 0.0743 ± 0.0050 |
| 3 obs DHR (C1, N, C4) | 4 | 0.0004 ± 0.0001 | 0.0102 ± 0.0007 | 0.0334 ± 0.0028 | 0.0747 ± 0.0050 |
| 3 obs DHR (C1, N, C4) | 6 | 0.0004 ± 0.0001 | 0.0109 ± 0.0007 | 0.0340 ± 0.0030 | 0.0754 ± 0.0053 |
| 4 obs DHR + physics | 2 | 0.0004 ± 0.0001 | 0.0074 ± 0.0008 | 0.0037 ± 0.0005 | 0.0017 ± 0.0001 |
| 4 obs DHR + physics | 4 | 0.0004 ± 0.0001 | 0.0098 ± 0.0008 | 0.0242 ± 0.0026 | 0.0147 ± 0.0019 |
| 4 obs DHR + physics | 6 | 0.0004 ± 0.0001 | 0.0107 ± 0.0008 | 0.0312 ± 0.0028 | 0.0478 ± 0.0048 |
| 4d obs DHR + dithered physics | 2 | 0.0004 ± 0.0001 | 0.0081 ± 0.0008 | 0.0064 ± 0.0012 | 0.0017 ± 0.0002 |
| 4d obs DHR + dithered physics | 4 | 0.0004 ± 0.0001 | 0.0100 ± 0.0008 | 0.0283 ± 0.0026 | 0.0279 ± 0.0032 |
| 4d obs DHR + dithered physics | 6 | 0.0004 ± 0.0001 | 0.0108 ± 0.0008 | 0.0327 ± 0.0027 | 0.0625 ± 0.0050 |
| 5c cheap physics (C1, C4) | 2 | 0.0002 ± 0.0001 | 0.0014 ± 0.0001 | 0.0013 ± 0.0002 | 0.0013 ± 0.0002 |
| 5c cheap physics (C1, C4) | 4 | 0.0002 ± 0.0001 | 0.0017 ± 0.0002 | 0.0020 ± 0.0003 | 0.0019 ± 0.0003 |
| 5c cheap physics (C1, C4) | 6 | 0.0002 ± 0.0001 | 0.0017 ± 0.0002 | 0.0021 ± 0.0002 | 0.0022 ± 0.0002 |


### Primary and secondary attack metrics (σ_map = 2, Δ = 10, trap)

| arm | ρ | attack-attributable success / targeted slot | attack-attributable success / opportunity | attack-attributable success / instant opportunity |
|---|---|---|---|---|
| 1 single (C1) | 0 | 0.0414 ± 0.0037 | 0.5336 ± 0.0177 | 0.1309 ± 0.0025 |
| 1 single (C1) | 0.5 | 0.0414 ± 0.0037 | 0.5336 ± 0.0177 | 0.1309 ± 0.0025 |
| 1 single (C1) | 1 | 0.0414 ± 0.0037 | 0.5336 ± 0.0177 | 0.1309 ± 0.0025 |
| 2' model DHR (3 families on C1) | 0 | 0.0132 ± 0.0017 | 0.0437 ± 0.0067 | 0.0328 ± 0.0038 |
| 2' model DHR (3 families on C1) | 0.5 | 0.0132 ± 0.0017 | 0.0437 ± 0.0067 | 0.0328 ± 0.0038 |
| 2' model DHR (3 families on C1) | 1 | 0.0132 ± 0.0017 | 0.0437 ± 0.0067 | 0.0328 ± 0.0038 |
| 3 obs DHR (C1, N, C4) | 0 | 0.0019 ± 0.0003 | 0.0064 ± 0.0011 | 0.0050 ± 0.0009 |
| 3 obs DHR (C1, N, C4) | 0.5 | 0.0068 ± 0.0007 | 0.0259 ± 0.0027 | 0.0187 ± 0.0016 |
| 3 obs DHR (C1, N, C4) | 1 | 0.0328 ± 0.0027 | 0.2964 ± 0.0150 | 0.1035 ± 0.0018 |
| 4 obs DHR + physics | 0 | 0.0013 ± 0.0002 | 0.0043 ± 0.0005 | 0.0035 ± 0.0004 |
| 4 obs DHR + physics | 0.5 | 0.0014 ± 0.0002 | 0.0046 ± 0.0008 | 0.0037 ± 0.0006 |
| 4 obs DHR + physics | 1 | 0.0037 ± 0.0005 | 0.0125 ± 0.0017 | 0.0098 ± 0.0012 |
| 4d obs DHR + dithered physics | 0 | 0.0013 ± 0.0002 | 0.0043 ± 0.0006 | 0.0034 ± 0.0005 |
| 4d obs DHR + dithered physics | 0.5 | 0.0019 ± 0.0004 | 0.0063 ± 0.0013 | 0.0050 ± 0.0009 |
| 4d obs DHR + dithered physics | 1 | 0.0064 ± 0.0012 | 0.0235 ± 0.0046 | 0.0173 ± 0.0028 |
| 5c cheap physics (C1, C4) | 0 | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0035 ± 0.0005 |
| 5c cheap physics (C1, C4) | 0.5 | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0035 ± 0.0005 |
| 5c cheap physics (C1, C4) | 1 | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0035 ± 0.0005 |


### Harm and quality of service: Δ = 0 (cost of the defence) and Δ = 10, ρ = 1 (its value); σ_map = 2

| arm | Δ | RSRP deficit (dB) | outage share | wrong-cell share | wrong handovers / handover | ping-pongs / handover | missed handovers / UE-slot | missed handovers / oracle handover | handovers / UE-slot | trusted-channel fallback rate | throughput proxy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 single (C1) | 0 (null) | 0.0499 ± 0.0039 | 0.0000 ± 0.0000 | 0.0077 ± 0.0005 | 0.0345 ± 0.0073 | 0.0445 ± 0.0099 | 0.0003 ± 0.0000 | 0.0732 ± 0.0075 | 0.0037 ± 0.0002 | 0.0000 ± 0.0000 | 1.3584 ± 0.0404 |
| 1 single (C1) | 10 | 0.0675 ± 0.0049 | 0.0000 ± 0.0000 | 0.0104 ± 0.0007 | 0.5407 ± 0.0139 | 0.6074 ± 0.0235 | 0.0011 ± 0.0002 | 0.1825 ± 0.0254 | 0.0137 ± 0.0009 | 0.0000 ± 0.0000 | 1.3536 ± 0.0436 |
| 2' model DHR (3 families on C1) | 0 (null) | 0.4826 ± 0.0421 | 0.0000 ± 0.0000 | 0.0504 ± 0.0034 | 0.0294 ± 0.0061 | 0.0196 ± 0.0058 | 0.0025 ± 0.0002 | 0.4858 ± 0.0209 | 0.0028 ± 0.0001 | 0.0000 ± 0.0000 | 1.2933 ± 0.0373 |
| 2' model DHR (3 families on C1) | 10 | 0.5620 ± 0.0490 | 0.0000 ± 0.0000 | 0.0591 ± 0.0049 | 0.3899 ± 0.0213 | 0.2946 ± 0.0226 | 0.0031 ± 0.0003 | 0.5047 ± 0.0234 | 0.0060 ± 0.0005 | 0.0000 ± 0.0000 | 1.2813 ± 0.0396 |
| 3 obs DHR (C1, N, C4) | 0 (null) | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 0.0103 ± 0.0008 | 0.0300 ± 0.0098 | 0.0383 ± 0.0071 | 0.0005 ± 0.0001 | 0.1262 ± 0.0187 | 0.0035 ± 0.0002 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 3 obs DHR (C1, N, C4) | 10 | 0.0740 ± 0.0048 | 0.0000 ± 0.0000 | 0.0118 ± 0.0009 | 0.5333 ± 0.0129 | 0.5497 ± 0.0157 | 0.0010 ± 0.0001 | 0.1883 ± 0.0189 | 0.0109 ± 0.0007 | 0.0000 ± 0.0000 | 1.3540 ± 0.0443 |
| 4 obs DHR + physics | 0 (null) | 0.0642 ± 0.0043 | 0.0000 ± 0.0000 | 0.0103 ± 0.0008 | 0.0300 ± 0.0098 | 0.0383 ± 0.0071 | 0.0005 ± 0.0001 | 0.1265 ± 0.0188 | 0.0035 ± 0.0002 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4 obs DHR + physics | 10 | 0.0902 ± 0.0120 | 0.0000 ± 0.0000 | 0.0136 ± 0.0014 | 0.1621 ± 0.0170 | 0.1049 ± 0.0158 | 0.0008 ± 0.0001 | 0.1947 ± 0.0285 | 0.0042 ± 0.0003 | 0.0000 ± 0.0000 | 1.3516 ± 0.0417 |
| 4d obs DHR + dithered physics | 0 (null) | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 0.0103 ± 0.0008 | 0.0300 ± 0.0098 | 0.0387 ± 0.0071 | 0.0005 ± 0.0001 | 0.1268 ± 0.0183 | 0.0035 ± 0.0002 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4d obs DHR + dithered physics | 10 | 0.0929 ± 0.0118 | 0.0000 ± 0.0000 | 0.0140 ± 0.0014 | 0.2385 ± 0.0283 | 0.1756 ± 0.0324 | 0.0008 ± 0.0001 | 0.1957 ± 0.0282 | 0.0049 ± 0.0004 | 0.0000 ± 0.0000 | 1.3517 ± 0.0433 |
| 5c cheap physics (C1, C4) | 0 (null) | 0.1126 ± 0.0118 | 0.0000 ± 0.0000 | 0.0175 ± 0.0021 | 0.0218 ± 0.0068 | 0.0254 ± 0.0089 | 0.0010 ± 0.0001 | 0.2275 ± 0.0330 | 0.0031 ± 0.0002 | 0.0007 ± 0.0002 | 1.3515 ± 0.0415 |
| 5c cheap physics (C1, C4) | 10 | 0.1167 ± 0.0131 | 0.0000 ± 0.0000 | 0.0181 ± 0.0024 | 0.0775 ± 0.0124 | 0.0314 ± 0.0084 | 0.0010 ± 0.0002 | 0.2449 ± 0.0371 | 0.0034 ± 0.0002 | 0.1098 ± 0.0059 | 1.3494 ± 0.0410 |


### Paired harm differences against arm 1 (`*` marks a CI excluding zero)

| arm | Δ | RSRP deficit (dB) | outage share | missed handovers / UE-slot |
|---|---|---|---|---|
| 2' model DHR (3 families on C1) | 0 (null) | 0.4327 ± 0.0407 * | 0.0000 ± 0.0000 | 0.0022 ± 0.0002 * |
| 2' model DHR (3 families on C1) | 10 | 0.4945 ± 0.0485 * | 0.0000 ± 0.0000 | 0.0020 ± 0.0004 * |
| 3 obs DHR (C1, N, C4) | 0 (null) | 0.0143 ± 0.0032 * | 0.0000 ± 0.0000 | 0.0002 ± 0.0001 * |
| 3 obs DHR (C1, N, C4) | 10 | 0.0065 ± 0.0037 * | 0.0000 ± 0.0000 | -0.0001 ± 0.0001 |
| 4 obs DHR + physics | 0 (null) | 0.0143 ± 0.0032 * | 0.0000 ± 0.0000 | 0.0002 ± 0.0001 * |
| 4 obs DHR + physics | 10 | 0.0227 ± 0.0132 * | 0.0000 ± 0.0000 | -0.0003 ± 0.0002 * |
| 4d obs DHR + dithered physics | 0 (null) | 0.0143 ± 0.0033 * | 0.0000 ± 0.0000 | 0.0002 ± 0.0001 * |
| 4d obs DHR + dithered physics | 10 | 0.0254 ± 0.0125 * | 0.0000 ± 0.0000 | -0.0003 ± 0.0002 * |
| 5c cheap physics (C1, C4) | 0 (null) | 0.0627 ± 0.0123 * | 0.0000 ± 0.0000 | 0.0007 ± 0.0002 * |
| 5c cheap physics (C1, C4) | 10 | 0.0492 ± 0.0140 * | 0.0000 ± 0.0000 | -0.0001 ± 0.0003 |


### Apparatus diagnostics at the gate setting

| arm | majority reachable | actionable share (with TTT) | actionable share (instantaneous) | falsified-channel exclusion on actionable slots | false exclusion (clean UE-slots) | voting channels |
|---|---|---|---|---|---|---|
| 1 single (C1) | yes | 0.0729 ± 0.0068 | 0.3126 ± 0.0259 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| 2' model DHR (3 families on C1) | yes | 0.2823 ± 0.0286 | 0.3967 ± 0.0331 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 3.0000 ± 0.0000 |
| 3 obs DHR (C1, N, C4) | yes | 0.1092 ± 0.0112 | 0.3162 ± 0.0266 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 3.0000 ± 0.0000 |
| 4 obs DHR + physics | yes | 0.2941 ± 0.0270 | 0.3798 ± 0.0319 | 0.9625 ± 0.0051 | 0.0008 ± 0.0002 | 2.8888 ± 0.0060 |
| 4d obs DHR + dithered physics | yes | 0.2708 ± 0.0248 | 0.3687 ± 0.0310 | 0.9220 ± 0.0097 | 0.0011 ± 0.0002 | 2.8978 ± 0.0053 |
| 5c cheap physics (C1, C4) | no | 0.3080 ± 0.0282 | 0.3858 ± 0.0330 | 0.9148 ± 0.0137 | 0.0008 ± 0.0002 | 1.8902 ± 0.0059 |


### False exclusion per check against its analytic floor (arm 4, Δ = 0, clean UE-slots)

| check | tests / UE-slot | measured | analytic floor |
|---|---|---|---|
| serving_reciprocity | 1 | 0.0000 ± 0.0000 | 1.97e-08 |
| neighbour_reciprocity | 2 | 0.0000 ± 0.0000 | 1.57e-07 |
| map | 3 | 0.0008 ± 0.0002 | 5.27e-07 |
| rate | 3 | 0.0000 ± 0.0000 | 5.27e-07 |
| any check (union) | n/a | 0.0008 ± 0.0002 | n/a |


### Both attacker modes with the Δ = 0 null (σ_map = 2, ρ = 0; ping-pong is only run at ρ = 0)

| arm | attack-attributable success / targeted slot (trap) | Δ = 0 null (trap) | wrong HO / handover (trap) | attack-attributable success / targeted slot (pingpong) | Δ = 0 null (pingpong) | wrong HO / handover (pingpong) |
|---|---|---|---|---|---|---|
| 1 single (C1) | 0.0414 ± 0.0037 | 0.0006 ± 0.0002 | 0.5407 ± 0.0139 | 0.0047 ± 0.0005 | 0.0008 ± 0.0002 | 0.1557 ± 0.0136 |
| 2' model DHR (3 families on C1) | 0.0132 ± 0.0017 | 0.0003 ± 0.0001 | 0.3899 ± 0.0213 | 0.0035 ± 0.0006 | 0.0006 ± 0.0001 | 0.1509 ± 0.0172 |
| 3 obs DHR (C1, N, C4) | 0.0019 ± 0.0003 | 0.0004 ± 0.0001 | 0.0735 ± 0.0140 | 0.0016 ± 0.0002 | 0.0005 ± 0.0001 | 0.0641 ± 0.0113 |
| 4 obs DHR + physics | 0.0013 ± 0.0002 | 0.0004 ± 0.0001 | 0.0774 ± 0.0114 | 0.0006 ± 0.0001 | 0.0005 ± 0.0001 | 0.0389 ± 0.0083 |
| 4d obs DHR + dithered physics | 0.0013 ± 0.0002 | 0.0004 ± 0.0001 | 0.0772 ± 0.0112 | 0.0007 ± 0.0001 | 0.0005 ± 0.0001 | 0.0410 ± 0.0096 |
| 5c cheap physics (C1, C4) | 0.0013 ± 0.0002 | 0.0002 ± 0.0001 | 0.0760 ± 0.0120 | 0.0018 ± 0.0002 | 0.0003 ± 0.0001 | 0.0728 ± 0.0115 |


### Sticky ramp attacker (DESIGN 5; reported, not gated)

| arm | σ_map | ramp = 1 slot(s) | ramp = 10 slot(s) | ramp = 20 slot(s) | detection, ramp = 1 | detection, ramp = 10 | detection, ramp = 20 | actionable share, ramp = 1 | actionable share, ramp = 10 | actionable share, ramp = 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 single (C1) | 2 | 0.0414 ± 0.0037 | 0.0261 ± 0.0021 | 0.0186 ± 0.0014 | 0.000 | 0.000 | 0.000 | 0.073 | 0.056 | 0.047 |
| 1 single (C1) | 4 | 0.0414 ± 0.0037 | 0.0261 ± 0.0021 | 0.0186 ± 0.0014 | 0.000 | 0.000 | 0.000 | 0.073 | 0.056 | 0.047 |
| 3 obs DHR (C1, N, C4) | 2 | 0.0328 ± 0.0027 | 0.0209 ± 0.0016 | 0.0151 ± 0.0012 | 0.000 | 0.000 | 0.000 | 0.109 | 0.096 | 0.082 |
| 3 obs DHR (C1, N, C4) | 4 | 0.0334 ± 0.0028 | 0.0215 ± 0.0016 | 0.0154 ± 0.0013 | 0.000 | 0.000 | 0.000 | 0.108 | 0.093 | 0.080 |
| 4 obs DHR + physics | 2 | 0.0037 ± 0.0005 | 0.0040 ± 0.0005 | 0.0041 ± 0.0005 | 0.962 | 0.953 | 0.932 | 0.294 | 0.268 | 0.235 |
| 4 obs DHR + physics | 4 | 0.0242 ± 0.0026 | 0.0174 ± 0.0017 | 0.0131 ± 0.0013 | 0.529 | 0.457 | 0.407 | 0.169 | 0.137 | 0.112 |


### Cost per arm at the gate setting (DESIGN 6: reported, not gated)

| arm | measurement bytes (B/UE/s) | over-the-air bytes (B/UE/s) | compute units/decision | OTA bytes / arm 1 | compute / arm 1 |
|---|---|---|---|---|---|
| 1 single (C1) | 400.0 | 400.0 | 1.0 | 1.00x | 1.00x |
| 2' model DHR (3 families on C1) | 400.0 | 400.0 | 3.0 | 1.00x | 3.00x |
| 3 obs DHR (C1, N, C4) | 4200.0 | 4000.0 | 3.0 | 10.00x | 3.00x |
| 4 obs DHR + physics | 4200.0 | 4000.0 | 7.0 | 10.00x | 7.00x |
| 4d obs DHR + dithered physics | 4200.0 | 4000.0 | 7.0 | 10.00x | 7.00x |
| 5c cheap physics (C1, C4) | 600.0 | 400.0 | 6.0 | 1.00x | 6.00x |


### Paired differences on the null-corrected primary metric (Δ = 10; `*` marks a 95 % CI excluding zero)

| pair | σ_map | ρ | paired difference |
|---|---|---|---|
| model_dhr3 − single | 2 | 0 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 2 | 0 | -0.0394 ± 0.0037 * |
| obs_dhr_phys − obs_dhr | 2 | 0 | -0.0006 ± 0.0002 * |
| obs_dhr_phys_dither − obs_dhr_phys | 2 | 0 | -0.0000 ± 0.0000 |
| cheap_phys − obs_dhr_phys | 2 | 0 | 0.0002 ± 0.0000 * |
| model_dhr3 − single | 2 | 1 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 2 | 1 | -0.0085 ± 0.0013 * |
| obs_dhr_phys − obs_dhr | 2 | 1 | -0.0291 ± 0.0025 * |
| obs_dhr_phys_dither − obs_dhr_phys | 2 | 1 | 0.0027 ± 0.0008 * |
| cheap_phys − obs_dhr_phys | 2 | 1 | -0.0022 ± 0.0004 * |
| model_dhr3 − single | 4 | 0 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 4 | 0 | -0.0382 ± 0.0034 * |
| obs_dhr_phys − obs_dhr | 4 | 0 | -0.0005 ± 0.0003 * |
| obs_dhr_phys_dither − obs_dhr_phys | 4 | 0 | 0.0002 ± 0.0002 * |
| cheap_phys − obs_dhr_phys | 4 | 0 | -0.0005 ± 0.0003 * |
| model_dhr3 − single | 4 | 1 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 4 | 1 | -0.0079 ± 0.0012 * |
| obs_dhr_phys − obs_dhr | 4 | 1 | -0.0091 ± 0.0012 * |
| obs_dhr_phys_dither − obs_dhr_phys | 4 | 1 | 0.0040 ± 0.0008 * |
| cheap_phys − obs_dhr_phys | 4 | 1 | -0.0221 ± 0.0024 * |
| model_dhr3 − single | 6 | 0 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 6 | 0 | -0.0373 ± 0.0033 * |
| obs_dhr_phys − obs_dhr | 6 | 0 | 0.0002 ± 0.0006 |
| obs_dhr_phys_dither − obs_dhr_phys | 6 | 0 | 0.0004 ± 0.0002 * |
| cheap_phys − obs_dhr_phys | 6 | 0 | -0.0019 ± 0.0007 * |
| model_dhr3 − single | 6 | 1 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 6 | 1 | -0.0073 ± 0.0011 * |
| obs_dhr_phys − obs_dhr | 6 | 1 | -0.0028 ± 0.0009 * |
| obs_dhr_phys_dither − obs_dhr_phys | 6 | 1 | 0.0015 ± 0.0005 * |
| cheap_phys − obs_dhr_phys | 6 | 1 | -0.0289 ± 0.0025 * |


### Check decomposition, arm 4 (diagnostic; **not** a gate result)

| check set | persistence | σ_map | ρ | Δ = 0 null | Δ = 10 | false exclusion | detection on actionable slots |
|---|---|---|---|---|---|---|---|
| default | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0013 ± 0.0002 | 0.0008 ± 0.0002 | 0.9716 ± 0.0025 |
| default | 3 | 2 | 0.5 | 0.0004 ± 0.0001 | 0.0014 ± 0.0002 | 0.0008 ± 0.0002 | 0.9324 ± 0.0092 |
| default | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0037 ± 0.0005 | 0.0008 ± 0.0002 | 0.9625 ± 0.0051 |
| default | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0026 ± 0.0005 | 0.0022 ± 0.0005 | 0.8501 ± 0.0102 |
| default | 3 | 4 | 0.5 | 0.0004 ± 0.0001 | 0.0063 ± 0.0008 | 0.0022 ± 0.0005 | 0.4023 ± 0.0405 |
| default | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0242 ± 0.0026 | 0.0022 ± 0.0005 | 0.5288 ± 0.0457 |
| default | 3 | 6 | 0 | 0.0004 ± 0.0001 | 0.0042 ± 0.0007 | 0.0030 ± 0.0007 | 0.8104 ± 0.0083 |
| default | 3 | 6 | 0.5 | 0.0004 ± 0.0001 | 0.0096 ± 0.0008 | 0.0030 ± 0.0007 | 0.2193 ± 0.0245 |
| default | 3 | 6 | 1 | 0.0004 ± 0.0001 | 0.0312 ± 0.0028 | 0.0030 ± 0.0007 | 0.2201 ± 0.0483 |
| map | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0007 ± 0.0001 | 0.0008 ± 0.0002 | 0.9160 ± 0.0116 |
| map | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0037 ± 0.0005 | 0.0008 ± 0.0002 | 0.9625 ± 0.0051 |
| map | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0026 ± 0.0005 | 0.0022 ± 0.0005 | 0.3040 ± 0.0423 |
| map | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0242 ± 0.0026 | 0.0022 ± 0.0005 | 0.5288 ± 0.0457 |
| neighbour | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0016 ± 0.0002 | 0.0000 ± 0.0000 | 0.8014 ± 0.0093 |
| neighbour | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0328 ± 0.0027 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| neighbour | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0030 ± 0.0007 | 0.0000 ± 0.0000 | 0.7969 ± 0.0071 |
| neighbour | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0334 ± 0.0028 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0019 ± 0.0003 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0328 ± 0.0027 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0031 ± 0.0006 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0334 ± 0.0028 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0019 ± 0.0003 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0328 ± 0.0027 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0031 ± 0.0006 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0334 ± 0.0028 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| default | 1 | 2 | 0 | 0.0004 ± 0.0001 | 0.0014 ± 0.0002 | 0.0183 ± 0.0013 | 0.9896 ± 0.0015 |
| default | 1 | 2 | 1 | 0.0004 ± 0.0001 | 0.0033 ± 0.0004 | 0.0183 ± 0.0013 | 0.9763 ± 0.0035 |
| default | 1 | 4 | 0 | 0.0005 ± 0.0001 | 0.0024 ± 0.0004 | 0.0185 ± 0.0013 | 0.9449 ± 0.0030 |
| default | 1 | 4 | 1 | 0.0005 ± 0.0001 | 0.0229 ± 0.0023 | 0.0185 ± 0.0013 | 0.5981 ± 0.0397 |


### Thresholds actually used (z = 3 × a standard deviation calibrated on the clean warm-up), with their spread across the 10 seeds

| σ_map | check | mean (dB) | min (dB) | max (dB) | sd (dB) |
|---|---|---|---|---|---|
| 2 | serving_reciprocity | 5.407 | 5.394 | 5.423 | 0.0105 |
| 2 | neighbour_reciprocity | 6.705 | 6.681 | 6.730 | 0.0162 |
| 2 | map | 6.705 | 6.558 | 6.914 | 0.1120 |
| 2 | rate | 5.327 | 5.169 | 5.535 | 0.1108 |
| 2 | calibrated sigma_C1 (dB) | 0.996 | 0.973 | 1.015 | 0.0120 |
| 2 | calibrated sigma_map (dB) | 2.001 | 1.957 | 2.076 | 0.0390 |
| 4 | serving_reciprocity | 5.407 | 5.394 | 5.423 | 0.0105 |
| 4 | neighbour_reciprocity | 6.705 | 6.681 | 6.730 | 0.0162 |
| 4 | map | 12.367 | 12.059 | 12.807 | 0.2392 |
| 4 | rate | 5.327 | 5.169 | 5.535 | 0.1108 |
| 4 | calibrated sigma_C1 (dB) | 0.996 | 0.973 | 1.015 | 0.0120 |
| 4 | calibrated sigma_map (dB) | 4.000 | 3.900 | 4.150 | 0.0807 |
| 6 | serving_reciprocity | 5.407 | 5.394 | 5.423 | 0.0105 |
| 6 | neighbour_reciprocity | 6.705 | 6.681 | 6.730 | 0.0162 |
| 6 | map | 18.247 | 17.782 | 18.911 | 0.3642 |
| 6 | rate | 5.327 | 5.169 | 5.535 | 0.1108 |
| 6 | calibrated sigma_C1 (dB) | 0.996 | 0.973 | 1.015 | 0.0120 |
| 6 | calibrated sigma_map (dB) | 6.000 | 5.847 | 6.224 | 0.1221 |
