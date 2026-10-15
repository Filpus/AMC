import json

from amc import llm, stage_a

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
        if schema is stage_a.SCHEMA_VERIFY:
            return {"message": {"content": json.dumps({"naukowe": verdicts.pop(0)})}}
        return {"message": {"content": answer}, "prompt_eval_count": tokens_in, "eval_count": 300}
    return chat


def test_schema_candidate_limit():
    assert stage_a.schema_for(8)["properties"]["kandydaci"]["maxItems"] == 8
    assert stage_a.SCHEMA["properties"]["kandydaci"]["maxItems"] == stage_a.MAX_CANDIDATES


def test_classify_keeps_only_verified_scientific_candidates(monkeypatch):
    verdicts = [True, False]
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"kandydaci": CANDIDATES}), verdicts))
    res = stage_a.classify("Smog zabija. Szczepionki powodują autyzm. Budżet wzrósł o 5%.", "system")
    assert res["blad"] is None and res["zawiera_twierdzenie"] == 1
    assert [c["weryfikacja"] for c in res["kandydaci"]] == [True, False, None]
    assert [c["twierdzenie"] for c in res["twierdzenia"]] == ["Smog powoduje przedwczesne zgony."]
    assert res["prompt_weryfikacji"] == stage_a.VERIFY_PROMPT and res["num_ctx"] == stage_a.NUM_CTX and not verdicts


def test_classify_reports_invalid_answer_and_overflow(monkeypatch):
    monkeypatch.setattr(llm, "chat", fake_chat("{nie json", []))
    assert stage_a.classify("Tekst.", "system")["blad"].startswith("Expecting")
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"kandydaci": []}), [], tokens_in=stage_a.NUM_CTX // 2 + 2))
    res = stage_a.classify("Tekst.", "system")
    assert res["blad"] == "overflow: przepelnienie" and res["zawiera_twierdzenie"] == 0
