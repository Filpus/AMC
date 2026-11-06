# Laya: fine-tuning klasyfikatora tematycznego

Fine-tuning modelu Laya (`pip install laya`, repozytorium https://github.com/NandhaKishorM/laya, licencja Apache 2.0)
na zbiorze z `../data/` do decyzji `klimat` (tak/nie) dla całych wypowiedzi.

**Środowisko.** Osobne `laya/.venv` (Python 3.14, `laya`, PyTorch z CUDA, pandas, scikit-learn); nie instalować Laya w
`AMC/.venv`, bo nowsze `transformers` wymagają innych wersji `tokenizers` i `click` niż `litellm` z pipeline'u.

**API.** `from laya.train import TrainConfig, finetune`; `finetune(data, model_dir, output_dir, config)` trenuje,
kalibruje temperaturę i zapisuje checkpoint. Dane: JSONL `{state, questions, expected}` albo CSV z kolumnami tekstu i
etykiety (`TrainConfig.text_column`, `label_column`). Punkt wyjścia: alias `multilingual` (enkoder mmBERT-base, kontekst
domyślnie 1024 tokeny, do 8192 przez `max_len`).

**Zasady** (jak w `../README.md`):
- próba golda nie służy do uczenia ani do wyboru progów i hiperparametrów;
- foldy po posiedzeniu (`kadencja` + `posiedzenie`), stratyfikowane etykietą, budowane w skrypcie treningowym;
- etykiety populacji dla wypowiedzi treningowych z cross-fittingu (model foldu, który ich nie widział); model końcowy na
  całym zbiorze etykietuje pozostałe wypowiedzi;
- wypowiedzi syntetyczne tylko w części treningowej każdego foldu.

**Stan danych (2026-10-28).** Etykiety 850 wypowiedzi realnych (Opus, bez relabelu niepewnych) i 150 syntetycznych.
Etap 5 (relabel 334 niepewnych po dodaniu reguł granicznych) odłożony; po nim trening trzeba powtórzyć.
