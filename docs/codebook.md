# Codebook

Instrukcja anotacji gold standardu i podstawa promptów klasyfikatora. Zakres i etykiety według suplementu karty
eksploracji, układ kategorii według Halterman, Keith (2025): definicja, kryteria włączenia i wyłączenia, przykłady.

**Status (2026-10-16):** wersja poprawiona, zgodna z suplementem B (light-release-supplement-B.md) i z repo AMC
(prompty `topic_v0`, `claims_v1`, `verdict_v1`, próba `data/gold/sample.csv`). Zmiany względem codebook.md:
codebook-correction-explanation.md. Według tej wersji oznaczamy gold standard. Decyzje i alternatywy są w sekcji 10,
pytania w sekcji 11.

## 1. Zakres

| | |
|---|---|
| mierzymy | odsetek wypowiedzi sprzecznych z konsensusem klimatycznym (AR6) wśród wypowiedzi o klimacie, osobno dla prawicy i reszty |
| jednostka | merytoryczne wystąpienie jednego mówcy na posiedzeniu plenarnym (bez prowadzącego obrady); mianownik: wypowiedzi o klimacie (sekcja 7) |
| okres | 13.11.2023–15.09.2026 (X kadencja) |
| populacja | wypowiedzi posłów, w tym ministrów-posłów: 43 991 (prawica 20 162, reszta 23 829) |
| grupy | **prawica**: klub w dniu wypowiedzi to PiS, RozwojPlus, Konfederacja albo Konfederacja_KP; **reszta**: pozostali, w tym Republikanie i Kukiz15 |
| źródło konsensusu | AR6 IPCC: WGI, WGII, WGIII |

Grupa jest metadaną z korpusu, nie polem anotacji. Anotator nie widzi mówcy ani klubu (sekcja 8).

**Zmiany klubów.** Liczy się klub w dniu wypowiedzi, jak w suplemencie, więc poseł, który zmienił klub, trafia do
różnych grup w różnych okresach:
- dwaj dzisiejsi posłowie Konfederacji_KP (m.in. Roman Fritz) byli niezrzeszeni od 19.03 do 3.06.2025, więc ich 25
  wypowiedzi z tego czasu należy do reszty. Jedna z nich (`10_32_2025-04-03_256`) nazywa absurdem to, „że zmiany
  klimatyczne spowodowane zostały przez normalnych ludzi”;
- posłowie dzisiejszego RozwojPlus byli wcześniej w Kukiz15 (64 wypowiedzi), w Republikanach (40) albo niezrzeszeni (18);
- 357 wypowiedzi dwóch posłów z czasu, gdy byli w PiS (dziś niezrzeszeni), należy do prawicy.

To nie jest błąd przypisania ze źródła błędu 7 w suplemencie (zmiana klubu widoczna w danych dopiero przy pierwszym
głosowaniu po niej): te wypowiedzi są przypisane zgodnie z definicją. Problem leży w samej definicji, bo klub w dniu
wypowiedzi nie zawsze odpowiada poglądom mówcy. Dotyczy to kilku mówców o wyrazistych poglądach, więc nie jest losowe
względem treści, a przy małej liczbie wypowiedzi sprzecznych liczy się każda (`10_32_2025-04-03_256` jest sprzeczna,
a trafia do reszty). Proponujemy opisać to jako osobne ograniczenie (pytanie 2).

## 2. Przebieg anotacji

```
wypowiedź ──> o klimacie? ──tak──> twierdzenia ──> atrybucja ──> werdykt (AR6) ──> sprzeczna (0/1)
                          └─nie──> koniec (poza mianownikiem)
```

| pole | jednostka | wartości |
|---|---|---|
| `klimat` | wypowiedź | `1` / `0` (sekcja 3) |
| `cytat` | twierdzenie | dosłowny fragment wypowiedzi, na którym opiera się twierdzenie |
| `twierdzenie` | twierdzenie | parafraza samodzielna (sekcja 4) |
| `atrybucja` | twierdzenie | `wlasne` / `cytat_zgoda` / `cytat_polemika` / `cytat_neutralny` (sekcja 5) |
| `werdykt` | twierdzenie | `sprzeczne` / `zgodne` / `brak_podstaw` (sekcja 6) |
| `ar6` | twierdzenie | identyfikator fragmentu i cytat, np. `WGI SPM A.1` „It is unequivocal that human influence has warmed…” |
| `sprzeczna` | wypowiedź | `1`, jeśli co najmniej jedno twierdzenie jest `sprzeczne`, inaczej `0`; tylko dla `klimat = 1` |
| `trudny`, `komentarz` | wypowiedź | flaga i komentarz do analizy błędów (sekcja 8) |

Anotacja ma dwie fazy: najpierw `klimat`, twierdzenia i atrybucja, potem werdykt z AR6 pod ręką. Twierdzenie oceniamy
zawsze w kontekście całej wypowiedzi.

## 3. Wypowiedź o klimacie (`klimat`, krok 2)

**Definicja.** `klimat = 1`, gdy klimat jest jednym z wątków wypowiedzi: mówca mówi coś o zmianie klimatu (przyczyny,
skutki, trendy, stan nauki) albo o polityce klimatycznej. Przelotna wzmianka nie wystarcza.

**Test.** Zdanie o klimacie odpowiada na pytanie „co mówca mówi o klimacie lub polityce klimatycznej?” (wątek, `1`)
czy tylko „w jakich okolicznościach dzieje się to, o czym mówi?” (tło, `0`). Wystarczy jeden akapit-wątek, niezależnie
od długości wypowiedzi.

**Włączamy:**
- zmianę klimatu, jej przyczyny, skutki i trendy, stan nauki o klimacie;
- politykę klimatyczną: redukcję emisji, ETS i ETS2, Zielony Ład, Fit for 55, dekarbonizację, neutralność klimatyczną,
  adaptację, OZE i inne technologie jako sposób ograniczania emisji;
- negowanie zmiany klimatu lub wyśmiewanie jej jako ideologii, jeśli mówca coś o niej twierdzi.

**Wyłączamy:**
- „klimat” w innym znaczeniu (polityczny, inwestycyjny, społeczny);
- nazwy urzędów i ustaw bez treści o klimacie (Ministerstwo Klimatu i Środowiska);
- zmianę klimatu jako tło innego tematu („w dobie zmian klimatu”);
- „klimatyzm”, „religia klimatyczna” itp. użyte tylko jako epitet wobec czegoś innego;
- smog, pogodę i klęski żywiołowe bez odniesienia do zmiany klimatu;
- politykę energetyczną (ceny, kopalnie, sieci) bez odniesienia do emisji lub klimatu.

**Warstwy próby** wyznacza etykieta modelu (sekcja 8), a nie słownik. Anotator nie wie, z której warstwy pochodzi
wypowiedź.

## 4. Twierdzenia

**Definicja.** Twierdzenie o stanie świata (fakt, zależność przyczynowa, trend, prognoza) dotyczące klimatu albo
działań wobec jego zmiany, które da się porównać z AR6.

**Włączamy:**
- przyczyny, skutki i trendy („emisje CO2 ocieplają klimat”, „susze są skutkiem zmiany klimatu”);
- stan nauki („naukowcy się spierają”, „modele klimatyczne się mylą”);
- fakty i prognozy o skuteczności i wykonalności działań oraz potencjale technologii („OZE nie zapewnią dość energii”,
  „redukcja emisji w UE nic nie zmieni”);
- dane krajowe i statystykę (emisje Polski, udział UE w emisjach), zwykle z werdyktem `brak_podstaw`;
- pytania retoryczne, które niosą twierdzenie.

**Wyłączamy:**
- oceny, epitety i inwektywy („szaleństwo ideologiczne”, „religia klimatyzmu”);
- twierdzenia o kosztach i tempie polityki klimatycznej („ETS podnosi ceny prądu”, „Zielony Ład zrujnuje rolnictwo”,
  „transformacja jest za szybka”). Według suplementu (źródło błędu 4) to ocena polityczna, a nie zaprzeczanie
  konsensusowi, więc nie może trafić do licznika;
- postulaty („trzeba wyjść z ETS”);
- zwykłe pytania (np. do ministra);
- treść przepisów, procedury, terminy i kwoty;
- twierdzenia o osobach i wydarzeniach politycznych (kto co powiedział, kto finansuje);
- smog i jakość powietrza.

**Wniosek mówcy.** Gdy fakt, pytanie retoryczne albo sarkazm służy wnioskowi, zapisujemy wniosek jako twierdzenie
i to on dostaje werdykt. Przykład z Coan i in. (2021): „dziś jest zimno” jest prawdą, „dziś jest zimno, więc nie ma
ocieplenia” już nie. Wniosek zapisujemy tylko wtedy, gdy wypowiedź go wyraża albo jednoznacznie sugeruje („więc”,
pytanie retoryczne, zestawienie z tezą przeciwną, czytelna ironia). Jeśli trzeba go zgadywać, nie zapisujemy.

**Do decyzji: jedno czy dwa twierdzenia.** Wypowiedź `10_7_2024-03-07_60`: „Zmiany klimatu, jak wiemy, na Ziemi
występowały zawsze. Jest pytanie o ich przyczyny i tutaj naukowcy się spierają, jaki rzeczywisty wpływ ma człowiek na
zmiany w klimacie.” Można ją zapisać na dwa sposoby:

| wariant | `twierdzenie` | `werdykt` |
|---|---|---|
| dwa twierdzenia | (a) Klimat Ziemi zmieniał się także w przeszłości. | `zgodne` |
| | (b) Nauka nie ustaliła, czy obecna zmiana klimatu wynika z działalności człowieka. | `sprzeczne` (WGI SPM A.1) |
| jedno twierdzenie | Skoro klimat zmieniał się zawsze, nauka nie ustaliła, czy obecna zmiana wynika z działalności człowieka. | `sprzeczne` (WGI SPM A.1) |

Etykieta wypowiedzi jest w obu wariantach taka sama (`sprzeczna = 1`). Dwa twierdzenia pokazują, na jakim fakcie mówca
opiera wniosek, i są zgodne z zasadą „jedno twierdzenie na wiersz”. Jedno twierdzenie jest prostsze i bliższe temu, co
mówca chce przekazać. Różnica ma znaczenie, jeśli mianownikiem będą twierdzenia (sekcja 7): wtedy fakt zapisany
osobno dokłada do mianownika twierdzenie `zgodne` i obniża odsetek.

**Parafraza:** jedno twierdzenie na wiersz, zrozumiałe bez wypowiedzi; liczby i stopień pewności mówcy zachowane; przy
polemice zapisujemy stanowisko mówcy.

## 5. Atrybucja

| wartość | kiedy | co oceniamy w werdykcie |
|---|---|---|
| `wlasne` | mówca twierdzi sam | twierdzenie |
| `cytat_zgoda` | mówca przytacza twierdzenie (także „jak pokazują naukowcy”) i się z nim zgadza | twierdzenie |
| `cytat_polemika` | mówca przytacza twierdzenie, żeby je odrzucić albo wyśmiać | **stanowisko mówcy**, czyli zaprzeczenie przytoczonego twierdzenia |
| `cytat_neutralny` | mówca relacjonuje bez oceny | nie oceniamy |

Przykład polemiki: `10_22_2024-11-20_257` (sekcja 9.2). W próbie LLM etap A zapisał je jako `wlasne`, czyli
z odwrotnym znakiem.

**Do decyzji: osobne pole czy sama zasada.** Zasada jest potrzebna w każdym wariancie: posłowie często przytaczają
przeciwnika, żeby się z nim nie zgodzić. Bez niej wypowiedź obalająca argumenty negujących zmianę klimatu dostałaby
`sprzeczna = 1`, a taki błąd częściej dotyczyłby reszty. Opcje:
- **zostawić pole**: da się policzyć, jak często model myli polemikę z twierdzeniem własnym;
- **usunąć pole**, zasadę stosować w parafrazie (stanowisko mówcy, bez cytatów neutralnych): mniej pracy, ale błędów
  modelu na polemikach nie policzymy bez ponownego czytania wypowiedzi.

Wybór nie zmienia kappy ani TPR/TNR, bo liczymy je na `sprzeczna` (sekcja 7). W literaturze takiego pola nie ma:
ClaimBuster ocenia, czy zdanie warto sprawdzić, CARDS oznacza akapity ze źródeł kontrariańskich (obecność twierdzenia
oznacza tam poparcie), a Rojas i in. (2024) rozpoznają stanowisko klasyfikatorem całego tekstu.

## 6. Werdykt

| wartość | definicja |
|---|---|
| `sprzeczne` | twierdzenie (przy polemice: stanowisko mówcy, przy wniosku: wniosek) przeczy ustaleniu AR6 |
| `zgodne` | twierdzenie odpowiada ustaleniu AR6 |
| `brak_podstaw` | pozostałe: AR6 się tym nie zajmuje (dane krajowe, zdarzenia po AR6, prawo UE) albo twierdzenie jest zbyt ogólne |

**Oba kierunki.** Jak w suplemencie, `sprzeczne` jest twierdzenie, które przeczy AR6 w którąkolwiek stronę: umniejsza
jego ustalenia („wpływ człowieka na klimat jest znikomy”) albo je wyolbrzymia („za 10 lat koniec świata”).

**Liczby i statystyki.** `sprzeczne` albo `zgodne` tylko wtedy, gdy fragment AR6 podaje tę samą wielkość co
twierdzenie: ten sam obszar (świat, region, kraj), ten sam gaz (CO2 albo wszystkie gazy cieplarniane), ten sam okres
i tę samą miarę (emisja roczna, skumulowana, na mieszkańca). Gdy fragment podaje inną wielkość, werdykt to
`brak_podstaw`, nawet jeśli liczby się różnią albo przypadkiem się zgadzają. Europa to nie Unia Europejska.

**Redukcja emisji w jednym regionie.** Twierdzenie, że redukcja emisji w jednym kraju albo regionie (np. w Polsce,
w UE) nic nie zmieni w sprawie klimatu, przeczy ustaleniu AR6, że ocieplenie zależy od skumulowanej emisji CO2 (WGI
SPM D.1, D.1.1), więc jest `sprzeczne`.

**Źródła w AR6.** Każdy raport grupy roboczej ma trzy warstwy: SPM (*Summary for Policymakers*, streszczenie dla
decydentów, kilkadziesiąt stron zatwierdzanych przez rządy zdanie po zdaniu), TS (*Technical Summary*, streszczenie
techniczne, ok. 100 stron) i rozdziały (2–3 tys. stron). Oceniamy tylko wobec SPM i TS WGI, WGII i WGIII: najpierw SPM,
potem TS. Do rozdziałów nie sięgamy, także przez odsyłacze w nawiasach klamrowych (np. `{2.3}`), bo model widzi tylko
SPM i TS. Raportu syntetycznego (SYR) nie używamy, bo suplement wymienia tylko WGI–WGIII. Oceniamy wobec AR6, a nie
wobec własnej wiedzy. `sprzeczne` i `zgodne` wymagają wskazania rozstrzygającego fragmentu (pole `ar6`); gdy żaden
fragment SPM ani TS nie rozstrzyga, werdykt to `brak_podstaw`.

**Data.** WGI ukazał się 9.08.2021, WGII 28.02.2022, WGIII 4.04.2022, czyli przed początkiem okresu, więc AR6 jest
punktem odniesienia dla wszystkich wypowiedzi.

## 7. Etykieta wypowiedzi i miary

`sprzeczna = 1`, gdy wypowiedź ma `klimat = 1` i co najmniej jedno twierdzenie `sprzeczne`. Wypowiedź o klimacie bez
takiego twierdzenia zostaje w mianowniku z `sprzeczna = 0`.

Jakość modelu liczymy na poziomie wypowiedzi:

| porównanie | miara | pole | podzbiór |
|---|---|---|---|
| model i gold: tematyczność | TPR, TNR, F1 | `klimat` | cała próba |
| model i gold: werdykt | TPR, TNR, F1 | `sprzeczna` | `klimat = 1` w goldzie i u modelu |
| model i gold: etykieta końcowa | TPR, TNR, F1 | `klimat = 1` i `sprzeczna = 1` | cała próba |

TPR/TNR/F1 pochodzą z kroku 5 suplementu. Miary modelu liczymy z wagami warstw, osobno dla prawicy i reszty.
Twierdzenia służą do uzasadnienia etykiety i analizy błędów; miar na nich nie liczymy, bo anotator i model wypisują
różne listy. Zgodności anotatorów (kappa) nie liczymy, bo anotator jest jeden; jeśli dojdzie drugi, stosujemy
light-release-extension-kappa.md.

**Decyzja: wypowiedzi w mianowniku** (opcja a niżej), jak w suplemencie i w repo. Poniżej zostawiamy argumenty, które
rozważaliśmy. Twierdzenia są potrzebne w obu wariantach: przez
nie suplement definiuje wypowiedź sprzeczną (uwaga 3), z AR6 porównuje się konkretną tezę, a narzędzie wyszukujące
dostaje ją jako zapytanie.

- Za twierdzeniami: przy wypowiedziach wynik zależy od długości, bo więcej twierdzeń daje większą szansę na sprzeczne.
  Wypowiedzi posłów z trafieniem słownika klimatu mają medianę 184 słów u prawicy i 346 u reszty; ponad 500 słów ma
  12% i 37%. CARDS i fact-checking też pracują na pojedynczych twierdzeniach.
- Przeciw: mianownik zależy od ekstrakcji, a listy anotatora i modelu się różnią. Miary trzeba by liczyć na twierdzeniach, ze wspólną listą albo dopasowaniem po cytacie,
  i ustalić reguły dla powtórzeń oraz dla `brak_podstaw`.

Kierunek efektu znamy: przy wypowiedziach długie wypowiedzi reszty częściej dostaną `sprzeczna = 1` (przeciw
hipotezie), przy twierdzeniach liczne twierdzenia `zgodne` reszty powiększą jej mianownik (na korzyść hipotezy).
Wielkości nie znamy. Jedyne dane z okresu to próba LLM z notatnika 03 (174 wypowiedzi prawicy i 230 reszty z filtra
wszystkich tematów, starszy prompt): twierdzenie naukowe o klimacie model potwierdził w 6 i 11 wypowiedziach.

| opcja | co to oznacza |
|---|---|
| a) wypowiedź | jak w suplemencie; twierdzenia są drogą do etykiety wypowiedzi |
| b) twierdzenie | zmiana hipotezy i definicji odsetka w suplemencie; gold porównywany na twierdzeniach |
| c) wypowiedź, twierdzenia jako wariant | suplement bez zmian; w kroku 8 dodatkowo odsetek twierdzeń, bez pełnej walidacji (gold waliduje tylko wypowiedzi) |

## 8. Gold standard

**Losowanie.** 100 wypowiedzi z populacji (sekcja 1), po 50 na grupę, według suplementu B (krok 4) i
gold-standard-blueprint.md, wariant B. Warstwy to grupa × etykieta modelu z pełnego przebiegu pipeline'u (Gemma 4 12B),
więc wymagają wcześniejszego przebiegu modelu na całej populacji. Wagi = N / n. Próba jest wylosowana (ziarno 0):
`AMC/data/gold/sample.csv`.

| warstwa | N | n | waga |
|---|---|---|---|
| prawica, model: tematyczna i sprzeczna | 60 | 20 | 3,0 |
| prawica, model: tematyczna i niesprzeczna | 828 | 15 | 55,2 |
| prawica, model: nietematyczna | 19 274 | 15 | 1 284,9 |
| reszta, model: tematyczna i sprzeczna | 28 | 20 | 1,4 |
| reszta, model: tematyczna i niesprzeczna | 729 | 15 | 48,6 |
| reszta, model: nietematyczna | 23 072 | 15 | 1 538,1 |

Warstwy „nietematyczna” mają duże wagi, więc oszacowanie tego, co gubi klasyfikator tematyczny, będzie mało precyzyjne.
Żadna z wypowiedzi cytowanych w codebooku (sekcje 1, 5 i 9) nie trafiła do próby.

**Anotator.** Jedna osoba z zespołu oznacza całą próbę. Nie ma drugiego anotatora ani rozstrzygającego; zakładamy, że
etykiety gold standardu są poprawne (suplement B, krok 4).

**Bez pilotażu.** Próba jest już wylosowana, więc codebook nie przechodzi pilotażu przed anotacją.

**Zasady:**
- anotacja przed zobaczeniem wyników modelu;
- anotator widzi tylko tekst, bez mówcy, klubu i daty; narzędzie maskuje też nazwiska we wtrąceniach prowadzącego
  („Poseł …:”). Treść może jednak zdradzać klub („Konfederacja wychodzi z tego stanowiska”);
- przy wątpliwości anotator wybiera etykietę i dodaje flagę `trudny` z komentarzem. Wypowiedzi nie odrzucamy (u Coan
  i in. „unable to decide” wracało do puli, co u nas zawyżyłoby TPR i TNR).

**Ograniczenie.** Anotator zna hipotezę. Ukrycie mówcy i klubu zmniejsza ryzyko, że wpłynie to na oceny, ale go
nie usuwa.

## 9. Przykłady z korpusu

Identyfikator to `wypowiedz_id` z `data/processed/korpus_plenarne.parquet`. Wszystkie przykłady pochodzą z okresu
i populacji z sekcji 1.

### 9.1. `klimat`

| wypowiedź | fragment | `klimat` | dlaczego |
|---|---|---|---|
| `10_60_2026-06-17_269` | „Czy osiągnięcie dekarbonizacji w europejskiej polityce klimatycznej, manipulacyjnie nazywanej neutralnością klimatyczną, ma sens?” | 1 | polityka klimatyczna jest przedmiotem całej wypowiedzi |
| `10_18_2024-09-25_107` | „Naukowcy są tutaj jednoznaczni, że nie chodzi o spory na temat klimatu, tylko chodzi o to, jak będą wyglądały zjawiska pogodowe (…). A sytuacja będzie krytyczna, jeśli chodzi o efekty tych zmian klimatycznych.” | 1 | 4,5 tys. słów o powodzi, ale jeden akapit mówi o skutkach zmiany klimatu |
| `10_10_2024-04-25_124` | „Proponowany przez pana eksperyment na tak dużym obszarze w obliczu obserwowanych zmian klimatycznych jest niezwykle niebezpieczny dla przyszłości lasów w Polsce.” | 0 | zmiana klimatu jako tło; przedmiot: gospodarka leśna |

### 9.2. Twierdzenia i werdykt

Fragmenty AR6 oznaczone „do wskazania” anotator wskazuje sam w SPM lub TS (sekcja 6).

| wypowiedź | fragment | zapis | werdykt |
|---|---|---|---|
| `10_7_2024-03-07_60` | „Zmiany klimatu, jak wiemy, na Ziemi występowały zawsze. Jest pytanie o ich przyczyny i tutaj naukowcy się spierają, jaki rzeczywisty wpływ ma człowiek…” | (a) klimat zmieniał się zawsze; (b) wniosek: nauka nie ustaliła, czy obecna zmiana wynika z działalności człowieka (wariant dwóch twierdzeń; do decyzji, sekcja 4) | (a) `zgodne`; (b) `sprzeczne` (WGI SPM A.1) |
| `10_22_2024-11-20_257` | „Pani minister wspomniała tu o konieczności walki z emisją CO2, co się zasadza na przekonaniu, że emisja CO2 powoduje globalne ocieplenie. (…) Nawet przy założeniu, że ta mitologia jest prawdziwa…” | `cytat_polemika`: związek emisji CO2 z ociepleniem to mit | `sprzeczne` (WGI SPM A.1) |
| `10_27_2025-01-23_218` | „A przyczyna tego wszystkiego to są opłaty ETS, to jest to szaleństwo ideologiczne zielonej energii, te głupoty, że krowy są odpowiedzialne za ocieplenie klimatu.” | wniosek: hodowla bydła nie przyczynia się do ocieplenia. Nie wypisujemy: „opłaty ETS” jako przyczyny cen prądu (koszty polityki, sekcja 4) ani „szaleństwa ideologicznego” (ocena) | `sprzeczne` (metan z rolnictwa, do wskazania) |

### 9.3. Przypadki do dyskusji

Bez etykiet, żeby nie sugerować odpowiedzi. Służą do przećwiczenia reguł przed anotacją (`klimat`, twierdzenia,
werdykt); nie wchodzą do gold standardu.

| | wypowiedź | fragment | pytanie |
|---|---|---|---|
| D1 | `10_41_2025-09-25_308` | „W dobie narastających wyzwań ekologicznych, takich jak postępujące zmiany klimatyczne (…) To także przeciwdziałanie skutkom zmian klimatycznych, które w szczególny sposób oddziałują na obszary rzeczne i podmokłe.” | park narodowy: klimat jako wątek czy tło? |
| D2 | `10_5_2024-02-07_117` | „…brednia klimatyzmu (…) jednak wali się (…) bo jednak deszcz pada, tak jak padał, śnieg pada, tak jak padał, mniej więcej, w pewnym tam przedziale.” | fakt o opadach w Polsce jako argument przeciw ociepleniu: jaki wniosek zapisać? |
| D3 | `10_22_2024-11-20_257` | „Nawet jak ją zlikwidujemy, to nic to nie zmieni, zwłaszcza że likwidowany w Unii Europejskiej przemysł wysokoemisyjny (…) przenosi się do Chin czy Indii.” | prognoza skuteczności i ucieczka emisji: czy WGIII daje podstawę do werdyktu? |

## 10. Decyzje i alternatywy

| punkt | decyzja | rozważane alternatywy |
|---|---|---|
| wypowiedź o klimacie | wątek, razem z polityką klimatyczną | twierdzenie ocenialne wobec AR6; dowolna wzmianka |
| pogoda, klęski, smog | tylko z odniesieniem do zmiany klimatu, także zaprzeczającym | ekstrema i klęski zawsze; dodatkowo smog |
| polityka klimatyczna | jak w suplemencie: koszty i tempo polityki nie są twierdzeniami; skuteczność i wykonalność działań oceniane wobec WGIII | wszystkie fakty i prognozy wobec WGIII; wyłączyć całą politykę; osobna kategoria poza licznikiem |
| znaczenie | dosłowne fakty i wniosek mówcy | tylko dosłowne; osobne pole wniosku |
| fakt i wniosek | **do decyzji** (sekcja 4) | dwa twierdzenia (fakt i wniosek); jedno twierdzenie (wniosek z faktem jako uzasadnieniem) |
| kierunek | oba kierunki (umniejszanie i wyolbrzymianie), jak w suplemencie | tylko umniejszanie; oba z polem kierunku |
| mianownik | wypowiedzi o klimacie, jak w suplemencie (sekcja 7) | twierdzenia; wypowiedzi z twierdzeniami jako wariantem |
| poziom porównań | wypowiedź (`klimat`, `sprzeczna`) | wspólna lista twierdzeń; dopasowanie po cytacie |
| atrybucja | **do decyzji** (sekcja 5) | pole z czterema wartościami; sama zasada w parafrazie; pole uproszczone (`wlasne` / `polemika` / `neutralny`) |
| CARDS | tylko literatura (reguła wniosku mówcy, sekcja 4) | ściąga z podkategoriami; pole `cards` |
| warstwy | grupa × etykieta modelu, 20 / 15 / 15 na grupę (suplement B) | grupa × filtr, 100 + 25 na grupę; dwie osobne próby |
| ślepota | bez mówcy, klubu i daty | wszystko widoczne; bez mówcy, ale z poprzednią wypowiedzią |
| `brak_podstaw` | jedna etykieta | „AR6 się tym nie zajmuje” i „nie znaleziono” osobno |
| pewność AR6 | bez progu: liczy się każde ustalenie AR6 (pytanie 7) | od *likely* / *medium confidence*; od *very likely* / *high confidence* |
| źródła AR6 | SPM → TS, bez rozdziałów i bez SYR (jak w modelu) | tylko SPM; rozdziały przez odsyłacze; dodatkowo SYR |
| dane krajowe | twierdzenia, zwykle `brak_podstaw` | wyłączyć |
| trudne przypadki | flaga `trudny` + komentarz | bez flagi |
| anotatorzy | jeden anotator z zespołu, bez pilotażu (suplement B) | dwie osoby i rozstrzygający, pilotaż 1 × 20; szkolenie i test kwalifikacyjny (jak u Coan i in.) |
| ministrowie-posłowie | w populacji | wyłączyć |
| Republikanie, Kukiz15 | reszta | wariant odporności z nimi w prawicy |
| zmiany klubów | klub w dniu wypowiedzi (także okresy bez klubu) | klub z dnia pobrania; klub, do którego poseł trafił później |

## 11. Pytania do zespołu

1. ~~**Lead:** co jest mianownikiem?~~ Rozstrzygnięte: wypowiedzi o klimacie (sekcja 7).
2. **Lead:** zostajemy przy klubie w dniu wypowiedzi (sekcja 1); czy dopisać skutki zmian klubów jako osobne ograniczenie?
3. Kto oznacza gold? (jedna osoba, sekcja 8)
4. Atrybucja (sekcja 5): osobne pole czy sama zasada w parafrazie?
5. Wniosek mówcy (sekcja 4): fakt i wniosek zapisujemy jako dwa twierdzenia czy jako jedno?
6. Uwagi do decyzji z sekcji 10.
7. Czy warto dodać próg pewności AR6? AR6 opisuje pewność ustaleń (*likely*, *very likely*, *medium* / *high
   confidence*). Teraz liczy się każde ustalenie, więc twierdzenie sprzeczne z ustaleniem o niskiej pewności też
   jest `sprzeczne`. Próg (np. od *likely* albo *medium confidence*) ograniczyłby `sprzeczne` i `zgodne` do ustaleń,
   które AR6 uznaje za co najmniej prawdopodobne.

## 12. Literatura

- Coan, T. G., Boussalis, C., Cook, J., Nanko, M. O. (2021). Computer-assisted classification of contrarian claims about
  climate change. *Scientific Reports*, 11, 22320.
- Rojas, C., Algra-Maschio, F., Andrejevic, M., Coan, T., Cook, J., Li, Y.-F. (2024). Hierarchical machine learning
  models can identify stimuli of climate change misinformation on social media. *Communications Earth & Environment*,
  5 (preprint: arXiv 2404.15673, *Augmented CARDS*).
- Hassan, N., Arslan, F., Li, C., Tremayne, M. (2017). Toward Automated Fact-Checking: Detecting Check-worthy Factual
  Claims by ClaimBuster. *KDD '17*.
- Halterman, A., Keith, K. A. (2025). Codebook LLMs: Evaluating LLMs as Measurement Tools for Political Science Concepts.
- IPCC (2021, 2022). *Sixth Assessment Report*, WGI, WGII, WGIII.
