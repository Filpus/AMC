"""AR6 knowledge base for the verdict step: SPM and TS of WGI-WGIII, split into fragments.

IPCC findings are numbered (A.1.8, TS.C.4.2) and end with a reference list in braces ({2.3, TS.2.6}); a fragment is one
finding where the layout allows it, otherwise up to ~250 words under the last numbered heading. Figure labels and table
cells (short lines) are dropped. Retrieval: bge-m3 embeddings served by Ollama plus BM25 on the English text, merged by
reciprocal rank fusion. The PDFs and the index stay outside the repository (IPCC copyright: data/ar6/ in .gitignore).
"""
import math
import re
from collections import Counter

import numpy as np
import pandas as pd
import requests

from .paths import ROOT

DIR = ROOT / "data" / "ar6"
PDF_DIR = DIR / "pdf"
FRAGMENTS = DIR / "fragments.parquet"
EMBED_MODEL = "bge-m3"
OLLAMA_EMBED = "http://127.0.0.1:11434/api/embed"
_BASE = "https://www.ipcc.ch/report/ar6/"
SOURCES = [
    ("WGI", "SPM", _BASE + "wg1/downloads/report/IPCC_AR6_WGI_SPM.pdf"),
    ("WGI", "TS", _BASE + "wg1/downloads/report/IPCC_AR6_WGI_TS.pdf"),
    ("WGII", "SPM", _BASE + "wg2/downloads/report/IPCC_AR6_WGII_SummaryForPolicymakers.pdf"),
    ("WGII", "TS", _BASE + "wg2/downloads/report/IPCC_AR6_WGII_TechnicalSummary.pdf"),
    ("WGIII", "SPM", _BASE + "wg3/downloads/report/IPCC_AR6_WGIII_SummaryForPolicymakers.pdf"),
    ("WGIII", "TS", _BASE + "wg3/downloads/report/IPCC_AR6_WGIII_TechnicalSummary.pdf"),
]
FINDING = re.compile(r"^\s*((?:TS\.)?[A-F](?:\.\d+){1,3}|TS\.[A-F](?:\.\d+){0,3}|TS\.\d+(?:\.\d+){0,3})\s+(?=\S)")
HEADER = re.compile(r"^\s*(\d{1,4}|SPM|TS|Summary for Policymakers|Technical Summary|This pre-final-publication version.*)\s*$")
MAX_WORDS, MIN_WORDS, MIN_LINE_CHARS = 250, 20, 35


def pdf_path(url):
    return PDF_DIR / url.rsplit("/", 1)[1]


def download():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    for _, _, url in SOURCES:
        path = pdf_path(url)
        if not path.exists():
            r = requests.get(url, timeout=300)
            r.raise_for_status()
            path.write_bytes(r.content)


def split_pages(pages, report, part):
    """Fragments from the text of consecutive pages: [{raport, czesc, numer, strona, tekst}], strona counted from 1."""
    out, buf, numer, start = [], [], "", 1

    def flush():
        lines = [x for x, _ in buf]
        words = " ".join(lines).split()
        if len(words) >= MIN_WORDS and np.mean([len(x) for x in lines]) >= MIN_LINE_CHARS:
            size = math.ceil(len(words) / math.ceil(len(words) / MAX_WORDS))
            for k in range(0, len(words), size):
                out.append({"raport": report, "czesc": part, "numer": numer, "strona": start,
                            "tekst": " ".join(words[k:k + size])})
        buf.clear()

    for page_no, text in enumerate(pages, 1):
        for line in text.split("\n"):
            if not line.strip() or HEADER.match(line):
                continue
            m = FINDING.match(line)
            if m or (len(" ".join(x for x, _ in buf).split()) >= MAX_WORDS and line.rstrip().endswith(".")):
                flush()
                numer = m.group(1) if m else numer
            if not buf:
                start = page_no
            buf.append((line.strip(), page_no))
            if line.rstrip().endswith("}"):
                flush()
    flush()
    return out


def build():
    """Parses the downloaded PDFs into data/ar6/fragments.parquet; returns the fragments."""
    import pypdf

    rows = []
    for report, part, url in SOURCES:
        reader = pypdf.PdfReader(pdf_path(url))
        rows += split_pages([p.extract_text() or "" for p in reader.pages], report, part)
    df = pd.DataFrame(rows)
    df.insert(0, "fragment_id", [f"{r}_{c}_{i}" for i, (r, c) in enumerate(zip(df["raport"], df["czesc"]))])
    df["etykieta"] = [f"{r} {c} {n} (s. {s})".replace("  ", " ") for r, c, n, s in
                      zip(df["raport"], df["czesc"], df["numer"], df["strona"])]
    DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(FRAGMENTS, index=False)
    return df


def embed(texts, model=EMBED_MODEL, batch=32):
    """L2-normalised embeddings from Ollama."""
    vecs = []
    for i in range(0, len(texts), batch):
        r = requests.post(OLLAMA_EMBED, json={"model": model, "input": list(texts[i:i + batch])}, timeout=600)
        r.raise_for_status()
        vecs += r.json()["embeddings"]
    v = np.asarray(vecs, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def embeddings_path(model=EMBED_MODEL):
    return DIR / f"embeddings_{model.replace(':', '_')}.npy"


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [Counter(tokens(d)) for d in docs]
        self.len = np.array([sum(d.values()) for d in self.docs], dtype=float)
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b, self.avg = k1, b, self.len.mean()

    def scores(self, query):
        s = np.zeros(len(self.docs))
        norm = self.k1 * (1 - self.b + self.b * self.len / self.avg)
        for t in set(tokens(query)):
            if t in self.idf:
                tf = np.array([d.get(t, 0) for d in self.docs], dtype=float)
                s += self.idf[t] * tf * (self.k1 + 1) / (tf + norm)
        return s


def rrf(rankings, k=60):
    """Reciprocal rank fusion of several rankings (lists of indices, best first)."""
    score = Counter()
    for ranking in rankings:
        for r, i in enumerate(ranking):
            score[i] += 1 / (k + r + 1)
    return [i for i, _ in score.most_common()]


class Index:
    """Fragments with their embeddings. `search` ranks by dense similarity of both texts and BM25 on the English one,
    and takes the best `per_part` fragments from the SPMs and from the TSs (codebook: SPM first, then TS)."""

    def __init__(self, fragments=None, vectors=None, model=EMBED_MODEL):
        self.df = pd.read_parquet(FRAGMENTS) if fragments is None else fragments.reset_index(drop=True)
        self.vec = np.load(embeddings_path(model)) if vectors is None else vectors
        self.model = model
        self.bm25 = BM25(self.df["tekst"].tolist())

    def search(self, query_pl, query_en="", per_part=3, pool=50, query_vectors=None):
        queries = [q for q in (query_pl, query_en) if q]
        qv = embed(queries, self.model) if query_vectors is None else query_vectors
        rankings = [list(np.argsort(-(self.vec @ v))[:pool]) for v in qv]
        if query_en:
            rankings.append(list(np.argsort(-self.bm25.scores(query_en))[:pool]))
        ranked = self.df.iloc[rrf(rankings)]
        return pd.concat([ranked[ranked["czesc"] == part].head(per_part) for part in ("SPM", "TS")])
