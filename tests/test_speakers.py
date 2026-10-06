import pandas as pd

from amc.speakers import (INNE, MpMatcher, blok, club_history, club_on_date, klub_z_etykiety, rola_komisja,
                          rola_plenarna)

MPS = [
    {"id": 1, "firstName": "Janusz", "lastName": "Cieszyński"},
    {"id": 2, "firstName": "Riad", "lastName": "Haidar"},
    {"id": 3, "firstName": "Anna", "secondName": "Maria", "lastName": "Siarkowska"},
]


def test_rola_plenarna():
    assert rola_plenarna("", "Marszałek") == "prowadzący"
    assert rola_plenarna("Wicemarszałek Sejmu", "X") == "prowadzący"
    assert rola_plenarna("Podsekretarz Stanu w Ministerstwie Zdrowia", "X") == "rząd"
    assert rola_plenarna("Poseł", "X") == "poseł"
    assert rola_plenarna("Rzecznik Praw Obywatelskich", "X") == "inni"


def test_rola_komisja():
    assert rola_komisja("Przewodnicząca poseł Elżbieta Gelert (KO)") == "prowadzący"
    assert rola_komisja("Poseł Janusz Cieszyński (PiS)") == "poseł"
    assert rola_komisja("Podsekretarz stanu w Ministerstwie Zdrowia Jerzy Szafranowicz") == "rząd"
    assert rola_komisja("Zastępca prezesa Narodowego Funduszu Zdrowia Marek Augustyn") == "inni"


def test_mp_matcher():
    match = MpMatcher(MPS)
    assert match("Poseł Janusz Cieszyński (PiS)") == 1
    assert match("Poseł Haidar Riad (KO)") == 2                         # odwrócona kolejność
    assert match("Poseł Anna Maria Siarkowska /PiS/ – spoza składu Komisji") == 3
    assert match("Legislator Urszula Sęk") == 0


def test_klub_z_etykiety():
    assert klub_z_etykiety("Poseł Jan Kowalski (PiS)") == "PiS"
    assert klub_z_etykiety("Poseł Jan Kowalski /KO/") == "KO"
    assert klub_z_etykiety("Minister zdrowia") is None


def test_club_history_and_on_date():
    obs = pd.DataFrame({"member_id": [1, 1, 1], "klub": ["PiS", "PiS", "RozwojPlus"],
                        "data": ["2024-01-10", "2024-02-10", "2024-03-10"]})
    hist = club_history(obs)
    assert hist[["klub", "od", "do"]].values.tolist() == [["PiS", "2024-01-10", "2024-02-10"],
                                                          ["RozwojPlus", "2024-03-10", "2024-03-10"]]
    df = pd.DataFrame({"member_id": [1, 1, 1, 0], "data": ["2024-01-01", "2024-02-20", "2024-04-01", "2024-02-20"]})
    # przed pierwszą obserwacją -> pierwsza; potem ostatnia nie późniejsza; nie-poseł -> None
    assert club_on_date(df, obs).fillna("-").tolist() == ["PiS", "PiS", "RozwojPlus", "-"]


def test_blok():
    klub = pd.Series(["RozwojPlus", "WiS", None, "Centrum"])
    member = pd.Series([5, 6, 0, 7])
    assert blok(klub, member).fillna("-").tolist() == ["PiS", INNE, "-", "Polska 2050"]
