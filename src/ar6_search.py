"""Wyszukiwarka AR6 dla anotatora golda: BM25 + EmbeddingGemma (fuzja RRF), --id, --grep. Odtworzona, bo oryginał Damiana
nie trafił do repo (data/gold/opus/README.md). Wymaga data/ar6/ (src/build_ar6.py) i Ollamy.

Przykład:
  python src/ar6_search.py "human influence has warmed the climate"
  python src/ar6_search.py --id "WGI SPM A.1"
  python src/ar6_search.py --grep "net zero"
"""
import argparse

import numpy as np

from amc import ar6


def show(rows):
    for r in rows.to_dict("records"):
        print(f"\n[{r['etykieta']}]\n{r['tekst']}")
    if rows.empty:
        print("brak wyników")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zapytanie", nargs="?")
    ap.add_argument("--id", help="etykieta ustalenia, np. 'WGIII TS TS.5.1'")
    ap.add_argument("--grep", help="wyrażenie regularne po tekście fragmentów")
    ap.add_argument("-k", type=int, default=6)
    a = ap.parse_args()
    if not (a.zapytanie or a.id or a.grep):
        ap.error("podaj zapytanie, --id albo --grep")
    index = ar6.Index()
    df = index.df
    if a.id:
        return show(df[df["etykieta"].str.startswith(a.id)])
    if a.grep:
        return show(df[df["tekst"].str.contains(a.grep, case=False, regex=True)].head(a.k))
    q = ar6.embed([a.zapytanie], query=True)[0]
    dense = list(np.argsort(-(index.vec @ q))[:50])
    sparse = list(np.argsort(-index.bm25.scores(a.zapytanie))[:50])
    show(df.iloc[ar6.rrf([dense, sparse])[:a.k]])


if __name__ == "__main__":
    main()
