"""Step 8: robustness of the step 6 test in the plan variants and the extensions (amc/robustness).

Input: data/processed/labels/<model>.csv (label_statements.py). Output in data/processed/results/:
<labels file name>_robustness.csv (one row per variant with beta1, 95% interval, model-label shares and the
criterion) and <labels file name>_loso.csv (leave-one-speaker-out); figure figures/<labels file name>_odpornosc.png.
The verdict counts only the plan variants (presentation, slide 12): same sign and 0.5-2 times beta1 of the main
result.

Examples:
  python src/robustness.py
  python src/robustness.py --werdykt-prompt paperqa_v0 --embedding embeddinggemma:300m   # labels from PaperQA2
"""
import argparse
import json

import matplotlib.pyplot as plt
import pandas as pd

from amc import llm, runs, viz
from amc import robustness as R
from amc.paths import PROCESSED, RAW
from amc.viz import ACCENT, AXIS, INK2, MUTED, SECOND

OUT = PROCESSED / "results"


def mp_names():
    """member_id -> "Imię Nazwisko" from data/raw/term10/mp.json (empty when missing)."""
    path = RAW / "term10" / "mp.json"
    if not path.exists():
        return {}
    return {m["id"]: m["firstLastName"] for m in json.loads(path.read_text(encoding="utf-8"))}


def forest(table, slug):
    """beta1 with the 95% interval per variant; band = robustness range [0.5; 2] x beta1 of the main result."""
    viz.setup()
    t = table.reset_index(drop=True)
    main = t.loc[t["rodzaj"] == "glowny", "beta1"].iloc[0]
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(t) + 1.6))
    ax.axvspan(R.LOW * main, R.HIGH * main, color=ACCENT, alpha=0.08, lw=0)
    ax.axvline(0, color=INK2, lw=1)
    ax.axvline(main, color=ACCENT, lw=1, ls="--")
    for i, r in t.iterrows():
        color = SECOND if r["rodzaj"] == "rozszerzenie" else ACCENT
        if pd.isna(r["beta1"]):
            ax.text(0, i, "  brak oszacowania (separacja)", va="center", fontsize=8, color=MUTED)
            continue
        ax.plot([r["ci_2.5"], r["ci_97.5"]], [i, i], color=color, lw=2, solid_capstyle="round")
        ax.plot(r["beta1"], i, "o", ms=8, color=color,
                mfc=color if r["odporny"] else viz.SURF, mew=2)
        ax.annotate(f"{r['beta1']:.2f}  (n = {r['n']}, sprz. = {r['sprzeczne']})", (r["ci_97.5"], i),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color=INK2)
    ax.set_yticks(range(len(t)), t["opis"])
    ax.set_ylim(len(t) - 0.5, -0.5)
    ax.grid(axis="y", visible=False)
    sep = [i - 0.5 for i in range(1, len(t)) if t.loc[i, "rodzaj"] != t.loc[i - 1, "rodzaj"]]
    for y in sep:
        ax.axhline(y, color=AXIS, lw=0.8)
    lo = min(0, t["ci_2.5"].min()) - 0.2
    ax.set_xlim(lo, t["ci_97.5"].max() + 1.2)
    ax.set_xlabel("β₁ (logit, prawica vs reszta), 95% CI z błędami klastrowanymi po mówcy")
    ax.set_title("Krok 8: odporność wyniku bez korekty")
    viz.subtitle(ax, "niebieskie: warianty z planu, pomarańczowe: rozszerzenia; pasmo: 0,5–2 × β₁ głównego; "
                     "pusty punkt: kryterium niespełnione")
    viz.save(fig, f"{slug}_odpornosc")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=llm.PIPELINE_MODEL)
    ap.add_argument("--werdykt-prompt", default=runs.VERDICT_PROMPT,
                    help=f"verdicts of the pipeline run ({runs.PAPERQA_PROMPT} for PaperQA2)")
    ap.add_argument("--bez-loso", action="store_true", help="skip leave-one-speaker-out")
    runs.add_retrieval_args(ap, frozen=True)
    a = ap.parse_args()
    labels_file = runs.labels_path(a.model, a.werdykt_prompt, a.wyszukiwanie, a.embedding)
    slug = labels_file.stem
    labels = pd.read_csv(labels_file)
    OUT.mkdir(parents=True, exist_ok=True)

    table = R.run(labels)
    table.to_csv(OUT / f"{slug}_robustness.csv", index=False)
    cols = ["wariant", "rodzaj", "n", "mowcy", "sprzeczne", "beta1", "ci_2.5", "ci_97.5", "p_jednostronne",
            "roznica", "krotnosc", "odporny"]
    print(f"Step 8, midpoint {R.MIDPOINT:%Y-%m-%d}:\n{table[cols].round(3).to_string(index=False)}")
    v = R.verdict(table)
    print("\nRobust (plan variants): " + ("yes" if v["odporny"] else f"no, fails: {', '.join(v['niespelnione'])}"))
    forest(table, slug)

    if a.bez_loso:
        return
    loso = R.leave_one_speaker_out(labels)
    loso.insert(1, "posel", loso["member_id"].map(mp_names()))
    loso.to_csv(OUT / f"{slug}_loso.csv", index=False)
    broken = loso[~loso["odporny"]]
    print(f"\nLeave-one-speaker-out ({len(loso)} speakers): beta1 from {loso['beta1'].min():.3f} to "
          f"{loso['beta1'].max():.3f}; criterion failed after removing {len(broken)} speaker(s)")
    print(loso.head(3).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
