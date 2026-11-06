"""Stage 6: assemble the dataset (dataset_prompt.md section 8).

Real statements: stage 4 labels (labels.jsonl); the statements marked `pewnosc = niska` take their stage 5 relabel
(relabel_part1-3.jsonl, borderline rules of section 2). The 100 hidden confident checks keep their stage 4 label
(98/100 agreed on `klimat`). Extra columns keep the stage 4 label and whether the two passes agreed, so variants
(drop disagreements, soft labels) can be built later without relabelling.
Synthetic statements: intended labels; the blind labeller agreed on `klimat` for all 150.

Writes dataset.csv, review_sample.csv (50 real statements stratified by category, for a human check),
review_low_confidence.csv and summary.md. Run from the project root (AMC).
"""
import json
from pathlib import Path

import pandas as pd

D = Path("pipeline_development/topical_speech_detection/data")
SEED = 2026
COLUMNS = ["wypowiedz_id", "zrodlo", "para_id", "typ_pary", "pula", "kadencja", "posiedzenie", "data", "grupa",
           "gemma_klimat", "hits", "tekst", "liczba_slow", "klimat", "kategoria", "blind_kategoria", "fragment",
           "uzasadnienie", "pewnosc", "odniesienie_do_innego_mowcy", "relabel", "klimat_etap4", "kategoria_etap4",
           "zgodnosc_relabel"]
md = lambda df: "```\n" + df.to_string() + "\n```"
LABEL_FIELDS = ["klimat", "kategoria", "fragment", "uzasadnienie", "pewnosc", "odniesienie_do_innego_mowcy"]

# --- real statements
first = pd.read_json(D / "labels.jsonl", lines=True).set_index("wypowiedz_id")
second = pd.concat(pd.read_json(D / f"relabel_part{i}.jsonl", lines=True) for i in (1, 2, 3)).set_index("wypowiedz_id")
plan = pd.read_csv(D / "relabel_plan.csv").set_index("wypowiedz_id")
cand = pd.read_csv(D / "candidates.csv").set_index("wypowiedz_id")
text = {}
for f in sorted((D / "batches").glob("batch_*.jsonl")):
    for line in f.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        text[r["wypowiedz_id"]] = r["tekst"]
assert len(first) == 850 and set(first.index) == set(cand.index) == set(text)
assert set(second.index) == set(plan.index) and second.index.is_unique

low = plan.index[plan.powod == "niska"]
real = first[LABEL_FIELDS].copy()
real["klimat_etap4"], real["kategoria_etap4"] = first.klimat, first.kategoria
real.loc[low, LABEL_FIELDS] = second.loc[low, LABEL_FIELDS]
real["relabel"] = real.index.isin(low)
real["zgodnosc_relabel"] = pd.Series(pd.NA, index=real.index, dtype="boolean")
real.loc[low, "zgodnosc_relabel"] = (first.loc[low, "klimat"] == second.loc[low, "klimat"]).to_numpy()
real = real.join(cand[["pula", "hits", "grupa", "gemma_klimat", "kadencja", "posiedzenie", "data", "liczba_slow"]])
real["tekst"] = [text[i] for i in real.index]
real["zrodlo"] = "realna"
real = real.reset_index()
assert all(f in t for f, t, k in zip(real.fragment, real.tekst, real.klimat) if k == 1), "fragment not verbatim"
assert ((real.kategoria.str[0] == "P") == (real.klimat == 1)).all()

# --- synthetic statements
syn = pd.read_json(D / "synthetic.jsonl", lines=True)
assert len(syn) == 150 and (syn.klimat == syn.blind_klimat).all(), "blind check not passed"
syn = syn.assign(zrodlo="syntetyczna", liczba_slow=syn.tekst.str.split().str.len())

ds = pd.concat([real.reindex(columns=COLUMNS), syn.reindex(columns=COLUMNS)], ignore_index=True)
assert len(ds) == 1000 and ds.wypowiedz_id.is_unique
ds.to_csv(D / "dataset.csv", index=False)

# --- review files (human check; nothing is marked as reviewed)
rv = pd.concat(g.sample(min(len(g), max(1, round(50 * len(g) / len(real)))), random_state=SEED)
               for _, g in real.groupby("kategoria"))
rv = rv.sample(min(50, len(rv)), random_state=SEED)
cols = ["wypowiedz_id", "klimat", "kategoria", "fragment", "uzasadnienie", "pewnosc", "tekst"]
rv[cols].assign(ocena_czlowieka="").to_csv(D / "review_sample.csv", index=False)
real.loc[real.pewnosc == "niska", cols + ["relabel", "zgodnosc_relabel"]].to_csv(
    D / "review_low_confidence.csv", index=False)

# --- summary
hb = real.hits.clip(upper=3).astype(str).str.replace("3", "3+")
lines = ["# Dataset summary", "",
         f"Items: {len(ds)} ({len(real)} real, {len(syn)} synthetic). Seed {SEED}.", "",
         "## klimat by source", "", pd.crosstab(ds.zrodlo, ds.klimat, margins=True).pipe(md), "",
         "## Real statements: klimat by pool and dictionary hits", "",
         pd.crosstab([real.pula, hb.rename("hits")], real.klimat, margins=True).pipe(md), "",
         "## Categories (real / synthetic)", "",
         pd.crosstab(ds.kategoria, ds.zrodlo, margins=True).pipe(md), "",
         "## Labelling passes (real)", "",
         f"- Stage 4: 850 statements, 5 parallel Opus labellers; {int((first.pewnosc == 'niska').sum())} marked "
         "`niska`.",
         f"- Stage 5: the {len(low)} `niska` statements relabelled by 3 fresh Opus labellers under the borderline "
         f"rules; `klimat` agreed with stage 4 for {int(real.zgodnosc_relabel.sum())} / {len(low)}; the relabel "
         "is used.",
         f"- Hidden checks: 100 stage-4 `wysoka` statements relabelled blind; `klimat` agreed for "
         f"{int((first.loc[plan.index[plan.powod == 'kontrola'], 'klimat'] == second.loc[plan.index[plan.powod == 'kontrola'], 'klimat']).sum())}"
         " / 100; their stage 4 labels are kept.",
         f"- `pewnosc = niska` in the final labels: {int((real.pewnosc == 'niska').sum())}.",
         f"- `odniesienie_do_innego_mowcy = 1`: {int(real.odniesienie_do_innego_mowcy.sum())} real statements; the "
         "flag follows the stricter section 3 rule only for relabelled statements.",
         "- Synthetic: 75 minimal pairs, blind check agreed on `klimat` for 150 / 150; categories follow the old P4 "
         "rule (`blind_kategoria` holds the blind labeller's).", "",
         "## Exclusion check", "",
         "- None of the 100 gold ids or 3 prompt-test ids is in the dataset (checked in `select_candidates.py`).", "",
         "## Length (words)", "", ds.groupby("zrodlo").liczba_slow.describe().round(0).pipe(md), ""]
(D / "summary.md").write_text("\n".join(lines), encoding="utf-8")
print(pd.crosstab(ds.zrodlo, ds.klimat, margins=True).to_string())
print("review_sample", len(rv), "low confidence", int((real.pewnosc == "niska").sum()))
