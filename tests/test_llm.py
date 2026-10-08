import json

from amc import llm

CANDIDATES = [
    {"cytat": "Smog zabija.", "rodzaj": "naukowe", "twierdzenie": "Smog powoduje przedwczesne zgony.", "temat": "smog",
     "atrybucja": "wlasne"},
    {"cytat": "Szczepionki powodują autyzm.", "rodzaj": "naukowe", "twierdzenie": "Szczepionki powodują autyzm.",
     "temat": "szczepienia", "atrybucja": "cytat_polemika"},
    {"cytat": "Budżet wzrósł o 5%.", "rodzaj": "budzet", "twierdzenie": "Budżet wzrósł o 5%.", "temat": "brak",
     "atrybucja": "wlasne"},
]


def fake_chat(answer, verdicts, tokens_in=5000):
    def chat(system, user, schema, model, *args, **kwargs):
        if schema is llm.SCHEMA_VERIFY:
            return {"message": {"content": json.dumps({"naukowe": verdicts.pop(0)})}}
        return {"message": {"content": answer}, "prompt_eval_count": tokens_in, "eval_count": 300}
    return chat


def test_overflow():
    assert llm.overflow(4098, 500, 8192) == "przepelnienie"
    assert llm.overflow(7650, 635, 8192) == "przesuniecie"
    assert llm.overflow(7650, 500, 8192) is None
    assert llm.overflow(None, None, 8192) is None


def test_schema_candidate_limit():
    assert llm.schema_for(8)["properties"]["kandydaci"]["maxItems"] == 8
    assert llm.SCHEMA["properties"]["kandydaci"]["maxItems"] == llm.MAX_CANDIDATES


def test_classify_keeps_only_verified_scientific_candidates(monkeypatch):
    verdicts = [True, False]
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"kandydaci": CANDIDATES}), verdicts))
    res = llm.classify("Smog zabija. Szczepionki powodują autyzm. Budżet wzrósł o 5%.", "system")
    assert res["blad"] is None and res["zawiera_twierdzenie"] == 1
    assert [c["weryfikacja"] for c in res["kandydaci"]] == [True, False, None]
    assert [c["twierdzenie"] for c in res["twierdzenia"]] == ["Smog powoduje przedwczesne zgony."]
    assert res["prompt_weryfikacji"] == llm.VERIFY_PROMPT and res["num_ctx"] == llm.NUM_CTX and not verdicts


def test_classify_reports_invalid_answer_and_overflow(monkeypatch):
    monkeypatch.setattr(llm, "chat", fake_chat("{nie json", []))
    assert llm.classify("Tekst.", "system")["blad"].startswith("Expecting")
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"kandydaci": []}), [], tokens_in=llm.NUM_CTX // 2 + 2))
    res = llm.classify("Tekst.", "system")
    assert res["blad"] == "overflow: przepelnienie" and res["zawiera_twierdzenie"] == 0
