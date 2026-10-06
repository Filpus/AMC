"""Parsowanie zapisów posiedzeń komisji: podział dokumentu na wypowiedzi po etykietach mówców.

API dla komisji zwraca jeden dokument na posiedzenie, więc wypowiedzi wydzielamy z tekstu:
  * HTML: etykieta to pogrubiony akapit "<p><b>Poseł Jan Kowalski (PiS):</b>" — podział precyzyjny,
  * PDF (zapas, gdy HTML zwraca błąd): linia zakończona dwukropkiem, wyglądająca jak etykieta — podział heurystyczny.
"""
import html
import logging
import re
import subprocess

from .text import html_to_text

log = logging.getLogger("amc.komisje")

ETYKIETA_HTML = re.compile(r"<p[^>]*>\s*<b>([^<]{3,250}?):\s*</b>", re.I)
# etykieta w PDF: krótka linia od wielkiej litery zakończona dwukropkiem, z funkcją typową dla zapisów komisji
ETYKIETA_PDF = re.compile(
    r"^((?:Przewodnicząc\w*|Zastępca|Poseł|Posłanka|Senator\w*|Minister|Wiceminister|Podsekretarz|Sekretarz|Prezes|"
    r"Wiceprezes|Dyrektor|Zastępca|Naczelnik|Główn\w+|Rzecznik|Legislator|Ekspert|Przedstawiciel\w*|Członek|Kierownik|"
    r"Doradca|Pełnomocnik|Prokurator|Radca|Konsultant|Członkini|Specjalist\w+|Starszy|Wojewoda|Burmistrz|Prezydent|"
    r"Wójt|Marszałek|Komendant|Inspektor|Pani|Pan)\b[^\n:]{2,200}):\s*$", re.M)
STOPKA_PDF = re.compile(r"^\s*(Pełny zapis przebiegu posiedzenia.*|Komisji .*\(nr \d+\)|\d+|M\.P\.\s*\d*)\s*$", re.M)


def split_html(h):
    """[(etykieta, tekst)] z zapisu HTML. Wstęp przed pierwszą etykietą (porządek obrad, lista obecnych) pomijamy."""
    h = h[h.find('class="transcript"'):] if 'class="transcript"' in h else h
    parts = ETYKIETA_HTML.split(h)
    return [(re.sub(r"\s+", " ", html.unescape(parts[i])).strip(), html_to_text(parts[i + 1]))
            for i in range(1, len(parts) - 1, 2)]


def split_pdf(path):
    """[(etykieta, tekst)] z zapisu PDF (przez pdftotext); pusta lista, gdy pdftotext zawiedzie."""
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
