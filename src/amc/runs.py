"""Shared plumbing of the codebook pipeline steps: result files, resuming, the population in a fixed random order."""
import hashlib
import json
import socket

import pandas as pd

from . import corpus, population
from . import text as T
from .paths import PROCESSED

HOST = socket.gethostname()


def model_slug(model):
    return model.replace("/", "_").replace(":", "_")


def out_path(step, prompt, model, suffix=""):
    """data/processed/<step>/<prompt>__<model><suffix>.jsonl"""
    return PROCESSED / step / f"{prompt}__{model_slug(model)}{suffix}.jsonl"


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
