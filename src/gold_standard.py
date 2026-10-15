"""Gold standard: draws the sample for annotation from the pipeline labels.

  losuj   n_h statements per group x stratum of the model labels (amc/estimation.draw; --werdykt-prompt paperqa_v0:
          the labels from the PaperQA2 verdicts), shuffled, drawn once ->
          data/gold/sample.csv (design: kolejnosc, wypowiedz_id, stratum, N_h, n_h, weight, seed; not for the
          annotator) and texts.csv (for the annotator: speaker names masked, empty columns tematyczna and sprzeczna)

Example:
  python src/gold_standard.py losuj
"""
import argparse
from pathlib import Path

import pandas as pd

from amc import corpus, llm, runs
from amc import estimation as E
from amc import text as T
from amc.paths import ROOT

GOLD = ROOT / "data" / "gold"


def draw(labels, seed, design_path):
    if design_path.exists():
        raise SystemExit(f"{design_path} exists; the gold sample is drawn once (delete it to draw again)")
    sample = E.draw(labels, seed=seed).sample(frac=1, random_state=seed).reset_index(drop=True)
    sample.insert(0, "kolejnosc", range(1, len(sample) + 1))
    sample[["kolejnosc", "wypowiedz_id", "grupa", "warstwa", "N_h", "n_h", "waga", "ziarno"]].to_csv(design_path, index=False)
    texts = corpus.load("plenarne").set_index("wypowiedz_id")["tekst"]
    blind = sample[["kolejnosc", "wypowiedz_id"]].assign(tekst=[T.mask_speakers(texts[i]) for i in sample["wypowiedz_id"]],
                                                         tematyczna="", sprzeczna="")
    texts_path = design_path.with_name("texts.csv")
    blind.to_csv(texts_path, index=False)
    print(f"{len(sample)} statements (seed {seed}) -> {design_path} and {texts_path}")
    print(sample.groupby(["grupa", "warstwa"]).agg(N_h=("N_h", "first"), n_h=("n_h", "first")).to_string())


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--proba", default=str(GOLD / "sample.csv"), help="gold sample design")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="polecenie", required=True)
    p = sub.add_parser("losuj", parents=[common], help="draw the gold sample")
    p.add_argument("--model", default=llm.PIPELINE_MODEL, help="model whose labels define the strata")
    p.add_argument("--werdykt-prompt", default=runs.VERDICT_PROMPT,
                   help=f"verdicts of the pipeline run ({runs.PAPERQA_PROMPT} for PaperQA2)")
    p.add_argument("--seed", type=int, default=0, help="seed of the draw")
    a = ap.parse_args()
    if a.polecenie == "losuj":
        draw(pd.read_csv(runs.labels_path(a.model, a.werdykt_prompt)), a.seed, Path(a.proba))


if __name__ == "__main__":
    main()
