from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .config import Settings
from .errors import ApiError, ConfigError


class AdWallClient:
    """Read-only client for the official AdWall Agent REST API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.last_response_meta: dict[str, Any] = {}

    def _headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        if not self.settings.api_key:
            raise ConfigError(
                "Set ADWALL_API_KEY in .env or the process environment. "
                "Create a key at https://app.adwall.io/api-agents/."
            )
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.settings.api_key}",
            "User-Agent": "adwall-cli/1.0",
        }
        headers.update(extra or {})
        return headers

    @staticmethod
    def _message(payload: Any, fallback: str) -> tuple[str, str | None]:
        if isinstance(payload, dict):
            code = payload.get("code") or payload.get("errorCode")
            for name in ("message", "error", "detail", "title"):
                value = payload.get(name)
                if isinstance(value, str) and value.strip():
                    return value.strip(), str(code) if code else None
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                first = errors[0]
                if isinstance(first, str):
                    return first, str(code) if code else None
                if isinstance(first, dict) and isinstance(first.get("message"), str):
                    return first["message"], str(code) if code else None
        return fallback, None

    @staticmethod
    def _response_meta(headers: Mapping[str, str]) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        mapping = {
            "retry-after": "retryAfter",
            "x-ratelimit-limit": "rateLimit",
            "x-ratelimit-remaining": "rateLimitRemaining",
            "x-ratelimit-reset": "rateLimitReset",
            "x-userratelimit-limit": "userRateLimit",
            "x-userratelimit-remaining": "userRateLimitRemaining",
            "x-userratelimit-reset": "userRateLimitReset",
        }
        lowered = {str(key).lower(): value for key, value in headers.items()}
        for source, target in mapping.items():
            if source in lowered:
                value: Any = lowered[source]
                if source.endswith(("limit", "remaining")):
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        pass
                meta[target] = value
        return meta

    def request(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        query = {
            key: value
            for key, value in (params or {}).items()
            if value is not None and value != ""
        }
        url = f"{self.settings.base_url}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode(query, doseq=True)}"
        request = Request(url, headers=self._headers(headers), method="GET")
        try:
            with urlopen(request, timeout=self.settings.timeout) as response:
                self.last_response_meta = self._response_meta(dict(response.headers.items()))
                raw = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            error_headers = dict(exc.headers.items()) if exc.headers else {}
            self.last_response_meta = self._response_meta(error_headers)
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload: Any = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            message, code = self._message(
                payload, f"AdWall request failed with HTTP {exc.code}: {exc.reason}"
            )
            raise ApiError(
                message,
                status=exc.code,
                code=code,
                errors=payload,
                response_meta=self.last_response_meta,
            ) from exc
        except URLError as exc:
            raise ApiError(f"Network error: {exc.reason}") from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApiError("AdWall returned invalid JSON") from exc

    def search_creatives(self, params: Mapping[str, Any]) -> dict[str, Any]:
        value = self.request("api/v1/creatives", params=params)
        if not isinstance(value, dict):
            raise ApiError("AdWall returned an unexpected search response")
        return value

    def get_creative(self, library_id: str, detail_grant: str | None = None) -> Any:
        headers = {"X-AdWall-Detail-Grant": detail_grant} if detail_grant else None
        return self.request(
            f"api/v1/creatives/{quote(library_id, safe='')}", headers=headers
        )

    def get_instances(
        self,
        library_id: str,
        detail_grant: str,
        *,
        limit: int = 10,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        value = self.request(
            f"api/v1/creatives/{quote(library_id, safe='')}/instances",
            params={"limit": limit, "cursor": cursor},
            headers={"X-AdWall-Detail-Grant": detail_grant},
        )
        if not isinstance(value, dict):
            raise ApiError("AdWall returned an unexpected instances response")
        return value

    def list_categories(self) -> Any:
        return self.request("api/v1/categories")

    def capabilities(self) -> Any:
        return self.request("api/v1/capabilities")

    def usage(self) -> Any:
        return self.request("api/v1/usage")

    def openapi(self) -> Any:
        return self.request("api/v1/openapi.json")
