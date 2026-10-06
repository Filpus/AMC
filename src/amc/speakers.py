"""Mówcy: rola, dopasowanie posła, klub w dniu wypowiedzi, blok polityczny."""
import json
import re

import pandas as pd

ROLE = ["poseł", "prowadzący", "rząd", "inni"]


# ---------- rola mówcy ----------

def rola_plenarna(funkcja, mowca):
    """Rola mówcy na posiedzeniu plenarnym (z pola `funkcja` stenogramu).
    Blok marszałka (num 0, mowca "Marszałek") to prowadzący obrady."""
    f = (funkcja or "").lower()
    if mowca == "Marszałek" or "marszałek" in f:
        return "prowadzący"
    if re.search(r"minist|stanu|prezes rady|wiceprezes rady", f):
        return "rząd"
    if "poseł" in f:
        return "poseł"
    return "inni"


def rola_komisja(etykieta):
    """Rola mówcy na posiedzeniu komisji (z etykiety, np. "Przewodnicząca poseł Anna Nowak (KO)")."""
    e = etykieta.lower()
    if e.startswith("przewodnicząc") or "prowadząc" in e:
        return "prowadzący"
    if re.search(r"\bpos(eł|łanka)\b", e):
        return "poseł"
    if re.search(r"minist|stanu|prezes rady", e):
        return "rząd"
    return "inni"


# ---------- dopasowanie posła ----------

KLUB_W_ETYKIECIE = re.compile(r"[(/]\s*([^()/]{1,40}?)\s*[)/]")


class MpMatcher:
    """Dopasowuje etykietę mówcy do id posła z mp.json danej kadencji.

    Najpierw: etykieta (bez nawiasów i dopisków typu "– spoza składu Komisji") kończy się
    "Imię [Drugie] Nazwisko" posła. Zapasowo: imię i nazwisko występują w dowolnej kolejności (np. "Haidar Riad"),
    jeśli jednoznacznie. Inaczej 0 (osoba spoza Sejmu albo literówka w zapisie).
    """

    def __init__(self, mps):
        self.idx, self.osoby = {}, []
        for m in mps:
            self.idx[f"{m['firstName']} {m['lastName']}"] = m["id"]
            if m.get("secondName"):
                self.idx[f"{m['firstName']} {m['secondName']} {m['lastName']}"] = m["id"]
            self.osoby.append((m["id"], m["firstName"], m["lastName"]))
        self.names = sorted(self.idx, key=len, reverse=True)

    @classmethod
    def from_file(cls, path):
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def __call__(self, etykieta):
        e = re.sub(r"\([^)]*\)|/[^/]*/", " ", etykieta)
        e = re.split(r"\s[–-]\s", e)[0]
        e = re.sub(r"\s+", " ", e).strip()
        for n in self.names:
            if e.endswith(n):
                return self.idx[n]
        slowa = set(e.split())
        kand = {i for i, imie, nazw in self.osoby if imie in slowa and nazw in slowa}
        return kand.pop() if len(kand) == 1 else 0


def klub_z_etykiety(etykieta):
    """Klub podany w etykiecie posła: "(PiS)" albo "/PiS/"; None, gdy brak."""
    m = KLUB_W_ETYKIECIE.search(etykieta)
    return m.group(1) if m else None


# ---------- klub w dniu wypowiedzi ----------

def club_history(obs):
    """Zwija obserwacje (member_id, klub, data) — np. z list głosowań — do przedziałów członkostwa od–do."""
    df = obs.sort_values(["member_id", "data"]).copy()
    df["zmiana"] = (df["klub"] != df.groupby("member_id")["klub"].shift()).cumsum()
    return (df.groupby(["member_id", "zmiana", "klub"], as_index=False)
              .agg(od=("data", "min"), do=("data", "max"))
              .drop(columns="zmiana"))


def club_on_date(df, obs):
    """Klub posła w dniu wypowiedzi: ostatnia obserwacja nie późniejsza niż data wypowiedzi,
    a przed pierwszą obserwacją — pierwsza obserwacja. Zwraca Series zgodną z df.index (None dla nie-posłów).

    df:  kolumny member_id, data;  obs: kolumny member_id, data, klub (obserwacje albo początki przedziałów).
    """
    obs = obs.assign(_d=pd.to_datetime(obs["data"]))[["member_id", "_d", "klub"]].rename(columns={"klub": "_k"})
    obs = obs.sort_values("_d")
    posl = df[df["member_id"] > 0][["member_id", "data"]].assign(_d=lambda x: pd.to_datetime(x["data"])).sort_values("_d")
    if posl.empty:
        return pd.Series(None, index=df.index, dtype=object)
    back = pd.merge_asof(posl, obs, on="_d", by="member_id", direction="backward")
    fwd = pd.merge_asof(posl, obs, on="_d", by="member_id", direction="forward")
    back.index, fwd.index = posl.index, posl.index
    return back["_k"].fillna(fwd["_k"]).reindex(df.index)


def club_obs_from_history(path):
    """Obserwacje (member_id, data, klub) z pliku historii klubów data/interim/posel_klub_term{T}.csv."""
    hist = pd.read_csv(path)
    return hist.rename(columns={"od": "data"})[["member_id", "data", "klub"]]


# ---------- bloki polityczne ----------

# Nazwy klubów zmieniają się między kadencjami — łączymy je w bloki o ciągłej tożsamości.
# Rozłamy -> blok macierzysty, jeśli (prawie) wszyscy członkowie przyszli z jednego klubu.
# Małe koła o mieszanym rodowodzie (WiS, UED, ED, L-S, TERAZ!, Republikanie, Demokracja, Porozumienie, PS...) -> "Inne / niez.".
KLUB_BLOK = {
    # PiS; RozwojPlus = rozłam z klubu PiS w X kadencji (39 z 41 posłów przeszło z PiS)
    "PiS": "PiS", "RozwojPlus": "PiS",
    # KO; w VIII kadencji osobno PO i Nowoczesna (N), które weszły potem do KO
    "PO": "KO", "PO-KO": "KO", "KO": "KO", "N": "KO",
    "Lewica": "Lewica", "SLD": "Lewica", "LD": "Lewica", "PPS": "Lewica", "Razem": "Lewica", "Nowa_Lewica": "Lewica",
    "PSL": "PSL", "PSL-UED": "PSL", "PSL-KP": "PSL", "KP": "PSL", "PSL-Kukiz15": "PSL", "PSL-TD": "PSL",
    "Konfederacja": "Konfederacja", "Konfederacja_KP": "Konfederacja", "Wolnościowcy": "Konfederacja", "UPR": "Konfederacja",
    # Centrum = rozłam z Polski 2050 (wszyscy członkowie wcześniej w Polska2050)
    "Polska2050": "Polska 2050", "Polska2050-TD": "Polska 2050", "Centrum": "Polska 2050",
    "Kukiz15": "Kukiz'15",
}
INNE = "Inne / niez."
BLOKI = ["PiS", "KO", "Kukiz'15", "Polska 2050", "Lewica", "PSL", "Konfederacja", INNE]  # stała kolejność na wykresach


def blok(klub, member_id):
    """Blok polityczny dla serii klubów; posłowie z klubem spoza mapowania -> "Inne / niez.", nie-posłowie -> NaN."""
    b = klub.map(KLUB_BLOK)
    return b.mask(member_id.gt(0) & b.isna(), INNE)
