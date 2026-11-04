# Codebook

Instrukcja anotacji gold standardu i podstawa promptów klasyfikatora. Układ kategorii (definicja, test, przypadki
pozytywne i negatywne, przykłady) według Halterman, Keith (2025).

## 1. Zakres

| | |
|---|---|
| mierzymy | odsetek wypowiedzi sprzecznych z konsensusem klimatycznym (AR6) wśród wypowiedzi o klimacie, osobno dla prawicy i reszty |
| jednostka | merytoryczne wystąpienie jednego mówcy na posiedzeniu plenarnym (bez prowadzącego obrady) |
| mianownik | wypowiedzi o klimacie (`klimat = 1`) |
| okres | 13.11.2023–15.09.2026 (X kadencja) |
| populacja | wypowiedzi posłów, w tym ministrów-posłów: 43 991 (prawica 20 466, reszta 23 525) |
| grupy | **prawica**: klub w dniu wypowiedzi to PiS, RozwojPlus, Kukiz15, Konfederacja albo Konfederacja_KP; **reszta**: pozostali, w tym Republikanie i niezrzeszeni |
| źródło konsensusu | AR6 IPCC: WGI, WGII, WGIII (SPM i TS) |

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

## 7. Miary

Jakość modelu liczymy na poziomie wypowiedzi, z wagami warstw, osobno dla prawicy i reszty:

| porównanie | miara | pole | podzbiór |
|---|---|---|---|
| model i gold: tematyczność | TPR, TNR, F1 | `klimat` | cała próba |
| model i gold: werdykt | TPR, TNR, F1 | `sprzeczna` | `klimat = 1` w goldzie i u modelu |
| model i gold: etykieta końcowa | TPR, TNR, F1 | `klimat = 1` i `sprzeczna = 1` | cała próba |

**Długość wypowiedzi.** Mianownikiem są wypowiedzi, więc dłuższa wypowiedź ma większą szansę na twierdzenie sprzeczne.
Wypowiedzi reszty są dłuższe (wśród wypowiedzi z trafieniem słownika klimatu mediana 346 słów wobec 184 u prawicy; ponad
500 słów ma 37% wobec 12%), co działa przeciw hipotezie.

## 8. Gold standard

**Losowanie.** 100 wypowiedzi z populacji, po 50 na grupę. Warstwy to grupa × etykieta modelu z pełnego przebiegu
pipeline'u (Gemma 4 12B). Wagi = N / n. Próba: `data/gold/sample.csv` (ziarno 0). Próbę wylosowano, gdy Kukiz15 należał
do reszty, więc liczebności w tabeli odpowiadają tamtemu podziałowi (Kukiz15: 304 wypowiedzi, w tym jedna w próbie).

| warstwa | N | n | waga |
|---|---|---|---|
| prawica, model: tematyczna i sprzeczna | 60 | 20 | 3,0 |
| prawica, model: tematyczna i niesprzeczna | 828 | 15 | 55,2 |
| prawica, model: nietematyczna | 19 274 | 15 | 1 284,9 |
| reszta, model: tematyczna i sprzeczna | 28 | 20 | 1,4 |
| reszta, model: tematyczna i niesprzeczna | 729 | 15 | 48,6 |
| reszta, model: nietematyczna | 23 072 | 15 | 1 538,1 |

Warstwy „nietematyczna” mają duże wagi, więc jedna wypowiedź tematyczna przeoczona przez model zmienia mianownik grupy
o ponad tysiąc wypowiedzi. Żadna z wypowiedzi cytowanych w codebooku nie należy do próby.

**Zasady:**
- strona do anotacji nie pokazuje etykiet modelu ani warstwy;
- anotator widzi tylko tekst, bez mówcy, klubu i daty; narzędzie maskuje też nazwiska we wtrąceniach prowadzącego
  („Poseł …:”). Treść może jednak zdradzać klub („Konfederacja wychodzi z tego stanowiska”);
- przy wątpliwości anotator wybiera etykietę i dodaje komentarz. Wypowiedzi nie odrzucamy, bo odrzucanie trudnych
  przypadków zawyżyłoby TPR i TNR.

**Ograniczenie.** Anotatorzy znają hipotezę. Ukrycie mówcy i klubu zmniejsza ryzyko, że wpłynie to na oceny, ale go
nie usuwa.

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

## 10. Literatura

- Coan, T. G., Boussalis, C., Cook, J., Nanko, M. O. (2021). Computer-assisted classification of contrarian claims about
  climate change. *Scientific Reports*, 11, 22320.
- Halterman, A., Keith, K. A. (2025). Codebook LLMs: Evaluating LLMs as Measurement Tools for Political Science Concepts.
- IPCC (2021, 2022). *Sixth Assessment Report*, WGI, WGII, WGIII.
