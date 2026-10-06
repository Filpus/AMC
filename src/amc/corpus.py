"""Korpus gotowy do analizy: data/processed/korpus_{plenarne,komisje}.parquet.

Z tabel zbudowanych przez fetch_sejm.py / fetch_komisje.py (data/interim/) robi jeden format:
  tekst                 oczyszczony (bez nagłówka stenogramu, wtrąceń z sali, stopki)
  liczba_slow           po czyszczeniu (liczba_slow_surowa — przed)
  rola                  poseł / prowadzący / rząd / inni
  blok                  blok polityczny (posłowie), patrz speakers.KLUB_BLOK
  merytoryczna          True dla wypowiedzi branych do analizy tematycznej (bez prowadzącego, >= MIN_SLOW słów)
  <temat>, <temat>_tem  trafienia słowników i flagi wypowiedzi tematycznych (topics.add_topic_columns)
  data, miesiac, rok    daty jako datetime
Korpus zawiera wszystkie wypowiedzi (także niemerytoryczne), żeby dało się liczyć przeglądy i lejek filtrów.
"""
import logging

import pandas as pd

from . import paths, speakers, text, topics

log = logging.getLogger("amc.corpus")

MIN_SLOW = 40
RODZAJE = ("plenarne", "komisje")


def _wspolne(df):
    df["data"] = pd.to_datetime(df["data"])
    df["miesiac"] = df["data"].dt.to_period("M").dt.to_timestamp()
    df["rok"] = df["data"].dt.year
    df["liczba_slow"] = text.word_count(df["tekst"])
    df["blok"] = speakers.blok(df["klub"], df["member_id"])
    df["merytoryczna"] = df["rola"].ne("prowadzący") & df["liczba_slow"].ge(MIN_SLOW)
    return topics.add_topic_columns(df)


def _wczytaj(wzorzec, terms):
    pliki = [paths.INTERIM / wzorzec.format(t=t) for t in terms]
    brak = [p.name for p in pliki if not p.exists()]
    if brak:
        log.warning("brak plików (pomijam): %s", ", ".join(brak))
    pliki = [p for p in pliki if p.exists()]
    if not pliki:
        raise FileNotFoundError(f"brak danych {wzorzec} — najpierw uruchom skrypt pobierający")
    return pd.concat([pd.read_parquet(p) for p in pliki], ignore_index=True)


def build_plenarne(terms=paths.TERMS):
    """Posiedzenia plenarne z data/interim/wypowiedzi_term{T}.parquet (fetch_sejm.py)."""
    df = _wczytaj("wypowiedzi_term{t}.parquet", terms)
    df["liczba_slow_surowa"] = df["liczba_slow"]
    df["tekst"] = [text.clean_statement(t, n) for t, n in zip(df["tekst"], df["mowca"])]
    df["rola"] = [speakers.rola_plenarna(f, n) for f, n in zip(df["funkcja"], df["mowca"])]
    return _wspolne(df)


def build_komisje(terms=paths.TERMS, committees=None):
    """Komisje z data/interim/komisje_wypowiedzi_term{T}.parquet (fetch_komisje.py); rola jest już w tabeli."""
    df = _wczytaj("komisje_wypowiedzi_term{t}.parquet", terms)
    if committees:
        df = df[df["komisja"].isin(committees)].reset_index(drop=True)
    df["liczba_slow_surowa"] = text.word_count(df["tekst"])
    df["tekst"] = [text.clean_statement(t) for t in df["tekst"]]
    return _wspolne(df)


def corpus_path(rodzaj):
    return paths.PROCESSED / f"korpus_{rodzaj}.parquet"


def build(rodzaj, terms=paths.TERMS, committees=None):
    """Buduje i zapisuje korpus danego rodzaju; zwraca DataFrame."""
    df = build_plenarne(terms) if rodzaj == "plenarne" else build_komisje(terms, committees)
    path = corpus_path(rodzaj)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    log.info("korpus %s: %d wypowiedzi (%d merytorycznych), %d słów -> %s",
             rodzaj, len(df), df["merytoryczna"].sum(), df["liczba_slow"].sum(), path)
    return df


def load(rodzaj):
    """Wczytuje gotowy korpus (data/processed/korpus_<rodzaj>.parquet)."""
    if rodzaj not in RODZAJE:
        raise ValueError(f"rodzaj musi być jednym z {RODZAJE}")
    path = corpus_path(rodzaj)
    if not path.exists():
        raise FileNotFoundError(f"brak {path} — uruchom: python src/build_corpus.py")
    return pd.read_parquet(path)
