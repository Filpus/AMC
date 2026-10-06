"""Pobieranie zapisów posiedzeń komisji sejmowych z API (https://api.sejm.gov.pl) i budowa tabeli wypowiedzi.

Etapy (każdy wznawialny, pomija pliki, które już istnieją):
  sittings  -> data/raw/term{T}/komisje/{KOD}/sittings.json        lista posiedzeń komisji
  records   -> data/raw/term{T}/komisje/{KOD}/{nr}.html (lub .pdf) zapis przebiegu posiedzenia
  build     -> data/interim/komisje_wypowiedzi_term{T}.parquet     wypowiedzi z mówcą, klubem i rolą

API dla komisji zwraca jeden dokument na posiedzenie (nie listę wypowiedzi jak dla posiedzeń plenarnych),
więc wypowiedzi wydzielamy z tekstu po etykietach mówców:
  * HTML: etykieta to pogrubiony akapit "<p><b>Poseł Jan Kowalski (PiS):</b>" — podział precyzyjny,
  * PDF (zapas, gdy HTML zwraca błąd): linia zakończona dwukropkiem, wyglądająca jak etykieta — podział
    heurystyczny, takie wiersze mają zrodlo = "pdf".
Posiedzenia wspólne kilku komisji mają ten sam zapis pod każdą komisją — w build zostaje jedna kopia,
a kolumna `komisje` wymienia wszystkie pobrane komisje, pod którymi wystąpił zapis.

Przykłady:
  python src/fetch_komisje.py --term 9 --committees ZDR OSZ          # wszystko dla dwóch komisji
  python src/fetch_komisje.py --term 9 --committees ZDR --limit 10   # pilotaż: 10 posiedzeń
  python src/fetch_komisje.py --term 9 --committees ZDR --steps build
"""
import argparse
import hashlib
import html
import json
import logging
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from fetch_sejm import API, INTERIM, RAW, write_json

log = logging.getLogger("fetch_komisje")
session = requests.Session()
session.headers["User-Agent"] = "AMC-research (projekt studencki, analiza wypowiedzi)"

DOMYSLNE_KOMISJE = ["ZDR", "OSZ", "ESK", "RRW"]


# ---------- HTTP ----------

def get_raw(url, tries=5, timeout=180):
    """GET z ponawianiem. Zwraca Response albo None (404 / 502 po wyczerpaniu prób / błąd sieci).
    API komisji często odpowiada 502 albo bardzo wolno — stąd długi timeout i backoff."""
    for i in range(tries):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code >= 500:
                raise requests.HTTPError(f"{r.status_code}")
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if i == tries - 1:
                log.warning("nie udało się pobrać %s: %s", url, e)
                return None
            time.sleep(2 ** (i + 1))


def write_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


# ---------- etapy ----------

def fetch_sittings(base, kdir, code):
    path = kdir / code / "sittings.json"
    if not path.exists():
        r = get_raw(f"{base}/committees/{code}/sittings")
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
    r = get_raw(f"{base}/committees/{code}/sittings/{num}/html")
    if r is not None and "transcript" in r.text:
        write_bytes(d / f"{num}.html", r.content)
        return "html"
    r = get_raw(f"{base}/committees/{code}/sittings/{num}/pdf")
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


# ---------- parsowanie ----------

ETYKIETA_HTML = re.compile(r"<p[^>]*>\s*<b>([^<]{3,250}?):\s*</b>", re.I)
# etykieta w PDF: krótka linia od wielkiej litery zakończona dwukropkiem, z funkcją typową dla zapisów komisji
ETYKIETA_PDF = re.compile(
    r"^((?:Przewodnicząc\w*|Zastępca|Poseł|Posłanka|Senator\w*|Minister|Wiceminister|Podsekretarz|Sekretarz|Prezes|"
    r"Wiceprezes|Dyrektor|Zastępca|Naczelnik|Główn\w+|Rzecznik|Legislator|Ekspert|Przedstawiciel\w*|Członek|Kierownik|"
    r"Doradca|Pełnomocnik|Prokurator|Radca|Konsultant|Członkini|Specjalist\w+|Starszy|Wojewoda|Burmistrz|Prezydent|"
    r"Wójt|Marszałek|Komendant|Inspektor|Pani|Pan)\b[^\n:]{2,200}):\s*$", re.M)
STOPKA_PDF = re.compile(r"^\s*(Pełny zapis przebiegu posiedzenia.*|Komisji .*\(nr \d+\)|\d+|M\.P\.\s*\d*)\s*$", re.M)


def html_to_text(h):
    t = re.sub(r"<(br|/p|p|/div|/h\d)[^>]*>", "\n", h, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\s*\n\s*", "\n", t).strip()


def split_html(h):
    """[(etykieta, tekst)] z zapisu HTML. Wstęp przed pierwszą etykietą (porządek obrad, lista obecnych) pomijamy."""
    h = h[h.find('class="transcript"'):] if 'class="transcript"' in h else h
    parts = ETYKIETA_HTML.split(h)
    return [(re.sub(r"\s+", " ", html.unescape(parts[i])).strip(), html_to_text(parts[i + 1]))
            for i in range(1, len(parts) - 1, 2)]


def split_pdf(path):
    try:
        t = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError) as e:
        log.warning("pdftotext nie zadziałał dla %s: %s", path, e)
        return []
    t = STOPKA_PDF.sub("", t)
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)  # dzielenie wyrazów na końcu linii
    parts = ETYKIETA_PDF.split(t)
    return [(re.sub(r"\s+", " ", parts[i]).strip(), re.sub(r"\s*\n\s*", "\n", parts[i + 1]).strip())
            for i in range(1, len(parts) - 1, 2)]


KLUB_W_ETYKIECIE = re.compile(r"[(/]\s*([^()/]{1,40}?)\s*[)/]")


def rola(etykieta):
    e = etykieta.lower()
    if e.startswith("przewodnicząc") or "prowadząc" in e:
        return "prowadzący"
    if re.search(r"\bpos(eł|łanka)\b", e):
        return "poseł"
    if re.search(r"minist|stanu|prezes rady", e):
        return "rząd"
    return "inni"


def mp_index(out):
    """Słownik 'Imię [Drugie] Nazwisko' -> id posła z mp.json danej kadencji
    oraz lista (id, imię, nazwisko) do dopasowania zapasowego."""
    idx, osoby = {}, []
    for m in json.loads((out / "mp.json").read_text(encoding="utf-8")):
        idx[f"{m['firstName']} {m['lastName']}"] = m["id"]
        if m.get("secondName"):
            idx[f"{m['firstName']} {m['secondName']} {m['lastName']}"] = m["id"]
        osoby.append((m["id"], m["firstName"], m["lastName"]))
    return idx, osoby


def match_mp(etykieta, idx, names_by_len, osoby):
    """Id posła, jeśli etykieta (bez nawiasów i dopisków) kończy się jego imieniem i nazwiskiem.
    Zapasowo: imię i nazwisko występują w etykiecie w dowolnej kolejności (np. "Haidar Riad") — jeśli jednoznacznie.
    Inaczej 0 (osoba spoza Sejmu albo literówka w zapisie)."""
    e = re.sub(r"\([^)]*\)|/[^/]*/", " ", etykieta)
    e = re.split(r"\s[–-]\s", e)[0]
    e = re.sub(r"\s+", " ", e).strip()
    for n in names_by_len:
        if e.endswith(n):
            return idx[n]
    slowa = set(e.split())
    kand = {i for i, imie, nazw in osoby if imie in slowa and nazw in slowa}
    return kand.pop() if len(kand) == 1 else 0


def club_on_date(df, term):
    """Klub w dniu posiedzenia wg historii klubów z głosowań (data/interim/posel_klub_term{T}.csv)."""
    path = INTERIM / f"posel_klub_term{term}.csv"
    if not path.exists():
        log.warning("brak %s — klub tylko z etykiety", path)
        return pd.Series(None, index=df.index, dtype=object)
    hist = pd.read_csv(path)
    hist["od"], hist["do"] = pd.to_datetime(hist["od"]), pd.to_datetime(hist["do"])
    posl = df[df["member_id"] > 0].assign(_d=pd.to_datetime(df["data"])).sort_values("_d")
    obs = hist.rename(columns={"od": "_d"}).sort_values("_d")[["member_id", "_d", "klub"]]
    back = pd.merge_asof(posl, obs.rename(columns={"klub": "k"}), on="_d", by="member_id", direction="backward")
    fwd = pd.merge_asof(posl, obs.rename(columns={"klub": "k"}), on="_d", by="member_id", direction="forward")
    back.index, fwd.index = posl.index, posl.index
    return back["k"].fillna(fwd["k"]).reindex(df.index)


def build_table(out, term, codes):
    kdir = out / "komisje"
    idx, osoby = mp_index(out)
    names = sorted(idx, key=len, reverse=True)
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
                klub_et = KLUB_W_ETYKIECIE.search(et)
                rows.append({
                    "wypowiedz_id": f"{term}_{code}_{num}_{i}", "kadencja": term, "komisja": code, "komisje": komisje,
                    "posiedzenie_nr": num, "data": s.get("date"), "num": i, "etykieta": et,
                    "member_id": match_mp(et, idx, names, osoby),
                    "klub_etykieta": klub_et.group(1) if klub_et and rola(et) in ("poseł", "prowadzący") else None,
                    "rola": rola(et), "tekst": tekst, "zrodlo": zrodlo,
                    "porzadek": re.sub(r"<[^>]+>", " ", s.get("agenda") or "").strip(),
                })
    if not rows:
        log.warning("brak wypowiedzi do zapisania")
        return
    df = pd.DataFrame(rows)
    df["komisje"] = df["komisje"].map(lambda k: ",".join(sorted(set(k))))
    df["liczba_slow"] = df["tekst"].str.split().str.len().fillna(0).astype(int)
    df["klub"] = club_on_date(df, term).fillna(df["klub_etykieta"])
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
