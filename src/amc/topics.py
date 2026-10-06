"""Słowniki tematyczne do wstępnego filtrowania wypowiedzi (EDA).

Każdy temat to lista wyrażeń regularnych dopasowywanych do tekstu zapisanego małymi literami.
Wzorce zaczynają się od granicy słowa (\\b) i kończą rdzeniem + \\w*, żeby łapać odmianę
(szczepionka, szczepionki, szczepionkami...). Słowniki są celowo nastawione na precyzję, nie
na pełność: lepiej przegapić część wypowiedzi niż zalać się fałszywymi trafieniami.
Przykłady trafień do ręcznej weryfikacji są w notatniku notebooks/01_eda_wypowiedzi.ipynb.

Progi:
  wzmianka              >= 1 trafienie słownika tematu
  wypowiedź tematyczna  >= PROG trafień (temat jest wyraźnym wątkiem, a nie przelotnym odniesieniem)
"""
import re

import pandas as pd

PROG = 3
# tematy zbiorcze: nazwa -> tematy składowe
GRUPY = {"zdrowie": ["szczepienia", "covid"]}

# Tematy, w których istnieje wyraźny konsensus naukowy (kandydaci na oś projektu).
TOPICS = {
    "szczepienia": [
        r"\bszczepi\w*", r"\bszczepion\w*", r"\bantyszczepion\w*", r"\bwakcyn\w*",
        r"\bodporno\w* zbiorow\w*", r"\bnop\b", r"\bniepożądan\w* odczyn\w*",
    ],
    "covid": [
        r"\bcovid\w*", r"\bkoronawirus\w*", r"\bsars-cov\w*", r"\bpandemi\w*",
        r"\blockdown\w*", r"\bmaseczk\w*", r"\bkwarantann\w*", r"\bepidemi\w* koronawirus\w*",
    ],
    "klimat": [
        r"\bzmian\w* klimat\w*", r"\bkryzys\w* klimat\w*", r"\bkatastrof\w* klimat\w*",
        r"\bocieplen\w* klimat\w*", r"\bglobaln\w* ocieplen\w*", r"\befekt\w* cieplarnian\w*",
        r"\bgaz\w* cieplarnian\w*", r"\bemisj\w* co2\b", r"\bemisj\w* dwutlenk\w*", r"\bdwutlenk\w* węgla\b",
        r"\bneutralno\w* klimatyczn\w*", r"\bpolityk\w* klimatyczn\w*", r"\bzielon\w* ład\w*",
        r"\bdekarbonizacj\w*", r"\bipcc\b", r"\bfit for 55\b", r"\bets\b", r"\bklimatyzm\w*",
    ],
    "energia_jadrowa": [
        r"\belektrown\w* jądrow\w*", r"\benergetyk\w* jądrow\w*", r"\benergi\w* jądrow\w*",
        r"\batomow\w*", r"\breaktor\w*", r"\bsmr\b",
    ],
    "gmo": [
        r"\bgmo\b", r"\bgenetycznie modyfikowan\w*", r"\bmodyfikowan\w* genetycznie\b", r"\btransgeniczn\w*",
    ],
    "5g_promieniowanie": [
        r"\b5g\b", r"\bpromieniowan\w* elektromagnetyczn\w*", r"\bpol\w* elektromagnetyczn\w*",
        r"\bpole elektromagnetyczne\b", r"\bnorm\w* promieniowan\w*",
    ],
    "smog": [
        r"\bsmog\w*", r"\bzanieczyszczen\w* powietrz\w*", r"\bjakoś\w* powietrz\w*",
        r"\bpył\w* zawieszon\w*", r"\bpm ?2[,.]5\b", r"\bpm ?10\b", r"\bkopciuch\w*",
    ],
    "in_vitro": [
        r"\bin vitro\b", r"\bzapłodnieni\w* pozaustrojow\w*", r"\bnaprotechnologi\w*",
    ],
}

# Odwołania do nauki / ekspertów — przekrojowy wskaźnik "czy mówca w ogóle powołuje się na naukę".
SCIENCE_REFS = [
    r"\bnaukowc\w*", r"\bnaukow\w* dowod\w*", r"\bdowod\w* naukow\w*", r"\bbada\w* naukow\w*",
    r"\bbadania (wykazały|pokazują|dowodzą|potwierdzają)", r"\bkonsensus\w* naukow\w*",
    r"\bświat\w* nauki\b", r"\bwedług (naukowców|ekspertów|badań)",
    r"\bwho\b", r"\bświatow\w* organizacj\w* zdrowia\b", r"\bpolsk\w* akademi\w* nauk\b",
]
# "PAN" (Polska Akademia Nauk) koliduje ze zwrotem "pan" — dlatego łapiemy tylko wersalikami, na oryginalnym tekście.
SCIENCE_REFS_CASED = [r"\bPAN\b"]

# Zwroty dystansujące / podważające naukę i ekspertów (marker potencjalnej sprzeczności z konsensusem).
SKEPTIC = [
    r"\brzekom\w* (pandemi|epidemi|zmian\w* klimat|ocieplen|szczepion|naukow|bezpieczn\w* szczepion)\w*", r"\btak zwan\w* (naukowc|eksperc|ekspert|pandemi|szczepion|zmian\w* klimat)\w*",
    r"\btzw\. (naukowc|eksperc|ekspert|pandemi|szczepion|zmian\w* klimat)\w*",
    r"\beksperyment\w* medyczn\w*", r"\beksperyment\w* na ludziach\b", r"\bpreparat\w* genetyczn\w*",
    r"\bsegregacj\w* sanitarn\w*", r"\bsanitaryzm\w*", r"\bplandemi\w*", r"\bcovidianizm\w*",
    r"\bklimatyzm\w*", r"\bklimatyczn\w* (religi|histeri|szaleństw|ideologi)\w*", r"\bekoterror\w*",
    r"\bterror\w* klimatyczn\w*", r"\bhisteri\w* (klimatyczn|covidow|pandemiczn)\w*",
    r"\bideologi\w* klimatyczn\w*", r"\bwielki\w* reset\w*", r"\bmit\w* klimatyczn\w*",
]


def _compile(patterns, flags=re.I):
    return re.compile("|".join(f"(?:{p})" for p in patterns), flags)


TOPIC_RE = {k: _compile(v) for k, v in TOPICS.items()}
SCIENCE_RE = _compile(SCIENCE_REFS)
SCIENCE_CASED_RE = re.compile("|".join(SCIENCE_REFS_CASED))
SKEPTIC_RE = _compile(SKEPTIC)


def flag_topics(texts):
    """Liczba trafień każdego tematu oraz markerów `nauka` i `sceptycyzm` dla serii tekstów."""
    low = texts.fillna("").str.lower()
    out = {k: low.str.count(r) for k, r in TOPIC_RE.items()}
    out["nauka"] = low.str.count(SCIENCE_RE) + texts.fillna("").str.count(SCIENCE_CASED_RE)
    out["sceptycyzm"] = low.str.count(SKEPTIC_RE)
    return pd.DataFrame(out, index=texts.index)


def add_topic_columns(df, text_col="tekst"):
    """Dokłada do df kolumny z liczbą trafień (<temat>, nauka, sceptycyzm), flagi wypowiedzi tematycznych
    (<temat>_tem: >= PROG trafień), tematy zbiorcze z GRUPY (<grupa>_tem, <grupa>_wzm) i dowolny_tem."""
    df = df.join(flag_topics(df[text_col]))
    for t in TOPICS:
        df[f"{t}_tem"] = df[t] >= PROG
    for g, sklad in GRUPY.items():
        df[f"{g}_tem"] = df[[f"{t}_tem" for t in sklad]].any(axis=1)
        df[f"{g}_wzm"] = (df[sklad] > 0).any(axis=1)
    df["dowolny_tem"] = df[[f"{t}_tem" for t in TOPICS]].any(axis=1)
    return df
