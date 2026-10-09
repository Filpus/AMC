"""Stage A: LLM (Ollama) finds scientific claims in statements (logic: amc/llm.py).

Sources:
  gold    data/gold/sample_<version>.csv (run only after manual annotation, to keep it blind)
  filtr   random statements passing the regex prefilter (speed tests)
  rok     --n statements per year from the prefilter (analysis sample, weight = N / n)
With --bez-filtra, filtr and rok draw from all `merytoryczna` statements instead of the prefilter; with --plenarne only
from plenary sittings (no committees).

Output: data/processed/llm_<prompt>_<source>[_plenarne][_bez_filtra].jsonl, one line per statement. Reruns skip ids
done without error and retry failed ones (a retried id then has several lines: use the last one). Context overflow
counts as an error.
  --ponow        also rerun ids whose last line overflowed the context or filled a candidate limit lower than the current one
  --weryfikacja  only step 2 again (current verification prompt, with context) on stored candidates; appends updated lines
  --powtorka N   test-retest: N random done statements classified again into llm_<prompt>_<source>_powtorka.jsonl
For --source rok the sample (ids, year, weight) is also saved next to the output as <output>_n<N>_proba.csv. Samples
for different --n are nested (n=60 is a subset of n=100), so results stay valid; the analysis takes ids and weights from
that file. Statements are processed interleaved by year, so a run stopped early still covers every year.

Example:
  python src/classify.py --source filtr --n 10
  python src/classify.py --source rok --n 100
  python src/classify.py --source rok --n 100 --bez-filtra
  python src/classify.py --source rok --n 80 --plenarne
  python src/classify.py --source gold --version v1
  python src/classify.py --source rok --n 60 --ponow
  python src/classify.py --source rok --n 60 --weryfikacja
  python src/classify.py --source rok --n 60 --powtorka 60
"""
import argparse
import json
import logging
import statistics

import pandas as pd
import requests

from amc import corpus, llm, sampling
from amc.paths import PROCESSED, ROOT

log = logging.getLogger("classify")


def statements(source, n, seed, version, use_prefilter=True, kinds=corpus.RODZAJE):
    if source == "gold":
        return pd.read_csv(ROOT / "data" / "gold" / f"sample_{version}.csv", encoding="utf-8-sig")[["wypowiedz_id", "tekst"]]
    df = pd.concat([corpus.load(k) for k in kinds], ignore_index=True)
    df = df[df["merytoryczna"] & (sampling.prefilter(df) if use_prefilter else True)]
    if source == "filtr":
        return df.sample(n=min(n, len(df)), random_state=seed)[["wypowiedz_id", "tekst"]]
    df["rok"] = pd.to_datetime(df["data"]).dt.year
    size = df.groupby("rok").size()
    out = df.sample(frac=1, random_state=seed)
    out["_nr"] = out.groupby("rok").cumcount()
    # interleaved by year, so a run stopped early is still a sample from every year
    out = out[out["_nr"] < n].sort_values(["_nr", "rok"])
    out["waga"] = out["rok"].map(size / out.groupby("rok").size())
    return out[["wypowiedz_id", "tekst", "rok", "waga"]]


def last_lines(path):
    """Last result line per id, with legacy run settings filled in for lines written before they were recorded."""
    lines = [{**llm.LEGACY_SETTINGS, **json.loads(x)} for x in path.open(encoding="utf-8")] if path.exists() else []
    return {r["wypowiedz_id"]: r for r in lines}


def needs_rerun(r):
    """Failed, context overflow, or a candidate limit lower than the current one was filled (sentences may be missing)."""
    full = r["max_kandydatow"] < llm.MAX_CANDIDATES and len(r.get("kandydaci") or []) >= r["max_kandydatow"]
    return bool(r["blad"]) or llm.overflow(r.get("tokeny_we"), r.get("tokeny_wy"), r["num_ctx"]) is not None or full


def reverify(out, last, todo, model):
    texts = dict(zip(todo["wypowiedz_id"], todo["tekst"]))
    rows = [r for i, r in last.items() if i in texts and not r["blad"] and r.get("kandydaci") is not None
            and r["prompt_weryfikacji"] != llm.VERIFY_PROMPT]
    log.info("%d statements: step 2 again with %s -> %s", len(rows), llm.VERIFY_PROMPT, out)
    with out.open("a", encoding="utf-8") as f:
        for i, r in enumerate(rows, 1):
            try:
                new = llm.reverify(r, texts[r["wypowiedz_id"]], model)
            except requests.RequestException as e:
                log.warning("%s: %s", r["wypowiedz_id"], e)
                continue
            f.write(json.dumps(new, ensure_ascii=False) + "\n")
            f.flush()
            log.info("%d/%d %s: claims %d -> %d", i, len(rows), r["wypowiedz_id"], len(r["twierdzenia"]), len(new["twierdzenia"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["gold", "filtr", "rok"], required=True)
    ap.add_argument("--n", type=int, default=10, help="statements in total (filtr) or per year (rok)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--version", default="v1", help="gold sample version")
    ap.add_argument("--prompt", default="etap_a_v2")
    ap.add_argument("--model", default=llm.DEFAULT_MODEL)
    ap.add_argument("--bez-filtra", action="store_true", help="sample from all statements, not only the regex prefilter")
    ap.add_argument("--plenarne", action="store_true", help="sample only plenary statements (no committees)")
    ap.add_argument("--max-kandydatow", type=int, default=llm.MAX_CANDIDATES)
    ap.add_argument("--ponow", action="store_true", help="also rerun overflowed statements and those with a full candidate list")
    ap.add_argument("--weryfikacja", action="store_true", help="only step 2 again on stored candidates")
    ap.add_argument("--powtorka", type=int, default=0, help="test-retest on N random done statements")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    suffix = ("_plenarne" if a.plenarne else "") + ("_bez_filtra" if a.bez_filtra else "")
    out = PROCESSED / f"llm_{a.prompt}_{a.source}{suffix}.jsonl"
    last = last_lines(out)
    todo = statements(a.source, a.n, a.seed, a.version, not a.bez_filtra, ["plenarne"] if a.plenarne else corpus.RODZAJE)
    if a.source == "rok":
        todo[["wypowiedz_id", "rok", "waga"]].to_csv(out.with_name(f"{out.stem}_n{a.n}_proba.csv"), index=False)
    if a.weryfikacja:
        return reverify(out, last, todo, a.model)
    settings = {}
    if a.powtorka:
        ok = [i for i in todo["wypowiedz_id"] if i in last and not last[i]["blad"]]
        pick = set(pd.Series(ok).sample(min(a.powtorka, len(ok)), random_state=a.seed))
        # repeat each statement with the settings of its current result, so the comparison measures run-to-run variation only
        settings = {i: (last[i]["num_ctx"], last[i]["max_kandydatow"]) for i in pick}
        out = out.with_name(f"{out.stem}_powtorka.jsonl")
        done = {i for i, r in last_lines(out).items() if not r["blad"]}
        todo = todo[todo["wypowiedz_id"].isin(pick)]
    else:
        rerun = needs_rerun if a.ponow else (lambda r: bool(r["blad"]))
        done = {i for i, r in last.items() if not rerun(r)}
    todo = todo[~todo["wypowiedz_id"].isin(done)]
    log.info("%d statements to classify (%d already done) -> %s", len(todo), len(done), out)

    secs = []
    with out.open("a", encoding="utf-8") as f:
        for i, row in enumerate(todo.to_dict("records"), 1):
            sid, text = row.pop("wypowiedz_id"), row.pop("tekst")
            num_ctx, max_cand = settings.get(sid, (llm.NUM_CTX, a.max_kandydatow))
            system, schema = llm.load_prompt(a.prompt, max_cand), llm.schema_for(max_cand)
            try:
                ans = llm.classify(text, system, a.model, schema, num_ctx=num_ctx)
            except requests.RequestException as e:
                ans = {"zawiera_twierdzenie": None, "twierdzenia": [], "blad": f"{type(e).__name__}: {e}", "sekundy": None}
            res = {"wypowiedz_id": sid, **row, "model": a.model, "prompt": a.prompt, "max_kandydatow": max_cand, **ans}
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            if res["sekundy"]:
                secs.append(res["sekundy"])
            log.info("%d/%d %s: %s claims, %ss%s", i, len(todo), sid, len(res["twierdzenia"]), res["sekundy"],
                     f" ERROR {res['blad'][:120]}" if res["blad"] else "")
    if secs:
        log.info("median %.1fs per statement; 19 417 filtered statements ~ %.1f h",
                 statistics.median(secs), statistics.median(secs) * 19417 / 3600)


if __name__ == "__main__":
    main()
