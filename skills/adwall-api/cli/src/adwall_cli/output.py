from __future__ import annotations

import json
import sys
from typing import Any, Iterable


def configure_utf8_stdout() -> None:
    """Make redirected JSON output reliable on Windows legacy code pages."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="strict")


def emit(value: Any, *, compact: bool = False) -> None:
    json.dump(
        value,
        sys.stdout,
        ensure_ascii=False,
        indent=None if compact else 2,
        separators=(",", ":") if compact else None,
        default=str,
    )
    sys.stdout.write("\n")


def emit_jsonl(values: Iterable[Any]) -> None:
    for value in values:
        json.dump(value, sys.stdout, ensure_ascii=False, separators=(",", ":"), default=str)
        sys.stdout.write("\n")


def error_payload(exc: Exception) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": False,
        "error": exc.__class__.__name__,
        "message": str(exc),
    }
    for name in ("status", "code"):
        value = getattr(exc, name, None)
        if value is not None:
            payload[name] = value
    return payload
