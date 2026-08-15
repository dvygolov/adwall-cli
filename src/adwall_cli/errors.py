class AdWallError(Exception):
    """Base CLI error."""


class ConfigError(AdWallError):
    """Configuration is missing or invalid."""


class ApiError(AdWallError):
    """AdWall returned an HTTP, JSON, or network error."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        errors: object | None = None,
        response_meta: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.errors = errors
        self.response_meta = response_meta or {}
