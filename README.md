# AMC — wypowiedzi sejmowe a konsensus naukowy

Analiza wypowiedzi w Sejmie RP (posiedzenia plenarne i komisje, kadencje VIII–X) pod kątem zgodności
lub sprzeczności z konsensusem naukowym (zdrowie: szczepienia i COVID-19; klimat).

**Dokumentacja danych** (pliki, kolumny, decyzje i ograniczenia): [docs/dane.md](docs/dane.md).
**Jak powstały słowniki tematyczne i markery:** [docs/slowniki.md](docs/slowniki.md).

## Pipeline

```
1. pobieranie   src/fetch_sejm.py, src/fetch_komisje.py  → data/raw/      (odpowiedzi API, nie w repo)
                                                          → data/interim/  (tabele wypowiedzi, historia klubów)
2. korpus       src/build_corpus.py                       → data/processed/korpus_{plenarne,komisje}.parquet
3. analiza      notebooks/01_eda_wypowiedzi.ipynb          (wczytuje korpus: amc.corpus.load)
                src/report_sceptycyzm.py                   → przegląd wypowiedzi z markerem sceptycyzmu (HTML + CSV)
4. LLM etap A   src/classify.py                           → data/processed/llm_*.jsonl (Bielik w Ollamie, prompty: prompts/)
```

Każdy krok można wznowić: pobieranie pomija pliki, które już istnieją.

```bash
pip install -r requirements.txt

for t in 8 9 10; do python src/fetch_sejm.py --term $t; done                       # posiedzenia plenarne + kluby
for t in 8 9 10; do python src/fetch_komisje.py --term $t --committees ZDR OSZ ESK RRW; done
python src/build_corpus.py                                                         # korpus do analizy
python src/report_sceptycyzm.py                                                    # opcjonalnie
python src/classify.py --source rok --n 60                                         # etap A na próbie 60 wypowiedzi / rok (Ollama)
pytest                                                                             # testy jednostkowe
```

`fetch_komisje.py` przypisuje klub z historii klubów budowanej przez `fetch_sejm.py`, więc najpierw uruchom `fetch_sejm.py`.

## Kod

Cała logika jest w pakiecie `src/amc/`; skrypty w `src/` to cienkie nakładki CLI.

| moduł | odpowiedzialność |
|---|---|
| `amc/paths.py` | ścieżki projektu, kadencje |
| `amc/http.py` | pobieranie z API z ponawianiem, zapis atomowy |
| `amc/text.py` | HTML → tekst, czyszczenie wypowiedzi (nagłówek, wtrącenia z sali, stopka), fragmenty z kontekstem, odnajdywanie cytatów LLM w tekście |
| `amc/komisje.py` | podział zapisu posiedzenia komisji na wypowiedzi (HTML, zapasowo PDF) |
| `amc/speakers.py` | rola mówcy, dopasowanie posła, klub w dniu wypowiedzi, mapowanie klub → blok |
| `amc/topics.py` | słowniki tematów, markery `nauka` / `sceptycyzm`, progi, kolumny tematyczne |
| `amc/sampling.py` | filtr regex (≥ 1 trafienie słownika), okresy H1 (przed COVID / COVID / po ChatGPT), warstwowe losowanie rok × filtr / spoza filtra z wagami N/n |
| `amc/llm.py` | etap A w Ollamie: krok 1 (kandydaci z rodzajem), krok 2 (weryfikacja kandydatów `naukowe` z kontekstem), wykrywanie przepełnienia kontekstu |
| `amc/llm_results.py` | wczytanie wyników etapu A z wagami próby i metadanymi korpusu, kandydaci i twierdzenia, estymatory ważone, bootstrap w warstwach roku, kappa (test–retest) |
| `amc/corpus.py` | budowa i wczytywanie korpusu (filtr wypowiedzi merytorycznych: bez prowadzącego, ≥ 40 słów) |
| `amc/viz.py` | paleta i styl wykresów |

Regułę (próg, słownik, mapowanie klubów) zmienia się w jednym miejscu w `amc/`, a potem przebudowuje korpus
(`python src/build_corpus.py`) i przelicza notatnik.

## Korpus (`data/processed/korpus_*.parquet`)

Jeden wiersz = jedna wypowiedź, klucz `wypowiedz_id`. Najważniejsze kolumny: `tekst` (oczyszczony), `liczba_slow`,
`rola` (poseł / prowadzący / rząd / inni), `member_id`, `klub` (w dniu wypowiedzi), `blok`, `merytoryczna`,
`data` / `miesiac` / `rok`, liczby trafień słowników (`covid`, `klimat`, …, `nauka`, `sceptycyzm`) i flagi
wypowiedzi tematycznych (`<temat>_tem`, `zdrowie_tem`, `dowolny_tem`). Korpus komisji ma dodatkowo `komisja`,
`etykieta` (mówca) i `porzadek` (porządek obrad).

Kolejne etapy (np. klasyfikacja LLM) powinny wczytywać korpus i zapisywać wyniki z kluczem `wypowiedz_id`.

## Struktura katalogów

```
data/raw/        surowe odpowiedzi API (poza repo, poza mp.json)
data/interim/    tabele z API (parquet poza repo; historia klubów w repo)
data/processed/  korpus (poza repo) i zagregowane tabele z EDA
data/gold/       ręczna anotacja (do zrobienia)
prompts/         prompty LLM: etap_a_v2 (krok 1), weryfikacja_v1 (krok 2; v0 dla wyników sprzed naprawy)
figures/         wykresy z notatnika
notebooks/       analiza
tests/           testy jednostkowe (pytest)
```
