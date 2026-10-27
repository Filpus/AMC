"""Stage 3: exclusions, masking, candidate selection (850, seed 2026) and batching (dataset_prompt.md sections 4-6).

Writes data/candidates.csv (pool, hits, grupa, gemma_klimat, batch) and data/batches/batch_NNN.jsonl with only
`wypowiedz_id` and the masked `tekst`. Run from the project root (AMC). Refuses to overwrite existing outputs.
"""
import json, re, sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from amc.text import mask_speakers  # same masking as the pipeline (dataset_prompt.md section 1)

D = Path("pipeline_development/topical_speech_detection/data")
CAND, BATCHES = D / "candidates.csv", D / "batches"
SEED, MAX_ITEMS, MAX_WORDS = 2026, 20, 8000
if CAND.exists() or (BATCHES.exists() and any(BATCHES.iterdir())):
    sys.exit("candidates.csv or batches/ already exist; candidates are never redrawn")

GOLD = """10_11_2024-05-08_134 10_36_2025-06-11_274 10_26_2025-01-09_139 10_22_2024-11-27_91 10_1_2023-12-06_19
10_16_2024-07-24_252 10_22_2024-11-27_98 10_62_2026-07-16_240 10_55_2026-04-16_30 10_34_2025-05-08_217
10_10_2024-04-26_103 10_26_2025-01-08_107 10_26_2025-01-08_7 10_22_2024-11-27_151 10_42_2025-10-08_216
10_28_2025-02-05_27 10_26_2025-01-08_201 10_28_2025-02-05_15 10_26_2025-01-08_6 10_36_2025-06-03_81
10_41_2025-09-24_361 10_18_2024-10-01_16 10_8_2024-03-20_61 10_6_2024-02-22_106 10_35_2025-05-20_278
10_13_2024-06-13_117 10_18_2024-09-26_287 10_24_2024-12-06_71 10_13_2024-06-13_6 10_25_2024-12-18_14
10_22_2024-11-21_225 10_63_2026-07-29_239 10_45_2025-11-21_149 10_26_2025-01-08_205 10_28_2025-02-05_20
10_29_2025-02-21_94 10_27_2025-01-22_106 10_55_2026-04-14_49 10_58_2026-05-29_31 10_25_2024-12-19_91
10_26_2025-01-08_196 10_33_2025-04-24_204 10_61_2026-07-02_265 10_38_2025-07-10_109 10_15_2024-07-11_170
10_11_2024-05-09_162 10_52_2026-02-26_31 10_32_2025-04-02_60 10_36_2025-06-03_50 10_40_2025-09-12_260
10_53_2026-03-11_215 10_53_2026-03-11_321 10_2_2024-01-17_2 10_26_2025-01-08_3 10_22_2024-11-20_246
10_5_2024-02-09_12 10_53_2026-03-11_304 10_17_2024-09-12_82 10_10_2024-04-26_160 10_48_2025-12-18_97
10_7_2024-03-08_51 10_48_2025-12-18_102 10_42_2025-10-08_228 10_41_2025-09-26_135 10_43_2025-10-15_272
10_1_2023-12-21_1 10_22_2024-11-22_166 10_8_2024-03-20_68 10_2_2024-01-16_72 10_36_2025-06-11_381
10_60_2026-06-18_385 10_12_2024-05-22_161 10_40_2025-09-12_286 10_54_2026-03-25_149 10_38_2025-07-09_138
10_45_2025-11-19_63 10_10_2024-04-26_133 10_19_2024-10-10_240 10_50_2026-01-21_105 10_22_2024-11-19_143
10_33_2025-04-24_211 10_39_2025-08-05_59 10_53_2026-03-11_305 10_19_2024-10-10_88 10_41_2025-09-24_318
10_29_2025-02-20_11 10_7_2024-03-07_46 10_58_2026-05-28_341 10_32_2025-04-04_32 10_44_2025-11-06_225
10_29_2025-02-21_163 10_44_2025-11-05_242 10_45_2025-11-21_53 10_18_2024-09-25_113 10_40_2025-09-10_73
10_64_2026-09-03_145 10_13_2024-06-14_24 10_8_2024-03-20_81 10_1_2023-11-22_36 10_58_2026-05-27_181""".split()
TESTS = ["10_10_2024-04-25_124", "10_18_2024-09-25_107", "10_60_2026-06-17_269"]
QUOTES = [  # section 2 examples, matched on their first ~60 characters
    "Zmiana klimatu powoduje, że pojawiające się opady są bardzo intensywne",
    "wydaje się zasadne, żeby w czasach wojennych i COVID-owych rynek handlu",
    "Lepiej, jak jest ciepło, i globalne ocieplenie jest korzystne, a nie",
    "Ponadto chodzi o klimat inwestycyjny. Koniunktura w przemyśle spadła",
    "Zmiany forsowane w pośpiechu przez Ministerstwo Klimatu i Środowiska",
    "Ministerstwo rolnictwa nastawione jest produkcję. To ostatnie, czego",
    "50 tys. Polek i Polaków rocznie umiera z powodu smogu",
    "Projekt ustawy ma na celu przeprowadzenie procesu restrukturyzacji sektora",
]
assert len(set(GOLD)) == 100

ADJACENT = re.compile(r"ceny? (energii|prądu)|smog\w*|powod\w*|susz\w*|ministerstw\w* klimatu"
                      r"|klimat\w* (polityczn|inwestycyjn|społeczn|debat)|kopal\w*|górnik\w*|elektrown\w*"
                      r"|fotowolta\w*|wiatrak\w*|\boze\b|\blas\w*|odpad\w*", re.I)




lab = pd.read_csv("data/processed/labels/gemma4_12b.csv",
                  usecols=["wypowiedz_id", "grupa", "klimat", "slownik_klimat"])
lab = lab.rename(columns={"klimat": "gemma_klimat", "slownik_klimat": "hits"})
kor = pd.read_parquet("data/processed/korpus_plenarne.parquet",
                      columns=["wypowiedz_id", "kadencja", "posiedzenie", "data", "liczba_slow", "tekst"])
df = lab.merge(kor, on="wypowiedz_id", how="left", validate="1:1")
assert df.tekst.notna().all() and len(df) == 43991 and (df.kadencja == 10).all()

n0 = len(df)
excl_quote = df.tekst.apply(lambda t: any(q in t for q in QUOTES))
df = df[~df.wypowiedz_id.isin(GOLD + TESTS) & ~excl_quote].copy()
print(f"population {n0}; excluded {n0 - len(df)} (quotes matched: {int(excl_quote.sum())}); remaining {len(df)}")
df["tekst"] = df.tekst.map(mask_speakers)
df = df.sort_values("wypowiedz_id").reset_index(drop=True)
rng = np.random.default_rng(SEED)


def draw(frame: pd.DataFrame, n: int) -> pd.DataFrame:
    n = min(n, len(frame))
    return frame.iloc[rng.choice(len(frame), size=n, replace=False)] if n else frame.iloc[:0]


# Pool A: Gemma positives, by hits bin and half per group (a short cell is filled from the other group).
a = df[df.gemma_klimat == 1].copy()
a["hbin"] = np.where(a.hits >= 3, "3+", a.hits.astype(str))
parts = []
for hb, n in {"0": 130, "1": 200, "2": 150, "3+": 170}.items():
    cell = a[a.hbin == hb]
    p, r = cell[cell.grupa == "prawica"], cell[cell.grupa == "reszta"]
    np_ = min(n // 2, len(p))
    nr = min(n - np_, len(r))
    np_ = min(n - nr, len(p))  # refill from prawica if reszta was short
    parts += [draw(p, np_), draw(r, nr)]
A = pd.concat(parts).assign(pula="A")
B = df[(df.gemma_klimat == 0) & (df.hits >= 1)].assign(pula="B")
rest = df[(df.gemma_klimat == 0) & (df.hits == 0)]
is_adj = rest.tekst.str.contains(ADJACENT)
C = draw(rest[is_adj], 70).assign(pula="C")
d_pool = rest[~is_adj].copy()
d_pool["tercyl"] = pd.qcut(d_pool.liczba_slow, 3, labels=False)
n_d = 850 - len(A) - len(B) - len(C)
D_ = pd.concat([draw(d_pool[d_pool.tercyl == t], n_d // 3 + (t < n_d % 3)) for t in range(3)]).assign(pula="D")
cand = pd.concat([A, B, C, D_.drop(columns="tercyl")])
assert len(cand) == 850 and cand.wypowiedz_id.is_unique
assert not cand.wypowiedz_id.isin(GOLD + TESTS).any()

# Shuffle and batch: up to 20 statements or about 8,000 words (a longer statement gets a batch of its own).
cand = cand.iloc[rng.permutation(len(cand))].reset_index(drop=True)
batch, cur_n, cur_w, b = [], 0, 0, 1
for w in cand.liczba_slow:
    if cur_n and (cur_n >= MAX_ITEMS or cur_w + w > MAX_WORDS):
        b, cur_n, cur_w = b + 1, 0, 0
    batch.append(f"batch_{b:03d}"); cur_n += 1; cur_w += w
cand["batch"] = batch

BATCHES.mkdir(exist_ok=True)
for name, g in cand.groupby("batch"):
    (BATCHES / f"{name}.jsonl").write_text(
        "".join(json.dumps({"wypowiedz_id": i, "tekst": t}, ensure_ascii=False) + "\n"
                for i, t in zip(g.wypowiedz_id, g.tekst)), encoding="utf-8")
cand[["wypowiedz_id", "pula", "hits", "grupa", "gemma_klimat", "kadencja", "posiedzenie", "data", "liczba_slow",
      "batch"]].to_csv(CAND, index=False)

print(cand.groupby(["pula", "gemma_klimat"]).size().to_string())
print(pd.crosstab(A.hbin, A.grupa).to_string())
print(f"batches {cand.batch.nunique()}; words {cand.liczba_slow.sum()}; "
      f"max batch words {cand.groupby('batch').liczba_slow.sum().max()}")
