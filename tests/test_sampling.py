import pandas as pd

from amc import sampling, topics


def corpus(texts, dates):
    df = pd.DataFrame({"tekst": texts, "data": pd.to_datetime(dates), "merytoryczna": True})
    df["wypowiedz_id"] = [str(i) for i in range(len(df))]
    return topics.add_topic_columns(df)


def test_prefilter_and_periods():
    df = corpus(["szczepionka", "według naukowców", "plandemia", "budżet państwa"],
                ["2019-12-31", "2020-01-24", "2022-11-30", "2025-01-01"])
    assert sampling.prefilter(df).tolist() == [True, True, True, False]
    assert sampling.period(df["data"]).tolist() == ["przed_covid", "covid", "po_chatgpt", "po_chatgpt"]


def test_window_bounds_inclusive():
    dates = pd.Series(pd.to_datetime(["2022-04-16", "2022-04-17", "2023-07-16", "2023-07-17", "2023-11-13", "2025-02-17",
                                      "2025-02-18"]))
    assert sampling.window(dates).fillna("-").tolist() == ["-", "A", "A", "-", "B", "B", "-"]


def test_draw_sizes_weights_and_merytoryczna():
    df = corpus(["budżet"] * 10 + ["szczepionka"] * 4, ["2019-01-01"] * 10 + ["2021-01-01"] * 4)
    df.loc[0, "merytoryczna"] = False
    sample, design = sampling.draw(df, sizes={"filtr": 3, "poza": 5}, seed=1)
    d = design.set_index(["rok", "warstwa"])
    assert d.loc[(2019, "poza"), ["N", "n"]].tolist() == [9, 5]
    assert d.loc[(2021, "filtr"), ["N", "n"]].tolist() == [4, 3]
    assert d.loc[(2021, "poza"), "n"] == 0
    assert "0" not in sample["wypowiedz_id"].tolist()
    assert sample.loc[sample["warstwa"].eq("poza"), "waga"].eq(9 / 5).all()
    assert sample.loc[sample["rok"].eq(2021), "okres"].eq("covid").all()
    assert sample["wypowiedz_id"].is_unique
    assert sample["kolejnosc"].tolist() == list(range(1, 9))


def test_prefix_is_proportional():
    df = corpus(["budżet"] * 200 + ["szczepionka"] * 200, ["2019-01-01"] * 400)
    sample, _ = sampling.draw(df, sizes={"filtr": 30, "poza": 10}, seed=0)
    head = sample.head(20)["warstwa"].value_counts()
    assert 13 <= head["filtr"] <= 17


def test_draw_is_reproducible():
    df = corpus(["budżet"] * 50, ["2019-01-01"] * 50)
    a, _ = sampling.draw(df, sizes={"poza": 10}, seed=3)
    b, _ = sampling.draw(df, sizes={"poza": 10}, seed=3)
    assert a["wypowiedz_id"].tolist() == b["wypowiedz_id"].tolist()
