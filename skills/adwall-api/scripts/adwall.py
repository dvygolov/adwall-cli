#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
CLI_SRC = SKILL_DIR / "cli" / "src"
sys.path.insert(0, str(CLI_SRC))

from adwall_cli.cli import main  # noqa: E402


if __name__ == "__main__":
    main()
