# Clef-Flash: klasyfikator tematyczny zero-shot

Ocena `Cloudflare/clef-flash` (9B, BF16, Apache-2.0, https://huggingface.co/Cloudflare/clef-flash) bez uczenia na
zbiorze z `../data/` do decyzji `klimat`. Pytanie to samo co przy Layi (`../laya/finetune_laya.py`), ustalone przed
przebiegiem. Model nie jest uczony, więc wszystkie 850 wypowiedzi realnych to walidacja (bez foldów).

**Środowisko.** `../laya/.venv` (torch, transformers z `Qwen3_5ForConditionalGeneration`, huggingface_hub). Model
pobiera się przy pierwszym uruchomieniu do `~/.cache/huggingface` (ok. 18 GB); `HF_TOKEN` z `clef_flash/.env` albo
`laya/.env`. Na RTX 3090 (24 GB) pamięci jest mało: w razie OOM zmniejsz `--window`.

Uruchomienie (z katalogu `AMC`):

    pipeline_development/topical_speech_detection/laya/.venv/bin/python \
        pipeline_development/topical_speech_detection/clef_flash/eval_clef_flash.py --name v1

Szybki test: `--name smoke --limit 5`. Przerwany przebieg wznawia się od ostatniej wypowiedzi.

**Wynik.** `runs/<nazwa>/predictions.csv` (P(klimat) na wypowiedź) i `run.json` (porównanie z Gemmą: recall,
precyzja, AUC, próg przy recallu Gemmy, znane przeoczenia Gemmy w warstwie 3).

**Zasady:** golda nie używamy; promptu nie zmieniamy po obejrzeniu wyników bez osobnej połowy silver do walidacji.
