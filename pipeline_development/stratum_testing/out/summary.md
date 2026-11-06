# Warstwa 3: drugi klasyfikator

Warstwa 3 (model: nietematyczna): prawica 19274, reszta 23072.
Znane przeoczenia modelu (silver: klimat = 1 w warstwie 3): 14; silver: klimat = 0 w warstwie 3: 186. Dla nich Laya daje prawdopodobieństwo z cross-fittingu.
Gold w warstwie 3: 30 wypowiedzi.

| Drugi klasyfikator | 3a prawica | 3a reszta | 3b prawica | 3b reszta | złapane przeoczenia (silver 1) | fałszywe trafienia (silver 0) | gold w 3a |
|---|---:|---:|---:|---:|---:|---:|---:|
| regex_strict | 106 | 199 | 19168 | 22873 | 12 / 14 | 57 / 186 | 0 / 30 |
| regex_broad | 489 | 752 | 18785 | 22320 | 14 / 14 | 75 / 186 | 2 / 30 |
| laya ≥ 0.5 | 411 | 492 | 18863 | 22580 | 6 / 14 | 22 / 186 | 1 / 30 |
| laya ≥ 0.5 lub regex_strict | 495 | 665 | 18779 | 22407 | 13 / 14 | 64 / 186 | 1 / 30 |
| laya ≥ 0.3 | 511 | 620 | 18763 | 22452 | 6 / 14 | 25 / 186 | 1 / 30 |
| laya ≥ 0.3 lub regex_strict | 594 | 787 | 18680 | 22285 | 13 / 14 | 67 / 186 | 1 / 30 |
| laya ≥ 0.1 | 769 | 901 | 18505 | 22171 | 9 / 14 | 42 / 186 | 2 / 30 |
| laya ≥ 0.1 lub regex_strict | 845 | 1052 | 18429 | 22020 | 13 / 14 | 79 / 186 | 2 / 30 |

Silver w warstwie 3 pochodzi z pul wzbogaconych (B–D), więc odsetek fałszywych trafień na silver jest zawyżony względem całej warstwy; rozmiar 3a z tabeli jest właściwą miarą.
