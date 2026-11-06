"""Zero-shot Clef-Flash on the silver dataset for the climate-topic decision (`klimat`).

Run with the Laya environment (it has torch, transformers, pandas), from the project root (AMC):

    pipeline_development/topical_speech_detection/laya/.venv/bin/python \
        pipeline_development/topical_speech_detection/clef_flash/eval_clef_flash.py --name v1

The model (Cloudflare/clef-flash, 9B, BF16, Apache-2.0) is downloaded on the first run into the Hugging Face cache
(~/.cache/huggingface, about 18 GB); HF_TOKEN is read from clef_flash/.env or laya/.env if set. Nothing is trained:
every real statement of data/dataset.csv is unseen, so no folds are needed. The question is fixed before the run:
`--question laya` is the short question Laya is trained with (laya/finetune_laya.py), `--question codebook` gives the
model section 3 of docs/codebook.md (definition, test, include and exclude lists). Do not reword either after seeing
the results without a held-out half of the silver.

Long statements are scored in token windows (`--window` tokens, half-window overlap) and P(klimat = 1) of a statement
is the maximum over its windows (one climate paragraph is enough, codebook section 3). Predictions are appended after
every statement, so an interrupted run resumes where it stopped.

Output in clef_flash/runs/<name>/:
- predictions.csv: wypowiedz_id, klimat (silver), gemma_klimat, p_klimat, windows, tokens;
- run.json: settings, model revision and the comparison with Gemma (recall, precision, AUC, threshold at Gemma's
  recall, known misses of Gemma in stratum 3).
"""
import argparse, json, os, sys
from pathlib import Path

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "dataset.csv"
sys.path.insert(0, str(HERE.parent / "laya"))
from finetune_laya import QID, QUESTION  # same question as Laya

YES = "A"  # criteria: A = tak, B = nie
CODEBOOK = HERE.parents[2] / "docs" / "codebook.md"


def codebook_question() -> dict:
    """The question with the full definition of section 3 of the codebook (definition, test, include and exclude
    lists) as instructions, read from docs/codebook.md, so the model gets the same rules as the gold annotators."""
    text = CODEBOOK.read_text(encoding="utf-8")
    sec = text[text.index("## 3. "):text.index("**Warstwy próby**")]
    sec = sec.split("\n", 1)[1].replace("`", "").strip()
    return {"type": "choice",
            "instructions": "Czy klimat jest jednym z wątków tej wypowiedzi sejmowej? Oceń według definicji:\n\n" + sec,
            "criteria": {"A": "tak, klimat = 1 według definicji", "B": "nie, klimat = 0 według definicji"}}


QUESTIONS = {"laya": lambda: QUESTION, "codebook": codebook_question}


def load_token() -> None:
    for env in (HERE / ".env", HERE.parent / "laya" / ".env"):
        if "HF_TOKEN" in os.environ or not env.exists():
            continue
        for line in env.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "HF_TOKEN" and v.strip():
                os.environ["HF_TOKEN"] = v.strip().strip("'\"")


def windows(tok, text: str, size: int) -> list:
    """Text pieces of at most `size` tokens with half-window overlap (character spans from token offsets)."""
    off = tok(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    if len(off) <= size:
        return [text]
    step, out = size // 2, []
    for s in range(0, len(off), step):
        e = min(s + size, len(off))
        out.append(text[off[s][0]:off[e - 1][1]])
        if e == len(off):
            break
    return out


def metrics(y: np.ndarray, p: np.ndarray, gemma: np.ndarray) -> dict:
    def at(hat):
        tp, fp, fn = int((hat & (y == 1)).sum()), int((hat & (y == 0)).sum()), int((~hat & (y == 1)).sum())
        return {"recall": tp / max(tp + fn, 1), "precision": tp / max(tp + fp, 1), "flagged": int(hat.sum())}

    pos, neg = y == 1, y == 0
    if not pos.any() or not neg.any():
        return {"n": int(len(y)), "note": "need both classes for the comparison (smoke test?)"}
    r = pd.Series(p).rank().to_numpy()  # AUC = Mann-Whitney
    auc = (r[pos].sum() - pos.sum() * (pos.sum() + 1) / 2) / (pos.sum() * neg.sum())
    g = at(gemma == 1)
    thr = float(np.sort(p[pos])[int(np.floor((1 - g["recall"]) * pos.sum()))])  # same recall as Gemma
    s3 = gemma == 0
    return {"n": int(len(y)), "positive": int(pos.sum()), "auc": float(auc), "gemma": g,
            "thresholds": {str(t): at(p >= t) for t in (0.5, 0.3, 0.1, 0.05, 0.02)},
            "at_gemma_recall": {"threshold": thr, **at(p >= thr)},
            "stratum3_misses": {str(t): {"caught": int(((p >= t) & s3 & pos).sum()), "of": int((s3 & pos).sum()),
                                         "false_flags": int(((p >= t) & s3 & neg).sum()), "negatives": int((s3 & neg).sum())}
                                for t in (0.5, 0.1, thr)},
            "note": "silver labels (Opus), not the gold; silver is enriched with Gemma positives"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="run name (folder in clef_flash/runs/)")
    ap.add_argument("--model", default="Cloudflare/clef-flash", help="Hub id or local folder")
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--question", choices=list(QUESTIONS), default="laya",
                    help="laya: the short question Laya is trained with; codebook: section 3 of docs/codebook.md")
    ap.add_argument("--window", type=int, default=6000, help="state tokens per window")
    ap.add_argument("--limit", type=int, default=0, help="score only the first N statements (smoke test)")
    a = ap.parse_args()

    import torch
    from huggingface_hub import snapshot_download

    load_token()
    path = Path(a.model) if Path(a.model).is_dir() else Path(snapshot_download(a.model))
    sys.path.insert(0, str(path))
    from joint_schema_model import collate_records, encode_record, load_release_model

    out = HERE / "runs" / a.name
    out.mkdir(parents=True, exist_ok=True)
    pred_path = out / "predictions.csv"
    df = pd.read_csv(a.data)
    df = df[df.zrodlo == "realna"].reset_index(drop=True)
    if a.limit:
        df = df.head(a.limit)
    done = set(pd.read_csv(pred_path).wypowiedz_id) if pred_path.exists() else set()

    # Text-only records never touch the processor (joint_schema_model._encode_media returns early without images or
    # videos), but loading the full processor needs torchvision for its video part. Load only the tokenizer instead.
    import transformers

    class TokenizerOnly:
        @staticmethod
        def from_pretrained(p, **kw):
            return type("Processor", (), {"tokenizer": transformers.AutoTokenizer.from_pretrained(p, **kw)})()

    transformers.AutoProcessor = TokenizerOnly
    model, processor = load_release_model(str(path), device="cuda")
    tok, dev = processor.tokenizer, torch.device("cuda")
    question = QUESTIONS[a.question]()
    questions = {QID: question}
    with torch.inference_mode():
        for i, r in df[~df.wypowiedz_id.isin(done)].iterrows():
            pieces, best = windows(tok, r.tekst, a.window), 0.0
            for piece in pieces:
                enc = encode_record(tok, {"id": r.wypowiedz_id, "state": piece, "questions": questions},
                                    max_length=a.window + 1024)
                logits = model(collate_records([enc], tok.pad_token_id, dev))[0][0]
                probs = dict(zip(enc.questions[0].option_ids, logits.float().softmax(-1).tolist()))
                best = max(best, probs[YES])
            row = pd.DataFrame([{"wypowiedz_id": r.wypowiedz_id, "klimat": r.klimat, "gemma_klimat": r.gemma_klimat,
                                 "p_klimat": best, "windows": len(pieces),
                                 "tokens": len(tok(r.tekst, add_special_tokens=False)["input_ids"])}])
            row.to_csv(pred_path, mode="a", header=not pred_path.exists(), index=False)
            if (i + 1) % 50 == 0:
                print(f"scored {i + 1} / {len(df)}", flush=True)

    pred = pd.read_csv(pred_path)
    pred = pred[pred.wypowiedz_id.isin(df.wypowiedz_id)]
    run = {"args": vars(a), "model_path": str(path), "revision": path.name, "question": question,
           "comparison": metrics(pred.klimat.to_numpy(), pred.p_klimat.to_numpy(), pred.gemma_klimat.to_numpy())}
    (out / "run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(run["comparison"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
