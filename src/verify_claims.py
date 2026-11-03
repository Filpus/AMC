"""Verdict of every claim against AR6 (prompt prompts/<prompt>.md, index from build_ar6.py).

For each claim the AR6 index returns the best fragments from the SPMs and from the TSs, and the model gives a verdict
(sprzeczne / zgodne / brak_podstaw) pointing to the deciding fragment. Retrieval (--wyszukiwanie): `en` embedding of the
English paraphrase (default), `pl` of the Polish one, `bm25` on the English one, `rrf` all three merged (the frozen
run); --embedding picks the embedding model (its index: build_ar6.py --model). Input:
data/processed/claims/<claims prompt>__<claims model>.jsonl. Output:
data/processed/verdicts/<prompt>__<model><variant>.jsonl (variant: __en, __pl, __bm25, __en_<embedding model>...;
none for rrf with bge-m3), one line per claim (twierdzenie_id = <wypowiedz_id>#<nr>). Reruns skip claims done without
error.
  --testy     claims with an expected verdict from data/tests/verdict.csv -> <...><variant>__tests.jsonl
  --ids FILE  claims of `extract_claims.py --ids FILE` (the same FILE); results get the same suffix

Example:
  python src/verify_claims.py
  python src/verify_claims.py --wyszukiwanie pl
  python src/verify_claims.py --wyszukiwanie en --embedding qwen3-embedding:8b
  python src/verify_claims.py --wyszukiwanie rrf --testy      # the frozen run's retrieval
  python src/verify_claims.py --ids data/gold/sample.csv
"""
import argparse
import logging
import statistics
from pathlib import Path

import pandas as pd
import requests

from amc import ar6, llm, runs
from amc.paths import ROOT

log = logging.getLogger("verify_claims")
STEP = "verdicts"
TESTS = ROOT / "data" / "tests" / "verdict.csv"


def claims(path):
    out = []
    for wid, r in runs.last_lines(path).items():
        if r["blad"]:
            continue
        out += [{"twierdzenie_id": f"{wid}#{c['nr']}", "wypowiedz_id": wid, **c} for c in r["twierdzenia"]]
    return out


def tests():
    t = pd.read_csv(TESTS, dtype=str, keep_default_na=False)
    return [{"twierdzenie_id": r["test"], "wypowiedz_id": "", "nr": 0, **r}
            for r in t.to_dict("records")]


def report(path):
    """Tests as expected among the lines without an error; lines with an error (e.g. written by an older version of the
    step) are listed apart, the next --testy run redoes them."""
    d = pd.DataFrame(runs.last_lines(path, "twierdzenie_id").values())
    d = d[d["oczekiwane"] != ""]
    failed = d["blad"].notna()
    ok = ~failed & (d["werdykt"] == d["oczekiwane"])
    log.info("tests: %d/%d as expected%s", ok.sum(), (~failed).sum(),
             f", {failed.sum()} with an error (run --testy again)" if failed.any() else "")
    for r in d[failed].to_dict("records"):
        log.info("  ERROR %s: %s", r["twierdzenie_id"], r["blad"][:150])
    for r in d[~failed & ~ok].to_dict("records"):
        said = r.get("werdykt_bez_ar6")
        log.info("  WRONG %s: expected %s, got %s (%s)%s", r["twierdzenie_id"], r["oczekiwane"], r["werdykt"], r["ar6"],
                 f"; the model said {said} without a fragment" if pd.notna(said) else "")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default="verdict_v1")
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--twierdzenia-prompt", default="claims_v1")
    ap.add_argument("--twierdzenia-model", help="model whose claims to judge (default: --model)")
    ap.add_argument("--na-czesc", type=int, default=3, help="fragments from the SPMs and from the TSs each")
    ap.add_argument("--num-ctx", type=int, default=llm.VERDICT_NUM_CTX)
    ap.add_argument("--testy", action="store_true", help="claims with expected verdicts from data/tests/verdict.csv")
    ap.add_argument("--ids", help="the CSV given to extract_claims.py --ids")
    runs.add_retrieval_args(ap)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    suffix = f"__{Path(a.ids).stem}" if a.ids else ""
    source = runs.out_path("claims", a.twierdzenia_prompt, a.twierdzenia_model or a.model, suffix)
    out = runs.verdicts_path(a.prompt, a.model, a.wyszukiwanie, a.embedding, "__tests" if a.testy else suffix)
    done = runs.done(out, "twierdzenie_id")
    todo = [c for c in (tests() if a.testy else claims(source)) if c["twierdzenie_id"] not in done]
    log.info("%d claims to judge from %s -> %s (retrieval %s%s)", len(todo), TESTS.name if a.testy else source.name,
             out, a.wyszukiwanie, "" if a.wyszukiwanie == "bm25" else f", {a.embedding}")
    if not todo:
        return report(out) if a.testy else None
    index = ar6.Index(model=a.embedding, method=a.wyszukiwanie)
    texts = [ar6.query_texts(a.wyszukiwanie, c["twierdzenie"], c["twierdzenie_en"]) for c in todo]
    vectors = (ar6.embed([q for t in texts for q in t], a.embedding, query=True).reshape(len(todo), len(texts[0]), -1)
               if texts[0] else [None] * len(todo))
    prompt = llm.load_topic_prompt(a.prompt)
    out.parent.mkdir(parents=True, exist_ok=True)
    secs = []
    with out.open("a", encoding="utf-8") as f:
        for i, (c, qv) in enumerate(zip(todo, vectors), 1):
            frags = index.search(c["twierdzenie"], c["twierdzenie_en"], a.na_czesc, query_vectors=qv)
            try:
                ans = llm.judge_claim(c, frags.to_dict("records"), prompt, a.model, a.num_ctx)
            except requests.RequestException as e:
                ans = {"werdykt": None, "blad": f"{type(e).__name__}: {e}", "sekundy": None}
            row = {k: c[k] for k in ("twierdzenie_id", "wypowiedz_id", "nr", "twierdzenie", "twierdzenie_en", "oczekiwane")
                   if k in c}
            runs.append(f, {**row, "model": a.model, "prompt": a.prompt, "twierdzenia_z": source.name,
                            "wyszukiwanie": a.wyszukiwanie, "embedding": None if a.wyszukiwanie == "bm25" else a.embedding,
                            "komputer": runs.HOST, **ans})
            secs += [ans["sekundy"]] if ans["sekundy"] else []
            log.info("%d/%d %s: %s %s%s", i, len(todo), c["twierdzenie_id"], ans["werdykt"], ans.get("ar6") or "",
                     f" ERROR {ans['blad'][:150]}" if ans["blad"] else "")
    if secs:
        log.info("median %.1fs per claim", statistics.median(secs))
    if a.testy:
        report(out)


if __name__ == "__main__":
    main()
