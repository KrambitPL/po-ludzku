# Po ludzku

Darmowe streszczenie pisma, które już masz. Tekst nie jest wysyłany.

To produkt **KOD.AI sp. z o.o.**, ul. Frezerów 2, 20-209 Lublin, KRS 0001218254, NIP 9462762849, REGON 543763281, info@kodai.com.pl.

To nie jest pomoc prawna. Automat może się mylić. Nie wysyła pisma do urzędu, pracodawcy ani do nas.

## Po co to jest

Wklejasz pismo z urzędu, banku, wspólnoty albo komornika. Dostajesz kartkę: co to jest, jaki termin da się wyczytać, jakie kwoty są w tekście, czego automat nie wie. Osobno, jeśli chcesz, kartka dla rodziny i informacja handlowa o KOD.AI. Tej drugiej nie wysyłamy za Ciebie.

Nie budujemy tu czytnika faktur, recenzenta umów, agenta głosowego ani portalu wspólnoty. Research z 2026-09-30 pokazał, że te rzeczy są albo zajęte, albo wymagają logowania. Notatki: `docs/SPEC.md`.

To nie jest aplikacja Gorgosa. Gorgos jest kokpitem firmy. Tu nie ma konta.

## Jak użyć

```bash
uv sync --all-packages
uv run --package poludzku-pismo pismo explain pismo.txt
uv run --package poludzku-pismo pismo explain skan.pdf   # tylko PDF z warstwą tekstu
uv run --package poludzku-pismo pismo serve             # http://127.0.0.1:8765
uv run --package poludzku-kartka kartka
```

`pismo serve` słucha wyłącznie na `127.0.0.1` i nie przyjmuje treści pisma. Strona liczy wynik w przeglądarce.

Zdjęcia i skany: nie czytamy. Przepisz nagłówek, znak, zdanie o terminie, kwotę i telefon z pisma.

## Paczki

| Paczka | Co robi |
|---|---|
| `packages/core` | Silnik. Zero sieci. |
| `apps/pismo` | CLI `pismo` i lokalny podgląd. |
| `apps/kartka` | Informacja handlowa. Nie wysyła jej. |
| `apps/web` | Ta sama logika w przeglądarce. |

To są paczki jednego repozytorium, nie git submodules. Jeden silnik, jeden lockfile.

Zdalne repozytorium może leżeć w organizacji GitHub, która nie jest sprzedawcą. Sprzedawcę drukuje `pismo about`.

## Testy

```bash
make test
```

## Granice

Nie liczymy dni do daty kalendarzowej. Jeśli pismo mówi „14 dni od doręczenia”, pokazujemy cytat i zostawiamy liczenie Tobie. Nie podajemy numerów urzędów z głowy. Linia UOKiK pojawia się tylko przy sporze o zakup i znika, gdy pismo jest z urzędu skarbowego, ZUS albo komornika.
