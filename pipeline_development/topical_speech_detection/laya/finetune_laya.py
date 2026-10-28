"""Fine-tune Laya for the climate-topic decision (`klimat`) with cross-fitting by sitting.

Run with the separate environment, from the project root (AMC):

    pipeline_development/topical_speech_detection/laya/.venv/bin/python \
        pipeline_development/topical_speech_detection/laya/finetune_laya.py --name v1

Input: data/dataset.csv (one row per statement: `tekst`, `klimat`, `zrodlo`, `kadencja`, `posiedzenie`, ...).
Real statements are split into folds by sitting (kadencja + posiedzenie), stratified by `klimat`; synthetic statements
are training data in every fold and never get a prediction. Each fold model predicts only its held-out statements
(cross-fitted labels), then a final model is trained on everything. Hyperparameters are fixed in advance: nothing is
tuned on the gold sample.

Output in laya/runs/<name>/:
- fold_<k>/ and final/: Laya checkpoints (model.safetensors, encoder/, tokenizer/, rl_agent_config.json,
  questions.json, train_report.json), loadable with `laya.load(path)`;
- oof_predictions.csv: cross-fitted P(klimat = 1) for every real statement;
- run.json: settings, fold sizes and metrics.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "dataset.csv"
QID = "klimat"
QUESTION = {
    "type": "choice",
    "instructions": ("Czy klimat jest jednym z wątków tej wypowiedzi sejmowej: czy mówca mówi coś o zmianie klimatu "
                     "(przyczyny, skutki, trendy, nauka) albo o polityce klimatycznej? Przelotna wzmianka, tło, "
                     "nazwa urzędu, epitet ani inne znaczenie słowa „klimat” nie wystarczają."),
    "criteria": {"A": "tak, klimat jest wątkiem wypowiedzi",
                 "B": "nie, klimat nie jest wątkiem wypowiedzi"},
}
LABEL = {1: "A", 0: "B"}


def rows(df: pd.DataFrame) -> list:
    return [{"state": t, "questions": {QID: QUESTION}, "expected": {QID: LABEL[int(k)]}}
            for t, k in zip(df.tekst, df.klimat)]


def write_jsonl(path: Path, df: pd.DataFrame) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows(df)), encoding="utf-8")
    return str(path)


def predict(model_dir: Path, texts: list, max_len: int, batch_size: int) -> np.ndarray:
    """P(klimat = 1) per text; texts longer than max_len are scanned in windows (predict_long)."""
    import laya

    agent = laya.load(str(model_dir), device="cuda")
    tok_len = [len(agent.tok(t, add_special_tokens=False)["input_ids"]) for t in texts]
    out = np.full(len(texts), np.nan)
    short = [i for i, n in enumerate(tok_len) if n <= max_len]
    res = agent.predict_batch([texts[i] for i in short], {QID: QUESTION}, batch_size=batch_size)
    for i, r in zip(short, res):
        out[i] = r.get("answers", r)[QID]["probabilities"]["A"]
    for i in (i for i, n in enumerate(tok_len) if n > max_len):
        r = agent.predict_long(texts[i], {QID: QUESTION}, batch_size=batch_size)
        out[i] = r.get("answers", r)[QID]["probabilities"]["A"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="run name (folder in laya/runs/)")
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--base", default="multilingual", help="Laya alias, Hub id or local checkpoint")
    ap.add_argument("--folds", type=int, default=5, help="0 = only the final model (no cross-fitting)")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=4096, help="token budget of the statement text")
    ap.add_argument("--micro-batch", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=32)
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()

    from laya.train import TrainConfig, finetune

    out = HERE / "runs" / a.name
    if out.exists():
        sys.exit(f"{out} exists; choose another --name")
    df = pd.read_csv(a.data)
    assert df.wypowiedz_id.is_unique and df.klimat.isin([0, 1]).all()
    real, syn = df[df.zrodlo == "realna"], df[df.zrodlo == "syntetyczna"]

    def config(eval_path=None) -> TrainConfig:
        return TrainConfig(epochs=a.epochs, micro_batch=a.micro_batch, grad_accum=a.grad_accum, max_len=a.max_len,
                           seed=a.seed, eval_data=eval_path)

    run = {"args": vars(a), "n_real": len(real), "n_synthetic": len(syn), "question": QUESTION, "folds": []}
    if a.folds and len(real):
        from sklearn.model_selection import StratifiedGroupKFold

        groups = real.kadencja.astype(int).astype(str) + "_" + real.posiedzenie.astype(int).astype(str)
        cv = StratifiedGroupKFold(n_splits=a.folds, shuffle=True, random_state=a.seed)
        oof = pd.Series(np.nan, index=real.index)
        fold_of = pd.Series(0, index=real.index)
        for k, (tr, te) in enumerate(cv.split(real, real.klimat, groups), 1):
            train, held = pd.concat([real.iloc[tr], syn]), real.iloc[te]
            d = out / f"fold_{k}"
            res = finetune(write_jsonl(d / "train.jsonl", train), a.base, str(d),
                           config(write_jsonl(d / "held_out.jsonl", held)))
            oof.iloc[te] = predict(d, held.tekst.tolist(), a.max_len, a.micro_batch * 4)
            fold_of.iloc[te] = k
            run["folds"].append({"fold": k, "train": len(train), "held_out": len(held),
                                 "held_out_positive": int(held.klimat.sum()), "report": res["train_report"]})
        pred = real[["wypowiedz_id", "klimat"]].assign(fold=fold_of, p_klimat=oof)
        pred.to_csv(out / "oof_predictions.csv", index=False)
        y, p = pred.klimat.to_numpy(), pred.p_klimat.to_numpy()
        hat = (p >= 0.5).astype(int)
        tp, fp, fn = int(((hat == 1) & (y == 1)).sum()), int(((hat == 1) & (y == 0)).sum()), int(((hat == 0) & (y == 1)).sum())
        run["oof_vs_silver_labels"] = {"accuracy": float((hat == y).mean()),
                                       "precision": tp / max(tp + fp, 1), "recall": tp / max(tp + fn, 1),
                                       "note": "against the LLM labels of the dataset, threshold 0.5; not the gold"}
    elif a.folds:
        print("no real statements: cross-fitting skipped, only the final model is trained", flush=True)

    d = out / "final"
    res = finetune(write_jsonl(d / "train.jsonl", df), a.base, str(d), config())
    run["final"] = {"train": len(df), "report": res["train_report"]}
    (out / "run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"done: {out}", flush=True)


if __name__ == "__main__":
    main()
