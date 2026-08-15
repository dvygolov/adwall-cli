#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
CLI_SRC = SKILL_DIR / "cli" / "src"
sys.path.insert(0, str(CLI_SRC))

# Make an installed skill self-contained without overriding explicit process
# configuration. The file is ignored by Git and must never be committed.
skill_env = SKILL_DIR / ".env"
if skill_env.is_file():
    os.environ.setdefault("ADWALL_ENV_FILE", str(skill_env))

from adwall_cli.cli import main  # noqa: E402


if __name__ == "__main__":
    main()
