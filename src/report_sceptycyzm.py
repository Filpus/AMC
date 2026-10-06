"""Przegląd wypowiedzi tematycznych ze zwrotem podważającym naukę (marker `sceptycyzm` z amc/topics.py).

Wyjście:
  data/processed/eda_wypowiedzi_sceptyczne.csv    lista wypowiedzi (mówca, klub, tematy, zwroty)
  notebooks/eda_wypowiedzi_sceptyczne.html        strona z fragmentami i filtrem po temacie / klubie

Wymaga korpusu: python src/build_corpus.py
"""
import argparse
import json
import logging

import pandas as pd

from amc import corpus, topics
from amc.paths import PROCESSED, ROOT
from amc.text import highlight_segments

log = logging.getLogger("report_sceptycyzm")
SZABLON = ROOT / "src" / "amc" / "templates" / "wypowiedzi_sceptyczne.html"


def wiersze(df):
    tem_cols = [f"{t}_tem" for t in topics.TOPICS]
    f = df[df["merytoryczna"] & df["dowolny_tem"] & df["sceptycyzm"].gt(0)].sort_values(["data", "num"])
    out = []
    for _, r in f.iterrows():
        t = r["tekst"]
        out.append({
            "data": f"{r['data']:%Y-%m-%d}", "kadencja": int(r["kadencja"]), "mowca": r["mowca"],
            "klub": r["klub"] if isinstance(r["klub"], str) else (r["funkcja"] or "—"),
            "tematy": [c[:-4] for c in tem_cols if r[c]],
            "zwroty": sorted({m.group(0) for m in topics.SKEPTIC_RE.finditer(t.lower())}),
            "fr": highlight_segments(t, topics.SKEPTIC_RE),
            "id": r["wypowiedz_id"], "slowa": int(r["liczba_slow"]),
        })
    return out


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    rows = wiersze(corpus.load("plenarne"))
    csv = PROCESSED / "eda_wypowiedzi_sceptyczne.csv"
    pd.DataFrame([{k: ", ".join(v) if isinstance(v, list) else v for k, v in x.items() if k != "fr"}
                  for x in rows]).to_csv(csv, index=False)
    dane = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    html_out = ROOT / "notebooks" / "eda_wypowiedzi_sceptyczne.html"
    html_out.write_text(SZABLON.read_text(encoding="utf-8").replace("__DATA__", dane), encoding="utf-8")
    log.info("%d wypowiedzi -> %s, %s", len(rows), csv, html_out)


if __name__ == "__main__":
    main()
