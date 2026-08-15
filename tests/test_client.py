import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from adwall_cli.client import AdWallClient
from adwall_cli.config import Settings
from adwall_cli.errors import ApiError, ConfigError


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    calls = []

    def log_message(self, *args):
        pass

    def _json(self, status, value, headers=None):
        raw = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlsplit(self.path)
        Handler.calls.append(
            {
                "path": parsed.path,
                "query": parse_qs(parsed.query),
                "authorization": self.headers.get("Authorization"),
                "detail_grant": self.headers.get("X-AdWall-Detail-Grant"),
                "accept": self.headers.get("Accept"),
            }
        )
        if parsed.path == "/api/v1/creatives":
            self._json(200, {"items": [{"library_id": "123"}], "next_cursor": None})
            return
        if parsed.path == "/api/v1/creatives/rate-limited":
            self._json(
                429,
                {"code": "RATE_LIMITED", "message": "Too many requests"},
                {
                    "Retry-After": "17",
                    "X-RateLimit-Limit": "100",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "42",
                },
            )
            return
        self._json(404, {"error": {"code": "NOT_FOUND", "message": "Not found"}})


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.calls = []

    def _settings(self, api_key="test-api-key"):
        return Settings(
            base_url=f"http://127.0.0.1:{self.server.server_port}/api",
            api_key=api_key,
            timeout=3,
            env_file=None,
        )

    def test_request_sends_bearer_and_encodes_query_parameters(self):
        client = AdWallClient(self._settings())

        result = client.request(
            "/v1/creatives",
            params={"q": "summer sale", "geo": "CZ,GB", "limit": 10, "cursor": None},
        )

        self.assertEqual(result["items"][0]["library_id"], "123")
        self.assertEqual(Handler.calls[0]["path"], "/api/v1/creatives")
        self.assertEqual(
            Handler.calls[0]["query"],
            {"q": ["summer sale"], "geo": ["CZ,GB"], "limit": ["10"]},
        )
        self.assertEqual(Handler.calls[0]["authorization"], "Bearer test-api-key")
        self.assertEqual(Handler.calls[0]["accept"], "application/json")

    def test_request_can_send_detail_grant_header(self):
        client = AdWallClient(self._settings())

        with self.assertRaises(ApiError):
            client.request(
                "/v1/creatives/missing",
                headers={"X-AdWall-Detail-Grant": "grant-value"},
            )

        self.assertEqual(Handler.calls[0]["detail_grant"], "grant-value")

    def test_missing_api_key_is_rejected_before_network_request(self):
        client = AdWallClient(self._settings(api_key=None))

        with self.assertRaises(ConfigError):
            client.request("/v1/creatives")

        self.assertEqual(Handler.calls, [])

    def test_json_error_exposes_status_code_and_rate_limit_metadata(self):
        client = AdWallClient(self._settings())

        with self.assertRaises(ApiError) as raised:
            client.request("/v1/creatives/rate-limited")

        error = raised.exception
        self.assertEqual(str(error), "Too many requests")
        self.assertEqual(error.status, 429)
        self.assertEqual(error.code, "RATE_LIMITED")
        self.assertEqual(
            error.response_meta,
            {
                "retryAfter": "17",
                "rateLimit": 100,
                "rateLimitRemaining": 0,
                "rateLimitReset": "42",
            },
        )

    def test_typed_methods_map_to_the_official_api(self):
        client = AdWallClient(self._settings())
        calls = []
        client.request = lambda path, params=None, headers=None: calls.append(
            (path, params, headers)
        ) or {"ok": True}

        client.search_creatives({"q": "casino", "countries_count": 2, "limit": 25})
        client.get_creative("lib/one", detail_grant="grant-1")
        client.get_instances(
            "lib/two", detail_grant="grant-2", limit=20, cursor="cursor-2"
        )
        client.list_categories()
        client.capabilities()
        client.usage()
        client.openapi()

        self.assertEqual(
            calls,
            [
                ("api/v1/creatives", {"q": "casino", "countries_count": 2, "limit": 25}, None),
                ("api/v1/creatives/lib%2Fone", None, {"X-AdWall-Detail-Grant": "grant-1"}),
                (
                    "api/v1/creatives/lib%2Ftwo/instances",
                    {"limit": 20, "cursor": "cursor-2"},
                    {"X-AdWall-Detail-Grant": "grant-2"},
                ),
                ("api/v1/categories", None, None),
                ("api/v1/capabilities", None, None),
                ("api/v1/usage", None, None),
                ("api/v1/openapi.json", None, None),
            ],
        )


if __name__ == "__main__":
    unittest.main()
