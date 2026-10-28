import numpy as np
import pandas as pd

from amc import ar6

FILLER = "The assessed evidence indicates that observed changes are consistent with the expected response here."


def test_split_pages_by_finding_number_and_reference_braces():
    pages = [f"6\nSPM\nSummary for Policymakers\nA.1  It is unequivocal that human influence has warmed the climate.\n"
             f"{FILLER}\n{FILLER} {{2.2, 2.3}}\nA.1.1 Observed increases in well-mixed greenhouse gas concentrations "
             f"since 1750 are unequivocally caused by human activities.\n{FILLER} {{2.2, 5.2}}",
             "0.5\n1.0\n1.5\nºC"]
    out = ar6.split_pages(pages, "WGI", "SPM")
    assert [f["numer"] for f in out] == ["A.1", "A.1.1"] and out[0]["strona"] == 1
    assert out[0]["tekst"].startswith("A.1 It is unequivocal") and "Summary for Policymakers" not in out[0]["tekst"]


def test_split_pages_evens_out_long_findings():
    out = ar6.split_pages(["TS.2 " + " ".join(["word"] * 260) + " {2.1}"], "WGI", "TS")
    assert len(out) == 2 and all(len(f["tekst"].split()) >= 100 for f in out)


def test_bm25_and_rrf():
    bm = ar6.BM25(["sea level rise accelerated", "heavy precipitation increased", "sea ice declined"])
    assert np.argmax(bm.scores("sea level")) == 0
    assert ar6.rrf([[0, 1, 2], [1, 0, 2], [1, 2, 0]])[:2] == [1, 0]


def test_index_search_takes_spm_and_ts_parts():
    df = pd.DataFrame({"czesc": ["SPM", "TS", "SPM", "TS"], "tekst": ["a", "b", "c", "d"], "etykieta": list("ABCD")})
    vec = np.eye(4, dtype=np.float32)
    idx = ar6.Index(df, vec)
    res = idx.search("x", query_vectors=np.array([[0.1, 0.2, 0.9, 0.4]], dtype=np.float32), per_part=1)
    assert res["etykieta"].tolist() == ["C", "D"]


def test_search_methods():
    df = pd.DataFrame({"czesc": ["SPM", "SPM", "SPM"], "etykieta": list("ABC"),
                       "tekst": ["sea level rise", "heavy precipitation", "glacier retreat"]})
    vec = np.eye(3, dtype=np.float32)
    pl, en = np.array([[1, 0, 0]], dtype=np.float32), np.array([[0, 1, 0]], dtype=np.float32)
    top = lambda method, qv: ar6.Index(df, vec, method=method).search("pl", "glacier", 1, query_vectors=qv)["etykieta"].item()
    assert top("pl", pl) == "A" and top("en", en) == "B" and top("bm25", None) == "C"
    assert top("rrf", np.vstack([pl, pl])) == "A"
    assert ar6.query_texts("en", "pl", "en") == ["en"] and ar6.query_texts("bm25", "pl", "en") == []
    assert ar6.query_texts("rrf", "pl", "en") == ["pl", "en"]
    assert ar6.Index(df, method="bm25").vec is None


def test_model_prefixes_for_queries_and_documents(monkeypatch):
    sent = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"embeddings": [[1.0, 0.0]] * len(sent[-1])}

    monkeypatch.setattr(ar6.requests, "post", lambda url, json, timeout: sent.append(json["input"]) or Response())
    ar6.embed(["claim"], "qwen3-embedding:8b", query=True)
    ar6.embed(["fragment"], "qwen3-embedding:8b")
    ar6.embed(["claim"], "bge-m3", query=True)
    ar6.embed(["claim"], "embeddinggemma:300m", query=True)
    ar6.embed(["fragment"], "embeddinggemma:300m")
    assert sent[0][0].startswith("Instruct: ") and sent[0][0].endswith("Query: claim")
    assert sent[1] == ["fragment"] and sent[2] == ["claim"]
    assert sent[3] == ["task: fact checking | query: claim"] and sent[4] == ["title: none | text: fragment"]
