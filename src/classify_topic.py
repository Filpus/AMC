"""Topic classification: is climate a thread of the statement? Local LLM via Ollama, prompt prompts/<prompt>.md.

Input: the study population (amc/population.select: MPs' substantive plenary statements in the study period), with
speaker names masked as for the annotators. Statements go in one fixed random order (--seed), so `--n N` is always the
same N statements, nested across N and identical for every model, and a run stopped early is a random sample.

Output: data/processed/topic/<prompt>__<model>.jsonl, one line per statement: klimat (0/1), fragment (the sentence the
model points to), fragment_w_tekscie (share of the fragment found verbatim in the text), seconds, tokens, error,
komputer (host name, as results from different machines may differ slightly).
Reruns skip ids done without error, so an interrupted run just continues.
  --testy     label-free checks from data/tests/topic.csv (codebook examples, full statements behind the prompt
              examples, minimal pairs) -> <prompt>__<model>__tests.jsonl
  --ids FILE  only statements listed in a CSV with a wypowiedz_id column (e.g. the gold sample)
  --podsumuj  compares every model run with the prompt: share of klimat = 1, agreement, time, test results

Examples:
  python src/classify_topic.py --testy
  python src/classify_topic.py --n 200 --model gemma4:12b
  python src/classify_topic.py --ids data/gold/sample.csv
  python src/classify_topic.py                       # whole population (~44 thousand statements)
  python src/classify_topic.py --podsumuj
"""
import argparse
import itertools
import logging
import statistics
import time

import pandas as pd
import requests

from amc import corpus, llm, runs
from amc import text as T
from amc.llm_results import cohen_kappa
from amc.paths import PROCESSED, ROOT

log = logging.getLogger("classify_topic")

STEP = "topic"
OUT_DIR = PROCESSED / STEP
TESTS = ROOT / "data" / "tests" / "topic.csv"


def tests():
    t = pd.read_csv(TESTS, dtype=str, keep_default_na=False)
    texts = corpus.load("plenarne").set_index("wypowiedz_id")["tekst"]
    t["tekst"] = [x or T.mask_speakers(texts[i]) for x, i in zip(t["tekst"], t["wypowiedz_id"])]
    return t.rename(columns={"wypowiedz_id": "zrodlo", "test": "wypowiedz_id"})


def run(todo, path, prompt, model, num_ctx):
    system = llm.load_topic_prompt(prompt)
    path.parent.mkdir(parents=True, exist_ok=True)
    secs, t0 = [], time.perf_counter()
    with path.open("a", encoding="utf-8") as f:
        for i, row in enumerate(todo.to_dict("records"), 1):
            try:
                ans = llm.classify_topic(row["tekst"], system, model, num_ctx)
            except requests.RequestException as e:
                ans = {"klimat": None, "blad": f"{type(e).__name__}: {e}", "sekundy": None}
            extra = {k: row[k] for k in ("regula", "oczekiwane", "zrodlo") if k in row}
            res = {"wypowiedz_id": row["wypowiedz_id"], "model": model, "prompt": prompt, "komputer": runs.HOST,
                   **extra, **ans}
            runs.append(f, res)
            if res["sekundy"]:
                secs.append(res["sekundy"])
            if res["blad"] or res["klimat"] or i % 50 == 0 or i == len(todo):
                left = (time.perf_counter() - t0) / i * (len(todo) - i) / 3600
                log.info("%d/%d %s: klimat=%s %ss (left ~%.1f h)%s", i, len(todo), row["wypowiedz_id"], res["klimat"],
                         res["sekundy"], left, f" ERROR {res['blad'][:150]}" if res["blad"] else "")
    if secs:
        log.info("median %.2fs per statement", statistics.median(secs))


def summarize(prompt):
    results = {p.stem.split("__")[1]: pd.DataFrame(runs.last_lines(p).values())
               for p in sorted(OUT_DIR.glob(f"{prompt}__*.jsonl")) if not p.stem.endswith("__tests")}
    for name, d in results.items():
        ok = d[d["blad"].isna()]
        frag = ok[ok["fragment_w_tekscie"].notna()]
        print(f"\n{name}: {len(d)} statements, errors {len(d) - len(ok)}, klimat=1 {int(ok['klimat'].sum())} "
              f"({ok['klimat'].mean():.1%}), median {ok['sekundy'].median():.2f}s, "
              f"fragment not verbatim (< 0.8) {int((frag['fragment_w_tekscie'] < 0.8).sum())}/{len(frag)}")
    for (a, da), (b, db) in itertools.combinations(results.items(), 2):
        m = da.dropna(subset=["klimat"]).merge(db.dropna(subset=["klimat"]), on="wypowiedz_id", suffixes=("_a", "_b"))
        if len(m):
            print(f"\n{a} vs {b}: {len(m)} common, agreement {(m['klimat_a'] == m['klimat_b']).mean():.1%}, "
                  f"kappa {cohen_kappa(m['klimat_a'], m['klimat_b']):.2f}, klimat=1: {int(m['klimat_a'].sum())} vs "
                  f"{int(m['klimat_b'].sum())}")
    for p in sorted(OUT_DIR.glob(f"{prompt}__*__tests.jsonl")):
        d = pd.DataFrame(runs.last_lines(p).values())
        d["ok"] = d["klimat"].astype("Int64").astype(str) == d["oczekiwane"].astype(str)
        print(f"\ntests {p.stem.split('__')[1]}: {int(d['ok'].sum())}/{len(d)} as expected")
        print(d.groupby("regula")["ok"].agg(["sum", "count"]).to_string())
        for r in d[~d["ok"]].to_dict("records"):
            print(f"  WRONG {r['wypowiedz_id']} ({r['regula']}): expected {r['oczekiwane']}, got {r['klimat']}; "
                  f"fragment: {r.get('fragment')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default="topic_v0")
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--n", type=int, help="only the first N statements of the fixed random order")
    ap.add_argument("--ids", help="CSV with a wypowiedz_id column: only these statements")
    ap.add_argument("--testy", action="store_true", help="label-free checks from data/tests/topic.csv")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--num-ctx", type=int, default=llm.TOPIC_NUM_CTX)
    ap.add_argument("--podsumuj", action="store_true", help="summary of all runs with this prompt")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    if a.podsumuj:
        return summarize(a.prompt)

    if a.testy:
        todo, out = tests(), runs.out_path(STEP, a.prompt, a.model, "__tests")
    else:
        todo, out = runs.shuffled_population(a.seed, log), runs.out_path(STEP, a.prompt, a.model)
        if a.ids:
            todo = todo[todo["wypowiedz_id"].isin(set(pd.read_csv(a.ids, encoding="utf-8-sig")["wypowiedz_id"]))]
        if a.n:
            todo = todo.head(a.n)
    done = runs.done(out)
    todo = todo[~todo["wypowiedz_id"].isin(done)]
    log.info("%d statements to classify (%d already done) with %s -> %s", len(todo), len(done), a.model, out)
    run(todo, out, a.prompt, a.model, a.num_ctx)


if __name__ == "__main__":
    main()
