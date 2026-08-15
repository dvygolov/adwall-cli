import io
import json
import sys
import unittest
from unittest.mock import patch

from adwall_cli.errors import ApiError
from adwall_cli.output import configure_utf8_stdout, emit, error_payload


class OutputTests(unittest.TestCase):
    def test_reconfigures_legacy_windows_stream_for_unicode_json(self):
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="cp1251")

        with patch.object(sys, "stdout", stream):
            configure_utf8_stdout()
            emit({"text": "🎁"})
            stream.flush()

        payload = json.loads(buffer.getvalue().decode("utf-8"))
        self.assertEqual(payload, {"text": "🎁"})

    def test_api_error_payload_includes_rate_limit_metadata(self):
        error = ApiError(
            "Too many requests",
            status=429,
            code="RATE_LIMITED",
            errors={"code": "RATE_LIMITED", "message": "Too many requests"},
            response_meta={
                "retryAfter": "17",
                "rateLimit": 100,
                "rateLimitRemaining": 0,
                "rateLimitReset": "42",
            },
        )

        self.assertEqual(
            error_payload(error),
            {
                "success": False,
                "error": "ApiError",
                "message": "Too many requests",
                "status": 429,
                "code": "RATE_LIMITED",
                "responseMeta": {
                    "retryAfter": "17",
                    "rateLimit": 100,
                    "rateLimitRemaining": 0,
                    "rateLimitReset": "42",
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
