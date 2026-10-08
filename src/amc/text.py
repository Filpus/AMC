"""Tekst wypowiedzi: konwersja HTML -> tekst, czyszczenie, fragmenty z kontekstem."""
import bisect
import difflib
import html
import re

# nagłówek stenogramu plenarnego z tytułem punktu porządku i drukiem — usuwany już przy budowie tabeli z API
HEADER_PLENARNY = re.compile(r"^.*?punkt porządku dziennego:.*?\(druk[^)]*\)\.?\s*", re.S)
# wtrącenia z sali i didaskalia w nawiasach: "(Oklaski)", "(Poseł X: Nie kłam!)", "(Głos z sali: ...)"
WTRACENIE = re.compile(r"\([^()]*\)")
# stopka stenogramu plenarnego
STOPKA = re.compile(r"\s*Przebieg posiedzenia\s*$")


def html_to_text(h):
    """HTML -> tekst z zachowaniem podziału na akapity."""
    if not h:
        return ""
    t = re.sub(r"<(br|/p|p|/div|/h\d)[^>]*>", "\n", h, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\s*\n\s*", "\n", t).strip()


def clean_statement(tekst, mowca=None):
    """Tekst wypowiedzi bez elementów, które nie są słowami mówcy.

    * nagłówek stenogramu — wszystko do linii z etykietą mówcy ("Poseł Jan Kowalski:") włącznie; w pierwszej
      wypowiedzi punktu obrad zawiera tytuł punktu, który inaczej dawałby fałszywe trafienia tematyczne,
    * wtrącenia z sali w nawiasach (słowa innych osób),
    * stopka "Przebieg posiedzenia".
    Dla zapisów komisji (bez nagłówka) wystarczy mowca=None.
    """
    if not isinstance(tekst, str):
        return ""
    if mowca:
        mm = re.search(rf"^[^\n]*{re.escape(mowca)}:[ \t]*$", tekst, flags=re.M)
        if mm:
            tekst = tekst[mm.end():]
    tekst = STOPKA.sub("", WTRACENIE.sub(" ", tekst))
    return re.sub(r"[ \t]+", " ", tekst).strip()


def word_count(texts):
    """Liczba słów dla serii tekstów (pandas.Series)."""
    return texts.fillna("").str.split().str.len().fillna(0).astype(int)


def kwic(text, rx, w=150):
    """Fragment ±w znaków wokół pierwszego dopasowania rx (wyszukiwanie bez rozróżniania wielkości liter),
    z dopasowaniem pogrubionym w Markdown. Pusty napis, gdy brak dopasowania."""
    mm = rx.search(text.lower())
    if not mm:
        return ""
    s, e = max(0, mm.start() - w), min(len(text), mm.end() + w)
    return (("…" if s else "") + text[s:mm.start()] + "**" + text[mm.start():mm.end()] + "**"
            + text[mm.end():e] + ("…" if e < len(text) else ""))


def highlight_segments(text, rx, window=220, merge=440, max_groups=3):
    """Fragmenty tekstu wokół wszystkich dopasowań rx, gotowe do wyróżnienia.

    Bliskie dopasowania (odstęp < merge znaków) łączymy w jeden fragment, żeby tekst się nie powtarzał.
    Zwraca listę fragmentów; fragment to lista [kawałek_tekstu, czy_wyróżnić] (0/1).
    """
    spans = [(x.start(), x.end()) for x in rx.finditer(text.lower())]
    groups = []
    for s, e in spans:
        if groups and s - groups[-1][-1][1] < merge:
            groups[-1].append((s, e))
        else:
            groups.append([(s, e)])
    frags = []
    for g in groups[:max_groups]:
        a, b = max(0, g[0][0] - window), min(len(text), g[-1][1] + window)
        seg, pos = [["…" if a else "", 0]], a
        for s, e in g:
            seg += [[text[pos:s], 0], [text[s:e], 1]]
            pos = e
        seg.append([text[pos:b] + ("…" if b < len(text) else ""), 0])
        frags.append(seg)
    return frags


SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def normalize(text):
    """Małe litery, bez interpunkcji, pojedyncze spacje (do porównywania cytatów z tekstem)."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def _locate(q, t):
    """(początek, długość) cytatu q w tekście t (oba znormalizowane); gdy q nie jest dosłowny, najdłuższy wspólny fragment."""
    i = t.find(q)
    if i >= 0:
        return i, len(q)
    m = difflib.SequenceMatcher(None, t, q, autojunk=False).find_longest_match(0, len(t), 0, len(q))
    return m.a, m.size


def quote_match(quote, text):
    """Jaka część cytatu występuje w tekście jako jeden ciągły fragment (bez wielkości liter i interpunkcji); 1 = dosłowny."""
    q = normalize(quote)
    return _locate(q, normalize(text))[1] / len(q) if q else 0.0


def quote_context(text, quote, n=1, max_chars=1500):
    """Zdania wypowiedzi zawierające cytat, plus n zdań przed i po. Pusty napis, gdy cytatu nie da się odnaleźć."""
    sents = [s for s in SENTENCE_END.split(text) if s.strip()]
    norm = [normalize(s) for s in sents]
    starts = [0]
    for s in norm[:-1]:
        starts.append(starts[-1] + len(s) + 1)
    q = normalize(quote)
    if not q:
        return ""
    pos, size = _locate(q, " ".join(norm))
    if size < min(30, len(q)):
        return ""
    first = bisect.bisect_right(starts, pos) - 1
    last = bisect.bisect_right(starts, pos + size - 1) - 1
    for k in (n, 0):
        ctx = " ".join(sents[max(0, first - k):last + k + 1])
        if len(ctx) <= max_chars:
            return ctx
    return quote
