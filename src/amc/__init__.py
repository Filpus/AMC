"""AMC — analiza wypowiedzi sejmowych pod kątem zgodności z konsensusem naukowym.

Pakiet zawiera całą logikę przetwarzania (bez efektów ubocznych przy imporcie):
  paths     ścieżki projektu i stałe kadencji
  http      pobieranie z API Sejmu z ponawianiem, zapis atomowy
  text      konwersja HTML -> tekst, czyszczenie wypowiedzi, fragmenty z kontekstem (kwic)
  speakers  rola mówcy, dopasowanie posłów, klub na dzień wypowiedzi, bloki polityczne
  topics    słowniki tematów i markery (nauka, sceptycyzm), kolumny tematyczne
  corpus    budowa i wczytywanie korpusu gotowego do analizy (data/processed/korpus_*.parquet)
  viz       styl i paleta wykresów

Skrypty w src/ (fetch_sejm.py, fetch_komisje.py, build_corpus.py, report_sceptycyzm.py) to cienkie
nakładki CLI na ten pakiet.
"""
