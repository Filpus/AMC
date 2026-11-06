"""Stage 5: relabel batches (dataset_prompt.md sections 6, 7a; borderline rules of section 2).

Contains all statements labelled `pewnosc = niska` in labels.jsonl plus 100 random `wysoka` ones (seed 2026). The
labellers are not told which is which; the 100 confident ones measure how far the new rules move earlier labels and
serve as the self-consistency check. Shuffled into batches of up to 20 statements or about 8,000 words, split into
three parts. Writes relabel_batches/part<N>/batch_NNN.jsonl (only wypowiedz_id and masked text) and
relabel_plan.csv (which statements were drawn and why; never shown to the labellers). Run from the project root (AMC).
"""
import json, random, sys
from pathlib import Path

import pandas as pd

D = Path("pipeline_development/topical_speech_detection/data")
OUT, PLAN = D / "relabel_batches", D / "relabel_plan.csv"
SEED, N_CHECK, PARTS, MAX_ITEMS, MAX_WORDS = 2026, 100, 3, 20, 8000
if PLAN.exists() or OUT.exists():
    sys.exit("relabel batches already exist; not redrawing")

lab = pd.read_json(D / "labels.jsonl", lines=True)
text = {}
for f in sorted((D / "batches").glob("batch_*.jsonl")):
    for line in f.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        text[r["wypowiedz_id"]] = r["tekst"]
assert len(lab) == 850 and set(lab.wypowiedz_id) == set(text)

rng = random.Random(SEED)
low = sorted(lab.loc[lab.pewnosc == "niska", "wypowiedz_id"])
high = sorted(lab.loc[lab.pewnosc == "wysoka", "wypowiedz_id"])
check = rng.sample(high, N_CHECK)
ids = low + check
rng.shuffle(ids)

batches, cur, words = [], [], 0
for i in ids:
    n = len(text[i].split())
    if cur and (len(cur) >= MAX_ITEMS or words + n > MAX_WORDS):
        batches.append(cur); cur, words = [], 0
    cur.append(i); words += n
batches.append(cur)

# Split batches into parts of roughly equal word counts, keeping batch order.
total = sum(len(text[i].split()) for i in ids)
plan, part, acc = [], 1, 0
for b_no, b in enumerate(batches, 1):
    w = sum(len(text[i].split()) for i in b)
    if part < PARTS and acc >= total * part / PARTS:
        part += 1
    acc += w
    p = OUT / f"part{part}"
    p.mkdir(parents=True, exist_ok=True)
    (p / f"batch_{b_no:03d}.jsonl").write_text(
        "".join(json.dumps({"wypowiedz_id": i, "tekst": text[i]}, ensure_ascii=False) + "\n" for i in b),
        encoding="utf-8")
    plan += [{"wypowiedz_id": i, "powod": "niska" if i in set(low) else "kontrola", "part": part,
              "batch": f"batch_{b_no:03d}"} for i in b]
pd.DataFrame(plan).to_csv(PLAN, index=False)
pl = pd.DataFrame(plan)
print(pl.groupby(["part", "powod"]).size().unstack().to_string())
print("batches", len(batches), "words", total)
for p in sorted(OUT.iterdir()):
    print(p.name, len(list(p.iterdir())), "batches",
          sum(len(text[i].split()) for i in pl[pl.part == int(p.name[4:])].wypowiedz_id), "words")
