Jesteś anotatorem wypowiedzi posłów z posiedzeń plenarnych Sejmu RP. Oceniasz, czy klimat jest jednym z wątków
wypowiedzi, według definicji poniżej. Przeczytaj definicję, doprecyzowania i przykłady, potem wypowiedź, i odpowiedz
w formacie JSON. Nazwiska mówców są w tekście usunięte („Poseł …:”).

## Etykieta: klimat

**Definicja.** `klimat = 1`, gdy klimat jest jednym z wątków wypowiedzi: mówca mówi coś o zmianie klimatu (przyczyny,
skutki, trendy, stan nauki) albo o polityce klimatycznej. Przelotna wzmianka nie wystarcza.

**Test.** Zdanie o klimacie odpowiada na pytanie „co mówca mówi o klimacie lub polityce klimatycznej?” (wątek, `1`)
czy tylko „w jakich okolicznościach dzieje się to, o czym mówi?” (tło, `0`). Wystarczy jeden akapit-wątek, niezależnie
od długości wypowiedzi.

**Włączamy (`klimat = 1`):**
- zmianę klimatu, jej przyczyny, skutki i trendy, stan nauki o klimacie;
- politykę klimatyczną: redukcję emisji, ETS i ETS2, Zielony Ład, Fit for 55, dekarbonizację, neutralność klimatyczną,
  adaptację, OZE i inne technologie jako sposób ograniczania emisji;
- negowanie zmiany klimatu lub wyśmiewanie jej jako ideologii, jeśli mówca coś o niej twierdzi.

**Wyłączamy (`klimat = 0`):**
- „klimat” w innym znaczeniu (polityczny, inwestycyjny, społeczny);
- nazwy urzędów i ustaw bez treści o klimacie (Ministerstwo Klimatu i Środowiska);
- zmianę klimatu jako tło innego tematu („w dobie zmian klimatu”);
- „klimatyzm”, „religia klimatyczna” itp. użyte tylko jako epitet wobec czegoś innego;
- smog, pogodę i klęski żywiołowe bez odniesienia do zmiany klimatu;
- politykę energetyczną (ceny, kopalnie, sieci) bez odniesienia do emisji lub klimatu.

## Przykłady

Fragmenty dłuższych wypowiedzi z wcześniejszych kadencji Sejmu.

**Przykład 1: `klimat = 1`.** „Kolejnym znaczącym czynnikiem jest deficyt opadów, na który nakłada się okres wzmożonej
wegetacji i parowania, czemu sprzyjają wysokie wartości temperatury powietrza. Zmiana klimatu powoduje, że pojawiające
się opady są bardzo intensywne i zwykle rozdzielają dłuższe okresy bezdeszczowe. Taka charakterystyka opadów przyczynia
się z kolei do intensyfikacji zjawiska suszy.”
Dlaczego: wypowiedź dotyczy suszy i programów retencji, ale mówca mówi, jakie skutki ma zmiana klimatu. Jeden taki
akapit wystarcza.

**Przykład 2: `klimat = 1`.** „W sytuacji kiedy Unia Europejska emituje do atmosfery ok. 10% globalnej emisji CO 2 ,
wydaje się zasadne, żeby w czasach wojennych i COVID-owych rynek handlu emisjami został czasowo zawieszony albo ceny
uprawnień do emisji zostały drastycznie ograniczone.”
Dlaczego: przedmiotem wypowiedzi jest system ETS, czyli polityka klimatyczna, choć mówca uzasadnia apel cenami energii.

**Przykład 3: `klimat = 1`.** „Lepiej, jak jest ciepło, i globalne ocieplenie jest korzystne, a nie niekorzystne. To
jest wariactwo ludzi, elit, które postanowiły robić pieniądze na straszeniu ludzi, że jak będzie ciepło, to będzie
niedobrze.”
Dlaczego: mówca twierdzi coś o skutkach globalnego ocieplenia i wyśmiewa obawy przed nim, choć reszta wypowiedzi
dotyczy energetyki.

**Przykład 4: `klimat = 0`.** „Ponadto chodzi o klimat inwestycyjny. Koniunktura w przemyśle spadła w ciągu ostatniego
miesiąca prawie o 7 punktów, w transporcie - o 15 punktów, a w budownictwie - o 7 punktów.”
Dlaczego: „klimat” w znaczeniu warunków dla inwestycji.

**Przykład 5: `klimat = 0`.** „Zmiany forsowane w pośpiechu przez Ministerstwo Klimatu i Środowiska są radykalne
i stworzą też nieprzewidywalne zasady rozliczania energii pochodzącej z mikroinstalacji OZE.”
Dlaczego: nazwa ministerstwa; przedmiotem są zasady rozliczania prosumentów, bez odniesienia do emisji ani klimatu.

**Przykład 6: `klimat = 0`.** „Ministerstwo rolnictwa nastawione jest produkcję. To ostatnie, czego potrzebuje nasza
przyroda w obliczu kryzysu klimatycznego.”
Dlaczego: kryzys klimatyczny jest tłem; przedmiotem jest przeniesienie leśnictwa i łowiectwa do ministra rolnictwa.

**Przykład 7: `klimat = 0`.** „To są bardzo niebezpieczne rozwiązania również z powodu tego, że 50 tys. Polek i Polaków
rocznie umiera z powodu smogu.”
Dlaczego: smog bez odniesienia do zmiany klimatu.

**Przykład 8: `klimat = 0`.** „Projekt ustawy ma na celu przeprowadzenie procesu restrukturyzacji sektora węgla
kamiennego w taki sposób, aby złagodzić jego negatywne skutki społeczne i zapewnić odpowiednie instrumenty osłonowe.”
Dlaczego: polityka energetyczna (likwidacja kopalń, zatrudnienie) bez odniesienia do emisji ani klimatu.

## Odpowiedź

Zwróć JSON z dwoma polami, w tej kolejności:
- `fragment`: zdanie z wypowiedzi, które najmocniej przemawia za `klimat = 1`, przepisane dosłownie (do 300 znaków).
  Wypisz je także wtedy, gdy klimat jest tylko tłem albo słowo „klimat” ma inne znaczenie. Pusty napis `""`, gdy
  wypowiedź w ogóle nie dotyczy klimatu;
- `klimat`: `1` albo `0` według definicji.

## Przypomnienie

Oceń powyższą wypowiedź według definicji etykiety `klimat`. Odpowiedz tylko JSON-em: najpierw `fragment` (dosłowne
zdanie z wypowiedzi albo `""`), potem `klimat` (`1` albo `0`).
