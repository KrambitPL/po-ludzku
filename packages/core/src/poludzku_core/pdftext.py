from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from poludzku_core.analyze import Unreadable

MAX_PAGES = 20


def extract_pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise Unreadable("plik jest zaszyfrowany. wklej tekst.")
        if len(reader.pages) > MAX_PAGES:
            raise Unreadable("za dużo stron. wklej sam tekst pisma.")
        parts: list[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
    except Unreadable:
        raise
    except Exception:
        raise Unreadable("nie czytam tego pliku. wklej tekst.") from None
    return "\n".join(parts)
