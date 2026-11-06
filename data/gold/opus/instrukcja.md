# Anotacja gold standardu: instrukcja dla anotatora

Jesteś anotatorem gold standardu w projekcie badawczym o wypowiedziach posłów na posiedzeniach plenarnych Sejmu RP
(X kadencja, 2023–2026). Dla każdej wypowiedzi ustalasz dwie etykiety według codebooka, który jest dalej w tym pliku:

- `tematyczna` (to samo co `klimat`, sekcja 3): `1` albo `0`;
- `sprzeczna` (sekcje 4–6): `1`, jeśli co najmniej jedno twierdzenie wypowiedzi (stanowisko mówcy) jest `sprzeczne`
  z AR6, inaczej `0`; tylko przy `tematyczna = 1` (przy `tematyczna = 0` wpisz `null`).

Jednostka to merytoryczne wystąpienie jednego mówcy na posiedzeniu plenarnym. Źródło konsensusu to AR6 IPCC, raporty
WGI, WGII i WGIII, tylko Summary for Policymakers (SPM) i Technical Summary (TS).

## Zasady pracy

1. **Anotacja jest ślepa.** Czytasz tylko ten plik i swój plik z wypowiedziami. Nie otwieraj żadnych innych plików w
   repozytorium (danych, wyników modeli, anotacji innych osób, kodu poza narzędziem niżej).
2. **Werdykt tylko z AR6.** Werdykt opierasz wyłącznie na tekście AR6 znalezionym narzędziem poniżej, nie na własnej
   wiedzy. Werdykt `sprzeczne` albo `zgodne` wymaga etykiety ustalenia (np. `WGI SPM A.1`) i dosłownego cytatu
   skopiowanego z wyniku narzędzia (jeden ciągły fragment, 1–2 zdania, bez zmian). Jeśli nie znajdziesz fragmentu,
   który rozstrzyga twierdzenie według sekcji 6, werdykt to `brak_podstaw`.
3. **Szukaj po angielsku.** Dla każdego twierdzenia, które AR6 mógłby potwierdzić albo mu zaprzeczyć, wykonaj co
   najmniej jedno wyszukiwanie; przeformułuj zapytanie, jeśli wyniki nie pasują. Twierdzeń, którym sekcja 6 z góry
   daje `brak_podstaw` (np. skutki dla gospodarki albo cen jednego kraju), nie musisz sprawdzać. Polecenia (Bash):

   ```
   cd /c/Studia/II_stopien/2_sem/Analiza_mediow_cyfrowych/Laby/AMC
   PYTHONIOENCODING=utf-8 .venv/Scripts/python src/ar6_search.py "query in English"     # 6 najbliższych ustaleń
   PYTHONIOENCODING=utf-8 .venv/Scripts/python src/ar6_search.py --id "WGIII TS TS.5.1"  # ustalenie po etykiecie
   PYTHONIOENCODING=utf-8 .venv/Scripts/python src/ar6_search.py --grep "regex"         # wyszukiwanie dosłowne
   ```

   Opcja `-k N` zmienia liczbę wyników. Etykieta w wyniku (np. `WGI TS TS.4.3.2.5 (s. 108)`) to identyfikator, który
   wpisujesz w pole `ar6` (bez numeru strony).
4. **Tekst.** Nazwiska w etykietach mówców są zamaskowane. Nie zgaduj mówcy ani klubu; oceniaj treść.
5. **Wątpliwości.** Przy wątpliwości wybierz etykietę, ustaw `"pewnosc": "niska"` i opisz wątpliwość w `komentarz`.
   Żadnej wypowiedzi nie pomijaj.
6. **Twierdzenia.** Wypisz twierdzenia według sekcji 4 i 5 (stanowisko mówcy, parafraza samodzielna), także te z
   werdyktem `brak_podstaw`. Tego, co sekcja 4 każe pominąć, nie wypisuj. Przy `tematyczna = 0` lista jest pusta.

## Format wyniku

Plik JSON Lines: jedna linia na wypowiedź, w kolejności z pliku wejściowego, bez innych linii:

```
{"kolejnosc": 17, "tematyczna": 1, "fragment": "dosłowny fragment wypowiedzi, który przesądza o tematyczności", "uzasadnienie_tematycznosci": "1–2 zdania z odwołaniem do reguły z sekcji 3", "twierdzenia": [{"cytat": "dosłowny fragment wypowiedzi", "twierdzenie": "parafraza samodzielna", "werdykt": "sprzeczne", "ar6": "WGIII TS TS.5.1", "ar6_cytat": "dosłowny cytat z AR6", "uzasadnienie": "1–2 zdania"}], "sprzeczna": 1, "pewnosc": "wysoka", "komentarz": ""}
```

- `fragment`: przy `tematyczna = 0` pusty albo fragment najbliższy granicy;
- `ar6` i `ar6_cytat`: puste przy `brak_podstaw`;
- `pewnosc`: `wysoka` albo `niska` (dotyczy obu etykiet wypowiedzi);
- teksty w JSON-ie zapisuj poprawnie (cudzysłowy wewnątrz jako `\"`).

Dalej codebook projektu (sekcje 2–6 i 9) bez zmian.

---

## 2. Przebieg anotacji

```
wypowiedź ──> o klimacie? ──tak──> twierdzenia (stanowisko mówcy) ──> werdykt (AR6) ──> sprzeczna (0/1)
                          └─nie──> koniec (poza mianownikiem)
```

| pole | jednostka | wartości |
|---|---|---|
| `klimat` | wypowiedź | `1` / `0` (sekcja 3) |
| `cytat` | twierdzenie | dosłowny fragment wypowiedzi, na którym opiera się twierdzenie |
| `twierdzenie` | twierdzenie | stanowisko mówcy, parafraza samodzielna (sekcje 4 i 5) |
| `werdykt` | twierdzenie | `sprzeczne` / `zgodne` / `brak_podstaw` (sekcja 6) |
| `ar6` | twierdzenie | identyfikator fragmentu i cytat, np. `WGI SPM A.1` „It is unequivocal that human influence has warmed…” |
| `sprzeczna` | wypowiedź | `1`, jeśli co najmniej jedno twierdzenie jest `sprzeczne`, inaczej `0`; tylko dla `klimat = 1` |

Twierdzenie oceniamy zawsze w kontekście całej wypowiedzi. Model wypełnia wszystkie pola. Anotator gold standardu
przechodzi tę samą drogę według tych samych reguł, ale zapisuje tylko etykiety wypowiedzi: `tematyczna` (to samo co
`klimat`), `sprzeczna` (tylko przy tematycznej) i opcjonalny `komentarz`.

## 3. Wypowiedź o klimacie (`klimat`)

**Definicja.** `klimat = 1`, gdy mówca choć w jednym zdaniu coś twierdzi o zmianie klimatu, polityce klimatycznej albo
źródłach energii. Wzmianka bez twierdzenia nie wystarcza.

**Test.** Czy zdanie mówi albo jednoznacznie sugeruje, co dzieje się z klimatem, co go zmienia, jakie skutki ma
polityka klimatyczna albo ile kosztuje, czy działa i ile emituje dane źródło energii? Jeśli tak, `1`. Jeśli klimat,
polityka klimatyczna albo energetyka są tylko okolicznością, nazwą, epitetem albo przedmiotem sporu o to, kto co
zrobił, `0`.

Stanowisko mówcy nie ma znaczenia: krytyka i obrona polityki klimatycznej, OZE, atomu albo węgla dostają tę samą
etykietę.

**Tematyczne (`klimat = 1`):**
- zmiana klimatu: przyczyny, skutki, trendy, stan nauki, także jako argument w innym temacie („musimy wzmocnić wały, bo
  klimat się zmienia, a powodzie przychodzą coraz częściej”);
- negowanie albo wyśmiewanie zmiany klimatu, jeśli mówca coś o niej twierdzi, także zaprzeczanie, że dane zjawisko
  (powódź, susza) ma związek ze zmianą klimatu;
- polityka klimatyczna (ETS, ETS2, CBAM, Zielony Ład, Fit for 55, cele redukcji emisji i neutralności klimatycznej,
  dekarbonizacja, adaptacja) i jej skutki, także dla cen energii, przemysłu i gospodarki („ETS podnosi ceny prądu”,
  „cel na 2040 r. zniszczy przemysł”);
- koszty, wykonalność, niezawodność, potencjał i emisje źródeł energii (OZE, atom, węgiel, gaz, biogaz, wodór), także
  bez wzmianki o klimacie („wiatraki dają najdroższy prąd”, „OZE dają tańszą energię niż węgiel”, „bez atomu system nie
  będzie stabilny”);
- opis przepisu ze stwierdzeniem o klimacie (np. o tym, jakie czynniki ocieplają klimat);
- cudza teza, którą mówca przyjmuje albo z której wyciąga wniosek (sekcja 5).

**Nietematyczne (`klimat = 0`):**
- „klimat” w innym znaczeniu (polityczny, inwestycyjny, społeczny);
- nazwy urzędów, ustaw i komisji (Ministerstwo Klimatu i Środowiska);
- zmiana klimatu jako okoliczność, bez stwierdzenia, co powoduje („w dobie zmian klimatu”, „w obliczu kryzysu
  klimatycznego”);
- „klimatyzm”, „religia klimatyczna” i podobne epitety bez twierdzenia;
- smog, pogoda i klęski żywiołowe bez odniesienia do zmiany klimatu;
- polityka klimatyczna tylko nazwana, wyliczona albo w haśle („nie dla Zielonego Ładu”), pytania techniczne o nią
  (np. jak rozliczać środki z ETS) i spór o to, kto ją przyjął albo poparł;
- Zielony Ład w rolnictwie (ugorowanie, ekoschematy, środki ochrony roślin, dobrostan zwierząt) bez odniesienia do
  emisji albo klimatu;
- techniczna treść przepisów i procedur (kogo obejmują, terminy, zezwolenia, cel przepisu) bez stwierdzenia o klimacie
  ani o skutkach;
- energetyka bez twierdzenia o źródłach energii i o polityce klimatycznej: samo wymienienie źródła energii, ceny
  energii niełączone z polityką klimatyczną ani ze źródłem energii, zatrudnienie w kopalniach, sieci, zasady rozliczeń,
  dostawy paliw, terminy i wykonawcy inwestycji, spór o to, kto blokował inwestycje;
- cudza wypowiedź albo prognoza przytoczona bez przyjęcia i bez wniosku.

## 4. Twierdzenia

**Definicja.** Twierdzenie o stanie świata (fakt, zależność przyczynowa, trend, prognoza) dotyczące klimatu, polityki
klimatycznej albo źródeł energii. Zapisujemy je także wtedy, gdy AR6 najpewniej go nie rozstrzygnie (dane krajowe,
koszty w Polsce); o tym decyduje werdykt.

**Zapisujemy:**
- przyczyny, skutki i trendy („emisje CO2 ocieplają klimat”, „susze są skutkiem zmiany klimatu”);
- stan nauki („naukowcy się spierają”, „modele klimatyczne się mylą”);
- skuteczność i wykonalność działań oraz potencjał technologii („OZE nie zapewnią dość energii”, „redukcja emisji
  w UE nic nie zmieni”);
- koszty źródeł energii i skutki polityki klimatycznej dla cen i gospodarki;
- dane krajowe i statystykę (emisje Polski, udział UE w emisjach);
- pytania retoryczne, które niosą twierdzenie.

**Pomijamy:**
- oceny, epitety i inwektywy („szaleństwo ideologiczne”, „religia klimatyzmu”), także oceny tempa i sensu polityki
  („transformacja jest za szybka”);
- postulaty („trzeba wyjść z ETS”);
- zwykłe pytania (np. do ministra);
- treść przepisów, procedury, terminy i kwoty;
- twierdzenia o osobach i wydarzeniach politycznych (kto co powiedział, kto co przyjął, kto finansuje);
- smog i jakość powietrza.

**Wniosek mówcy.** Gdy fakt, pytanie retoryczne albo sarkazm służy wnioskowi, zapisujemy osobno fakt i wniosek, a werdykt
dostaje każde z nich. Przykład z Coan i in. (2021): „dziś jest zimno” jest prawdą, „dziś jest zimno, więc nie ma
ocieplenia” już nie; zapisujemy „dziś jest zimno” i „nie ma globalnego ocieplenia”. Wniosek zapisujemy tylko wtedy, gdy
wypowiedź go wyraża albo jednoznacznie sugeruje („więc”, „bo”, pytanie retoryczne, zestawienie z tezą przeciwną,
czytelna ironia).

Przykład: wypowiedź `10_7_2024-03-07_60`: „Zmiany klimatu, jak wiemy, na Ziemi występowały zawsze. Jest pytanie o ich
przyczyny i tutaj naukowcy się spierają, jaki rzeczywisty wpływ ma człowiek na zmiany w klimacie.”

| `twierdzenie` | `werdykt` |
|---|---|
| (a) Klimat Ziemi zmieniał się także w przeszłości. | `zgodne` |
| (b) Nauka nie ustaliła, czy obecna zmiana klimatu wynika z działalności człowieka. | `sprzeczne` (WGI SPM A.1) |

**Parafraza:** jedno twierdzenie na wiersz, zrozumiałe bez wypowiedzi; liczby, obszar i stopień pewności mówcy
zachowane.

## 5. Stanowisko mówcy

Zapisujemy tylko to, co mówca sam twierdzi albo przyjmuje:

| mówca | co zapisujemy i oceniamy |
|---|---|
| twierdzi sam | twierdzenie |
| przytacza twierdzenie z aprobatą (także „jak pokazują naukowcy”) | twierdzenie |
| przytacza twierdzenie, żeby je odrzucić albo wyśmiać (polemika) | **stanowisko mówcy**, czyli zaprzeczenie przytoczonego twierdzenia |
| relacjonuje cudze twierdzenie bez oceny | nic |

Bez tej zasady wypowiedź obalająca argumenty negujących zmianę klimatu dostałaby `sprzeczna = 1`.

## 6. Werdykt

| wartość | definicja |
|---|---|
| `sprzeczne` | twierdzenie (przy polemice: stanowisko mówcy, przy wniosku: wniosek) przeczy ustaleniu AR6 |
| `zgodne` | twierdzenie odpowiada ustaleniu AR6 |
| `brak_podstaw` | pozostałe: AR6 się tym nie zajmuje (dane krajowe, zdarzenia po AR6, prawo UE) albo twierdzenie jest zbyt ogólne |

Oceniamy wobec AR6, a nie wobec własnej wiedzy. `sprzeczne` i `zgodne` wymagają wskazania rozstrzygającego fragmentu
(pole `ar6`).

**Kierunek i skala.**
- Twierdzenie, które przeczy kierunkowi ustalenia AR6 (zjawisko nie zachodzi, zachodzi odwrotnie, człowiek nie ma na nie
  wpływu), jest `sprzeczne`.
- Gdy kierunek się zgadza, a twierdzenie przesadza albo umniejsza skalę, `sprzeczne` jest tylko wtedy, gdy fragment AR6
  podaje wielkość albo termin, z którymi twierdzenie się nie zgadza. Gdy AR6 takiej wielkości nie podaje, werdykt to
  `brak_podstaw`. Przykłady: „poziom morza podnosi się o kilka centymetrów rocznie” jest `sprzeczne` (WGI SPM A.1.7:
  3,7 mm rocznie w latach 2006–2018); „powódź stulecia będziemy mieć co roku” to `brak_podstaw`, bo AR6 mówi, że powodzie
  w Europie Zachodniej i Środkowej, w tym w Polsce, będą częstsze (WGI TS.4.3.2.5), ale nie podaje, jak często.
- Kierunek zmian klimatu w Polsce (opady, powodzie, susze, temperatura) oceniamy wobec ustaleń AR6 dla regionu Europa
  Zachodnia i Środkowa (*West and Central Europe*, WCE), do którego należy Polska.

**Liczby i statystyki.** `sprzeczne` albo `zgodne` tylko wtedy, gdy fragment AR6 podaje tę samą wielkość co
twierdzenie: ten sam obszar (świat, region, kraj), ten sam gaz (CO2 albo wszystkie gazy cieplarniane), ten sam okres
i tę samą miarę (emisja roczna, skumulowana, na mieszkańca). Gdy fragment podaje inną wielkość, werdykt to
`brak_podstaw`, nawet jeśli liczby się różnią albo przypadkiem się zgadzają. Europa to nie Unia Europejska. Twierdzenie
o stanie obecnym („już”, „teraz”) porównujemy z najnowszym okresem, który podaje AR6. Gdy twierdzenie nie mówi, o jaką
miarę chodzi, a fragment podaje konkretną, to inna wielkość. Liczb z rysunków, których nie da się jednoznacznie
przypisać do regionu, nie używamy.

**Koszty, ceny i wykonalność.** Oceniamy tylko twierdzenia ogólne o technologii albo źródle energii: o koszcie energii
z danego źródła, o tym, czy jedne źródła mogą zastąpić inne, czy system oparty na OZE może działać niezawodnie. Fragment
AR6 musi mówić o tej samej mierze (np. o koszcie jednostkowym energii elektrycznej, a nie o cenie dla odbiorcy). Werdykt
`brak_podstaw` dostają twierdzenia o:
- Polsce, UE i innych konkretnych krajach, regionach, elektrowniach i inwestycjach;
- obecnych cenach, rachunkach, taryfach i dopłatach;
- skutkach polityki klimatycznej dla cen, przemysłu i gospodarki kraju albo regionu. AR6 podaje skutki globalne (np. dla
  PKB świata, WGIII SPM C.12.2) i nie rozstrzyga o gospodarce Polski ani UE.

**Redukcja emisji w jednym regionie.** Twierdzenie, że redukcja emisji w jednym kraju albo regionie (np. w Polsce,
w UE) nic nie zmieni w sprawie klimatu, przeczy ustaleniu AR6, że ocieplenie zależy od skumulowanej emisji CO2 (WGI
SPM D.1, D.1.1), więc jest `sprzeczne`.

**Źródła w AR6.** Oceniamy tylko wobec streszczeń SPM (*Summary for Policymakers*) i TS (*Technical Summary*) WGI,
WGII i WGIII: najpierw SPM, potem TS. Rozdziałów (także przez odsyłacze w nawiasach klamrowych, np. `{2.3}`) ani
raportu syntetycznego (SYR) nie używamy, bo model widzi tylko SPM i TS. Fragment wskazujemy numerem ustalenia (np.
`WGIII TS.5.1`). Numer strony w polu `ar6` modelu to strona w pliku PDF danej części, a nie numer drukowany (zgadzają
się tylko w SPM WGI).

**Data.** WGI ukazał się 9.08.2021, WGII 28.02.2022, WGIII 4.04.2022, czyli przed początkiem okresu, więc AR6 jest
punktem odniesienia dla wszystkich wypowiedzi.

## 9. Przykłady z korpusu

Identyfikator to `wypowiedz_id` z `data/processed/korpus_plenarne.parquet`; wszystkie przykłady pochodzą z populacji.

### 9.1. `klimat`

| wypowiedź | fragment | `klimat` | dlaczego |
|---|---|---|---|
| `10_60_2026-06-17_269` | „Czy osiągnięcie dekarbonizacji w europejskiej polityce klimatycznej, manipulacyjnie nazywanej neutralnością klimatyczną, ma sens?” | 1 | polityka klimatyczna jest przedmiotem całej wypowiedzi (emisje świata i UE, sens redukcji) |
| `10_18_2024-09-25_107` | „Naukowcy są tutaj jednoznaczni, że nie chodzi o spory na temat klimatu, tylko chodzi o to, jak będą wyglądały zjawiska pogodowe (…). A sytuacja będzie krytyczna, jeśli chodzi o efekty tych zmian klimatycznych.” | 1 | 4,5 tys. słów o powodzi, ale jeden akapit mówi o skutkach zmiany klimatu |
| `10_41_2025-09-25_308` | „To także przeciwdziałanie skutkom zmian klimatycznych, które w szczególny sposób oddziałują na obszary rzeczne i podmokłe.” | 1 | jedno zdanie mówi, na co oddziałuje zmiana klimatu; wcześniejsze „W dobie narastających wyzwań ekologicznych, takich jak postępujące zmiany klimatyczne” to samo tło |
| `10_43_2025-10-16_309` | „ETS 2 podwyższy też drastycznie koszty ogrzewania w naszych domach.” | 1 | skutek instrumentu polityki klimatycznej dla cen |
| `10_42_2025-10-08_221` | „Wiatraki produkują najdroższy prąd, w dodatku niestabilny i jeszcze niszczą środowisko naturalne.” | 1 | twierdzenie o koszcie i niezawodności źródła energii |
| `10_10_2024-04-25_124` | „Proponowany przez pana eksperyment na tak dużym obszarze w obliczu obserwowanych zmian klimatycznych jest niezwykle niebezpieczny dla przyszłości lasów w Polsce.” | 0 | zmiana klimatu jako okoliczność; zdanie nie mówi, co robi z lasami; przedmiot: gospodarka leśna |
| `10_10_2024-04-25_40` | „Wszystkie zmiany dla rolników to jest jakaś kpina, nie ma żadnych zmian w zielonym ładzie dla rolników, to ugorowanie to jest przejście z deszczu pod rynnę, jest to oszukiwanie polskich rolników.” | 0 | Zielony Ład w rolnictwie bez odniesienia do emisji i klimatu |
| `10_27_2025-01-23_254` | „W związku z nowelizacją dyrektywy w sprawie systemu handlu przydziałami uprawnień do emisji gazów cieplarnianych w Unii do systemu włączono sektory budownictwa mieszkaniowego i transportu drogowego.” | 0 | treść przepisu i procedura (zezwolenia dla dostawców paliw); o skutkach ETS2 mówca nic nie twierdzi |

### 9.2. Twierdzenia i werdykt

| wypowiedź | fragment | zapis | werdykt |
|---|---|---|---|
| `10_22_2024-11-20_257` | „Pani minister wspomniała tu o konieczności walki z emisją CO2, co się zasadza na przekonaniu, że emisja CO2 powoduje globalne ocieplenie. (…) Nawet przy założeniu, że ta mitologia jest prawdziwa, problem polega na tym, pani minister, że emisja CO 2 w Unii Europejskiej to jest 8% światowej emisji. W Polsce to ok. 1%. Nawet jak ją zlikwidujemy, to nic to nie zmieni, zwłaszcza że likwidowany w Unii Europejskiej przemysł wysokoemisyjny, na czym tracimy gospodarczo, przenosi się do Chin czy Indii.” | (a) polemika, stanowisko mówcy: emisja CO2 nie powoduje globalnego ocieplenia; (b) UE emituje 8% światowej emisji CO2, Polska 1%; (c) likwidacja emisji w UE nic nie zmieni; (d) przemysł wysokoemisyjny przenosi się z UE do Chin i Indii | (a) `sprzeczne` (WGI SPM A.1); (b) `brak_podstaw` (inny obszar); (c) `sprzeczne` (WGI SPM D.1.1); (d) `brak_podstaw` (gospodarka UE) |
| `10_27_2025-01-23_218` | „A przyczyna tego wszystkiego to są opłaty ETS, to jest to szaleństwo ideologiczne zielonej energii, te głupoty, że krowy są odpowiedzialne za ocieplenie klimatu.” | (a) opłaty ETS są przyczyną wysokich cen prądu w Polsce; (b) wniosek: hodowla bydła nie przyczynia się do ocieplenia; „szaleństwo ideologiczne” pomijamy (ocena) | (a) `brak_podstaw` (ceny w Polsce); (b) `sprzeczne` (WGIII TS.5.6.1: emisje metanu z rolnictwa rosną, głównie z fermentacji jelitowej przeżuwaczy) |
| `10_42_2025-10-08_221` | jak w 9.1 | (a) energia z wiatru jest najdroższa; (b) produkcja energii z wiatru jest zmienna; „niszczą środowisko” pomijamy (nie dotyczy klimatu) | (a) `sprzeczne` (WGIII TS.5.1: energia z fotowoltaiki i wiatru jest w wielu regionach tańsza niż z paliw kopalnych); (b) `zgodne` (WGIII TS.5.1: wiatr i fotowoltaika jako źródła zmienne) |
| `10_11_2024-05-15_88` | „…to w Polsce, szanowni państwo, na lądzie tak dużo wiatrów nie wieje. Realnie wiatraki mają ok. 15% wydajności, czyli jest to droga i niezbyt efektywna inwestycja.” | energia z wiatraków na lądzie jest w Polsce droga, bo wiatr wieje za słabo | `brak_podstaw` (Polska) |
| `10_5_2024-02-07_117` | „…brednia klimatyzmu (…) jednak wali się (…) bo jednak deszcz pada, tak jak padał, śnieg pada, tak jak padał, mniej więcej, w pewnym tam przedziale.” | (a) suma opadów w Polsce się nie zmienia; (b) wniosek: zmiana klimatu nie zachodzi | (a) `sprzeczne` (WGI TS.4.3.2.5: średnie roczne opady w Europie Zachodniej i Środkowej wzrosły od początku XX w.); (b) `sprzeczne` (WGI SPM A.1) |
