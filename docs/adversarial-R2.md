# R2 fixes

R2 (grok-4.7, 2026-09-30) was OPEN: 1×P0  several P1. Accepted, not rejected.

- Grouped accounts and a PESEL followed by more digits are redacted by exact patterns, not a greedy digit run.
- Amounts keep the thousands separator (space or dot) and allow a whole złoty.
- Deadlines include „termin płatności”, „płatna do”, „wpłacić do”, and day-counts written as words. Business-day warning is not overwritten.
- Case id stops at the sentence and does not swallow REGON.
- A phone needs the word telefon/tel/fax. A bare REGON is not a phone.
- cp1250 files decode or exit 3, no traceback.
- A bad delivery date does not erase the card.
- „towar” is a whole word. „skarbow” and „zajęci” cover the inflected forms.

Cross-model round remains incomplete: Codex API key has no credits; `gpt-6-astra` was not run. Gemini `gemini-3-pro` was not found.
