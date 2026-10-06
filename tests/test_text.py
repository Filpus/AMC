import re

import pandas as pd

from amc.text import clean_statement, highlight_segments, html_to_text, kwic, word_count


def test_html_to_text_paragraphs_and_entities():
    assert html_to_text("<p>Pierwszy&nbsp;akapit</p><p>Drugi <b>akapit</b></p>") == "Pierwszy akapit\nDrugi akapit"
    assert html_to_text(None) == ""


def test_clean_statement_removes_header_interjections_and_footer():
    surowy = ("9. kadencja, 36. posiedzenie\n34. punkt porządku dziennego: Informacja w sprawie Programu Szczepień\n"
              "Poseł Jan Kowalski:\nWysoka Izbo! (Oklaski) To ważne. (Poseł Anna Nowak: Nieprawda!)\nPrzebieg posiedzenia")
    assert clean_statement(surowy, "Jan Kowalski") == "Wysoka Izbo! To ważne."


def test_clean_statement_without_speaker_label_keeps_text():
    assert clean_statement("Tekst (Oklaski) dalej", "Ktoś Inny") == "Tekst dalej"
    assert clean_statement(None) == ""


def test_word_count():
    assert word_count(pd.Series(["a b c", "", None])).tolist() == [3, 0, 0]


def test_kwic_and_highlight():
    rx = re.compile(r"szczepion\w*")
    assert kwic("Mówimy o Szczepionkach dziś", rx, w=5) == "…my o **Szczepionkach** dziś"
    frag = highlight_segments("x " * 10 + "szczepionka i szczepionki", rx, window=3, merge=20)
    assert len(frag) == 1 and [t for t, m in frag[0] if m] == ["szczepionka", "szczepionki"]
