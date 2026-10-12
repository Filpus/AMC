## Pytanie badawcze:
Czy w okresie od wyborów na sejm RP X kadencji (13.11.2023) do 15.09.2026 odsetek wypowiedzi plenarnych posłów reprezentujących prawicę sprzecznych z konsensusem naukowym dotyczącym klimatu był wyższy niż wśród pozostałych posłów?

## Hipoteza:
W okresie 13.11.2023–15.09.2026 odsetek wypowiedzi plenarnych posłów reprezentujących prawicę, sprzecznych z konsensusem naukowym dotyczącym klimatu, jest wyższy niż odsetek takich wypowiedzi wśród pozostałych posłów.

Uwagi:
1. Hipoteza opisuje różnicę między grupami i nie stwierdza przyczynowości
2. **Prawica i reszta.** Prawica i reszta tworzą grupy. Wypowiedź posła należy do prawicy, jeśli w dniu wypowiedzi poseł należał do klubu z listy: PiS, RozwojPlus, Konfederacja, Konfederacja_KP. W przeciwnym przypadku należy do reszty.
3. **Wypowiedź plenarna.** Pełne wystąpienie jednego mówcy podczas posiedzenia plenarnego Sejmu, czyli posiedzenia izby w pełnym składzie (posiedzenia komisji i zespołów nie są objęte). Dalej „wypowiedź" oznacza wypowiedź plenarną. Wypowiedź z wieloma twierdzeniami jest „sprzeczna", jeśli zawiera co najmniej jedno twierdzenie sprzeczne z konsensusem.
4. **Odsetek wypowiedzi.** Dla każdej grupy (prawica i reszta posłów osobno) odsetek to liczba wypowiedzi plenarnych posłów z tej grupy uznanych za sprzeczne z konsensusem klimatycznym, podzielona przez liczbę tematycznych wypowiedzi plenarnych o klimacie posłów z tej grupy w mianowniku.
5. **Konsensus klimatyczny.** Jako źródło wiedzy o konsensusie uznajemy raporty AR6 IPCC (WGI, WGII, WGIII – kwiecień 2022). 


## Zakres próby:
- **Okres:** 13.11.2023–15.09.2026 (X kadencja Sejmu), posiedzenia plenarne.
- **Populacja:** wypowiedzi merytoryczne (bez prowadzącego obrady) posłów. Grupa (prawica lub reszta) wynika z klubu posła w dniu wypowiedzi.
- **Próba do ręcznego oznaczenia:** 250 wypowiedzi (krok 4 planu pomiaru).

## Plan pomiaru zjawiska:

- Krok 1. Dane: wypowiedzi plenarne posłów z okresu 13.11.2023–15.09.2026, uzyskiwane ze stenogramów posiedzeń plenarnych z API Sejmu. Każdej wypowiedzi przypisujemy grupę (prawica lub reszta) według klubu posła w dniu wypowiedzi.
- Krok 2. Wybór wypowiedzi tematycznych o klimacie (klasyfikator NLI lub LLM lub słownik tematyczny).
- Krok 3. Werdykt: model NLI lub LLM porównuje wypowiedź z dokumentem konsensusu (AR6 IPCC, WGI–WGIII) i zwraca sprzeczne / zgodne / brak podstaw.
- Krok 4. Gold standard: ręcznie oznaczona próbka dla klasyfikatora tematycznego i weryfikatora.
  Sposób losowania: losowanie warstwowe (warstwy: grupa) z nadreprezentowaniem. TPR, TNR i F1 liczymy wtedy z wagami (odwrotność prawdopodobieństwa wylosowania).
  Wielkość próby: 250

- Krok 5. TPR, TNR i F1 osobno w grupach (prawica, reszta), dla obu etapów (tematyczność, werdykt) i dla etykiety końcowej.
- Krok 6. Test hipotezy, na zmiennej zależnej z kroku 3: regresja logistyczna, prawica vs reszta, β1 > 0, z błędami odpornymi na klastrowanie po mówcy.
- Krok 7. Błąd klasyfikatora, wejście: wynik kroku 6 i TPR/TNR z kroku 5:
    Z korekcją Rogan–Gladen: korekta odsetka w grupie, potem ten sam test z kroku 6. Bootstrap (losowanie próby walidacyjnej i wypowiedzi) daje przedział ufności parametru głównego.
    TPR/TNR szacowane osobno w porównywanych grupach, bo błąd może być różnicowy.
- Krok 8. Odporność: ten sam test co w kroku 6 powtórzony w wariantach. Krok 8 nie jest warunkiem weryfikacji hipotezy (rozstrzyga krok 6), tylko oceną, na ile wynik jest ogólny. Wynik uznajemy za odporny, jeśli β1 ma ten sam znak i podobną wielkość we wszystkich wariantach.
    1) Definicja prawicy: wyłączenie kolejno poszczególnych klubów z prawicy (Konfederacja, PIS).
    2) Podokresy: β1 osobno w pierwszej i drugiej połowie okna.
- Krok 9. Raport: parametr główny z przedziałem ufności, bez korekty (krok 6) i po korekcie (krok 7, bootstrap), liczba wypowiedzi w mianowniku w każdej grupie, jakość klasyfikatora, ograniczenia.


## Możliwe źródła błędu:
1. **Błąd klasyfikatora tematycznego.** Zmienia mianownik i licznik; może różnić się między grupami, bo styl wypowiedzi (np. ironia, polemika) zależy od mówcy. -> Adresowane: TPR/TNR w grupach (kroki 4–5, 7).
2. **Błąd weryfikatora (NLI/LLM).** Fałszywe „sprzeczne" lub przeoczone „sprzeczne", prawdopodobnie różnicowe między grupami. Wiarygodność NLI przy wykrywaniu sprzeczności bywa niska. -> Adresowane: gold standard, kroki 5 i 7.
3. **Rzadkość zjawiska.** Wypowiedzi sprzecznych z konsensusem klimatycznym jest mało, więc przy małej liczbie zdarzeń test ma niską moc, regresja jest niestabilna, a TPR słabo oszacowane. -> Częściowo adresowane (korekta Rogan-Gladen, warstwowa próba). Próg: jeśli w pełnym korpusie któraś grupa ma mniej niż 30 wypowiedzi „sprzecznych" (według etykiet modelu), wynik opisujemy jako brak możliwości pomiaru. 
4. **Konstrukt: sprzeczność z konsensusem a ocena polityczna.** Twierdzenia o kosztach i tempie polityk klimatycznej mylone z zaprzeczaniem zawyżają licznik. -> Zaadresowanie w implementacji: reguła w codebooku, kappa na gold standardzie.
5. **Zależność wypowiedzi tego samego mówcy.** Zaniża błędy standardowe. -> Adresowane: krok 6 (błędy odporne na klastrowanie po mówcy).
6. **Zmiana udziału tematu.** Odsetek spada lub rośnie wraz z częstością debat o klimacie. -> Adresowane: mianownik obejmuje tylko wypowiedzi o klimacie.
7. **Przypisanie klubu.** Klub posła w dniu wypowiedzi pochodzi z głosowań: zmiana klubu jest widoczna dopiero w pierwszym głosowaniu po niej, a poseł bez głosowań dostaje klub ze stanu na dzień pobrania, więc część wypowiedzi może trafić do złej grupy. -> Niezaadresowane w planie: błąd jest losowy względem treści i dotyczy niewielu posłów - jego wpływ jest minimalny.

## Uzasadnienie wykonalności tematu w skali kursu:
- **Dane:** wypowiedzi plenarne są dostępne w API Sejmu, bez potrzeby scrapingu. Okno ok. 34 miesięcy to ograniczony zbiór. Zgodność z regulaminem API i RODO (data statement).
- **Zjawisko:** w wyniku etapu eksploracji wynika, że kwestie klimatyczne są relatywnie często poruszaną kwestią tematyczną podlegającą konsensusowi naukowemu.
- **Źródło weryfikacji:** badanie ograniczone do jednego tematu (klimat) i jednego dokument odniesienia (AR6).
- **Zasoby obliczeniowe:** zespół ma dostęp do narzędzi LLM uruchamianych w środowiskach chmurowych oraz dysponuje kartami graficznymi w przypadku potrzeby lokalnego przetwarzania.
- **Praca ręczna:** gold standard o ograniczonej wielkości (dwóch adnotatorów plus rozstrzygający) mieści się w harmonogramie (zajęcia 3: codebook i gold standard, zajęcia 4: pierwszy wynik na pełnych danych). 
- **Ryzyko:** rzadkość zjawiska może uniemożliwić wykrycie efektu. Według zasad AMC poprawnie uzasadniony wynik negatywny lub stwierdzenie niemożności pomiaru jest pełnoprawnym rezultatem. 


## Literatura

- Coan, T. G., Boussalis, C., Cook, J., Nanko, M. O. (2021). Computer-assisted classification of contrarian claims about climate change. *Scientific Reports*, 11(1), 22320.
- Guo, Z., Schlichtkrull, M., Vlachos, A. (2022). A survey on automated fact-checking. *Transactions of the Association for Computational Linguistics*, 10, 178–206.
- Lockwood, B., Lockwood, M. (2022). How do right-wing populist parties influence climate and renewable energy policies? Evidence from OECD countries. *Global Environmental Politics*, 22(3), 12–37.
- TeBlunthuis, N., Hase, V., Chan, C.-H. (2024). Misclassification in automated content analysis causes bias in regression. Can we fix it? Yes we can! *Communication Methods and Measures*, 18(3), 278–299.
- Żuk, P., Szulecki, K. (2020). Unpacking the right-populist threat to climate action: Poland's pro-governmental media on energy transition and climate change. *Energy Research & Social Science*, 66, 101485.

