# Dane: co przygotowujemy i jak z tego korzystać

Ten dokument opisuje wszystkie pliki z danymi w projekcie: skąd się biorą, co zawierają i na co uważać.
Jak uruchomić pipeline — patrz [README](../README.md).

**Jeśli chcesz tylko analizować:** wczytaj gotowy korpus.

```python
import sys; sys.path.insert(0, "src")
from amc import corpus
df = corpus.load("plenarne")          # albo "komisje"
m = df[df["merytoryczna"]]            # wypowiedzi brane do analizy tematycznej
```

---

## Źródło

Wszystko pochodzi z oficjalnego **API Sejmu RP** (`https://api.sejm.gov.pl`), kadencje **VIII (2015–2019),
IX (2019–2023), X (2023–)**.

| co | endpoint API | uwagi |
|---|---|---|
| stenogramy posiedzeń plenarnych | `/sejm/term{T}/proceedings/{n}/{data}/transcripts` | jedna wypowiedź = jeden rekord z id posła |
| zapisy posiedzeń komisji | `/sejm/term{T}/committees/{KOD}/sittings/{nr}/html` (zapasowo `/pdf`) | jeden dokument na posiedzenie, dzielony na wypowiedzi przez nas |
| posłowie | `/sejm/term{T}/MP` | klub = stan na dzień pobrania |
| głosowania | `/sejm/term{T}/votings/...` | jedno głosowanie dziennie — z niego bierzemy klub posła w danym dniu |

Pobrane komisje: **ZDR** (Zdrowia), **OSZ** (Ochrony Środowiska), **ESK** (Energii, Klimatu i Aktywów Państwowych),
**RRW** (Rolnictwa i Rozwoju Wsi).

---

## Warstwy danych

| warstwa | katalog | w repo? | kto tworzy |
|---|---|---|---|
| surowe odpowiedzi API | `data/raw/term{T}/` | nie (poza `mp.json`) | `fetch_sejm.py`, `fetch_komisje.py` |
| tabele z API | `data/interim/` | tylko historia klubów (CSV) | `fetch_sejm.py`, `fetch_komisje.py` (krok `build`) |
| **korpus do analizy** | `data/processed/korpus_*.parquet` | nie (duże; odtwarzalne) | `build_corpus.py` |
| wyniki EDA | `data/processed/eda_*.csv`, `figures/` | tak | notatnik, `report_sceptycyzm.py` |
| ręczna anotacja | `data/gold/` | tak | (do zrobienia) |

Zasada: **nie edytujemy ręcznie plików w `raw/`, `interim/` ani korpusu** — zmieniamy kod w `src/amc/` i przebudowujemy.

### `data/raw/term{T}/`

| plik | zawartość |
|---|---|
| `mp.json` | lista posłów kadencji (id, imię, nazwisko, klub dzisiaj, okręg…) |
| `transcripts/{posiedzenie}_{data}.jsonl` | metadane wypowiedzi + surowy HTML, jeden wiersz = jedna wypowiedź |
| `votings/{posiedzenie}_{data}.json` | lista głosów z jednego głosowania danego dnia (`member_id`, `klub`) |
| `komisje/{KOD}/sittings.json` | lista posiedzeń komisji (data, porządek obrad, status, posiedzenia wspólne) |
| `komisje/{KOD}/{nr}.html` / `.pdf` | zapis przebiegu posiedzenia; `{nr}.missing` = API nie zwróciło zapisu |

### `data/interim/`

| plik | jeden wiersz = | uwagi |
|---|---|---|
| `wypowiedzi_term{T}.parquet` | wypowiedź na posiedzeniu plenarnym | tekst po konwersji z HTML, bez nagłówka z numerem druku |
| `komisje_wypowiedzi_term{T}.parquet` | wypowiedź na posiedzeniu komisji | podział po etykietach mówców |
| `posel_klub_term{T}.csv` | okres członkostwa posła w klubie | `member_id, klub, od, do` — z list głosowań |

---

## Korpus: `data/processed/korpus_plenarne.parquet` i `korpus_komisje.parquet`

Jeden wiersz = jedna wypowiedź. Korpus zawiera **wszystkie** wypowiedzi (także proceduralne) — do analizy
tematycznej filtruj `merytoryczna == True`.

| kolumna | typ | opis |
|---|---|---|
| `wypowiedz_id` | str | **stały klucz**: `{kadencja}_{posiedzenie}_{data}_{num}` (plenarne), `{kadencja}_{KOD}_{nr}_{num}` (komisje). Łącz po nim wyniki kolejnych etapów. |
| `kadencja` | int | 8, 9, 10 |
| `data`, `miesiac`, `rok` | datetime / int | dzień posiedzenia, początek miesiąca, rok |
| `num` | int | kolejność wypowiedzi w ramach dnia / posiedzenia |
| `tekst` | str | **oczyszczony** tekst: bez nagłówka stenogramu, wtrąceń z sali w nawiasach i stopki |
| `liczba_slow` / `liczba_slow_surowa` | int | po / przed czyszczeniem |
| `rola` | str | `poseł`, `prowadzący` (marszałek / przewodniczący komisji), `rząd` (ministrowie, sekretarze stanu), `inni` (eksperci, NFZ, RPO, organizacje, goście) |
| `member_id` | int | id posła z API; **0 = osoba spoza Sejmu** |
| `klub` | str | klub posła **w dniu wypowiedzi** (z głosowań); w komisjach zapasowo z etykiety |
| `blok` | str | klub zmapowany na blok o ciągłej tożsamości między kadencjami (PiS, KO, Kukiz'15, Polska 2050, Lewica, PSL, Konfederacja, Inne / niez.); puste dla nie-posłów. Mapowanie: `amc/speakers.py` → `KLUB_BLOK` |
| `merytoryczna` | bool | `rola != "prowadzący"` i `liczba_slow >= 40` |
| `szczepienia`, `covid`, `klimat`, `energia_jadrowa`, `gmo`, `5g_promieniowanie`, `smog`, `in_vitro` | int | liczba trafień słownika tematu |
| `<temat>_tem` | bool | **wypowiedź tematyczna**: ≥ 3 trafienia (`topics.PROG`) |
| `zdrowie_tem` / `zdrowie_wzm` | bool | szczepienia lub COVID: tematyczna / jakakolwiek wzmianka |
| `dowolny_tem` | bool | tematyczna w którymkolwiek temacie |
| `nauka` | int | odwołania do nauki („naukowcy”, „badania wykazały”, WHO, PAN, „konsensus naukowy”…) |
| `sceptycyzm` | int | zwroty podważające naukę („tzw. pandemia”, „eksperyment medyczny”, „klimatyzm”, „segregacja sanitarna”…) |

Tylko w `korpus_plenarne`: `posiedzenie`, `mowca`, `funkcja`, `klub_dzis` (klub w dniu pobrania), `start`, `koniec`,
`niewygloszona` (oświadczenie złożone do protokołu), `rapporteur`, `secretary`.

Tylko w `korpus_komisje`: `komisja` (kod), `komisje` (wszystkie kody, gdy posiedzenie wspólne), `posiedzenie_nr`,
`etykieta` (mówca tak jak w zapisie, np. „Poseł Jan Kowalski (PiS)”), `klub_etykieta`, `porzadek` (porządek obrad),
`zrodlo` (`html` / `pdf`).

---

## Decyzje i ograniczenia — przeczytaj przed analizą

1. **Słowniki to filtr, nie klasyfikacja.** Trafienie „sceptycyzm” oznacza użycie zwrotu, nie stanowisko —
   część to cytowanie lub polemika („to nie jest sanitaryzm”). Precyzja i czułość słowników nie są jeszcze zmierzone.
2. **Klub na dzień wypowiedzi** pochodzi z głosowań; przed pierwszym głosowaniem posła bierzemy pierwszy znany klub.
   `klub_dzis` (stan na dzień pobrania) służy tylko jako zapas.
3. **Bloki** łączą rozłamy z klubem macierzystym, gdy (prawie) wszyscy członkowie przyszli z jednego klubu
   (RozwojPlus → PiS, Centrum → Polska 2050); małe koła o mieszanym rodowodzie → „Inne / niez.”.
4. **Komisje:** w zapisach jest dużo osób spoza Sejmu (`member_id == 0`, `rola == "inni"`) — przy analizie
   stanowisk polityków trzeba je świadomie uwzględnić lub odfiltrować. ~2% posiedzeń ma tylko skrócony zapis.
   Kilka etykiet posłów (~0,3%) nie dopasowuje się z powodu literówek w samych zapisach.
5. **Wtrącenia prowadzącego** wewnątrz wypowiedzi plenarnej („Wicemarszałek X: …”) zostają w tekście — niewielki szum.
6. **Kadencja X trwa** — dane kończą się na dniu pobrania (październik 2026); porównując kadencje, normalizuj
   (np. na 1000 wypowiedzi), a nie licz wartości bezwzględnych.

---

## Jak zmienić regułę

| chcę zmienić… | plik | potem |
|---|---|---|
| słownik tematu / marker / próg | `src/amc/topics.py` | `python src/build_corpus.py`, przelicz notatnik |
| mapowanie klub → blok | `src/amc/speakers.py` (`KLUB_BLOK`) | jw. |
| czyszczenie tekstu | `src/amc/text.py` | jw. |
| filtr wypowiedzi merytorycznych | `src/amc/corpus.py` (`MIN_SLOW`) | jw. |
| zbiór komisji | `python src/fetch_komisje.py --committees …` | `build_corpus.py` |

Po zmianie uruchom `pytest` — testy pilnują podstawowych reguł (czyszczenie, dopasowanie posłów, klub na dzień, słowniki).
