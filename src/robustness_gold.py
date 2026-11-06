"""Robustness of the step 7 result (estimate from the gold sample), complementing step 8 (robustness.py), which checks
only the step 6 result on model labels.

The step 7 verdict rests on 100 hand-labelled statements with weights up to ~1 500, so the questions are:
  1. baseline       step 7 with and without the correction of statement #94 (the team decision: the plan result is
                    without it, the correction is a sensitivity analysis)
  2. single flips   for every statement: change its gold label (contradicting <-> not, among gold-topical; topical
                    <-> not) and recompute the estimate and the one-sided 95% lower bound; which single labels decide
                    the verdict
  3. leave-one-out  drop one statement (its stratum weight becomes N_h / (n_h - 1)) and recompute
  4. stratum 3      the model-non-topical stratum has 0 / 15 gold-topical statements in both groups, so the bootstrap
                    never draws a topical statement there and treats the stratum as certain. Scenarios: a share x of
                    stratum 3 is topical (up to the one-sided 95% upper bound for 0 / 15, ~18%), contradicting at rate
                    r (0, or the gold rate of the group's stratum 2); the scenario adds N_h * x to T and N_h * x * r
                    to C in every bootstrap draw.

Input: data/processed/results/<model>_gold.csv (estimate.py). Output in data/processed/results/:
<model>_gold_robustness.csv (baseline and summaries), <model>_gold_flips.csv, <model>_gold_loo.csv,
<model>_gold_stratum3.csv; figures figures/<model>_gold_*.png.

Uses only numpy, pandas and matplotlib. The bootstrap is the one of estimation.bootstrap (resampling with
replacement within group x stratum, fixed weights), vectorised; with another random stream the bounds may differ
from estimates.csv in the third decimal.

Example:
  python src/robustness_gold.py
  python src/robustness_gold.py --powtorzenia 2000      # faster
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from amc import viz
from amc.paths import PROCESSED
from amc.viz import ACCENT, AXIS, INK2, MUTED, SECOND

OUT = PROCESSED / "results"
GROUPS = ("prawica", "reszta")
CORRECTED = 94          # `kolejnosc` of the statement whose label was corrected after the frozen run
SEED = 2026
STRATUM_COLOR = {1: SECOND, 2: ACCENT, 3: MUTED}
STRATUM_NAME = {1: "warstwa 1: model – sprzeczna", 2: "warstwa 2: model – tematyczna, niesprzeczna",
                3: "warstwa 3: model – nietematyczna"}


def prepare(gold):
    """Gold sample with integer t (topical) and s (topical and contradicting) and the cell key."""
    g = gold.copy()
    g["t"] = g["tematyczna"].astype(int)
    g["s"] = g["t"] * g["sprzeczna"].fillna(0).astype(int)
    g["komorka"] = g["grupa"] + "_" + g["warstwa"].astype(str)
    return g.reset_index(drop=True)


def with_label(g, kolejnosc, t, s):
    out = g.copy()
    i = out.index[out["kolejnosc"] == kolejnosc]
    out.loc[i, "t"], out.loc[i, "s"] = t, s * t
    return out


def point(g, extra=None):
    """p_g = C_g / T_g with C_g = sum N_h * mean(s), T_g = sum N_h * mean(t); `extra` adds (T, C) per group."""
    out = {}
    for grp in GROUPS:
        cells = g[g["grupa"] == grp].groupby("warstwa").agg(N=("N_h", "first"), t=("t", "mean"), s=("s", "mean"))
        T, C = (cells["N"] * cells["t"]).sum(), (cells["N"] * cells["s"]).sum()
        if extra:
            T, C = T + extra[grp][0], C + extra[grp][1]
        out[f"T_{grp}"], out[f"C_{grp}"] = T, C
        out[f"p_{grp}"] = C / T if T else np.nan
    out["roznica"] = out["p_prawica"] - out["p_reszta"]
    return out


def boot(g, reps, seed=SEED, extra=None):
    """Stratified bootstrap of the difference: per cell, `reps` resamples of t and s means, N_h fixed."""
    rng = np.random.default_rng(seed)
    T = {grp: np.zeros(reps) for grp in GROUPS}
    C = {grp: np.zeros(reps) for grp in GROUPS}
    for (grp, h), c in g.groupby(["grupa", "warstwa"]):
        n, N = len(c), c["N_h"].iloc[0]
        idx = rng.integers(0, n, (reps, n))
        T[grp] += N * c["t"].to_numpy()[idx].mean(axis=1)
        C[grp] += N * c["s"].to_numpy()[idx].mean(axis=1)
    p = {}
    for grp in GROUPS:
        if extra:
            T[grp], C[grp] = T[grp] + extra[grp][0], C[grp] + extra[grp][1]
        with np.errstate(invalid="ignore", divide="ignore"):
            p[grp] = np.where(T[grp] > 0, C[grp] / T[grp], np.nan)
    return p["prawica"] - p["reszta"]


def summary(g, reps, seed=SEED, extra=None):
    d = boot(g, reps, seed, extra)
    est = point(g, extra)
    return {**est, "dolna_95_jednostronna": np.nanquantile(d, 0.05), "ci_2.5": np.nanquantile(d, 0.025),
            "ci_97.5": np.nanquantile(d, 0.975), "bootstrap_brak": int(np.isnan(d).sum()),
            "poparta": bool(np.nanquantile(d, 0.05) > 0)}


def single_flips(g, reps):
    """Every possible single-label change: contradicting <-> not among gold-topical, topical <-> not."""
    rows = []
    for _, r in g.iterrows():
        changes = [("tematycznosc", 1 - r["t"], 0)]
        if r["t"] == 1:
            changes.append(("sprzecznosc", 1, 1 - r["s"]))
        else:
            changes.append(("tematyczna_i_sprzeczna", 1, 1))
        for kind, t, s in changes:
            res = summary(with_label(g, r["kolejnosc"], t, s), reps)
            rows.append({"kolejnosc": r["kolejnosc"], "wypowiedz_id": r["wypowiedz_id"], "grupa": r["grupa"],
                         "warstwa": r["warstwa"], "waga": r["waga"], "anotator": r["anotator"], "zmiana": kind,
                         "t_przed": r["t"], "s_przed": r["s"], "t_po": t, "s_po": s * t,
                         **{k: res[k] for k in ("roznica", "dolna_95_jednostronna", "poparta")}})
    return pd.DataFrame(rows)


def leave_one_out(g, reps):
    rows = []
    for i, r in g.iterrows():
        rest = g.drop(index=i)
        res = summary(rest, reps)
        rows.append({"kolejnosc": r["kolejnosc"], "wypowiedz_id": r["wypowiedz_id"], "grupa": r["grupa"],
                     "warstwa": r["warstwa"], "waga": r["waga"], "t": r["t"], "s": r["s"],
                     **{k: res[k] for k in ("roznica", "dolna_95_jednostronna", "poparta")}})
    return pd.DataFrame(rows)


def stratum3(g, reps, shares):
    """Scenarios for the hidden topical statements of stratum 3 (equal share x in both groups)."""
    s2 = {grp: g[(g["grupa"] == grp) & (g["warstwa"] == 2) & (g["t"] == 1)]["s"].mean() for grp in GROUPS}
    N3 = {grp: g[(g["grupa"] == grp) & (g["warstwa"] == 3)]["N_h"].iloc[0] for grp in GROUPS}
    rows = []
    for rate_name, rate in (("0", {grp: 0.0 for grp in GROUPS}), ("jak_warstwa_2", s2)):
        for x in shares:
            extra = {grp: (N3[grp] * x, N3[grp] * x * rate[grp]) for grp in GROUPS}
            res = summary(g, reps, extra=extra)
            rows.append({"udzial_tematycznych_w3": x, "odsetek_sprzecznych_w3": rate_name,
                         "sprz_w3_prawica": rate["prawica"], "sprz_w3_reszta": rate["reszta"], **res})
    return pd.DataFrame(rows)


def pl(v, d=1):
    """Number with a Polish decimal comma."""
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def upper_zero(n, alpha=0.05):
    """One-sided (1 - alpha) upper bound for a proportion with 0 successes in n (exact binomial)."""
    return 1 - alpha ** (1 / n)


# ---------------------------------------------------------------- figures

def fig_estimates(base, model, slug):
    """Model-label shares vs the gold estimate (with and without #94), with 95% intervals for the difference."""
    viz.setup()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    rows = [("prawica", "p_prawica"), ("reszta", "p_reszta"), ("różnica (pp)", "roznica")]
    variants = [("etykiety modelu (krok 6)", None, MUTED, -0.22),
                ("próba walidacyjna, plan (bez korekty #94)", "plan", ACCENT, 0.0),
                ("próba walidacyjna, z korektą #94", "korekta", SECOND, 0.22)]
    for label, key, color, dy in variants:
        for i, (_, col) in enumerate(rows):
            if key is None:
                v = model[col]
                ax.plot(100 * v, i + dy, "D", color=color, ms=6, label=label if i == 0 else None)
                continue
            b = base[key]
            v = b[col]
            if col == "roznica":
                ax.plot([100 * b["ci_2.5"], 100 * b["ci_97.5"]], [i + dy] * 2, color=color, lw=2)
            ax.plot(100 * v, i + dy, "o", color=color, ms=7, label=label if i == 0 else None)
            ax.annotate(pl(100 * v), (100 * v, i + dy), xytext=(0, 7), textcoords="offset points",
                        ha="center", fontsize=7.5, color=color,
                        bbox=dict(boxstyle="square,pad=0.1", fc=viz.SURF, ec="none"))
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("odsetek wypowiedzi sprzecznych wśród wypowiedzi o klimacie (%) / różnica (pp)")
    ax.set_title("Model a próba walidacyjna")
    viz.subtitle(ax, "dla różnicy: 95% przedział z bootstrapu warstwowego (10 000 powtórzeń)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=2, fontsize=8)
    viz.save(fig, f"{slug}_gold_oszacowania")
    plt.close(fig)


def fig_bootstrap(g_plan, g_corr, reps, slug):
    viz.setup()
    fig, ax = plt.subplots(figsize=(8, 3.4))
    bins = np.linspace(-0.6, 1.0, 81)
    for g, label, color in ((g_plan, "plan (bez korekty #94)", ACCENT), (g_corr, "z korektą #94", SECOND)):
        d = boot(g, reps)
        ax.hist(100 * d, bins=100 * bins, color=color, alpha=0.45, label=label)
        q = np.nanquantile(d, 0.05)
        ax.axvline(100 * q, color=color, lw=1.5, ls="--")
        ax.annotate(f"5. percentyl: {pl(100 * q)} pp", (100 * q, ax.get_ylim()[1] * 0.92), xytext=(4, 0),
                    textcoords="offset points", fontsize=8, color=color)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_xlabel("różnica prawica − reszta (pp), powtórzenia bootstrapu")
    ax.set_ylabel("liczba powtórzeń")
    ax.set_title("Rozkład bootstrapowy różnicy")
    viz.subtitle(ax, "hipoteza poparta, gdy 5. percentyl > 0")
    ax.legend(loc="upper right", fontsize=8)
    viz.save(fig, f"{slug}_gold_bootstrap")
    plt.close(fig)


def fig_flips(flips, base_lb, title, name):
    """Lower bound after each single-label change; labelled: changes that cross zero."""
    viz.setup()
    f = flips.sort_values("dolna_95_jednostronna").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for h, c in STRATUM_COLOR.items():
        m = f["warstwa"] == h
        ax.scatter(np.flatnonzero(m), 100 * f.loc[m, "dolna_95_jednostronna"], s=14, color=c, label=STRATUM_NAME[h])
    ax.axhline(0, color=INK2, lw=1)
    ax.axhline(100 * base_lb, color=ACCENT, lw=1, ls="--")
    ax.annotate(f"bez zmiany: {pl(100 * base_lb)} pp", (0, 100 * base_lb), xytext=(2, 3), textcoords="offset points",
                fontsize=8, color=ACCENT)
    crossing = f[f["poparta"] != (base_lb > 0)]
    named = crossing[crossing["warstwa"] != 3]
    ax.set_xticks([])
    ax.grid(axis="x", visible=False)
    ax.set_xlabel(f"wszystkie możliwe zmiany jednej etykiety ({len(f)}), posortowane")
    ax.set_ylabel("dolna granica 95% (pp)")
    ax.set_title(title)
    n3 = len(crossing) - len(named)
    viz.subtitle(ax, f"werdykt odwraca {len(crossing)} zmian: {len(named)} w warstwach 1–2 "
                     f"i {n3} w warstwie 3 (waga ok. 1 300–1 500); lista: _gold_flips.csv")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=7.5)
    viz.save(fig, name)
    plt.close(fig)


def fig_stratum3(sc, slug, ub):
    viz.setup()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for (variant, rate), c in sc.groupby(["wariant", "odsetek_sprzecznych_w3"]):
        color = ACCENT if variant == "plan" else SECOND
        ls = "-" if rate == "0" else ":"
        x = 100 * c["udzial_tematycznych_w3"]
        name = f"{'plan' if variant == 'plan' else 'z korektą #94'}"
        if rate == "0":
            ax.plot(x, 100 * c["roznica"], color=color, lw=2, label=f"{name}: oszacowanie")
            ax.fill_between(x, 100 * c["dolna_95_jednostronna"], 100 * c["roznica"], color=color, alpha=0.12,
                            lw=0, label=f"{name}: do dolnej granicy 95%")
        else:
            # point estimate only: a fixed scenario added to every bootstrap draw shrinks the variance, so its
            # lower bound would look more certain than the data are
            ax.plot(x, 100 * c["roznica"], color=color, ls=":", lw=1.5,
                    label=f"{name}: oszacowanie, ukryte sprzeczne jak w warstwie 2")
    ax.axhline(0, color=INK2, lw=1)
    ax.axvline(100 * ub, color=AXIS, lw=1, ls="--")
    ax.annotate(f"górna granica 95%\ndla 0/15: {pl(100 * ub, 0)}%", (100 * ub, 15), xytext=(-4, 0),
                textcoords="offset points", ha="right", fontsize=8, color=MUTED)
    ax.set_xlabel("założony udział wypowiedzi o klimacie w warstwie 3 (%)")
    ax.set_ylabel("różnica (pp)")
    ax.set_title("Warstwa 3: wypowiedzi o klimacie przeoczone przez model")
    viz.subtitle(ax, "ciągła: ukryte wypowiedzi niesprzeczne; kropkowana: sprzeczne w tym samym odsetku co w warstwie 2")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=7.5)
    viz.save(fig, f"{slug}_gold_warstwa3")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="gemma4_12b")
    ap.add_argument("--powtorzenia", type=int, default=10_000, help="bootstrap resamples for the baseline")
    ap.add_argument("--powtorzenia-wariantow", type=int, default=2_000,
                    help="bootstrap resamples for each flip / leave-one-out / scenario")
    a = ap.parse_args()
    slug = a.model
    gold = prepare(pd.read_csv(OUT / f"{slug}_gold.csv"))
    g_plan = with_label(gold, CORRECTED, 1, 1)
    g_corr = with_label(gold, CORRECTED, 1, 0)

    base = {"plan": summary(g_plan, a.powtorzenia), "korekta": summary(g_corr, a.powtorzenia)}
    table = pd.DataFrame(base).T
    print("Step 7 baseline:\n", table[["p_prawica", "p_reszta", "roznica", "dolna_95_jednostronna", "ci_2.5",
                                      "ci_97.5", "poparta"]].round(4).to_string())

    raw = pd.read_csv(OUT / f"{slug}_uncorrected.csv").set_index("grupa")
    model = {"p_prawica": raw.loc["prawica", "odsetek"], "p_reszta": raw.loc["reszta", "odsetek"]}
    model["roznica"] = model["p_prawica"] - model["p_reszta"]

    flips, loo, sc = {}, {}, []
    shares = np.round(np.arange(0, 0.201, 0.01), 3)
    ub = upper_zero(15)
    for key, g in (("plan", g_plan), ("korekta", g_corr)):
        flips[key] = single_flips(g, a.powtorzenia_wariantow).assign(wariant=key)
        loo[key] = leave_one_out(g, a.powtorzenia_wariantow).assign(wariant=key)
        sc.append(stratum3(g, a.powtorzenia_wariantow, shares).assign(wariant=key))
    flips_all = pd.concat(flips.values(), ignore_index=True)
    loo_all = pd.concat(loo.values(), ignore_index=True)
    sc = pd.concat(sc, ignore_index=True)

    summary_rows = []
    for key in base:
        b = base[key]
        f, l = flips[key], loo[key]
        cross_f = f[f["poparta"] != b["poparta"]]
        cross_l = l[l["poparta"] != b["poparta"]]
        s0 = sc[(sc["wariant"] == key) & (sc["odsetek_sprzecznych_w3"].astype(str) == "0")]
        flip_point = s0.loc[s0["poparta"] != b["poparta"], "udzial_tematycznych_w3"]
        summary_rows.append({
            "wariant": key, **{k: b[k] for k in ("p_prawica", "p_reszta", "roznica", "dolna_95_jednostronna",
                                                "ci_2.5", "ci_97.5", "poparta", "T_prawica", "C_prawica",
                                                "T_reszta", "C_reszta")},
            "zmiany_jednej_etykiety": len(f), "zmiany_odwracajace_werdykt": len(cross_f),
            "odwracajace_kolejnosc": " ".join(f"#{k}" for k in sorted(cross_f["kolejnosc"].unique())),
            "loo_roznica_min": l["roznica"].min(), "loo_roznica_max": l["roznica"].max(),
            "loo_dolna_min": l["dolna_95_jednostronna"].min(), "loo_dolna_max": l["dolna_95_jednostronna"].max(),
            "loo_odwracajace": " ".join(f"#{k}" for k in cross_l["kolejnosc"]),
            "w3_udzial_odwracajacy_werdykt": flip_point.min() if len(flip_point) else np.nan,
            "w3_gorna_granica_0_na_15": ub,
        })
    out = pd.DataFrame(summary_rows)
    out.to_csv(OUT / f"{slug}_gold_robustness.csv", index=False)
    flips_all.to_csv(OUT / f"{slug}_gold_flips.csv", index=False)
    loo_all.to_csv(OUT / f"{slug}_gold_loo.csv", index=False)
    sc.to_csv(OUT / f"{slug}_gold_stratum3.csv", index=False)
    print("\nSummary:\n", out.T.to_string())

    fig_estimates(base, model, slug)
    fig_bootstrap(g_plan, g_corr, a.powtorzenia, slug)
    fig_flips(flips["plan"], base["plan"]["dolna_95_jednostronna"],
              "Zmiana jednej etykiety: plan (bez korekty #94)", f"{slug}_gold_wplyw_plan")
    fig_flips(flips["korekta"], base["korekta"]["dolna_95_jednostronna"],
              "Zmiana jednej etykiety: z korektą #94", f"{slug}_gold_wplyw_korekta")
    fig_stratum3(sc, slug, ub)


if __name__ == "__main__":
    main()
