"""Pobieranie zapisów posiedzeń komisji sejmowych z API (https://api.sejm.gov.pl) i budowa tabeli wypowiedzi.

Etapy (każdy wznawialny, pomija pliki, które już istnieją):
  sittings  -> data/raw/term{T}/komisje/{KOD}/sittings.json        lista posiedzeń komisji
  records   -> data/raw/term{T}/komisje/{KOD}/{nr}.html (lub .pdf) zapis przebiegu posiedzenia
  build     -> data/interim/komisje_wypowiedzi_term{T}.parquet     wypowiedzi z mówcą, klubem i rolą

Zapis posiedzenia dzielimy na wypowiedzi po etykietach mówców (amc/komisje.py): HTML precyzyjnie,
PDF (zapas, gdy HTML zwraca błąd) heurystycznie — takie wiersze mają zrodlo = "pdf".
Posiedzenia wspólne kilku komisji mają ten sam zapis pod każdą komisją — w build zostaje jedna kopia,
a kolumna `komisje` wymienia wszystkie pobrane komisje, pod którymi wystąpił zapis.

Przykłady:
  python src/fetch_komisje.py --term 9 --committees ZDR OSZ          # wszystko dla dwóch komisji
  python src/fetch_komisje.py --term 9 --committees ZDR --limit 10   # pilotaż: 10 posiedzeń
  python src/fetch_komisje.py --term 9 --committees ZDR --steps build
"""
import argparse
import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pandas as pd

from amc import http, speakers
from amc.http import write_bytes, write_json
from amc.komisje import split_html, split_pdf
from amc.paths import API, INTERIM, RAW
from amc.text import word_count

log = logging.getLogger("fetch_komisje")

DOMYSLNE_KOMISJE = ["ZDR", "OSZ", "ESK", "RRW"]


# ---------- etapy ----------

def fetch_sittings(base, kdir, code):
    path = kdir / code / "sittings.json"
    if not path.exists():
        r = http.get(f"{base}/committees/{code}/sittings", as_="response", timeout=180)
        if r is None:
            log.warning("%s: brak listy posiedzeń", code)
            return []
        write_json(path, r.json())
    return json.loads(path.read_text(encoding="utf-8"))


def do_pobrania(sittings):
    """Tylko posiedzenia, które się odbyły i były jawne (zamknięte nie mają publicznego zapisu)."""
    dzis = date.today().isoformat()
    return [s for s in sittings
            if s.get("status", "FINISHED") == "FINISHED" and not s.get("closed") and s.get("date", "") <= dzis]


def fetch_record(base, kdir, code, num):
    """Najpierw HTML, a gdy się nie uda — PDF. Pusty plik .missing zapamiętuje, że nie było żadnego."""
    d = kdir / code
    if any((d / f"{num}{ext}").exists() for ext in (".html", ".pdf", ".missing")):
        return "pominięte"
    r = http.get(f"{base}/committees/{code}/sittings/{num}/html", as_="response", timeout=180)
    if r is not None and "transcript" in r.text:
        write_bytes(d / f"{num}.html", r.content)
        return "html"
    r = http.get(f"{base}/committees/{code}/sittings/{num}/pdf", as_="response", timeout=180)
    if r is not None and r.content[:4] == b"%PDF":
        write_bytes(d / f"{num}.pdf", r.content)
        return "pdf"
    write_bytes(d / f"{num}.missing", b"")
    return "brak"


def fetch_records(base, kdir, code, sittings, workers, limit=None):
    todo = do_pobrania(sittings)
    if limit:
        todo = todo[:limit]
    log.info("%s: %d posiedzeń do sprawdzenia", code, len(todo))
    stats = {}
    with ThreadPoolExecutor(workers) as ex:
        for i, wynik in enumerate(ex.map(lambda s: fetch_record(base, kdir, code, s["num"]), todo), 1):
            stats[wynik] = stats.get(wynik, 0) + 1
            if i % 25 == 0 or i == len(todo):
                log.info("%s: [%d/%d] %s", code, i, len(todo), stats)


def build_table(out, term, codes):
    kdir = out / "komisje"
    match_mp = speakers.MpMatcher.from_file(out / "mp.json")
    rows, seen = [], {}
    for code in codes:
        sp = kdir / code / "sittings.json"
        if not sp.exists():
            continue
        meta = {s["num"]: s for s in json.loads(sp.read_text(encoding="utf-8"))}
        for f in sorted((kdir / code).glob("*.*"), key=lambda p: (p.suffix, p.stem)):
            if f.suffix not in (".html", ".pdf") or not f.stem.isdigit():
                continue
            num = int(f.stem)
            if f.suffix == ".html":
                wyp, zrodlo = split_html(f.read_text(encoding="utf-8", errors="replace")), "html"
            else:
                wyp, zrodlo = split_pdf(f), "pdf"
            if not wyp:
                log.warning("%s nr %s: nie wydzielono wypowiedzi (%s)", code, num, zrodlo)
                continue
            # posiedzenia wspólne: ten sam zapis pod kilkoma komisjami -> zostaje jedna kopia
            klucz = hashlib.md5("".join(t for _, t in wyp[:20]).encode()).hexdigest()
            if klucz in seen:
                seen[klucz].append(code)
                continue
            seen[klucz] = komisje = [code]
            s = meta.get(num, {})
            for i, (et, tekst) in enumerate(wyp):
                rola = speakers.rola_komisja(et)
                rows.append({
                    "wypowiedz_id": f"{term}_{code}_{num}_{i}", "kadencja": term, "komisja": code, "komisje": komisje,
                    "posiedzenie_nr": num, "data": s.get("date"), "num": i, "etykieta": et,
                    "member_id": match_mp(et),
                    "klub_etykieta": speakers.klub_z_etykiety(et) if rola in ("poseł", "prowadzący") else None,
                    "rola": rola, "tekst": tekst, "zrodlo": zrodlo,
                    "porzadek": re.sub(r"<[^>]+>", " ", s.get("agenda") or "").strip(),
                })
    if not rows:
        log.warning("brak wypowiedzi do zapisania")
        return
    df = pd.DataFrame(rows)
    df["komisje"] = df["komisje"].map(lambda k: ",".join(sorted(set(k))))
    df["liczba_slow"] = word_count(df["tekst"])
    # klub w dniu posiedzenia z historii klubów (fetch_sejm.py --steps clubs); zapasowo — z etykiety
    hist = INTERIM / f"posel_klub_term{term}.csv"
    if hist.exists():
        df["klub"] = speakers.club_on_date(df, speakers.club_obs_from_history(hist)).fillna(df["klub_etykieta"])
    else:
        log.warning("brak %s — klub tylko z etykiety", hist)
        df["klub"] = df["klub_etykieta"]
    path = INTERIM / f"komisje_wypowiedzi_term{term}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    posel = df["rola"].eq("poseł")
    log.info("tabela: %d wypowiedzi z %d posiedzeń, %d słów; etykieta posła rozpoznana w %d/%d wypowiedzi; "
             "z PDF: %d -> %s", len(df), df.groupby(["komisja", "posiedzenie_nr"]).ngroups, df["liczba_slow"].sum(),
             (posel & df["member_id"].gt(0)).sum(), posel.sum(), (df["zrodlo"] == "pdf").sum(), path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--term", type=int, default=10)
    ap.add_argument("--committees", nargs="*", default=DOMYSLNE_KOMISJE, help="kody komisji (domyślnie ZDR OSZ ESK RRW)")
    ap.add_argument("--steps", nargs="*", default=["sittings", "records", "build"])
    ap.add_argument("--limit", type=int, help="pobierz tylko N pierwszych posiedzeń każdej komisji (pilotaż)")
    ap.add_argument("--workers", type=int, default=3, help="równoległe zapytania (API komisji jest wolne i kapryśne)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    base, out = API.format(term=a.term), RAW / f"term{a.term}"
    kdir = out / "komisje"
    for code in a.committees:
        sittings = fetch_sittings(base, kdir, code) if {"sittings", "records"} & set(a.steps) else []
        if "records" in a.steps:
            fetch_records(base, kdir, code, sittings, a.workers, a.limit)
    if "build" in a.steps:
        build_table(out, a.term, a.committees)


if __name__ == "__main__":
    main()
