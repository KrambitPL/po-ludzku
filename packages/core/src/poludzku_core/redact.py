from __future__ import annotations

import re

PESEL_MARK = "[PESEL wycięty]"
ACCOUNT_MARK = "[rachunek wycięty]"

# Longer and more specific patterns first. A following amount must not join the run.
_ACCOUNTS = (
    re.compile(r"(?<![0-9])[0-9]{26}(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9]{2}(?: [0-9]{4}){6}(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9]{2}(?:-[0-9]{4}){6}(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9]{2}(?: [0-9]{2}){12}(?![0-9])"),
)
_PESEL = (
    re.compile(r"(?<![0-9])[0-9]{11}(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9](?: [0-9]){10}(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9](?:-[0-9]){10}(?![0-9])"),
)


def pesel_checksum_ok(digits: str) -> bool:
    if len(digits) != 11 or not digits.isdigit():
        return False
    weights = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
    total = sum(int(digits[i]) * weights[i] for i in range(10))
    check = (10 - (total % 10)) % 10
    return check == int(digits[10])


def _sub_all(text: str, patterns: tuple[re.Pattern[str], ...], mark: str, pred=None) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        digits = re.sub(r"[^0-9]", "", match.group(0))
        if pred is not None and not pred(digits):
            return match.group(0)
        count += 1
        return mark

    for pattern in patterns:
        text = pattern.sub(repl, text)
    return text, count


def _glued_pesel(text: str) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        digits = match.group(0)
        for start in range(0, len(digits) - 10):
            if pesel_checksum_ok(digits[start : start + 11]):
                count += 1
                return digits[:start] + PESEL_MARK + digits[start + 11 :]
        return digits

    return re.sub(r"(?<![0-9])[0-9]{12,}(?![0-9])", repl, text), count


def redact(text: str) -> tuple[str, dict]:
    text, accounts = _sub_all(text, _ACCOUNTS, ACCOUNT_MARK)
    text, pesel = _sub_all(text, _PESEL, PESEL_MARK, pesel_checksum_ok)
    text, glued = _glued_pesel(text)
    return text, {"pesel": pesel + glued, "accounts": accounts}
