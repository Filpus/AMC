"""AR6 knowledge base: downloads the SPM and TS of WGI-WGIII, splits them into fragments and embeds them (amc/ar6.py).

Output (data/ar6/, outside the repository): pdf/, fragments.parquet, embeddings_<model>.npy. Needs Ollama with the
embedding model (`ollama pull bge-m3`). Existing PDFs are not downloaded again.

Example:
  python src/build_ar6.py
  python src/build_ar6.py --pokaz "human influence has warmed the climate"
"""
import argparse
import logging

import numpy as np

from amc import ar6

log = logging.getLogger("build_ar6")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=ar6.EMBED_MODEL)
    ap.add_argument("--pokaz", help="only search the existing index for this query and print the fragments")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    if a.pokaz:
        for r in ar6.Index(model=a.model).search(a.pokaz, a.pokaz).to_dict("records"):
            print(f"\n[{r['etykieta']}] {r['tekst'][:600]}")
        return
    ar6.download()
    df = ar6.build()
    log.info("%d fragments, median %d words:\n%s", len(df), df["tekst"].str.split().str.len().median(),
             df.groupby(["raport", "czesc"]).size().to_string())
    vec = ar6.embed(df["tekst"].tolist(), a.model)
    np.save(ar6.embeddings_path(a.model), vec)
    log.info("embeddings %s -> %s", vec.shape, ar6.embeddings_path(a.model))


if __name__ == "__main__":
    main()
