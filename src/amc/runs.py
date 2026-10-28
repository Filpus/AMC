"""Shared plumbing of the codebook pipeline steps: result files, resuming, the population in a fixed random order."""
import hashlib
import json
import socket

import pandas as pd

from . import ar6, corpus, population
from . import text as T
from .paths import PROCESSED

HOST = socket.gethostname()
VERDICT_PROMPT = "verdict_v1"
PAPERQA_PROMPT = "paperqa_v0"


def model_slug(model):
    return model.replace("/", "_").replace(":", "_")


def out_path(step, prompt, model, suffix=""):
    """data/processed/<step>/<prompt>__<model><suffix>.jsonl"""
    return PROCESSED / step / f"{prompt}__{model_slug(model)}{suffix}.jsonl"


def add_retrieval_args(ap, frozen=False):
    """--wyszukiwanie and --embedding; `frozen` defaults them to the frozen run (rrf with bge-m3), for the analysis
    scripts tied to the gold sample drawn from its labels."""
    search, embedding = ("rrf", ar6.FROZEN_EMBED_MODEL) if frozen else (ar6.DEFAULT_SEARCH, ar6.EMBED_MODEL)
    ap.add_argument("--wyszukiwanie", choices=ar6.SEARCH, default=search,
                    help="AR6 retrieval: embedding of the English or Polish claim, BM25, or rrf (the frozen run)")
    ap.add_argument("--embedding", default=embedding, help="embedding model (Ollama) for en, pl and rrf")


def retrieval_tag(verdict_prompt, search=ar6.DEFAULT_SEARCH, embedding=ar6.EMBED_MODEL):
    """File name part of the retrieval variant: none for rrf with bge-m3 (the frozen run), else __<search>, followed by
    _<embedding model> for any model but bge-m3. PaperQA2 has its own retrieval: only __<embedding model>, none for
    bge-m3."""
    if verdict_prompt == PAPERQA_PROMPT:
        return "" if embedding == ar6.FROZEN_EMBED_MODEL else f"__{model_slug(embedding)}"
    if (search, embedding) == ("rrf", ar6.FROZEN_EMBED_MODEL):
        return ""
    return f"__{search}" + ("" if search == "bm25" or embedding == ar6.FROZEN_EMBED_MODEL
                            else f"_{model_slug(embedding)}")


def verdicts_path(verdict_prompt, model, search=ar6.DEFAULT_SEARCH, embedding=ar6.EMBED_MODEL, suffix=""):
    """data/processed/verdicts/<prompt>__<model><retrieval tag><suffix>.jsonl"""
    return out_path("verdicts", verdict_prompt, model, retrieval_tag(verdict_prompt, search, embedding) + suffix)


def labels_path(model, verdict_prompt=VERDICT_PROMPT, search=ar6.DEFAULT_SEARCH, embedding=ar6.EMBED_MODEL):
    """data/processed/labels/<model>[__<prompt>]<retrieval tag>.csv; another verdict prompt (PaperQA2: paperqa_v0)
    gets __<prompt>."""
    suffix = "" if verdict_prompt == VERDICT_PROMPT else f"__{verdict_prompt}"
    return PROCESSED / "labels" / f"{model_slug(model)}{suffix}{retrieval_tag(verdict_prompt, search, embedding)}.csv"


def last_lines(path, key="wypowiedz_id"):
    """Last result line per key (reruns append, so the last line is the current one)."""
    if not path.exists():
        return {}
    return {r[key]: r for r in map(json.loads, path.open(encoding="utf-8"))}


def done(path, key="wypowiedz_id"):
    return {k for k, r in last_lines(path, key).items() if not r["blad"]}


def append(f, row):
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
    f.flush()


def fingerprint(ids):
    """Short hash of the id set, to check that another machine has the same population."""
    return hashlib.sha1("\n".join(sorted(ids)).encode()).hexdigest()[:10]


def shuffled_population(seed=0, log=None):
    """Study population (amc/population.select) in a fixed random order, speaker names masked as for annotators."""
    pop = population.select(corpus.load("plenarne"))
    if log:
        log.info("population: %d statements, fingerprint %s", len(pop), fingerprint(pop["wypowiedz_id"]))
    pop = pop.sample(frac=1, random_state=seed)
    return pd.DataFrame({"wypowiedz_id": pop["wypowiedz_id"], "tekst": pop["tekst"].map(T.mask_speakers),
                         "grupa": pop["grupa"]})
