# Wykrywanie wypowiedzi o klimacie (krok 2)

Rozwój klasyfikatora tematycznego jako alternatywy dla `src/classify_topic.py` (Gemma 4 12B, prompt `topic_v0`, ok.
10 h na 43 991 wypowiedzi). Cel: szybszy klasyfikator (enkoder, zero-shot NLI albo model decyzyjny) przy co najmniej
tej samej jakości.

Ocena na próbie golda (`data/gold/`) z wagami warstw, jak w kroku 5. Próby golda nie używamy do uczenia ani do
dobierania promptów i progów.
