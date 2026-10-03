from __future__ import annotations

from poludzku_core.analyze import DISCLAIMER, load_identity


def commercial_card() -> str:
    """Static. Takes no letter, so it cannot leak one."""
    who = load_identity()
    return "\n".join(
        [
            "INFORMACJA HANDLOWA",
            "",
            who["vendor"],
            f"{who['street']}, {who['postal_city']}",
            f"KRS {who['krs']}, NIP {who['nip']}, REGON {who['regon']}",
            who["email"],
            who["phone"],
            "",
            "Po ludzku streszcza pismo, które już masz. Jest darmowe. Nie wysyła go nigdzie.",
            "Jeśli w firmie utykacie na poczcie wpływającej, można o tym porozmawiać:",
            who["book"],
            "",
            "Tej kartki nie wysyłamy za Ciebie. Skopiuj ją sam, jeśli chcesz.",
            "Nie dołączaj do niej swojego pisma. Nie przysyłaj pisma na ten adres.",
        ]
    )


def _family_demand(analysis: dict) -> str | None:
    quote = analysis.get("demand_quote")
    if not quote:
        return None
    folded = quote.casefold()
    if any(token in folded for token in ("ul.", "ulica", "al.", "aleja", "osiedle")):
        return None
    if __import__("re").search(r"\d{2}[-\u2013]\d{3}|\d{11,}", quote):
        return None
    return quote


def family_card(analysis: dict) -> str:
    lines = [
        "Kartka do rodziny. Możesz ją skopiować.",
        "Nie ma tu PESEL ani numeru rachunku. To nie jest porada. Nic nie zostało wysłane.",
        "",
    ]
    kind = analysis.get("kind")
    lines.append(f"Rodzaj: {kind['label'] if kind else 'nie wiem'}")
    lines.append(f"Kto napisał: {analysis.get('sender') or 'nie wiem'}")
    lines.append(f"Znak: {analysis.get('case_id') or 'nie wiem'}")
    deadlines = analysis.get("deadlines") or []
    if not deadlines:
        lines.append("Termin: nie widzę go w tekście")
    else:
        lines.append("Terminy, cytat z pisma:")
        for item in deadlines:
            lines.append(f"- {item['quote']}")
            lines.append(f"  {item['note']}")
    phones = analysis.get("phones_in_text") or []
    if phones:
        lines.append("Telefon zapisany w piśmie: " + ", ".join(phones))
    else:
        lines.append("Telefonu w tekście nie znalazłem. Nie podaję numeru z głowy.")
    demand = _family_demand(analysis)
    if demand:
        lines.append(f"Czego żąda, cytat: {demand}")
    if analysis.get("enforcement"):
        lines.append(
            "To wygląda jak pismo komornicze albo egzekucyjne. "
            "Tu jest tylko opis. Nie ma instrukcji, co robić wobec zajęcia."
        )
    missing = analysis.get("unknown") or []
    if missing:
        lines.append("Czego nie znalazłem: " + "; ".join(missing) + ".")
    lines.append("")
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def _draft(analysis: dict) -> str:
    bits = ["nawiązuję do pisma"]
    letter_date = analysis.get("letter_date")
    if letter_date:
        bits.append(f"z dnia {letter_date['quote']}")
    case_id = analysis.get("case_id")
    if case_id:
        bits.append(f"znak {case_id}")
    return "\n".join(
        [
            "Szkic do własnej edycji. Nic nie zostało wysłane.",
            "To nie jest pismo do sądu i nie jest pomocą prawną.",
            "",
            "Szanowni Państwo,",
            "",
            " ".join(bits) + ".",
            "",
            "[Tu napisz jednym zdaniem, o co prosisz. Automat tego nie wpisuje.]",
            "",
            "Proszę o pisemną odpowiedź.",
            "",
            "[imię]",
            "[adres do odpowiedzi]",
        ]
    )


def human_card(analysis: dict) -> str:
    lines = [analysis["disclaimer"], ""]
    kind = analysis.get("kind")
    lines.append(f"Rodzaj: {kind['label'] if kind else 'nie rozpoznałem'}")
    if kind and kind.get("quote"):
        lines.append(f"Cytat: {kind['quote']}")
    lines.append(f"Kto napisał: {analysis.get('sender') or 'nie widzę'}")
    lines.append(f"Znak sprawy: {analysis.get('case_id') or 'nie widzę'}")
    if analysis.get("letter_date"):
        lines.append(f"Data pisma: {analysis['letter_date']['quote']}")
    dates = analysis.get("dates_found") or []
    if dates:
        lines.append(
            "Daty znalezione w tekście (to nie znaczy, że to termin): "
            + ", ".join(item["quote"] for item in dates)
        )
    else:
        lines.append("Daty w tekście: nie widzę")
    lines.append("")
    lines.append("Terminy:")
    deadlines = analysis.get("deadlines") or []
    if not deadlines:
        lines.append("- nie widzę terminu. Nie wymyślam daty.")
    for item in deadlines:
        when = item["calendar_date"] or "bez daty kalendarzowej"
        lines.append(f"- {item['quote']} ({when})")
        lines.append(f"  {item['note']}")
    lines.append("")
    amounts = analysis.get("amounts") or []
    if amounts:
        lines.append("Kwoty zapisane w tekście. Nie wiem, która jest do zapłaty:")
        for item in amounts:
            lines.append(f"- {item['quote']}")
    else:
        lines.append("Kwoty: nie widzę")
    phones = analysis.get("phones_in_text") or []
    if phones:
        lines.append("Telefon z pisma: " + ", ".join(phones))
    else:
        lines.append("Telefonu w piśmie nie ma. Nie podaję innego.")
    if analysis.get("demand_quote"):
        lines.append(f"Czego żąda, cytat: {analysis['demand_quote']}")
    legal = analysis.get("legal_basis_quotes") or []
    if legal:
        lines.append("Podstawa, cytat, bez oceny:")
        for quote in legal:
            lines.append(f"- {quote}")
    if analysis.get("pesel_redacted"):
        lines.append("Wyciąłem numer, który wygląda jak PESEL. Został tylko w tekście, który wkleiłeś.")
    if analysis.get("accounts_redacted"):
        lines.append("Wyciąłem numer rachunku. Został tylko w tekście, który wkleiłeś.")
    if analysis.get("enforcement"):
        lines.append(
            "To wygląda jak pismo komornicze albo egzekucyjne. "
            "Pokazuję, co jest w tekście. Nie podpowiadam, jak zachować się wobec zajęcia."
        )
    hotline = analysis.get("consumer_hotline")
    if hotline:
        lines.append(
            "Spór o zakup: "
            + " i ".join(hotline["phones"])
            + f", {hotline['hours']}, {hotline['tariff']}."
        )
        lines.append(hotline["note"])
    missing = analysis.get("unknown") or []
    if missing:
        lines.append("")
        lines.append("Czego nie znalazłem: " + "; ".join(missing) + ".")
    if analysis.get("delivery_given"):
        lines.append(f"Data doręczenia, którą podałeś: {analysis['delivery_given']}.")
    if analysis.get("delivery_ignored"):
        lines.append("Daty doręczenia nie rozumiem, więc jej nie używam. Kartka jest z samego pisma.")
    lines.extend(["", "--- szkic ---", _draft(analysis), "--- koniec szkicu ---"])
    lines.extend(["", "--- do skopiowania rodzinie ---", family_card(analysis), "--- koniec kartki dla rodziny ---"])
    return "\n".join(lines)
