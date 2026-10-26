"""Verdict of every claim against AR6 with PaperQA2 instead of the RAG of verify_claims.py.

PaperQA2 with its default settings (settings() lists the exceptions) splits the six AR6 PDFs (SPM and TS of WGI-WGIII,
data/ar6/pdf/) into chunks, retrieves chunks for the claim (--embedding in Ollama), summarises each against the claim and
answers with the QA prompt prompts/<prompt>.md (the rules of verdict_v1 with PaperQA citation keys). The answer starts
with the verdict; `ar6` lists the cited chunks ("WGI_SPM pages 8-9"), not finding numbers. sprzeczne / zgodne without a
cited chunk becomes brak_podstaw, as in verify_claims.py (`werdykt_bez_ar6` keeps the model's verdict). Input, output,
--testy and --ids as in verify_claims.py: data/processed/verdicts/<prompt>__<model>__<embedding model>.jsonl (no
embedding part for bge-m3, the earlier tests). The chunk index is cached in
data/ar6/paperqa_<embedding model>_<chunk chars>.pkl.

Example:
  python src/verify_claims_paperqa.py
  python src/verify_claims_paperqa.py --testy
  python src/verify_claims_paperqa.py --ids data/gold/sample.csv
"""
import argparse
import asyncio
import logging
import os
import pickle
import re
import statistics
import time
from pathlib import Path

from amc import ar6, llm, runs
from verify_claims import STEP, TESTS, claims, report, tests

log = logging.getLogger("verify_claims_paperqa")
OLLAMA = llm.OLLAMA.rsplit("/api", 1)[0]
QUESTION = ('Is the following claim supported or contradicted by the IPCC AR6 reports, or not addressed by them? '
            'Claim: "{en}" (Polish original: "{pl}")')
LABEL = re.compile(r"\b(sprzeczne|zgodne|brak[ _]podstaw)\b", re.IGNORECASE)


def parse_answer(answer, cited):
    """Verdict fields as in llm.judge_claim from the PaperQA answer and the names of the chunks it cites."""
    res = {"werdykt": None, "ar6": "; ".join(cited), "uzasadnienie": answer, "werdykt_bez_ar6": None, "blad": None}
    m = LABEL.search(answer or "")
    if m:
        res["werdykt"] = m.group(1).lower().replace(" ", "_")
    elif "cannot answer" in (answer or "").lower():
        res["werdykt"] = "brak_podstaw"
    else:
        res["blad"] = f"no verdict in the answer: {(answer or '')[:300]}"
    if res["werdykt"] not in (None, "brak_podstaw") and not cited:
        res["werdykt_bez_ar6"], res["werdykt"] = res["werdykt"], "brak_podstaw"
    return res


def settings(model, embedding, prompt, num_ctx):
    """PaperQA2 defaults except: local models in Ollama (no thinking), no metadata lookup on the internet, no figure
    descriptions, the codebook QA prompt."""
    from paperqa import Settings
    from paperqa.settings import ParsingSettings, PromptSettings

    name = f"ollama_chat/{model}"
    config = {"name": name, "model_list": [{"model_name": name, "litellm_params": {
        "model": name, "api_base": OLLAMA, "temperature": 0, "num_ctx": num_ctx, "reasoning_effort": "none"}}]}
    return Settings(llm=name, llm_config=config, summary_llm=name, summary_llm_config=config,
                    embedding=f"ollama/{embedding}", prompts=PromptSettings(qa=prompt),
                    parsing=ParsingSettings(use_doc_details=False, multimodal=False))


async def index(s, embedding):
    from paperqa import Docs

    cache = ar6.DIR / f"paperqa_{embedding}_{s.parsing.reader_config['chunk_chars']}.pkl"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    ar6.download()
    docs = Docs()
    for wg, part, url in ar6.SOURCES:
        title = "Summary for Policymakers" if part == "SPM" else "Technical Summary"
        await docs.aadd(ar6.pdf_path(url), citation=f"IPCC AR6 {wg} {title}", docname=f"{wg}_{part}", settings=s)
        log.info("indexed %s_%s", wg, part)
    cache.write_bytes(pickle.dumps(docs))
    return docs


async def judge(docs, claim, s):
    t0 = time.perf_counter()
    try:
        session = await docs.aquery(QUESTION.format(en=claim["twierdzenie_en"], pl=claim["twierdzenie"]), settings=s)
        names = {c.id: c.text.name for c in session.contexts}
        ans = {**parse_answer(session.answer, sorted(names[i] for i in session.used_contexts)),
               "fragmenty": [c.text.name for c in session.contexts]}
    except Exception as e:  # noqa: BLE001  (litellm and PaperQA raise many types; one claim must not stop the run)
        ans = {"werdykt": None, "blad": f"{type(e).__name__}: {e}"[:500]}
    return {**ans, "sekundy": round(time.perf_counter() - t0, 1)}


async def run(a):
    suffix = f"__{Path(a.ids).stem}" if a.ids else ""
    source = runs.out_path("claims", a.twierdzenia_prompt, a.twierdzenia_model or a.model, suffix)
    out = runs.verdicts_path(a.prompt, a.model, embedding=a.embedding, suffix="__tests" if a.testy else suffix)
    done = runs.done(out, "twierdzenie_id")
    todo = [c for c in (tests() if a.testy else claims(source)) if c["twierdzenie_id"] not in done]
    log.info("%d claims to judge from %s -> %s", len(todo), TESTS.name if a.testy else source.name, out)
    if not todo:
        return report(out) if a.testy else None
    s = settings(a.model, a.embedding, llm.load_prompt(a.prompt), a.num_ctx)
    docs = await index(s, a.embedding)
    out.parent.mkdir(parents=True, exist_ok=True)
    secs = []
    with out.open("a", encoding="utf-8") as f:
        for i, c in enumerate(todo, 1):
            ans = await judge(docs, c, s)
            row = {k: c[k] for k in ("twierdzenie_id", "wypowiedz_id", "nr", "twierdzenie", "twierdzenie_en", "oczekiwane")
                   if k in c}
            runs.append(f, {**row, "model": a.model, "prompt": a.prompt, "narzedzie": "paperqa", "embedding": a.embedding,
                            "twierdzenia_z": source.name, "komputer": runs.HOST, **ans})
            secs += [] if ans["blad"] else [ans["sekundy"]]
            log.info("%d/%d %s: %s %s%s", i, len(todo), c["twierdzenie_id"], ans["werdykt"], ans.get("ar6") or "",
                     f" ERROR {ans['blad'][:150]}" if ans["blad"] else "")
    if secs:
        log.info("median %.1fs per claim", statistics.median(secs))
    if a.testy:
        report(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=runs.PAPERQA_PROMPT, help="QA prompt (PaperQA variables only)")
    ap.add_argument("--model", default=llm.PIPELINE_MODEL, help="Ollama model for the summaries and the answer")
    ap.add_argument("--embedding", default=ar6.EMBED_MODEL, help="Ollama embedding model (bge-m3: the earlier tests)")
    ap.add_argument("--twierdzenia-prompt", default="claims_v1")
    ap.add_argument("--twierdzenia-model", help="model whose claims to judge (default: --model)")
    ap.add_argument("--num-ctx", type=int, default=llm.VERDICT_NUM_CTX)
    ap.add_argument("--testy", action="store_true", help="claims with expected verdicts from data/tests/verdict.csv")
    ap.add_argument("--ids", help="the CSV given to extract_claims.py --ids")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    for name in ("LiteLLM", "httpx", "paperqa"):
        logging.getLogger(name).setLevel(logging.WARNING)
    os.environ.setdefault("OLLAMA_API_BASE", OLLAMA)
    asyncio.run(run(a))


if __name__ == "__main__":
    main()
