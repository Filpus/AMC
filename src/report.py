"""Step 9: the numbers for the report in one Markdown file (presentation, slides 13-14).

Reads only the result files of estimate.py (with --anotacje) and robustness.py from data/processed/results/ and writes
<labels file name>_raport.md there: 1) main result before and after the correction, 2) statements in the denominator,
3) quality of the model labels, 4) robustness, 5) facts for the limitations section, and the verdict. The text of the
preprint is written by hand; this file only collects the numbers so that the preprint and the poster quote the same
values.

Example:
  python src/estimate.py --anotacje data/gold/annotations_FP.csv data/gold/annotations_DK.csv
  python src/robustness.py
  python src/report.py
"""
import argparse

import pandas as pd

from amc import llm, runs
from amc import estimation as E
from amc import robustness as R
from amc.paths import PROCESSED

RES = PROCESSED / "results"
STAGES = {"tematycznosc": "tematyczność", "werdykt": "werdykt (tematyczne wg modelu i golda)",
          "etykieta": "etykieta końcowa"}


def pct(x, digits=1):
    return "–" if pd.isna(x) else f"{100 * x:.{digits}f}".replace(".", ",")


def num(x, digits=3):
    return "–" if pd.isna(x) else f"{x:.{digits}f}".replace(".", ",")


def interval(r, fmt):
    return f"{fmt(r['wartosc'])} [{fmt(r['przedzial_2.5'])}; {fmt(r['przedzial_97.5'])}]"


def table(rows, header):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def verdict(rarity_ok, lower):
    if not rarity_ok:
        return "nierozstrzygający wskutek małej liczby danych (warunek rzadkości niespełniony)"
    return "hipoteza potwierdzona" if lower > 0 else "hipoteza niepotwierdzona"


def build(slug):
    load = lambda name, **kw: pd.read_csv(RES / f"{slug}_{name}.csv", **kw)
    est, qual = load("estimates", index_col=0), load("quality", index_col=0)
    raw, reg = load("uncorrected", index_col="grupa"), load("regression").iloc[0]
    comp, rob = load("composition"), load("robustness")
    loso = load("loso") if (RES / f"{slug}_loso.csv").exists() else None
    labels = pd.read_csv(PROCESSED / "labels" / f"{slug}.csv")
    rare = E.rarity(labels)
    diff = est.loc["roznica"]
    out = [f"# Krok 9: zestawienie wyników ({slug})", "",
           "Plik generowany przez `src/report.py` z plików w `data/processed/results/`; nie edytować ręcznie.", ""]

    out += ["## Werdykt", "",
            f"**{verdict(rare['warunek_spelniony'], diff['dolna_95_jednostronna'])}**: różnica prawica − reszta po "
            f"korekcie {pct(diff['wartosc'])} pp, dolna granica jednostronnego 95% przedziału "
            f"{pct(diff['dolna_95_jednostronna'])} pp (krok 7, bootstrap warstwowy próby gold standardu).", ""]

    out += ["## 1. Wynik główny przed korektą i po korekcie", "",
            table([[g, pct(raw.loc[g, "odsetek"]), interval(est.loc[f"p_{g}"], pct)] for g in E.GROUPS]
                  + [["różnica (pp)", pct(raw.loc["prawica", "odsetek"] - raw.loc["reszta", "odsetek"]),
                      interval(diff, pct)]],
                  ["grupa", "bez korekty: odsetek wg modelu (%)", "po korekcie: gold, krok 7 (%) [95% CI]"]), "",
            f"Krok 6 (etykiety modelu, logit, SE klastrowane po mówcy): β₁ = {num(reg['beta1'])}, "
            f"SE = {num(reg['se'])}, 95% CI [{num(reg['beta1'] - R.Z95 * reg['se'])}; "
            f"{num(reg['beta1'] + R.Z95 * reg['se'])}], p jednostronne = {num(reg['p_jednostronne'])}; "
            f"n = {int(reg['n'])} wypowiedzi, {int(reg['mowcy'])} mówców.", ""]

    w = comp.assign(T=comp["waga"] * comp["tematyczne"], C=comp["waga"] * comp["sprzeczne"]).groupby("grupa")
    w = w[["T", "C"]].sum()
    out += ["## 2. Wypowiedzi w mianowniku", "",
            table([[g, int(raw.loc[g, "tematyczne"]), int(raw.loc[g, "sprzeczne"]), f"{w.loc[g, 'T']:.0f}",
                    f"{w.loc[g, 'C']:.0f}"] for g in E.GROUPS],
                  ["grupa", "tematyczne wg modelu", "sprzeczne wg modelu", "tematyczne z golda (T̂)",
                   "sprzeczne z golda (Ĉ)"]), "",
            f"Warunek rzadkości (≥ {E.MIN_TOPICAL} tematycznych w grupie, ≥ {E.MIN_CONTRADICTING} sprzecznych łącznie): "
            f"{'spełniony' if rare['warunek_spelniony'] else 'niespełniony'}.", ""]

    rows = []
    for stage, name in STAGES.items():
        for m in ["TPR", "TNR", "precyzja", "F1"]:
            rows.append([name, m] + [interval(qual.loc[f"{g}_{stage}_{m}"], num) for g in E.GROUPS])
    out += ["## 3. Jakość etykiet modelu (krok 5, wagi warstw, 95% CI z bootstrapu)", "",
            table(rows, ["etap", "miara", *E.GROUPS]), ""]

    v = R.verdict(rob)
    out += ["## 4. Odporność (krok 8, test z kroku 6 w wariantach)", "",
            table([[r["opis"], r["rodzaj"], int(r["n"]), int(r["sprzeczne"]), num(r["beta1"]),
                    f"[{num(r['ci_2.5'])}; {num(r['ci_97.5'])}]", pct(r["roznica"]), num(r["krotnosc"], 2),
                    "tak" if r["odporny"] else "nie"] for _, r in rob.iterrows()],
                  ["wariant", "rodzaj", "n", "sprzeczne", "β₁", "95% CI", "różnica wg modelu (pp)",
                   "β₁ / β₁ główne", "kryterium"]), "",
            f"Kryterium (warianty z planu): ten sam znak i {num(R.LOW, 1)}–{num(R.HIGH, 1)} × β₁ wyniku głównego. "
            f"Wynik bez korekty jest **{'odporny' if v['odporny'] else 'nieodporny'}**"
            + (f" (niespełnione: {', '.join(v['niespelnione'])})" if v["niespelnione"] else "") + ".",
            f"Połowy okresu dzieli {R.MIDPOINT:%d.%m.%Y}.", ""]
    if loso is not None:
        lo, hi = loso.iloc[0], loso.iloc[-1]
        out += [f"Leave-one-speaker-out ({len(loso)} mówców): β₁ od {num(lo['beta1'])} (bez: {lo['posel']}) "
                f"do {num(hi['beta1'])} (bez: {hi['posel']}); kryterium niespełnione po usunięciu "
                f"{int((~loso['odporny']).sum())} mówców.", ""]

    ci_zero = rob.loc[(rob["ci_2.5"] <= 0) & (rob["rodzaj"] != "glowny"), "opis"].tolist()
    key = comp[comp["warstwa"] == 2]
    out += ["## 5. Fakty do sekcji „Ograniczenia”", "",
            "- Krok 8 sprawdza wynik bez korekty (etykiety modelu); o hipotezie rozstrzyga krok 7.",
            f"- Warianty, w których 95% CI β₁ obejmuje 0: {', '.join(ci_zero) if ci_zero else 'brak'}.",
            "- Wypowiedzi sprzeczne wg golda w warstwie 2 (model: tematyczna, niesprzeczna), liczba × waga: "
            + ", ".join(f"{r['grupa']}: {int(r['sprzeczne'])} × {num(r['waga'], 1)}" for _, r in key.iterrows()) + ".",
            "- Gold w warstwie 3: tematyczne " + ", ".join(
                f"{r['grupa']}: {int(r['tematyczne'])}/{int(r['n_h'])} (waga {r['waga']:.0f})"
                for _, r in comp[comp["warstwa"] == 3].iterrows()) + ".",
            "- Przypadki bootstrapu bez wartości różnicy: " + str(int(diff["bootstrap_brak"])) + ".", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--werdykt-prompt", default=runs.VERDICT_PROMPT)
    runs.add_retrieval_args(ap, frozen=True)
    a = ap.parse_args()
    slug = runs.labels_path(a.model, a.werdykt_prompt, a.wyszukiwanie, a.embedding).stem
    try:
        text = build(slug)
    except FileNotFoundError as e:
        raise SystemExit(f"missing {e.filename}: run estimate.py --anotacje and robustness.py first")
    path = RES / f"{slug}_raport.md"
    path.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
