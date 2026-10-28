"""Assemble data/dataset.csv (dataset_prompt.md section 8).

Currently only the 150 synthetic items (stage 5 relabel of the real statements is pending). Columns that exist only for
real statements (pula, kadencja, posiedzenie, data, grupa, gemma_klimat, uzasadnienie, pewnosc) are left empty.
Synthetic labels are the intended ones; the blind labeller agreed on `klimat` for all 150 (checked here). Run from the
project root (AMC).
"""
from pathlib import Path

import pandas as pd

D = Path("pipeline_development/topical_speech_detection/data")
COLUMNS = ["wypowiedz_id", "zrodlo", "para_id", "typ_pary", "pula", "kadencja", "posiedzenie", "data", "grupa",
           "gemma_klimat", "tekst", "liczba_slow", "klimat", "kategoria", "blind_kategoria", "fragment", "uzasadnienie",
           "pewnosc", "odniesienie_do_innego_mowcy"]

syn = pd.read_json(D / "synthetic.jsonl", lines=True)
assert len(syn) == 150 and syn.wypowiedz_id.is_unique
assert (syn.klimat == syn.blind_klimat).all(), "blind check not passed"
syn = syn.assign(zrodlo="syntetyczna", liczba_slow=syn.tekst.str.split().str.len())

out = syn.reindex(columns=COLUMNS)
out.to_csv(D / "dataset.csv", index=False)
print(len(out), out.klimat.value_counts().to_dict(), out.typ_pary.value_counts().to_dict())
