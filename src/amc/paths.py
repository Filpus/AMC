"""Ścieżki projektu i stałe wspólne dla całego pipeline'u."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"            # surowe odpowiedzi API (nie w repo)
INTERIM = ROOT / "data" / "interim"    # tabele z API: wypowiedzi, historia klubów
PROCESSED = ROOT / "data" / "processed"  # korpus gotowy do analizy + zagregowane tabele
FIGURES = ROOT / "figures"

API = "https://api.sejm.gov.pl/sejm/term{term}"
TERMS = [8, 9, 10]
# pierwszy dzień kadencji (do zaznaczania granic na wykresach)
TERM_START = {8: pd.Timestamp("2015-11-12"), 9: pd.Timestamp("2019-11-12"), 10: pd.Timestamp("2023-11-13")}


def raw_term(term):
    return RAW / f"term{term}"
