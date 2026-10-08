"""Loading and summarising stage A (LLM) results: statements, candidates, claims, weighted estimates, error checks."""
import json

import numpy as np
import pandas as pd

from . import corpus, llm, sampling
from .paths import PROCESSED

META = ["wypowiedz_id", "kadencja", "data", "rola", "blok", "liczba_slow", "tekst", *sampling.HIT_COLS]
STATEMENT_COLS = ["wypowiedz_id", "rok", "waga", "data", "okres", "zrodlo", "gremium", "blok", "rola", "mowca",
                  "liczba_slow", "przepelnienie", "przesuniecie"]


def _dedup(items):
    seen, out = set(), []
    for c in items:
        if c["cytat"] not in seen:
            seen.add(c["cytat"])
            out.append(c)
    return out


def _meta(kind):
    c = corpus.load(kind)
    if kind == "komisje":
        c = c.rename(columns={"etykieta": "mowca"}).assign(gremium=c["komisja"])
    else:
        c = c.assign(gremium="plenarne")
    return c[[*META, "mowca", "gremium"]].assign(zrodlo=kind)


def load(prompt="etap_a_v2", source="rok", n=60, keep="last", suffix=""):
    """One row per sampled statement: ids and weights from the sample file, one result line per id, corpus metadata.

    keep="last" gives the current result, keep="first" the result of the first run (before reruns and re-verification).
    suffix="_powtorka" reads the test-retest run instead (only statements it contains).
    Duplicate quotes within a statement are dropped. `zrodlo` is plenarne/komisje, `gremium` is plenarne or the committee.
    `przepelnienie` / `przesuniecie`: context overflow flags, see `llm.overflow`.
    """
    sample = pd.read_csv(PROCESSED / f"llm_{prompt}_{source}_n{n}_proba.csv")
    lines = [{**llm.LEGACY_SETTINGS, **json.loads(x)}
             for x in (PROCESSED / f"llm_{prompt}_{source}{suffix}.jsonl").open(encoding="utf-8")]
    res = pd.DataFrame(lines).drop_duplicates("wypowiedz_id", keep=keep).drop(columns=["rok", "waga"], errors="ignore")
    if suffix:
        sample = sample[sample["wypowiedz_id"].isin(res["wypowiedz_id"])]
    meta = pd.concat([_meta(k) for k in corpus.RODZAJE], ignore_index=True)
    df = (sample.merge(res, on="wypowiedz_id", how="left", validate="1:1")
          .merge(meta, on="wypowiedz_id", how="left", validate="1:1"))
    df["data"] = pd.to_datetime(df["data"])
    df["okres"] = sampling.period(df["data"])
    for col in ["kandydaci", "twierdzenia"]:
        df[col] = df[col].apply(_dedup)
    df["n_kandydatow"] = df["kandydaci"].str.len()
    df["n_twierdzen"] = df["twierdzenia"].str.len()
    df["y"] = (df["n_twierdzen"] > 0).astype(int)
    flag = [llm.overflow(a, b, c) for a, b, c in zip(df["tokeny_we"], df["tokeny_wy"], df["num_ctx"])]
    df["przepelnienie"] = [f == "przepelnienie" for f in flag]
    df["przesuniecie"] = [f == "przesuniecie" for f in flag]
    return df


def candidates(df):
    """One row per candidate sentence (`rodzaj` = kind of sentence), with statement metadata."""
    return pd.DataFrame([{**c, **{k: r[k] for k in STATEMENT_COLS}}
                         for r in df[STATEMENT_COLS + ["kandydaci"]].to_dict("records") for c in r["kandydaci"]])


def claims(df):
    """Confirmed claims: candidates labelled `naukowe` in step 1 and confirmed in step 2."""
    k = candidates(df)
    return k[k["rodzaj"].eq("naukowe") & k["weryfikacja"].eq(True)].reset_index(drop=True)


def topic_flags(df, cl, topics):
    """Statement x topic table of 0/1: the statement has >= 1 claim with that topic."""
    hit = pd.crosstab(cl["wypowiedz_id"], cl["temat"]).gt(0)
    return hit.reindex(index=df["wypowiedz_id"], columns=topics, fill_value=False).astype(int).set_axis(df.index)


def weighted_share(df, by, y="y", w="waga"):
    s = df.assign(_wy=df[y] * df[w]).groupby(by)[["_wy", w]].sum()
    return s["_wy"] / s[w]


def weighted_total(df, by, y="y", w="waga"):
    """Horvitz-Thompson estimate of the population total of `y` per group."""
    return df.assign(_wy=df[y] * df[w]).groupby(by)["_wy"].sum()


def bootstrap(df, by, y="y", w="waga", strata="rok", reps=2000, seed=0):
    """Weighted mean of `y` per group with percentile 95% CI; statements resampled within year strata."""
    rng = np.random.default_rng(seed)
    groups = [g.index.to_numpy() for _, g in df.groupby(strata)]
    est = pd.concat([weighted_share(df.loc[np.concatenate([rng.choice(g, len(g)) for g in groups])], by, y, w)
                     for _ in range(reps)], axis=1)
    return pd.DataFrame({"n": df.groupby(by).size(), "p": weighted_share(df, by, y, w),
                         "lo": est.quantile(0.025, axis=1), "hi": est.quantile(0.975, axis=1)})


def bootstrap_diff(df, by, a, b, y="y", w="waga", strata="rok", reps=2000, seed=0):
    """Difference of weighted means (group b minus group a) with percentile 95% CI."""
    rng = np.random.default_rng(seed)
    groups = [g.index.to_numpy() for _, g in df.groupby(strata)]
    diffs = []
    for _ in range(reps):
        s = weighted_share(df.loc[np.concatenate([rng.choice(g, len(g)) for g in groups])], by, y, w)
        diffs.append(s[b] - s[a])
    s = weighted_share(df, by, y, w)
    return s[b] - s[a], np.quantile(diffs, 0.025), np.quantile(diffs, 0.975)


def cohen_kappa(a, b):
    """Cohen's kappa for two binary ratings of the same items."""
    a, b = np.asarray(a, dtype=int), np.asarray(b, dtype=int)
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
