from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from poludzku_core import Unreadable, analyze, commercial_card, human_card, load_identity
from poludzku_core.pdftext import extract_pdf_text

WEB = Path(__file__).resolve().parents[4] / "apps" / "web"
ALLOWED = {
    "/": "index.html",
    "/index.html": "index.html",
    "/explain.mjs": "explain.mjs",
    "/page.mjs": "page.mjs",
}
HOST = "127.0.0.1"


def _read_input(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    file_path = Path(path)
    if file_path.suffix.lower() == ".pdf":
        return extract_pdf_text(file_path)
    raw = file_path.read_bytes()
    for encoding in ("utf-8", "cp1250"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise Unreadable("nie czytam kodowania tego pliku. wklej tekst.")


def _about() -> str:
    who = load_identity()
    return "\n".join(
        [
            who["product"],
            who["vendor"],
            f"{who['street']}, {who['postal_city']}",
            f"KRS {who['krs']}, NIP {who['nip']}, REGON {who['regon']}",
            who["email"],
            who["phone"],
            "",
            "Automat streszcza pismo, które wkleisz. Może się mylić.",
            "To nie jest pomoc prawna. Nic nie wysyłamy.",
            "Tekst nie wychodzi z tego komputera, chyba że sam go skopiujesz.",
            "Skarga na to narzędzie: napisz na adres wyżej.",
        ]
    )


def _explain(args: argparse.Namespace) -> int:
    try:
        text = _read_input(args.path)
        result = analyze(text, delivery=args.doreczenie)
    except Unreadable as exc:
        print(exc.message, file=sys.stderr)
        return 3
    except OSError:
        print("nie czytam tego pliku. wklej tekst.", file=sys.stderr)
        return 3
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(human_card(result))
    if not args.no_card:
        print("Informacja handlowa — nie wysyłaj tu pisma. Pełna kartka: kartka", file=sys.stderr)
    return 0


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _deny(self, code: int) -> None:
        body = b"nie\n"
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if "?" in self.path or self.command != "GET":
            self._deny(400)
            return
        name = ALLOWED.get(self.path)
        if name is None:
            self._deny(404)
            return
        file_path = WEB / name
        if not file_path.is_file():
            self._deny(404)
            return
        data = file_path.read_bytes()
        kind = "text/html" if name.endswith(".html") else "text/javascript" if name.endswith(".mjs") else "application/json"
        self.send_response(200)
        self.send_header("Content-Type", f"{kind}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'; script-src 'self'",
        )
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        self._deny(405)

    def do_PUT(self) -> None:
        self._deny(405)


def _serve(port: int) -> int:
    if HOST != "127.0.0.1":
        print("serwer może słuchać tylko na 127.0.0.1", file=sys.stderr)
        return 2
    try:
        server = ThreadingHTTPServer((HOST, port), _Handler)
    except OSError:
        print("nie mogę otworzyć portu. podaj inny: pismo serve --port", file=sys.stderr)
        return 2
    print(f"http://{HOST}:{port}", file=sys.stderr)
    print("Tekst pisma zostaje w przeglądarce. Ten serwer go nie przyjmuje.", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pismo", description="Streszczenie pisma. Nic nie jest wysyłane.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    explain = sub.add_parser("explain", help="streść pismo z pliku, PDF albo stdin")
    explain.add_argument("path", nargs="?", default="-")
    explain.add_argument("--json", action="store_true")
    explain.add_argument("--no-card", action="store_true")
    explain.add_argument("--doreczenie", default=None, help="RRRR-MM-DD, data którą znasz, nie z pisma")
    serve = sub.add_parser("serve", help="lokalna strona, tylko 127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    sub.add_parser("about", help="kto to prowadzi i czego nie robi")
    args = parser.parse_args(argv)
    if args.cmd == "about":
        print(_about())
        return 0
    if args.cmd == "serve":
        return _serve(args.port)
    return _explain(args)


if __name__ == "__main__":
    raise SystemExit(main())
