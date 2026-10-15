import pandas as pd

from amc import topics


def test_flag_counts_and_inflection():
    f = topics.flag_topics(pd.Series(["Szczepionki i szczepienia ratują życie; antyszczepionkowcy kłamią."]))
    assert f.loc[0, "szczepienia"] == 3
    assert f.loc[0, "covid"] == 0


def test_polish_inflection_with_string_dtype():
    f = topics.flag_topics(pd.Series(["zmianą klimatu", "energią jądrową"], dtype="string[pyarrow]"))
    assert f["klimat"].tolist() == [1, 0]
    assert f["energia_jadrowa"].tolist() == [0, 1]


def test_phrases_broken_across_lines():
    f = topics.flag_topics(pd.Series(["skutki zmiany\nklimatu", "tzw.\npandemia", "pyłu PM\n10"]))
    assert f["klimat"].tolist() == [1, 0, 0]
    assert f["sceptycyzm"].tolist() == [0, 1, 0]
    assert f["smog"].tolist() == [0, 0, 1]


def test_climate_co2_and_ets_spellings():
    f = topics.flag_topics(pd.Series(["emisji CO 2", "emisja CO2", "od 2027 r. wchodzi ETS2", "ETS1 i ETS 2",
                                      "co 2 lata", "emisji\nCO 2"]))
    assert f["klimat"].tolist() == [1, 1, 1, 2, 0, 1]


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
