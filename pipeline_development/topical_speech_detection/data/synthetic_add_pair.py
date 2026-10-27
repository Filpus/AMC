"""Append one synthetic minimal pair (stage 1) to data/synthetic.jsonl and update data/progress.md.

Reads a pair spec from stdin in this format:

@@para S01
@@typ odniesienie
@@a kategoria=N8_inne odn=1
<passage of version a (klimat=0)>
@@b kategoria=P2_polityka odn=1
<passage of version b (klimat=1)>
@@fa <optional: deciding sentence of a; default = whole passage a>
@@fb <deciding sentence of b; must occur verbatim in text b>
@@text
<shared statement text containing the placeholder {X} exactly once>

Run from the project root (AMC).
"""
import json, re, sys
from pathlib import Path

D = Path("pipeline_development/topical_speech_detection/data")
OUT = D / "synthetic.jsonl"
PROG = D / "progress.md"
TYPES = {"odniesienie": 15, "tlo_watek": 12, "dluga_wypowiedz": 8, "epitet": 10,
         "kleski": 8, "energetyka": 12, "slowo_nazwa": 10}
CATS = {"P1_nauka_skutki", "P2_polityka", "P3_negowanie", "P4_watek_poboczny", "N1_inne_znaczenie",
        "N2_nazwy", "N3_tlo", "N4_epitet", "N5_smog_pogoda", "N6_energetyka", "N7_srodowisko", "N8_inne"}


def parse(raw):
    spec, key, buf = {}, None, []
    def flush():
        if key:
            spec[key] = "\n".join(buf).strip()
    for line in raw.splitlines():
        m = re.match(r"^@@(para|typ|a|b|fa|fb|text)\b ?(.*)$", line)
        if m:
            flush()
            key, rest = m.group(1), m.group(2)
            if key in ("para", "typ", "fa", "fb"):
                spec[key] = rest.strip(); key, buf = None, []
            else:
                spec[key + "_hdr"] = rest.strip(); buf = []
        elif key:
            buf.append(line)
    flush()
    return spec


def load_existing():
    rows = []
    if OUT.exists():
        lines = OUT.read_text(encoding="utf-8").splitlines()
        good = []
        for ln in lines:
            try:
                rows.append(json.loads(ln)); good.append(ln)
            except json.JSONDecodeError:
                print("WARNING: dropping incomplete line", file=sys.stderr)
        if len(good) != len(lines):
            OUT.write_text("".join(l + "\n" for l in good), encoding="utf-8")
    return rows


def write_progress(rows):
    decisions = ""
    if PROG.exists():
        txt = PROG.read_text(encoding="utf-8")
        i = txt.find("## Decisions not covered by the prompt")
        if i >= 0:
            decisions = txt[i:]
    if not decisions:
        decisions = "## Decisions not covered by the prompt\n\n"
    pairs = sorted({r["para_id"] for r in rows})
    per = {t: len({r["para_id"] for r in rows if r["typ_pary"] == t}) for t in TYPES}
    wc = [len(r["tekst"].split()) for r in rows]
    done = len(pairs) == 75
    s = ["# Progress: topical speech detection dataset", "",
         f"- Current stage: {'1 finished; next: blind-check batch files (stage 2 preparation)' if done else '1 (writing synthetic pairs)'}",
         f"- Last finished pair: {pairs[-1] if pairs else 'none'}",
         f"- Pairs written: {len(pairs)} / 75 (items: {len(rows)} / 150)",
         "- Pairs per typ_pary (written / target): " + ", ".join(f"{t} {per[t]}/{n}" for t, n in TYPES.items()),
         f"- Item length (words): {min(wc) if wc else '-'}–{max(wc) if wc else '-'}",
         "- Real statements read: 0 (stage 1 must precede reading the corpus)", ""]
    PROG.write_text("\n".join(s) + "\n" + decisions, encoding="utf-8")


def main():
    spec = parse(sys.stdin.read())
    pid, typ = spec["para"], spec["typ"]
    assert re.fullmatch(r"S\d\d", pid) and 1 <= int(pid[1:]) <= 75, pid
    assert typ in TYPES, typ
    rows = load_existing()
    if any(r["para_id"] == pid for r in rows):
        sys.exit(f"{pid} already written; not overwriting")
    if sum(1 for r in rows if r["typ_pary"] == typ) // 2 >= TYPES[typ]:
        sys.exit(f"quota for {typ} already full")
    tpl = spec["text"]
    assert tpl.count("{X}") == 1, "template must contain {X} exactly once"
    items = []
    for v, kl in (("a", 0), ("b", 1)):
        hdr = dict(kv.split("=") for kv in spec[v + "_hdr"].split())
        kat, odn = hdr["kategoria"], int(hdr["odn"])
        assert kat in CATS and kat.startswith("P" if kl else "N"), kat
        passage = spec[v]
        text = tpl.replace("{X}", passage)
        frag = spec.get("f" + v) or passage
        assert frag in text, f"fragment of {v} not verbatim in text"
        n = len(text.split())
        lo, hi = (800, 1500) if typ == "dluga_wypowiedz" else (120, 600)
        assert lo <= n <= hi, f"{pid}{v}: {n} words outside {lo}-{hi}"
        items.append({"wypowiedz_id": pid + v, "para_id": pid, "typ_pary": typ, "tekst": text,
                      "klimat": kl, "kategoria": kat, "fragment": frag,
                      "odniesienie_do_innego_mowcy": odn,
                      "blind_klimat": None, "blind_kategoria": None})
    with OUT.open("a", encoding="utf-8") as f:
        f.write("".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items))
    rows += items
    write_progress(rows)
    print(pid, typ, [len(it["tekst"].split()) for it in items])


if __name__ == "__main__":
    main()
