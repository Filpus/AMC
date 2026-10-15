"""Exploration sample (stage A, notebooks 02-03): dictionary prefilter, analysis periods and hypothesis windows."""
import numpy as np
import pandas as pd

from . import topics

PERIOD_BREAKS = (pd.Timestamp("2020-01-24"), pd.Timestamp("2022-11-30"))
PERIODS = ("przed_covid", "covid", "po_chatgpt")
# hypothesis windows from the exploration card supplement (both ends inclusive)
WINDOWS = {"A": (pd.Timestamp("2022-04-17"), pd.Timestamp("2023-07-16")),
           "B": (pd.Timestamp("2023-11-13"), pd.Timestamp("2025-02-17"))}
HIT_COLS = [*topics.TOPICS, "nauka", "sceptycyzm"]


def prefilter(df):
    return df[HIT_COLS].gt(0).any(axis=1)


def period(dates):
    d = pd.to_datetime(dates)
    return pd.Series(np.select([d < PERIOD_BREAKS[0], d < PERIOD_BREAKS[1]], PERIODS[:2], PERIODS[2]), index=d.index)


def window(dates):
    """Window label (A / B), missing outside both windows."""
    d = pd.to_datetime(dates)
    out = pd.Series(np.nan, index=d.index, dtype=object)
    for k, (a, b) in WINDOWS.items():
        out[d.between(a, b)] = k
    return out

