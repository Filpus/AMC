"""Fine-tune HerBERT for the climate-topic decision (`klimat`) with cross-fitting by sitting.

Run with the Laya environment (it has torch, transformers, pandas, scikit-learn), from the project root (AMC):

    pipeline_development/topical_speech_detection/laya/.venv/bin/python \
        pipeline_development/topical_speech_detection/herbert/finetune_herbert.py --name v1

Input: data/dataset.csv, as for Laya. Folds are the same as in laya/finetune_laya.py (StratifiedGroupKFold by sitting,
same seed and row order), so the two models can be compared statement by statement. Synthetic statements are
training data in every fold. Hyperparameters are fixed in advance; the held-out fold is used only for predictions, not
for early stopping, and nothing is tuned on the gold sample.

HerBERT reads at most 512 tokens (about 330 words), so statements are split into word windows (`--window` words,
stride half a window). Training: for `klimat = 1` the window containing the deciding `fragment` (one paragraph is
enough, codebook section 3); for `klimat = 0` up to `--neg-windows` random windows, all negative. Prediction:
P(klimat = 1) of a statement is the maximum over its windows.

Output in herbert/runs/<name>/:
- final/: the model in Hugging Face format (AutoModelForSequenceClassification + tokenizer), ready for
  `push_to_hub` or `from_pretrained`;
- fold_<k>/: fold models only with --keep-folds (by default they are deleted after predicting their fold);
- oof_predictions.csv: cross-fitted P(klimat = 1) for every real statement;
- run.json: settings, fold sizes, training losses and agreement with the dataset labels.
"""
import argparse, json, math, random, shutil, sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "dataset.csv"


def windows(text: str, size: int) -> list:
    words = text.split()
    step = max(size // 2, 1)
    starts = range(0, max(len(words) - size, 0) + 1, step)
    out = [" ".join(words[s:s + size]) for s in starts]
    if len(words) > size and (len(words) - size) % step:
        out.append(" ".join(words[-size:]))  # cover the tail
    return out or [""]


def training_windows(df: pd.DataFrame, size: int, neg_windows: int, rng: random.Random) -> tuple:
    texts, labels, no_fragment = [], [], 0
    for t, k, frag in zip(df.tekst, df.klimat, df.fragment.fillna("")):
        ws = windows(t, size)
        if k == 1:
            key = " ".join(str(frag).split()[:8])
            hit = [w for w in ws if key and key in w]
            if not hit:
                no_fragment += 1
            texts.append((hit or ws)[0]); labels.append(1)
        else:
            for w in rng.sample(ws, min(neg_windows, len(ws))):
                texts.append(w); labels.append(0)
    return texts, labels, no_fragment


def train(texts, labels, a, device):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    tok = AutoTokenizer.from_pretrained(a.base)
    model = AutoModelForSequenceClassification.from_pretrained(
        a.base, num_labels=2, id2label={0: "nie", 1: "klimat"}, label2id={"nie": 0, "klimat": 1}).to(device)
    model.gradient_checkpointing_enable()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    steps = math.ceil(len(texts) / (a.micro_batch * a.grad_accum)) * a.epochs
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
    g = torch.Generator().manual_seed(a.seed)
    losses = []
    model.train()
    for epoch in range(a.epochs):
        order = torch.randperm(len(texts), generator=g).tolist()
        total, n = 0.0, 0
        for i, s in enumerate(range(0, len(order), a.micro_batch)):
            idx = order[s:s + a.micro_batch]
            enc = tok([texts[j] for j in idx], truncation=True, max_length=512, padding=True,
                      return_tensors="pt").to(device)
            y = torch.tensor([labels[j] for j in idx], device=device)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = model(**enc, labels=y).loss / a.grad_accum
            loss.backward()
            total, n = total + loss.item() * a.grad_accum * len(idx), n + len(idx)
            if (i + 1) % a.grad_accum == 0 or s + a.micro_batch >= len(order):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step(); sched.step(); opt.zero_grad()
        losses.append(total / n)
        print(f"epoch {epoch + 1}/{a.epochs} mean loss {total / n:.4f}", flush=True)
    model.eval()
    return model, tok, losses


@torch.no_grad()
def predict(model, tok, texts, size, device, batch=32) -> np.ndarray:
    out = []
    for t in texts:
        ws, p = windows(t, size), []
        for s in range(0, len(ws), batch):
            enc = tok(ws[s:s + batch], truncation=True, max_length=512, padding=True, return_tensors="pt").to(device)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                p += torch.softmax(model(**enc).logits.float(), -1)[:, 1].tolist()
        out.append(max(p))
    return np.array(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="run name (folder in herbert/runs/)")
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--base", default="allegro/herbert-large-cased")
    ap.add_argument("--folds", type=int, default=5, help="0 = only the final model (no cross-fitting)")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--micro-batch", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=2)
    ap.add_argument("--window", type=int, default=300, help="window length in words (about 450 HerBERT tokens)")
    ap.add_argument("--neg-windows", type=int, default=3, help="training windows per negative statement")
    ap.add_argument("--keep-folds", action="store_true", help="keep fold models (about 1.4 GB each)")
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()

    out = HERE / "runs" / a.name
    if out.exists():
        sys.exit(f"{out} exists; choose another --name")
    random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
    device = "cuda"
    df = pd.read_csv(a.data)
    assert df.wypowiedz_id.is_unique and df.klimat.isin([0, 1]).all()
    real, syn = df[df.zrodlo == "realna"], df[df.zrodlo == "syntetyczna"]
    run = {"args": vars(a), "n_real": len(real), "n_synthetic": len(syn), "folds": []}

    def fit(frame):
        texts, labels, no_frag = training_windows(frame, a.window, a.neg_windows, random.Random(a.seed))
        model, tok, losses = train(texts, labels, a, device)
        return model, tok, {"windows": len(texts), "positive_windows": int(sum(labels)),
                            "positives_without_fragment_match": no_frag, "epoch_loss": losses}

    if a.folds and len(real):
        from sklearn.model_selection import StratifiedGroupKFold

        groups = real.kadencja.astype(int).astype(str) + "_" + real.posiedzenie.astype(int).astype(str)
        cv = StratifiedGroupKFold(n_splits=a.folds, shuffle=True, random_state=a.seed)
        oof = pd.Series(np.nan, index=real.index)
        fold_of = pd.Series(0, index=real.index)
        for k, (tr, te) in enumerate(cv.split(real, real.klimat, groups), 1):
            train_df, held = pd.concat([real.iloc[tr], syn]), real.iloc[te]
            model, tok, info = fit(train_df)
            oof.iloc[te] = predict(model, tok, held.tekst.tolist(), a.window, device)
            fold_of.iloc[te] = k
            if a.keep_folds:
                model.save_pretrained(out / f"fold_{k}"); tok.save_pretrained(out / f"fold_{k}")
            del model; torch.cuda.empty_cache()
            run["folds"].append({"fold": k, "train": len(train_df), "held_out": len(held),
                                 "held_out_positive": int(held.klimat.sum()), **info})
        pred = real[["wypowiedz_id", "klimat"]].assign(fold=fold_of, p_klimat=oof)
        out.mkdir(parents=True, exist_ok=True)
        pred.to_csv(out / "oof_predictions.csv", index=False)
        y, hat = pred.klimat.to_numpy(), (pred.p_klimat.to_numpy() >= 0.5).astype(int)
        tp, fp, fn = int(((hat == 1) & (y == 1)).sum()), int(((hat == 1) & (y == 0)).sum()), int(((hat == 0) & (y == 1)).sum())
        run["oof_vs_silver_labels"] = {"accuracy": float((hat == y).mean()),
                                       "precision": tp / max(tp + fp, 1), "recall": tp / max(tp + fn, 1),
                                       "note": "against the LLM labels of the dataset, threshold 0.5; not the gold"}
    elif a.folds:
        print("no real statements: cross-fitting skipped, only the final model is trained", flush=True)

    model, tok, info = fit(df)
    model.save_pretrained(out / "final"); tok.save_pretrained(out / "final")
    run["final"] = {"train": len(df), **info}
    (out / "run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"done: {out}", flush=True)


if __name__ == "__main__":
    main()
