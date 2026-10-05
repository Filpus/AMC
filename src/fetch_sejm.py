"""Pobieranie stenogramów Sejmu z API (https://api.sejm.gov.pl) i budowa tabeli wypowiedzi.

Etapy (każdy wznawialny, pomija pliki, które już istnieją):
  mps          -> data/raw/term{T}/mp.json                    lista posłów (klub = stan na dzień pobrania)
  transcripts  -> data/raw/term{T}/transcripts/{n}_{data}.jsonl   metadane + surowy HTML wypowiedzi
  votings      -> data/raw/term{T}/votings/{n}_{data}.json    jedno głosowanie z każdego dnia (klub w chwili głosowania)
  clubs        -> data/interim/posel_klub_term{T}.csv         historia klubów: member_id | klub | od | do
  build        -> data/interim/wypowiedzi_term{T}.parquet     wypowiedzi z klubem przypisanym wg daty

Przykłady:
  python src/fetch_sejm.py --term 10                       # wszystko
  python src/fetch_sejm.py --term 10 --proceedings 61 62   # tylko wybrane posiedzenia
  python src/fetch_sejm.py --term 10 --steps build         # tylko przebudowa parquet
"""
import argparse
import html
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
API = "https://api.sejm.gov.pl/sejm/term{term}"

log = logging.getLogger("fetch_sejm")
session = requests.Session()
session.headers["User-Agent"] = "AMC-research (projekt studencki, analiza wypowiedzi)"


# ---------- HTTP ----------

def get(url, as_json=True, tries=5, timeout=60):
    """GET z ponawianiem (backoff wykładniczy). Zwraca None po wyczerpaniu prób albo przy 404."""
    for i in range(tries):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json() if as_json else r.text
        except requests.RequestException as e:
            if i == tries - 1:
                log.warning("nie udało się pobrać %s: %s", url, e)
                return None
            time.sleep(2 ** i)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)  # zapis atomowy: przerwane pobranie nie zostawia połówki pliku


# ---------- etapy ----------

def sitting_days(base, proceedings=None):
    """Lista (nr posiedzenia, data). Pomija posiedzenie nr 0 (techniczne, z przyszłymi datami) i bieżące."""
    procs = get(f"{base}/proceedings") or []
    days = [(p["number"], d) for p in procs
            if p["number"] > 0 and not p.get("current") for d in p["dates"]]
    if proceedings:
        days = [x for x in days if x[0] in set(proceedings)]
    return days


def fetch_mps(base, out):
    path = out / "mp.json"
    if not path.exists():
        write_json(path, get(f"{base}/MP"))
        log.info("posłowie -> %s", path)


def fetch_transcripts(base, out, days, workers):
    tdir = out / "transcripts"
    todo = [(n, d) for n, d in days if not (tdir / f"{n}_{d}.jsonl").exists()]
    log.info("stenogramy: %d dni do pobrania (z %d)", len(todo), len(days))
    with ThreadPoolExecutor(workers) as ex:
        for i, (n, d) in enumerate(todo, 1):
            meta = get(f"{base}/proceedings/{n}/{d}/transcripts")
            if not meta:
                log.warning("brak listy wypowiedzi: %s %s", n, d)
                continue
            st = meta["statements"]
            htmls = ex.map(lambda s: get(f"{base}/proceedings/{n}/{d}/transcripts/{s['num']}", as_json=False), st)
            rows = [{**s, "posiedzenie": n, "data": d, "html": h} for s, h in zip(st, htmls)]
            missing = sum(r["html"] is None for r in rows)
            if missing:
                log.warning("%s %s: %d wypowiedzi bez treści", n, d, missing)
            tdir.mkdir(parents=True, exist_ok=True)
            tmp = tdir / f"{n}_{d}.jsonl.tmp"
            tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
            tmp.replace(tdir / f"{n}_{d}.jsonl")
            log.info("[%d/%d] %s %s: %d wypowiedzi", i, len(todo), n, d, len(rows))


def fetch_votings(base, out, proceedings=None):
    """Z każdego dnia głosowań pobiera pierwsze głosowanie: lista głosów zawiera klub posła w tym dniu."""
    vdir = out / "votings"
    days = get(f"{base}/votings") or []
    if proceedings:
        days = [x for x in days if x["proceeding"] in set(proceedings)]
    for x in days:
        n, d = x["proceeding"], x["date"]
        path = vdir / f"{n}_{d}.json"
        if path.exists():
            continue
        sitting = get(f"{base}/votings/{n}") or []
        first = next((v for v in sorted(sitting, key=lambda v: v["votingNumber"])
                      if v["date"].startswith(d)), None)
        if not first:
            continue
        v = get(f"{base}/votings/{n}/{first['votingNumber']}")
        if v and v.get("votes"):
            write_json(path, {"posiedzenie": n, "data": d, "votingNumber": first["votingNumber"],
                              "votes": [{"member_id": g["MP"], "klub": g.get("club")} for g in v["votes"]]})
            log.info("głosowanie %s %s nr %s", n, d, first["votingNumber"])


def build_clubs(out, term):
    """Zwija obserwacje (member_id, klub, data) do przedziałów członkostwa."""
    obs = [{"member_id": g["member_id"], "klub": g["klub"], "data": v["data"]}
           for f in sorted((out / "votings").glob("*.json"))
           for v in [json.loads(f.read_text(encoding="utf-8"))] for g in v["votes"]]
    if not obs:
        log.warning("brak głosowań, pomijam historię klubów")
        return None
    df = pd.DataFrame(obs).sort_values(["member_id", "data"])
    df["zmiana"] = (df["klub"] != df.groupby("member_id")["klub"].shift()).cumsum()
    hist = (df.groupby(["member_id", "zmiana", "klub"], as_index=False)
              .agg(od=("data", "min"), do=("data", "max"))
              .drop(columns="zmiana"))
    path = INTERIM / f"posel_klub_term{term}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    hist.to_csv(path, index=False)
    n_zmian = (hist.groupby("member_id").size() > 1).sum()
    log.info("historia klubów: %d posłów, %d ze zmianą klubu -> %s", hist.member_id.nunique(), n_zmian, path)
    return df[["member_id", "klub", "data"]]


HEADER = re.compile(r"^.*?punkt porządku dziennego:.*?\(druk[^)]*\)\.?\s*", re.S)


def html_to_text(h):
    if not h:
        return ""
    t = re.sub(r"<(br|/p|/div|/h\d)[^>]*>", "\n", h, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\s*\n\s*", "\n", t).strip()


def build_table(out, term, club_obs):
    rows = [json.loads(l) for f in sorted((out / "transcripts").glob("*.jsonl"))
            for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    df = pd.DataFrame(rows)
    df["tekst"] = df["html"].map(html_to_text)
    # nagłówek wypowiedzi (kadencja, posiedzenie, punkt porządku, nazwy komisji) zaśmieca filtr słownikowy
    df["tekst"] = df["tekst"].str.replace(HEADER, "", n=1, regex=True)
    df["liczba_slow"] = df["tekst"].str.split().str.len().fillna(0).astype(int)
    df["wypowiedz_id"] = f"{term}_" + df["posiedzenie"].astype(str) + "_" + df["data"] + "_" + df["num"].astype(str)
    df = df.rename(columns={"name": "mowca", "memberID": "member_id", "function": "funkcja",
                            "startDateTime": "start", "endDateTime": "koniec", "unspoken": "niewygloszona"})
    df["kadencja"] = term

    mps = {m["id"]: m.get("club") for m in json.loads((out / "mp.json").read_text(encoding="utf-8"))}
    df["klub_dzis"] = df["member_id"].map(mps)

    # klub w dniu wypowiedzi = klub z ostatniego głosowania nie później niż ta data (a przed pierwszym: z pierwszego)
    df["klub"] = None
    if club_obs is not None:
        obs = club_obs.assign(data=pd.to_datetime(club_obs["data"])).sort_values("data")
        posl = df[df["member_id"] > 0].assign(_d=lambda x: pd.to_datetime(x["data"])).sort_values("_d")
        back = pd.merge_asof(posl, obs.rename(columns={"data": "_d", "klub": "k"}), on="_d", by="member_id", direction="backward")
        fwd = pd.merge_asof(posl, obs.rename(columns={"data": "_d", "klub": "k"}), on="_d", by="member_id", direction="forward")
        back.index, fwd.index = posl.index, posl.index
        df.loc[posl.index, "klub"] = back["k"].fillna(fwd["k"])
    df["klub"] = df["klub"].fillna(df["klub_dzis"])  # fallback, np. posłowie bez żadnego głosowania

    cols = ["wypowiedz_id", "kadencja", "posiedzenie", "data", "num", "start", "koniec", "mowca", "member_id",
            "klub", "klub_dzis", "funkcja", "rapporteur", "secretary", "niewygloszona", "tekst", "liczba_slow"]
    df = df[[c for c in cols if c in df.columns]].sort_values(["data", "num"])
    path = INTERIM / f"wypowiedzi_term{term}.parquet"
    df.to_parquet(path, index=False)
    zmienione = (df["klub"] != df["klub_dzis"]) & df["member_id"].gt(0)
    log.info("tabela: %d wypowiedzi, %d słów, %d z klubem innym niż dzisiejszy -> %s",
             len(df), df["liczba_slow"].sum(), zmienione.sum(), path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--term", type=int, default=10)
    ap.add_argument("--proceedings", type=int, nargs="*", help="numery posiedzeń (domyślnie wszystkie)")
    ap.add_argument("--steps", nargs="*", default=["mps", "transcripts", "votings", "clubs", "build"])
    ap.add_argument("--workers", type=int, default=4, help="równoległe zapytania (bądźmy uprzejmi dla API)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    base, out = API.format(term=a.term), RAW / f"term{a.term}"
    if "mps" in a.steps:
        fetch_mps(base, out)
    if "transcripts" in a.steps:
        fetch_transcripts(base, out, sitting_days(base, a.proceedings), a.workers)
    if "votings" in a.steps:
        fetch_votings(base, out, a.proceedings)
    club_obs = build_clubs(out, a.term) if {"clubs", "build"} & set(a.steps) else None
    if "build" in a.steps:
        build_table(out, a.term, club_obs)


if __name__ == "__main__":
    main()
