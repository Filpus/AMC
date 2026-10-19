# Suplement (wersja light), wariant B: model na wszystkich wypowiedziach

## Pytanie badawcze:
Czy w okresie od wyborów na sejm RP X kadencji (13.11.2023) do 15.09.2026 odsetek wypowiedzi plenarnych posłów reprezentujących prawicę sprzecznych z konsensusem naukowym dotyczącym klimatu był wyższy niż wśród pozostałych posłów?

## Hipoteza:
W okresie 13.11.2023–15.09.2026 odsetek wypowiedzi plenarnych posłów reprezentujących prawicę, sprzecznych z konsensusem naukowym dotyczącym klimatu, jest wyższy niż odsetek takich wypowiedzi wśród pozostałych posłów.

Uwagi:
1. Hipoteza opisuje różnicę między grupami w badanym oknie (pełna populacja wypowiedzi) i nie stwierdza przyczynowości ani nie uogólnia na posłów, którzy mogliby wygłaszać te wypowiedzi
2. **Prawica i reszta.** Prawica i reszta tworzą grupy. Wypowiedź posła należy do prawicy, jeśli w dniu wypowiedzi poseł należał do klubu z listy: PiS, RozwojPlus, Konfederacja, Konfederacja_KP. W przeciwnym przypadku należy do reszty.
3. **Wypowiedź plenarna.** Pełne wystąpienie jednego mówcy podczas posiedzenia plenarnego Sejmu, czyli posiedzenia izby w pełnym składzie (posiedzenia komisji i zespołów nie są objęte). Dalej „wypowiedź" oznacza wypowiedź plenarną. Wypowiedź z wieloma twierdzeniami jest „sprzeczna", jeśli zawiera co najmniej jedno twierdzenie sprzeczne z konsensusem.
4. **Odsetek wypowiedzi.** Dla każdej grupy (prawica i reszta posłów osobno) odsetek to liczba wypowiedzi plenarnych posłów z tej grupy uznanych za sprzeczne z konsensusem klimatycznym, podzielona przez liczbę tematycznych wypowiedzi plenarnych o klimacie posłów z tej grupy w mianowniku.
5. **Konsensus klimatyczny.** Jako źródło wiedzy o konsensusie uznajemy raporty AR6 IPCC (WGI – sierpień 2021, WGII – luty 2022, WGIII – kwiecień 2022). 

## Zakres próby:
- **Okres:** 13.11.2023–15.09.2026 (X kadencja Sejmu), posiedzenia plenarne.
- **Populacja:** wypowiedzi merytoryczne (bez prowadzącego obrady) posłów. Grupa (prawica lub reszta) wynika z klubu posła w dniu wypowiedzi.
- **Próba do ręcznego oznaczenia:** 100 wypowiedzi (krok 4 planu pomiaru).

## Plan pomiaru zjawiska:

- Krok 1. Dane: wypowiedzi plenarne posłów z okresu 13.11.2023–15.09.2026, uzyskiwane ze stenogramów posiedzeń plenarnych z API Sejmu. Każdej wypowiedzi przypisujemy grupę (prawica lub reszta) według klubu posła w dniu wypowiedzi.
- Krok 2. Wybór wypowiedzi tematycznych o klimacie: klasyfikator NLI lub LLM uruchamiany na wszystkich wypowiedziach (bez filtra słów kluczowych).
- Krok 3. Werdykt: model NLI lub LLM porównuje wypowiedź z dokumentem konsensusu (AR6 IPCC, WGI–WGIII) i zwraca sprzeczne / zgodne / brak podstaw.
- Krok 4. Gold standard: ręcznie oznaczona próbka dla klasyfikatora tematycznego i weryfikatora.
  Sposób losowania: losowanie warstwowe z nadreprezentowaniem. Warstwy w każdej grupie (prawica, reszta): 1) model: tematyczna i sprzeczna (20); 2) model: tematyczna i niesprzeczna (15); 3) model: nietematyczna (15). TPR, TNR i F1 liczymy z wagami (odwrotność prawdopodobieństwa wylosowania). Szczegóły: gold-standard-blueprint.md, wariant B.
  Adnotacja: jeden adnotator według zamrożonego codebooka; zakładamy, że etykiety gold standardu są poprawne (bez miary zgodności).
  Wielkość próby: 100 (po 50 na grupę)

- Krok 5. TPR, TNR i F1 osobno w grupach (prawica, reszta), dla obu etapów (tematyczność, werdykt) i dla etykiety końcowej.
- Krok 6. Test bez korekty, na wypowiedziach tematycznych (krok 2), ze zmienną zależną z kroku 3 (etykiety modelu): regresja logistyczna, prawica vs reszta, $\beta_1 > 0$, z błędami odpornymi na klastrowanie po mówcy. Wynik pomocniczy; o hipotezie rozstrzyga krok 7.
- Krok 7. Błąd klasyfikatora: estymacja wprost z gold standardu (bez korekty ilorazu). W każdej grupie $g$ liczymy z wagami $w_h = N_h / n_h$ ($N_h$ z pełnego korpusu, $n_h$ z próbki gold standardu): liczbę prawdziwych wypowiedzi sprzecznych $\hat{C}_g = \sum_i w_{h(i)}\,\mathbf{1}[\text{gold: sprzeczna}]$ oraz liczbę prawdziwych wypowiedzi tematycznych $\hat{T}_g = \sum_i w_{h(i)}\,\mathbf{1}[\text{gold: tematyczna}]$, gdzie suma przebiega po wypowiedziach gold standardu z grupy $g$, a $h(i)$ to warstwa wypowiedzi $i$. Skorygowany odsetek to $\hat{p}_g = \hat{C}_g / \hat{T}_g$, a parametr główny to $\hat{p}_{\text{prawica}} - \hat{p}_{\text{reszta}}$. Przedział ufności: bootstrap warstwowy próby gold standardu (losowanie w obrębie warstw grupa × werdykt modelu). Hipoteza jest poparta, jeśli dolna granica jednostronnego 95% przedziału jest większa od 0.
    Etykiety modelu wchodzą tylko przez podział na warstwy, więc błąd różnicowy między grupami jest uwzględniony automatycznie. Ograniczenie: przy 100 wypowiedziach przedział będzie szeroki.
- Krok 8. Odporność: ten sam test co w kroku 6 powtórzony w wariantach. Krok 8 nie jest warunkiem weryfikacji hipotezy (rozstrzyga krok 7), tylko oceną, na ile wynik jest ogólny. Wynik uznajemy za odporny, jeśli $\beta_1$ ma ten sam znak i podobną wielkość we wszystkich wariantach.
    1) Definicja prawicy: wyłączenie kolejno poszczególnych klubów z prawicy (Konfederacja, PIS).
    2) Podokresy: $\beta_1$ osobno w pierwszej i drugiej połowie okna.
- Krok 9. Raport: parametr główny z przedziałem ufności (krok 7, bootstrap), wynik bez korekty (krok 6), liczba wypowiedzi w mianowniku w każdej grupie, jakość klasyfikatora, ograniczenia.

## Możliwe źródła błędu:
1. **Błąd klasyfikatora tematycznego.** Zmienia mianownik i licznik; może różnić się między grupami, bo styl wypowiedzi (np. ironia, polemika) zależy od mówcy. -> Adresowane: gold standard w grupach (kroki 4–5, 7).
2. **Błąd weryfikatora (NLI/LLM).** Fałszywe „sprzeczne" lub przeoczone „sprzeczne", prawdopodobnie różnicowe między grupami. Wiarygodność NLI przy wykrywaniu sprzeczności bywa niska. -> Adresowane: gold standard, kroki 5 i 7.
3. **Rzadkość zjawiska.** Wypowiedzi sprzecznych z konsensusem klimatycznym jest mało, więc przy małej liczbie zdarzeń test ma niską moc, regresja jest niestabilna, a TPR słabo oszacowane. -> Częściowo adresowane (estymacja z wagami z warstwowej próby, krok 7). Warunek: jeśli w pełnym korpusie każda grupa ma co najmniej 100 wypowiedzi tematycznych, a obie grupy łącznie co najmniej 30 wypowiedzi sprzecznych (liczone według modelu), rozstrzygamy według kroku 7: hipoteza jest poparta albo niepoparta. Jeśli któryś z tych warunków nie jest spełniony, wynik opisujemy jako nierozstrzygający wskutek małej liczby danych (nie jako brak możliwości pomiaru). 
4. **Konstrukt: sprzeczność z konsensusem a ocena polityczna.** Twierdzenia o kosztach i tempie polityk klimatycznej mylone z zaprzeczaniem zawyżają licznik. -> Zaadresowanie w implementacji: reguła w codebooku.
5. **Zmiana udziału tematu.** Odsetek spada lub rośnie wraz z częstością debat o klimacie. -> Adresowane: mianownik obejmuje tylko wypowiedzi o klimacie.
6. **Przypisanie klubu.** Klub posła w dniu wypowiedzi pochodzi z głosowań: zmiana klubu jest widoczna dopiero w pierwszym głosowaniu po niej, a poseł bez głosowań dostaje klub ze stanu na dzień pobrania, więc część wypowiedzi może trafić do złej grupy. -> Niezaadresowane w planie: błąd jest losowy względem treści i dotyczy niewielu posłów - jego wpływ jest minimalny.

## Uzasadnienie wykonalności tematu w skali kursu:
- **Dane:** wypowiedzi plenarne są dostępne w API Sejmu, bez potrzeby scrapingu. Okno ok. 34 miesięcy to ograniczony zbiór. Zgodność z regulaminem API i RODO (data statement).
- **Zjawisko:** w wyniku etapu eksploracji wynika, że kwestie klimatyczne są relatywnie często poruszaną kwestią tematyczną podlegającą konsensusowi naukowemu.
- **Źródło weryfikacji:** badanie ograniczone do jednego tematu (klimat) i jednego dokument odniesienia (AR6).
- **Zasoby obliczeniowe:** zespół ma dostęp do narzędzi LLM uruchamianych w środowiskach chmurowych oraz dysponuje kartami graficznymi w przypadku potrzeby lokalnego przetwarzania. Model jest uruchamiany na wszystkich wypowiedziach, więc koszt całego przebiegu musi mieścić się w budżecie.
- **Praca ręczna:** gold standard o ograniczonej wielkości (100 wypowiedzi, jeden adnotator) mieści się w harmonogramie (zajęcia 3: codebook i gold standard, zajęcia 4: pierwszy wynik na pełnych danych). 
- **Ryzyko:** rzadkość zjawiska może uniemożliwić wykrycie efektu. Według zasad AMC poprawnie uzasadniony wynik negatywny lub wynik nierozstrzygający wskutek małej liczby danych jest pełnoprawnym rezultatem. 


## Literatura

- Coan, T. G., Boussalis, C., Cook, J., Nanko, M. O. (2021). Computer-assisted classification of contrarian claims about climate change. *Scientific Reports*, 11(1), 22320.
- Guo, Z., Schlichtkrull, M., Vlachos, A. (2022). A survey on automated fact-checking. *Transactions of the Association for Computational Linguistics*, 10, 178–206.
- Lockwood, B., Lockwood, M. (2022). How do right-wing populist parties influence climate and renewable energy policies? Evidence from OECD countries. *Global Environmental Politics*, 22(3), 12–37.
- TeBlunthuis, N., Hase, V., Chan, C.-H. (2024). Misclassification in automated content analysis causes bias in regression. Can we fix it? Yes we can! *Communication Methods and Measures*, 18(3), 278–299.
- Żuk, P., Szulecki, K. (2020). Unpacking the right-populist threat to climate action: Poland's pro-governmental media on energy transition and climate change. *Energy Research & Social Science*, 66, 101485.

