from __future__ import annotations

import json
from pathlib import Path

import pytest
from pypdf import PdfWriter

from poludzku_core import Unreadable, analyze, commercial_card, family_card, human_card
from poludzku_core.pdftext import extract_pdf_text

PESEL = "00010100008"
ACCOUNT = "00000000000000000000000000"
FIXTURES = Path(__file__).parent / "fixtures"

TAX = f"""Urząd Skarbowy w Lublinie
Lublin, dnia 1 marca 2026 r.

Znak: US-LUB.123.2026

Wezwanie do zapłaty

Wzywa się do zapłaty kwoty 1 250,50 zł w terminie do dnia 15.04.2026.

W terminie 14 dni od dnia doręczenia niniejszego pisma można wnieść odwołanie.

Podstawa prawna: art. 15 ustawy z dnia 29 sierpnia 1997 r.
Telefon: 81 123 45 67
PESEL {PESEL}
rachunek {ACCOUNT}
"""

CONSUMER = """Sklep Testowy
Reklamacja towaru odrzucona.

Wzywa się do zapłaty kwoty 50,00 zł do dnia 1.05.2026.
Telefon: 500 600 700
"""

BAILIFF = """Komornik Sądowy przy Sądzie Rejonowym
Znak: KM 1/26

Wezwanie

W terminie 7 dni roboczych od dnia doręczenia należy zapłacić 10,00 zł.
W piśmie jest też słowo towar, bo dłużnik kupił towar.
"""


def test_tax_letter_does_not_invent_a_date_or_leak_ids():
    result = analyze(TAX, delivery="2026-03-10")
    assert result["kind"]["id"] == "wezwanie_do_zaplaty"
    assert result["sender"] == "Urząd Skarbowy w Lublinie"
    assert result["case_id"] == "US-LUB.123.2026"
    assert result["pesel_redacted"] is True
    assert result["accounts_redacted"] == 1
    assert result["consumer_hotline"] is None
    absolute = [item for item in result["deadlines"] if item["kind"] == "absolute"]
    relative = [item for item in result["deadlines"] if item["kind"] == "relative"]
    assert absolute[0]["calendar_date"] == "2026-04-15"
    assert relative[0]["calendar_date"] is None
    assert relative[0]["days"] == 14
    assert "2026-03-10" in relative[0]["note"]
    blob = json.dumps(result, ensure_ascii=False)
    assert PESEL not in blob
    assert ACCOUNT not in blob
    assert "wnoszę" not in human_card(result)
    assert "uniknij zajęcia" not in human_card(result)


def test_consumer_hotline_only_without_office():
    result = analyze(CONSUMER)
    assert result["consumer_hotline"]["phones"] == ["801 440 220", "222 66 76 76"]
    assert "taryfy" in result["consumer_hotline"]["tariff"]


def test_bailiff_beats_consumer_word_and_does_not_count_business_days():
    result = analyze(BAILIFF)
    assert result["enforcement"] is True
    assert result["consumer_hotline"] is None
    assert result["deadlines"][0]["business_days"] is True
    assert result["deadlines"][0]["calendar_date"] is None
    card = human_card(result)
    assert "wobec zajęcia" in card
    assert "801 440 220" not in card


def test_usluga_alone_is_not_a_consumer_dispute():
    text = "Zakład " + ("x" * 40) + " świadczenie usług w terminie do dnia 2.02.2026. Telefon 111 222 333."
    result = analyze(text)
    assert result["consumer_hotline"] is None


def test_short_scan_and_oversize_fail_closed():
    with pytest.raises(Unreadable):
        analyze("skan")
    with pytest.raises(Unreadable):
        analyze("a" * 200_001)
    with pytest.raises(Unreadable):
        analyze("ł" * 30 + "\ufffd" * 30)


def test_commercial_card_is_static_and_labelled():
    card = commercial_card()
    assert card.startswith("INFORMACJA HANDLOWA")
    assert "KOD.AI sp. z o.o." in card
    assert "Krambit" not in card
    assert "0001218254" in card
    assert PESEL not in card
    assert "book.kodai.com.pl" in card
    assert "Nie dołączaj" in card


def test_family_card_keeps_the_amount_and_drops_ids():
    card = family_card(analyze(TAX))
    assert PESEL not in card
    assert ACCOUNT not in card
    assert "1 250,50" in card
    assert "Rodzaj: wezwanie do zapłaty" in card


def test_dotted_delivery_is_kept_and_garbage_is_ignored():
    parsed = analyze(TAX, delivery="10.03.2026")
    assert parsed["delivery_given"] == "2026-03-10"
    ignored = analyze(TAX, delivery="wczoraj")
    assert ignored["delivery_ignored"] is True
    assert ignored["kind"]["id"] == "wezwanie_do_zaplaty"
    assert "nie rozumiem" in human_card(ignored)


def test_grouped_account_and_trailing_pesel_are_cut():
    text = (
        "Urząd Skarbowy w Lublinie\n"
        "Wezwanie do zapłaty na rachunek 12 1234 5678 9012 3456 7890 1234 1 250,50 zł "
        "do dnia 15.04.2026. PESEL 00010100008 99. Telefon: 81 123 45 67. "
        "Znak sprawy: WM/2026/18.\n"
    )
    result = analyze(text)
    blob = json.dumps(result, ensure_ascii=False) + family_card(result)
    assert "1234 5678" not in blob
    assert "00010100008" not in blob
    assert result["accounts_redacted"] == 1
    assert result["pesel_redacted"] is True
    assert result["case_id"] == "WM/2026/18"
    assert any(item["quote"] == "1 250,50 zł" for item in result["amounts"])


def test_amounts_deadlines_phones_and_false_hotline():
    text = (
        "Towarzystwo w towarzystwie. Urzędzie skarbowym nie, ale Zakład ubezpieczeń też nie. "
        "Kwota 2.450,80 zł oraz 350 zł i 4 200 zł. Termin płatności: 15.04.2026. "
        "Sygn. akt I C 123/26. REGON 123456785. Telefon: (81) 532-10-20. "
        "W terminie czternastu dni od dnia doręczenia.\n"
    )
    # tax stem is absent; "urzędzie skarbowym" must still suppress the hotline
    office = analyze(
        "Reklamacja towaru. Urzędzie skarbowym w Lublinie wezwanie do zapłaty 10,00 zł do dnia 1.05.2026. "
        + ("x" * 20)
    )
    assert office["consumer_hotline"] is None
    seizure = analyze(
        "Reklamacja towaru. Zajęciu wynagrodzenia dotyczy wezwanie do zapłaty 10,00 zł do dnia 1.05.2026. "
        + ("y" * 20)
    )
    assert seizure["enforcement"] is True
    assert seizure["consumer_hotline"] is None
    result = analyze(text + ("z" * 10))
    quotes = [item["quote"] for item in result["amounts"]]
    assert "2.450,80 zł" in quotes
    assert "350 zł" in quotes
    assert "4 200 zł" in quotes
    assert any(item["calendar_date"] == "2026-04-15" for item in result["deadlines"])
    assert any(item["days"] == 14 for item in result["deadlines"])
    assert result["case_id"] == "I C 123/26"
    assert "123456785" not in result["phones_in_text"]
    assert any("532" in phone for phone in result["phones_in_text"])
    assert analyze("oznakowanie " + ("q" * 40) + " wezwanie do zapłaty 10,00 zł do dnia 1.05.2026.")["case_id"] is None


def test_r3_amount_pesel_and_zajecia():
    whole = analyze("Bank Testowy. Do zapłaty 1250,50 zł oraz 1000 zł do dnia 2.06.2026. Telefon: 500 600 700.")
    assert [item["quote"] for item in whole["amounts"]] == ["1250,50 zł", "1000 zł"]
    glued = "Urząd Skarbowy w Lublinie PESEL 0001010000899 wezwanie do zapłaty 10,00 zł do dnia 1.05.2026."
    card = family_card(analyze(glued))
    assert "00010100008" not in card
    classes = analyze("Reklamacja towaru. Opłata za zajęcia 40,00 zł do dnia 1.05.2026. Telefon: 500 600 700.")
    assert classes["enforcement"] is False
    assert classes["consumer_hotline"] is not None


def test_cp1250_file_does_not_traceback(tmp_path: Path):
    path = tmp_path / "pismo.txt"
    path.write_bytes("Urząd Skarbowy w Lublinie. Wezwanie do zapłaty kwoty 10,00 zł do dnia 1.05.2026.\n".encode("cp1250"))
    assert main_explain(path) == 0


def main_explain(path: Path) -> int:
    from poludzku_pismo.cli import main

    return main(["explain", str(path), "--json"])


def test_empty_pdf_fails_closed(tmp_path: Path):
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=400)
    blank = tmp_path / "blank.pdf"
    writer.write(blank)
    with pytest.raises(Unreadable):
        analyze(extract_pdf_text(blank))


BAILIFF_REAL = """Komornik Sądowy przy Sądzie Rejonowym w Krakowie
Kancelaria Komornicza nr X w Krakowie
Sygn. akt KM 1234/26

ZAWIADOMIENIE O WSZCZĘCIU EGZEKUCJI

Na podstawie tytułu wykonawczego - nakazu zapłaty Sądu Rejonowego z dnia 12.01.2026, sygn. I Nc 55/26.
Należność główna: 12 450,00 zł, odsetki 1 103,22 zł.
Wzywam dłużnika do zapłaty w terminie 7 dni.
Na czynności komornika przysługuje skarga do Sądu Rejonowego w terminie 7 dni od dnia dokonania czynności.
"""

ZUS_REAL = """ZAKŁAD UBEZPIECZEŃ SPOŁECZNYCH
Oddział w Lublinie
Lublin, 2026-09-14

DECYZJA nr 123/2026

ZUS ustala zaległość z tytułu składek w wysokości 3 400 PLN.
Od niniejszej decyzji przysługuje odwołanie do Sądu Okręgowego za pośrednictwem ZUS w terminie miesiąca od dnia jej doręczenia.
Płatność do 30 października 2026 r.
"""


def test_relative_deadline_without_anchor_is_found():
    result = analyze(BAILIFF_REAL)
    quotes = [item["quote"] for item in result["deadlines"]]
    assert "w terminie 7 dni" in quotes
    assert any("dokonania czynności" in quote for quote in quotes)


def test_month_deadline_payment_cue_and_iso_date():
    result = analyze(ZUS_REAL)
    assert "nie widzę terminu" not in result["unknown"]
    month = [item for item in result["deadlines"] if "miesiąca" in item["quote"]]
    assert month and month[0]["anchor"] == "doreczenie"
    assert month[0]["days"] is None
    assert month[0]["calendar_date"] is None
    assert any(item["calendar_date"] == "2026-10-30" for item in result["deadlines"])
    assert any(item["iso"] == "2026-09-14" for item in result["dates_found"])
    weeks = analyze("Urząd Miasta. Wezwanie. Odpowiedz w ciągu dwóch tygodni od dnia doręczenia pisma.")
    assert weeks["deadlines"] and weeks["deadlines"][0]["days"] is None


def test_letter_date_comes_from_the_header_only():
    assert analyze(TAX)["letter_date"] == {"iso": "2026-03-01", "quote": "1 marca 2026"}
    assert analyze(ZUS_REAL)["letter_date"]["iso"] == "2026-09-14"
    bailiff = analyze(BAILIFF_REAL)
    assert bailiff["letter_date"] is None
    assert "12.01.2026" not in human_card(bailiff).split("--- szkic ---")[1]


def test_draft_is_formatted():
    card = human_card(analyze(TAX))
    draft = card.split("--- szkic ---")[1].split("--- koniec szkicu ---")[0]
    assert "Szanowni Państwo,\n\nnawiązuję do pisma z dnia 1 marca 2026 znak US-LUB.123.2026." in draft
    assert "  " not in draft
    assert " ." not in draft


def _quotes_of(text: str) -> list[str]:
    return [item["quote"] for item in analyze(text)["deadlines"]]


def test_r1_two_deadlines_in_one_sentence():
    quotes = _quotes_of(
        "Urząd Miasta. Wezwanie do zapłaty 100 zł w terminie 7 dni od doręczenia, "
        "a odwołanie można wnieść w terminie czternastu dni od dnia doręczenia decyzji."
    )
    assert quotes == ["w terminie 7 dni od doręczenia", "w terminie czternastu dni od dnia doręczenia decyzji"]
    months = _quotes_of("Urząd Miasta. Wezwanie w terminie 3 miesięcy od dnia doręczenia oraz w ciągu miesiąca od publikacji.")
    assert len(months) == 2


def test_r1_year_glued_to_r_and_upływa_phrasings():
    glued = analyze("Urząd Miasta. Wezwanie do zapłaty 100 zł w terminie do dnia 15.03.2026r. Telefon 81 123 45 67.")
    assert [item["calendar_date"] for item in glued["deadlines"]] == ["2026-03-15"]
    for text in (
        "Wezwanie. Proszę zapłacić w nieprzekraczalnym terminie 7 dni od daty otrzymania niniejszego wezwania.",
        "Wezwanie. Proszę zapłacić w terminie 14 (czternastu) dni od dnia doręczenia wezwania.",
        "Wezwanie. Termin płatności upływa dnia 15.03.2026 dla tej należności.",
        "Wezwanie. Termin upływa z dniem 15.03.2026 dla tej należności i tyle.",
    ):
        assert analyze(text)["deadlines"], text
    twice = analyze("Wezwanie do zapłaty. Termin płatności: 15.03.2026 (płatne do 15.03.2026).")
    assert len(twice["deadlines"]) == 1


def test_r1_letter_date_skips_labelled_deadline_and_reads_more_headers():
    labelled = analyze("Urząd Miasta Lublin\nTermin płatności:\n15.03.2026\nData wystawienia:\n01.03.2026\nWezwanie do zapłaty 10,00 zł.")
    assert labelled["letter_date"] is None
    assert analyze("Urząd Miasta\nLublin, 1 marca 2026 roku\nWezwanie do zapłaty 10,00 zł teraz.")["letter_date"]["iso"] == "2026-03-01"
    assert analyze("Urząd Miasta\nLublin dnia 1 marca 2026 r.\nWezwanie do zapłaty 10,00 zł teraz.")["letter_date"]["iso"] == "2026-03-01"
    cr = analyze("Urząd Miasta\rLublin, dnia 1 marca 2026 r.\rWezwanie do zapłaty 10,00 zł teraz.")
    assert cr["letter_date"]["iso"] == "2026-03-01"


def test_r2_idioms_are_not_deadlines():
    assert _quotes_of("Wspólnota. Najemca w dalszym ciągu 2 miesiące zalega z czynszem za lokal.") == []
    assert _quotes_of("Wspólnota. Wpłaty dokonano w poprzednim terminie 3 dni po upomnieniu z biura.") == []
