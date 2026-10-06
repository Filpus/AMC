"""Budowa korpusu gotowego do analizy: data/processed/korpus_{plenarne,komisje}.parquet.

Wejście: tabele z data/interim/ (fetch_sejm.py, fetch_komisje.py). Logika w amc/corpus.py:
czyszczenie tekstu, rola mówcy, blok polityczny, filtr wypowiedzi merytorycznych, flagi tematów.

Przykłady:
  python src/build_corpus.py                              # oba korpusy, kadencje 8–10
  python src/build_corpus.py --kinds komisje --committees ZDR OSZ
"""
import argparse
import logging

from amc import corpus
from amc.paths import TERMS


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kinds", nargs="*", default=list(corpus.RODZAJE), choices=corpus.RODZAJE)
    ap.add_argument("--terms", type=int, nargs="*", default=TERMS)
    ap.add_argument("--committees", nargs="*", help="kody komisji (domyślnie wszystkie pobrane)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    for rodzaj in a.kinds:
        corpus.build(rodzaj, a.terms, a.committees)


if __name__ == "__main__":
    main()
