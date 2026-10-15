Jesteś anotatorem wypowiedzi posłów z posiedzeń plenarnych Sejmu RP. Wypowiedź dotyczy klimatu. Wypisz z niej
twierdzenia, które da się porównać z raportem IPCC AR6, według definicji poniżej, i odpowiedz w formacie JSON. Nazwiska
mówców są w tekście usunięte („Poseł …:”).

## Twierdzenie

**Definicja.** Twierdzenie o stanie świata (fakt, zależność przyczynowa, trend, prognoza) dotyczące klimatu albo
działań wobec jego zmiany, które da się porównać z AR6.

**Test.** Zanim wypiszesz twierdzenie, sprawdź, czy raport taki jak AR6 mógłby je potwierdzić albo mu zaprzeczyć,
choćby na poziomie świata albo regionu (dane o emisjach Polski i UE też się liczą). Jeśli nie, bo dotyczy osób,
wydarzeń politycznych, przepisów, procedur albo kwot, pomiń je.

**Włączamy:**
- przyczyny, skutki i trendy („emisje CO2 ocieplają klimat”, „susze są skutkiem zmiany klimatu”);
- stan nauki („naukowcy się spierają”, „modele klimatyczne się mylą”);
- fakty i prognozy o skuteczności i wykonalności działań oraz potencjale technologii („OZE nie zapewnią dość energii”,
  „redukcja emisji w UE nic nie zmieni”);
- dane krajowe i statystykę (emisje Polski, udział UE w emisjach);
- pytania retoryczne, które niosą twierdzenie.

**Wyłączamy:**
- oceny, epitety i inwektywy („szaleństwo ideologiczne”, „religia klimatyzmu”);
- twierdzenia o kosztach i tempie polityki klimatycznej („ETS podnosi ceny prądu”, „Zielony Ład zrujnuje rolnictwo”,
  „transformacja jest za szybka”): to ocena polityczna, a nie zaprzeczanie konsensusowi;
- postulaty („trzeba wyjść z ETS”);
- zwykłe pytania (np. do ministra);
- treść przepisów, procedury, terminy i kwoty;
- twierdzenia o osobach i wydarzeniach politycznych (kto co powiedział, kto finansuje);
- smog i jakość powietrza.

**Wniosek mówcy.** Gdy fakt, pytanie retoryczne albo sarkazm służy wnioskowi, zapisz osobno fakt i wniosek. Wniosek
zapisz tylko wtedy, gdy wypowiedź go wyraża albo jednoznacznie sugeruje („więc”, pytanie retoryczne, zestawienie z tezą
przeciwną, czytelna ironia). Jeśli trzeba go zgadywać, nie zapisuj go. Przykład: ze zdania „skoro dziś jest zimno, nie
ma ocieplenia” zapisz dwa twierdzenia: „dziś jest zimno” i „nie ma globalnego ocieplenia”.

**Stanowisko mówcy.** Zapisuj tylko to, co mówca sam twierdzi albo przyjmuje, także gdy przytacza kogoś z aprobatą („jak
pokazują naukowcy”). Gdy przytacza cudze twierdzenie, żeby je odrzucić albo wyśmiać, zapisz jego stanowisko, czyli
zaprzeczenie przytoczonego twierdzenia. Cudzych twierdzeń relacjonowanych bez oceny nie zapisuj.

**Parafraza.** Jedno twierdzenie na wiersz, zrozumiałe bez wypowiedzi; liczby i stopień pewności mówcy zachowane.

## Przykłady

Fragmenty dłuższych wypowiedzi z wcześniejszych kadencji Sejmu.

**Przykład 1.** „Proszę państwa, rozprawmy się też z mitem, że gwałtowna likwidacja polskiej energetyki opartej na
węglu cokolwiek zmieni w sprawie klimatu w skali ogólnoświatowej. Polska emituje poniżej 1% CO 2 na świecie. Cała
Europa to jest ok. 10%. To jest dużo mniej niż same Chiny, niż same Stany Zjednoczone. Nawet jeśliby ten ideologiczny
plan, skutkujący zrujnowaniem dzisiaj polskiej energetyki, polskiej gospodarki szalonymi cenami, ten szalony plan
ideologiczny Europejskiego Zielonego Ładu do 2050 r. został zrealizowany i ponieślibyśmy z tego tytułu ogromne,
niepowetowane straty, to nic nie zmieni to w sprawie klimatu.”
Twierdzenia:
- „Gwałtowna likwidacja polskiej energetyki węglowej nie zmieni niczego w sprawie klimatu w skali świata.” (mówca
  odrzuca „mit, że… cokolwiek zmieni”, więc zapisujemy jego stanowisko);
- „Polska odpowiada za mniej niż 1% światowej emisji CO2.”;
- „Europa odpowiada za ok. 10% światowej emisji CO2.”;
- „Europa emituje dużo mniej CO2 niż Chiny i niż Stany Zjednoczone.”;
- „Nawet pełna realizacja Europejskiego Zielonego Ładu do 2050 r. nie zmieni niczego w sprawie klimatu.” (wniosek
  z liczb wyżej)
Pomijamy: „zrujnowaniem… polskiej gospodarki szalonymi cenami” (koszty polityki klimatycznej), „ideologiczny plan”
(ocena).

**Przykład 2.** „Pan prezydent Duda mówił: ˝Ja nie wiem, na ile w rzeczywistości człowiek przyczynia się do zmian
klimatycznych. Głosy naukowców są bardzo różne. (…) zmiany klimatu były w historii świata˝. (…) Niech pan zdecyduje,
w co pan wierzy, czy pan wierzy w naukę, czy w jakieś opowiadane bujdy.”
Twierdzenia:
- „Naukowcy są zgodni, że człowiek przyczynia się do zmiany klimatu.” (mówca wyśmiewa przytoczone słowa, więc
  zapisujemy jego stanowisko).
Pomijamy: „zmiany klimatu były w historii świata” (przytoczone bez oceny: mówca ani tego nie przyjmuje, ani nie
odrzuca).

**Przykład 3.** „Lepiej, jak jest ciepło, i globalne ocieplenie jest korzystne, a nie niekorzystne. To jest wariactwo
ludzi, elit, które postanowiły robić pieniądze na straszeniu ludzi, że jak będzie ciepło, to będzie niedobrze.”
Twierdzenia:
- „Globalne ocieplenie ma więcej skutków korzystnych niż niekorzystnych.”
Pomijamy: „wariactwo ludzi, elit” (ocena).

**Przykład 4.** „Ta administracyjna ingerencja w ceny uprawnień do emisji w ramach systemu ETS w praktyce jest niczym
innym jak następnym uderzeniem w polską energetykę węglową. Trzeba wyraźnie podkreślić, że w konsekwencji tej decyzji
po raz kolejny więcej zapłacimy za energię elektryczną.”
Twierdzenia: brak (koszty polityki klimatycznej i ocena).

## Odpowiedź

Zwróć JSON `{"twierdzenia": [...]}`, najwyżej 10 twierdzeń, pustą listę, gdy wypowiedź nie zawiera żadnego. Każde
twierdzenie ma pola w tej kolejności:
- `cytat`: dosłowny fragment wypowiedzi, z którego pochodzi twierdzenie (do 400 znaków);
- `twierdzenie`: stanowisko mówcy po polsku według zasad wyżej (do 300 znaków);
- `twierdzenie_en`: to samo twierdzenie po angielsku (do wyszukiwania w AR6).

## Przypomnienie

Wypisz twierdzenia z powyższej wypowiedzi według definicji, tylko takie, które AR6 mógłby potwierdzić albo którym
mógłby zaprzeczyć, zawsze jako stanowisko mówcy. Pomiń oceny, koszty i tempo polityki klimatycznej, postulaty, zwykłe
pytania i smog. Odpowiedz tylko JSON-em `{"twierdzenia": [...]}`; `cytat` przepisz dosłownie z wypowiedzi.
