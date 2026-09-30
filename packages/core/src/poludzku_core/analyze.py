from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

from poludzku_core.redact import redact

MAX_CHARS = 200_000
MIN_CHARS = 40

DISCLAIMER = (
    "To jest automat. Może się mylić. To nie jest pomoc prawna "
    "i nie zastępuje rozmowy z osobą, która może jej udzielić. "
    "Nic nie zostało wysłane."
)

MONTHS = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "wrzesnia": 9,
    "października": 10,
    "pazdziernika": 10,
    "listopada": 11,
    "grudnia": 12,
}

KINDS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("wezwanie_do_zaplaty", "wezwanie do zapłaty", ("wezwanie do zapłaty", "wezwanie do zaplaty")),
    ("upomnienie", "upomnienie", ("upomnienie",)),
    ("postanowienie", "postanowienie", ("postanowienie",)),
    ("decyzja", "decyzja", ("decyzja",)),
    ("zawiadomienie", "zawiadomienie", ("zawiadomienie",)),
    ("uchwala", "uchwała", ("uchwała", "uchwala")),
    ("wezwanie", "wezwanie", ("wezwanie",)),
)

SENDER_HINTS = (
    "urząd",
    "urzad",
    "zus",
    "komornik",
    "sąd",
    "sad",
    "bank",
    "wspólnota",
    "wspolnota",
    "zarząd",
    "zarzad",
    "naczelnik",
    "zakład",
    "zaklad",
    "ubezpiecz",
)

CONSUMER_WORDS = ("reklamacj", "sprzedawc", "rękojmi", "rekojmi")
ENFORCEMENT = (
    "komornik",
    "egzekuc",
    "zajęcie",
    "zajecie",
    "zajęciu",
    "zajeciu",
    "zajęciem",
    "zajeciem",
    "zajęcia wynagrodzenia",
    "zajecia wynagrodzenia",
    "tytuł wykonawczy",
    "tytul wykonawczy",
)
ZUS = ("zakład ubezpiecze", "zaklad ubezpiecze", "zakładu ubezpiecze", "zakladu ubezpiecze")
TAX_STEM = "skarbow"

UOKiK_PHONES = ("801 440 220", "222 66 76 76")
NUMERIC_DATE = re.compile(r"\b(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\b")
WORD_DATE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})\b",
    re.IGNORECASE,
)
CASE_ID = re.compile(
    r"(?i)\b(?:znak sprawy|numer sprawy|nr sprawy|sygn\.?\s*akt|sygnatura|sygn\.|znak)\s*[:.]?\s*"
    r"([A-Z0-9][A-Z0-9./\-]*(?:[ ]+[A-Z0-9][A-Z0-9./\-]*){0,5})"
)
KM_ID = re.compile(r"(?i)\bKM\s*\d+/\d+\b")
AMOUNT = re.compile(
    r"(?i)(?<!\d)(\d{1,3}(?:[ \u00a0.]\d{3})+(?:,\d{2})?|\d+(?:,\d{2})?)\s*(zł|zl|pln)\b"
)
PHONE = re.compile(
    r"(?i)(?:telefon|tel\.?|fax)\s*[:.]?\s*(\+48[\s-]?)?(\(?\d{2,3}\)?(?:[\s\-]\d{2,3}){2,3})"
)
RELATIVE = re.compile(
    r"(?i)w (?:terminie|ciągu)\s+(\d{1,3})\s+dni(?:\s+(kalendarzowych|roboczych))?\s+od\s+([^.\n]{3,80})"
)
ABSOLUTE_CUE = re.compile(
    r"(?i)(?:do dnia|nie później niż|nie pozniej niz|termin upływa|termin uplywa|"
    r"termin płatności|termin platnosci|płatne do|platne do|płatna do|platna do|"
    r"płatny do|platny do|zapłacić do|zaplacic do|wpłacić do|wplacic do)\s*:?\s+"
)
WORD_NUMBERS = {
    "jeden": 1,
    "jednego": 1,
    "dwa": 2,
    "dwóch": 2,
    "dwoch": 2,
    "trzech": 3,
    "trzy": 3,
    "siedmiu": 7,
    "siedem": 7,
    "czternastu": 14,
    "czternaście": 14,
    "czternascie": 14,
    "trzydziestu": 30,
    "trzydzieści": 30,
    "trzydziesci": 30,
}


class Unreadable(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def load_identity() -> dict:
    path = Path(__file__).with_name("identity.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _fold(text: str) -> str:
    return text.casefold()


def _valid_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _readable(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < MIN_CHARS:
        return False
    bad = 0
    considered = 0
    for char in stripped:
        if char.isspace():
            continue
        considered += 1
        if char == "\ufffd":
            bad += 1
            continue
        cat = unicodedata.category(char)
        if cat[0] not in {"L", "N", "P", "S"} and char not in {"+", "#"}:
            bad += 1
    if considered == 0:
        return False
    return (bad / considered) <= 0.05


def _line_of(text: str, needle: str) -> str | None:
    folded = _fold(needle)
    for line in text.splitlines():
        if folded in _fold(line):
            clean = " ".join(line.split())
            return clean[:180] if clean else None
    return None


def _kind(text: str) -> dict | None:
    folded = _fold(text)
    for kind_id, label, phrases in KINDS:
        for phrase in phrases:
            if phrase in folded:
                return {"id": kind_id, "label": label, "quote": _line_of(text, phrase)}
    return None


def _sender(text: str) -> str | None:
    for line in text.splitlines()[:20]:
        clean = " ".join(line.split())
        if not clean or len(clean) > 120:
            continue
        folded = _fold(clean)
        if any(hint in folded for hint in SENDER_HINTS):
            return clean
    return None


def _dates(text: str) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    for match in NUMERIC_DATE.finditer(text):
        iso = _valid_date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        if iso and iso not in seen:
            seen.add(iso)
            found.append({"iso": iso, "quote": match.group(0)})
    for match in WORD_DATE.finditer(text):
        month = MONTHS[_fold(match.group(2))]
        iso = _valid_date(int(match.group(3)), month, int(match.group(1)))
        if iso and iso not in seen:
            seen.add(iso)
            found.append({"iso": iso, "quote": match.group(0)})
    return found


def _deadlines(text: str, delivery: str | None) -> list[dict]:
    items: list[dict] = []
    for match in RELATIVE.finditer(text):
        business = (match.group(2) or "").casefold().startswith("robocz")
        anchor_text = match.group(3).strip()
        folded = _fold(anchor_text)
        if "doręcz" in folded or "dorecz" in folded or "otrzym" in folded:
            anchor = "doreczenie"
        elif "niniejsz" in folded:
            anchor = "data_pisma"
        else:
            anchor = "inny"
        if business:
            note = "Pismo mówi o dniach roboczych. Tych dni nie liczę."
        elif delivery and anchor == "doreczenie":
            note = (
                f"Podałeś datę doręczenia {delivery}. "
                "Nie dodaję do niej dni — sam policz, czy liczyć od tego dnia, czy od następnego."
            )
        else:
            note = "Daty kalendarzowej nie liczę. W piśmie jest tylko liczba dni."
        items.append(
            {
                "kind": "relative",
                "quote": " ".join(match.group(0).split()),
                "days": int(match.group(1)),
                "business_days": business,
                "anchor": anchor,
                "calendar_date": None,
                "note": note,
            }
        )
    for cue in ABSOLUTE_CUE.finditer(text):
        window = text[cue.end() : cue.end() + 32]
        date_match = NUMERIC_DATE.match(window) or WORD_DATE.match(window.lstrip())
        if date_match is None:
            continue
        if not date_match.group(0)[:1].isdigit():
            continue
        if WORD_DATE.match(date_match.group(0)):
            month = MONTHS[_fold(date_match.group(2))]
            iso = _valid_date(int(date_match.group(3)), month, int(date_match.group(1)))
        else:
            iso = _valid_date(int(date_match.group(3)), int(date_match.group(2)), int(date_match.group(1)))
        if not iso:
            continue
        quote = " ".join((cue.group(0) + date_match.group(0)).split())
        items.append(
            {
                "kind": "absolute",
                "quote": quote,
                "days": None,
                "business_days": False,
                "anchor": "data_w_tekscie",
                "calendar_date": iso,
                "note": "Ta data jest w piśmie, przy słowie o terminie. Nie sprawdzałem, czy to na pewno ten termin.",
            }
        )
    word_rel = re.compile(
        r"(?i)w (?:terminie|ciągu)\s+("
        + "|".join(WORD_NUMBERS)
        + r")\s+dni(?:\s+(kalendarzowych|roboczych))?(?:\s+od\s+([^.\n]{3,60}))?"
    )
    for match in word_rel.finditer(text):
        business = (match.group(2) or "").casefold().startswith("robocz")
        items.append(
            {
                "kind": "relative",
                "quote": " ".join(match.group(0).split()),
                "days": WORD_NUMBERS[_fold(match.group(1))],
                "business_days": business,
                "anchor": "doreczenie" if match.group(3) and "doręcz" in _fold(match.group(3)) else "inny",
                "calendar_date": None,
                "note": "Pismo mówi o dniach roboczych. Tych dni nie liczę."
                if business
                else "Daty kalendarzowej nie liczę. W piśmie jest liczba dni słowem, nie cyfrą.",
            }
        )
    return items


def _amounts(text: str) -> list[dict]:
    found = []
    seen: set[str] = set()
    for match in AMOUNT.finditer(text):
        quote = " ".join(match.group(0).split())
        if quote in seen:
            continue
        seen.add(quote)
        found.append({"quote": quote, "raw": match.group(1)})
    return found


def _phones(text: str) -> list[str]:
    found = []
    seen: set[str] = set()
    for match in PHONE.finditer(text):
        pretty = " ".join(match.group(2).split())
        if pretty in seen:
            continue
        seen.add(pretty)
        found.append(pretty)
    return found


def _quotes(text: str, pattern: str, limit: int) -> list[str]:
    found = []
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        quote = " ".join(match.group(0).split())[:240]
        if quote and quote not in found:
            found.append(quote)
        if len(found) >= limit:
            break
    return found


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    folded = _fold(text)
    return any(needle in folded for needle in needles)


def _word(text: str, word: str) -> bool:
    return re.search(rf"(?i)(?<!\w){re.escape(word)}(?!\w)", text) is not None


def _case_id(text: str) -> str | None:
    match = CASE_ID.search(text)
    if match:
        raw = re.split(r"\.\s", match.group(1), maxsplit=1)[0]
        kept: list[str] = []
        for token in raw.split():
            token = token.strip(".,;")
            if not token:
                continue
            if re.search(r"\d|/", token) or not kept or len(token) <= 2:
                kept.append(token)
            else:
                break
        if kept:
            return " ".join(kept)
    km = KM_ID.search(text)
    return " ".join(km.group(0).split()) if km else None


def _parse_delivery(value: str) -> str | None:
    cleaned = value.strip()
    try:
        return date.fromisoformat(cleaned).isoformat()
    except ValueError:
        pass
    match = re.fullmatch(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", cleaned)
    if not match:
        return None
    return _valid_date(int(match.group(3)), int(match.group(2)), int(match.group(1)))


def analyze(text: str, *, delivery: str | None = None) -> dict:
    if text is None:
        raise Unreadable("brak tekstu. wklej pismo.")
    if len(text) > MAX_CHARS:
        raise Unreadable("za długi tekst. wklej samo pismo, bez załączników.")
    if not _readable(text):
        raise Unreadable(
            "Nie czytam skanu, zdjęcia ani pustego pliku. "
            "Przepisz: kto napisał, znak sprawy, datę, zdanie o terminie, kwotę i telefon z pisma."
        )
    delivery_ignored = False
    if delivery:
        parsed = _parse_delivery(delivery)
        if parsed is None:
            delivery = None
            delivery_ignored = True
        else:
            delivery = parsed

    redacted, stats = redact(text)
    kind = _kind(redacted)
    sender = _sender(redacted)
    case_id = _case_id(redacted)
    dates = _dates(redacted)
    deadlines = _deadlines(redacted, delivery)
    amounts = _amounts(redacted)
    phones = _phones(redacted)
    legal = _quotes(redacted, r"[^.\n]{0,40}(?:art\.|ustawy|rozporządzen)[^.\n]{0,160}", 3)
    demand = _quotes(
        redacted,
        r"[^.\n]{0,40}(?:wzywa|zobowiązuje|zobowiazuje|należy zapłacić|nalezy zaplacic|wnosi się o zapłatę)[^.\n]{0,180}",
        1,
    )
    enforcement = _has_any(redacted, ENFORCEMENT)
    zus = _word(redacted, "zus") or _has_any(redacted, ZUS)
    tax = TAX_STEM in _fold(redacted)
    consumer = any(_word(redacted, stem) or stem in _fold(redacted) for stem in CONSUMER_WORDS)
    consumer = consumer or _word(redacted, "towar")
    hotline = None
    if consumer and not enforcement and not zus and not tax:
        hotline = {
            "phones": list(UOKiK_PHONES),
            "hours": "dni robocze 10:00–18:00",
            "tariff": "opłata według taryfy operatora",
            "source": "https://uokik.gov.pl/pomoc-dla-konsumentow",
            "note": "To pomoc przy sporze o zakup. Nie jest numerem z tego pisma.",
        }

    unknown: list[str] = []
    if kind is None:
        unknown.append("nie rozpoznałem rodzaju pisma")
    if sender is None:
        unknown.append("nie widzę, kto pismo wysłał")
    if case_id is None:
        unknown.append("nie widzę znaku sprawy")
    if not deadlines:
        unknown.append("nie widzę terminu")
    if not amounts:
        unknown.append("nie widzę kwoty")
    if not phones:
        unknown.append("nie widzę telefonu w tekście")
    if not demand:
        unknown.append("nie widzę zdania, czego pismo żąda")

    return {
        "disclaimer": DISCLAIMER,
        "kind": kind,
        "sender": sender,
        "case_id": case_id,
        "dates_found": dates,
        "deadlines": deadlines,
        "amounts": amounts,
        "phones_in_text": phones,
        "legal_basis_quotes": legal,
        "demand_quote": demand[0] if demand else None,
        "unknown": unknown,
        "pesel_redacted": stats["pesel"] > 0,
        "accounts_redacted": stats["accounts"],
        "enforcement": enforcement,
        "consumer_hotline": hotline,
        "delivery_given": delivery,
        "delivery_ignored": delivery_ignored,
    }
