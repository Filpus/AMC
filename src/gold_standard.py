"""Gold standard: draws the sample, builds the annotation page, handles the optional second annotator.

Files (data/gold/, or next to --proba):
  sample.csv       design: kolejnosc, wypowiedz_id, stratum, N_h, n_h, weight, seed; not for the annotator
  texts.csv        texts for the page: kolejnosc and text with speaker names masked, in the shuffled order
  annotation.html  annotation page; it exports annotations_<initials>.csv (kolejnosc, tematyczna, sprzeczna, komentarz,
                   proba = sample fingerprint) for `estimate.py --anotacje`
  subsample.csv    second annotator's statements, with annotation_subsample.html -> annotations_subsample_<initials>.csv

Commands:
  losuj            n_h statements per group x stratum of the model labels (amc/estimation.draw; --werdykt-prompt
                   paperqa_v0: the labels from the PaperQA2 verdicts), drawn once and only when the labels cover the
                   whole population -> sample.csv, texts.csv
  strona           annotation page: only the texts in the shuffled order (no wypowiedz_id, speaker, club, stratum or
                   model label) and two labels, tematyczna and (when topical) sprzeczna z AR6; autosaves in the browser
  podproba F1      second annotator: 40 statements of the sample at random, topped up to 10 that the first annotator
                   (F1) labelled contradicting -> subsample.csv (drawn once) and its page
  zgodnosc F1 F2   Cohen's kappa and share of agreement (tematyczna, final label) of the first annotator's file from
                   before the discussion (F1) and the second annotator's (F2); disagreements to discuss ->
                   disagreements_subsample_<initials>.csv

Example:
  python src/gold_standard.py losuj
  python src/gold_standard.py strona
  python src/gold_standard.py podproba data/gold/annotations_FK.csv
  python src/gold_standard.py zgodnosc data/gold/annotations_FK.csv data/gold/annotations_subsample_XY.csv
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from amc import annotation as A
from amc import corpus, llm, population, runs
from amc import estimation as E
from amc import text as T
from amc.paths import ROOT

GOLD = ROOT / "data" / "gold"
TEMPLATE = ROOT / "src" / "amc" / "templates" / "annotation_page.html"


def check_coverage(labels, pop):
    """The strata come from the labels of the whole study population, not of a test run (--n), an unfinished run or a
    run on another corpus."""
    have, want = set(labels["wypowiedz_id"]), set(pop["wypowiedz_id"])
    if have != want:
        extra = f" and {len(have - want)} statements outside it" if have - want else ""
        raise SystemExit(f"the labels cover {len(have & want)} of {len(want)} statements of the study population "
                         f"(fingerprint {runs.fingerprint(want)}){extra}: finish the pipeline on this corpus first")


def draw(labels, seed, design_path):
    if design_path.exists():
        raise SystemExit(f"{design_path} exists; the gold sample is drawn once (delete it to draw again)")
    pop = population.select(corpus.load("plenarne"))
    check_coverage(labels, pop)
    sample = E.draw(labels, seed=seed).sample(frac=1, random_state=seed).reset_index(drop=True)
    sample.insert(0, "kolejnosc", range(1, len(sample) + 1))
    sample[["kolejnosc", "wypowiedz_id", "grupa", "warstwa", "N_h", "n_h", "waga", "ziarno"]].to_csv(design_path, index=False)
    texts = pop.set_index("wypowiedz_id")["tekst"]
    blind = sample[["kolejnosc"]].assign(tekst=[T.mask_speakers(texts[i]) for i in sample["wypowiedz_id"]])
    texts_path = design_path.with_name("texts.csv")
    blind.to_csv(texts_path, index=False)
    print(f"{len(sample)} statements (seed {seed}) -> {design_path} and {texts_path}")
    print(sample.groupby(["grupa", "warstwa"]).agg(N_h=("N_h", "first"), n_h=("n_h", "first")).to_string())


def page(texts, design, name, title, order=None):
    """Self-contained HTML page for the statements of `texts` (all, or `order` in that order); it exports
    <name>_<initials>.csv."""
    rows = texts.sort_values("kolejnosc") if order is None else texts.set_index("kolejnosc").loc[order].reset_index()
    rows = [{"kolejnosc": int(r.kolejnosc), "liczba_slow": len(str(r.tekst).split()), "tekst": str(r.tekst)}
            for r in rows.itertuples()]
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    return (TEMPLATE.read_text(encoding="utf-8").replace("__TITLE__", title).replace("__NAME__", name)
            .replace("__SAMPLE__", A.sample_id(design)).replace("__DATA__", data))


def write_page(texts, design, out, name, title, order=None):
    out.write_text(page(texts, design, name, title, order), encoding="utf-8")
    print(f"{len(texts) if order is None else len(order)} statements -> {out}")


def load(path, design, required=None):
    try:
        return A.load(path, design, required)
    except ValueError as e:
        raise SystemExit(e)


def agreement(design, sub_path, first, second):
    sub = pd.read_csv(sub_path)["kolejnosc"]
    ann2 = load(second, design, required=sub)
    table, diff = A.agreement(load(first, design), ann2[ann2["kolejnosc"].isin(sub)])
    print(table.round(3).to_string(index=False))
    final = table["kappa"].iloc[-1]
    print(f"\nkappa of the final label {final:.3f}: " + ("threshold met" if final >= A.KAPPA_THRESHOLD else
          f"below {A.KAPPA_THRESHOLD}: refine the codebook rule and annotate the subsample again"))
    out = Path(second).with_name(Path(second).stem.replace("annotations", "disagreements") + ".csv")
    diff.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"{len(diff)} disagreements to discuss -> {out}")


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
    sub.add_parser("strona", parents=[common], help="annotation page")
    p = sub.add_parser("podproba", parents=[common], help="subsample and page for the second annotator")
    p.add_argument("pierwszy", help="first annotator's file")
    p.add_argument("--seed", type=int, default=0, help="seed of the subsample")
    p = sub.add_parser("zgodnosc", parents=[common], help="agreement of the two annotators")
    p.add_argument("pierwszy", help="first annotator's file from before the discussion")
    p.add_argument("drugi", help="second annotator's file")
    a = ap.parse_args()
    design_path = Path(a.proba)
    if a.polecenie == "losuj":
        return draw(pd.read_csv(runs.labels_path(a.model, a.werdykt_prompt)), a.seed, design_path)

    design = pd.read_csv(design_path)
    texts = pd.read_csv(design_path.with_name("texts.csv"))
    sub_path = design_path.with_name("subsample.csv")
    if a.polecenie == "strona":
        return write_page(texts, design, design_path.with_name("annotation.html"), "annotations", "Gold standard")
    if a.polecenie == "zgodnosc":
        return agreement(design, sub_path, a.pierwszy, a.drugi)
    if sub_path.exists():
        raise SystemExit(f"{sub_path} exists; the subsample is drawn once (delete it to draw again)")
    order, topped = A.kappa_subsample(load(a.pierwszy, design), seed=a.seed)
    pd.DataFrame({"kolejnosc": order, "ziarno": a.seed}).to_csv(sub_path, index=False)
    print(f"subsample: {len(order)} statements ({topped} added to reach {A.KAPPA_MIN_CONTRADICTING} contradicting)"
          f" -> {sub_path}")
    write_page(texts, design, design_path.with_name("annotation_subsample.html"), "annotations_subsample",
               "Gold standard: podpróbka drugiego anotatora", order)


if __name__ == "__main__":
    main()
