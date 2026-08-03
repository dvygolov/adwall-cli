from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT
TARGET = ROOT / "skills" / "adwall-api" / "cli"
FILES = [
    Path(".env.example"),
    Path("pyproject.toml"),
    Path("src/adwall_cli/__init__.py"),
    Path("src/adwall_cli/__main__.py"),
    Path("src/adwall_cli/cli.py"),
    Path("src/adwall_cli/client.py"),
    Path("src/adwall_cli/config.py"),
    Path("src/adwall_cli/errors.py"),
    Path("src/adwall_cli/graphql.py"),
    Path("src/adwall_cli/output.py"),
]


def synchronized() -> bool:
    return all(
        (TARGET / rel).is_file()
        and filecmp.cmp(SOURCE / rel, TARGET / rel, shallow=False)
        for rel in FILES
    )


def sync() -> None:
    for rel in FILES:
        destination = TARGET / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / rel, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if not synchronized():
            print("Skill CLI is out of sync.", file=sys.stderr)
            raise SystemExit(1)
        print("Skill CLI is synchronized.")
        return
    sync()
    print(f"Synchronized {len(FILES)} files to {TARGET}")


if __name__ == "__main__":
    main()
