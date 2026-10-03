# Przegląd adwersaryjny — terminy, data pisma, szkic (2026-10-03)

Lens: Correctness. Recenzent: natywny subagent adversarial-reviewer (Claude, harness: claude-opus-5-5). Brak paragonu §5b — runda formalnie nieudokumentowana modelem.

Powód: przejęta sesja opencode zostawiła R4 bez wyniku. Ręczne testy na realistycznych pismach pokazały, że ZUS („w terminie miesiąca”, „Płatność do 30 października 2026”) dawał „nie widzę terminu”, komornik gubił „w terminie 7 dni.”, a szkic wpisywał termin płatności albo datę nakazu jako „pismo z dnia”.

- R1: 2×P1 (drugi termin w zdaniu połknięty; „2026r.” zabijało datę), 2×P2, 3×P3. Wszystkie naprawione, poza cyframi Unicode.
- R2: 0×P0, 0×P1. P2 (idiomy „w dalszym ciągu”, „w poprzednim terminie”) naprawione whitelistą przymiotników. Spacja w cytacie JS naprawiona.

Odłożone (P3, znane):
- cyfry pełnej szerokości: Python je czyta, JS nie (tylko brak terminu, nigdy zła data);
- linia kończąca się „:” przed nagłówkiem z datą gubi datę pisma (bezpieczne: szkic bez daty);
- „w ciągu jednego miesiąca” nie jest rozpoznawane;
- „od dnia 01.03.2026” w kotwicy jest ucięte na pierwszej kropce.
