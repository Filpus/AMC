import json
import re

import pandas as pd
import pytest

from amc import annotation as A
from amc import corpus
from gold_standard import draw, page


def design(n=100):
    return pd.DataFrame({"kolejnosc": range(1, n + 1), "wypowiedz_id": [f"10_1_2024-01-0{i % 9 + 1}_{i}" for i in range(n)]})


def write(tmp_path, rows, name="a.csv", proba=None):
    df = pd.DataFrame(rows, columns=["kolejnosc", "tematyczna", "sprzeczna"])
    if proba:
        df["proba"] = proba
    path = tmp_path / name
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def full(n=100, contradicting=()):
    return [(k, 1 if k <= 30 else 0, (1 if k in contradicting else 0) if k <= 30 else "") for k in range(1, n + 1)]


def test_load_complete_file(tmp_path):
    d = design()
    ann = A.load(write(tmp_path, full(contradicting={1, 2}), proba=A.sample_id(d)), d)
    assert len(ann) == 100 and ann["koncowa"].sum() == 2 and ann["tematyczna"].sum() == 30
    assert ann.loc[ann["tematyczna"] == 0, "sprzeczna"].isna().all()
    assert ann.set_index("kolejnosc").loc[1, "wypowiedz_id"] == d.set_index("kolejnosc").loc[1, "wypowiedz_id"]


def test_load_refuses_bad_files(tmp_path):
    d = design()
    with pytest.raises(ValueError, match="without `tematyczna`"):
        A.load(write(tmp_path, full()[:99]), d)
    with pytest.raises(ValueError, match="without `sprzeczna`"):
        A.load(write(tmp_path, [(1, 1, "")] + full()[1:]), d)
    with pytest.raises(ValueError, match="not topical"):
        A.load(write(tmp_path, full()[:99] + [(100, 0, 1)]), d)
    with pytest.raises(ValueError, match="another gold sample"):
        A.load(write(tmp_path, full(), proba="0000000000"), d)
    with pytest.raises(ValueError, match="0, 1 or empty"):
        A.load(write(tmp_path, [(1, "tak", "")] + full()[1:]), d)
    assert len(A.load(write(tmp_path, full()[:40]), d, required=range(1, 41))) == 40


def test_load_parts_of_a_split_sample(tmp_path):
    d = design()
    rows = full(contradicting={1, 40})
    blank = lambda part: [(k, "", "") for k, *_ in part]
    first = write(tmp_path, rows[:50] + blank(rows[50:]), "annotations_AA.csv")
    second = write(tmp_path, blank(rows[:50]) + rows[50:], "annotations_BB.csv")
    assert A.labelled(first, d) == set(range(1, 51))
    ann = A.load_parts([first, second], d)
    assert len(ann) == 100 and ann["koncowa"].sum() == 1
    assert ann.groupby("anotator").size().to_dict() == {"AA": 50, "BB": 50}
    with pytest.raises(ValueError, match="in none of the files"):
        A.load_parts([first, write(tmp_path, blank(rows[:50]) + rows[50:99], "annotations_CC.csv")], d)
    with pytest.raises(ValueError, match="more than one file"):
        A.load_parts([first, write(tmp_path, rows, "annotations_DD.csv")], d)


def test_kappa_subsample_tops_up_contradicting(tmp_path):
    d = design()
    ann = A.load(write(tmp_path, full(contradicting=set(range(1, 13)))), d)
    order, topped = A.kappa_subsample(ann, seed=3)
    picked = ann.set_index("kolejnosc").loc[order]
    assert len(set(order)) == len(order) == A.KAPPA_SIZE + topped
    assert picked["koncowa"].sum() >= A.KAPPA_MIN_CONTRADICTING
    few = A.load(write(tmp_path, full(contradicting={1, 2, 3})), d)
    order, topped = A.kappa_subsample(few, seed=3)
    assert set(range(1, 4)) <= set(order) and len(order) == A.KAPPA_SIZE + topped


def test_agreement_lists_disagreements(tmp_path):
    d = design()
    a1 = A.load(write(tmp_path, full(contradicting={1, 2}), "a1.csv"), d)
    rows = full(contradicting={1})[:40]
    a2 = A.load(write(tmp_path, rows[:30] + [(31, 1, 0)] + rows[31:], "a2.csv"), d, required=range(1, 41))
    table, diff = A.agreement(a1, a2)
    assert table["n"].tolist() == [40, 40]
    assert diff["kolejnosc"].tolist() == [2, 31]


def test_page_is_blind():
    d = design(3)
    texts = pd.DataFrame({"kolejnosc": [1, 2, 3], "tekst": ["Poseł …:\nKlimat się zmienia.", "Drugi tekst.", "</script>"]})
    html = page(texts, d, "annotations", "Gold standard", order=[3, 1])
    data = json.loads(re.search(r"const ROWS = (\[.*?\]);\n", html).group(1).replace("<\\/", "</"))
    assert [r["kolejnosc"] for r in data] == [3, 1]
    assert A.sample_id(d) in html and not re.search(r"__[A-Z]+__", html)
    assert not any(i in html for i in d["wypowiedz_id"]) and "</script>\"" not in html


def test_draw_only_from_labels_of_the_whole_population(tmp_path, monkeypatch):
    statements = pd.DataFrame({"wypowiedz_id": [f"10_1_2024-05-0{i}_1" for i in range(1, 5)], "member_id": 1,
                               "data": pd.Timestamp("2024-05-01"), "merytoryczna": True, "klub": ["PiS", "KO"] * 2,
                               "tekst": [f"Poseł Jan Kowalski:\nKlimat {i}." for i in range(4)]})
    monkeypatch.setattr(corpus, "load", lambda kind: statements)
    labels = statements[["wypowiedz_id"]].assign(grupa=["prawica", "reszta"] * 2, klimat=[1, 1, 0, 0],
                                                 sprzeczna=[1.0, 0.0, 0.0, 0.0])
    with pytest.raises(SystemExit, match="cover 3 of 4"):
        draw(labels.iloc[:3], 0, tmp_path / "sample.csv")
    assert not (tmp_path / "sample.csv").exists()
    draw(labels, 0, tmp_path / "sample.csv")
    texts = pd.read_csv(tmp_path / "texts.csv")
    assert len(texts) == 4 and texts["tekst"].str.startswith("Poseł …:").all()
