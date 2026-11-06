"""Rozszerzenie golda v2 ze 100 do 200 wypowiedzi. Uruchamiać z katalogu głównego repo: PYTHONPATH=src python <ten plik>

Warstwy jak w `data/gold/v2/sample.csv` (etykiety przebiegu v2: topic_v1, claims_v2, verdict_v2, EmbeddingGemma EN;
prawica z Kukiz15 i Republikanami). Z każdej warstwy losujemy 20/15/15 wypowiedzi bez zwracania spośród tych, których nie
ma w pierwszej próbie, ziarnem 1: suma obu prób jest prostą próbą losową warstwy, więc waga łączna to N_h / n_h przy
n_h = 40/30/30.

Wyjście: sample.csv (nowe 100, kolejnosc 101-200), sample_200.csv (obie próby, wspólne wagi), texts.csv.
Teksty: stenogramy z api.sejm.gov.pl, to samo czyszczenie i maskowanie co w korpusie. Do kontroli odtwarzamy też teksty
pierwszej próby i porównujemy je z data/gold/v2/texts.csv.
"""
import sys
import time
from pathlib import Path

import pandas as pd
import requests

from amc import estimation as E
from amc import text as T
from amc.paths import API

HERE = Path(__file__).resolve().parent
SEED = 1
LABELS = "data/processed/labels/gemma4_12b__verdict_v2__en_embeddinggemma_300m.csv"
BASE = API.format(term=10)


def fetch(url, tries=6):
    """Bez wspólnej sesji amc.http: keep-alive potrafi zawisnąć na tym API."""
    for i in range(tries):
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "AMC-research (projekt studencki)"})
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"ponawiam ({e})", flush=True)
            time.sleep(2 ** i)
    sys.exit(f"nie udało się pobrać {url}")


def statement_text(wid, meta):
    _, n, d, num = wid.split("_")
    html = fetch(f"{BASE}/proceedings/{n}/{d}/transcripts/{num}").text
    if (n, d) not in meta:
        meta[n, d] = {s["num"]: s for s in fetch(f"{BASE}/proceedings/{n}/{d}/transcripts").json()["statements"]}
    t = T.html_to_text(html)
    t = pd.Series([t]).str.replace(T.HEADER_PLENARNY, "", n=1, regex=True).iloc[0]
    return T.mask_speakers(T.clean_statement(t, meta[n, d][int(num)]["name"]))


def main():
    first = pd.read_csv("data/gold/v2/sample.csv")
    labels = pd.read_csv(LABELS)
    d = labels.assign(warstwa=E.stratum(labels))
    N = d.groupby(["grupa", "warstwa"]).size().rename("N_h")
    check = first.groupby(["grupa", "warstwa"])["N_h"].first()
    if not check.equals(N.reindex(check.index).rename("N_h")):
        sys.exit("warstwy etykiet różnią się od warstw pierwszej próby")

    rest = d[~d["wypowiedz_id"].isin(first["wypowiedz_id"])]
    parts = [cell.sample(E.SIZES[h], random_state=SEED).assign(N_h=N[g, h], n_h=E.SIZES[h])
             for (g, h), cell in rest.groupby(["grupa", "warstwa"])]
    new = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    new["waga"], new["ziarno"] = new["N_h"] / new["n_h"], SEED
    new.insert(0, "kolejnosc", range(101, 201))
    cols = ["kolejnosc", "wypowiedz_id", "grupa", "warstwa", "N_h", "n_h", "waga", "ziarno"]
    new[cols].to_csv(HERE / "sample.csv", index=False)

    both = pd.concat([first[cols], new[cols]], ignore_index=True)
    if both["wypowiedz_id"].duplicated().any():
        sys.exit("powtórzone wypowiedzi")
    both["n_h"] = both.groupby(["grupa", "warstwa"])["wypowiedz_id"].transform("size")
    both["waga"] = both["N_h"] / both["n_h"]
    both.to_csv(HERE / "sample_200.csv", index=False)
    print(both.groupby(["grupa", "warstwa"]).agg(N_h=("N_h", "first"), n_h=("n_h", "first"), waga=("waga", "first")))

    meta = {}
    ref = pd.read_csv("data/gold/v2/texts.csv").set_index("kolejnosc")["tekst"]
    diff = [k for k, w in zip(first["kolejnosc"], first["wypowiedz_id"]) if statement_text(w, meta) != ref[k]]
    print(f"kontrola: {100 - len(diff)}/100 tekstów pierwszej próby odtworzonych co do znaku; różne: {diff}")
    if diff:
        sys.exit("teksty nie odtwarzają pierwszej próby")
    new.assign(tekst=[statement_text(w, meta) for w in new["wypowiedz_id"]])[["kolejnosc", "tekst"]].to_csv(
        HERE / "texts.csv", index=False)
    print(f"100 tekstów -> {HERE / 'texts.csv'}")


if __name__ == "__main__":
    main()
