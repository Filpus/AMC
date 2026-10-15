"""Local LLM served by Ollama with structured JSON output: the client and the steps of the codebook pipeline (topic,
claims, verdict)."""
import json
import time

import requests

from . import text as T
from .paths import ROOT

OLLAMA = "http://127.0.0.1:11434/api/chat"
PROMPTS = ROOT / "prompts"
PIPELINE_MODEL = "gemma4:12b"  # codebook pipeline: klimat, twierdzenia, werdykt
MAX_WORDS = 2500
MAX_OUTPUT_TOKENS = 4096  # stops runaway generation (repetition loops inside the JSON schema)

SCHEMA_TOPIC = {
    "type": "object",
    "properties": {"fragment": {"type": "string", "maxLength": 300}, "klimat": {"type": "integer", "enum": [0, 1]}},
    "required": ["fragment", "klimat"],
}
TOPIC_NUM_CTX = 16384  # topic_v0 ~4.4k tokens + 2500 words x up to ~3.4 tokens (Bielik) + answer
CLAIMS_NUM_CTX = 16384
VERDICT_NUM_CTX = 16384
REMINDER_HEADER = "## Przypomnienie"
VERDICTS = ["sprzeczne", "zgodne", "brak_podstaw"]
MAX_CLAIMS = 10
SCHEMA_CLAIMS = {
    "type": "object",
    "properties": {"twierdzenia": {"type": "array", "maxItems": MAX_CLAIMS, "items": {
        "type": "object",
        "properties": {
            "cytat": {"type": "string", "maxLength": 400},
            "twierdzenie": {"type": "string", "maxLength": 300},
            "twierdzenie_en": {"type": "string", "maxLength": 300},
        },
        "required": ["cytat", "twierdzenie", "twierdzenie_en"],
    }}},
    "required": ["twierdzenia"],
}


def chat(system, user, schema, model, num_ctx, timeout=600, num_predict=MAX_OUTPUT_TOKENS, think=None):
    body = {
        "model": model, "stream": False, "format": schema,
        "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": num_predict},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if think is not None:
        body["think"] = think
    r = requests.post(OLLAMA, timeout=timeout, json=body)
    r.raise_for_status()
    return r.json()


def overflow(tokens_in, tokens_out, num_ctx):
    """Context overflow; in both cases the model loses the system prompt (instructions) without any error.

    "przepelnienie": the prompt did not fit; Ollama cut it to num_ctx/2 + 2 tokens (the first 4 and the end) and reports
    that number as prompt_eval_count.
    "przesuniecie": the prompt fitted, but prompt + answer did not; llama-server dropped the oldest tokens while generating.
    """
    if tokens_in is None or tokens_in != tokens_in:
        return None
    if tokens_in == num_ctx // 2 + 2:
        return "przepelnienie"
    if tokens_in + (tokens_out or 0) > num_ctx:
        return "przesuniecie"
    return None


def load_prompt(name):
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def load_topic_prompt(name):
    """(system, reminder): the codebook part and the output reminder that follows the statement."""
    system, reminder = load_prompt(name).split(REMINDER_HEADER)
    return system.strip(), reminder.strip()


def ask(prompt, body, schema, model, num_ctx, num_predict, timeout=600):
    """One structured call with a codebook prompt: (answer or None, meta with `blad`). The reminder follows the body;
    thinking is switched off for models that have it; context overflow counts as an error."""
    system, reminder = prompt
    t0 = time.perf_counter()
    res = chat(system, f"{body}\n\n{reminder}", schema, model, num_ctx, timeout, num_predict=num_predict, think=False)
    meta = {"tokeny_we": res.get("prompt_eval_count"), "tokeny_wy": res.get("eval_count"), "num_ctx": num_ctx}
    answer, error = None, None
    try:
        answer = json.loads(res["message"]["content"])
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        error = f"{type(e).__name__}: {e}: {res.get('message')}"
    flag = overflow(meta["tokeny_we"], meta["tokeny_wy"], num_ctx)
    if flag and not error:
        error = f"overflow: {flag}"
    return answer, {**meta, "blad": error, "sekundy": round(time.perf_counter() - t0, 2)}


def classify_topic(text, prompt, model=PIPELINE_MODEL, num_ctx=TOPIC_NUM_CTX, timeout=600):
    """Topic classification: `klimat` (0/1) and the sentence the model points to; `fragment_w_tekscie` = share of the
    fragment found verbatim in the text."""
    text, cut = truncate(text)
    answer, meta = ask(prompt, f"Wypowiedź:\n{text}", SCHEMA_TOPIC, model, num_ctx, 256, timeout)
    res = {"klimat": None, "fragment": None, "fragment_w_tekscie": None}
    if not meta["blad"]:
        try:
            fragment = answer["fragment"].strip()
            res = {"klimat": int(answer["klimat"]), "fragment": fragment,
                   "fragment_w_tekscie": round(T.quote_match(fragment, text), 2) if fragment else None}
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            meta["blad"] = f"{type(e).__name__}: {e}: {answer}"
    return {**res, "obciete": cut, **meta}


def extract_claims(text, prompt, model=PIPELINE_MODEL, num_ctx=CLAIMS_NUM_CTX, timeout=900):
    """Claims with quote and the speaker's position in Polish and English; each claim gets `nr`
    and `cytat_w_tekscie` (share of the quote found verbatim in the text)."""
    text, cut = truncate(text)
    answer, meta = ask(prompt, f"Wypowiedź:\n{text}", SCHEMA_CLAIMS, model, num_ctx, 3072, timeout)
    claims = []
    if not meta["blad"]:
        try:
            claims = [{"nr": i, **c, "cytat_w_tekscie": round(T.quote_match(c["cytat"], text), 2)}
                      for i, c in enumerate(answer["twierdzenia"], 1)]
        except (KeyError, TypeError) as e:
            meta["blad"] = f"{type(e).__name__}: {e}: {answer}"
    return {"twierdzenia": claims, "obciete": cut, **meta}


def schema_verdict(k):
    return {"type": "object", "properties": {
        "uzasadnienie": {"type": "string", "maxLength": 1000},
        "ar6": {"type": "integer", "enum": list(range(k + 1))},
        "werdykt": {"type": "string", "enum": VERDICTS}},
        "required": ["uzasadnienie", "ar6", "werdykt"]}


def judge_claim(claim, fragments, prompt, model=PIPELINE_MODEL, num_ctx=VERDICT_NUM_CTX, timeout=600):
    """Verdict of one claim against numbered AR6 fragments (dicts with `etykieta`, `tekst`).
    `ar6` is the label of the fragment the model points to. A verdict other than brak_podstaw without one becomes
    brak_podstaw (codebook: no deciding fragment, no verdict); the model's verdict is kept in `werdykt_bez_ar6`."""
    listing = "\n\n".join(f"[{i}] {f['etykieta']}: {f['tekst']}" for i, f in enumerate(fragments, 1))
    body = (f"Twierdzenie: {claim['twierdzenie']}\n(po angielsku: {claim.get('twierdzenie_en', '')})\n\n"
            f"Fragmenty AR6:\n{listing}")
    answer, meta = ask(prompt, body, schema_verdict(len(fragments)), model, num_ctx, 768, timeout)
    res = {"werdykt": None, "ar6": None, "uzasadnienie": None, "werdykt_bez_ar6": None}
    if not meta["blad"]:
        try:
            nr = int(answer["ar6"])
            res = {"werdykt": answer["werdykt"], "ar6": fragments[nr - 1]["etykieta"] if nr else "",
                   "uzasadnienie": answer["uzasadnienie"], "werdykt_bez_ar6": None}
            if nr == 0 and res["werdykt"] != "brak_podstaw":
                res["werdykt_bez_ar6"], res["werdykt"] = res["werdykt"], "brak_podstaw"
        except (KeyError, TypeError, ValueError, IndexError) as e:
            meta["blad"] = f"{type(e).__name__}: {e}: {answer}"
    return {**res, "fragmenty": [f["etykieta"] for f in fragments], **meta}


def truncate(text, max_words=MAX_WORDS):
    words = text.split()
    return (" ".join(words[:max_words]), True) if len(words) > max_words else (text, False)
