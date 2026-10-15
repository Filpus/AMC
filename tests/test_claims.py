import json
import logging

from amc import llm
from verify_claims import report

TEXT = "Wysoka Izbo! Polska emituje poniżej 1% CO2 na świecie, więc nasza redukcja nic nie zmieni. Dziękuję."


def fake_chat(content):
    def chat(system, user, schema, model, num_ctx, timeout, num_predict, think):
        fake_chat.schema, fake_chat.user = schema, user
        return {"message": {"content": content}, "prompt_eval_count": 1000, "eval_count": 50}
    return chat


def test_extract_claims_numbers_claims_and_checks_quotes(monkeypatch):
    claim = {"cytat": "Polska emituje poniżej 1% CO2 na świecie",
             "twierdzenie": "Polska odpowiada za mniej niż 1% światowej emisji CO2.",
             "twierdzenie_en": "Poland emits less than 1% of global CO2."}
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"twierdzenia": [claim, {**claim, "cytat": "wymyślone"}]})))
    res = llm.extract_claims(TEXT, ("s", "r"))
    assert res["blad"] is None and [c["nr"] for c in res["twierdzenia"]] == [1, 2]
    assert res["twierdzenia"][0]["cytat_w_tekscie"] == 1.0 and res["twierdzenia"][1]["cytat_w_tekscie"] < 0.5
    assert fake_chat.schema is llm.SCHEMA_CLAIMS


def test_judge_claim_maps_fragment_and_demotes_verdict_without_it(monkeypatch):
    frags = [{"etykieta": "WGI SPM A.1 (s. 4)", "tekst": "It is unequivocal..."}, {"etykieta": "WGI TS TS.1", "tekst": "x"}]
    claim = {"twierdzenie": "Wpływ człowieka jest znikomy.", "twierdzenie_en": "Human influence is negligible."}
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"uzasadnienie": "u", "ar6": 1, "werdykt": "sprzeczne"})))
    res = llm.judge_claim(claim, frags, ("s", "r"))
    assert res["werdykt"] == "sprzeczne" and res["ar6"] == "WGI SPM A.1 (s. 4)" and res["blad"] is None
    assert fake_chat.schema["properties"]["ar6"]["enum"] == [0, 1, 2] and "[2] WGI TS TS.1: x" in fake_chat.user
    monkeypatch.setattr(llm, "chat", fake_chat(json.dumps({"uzasadnienie": "u", "ar6": 0, "werdykt": "zgodne"})))
    res = llm.judge_claim(claim, frags, ("s", "r"))
    assert (res["werdykt"], res["werdykt_bez_ar6"], res["ar6"], res["blad"]) == ("brak_podstaw", "zgodne", "", None)


def test_report_counts_only_lines_without_error(tmp_path, caplog):
    rows = [{"twierdzenie_id": "w1", "oczekiwane": "zgodne", "werdykt": "zgodne", "ar6": "A.1", "werdykt_bez_ar6": None,
             "blad": None},
            {"twierdzenie_id": "w2", "oczekiwane": "sprzeczne", "werdykt": "brak_podstaw", "ar6": "",
             "werdykt_bez_ar6": "sprzeczne", "blad": None},
            {"twierdzenie_id": "w3", "oczekiwane": "sprzeczne", "werdykt": "sprzeczne", "ar6": "",
             "blad": "werdykt sprzeczne bez fragmentu ar6"}]
    path = tmp_path / "tests.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    with caplog.at_level(logging.INFO, logger="verify_claims"):
        report(path)
    assert "tests: 1/2 as expected, 1 with an error" in caplog.text
    assert "ERROR w3" in caplog.text and "WRONG w2" in caplog.text and "WRONG w1" not in caplog.text
    assert "said sprzeczne without a fragment" in caplog.text
