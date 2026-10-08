import pandas as pd

from amc import llm_results as R


def test_weighted_total_and_topic_flags():
    df = pd.DataFrame({"wypowiedz_id": ["a", "b", "c"], "okres": ["x", "x", "y"], "y": [1, 0, 1], "waga": [2.0, 2.0, 5.0]})
    assert R.weighted_total(df, "okres").to_dict() == {"x": 2.0, "y": 5.0}
    cl = pd.DataFrame({"wypowiedz_id": ["a", "a", "c"], "temat": ["klimat", "smog", "klimat"]})
    flags = R.topic_flags(df, cl, ["klimat", "smog", "gmo"])
    assert flags.to_dict("list") == {"klimat": [1, 0, 1], "smog": [1, 0, 0], "gmo": [0, 0, 0]}


def test_cohen_kappa():
    assert R.cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    assert abs(R.cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0])) < 1e-12
