import pandas as pd

from amc import population


def statements(n_right_climate, n_right_other, n_rest_climate, n_rest_other, date="2024-05-01"):
    clubs = (["PiS"] * n_right_climate + ["Konfederacja_KP"] * n_right_other + ["KO"] * n_rest_climate
             + ["Republikanie"] * n_rest_other)
    climate = [1] * n_right_climate + [0] * n_right_other + [1] * n_rest_climate + [0] * n_rest_other
    n = len(clubs)
    return pd.DataFrame({"wypowiedz_id": [f"10_1_{date}_{i}" for i in range(n)], "data": pd.to_datetime([date] * n),
                         "merytoryczna": True, "member_id": 1, "klub": clubs, "klimat": climate,
                         "tekst": "x", "liczba_slow": 1})


def test_population_scope_and_groups():
    df = statements(1, 1, 1, 1)
    extra = df.iloc[:4].copy()
    extra["wypowiedz_id"] = ["a", "b", "c", "d"]
    extra["data"] = pd.to_datetime(["2023-11-12", "2026-09-16", "2023-11-13", "2026-09-15"])
    extra.loc[extra.index[2], "member_id"] = 0
    extra.loc[extra.index[3], "merytoryczna"] = False
    pop = population.select(pd.concat([df, extra], ignore_index=True))
    assert len(pop) == 4
    assert pop["grupa"].tolist() == ["prawica", "prawica", "reszta", "reszta"]

