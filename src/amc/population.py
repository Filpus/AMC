"""Study population: substantive plenary statements of MPs (member_id > 0, including ministers who are MPs) in the study
period. Group = club on the day of the statement (`klub`): prawica (RIGHT_CLUBS) or reszta.
"""
import numpy as np
import pandas as pd

STUDY_PERIOD = (pd.Timestamp("2023-11-13"), pd.Timestamp("2026-09-15"))
RIGHT_CLUBS = ("PiS", "RozwojPlus", "Konfederacja", "Konfederacja_KP")


def select(df):
    """Statements of the study population with `grupa` (prawica / reszta)."""
    d = pd.to_datetime(df["data"])
    pop = df[df["merytoryczna"] & df["member_id"].gt(0) & d.between(*STUDY_PERIOD)].copy()
    pop["grupa"] = np.where(pop["klub"].isin(RIGHT_CLUBS), "prawica", "reszta")
    return pop
