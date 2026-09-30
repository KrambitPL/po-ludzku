# Spec v2 — po recenzji R1

Data: 2026-09-30. Research: `/home/piotr/research_notes/KODAI B2C referral apps/`.

Jedna aplikacja, trzy paczki uv. Nie git submodules. Nie Gorgos. Nie Krambit w copy klienta.

## Obietnica

Lokalne streszczenie pisma, które użytkownik już ma. Bez konta, bez płatności, bez wysyłki, bez LLM.

## Po R1, na sztywno

- Cytat nie może zawierać PESEL ani 26-cyfrowego rachunku. Wycinamy je przed cytowaniem. Suma kontrolna PESEL, nie każda jedenastka.
- Terminu względnego nie zamieniamy na datę, nawet gdy użytkownik poda datę doręczenia. Pokazujemy obie liczby i mówimy, żeby policzył sam.
- Termin bezwzględny tylko wtedy, gdy data stoi tuż za „do dnia” albo równoważnym zwrotem.
- Wiele terminów to lista.
- `--json` jest czystym JSON na stdout. Linia handlowa idzie na stderr i nie wchodzi do kartki z pismem.
- `kartka` nie przyjmuje pisma. Funkcja nie ma argumentu z tekstem.
- Skan, pusty PDF, mojibake, tekst ponad 200 000 znaków: kod 3, bez zgadywania.
- UOKiK (801 440 220, 222 66 76 76, dni robocze 10:00–18:00, taryfa operatora) tylko przy sporze o zakup i nigdy przy ZUS, urzędzie skarbowym albo komorniku. Samo słowo „usługa” nie włącza linii.
- Serwer lokalny: tylko 127.0.0.1, GET z allowlisty, POST 405, log bez ścieżki. Strona liczy wynik u siebie (`textContent`, CSP `connect-src 'none'`).
- Szkic nie zawiera „wnoszę” i nie jest pismem do sądu.
- Komornik: zdanie, że nie ma instrukcji wobec zajęcia.

## Odłożone

OCR, faktury, osobny recenzent umów, głos, portal wspólnoty, konto, płatność, publiczny serwer przyjmujący pismo.
