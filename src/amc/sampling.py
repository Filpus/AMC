"""Stratified sample of statements for manual annotation (gold standard).

Cells = year x stratum:
  filtr  >= 1 hit of any topic dictionary, `nauka` or `sceptycyzm` (what the LLM will see)
  poza   no hit (measures what the regex prefilter loses)
Weight = N / n of the cell (inverse inclusion probability).
Rows are ordered so that every prefix of the file is itself a proportional stratified sample (column `kolejnosc`),
so annotation can be done in batches; weights for a prefix are recomputed from the annotated rows.
`okres` (przed_covid / covid / po_chatgpt) is added for pooling years in the analysis.
"""
import numpy as np
import pandas as pd

from . import topics

PERIOD_BREAKS = (pd.Timestamp("2020-01-24"), pd.Timestamp("2022-11-30"))
PERIODS = ("przed_covid", "covid", "po_chatgpt")
# hypothesis windows from the exploration card supplement (both ends inclusive)
WINDOWS = {"A": (pd.Timestamp("2022-04-17"), pd.Timestamp("2023-07-16")),
           "B": (pd.Timestamp("2023-11-13"), pd.Timestamp("2025-02-17"))}
DEFAULT_SIZES = {"filtr": 20, "poza": 10}

ANNOTATION_COLS = ["tematy", "zawiera_twierdzenie", "uwagi"]
CLAIM_COLS = ["wypowiedz_id", "nr", "twierdzenie", "atrybucja", "werdykt", "zrodla", "uwagi"]
HIT_COLS = [*topics.TOPICS, "nauka", "sceptycyzm"]


def prefilter(df):
    return df[HIT_COLS].gt(0).any(axis=1)


def period(dates):
    d = pd.to_datetime(dates)
    return pd.Series(np.select([d < PERIOD_BREAKS[0], d < PERIOD_BREAKS[1]], PERIODS[:2], PERIODS[2]), index=d.index)


def window(dates):
    """Window label (A / B), missing outside both windows."""
    d = pd.to_datetime(dates)
    out = pd.Series(np.nan, index=d.index, dtype=object)
    for k, (a, b) in WINDOWS.items():
        out[d.between(a, b)] = k
    return out


def draw(df, sizes=None, seed=0):
    """Returns (sample, design). Only `merytoryczna` statements; a cell smaller than its size is taken whole."""
    sizes = sizes or DEFAULT_SIZES
    pop = df[df["merytoryczna"]].copy()
    pop["warstwa"] = np.where(prefilter(pop), "filtr", "poza")
    pop["rok"] = pd.to_datetime(pop["data"]).dt.year
    rng = np.random.default_rng(seed)
    parts, design = [], []
    for year in sorted(pop["rok"].unique()):
        for stratum, n in sizes.items():
            cell = pop[(pop["rok"] == year) & (pop["warstwa"] == stratum)]
            k = min(n, len(cell))
            if k:
                part = cell.sample(n=k, random_state=rng)
                part["_key"] = (np.arange(k) + rng.uniform(size=k)) / k
                parts.append(part)
            design.append({"rok": year, "warstwa": stratum, "N": len(cell), "n": k, "waga": len(cell) / k if k else np.nan})
    design = pd.DataFrame(design)
    sample = pd.concat(parts).merge(design[["rok", "warstwa", "waga"]], on=["rok", "warstwa"])
    sample["okres"] = period(sample["data"]).to_numpy()
    sample = sample.sort_values("_key").drop(columns="_key").reset_index(drop=True)
    sample.insert(0, "kolejnosc", np.arange(1, len(sample) + 1))
    return sample, design


def topic_hits(row):
    return ", ".join(f"{c}={row[c]}" for c in HIT_COLS if row[c] > 0)
