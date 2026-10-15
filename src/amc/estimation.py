"""Hypothesis test from the gold standard (measurement plan, variant B: the model runs on all statements).

Strata = group x model label: 1 topical and contradicting, 2 topical not contradicting, 3 not topical. The gold sample
is drawn within strata with weight w_h = N_h / n_h. Step 5: weighted TPR / TNR / precision / F1 by group for topicality,
the verdict (statements topical by the model and by the gold) and the final label. Step 6: logistic regression of the
model label on the group among statements topical by the model, standard errors clustered by speaker. Step 7:
p_g = C_g / T_g from the gold labels, difference prawica - reszta, stratified bootstrap of the gold sample.
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

GROUPS = ["prawica", "reszta"]
STRATA = {1: "tematyczna i sprzeczna", 2: "tematyczna i niesprzeczna", 3: "nietematyczna"}
SIZES = {1: 20, 2: 15, 3: 15}
MIN_TOPICAL, MIN_CONTRADICTING = 100, 30


def stratum(labels):
    """Model stratum of each statement from the label_statements columns `klimat` and `sprzeczna`."""
    if labels.loc[labels["klimat"] == 1, "sprzeczna"].isna().any():
        raise ValueError("some statements with klimat = 1 have no label yet: finish the pipeline first")
    return np.where(labels["klimat"] == 0, 3, np.where(labels["sprzeczna"] == 1, 1, 2))


def strata_sizes(labels):
    """N_h: statements per group x stratum."""
    return labels.assign(warstwa=stratum(labels)).groupby(["grupa", "warstwa"]).size().rename("N_h").reset_index()


def draw(labels, sizes=SIZES, seed=0):
    """Gold sample: n_h statements per group x stratum without replacement (the whole stratum if N_h < n_h), with
    N_h, n_h and weight N_h / n_h."""
    d = labels.assign(warstwa=stratum(labels))
    parts = [cell.sample(min(sizes[h], len(cell)), random_state=seed).assign(N_h=len(cell))
             for (_, h), cell in d.groupby(["grupa", "warstwa"])]
    out = pd.concat(parts)
    out["n_h"] = out.groupby(["grupa", "warstwa"])["wypowiedz_id"].transform("size")
    out["waga"] = out["N_h"] / out["n_h"]
    out["ziarno"] = seed
    return out.reset_index(drop=True)


def rarity(labels):
    """Supplement, source of error 3: every group has >= 100 statements topical by the model and both groups together
    >= 30 contradicting ones; otherwise the result is inconclusive for lack of data."""
    t = labels[labels["klimat"] == 1]
    topical = t.groupby("grupa").size().reindex(GROUPS, fill_value=0)
    contradicting = int((t["sprzeczna"] == 1).sum())
    ok = bool((topical >= MIN_TOPICAL).all() and contradicting >= MIN_CONTRADICTING)
    return {**{f"tematyczne_{g}": int(n) for g, n in topical.items()}, "sprzeczne_razem": contradicting,
            "warunek_spelniony": ok}


def raw_shares(labels):
    """Uncorrected shares: contradicting among topical by the model, by group."""
    t = labels[labels["klimat"] == 1].groupby("grupa")["sprzeczna"].agg(["size", "sum", "mean"])
    return t.reindex(GROUPS).rename(columns={"size": "tematyczne", "sum": "sprzeczne", "mean": "odsetek"})


def regression(labels):
    """Step 6 (and step 8 on subsets): logit of the model label `sprzeczna` on prawica among statements topical by the
    model, standard errors clustered by `member_id`; one-sided p for beta1 > 0. Without contradicting statements in
    one of the groups the estimate does not exist (separation) and only the counts are returned."""
    d = labels[labels["klimat"] == 1].dropna(subset=["sprzeczna"])
    y, x = d["sprzeczna"].astype(float), (d["grupa"] == "prawica").astype(float).rename("prawica")
    out = {"n": len(d), "mowcy": d["member_id"].nunique(), "sprzeczne": int(y.sum())}
    by_group = y.groupby(x).agg(["sum", "size"])
    if len(by_group) < 2 or ((by_group["sum"] == 0) | (by_group["sum"] == by_group["size"])).any():
        return {**out, "beta1": np.nan, "se": np.nan, "p_jednostronne": np.nan, "uwaga": "separacja"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = sm.Logit(y, sm.add_constant(x)).fit(disp=0, cov_type="cluster", cov_kwds={"groups": d["member_id"]})
    b, p = fit.params["prawica"], fit.pvalues["prawica"]
    return {**out, "beta1": b, "se": fit.bse["prawica"], "p_jednostronne": p / 2 if b > 0 else 1 - p / 2, "uwaga": ""}


def arrays(gold):
    """Gold sample as numpy arrays: model labels from the stratum, gold `t` (topical) and `s` (topical and
    contradicting)."""
    t = gold["tematyczna"].astype(int).to_numpy()
    out = {"grupa": gold["grupa"].to_numpy(), "warstwa": gold["warstwa"].to_numpy(),
           "w": gold["waga"].to_numpy(float), "mt": (gold["warstwa"] != 3).to_numpy(int),
           "ms": (gold["warstwa"] == 1).to_numpy(int), "t": t, "s": t * gold["sprzeczna"].fillna(0).astype(int).to_numpy()}
    if "werdykt_modelu" in gold and gold["werdykt_modelu"].notna().all():
        out["mv"] = gold["werdykt_modelu"].astype(int).to_numpy()
    return out


def sample_verdicts(gold, verdict_any):
    """Model verdict for every statement of the gold sample: the full-run label in strata 1-2 and, in stratum 3,
    `verdict_any` (wypowiedz_id -> 0/1 from claims and verdicts run on the sample whatever the topicality)."""
    return np.where(gold["warstwa"] == 3, gold["wypowiedz_id"].map(verdict_any), (gold["warstwa"] == 1).astype(float))


def composition(gold):
    """Per group x stratum: N_h, n_h, weight and the gold counts of topical and contradicting statements."""
    a = arrays(gold)
    return (gold.assign(tematyczne=a["t"], sprzeczne=a["s"]).groupby(["grupa", "warstwa"])
            .agg(N_h=("N_h", "first"), n_h=("n_h", "first"), waga=("waga", "first"), tematyczne=("tematyczne", "sum"),
                 sprzeczne=("sprzeczne", "sum")).reset_index())


def proportions(a):
    """Step 7: p_g = sum w * s / sum w * t in each group and the difference prawica - reszta."""
    out = {}
    for g in GROUPS:
        m = a["grupa"] == g
        topical = (a["w"][m] * a["t"][m]).sum()
        out[f"p_{g}"] = (a["w"][m] * a["s"][m]).sum() / topical if topical else np.nan
    out["roznica"] = out["p_prawica"] - out["p_reszta"]
    return out


def rates(model, gold, w):
    tp, fp = w[(model == 1) & (gold == 1)].sum(), w[(model == 1) & (gold == 0)].sum()
    fn, tn = w[(model == 0) & (gold == 1)].sum(), w[(model == 0) & (gold == 0)].sum()
    ratio = lambda a, b: a / (a + b) if a + b else np.nan
    tpr, prec = ratio(tp, fn), ratio(tp, fp)
    return {"TPR": tpr, "TNR": ratio(tn, fp), "precyzja": prec,
            "F1": 2 * prec * tpr / (prec + tpr) if prec + tpr else np.nan}


def quality(a):
    """Step 5: weighted rates by group for topicality, the verdict on statements topical by the model and the gold, the
    final label and, when the model verdict exists for the whole sample, the verdict on all statements topical by the
    gold (`werdykt_bez_filtra`)."""
    out = {}
    for g in GROUPS:
        m = a["grupa"] == g
        stages = {"tematycznosc": (a["mt"], a["t"], m), "werdykt": (a["ms"], a["s"], m & (a["mt"] == 1) & (a["t"] == 1)),
                  "etykieta": (a["ms"], a["s"], m)}
        if "mv" in a:
            stages["werdykt_bez_filtra"] = (a["mv"], a["s"], m & (a["t"] == 1))
        for stage, (model, truth, rows) in stages.items():
            out.update({f"{g}_{stage}_{k}": v for k, v in rates(model[rows], truth[rows], a["w"][rows]).items()})
    return out


def bootstrap(gold, stat, reps=10_000, seed=2026):
    """`stat` on `reps` stratified resamples of the gold sample (with replacement within group x stratum, weights
    fixed)."""
    a = arrays(gold)
    cells = [np.flatnonzero((a["grupa"] == g) & (a["warstwa"] == h)) for g, h in set(zip(a["grupa"], a["warstwa"]))]
    cells.sort(key=lambda c: c[0])
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(reps):
        idx = np.concatenate([c[rng.integers(0, len(c), len(c))] for c in cells])
        rows.append(stat({k: v[idx] for k, v in a.items()}))
    return pd.DataFrame(rows)


def summarize(gold, stat, reps=10_000, seed=2026):
    """Point estimate, one-sided 95% lower bound (5th percentile), two-sided 95% interval and the number of resamples
    where the statistic is undefined."""
    boot = bootstrap(gold, stat, reps, seed)
    return pd.DataFrame({"wartosc": pd.Series(stat(arrays(gold))), "dolna_95_jednostronna": boot.quantile(0.05),
                         "przedzial_2.5": boot.quantile(0.025), "przedzial_97.5": boot.quantile(0.975),
                         "bootstrap_brak": boot.isna().sum()})
