import pandas as pd

from amc import topics


def test_flag_counts_and_inflection():
    f = topics.flag_topics(pd.Series(["Szczepionki i szczepienia ratują życie; antyszczepionkowcy kłamią."]))
    assert f.loc[0, "szczepienia"] == 3
    assert f.loc[0, "covid"] == 0


def test_science_markers_who_and_pan():
    f = topics.flag_topics(pd.Series(["Według WHO i według badań — tak mówi PAN.", "Panie pośle, pan nie ma racji."]))
    assert f.loc[0, "nauka"] == 3
    assert f.loc[1, "nauka"] == 0  # "pan" jako zwrot grzecznościowy nie jest PAN


def test_skeptic_markers_narrow():
    f = topics.flag_topics(pd.Series(["To religia klimatyzmu i tzw. pandemia.", "Rzekomo zrównoważony budżet."]))
    assert f.loc[0, "sceptycyzm"] == 2
    assert f.loc[1, "sceptycyzm"] == 0  # samo "rzekomo" nie jest markerem


def test_add_topic_columns_thresholds_and_groups():
    df = pd.DataFrame({"tekst": ["covid covid covid", "szczepionka", "klimat"]})
    out = topics.add_topic_columns(df)
    assert out["covid_tem"].tolist() == [True, False, False]
    assert out["zdrowie_tem"].tolist() == [True, False, False]
    assert out["zdrowie_wzm"].tolist() == [True, True, False]
    assert out["dowolny_tem"].tolist() == [True, False, False]
