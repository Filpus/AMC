"""Verdict of every claim against AR6 with a Claude model through the installed Claude Code CLI (`claude -p`).

An alternative to src/verify_claims.py (Gemma 4 12B + retrieval of 6 fragments): the model gets the verdict rules of
prompts/verdict_v1.md and, depending on --context, the AR6 text itself instead of retrieved fragments:
  no_context  no AR6 text (only with --memory: the model judges from what it knows of AR6);
  SPMs        all fragments of the three Summaries for Policymakers (WGI, WGII, WGIII);
  All         all fragments of the SPMs and the Technical Summaries (the whole index of build_ar6.py).
--memory lets the model use its own knowledge of AR6. With a context, a verdict other than brak_podstaw still needs a
fragment_id from the context and a verbatim quote from that fragment; the script checks both, and a verdict that fails
becomes brak_podstaw (the model's verdict is kept in `werdykt_bez_ar6`, as in verify_claims.py). Without a context the
cited AR6 section cannot be checked against a text: `ar6_w_indeksie` only says whether such a section label exists.

Run from the project root (AMC) with the project environment; only `claude` (Claude Code, logged in) is needed:

    .venv/bin/python pipeline_development/alternative_verification/verify_claude.py --context SPMs --estimate
    .venv/bin/python pipeline_development/alternative_verification/verify_claude.py --context SPMs --testy
    .venv/bin/python pipeline_development/alternative_verification/verify_claude.py --context All --model sonnet
    .venv/bin/python pipeline_development/alternative_verification/verify_claude.py --context SPMs \
        --claims data/processed/claims/claims_v1__gemma4_12b__sample.jsonl      # the 100 gold statements

Claims are sent in batches (--batch-size) with the same system prompt (rules + AR6 text), so after the first call the
AR6 text is read from the prompt cache. --budget stops the run when the summed cost reported by Claude Code reaches it.
Reruns skip claims judged without an error.

Output in alternative_verification/out/:
- verdicts/<prompt>__gemma4_12b[__tests].jsonl: one line per claim, the fields of verify_claims.py (twierdzenie_id,
  werdykt, ar6, uzasadnienie, werdykt_bez_ar6, ...) plus kontekst, pamiec, cytat, ar6_fragment_id, sprawdzenie and
  wywolanie; <prompt> = claude_<context>[_mem]_<model alias>; claims of `extract_claims.py --ids FILE` add
  __<FILE stem> (e.g. __sample for the gold sample), --testy adds __tests. The model part of the file name is the one of the
  claims (gemma4_12b), so the file drops into the pipeline: copy it to data/processed/verdicts/ and run
  `python src/label_statements.py --werdykt-prompt <prompt> --wyszukiwanie rrf --embedding bge-m3`;
- calls/<prompt>.jsonl: one line per CLI call (claims, tokens, cost, seconds, error).
"""
import argparse, json, re, subprocess, sys, tempfile, time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
AMC = HERE.parents[1]
sys.path.insert(0, str(AMC / "src"))
from amc import runs  # noqa: E402

FRAGMENTS = AMC / "data" / "ar6" / "fragments.parquet"
RULES = AMC / "prompts" / "verdict_v1.md"
CLAIMS = AMC / "data" / "processed" / "claims" / "claims_v1__gemma4_12b.jsonl"
TESTS = AMC / "data" / "tests" / "verdict.csv"
CLAIMS_MODEL = "gemma4_12b"
CONTEXTS = {"no_context": [], "SPMs": ["SPM"], "All": ["SPM", "TS"]}
VERDICTS = ["sprzeczne", "zgodne", "brak_podstaw"]

SOURCE = {
    ("context", False): (
        "Dostajesz twierdzenia posłów i pełny tekst wybranych części AR6 jako fragmenty z identyfikatorem "
        "(`fragment_id`) i etykietą sekcji. Oceniaj wyłącznie na podstawie tych fragmentów, a nie własnej wiedzy."),
    ("context", True): (
        "Dostajesz twierdzenia posłów i pełny tekst wybranych części AR6 jako fragmenty z identyfikatorem "
        "(`fragment_id`) i etykietą sekcji. Możesz korzystać ze swojej wiedzy o AR6, żeby wiedzieć, gdzie szukać, "
        "ale werdykt `sprzeczne` albo `zgodne` musi się opierać na podanym fragmencie."),
    ("no_context", True): (
        "Dostajesz twierdzenia posłów bez tekstu AR6. Oceniaj na podstawie swojej wiedzy o raporcie AR6: "
        "streszczeniach dla decydentów (SPM) i streszczeniach technicznych (TS) grup roboczych WGI, WGII i WGIII. "
        "Werdykt `sprzeczne` albo `zgodne` wymaga wskazania konkretnej sekcji AR6 (np. „WGI SPM A.1”) i przytoczenia "
        "jej ustalenia; jeśli nie pamiętasz takiej sekcji, werdykt to `brak_podstaw`."),
}
RESPONSE = """## Odpowiedź

W przykładach wyżej fragmenty są ponumerowane; tutaj zamiast numeru podajesz {ref}. Oceń każde twierdzenie osobno
i zwróć JSON z listą `oceny`, po jednej pozycji na twierdzenie, w kolejności twierdzeń, z polami:
- `twierdzenie_id`: identyfikator twierdzenia z wejścia;
- `uzasadnienie`: krótko (do 1000 znaków): co twierdzi mówca, co mówi rozstrzygające ustalenie AR6, czy się zgadzają;
- `ar6`: {ref}, albo pusty napis, gdy żadne ustalenie nie rozstrzyga;
- `cytat`: {quote}, albo pusty napis;
- `werdykt`: `sprzeczne`, `zgodne` albo `brak_podstaw` (`brak_podstaw`, gdy `ar6` jest pusty).
"""
REF = {True: ("`fragment_id` fragmentu, który rozstrzyga", "dosłowny cytat (jedno zdanie lub jego część) z tego fragmentu"),
       False: ("etykietę sekcji AR6, która rozstrzyga (np. „WGI SPM D.1.1”)", "ustalenie tej sekcji, tak dokładnie, jak je pamiętasz")}


def fragments(context: str) -> pd.DataFrame:
    f = pd.read_parquet(FRAGMENTS)
    return f[f.czesc.isin(CONTEXTS[context])].reset_index(drop=True)


def system_prompt(context: str, memory: bool, frags: pd.DataFrame) -> str:
    rules = RULES.read_text(encoding="utf-8").split("## Odpowiedź")[0]
    rules = rules.split("\n\n", 1)[1]  # drop the intro about numbered, retrieved fragments
    has = bool(len(frags))
    intro = ("Jesteś anotatorem. Porównujesz twierdzenia posłów z ustaleniami raportu IPCC AR6, czyli z konsensusem "
             "naukowym o klimacie. " + SOURCE[("context" if has else "no_context", memory)])
    out = intro + "\n\n" + rules.strip() + "\n\n" + RESPONSE.format(ref=REF[has][0], quote=REF[has][1])
    if has:
        listing = "\n\n".join(f"[{r.fragment_id}] {r.etykieta}: {r.tekst}" for r in frags.itertuples())
        out += f"\n## Tekst AR6 ({' + '.join(CONTEXTS[context])})\n\n{listing}\n"
    return out


def user_message(batch: list) -> str:
    return "Twierdzenia do oceny:\n\n" + "\n\n".join(
        f"[{c['twierdzenie_id']}] {c['twierdzenie']}\n(po angielsku: {c.get('twierdzenie_en', '')})" for c in batch)


def schema() -> str:
    """The same schema for every call: it is part of the request prefix, so a batch-dependent schema (e.g. the
    number of items of a shorter last batch) would break the prompt cache."""
    item = {"type": "object", "additionalProperties": False,
            "properties": {"twierdzenie_id": {"type": "string"}, "uzasadnienie": {"type": "string"},
                           "ar6": {"type": "string"}, "cytat": {"type": "string"},
                           "werdykt": {"type": "string", "enum": VERDICTS}},
            "required": ["twierdzenie_id", "uzasadnienie", "ar6", "cytat", "werdykt"]}
    return json.dumps({"type": "object", "additionalProperties": False,
                       "properties": {"oceny": {"type": "array", "items": item}},
                       "required": ["oceny"]})


def load_claims(path: Path) -> list:
    out = []
    for wid, r in runs.last_lines(path).items():
        if not r["blad"]:
            out += [{"twierdzenie_id": f"{wid}#{c['nr']}", "wypowiedz_id": wid, **c} for c in r["twierdzenia"]]
    return out


def load_tests() -> list:
    t = pd.read_csv(TESTS, dtype=str, keep_default_na=False)
    return [{"twierdzenie_id": r["test"], "wypowiedz_id": "", "nr": 0, **r} for r in t.to_dict("records")]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[‘’“”„\"']", "", s)).strip().lower()


def check(ans: dict, frags: pd.DataFrame, labels: set) -> dict:
    """werdykt, ar6 (section label), ar6_fragment_id, sprawdzenie, werdykt_bez_ar6, ar6_w_indeksie."""
    v, ref, quote = ans["werdykt"], ans["ar6"].strip(), ans["cytat"].strip()
    res = {"werdykt": v, "ar6": ref, "ar6_fragment_id": None, "werdykt_bez_ar6": None, "ar6_w_indeksie": None}
    if len(frags):
        row = frags[frags.fragment_id == ref.strip("[]")]
        if not ref:
            why = "brak_fragmentu"
        elif row.empty:
            why = "nieznany_fragment"
        elif norm(quote) and norm(quote) in norm(row.tekst.iloc[0]):
            why = "ok"
        else:
            why = "cytat_nie_pasuje"
        if not row.empty:
            res["ar6"], res["ar6_fragment_id"] = row.etykieta.iloc[0], row.fragment_id.iloc[0]
    else:
        why = "ok" if ref else "brak_fragmentu"
        res["ar6_w_indeksie"] = bool(ref) and any(l.startswith(norm(ref)) for l in labels)
    if v != "brak_podstaw" and why != "ok":
        res["werdykt_bez_ar6"], res["werdykt"] = v, "brak_podstaw"
    return {**res, "sprawdzenie": why if v != "brak_podstaw" else None}


def call(system_file: Path, batch: list, model: str, effort, workdir: Path) -> tuple:
    cmd = ["claude", "-p", "--system-prompt-file", str(system_file), "--tools", "", "--model", model,
           "--output-format", "json", "--no-session-persistence", "--strict-mcp-config", "--json-schema", schema()]
    if effort:
        cmd += ["--effort", effort]
    t0 = time.time()
    p = subprocess.run(cmd, input=user_message(batch), capture_output=True, text=True, cwd=workdir, timeout=3600)
    secs = round(time.time() - t0, 1)
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        return None, {"blad": f"exit {p.returncode}: {(p.stderr or p.stdout)[:500]}", "sekundy": secs}
    u = d.get("usage") or {}
    meta = {"blad": d.get("result")[:500] if d.get("is_error") else None, "sekundy": secs,
            "koszt_usd": d.get("total_cost_usd"), "model_pelny": next(iter(d.get("modelUsage") or {}), None),
            **{k: u.get(k) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}}
    return d.get("structured_output"), meta


def estimate(system: str, claims: list, batch: int) -> str:
    """Rough input tokens: English AR6 text ~4 characters per token, Polish rules and claims ~3."""
    frag_chars = len(system.split("\n## Tekst AR6", 1)[1]) if "\n## Tekst AR6" in system else 0
    sys_tok = frag_chars / 4 + (len(system) - frag_chars) / 3 + 1500  # + Claude Code's own instructions
    calls = -(-len(claims) // batch)
    msg_tok = sum(len(user_message([c])) for c in claims) / 3
    total = calls * sys_tok + msg_tok
    return (f"system prompt ~{sys_tok / 1e3:.0f}k tokens (AR6 text {frag_chars / 1e6:.2f}M characters); "
            f"{len(claims)} claims in {calls} calls of {batch}; input ~{total / 1e6:.1f}M tokens in total, "
            f"of which ~{(calls - 1) * sys_tok / 1e6:.1f}M can be read from the prompt cache")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--context", choices=list(CONTEXTS), required=True)
    ap.add_argument("--memory", action="store_true", help="let the model use its own knowledge of AR6")
    ap.add_argument("--model", default="sonnet", help="Claude Code model alias or full name (sonnet, opus, haiku...)")
    ap.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="default: the CLI's")
    ap.add_argument("--batch-size", type=int, default=20, help="claims per call")
    ap.add_argument("--claims", default=str(CLAIMS), help="claims file of extract_claims.py")
    ap.add_argument("--testy", action="store_true", help="claims with expected verdicts from data/tests/verdict.csv")
    ap.add_argument("--limit", type=int, default=0, help="judge only the first N claims")
    ap.add_argument("--budget", type=float, default=0, help="stop when the summed reported cost (USD) reaches this")
    ap.add_argument("--estimate", action="store_true", help="print the token estimate and exit, no calls")
    a = ap.parse_args()
    if a.context == "no_context" and not a.memory:
        sys.exit("no_context without --memory leaves the model nothing to judge by; add --memory")

    frags = fragments(a.context)
    labels = {norm(re.sub(r"\s*\(s\.\s*\d+\)$", "", l)) for l in pd.read_parquet(FRAGMENTS).etykieta}
    system = system_prompt(a.context, a.memory, frags)
    claims = load_tests() if a.testy else load_claims(Path(a.claims))
    prompt = f"claude_{a.context}{'_mem' if a.memory else ''}_{runs.model_slug(a.model)}"
    # claims of `extract_claims.py --ids FILE` (claims_v1__gemma4_12b__<FILE stem>.jsonl) keep their suffix, as in
    # verify_claims.py, so a run on the gold sample does not mix with the full run
    suffix = "__tests" if a.testy else Path(a.claims).stem.partition(f"__{CLAIMS_MODEL}")[2]
    out = HERE / "out" / "verdicts" / f"{prompt}__{CLAIMS_MODEL}{suffix}.jsonl"
    log = HERE / "out" / "calls" / f"{prompt}{suffix}.jsonl"
    done = runs.done(out, "twierdzenie_id") if out.exists() else set()
    todo = [c for c in claims if c["twierdzenie_id"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    print(f"{prompt}: {len(todo)} claims to judge -> {out.relative_to(AMC)}")
    print(estimate(system, todo, a.batch_size))
    if a.estimate or not todo:
        return report(out) if a.testy and out.exists() else None

    out.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    spent = 0.0
    with tempfile.TemporaryDirectory() as tmp, out.open("a", encoding="utf-8") as fo, log.open("a", encoding="utf-8") as fl:
        system_file = Path(tmp) / "system.md"
        system_file.write_text(system, encoding="utf-8")
        for k in range(0, len(todo), a.batch_size):
            batch, call_id = todo[k:k + a.batch_size], f"{int(time.time())}_{k // a.batch_size}"
            ans, meta = call(system_file, batch, a.model, a.effort, Path(tmp))
            by_id = {o["twierdzenie_id"]: o for o in (ans or {}).get("oceny", [])}
            for c in batch:
                row = {key: c[key] for key in ("twierdzenie_id", "wypowiedz_id", "nr", "twierdzenie", "twierdzenie_en",
                                               "oczekiwane") if key in c}
                o = by_id.get(c["twierdzenie_id"])
                res = ({**check(o, frags, labels), "uzasadnienie": o["uzasadnienie"], "cytat": o["cytat"], "blad": None}
                       if o and not meta["blad"] else
                       {"werdykt": None, "blad": meta["blad"] or "no answer for this claim in the batch"})
                runs.append(fo, {**row, "model": meta.get("model_pelny") or a.model, "prompt": prompt,
                                 "twierdzenia_z": TESTS.name if a.testy else Path(a.claims).name, "kontekst": a.context,
                                 "pamiec": a.memory, "komputer": runs.HOST, "wywolanie": call_id, **res})
            runs.append(fl, {"wywolanie": call_id, "twierdzenia": len(batch), "odpowiedzi": len(by_id), **meta})
            spent += meta.get("koszt_usd") or 0
            print(f"{min(k + a.batch_size, len(todo))}/{len(todo)} claims, {meta['sekundy']}s, "
                  f"cache read {meta.get('cache_read_input_tokens')}, cost so far ${spent:.2f}"
                  + (f" ERROR {meta['blad'][:150]}" if meta["blad"] else ""), flush=True)
            if a.budget and spent >= a.budget:
                print(f"budget ${a.budget} reached; rerun to continue")
                break
    if a.testy:
        report(out)


def report(path: Path) -> None:
    d = pd.DataFrame(runs.last_lines(path, "twierdzenie_id").values())
    ok = d.blad.isna() & (d.werdykt == d.oczekiwane)
    print(f"tests: {ok.sum()}/{d.blad.isna().sum()} as expected")
    for r in d[d.blad.isna() & ~ok].to_dict("records"):
        print(f"  WRONG {r['twierdzenie_id']}: expected {r['oczekiwane']}, got {r['werdykt']} ({r['ar6']}; "
              f"{r.get('sprawdzenie')}, model said {r.get('werdykt_bez_ar6')})")


if __name__ == "__main__":
    main()
