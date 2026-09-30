from pathlib import Path

from poludzku_pismo.cli import HOST, main
from poludzku_kartka.cli import main as kartka_main


def test_about_names_kodai_not_krambit(capsys):
    assert main(["about"]) == 0
    out = capsys.readouterr().out
    assert "KOD.AI sp. z o.o." in out
    assert "Krambit" not in out
    assert "To nie jest pomoc prawna" in out


def test_json_stdout_has_no_sales_line(capsys, tmp_path: Path):
    path = tmp_path / "pismo.txt"
    path.write_text(
        "Urząd Skarbowy w Lublinie\n"
        + ("Wezwanie do zapłaty kwoty 10,00 zł do dnia 1.05.2026. " * 2),
        encoding="utf-8",
    )
    assert main(["explain", str(path), "--json"]) == 0
    captured = capsys.readouterr()
    assert captured.out.lstrip().startswith("{")
    assert "INFORMACJA HANDLOWA" not in captured.out
    assert captured.err == ""


def test_human_sales_line_is_stderr(capsys, tmp_path: Path):
    path = tmp_path / "pismo.txt"
    path.write_text("Urząd Skarbowy w Lublinie\n" + ("Wezwanie do zapłaty. " * 6), encoding="utf-8")
    assert main(["explain", str(path), "--no-card"]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("To jest automat.")
    assert "Informacja handlowa" not in captured.err
    assert main(["explain", str(path)]) == 0
    again = capsys.readouterr()
    assert "Informacja handlowa" in again.err
    assert "Informacja handlowa" not in again.out


def test_kartka_does_not_send(capsys):
    assert kartka_main([]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("INFORMACJA HANDLOWA")
    assert "Nie wysłano" in captured.err


def test_serve_is_loopback_only():
    source = Path(__file__).parents[1].joinpath("apps/pismo/src/poludzku_pismo/cli.py").read_text(encoding="utf-8")
    assert HOST == "127.0.0.1"
    assert "0.0.0.0" not in source
    assert "def do_POST" in source
    assert "def log_message" in source
