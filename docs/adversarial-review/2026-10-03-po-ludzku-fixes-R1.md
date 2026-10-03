# po-ludzku fixes — rundy R1–R4 (2026-10-03)

Preflight modelu: Fable 5.1 (najwyższy tier wg platform.claude.com/docs models) — CLI i natywny subagent zwróciły HTTP 429 „Fable limit” (req_011CfeQ51kTKX3ddZ7bEQAJx). Następny aktualny model: Opus 5.5, `model: opus`, natywny subagent adversarial-reviewer. Runtime zgłoszony przez recenzenta w każdej rundzie: `claude-opus-5-5` (self-report, przyjęty przez orkiestratora).

Zakres: commit 1365684 + poprawki pozostałych P3 z docs/adversarial-R4-2026-10-03.md.

- R1: 0×P0, 1×P1 (rachunek z twardą spacją nie wycinany — był w HEAD), 2×P2 (data płatności znów jako data pisma; „jednego tygodnia”), 3×P3. Wszystko naprawione.
- R2: 0×P0, 0×P1, 1×P2 (tekst NFD gubił terminy), 2×P3 („dwudziestu\njeden”, „1 dnia”). Naprawione.
- R3: 1×P1 nowe („w terminie 10 dnia miesiąca” jako 10 dni), 1×P3 („dnia roboczego”). Naprawione.
- R4 (weryfikacja): 66 sond, Python = JS, 0 wycieków. **ADVERSARIAL VERDICT: SIGN-OFF**.

Odrzucone: brak. Znane, nie zgłoszone: „w terminie 1 dniach” czytane jako 1 dzień (niepoprawna polszczyzna, nieszkodliwe).
