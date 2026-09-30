# Po ludzku

Produkt KOD.AI sp. z o.o. dla osoby, która ma w ręku pismo. Nie dla kokpitu Gorgosa.

## Nie mieszać podmiotów

W copy klienta (CLI, strona, kartka, about) jest tylko KOD.AI sp. z o.o. Nie pisać Krambit. Nie pisać, że AI.DENT jest firmą. Org GitHuba nie jest sprzedawcą.

## Silnik

`packages/core` jest źródłem dla CLI. `apps/web/explain.mjs` ma dawać ten sam JSON. Rozjazd łapie `node --test apps/web/explain.test.mjs`. Nie dodawać LLM, OCR, KSeF ani wysyłki. Brak klucza nie może podstawić odpowiedzi — nie ma tu modelu.

`pismo serve` zostaje na `127.0.0.1`. Nie dodawać `--host`. Nie logować treści pisma.

## CLI

Każda akcja strony ma odpowiednik: `pismo explain`, `pismo serve`, `pismo about`, `kartka`.

## Testy

`make test`. Python: `uv run pytest`. Fixtures są syntetyczne.
