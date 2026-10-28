# Task: build a 1,000-item dataset for a Polish climate-topic classifier

## Goal

Build a training dataset of **exactly 1,000** labelled Polish parliamentary statements: **850 real** statements of the
Sejm, which you label yourself in batches, and **150 synthetic** statements (75 minimal pairs) that you write. Each item
says whether climate is one of the statement's threads (`klimat` = 1 / 0) and carries one fine-grained category. The
dataset will be used to fine-tune encoder classifiers (e.g. HerBERT large, Laya Multilingual) that decide `klimat` for
whole statements. Do not download any data.

All paths are relative to the project root (the `AMC` directory). Run every script from there. All outputs go to
`pipeline_development/topical_speech_detection/data/` (below: `data/`).

## 0. Stages and resuming

The work may be stopped at any point and resumed later, by you or by a new agent given this prompt. Work in stages, in
this order; each stage ends with files on disk:

| Stage | Work | Done when |
|---|---|---|
| 1 | write the synthetic pairs (section 7) | `data/synthetic.jsonl` has 75 pairs |
| 2 | blind check of the synthetic pairs (sections 7, 7a) | every pair in `data/synthetic_blind.jsonl` agrees with its intended label, after rewrites and replacements |
| 3 | candidate selection and batching (sections 4, 5, 6) | `data/candidates.csv` and `data/batches/batch_NNN.jsonl` exist |
| 4 | labelling the real statements (section 6) | every id of `candidates.csv` is in `data/labels.jsonl` |
| 5 | self-consistency relabel (sections 6, 7a) | `data/relabel.jsonl` has 100 lines |
| 6 | assembly, review files, summary (section 8) | `data/dataset.csv` and `data/summary.md` exist |

Rules:
- Keep `data/progress.md` up to date: the current stage, the last finished batch or pair, counts so far, and every
  decision not covered by this prompt. Update it after every batch or pair.
- On start, read `data/progress.md` and the existing files, and continue from the first unfinished stage and the first
  unfinished batch or pair. Never redo or overwrite finished work; never redraw candidates once `candidates.csv` exists.
- Append to `.jsonl` files one complete line per item. If the last line of a file is incomplete, remove only that line
  and redo that item.
- Every random step uses seed 2026, so scripts give the same result when rerun.

## 1. Input data

**Corpus:** `data/processed/korpus_plenarne.parquet`. One row = one statement (the complete speech of one speaker at a
plenary sitting). Columns used:

| Column | Meaning |
|---|---|
| `wypowiedz_id` | id `{term}_{sitting}_{date}_{num}`, e.g. `10_22_2024-11-27_98`; keep unchanged |
| `kadencja`, `posiedzenie`, `data` | term, sitting, date |
| `liczba_slow` | number of words |
| `tekst` | cleaned text |

**Sampling aid:** `data/processed/labels/gemma4_12b.csv`, one row per statement of the study population (43,991
statements of term 10). Columns used:

| Column | Meaning |
|---|---|
| `wypowiedz_id` | joins to the corpus |
| `grupa` | `prawica` (right-wing clubs) / `reszta` (all others) |
| `klimat` | **prediction** of an earlier zero-shot classifier (Gemma 4 12B) for the same definition; rename it `gemma_klimat` |
| `slownik_klimat` | number of climate-dictionary matches in the statement; rename it `hits` |

Use only statements present in this file. The earlier classifier is a recall filter, not a source of labels: on a
checked sample it found every climate statement, but only about a third of its positives were truly about climate. Its
positives therefore hold nearly all real climate threads and most of the hard negatives. Never copy its prediction into
your label. If either file is missing or lacks these columns, stop and report it.

**Mask speaker names** before you read or store any text: remove a header line matching
`^[ \t]*\d+\. kadencja, \d+\. posiedzenie[^\n]*(?:\n|$)` (multiline), and in every line that starts with a speaker label
replace the name, keeping the function: `Poseł Jan Kowalski:` → `Poseł …:`. A speaker label is a line start matching
`(Poseł|Posłanka|Wicemarszałek|Marszałek|Minister|Wiceminister|Prezes|Sekretarz|Podsekretarz|Przewodnicząc[ya]|Prezydent|Szef|Rzecznik|Prokurator|Członek|Przedstawiciel\w*|Zastępca)`
followed by capitalised words and a colon.

## 2. Label definition (binding; Polish, as used by the project's human annotators)

**Definicja.** `klimat = 1`, gdy klimat jest jednym z wątków wypowiedzi: mówca mówi coś o zmianie klimatu (przyczyny,
skutki, trendy, stan nauki) albo o polityce klimatycznej. Przelotna wzmianka nie wystarcza.

**Test.** Zdanie o klimacie odpowiada na pytanie „co mówca mówi o klimacie lub polityce klimatycznej?” (wątek, `1`)
czy tylko „w jakich okolicznościach dzieje się to, o czym mówi?” (tło, `0`). Wystarczy jeden akapit-wątek, niezależnie
od długości wypowiedzi.

**Włączamy (`klimat = 1`):**
- zmianę klimatu, jej przyczyny, skutki i trendy, stan nauki o klimacie;
- politykę klimatyczną: redukcję emisji, ETS i ETS2, Zielony Ład, Fit for 55, dekarbonizację, neutralność klimatyczną,
  adaptację, OZE i inne technologie jako sposób ograniczania emisji;
- negowanie zmiany klimatu lub wyśmiewanie jej jako ideologii, jeśli mówca coś o niej twierdzi, także zaprzeczanie, że
  dane zjawisko (powódź, susza) ma związek ze zmianą klimatu.

**Wyłączamy (`klimat = 0`):**
- „klimat” w innym znaczeniu (polityczny, inwestycyjny, społeczny);
- nazwy urzędów i ustaw bez treści o klimacie (Ministerstwo Klimatu i Środowiska);
- zmianę klimatu jako tło innego tematu („w dobie zmian klimatu”);
- „klimatyzm”, „religia klimatyczna” itp. użyte tylko jako epitet wobec czegoś innego;
- smog, pogodę i klęski żywiołowe bez odniesienia do zmiany klimatu;
- politykę energetyczną (ceny, kopalnie, sieci) bez odniesienia do emisji lub klimatu.

**Odniesienie do innego mówcy (reguła tego zbioru).** Gdy treść o klimacie jest odniesieniem do wypowiedzi kogoś
innego (posła, klubu, rządu, UE, mediów, organizacji, branży, ekspertów, aktywistów; „pan minister twierdzi, że…”),
liczy się to, co mówi sam mówca. `1`, gdy mówca podejmuje
temat: przytacza cudzą tezę o klimacie lub polityce klimatycznej i sam coś o niej twierdzi (zgadza się, polemizuje,
ocenia jej skutki). `0`, gdy tylko odnotowuje, że ktoś o klimacie mówił, bez własnej treści („odpowiem na piśmie na
pytanie pana posła o politykę klimatyczną”, „jak mówił przedmówca, także w kontekście klimatu…”).

**Przypadki graniczne (reguły tego zbioru).**
- **Zielony Ład w rolnictwie.** Zielony Ład jest polityką klimatyczną ze względu na treść klimatyczną. Krytyka lub
  ocena jego zasad rolnych (ugorowanie, pestycydy, nawozy, ekoschematy) bez odniesienia do emisji lub klimatu to `0`
  (N8). `1` dopiero wtedy, gdy mówca mówi coś o celach lub skutkach klimatycznych (emisje, neutralność klimatyczna,
  zmiana klimatu).
- **Krótka wzmianka o ETS, Zielonym Ładzie lub innym instrumencie polityki klimatycznej.** `1`, gdy mówca coś o nim
  twierdzi: przyczynę, skutek albo ocenę z uzasadnieniem („ETS podnosi ceny prądu”, „pieniądze z ETS przejedzono
  zamiast na transformację”). Wystarczy jedno takie zdanie. `0`, gdy instrument jest tylko nazwany, wyliczony, zapytany
  technicznie albo użyty jako hasło („wyrzucić Zielony Ład do kosza”, „zaorać Zielony Ład”).
- **Jedno zdanie łączące zjawisko ze zmianą klimatu.** `1`, gdy zdanie stwierdza konkretny skutek lub przyczynę jako
  część argumentu mówcy („burze są skutkiem zmiany klimatu, dlatego…”). `0`, gdy to zwrot ramowy, który nic o klimacie
  nie twierdzi („w obliczu postępujących zmian klimatu…”, „w dobie kryzysu klimatycznego”).

**Przykłady** (fragmenty dłuższych wypowiedzi z wcześniejszych kadencji):
1. `1`: „Zmiana klimatu powoduje, że pojawiające się opady są bardzo intensywne i zwykle rozdzielają dłuższe okresy
   bezdeszczowe. Taka charakterystyka opadów przyczynia się z kolei do intensyfikacji zjawiska suszy.” Wypowiedź
   dotyczy suszy, ale mówca mówi, jakie skutki ma zmiana klimatu; jeden akapit wystarcza.
2. `1`: „…wydaje się zasadne, żeby w czasach wojennych i COVID-owych rynek handlu emisjami został czasowo zawieszony
   albo ceny uprawnień do emisji zostały drastycznie ograniczone.” Przedmiotem jest ETS, czyli polityka klimatyczna.
3. `1`: „Lepiej, jak jest ciepło, i globalne ocieplenie jest korzystne, a nie niekorzystne. To jest wariactwo ludzi,
   elit, które postanowiły robić pieniądze na straszeniu ludzi…” Mówca twierdzi coś o skutkach ocieplenia.
4. `0`: „Ponadto chodzi o klimat inwestycyjny. Koniunktura w przemyśle spadła…” Inne znaczenie słowa.
5. `0`: „Zmiany forsowane w pośpiechu przez Ministerstwo Klimatu i Środowiska są radykalne i stworzą też
   nieprzewidywalne zasady rozliczania energii pochodzącej z mikroinstalacji OZE.” Nazwa ministerstwa, bez klimatu.
6. `0`: „Ministerstwo rolnictwa nastawione jest produkcję. To ostatnie, czego potrzebuje nasza przyroda w obliczu
   kryzysu klimatycznego.” Kryzys klimatyczny jako tło.
7. `0`: „…50 tys. Polek i Polaków rocznie umiera z powodu smogu.” Smog bez odniesienia do zmiany klimatu.
8. `0`: „Projekt ustawy ma na celu przeprowadzenie procesu restrukturyzacji sektora węgla kamiennego…” Polityka
   energetyczna bez emisji ani klimatu.

## 3. Categories

Every item gets `klimat` and exactly one `kategoria`:

| kategoria | klimat | Definition |
|---|---|---|
| `P1_nauka_skutki` | 1 | climate change, its causes, effects, trends, state of the science (incl. drought, floods, heat explicitly linked to climate change) |
| `P2_polityka` | 1 | climate policy: emission reduction, ETS/ETS2, Green Deal, Fit for 55, decarbonisation, climate neutrality, adaptation, RES and other technologies as a way to cut emissions |
| `P3_negowanie` | 1 | denying or ridiculing climate change as ideology when the speaker claims something about it, incl. denying a link between a phenomenon and climate change |
| `P4_watek_poboczny` | 1 | a statement whose main topic is unrelated to climate and energy (e.g. transport, budget, health, agriculture, insurance), or which covers many topics, with at least one genuine climate thread |
| `N1_inne_znaczenie` | 0 | "klimat" in another sense (political, investment, social, atmosphere of a debate) |
| `N2_nazwy` | 0 | names of ministries, acts, funds without climate content |
| `N3_tlo` | 0 | climate change only as background ("w dobie zmian klimatu") |
| `N4_epitet` | 0 | "klimatyzm", "religia klimatyczna" etc. only as an epithet against something else, no claim about climate |
| `N5_smog_pogoda` | 0 | smog, weather, natural disasters without a link to climate change |
| `N6_energetyka` | 0 | energy policy (prices, mines, grids, coal jobs) without reference to emissions or climate |
| `N7_srodowisko` | 0 | other environmental topics (forests, water, waste, hunting, animals) without a climate thread |
| `N8_inne` | 0 | everything else, incl. climate mentioned only as someone else's statement with no content of the speaker's own (rule in section 2), unless N5–N7 fits the statement's topic |

When an item fits several categories:
- **Positives:** first decide the main topic of the statement. If it is unrelated to climate and energy, or the
  statement covers many topics, use P4. If the main topic is climate, a climate-related phenomenon (drought, flood,
  heat) or climate and energy policy (ETS, mines, heating, RES, emissions), use P1, P2 or P3 by what the climate
  passage says.
- **Negatives:** the exclusion rule that applies. There are no per-category quotas for real statements: label what
you read and report the counts.

Flag on every item: `odniesienie_do_innego_mowcy` = 1 only when the climate content explicitly names another actor as
the holder or source of a climate position (another speaker, a party, the government, the EU, the media, NGOs,
foundations, industry, experts or activists) and the speaker refers to or argues with that position. Criticising a
policy without naming whose position it is gets 0. The flag does not change `klimat` (labelled by the rule in
section 2).

## 4. Exclusions

Never include, label, paraphrase or use in any way:
- **Gold-standard statements (evaluation set):** 10_11_2024-05-08_134, 10_36_2025-06-11_274, 10_26_2025-01-09_139,
  10_22_2024-11-27_91, 10_1_2023-12-06_19, 10_16_2024-07-24_252, 10_22_2024-11-27_98, 10_62_2026-07-16_240,
  10_55_2026-04-16_30, 10_34_2025-05-08_217, 10_10_2024-04-26_103, 10_26_2025-01-08_107, 10_26_2025-01-08_7,
  10_22_2024-11-27_151, 10_42_2025-10-08_216, 10_28_2025-02-05_27, 10_26_2025-01-08_201, 10_28_2025-02-05_15,
  10_26_2025-01-08_6, 10_36_2025-06-03_81, 10_41_2025-09-24_361, 10_18_2024-10-01_16, 10_8_2024-03-20_61,
  10_6_2024-02-22_106, 10_35_2025-05-20_278, 10_13_2024-06-13_117, 10_18_2024-09-26_287, 10_24_2024-12-06_71,
  10_13_2024-06-13_6, 10_25_2024-12-18_14, 10_22_2024-11-21_225, 10_63_2026-07-29_239, 10_45_2025-11-21_149,
  10_26_2025-01-08_205, 10_28_2025-02-05_20, 10_29_2025-02-21_94, 10_27_2025-01-22_106, 10_55_2026-04-14_49,
  10_58_2026-05-29_31, 10_25_2024-12-19_91, 10_26_2025-01-08_196, 10_33_2025-04-24_204, 10_61_2026-07-02_265,
  10_38_2025-07-10_109, 10_15_2024-07-11_170, 10_11_2024-05-09_162, 10_52_2026-02-26_31, 10_32_2025-04-02_60,
  10_36_2025-06-03_50, 10_40_2025-09-12_260, 10_53_2026-03-11_215, 10_53_2026-03-11_321, 10_2_2024-01-17_2,
  10_26_2025-01-08_3, 10_22_2024-11-20_246, 10_5_2024-02-09_12, 10_53_2026-03-11_304, 10_17_2024-09-12_82,
  10_10_2024-04-26_160, 10_48_2025-12-18_97, 10_7_2024-03-08_51, 10_48_2025-12-18_102, 10_42_2025-10-08_228,
  10_41_2025-09-26_135, 10_43_2025-10-15_272, 10_1_2023-12-21_1, 10_22_2024-11-22_166, 10_8_2024-03-20_68,
  10_2_2024-01-16_72, 10_36_2025-06-11_381, 10_60_2026-06-18_385, 10_12_2024-05-22_161, 10_40_2025-09-12_286,
  10_54_2026-03-25_149, 10_38_2025-07-09_138, 10_45_2025-11-19_63, 10_10_2024-04-26_133, 10_19_2024-10-10_240,
  10_50_2026-01-21_105, 10_22_2024-11-19_143, 10_33_2025-04-24_211, 10_39_2025-08-05_59, 10_53_2026-03-11_305,
  10_19_2024-10-10_88, 10_41_2025-09-24_318, 10_29_2025-02-20_11, 10_7_2024-03-07_46, 10_58_2026-05-28_341,
  10_32_2025-04-04_32, 10_44_2025-11-06_225, 10_29_2025-02-21_163, 10_44_2025-11-05_242, 10_45_2025-11-21_53,
  10_18_2024-09-25_113, 10_40_2025-09-10_73, 10_64_2026-09-03_145, 10_13_2024-06-14_24, 10_8_2024-03-20_81,
  10_1_2023-11-22_36, 10_58_2026-05-27_181.
- **Prompt-test statements:** 10_10_2024-04-25_124, 10_18_2024-09-25_107, 10_60_2026-06-17_269.
- **Statements containing any example quote of section 2** (match on the first ~60 characters of each quote).

At the end, verify that none of these ids is in the output and report the check.

## 5. Real statements: candidate selection (850, fixed seed 2026)

After the exclusions, draw 850 statements from four pools:

| Pool | Content | Available | Draw |
|---|---|---|---|
| A | `gemma_klimat == 1` | ~1,570 | **650**, stratified by `hits` (0: 130, 1: 200, 2: 150, ≥3: 170) and, within each, half `prawica`, half `reszta` (take what is there if a cell is short and fill from the other group) |
| B | `gemma_klimat == 0` and `hits >= 1` | ~82 | **all** |
| C | `gemma_klimat == 0`, `hits == 0`, and the text matches the adjacent-topic regex below | several thousand | **70** |
| D | `gemma_klimat == 0`, `hits == 0`, no adjacent-topic match | tens of thousands | the rest up to 850 (~48), stratified by `liczba_slow` terciles |

Adjacent-topic regex (case-insensitive): `ceny? (energii|prądu)`, `smog\w*`, `powod\w*`, `susz\w*`,
`ministerstw\w* klimatu`, `klimat\w* (polityczn|inwestycyjn|społeczn|debat)`, `kopal\w*`, `górnik\w*`, `elektrown\w*`,
`fotowolta\w*`, `wiatrak\w*`, `\boze\b`, `\blas\w*`, `odpad\w*`.

Expected yield: about 350 positives (mostly pool A) and 500 negatives, most of them hard. Do not top up or replace
statements to reach a positive share.

## 6. Labelling real statements in batches

- In stage 3, shuffle all 850 candidates (seed 2026), so pools are mixed, and write the batch files
  `data/batches/batch_001.jsonl`, … containing only `wypowiedz_id` and the masked text. One batch = up to 20 statements
  or about 8,000 words, whichever comes first.
- **Never look at a statement's pool, `hits` or `gemma_klimat` while labelling;** label from the batch files only.
- Before each batch, re-read section 2 and the category table of section 3. Judge each statement on its own; neighbours
  in the batch must not influence the decision.
- After each batch, append one JSON line per statement to `data/labels.jsonl` and update `data/progress.md`.

For each statement:

```json
{"wypowiedz_id": "...", "klimat": 0, "kategoria": "N6_energetyka",
 "fragment": "<verbatim sentence that decided the label, or empty>",
 "uzasadnienie": "<one sentence in Polish>", "pewnosc": "wysoka|niska", "odniesienie_do_innego_mowcy": 0}
```

Checks:
- For `klimat = 1`, `fragment` must occur verbatim in the masked statement; if it does not, label the statement again.
- `kategoria` must agree with `klimat` (P* ↔ 1, N* ↔ 0).
- Self-consistency: after all 850 are labelled, draw a random 100 and write them as batch files (`relabel_batches/`,
  only `wypowiedz_id` and masked text). They are labelled by an independent labeller (section 7a); the first labels stay
  in the dataset.

## 7. Synthetic statements: 75 minimal pairs (150 items)

Write these **first** (stage 1), before reading any real statement, so they cannot borrow from one. Append each finished
pair (both items) to `data/synthetic.jsonl` and update `data/progress.md`. Each pair is two versions of one plenary
statement that differ only
in the passage that decides the label: version `a` has `klimat = 0`, version `b` has `klimat = 1`. Everything else
(topic, structure, length, tone, speaker role) stays the same, so the only signal is the rule.

| typ_pary | Pairs | `a` (0) | `b` (1) |
|---|---|---|---|
| `odniesienie` | 15 | the speaker only notes that another MP, club, the government or the EU spoke about climate | the speaker quotes the other side's climate claim and says something of their own about it (agrees, disputes, assesses consequences) |
| `tlo_watek` | 12 | climate change only as a framing phrase for another topic | one passage says what climate change causes or what climate policy should do |
| `dluga_wypowiedz` | 8 | 800–1,500 words on another topic (budget, agriculture, flood relief) with a passing climate mention | the same statement with that mention replaced by one genuine climate paragraph |
| `epitet` | 10 | "klimatyzm", "religia klimatyczna" etc. as an insult aimed at something else | the speaker claims something about climate change (e.g. that it is not caused by humans, or harmless) |
| `kleski` | 8 | flood, drought or heat described without a link to climate change | the same event explicitly linked to (or explicitly denied a link to) climate change |
| `energetyka` | 12 | energy prices, coal mines, grids, RES as cheap or local energy | the same subject framed through emissions, ETS or decarbonisation |
| `slowo_nazwa` | 10 | "klimat" in another sense, or the Ministry of Climate and Environment named without climate content | the same sentence frame with genuine climate content |

Writing rules:
- Polish parliamentary register (e.g. „Panie Marszałku! Wysoka Izbo!”), length 120–600 words except `dluga_wypowiedz`.
- Vary the speaker role (MP of the governing coalition, MP of the opposition, a minister answering), stance (supporting,
  opposing, sceptical) and subject. Speaker labels as masked in section 1 (`Poseł …:`); no real names, no real
  statement ids.
- Write new text. Do not reproduce or paraphrase any real statement from the corpus, any statement from section 4 or
  any example quote of section 2.
- Each pair gets `para_id` (`S01`–`S75`); items `S01a`, `S01b`, … are their `wypowiedz_id`.

Blind check: shuffle the 150 items and write them as batch files (`synthetic_batches/`, only `wypowiedz_id` and text).
They are labelled by an independent labeller (section 7a). Rewrite a pair whose blind label differs from the intended
one and send the rewritten pair through the blind check again; drop and replace it after a second failure. Report the
number of rewritten and replaced pairs.

## 7a. Independent labeller

You remember your own labels and the texts you wrote, so you cannot do the self-consistency relabel or the blind check
yourself. Start a fresh subagent with no access to your context, files or outputs other than: sections 2 and 3 of this
prompt, the label format of section 6, and the batch files in `relabel_batches/` or `synthetic_batches/`. It writes
`relabel.jsonl` and `synthetic_blind.jsonl`. If you cannot start a subagent, stop after writing the batch files and
report that these two steps must be run separately; do not label them yourself.

Then compare: report agreement on `klimat` and `kategoria` for the 100 relabelled statements and list disagreements.

## 8. Outputs

Save to `data/`:
- the script(s) that perform masking, exclusions, candidate selection, shuffling, batching and assembly (labelling and
  writing are done by you);
- `candidates.csv`: the 850 drawn statements with `wypowiedz_id`, `pula`, `hits`, `grupa`, `gemma_klimat`;
- `labels.jsonl`: your labels of the real statements;
- `synthetic.jsonl`: the 150 synthetic items with `wypowiedz_id`, `para_id`, `typ_pary`, `tekst`, intended `klimat`,
  `kategoria`, `fragment` (the deciding passage), `odniesienie_do_innego_mowcy`, and the blind label;
- `dataset.csv`: all 1,000 items with `wypowiedz_id`, `zrodlo` (`realna`/`syntetyczna`), `para_id`, `typ_pary`, `pula`,
  `kadencja`, `posiedzenie`, `data`, `grupa`, `gemma_klimat`, `tekst` (masked), `liczba_slow`, `klimat`, `kategoria`,
  `fragment`, `uzasadnienie`, `pewnosc`, `odniesienie_do_innego_mowcy`. Do not assign train/validation splits or
  folds: the training script does that later, by sitting and stratified by label;
- `relabel.jsonl` and `synthetic_blind.jsonl`: the independent labeller's labels;
- `review_sample.csv`: 50 real statements stratified across categories for a human check (do not mark anything as
  reviewed), and `review_low_confidence.csv`: all real statements with `pewnosc = niska`;
- `summary.md`: counts per category × pool and per `zrodlo`; share of positives; positives by `hits` and
  `gemma_klimat` (how many of Gemma's positives you labelled 0, and any positives in pools B–D); length distribution of
  real and synthetic items; self-consistency; the blind-check result; number of flagged references; the exclusion
  check; the seed; and every decision not covered by this prompt.

## 9. Report back

Final counts per category, `zrodlo`, the share of positives, self-consistency, the blind-check result, the
number of low-confidence items, the exclusion check, the paths of all outputs, and every assumption made beyond this
prompt.
