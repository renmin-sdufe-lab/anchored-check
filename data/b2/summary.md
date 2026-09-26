# WES majority-reach run b2: analysis summary

Runs: 3400 runs; mean 1.29 s, max 2.14 s per run (DESIGN 8 budget 20 s); 4392 s CPU in total

Gate setting: {'p': 0.2, 'delta': 10.0, 'rho': 1.0, 'sigma_map': 2.0, 'mode': 'trap', 'check_set': 'default', 'z': 3.0, 'ramp_slots': 1, 'persistence_slots': 3}


### Gate-2 table (PROTOCOL.md, evaluated literally on the attack-attributable rate per targeted slot)

| gate | criterion | numbers | verdict |
|---|---|---|---|
| **G2-a** | ρ = 1, Δ = 10, every σ_map: arm 3 ≥ 0.5 × arm 1 on the primary metric | σ_map = 2: arm 1 = 0.0415 ± 0.0037, arm 3 = 0.0327 ± 0.0027 (0.790 × arm 1, ≥ 0.5×); paired arm3 − 0.5·arm1 = 0.0120 ± 0.0010; null-corrected 0.0119 ± 0.0009; σ_map = 4: arm 1 = 0.0415 ± 0.0037, arm 3 = 0.0333 ± 0.0028 (0.804 × arm 1, ≥ 0.5×); paired arm3 − 0.5·arm1 = 0.0126 ± 0.0011; null-corrected 0.0125 ± 0.0011; σ_map = 6: arm 1 = 0.0415 ± 0.0037, arm 3 = 0.0340 ± 0.0030 (0.820 × arm 1, ≥ 0.5×); paired arm3 − 0.5·arm1 = 0.0132 ± 0.0012; null-corrected 0.0131 ± 0.0012 | **PASS** |
| **G2-b** | ρ = 1, Δ = 10, σ_map = 2, step: arm 4 ≤ 0.2 × arm 3 with the CI excluding the boundary **and** false exclusion ≤ 0.05 | arm 3 = 0.0327 ± 0.0027; arm 4 = 0.0037 ± 0.0005 (0.1129 × arm 3); paired arm4 − 0.2·arm3 = -0.0029 ± 0.0005 (CI wholly below 0: yes); null-corrected -0.0032 ± 0.0006; false exclusion = 0.0008 ± 0.0002 (≤ 0.05: yes). σ_map = 4 (reported): arm 3 = 0.0333 ± 0.0028, arm 4 = 0.0243 ± 0.0026 (0.727 × arm 3); σ_map = 6 (reported): arm 3 = 0.0340 ± 0.0030, arm 4 = 0.0312 ± 0.0027 (0.917 × arm 3) | **PASS** |
| **G2-c** | at Δ = 0, arms 4 and 5c against arm 1: `rsrp_deficit` not worse by more than 0.5 dB and `outage_share` not worse by more than 10 % relative | rsrp_deficit arm1 = 0.0499 ± 0.0039, obs_dhr_phys = 0.0642 ± 0.0043, paired 0.0143 ± 0.0032 (≤ +0.5 dB: yes); outage_share arm1 = 0.0000 ± 0.0000, obs_dhr_phys = 0.0000 ± 0.0000, paired 0.0000 ± 0.0000 (≤ +10 % relative: yes); missed handovers / UE-slot obs_dhr_phys = 0.0005 ± 0.0001 at Δ = 0 and 0.0008 ± 0.0001 under attack (reported, PROTOCOL.md sets no threshold); rsrp_deficit arm1 = 0.0499 ± 0.0039, cheap_phys = 0.1130 ± 0.0113, paired 0.0632 ± 0.0118 (≤ +0.5 dB: yes); outage_share arm1 = 0.0000 ± 0.0000, cheap_phys = 0.0000 ± 0.0000, paired 0.0000 ± 0.0000 (≤ +10 % relative: yes); missed handovers / UE-slot cheap_phys = 0.0010 ± 0.0001 at Δ = 0 and 0.0010 ± 0.0002 under attack (reported, PROTOCOL.md sets no threshold) | **PASS** |


**G2-a and G2-b pass** → in the specification's own words: *"G2-a and G2-b pass → the paper is 'what anchors the check', with σ_map the design parameter and the ramp the boundary."*


### Δ = 0 null control (attacker present, falsification zero; σ_map = 2)

| arm | attack-attributable success / targeted slot | attack-attributable success / opportunity | actionable share (with TTT) | false exclusion (clean UE-slots) | RSRP deficit (dB) | outage share | throughput proxy |
|---|---|---|---|---|---|---|---|
| 1 single (C1) | 0.0006 ± 0.0002 | 0.0021 ± 0.0031 | 0.0056 ± 0.0010 | 0.0000 ± 0.0000 | 0.0499 ± 0.0039 | 0.0000 ± 0.0000 | 1.3584 ± 0.0404 |
| 2' model DHR (3 families on C1) | 0.0003 ± 0.0001 | 0.0009 ± 0.0008 | 0.0405 ± 0.0104 | 0.0000 ± 0.0000 | 0.4826 ± 0.0421 | 0.0000 ± 0.0000 | 1.2933 ± 0.0373 |
| 3 obs DHR (C1, N, C4) | 0.0004 ± 0.0001 | 0.0028 ± 0.0033 | 0.0072 ± 0.0013 | 0.0000 ± 0.0000 | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4 obs DHR + physics | 0.0004 ± 0.0001 | 0.0028 ± 0.0033 | 0.0072 ± 0.0013 | 0.0008 ± 0.0002 | 0.0642 ± 0.0043 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4d obs DHR + dithered physics | 0.0004 ± 0.0001 | 0.0028 ± 0.0033 | 0.0072 ± 0.0013 | 0.0011 ± 0.0002 | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 5c cheap physics (C1, C4) | 0.0002 ± 0.0001 | 0.0016 ± 0.0019 | 0.0120 ± 0.0031 | 0.0009 ± 0.0002 | 0.1130 ± 0.0113 | 0.0000 ± 0.0000 | 1.3515 ± 0.0415 |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |


### Headline metrics at the gate setting (p = 0.2, Δ = 10 dB, ρ = 1, σ_map = 2 dB, trap; mean ± 95 % CI)

| arm | attack-attributable success / targeted slot | attack-attributable success / opportunity | raw success / targeted slot | actionable share (with TTT) | false exclusion (clean UE-slots) | throughput proxy |
|---|---|---|---|---|---|---|
| 1 single (C1) | 0.0415 ± 0.0037 | 0.5346 ± 0.0174 | 0.0472 ± 0.0043 | 0.0728 ± 0.0067 | 0.0000 ± 0.0000 | 1.3535 ± 0.0437 |
| 2' model DHR (3 families on C1) | 0.0133 ± 0.0016 | 0.0440 ± 0.0063 | 0.0155 ± 0.0019 | 0.2809 ± 0.0275 | 0.0000 ± 0.0000 | 1.2803 ± 0.0408 |
| 3 obs DHR (C1, N, C4) | 0.0327 ± 0.0027 | 0.2967 ± 0.0152 | 0.0359 ± 0.0031 | 0.1090 ± 0.0113 | 0.0000 ± 0.0000 | 1.3541 ± 0.0442 |
| 4 obs DHR + physics | 0.0037 ± 0.0005 | 0.0125 ± 0.0018 | 0.0055 ± 0.0008 | 0.2927 ± 0.0273 | 0.0008 ± 0.0002 | 1.3517 ± 0.0416 |
| 4d obs DHR + dithered physics | 0.0064 ± 0.0012 | 0.0235 ± 0.0047 | 0.0084 ± 0.0014 | 0.2695 ± 0.0251 | 0.0011 ± 0.0002 | 1.3518 ± 0.0432 |
| 5c cheap physics (C1, C4) | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0028 ± 0.0003 | 0.3065 ± 0.0284 | 0.0009 ± 0.0002 | 1.3493 ± 0.0409 |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a | n/a | n/a | n/a |


### attack-attributable success / targeted slot over σ_map × ρ (Δ = 10 dB, trap)

| arm | σ_map | ρ = 0 | ρ = 0.5 | ρ = 1 | Δ = 0 null |
|---|---|---|---|---|---|
| 1 single (C1) | 2 | 0.0415 ± 0.0037 | 0.0415 ± 0.0037 | 0.0415 ± 0.0037 | 0.0006 ± 0.0002 |
| 1 single (C1) | 4 | 0.0415 ± 0.0037 | 0.0415 ± 0.0037 | 0.0415 ± 0.0037 | 0.0006 ± 0.0002 |
| 1 single (C1) | 6 | 0.0415 ± 0.0037 | 0.0415 ± 0.0037 | 0.0415 ± 0.0037 | 0.0006 ± 0.0002 |
| 3 obs DHR (C1, N, C4) | 2 | 0.0019 ± 0.0003 | 0.0067 ± 0.0007 | 0.0327 ± 0.0027 | 0.0004 ± 0.0001 |
| 3 obs DHR (C1, N, C4) | 4 | 0.0031 ± 0.0006 | 0.0083 ± 0.0008 | 0.0333 ± 0.0028 | 0.0004 ± 0.0001 |
| 3 obs DHR (C1, N, C4) | 6 | 0.0040 ± 0.0007 | 0.0097 ± 0.0010 | 0.0340 ± 0.0030 | 0.0004 ± 0.0001 |
| 4 obs DHR + physics | 2 | 0.0013 ± 0.0002 | 0.0014 ± 0.0002 | 0.0037 ± 0.0005 | 0.0004 ± 0.0001 |
| 4 obs DHR + physics | 4 | 0.0026 ± 0.0005 | 0.0063 ± 0.0008 | 0.0243 ± 0.0026 | 0.0004 ± 0.0001 |
| 4 obs DHR + physics | 6 | 0.0042 ± 0.0007 | 0.0095 ± 0.0008 | 0.0312 ± 0.0027 | 0.0004 ± 0.0001 |
| 5c cheap physics (C1, C4) | 2 | 0.0013 ± 0.0002 | 0.0013 ± 0.0002 | 0.0013 ± 0.0002 | 0.0002 ± 0.0001 |
| 5c cheap physics (C1, C4) | 4 | 0.0020 ± 0.0003 | 0.0020 ± 0.0003 | 0.0020 ± 0.0003 | 0.0002 ± 0.0001 |
| 5c cheap physics (C1, C4) | 6 | 0.0021 ± 0.0003 | 0.0021 ± 0.0003 | 0.0021 ± 0.0003 | 0.0002 ± 0.0001 |


### attack-attributable success / targeted slot against Δ (ρ = 1, trap)

| arm | σ_map | Δ = 0 (null) | Δ = 6 dB | Δ = 10 dB | Δ = 15 dB |
|---|---|---|---|---|---|
| 1 single (C1) | 2 | 0.0006 ± 0.0002 | 0.0151 ± 0.0011 | 0.0415 ± 0.0037 | 0.0847 ± 0.0054 |
| 1 single (C1) | 4 | 0.0006 ± 0.0002 | 0.0151 ± 0.0011 | 0.0415 ± 0.0037 | 0.0847 ± 0.0054 |
| 1 single (C1) | 6 | 0.0006 ± 0.0002 | 0.0151 ± 0.0011 | 0.0415 ± 0.0037 | 0.0847 ± 0.0054 |
| 2' model DHR (3 families on C1) | 2 | 0.0003 ± 0.0001 | 0.0058 ± 0.0006 | 0.0133 ± 0.0016 | 0.0189 ± 0.0021 |
| 2' model DHR (3 families on C1) | 4 | 0.0003 ± 0.0001 | 0.0058 ± 0.0006 | 0.0133 ± 0.0016 | 0.0189 ± 0.0021 |
| 2' model DHR (3 families on C1) | 6 | 0.0003 ± 0.0001 | 0.0058 ± 0.0006 | 0.0133 ± 0.0016 | 0.0189 ± 0.0021 |
| 3 obs DHR (C1, N, C4) | 2 | 0.0004 ± 0.0001 | 0.0096 ± 0.0005 | 0.0327 ± 0.0027 | 0.0742 ± 0.0050 |
| 3 obs DHR (C1, N, C4) | 4 | 0.0004 ± 0.0001 | 0.0103 ± 0.0007 | 0.0333 ± 0.0028 | 0.0747 ± 0.0049 |
| 3 obs DHR (C1, N, C4) | 6 | 0.0004 ± 0.0001 | 0.0109 ± 0.0007 | 0.0340 ± 0.0030 | 0.0754 ± 0.0053 |
| 4 obs DHR + physics | 2 | 0.0004 ± 0.0001 | 0.0075 ± 0.0008 | 0.0037 ± 0.0005 | 0.0017 ± 0.0002 |
| 4 obs DHR + physics | 4 | 0.0004 ± 0.0001 | 0.0099 ± 0.0008 | 0.0243 ± 0.0026 | 0.0147 ± 0.0019 |
| 4 obs DHR + physics | 6 | 0.0004 ± 0.0001 | 0.0107 ± 0.0008 | 0.0312 ± 0.0027 | 0.0478 ± 0.0048 |
| 4d obs DHR + dithered physics | 2 | 0.0004 ± 0.0001 | 0.0081 ± 0.0008 | 0.0064 ± 0.0012 | 0.0017 ± 0.0002 |
| 4d obs DHR + dithered physics | 4 | 0.0004 ± 0.0001 | 0.0100 ± 0.0008 | 0.0283 ± 0.0026 | 0.0279 ± 0.0032 |
| 4d obs DHR + dithered physics | 6 | 0.0004 ± 0.0001 | 0.0108 ± 0.0008 | 0.0327 ± 0.0026 | 0.0626 ± 0.0050 |
| 5c cheap physics (C1, C4) | 2 | 0.0002 ± 0.0001 | 0.0013 ± 0.0002 | 0.0013 ± 0.0002 | 0.0013 ± 0.0002 |
| 5c cheap physics (C1, C4) | 4 | 0.0002 ± 0.0001 | 0.0017 ± 0.0003 | 0.0020 ± 0.0003 | 0.0019 ± 0.0003 |
| 5c cheap physics (C1, C4) | 6 | 0.0002 ± 0.0001 | 0.0017 ± 0.0002 | 0.0021 ± 0.0003 | 0.0022 ± 0.0003 |
| 2p param DHR (3 A3 variants on C1) | 2 | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 4 | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 6 | n/a | n/a | n/a | n/a |


### Primary and secondary attack metrics (σ_map = 2, Δ = 10, trap)

| arm | ρ | attack-attributable success / targeted slot | attack-attributable success / opportunity | attack-attributable success / instant opportunity |
|---|---|---|---|---|
| 1 single (C1) | 0 | 0.0415 ± 0.0037 | 0.5346 ± 0.0174 | 0.1310 ± 0.0025 |
| 1 single (C1) | 0.5 | 0.0415 ± 0.0037 | 0.5346 ± 0.0174 | 0.1310 ± 0.0025 |
| 1 single (C1) | 1 | 0.0415 ± 0.0037 | 0.5346 ± 0.0174 | 0.1310 ± 0.0025 |
| 2' model DHR (3 families on C1) | 0 | 0.0133 ± 0.0016 | 0.0440 ± 0.0063 | 0.0330 ± 0.0035 |
| 2' model DHR (3 families on C1) | 0.5 | 0.0133 ± 0.0016 | 0.0440 ± 0.0063 | 0.0330 ± 0.0035 |
| 2' model DHR (3 families on C1) | 1 | 0.0133 ± 0.0016 | 0.0440 ± 0.0063 | 0.0330 ± 0.0035 |
| 3 obs DHR (C1, N, C4) | 0 | 0.0019 ± 0.0003 | 0.0064 ± 0.0012 | 0.0050 ± 0.0009 |
| 3 obs DHR (C1, N, C4) | 0.5 | 0.0067 ± 0.0007 | 0.0258 ± 0.0027 | 0.0186 ± 0.0016 |
| 3 obs DHR (C1, N, C4) | 1 | 0.0327 ± 0.0027 | 0.2967 ± 0.0152 | 0.1035 ± 0.0018 |
| 4 obs DHR + physics | 0 | 0.0013 ± 0.0002 | 0.0043 ± 0.0006 | 0.0034 ± 0.0005 |
| 4 obs DHR + physics | 0.5 | 0.0014 ± 0.0002 | 0.0046 ± 0.0008 | 0.0036 ± 0.0006 |
| 4 obs DHR + physics | 1 | 0.0037 ± 0.0005 | 0.0125 ± 0.0018 | 0.0098 ± 0.0013 |
| 4d obs DHR + dithered physics | 0 | 0.0013 ± 0.0002 | 0.0043 ± 0.0007 | 0.0034 ± 0.0005 |
| 4d obs DHR + dithered physics | 0.5 | 0.0019 ± 0.0004 | 0.0063 ± 0.0012 | 0.0050 ± 0.0009 |
| 4d obs DHR + dithered physics | 1 | 0.0064 ± 0.0012 | 0.0235 ± 0.0047 | 0.0173 ± 0.0029 |
| 5c cheap physics (C1, C4) | 0 | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0035 ± 0.0005 |
| 5c cheap physics (C1, C4) | 0.5 | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0035 ± 0.0005 |
| 5c cheap physics (C1, C4) | 1 | 0.0013 ± 0.0002 | 0.0044 ± 0.0006 | 0.0035 ± 0.0005 |
| 2p param DHR (3 A3 variants on C1) | 0 | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 0.5 | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 1 | n/a | n/a | n/a |


### Harm and quality of service: Δ = 0 (cost of the defence) and Δ = 10, ρ = 1 (its value); σ_map = 2

| arm | Δ | RSRP deficit (dB) | outage share | wrong-cell share | wrong handovers / handover | ping-pongs / handover | missed handovers / UE-slot | missed handovers / oracle handover | handovers / UE-slot | trusted-channel fallback rate | throughput proxy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 single (C1) | 0 (null) | 0.0499 ± 0.0039 | 0.0000 ± 0.0000 | 0.0077 ± 0.0005 | 0.0345 ± 0.0073 | 0.0445 ± 0.0099 | 0.0003 ± 0.0000 | 0.0732 ± 0.0075 | 0.0037 ± 0.0002 | 0.0000 ± 0.0000 | 1.3584 ± 0.0404 |
| 1 single (C1) | 10 | 0.0674 ± 0.0048 | 0.0000 ± 0.0000 | 0.0104 ± 0.0007 | 0.5409 ± 0.0141 | 0.6061 ± 0.0239 | 0.0011 ± 0.0002 | 0.1829 ± 0.0256 | 0.0137 ± 0.0009 | 0.0000 ± 0.0000 | 1.3535 ± 0.0437 |
| 2' model DHR (3 families on C1) | 0 (null) | 0.4826 ± 0.0421 | 0.0000 ± 0.0000 | 0.0504 ± 0.0034 | 0.0294 ± 0.0061 | 0.0196 ± 0.0058 | 0.0025 ± 0.0002 | 0.4858 ± 0.0209 | 0.0028 ± 0.0001 | 0.0000 ± 0.0000 | 1.2933 ± 0.0373 |
| 2' model DHR (3 families on C1) | 10 | 0.5692 ± 0.0577 | 0.0000 ± 0.0000 | 0.0597 ± 0.0060 | 0.3922 ± 0.0175 | 0.2971 ± 0.0183 | 0.0031 ± 0.0004 | 0.5077 ± 0.0263 | 0.0060 ± 0.0005 | 0.0000 ± 0.0000 | 1.2803 ± 0.0408 |
| 3 obs DHR (C1, N, C4) | 0 (null) | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 0.0103 ± 0.0008 | 0.0300 ± 0.0098 | 0.0383 ± 0.0071 | 0.0005 ± 0.0001 | 0.1262 ± 0.0187 | 0.0035 ± 0.0002 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 3 obs DHR (C1, N, C4) | 10 | 0.0738 ± 0.0047 | 0.0000 ± 0.0000 | 0.0118 ± 0.0009 | 0.5333 ± 0.0131 | 0.5482 ± 0.0156 | 0.0010 ± 0.0001 | 0.1874 ± 0.0189 | 0.0109 ± 0.0007 | 0.0000 ± 0.0000 | 1.3541 ± 0.0442 |
| 4 obs DHR + physics | 0 (null) | 0.0642 ± 0.0043 | 0.0000 ± 0.0000 | 0.0103 ± 0.0008 | 0.0300 ± 0.0098 | 0.0383 ± 0.0071 | 0.0005 ± 0.0001 | 0.1265 ± 0.0188 | 0.0035 ± 0.0002 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4 obs DHR + physics | 10 | 0.0900 ± 0.0121 | 0.0000 ± 0.0000 | 0.0135 ± 0.0015 | 0.1616 ± 0.0177 | 0.1051 ± 0.0159 | 0.0008 ± 0.0001 | 0.1941 ± 0.0291 | 0.0042 ± 0.0003 | 0.0000 ± 0.0000 | 1.3517 ± 0.0416 |
| 4d obs DHR + dithered physics | 0 (null) | 0.0641 ± 0.0043 | 0.0000 ± 0.0000 | 0.0103 ± 0.0008 | 0.0300 ± 0.0098 | 0.0387 ± 0.0071 | 0.0005 ± 0.0001 | 0.1268 ± 0.0183 | 0.0035 ± 0.0002 | 0.0000 ± 0.0000 | 1.3553 ± 0.0402 |
| 4d obs DHR + dithered physics | 10 | 0.0926 ± 0.0120 | 0.0000 ± 0.0000 | 0.0139 ± 0.0014 | 0.2375 ± 0.0282 | 0.1751 ± 0.0314 | 0.0008 ± 0.0001 | 0.1941 ± 0.0287 | 0.0049 ± 0.0004 | 0.0000 ± 0.0000 | 1.3518 ± 0.0432 |
| 5c cheap physics (C1, C4) | 0 (null) | 0.1130 ± 0.0113 | 0.0000 ± 0.0000 | 0.0176 ± 0.0020 | 0.0225 ± 0.0064 | 0.0253 ± 0.0088 | 0.0010 ± 0.0001 | 0.2285 ± 0.0322 | 0.0032 ± 0.0002 | 0.0008 ± 0.0002 | 1.3515 ± 0.0415 |
| 5c cheap physics (C1, C4) | 10 | 0.1169 ± 0.0128 | 0.0000 ± 0.0000 | 0.0181 ± 0.0023 | 0.0758 ± 0.0118 | 0.0314 ± 0.0085 | 0.0010 ± 0.0002 | 0.2442 ± 0.0367 | 0.0034 ± 0.0002 | 0.1090 ± 0.0057 | 1.3493 ± 0.0409 |
| 2p param DHR (3 A3 variants on C1) | 0 (null) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 10 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |


### Paired harm differences against arm 1 (`*` marks a CI excluding zero)

| arm | Δ | RSRP deficit (dB) | outage share | missed handovers / UE-slot |
|---|---|---|---|---|
| 2' model DHR (3 families on C1) | 0 (null) | 0.4327 ± 0.0407 * | 0.0000 ± 0.0000 | 0.0022 ± 0.0002 * |
| 2' model DHR (3 families on C1) | 10 | 0.5019 ± 0.0576 * | 0.0000 ± 0.0000 | 0.0020 ± 0.0004 * |
| 3 obs DHR (C1, N, C4) | 0 (null) | 0.0143 ± 0.0032 * | 0.0000 ± 0.0000 | 0.0002 ± 0.0001 * |
| 3 obs DHR (C1, N, C4) | 10 | 0.0064 ± 0.0037 * | 0.0000 ± 0.0000 | -0.0001 ± 0.0001 * |
| 4 obs DHR + physics | 0 (null) | 0.0143 ± 0.0032 * | 0.0000 ± 0.0000 | 0.0002 ± 0.0001 * |
| 4 obs DHR + physics | 10 | 0.0226 ± 0.0134 * | 0.0000 ± 0.0000 | -0.0003 ± 0.0002 * |
| 4d obs DHR + dithered physics | 0 (null) | 0.0143 ± 0.0033 * | 0.0000 ± 0.0000 | 0.0002 ± 0.0001 * |
| 4d obs DHR + dithered physics | 10 | 0.0252 ± 0.0128 * | 0.0000 ± 0.0000 | -0.0003 ± 0.0002 * |
| 5c cheap physics (C1, C4) | 0 (null) | 0.0632 ± 0.0118 * | 0.0000 ± 0.0000 | 0.0007 ± 0.0002 * |
| 5c cheap physics (C1, C4) | 10 | 0.0495 ± 0.0139 * | 0.0000 ± 0.0000 | -0.0001 ± 0.0003 |
| 2p param DHR (3 A3 variants on C1) | 0 (null) | n/a | n/a | n/a |
| 2p param DHR (3 A3 variants on C1) | 10 | n/a | n/a | n/a |


### Apparatus diagnostics at the gate setting

| arm | majority reachable | actionable share (with TTT) | actionable share (instantaneous) | falsified-channel exclusion on actionable slots | false exclusion (clean UE-slots) | voting channels |
|---|---|---|---|---|---|---|
| 1 single (C1) | yes | 0.0728 ± 0.0067 | 0.3126 ± 0.0259 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 |
| 2' model DHR (3 families on C1) | yes | 0.2809 ± 0.0275 | 0.3961 ± 0.0318 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 3.0000 ± 0.0000 |
| 3 obs DHR (C1, N, C4) | yes | 0.1090 ± 0.0113 | 0.3160 ± 0.0266 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 3.0000 ± 0.0000 |
| 4 obs DHR + physics | yes | 0.2927 ± 0.0273 | 0.3790 ± 0.0321 | 0.9622 ± 0.0053 | 0.0008 ± 0.0002 | 2.8891 ± 0.0061 |
| 4d obs DHR + dithered physics | yes | 0.2695 ± 0.0251 | 0.3678 ± 0.0312 | 0.9223 ± 0.0090 | 0.0011 ± 0.0002 | 2.8980 ± 0.0053 |
| 5c cheap physics (C1, C4) | no | 0.3065 ± 0.0284 | 0.3847 ± 0.0331 | 0.9128 ± 0.0120 | 0.0009 ± 0.0002 | 1.8910 ± 0.0057 |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a | n/a | n/a | n/a |


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
| 1 single (C1) | 0.0415 ± 0.0037 | 0.0006 ± 0.0002 | 0.5409 ± 0.0141 | 0.0049 ± 0.0005 | 0.0008 ± 0.0002 | 0.1633 ± 0.0127 |
| 2' model DHR (3 families on C1) | 0.0133 ± 0.0016 | 0.0003 ± 0.0001 | 0.3922 ± 0.0175 | 0.0037 ± 0.0006 | 0.0006 ± 0.0001 | 0.1586 ± 0.0163 |
| 3 obs DHR (C1, N, C4) | 0.0019 ± 0.0003 | 0.0004 ± 0.0001 | 0.0731 ± 0.0139 | 0.0016 ± 0.0002 | 0.0005 ± 0.0001 | 0.0653 ± 0.0109 |
| 4 obs DHR + physics | 0.0013 ± 0.0002 | 0.0004 ± 0.0001 | 0.0774 ± 0.0116 | 0.0006 ± 0.0001 | 0.0005 ± 0.0001 | 0.0388 ± 0.0086 |
| 4d obs DHR + dithered physics | 0.0013 ± 0.0002 | 0.0004 ± 0.0001 | 0.0772 ± 0.0114 | 0.0007 ± 0.0001 | 0.0005 ± 0.0001 | 0.0413 ± 0.0094 |
| 5c cheap physics (C1, C4) | 0.0013 ± 0.0002 | 0.0002 ± 0.0001 | 0.0758 ± 0.0118 | 0.0018 ± 0.0002 | 0.0003 ± 0.0001 | 0.0715 ± 0.0108 |
| 2p param DHR (3 A3 variants on C1) | n/a | n/a | n/a | n/a | n/a | n/a |


### Sticky ramp attacker (DESIGN 5; reported, not gated)

| arm | σ_map | ramp = 1 slot(s) | ramp = 10 slot(s) | ramp = 20 slot(s) | detection, ramp = 1 | detection, ramp = 10 | detection, ramp = 20 | actionable share, ramp = 1 | actionable share, ramp = 10 | actionable share, ramp = 20 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 single (C1) | 2 | 0.0415 ± 0.0037 | 0.0261 ± 0.0021 | 0.0185 ± 0.0015 | 0.000 | 0.000 | 0.000 | 0.073 | 0.056 | 0.046 |
| 1 single (C1) | 4 | 0.0415 ± 0.0037 | 0.0261 ± 0.0021 | 0.0185 ± 0.0015 | 0.000 | 0.000 | 0.000 | 0.073 | 0.056 | 0.046 |
| 3 obs DHR (C1, N, C4) | 2 | 0.0327 ± 0.0027 | 0.0209 ± 0.0016 | 0.0150 ± 0.0012 | 0.000 | 0.000 | 0.000 | 0.109 | 0.096 | 0.082 |
| 3 obs DHR (C1, N, C4) | 4 | 0.0333 ± 0.0028 | 0.0214 ± 0.0017 | 0.0153 ± 0.0012 | 0.000 | 0.000 | 0.000 | 0.107 | 0.093 | 0.080 |
| 4 obs DHR + physics | 2 | 0.0037 ± 0.0005 | 0.0040 ± 0.0005 | 0.0041 ± 0.0006 | 0.962 | 0.953 | 0.931 | 0.293 | 0.266 | 0.233 |
| 4 obs DHR + physics | 4 | 0.0243 ± 0.0026 | 0.0174 ± 0.0018 | 0.0131 ± 0.0013 | 0.528 | 0.456 | 0.404 | 0.169 | 0.136 | 0.111 |


### Cost per arm at the gate setting (DESIGN 6: reported, not gated)

| arm | measurement bytes (B/UE/s) | over-the-air bytes (B/UE/s) | compute units/decision | OTA bytes / arm 1 | compute / arm 1 |
|---|---|---|---|---|---|
| 1 single (C1) | 400.0 | 400.0 | 1.0 | 1.00x | 1.00x |
| 2' model DHR (3 families on C1) | 400.0 | 400.0 | 3.0 | 1.00x | 3.00x |
| 3 obs DHR (C1, N, C4) | 4200.0 | 4000.0 | 3.0 | 10.00x | 3.00x |
| 4 obs DHR + physics | 4200.0 | 4000.0 | 7.0 | 10.00x | 7.00x |
| 4d obs DHR + dithered physics | 4200.0 | 4000.0 | 7.0 | 10.00x | 7.00x |
| 5c cheap physics (C1, C4) | 600.0 | 400.0 | 5.0 | 1.00x | 5.00x |
| 2p param DHR (3 A3 variants on C1) | nan | nan | nan | nanx | nanx |


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
| obs_dhr_phys − obs_dhr | 2 | 1 | -0.0290 ± 0.0025 * |
| obs_dhr_phys_dither − obs_dhr_phys | 2 | 1 | 0.0027 ± 0.0007 * |
| cheap_phys − obs_dhr_phys | 2 | 1 | -0.0022 ± 0.0005 * |
| model_dhr3 − single | 4 | 0 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 4 | 0 | -0.0383 ± 0.0034 * |
| obs_dhr_phys − obs_dhr | 4 | 0 | -0.0005 ± 0.0003 * |
| obs_dhr_phys_dither − obs_dhr_phys | 4 | 0 | 0.0002 ± 0.0002 * |
| cheap_phys − obs_dhr_phys | 4 | 0 | -0.0004 ± 0.0003 * |
| model_dhr3 − single | 4 | 1 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 4 | 1 | -0.0080 ± 0.0012 * |
| obs_dhr_phys − obs_dhr | 4 | 1 | -0.0091 ± 0.0012 * |
| obs_dhr_phys_dither − obs_dhr_phys | 4 | 1 | 0.0040 ± 0.0008 * |
| cheap_phys − obs_dhr_phys | 4 | 1 | -0.0221 ± 0.0023 * |
| model_dhr3 − single | 6 | 0 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 6 | 0 | -0.0373 ± 0.0033 * |
| obs_dhr_phys − obs_dhr | 6 | 0 | 0.0002 ± 0.0006 |
| obs_dhr_phys_dither − obs_dhr_phys | 6 | 0 | 0.0004 ± 0.0002 * |
| cheap_phys − obs_dhr_phys | 6 | 0 | -0.0019 ± 0.0007 * |
| model_dhr3 − single | 6 | 1 | -0.0280 ± 0.0030 * |
| obs_dhr − single | 6 | 1 | -0.0073 ± 0.0010 * |
| obs_dhr_phys − obs_dhr | 6 | 1 | -0.0028 ± 0.0009 * |
| obs_dhr_phys_dither − obs_dhr_phys | 6 | 1 | 0.0015 ± 0.0006 * |
| cheap_phys − obs_dhr_phys | 6 | 1 | -0.0289 ± 0.0025 * |


### Check decomposition, arm 4 (diagnostic; **not** a gate result)

| check set | persistence | σ_map | ρ | Δ = 0 null | Δ = 10 | false exclusion | detection on actionable slots |
|---|---|---|---|---|---|---|---|
| default | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0013 ± 0.0002 | 0.0008 ± 0.0002 | 0.9718 ± 0.0021 |
| default | 3 | 2 | 0.5 | 0.0004 ± 0.0001 | 0.0014 ± 0.0002 | 0.0008 ± 0.0002 | 0.9324 ± 0.0088 |
| default | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0037 ± 0.0005 | 0.0008 ± 0.0002 | 0.9622 ± 0.0053 |
| default | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0026 ± 0.0005 | 0.0022 ± 0.0005 | 0.8508 ± 0.0102 |
| default | 3 | 4 | 0.5 | 0.0004 ± 0.0001 | 0.0063 ± 0.0008 | 0.0022 ± 0.0005 | 0.4028 ± 0.0403 |
| default | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0243 ± 0.0026 | 0.0022 ± 0.0005 | 0.5282 ± 0.0461 |
| default | 3 | 6 | 0 | 0.0004 ± 0.0001 | 0.0042 ± 0.0007 | 0.0030 ± 0.0007 | 0.8111 ± 0.0080 |
| default | 3 | 6 | 0.5 | 0.0004 ± 0.0001 | 0.0095 ± 0.0008 | 0.0030 ± 0.0007 | 0.2197 ± 0.0245 |
| default | 3 | 6 | 1 | 0.0004 ± 0.0001 | 0.0312 ± 0.0027 | 0.0030 ± 0.0007 | 0.2189 ± 0.0500 |
| map | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0007 ± 0.0001 | 0.0008 ± 0.0002 | 0.9168 ± 0.0098 |
| map | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0037 ± 0.0005 | 0.0008 ± 0.0002 | 0.9622 ± 0.0053 |
| map | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0026 ± 0.0005 | 0.0022 ± 0.0005 | 0.3055 ± 0.0418 |
| map | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0243 ± 0.0026 | 0.0022 ± 0.0005 | 0.5282 ± 0.0461 |
| neighbour | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0016 ± 0.0002 | 0.0000 ± 0.0000 | 0.8019 ± 0.0093 |
| neighbour | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0327 ± 0.0027 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| neighbour | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0030 ± 0.0007 | 0.0000 ± 0.0000 | 0.7975 ± 0.0074 |
| neighbour | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0333 ± 0.0028 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0019 ± 0.0003 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0327 ± 0.0027 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0031 ± 0.0006 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| rate | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0333 ± 0.0028 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 2 | 0 | 0.0004 ± 0.0001 | 0.0019 ± 0.0003 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 2 | 1 | 0.0004 ± 0.0001 | 0.0327 ± 0.0027 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 4 | 0 | 0.0004 ± 0.0001 | 0.0031 ± 0.0006 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| serving | 3 | 4 | 1 | 0.0004 ± 0.0001 | 0.0333 ± 0.0028 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| default | 1 | 2 | 0 | 0.0004 ± 0.0001 | 0.0014 ± 0.0002 | 0.0183 ± 0.0014 | 0.9897 ± 0.0015 |
| default | 1 | 2 | 1 | 0.0004 ± 0.0001 | 0.0033 ± 0.0004 | 0.0183 ± 0.0014 | 0.9761 ± 0.0037 |
| default | 1 | 4 | 0 | 0.0005 ± 0.0001 | 0.0024 ± 0.0004 | 0.0185 ± 0.0014 | 0.9451 ± 0.0030 |
| default | 1 | 4 | 1 | 0.0005 ± 0.0001 | 0.0229 ± 0.0023 | 0.0185 ± 0.0014 | 0.5973 ± 0.0402 |


### Thresholds actually used (z = 3 × a standard deviation calibrated on the clean warm-up), with their spread across the 10 seeds

| σ_map | check | mean (dB) | min (dB) | max (dB) | sd (dB) |
|---|---|---|---|---|---|
| 2 | serving_reciprocity | 5.409 | 5.342 | 5.503 | 0.0529 |
| 2 | neighbour_reciprocity | 6.701 | 6.667 | 6.732 | 0.0237 |
| 2 | map | 6.705 | 6.558 | 6.914 | 0.1120 |
| 2 | rate | 5.327 | 5.169 | 5.535 | 0.1108 |
| 2 | calibrated sigma_C1 (dB) | 0.996 | 0.973 | 1.015 | 0.0120 |
| 2 | calibrated sigma_map (dB) | 2.001 | 1.957 | 2.076 | 0.0390 |
| 4 | serving_reciprocity | 5.408 | 5.340 | 5.501 | 0.0529 |
| 4 | neighbour_reciprocity | 6.701 | 6.668 | 6.732 | 0.0238 |
| 4 | map | 12.367 | 12.059 | 12.807 | 0.2392 |
| 4 | rate | 5.327 | 5.169 | 5.535 | 0.1108 |
| 4 | calibrated sigma_C1 (dB) | 0.996 | 0.973 | 1.015 | 0.0120 |
| 4 | calibrated sigma_map (dB) | 4.000 | 3.900 | 4.150 | 0.0807 |
| 6 | serving_reciprocity | 5.410 | 5.341 | 5.500 | 0.0518 |
| 6 | neighbour_reciprocity | 6.701 | 6.668 | 6.733 | 0.0240 |
| 6 | map | 18.247 | 17.782 | 18.911 | 0.3642 |
| 6 | rate | 5.327 | 5.169 | 5.535 | 0.1108 |
| 6 | calibrated sigma_C1 (dB) | 0.996 | 0.973 | 1.015 | 0.0120 |
| 6 | calibrated sigma_map (dB) | 6.000 | 5.847 | 6.224 | 0.1221 |
