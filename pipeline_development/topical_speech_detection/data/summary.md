# Dataset summary

Items: 1000 (850 real, 150 synthetic). Seed 2026.

## klimat by source

```
klimat         0    1   All
zrodlo                     
realna       426  424   850
syntetyczna   75   75   150
All          501  499  1000
```

## Real statements: klimat by pool and dictionary hits

```
klimat       0    1  All
pula hits               
A    0      71   59  130
     1      98  102  200
     2      41  109  150
     3+     30  140  170
B    1      61   11   72
     2       7    1    8
     3+      0    2    2
C    0      70    0   70
D    0      48    0   48
All        426  424  850
```

## Categories (real / synthetic)

```
zrodlo             realna  syntetyczna   All
kategoria                                   
N1_inne_znaczenie       3            5     8
N2_nazwy                4            5     9
N3_tlo                 46           20    66
N4_epitet              14           10    24
N5_smog_pogoda         13            8    21
N6_energetyka          43           12    55
N7_srodowisko          20            1    21
N8_inne               283           14   297
P1_nauka_skutki        17           22    39
P2_polityka           268           32   300
P3_negowanie           12           13    25
P4_watek_poboczny     127            8   135
All                   850          150  1000
```

## Labelling passes (real)

- Stage 4: 850 statements, 5 parallel Opus labellers; 334 marked `niska`.
- Stage 5: the 334 `niska` statements relabelled by 3 fresh Opus labellers under the borderline rules; `klimat` agreed with stage 4 for 233 / 334; the relabel is used.
- Hidden checks: 100 stage-4 `wysoka` statements relabelled blind; `klimat` agreed for 98 / 100; their stage 4 labels are kept.
- `pewnosc = niska` in the final labels: 168.
- `odniesienie_do_innego_mowcy = 1`: 318 real statements; the flag follows the stricter section 3 rule only for relabelled statements.
- Synthetic: 75 minimal pairs, blind check agreed on `klimat` for 150 / 150; categories follow the old P4 rule (`blind_kategoria` holds the blind labeller's).

## Exclusion check

- None of the 100 gold ids or 3 prompt-test ids is in the dataset (checked in `select_candidates.py`).

## Length (words)

```
             count   mean    std    min    25%    50%    75%      max
zrodlo                                                               
realna       850.0  412.0  584.0   48.0  148.0  220.0  496.0  11502.0
syntetyczna  150.0  228.0  216.0  123.0  142.0  154.0  169.0    909.0
```
