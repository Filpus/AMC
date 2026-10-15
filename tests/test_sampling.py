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
