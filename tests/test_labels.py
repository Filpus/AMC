import numpy as np
import pandas as pd

from label_statements import label


def test_label_statements():
    klimat = [{"wypowiedz_id": i, "klimat": k, "blad": None} for i, k in [("a", 1), ("b", 1), ("c", 0), ("d", 1)]]
    c = lambda nr: {"nr": nr, "cytat": "", "cytat_w_tekscie": 1.0, "twierdzenie": "t", "twierdzenie_en": "t"}
    claims = [{"wypowiedz_id": "a", "blad": None, "twierdzenia": [c(1), c(2)]},
              {"wypowiedz_id": "b", "blad": None, "twierdzenia": [c(1)]}]
    verdicts = [{"twierdzenie_id": "a#1", "werdykt": "sprzeczne", "ar6": "x", "uzasadnienie": "", "blad": None},
                {"twierdzenie_id": "a#2", "werdykt": "zgodne", "ar6": "z", "uzasadnienie": "", "blad": None},
                {"twierdzenie_id": "b#1", "werdykt": "zgodne", "ar6": "y", "uzasadnienie": "", "blad": None}]
    meta = pd.DataFrame({"wypowiedz_id": list("abcde"), "grupa": ["prawica", "reszta", "reszta", "prawica", "reszta"],
                         "klub": ["PiS", "KO", "KO", "PiS", "KO"]})
    st, cl = label(klimat, claims, verdicts, meta)
    s = st.set_index("wypowiedz_id")
    assert s.loc["a", "sprzeczna"] == 1 and s.loc["b", "sprzeczna"] == 0 and s.loc["c", "sprzeczna"] == 0
    assert np.isnan(s.loc["d", "sprzeczna"])  # klimat = 1, claims not extracted yet
    assert s.loc["a", "n_ocenianych"] == 2 and len(cl) == 3
    assert list(st["wypowiedz_id"]) == list("abcd") and s.loc["a", "klub"] == "PiS"
