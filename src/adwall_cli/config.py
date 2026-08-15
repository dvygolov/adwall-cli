from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_dotenv(path: str | os.PathLike[str] | None = None) -> Path | None:
    """Load a small .env file without overriding process environment values."""
    explicit = Path(path).expanduser() if path else None
    candidates = [explicit] if explicit else []
    if not explicit:
        configured = os.environ.get("ADWALL_ENV_FILE")
        if configured:
            candidates.append(Path(configured).expanduser())
        candidates.append(Path.cwd() / ".env")

    for candidate in candidates:
        if candidate is None or not candidate.is_file():
            continue
        for raw in candidate.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[7:].strip()
            if key:
                os.environ.setdefault(key, _unquote(value))
        return candidate.resolve()

    if explicit:
        raise ConfigError(f"Environment file not found: {explicit}")
    return None


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str | None
    timeout: float
    env_file: Path | None

    @classmethod
    def from_env(cls, env_file: str | None = None) -> "Settings":
        loaded = load_dotenv(env_file)
        try:
            timeout = float(os.environ.get("ADWALL_TIMEOUT", "60"))
        except ValueError as exc:
            raise ConfigError("ADWALL_TIMEOUT must be a number") from exc
        if timeout <= 0:
            raise ConfigError("ADWALL_TIMEOUT must be positive")

        base_url = os.environ.get("ADWALL_BASE_URL", "https://adwall.io/api")
        base_url = base_url.strip().rstrip("/")
        if not base_url.startswith(("https://", "http://")):
            raise ConfigError("ADWALL_BASE_URL must be an HTTP(S) URL")

        api_key = os.environ.get("ADWALL_API_KEY", "").strip() or None
        return cls(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            env_file=loaded,
        )
