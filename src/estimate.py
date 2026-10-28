"""Hypothesis test from the pipeline labels and the gold standard (measurement plan, variant B; amc/estimation).

Input: data/processed/labels/<model><variant>.csv (label_statements.py with the same --wyszukiwanie / --embedding; by
default the frozen run, rrf with bge-m3, from whose labels the gold sample in the repo was drawn; with --werdykt-prompt
paperqa_v0 the labels from the PaperQA2 verdicts). Without annotations: stratum sizes N_h, the rarity condition, uncorrected shares and the step 6
regression. With --anotacje (the export of the annotation page of `gold_standard.py strona`, checked by
amc/annotation.load): sample composition (true contradicting statements per stratum), steps 5 and 7 (stratified
bootstrap) and the verdict on the hypothesis. The model verdict for the statements of stratum 3 (not topical by the
model) comes from `extract_claims.py --ids` and `verify_claims.py --ids` (or verify_claims_paperqa.py) on the sample
file; with it step 5 also rates the verdict on all statements topical by the gold. Results:
data/processed/results/<labels file name>_*.csv.

Examples:
  python src/estimate.py                                     # after the pipeline: N_h, rarity, step 6
  python src/gold_standard.py losuj                          # gold sample
  python src/gold_standard.py strona                         # annotation page data/gold/annotation.html
  python src/extract_claims.py --ids data/gold/sample.csv    # model verdict for the whole sample
  python src/verify_claims.py --ids data/gold/sample.csv
  python src/estimate.py --anotacje data/gold/annotations_FK.csv
  python src/estimate.py --anotacje data/gold/annotations_FP.csv data/gold/annotations_DK.csv   # split sample
"""
import argparse
from pathlib import Path

import pandas as pd

from amc import llm, runs
from amc import annotation as A
from amc import estimation as E
from amc.paths import PROCESSED, ROOT
from label_statements import label

GOLD = ROOT / "data" / "gold"
OUT = PROCESSED / "results"


def check_design(design, labels):
    sizes = E.strata_sizes(labels).set_index(["grupa", "warstwa"])["N_h"]
    drawn = design.groupby(["grupa", "warstwa"])["N_h"].first()
    if not drawn.equals(sizes.reindex(drawn.index)):
        raise SystemExit(f"the gold sample was drawn from other labels (N_h differ):\n{pd.concat([drawn, sizes], axis=1)}")


def sample_run(design_path, model, claims_prompt, verdicts_file):
    """wypowiedz_id -> 0/1 (>= 1 contradicting claim) from `extract_claims.py --ids` and `verify_claims.py --ids` on the
    sample file; missing when the run is absent or unfinished."""
    suffix = f"__{design_path.stem}"
    claims = list(runs.last_lines(runs.out_path("claims", claims_prompt, model, suffix)).values())
    verdicts = list(runs.last_lines(verdicts_file, "twierdzenie_id").values())
    ids = [r["wypowiedz_id"] for r in claims]
    if not ids:
        return {}
    st, _ = label([{"wypowiedz_id": i, "klimat": 1, "blad": None} for i in ids], claims, verdicts,
                  pd.DataFrame({"wypowiedz_id": ids}))
    return dict(zip(st["wypowiedz_id"], st["sprzeczna"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--proba", default=str(GOLD / "sample.csv"), help="gold sample design")
    ap.add_argument("--anotacje", nargs="+", metavar="PLIK",
                    help="export(s) of the annotation page: kolejnosc, tematyczna, sprzeczna (0/1); several files when "
                         "annotators split the sample")
    ap.add_argument("--powtorzenia", type=int, default=10_000, help="bootstrap resamples")
    ap.add_argument("--twierdzenia-prompt", default="claims_v1")
    ap.add_argument("--werdykt-prompt", default=runs.VERDICT_PROMPT,
                    help=f"verdicts of the pipeline run ({runs.PAPERQA_PROMPT} for PaperQA2)")
    runs.add_retrieval_args(ap, frozen=True)
    a = ap.parse_args()
    labels_file = runs.labels_path(a.model, a.werdykt_prompt, a.wyszukiwanie, a.embedding)
    slug = labels_file.stem
    labels = pd.read_csv(labels_file)
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
    try:
        ann = A.load_parts(a.anotacje, design)
    except ValueError as e:
        raise SystemExit(e)
    gold = design.merge(ann[["kolejnosc", "tematyczna", "sprzeczna", "komentarz", "anotator"]], on="kolejnosc")
    verdicts_file = runs.verdicts_path(a.werdykt_prompt, a.model, a.wyszukiwanie, a.embedding, f"__{design_path.stem}")
    gold["werdykt_modelu"] = E.sample_verdicts(gold, sample_run(design_path, a.model, a.twierdzenia_prompt,
                                                                verdicts_file))
    no_verdict = int(gold["werdykt_modelu"].isna().sum())
    if no_verdict:
        print(f"\nNo model verdict for {no_verdict} statements of stratum 3: run extract_claims.py and verify_claims.py "
              f"with --ids {design_path}; step 5 skips the verdict on all topical statements")
    gold.drop(columns=["tekst"], errors="ignore").to_csv(OUT / f"{slug}_gold.csv", index=False)
    comp = E.composition(gold)
    comp.to_csv(OUT / f"{slug}_composition.csv", index=False)
    print(f"\nGold sample composition (gold counts per stratum):\n{comp.to_string(index=False)}")
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
