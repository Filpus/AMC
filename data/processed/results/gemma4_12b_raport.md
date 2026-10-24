# Krok 9: zestawienie wyników (gemma4_12b)

Plik generowany przez `src/report.py` z plików w `data/processed/results/`; nie edytować ręcznie.

## Werdykt

**hipoteza niepotwierdzona**: różnica prawica − reszta po korekcie 35,2 pp, dolna granica jednostronnego 95% przedziału -11,2 pp (krok 7, bootstrap warstwowy próby gold standardu).

## 1. Wynik główny przed korektą i po korekcie

| grupa | bez korekty: odsetek wg modelu (%) | po korekcie: gold, krok 7 (%) [95% CI] |
|---|---|---|
| prawica | 6,8 | 55,1 [15,2; 97,2] |
| reszta | 3,7 | 19,9 [0,0; 62,6] |
| różnica (pp) | 3,1 | 35,2 [-21,1; 92,4] |

Krok 6 (etykiety modelu, logit, SE klastrowane po mówcy): β₁ = 0,635, SE = 0,240, 95% CI [0,164; 1,106], p jednostronne = 0,004; n = 1645 wypowiedzi, 285 mówców.

## 2. Wypowiedzi w mianowniku

| grupa | tematyczne wg modelu | sprzeczne wg modelu | tematyczne z golda (T̂) | sprzeczne z golda (Ĉ) |
|---|---|---|---|---|
| prawica | 888 | 60 | 266 | 146 |
| reszta | 757 | 28 | 258 | 51 |

Warunek rzadkości (≥ 100 tematycznych w grupie, ≥ 30 sprzecznych łącznie): spełniony.

## 3. Jakość etykiet modelu (krok 5, wagi warstw, 95% CI z bootstrapu)

| etap | miara | prawica | reszta |
|---|---|---|---|
| tematyczność | TPR | 1,000 [1,000; 1,000] | 1,000 [1,000; 1,000] |
| tematyczność | TNR | 0,969 [0,961; 0,979] | 0,979 [0,973; 0,987] |
| tematyczność | precyzja | 0,299 [0,109; 0,534] | 0,341 [0,145; 0,596] |
| tematyczność | F1 | 0,461 [0,197; 0,697] | 0,509 [0,253; 0,747] |
| werdykt (tematyczne wg modelu i golda) | TPR | 0,246 [0,109; 1,000] | 0,054 [0,000; 1,000] |
| werdykt (tematyczne wg modelu i golda) | TNR | 0,925 [0,000; 1,000] | 0,939 [0,776; 0,972] |
| werdykt (tematyczne wg modelu i golda) | precyzja | 0,800 [0,583; 1,000] | 0,182 [0,000; 0,444] |
| werdykt (tematyczne wg modelu i golda) | F1 | 0,376 [0,186; 0,938] | 0,084 [0,023; 0,545] |
| etykieta końcowa | TPR | 0,246 [0,109; 1,000] | 0,054 [0,000; 1,000] |
| etykieta końcowa | TNR | 0,999 [0,998; 0,999] | 0,999 [0,999; 0,999] |
| etykieta końcowa | precyzja | 0,600 [0,400; 0,800] | 0,100 [0,000; 0,250] |
| etykieta końcowa | F1 | 0,349 [0,175; 0,824] | 0,071 [0,022; 0,333] |

## 4. Odporność (krok 8, test z kroku 6 w wariantach)

| wariant | rodzaj | n | sprzeczne | β₁ | 95% CI | różnica wg modelu (pp) | β₁ / β₁ główne | kryterium |
|---|---|---|---|---|---|---|---|---|
| wynik główny (krok 6) | glowny | 1645 | 88 | 0,635 | [0,164; 1,106] | 3,1 | 1,00 | tak |
| bez Konfederacji (i Konfederacji KP) | plan | 1317 | 63 | 0,551 | [-0,004; 1,107] | 2,6 | 0,87 | tak |
| bez PiS (i RozwojPlus) | plan | 1085 | 53 | 0,765 | [0,204; 1,325] | 3,9 | 1,20 | tak |
| pierwsza połowa okresu (do 13.04.2025) | plan | 944 | 59 | 0,635 | [0,058; 1,213] | 3,5 | 1,00 | tak |
| druga połowa okresu (od 14.04.2025) | plan | 701 | 29 | 0,594 | [-0,119; 1,308] | 2,3 | 0,94 | tak |
| tylko rola „poseł” (bez ministrów) | rozszerzenie | 1553 | 85 | 0,632 | [0,146; 1,117] | 3,1 | 1,00 | tak |
| prawica + Republikanie i Kukiz15 | rozszerzenie | 1645 | 88 | 0,691 | [0,207; 1,174] | 3,3 | 1,09 | tak |
| sprzeczna = co najmniej 2 twierdzenia sprzeczne | rozszerzenie | 1645 | 15 | 1,236 | [-0,058; 2,530] | 1,0 | 1,95 | tak |

Kryterium (warianty z planu): ten sam znak i 0,5–2,0 × β₁ wyniku głównego. Wynik bez korekty jest **odporny**.
Połowy okresu dzieli 14.04.2025.

Leave-one-speaker-out (285 mówców): β₁ od 0,562 (bez: Mariusz Krystian) do 0,727 (bez: Tomasz Piotr Nowak); kryterium niespełnione po usunięciu 0 mówców.

## 5. Fakty do sekcji „Ograniczenia”

- Krok 8 sprawdza wynik bez korekty (etykiety modelu); o hipotezie rozstrzyga krok 7.
- Warianty, w których 95% CI β₁ obejmuje 0: bez Konfederacji (i Konfederacji KP), druga połowa okresu (od 14.04.2025), sprzeczna = co najmniej 2 twierdzenia sprzeczne.
- Wypowiedzi sprzeczne wg golda w warstwie 2 (model: tematyczna, niesprzeczna), liczba × waga: prawica: 2 × 55,2, reszta: 1 × 48,6.
- Gold w warstwie 3: tematyczne prawica: 0/15 (waga 1285), reszta: 0/15 (waga 1538).
- Przypadki bootstrapu bez wartości różnicy: 0.

