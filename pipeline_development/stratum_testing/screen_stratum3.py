"""Second topic screen on stratum 3 (model: not about climate): how would 3a / 3b look?

Run with the Laya environment, from the project root (AMC):

    pipeline_development/topical_speech_detection/laya/.venv/bin/python \
        pipeline_development/stratum_testing/screen_stratum3.py

Stratum 3 = statements with `klimat = 0` in the frozen run labels (data/processed/labels/gemma4_12b.csv). Each one gets
P(klimat = 1) from the fine-tuned Laya model. Statements from the Laya training set get their cross-fitted
(out-of-fold) probability instead, so no statement is scored by a model that saw it. Two regexes are added as
alternative or extra screens. Predictions are cached per chunk, so an interrupted run resumes where it stopped.

Output in stratum_testing/out/:
- laya_p_stratum3.csv: wypowiedz_id, grupa, p_klimat, source (final / oof), regex flags;
- summary.md: 3a / 3b sizes per group for each screen and threshold, how many known misses of the run model (silver
  positives in stratum 3) each screen catches, and where the current stratum-3 gold statements fall.

The gold sample is not used to choose anything: it is only located in 3a / 3b.
"""
import argparse, re, sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
AMC = HERE.parents[1]
TSD = AMC / "pipeline_development" / "topical_speech_detection"
sys.path.insert(0, str(TSD / "laya"))
from finetune_laya import QID, QUESTION  # same question as in training

LABELS = AMC / "data" / "processed" / "labels" / "gemma4_12b.csv"
CORPUS = AMC / "data" / "processed" / "korpus_plenarne.parquet"
GOLD = AMC / "data" / "gold" / "sample.csv"
DATASET = TSD / "data" / "dataset.csv"

REGEX = {
    # phrases that name climate or climate policy directly
    "regex_strict": r"zmian\w* klimat|klimatyczn|emisj|\bets\d?\b|cieplarnian|dekarboniz|ocieplen|zielon\w* ład|fit for",
    # anything with the word "klimat" or emissions / renewables vocabulary
    "regex_broad": r"klimat|emisj|\bets\d?\b|cieplarnian|dekarboniz|ocieplen|\boze\b|odnawialn|zielon\w* ład|fit for",
}
THRESHOLDS = (0.5, 0.3, 0.1)


def score(model_dir: Path, texts: pd.Series, cache: Path, max_len: int, batch_size: int, chunk: int) -> pd.Series:
    """P(klimat = 1) per text, cached in `cache` after every chunk; long texts are scanned in windows."""
    import laya

    done = pd.read_csv(cache, index_col=0).p_klimat if cache.exists() else pd.Series(dtype=float)
    todo = texts.drop(done.index, errors="ignore")
    if todo.empty:
        return done
    agent = laya.load(str(model_dir), device="cuda")
    n_tok = todo.map(lambda t: len(agent.tok(t, add_special_tokens=False)["input_ids"])).sort_values()
    todo = todo[n_tok.index]  # similar lengths per batch
    for s in range(0, len(todo), chunk):
        part, out = todo.iloc[s:s + chunk], {}
        short = [i for i in part.index if n_tok[i] <= max_len]
        for i, r in zip(short, agent.predict_batch(part[short].tolist(), {QID: QUESTION}, batch_size=batch_size)):
            out[i] = r.get("answers", r)[QID]["probabilities"]["A"]
        for i in (i for i in part.index if n_tok[i] > max_len):
            r = agent.predict_long(part[i], {QID: QUESTION}, batch_size=batch_size)
            out[i] = r.get("answers", r)[QID]["probabilities"]["A"]
        done = pd.concat([done, pd.Series(out, dtype=float)])
        done.rename("p_klimat").to_csv(cache)
        print(f"scored {len(done)} / {len(texts)}", flush=True)
    return done


def summary(d: pd.DataFrame) -> str:
    screens = {"regex_strict": d.regex_strict, "regex_broad": d.regex_broad}
    for t in THRESHOLDS:
        screens[f"laya ≥ {t}"] = d.p_klimat >= t
        screens[f"laya ≥ {t} lub regex_strict"] = (d.p_klimat >= t) | d.regex_strict
    miss = d.silver == 1
    n3 = d.groupby("grupa").size()
    lines = ["# Warstwa 3: drugi klasyfikator", "",
             f"Warstwa 3 (model: nietematyczna): prawica {n3.get('prawica', 0)}, reszta {n3.get('reszta', 0)}.",
             f"Znane przeoczenia modelu (silver: klimat = 1 w warstwie 3): {int(miss.sum())}; "
             f"silver: klimat = 0 w warstwie 3: {int((d.silver == 0).sum())}. "
             "Dla nich Laya daje prawdopodobieństwo z cross-fittingu.",
             f"Gold w warstwie 3: {int(d.gold.sum())} wypowiedzi.", "",
             "| Drugi klasyfikator | 3a prawica | 3a reszta | 3b prawica | 3b reszta | złapane przeoczenia (silver 1) "
             "| fałszywe trafienia (silver 0) | gold w 3a |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, f in screens.items():
        a = d[f].groupby("grupa").size().reindex(n3.index, fill_value=0)
        lines.append(f"| {name} | {a.get('prawica', 0)} | {a.get('reszta', 0)} | "
                     f"{n3.get('prawica', 0) - a.get('prawica', 0)} | {n3.get('reszta', 0) - a.get('reszta', 0)} | "
                     f"{int((f & miss).sum())} / {int(miss.sum())} | {int((f & (d.silver == 0)).sum())} / "
                     f"{int((d.silver == 0).sum())} | {int((f & d.gold).sum())} / {int(d.gold.sum())} |")
    lines += ["", "Silver w warstwie 3 pochodzi z pul wzbogaconych (B–D), więc odsetek fałszywych trafień na silver jest "
              "zawyżony względem całej warstwy; rozmiar 3a z tabeli jest właściwą miarą."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=str(TSD / "laya" / "runs" / "v2"), help="Laya run folder (final/ + oof_predictions.csv)")
    ap.add_argument("--max-len", type=int, default=2048)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=2000, help="statements per cached chunk")
    ap.add_argument("--limit", type=int, default=0, help="score only the first N statements (smoke test)")
    a = ap.parse_args()
    run, out = Path(a.run), HERE / "out"
    out.mkdir(exist_ok=True)

    lab = pd.read_csv(LABELS, usecols=["wypowiedz_id", "grupa", "klimat"])
    s3 = lab[lab.klimat == 0].drop(columns="klimat")
    text = pd.read_parquet(CORPUS, columns=["wypowiedz_id", "tekst"])
    d = s3.merge(text, on="wypowiedz_id", how="left").set_index("wypowiedz_id")
    assert d.tekst.notna().all(), "stratum-3 statements missing from the corpus"
    if a.limit:
        d = d.head(a.limit)

    ds = pd.read_csv(DATASET, usecols=["wypowiedz_id", "zrodlo", "klimat"])
    ds = ds[ds.zrodlo == "realna"].set_index("wypowiedz_id").klimat
    oof = pd.read_csv(run / "oof_predictions.csv").set_index("wypowiedz_id").p_klimat
    d["silver"] = ds.reindex(d.index)
    d["gold"] = d.index.isin(pd.read_csv(GOLD).query("warstwa == 3").wypowiedz_id)

    in_train = d.index.isin(oof.index)
    p_final = score(run / "final", d.tekst[~in_train], out / f"cache_{run.name}.csv", a.max_len, a.batch_size, a.chunk)
    d["p_klimat"] = oof.reindex(d.index).where(in_train, p_final.reindex(d.index))
    d["source"] = np.where(in_train, "oof", "final")
    for k, rx in REGEX.items():
        d[k] = d.tekst.str.contains(re.compile(rx, re.I))

    d.drop(columns="tekst").to_csv(out / "laya_p_stratum3.csv")
    (out / "summary.md").write_text(summary(d), encoding="utf-8")
    print((out / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
