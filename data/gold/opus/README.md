# Gold poprawiany Opusem (05.11)

Ślepa anotacja starego golda (100 wypowiedzi, `data/gold/texts.csv`) przez subagentów Claude Code (Opus) według
nowego codebooka; niezgodności z FP/DK rozstrzyga Damian. Decyzje Damiana (05.11): ślepo + rozstrzyganie przez
człowieka, oba goldy (stary teraz, nowy z warstw przebiegu v2 potem).
Przebiegi 2–3 nie zostały wykonane (decyzja 05.11); obowiązuje przebieg 1.

## Pliki

| plik | co to |
|---|---|
| `header.md` | zasady pracy anotatora i format JSONL (napisane przez Claude'a) |
| `instrukcja.md` | `header.md` + codebook, sekcje 2–6 i 9, dosłownie (sekcja 1 pominięta: hipoteza i grupy) |
| `instrukcja.sha256` | zamrożenie: `72f87359bcee1db9668e1337c373510c7cc151e51f40610540aa0f21d4d73fb5` |
| `batches/run1_b00–b09.md` | po 10 wypowiedzi, potasowane (ziarno 1) |
| `out/run*_b*.jsonl` | wyniki subagentów: etykiety, fragment, twierdzenia z werdyktem i cytatem AR6, pewność, komentarz |
| `pilot/` | pilot na 3 wypowiedziach spoza golda i codebooka |
| `check.py` | sprawdzenie (cytaty z wypowiedzi i AR6 dosłowne, spójność etykiet z werdyktami), większość, porównanie z FP/DK |
| `niezgodnosci.csv`, `porownanie.csv`, `llm_claims.csv` | wyjście `check.py --compare` (teraz tylko z przebiegu 1) |

Wyszukiwarka AR6 dla anotatora: `src/ar6_search.py` (BM25 + EmbeddingGemma przez Ollamę na porcie 11434, `--id`,
`--grep`), niezacommitowana.

## Stan

- Pilot (3 wypowiedzi): bez problemów; po nim do `header.md` dopisane zdanie, że twierdzeń, którym sekcja 6 z góry
  daje `brak_podstaw`, nie trzeba sprawdzać w AR6. Potem zamrożenie.
- **Przebieg 1: gotowy** (10 subagentów, ok. 3–7 min każdy, ok. 2,4 mln tokenów łącznie). `check.py`: 0 problemów,
  100 wypowiedzi, 177 twierdzeń (brak_podstaw 131, zgodne 28, sprzeczne 18); tematyczne 50, sprzeczne 11.
  Wobec FP/DK: tematyczność zgodność 0,83, κ 0,66; etykieta końcowa 0,94, κ 0,75. Niezgodności 23:
  - LLM tematyczna, ludzie nie (16): #17, #18, #19, #62, #93, #14, #41, #47, #29, #9, #22, #34, #86, #96, #5
    (zgodnie z listą skutków codebooka z 04.11) oraz #60 (nowa);
  - ludzie tematyczna, LLM nie: #56;
  - ludzie sprzeczna, LLM nie (6): #36, #94 (jak przewidziano 04.11), #59 (otwarte), #23, #27, #71 (nowe);
  - LLM sprzeczna, ludzie nie: 0.
- Uwagi subagentów do codebooka: poparcie cudzego tytułu („Klimatyczne oszustwo”) bez wypowiedzianej tezy — przyjęta
  cudza teza (1/1) czy epitet (0)? Przy #64 wyszukiwarka nie znalazła ustaleń AR6 o suszy dla WCE (WGI TS.4.3.2.5),
  więc `brak_podstaw` zamiast raczej `zgodne` — sprawdzić przy rozstrzyganiu.

## Dalej

1. Damian rozstrzyga niezgodności; wynik do nowego pliku (np. `data/gold/annotations_final.csv` z kolumną źródła),
   `annotations_FP.csv` i `annotations_DK.csv` bez zmian; w raporcie obie wersje i ujawnienie użycia LLM-a.
2. Nowy gold z warstw przebiegu v2: `gold_standard.py losuj --proba data/gold/v2/sample.csv --werdykt-prompt
   verdict_v2` (stary `sample.csv` nietknięty), ta sama procedura.
