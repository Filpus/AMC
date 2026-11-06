"""Check and aggregate LLM gold annotations. Run from the repo root:
    .venv/Scripts/python data/gold/opus/check.py data/gold/opus/out [--texts data/gold/texts.csv] [--compare]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")
from amc import annotation  # noqa: E402

VERDICTS = {"sprzeczne", "zgodne", "brak_podstaw"}


def norm(s):
    s = re.sub(r"[‘’‚‛]", "'", s or "")
    s = re.sub(r"[“”„‟«»]", '"', s)
    s = re.sub(r"[‐-―−]", "-", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def found(quote, text):
    q = norm(quote)
    if not q:
        return False
    pieces = [p.strip(" .") for p in re.split(r"\(?(?:…|\.\.\.)\)?", q) if len(p.strip(" .")) > 8]
    return all(p in text for p in pieces) if pieces else q in text


def load_runs(out_dir):
    rows, problems = [], []
    for f in sorted(Path(out_dir).glob("*.jsonl")):
        run = re.match(r"(run\d+|pilot)", f.stem).group(1)
        for i, line in enumerate(open(f, encoding="utf-8")):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                problems.append(f"{f.name}:{i + 1} JSON {e}")
                continue
            r["run"], r["plik"] = run, f.name
            rows.append(r)
    return rows, problems


def check(rows, texts, ar6_text):
    problems, claims = [], []
    for r in rows:
        k, t = r.get("kolejnosc"), texts.get(r.get("kolejnosc"), "")
        tag = f"{r['plik']} #{k}"
        if r.get("tematyczna") not in (0, 1):
            problems.append(f"{tag} tematyczna={r.get('tematyczna')}")
        if r.get("tematyczna") == 0 and r.get("sprzeczna") not in (None, 0):
            problems.append(f"{tag} sprzeczna przy tematyczna=0")
        if r.get("tematyczna") == 1 and r.get("sprzeczna") not in (0, 1):
            problems.append(f"{tag} sprzeczna={r.get('sprzeczna')}")
        if r.get("fragment") and not found(r["fragment"], t):
            problems.append(f"{tag} fragment spoza tekstu: {r['fragment'][:80]}")
        tw = r.get("twierdzenia") or []
        has_contra = any(c.get("werdykt") == "sprzeczne" for c in tw)
        if r.get("tematyczna") == 1 and bool(r.get("sprzeczna")) != has_contra:
            problems.append(f"{tag} sprzeczna={r.get('sprzeczna')} a twierdzenia sprzeczne={has_contra}")
        for j, c in enumerate(tw, 1):
            ok_cytat = found(c.get("cytat", ""), t)
            ok_ar6 = None
            if c.get("werdykt") not in VERDICTS:
                problems.append(f"{tag}.{j} werdykt={c.get('werdykt')}")
            if c.get("werdykt") in ("sprzeczne", "zgodne"):
                ok_ar6 = bool(c.get("ar6")) and found(c.get("ar6_cytat", ""), ar6_text)
                if not ok_ar6:
                    problems.append(f"{tag}.{j} {c.get('werdykt')} bez dosłownego cytatu AR6 ({c.get('ar6')}): "
                                    f"{(c.get('ar6_cytat') or '')[:80]}")
            if not ok_cytat:
                problems.append(f"{tag}.{j} cytat spoza tekstu: {(c.get('cytat') or '')[:80]}")
            claims.append({"run": r["run"], "kolejnosc": k, **{x: c.get(x) for x in
                           ("cytat", "twierdzenie", "werdykt", "ar6", "ar6_cytat", "uzasadnienie")},
                           "cytat_ok": ok_cytat, "ar6_ok": ok_ar6})
    return problems, pd.DataFrame(claims)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--texts", default="data/gold/texts.csv")
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args()
    texts = {int(k): norm(v) for k, v in pd.read_csv(a.texts)[["kolejnosc", "tekst"]].values} \
        if a.texts.endswith(".csv") else parse_md(a.texts)
    ar6_text = norm(" ".join(pd.read_parquet("data/ar6/fragments.parquet")["tekst"]))
    rows, problems = load_runs(a.out_dir)
    p2, claims = check(rows, texts, ar6_text)
    problems += p2
    df = pd.DataFrame(rows)
    print(f"wiersze {len(df)}, przebiegi {df['run'].value_counts().to_dict()}, twierdzenia {len(claims)}")
    dup = df[df.duplicated(["run", "kolejnosc"], keep=False)]
    if len(dup):
        problems.append(f"powtórzone: {dup[['run', 'kolejnosc']].values.tolist()}")
    for r in sorted(df["run"].unique()):
        miss = set(texts) - set(df.loc[df["run"] == r, "kolejnosc"])
        if miss:
            problems.append(f"{r}: brak {len(miss)}: {sorted(miss)[:15]}")
    print(f"problemy {len(problems)}")
    for p in problems:
        print("  ", p)
    if len(claims):
        print("werdykty", claims["werdykt"].value_counts().to_dict())
    df["etykieta"] = (df["tematyczna"] == 1) & (df["sprzeczna"] == 1)
    wide = df.pivot_table(index="kolejnosc", columns="run", values=["tematyczna", "etykieta"], aggfunc="first")
    agg = pd.DataFrame({"tem_glosy": wide["tematyczna"].sum(axis=1), "sprz_glosy": wide["etykieta"].sum(axis=1),
                        "n": wide["tematyczna"].notna().sum(axis=1)})
    agg["tematyczna_llm"] = (agg["tem_glosy"] * 2 > agg["n"]).astype(int)
    agg["sprzeczna_llm"] = ((agg["sprz_glosy"] * 2 > agg["n"]) & (agg["tematyczna_llm"] == 1)).astype(int)
    agg["jednomyslnie"] = agg["tem_glosy"].isin([0, agg["n"].max()]) & agg["sprz_glosy"].isin([0, agg["n"].max()])
    niska = df[df["pewnosc"] == "niska"].groupby("kolejnosc").size()
    agg["niska_pewnosc"] = niska.reindex(agg.index).fillna(0).astype(int)
    out = Path(a.out_dir).parent
    claims.to_csv(out / "llm_claims.csv", index=False)
    print(f"głosy jednomyślne {int(agg['jednomyslnie'].sum())}/{len(agg)}; tematyczne {agg['tematyczna_llm'].sum()}, "
          f"sprzeczne {agg['sprzeczna_llm'].sum()}")
    if a.compare:
        design = pd.read_csv("data/gold/sample.csv")
        hum = annotation.load_parts(["data/gold/annotations_FP.csv", "data/gold/annotations_DK.csv"], design)
        m = design[["kolejnosc", "grupa", "warstwa", "waga"]].merge(hum, on="kolejnosc").merge(
            agg.reset_index(), on="kolejnosc")
        m["sprzeczna"] = m["sprzeczna"].fillna(0).astype(int)
        m["etykieta"] = ((m["tematyczna"] == 1) & (m["sprzeczna"] == 1)).astype(int)
        for col, llm in (("tematyczna", "tematyczna_llm"), ("etykieta", "sprzeczna_llm")):
            ct = pd.crosstab(m[col], m[llm], rownames=[f"ludzie {col}"], colnames=["LLM"])
            po = (m[col] == m[llm]).mean()
            pe = sum(m[col].eq(v).mean() * m[llm].eq(v).mean() for v in (0, 1))
            print(f"\n{col}: zgodność {po:.2f}, kappa {(po - pe) / (1 - pe):.2f}\n{ct}")
        diff = m[(m["tematyczna"] != m["tematyczna_llm"]) | (m["etykieta"] != m["sprzeczna_llm"])]
        cols = ["kolejnosc", "anotator", "grupa", "warstwa", "waga", "tematyczna", "etykieta", "tem_glosy",
                "sprz_glosy", "n", "niska_pewnosc", "komentarz"]
        diff[cols].sort_values(["waga", "kolejnosc"], ascending=[False, True]).to_csv(out / "niezgodnosci.csv",
                                                                                      index=False)
        m.to_csv(out / "porownanie.csv", index=False)
        print(f"\nniezgodności {len(diff)} -> {out / 'niezgodnosci.csv'}")


def parse_md(path):
    txt = open(path, encoding="utf-8").read()
    parts = re.split(r"(?m)^## kolejnosc (\d+)\s*$", txt)
    return {int(parts[i]): norm(parts[i + 1]) for i in range(1, len(parts), 2)}


if __name__ == "__main__":
    main()
