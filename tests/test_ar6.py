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
