import json

import pandas as pd

import classify_topic as K
from amc import llm, runs

TEXT = "Wysoka Izbo! Zmiana klimatu powoduje coraz dłuższe susze. Dziękuję."


def fake_chat(content, calls, tokens_in=1000):
    def chat(system, user, schema, model, num_ctx, timeout, num_predict, think):
        calls.append({"system": system, "user": user, "schema": schema, "think": think})
        return {"message": {"content": content}, "prompt_eval_count": tokens_in, "eval_count": 20}
    return chat


def test_classify_topic_parses_answer_and_checks_fragment(monkeypatch):
    calls = []
    answer = json.dumps({"fragment": "Zmiana klimatu powoduje coraz dłuższe susze.", "klimat": 1})
    monkeypatch.setattr(llm, "chat", fake_chat(answer, calls))
    res = llm.classify_topic(TEXT, ("system", "Przypomnienie."))
    assert res["klimat"] == 1 and res["blad"] is None and res["fragment_w_tekscie"] == 1.0
    assert calls[0]["schema"] is llm.SCHEMA_TOPIC and calls[0]["think"] is False
    assert calls[0]["user"].startswith("Wypowiedź:\n" + TEXT) and calls[0]["user"].endswith("Przypomnienie.")


def test_classify_topic_empty_fragment_invalid_answer_and_overflow(monkeypatch):
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"fragment": "", "klimat": 0}), []))
    res = llm.classify_topic(TEXT, ("s", "r"))
    assert res["klimat"] == 0 and res["fragment_w_tekscie"] is None
    monkeypatch.setattr(llm, "chat", fake_chat("{nie json", []))
    assert llm.classify_topic(TEXT, ("s", "r"))["blad"].startswith("JSONDecodeError")
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"fragment": "", "klimat": 0}), [], llm.TOPIC_NUM_CTX // 2 + 2))
    assert llm.classify_topic(TEXT, ("s", "r"))["blad"] == "overflow: przepelnienie"


def test_topic_prompt_splits_into_codebook_and_reminder():
    system, reminder = llm.load_topic_prompt("topic_v0")
    assert "## Etykieta: klimat" in system and llm.REMINDER_HEADER not in system
    assert reminder and "klimat" in reminder


def test_output_names_and_fingerprint():
    assert runs.out_path("topic", "topic_v0", "SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M").name == \
        "topic_v0__SpeakLeash_bielik-11b-v3.0-instruct_Q4_K_M.jsonl"
    assert runs.out_path("topic", "topic_v0", "gemma4:12b", "__tests").name == "topic_v0__gemma4_12b__tests.jsonl"
    assert runs.fingerprint(["b", "a"]) == runs.fingerprint(["a", "b"]) != runs.fingerprint(["a"])


def test_test_cases_are_well_formed():
    t = pd.read_csv(K.TESTS, dtype=str, keep_default_na=False)
    assert t["test"].is_unique and set(t["oczekiwane"]) == {"0", "1"}
    assert ((t["wypowiedz_id"] != "") ^ (t["tekst"] != "")).all()
    pairs = t[t["regula"].str.startswith("para:")]
    assert (pairs.groupby("regula")["oczekiwane"].apply(set) == {"0", "1"}).all()
