# Warstwa 3: test drugiego klasyfikatora

Czy podział warstwy 3 (model: nietematyczna) na 3a / 3b ma sens? Skrypt ocenia każdą wypowiedź z warstwy 3
fine-tunowaną Layą (`../topical_speech_detection/laya/runs/v2`) i dwoma regexami, a potem podaje rozmiary 3a / 3b
w grupach oraz ile znanych przeoczeń modelu (silver: `klimat = 1` w warstwie 3) łapie każdy wariant.

Uruchomienie (z katalogu `AMC`, środowisko Layi, GPU):

    pipeline_development/topical_speech_detection/laya/.venv/bin/python \
        pipeline_development/stratum_testing/screen_stratum3.py

Przerwany przebieg wznawia się od ostatniej zapisanej porcji. Szybki test: `--limit 40`.

Wynik w `out/`: `summary.md` (tabela 3a / 3b) i `laya_p_stratum3.csv` (prawdopodobieństwa i flagi regexów).

Próby golda nie używamy do wyboru progu ani wariantu; skrypt tylko pokazuje, gdzie trafiają wypowiedzi golda.
