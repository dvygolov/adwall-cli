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
    """Load a small .env file without overriding real environment variables."""
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
    api_url: str
    stats_api_url: str
    proxies_api_url: str
    admin_api_url: str
    email: str | None
    password: str | None
    session_file: Path
    timeout: float
    env_file: Path | None

    @classmethod
    def from_env(cls, env_file: str | None = None) -> "Settings":
        loaded = load_dotenv(env_file)
        session_raw = os.environ.get("ADWALL_SESSION_FILE", ".adwall-session.json")
        session_file = Path(session_raw).expanduser()
        if not session_file.is_absolute():
            anchor = loaded.parent if loaded else Path.cwd()
            session_file = anchor / session_file
        try:
            timeout = float(os.environ.get("ADWALL_TIMEOUT", "60"))
        except ValueError as exc:
            raise ConfigError("ADWALL_TIMEOUT must be a number") from exc
        if timeout <= 0:
            raise ConfigError("ADWALL_TIMEOUT must be positive")
        return cls(
            api_url=os.environ.get(
                "ADWALL_API_URL", "https://adwall.io/api/graphql"
            ),
            stats_api_url=os.environ.get(
                "ADWALL_STATS_API_URL", "https://adwall.io/stats-api/graphql"
            ),
            proxies_api_url=os.environ.get(
                "ADWALL_PROXIES_API_URL", "https://adwall.io/proxies-api/graphql"
            ),
            admin_api_url=os.environ.get(
                "ADWALL_ADMIN_API_URL", "https://adwall.io/admin-api/graphql"
            ),
            email=os.environ.get("ADWALL_EMAIL") or None,
            password=os.environ.get("ADWALL_PASSWORD") or None,
            session_file=session_file.resolve(),
            timeout=timeout,
            env_file=loaded,
        )
