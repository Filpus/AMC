"""Statement verdicts of an alternative verification run against the gold standard, next to the frozen Gemma run.

Run from the project root (AMC) after verify_claude.py on the claims of the gold sample:

    .venv/bin/python pipeline_development/alternative_verification/compare_gold.py --prompt claude_SPMs_sonnet

A statement is contradicting for a model when at least one of its claims is judged `sprzeczne` (a statement without
claims is not contradicting), as in src/label_statements.py. Gemma's verdict is the frozen run's stratum: 1 = sprzeczna,
2 = not, 3 = no verdict (the model did not find the statement topical). The comparison covers the statements topical in
the gold (`tematyczna = 1`): counts and rates with the sample weights (waga = N_h / n_h), once on strata 1-2 (where both
models have a verdict) and once on all gold-topical statements (only the alternative run). The disagreements are listed
for reading: the gold has known errors (cost claims judged contradicting against codebook section 4), so a disagreement
is not always the model's error.

This only assesses the verdict step on the gold sample; it does not change the frozen run or its strata. Do not tune
the prompt on these results.
"""
import argparse, sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
AMC = HERE.parents[1]
sys.path.insert(0, str(AMC / "src"))
from amc import runs  # noqa: E402

GOLD = AMC / "data" / "gold"
CLAIMS = AMC / "data" / "processed" / "claims" / "claims_v1__gemma4_12b__sample.jsonl"


def gold_sample() -> pd.DataFrame:
    ann = pd.concat([pd.read_csv(p, encoding="utf-8-sig") for p in sorted(GOLD.glob("annotations_*.csv"))])
    g = pd.read_csv(GOLD / "sample.csv").merge(ann[["kolejnosc", "tematyczna", "sprzeczna"]], on="kolejnosc")
    g["gold_s"] = (g.tematyczna == 1) & (g.sprzeczna.fillna(0) == 1)
    g["gemma_s"] = np.where(g.warstwa == 3, np.nan, (g.warstwa == 1).astype(float))
    return g


def model_verdicts(path: Path) -> tuple:
    claims = runs.last_lines(CLAIMS)
    verdicts = runs.last_lines(path, "twierdzenie_id")
    per, contra = {}, {}
    for wid, r in claims.items():
        ids = [f"{wid}#{c['nr']}" for c in r["twierdzenia"]]
        got = [verdicts.get(i) for i in ids]
        if r["blad"] or any(v is None or v["blad"] for v in got):
            per[wid] = np.nan
            continue
        hits = [v for v in got if v["werdykt"] == "sprzeczne"]
        per[wid] = float(bool(hits))
        contra[wid] = "; ".join(f"{v['twierdzenie']} [{v['ar6']}]" for v in hits)
    return per, contra


def rates(m: pd.Series, g: pd.Series, w: pd.Series) -> dict:
    m, g = m.astype(bool), g.astype(bool)
    tp, fp, fn, tn = (w[m & g].sum(), w[m & ~g].sum(), w[~m & g].sum(), w[~m & ~g].sum())
    ratio = lambda a, b: round(a / (a + b), 3) if a + b else np.nan
    return {"n": int(len(m)), "TP": int((m & g).sum()), "FP": int((m & ~g).sum()), "FN": int((~m & g).sum()),
            "TN": int((~m & ~g).sum()), "TPR_w": ratio(tp, fn), "precyzja_w": ratio(tp, fp), "TNR_w": ratio(tn, fp)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", required=True, help="prompt name of verify_claude.py, e.g. claude_SPMs_sonnet")
    ap.add_argument("--verdicts", help="verdicts file (default: out/verdicts/<prompt>__gemma4_12b__sample.jsonl)")
    a = ap.parse_args()
    path = Path(a.verdicts) if a.verdicts else HERE / "out" / "verdicts" / f"{a.prompt}__gemma4_12b__sample.jsonl"
    g = gold_sample()
    per, contra = model_verdicts(path)
    g["alt_s"] = g.wypowiedz_id.map(per)
    if g.alt_s.isna().any():
        print(f"{int(g.alt_s.isna().sum())} statements without a complete verdict of {a.prompt}: rerun verify_claude.py")
    t = g[(g.tematyczna == 1) & g.alt_s.notna()]
    both = t[t.gemma_s.notna()]
    rows = {"gemma, strata 1-2": rates(both.gemma_s, both.gold_s, both.waga),
            f"{a.prompt}, strata 1-2": rates(both.alt_s, both.gold_s, both.waga),
            f"{a.prompt}, all gold-topical": rates(t.alt_s, t.gold_s, t.waga)}
    print("Statements topical in the gold; TPR / precision / TNR weighted by waga\n")
    print(pd.DataFrame(rows).T.to_string())
    by_group = {(grp, who): rates(d[col], d.gold_s, d.waga)
                for grp, d in both.groupby("grupa") for who, col in (("gemma", "gemma_s"), (a.prompt, "alt_s"))}
    print("\nBy group, strata 1-2\n")
    print(pd.DataFrame(by_group).T.to_string())
    dis = t[(t.alt_s.astype(bool) != t.gold_s) | (t.gemma_s.notna() & (t.gemma_s.fillna(0).astype(bool) != t.gold_s))]
    print(f"\nDisagreements with the gold ({len(dis)}):")
    for r in dis.sort_values("kolejnosc").itertuples():
        gem = "-" if np.isnan(r.gemma_s) else int(r.gemma_s)
        print(f"  #{r.kolejnosc} ({r.grupa}, stratum {r.warstwa}): gold {int(r.gold_s)}, gemma {gem}, "
              f"{a.prompt} {int(r.alt_s)}" + (f" <- {contra[r.wypowiedz_id][:300]}" if contra.get(r.wypowiedz_id) else ""))


if __name__ == "__main__":
    main()
