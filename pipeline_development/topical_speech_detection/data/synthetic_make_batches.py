"""Stage 2 preparation: write blind-check batch files for the 150 synthetic items (seed 2026).

Each line of data/synthetic_batches/batch_NNN.jsonl holds only a neutral `wypowiedz_id` (B001-B150, in random order,
revealing neither the pair nor the version) and `tekst`. The two items of a pair never share a batch. One batch = up
to 20 items or about 8,000 words. The mapping neutral id -> synthetic id is in data/synthetic_blind_ids.csv, which the
labeller must not see. Run from the project root (AMC). Refuses to overwrite existing batch files.
"""
import csv, json, random, sys
from pathlib import Path

D = Path("pipeline_development/topical_speech_detection/data")
SRC, OUT, MAP = D / "synthetic.jsonl", D / "synthetic_batches", D / "synthetic_blind_ids.csv"
SEED, MAX_ITEMS, MAX_WORDS = 2026, 20, 8000

rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
assert len(rows) == 150 and len({r["wypowiedz_id"] for r in rows}) == 150, "stage 1 incomplete"
if OUT.exists() and any(OUT.iterdir()):
    sys.exit(f"{OUT} already contains files; not overwriting")
OUT.mkdir(exist_ok=True)

rng = random.Random(SEED)
rows.sort(key=lambda r: r["wypowiedz_id"])
rng.shuffle(rows)
neutral = [f"B{i:03d}" for i in range(1, 151)]
rng.shuffle(neutral)
for r, n in zip(rows, neutral):
    r["neutral"] = n
words = lambda r: len(r["tekst"].split())

# Greedy fill in shuffled order; an item whose twin is already in the current batch waits for the next one.
batches, cur, cur_words, pending = [], [], 0, list(rows)
while pending:
    pairs_in = {r["para_id"] for r in cur}
    pick = next((r for r in pending if r["para_id"] not in pairs_in and cur_words + words(r) <= MAX_WORDS), None)
    if pick is None or len(cur) >= MAX_ITEMS:
        batches.append(cur); cur, cur_words = [], 0
        continue
    pending.remove(pick); cur.append(pick); cur_words += words(pick)
batches.append(cur)

for b in batches:
    assert len({r["para_id"] for r in b}) == len(b), "pair halves in one batch"
for i, b in enumerate(batches, 1):
    p = OUT / f"batch_{i:03d}.jsonl"
    p.write_text("".join(json.dumps({"wypowiedz_id": r["neutral"], "tekst": r["tekst"]}, ensure_ascii=False) + "\n"
                         for r in b), encoding="utf-8")
    print(p.name, len(b), "items", sum(map(words, b)), "words")
with MAP.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["neutral_id", "wypowiedz_id", "batch"])
    for i, b in enumerate(batches, 1):
        for r in b:
            w.writerow([r["neutral"], r["wypowiedz_id"], f"batch_{i:03d}"])
