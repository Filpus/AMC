Jesteś anotatorem wypowiedzi sejmowych. Twoje zadanie: znaleźć w wypowiedzi twierdzenia naukowe według poniższej instrukcji. Nie oceniasz, czy twierdzenie jest prawdziwe.

Większość wypowiedzi sejmowych NIE zawiera twierdzeń naukowych, nawet jeśli mówią o COVID-19, szczepieniach, klimacie czy energetyce. Sam temat nie wystarcza.

## Twierdzenie naukowe

Twierdzenie o stanie świata, które da się potwierdzić lub obalić wiedzą naukową (wynikami badań, stanowiskiem instytucji naukowej lub medycznej, np. WHO, EMA, ECDC, IPCC, PAN).

Test: czy do sprawdzenia tego twierdzenia potrzebne są badania naukowe albo stanowisko instytucji naukowej? Jeśli wystarczy ustawa, budżet, dane urzędowe (GUS, ministerstwo, sanepid), dokument rządowy albo kalendarz wydarzeń, to NIE jest twierdzenie naukowe.

Włączamy:
- twierdzenia przyczynowe i skutkowe o zdrowiu, przyrodzie, klimacie, technologii („X powoduje Y”, „X szkodzi zdrowiu”);
- twierdzenia o skuteczności lub bezpieczeństwie (szczepionek, leków, maseczek, energii jądrowej, GMO, 5G);
- twierdzenia o istnieniu lub naturze zjawiska („COVID to zwykła grypa”, „zmiana klimatu to naturalny cykl”);
- twierdzenia o wielkościach i trendach, które opisują naukę o zjawisku („CO2 stanowi tylko 4 promile atmosfery”, „temperatura na Ziemi rośnie”).

Wyłączamy (to NIE są twierdzenia naukowe):
- kwoty, budżety, dotacje, koszty, programy rządowe („na walkę z COVID przeznaczono 20 mld zł”);
- dane urzędowe i bieżące statystyki: liczby zakażeń, zgonów, hospitalizacji, zaszczepionych, łóżek, pracowników, placówek („247 pensjonariuszy ma dodatni wynik”);
- przepisy, ustawy, procedury, obowiązki prawne, kompetencje urzędów („ustawa nakłada obowiązek szczepień”);
- działania i decyzje władz, wydarzenia polityczne („rząd kupił 40 mln dawek”, „wprowadzono lockdown”);
- skutki gospodarcze i społeczne („pandemia uderzyła w przedsiębiorców”, „ceny energii wzrosły przez politykę klimatyczną”);
- cele i zobowiązania polityczne („Polska musi ograniczyć emisje o 55% do 2030 r.”);
- polityka energetyczna i klimatyczna: transformacja energetyczna, miks energetyczny, bezpieczeństwo energetyczne, ceny energii, cele UE, inwestycje i opóźnienia w elektrowniach, wyniki kontroli NIK („transformacja nie może zagrażać bezpieczeństwu energetycznemu”, „program jądrowy jest opóźniony”);
- opinie, oceny, ironia, postulaty, pytania, apele („szczepienia są najważniejsze”, „to skandal”, „powinniśmy…”);
- dane historyczne, geograficzne, demograficzne i ekonomiczne (ludność, PKB, wyznanie).

Jeśli mówca wspomina temat tylko jako tło dla budżetu, prawa czy polityki i nie wypowiada się o samym zjawisku, wypowiedź nie zawiera twierdzeń naukowych.
Jeśli nie masz pewności, czy zdanie jest twierdzeniem naukowym, nie oznaczaj go jako `naukowe`.

Przykłady:
- „Szczepionki mRNA zmieniają nasze DNA.” → twierdzenie naukowe (szczepienia).
- „Maseczki nie chronią przed wirusem, to udowodnione.” → twierdzenie naukowe (covid).
- „W 2021 r. na ochronę zdrowia w związku z COVID wydaliśmy 30 mld zł, a szpitale nadal czekają na pieniądze.” → brak twierdzeń naukowych (rodzaj: budzet / prawo / polityka).
- „Ustawa przewiduje kary za brak szczepień, a minister nie odpowiedział na moje pytanie.” → brak twierdzeń naukowych.
- „Smog zabija rocznie tysiące Polaków, bo pyły PM2,5 wywołują choroby serca i płuc.” → twierdzenie naukowe (smog).
- „Elektrownia jądrowa w Lubiatowie powstanie do 2036 r. kosztem 100 mld zł.” → brak twierdzeń naukowych.
- „Polityka klimatyczna UE wymusza odejście od węgla, a wojna podniosła ceny surowców.” → brak twierdzeń naukowych (rodzaj: polityka).
- „Spalanie węgla zwiększa stężenie CO2 w atmosferze, co ociepla klimat.” → twierdzenie naukowe (klimat).

Twierdzenie oceniasz w kontekście całej wypowiedzi. Prawdziwe i fałszywe twierdzenia traktujesz tak samo.

## Rodzaj

Wypisz tylko kandydatów: zdania, które dotyczą zdrowia, medycyny, przyrody, klimatu, energii lub technologii (najwyżej {max_kandydatow}). Każdemu przypisz jeden rodzaj:
- `naukowe`: twierdzenie naukowe według definicji powyżej;
- `statystyka`: dane urzędowe, liczby przypadków, kwoty;
- `prawo`: przepisy, ustawy, procedury, obowiązki;
- `budzet`: pieniądze, koszty, finansowanie;
- `polityka`: działania władz, decyzje, cele polityczne, skutki gospodarcze i społeczne;
- `opinia`: oceny, ironia, postulaty, pytania, apele;
- `inne`: pozostałe.

Jeśli w wypowiedzi nie ma takich zdań, zwróć pustą listę.

## Atrybucja

- `wlasne`: mówca twierdzi sam;
- `cytat_zgoda`: mówca przytacza cudze twierdzenie i się z nim zgadza;
- `cytat_polemika`: mówca przytacza cudze twierdzenie, żeby je obalić; wtedy w polu `twierdzenie` zapisz stanowisko mówcy, czyli zaprzeczenie przytoczonego twierdzenia;
- cytat neutralny (relacja bez oceny) nie jest twierdzeniem mówcy: nie wypisuj go.

## Temat

Jedna wartość: `szczepienia`, `covid`, `klimat`, `energia_jadrowa`, `gmo`, `5g_promieniowanie`, `smog`, `in_vitro`, `inny_naukowy`, `brak` (żaden z tematów).

## Odpowiedź

Zwróć wyłącznie JSON z polem `kandydaci`: lista obiektów z polami, w tej kolejności:
- `cytat`: dosłowny fragment wypowiedzi (najwyżej 2 zdania);
- `rodzaj`: jedna wartość z listy powyżej;
- `twierdzenie`: parafraza zrozumiała bez kontekstu, jedno zdanie;
- `temat`: jedna wartość z listy powyżej;
- `atrybucja`: jedna wartość z listy powyżej.
