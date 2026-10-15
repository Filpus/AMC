"""Hypothesis test from the pipeline labels and the gold standard (measurement plan, variant B; amc/estimation).

Input: data/processed/labels/<model>.csv (label_statements.py). Without annotations: stratum sizes N_h, the rarity
condition, uncorrected shares and the step 6 regression. With --anotacje (the gold sample of `gold_standard.py losuj`,
annotated): steps 5 and 7 (stratified bootstrap) and the verdict on the hypothesis. Results:
data/processed/results/<model>_*.csv.

Examples:
  python src/estimate.py                                   # after the pipeline: N_h, rarity, step 6
  python src/estimate.py --anotacje data/gold/annotations_FK.csv
"""
import argparse
from pathlib import Path

import pandas as pd

from amc import llm, runs
from amc import estimation as E
from amc.paths import PROCESSED, ROOT

GOLD = ROOT / "data" / "gold"
OUT = PROCESSED / "results"


def check_design(design, labels):
    sizes = E.strata_sizes(labels).set_index(["grupa", "warstwa"])["N_h"]
    drawn = design.groupby(["grupa", "warstwa"])["N_h"].first()
    if not drawn.equals(sizes.reindex(drawn.index)):
        raise SystemExit(f"the gold sample was drawn from other labels (N_h differ):\n{pd.concat([drawn, sizes], axis=1)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--proba", default=str(GOLD / "sample.csv"), help="gold sample design")
    ap.add_argument("--anotacje", help="CSV with wypowiedz_id, tematyczna (0/1), sprzeczna (0/1)")
    ap.add_argument("--powtorzenia", type=int, default=10_000, help="bootstrap resamples")
    a = ap.parse_args()
    slug = runs.model_slug(a.model)
    labels = pd.read_csv(PROCESSED / "labels" / f"{slug}.csv")
    design_path = Path(a.proba)
    OUT.mkdir(parents=True, exist_ok=True)

    sizes = E.strata_sizes(labels)
    sizes["warstwa_opis"] = sizes["warstwa"].map(E.STRATA)
    print(f"{len(labels)} statements in {slug}.csv\n\nStrata N_h:\n{sizes.to_string(index=False)}")

    rare = E.rarity(labels)
    raw = E.raw_shares(labels)
    reg = pd.DataFrame([E.regression(labels)])
    print(f"\nRarity condition (>= {E.MIN_TOPICAL} topical per group, >= {E.MIN_CONTRADICTING} contradicting): {rare}")
    print(f"\nUncorrected shares (model labels):\n{raw.to_string()}")
    print(f"\nStep 6, logit sprzeczna ~ prawica, SE clustered by speaker:\n{reg.to_string(index=False)}")
    sizes.to_csv(OUT / f"{slug}_strata.csv", index=False)
    raw.to_csv(OUT / f"{slug}_uncorrected.csv")
    reg.to_csv(OUT / f"{slug}_regression.csv", index=False)
    if not a.anotacje:
        return

    design = pd.read_csv(design_path)
    check_design(design, labels)
    ann = pd.read_csv(a.anotacje)[["wypowiedz_id", "tematyczna", "sprzeczna"]]
    gold = design.merge(ann, on="wypowiedz_id", how="left")
    missing = gold["tematyczna"].isna().sum()
    if missing:
        raise SystemExit(f"{missing} statements of the gold sample have no annotation")
    step5 = E.summarize(gold, E.quality, a.powtorzenia)
    step7 = E.summarize(gold, E.proportions, a.powtorzenia)
    step5.to_csv(OUT / f"{slug}_quality.csv")
    step7.to_csv(OUT / f"{slug}_estimates.csv")
    print(f"\nStep 5, weighted rates (bootstrap {a.powtorzenia}):\n{step5.round(3).to_string()}")
    print(f"\nStep 7, corrected shares:\n{step7.round(4).to_string()}")
    lower = step7.loc["roznica", "dolna_95_jednostronna"]
    if not rare["warunek_spelniony"]:
        verdict = "inconclusive for lack of data (rarity condition not met)"
    else:
        verdict = "supported" if lower > 0 else "not supported"
    print(f"\nHypothesis: {verdict} (one-sided 95% lower bound of the difference: {lower:.4f})")


if __name__ == "__main__":
    main()
