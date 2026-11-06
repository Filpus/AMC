"""Steps 6-8 side by side for the candidate main results: frozen run (v1 prompts) vs the run on the current codebook
(topic_v1 / claims_v2 / verdict_v2), and the frozen right (PiS, RozwojPlus, Konfederacja, Konfederacja_KP) vs the
right with Kukiz15 and Republikanie.

Step 7 (gold estimate) does not depend on the pipeline run: model labels only defined the strata the gold sample was
drawn from, so the design weights stay. Changing the right only moves gold statements between groups (Horvitz-Thompson
with the original weights; the bootstrap still resamples within the original group x stratum cells).

Step 6 / 8 (model labels) are recomputed here without statsmodels: logit with one binary regressor fitted by
Newton-Raphson, SE clustered by speaker with the statsmodels small-sample correction (G/(G-1) * (N-1)/(N-K)).

Output: data/processed/results/compare_runs.csv, compare_runs_gold.csv; printed summary.

  python src/compare_runs.py
"""
import numpy as np
import pandas as pd

from amc.paths import PROCESSED

OUT = PROCESSED / "results"
LABELS = {"v1 (zamrożony)": "gemma4_12b.csv", "v2 (obecny codebook)": "gemma4_12b__verdict_v2__en_embeddinggemma_300m.csv"}
FROZEN_RIGHT = ("PiS", "RozwojPlus", "Konfederacja", "Konfederacja_KP")
BROAD_RIGHT = FROZEN_RIGHT + ("Kukiz15", "Republikanie")
RIGHTS = {"prawica zamrożona": FROZEN_RIGHT, "prawica + Kukiz15 i Republikanie": BROAD_RIGHT}
KONF, PIS = ("Konfederacja", "Konfederacja_KP"), ("PiS", "RozwojPlus")
MIDPOINT = pd.Timestamp("2025-04-14")
CORRECTED = 94
SEED = 2026


def logit_cluster(y, x, groups):
    """beta1, clustered SE and one-sided p for logit(y) = b0 + b1 x."""
    X = np.column_stack([np.ones_like(x, dtype=float), x.astype(float)])
    b = np.zeros(2)
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ b))
        H = X.T @ (X * (p * (1 - p))[:, None])
        step = np.linalg.solve(H, X.T @ (y - p))
        b += step
        if np.abs(step).max() < 1e-10:
            break
    p = 1 / (1 + np.exp(-X @ b))
    Hinv = np.linalg.inv(X.T @ (X * (p * (1 - p))[:, None]))
    score = X * (y - p)[:, None]
    S = pd.DataFrame(score).groupby(np.asarray(groups)).sum().to_numpy()
    G, N, K = len(S), len(y), 2
    V = Hinv @ (S.T @ S) @ Hinv * G / (G - 1) * (N - 1) / (N - K)
    se = np.sqrt(V[1, 1])
    z = b[1] / se
    from math import erfc, sqrt
    p_one = 0.5 * erfc(z / sqrt(2))
    return b[1], se, p_one


def step6(labels):
    t = labels[labels["klimat"] == 1]
    y = t["sprzeczna"].fillna(0).to_numpy(float)
    x = (t["grupa"] == "prawica").to_numpy(int)
    b, se, p = logit_cluster(y, x, t["member_id"].to_numpy())
    pr, re = y[x == 1].mean(), y[x == 0].mean()
    return {"n": len(t), "mowcy": t["member_id"].nunique(), "sprzeczne": int(y.sum()),
            "tematyczne_prawica": int(x.sum()), "tematyczne_reszta": int((1 - x).sum()),
            "odsetek_prawica": pr, "odsetek_reszta": re, "roznica": pr - re,
            "beta1": b, "se": se, "ci_2.5": b - 1.96 * se, "ci_97.5": b + 1.96 * se, "p_jednostronne": p}


def regroup(labels, right):
    out = labels.copy()
    out["grupa"] = np.where(out["klub"].isin(right), "prawica", "reszta")
    return out


def variants(labels):
    d = pd.to_datetime(labels["data"])
    two = labels.copy()
    top = two["klimat"] == 1
    two.loc[top, "sprzeczna"] = (two.loc[top, "n_sprzecznych"].fillna(0) >= 2).astype(float)
    return {"wynik główny": labels, "bez Konfederacji": labels[~labels["klub"].isin(KONF)],
            "bez PiS": labels[~labels["klub"].isin(PIS)], "pierwsza połowa": labels[d < MIDPOINT],
            "druga połowa": labels[d >= MIDPOINT], "tylko rola poseł": labels[labels["rola"] == "poseł"],
            "≥ 2 twierdzenia sprzeczne": two}


def loso(labels):
    t = labels[labels["klimat"] == 1]
    betas = []
    for m in t["member_id"].unique():
        betas.append(step6(labels[labels["member_id"] != m])["beta1"])
    return min(betas), max(betas)


# ------------------------------------------------------------------ gold

def gold_estimate(g, reps=10_000, seed=SEED):
    """HT estimate by analysis group `grupa_an`, bootstrap within design cells (`grupa`, `warstwa`)."""
    def totals(frame):
        out = {}
        for grp in ("prawica", "reszta"):
            m = frame["grupa_an"] == grp
            out[grp] = ((frame["waga"] * frame["t"])[m].sum(), (frame["waga"] * frame["s"])[m].sum())
        return out

    tot = totals(g)
    est = {f"p_{k}": c / t for k, (t, c) in tot.items()}
    est["roznica"] = est["p_prawica"] - est["p_reszta"]
    rng = np.random.default_rng(seed)
    T = {k: np.zeros(reps) for k in ("prawica", "reszta")}
    C = {k: np.zeros(reps) for k in ("prawica", "reszta")}
    for _, c in g.groupby(["grupa", "warstwa"]):
        idx = rng.integers(0, len(c), (reps, len(c)))
        w = c["waga"].to_numpy()[idx]
        for grp in ("prawica", "reszta"):
            m = (c["grupa_an"].to_numpy() == grp)[idx]
            T[grp] += (w * c["t"].to_numpy()[idx] * m).sum(axis=1)
            C[grp] += (w * c["s"].to_numpy()[idx] * m).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = C["prawica"] / T["prawica"] - C["reszta"] / T["reszta"]
    lb = np.nanquantile(d, 0.05)
    return {**est, "dolna_95_jednostronna": lb, "ci_2.5": np.nanquantile(d, 0.025),
            "ci_97.5": np.nanquantile(d, 0.975), "poparta": bool(lb > 0), "bootstrap_brak": int(np.isnan(d).sum())}


def main():
    rows = []
    for run, file in LABELS.items():
        base = pd.read_csv(PROCESSED / "labels" / file)
        for right_name, right in RIGHTS.items():
            labels = regroup(base, right)
            main_beta = None
            for vname, sub in variants(labels).items():
                r = step6(sub)
                if main_beta is None:
                    main_beta = r["beta1"]
                ratio = r["beta1"] / main_beta
                rows.append({"przebieg": run, "prawica": right_name, "wariant": vname, **r, "krotnosc": ratio,
                             "kryterium": bool(np.sign(r["beta1"]) == np.sign(main_beta) and 0.5 <= ratio <= 2)})
            lo, hi = loso(labels)
            rows.append({"przebieg": run, "prawica": right_name, "wariant": "leave-one-speaker-out (zakres β₁)",
                         "beta1": lo, "ci_97.5": hi})
            print(f"done {run} / {right_name}")
    model = pd.DataFrame(rows)
    model.to_csv(OUT / "compare_runs.csv", index=False)

    gold = pd.read_csv(OUT / "gemma4_12b_gold.csv")
    clubs = pd.read_csv(PROCESSED / "labels" / "gemma4_12b.csv", usecols=["wypowiedz_id", "klub"])
    gold = gold.merge(clubs, on="wypowiedz_id", how="left")
    gold["t"] = gold["tematyczna"].astype(int)
    gold["s"] = gold["t"] * gold["sprzeczna"].fillna(0).astype(int)
    grows = []
    for right_name, right in RIGHTS.items():
        for corr_name, s94 in (("bez korekty #94 (plan)", 1), ("z korektą #94", 0)):
            g = gold.copy()
            g.loc[g["kolejnosc"] == CORRECTED, "s"] = s94
            g["grupa_an"] = np.where(g["klub"].isin(right), "prawica", "reszta")
            grows.append({"prawica": right_name, "anotacje": corr_name, **gold_estimate(g)})
    goldt = pd.DataFrame(grows)
    goldt.to_csv(OUT / "compare_runs_gold.csv", index=False)

    pd.set_option("display.width", 250)
    print("\nSTEP 7 (gold; identical for v1 and v2):")
    print(goldt.round(3).to_string(index=False))
    print("\nSTEPS 6 / 8 (model labels):")
    cols = ["przebieg", "prawica", "wariant", "n", "sprzeczne", "odsetek_prawica", "odsetek_reszta", "beta1", "se",
            "ci_2.5", "ci_97.5", "p_jednostronne", "krotnosc", "kryterium"]
    print(model[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
