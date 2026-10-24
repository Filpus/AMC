import numpy as np
import pandas as pd
import pytest

from amc import robustness as R


def labels(seed=0, n=1200):
    """Invented topical statements: prawica contradicts more often (0.10 vs 0.04), 60 speakers, the whole period."""
    rng = np.random.default_rng(seed)
    clubs = rng.choice(["PiS", "RozwojPlus", "Konfederacja", "Konfederacja_KP", "KO", "Lewica", "Republikanie"], n)
    right = np.isin(clubs, ["PiS", "RozwojPlus", "Konfederacja", "Konfederacja_KP"])
    days = rng.integers(0, (R.STUDY_PERIOD[1] - R.STUDY_PERIOD[0]).days + 1, n)
    contradicting = rng.random(n) < np.where(right, 0.10, 0.04)
    return pd.DataFrame({
        "wypowiedz_id": [f"w{i}" for i in range(n)], "data": (R.STUDY_PERIOD[0] + pd.to_timedelta(days, "D")).strftime("%Y-%m-%d"),
        "member_id": rng.integers(1, 61, n), "rola": np.where(rng.random(n) < 0.05, "rząd", "poseł"), "klub": clubs,
        "grupa": np.where(right, "prawica", "reszta"), "klimat": 1, "sprzeczna": contradicting.astype(float),
        "n_sprzecznych": np.where(contradicting, rng.integers(1, 3, n), 0).astype(float)})


def test_midpoint_splits_the_period():
    assert R.MIDPOINT == pd.Timestamp("2025-04-14")
    d = labels()
    first, second = R.PLAN["pierwsza_polowa"][1](d), R.PLAN["druga_polowa"][1](d)
    assert len(first) + len(second) == len(d)
    assert pd.to_datetime(first["data"]).max() < R.MIDPOINT <= pd.to_datetime(second["data"]).min()


def test_club_variants_remove_clubs_and_keep_groups():
    d = labels()
    no_konf = R.PLAN["bez_konfederacji"][1](d)
    no_pis = R.PLAN["bez_pis"][1](d)
    assert not no_konf["klub"].isin(R.KONFEDERACJA).any() and set(no_konf.loc[no_konf["grupa"] == "prawica", "klub"]) == set(R.PIS)
    assert not no_pis["klub"].isin(R.PIS).any() and set(no_pis.loc[no_pis["grupa"] == "prawica", "klub"]) == set(R.KONFEDERACJA)
    assert (no_konf["grupa"] == "reszta").sum() == (d["grupa"] == "reszta").sum()


def test_extensions():
    d = labels()
    broad = R.EXTENSIONS["prawica_szeroka"][1](d)
    assert (broad.loc[broad["klub"] == "Republikanie", "grupa"] == "prawica").all()
    two = R.EXTENSIONS["dwa_twierdzenia"][1](d)
    assert two["sprzeczna"].sum() == (d["n_sprzecznych"] >= 2).sum()
    assert (R.EXTENSIONS["tylko_poslowie"][1](d)["rola"] == "poseł").all()


@pytest.mark.parametrize("beta, ok", [(0.6, True), (0.3, True), (1.2, True), (0.29, False), (1.21, False),
                                      (-0.6, False), (np.nan, False)])
def test_criterion(beta, ok):
    assert R.criterion(beta, 0.6)["odporny"] is ok


def test_run_and_verdict():
    t = R.run(labels())
    assert t["wariant"].tolist() == ["glowny", *R.PLAN, *R.EXTENSIONS]
    assert t.loc[0, "krotnosc"] == 1.0 and t.loc[0, "beta1"] > 0
    assert (t["ci_2.5"] < t["beta1"]).all() and (t["beta1"] < t["ci_97.5"]).all()
    t.loc[t["wariant"] == "bez_pis", "odporny"] = False
    t.loc[t["wariant"] == "dwa_twierdzenia", "odporny"] = False   # extensions do not decide
    assert R.verdict(t) == {"odporny": False, "niespelnione": ["bez_pis"]}
