from string import Formatter

from amc import llm, runs
from verify_claims_paperqa import parse_answer

PAPERQA_QA_VARIABLES = {"context", "answer_length", "question", "example_citation", "prior_answer_prompt"}


def test_verdict_with_citation():
    r = parse_answer("Sprzeczne. AR6 stwierdza, że ocieplenie zależy od emisji (WGI_SPM pages 28-29).", ["WGI_SPM pages 28-29"])
    assert r["werdykt"] == "sprzeczne" and r["ar6"] == "WGI_SPM pages 28-29" and r["blad"] is None


def test_first_label_wins():
    assert parse_answer("`brak_podstaw` Fragmenty nie są sprzeczne ani zgodne.", [])["werdykt"] == "brak_podstaw"
    assert parse_answer("Zgodne: nie jest to sprzeczne z AR6.", ["WGI_TS pages 7-7"])["werdykt"] == "zgodne"


def test_verdict_without_citation_becomes_no_basis():
    r = parse_answer("zgodne. Model nie podał źródła.", [])
    assert r["werdykt"] == "brak_podstaw" and r["werdykt_bez_ar6"] == "zgodne"


def test_cannot_answer_and_missing_label():
    assert parse_answer("I cannot answer this question due to insufficient information.", [])["werdykt"] == "brak_podstaw"
    r = parse_answer("The reports discuss emissions.", [])
    assert r["werdykt"] is None and r["blad"].startswith("no verdict")


def test_prompt_uses_paperqa_variables_only():
    prompt = llm.load_prompt(runs.PAPERQA_PROMPT)
    fields = {f for _, f, _, _ in Formatter().parse(prompt) if f is not None}
    assert {"context", "question"} <= fields <= PAPERQA_QA_VARIABLES
    prompt.format(context="c", answer_length="about 120 words", question="q", example_citation="(pqac-0f650d59)",
                  prior_answer_prompt="")


def test_labels_path():
    assert runs.labels_path("gemma4:12b").name == "gemma4_12b.csv"
    assert runs.labels_path("gemma4:12b", runs.PAPERQA_PROMPT).name == "gemma4_12b__paperqa_v0.csv"
