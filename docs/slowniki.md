# Słowniki tematyczne i markery: jak powstały

Kod: [`src/amc/topics.py`](../src/amc/topics.py). Ten dokument wyjaśnia, skąd wzięły się słowniki, jakie mają założenia
i czego od nich **nie** oczekiwać.

## Na czym się opierają

**Słowniki zostały ułożone ręcznie, na etapie EDA, na podstawie wiedzy o tematach i o polskiej debacie publicznej.**
Nie pochodzą z gotowego leksykonu, korpusu treningowego ani publikacji, a ich precyzja i czułość **nie zostały zmierzone**.
Ich zadaniem było szybkie oszacowanie skali tematów, trendów w czasie i rozkładu między partiami — nie ostateczna klasyfikacja.

Literatura, na której warto oprzeć **kolejne wersje** (na razie *nie* była źródłem słów kluczowych):

| obszar | źródło | do czego |
|---|---|---|
| klimat | Coan, Boussalis, Cook, Nanko (2021), *Computer-assisted classification of contrarian claims about climate change*, Scientific Reports — taksonomia **CARDS** | kategorie twierdzeń kontrariańskich (np. „to się nie dzieje”, „nauka jest niewiarygodna”) jako schemat markerów i anotacji |
| szczepienia | Kata (2012), *Anti-vaccine activists, Web 2.0, and the postmodern paradigm*, Vaccine | katalog taktyk i motywów antyszczepionkowych |
| podważanie nauki | Mede, Schäfer (2020), *Science-related populism*, Public Understanding of Science; skala SciPop | konceptualizacja „lud vs elita naukowa” dla markera sceptycyzmu |
| tematy polityk | Comparative Agendas Project; korpus **ParlaMint / ParlaCAP** (Sejm 2015–2022 z etykietami tematów) | niezależna walidacja trafień tematycznych |

## Zasady konstrukcji

1. **Tematy z wyraźnym konsensusem naukowym.** Wybraliśmy obszary, w których da się mówić o zgodności lub sprzeczności
   z nauką: szczepienia, COVID-19, klimat, energetyka jądrowa, GMO, 5G / promieniowanie elektromagnetyczne, smog, in vitro.
2. **Rdzeń + dowolna końcówka** zamiast lematyzacji: `\bszczepion\w*` łapie *szczepionka, szczepionki, szczepionkami*.
   `\b` na początku pilnuje, żeby rdzeń nie trafiał w środek innego słowa. Wyszukiwanie bez rozróżniania wielkości liter.
3. **Frazy zamiast pojedynczych słów**, gdy słowo jest wieloznaczne: samo „klimat” łapałoby „klimat polityczny”, więc słownik
   klimatu zawiera frazy (`zmian\w* klimat\w*`, `gaz\w* cieplarnian\w*`, `neutralno\w* klimatyczn\w*`, `zielon\w* ład\w*`…).
4. **Precyzja ważniejsza niż czułość:** lepiej przegapić część wypowiedzi niż zalać się fałszywymi trafieniami.
5. **Dwa progi:** *wzmianka* = ≥ 1 trafienie; *wypowiedź tematyczna* = ≥ 3 trafienia (`PROG`) — temat jest wyraźnym
   wątkiem, a nie przelotnym odniesieniem.

## Dwa markery przekrojowe

| marker | co łapie | uwagi |
|---|---|---|
| `nauka` | odwołania do nauki: „naukowcy”, „badania naukowe”, „badania wykazały / pokazują”, „konsensus naukowy”, „według naukowców / badań”, WHO, Polska Akademia Nauk | „PAN” liczony tylko wersalikami (inaczej myli się ze zwrotem „pan”). Słowo „eksperci” celowo pominięte — w Sejmie to głównie eksperci od legislacji. |
| `sceptycyzm` | zwroty dystansujące i podważające: „tzw. pandemia”, „tak zwani eksperci”, „eksperyment medyczny”, „segregacja sanitarna”, „sanitaryzm”, „plandemia”, „klimatyzm”, „religia / histeria klimatyczna”, „ekoterroryzm”, „wielki reset” | Marker zwrotu, **nie stanowiska** — łapie też cytowanie i polemikę („to nie jest sanitaryzm”). Nie wykryje sprzeczności wyrażonej neutralnym językiem („nie ma badań na płodność”). |

## Jak były poprawiane

Słowniki testowaliśmy na pierwszych pobranych danych, czytając losowe trafienia, i zawężaliśmy wzorce dające szum:

| zmiana | powód |
|---|---|
| „rzekomo” → tylko w zestawieniach naukowych („rzekoma pandemia”, „rzekoma zmiana klimatu”…) | samo „rzekomo” łapało np. „rzekomo zrównoważony budżet” |
| usunięte „eksperci” z markera `nauka` | szum z debat legislacyjnych |
| tekst wypowiedzi czyszczony przed liczeniem (`amc/text.py`) | tytuł punktu obrad w nagłówku stenogramu („…Narodowego Programu Szczepień”) dawał fałszywe trafienia; wtrącenia z sali to słowa innych osób |
| naprawiony brakujący przecinek w liście `nauka` | sklejał wzorce „według badań/naukowców” i „WHO” — nie były wykrywane |

## Znane ograniczenia

* **szczepienia** łapią też weterynarię (np. szczepionka na ASF) i pozycje budżetowe,
* **5G** łapie głównie aukcję częstotliwości, nie wątki zdrowotne,
* **atomow\*** łapie też broń atomową,
* **in vitro** to bardziej spór etyczny niż naukowy; łapie też „diagnostykę in vitro”,
* **„klimatyzm”** to stosunkowo nowe słowo — wzrost markera `sceptycyzm` w czasie może częściowo odzwierciedlać zmianę języka, a nie stanowisk.

Przykłady trafień do ręcznej kontroli: notatnik `notebooks/01_eda_wypowiedzi.ipynb` (sekcja 4) oraz
`notebooks/eda_wypowiedzi_sceptyczne.html`. Podstawowe zachowanie słowników pilnują testy w `tests/test_topics.py`.

## Następne kroki

1. Ręcznie ocenić ~100 losowych trafień na temat (`data/gold/`) i zmierzyć precyzję; dla czułości — próbka wypowiedzi bez trafień.
2. Porównać trafienia z etykietami tematów CAP z ParlaMint / ParlaCAP (kadencje VIII–IX).
3. Przebudować `sceptycyzm` według kategorii CARDS (klimat) i motywów Katy (szczepienia).
4. Rozważyć lematyzację (Stanza / Morfeusz2) zamiast rdzeni.
5. Słowniki traktować jako sito wybierające kandydatów do klasyfikacji na poziomie twierdzeń (anotacja / LLM), nie jako klasyfikator.
