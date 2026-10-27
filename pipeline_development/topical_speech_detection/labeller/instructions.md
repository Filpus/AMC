# Labelling instructions

Label every statement in the batch files you are given: does climate form one of its threads (`klimat` = 1 / 0), and
which single category fits. Statements are Polish parliamentary speeches with speaker names masked.

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
- **Negatives:** the exclusion rule that applies. There are no per-category quotas: label what
you read and report the counts.

Flag on every item: `odniesienie_do_innego_mowcy` = 1 when the climate content is a reference to or polemic with any
other actor: another speaker, a party, the government, the EU, the media, NGOs, foundations, industry, experts or
activists (labelled by the rule in section 2).

## Label format

Write one JSON line per statement:

```json
{"wypowiedz_id": "...", "klimat": 0, "kategoria": "N6_energetyka",
 "fragment": "<verbatim sentence that decided the label, or empty>",
 "uzasadnienie": "<one sentence in Polish>", "pewnosc": "wysoka|niska", "odniesienie_do_innego_mowcy": 0}
```


- For `klimat = 1`, `fragment` must occur verbatim in the statement.
- `kategoria` must agree with `klimat` (P* ↔ 1, N* ↔ 0).
- Re-read sections 2 and 3 before each batch. Judge each statement on its own; other statements in a batch must not
  influence the decision.
