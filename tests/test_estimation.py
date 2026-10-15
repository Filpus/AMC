import numpy as np
import pandas as pd
import pytest

from amc import estimation as E


def example_gold():
    """Worked example of step 7 (invented numbers; difference 0.218, one-sided lower bound 0.134, 95% interval
    [0.120; 0.354]): group, stratum, N_h and the gold counts (1,1), (1,0), (0,0)."""
    rows = [("prawica", 1, 150, 14, 4, 2), ("prawica", 2, 450, 1, 13, 1), ("prawica", 3, 19400, 0, 0, 15),
            ("reszta", 1, 60, 8, 9, 3), ("reszta", 2, 900, 0, 15, 0), ("reszta", 3, 39040, 0, 0, 15)]
    out = []
    for g, h, n_pop, s, t, nt in rows:
        labels = [(1, 1)] * s + [(1, 0)] * t + [(0, 0)] * nt
        out += [{"grupa": g, "warstwa": h, "waga": n_pop / len(labels), "tematyczna": a, "sprzeczna": b}
                for a, b in labels]
    return pd.DataFrame(out)


def test_step7_reproduces_example():
    gold = example_gold()
    p = E.proportions(E.arrays(gold))
    assert p["p_prawica"] == pytest.approx(135 / 555) and p["p_reszta"] == pytest.approx(24 / 951)
    assert p["roznica"] == pytest.approx(0.218, abs=5e-4)
    s = E.summarize(gold, E.proportions, reps=10_000)
    assert s.loc["roznica", "dolna_95_jednostronna"] == pytest.approx(0.134, abs=0.01)
    assert s.loc["roznica", "przedzial_97.5"] == pytest.approx(0.354, abs=0.015)


def test_step5_rates_by_stage():
    gold = example_gold()
    q = E.quality(E.arrays(gold))
    # final label in prawica: TP = 7.5 * 14, FP = 7.5 * 6, FN = 30 * 1
    assert q["prawica_etykieta_TPR"] == pytest.approx(105 / 135)
    assert q["prawica_etykieta_precyzja"] == pytest.approx(105 / 150)
    # topicality in prawica: misses only in stratum 3, none in the example
    assert q["prawica_tematycznosc_TPR"] == 1.0
    # verdict on statements topical by both: prawica stratum 1 has 18 such, 14 contradicting; stratum 2 has 14, 1
    assert q["prawica_werdykt_TPR"] == pytest.approx(7.5 * 14 / (7.5 * 14 + 30))
    assert q["reszta_werdykt_TNR"] == pytest.approx(60 * 15 / (60 * 15 + 3 * 9))


def labels(n_right=300, n_rest=300, p_right=0.2, p_rest=0.05, seed=1):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"wypowiedz_id": [f"w{i}" for i in range(n_right + n_rest)],
                      "grupa": ["prawica"] * n_right + ["reszta"] * n_rest})
    d["member_id"] = rng.integers(0, 60, len(d)) + np.where(d["grupa"] == "prawica", 0, 100)
    d["klimat"] = (rng.uniform(size=len(d)) < 0.5).astype(int)
    p = np.where(d["grupa"] == "prawica", p_right, p_rest)
    d["sprzeczna"] = np.where(d["klimat"] == 1, (rng.uniform(size=len(d)) < p).astype(float), 0.0)
    return d


def test_draw_takes_whole_small_stratum_and_weights():
    d = labels()
    sample = E.draw(d)
    sizes = E.strata_sizes(d).set_index(["grupa", "warstwa"])["N_h"]
    for (g, h), cell in sample.groupby(["grupa", "warstwa"]):
        assert len(cell) == min(E.SIZES[h], sizes[(g, h)])
        assert (cell["waga"] == sizes[(g, h)] / len(cell)).all()
    assert sample["wypowiedz_id"].is_unique


def test_stratum_requires_finished_labels():
    d = labels()
    d.loc[d["klimat"] == 1, "sprzeczna"] = np.nan
    with pytest.raises(ValueError):
        E.stratum(d)


def test_regression_and_separation():
    r = E.regression(labels())
    assert r["beta1"] > 0 and r["p_jednostronne"] < 0.05 and r["uwaga"] == ""
    sep = E.regression(labels(p_rest=0.0))
    assert sep["uwaga"] == "separacja" and np.isnan(sep["beta1"])


def test_rarity():
    r = E.rarity(labels())
    assert r["warunek_spelniony"] and r["tematyczne_prawica"] >= 100
    assert not E.rarity(labels(n_right=150, n_rest=150))["warunek_spelniony"]
