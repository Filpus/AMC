"""The whole codebook pipeline for one model, step by step; every step resumes where it stopped.

  1. classify_topic.py    klimat + fragment for the population (or its first --n statements)
  2. build_ar6.py         AR6 index (fragments, embeddings of --embedding), only if it is missing (RAG only)
  3. extract_claims.py    claims from the statements with klimat = 1
  4. verify_claims.py     verdicts against AR6: RAG with --wyszukiwanie en (default) / pl / bm25 / rrf (the frozen
                          run) or, with --weryfikator paperqa, verify_claims_paperqa.py
  5. label_statements.py  statement labels and a raw summary by group

Example:
  python src/pipeline.py --n 200                       # quick test
  python src/pipeline.py                               # whole population (llm.PIPELINE_MODEL)
  python src/pipeline.py --n 200 --model qwen3.5:9b    # another model, the same statements
  python src/pipeline.py --wyszukiwanie bm25           # another retrieval; topic and claims are reused
  python src/pipeline.py --embedding qwen3-embedding:8b
  python src/pipeline.py --weryfikator paperqa         # verdicts by PaperQA2 instead of the RAG
"""
import argparse
import subprocess
import sys
from pathlib import Path

from amc import ar6, llm, runs

SRC = Path(__file__).resolve().parent


def step(script, *args):
    print(f"\n=== {script} {' '.join(args)}", flush=True)
    subprocess.run([sys.executable, str(SRC / script), *args], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--n", type=int, help="only the first N statements of the fixed random order (topic classification)")
    ap.add_argument("--weryfikator", choices=["rag", "paperqa"], default="rag", help="verdict step")
    runs.add_retrieval_args(ap)
    a = ap.parse_args()
    retrieval = ["--wyszukiwanie", a.wyszukiwanie, "--embedding", a.embedding]
    step("classify_topic.py", "--model", a.model, *(["--n", str(a.n)] if a.n else []))
    dense = a.wyszukiwanie != "bm25"
    if a.weryfikator == "rag" and not (ar6.FRAGMENTS.exists() and (not dense or ar6.embeddings_path(a.embedding).exists())):
        step("build_ar6.py", "--model", a.embedding)
    step("extract_claims.py", "--model", a.model)
    if a.weryfikator == "rag":
        step("verify_claims.py", "--model", a.model, *retrieval)
        verdict_prompt = runs.VERDICT_PROMPT
    else:
        step("verify_claims_paperqa.py", "--model", a.model, "--embedding", a.embedding)
        verdict_prompt = runs.PAPERQA_PROMPT
    step("label_statements.py", "--model", a.model, "--werdykt-prompt", verdict_prompt, *retrieval)


if __name__ == "__main__":
    main()
