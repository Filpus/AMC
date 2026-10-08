"""Stage A classification with a local LLM served by Ollama (structured JSON output)."""
import copy
import json
import time

import requests

from . import text as T
from .paths import ROOT

OLLAMA = "http://localhost:11434/api/chat"
PROMPTS = ROOT / "prompts"
DEFAULT_MODEL = "SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M"
MAX_WORDS = 2500
# prompt of etap_a_v2 ~4.7k tokens + 2500 words x ~2.9 tokens + answer must fit; the same size for both steps avoids model reloads
NUM_CTX = 16384
MAX_OUTPUT_TOKENS = 4096  # stops runaway generation (repetition loops inside the JSON schema)
MAX_CANDIDATES = 16
VERIFY_PROMPT = "weryfikacja_v1"
# run settings of result lines written before these fields were recorded
LEGACY_SETTINGS = {"num_ctx": 8192, "max_kandydatow": 8, "prompt_weryfikacji": "weryfikacja_v0"}
TOPICS = ["szczepienia", "covid", "klimat", "energia_jadrowa", "gmo", "5g_promieniowanie", "smog", "in_vitro",
          "inny_naukowy"]
ATTRIBUTION = ["wlasne", "cytat_zgoda", "cytat_polemika"]

KINDS = ["naukowe", "statystyka", "prawo", "budzet", "polityka", "opinia", "inne"]
# the model labels candidate sentences with a kind; only `naukowe` go to step 2 and, if confirmed, become claims
SCHEMA = {
    "type": "object",
    "properties": {"kandydaci": {"type": "array", "maxItems": MAX_CANDIDATES, "items": {
        "type": "object",
        "properties": {
            "cytat": {"type": "string", "maxLength": 300},
            "rodzaj": {"type": "string", "enum": KINDS},
            "twierdzenie": {"type": "string", "maxLength": 250},
            "temat": {"type": "string", "enum": [*TOPICS, "brak"]},
            "atrybucja": {"type": "string", "enum": ATTRIBUTION},
        },
        "required": ["cytat", "rodzaj", "twierdzenie", "temat", "atrybucja"],
    }}},
    "required": ["kandydaci"],
}


def schema_for(max_candidates=MAX_CANDIDATES):
    schema = copy.deepcopy(SCHEMA)
    schema["properties"]["kandydaci"]["maxItems"] = max_candidates
    return schema


SCHEMA_VERIFY = {"type": "object", "properties": {"naukowe": {"type": "boolean"}}, "required": ["naukowe"]}


def chat(system, user, schema, model, num_ctx=NUM_CTX, timeout=600, num_predict=MAX_OUTPUT_TOKENS):
    r = requests.post(OLLAMA, timeout=timeout, json={
        "model": model, "stream": False, "format": schema,
        "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": num_predict},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    })
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


def verify(claim, context, model, num_ctx=NUM_CTX):
    """Step 2: is the paraphrased claim a scientific claim, judged together with its passage of the statement."""
    user = f"Twierdzenie: {claim}\nFragment wypowiedzi: {context}"
    body = chat(load_prompt(VERIFY_PROMPT), user, SCHEMA_VERIFY, model, num_ctx=num_ctx, num_predict=32)
    return bool(json.loads(body["message"]["content"])["naukowe"])


def verify_candidates(candidates, text, model):
    """Sets `weryfikacja` on every candidate: step 2 result for `naukowe`, None for other kinds."""
    for c in candidates:
        ctx = T.quote_context(text, c["cytat"]) or c["cytat"]
        c["weryfikacja"] = verify(c["twierdzenie"], ctx, model) if c["rodzaj"] == "naukowe" else None
    return candidates


def with_claims(candidates):
    claims = [c for c in candidates if c["weryfikacja"]]
    return {"zawiera_twierdzenie": int(bool(claims)), "twierdzenia": claims, "kandydaci": candidates,
            "prompt_weryfikacji": VERIFY_PROMPT}


def reverify(row, text, model=DEFAULT_MODEL):
    """Step 2 again (current VERIFY_PROMPT) on the stored candidates of a result line; old decisions kept as `weryfikacja_v0`."""
    text, _ = truncate(text)
    cands = [{**c, "weryfikacja_v0": c.get("weryfikacja")} for c in row["kandydaci"]]
    t0 = time.perf_counter()
    out = {**row, **with_claims(verify_candidates(cands, text, model))}
    out["sekundy_weryfikacji"] = round(time.perf_counter() - t0, 2)
    return out


def load_prompt(name, max_candidates=MAX_CANDIDATES):
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8").replace("{max_kandydatow}", str(max_candidates))


def truncate(text, max_words=MAX_WORDS):
    words = text.split()
    return (" ".join(words[:max_words]), True) if len(words) > max_words else (text, False)


def classify(text, system, model=DEFAULT_MODEL, schema=SCHEMA, num_ctx=NUM_CTX, timeout=600):
    """Returns the parsed answer plus run metadata; `blad` is set when the answer is not valid JSON or the context overflowed."""
    text, cut = truncate(text)
    t0 = time.perf_counter()
    body = chat(system, f"Wypowiedź:\n{text}", schema, model, num_ctx, timeout)
    meta = {"tokeny_we": body.get("prompt_eval_count"), "tokeny_wy": body.get("eval_count"), "num_ctx": num_ctx}
    try:
        answer = json.loads(body["message"]["content"])
        res = {**with_claims(verify_candidates(answer["kandydaci"], text, model)), "blad": None}
    except (json.JSONDecodeError, KeyError) as e:
        res = {"zawiera_twierdzenie": None, "twierdzenia": [], "blad": f"{e}: {body.get('message')}"}
    flag = overflow(meta["tokeny_we"], meta["tokeny_wy"], num_ctx)
    if flag and not res["blad"]:
        res["blad"] = f"overflow: {flag}"
    return {**res, "obciete": cut, "sekundy": round(time.perf_counter() - t0, 2), **meta}
