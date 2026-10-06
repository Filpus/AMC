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
import json
import logging
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from amc import http, speakers, text
from amc.http import write_json
from amc.paths import API, INTERIM, RAW

log = logging.getLogger("fetch_sejm")


def get(url, as_json=True):
    return http.get(url, as_="json" if as_json else "text")


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
    df = pd.DataFrame(obs)
    hist = speakers.club_history(df)
    path = INTERIM / f"posel_klub_term{term}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    hist.to_csv(path, index=False)
    n_zmian = (hist.groupby("member_id").size() > 1).sum()
    log.info("historia klubów: %d posłów, %d ze zmianą klubu -> %s", hist.member_id.nunique(), n_zmian, path)
    return df[["member_id", "klub", "data"]]


def build_table(out, term, club_obs):
    rows = [json.loads(l) for f in sorted((out / "transcripts").glob("*.jsonl"))
            for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    df = pd.DataFrame(rows)
    df["tekst"] = df["html"].map(text.html_to_text)
    # nagłówek wypowiedzi (kadencja, posiedzenie, punkt porządku, nazwy komisji) zaśmieca filtr słownikowy
    df["tekst"] = df["tekst"].str.replace(text.HEADER_PLENARNY, "", n=1, regex=True)
    df["liczba_slow"] = text.word_count(df["tekst"])
    df["wypowiedz_id"] = f"{term}_" + df["posiedzenie"].astype(str) + "_" + df["data"] + "_" + df["num"].astype(str)
    df = df.rename(columns={"name": "mowca", "memberID": "member_id", "function": "funkcja",
                            "startDateTime": "start", "endDateTime": "koniec", "unspoken": "niewygloszona"})
    df["kadencja"] = term

    mps = {m["id"]: m.get("club") for m in json.loads((out / "mp.json").read_text(encoding="utf-8"))}
    df["klub_dzis"] = df["member_id"].map(mps)

    # klub w dniu wypowiedzi = klub z ostatniego głosowania nie później niż ta data (a przed pierwszym: z pierwszego)
    df["klub"] = speakers.club_on_date(df, club_obs) if club_obs is not None else None
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
