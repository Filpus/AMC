# Progress: topical speech detection dataset

- Current stage: 5 PAUSED (2026-10-28, user decision: go to fine-tuning first, relabel later). Stage 4 DONE: 850 real
  statements labelled by 5 parallel Opus labellers (`labels_part1-5.jsonl`, merged into `labels.jsonl`; all checks
  pass): 453 positives, 397 negatives; 334 `pewnosc = niska` (306 in pool A, 28 in B). Labellers were inconsistent on
  borderline types (Green Deal in farming, short ETS mentions, one-clause climate links, reference flag 30-63% by
  part) and more liberal than the human gold among Gemma positives with 0 hits (47% vs 24%). Borderline rules were
  added to section 2 and the flag rule to section 3; `labeller/instructions.md` regenerated. Planned stage 5: relabel
  the 334 uncertain statements with Sonnet under the new rules, plus ~50 hidden high-confidence check statements.
- (previous status, kept for history:) stage 2 batch files written, waiting for the independent labeller
- STOP POINT: stage 1 finished (75 pairs in synthetic.jsonl); blind-check batches written to
  `synthetic_batches/batch_001.jsonl`-`batch_008.jsonl` (150 items, shuffled with seed 2026; 20/20/20/20/20/20/20/10
  items; only `wypowiedz_id` and `tekst`) by `synthetic_make_batches.py`. The building agent cannot start subagents, so
  the blind labelling (section 7a) must be run separately: a fresh labeller given only sections 2, 3, the label format of
  section 6 and `synthetic_batches/` writes `synthetic_blind.jsonl`. Next: compare blind vs intended labels, rewrite /
  replace failing pairs (section 7), fill `blind_klimat`/`blind_kategoria` in synthetic.jsonl; then stage 3.
- UPDATE (main session): blind-check batches rebuilt by `synthetic_make_batches.py` with neutral ids B001-B150 (random,
  revealing neither pair nor version; mapping in `synthetic_blind_ids.csv`, never shown to the labeller) and with the
  two items of a pair always in different batches. The labeller gets only `labeller/instructions.md` (sections 2, 3
  and the label format) and `data/synthetic_batches/`; it writes `data/synthetic_blind.jsonl` keyed by neutral id.
- Rewritten pairs: 0, replaced pairs: 0 (blind check not run yet)
- Last finished pair: S75 (pairs were appended in order S01-S62, S64, S65, S63, S66-S73, S74, S75)
- Pairs written: 75 / 75 (items: 150 / 150)
- Pairs per typ_pary (written / target): odniesienie 15/15, tlo_watek 12/12, dluga_wypowiedz 8/8, epitet 10/10, kleski 8/8, energetyka 12/12, slowo_nazwa 10/10
- Item length (words): 123–909
- Real statements read: 0 (stage 1 must precede reading the corpus)

## Decisions not covered by the prompt

- Synthetic items start with a masked speaker label line (e.g. `Poseł …:`), as the prompt's section 1/7 format implies.
- Each pair is written as one shared text with a single placeholder replaced by the a/b deciding passage, so the two
  versions differ only in that passage (script `data/synthetic_add_pair.py`).
- Word count = whitespace-separated tokens of the full text (incl. speaker label).
- `fragment` of version a = its deciding (background/other-sense) passage or sentence; for b = verbatim climate sentence.
- `odniesienie_do_innego_mowcy` = 1 on both versions of `odniesienie` pairs (in a the climate mention itself is a
  reference to another speaker), and wherever else the climate content refers to another speaker.
- Blind labels are stored later in `blind_klimat` / `blind_kategoria` (null until the blind check is run).
- Synthetic blind-check batches use the section 6 batch rule (up to 20 items or ~8,000 words).
- Category of `b` items: P1/P2/P3 by the content of the deciding sentence; P4_watek_poboczny used for all 8
  `dluga_wypowiedz` b items (long statement on another topic with one climate paragraph), not for the short types.
- `a` items of `odniesienie` pairs get N8_inne (N7_srodowisko for S07a, a forestry statement); `slowo_nazwa` a items:
  S66-S70 N1_inne_znaczenie, S71-S75 N2_nazwy.
- `kleski` b items: 5 linked to climate change (P1), 3 with an explicitly denied link (P3: S48, S51, S53).
- `epitet` S42b is an affirming reply to another MP's "religia klimatyczna" (P1, odn=1) rather than a denial.
- Speaker label "Pełnomocnik" is not in the masking regex, so all speaker labels use roles from that regex
  (Poseł, Posłanka, Minister, Wiceminister).
- Synthetic batch files use the field name `tekst` (as in synthetic.jsonl) for the text.
- Pair ids S01a/S01b are visible to the blind labeller (the prompt requires wypowiedz_id in the batches); after the
  seeded shuffle 12 of 75 pairs have both items in the same batch.
