from __future__ import annotations

import argparse
import sys

from poludzku_core import commercial_card, load_identity


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kartka", description="Informacja handlowa do samodzielnego skopiowania.")
    parser.add_argument("cmd", nargs="?", default="show", choices=["show", "about"])
    args = parser.parse_args(argv)
    if args.cmd == "about":
        who = load_identity()
        print(f"{who['product']}\n{who['vendor']}\nNic nie wysyłamy.")
        return 0
    print(commercial_card())
    print("Nie wysłano. Skopiuj sam, jeśli chcesz.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
