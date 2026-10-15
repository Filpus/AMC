"""Statement labels from the three pipeline steps: topic, claims, verdicts.

`sprzeczna` = 1 when a statement with klimat = 1 has at least one claim judged `sprzeczne`. It is empty when klimat = 1 but the claims or some verdicts are missing (the steps
have not finished). Output: data/processed/labels/<model>.csv, one row per statement classified for topic, with the
columns the analysis needs (data, member_id, rola, klub, grupa, slownik_klimat = climate dictionary hits), and
<model>_claims.csv (claims with verdicts). The printed shares are raw: no weights, no correction.

Example:
  python src/label_statements.py
  python src/label_statements.py --model gemma4:12b
"""
import argparse

import numpy as np
import pandas as pd

from amc import corpus, llm, population, runs
from amc.paths import PROCESSED


META = ["wypowiedz_id", "data", "member_id", "rola", "klub", "grupa", "slownik_klimat"]


def label(klimat, claims, verdicts, meta):
    """(statements, claims) tables; inputs are the last result lines of each step as lists of dicts and a table with
    `wypowiedz_id` and the statement columns to keep (META)."""
    st = pd.DataFrame([r for r in klimat if not r["blad"]], columns=["wypowiedz_id", "klimat"])
    st = meta.merge(st, on="wypowiedz_id", how="right")
    cl = pd.DataFrame([{"wypowiedz_id": r["wypowiedz_id"], **c} for r in claims if not r["blad"] for c in r["twierdzenia"]],
                      columns=["wypowiedz_id", "nr", "cytat", "cytat_w_tekscie", "twierdzenie", "twierdzenie_en"])
    cl["twierdzenie_id"] = cl["wypowiedz_id"] + "#" + cl["nr"].astype(str)
    vd = pd.DataFrame([r for r in verdicts if not r["blad"]],
                      columns=["twierdzenie_id", "werdykt", "ar6", "uzasadnienie", "werdykt_bez_ar6"])
    cl = cl.merge(vd, on="twierdzenie_id", how="left")
    per = cl.groupby("wypowiedz_id").agg(n_ocenianych=("twierdzenie_id", "size"),
                                             n_werdyktow=("werdykt", "count"),
                                             n_sprzecznych=("werdykt", lambda w: int((w == "sprzeczne").sum())))
    st = st.merge(per, on="wypowiedz_id", how="left")
    st["twierdzenia_gotowe"] = st["wypowiedz_id"].isin({r["wypowiedz_id"] for r in claims if not r["blad"]})
    st[["n_ocenianych", "n_werdyktow", "n_sprzecznych"]] = st[["n_ocenianych", "n_werdyktow", "n_sprzecznych"]].fillna(0)
    complete = st["twierdzenia_gotowe"] & (st["n_werdyktow"] == st["n_ocenianych"])
    st["sprzeczna"] = np.where(st["klimat"] == 1, np.where(complete, (st["n_sprzecznych"] > 0).astype(float), np.nan), 0.0)
    return st, cl


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=llm.PIPELINE_MODEL, help="model of all three steps")
    ap.add_argument("--klimat-prompt", default="topic_v0")
    ap.add_argument("--twierdzenia-prompt", default="claims_v1")
    ap.add_argument("--werdykt-prompt", default="verdict_v1")
    a = ap.parse_args()
    files = [runs.out_path("topic", a.klimat_prompt, a.model), runs.out_path("claims", a.twierdzenia_prompt, a.model),
             runs.out_path("verdicts", a.werdykt_prompt, a.model)]
    k, c, v = (list(runs.last_lines(p, key).values()) for p, key in zip(files, ["wypowiedz_id"] * 2 + ["twierdzenie_id"]))
    pop = population.select(corpus.load("plenarne")).rename(columns={"klimat": "slownik_klimat"})
    st, cl = label(k, c, v, pop[META])
    out = PROCESSED / "labels" / f"{runs.model_slug(a.model)}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    st.to_csv(out, index=False)
    cl.to_csv(out.with_name(f"{out.stem}_claims.csv"), index=False)
    t = st[st["klimat"] == 1]
    print(f"{len(st)} statements classified, klimat = 1: {len(t)}, labels complete: {t['sprzeczna'].notna().sum()}")
    print(st.groupby("grupa").agg(wypowiedzi=("klimat", "size"), klimat=("klimat", "sum"),
                                  sprzeczne=("sprzeczna", "sum")).assign(
        odsetek_wsrod_klimat=lambda d: (d["sprzeczne"] / d["klimat"]).round(3)).to_string())
    print(cl["werdykt"].value_counts(dropna=False).to_string())
    print(f"-> {out}")


if __name__ == "__main__":
    main()
