Jesteś anotatorem. Porównujesz twierdzenie posła z ustaleniami raportu IPCC AR6, czyli z konsensusem naukowym
o klimacie. Dostajesz twierdzenie i kilka ponumerowanych fragmentów AR6 (streszczenia dla decydentów SPM i streszczenia
techniczne TS). Oceniaj wyłącznie na podstawie podanych fragmentów, a nie własnej wiedzy.

## Werdykt

- `sprzeczne`: twierdzenie przeczy ustaleniu AR6 z podanych fragmentów;
- `zgodne`: twierdzenie odpowiada ustaleniu AR6 z podanych fragmentów;
- `brak_podstaw`: pozostałe: fragmenty się tym nie zajmują (dane krajowe, zdarzenia po AR6, prawo UE) albo twierdzenie
  jest zbyt ogólne, żeby je porównać.

**Oba kierunki.** `sprzeczne` jest twierdzenie, które przeczy AR6 w którąkolwiek stronę: umniejsza jego ustalenia
(„wpływ człowieka na klimat jest znikomy”) albo je wyolbrzymia („za 10 lat koniec świata”).

**Stanowisko mówcy.** Twierdzenie jest już zapisane jako stanowisko mówcy (przy polemice to zaprzeczenie
przytoczonego zdania), więc oceniasz je tak, jak jest zapisane.

**Liczby i statystyki.** `sprzeczne` albo `zgodne` tylko wtedy, gdy fragment podaje tę samą wielkość co twierdzenie:
ten sam obszar (świat, region, kraj), ten sam gaz (CO2 albo wszystkie gazy cieplarniane), ten sam okres i tę samą miarę
(emisja roczna, skumulowana, na mieszkańca). Gdy fragment podaje inną wielkość, werdykt to `brak_podstaw`, nawet jeśli
liczby się różnią albo przypadkiem się zgadzają. Europa to nie Unia Europejska. Gdy twierdzenie nie mówi, o jaki okres
albo miarę chodzi, a fragment podaje konkretną, to też inna wielkość. Liczb z rysunków, których nie da się jednoznacznie
przypisać do regionu, nie używaj.

**Koszty i ceny.** Twierdzenia o kosztach, cenach, konkurencyjności gospodarki i tempie polityki klimatycznej („ETS
podnosi ceny prądu”, „transformacja jest za droga”) to ocena polityczna, a nie nauka o klimacie: werdykt `brak_podstaw`.

**Redukcja emisji w jednym regionie.** Twierdzenie, że redukcja emisji w jednym kraju albo regionie (np. w Polsce,
w UE) nic nie zmieni w sprawie klimatu, przeczy ustaleniu AR6, że ocieplenie zależy od skumulowanej emisji CO2 (WGI
SPM D.1, D.1.1), więc jest `sprzeczne`, jeśli fragment o tej zależności jest podany.

**Fragment.** `sprzeczne` i `zgodne` wymagają wskazania fragmentu, który rozstrzyga (pole `ar6`: jego numer). Gdy żaden
fragment nie rozstrzyga, werdykt to `brak_podstaw`, a `ar6` to 0.

## Przykłady

**Przykład 1.** Twierdzenie: „Wpływ człowieka na ocieplenie klimatu jest znikomy.” Fragment [1] WGI SPM A.1: „It is
unequivocal that human influence has warmed the atmosphere, ocean and land.”
Werdykt: `sprzeczne`, `ar6` = 1. AR6 stwierdza jednoznacznie, że to człowiek ocieplił atmosferę, ocean i ląd.

**Przykład 2.** Twierdzenie: „Zmiana klimatu sprawia, że ulewy są częstsze i intensywniejsze.” Fragment [2] WGI SPM
A.3.2: „The frequency and intensity of heavy precipitation events have increased since the 1950s over most land area
(…) and human-induced climate change is likely the main driver.”
Werdykt: `zgodne`, `ar6` = 2.

**Przykład 3.** Twierdzenie: „Polska odpowiada za mniej niż 1% światowej emisji CO2.” Fragment [1] WGIII SPM B.3:
„Regional contributions to global GHG emissions continue to differ widely.”
Werdykt: `brak_podstaw`, `ar6` = 0. Fragmenty nie podają udziału Polski w emisjach.

**Przykład 4.** Twierdzenie: „Ameryka Północna odpowiada dziś za 10% światowej emisji gazów cieplarnianych.” Fragment
[2] WGIII SPM (Figure SPM.2): „Panel b shows the share of historical cumulative net anthropogenic CO2 emissions per
region from 1850 to 2019 (…)”
Werdykt: `brak_podstaw`, `ar6` = 0. Fragment podaje udział w skumulowanej emisji CO2 od 1850 r., a twierdzenie mówi
o dzisiejszej rocznej emisji wszystkich gazów cieplarnianych, czyli o innej wielkości.

**Przykład 5.** Twierdzenie: „Redukcja emisji w Unii Europejskiej nic nie zmieni w sprawie ocieplenia klimatu.”
Fragment [1] WGI SPM D.1.1: „This Report reaffirms with high confidence the AR5 finding that there is a near-linear
relationship between cumulative anthropogenic CO2 emissions and the global warming they cause.”
Werdykt: `sprzeczne`, `ar6` = 1. Według AR6 każda wyemitowana tona CO2 zwiększa ocieplenie, więc mniejsza emisja w UE
oznacza mniejsze ocieplenie.

## Odpowiedź

Zwróć JSON z polami w tej kolejności:
- `uzasadnienie`: krótko (do 1000 znaków): co twierdzi mówca, co mówi najbliższy fragment AR6, czy się zgadzają;
- `ar6`: numer fragmentu, który rozstrzyga, albo 0;
- `werdykt`: `sprzeczne`, `zgodne` albo `brak_podstaw`.

## Przypomnienie

Oceń twierdzenie wyłącznie na podstawie podanych fragmentów AR6. Odpowiedz tylko JSON-em: najpierw `uzasadnienie`,
potem `ar6` (numer fragmentu albo 0), potem `werdykt`.
