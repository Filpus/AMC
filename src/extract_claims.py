"""Claims from the statements the topic classification marked `klimat = 1` (prompt prompts/<prompt>.md).

Input: data/processed/topic/<topic prompt>__<topic model>.jsonl (by default the same model). Output:
data/processed/claims/<prompt>__<model>.jsonl, one line per statement with the list `twierdzenia`: nr, cytat,
cytat_w_tekscie (share of the quote found verbatim), twierdzenie (the speaker's position), twierdzenie_en. Reruns skip
statements done without error.

Example:
  python src/extract_claims.py
  python src/extract_claims.py --model qwen3.5:9b
"""
import argparse
import logging
import statistics

import requests

from amc import llm, runs

log = logging.getLogger("extract_claims")
STEP = "claims"


def topical_ids(path):
    return [i for i, r in runs.last_lines(path).items() if not r["blad"] and r["klimat"] == 1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default="claims_v1")
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--klimat-prompt", default="topic_v0")
    ap.add_argument("--klimat-model", help="model whose topic classification to use (default: --model)")
    ap.add_argument("--num-ctx", type=int, default=llm.CLAIMS_NUM_CTX)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    source = runs.out_path("topic", a.klimat_prompt, a.klimat_model or a.model)
    ids = set(topical_ids(source))
    pop = runs.shuffled_population()
    out = runs.out_path(STEP, a.prompt, a.model)
    todo = pop[pop["wypowiedz_id"].isin(ids - runs.done(out))]
    log.info("%d statements with klimat = 1 in %s; %d to do -> %s", len(ids), source.name, len(todo), out)
    prompt = llm.load_topic_prompt(a.prompt)
    out.parent.mkdir(parents=True, exist_ok=True)
    secs = []
    with out.open("a", encoding="utf-8") as f:
        for i, row in enumerate(todo.to_dict("records"), 1):
            try:
                ans = llm.extract_claims(row["tekst"], prompt, a.model, a.num_ctx)
            except requests.RequestException as e:
                ans = {"twierdzenia": [], "blad": f"{type(e).__name__}: {e}", "sekundy": None}
            runs.append(f, {"wypowiedz_id": row["wypowiedz_id"], "model": a.model, "prompt": a.prompt,
                            "klimat_z": source.name, "komputer": runs.HOST, **ans})
            secs += [ans["sekundy"]] if ans["sekundy"] else []
            log.info("%d/%d %s: %d claims, %ss%s", i, len(todo), row["wypowiedz_id"], len(ans["twierdzenia"]),
                     ans["sekundy"], f" ERROR {ans['blad'][:150]}" if ans["blad"] else "")
    if secs:
        log.info("median %.1fs per statement", statistics.median(secs))


if __name__ == "__main__":
    main()
