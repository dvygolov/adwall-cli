from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .errors import ApiError, ConfigError
from .graphql import RENEW_TOKENS, SIGN_IN


class AdWallClient:
    """GraphQL client with an isolated access/refresh-token session."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self._load_session()

    def _load_session(self) -> None:
        path = self.settings.session_file
        if not path.is_file():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return
        if isinstance(payload, dict):
            self.access_token = payload.get("access_token") or None
            self.refresh_token = payload.get("refresh_token") or None

    def _save_session(self) -> None:
        if not self.access_token or not self.refresh_token:
            raise ApiError("AdWall did not return both session tokens")
        path = Path(self.settings.session_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        if os.name != "nt":
            os.chmod(path, 0o600)

    def clear_session(self) -> None:
        self.access_token = None
        self.refresh_token = None
        path = Path(self.settings.session_file)
        if path.exists():
            path.unlink()

    def _endpoint(self, endpoint: str) -> str:
        endpoints = {
            "api": self.settings.api_url,
            "stats": self.settings.stats_api_url,
            "proxies": self.settings.proxies_api_url,
            "admin": self.settings.admin_api_url,
        }
        try:
            return endpoints[endpoint]
        except KeyError as exc:
            raise ConfigError(f"Unknown AdWall endpoint: {endpoint}") from exc

    @staticmethod
    def _error_from_payload(payload: Any, *, status: int | None = None) -> ApiError:
        errors = payload.get("errors") if isinstance(payload, dict) else None
        first = errors[0] if isinstance(errors, list) and errors else {}
        message = first.get("message") if isinstance(first, dict) else None
        extensions = first.get("extensions", {}) if isinstance(first, dict) else {}
        code = extensions.get("code") if isinstance(extensions, dict) else None
        return ApiError(
            message or f"AdWall request failed{f' with HTTP {status}' if status else ''}",
            status=status,
            code=code,
            errors=errors or payload,
        )

    def _post(
        self,
        query: str,
        variables: Mapping[str, Any] | None,
        operation_name: str,
        *,
        endpoint: str,
        token: str | None,
    ) -> dict[str, Any]:
        body = json.dumps(
            {
                "query": query,
                "variables": dict(variables or {}),
                "operationName": operation_name,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "adwall-cli/0.1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(
            self._endpoint(endpoint), data=body, headers=headers, method="POST"
        )
        try:
            with urlopen(request, timeout=self.settings.timeout) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8", errors="replace"))
            except (ValueError, json.JSONDecodeError):
                payload = {"errors": [{"message": f"HTTP {exc.code}: {exc.reason}"}]}
            raise self._error_from_payload(payload, status=exc.code) from exc
        except URLError as exc:
            raise ApiError(f"Network error: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise ApiError("AdWall returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise ApiError("AdWall returned an unexpected response")
        if payload.get("errors"):
            raise self._error_from_payload(payload)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ApiError("AdWall response does not contain GraphQL data")
        return data

    def request(
        self,
        query: str,
        variables: Mapping[str, Any] | None,
        operation_name: str,
        *,
        endpoint: str = "api",
        authenticated: bool = True,
        retry_auth: bool = True,
    ) -> dict[str, Any]:
        token = self.access_token if authenticated else None
        try:
            return self._post(
                query,
                variables,
                operation_name,
                endpoint=endpoint,
                token=token,
            )
        except ApiError as exc:
            if (
                authenticated
                and retry_auth
                and exc.code == "UNAUTHENTICATED"
                and operation_name != "RenewTokens"
                and self.refresh_token
            ):
                self.renew()
                return self.request(
                    query,
                    variables,
                    operation_name,
                    endpoint=endpoint,
                    authenticated=True,
                    retry_auth=False,
                )
            raise

    def login(self, email: str | None = None, password: str | None = None) -> dict[str, Any]:
        email = email or self.settings.email
        password = password or self.settings.password
        if not email or not password:
            raise ConfigError(
                "Set ADWALL_EMAIL and ADWALL_PASSWORD in .env or use the hidden login prompt"
            )
        data = self.request(
            SIGN_IN,
            {"email": email, "password": password},
            "SignIn",
            authenticated=False,
        )
        sign_in = data.get("signIn")
        if not isinstance(sign_in, dict):
            raise ApiError("AdWall login returned no session")
        self.access_token = sign_in.get("accessToken") or None
        self.refresh_token = sign_in.get("refreshToken") or None
        self._save_session()
        return sign_in.get("user") or {}

    def renew(self) -> None:
        if not self.refresh_token:
            raise ConfigError("No AdWall refresh token; run auth login")
        try:
            data = self._post(
                RENEW_TOKENS,
                {},
                "RenewTokens",
                endpoint="api",
                token=self.refresh_token,
            )
        except ApiError:
            self.clear_session()
            raise
        renewed = data.get("renewTokens")
        if not isinstance(renewed, dict):
            self.clear_session()
            raise ApiError("AdWall token renewal returned no session")
        self.access_token = renewed.get("accessToken") or None
        self.refresh_token = renewed.get("refreshToken") or None
        self._save_session()
