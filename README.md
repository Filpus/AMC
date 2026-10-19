# AMC — wypowiedzi sejmowe a konsensus naukowy

**Pytanie badawcze:** czy w okresie 13.11.2023–15.09.2026 odsetek wypowiedzi plenarnych posłów prawicy (klub w dniu
wypowiedzi: PiS, RozwojPlus, Konfederacja, Konfederacja_KP) sprzecznych z konsensusem naukowym dotyczącym klimatu
(raporty AR6 IPCC) był wyższy niż wśród pozostałych posłów? Mianownik to wypowiedzi o klimacie w danej grupie.

Lokalny LLM (Ollama, domyślnie Gemma 4 12B) oznacza wypowiedzi o klimacie, wypisuje z nich twierdzenia i ocenia je
wobec fragmentów AR6. Na ręcznie oznaczonej próbie warstwowej (gold standard) mierzymy jakość tych etykiet i liczymy
z niej odsetki w grupach.

Dane, kolumny i decyzje: [docs/dane.md](docs/dane.md). Słowniki tematów: [docs/slowniki.md](docs/slowniki.md).
Opcje, wejście i wyjście każdego skryptu: `python src/<skrypt>.py --help`.

## Schemat

```
dane      fetch_sejm.py, fetch_komisje.py → build_corpus.py → korpus wypowiedzi
pipeline  classify_topic.py     czy wypowiedź dotyczy klimatu (cała populacja: 43 991 wypowiedzi posłów)
          extract_claims.py     twierdzenia mówcy z wypowiedzi o klimacie
          verify_claims.py      werdykt wobec AR6: sprzeczne / zgodne / brak_podstaw (RAG; albo PaperQA2)
          label_statements.py   wypowiedź sprzeczna = co najmniej jedno twierdzenie sprzeczne
gold      gold_standard.py      próba warstwowa według etykiet modelu, strona do anotacji (jeden anotator albo podział próby; kappa drugiego anotatora opcjonalnie)
wynik     estimate.py           jakość etykiet (TPR/TNR/F1 z wagami), odsetki z golda, test hipotezy
```

## Instalacja

```bash
pip install -r requirements.txt
ollama pull gemma4:12b         # model pipeline'u (https://ollama.com)
ollama pull bge-m3             # embeddingi do wyszukiwania w AR6
```

Korpus i PDF-y AR6 są poza repo (dane z API, prawa IPCC); odtwarzają je polecenia niżej. Wyniki pełnego przebiegu
pipeline'u (Gemma 4 12B, ok. 15 h na GPU) są w repo.

## Uruchomienie

```bash
# dane
for t in 8 9 10; do python src/fetch_sejm.py --term $t; done                       # posiedzenia plenarne i kluby
for t in 8 9 10; do python src/fetch_komisje.py --term $t --committees ZDR OSZ ESK RRW; done   # komisje (eksploracja)
python src/build_corpus.py

# pipeline: każdy krok wznawia się od miejsca przerwania; odcisk populacji musi być 43991 / 2cdcf73e5b
python src/pipeline.py --n 200                    # szybki test na 200 wypowiedziach
python src/pipeline.py                            # cała populacja
python src/pipeline.py --weryfikator paperqa      # werdykt przez PaperQA2 zamiast RAG-a

# gold standard i test hipotezy
python src/estimate.py                            # warstwy, warunek rzadkości, wynik bez korekty
python src/gold_standard.py losuj                 # próba golda: data/gold/sample.csv i texts.csv
python src/gold_standard.py strona                # strona dla anotatora: data/gold/annotation.html
python src/extract_claims.py --ids data/gold/sample.csv   # werdykt modelu dla całej próby
python src/verify_claims.py --ids data/gold/sample.csv
python src/estimate.py --anotacje data/gold/annotations_XX.csv   # jakość etykiet, odsetki, werdykt hipotezy
python src/gold_standard.py strona --pomin data/gold/annotations_XX.csv   # podział próby: strona z resztą wypowiedzi
python src/estimate.py --anotacje data/gold/annotations_XX.csv data/gold/annotations_YY.csv   # oba pliki razem

pytest
```

## Eksploracja

`notebooks/01_eda_wypowiedzi.ipynb` opisuje korpus i słowniki tematów. `notebooks/02`–`03` i `src/classify.py` to
etap A, liczony dla wcześniejszej wersji hipotezy (okna czasowe A i B). `src/report_sceptycyzm.py` daje przegląd
wypowiedzi z markerem sceptycyzmu. `notebooks/04_gold_standard.ipynb` krótko opisuje wyniki golda (skład próby, jakość
etykiet modelu, odsetki z kroku 7) na podstawie plików z `data/processed/results/`.

## Struktura repo

```
src/             skrypty (nakładki CLI); logika w src/amc/
prompts/         prompty LLM: topic_v0, claims_v1, verdict_v1, paperqa_v0; etap A: etap_a_v2, weryfikacja_v*
data/raw/        odpowiedzi API (poza repo)
data/interim/    tabele z API (w repo tylko historia klubów)
data/processed/  korpus (poza repo), wyniki pipeline'u (topic/, claims/, verdicts/, labels/, results/), tabele z EDA
                 i wyniki etapu A
data/ar6/        PDF-y SPM i TS AR6 z indeksem (poza repo; python src/build_ar6.py, pipeline robi to sam)
data/gold/       próba golda i anotacje
data/tests/      testy promptów (--testy w classify_topic.py i verify_claims.py)
notebooks/, figures/, tests/
```
