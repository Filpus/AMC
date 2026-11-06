# Anotacja gold standardu: instrukcja dla anotatora

Jesteś anotatorem gold standardu w projekcie badawczym o wypowiedziach posłów na posiedzeniach plenarnych Sejmu RP
(X kadencja, 2023–2026). Dla każdej wypowiedzi ustalasz dwie etykiety według codebooka, który jest dalej w tym pliku:

- `tematyczna` (to samo co `klimat`, sekcja 3): `1` albo `0`;
- `sprzeczna` (sekcje 4–6): `1`, jeśli co najmniej jedno twierdzenie wypowiedzi (stanowisko mówcy) jest `sprzeczne`
  z AR6, inaczej `0`; tylko przy `tematyczna = 1` (przy `tematyczna = 0` wpisz `null`).

Jednostka to merytoryczne wystąpienie jednego mówcy na posiedzeniu plenarnym. Źródło konsensusu to AR6 IPCC, raporty
WGI, WGII i WGIII, tylko Summary for Policymakers (SPM) i Technical Summary (TS).

## Zasady pracy

1. **Anotacja jest ślepa.** Czytasz tylko ten plik i swój plik z wypowiedziami. Nie otwieraj żadnych innych plików w
   repozytorium (danych, wyników modeli, anotacji innych osób, kodu poza narzędziem niżej).
2. **Werdykt tylko z AR6.** Werdykt opierasz wyłącznie na tekście AR6 znalezionym narzędziem poniżej, nie na własnej
   wiedzy. Werdykt `sprzeczne` albo `zgodne` wymaga etykiety ustalenia (np. `WGI SPM A.1`) i dosłownego cytatu
   skopiowanego z wyniku narzędzia (jeden ciągły fragment, 1–2 zdania, bez zmian). Jeśli nie znajdziesz fragmentu,
   który rozstrzyga twierdzenie według sekcji 6, werdykt to `brak_podstaw`.
3. **Szukaj po angielsku.** Dla każdego twierdzenia, które AR6 mógłby potwierdzić albo mu zaprzeczyć, wykonaj co
   najmniej jedno wyszukiwanie; przeformułuj zapytanie, jeśli wyniki nie pasują. Twierdzeń, którym sekcja 6 z góry
   daje `brak_podstaw` (np. skutki dla gospodarki albo cen jednego kraju), nie musisz sprawdzać. Polecenia (Bash):

   ```
   cd /c/Studia/II_stopien/2_sem/Analiza_mediow_cyfrowych/Laby/AMC
   PYTHONIOENCODING=utf-8 .venv/Scripts/python src/ar6_search.py "query in English"     # 6 najbliższych ustaleń
   PYTHONIOENCODING=utf-8 .venv/Scripts/python src/ar6_search.py --id "WGIII TS TS.5.1"  # ustalenie po etykiecie
   PYTHONIOENCODING=utf-8 .venv/Scripts/python src/ar6_search.py --grep "regex"         # wyszukiwanie dosłowne
   ```

   Opcja `-k N` zmienia liczbę wyników. Etykieta w wyniku (np. `WGI TS TS.4.3.2.5 (s. 108)`) to identyfikator, który
   wpisujesz w pole `ar6` (bez numeru strony).
4. **Tekst.** Nazwiska w etykietach mówców są zamaskowane. Nie zgaduj mówcy ani klubu; oceniaj treść.
5. **Wątpliwości.** Przy wątpliwości wybierz etykietę, ustaw `"pewnosc": "niska"` i opisz wątpliwość w `komentarz`.
   Żadnej wypowiedzi nie pomijaj.
6. **Twierdzenia.** Wypisz twierdzenia według sekcji 4 i 5 (stanowisko mówcy, parafraza samodzielna), także te z
   werdyktem `brak_podstaw`. Tego, co sekcja 4 każe pominąć, nie wypisuj. Przy `tematyczna = 0` lista jest pusta.

## Format wyniku

Plik JSON Lines: jedna linia na wypowiedź, w kolejności z pliku wejściowego, bez innych linii:

```
{"kolejnosc": 17, "tematyczna": 1, "fragment": "dosłowny fragment wypowiedzi, który przesądza o tematyczności", "uzasadnienie_tematycznosci": "1–2 zdania z odwołaniem do reguły z sekcji 3", "twierdzenia": [{"cytat": "dosłowny fragment wypowiedzi", "twierdzenie": "parafraza samodzielna", "werdykt": "sprzeczne", "ar6": "WGIII TS TS.5.1", "ar6_cytat": "dosłowny cytat z AR6", "uzasadnienie": "1–2 zdania"}], "sprzeczna": 1, "pewnosc": "wysoka", "komentarz": ""}
```

- `fragment`: przy `tematyczna = 0` pusty albo fragment najbliższy granicy;
- `ar6` i `ar6_cytat`: puste przy `brak_podstaw`;
- `pewnosc`: `wysoka` albo `niska` (dotyczy obu etykiet wypowiedzi);
- teksty w JSON-ie zapisuj poprawnie (cudzysłowy wewnątrz jako `\"`).

Dalej codebook projektu (sekcje 2–6 i 9) bez zmian.

---

