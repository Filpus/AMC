"""Step 8: robustness of the step 6 test (logit of the model label on prawica, SE clustered by speaker) in variants.

Plan variants (presentation, slide 12; supplement, step 8) decide whether the result is robust:
  bez_konfederacji   statements of Konfederacja and Konfederacja_KP removed (prawica = PiS, RozwojPlus)
  bez_pis            statements of PiS and RozwojPlus removed (prawica = Konfederacja, Konfederacja_KP)
  pierwsza_polowa    statements before the midpoint of the study period
  druga_polowa       statements from the midpoint on
A removed club leaves the sample (it does not move to reszta). RozwojPlus goes with PiS and Konfederacja_KP with
Konfederacja, as in the blocks of amc/speakers.py. The midpoint is the calendar middle of
population.STUDY_PERIOD.

Robust = in every plan variant beta1 has the sign of the main result and beta1 / beta1_main is in [0.5; 2]. A variant
without an estimate (separation) fails the criterion.

Extensions answer likely objections but do not enter the criterion: only MPs speaking as MPs (rola == "poseł", without
ministers), a broad right (plus Republikanie and Kukiz15), a statement contradicting only with >= 2 contradicting
claims, and leave-one-speaker-out.
"""
import numpy as np
import pandas as pd

from . import estimation as E
from .population import RIGHT_CLUBS, STUDY_PERIOD

KONFEDERACJA = ("Konfederacja", "Konfederacja_KP")
PIS = ("PiS", "RozwojPlus")
assert set(KONFEDERACJA) | set(PIS) == set(RIGHT_CLUBS)
BROAD_RIGHT = ("Republikanie", "Kukiz15")
MIDPOINT = (STUDY_PERIOD[0] + (STUDY_PERIOD[1] - STUDY_PERIOD[0]) / 2).normalize()
LOW, HIGH = 0.5, 2.0
Z95 = 1.959963984540054


def _without(labels, clubs):
    return labels[~labels["klub"].isin(clubs)]


def _period(labels, first):
    d = pd.to_datetime(labels["data"])
    return labels[d < MIDPOINT] if first else labels[d >= MIDPOINT]


def _broad_right(labels):
    out = labels.copy()
    out.loc[out["klub"].isin(BROAD_RIGHT), "grupa"] = "prawica"
    return out


def _two_claims(labels):
    out = labels.copy()
    topical = out["klimat"] == 1
    out.loc[topical, "sprzeczna"] = (out.loc[topical, "n_sprzecznych"].fillna(0) >= 2).astype(float)
    return out


PLAN = {
    "bez_konfederacji": ("bez Konfederacji (i Konfederacji KP)", lambda l: _without(l, KONFEDERACJA)),
    "bez_pis": ("bez PiS (i RozwojPlus)", lambda l: _without(l, PIS)),
    "pierwsza_polowa": (f"pierwsza połowa okresu (do {(MIDPOINT - pd.Timedelta(days=1)):%d.%m.%Y})",
                        lambda l: _period(l, True)),
    "druga_polowa": (f"druga połowa okresu (od {MIDPOINT:%d.%m.%Y})", lambda l: _period(l, False)),
}
EXTENSIONS = {
    "tylko_poslowie": ("tylko rola „poseł” (bez ministrów)", lambda l: l[l["rola"] == "poseł"]),
    "prawica_szeroka": ("prawica + Republikanie i Kukiz15", _broad_right),
    "dwa_twierdzenia": ("sprzeczna = co najmniej 2 twierdzenia sprzeczne", _two_claims),
}


def shares(labels):
    """Model-label shares of contradicting among topical, by group, and the difference prawica - reszta (pp scale 0-1)."""
    r = E.raw_shares(labels)
    return {"tematyczne_prawica": int(r.loc["prawica", "tematyczne"]), "tematyczne_reszta": int(r.loc["reszta", "tematyczne"]),
            "odsetek_prawica": r.loc["prawica", "odsetek"], "odsetek_reszta": r.loc["reszta", "odsetek"],
            "roznica": r.loc["prawica", "odsetek"] - r.loc["reszta", "odsetek"]}


def fit(labels):
    """Step 6 regression with the 95% interval and the odds ratio, plus model-label shares."""
    r = E.regression(labels)
    b, se = r["beta1"], r["se"]
    return {**r, "ci_2.5": b - Z95 * se, "ci_97.5": b + Z95 * se, "iloraz_szans": np.exp(b), **shares(labels)}


def criterion(beta, beta_main):
    """Same sign as the main result and beta / beta_main in [LOW; HIGH]; False without an estimate."""
    if not np.isfinite(beta) or not np.isfinite(beta_main) or beta_main == 0:
        return {"krotnosc": np.nan, "kierunek_ok": False, "wielkosc_ok": False, "odporny": False}
    ratio = beta / beta_main
    same = bool(np.sign(beta) == np.sign(beta_main))
    size = bool(LOW <= ratio <= HIGH)
    return {"krotnosc": ratio, "kierunek_ok": same, "wielkosc_ok": size, "odporny": same and size}


def run(labels):
    """One row per variant: the main result, the plan variants and the extensions, with the criterion vs the main
    result (`rodzaj`: glowny / plan / rozszerzenie)."""
    main = fit(labels)
    rows = [{"wariant": "glowny", "opis": "wynik główny (krok 6)", "rodzaj": "glowny", **main,
             **criterion(main["beta1"], main["beta1"])}]
    for kind, variants in (("plan", PLAN), ("rozszerzenie", EXTENSIONS)):
        for key, (desc, subset) in variants.items():
            r = fit(subset(labels))
            rows.append({"wariant": key, "opis": desc, "rodzaj": kind, **r, **criterion(r["beta1"], main["beta1"])})
    return pd.DataFrame(rows)


def verdict(table):
    """Robust if every plan variant meets the criterion; also the failing plan variants."""
    plan = table[table["rodzaj"] == "plan"]
    failing = plan.loc[~plan["odporny"], "wariant"].tolist()
    return {"odporny": not failing, "niespelnione": failing}


def leave_one_speaker_out(labels):
    """beta1 after removing each speaker with a topical statement in turn, with the criterion vs the main result,
    sorted by beta1."""
    main = E.regression(labels)["beta1"]
    topical = labels[labels["klimat"] == 1]
    stats = topical.groupby("member_id").agg(grupa=("grupa", "first"), tematyczne=("sprzeczna", "size"),
                                             sprzeczne=("sprzeczna", "sum"))
    rows = []
    for member in stats.index:
        r = E.regression(labels[labels["member_id"] != member])
        rows.append({"member_id": member, **stats.loc[member].to_dict(), "beta1": r["beta1"], "se": r["se"],
                     "p_jednostronne": r["p_jednostronne"], **criterion(r["beta1"], main)})
    return pd.DataFrame(rows).sort_values("beta1").reset_index(drop=True)
