"""Gold-standard annotation: one annotator labels the whole sample (or annotators split it), optionally a second one a
subsample (Cohen's kappa).

An annotation file has `kolejnosc` (the shuffled order of the sample, so the annotator never sees wypowiedz_id, which
contains the date), `tematyczna` (0/1), `sprzeczna` (0/1 when tematyczna = 1, else empty), optionally `komentarz` and
`proba` (the sample fingerprint: a file annotated on another draw is refused). The final label is tematyczna and
sprzeczna.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from . import runs
from .llm_results import cohen_kappa

KAPPA_SIZE, KAPPA_MIN_CONTRADICTING, KAPPA_THRESHOLD = 40, 10, 0.6
VALUES = {"1": 1.0, "0": 0.0, "1.0": 1.0, "0.0": 0.0, "": np.nan}


def sample_id(design):
    return runs.fingerprint(design["wypowiedz_id"])


def _ids(rows):
    return ", ".join(f"#{k}" for k in sorted(rows)[:20]) + (" …" if len(rows) > 20 else "")


def load(path, design, required=None):
    """Annotation file checked against the sample design: kolejnosc, wypowiedz_id, tematyczna, sprzeczna (NaN when not
    topical), koncowa, komentarz. Every statement in `required` (default: the whole sample) must be labelled."""
    ann = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    ann.columns = ann.columns.str.strip()
    missing = {"kolejnosc", "tematyczna", "sprzeczna"} - set(ann.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    if "proba" in ann and set(ann["proba"].str.strip()) - {"", sample_id(design)}:
        raise ValueError(f"{path} was annotated on another gold sample (proba != {sample_id(design)})")
    ann["kolejnosc"] = ann["kolejnosc"].astype(int)
    unknown = set(ann["kolejnosc"]) - set(design["kolejnosc"])
    if unknown:
        raise ValueError(f"{path}: statements not in the sample: {_ids(unknown)}")
    for col in ("tematyczna", "sprzeczna"):
        raw = ann[col].str.strip()
        bad = ~raw.isin(VALUES)
        if bad.any():
            raise ValueError(f"{path}: {col} must be 0, 1 or empty: {_ids(ann.loc[bad, 'kolejnosc'])}")
        ann[col] = raw.map(VALUES)
    required = set(design["kolejnosc"]) if required is None else set(required)
    labelled = set(ann.loc[ann["tematyczna"].notna(), "kolejnosc"])
    if required - labelled:
        raise ValueError(f"{path}: {len(required - labelled)} statements without `tematyczna`: {_ids(required - labelled)}")
    no_s = ann["tematyczna"].eq(1) & ann["sprzeczna"].isna()
    if no_s.any():
        raise ValueError(f"{path}: topical statements without `sprzeczna`: {_ids(ann.loc[no_s, 'kolejnosc'])}")
    s_not_t = ann["tematyczna"].eq(0) & ann["sprzeczna"].eq(1)
    if s_not_t.any():
        raise ValueError(f"{path}: `sprzeczna` = 1 in statements that are not topical: {_ids(ann.loc[s_not_t, 'kolejnosc'])}")
    ann.loc[ann["tematyczna"].eq(0), "sprzeczna"] = np.nan
    ann = ann[ann["tematyczna"].notna()].copy()
    ann["koncowa"] = ann["tematyczna"] * ann["sprzeczna"].fillna(0)
    if "komentarz" not in ann:
        ann["komentarz"] = ""
    return design[["kolejnosc", "wypowiedz_id"]].merge(
        ann[["kolejnosc", "tematyczna", "sprzeczna", "koncowa", "komentarz"]], on="kolejnosc")


def labelled(path, design):
    """kolejnosc of the statements labelled in an annotation file (complete or not)."""
    return set(load(path, design, required=())["kolejnosc"])


def load_parts(paths, design):
    """Annotation files of annotators who split the sample: together they label every statement exactly once. Adds
    `anotator` (the initials from annotations_<initials>.csv)."""
    if len(paths) == 1:
        return load(paths[0], design).assign(anotator=_initials(paths[0]))
    parts = [load(p, design, required=()).assign(anotator=_initials(p)) for p in paths]
    ann = pd.concat(parts, ignore_index=True)
    twice = ann.loc[ann["kolejnosc"].duplicated(), "kolejnosc"]
    if len(twice):
        raise ValueError(f"statements labelled in more than one file: {_ids(set(twice))}")
    missing = set(design["kolejnosc"]) - set(ann["kolejnosc"])
    if missing:
        raise ValueError(f"{len(missing)} statements labelled in none of the files: {_ids(missing)}")
    return ann.sort_values("kolejnosc").reset_index(drop=True)


def _initials(path):
    return Path(path).stem.removeprefix("annotations_")


def kappa_subsample(ann1, size=KAPPA_SIZE, min_contradicting=KAPPA_MIN_CONTRADICTING, seed=0):
    """Subsample for the second annotator: `size` statements of the sample at random, topped up with statements the
    first annotator labelled contradicting until there are `min_contradicting`; shuffled, so the top-up is not at the
    end. Returns (kolejnosc list in display order, number topped up)."""
    rng = np.random.default_rng(seed)
    pick = ann1.sample(n=min(size, len(ann1)), random_state=rng)
    rest = ann1[~ann1["kolejnosc"].isin(pick["kolejnosc"]) & ann1["koncowa"].eq(1)]
    need = min(max(min_contradicting - int(pick["koncowa"].sum()), 0), len(rest))
    if need:
        pick = pd.concat([pick, rest.sample(n=need, random_state=rng)])
    return pick.sample(frac=1, random_state=rng)["kolejnosc"].tolist(), need


def agreement(ann1, ann2):
    """Agreement on the statements of `ann2` (before disagreements are discussed): per label n, share of agreement and
    Cohen's kappa; and the disagreeing statements."""
    d = ann2.merge(ann1, on=["kolejnosc", "wypowiedz_id"], suffixes=("_2", "_1"))
    table = pd.DataFrame([{"etykieta": label, "n": len(d), "zgodnosc": float((d[f"{col}_1"] == d[f"{col}_2"]).mean()),
                           "kappa": cohen_kappa(d[f"{col}_1"], d[f"{col}_2"])}
                          for label, col in (("tematyczna", "tematyczna"), ("koncowa (tematyczna i sprzeczna)", "koncowa"))])
    diff = d[(d["tematyczna_1"] != d["tematyczna_2"]) | (d["koncowa_1"] != d["koncowa_2"])]
    cols = ["kolejnosc", "tematyczna_1", "koncowa_1", "komentarz_1", "tematyczna_2", "koncowa_2", "komentarz_2"]
    labels = ["tematyczna_1", "koncowa_1", "tematyczna_2", "koncowa_2"]
    return table, diff[cols].astype({c: int for c in labels}).sort_values("kolejnosc").reset_index(drop=True)
