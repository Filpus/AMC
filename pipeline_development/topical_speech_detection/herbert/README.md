# HerBERT: fine-tuning klasyfikatora tematycznego

Fine-tuning `allegro/herbert-large-cased` (Hugging Face `transformers`, klasyfikacja sekwencji, 2 klasy) na zbiorze z
`../data/` do decyzji `klimat` dla całych wypowiedzi. Skrypt: `finetune_herbert.py`; środowisko: `../laya/.venv`
(ma `torch`, `transformers`, `pandas`, `scikit-learn`).

**Okna.** HerBERT czyta do 512 tokenów (ok. 330 słów), więc wypowiedź dzielimy na okna słów. Uczenie: dla `klimat = 1`
okno z fragmentem rozstrzygającym, dla `klimat = 0` kilka losowych okien. Predykcja: maksimum P(klimat) po oknach.

**Zasady** jak w `../laya/README.md`: te same foldy po posiedzeniu (ten sam seed), cross-fitting, syntetyczne tylko w
uczeniu, żadnego strojenia na goldzie, stałe hiperparametry.

**Wynik.** `runs/<nazwa>/final/` w formacie Hugging Face (`from_pretrained`, `push_to_hub`), `oof_predictions.csv`,
`run.json`. Modele foldów są domyślnie usuwane po predykcji (`--keep-folds`, by je zachować).
