"""Stage A of the exploration (src/classify.py, notebooks 02-03): candidate sentences with a kind, one of eight
topics and the attribution, then a check of the `naukowe` candidates. Superseded by the codebook pipeline
(amc/llm.py), which does not use it."""
import copy
import json
import time

from . import llm
from . import text as T

DEFAULT_MODEL = "SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M"
# prompt of etap_a_v2 ~4.7k tokens + 2500 words x ~2.9 tokens + answer must fit; the same size for both steps avoids model reloads
NUM_CTX = 16384
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


def verify(claim, context, model, num_ctx=NUM_CTX):
    """Step 2: is the paraphrased claim a scientific claim, judged together with its passage of the statement."""
    user = f"Twierdzenie: {claim}\nFragment wypowiedzi: {context}"
    body = llm.chat(load_prompt(VERIFY_PROMPT), user, SCHEMA_VERIFY, model, num_ctx=num_ctx, num_predict=32)
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
    text, _ = llm.truncate(text)
    cands = [{**c, "weryfikacja_v0": c.get("weryfikacja")} for c in row["kandydaci"]]
    t0 = time.perf_counter()
    out = {**row, **with_claims(verify_candidates(cands, text, model))}
    out["sekundy_weryfikacji"] = round(time.perf_counter() - t0, 2)
    return out


def load_prompt(name, max_candidates=MAX_CANDIDATES):
    return llm.load_prompt(name).replace("{max_kandydatow}", str(max_candidates))


def classify(text, system, model=DEFAULT_MODEL, schema=SCHEMA, num_ctx=NUM_CTX, timeout=600):
    """Returns the parsed answer plus run metadata; `blad` is set when the answer is not valid JSON or the context overflowed."""
    text, cut = llm.truncate(text)
    t0 = time.perf_counter()
    body = llm.chat(system, f"Wypowiedź:\n{text}", schema, model, num_ctx, timeout)
    meta = {"tokeny_we": body.get("prompt_eval_count"), "tokeny_wy": body.get("eval_count"), "num_ctx": num_ctx}
    try:
        answer = json.loads(body["message"]["content"])
        res = {**with_claims(verify_candidates(answer["kandydaci"], text, model)), "blad": None}
    except (json.JSONDecodeError, KeyError) as e:
        res = {"zawiera_twierdzenie": None, "twierdzenia": [], "blad": f"{e}: {body.get('message')}"}
    flag = llm.overflow(meta["tokeny_we"], meta["tokeny_wy"], num_ctx)
    if flag and not res["blad"]:
        res["blad"] = f"overflow: {flag}"
    return {**res, "obciete": cut, "sekundy": round(time.perf_counter() - t0, 2), **meta}
