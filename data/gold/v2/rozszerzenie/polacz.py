"""Nowy gold v2: obie próby (po 100) z etykietami Claude Opus jako jedna próba warstwowa, n_h = 40/30/30.
Uruchamiać z katalogu głównego repo: PYTHONPATH=src python data/gold/v2/rozszerzenie/polacz.py

Obie próby są losowaniami bez zwracania z tych samych warstw (druga bez wypowiedzi z pierwszej), więc ich suma jest prostą
próbą losową warstwy i waga łączna to N_h / n_h. Wyjście w data/gold/v2/: gold_200.csv (etykiety i wagi),
gold_200_wyniki.csv (krok 5 i 7). Kontrola: te same funkcje na pierwszych 100 odtwarzają liczby z preprintu.
"""
import json
from pathlib import Path

import pandas as pd

from amc import estimation as E

V2 = Path("data/gold/v2")
HERE = V2 / "rozszerzenie"
REPS = 10_000


def opus(out_dir):
    rows = [json.loads(line) for f in sorted(out_dir.glob("run1_*.jsonl"))
            for line in open(f, encoding="utf-8") if line.strip()]
    return pd.DataFrame(rows)[["kolejnosc", "tematyczna", "sprzeczna", "pewnosc"]]


def main():
    first = pd.read_csv(V2 / "sample.csv").merge(opus(V2 / "opus" / "out"), on="kolejnosc", validate="1:1")
    both = pd.read_csv(HERE / "sample_200.csv")
    labels = pd.concat([opus(V2 / "opus" / "out"), opus(HERE / "opus" / "out")], ignore_index=True)
    gold = both.merge(labels, on="kolejnosc", validate="1:1")
    if len(gold) != 200 or gold["wypowiedz_id"].duplicated().any():
        raise SystemExit("gold nie ma 200 różnych wypowiedzi")
    gold.loc[gold["tematyczna"] == 0, "sprzeczna"] = pd.NA
    gold["sprzeczna"] = gold["sprzeczna"].astype("Int64")
    gold.insert(1, "losowanie", (gold["kolejnosc"] > 100).map({False: 1, True: 2}))
    gold["anotator"] = "claude-opus"
    gold.to_csv(V2 / "gold_200.csv", index=False)

    rows = {}
    for name, sample in (("pierwsze_100", first), ("gold_200", gold)):
        print(name, E.composition(sample).round(2).to_string(), sep="\n")
        a = E.arrays(sample)
        s = E.summarize(sample, E.proportions, reps=REPS)
        print((100 * s.drop(columns="bootstrap_brak")).round(1).to_string())
        for g in E.GROUPS:
            m = a["grupa"] == g
            print(g, "S", round((a["w"] * a["s"])[m].sum(), 1), "T", round((a["w"] * a["t"])[m].sum(), 1))
        q = E.quality(a)
        print({k: round(v, 2) for k, v in q.items() if "etykieta" not in k})
        rows[name] = pd.concat([s.stack(), pd.Series(q)])
    pd.DataFrame(rows).to_csv(V2 / "gold_200_wyniki.csv")

    low = gold.copy()
    low.loc[(low["sprzeczna"] == 1) & (low["pewnosc"] == "niska"), "sprzeczna"] = 0
    print("niska->0", (100 * E.summarize(low, E.proportions, reps=REPS).drop(columns="bootstrap_brak")).round(1).to_string(), sep="\n")
    worst = []
    for i in gold.index[gold["sprzeczna"] == 1]:
        flip = gold.copy()
        flip.loc[i, "sprzeczna"] = 0
        s = E.summarize(flip, E.proportions, reps=2_000).loc["roznica"]
        worst.append((round(100 * s["dolna_95_jednostronna"], 1), int(gold.loc[i, "kolejnosc"]), gold.loc[i, "grupa"], gold.loc[i, "pewnosc"]))
    print("po zamianie jednej sprzecznej, najniższe dolne granice:", sorted(worst)[:3])
    print("sprzeczne", int((gold["sprzeczna"] == 1).sum()), "niska", int(((gold["sprzeczna"] == 1) & (gold["pewnosc"] == "niska")).sum()))


if __name__ == "__main__":
    main()
